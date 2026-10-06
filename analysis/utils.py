from collections import defaultdict
import json
import os

import numpy as np
import pandas as pd
import scipy.stats as stats
import scipy.spatial.distance as dist

# ---- Paths -------------------------------------------------------------------
BASE = os.path.dirname(os.path.abspath(__file__))
CARE_ROOT = os.path.join(BASE, '../..')
CAREV1 = os.path.join(CARE_ROOT, 'CAREv1')
EXP_DATA = os.path.join(CAREV1, 'experiments', 'exp_data')
RESULTS = os.path.join(EXP_DATA, 'all_in_one_results.json')

# ---- Load hierarchical synonym structure from JSON ---------------------------
with open(os.path.join(EXP_DATA, 'tone_hierarchical_synonyms.json')) as _f:
    _HIER_ALL = json.load(_f)

HIERARCHICAL_NEGATIVE_TONES = _HIER_ALL["NEGATIVE"]
HIERARCHICAL_POSITIVE_TONES = _HIER_ALL["POSITIVE"]
HIERARCHICAL_NEUTRAL_TONES = _HIER_ALL["NEUTRAL"]
HIERARCHICAL_UNSURE_MIXED_TONES = _HIER_ALL["MIXED"]

# ---- L2 groups (flattened from hierarchical lookup) -------------------------
TONE_L2_GROUPS = {}   # L2 group name → list of synonym tones
for _hier in (HIERARCHICAL_NEGATIVE_TONES, HIERARCHICAL_POSITIVE_TONES,
              HIERARCHICAL_NEUTRAL_TONES, HIERARCHICAL_UNSURE_MIXED_TONES):
    for _cat in _hier.values():              # L1 categories
        for _l2_name, _tones in _cat.items():  # L2 groups
            if _tones:  # skip empty groups
                TONE_L2_GROUPS[_l2_name] = _tones

_tone_to_L2 = {}   # individual tone → L2 group name
for _l2_name, _tones in TONE_L2_GROUPS.items():
    for _tone in _tones:
        if _tone in _tone_to_L2:
            raise ValueError(
                f"Tone '{_tone}' in L2 group '{_l2_name}' already in '{_tone_to_L2[_tone]}'")
        _tone_to_L2[_tone] = _l2_name


def soft_tone_match(real_tones, sim_tone):
    """1.0 if sim_tone exactly matches or is in the same L2 group as any real tone."""
    if sim_tone in real_tones:
        return 1.0
    sim_l2 = _tone_to_L2.get(sim_tone)
    if sim_l2 is not None:
        for rt in real_tones:
            if _tone_to_L2.get(rt) == sim_l2:
                return 1.0
    return 0.0


def get_L2_synonyms(tone):
    """Return the list of synonym tones in the same L2 group, or None."""
    l2 = _tone_to_L2.get(tone)
    if l2 is not None:
        return TONE_L2_GROUPS[l2]
    return None


def tone_to_L2_label(tone):
    """Map a tone to its L2 group name, or itself if ungrouped."""
    return _tone_to_L2.get(tone, tone)


def get_all_L2_labels(tones):
    """Given a collection of tones, return sorted unique L2 group labels."""
    return sorted(set(tone_to_L2_label(t) for t in tones))


def L2_tone_counts(tones):
    """Count tones collapsed by L2 group. Returns {L2_label: count}."""
    from collections import Counter
    counts = Counter()
    for t in tones:
        counts[tone_to_L2_label(t)] += 1
    return dict(counts)


SEASONS = ["season_1", "season_2", "season_3", "season_4"]

CONDITIONS = {
    "G1":  ("gemini-2.5-pro",         "community-blind"),
    "G2":  ("gemini-2.5-pro",         "community-informed"),
    "G3":  ("gemini-2.5-pro",         "community-informed-cot"),
    "G4":  ("gemini-3.1-pro-preview", "community-blind"),
    "G5":  ("gemini-3.1-pro-preview", "community-informed"),
    "G6":  ("gemini-3.1-pro-preview", "community-informed-cot"),
    "G7":  ("/",                      "100-random-0-top"),
    "G8":  ("/",                      "50-random-50-top"),
    "G9":  ("/",                      "25-random-75-top"),
    "G10": ("/",                      "0-random-100-top"),
}


LABEL = {"G1": "[2.5] Comm-Blind", "G2": "[2.5] Comm-Informed", "G3": "[2.5] Comm-Inf.-CoT",
         "G4": "[3.1] Comm-Blind", "G5": "[3.1] Comm-Informed", "G6": "[3.1] Comm-Inf.-CoT",
         "G7": "Random", "G8": "50/50", "G9": "25/75", "G10": "Top Reaction"}
MODEL_CONDS = ["G1", "G2", "G3", "G4", "G5", "G6"]   # the real ones
REF_CONDS = ["G7", "G8", "G9", "G10"]                # random -> top ladder


def load_posts(path=RESULTS):
    raw = json.load(open(path))
    posts = []
    for sub, d in raw.items():
        info = d["comm_info"]
        topic = (info.get("topics") or ["NONE"])[0]
        for season in SEASONS:
            for month, plist in d.get(season, {}).items():
                for p in plist:
                    row = dict(
                        subreddit=sub, month=month, season=season, topic=topic,
                        geopath=info["geopath"], negativity=p["negativity"],
                        submission_id=p["submission_id"],
                        real_tones=list(p["real_tones"]),
                        real_atts=[float(a) for a in p["real_attitudes"]],
                        sim_tone={}, sim_att={},
                    )
                    for cond, (m, s) in CONDITIONS.items():
                        row["sim_tone"][cond] = p["sim_tones"][m][s]
                        row["sim_att"][cond] = float(p["sim_attitudes"][m][s])
                    posts.append(row)
    return posts

def count_reactions(posts):
    """Count the number of posts with each reaction type."""
    counts = defaultdict(int)
    for p in posts:
        counts[p["negativity"]] += len(p["real_tones"])
    return dict(counts)

# ---- per-post metrics -----------------------------------------------------
def att_hit(real_atts, sim_att):
    return float(np.mean(np.asarray(real_atts) == sim_att))


def tone_exact_match(real_tones, sim_tone):
    return 1.0 if sim_tone in real_tones else 0.0


# ---- pooled/aggregate metrics for a set of posts --------------------------

def js_distance(p, q):
    return float(dist.jensenshannon(p, q, base=2))

def soft_tone_jsd(posts, condition):
    """JSD between real and sim tone distributions, with L2 groups collapsed."""
    all_tones_raw = set(t for p in posts for t in p["real_tones"]) | \
                    set(p["sim_tone"][condition] for p in posts)
    all_labels = sorted(set(tone_to_L2_label(t) for t in all_tones_raw))
    rc = {l: 0 for l in all_labels}
    sc = {l: 0 for l in all_labels}
    for p in posts:
        for t in p["real_tones"]:
            rc[tone_to_L2_label(t)] += 1
        sc[tone_to_L2_label(p["sim_tone"][condition])] += 1
    rd = np.array([rc[l] for l in all_labels], float)
    sd = np.array([sc[l] for l in all_labels], float)
    return js_distance(rd, sd)

def tone_jsd(posts, condition):
    real_set = set(t for p in posts for t in p["real_tones"])
    all_t = sorted(real_set | set(p["sim_tone"][condition] for p in posts))
    rc = {t: 0 for t in all_t}
    sc = {t: 0 for t in all_t}
    for p in posts:
        for t in p["real_tones"]:
            rc[t] += 1
        sc[p["sim_tone"][condition]] += 1
    rd = np.array([rc[t] for t in all_t], float)
    sd = np.array([sc[t] for t in all_t], float)
    return js_distance(rd, sd)

def spearman(x, y):
    return float(stats.spearmanr(x, y).correlation)

def me_by_negativity(posts, condition):
    def me(subset):
        if not subset:
            return float("nan")
        sim = np.array([p["sim_att"][condition] for p in subset])
        real_avg = np.array([np.mean(p["real_atts"]) for p in subset])
        return float(np.mean(sim - real_avg))
    return {
        # "me_all":          me(posts),
        "me_negative":     me([p for p in posts if p["negativity"] == "negative"]),
        "me_non-neg": me([p for p in posts if p["negativity"] == "non-negative"]),
    }


def tone_metrics_overall(posts, condition):
    counts = defaultdict(int)
    for p in posts:
        counts[p["sim_tone"][condition]] += 1
    n = sum(counts.values())
    probs = np.array(list(counts.values()), float) / n
    return dict(
        exact_match=float(np.mean([tone_exact_match(p["real_tones"], p["sim_tone"][condition]) for p in posts])),
        soft_exact_match=float(np.mean([soft_tone_match(p["real_tones"], p["sim_tone"][condition]) for p in posts])),
        jsd=tone_jsd(posts, condition),
        soft_jsd=soft_tone_jsd(posts, condition),
        n_unique=len(counts),
        entropy=stats.entropy(probs),
        pct_sarcastic=100.0 * counts.get("sarcastic", 0) / n,
    )


def attitude_metrics_overall(posts, condition):
    real_avg = np.array([np.mean(p["real_atts"]) for p in posts])
    sim = np.array([p["sim_att"][condition] for p in posts])
    return dict(
        att_hit=float(np.mean([att_hit(p["real_atts"], p["sim_att"][condition]) for p in posts])),
        rmse=float(np.sqrt(np.mean((real_avg - sim) ** 2))),
        **me_by_negativity(posts, condition),
        spearman=spearman(real_avg, sim),
    )


def tone_metrics_real(posts):
    counts = defaultdict(int)
    for p in posts:
        for t in p["real_tones"]:
            counts[t] += 1
    n = sum(counts.values())
    probs = np.array(list(counts.values()), float) / n
    return dict(
        exact_match=1.0, soft_exact_match=1.0,
        jsd=0.0, soft_jsd=0.0,
        n_unique=len(counts),
        entropy=stats.entropy(probs),
        pct_sarcastic=100.0 * counts.get("sarcastic", 0) / n,
    )


def tone_metrics_table(posts, conds=None):
    conds = MODEL_CONDS if conds is None else conds
    rows = [{"condition": "real", **tone_metrics_real(posts)}]
    rows += [{"condition": f"{cond}  {LABEL[cond]}", **tone_metrics_overall(posts, cond)} for cond in conds]
    return pd.DataFrame(rows)


def attitude_metrics_table(posts, conds=None):
    conds = list(CONDITIONS) if conds is None else conds
    rows = [{"condition": f"{cond}  {LABEL[cond]}", **attitude_metrics_overall(posts, cond)} for cond in conds]
    return pd.DataFrame(rows)
