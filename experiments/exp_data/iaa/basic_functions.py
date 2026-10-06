import csv, math, re
from pathlib import Path

CATS = [-1.0, -0.5, 0.0, 1.0]   # ordinal, the order is what alpha and the weights use
RATERS = ["Annotator_1", "Annotator_2", "Annotator_3"]
PAIRS = [("Annotator_1", "Annotator_2"), ("Annotator_2", "Annotator_3"), ("Annotator_1", "Annotator_3")]

# Resolved against this file, so the scripts run from any directory.
CSV_PATH = Path(__file__).resolve().parent / "data" / "labels.csv"


# read labels.csv into [{row, id, Annotator_1, Annotator_2, Annotator_3}, ...]; a blank cell stays None (missing)
def load(path=CSV_PATH):
    units = []
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            r = int(row["sheet_row"])
            u = {
                "row": r, "id": row["id"],
                "Annotator_1": float(row["Annotator_1"]),
                "Annotator_2": float(row["Annotator_2"]),
                "Annotator_3": float(row["Annotator_3"]) if row["Annotator_3"] != "" else None,
            }
            for k in RATERS:
                if u[k] is not None and u[k] not in CATS:
                    raise SystemExit(f"unexpected value {u[k]!r} in {k} at sheet_row {r}")
            units.append(u)
    return units


# share of units where raters a and b gave exactly the same value (no chance correction)
def pct_pairwise(units, a, b):
    n = agree = 0
    for u in units:
        if u.get(a) is None or u.get(b) is None: continue
        n += 1; agree += (u[a] == u[b])
    return (agree / n if n else float("nan")), n


# share of units where every rater gave exactly the same value (no chance correction)
def pct_all(units, raters=RATERS):
    n = agree = 0
    for u in units:
        vals = [u.get(x) for x in raters]
        if any(v is None for v in vals): continue
        n += 1; agree += len(set(vals)) == 1
    return (agree / n if n else float("nan")), n


# 3 decimals, or "nan" when a coefficient is undefined for the given data
def fmt(v):
    return "nan" if math.isnan(v) else f"{v:.3f}"


# fixed-width text table; columns holding only numbers are right-aligned
def table(headers, rows):
    cols = list(zip(*([headers] + rows)))
    width = [max(len(str(c)) for c in col) for col in cols]
    right = [all(re.fullmatch(r"-?[\d.]+%?|-|nan", str(c)) for c in col[1:]) for col in cols]
    def line(cells):
        return "  ".join(str(c).rjust(width[i]) if right[i] else str(c).ljust(width[i])
                         for i, c in enumerate(cells)).rstrip()
    return "\n".join([line(headers), "  ".join("-" * w for w in width)]
                     + [line(r) for r in rows])


# one section = a heading plus its table
def section(heading, headers, rows):
    return [heading, table(headers, rows), ""]
