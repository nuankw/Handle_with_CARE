import json
from collections import defaultdict
import random
random.seed(42)

fetched_samples_path = "../../CAREv0/reaction_tone_to_attitude/batch_round/sampled_batch_data.jsonl"
fetched_samples = defaultdict(lambda: defaultdict(str)) # subreddit -> month -> post_id

with open(fetched_samples_path, 'r') as f:
    for line in f:
        sample = json.loads(line)
        fetched_samples[sample["subreddit"]][sample["submission_date"][:7]] = sample["submission_id"]

all_data_path = "../../CAREv0/reaction_tone_to_attitude/comm_reactions.json"
with open(all_data_path, 'r') as f:
    all_data = json.load(f)
    subr_2_monthly_subm_ids = all_data["subr_2_monthly_subm_ids"]
    subm_id_2_entry         = all_data["subm_id_2_entry"]

months = ["2020-01", "2020-02", "2020-03", "2020-04", "2020-05", "2020-06", "2020-07", "2020-08", "2020-09", "2020-10", "2020-11", "2020-12"]
all_sample_ids = defaultdict(lambda: defaultdict(str)) # subreddit -> month -> post_id
for subreddit in subr_2_monthly_subm_ids:
    for month in months:
        if month in subr_2_monthly_subm_ids[subreddit] and month not in fetched_samples[subreddit]:
            all_monthly_subm_ids = subr_2_monthly_subm_ids[subreddit][month]
            assert len(all_monthly_subm_ids) > 0, f"No submission IDs found for subreddit {subreddit} in month {month}"
            # Randomly sample one submission ID from the list of all submission IDs for that subreddit and month
            sampled_subm_id = random.choice(all_monthly_subm_ids)
            all_sample_ids[subreddit][month] = sampled_subm_id
        elif month in fetched_samples[subreddit]:
            all_sample_ids[subreddit][month] = fetched_samples[subreddit][month]

# save the sampled ids
json.dump(all_sample_ids, open("../data/all_sampled_ids.json", "w"), indent=4)

sampled_batch_data = []
for subreddit in all_sample_ids:
    for month in all_sample_ids[subreddit]:
        subm_id = all_sample_ids[subreddit][month]
        entry = subm_id_2_entry[subm_id]
        new_entry = {}
        for field in ['subreddit', 'submission_date', 'news_title', 'news_content', 'reactions']:
            assert field in entry, f"Field '{field}' not found in entry for submission ID {subm_id}"
            new_entry[field] = entry[field]
        new_entry['submission_id'] = subm_id
        # select_reaction_idx = random.randint(0, len(entry['reactions']) - 1)
        # new_entry['selected_reaction_idx'] = select_reaction_idx
        # new_entry['selected_reaction'] = entry['reactions'][select_reaction_idx]
        sampled_batch_data.append(new_entry)

# save the sampled batch data
with open("../data/sampled_batch_data.jsonl", "w") as f:
    for entry in sampled_batch_data:
        f.write(json.dumps(entry) + "\n")