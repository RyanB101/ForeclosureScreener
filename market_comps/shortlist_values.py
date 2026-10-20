"""Tighter sold-comp values for a shortlist, one row per auction lot.

Differences from comps.py (the first pass over every parcel):

  * Comps match on building class (row, twin, detached, small apartment,
    condo), not just OPA category, so condos value off condos.
  * Rings start at 0.25 mi and widen only until 5 comps are found, and up to
    24 months back, so values lean on the block rather than the ZIP.
  * ARV (80th percentile $/sqft x sqft) is capped at the 90th percentile
    actual sale price of the comps, so a large house isn't valued off a
    small renovated house's $/sqft.
  * Block check: every sale within 0.15 mi of any size, and every sale on the
    same street within 0.3 mi, is reported so hot pockets are visible.
    hot_pocket = Y when ARV is over 1.6x the block median, and
    arv_conservative caps ARV at that 1.6x.
  * HUD FY2027 Small Area FMR rent at the subject's bedroom count.

Condo sales mostly don't join from transfer records to OPA, so condo comps
come from OPA's own last-sale fields.

Usage:
    python shortlist_values.py --sales sales_24mo.csv --rents zip_rents_fy27_safmr.csv \
        --shortlist nov3_shortlist.csv --out shortlist_values.csv
"""
import argparse
import csv
import datetime as dt
import re
import statistics

from carto import query, sql_list
from comps import SUBJECT_SQL, miles, pctile

RINGS_MI = (0.25, 0.5, 0.75, 1.0)
MIN_COMPS = 5
MAX_AGE_DAYS = 730
SIZE_BAND = 0.35
BLOCK_MI = 0.15
HOT_POCKET_RATIO = 1.6

CONDO_SQL = """
SELECT parcel_number AS opa, location AS street_address, sale_date::date AS sale_date,
       sale_price AS price, total_livable_area AS sqft, building_code_description AS building,
       ST_Y(the_geom) AS lat, ST_X(the_geom) AS lng
FROM opa_properties_public
WHERE building_code_description LIKE '%CONDO%'
  AND sale_date >= '{since}' AND sale_price >= 25000 AND total_livable_area > 300
  AND ST_DWithin(the_geom::geography, ST_SetSRID(ST_MakePoint({lng}, {lat}), 4326)::geography, 1200)
"""


def bclass(building):
    b = (building or "").upper()
    if "CONDO" in b:
        return "condo"
    if b.startswith("APT") or "CONV/APT" in b or "CONV APT" in b:
        return "apt"
    if b.startswith(("S/D", "SEMI", "TWIN")):
        return "twin"
    if b.startswith("DET"):
        return "det"
    if b.startswith(("STR", "ROW W/OFF", "ROW W/STR")) or "STORE" in b:
        return "mixed"
    return "row"


def street(addr):
    a = re.sub(r"\s*#.*$", "", (addr or "").upper())
    return re.sub(r"^[\d\-/ ]+", "", a).strip()


def ppsf(s):
    return float(s["price"]) / float(s["sqft"])


def comps_for(subj, pool, asof):
    slat, slng, ssq = float(subj["lat"]), float(subj["lng"]), float(subj["sqft"] or 0)
    cls = bclass(subj["building"])
    cand = []
    for s in pool:
        if s["opa"] == subj["opa"] or s.get("new_build") or not s.get("lat"):
            continue
        if not s.get("sqft") or float(s["sqft"]) <= 300:
            continue
        if (asof - dt.date.fromisoformat(s["sale_date"][:10])).days > MAX_AGE_DAYS:
            continue
        d = miles(slat, slng, float(s["lat"]), float(s["lng"]))
        cand.append((d, s))
    block = [(d, s) for d, s in cand if d <= BLOCK_MI]
    same_st = [(d, s) for d, s in cand if d <= 0.3 and street(s["street_address"]) == street(subj["location"])]
    matched = [(d, s) for d, s in cand if bclass(s.get("building")) == cls
               and (ssq <= 300 or abs(float(s["sqft"]) / ssq - 1) <= SIZE_BAND)]
    for r in RINGS_MI:
        ring = [(d, s) for d, s in matched if d <= r]
        if len(ring) >= MIN_COMPS:
            return ring, r, block, same_st
    return [(d, s) for d, s in matched if d <= RINGS_MI[-1]], RINGS_MI[-1], block, same_st


def describe(comps, n=5, key=None):
    comps = sorted(comps, key=key or (lambda c: c[0]))[:n]
    return "; ".join(f"{s['street_address']} {s['sale_date'][:10]} ${float(s['price']):,.0f} "
                     f"{float(s['sqft']):,.0f}sf ({d:.2f}mi)" for d, s in comps)


def value_parcel(subj, sales, asof):
    pool = sales
    if bclass(subj["building"]) == "condo":
        since = (asof - dt.timedelta(days=MAX_AGE_DAYS)).isoformat()
        pool = query(CONDO_SQL.format(since=since, lat=subj["lat"], lng=subj["lng"]))
    comps, ring, block, same_st = comps_for(subj, pool, asof)
    ssq = float(subj["sqft"] or 0)
    row = {"opa": subj["opa"], "address": subj["location"], "building": subj["building"],
           "class": bclass(subj["building"]), "sqft": ssq, "beds": subj.get("beds"),
           "comp_count": len(comps), "ring_mi": ring}
    m = re.search(r"(\d(?:\.5)?) STY", subj["building"] or "")
    # A 2-story row recorded at ~650 sf is likely footprint only (rows run ~14x45 ft).
    if (m and bclass(subj["building"]) != "condo" and subj.get("stories")
            and float(subj["stories"]) < float(m.group(1)) and ssq / float(m.group(1)) < 450):
        row["sqft_check"] = (f"OPA records {subj['stories']} story but building is {m.group(1)} story; "
                             "living area may be understated")
    if len(comps) < 3 or ssq <= 300:
        row["note"] = "too few comps" if ssq > 300 else "no living area on record"
        return row
    ps = [ppsf(s) for _, s in comps]
    prices = [float(s["price"]) for _, s in comps]
    arv_raw = pctile(ps, 0.8) * ssq
    arv = min(arv_raw, pctile(prices, 0.9))
    block_prices = [float(s["price"]) for _, s in block]
    block_med = statistics.median(block_prices) if block_prices else None
    row.update({
        "as_is_value": round(min(pctile(ps, 0.25) * ssq, pctile(prices, 0.5)), -3),
        "market_value_est": round(min(statistics.median(ps) * ssq, pctile(prices, 0.75)), -3),
        "arv": round(arv, -3),
        "arv_capped_by_price": "Y" if arv < arv_raw else "",
        "block_sales_0_15mi": len(block_prices),
        "block_median_price": round(block_med, -3) if block_med else "",
        "block_max_price": round(max(block_prices), -3) if block_prices else "",
        "hot_pocket": "Y" if block_med and arv > HOT_POCKET_RATIO * block_med else "",
        "arv_conservative": round(min(arv, HOT_POCKET_RATIO * block_med) if block_med else arv, -3),
        "confidence": "High" if len(comps) >= 8 and ring <= 0.25 else
                      "Medium" if len(comps) >= MIN_COMPS and ring <= 0.5 else "Low",
        "top_comps": describe(comps, key=lambda c: -ppsf(c[1])),
        "same_street_sales": describe(same_st, n=6),
    })
    return row


def lot_rows(shortlist, sales, rents, asof):
    opas = sorted({o.strip() for r in shortlist for o in r["OPA"].split("&")} - {""})
    subjects = {s["opa"]: s for s in query(SUBJECT_SQL.format(opas=sql_list(opas)))}
    out = []
    for lot in shortlist:
        parts = [value_parcel(subjects[o.strip()], sales, asof)
                 for o in lot["OPA"].split("&") if o.strip() in subjects]
        row = {"rank": lot.get("Rank"), "auction_id": lot["Auction ID"], "address": lot["Address"],
               "zip": lot["ZIP"], "opa": lot["OPA"], "parcels": len(parts)}
        first = parts[0] if parts else {}
        for k in ("building", "class", "sqft", "beds", "comp_count", "ring_mi", "confidence",
                  "block_sales_0_15mi", "block_median_price", "block_max_price", "hot_pocket",
                  "arv_capped_by_price", "sqft_check", "top_comps", "same_street_sales", "note"):
            row[k] = first.get(k, "")
        for k in ("as_is_value", "market_value_est", "arv", "arv_conservative"):
            vals = [p.get(k) for p in parts]
            row[k] = sum(vals) if vals and all(v not in (None, "") for v in vals) else ""
        beds = int(float(first.get("beds") or 0))
        r = rents.get(lot["ZIP"], {})
        if beds:
            row["hud_rent_at_beds"] = r.get(f"safmr_{min(beds, 4)}br", "")
        row["hud_rent_3br"] = r.get("safmr_3br", "")
        out.append(row)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sales", required=True)
    ap.add_argument("--rents", required=True)
    ap.add_argument("--shortlist", required=True)
    ap.add_argument("--asof", default=dt.date.today().isoformat())
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    with open(a.sales) as f:
        sales = list(csv.DictReader(f))
    with open(a.rents) as f:
        rents = {r["zip"]: r for r in csv.DictReader(f)}
    with open(a.shortlist) as f:
        shortlist = list(csv.DictReader(f))
    out = lot_rows(shortlist, sales, rents, dt.date.fromisoformat(a.asof))
    lead = ["rank", "auction_id", "address", "zip", "opa", "parcels", "as_is_value",
            "market_value_est", "arv", "arv_conservative", "confidence", "hot_pocket",
            "hud_rent_at_beds", "hud_rent_3br"]
    keys = list(dict.fromkeys(lead + [k for r in out for k in r]))
    with open(a.out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        w.writerows(out)
    print(f"{len(out)} lots -> {a.out}")


if __name__ == "__main__":
    main()
