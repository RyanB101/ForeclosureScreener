"""Merge city-sale ZIP stats, HUD Small Area FMRs and the auction list into
one ZIP market table with a suggested play per ZIP.

Usage:
    python build_zip_market.py --stats zip_stats.csv --rents zip_rents_fy27_safmr.csv \
        --auction-csv nov3_2026_auction_parcels.csv --out zip_market.csv
"""
import argparse
import csv
from collections import Counter, defaultdict

# The flip question is whether a renovated house sells high enough to clear a
# blind rehab, a year-plus of carry and a $50k profit. The ZIP's 75th
# percentile sale is a rough stand-in for renovated value.
FLIP_MIN_P75 = 250_000
FLIP_MAX_P75 = 450_000
HOLD_MIN_GROSS_YIELD = 0.14


def play(p75, gross_yield):
    if p75 and p75 > FLIP_MAX_P75:
        return "Flip, likely above $300k all-in (exceptional deals only)"
    if p75 and p75 >= FLIP_MIN_P75:
        return "Flip (core of buy box)"
    if gross_yield and gross_yield >= HOLD_MIN_GROSS_YIELD:
        return "Hold / BRRRR (flip margins thin)"
    return "Hold, or flip on the better blocks"


def num(x):
    return float(x) if x not in ("", None) else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stats", required=True)
    ap.add_argument("--rents", required=True)
    ap.add_argument("--auction-csv", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    with open(a.stats) as f:
        stats = {r["zip"]: r for r in csv.DictReader(f)}
    with open(a.rents) as f:
        rents = {r["zip"]: r for r in csv.DictReader(f)}
    with open(a.auction_csv) as f:
        parcels = list(csv.DictReader(f))
    counts = Counter(p["ZIP"] for p in parcels)
    lots = defaultdict(set)
    for p in parcels:
        lots[p["ZIP"]].add(p["Auction ID"])

    out = []
    for z, n in counts.most_common():
        s, r = stats.get(z, {}), rents.get(z, {})
        med, p75 = num(s.get("median_price_last_12m")), num(s.get("p75_price_last_12m"))
        rent3 = num(r.get("safmr_3br"))
        gy = round(12 * rent3 / med, 3) if med and rent3 else None
        out.append({
            "zip": z,
            "parcels_on_list": n,
            "lots_on_list": len(lots[z]),
            "sales_last_12m": s.get("sales_last_12m"),
            "median_price_last_12m": s.get("median_price_last_12m"),
            "p25_price_last_12m": s.get("p25_price_last_12m"),
            "p75_price_last_12m": s.get("p75_price_last_12m"),
            "price_yoy_pct": s.get("price_yoy_pct"),
            "median_ppsf_last_12m": s.get("median_ppsf_last_12m"),
            "ppsf_yoy_pct": s.get("ppsf_yoy_pct"),
            "safmr_2br": r.get("safmr_2br"),
            "safmr_3br": r.get("safmr_3br"),
            "gross_yield_3br_at_median": gy,
            "suggested_play": play(p75, gy),
        })
    with open(a.out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0].keys()))
        w.writeheader()
        w.writerows(out)
    print(f"{len(out)} ZIPs -> {a.out}")


if __name__ == "__main__":
    main()
