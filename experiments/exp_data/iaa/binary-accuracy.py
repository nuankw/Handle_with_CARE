"""
Binary accuracy and agreement for CARE tone-eval scores.

Binary: 1 and 0 count as correct, -0.5 and -1 as incorrect.

"""
import argparse
import numpy as np
import pandas as pd
import krippendorff as kd
from irrCAC.raw import CAC
from statsmodels.stats.proportion import proportion_confint

from basic_functions import RATERS, PAIRS, load, pct_pairwise, pct_all, fmt, section

INCORRECT, CORRECT = 0.0, 1.0
CATS = [INCORRECT, CORRECT]

# ------------------------------------------------------------------ helpers
# units -> pandas frame (subjects x raters), for irrCAC
def _frame(units, raters=RATERS):
    return pd.DataFrame([[u[r] for r in raters] for u in units], columns=list(raters))

# units -> numpy matrix (raters x subjects), for the krippendorff package
def _matrix(units, raters=RATERS):
    return np.array([[u[r] for u in units] for r in raters], dtype=float)

# pull (value, lo, hi) out of an irrCAC result dict
def _est(res):
    e = res["est"]
    lo, hi = e["confidence_interval"]
    return e["coefficient_value"], lo, hi

# ------------------------------------------------------------------ binary view
# collapse the four-level score: an acceptable label (1 or 0) counts as correct
def binarize(units):
    return [{**u, **{r: (CORRECT if u[r] in (1.0, 0.0) else INCORRECT) for r in RATERS}}
            for u in units]

# a row is correct when at least two of the three raters called it correct
def majority(units):
    return [sum(u[r] for r in RATERS) >= 2 for u in units]

# ------------------------------------------------------------------ metrics
def kripp_alpha(units, raters=RATERS):
    return kd.alpha(reliability_data=_matrix(units, raters),
                    level_of_measurement="nominal", value_domain=CATS)

def gwet_ac1(units, raters=RATERS):
    return _est(CAC(_frame(units, raters), categories=CATS).gwet())

def fleiss_kappa(units, raters=RATERS):
    return _est(CAC(_frame(units, raters), categories=CATS).fleiss())

# ------------------------------------------------------------------ report
def report(units, title):
    b = binarize(units)
    f = _frame(b)
    maj = majority(b)
    n, hits = len(b), sum(maj)
    lo, hi = proportion_confint(hits, n, method="wilson")
    bad = [u["row"] for u, m in zip(b, maj) if not m]

    out = [title, "=" * len(title), "",
           f"units = {n}, 1 and 0 = correct, -0.5 and -1 = incorrect", ""]

    out += section(
        "Majority-vote accuracy (how GPT-5's picks scored)",
        ["quantity", "value"],
        [["rows", n],
         ["correct by majority", hits],
         ["accuracy", fmt(hits / n)],
         ["95% CI (Wilson)", f"[{fmt(lo)}, {fmt(hi)}]"],
         ["rows voted incorrect", ", ".join(str(r) for r in bad)]],
    )

    out += section(
        "Label distribution",
        ["value", "Annotator_1", "Annotator_2", "Annotator_3"],
        [[name] + [int((f[r] == v).sum()) for r in RATERS]
         for name, v in [("correct", CORRECT), ("incorrect", INCORRECT)]],
    )

    pairs = [(f"{a}-{b_}",) + pct_pairwise(b, a, b_) for a, b_ in PAIRS]
    out += section(
        "Percent agreement",
        ["pair", "agree", "n"],
        [[name, f"{pa:.1%}", cnt] for name, pa, cnt in pairs]
        + [["all three", f"{pct_all(b)[0]:.1%}", pct_all(b)[1]]],
    )

    v, lo, hi = gwet_ac1(b)
    metrics = [["Gwet AC1", fmt(v), f"[{fmt(lo)}, {fmt(hi)}]", "irrCAC"]]
    v, lo, hi = fleiss_kappa(b)
    metrics.append(["Fleiss kappa", fmt(v), f"[{fmt(lo)}, {fmt(hi)}]", "irrCAC"])
    metrics.append(["Krippendorff alpha", fmt(kripp_alpha(b)), "-", "krippendorff"])
    out += section(
        "Chance-corrected agreement (3 raters)",
        ["metric", "value", "95% CI", "library"], metrics,
    )
    return "\n".join(out)

# ------------------------------------------------------------------ main
def main():
    argparse.ArgumentParser(description=__doc__.splitlines()[0]).parse_args()
    print(report(load(), "CARE tone-eval binary accuracy"))

if __name__ == "__main__":
    main()
