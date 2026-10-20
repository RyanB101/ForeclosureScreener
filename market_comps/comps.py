"""Sold-comp values for auction properties: as-is value and after-repair value.

We can't see inside sheriff-sale houses, so values come from the spread of
nearby sold $/sqft rather than condition-matched comps:

  * as-is value = 25th percentile $/sqft of comps x subject sqft
  * market value = median $/sqft x subject sqft
  * ARV          = 80th percentile $/sqft x subject sqft (renovated sales
                   cluster at the top of a block's range)

Comps are same-category sales within a radius that widens (0.35 -> 0.5 ->
0.75 -> 1.0 mi) until at least MIN_COMPS are found, with living area within
+/-35% of the subject when the subject's size is known.

Usage:
    python comps.py --sales sales.csv --subjects shortlist.csv --out values.csv
The subjects CSV needs an OPA column (named "OPA" or "opa").
"""
import argparse
import csv
import datetime as dt
import math
import statistics

from carto import query, sql_list

RADII_MI = (0.35, 0.5, 0.75, 1.0)
MIN_COMPS = 6
MAX_AGE_DAYS = 548  # 18 months
SIZE_BAND = 0.35

SUBJECT_SQL = """
SELECT parcel_number AS opa, location, zip_code, category_code_description AS category,
       building_code_description AS building, total_livable_area AS sqft,
       total_area AS lot_sqft, number_of_bedrooms AS beds, number_of_bathrooms AS baths,
       year_built, exterior_condition, interior_condition, market_value,
       sale_date, sale_price, zoning, ST_Y(the_geom) AS lat, ST_X(the_geom) AS lng
FROM opa_properties_public WHERE parcel_number IN ({opas})
"""


def miles(lat1, lng1, lat2, lng2):
    r = 3958.8
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lng2 - lng1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def pctile(xs, q):
    xs = sorted(xs)
    if len(xs) == 1:
        return xs[0]
    i = (len(xs) - 1) * q
    lo, hi = math.floor(i), math.ceil(i)
    return xs[lo] + (xs[hi] - xs[lo]) * (i - lo)


def find_comps(subj, sales, asof):
    if not subj.get("lat"):
        return [], None
    slat, slng = float(subj["lat"]), float(subj["lng"])
    ssq = float(subj.get("sqft") or 0)
    cand = []
    for s in sales:
        if s["opa"] == subj["opa"] or not s["price_per_sqft"] or not s["lat"]:
            continue
        if s["category"] != subj["category"]:
            continue
        if (asof - dt.date.fromisoformat(s["sale_date"][:10])).days > MAX_AGE_DAYS:
            continue
        if ssq > 300 and abs(float(s["sqft"]) / ssq - 1) > SIZE_BAND:
            continue
        d = miles(slat, slng, float(s["lat"]), float(s["lng"]))
        cand.append((d, s))
    for r in RADII_MI:
        comps = [(d, s) for d, s in cand if d <= r]
        if len(comps) >= MIN_COMPS:
            return comps, r
    return [(d, s) for d, s in cand if d <= RADII_MI[-1]], RADII_MI[-1]


def value(subj, sales, asof):
    comps, radius = find_comps(subj, sales, asof)
    row = {"opa": subj["opa"], "address": subj.get("location"), "zip": str(subj.get("zip_code"))[:5],
           "category": subj.get("category"), "sqft": subj.get("sqft"), "beds": subj.get("beds"),
           "year_built": subj.get("year_built"), "opa_market_value": subj.get("market_value"),
           "comp_count": len(comps), "radius_mi": radius}
    ssq = float(subj.get("sqft") or 0)
    if not comps or ssq <= 300:
        row["note"] = "no comps" if not comps else "no living area on record"
        return row
    ppsf = [float(s["price_per_sqft"]) for _, s in comps]
    prices = [float(s["price"]) for _, s in comps]
    row.update({
        "ppsf_p25": round(pctile(ppsf, 0.25)),
        "ppsf_median": round(statistics.median(ppsf)),
        "ppsf_p80": round(pctile(ppsf, 0.80)),
        "as_is_value": round(pctile(ppsf, 0.25) * ssq, -3),
        "market_value_est": round(statistics.median(ppsf) * ssq, -3),
        "arv": round(pctile(ppsf, 0.80) * ssq, -3),
        "comp_price_median": round(statistics.median(prices), -3),
        "comp_price_max": round(max(prices), -3),
        "confidence": "High" if len(comps) >= 10 and radius <= 0.5 else
                      "Medium" if len(comps) >= MIN_COMPS else "Low",
        "top_comps": "; ".join(
            f"{s['street_address']} {s['sale_date'][:10]} ${float(s['price']):,.0f} ({d:.2f}mi)"
            for d, s in sorted(comps, key=lambda c: -float(c[1]["price_per_sqft"]))[:5]),
    })
    return row


def load_subjects(path):
    with open(path) as f:
        rows = list(csv.DictReader(f))
    opas = sorted({(r.get("OPA") or r.get("opa") or r.get("OPA (primary)") or "").strip()
                   for r in rows} - {""})
    return query(SUBJECT_SQL.format(opas=sql_list(opas)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sales", required=True)
    ap.add_argument("--subjects", required=True)
    ap.add_argument("--asof", default=dt.date.today().isoformat())
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    with open(a.sales) as f:
        sales = list(csv.DictReader(f))
    asof = dt.date.fromisoformat(a.asof)
    out = [value(s, sales, asof) for s in load_subjects(a.subjects)]
    keys = list(dict.fromkeys(k for r in out for k in r))
    with open(a.out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        w.writerows(out)
    print(f"{len(out)} subjects valued -> {a.out}")


if __name__ == "__main__":
    main()
