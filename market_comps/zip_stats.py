"""ZIP-level market stats from a sales CSV made by pull_sales.py.

Resales only (new construction excluded). For each ZIP: sale count, median price and $/sqft for the last 12 months,
the prior 12 months, and the year-over-year change.

Usage:
    python zip_stats.py sales.csv --asof 2026-10-20 --out zip_stats.csv
"""
import argparse
import csv
import datetime as dt
import statistics
from collections import defaultdict


def median(xs):
    return round(statistics.median(xs)) if xs else ""


def pct(a, b):
    return round((a / b - 1) * 100, 1) if a and b else ""


def stats(rows, asof):
    cut1 = asof - dt.timedelta(days=365)
    cut2 = asof - dt.timedelta(days=730)
    by = defaultdict(lambda: {"p1": [], "p2": [], "s1": [], "s2": []})
    for r in rows:
        d = dt.date.fromisoformat(r["sale_date"][:10])
        k = "1" if d >= cut1 else "2" if d >= cut2 else None
        if not k or r.get("new_build"):
            continue
        b = by[r["zip_code"]]
        b["p" + k].append(float(r["price"]))
        if r["price_per_sqft"]:
            b["s" + k].append(float(r["price_per_sqft"]))
    out = []
    for z, b in sorted(by.items()):
        m1, m2 = median(b["p1"]), median(b["p2"])
        s1, s2 = median(b["s1"]), median(b["s2"])
        out.append({
            "zip": z,
            "sales_last_12m": len(b["p1"]),
            "median_price_last_12m": m1,
            "median_price_prior_12m": m2,
            "price_yoy_pct": pct(m1, m2),
            "median_ppsf_last_12m": s1,
            "median_ppsf_prior_12m": s2,
            "ppsf_yoy_pct": pct(s1, s2),
            "p25_price_last_12m": round(statistics.quantiles(b["p1"], n=4)[0]) if len(b["p1"]) >= 4 else "",
            "p75_price_last_12m": round(statistics.quantiles(b["p1"], n=4)[2]) if len(b["p1"]) >= 4 else "",
        })
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("sales_csv")
    ap.add_argument("--asof", default=dt.date.today().isoformat())
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    with open(a.sales_csv) as f:
        rows = list(csv.DictReader(f))
    out = stats(rows, dt.date.fromisoformat(a.asof))
    with open(a.out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0].keys()))
        w.writeheader()
        w.writerows(out)
    print(f"{len(out)} ZIPs -> {a.out}")


if __name__ == "__main__":
    main()
