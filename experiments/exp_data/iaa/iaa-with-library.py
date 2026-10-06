import argparse
import numpy as np
import pandas as pd
import krippendorff as kd
from irrCAC.raw import CAC

from basic_functions import CATS, RATERS, PAIRS, load, pct_pairwise, pct_all, fmt, section

# ------------------------------------------------------------------ helpers
# units -> pandas frame (subjects x raters), missing values as NaN, for irrCAC
def _frame(units, raters=RATERS):
    return pd.DataFrame(
        [[np.nan if u[r] is None else u[r] for r in raters] for u in units],
        columns=list(raters),
    )

# units -> numpy matrix (raters x subjects), missing as NaN, for the krippendorff package
def _matrix(units, raters=RATERS):
    return np.array(
        [[np.nan if u[r] is None else u[r] for u in units] for r in raters], dtype=float
    )

# pull (value, lo, hi) out of an irrCAC result dict
def _est(res):
    e = res["est"]
    lo, hi = e["confidence_interval"]
    return e["coefficient_value"], lo, hi

# ------------------------------------------------------------------ metrics
# alpha = 1 - observed disagreement / expected disagreement; the package has no CI
def kripp_alpha(units, raters=RATERS, metric="ordinal", cats=CATS):
    return kd.alpha(reliability_data=_matrix(units, raters),
                    level_of_measurement=metric, value_domain=list(cats))

# Gwet's AC1 (identity weights) / AC2 (weighted), with Gwet's own weight definitions
def gwet_ac(units, raters=RATERS, weights="identity", cats=CATS):
    return _est(CAC(_frame(units, raters), weights=weights, categories=list(cats)).gwet())

# Fleiss' kappa, nominal only
def fleiss_kappa(units, raters=RATERS, cats=CATS):
    return _est(CAC(_frame(units, raters), categories=list(cats)).fleiss())

# ------------------------------------------------------------------ report
# the four blocks are built as plain data; `table` does all the formatting
def report(units, title):
    f = _frame(units)
    out = [title, "=" * len(title), "",
           f"units = {len(units)}, CIs are irrCAC analytic intervals (not bootstrap)", ""]

    out += section(
        "Label distribution",
        ["value", "Annotator_1", "Annotator_2", "Annotator_3"],
        [[f"{c:g}"] + [int((f[r] == c).sum()) for r in RATERS] for c in reversed(CATS)]
        + [["(missing)"] + [int(f[r].isna().sum()) for r in RATERS]],
    )

    pairs = [(f"{a}-{b}",) + pct_pairwise(units, a, b) for a, b in PAIRS]
    out += section(
        "Percent agreement",
        ["pair", "agree", "n"],
        [[name, f"{pa:.1%}", n] for name, pa, n in pairs]
        + [["all three", f"{pct_all(units)[0]:.1%}", pct_all(units)[1]]],
    )

    metrics = [[f"Krippendorff alpha ({m})", fmt(kripp_alpha(units, RATERS, m)), "-", "krippendorff"]
               for m in ("ordinal", "interval", "nominal")]
    for label, w in [("AC2 (ordinal weights)", "ordinal"),
                     ("AC2 (quadratic weights)", "quadratic"),
                     ("AC2 (linear weights)", "linear"),
                     ("AC1 (nominal)", "identity")]:
        v, lo, hi = gwet_ac(units, RATERS, w)
        metrics.append([f"Gwet {label}", fmt(v), f"[{fmt(lo)}, {fmt(hi)}]", "irrCAC"])
    v, lo, hi = fleiss_kappa(units, RATERS)
    metrics.append(["Fleiss kappa (nominal)", fmt(v), f"[{fmt(lo)}, {fmt(hi)}]", "irrCAC"])
    out += section("Chance-corrected agreement (3 raters)",
                   ["metric", "value", "95% CI", "library"], metrics)
    return "\n".join(out)

# ------------------------------------------------------------------ main
def main():
    # argparse.ArgumentParser(description=__doc__.splitlines()[0]).parse_args()
    units = load()
    print(report(units, "CARE tone-eval agreement (library version)"))

if __name__ == "__main__":
    main()
