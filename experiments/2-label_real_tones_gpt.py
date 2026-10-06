import sys
import os
import json
import time

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
CHUNK_SIZE = 2000          # no natural style split like 02 has, so just cut by count
GPT_MODEL  = 'gpt-5-2025-08-07'
POLL_INTERVAL = 60               # seconds between state checks

OUT_DIR = os.path.join(CAREV1, 'ground_truth_tones')
os.makedirs(OUT_DIR, exist_ok=True)
RESULTS_FP = os.path.join(OUT_DIR, 'id_to_generated_tones.json')

samples_fp = os.path.join(CAREV1, 'data', 'sampled_batch_data.jsonl')
with open(samples_fp) as f:
    samples = [json.loads(line) for line in f]

client = OpenAI(api_key=os.getenv('BCA_OpenAI-API_Key'))

# ── Build request list (skip empty reactions) ────────────────────────────────
all_entries = []
for sample in samples:
    for idx, reaction in enumerate(sample['reactions']):
        if not reaction.strip():
            continue
        entry = dict(sample, reaction=reaction)
        custom_id = f"{sample['subreddit']}_{sample['submission_id']}_REAL-TONE_{idx}"
        all_entries.append((custom_id, entry))

print(f"total requests: {len(all_entries)}")


def label_chunk(chunk_idx, chunk_entries):
    tag = f"chunk {chunk_idx}"
    batch_input_fp  = os.path.join(OUT_DIR, f'batch_input_{chunk_idx}.jsonl')
    batch_output_fp = os.path.join(OUT_DIR, f'batch_output_{chunk_idx}.jsonl')

    batch_entries = []
    for custom_id, entry in chunk_entries:
        prompt = get_tone_prompt(entry, separate_instructions=True)
        batch_entries.append({
            "custom_id": custom_id,
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

    # load existing results (other chunks) so we don't wipe them out
    id_to_tones = {}
    if os.path.exists(RESULTS_FP):
        with open(RESULTS_FP) as f:
            id_to_tones = json.load(f)
    id_to_tones.update(new_tones)

    with open(RESULTS_FP, 'w') as f:
        json.dump(id_to_tones, f, indent=2)

    print(f"[{tag}] saved {len(id_to_tones)} total tones ({len(new_tones)} from this run) -> {RESULTS_FP}")
    if failed_ids:
        print(f"[{tag}] [WARNING] {len(failed_ids)} failed: {failed_ids}")


# ── Run in chunks ─────────────────────────────────────────────────────────────
for i in range(0, len(all_entries), CHUNK_SIZE):
    label_chunk(i // CHUNK_SIZE, all_entries[i:i + CHUNK_SIZE])
