import json
from collections import defaultdict
import pandas as pd
import numpy as np
from scipy import stats
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.spatial.distance import jensenshannon
from scipy.stats import entropy
import random
import math

#----- Real Reaction Tones -----#
# Format: {subreddit: post_id: tone list}

real_tone_results = defaultdict(lambda: defaultdict(list))

real_tone_results_fp = "./exp_data/real_reactions/id_to_generated_tones.json"

with open(real_tone_results_fp, "r") as f:
    id_to_real_tones = json.load(f)
    for request_id, tone in id_to_real_tones.items():
        splits = request_id.split("_")
        assert splits[-2] == "REAL-TONE", f"Unexpected style in: {splits}"
        # "medicine_kbhejq_REAL-TONE_4": "apprehensive",
        # "China_Flu_ewqosg_REAL-TONE_0": "optimistic",
        subreddit = "_".join(splits[:-3])
        submission_id = splits[-3]
        real_tone_results[subreddit][submission_id].append(tone)
        # check index for once (empty comment handling...)
        # if len(real_tone_results[subreddit][submission_id]) != int(splits[-1]) + 1:
            # print(f"Unexpected index in: {splits}, current length: {len(real_tone_results[subreddit][submission_id])}, check if the comment is empty string")
            # all checked, the comment is indeed empty string, so the index is not continuous, but we can still use the existing tones for analysis
            # Unexpected index in: ['China', 'Flu', 'g71smi', 'REAL-TONE', '3'], current length: 3, check if the comment is empty string
            # Unexpected index in: ['China', 'Flu', 'g71smi', 'REAL-TONE', '4'], current length: 4, check if the comment is empty string
            # Unexpected index in: ['ottawa', 'hvvebs', 'REAL-TONE', '2'], current length: 2, check if the comment is empty string
            # Unexpected index in: ['ottawa', 'hvvebs', 'REAL-TONE', '3'], current length: 3, check if the comment is empty string
            # Unexpected index in: ['phoenix', 'faux22', 'REAL-TONE', '3'], current length: 3, check if the comment is empty string
            # Unexpected index in: ['phoenix', 'faux22', 'REAL-TONE', '4'], current length: 4, check if the comment is empty string
            # Unexpected index in: ['newjersey', 'eux6hr', 'REAL-TONE', '1'], current length: 1, check if the comment is empty string
            # Unexpected index in: ['newjersey', 'eux6hr', 'REAL-TONE', '2'], current length: 2, check if the comment is empty string
            # Unexpected index in: ['newjersey', 'eux6hr', 'REAL-TONE', '3'], current length: 3, check if the comment is empty string
            # Unexpected index in: ['newjersey', 'eux6hr', 'REAL-TONE', '4'], current length: 4, check if the comment is empty string
            # Unexpected index in: ['Detroit', 'jbweyu', 'REAL-TONE', '2'], current length: 2, check if the comment is empty string
            # Unexpected index in: ['Detroit', 'jbweyu', 'REAL-TONE', '3'], current length: 3, check if the comment is empty string
            # Unexpected index in: ['Detroit', 'jbweyu', 'REAL-TONE', '4'], current length: 4, check if the comment is empty string
            # Unexpected index in: ['sanfrancisco', 'jl2sjm', 'REAL-TONE', '1'], current length: 1, check if the comment is empty string
            # Unexpected index in: ['sanfrancisco', 'jl2sjm', 'REAL-TONE', '2'], current length: 2, check if the comment is empty string
            # Unexpected index in: ['SanJose', 'fll9kp', 'REAL-TONE', '3'], current length: 3, check if the comment is empty string
            # Unexpected index in: ['SanJose', 'fll9kp', 'REAL-TONE', '4'], current length: 4, check if the comment is empty string
            # Unexpected index in: ['newyorkcity', 'j7cpw9', 'REAL-TONE', '1'], current length: 1, check if the comment is empty string
            # Unexpected index in: ['newyorkcity', 'j7cpw9', 'REAL-TONE', '2'], current length: 2, check if the comment is empty string
            # Unexpected index in: ['newyorkcity', 'j7cpw9', 'REAL-TONE', '3'], current length: 3, check if the comment is empty string
            # Unexpected index in: ['newyorkcity', 'j7cpw9', 'REAL-TONE', '4'], current length: 4, check if the comment is empty string
            # Unexpected index in: ['brexit', 'in45gu', 'REAL-TONE', '4'], current length: 4, check if the comment is empty string
            # Unexpected index in: ['missouri', 'jascpj', 'REAL-TONE', '4'], current length: 4, check if the comment is empty string
            # Unexpected index in: ['Hamilton', 'icm3ec', 'REAL-TONE', '1'], current length: 1, check if the comment is empty string
            # Unexpected index in: ['Hamilton', 'icm3ec', 'REAL-TONE', '2'], current length: 2, check if the comment is empty string
            # Unexpected index in: ['Hamilton', 'icm3ec', 'REAL-TONE', '3'], current length: 3, check if the comment is empty string
            # Unexpected index in: ['Hamilton', 'icm3ec', 'REAL-TONE', '4'], current length: 4, check if the comment is empty string
            # Unexpected index in: ['NewOrleans', 'g0yoxc', 'REAL-TONE', '1'], current length: 1, check if the comment is empty string
            # Unexpected index in: ['NewOrleans', 'g0yoxc', 'REAL-TONE', '2'], current length: 2, check if the comment is empty string


#----- Simulated Reaction Tones -----#
    # Format: {model: style: subreddit: post_id: tone}

sim_tone_results = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(str))))
STYLES = {
    "COMM-INFORMED": "community-informed",
    "COMM-BLIND": "community-blind",
    "COMM-INFORMED-COT": "community-informed-cot"
}

### Gemini-2.5-pro
gemini_25_sim_tone_cot_results_fp = "./exp_data/sim_reactions/gemini-2.5-pro/tone_eval/id_to_tones.json"
with open(gemini_25_sim_tone_cot_results_fp, "r") as f:
    new_gemini_25_id_to_sim_tones = json.load(f)
    for request_id, tone in new_gemini_25_id_to_sim_tones.items():
        splits = request_id.split("_")
        assert splits[-2] == "SIM-TONE", f"Wrong task in: {splits}, double check the file path"
        # "medicine_kbhejq_SIM-TONE_COMM-INFORMED": "exasperated",
        # "China_Flu_ewqosg_SIM-TONE_COMM-INFORMED": "resigned",
        style = STYLES[splits[-1]]
        subreddit = "_".join(splits[:-3])
        submission_id = splits[-3]
        sim_tone_results["gemini-2.5-pro"][style][subreddit][submission_id] = tone

### Gemini-3.1-pro-preview
gemini_31_sim_tone_results_fp = "./exp_data/sim_reactions/gemini-3.1-pro-preview/tone_eval/id_to_tones.json"
with open(gemini_31_sim_tone_results_fp, "r") as f:
    new_gemini_31_id_to_sim_tones = json.load(f)
    for request_id, tone in new_gemini_31_id_to_sim_tones.items():
        splits = request_id.split("_")
        assert splits[-2] == "SIM-TONE", f"Wrong task in: {splits}, double check the file path"
        style = STYLES[splits[-1]]
        subreddit = "_".join(splits[:-3])
        submission_id = splits[-3]
        sim_tone_results["gemini-3.1-pro-preview"][style][subreddit][submission_id] = tone

### attitude results
attitude_scores = {
    "negative": -1,
    "neutral": 0,
    "positive": 1,
    "unsure/mixed": 0,
}

tone_mapped = pd.read_csv("./exp_data/tone_mapped.csv")
tone_attitude_dict = dict(zip(tone_mapped['tone'], tone_mapped['attitude']))

# # check that all appeared tones (both in real and simulated data) are covered and nothing else is in the mapping
# all_appeared_tones = set()
# for subreddit, submission_dict in real_tone_results.items():
#     for submission_id, tone_list in submission_dict.items():
#         all_appeared_tones.update(tone_list)
# for model, style_dict in sim_tone_results.items():
#     for style, subreddit_dict in style_dict.items():
#         for subreddit, submission_dict in subreddit_dict.items():
#             for submission_id, tone in submission_dict.items():
#                 all_appeared_tones.add(tone)

# # the mapping should not have any tone that is not in the appeared tones 
# # (this is caused by batch request and return mismatch, 
# # and previous v0 tones no longer appearing in the new v1 tone set)

# # tones to remove from the mapping
# print(f"No-show tones in existing tone_attitude_dict: {set(tone_attitude_dict.keys()) - all_appeared_tones}")
# tones_to_remove_from_ta_mappings = {'poignant', 'watchful', 'preachy', 'pastoral', 'decisive', 'trusting', 'abrupt', 'grudging', 'overwhelmed', 'prejudiced', 'silent', 'satisfied', 'pithy', 'forgiving', 'unclear', 'bawdy', 'sober', 'resilient', 'inspired', 'chauvinistic', 'wonkish', 'doubtful', 'automated', 'gracious', 'emotional', 'speechless', 'disparaging', 'prayerful', 'instructional', 'imperious', 'crude', 'opinionated', 'convinced', 'ranting', 'predictive', 'revolutionary'}

# tone_attitude_dict = {tone: attitude for tone, attitude in tone_attitude_dict.items() if tone not in tones_to_remove_from_ta_mappings}
# # two tones not labeled
# print(f"Unmapped tones in all data: {all_appeared_tones - set(tone_attitude_dict.keys())}")
# # Unmapped tones in all data: {'prophetic', 'deferential'}
# tone_attitude_dict['prophetic'] = 'neutral'
# tone_attitude_dict['deferential'] = 'positive'

# # save the new tone_mapped csv then comment out the above
# pd.DataFrame(list(tone_attitude_dict.items()), columns=['tone', 'attitude']).to_csv("./exp_data/tone_mapped.csv", index=False)
# exit()


real_attitude_results = defaultdict(lambda: defaultdict(lambda: defaultdict(dict))) # {subreddit: post_id: attitude(float) list}
for subreddit, submission_dict in real_tone_results.items():
    for submission_id, tone_list in submission_dict.items():
        assert all(tone in tone_attitude_dict for tone in tone_list), f"Unexpected tone in: {tone_list}"
        real_attitude_results[subreddit][submission_id] = [float(attitude_scores[tone_attitude_dict[tone]]) for tone in tone_list]

sim_attitude_results = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(float)))) # {model: style: subreddit: post_id: attitude(float)}
for model, style_dict in sim_tone_results.items():
    for style, subreddit_dict in style_dict.items():
        for subreddit, submission_dict in subreddit_dict.items():
            for submission_id, tone in submission_dict.items():
                sim_attitude_results[model][style][subreddit][submission_id] = float(attitude_scores[tone_attitude_dict[tone]])

random_tone_guesses     = defaultdict(lambda: defaultdict(str))   # {subreddit: post_id: random_tone_string}
random_attitude_guesses = defaultdict(lambda: defaultdict(float)) # {subreddit: post_id: random_mapped_attitude_float}
half_time_random_tone_guesses     = defaultdict(lambda: defaultdict(str))   # {subreddit: post_id: random or top reaction tone}
half_time_random_attitude_guesses = defaultdict(lambda: defaultdict(float)) # {subreddit: post_id: random or top reaction mapped attitude float}
quarter_time_random_tone_guesses     = defaultdict(lambda: defaultdict(str))   # {subreddit: post_id: random or top reaction tone}
quarter_time_random_attitude_guesses = defaultdict(lambda: defaultdict(float)) # {subreddit: post_id: random or top reaction mapped attitude float}
top_reaction_tone_as_guesses     = defaultdict(lambda: defaultdict(str))   # {subreddit: post_id: top reaction tone}
top_reaction_attitude_as_guesses = defaultdict(lambda: defaultdict(float)) # {subreddit: post_id: top reaction mapped attitude float}
all_appeared_tones = list(tone_attitude_dict.keys())

tone_rng = random.Random(1)
for subreddit, submission_dict in real_tone_results.items():
    for post_id in submission_dict:
        random_tone = tone_rng.choice(all_appeared_tones)
        random_tone_guesses[subreddit][post_id] = random_tone
        random_attitude_guesses[subreddit][post_id] = float(attitude_scores[tone_attitude_dict[random_tone]])

half_toss_rng = random.Random(2)
half_rng = random.Random(3)
for subreddit, submission_dict in real_tone_results.items():
    for post_id in submission_dict:
        if half_toss_rng.random() < 0.5:
            # random guess
            random_tone = half_rng.choice(all_appeared_tones)
            half_time_random_tone_guesses[subreddit][post_id] = random_tone
            half_time_random_attitude_guesses[subreddit][post_id] = float(attitude_scores[tone_attitude_dict[random_tone]])
        else:
            # top reaction tone
            top_reaction_tone = real_tone_results[subreddit][post_id][0]
            half_time_random_tone_guesses[subreddit][post_id] = top_reaction_tone
            half_time_random_attitude_guesses[subreddit][post_id] = float(attitude_scores[tone_attitude_dict[top_reaction_tone]])

quarter_toss_rng = random.Random(4)
quarter_rng = random.Random(5)
for subreddit, submission_dict in real_tone_results.items():
    for post_id in submission_dict:
        if quarter_toss_rng.random() < 0.25:
            # random guess
            random_tone = quarter_rng.choice(all_appeared_tones)
            quarter_time_random_tone_guesses[subreddit][post_id] = random_tone
            quarter_time_random_attitude_guesses[subreddit][post_id] = float(attitude_scores[tone_attitude_dict[random_tone]])
        else:
            # top reaction tone
            top_reaction_tone = real_tone_results[subreddit][post_id][0]
            quarter_time_random_tone_guesses[subreddit][post_id] = top_reaction_tone
            quarter_time_random_attitude_guesses[subreddit][post_id] = float(attitude_scores[tone_attitude_dict[top_reaction_tone]])

for subreddit, submission_dict in real_tone_results.items():
    for post_id in submission_dict:
        top_reaction_tone = real_tone_results[subreddit][post_id][0]
        top_reaction_tone_as_guesses[subreddit][post_id] = top_reaction_tone
        top_reaction_attitude_as_guesses[subreddit][post_id] = float(attitude_scores[tone_attitude_dict[top_reaction_tone]])

tone_results = {
    "real_tone_results": real_tone_results,                               # {subreddit: post_id: tone list}
    "sim_tone_results": sim_tone_results,                                 # {model: style: subreddit: post_id: tone}
    "random_tone_guesses": random_tone_guesses,                           # {subreddit: post_id: random_tone}
    "half_time_random_tone_guesses": half_time_random_tone_guesses,       # {subreddit: post_id: random or top reaction tone}
    "quarter_time_random_tone_guesses": quarter_time_random_tone_guesses, # {subreddit: post_id: random or top reaction tone}
    "top_reaction_tone_as_guesses": top_reaction_tone_as_guesses,         # {subreddit: post_id: top reaction tone}
}

attitude_results = {
    "real_attitude_results": real_attitude_results,                               # {subreddit: post_id: attitude(float) list}
    "sim_attitude_results": sim_attitude_results,                                 # {model: style: subreddit: post_id: attitude(float)}
    "random_attitude_guesses": random_attitude_guesses,                           # {subreddit: post_id: random_tone_mapped_attitude(float)}
    "half_time_random_attitude_guesses": half_time_random_attitude_guesses,       # {subreddit: post_id: random or top reaction attitude(float)}
    "quarter_time_random_attitude_guesses": quarter_time_random_attitude_guesses, # {subreddit: post_id: random or top reaction attitude(float)}
    "top_reaction_attitude_as_guesses": top_reaction_attitude_as_guesses,         # {subreddit: post_id: top reaction attitude(float)}
}


# Prep for non-overall analysis: looking into negative & non-negative tones/attitudes

submission_ids_negative = set()
submission_ids_non_negative = set()

for subreddit, submission_dict in real_attitude_results.items():
    for submission_id, attitude_list in submission_dict.items():
        if np.mean(attitude_list) < 0:
            submission_ids_negative.add(submission_id)
        else:
            submission_ids_non_negative.add(submission_id)

# Consider temporal and community's geo/topic info
# temporal_info: submission_id -> (month_str, season_in_int_1234)
temporal_info = defaultdict(tuple)
temp_info_from_sample_ids = json.load(open("./exp_data/all_sampled_ids.json", "r"))
# "worldnews": {
#     "2020-01": "em49fj",
#     "2020-02": "f2nbnk",
#     "2020-03": "fr6iya",
#     "2020-04": "g5s7mh",
#     "2020-05": "ghr7yv",
#     "2020-06": "hf39g6",
#     "2020-07": "hq38si",
#     "2020-08": "ifk5iv",
#     "2020-09": "ioyvjs",
#     "2020-10": "jb95bs",
#     "2020-11": "jxt8fp",
#     "2020-12": "khmly3"
# },
# ...

def get_season_from_month(yyyy_dash_mm):
    month = int(yyyy_dash_mm.split("-")[-1])
    if month in [1, 2, 3]:
        return "season_1"
    elif month in [4, 5, 6]:
        return "season_2"
    elif month in [7, 8, 9]:
        return "season_3"
    elif month in [10, 11, 12]:
        return "season_4"
    else:
        raise ValueError(f"Invalid month: {yyyy_dash_mm}")
    
for subreddit, month_dict in temp_info_from_sample_ids.items():
    for month, submission_id in month_dict.items():
        temporal_info[submission_id] = (month, get_season_from_month(month))

# comm_info: subreddit -> {"geopath": str, "topics": list of str}
comm_info = json.load(open("./exp_data/subreddits_geo_topic_info.json"))
# e.g. 
#     "AnythingGoesNews": {
#             "geopath": "GLOBAL",
#             "topics": [
#                 "SOCIAL_DISCUSSION_AND_THOUGHTS"
#             ],
#         },
#     "AusFinance": {
#         "geopath": "GLOBAL-OCEANIA-AUS",
#         "topics": [
#             "BUSINESS/ECONOMICS/FINANCE"
#         ]
#     },

comm_descriptions = json.load(open("./exp_data/subreddit_descriptions.json"))
#   "AnythingGoesNews": {
#     "url": "https://www.reddit.com/r/AnythingGoesNews/",
#     "description": "Reddit's (Almost) Anything Goes News Sub"
#   },

# all in one results
# format: {subreddit: {
#     "comm_info": {geopath: str, topics: list of str, description: str},
#     "<season_str>": {
#         "<month_str>": [
#             {
#                 "submission_id": post_id,
#                 "negativity": "negative" or "non-negative",
#                 "real_tones": list of str,
#                 "sim_tones": {
#                     model -> style -> tone
#                 },
#                 "real_attitudes": list of float,
#                 "sim_attitudes": {
#                     model -> style -> attitude
#                 }
#             }
#         ]
#     }
# }}

all_in_one_results = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))

sim_models = ["gemini-2.5-pro", "gemini-3.1-pro-preview"]
sim_styles = ["community-informed", "community-blind", "community-informed-cot"]
random_model = "/"
random_tone_styles = {
    "100-random-0-top": "random_tone_guesses",
    "50-random-50-top": "half_time_random_tone_guesses",
    "25-random-75-top": "quarter_time_random_tone_guesses",
    "0-random-100-top": "top_reaction_tone_as_guesses"
}
random_attitude_styles = {
    "100-random-0-top": "random_attitude_guesses",
    "50-random-50-top": "half_time_random_attitude_guesses",
    "25-random-75-top": "quarter_time_random_attitude_guesses",
    "0-random-100-top": "top_reaction_attitude_as_guesses"
}

for subreddit, post_dict in real_tone_results.items():
    comm_info[subreddit].update(
        {"description": comm_descriptions[subreddit]["description"]}
    )
    all_in_one_results[subreddit]["comm_info"] = comm_info[subreddit]
    for post_id, real_tone_list in post_dict.items():
        month, season = temporal_info[post_id]
        generated_tones = {model: {style: sim_tone_results[model][style][subreddit][post_id] for style in sim_styles} for model in sim_models}
        generated_tones[random_model] = {style: tone_results[orig_style_name][subreddit][post_id] for style, orig_style_name in random_tone_styles.items()}
        generated_attitudes = {model: {style: sim_attitude_results[model][style][subreddit][post_id] for style in sim_styles} for model in sim_models}
        generated_attitudes[random_model] = {style: attitude_results[orig_style_name][subreddit][post_id] for style, orig_style_name in random_attitude_styles.items()}
        all_in_one_results[subreddit][season][month].append(
            {
                "submission_id": post_id,
                "negativity": "negative" if post_id in submission_ids_negative else "non-negative",
                "real_tones": real_tone_list,
                "sim_tones": generated_tones,
                "real_attitudes": real_attitude_results[subreddit][post_id],
                "sim_attitudes": generated_attitudes
            }
        )
# sort all_in_one_results by subreddit names
all_in_one_results = dict(sorted(all_in_one_results.items(), key=lambda x: x[0]))

with open("./exp_data/all_in_one_results.json", "w") as f:
    json.dump(all_in_one_results, f, indent=4)
print("Saved all-in-one results to ./exp_data/all_in_one_results.json")


