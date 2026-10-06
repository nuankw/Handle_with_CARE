import sys
import os
import json
import re
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
from prompt_eng import get_reaction_prompt

from google import genai

# ── Config ────────────────────────────────────────────────────────────────────
MODELS = ['gemini-2.5-pro', 'gemini-3.1-pro-preview']
STYLES = ['comm-blind', 'comm-informed', 'comm-informed-cot']
POLL_INTERVAL = 300        # seconds between state checks

# ── Load data (shared across all runs) ──────────────────────────────────────────
with open(os.path.join(CAREV1, 'subreddit_descriptions.json')) as f:
    descriptions = json.load(f)

samples_fp = os.path.join(CAREV1, 'data', 'sampled_batch_data.jsonl')
with open(samples_fp) as f:
    samples = [json.loads(line) for line in f]

for sample in samples:
    sample['subreddit_description'] = descriptions.get(sample['subreddit'], {}).get('description', '')

client = genai.Client()


def build_inline_batch(style):
    # only comm-informed-cot returns structured JSON (with reasoning); comm-blind
    # and comm-informed return the plain comment text as-is.
    is_cot = (style == 'comm-informed-cot')
    inline_batch = []
    for sample in samples:
        prompt = get_reaction_prompt(sample, style=style, separate_instructions=True)
        config = {"system_instruction": prompt['instructions']}
        if is_cot:
            config["response_mime_type"] = "application/json"
        inline_batch.append({
            "contents": prompt['input'],
            "config": config,
        })
    return inline_batch


def submit_job(model, style):
    out_dir = os.path.join(CAREV1, 'sim_reactions', model)
    os.makedirs(out_dir, exist_ok=True)
    job_names_fp = os.path.join(out_dir, 'batch_job_names.jsonl')

    inline_batch = build_inline_batch(style)
    display_name = f'sim-reaction-{style}-{model}'
    print(f"[{model} / {style}] submitting {len(inline_batch)} requests -> {display_name}")

    batch_job = client.batches.create(
        model=model,
        src=inline_batch,
        config={'display_name': display_name},
    )
    print(f"[{model} / {style}] job name: {batch_job.name}")

    with open(job_names_fp, 'a') as f:
        f.write(json.dumps({'display_name': display_name, 'batch_job_name': batch_job.name}) + '\n')

    return {
        'model': model,
        'style': style,
        'is_cot': (style == 'comm-informed-cot'),
        'out_dir': out_dir,
        'job_name': batch_job.name,
        'job': None,
        'done': False,
    }


def collect_job(run):
    model, style, is_cot = run['model'], run['style'], run['is_cot']
    out_dir, job = run['out_dir'], run['job']
    results_fp = os.path.join(out_dir, 'id_to_simulated_reactions.json')

    print(f"[{model} / {style}] collecting results...")

    # load existing results (other styles for this model) so we don't wipe them out
    sim_results = {}
    if os.path.exists(results_fp):
        with open(results_fp) as f:
            sim_results = json.load(f)

    parse_errors = []

    for idx, inlined in enumerate(job.dest.inlined_responses):
        raw = inlined.response.text

        subreddit     = samples[idx]['subreddit']
        submission_id = samples[idx]['submission_id']
        key = f"{subreddit}_{submission_id}_SIM_{style.upper()}"

        if not is_cot:
            # comm-blind / comm-informed: plain text response, no reasoning
            sim_results[key] = {'simulated_comment': raw.strip(), 'reasoning': {}}
            continue

        try:
            parsed = json.loads(raw)
            sim_results[key] = {
                'simulated_comment': parsed['simulated_comment'],
                'reasoning': parsed['reasoning'],
            }
        except (json.JSONDecodeError, KeyError) as e:
            recovered = False
            if isinstance(e, json.JSONDecodeError):
                # retry 1: Extra data → truncate at e.pos
                if 'Extra data' in str(e):
                    try:
                        parsed = json.loads(raw[:e.pos])
                        sim_results[key] = {
                            'simulated_comment': parsed['simulated_comment'],
                            'reasoning': parsed['reasoning'],
                        }
                        recovered = True
                    except (json.JSONDecodeError, KeyError):
                        pass
                # retry 2: truncated JSON (missing closing brace) → append \n}
                if not recovered:
                    try:
                        parsed = json.loads(raw + '\n}')
                        sim_results[key] = {
                            'simulated_comment': parsed['simulated_comment'],
                            'reasoning': parsed['reasoning'],
                        }
                        recovered = True
                    except (json.JSONDecodeError, KeyError):
                        pass
                # retry 3: junk chars after simulated_comment closing quote → strip and close
                if not recovered:
                    try:
                        cleaned = re.sub(
                            r'("simulated_comment"\s*:\s*"(?:[^"\\]|\\.)*").*$',
                            r'\1\n}',
                            raw, flags=re.DOTALL
                        )
                        parsed = json.loads(cleaned)
                        sim_results[key] = {
                            'simulated_comment': parsed['simulated_comment'],
                            'reasoning': parsed['reasoning'],
                        }
                        recovered = True
                    except (json.JSONDecodeError, KeyError):
                        pass
            if not recovered:
                parse_errors.append({'key': key, 'error': str(e), 'raw': raw[:200]})
                sim_results[key] = {'simulated_comment': raw, 'reasoning': {}}

    with open(results_fp, 'w') as f:
        json.dump(sim_results, f, indent=2)

    print(f"[{model} / {style}] saved {len(sim_results)} total results "
          f"({len(job.dest.inlined_responses)} from this run) -> {results_fp}")

    if parse_errors:
        err_fp = os.path.join(out_dir, f'parse_errors_{style}.json')
        with open(err_fp, 'w') as f:
            json.dump(parse_errors, f, indent=2)
        print(f"[{model} / {style}] [WARNING] {len(parse_errors)} parse errors -> {err_fp}")


# ── Submit all 6 jobs up front ───────────────────────────────────────────────
runs = [submit_job(model, style) for model in MODELS for style in STYLES]

# ── Poll all jobs together, collecting each as soon as it finishes ──────────
print(f"\nPolling {len(runs)} jobs for completion (every {POLL_INTERVAL // 60} min)...")
while any(not r['done'] for r in runs):
    for r in runs:
        if r['done']:
            continue
        job = client.batches.get(name=r['job_name'])
        state = str(job.state)
        if 'JOB_STATE_SUCCEEDED' in state:
            print(f"  [{time.strftime('%H:%M:%S')}] [{r['model']} / {r['style']}] succeeded")
            r['job'] = job
            r['done'] = True
            collect_job(r)
        elif any(s in state for s in ('JOB_STATE_FAILED', 'JOB_STATE_CANCELLED')):
            print(f"  [{time.strftime('%H:%M:%S')}] [{r['model']} / {r['style']}] {state} — skipping")
            r['done'] = True
        else:
            print(f"  [{time.strftime('%H:%M:%S')}] [{r['model']} / {r['style']}] {state}")
    if any(not r['done'] for r in runs):
        time.sleep(POLL_INTERVAL)

print("\nAll runs finished.")
