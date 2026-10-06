import sys
import os
import json
import time
import copy

BASE = os.path.dirname(os.path.abspath(__file__))
CARE_ROOT = os.path.join(BASE, '../..')
RTA_ROOT = os.path.join(CARE_ROOT, 'reaction_tone_to_attitude')
CAREV0_RTA = os.path.join(CARE_ROOT, 'CAREv0', 'reaction_tone_to_attitude')
CAREV1 = os.path.join(CARE_ROOT, 'CAREv1')

sys.path.insert(0, CAREV0_RTA)
sys.path.insert(0, CAREV1)
os.chdir(RTA_ROOT)

from env_loader import load_env
load_env('batch_round')
from prompt_eng import get_tone_prompt

from openai import OpenAI

# ── Config ────────────────────────────────────────────────────────────────────
SIM_MODELS = ['gemini-2.5-pro', 'gemini-3.1-pro-preview']
STYLES = ['COMM-BLIND', 'COMM-INFORMED', 'COMM-INFORMED-COT']  # split per style: one model's full
                                                                 # batch (6,582 reqs) exceeds the
                                                                 # 1.5M enqueued-token org limit
GPT_MODEL  = 'gpt-5-2025-08-07'
POLL_INTERVAL = 60               # seconds between state checks

samples_fp = os.path.join(CAREV1, 'data', 'sampled_batch_data.jsonl')
with open(samples_fp) as f:
    samples = [json.loads(line) for line in f]

subm_id_2_entry = {s['submission_id']: s for s in samples}

client = OpenAI(api_key=os.getenv('BCA_OpenAI-API_Key'))


def label_tones(sim_model):
    sim_dir = os.path.join(CAREV1, 'sim_reactions', sim_model)
    sim_fp  = os.path.join(sim_dir, 'id_to_simulated_reactions.json')
    out_dir = os.path.join(sim_dir, 'tone_eval')
    os.makedirs(out_dir, exist_ok=True)

    results_fp = os.path.join(out_dir, 'id_to_tones.json')

    with open(sim_fp) as f:
        sim_results = json.load(f)  # {key: {simulated_comment, reasoning}}, all 3 styles mixed

    for style in STYLES:
        # filter in memory only — the input file itself is never split or rewritten
        style_entries = {k: v for k, v in sim_results.items() if k.endswith(f'_SIM_{style}')}
        label_tones_for_style(sim_model, style, style_entries, out_dir, results_fp)


def label_tones_for_style(sim_model, style, style_entries, out_dir, results_fp):
    batch_input_fp  = os.path.join(out_dir, f'batch_input_{style}.jsonl')
    batch_output_fp = os.path.join(out_dir, f'batch_output_{style}.jsonl')
    tag = f"{sim_model}/{style}"

    # ── Build batch input ────────────────────────────────────────────────────
    batch_entries = []
    for key, sim_entry in style_entries.items():
        parts = key.split('_')
        subm_id = parts[-3]
        entry = subm_id_2_entry.get(subm_id)
        if not entry:
            print(f"[{tag}] [WARNING] submission_id not found: {subm_id}")
            continue

        data_entry = copy.deepcopy(entry)
        data_entry['reaction'] = sim_entry['simulated_comment']

        prompt = get_tone_prompt(data_entry, separate_instructions=True)
        batch_entries.append({
            "custom_id": key.replace('_SIM_', '_SIM-TONE_'),
            "method": "POST",
            "url": "/v1/responses",
            "body": {
                "model": GPT_MODEL,
                "reasoning": {"effort": "medium"},
                "text": {"verbosity": "low"},
                "instructions": prompt['instructions'],
                "input": prompt['input'],
            }
        })

    with open(batch_input_fp, 'w') as f:
        for entry in batch_entries:
            f.write(json.dumps(entry) + '\n')

    print(f"[{tag}] prepared {len(batch_entries)} entries -> {batch_input_fp}")

    # ── Upload & Submit ──────────────────────────────────────────────────────
    print(f"[{tag}] uploading batch input file...")
    batch_file = client.files.create(file=open(batch_input_fp, 'rb'), purpose='batch')
    print(f"[{tag}] file ID: {batch_file.id}")

    batch_job = client.batches.create(
        input_file_id=batch_file.id,
        endpoint='/v1/responses',
        completion_window='24h',
    )
    print(f"[{tag}] job ID: {batch_job.id}")

    # ── Poll ─────────────────────────────────────────────────────────────────
    print(f"[{tag}] polling for completion...")
    while True:
        job = client.batches.retrieve(batch_job.id)
        print(f"  [{time.strftime('%H:%M:%S')}] [{tag}] {job.status}")
        if job.status == 'completed':
            break
        if job.status in ('failed', 'cancelled', 'expired'):
            print(f"[{tag}] job ended unexpectedly: {job.status} — skipping")
            return
        time.sleep(POLL_INTERVAL)

    # ── Download & Collect ─────────────────────────────────────────────────────
    print(f"[{tag}] downloading results...")
    file_response = client.files.content(job.output_file_id)
    with open(batch_output_fp, 'wb') as f:
        f.write(file_response.read())

    new_tones = {}
    failed_ids = []

    with open(batch_output_fp, 'rb') as f:
        for line in f:
            entry = json.loads(line)
            if entry['response'].get('status_code') != 200:
                failed_ids.append(entry.get('custom_id'))
                continue
            custom_id = entry['custom_id']
            tone_text = None
            for output in entry['response']['body']['output']:
                if 'content' in output:
                    for content in output['content']:
                        if content.get('type') == 'output_text':
                            tone_text = content.get('text', '').strip()
                            break
                if tone_text:
                    break
            if tone_text:
                new_tones[custom_id] = tone_text
            else:
                failed_ids.append(custom_id)

    # load existing results (other styles for this model) so we don't wipe them out
    id_to_tones = {}
    if os.path.exists(results_fp):
        with open(results_fp) as f:
            id_to_tones = json.load(f)
    id_to_tones.update(new_tones)

    with open(results_fp, 'w') as f:
        json.dump(id_to_tones, f, indent=2)

    print(f"[{tag}] saved {len(id_to_tones)} total tones ({len(new_tones)} from this run) -> {results_fp}")
    if failed_ids:
        print(f"[{tag}] [WARNING] {len(failed_ids)} failed: {failed_ids}")


# ── Run for each simulation model ────────────────────────────────────────────
for sim_model in SIM_MODELS:
    label_tones(sim_model)
