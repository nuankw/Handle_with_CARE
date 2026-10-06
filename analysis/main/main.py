"""
main_results.py — Main paper results for CARE.

  §5.1  Overall fidelity tables (attitude and tone metrics)
  §5.2  Community-level correlation figures
        - Attitude: level + swing  (vertical 2×1)
        - Tonal structure: diversity + pairwise JSD correlation (vertical 2×1)
  §5.3  Who benefits — community TEM_syn shift heatmaps (3×3 grid)

Output:
    results/   — figures (PDF + PNG) and CSVs
    stdout     — metric tables
"""
import sys, os, collections, itertools
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import scipy.stats as stats
import scipy.spatial.distance as dist

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from utils import (
    load_posts, CONDITIONS, LABEL, MODEL_CONDS, REF_CONDS,
    soft_tone_match, tone_to_L2_label, tone_exact_match,
    att_hit, tone_jsd, soft_tone_jsd,
)

# ============================================================
# SETUP
# ============================================================
OUTDIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")
os.makedirs(OUTDIR, exist_ok=True)

posts = load_posts()
N = len(posts)
print(f"Loaded {N} posts\n")

by_comm = collections.defaultdict(list)
for p in posts:
    by_comm[p["subreddit"]].append(p)
comms = sorted(list(by_comm.keys()))
n_comm = len(comms)

def spearman(x, y):
    return float(stats.spearmanr(x, y).correlation)

ALL_CONDS = MODEL_CONDS + REF_CONDS

# model / style split for table display
MODEL_STYLE = {
    "G1": ("2.5", "Blind"), "G2": ("2.5", "Informed"), "G3": ("2.5", "CoT"),
    "G4": ("3.1", "Blind"), "G5": ("3.1", "Informed"), "G6": ("3.1", "CoT"),
    "G7": ("Ref", "Random"), "G8": ("Ref", "50/50"),
    "G9": ("Ref", "25/75"),  "G10": ("Ref", "Top Reaction"),
}

# ============================================================
# §5.1  OVERALL FIDELITY — TABLES
# ============================================================
print("\n" + "=" * 70)
print("§5.1  OVERALL FIDELITY")
print("=" * 70)

# ---- Attitude metrics table ----
def attitude_metrics_row(posts, condition):
    real_avg = np.array([np.mean(p["real_atts"]) for p in posts])
    sim = np.array([p["sim_att"][condition] for p in posts])
    neg = [p for p in posts if p["negativity"] == "negative"]
    nonneg = [p for p in posts if p["negativity"] == "non-negative"]
    def me(subset):
        if not subset: return float("nan")
        s = np.array([p["sim_att"][condition] for p in subset])
        r = np.array([np.mean(p["real_atts"]) for p in subset])
        return float(np.mean(s - r))
    return {
        "att_hit": float(np.mean([att_hit(p["real_atts"], p["sim_att"][condition]) for p in posts])),
        "rmse": float(np.sqrt(np.mean((real_avg - sim) ** 2))),
        "me_negative": me(neg),
        "me_non-neg": me(nonneg),
        "spearman": spearman(real_avg, sim),
    }

att_rows = []
for cond in ALL_CONDS:
    m, s = MODEL_STYLE[cond]
    att_rows.append({"model": m, "style": s, **attitude_metrics_row(posts, cond)})
att_df = pd.DataFrame(att_rows)

print("\n--- Attitude Metrics Table ---")
print(att_df.to_string(index=False, float_format="{:.2f}".format))
att_df.to_csv(os.path.join(OUTDIR, "attitude_metrics.csv"), index=False)

# ---- Tone metrics table ----
def tone_metrics_row(posts, condition=None):
    if condition is None:
        counts = collections.Counter(t for p in posts for t in p["real_tones"])
        group_counts = collections.Counter(
            tone_to_L2_label(t) for p in posts for t in p["real_tones"])
    else:
        counts = collections.Counter(p["sim_tone"][condition] for p in posts)
        group_counts = collections.Counter(
            tone_to_L2_label(p["sim_tone"][condition]) for p in posts)

    n_tok = sum(counts.values())
    n_tok_syn = sum(group_counts.values())
    assert n_tok == n_tok_syn
    row = {}
    if condition is None:
        row["TEM"] = 1.0
        row["TEM_syn"] = 1.0
        row["JSD"] = 0.0
        row["JSD_syn"] = 0.0
    else:
        row["TEM"] = float(np.mean([
            tone_exact_match(p["real_tones"], p["sim_tone"][condition]) for p in posts]))
        row["TEM_syn"] = float(np.mean([
            soft_tone_match(p["real_tones"], p["sim_tone"][condition]) for p in posts]))
        row["JSD"] = tone_jsd(posts, condition)
        row["JSD_syn"] = soft_tone_jsd(posts, condition)

    row["n_unique"] = len(counts)
    row["n_syn_groups"] = len(group_counts)
    row["pct_sarcastic"] = 100.0 * counts.get("sarcastic", 0) / n_tok
    row["pct_sarcastic_syn"] = 100.0 * group_counts.get(tone_to_L2_label("sarcastic"), 0) / n_tok_syn
    return row

tone_rows = [{"model": "—", "style": "Real", **tone_metrics_row(posts)}]
for cond in ALL_CONDS:
    m, s = MODEL_STYLE[cond]
    tone_rows.append({"model": m, "style": s, **tone_metrics_row(posts, cond)})

tone_df = pd.DataFrame(tone_rows)[
    [
        "model", "style", 
        "TEM", "JSD", "n_unique", "pct_sarcastic", 
        "TEM_syn", "JSD_syn", "n_syn_groups", "pct_sarcastic_syn"
    ]
]

print("\n--- Tone Metrics Table ---")
pd.set_option("display.width", 200)
pd.set_option("display.max_columns", 20)
print(tone_df.to_string(index=False, float_format="{:.2f}".format))
tone_df.to_csv(os.path.join(OUTDIR, "tone_metrics.csv"), index=False)


# ============================================================
# §5.2  COMMUNITY-LEVEL CORRELATIONS
# ============================================================
print("\n" + "=" * 70)
print("§5.2  COMMUNITY-LEVEL CORRELATIONS")
print("=" * 70)

# ---- Attitude: level + swing ----
def per_comm_stat(fn, condition=None):
    return np.array([fn([(np.mean(p["real_atts"]) if condition is None else p["sim_att"][condition])
                         for p in by_comm[s]]) for s in comms])

real_level = per_comm_stat(np.mean)
real_swing = per_comm_stat(np.std)

level_corr = {}
swing_corr = {}
for cond in ALL_CONDS:
    level_corr[cond] = spearman(real_level, per_comm_stat(np.mean, cond))
    swing_corr[cond] = spearman(real_swing, per_comm_stat(np.std, cond))

print("\n--- Community-Level Attitude Correlations ---")
print(f"{'Cond':5s}  {'Label':20s}  {'level_ρ':>8s}  {'swing_ρ':>8s}")
for cond in ALL_CONDS:
    print(f"{cond:5s}  {LABEL[cond]:20s}  {level_corr[cond]:+8.2f}  {swing_corr[cond]:+8.2f}")


# ---- Figure: attitude correlations (horizontal 2×1) ----
fig, axes = plt.subplots(1, 2, figsize=(14, 6))
tab10 = plt.cm.tab10.colors
pal = [tab10[i] for i in range(6)]

# pal = ["#93c5fd", "#3b82f6", "#1d4ed8",
#        "#fdba74", "#f97316", "#c2410c"]

for ax, corr, title, xlim_upper in [
    (axes[0], swing_corr, "(a) Reproducing Community Attitudinal Swing", 0.65),
    (axes[1], level_corr, "(b) Reproducing Community Attitudinal Level", 0.85),
]:
    vals = [corr[cond] for cond in MODEL_CONDS]
    bars = ax.barh(range(len(MODEL_CONDS)), vals, color=pal, height=0.6,
                   edgecolor="none", zorder=3)
    ax.axvline(corr["G10"], ls="--", color="black", lw=1.2,
               label=f"top-reaction ceiling ({corr['G10']:.2f})")
    ax.set_yticks(range(len(MODEL_CONDS)))
    ax.set_yticklabels([LABEL[cond] for cond in MODEL_CONDS], fontsize=10, fontweight="bold")
    ax.invert_yaxis()
    ax.tick_params(axis="y", length=0, pad=5)
    ax.set_xlim(0, xlim_upper)
    ax.set_xticks(np.arange(0, xlim_upper, 0.1))
    ax.tick_params(axis="x", labelsize=7)
    ax.set_xlabel(f"Spearman ρ (real vs sim, {n_comm} communities)", fontsize=8)
    ax.set_title(title, fontsize=12, fontweight="bold")
    ax.legend(fontsize=8, loc="upper right")
    ax.grid(axis="x", color="#dddddd", lw=0.5, zorder=0)
    for i, v in enumerate(vals):
        ax.text(v + 0.01, i, f"{v:.2f}", va="center", fontsize=9)

fig.tight_layout(h_pad=2.0)
for ext in ["pdf", "png"]:
    fig.savefig(os.path.join(OUTDIR, f"comm_att_level_swing_corr.{ext}"),
                dpi=150, bbox_inches="tight")
print("\nwrote results/comm_att_level_swing_corr.pdf/.png")

# ---- Tonal structure: diversity + cross-community pairwise JSD ----
def per_comm_tone_diversity(condition=None):
    """Entropy of (L2-grouped) tone distribution per community."""
    out = []
    for c in comms:
        if condition is None:
            tones = [tone_to_L2_label(t) for p in by_comm[c] for t in p["real_tones"]]
        else:
            tones = [tone_to_L2_label(p["sim_tone"][condition]) for p in by_comm[c]]
        counts = collections.Counter(tones)
        n_tok = sum(counts.values())
        probs = np.array(list(counts.values()), float) / n_tok
        out.append(float(stats.entropy(probs)))
    return np.array(out)

# L2-grouped tone distribution vectors per community
all_group_labels = sorted(set(
    tone_to_L2_label(t) for p in posts for t in p["real_tones"]))

def comm_tone_vec(c, condition=None):
    """L2-grouped tone distribution vector for community c."""
    if condition is None:
        tones = [tone_to_L2_label(t) for p in by_comm[c] for t in p["real_tones"]]
    else:
        tones = [tone_to_L2_label(p["sim_tone"][condition]) for p in by_comm[c]]
    counts = collections.Counter(tones)
    v = np.array([counts.get(l, 0) for l in all_group_labels], float)
    s = v.sum()
    return v / s if s > 0 else v

def pairwise_jsd_vector(condition=None):
    """Condensed pairwise JSD vector across all community pairs (L2-grouped)."""
    vecs = [comm_tone_vec(c, condition) for c in comms]
    jsd_vec = []
    for i, j in itertools.combinations(range(n_comm), 2):
        jsd_vec.append(float(dist.jensenshannon(vecs[i], vecs[j], base=2)))
    return np.array(jsd_vec)

real_div = per_comm_tone_diversity()
real_jsd_vec = pairwise_jsd_vector()

# ---- Descriptive: spread of the real cross-community tonal distances ----
_q = np.percentile(real_jsd_vec, [5, 25, 50, 75, 95])
print(f"\n--- Real cross-community tonal distance ({real_jsd_vec.size} pairs) ---")
print(f"mean {real_jsd_vec.mean():.3f}   std {real_jsd_vec.std():.3f}   "
      f"min {real_jsd_vec.min():.3f}   max {real_jsd_vec.max():.3f}")
print(f"p5 {_q[0]:.3f}   q1 {_q[1]:.3f}   median {_q[2]:.3f}   "
      f"q3 {_q[3]:.3f}   p95 {_q[4]:.3f}")
pd.DataFrame([{
    "n_pairs": int(real_jsd_vec.size), "n_comm": n_comm,
    "mean": float(real_jsd_vec.mean()), "std": float(real_jsd_vec.std()),
    "min": float(real_jsd_vec.min()), "p5": float(_q[0]), "q1": float(_q[1]),
    "median": float(_q[2]), "q3": float(_q[3]), "p95": float(_q[4]),
    "max": float(real_jsd_vec.max()),
}]).to_csv(os.path.join(OUTDIR, "real_pairwise_jsd_stats.csv"), index=False)

div_corr = {}
jsd_struct_corr = {}
for cond in ALL_CONDS:
    div_corr[cond] = spearman(real_div, per_comm_tone_diversity(cond))
    jsd_struct_corr[cond] = spearman(real_jsd_vec, pairwise_jsd_vector(cond))

print("\n--- Community-Level Tonal Structure Correlations ---")
print(f"{'Cond':5s}  {'Label':20s}  {'div_ρ':>8s}  {'JSD_ρ':>8s}")
for cond in ALL_CONDS:
    print(f"{cond:5s}  {LABEL[cond]:20s}  {div_corr[cond]:+8.2f}  {jsd_struct_corr[cond]:+8.2f}")

# ---- Figure: tonal structure correlations (horizontal 2×1) ----
fig2, axes2 = plt.subplots(1, 2, figsize=(14, 6))

for ax, corr, title, xlim_upper, x_label_str in [
    (axes2[0], div_corr, "(a) Reproducing Community Tonal Diversity", 0.65, f"Spearman ρ (real vs sim, {n_comm} communities)"),
    (axes2[1], jsd_struct_corr, "(b) Reproducing Cross-community Tonal Structure", 0.45, f"Spearman ρ (real vs sim, {real_jsd_vec.size} community pairs)"),
]:
    vals = [corr[cond] for cond in MODEL_CONDS]
    bars = ax.barh(range(len(MODEL_CONDS)), vals, color=pal, height=0.6,
                   edgecolor="none", zorder=3)
    ax.axvline(corr["G10"], ls="--", color="black", lw=1.2,
               label=f"top-reaction ceiling ({corr['G10']:.2f})")
    ax.set_yticks(range(len(MODEL_CONDS)))
    ax.set_yticklabels([LABEL[cond] for cond in MODEL_CONDS], fontsize=10, fontweight="bold")
    ax.invert_yaxis()
    ax.tick_params(axis="y", length=0, pad=5)
    ax.set_xlim(0, xlim_upper)
    ax.set_xticks(np.arange(0, xlim_upper, 0.1))
    ax.tick_params(axis="x", labelsize=7)
    ax.set_xlabel(x_label_str, fontsize=9)
    ax.set_title(title, fontsize=12, fontweight="bold")
    ax.legend(fontsize=8, loc="upper right")
    ax.grid(axis="x", color="#dddddd", lw=0.5, zorder=0)
    for i, v in enumerate(vals):
        ax.text(v + 0.01, i, f"{v:.2f}", va="center", fontsize=9)

fig2.tight_layout(h_pad=2.0)
for ext in ["pdf", "png"]:
    fig2.savefig(os.path.join(OUTDIR, f"comm_tonal_structure_corr.{ext}"),
                 dpi=150, bbox_inches="tight")
print("wrote results/comm_tonal_structure_corr.pdf/.png")

# ============================================================
# §5.3  WHO BENEFITS — COMMUNITY TEM_syn SHIFT HEATMAPS (3×3)
# ============================================================
print("\n" + "=" * 70)
print("§5.3  WHO BENEFITS — COMMUNITY TEM_syn SHIFTS")
print("=" * 70)

# per-community TEM_syn for each condition
def per_comm_tem_syn(condition):
    out = []
    for c in comms:
        vals = [soft_tone_match(p["real_tones"], p["sim_tone"][condition]) for p in by_comm[c]]
        out.append(float(np.mean(vals)))
    return np.array(out)

comm_tem = {cond: per_comm_tem_syn(cond) for cond in MODEL_CONDS}

# 3×3 grid of comparisons
comparisons = [
    # Row 1: Within Gemini 2.5
    [("+name (2.5)",         "G1", "G2"),
     ("+CoT (2.5)",          "G2", "G3"),
     ("net: blind→CoT (2.5)","G1", "G3")],
    # Row 2: Within Gemini 3.1
    [("+name (3.1)",         "G4", "G5"),
     ("+CoT (3.1)",          "G5", "G6"),
     ("net: blind→CoT (3.1)","G4", "G6")],
    # Row 3: Cross-model
    [("2.5→3.1 (blind)",    "G1", "G4"),
     ("2.5→3.1 (informed)", "G2", "G5"),
     ("2.5→3.1 (CoT)",      "G3", "G6")],
]
row_labels = ["Within Gemini 2.5 Pro", "Within Gemini 3.1 Pro Prev.", "Cross-model"]

bin_edges = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0001]
bin_labels = ["≤.2", ".2–.4", ".4–.6", ".6–.8", ".8–1"]
n_bins = len(bin_labels)

fig3, axes3 = plt.subplots(3, 3, figsize=(14, 13))
# fig3.suptitle(f"Community EM_syn shifts ({n_comm} communities)\n",fontsize=13, y=0.98)

cmap_seq = plt.cm.Blues

for ri, row_comps in enumerate(comparisons):
    for ci, (title, cond_x, cond_y) in enumerate(row_comps):
        ax = axes3[ri, ci]
        x_vals = comm_tem[cond_x]
        y_vals = comm_tem[cond_y]

        # bin communities
        x_bin = np.digitize(x_vals, bin_edges) - 1
        y_bin = np.digitize(y_vals, bin_edges) - 1
        x_bin = np.clip(x_bin, 0, n_bins - 1)
        y_bin = np.clip(y_bin, 0, n_bins - 1)

        mat = np.zeros((n_bins, n_bins), int)
        for xi, yi in zip(x_bin, y_bin):
            mat[yi, xi] += 1  # row=y, col=x

        delta = float(np.mean(y_vals - x_vals))
        n_up = int(np.sum(y_vals > x_vals))
        n_down = int(np.sum(y_vals < x_vals))

        # plot
        max_val = max(mat.max(), 1)
        ax.imshow(mat, cmap=cmap_seq, vmin=0, vmax=max_val,
                  origin="lower", aspect="equal")

        # cell counts (skip zeros)
        for i in range(n_bins):
            for j in range(n_bins):
                if mat[i, j] > 0:
                    color = "white" if mat[i, j] > max_val * 0.6 else "black"
                    ax.text(j, i, str(mat[i, j]), ha="center", va="center",
                            fontsize=9, fontweight="bold", color=color)

        # diagonal
        ax.plot([-0.5, n_bins - 0.5], [-0.5, n_bins - 0.5],
                color="red", ls="--", lw=1, alpha=0.6)

        ax.set_xticks(range(n_bins))
        ax.set_xticklabels(bin_labels, fontsize=8)
        ax.set_yticks(range(n_bins))
        ax.set_yticklabels(bin_labels, fontsize=8)
        ax.set_xlabel(f"{LABEL[cond_x]}", fontsize=9)
        ax.set_ylabel(f"{LABEL[cond_y]}", fontsize=9)
        ax.set_title(f"{title}\nΔ={delta:+.3f}  ↑{n_up} ↓{n_down}",
                     fontsize=10)

    # row label on both right and left
    axes3[ri, 0].annotate(row_labels[ri], xy=(-0.25, 0.5),
                          xycoords="axes fraction", fontsize=11,
                          rotation=90, va="center", ha="center",
                          fontweight="bold")
    axes3[ri, 2].annotate(row_labels[ri], xy=(1.1, 0.5),
                          xycoords="axes fraction", fontsize=11,
                          rotation=-90, va="center", ha="center",
                          fontweight="bold")

fig3.tight_layout(rect=[0, 0, 0.95, 0.94])
for ext in ["pdf", "png"]:
    fig3.savefig(os.path.join(OUTDIR, f"comm_tem_syn_shifts.{ext}"),
                 dpi=150, bbox_inches="tight")
print("wrote results/comm_tem_syn_shifts.pdf/.png")

# also print the summary table
print("\n--- Community TEM_syn shift summary ---")
print(f"{'Comparison':30s}  {'Δ':>7s}  {'↑':>4s}  {'↓':>4s}")
for row_comps in comparisons:
    for title, cond_x, cond_y in row_comps:
        x_vals = comm_tem[cond_x]
        y_vals = comm_tem[cond_y]
        delta = float(np.mean(y_vals - x_vals))
        n_up = int(np.sum(y_vals > x_vals))
        n_down = int(np.sum(y_vals < x_vals))
        print(f"{title:30s}  {delta:+7.3f}  {n_up:4d}  {n_down:4d}")

print("\n✓ main_results.py done")
