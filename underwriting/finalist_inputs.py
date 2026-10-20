"""Turn the screen's shortlist into a deals CSV for the model.

Uses the screen's property data (size, condition, violations, vacancy, capped
ARV) and HUD Small Area FMR rents, with blind-rehab rules:
- L&I unsafe -> Gut. Light band -> Medium (interior unseen).
- Pre-1980 -> Heavy unless the OPA exterior grade is good (3 or better), then Medium.
- Open roof/structure violations add $15k; a city vacancy flag adds $5k for
  boarding, cleanout and break-in damage.
Occupancy: vacancy flag -> Vacant, owner may live there -> Occupied, else Unknown.

With --values (Market and comps' per-lot file), its ARV, as-is value and
HUD rent at the lot's bedroom count replace the screen's; hot-pocket lots use
the conservative ARV.

With --title (the title and lien check), its lien position and surviving cost
fill those inputs: the worst case for --case worst, else the base case. Its
6 months of condo/HOA dues become the monthly HOA input instead.

Usage:
    python finalist_inputs.py SHORTLIST_CSV RENTS_CSV [--values VALUES_CSV]
        [--title TITLE_CSV --case base|worst] -o deals.csv
"""

import argparse
import csv
import re

CONDO_HOA_MO = 250   # estimate until the association's figure is known


def truthy(v):
    return str(v).strip().lower() in ("true", "1", "y", "yes")


def num(v, default=None):
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def scope_for(row):
    year = num(row["Year built"], 1900)
    ext = num(row["OPA exterior condition"], 4)
    if truthy(row["L&I unsafe"]) or truthy(row["L&I imminently dangerous"]):
        return "Gut"
    if row["Rehab band"] == "light":
        return "Medium"
    if row["Rehab band"] in ("heavy", "gut"):
        return row["Rehab band"].title()
    return "Medium" if year >= 1980 or ext <= 3 else "Heavy"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("shortlist")
    ap.add_argument("rents")
    ap.add_argument("--values")
    ap.add_argument("--title")
    ap.add_argument("--case", choices=["base", "worst"], default="base")
    ap.add_argument("-o", "--out", required=True)
    args = ap.parse_args()
    title = {}
    if args.title:
        with open(args.title, newline="") as f:
            title = {r["Auction ID"]: r for r in csv.DictReader(f)}
    values = {}
    if args.values:
        with open(args.values, newline="") as f:
            values = {r["auction_id"]: r for r in csv.DictReader(f)}
    with open(args.rents, newline="") as f:
        rents = {r["zip"]: r for r in csv.DictReader(f)}
    deals = []
    with open(args.shortlist, newline="") as f:
        for row in csv.DictReader(f):
            zip_code = row["ZIP"][:5]
            multi = row["Property type"] == "MULTI FAMILY"
            condo = "CONDO" in row["Building type"]
            beds = num(row["Beds"], 0) or 3
            r = rents[zip_code]
            rent = 2 * num(r["safmr_1br"]) if multi else num(r[f"safmr_{int(min(beds, 4))}br"])
            violations = row["Open violation types"] or ""
            adders = (15000 if ("ROOF" in violations or "STRUCT" in violations) else 0) \
                + (5000 if truthy(row["City vacancy flag"]) else 0)
            if truthy(row["City vacancy flag"]):
                occupancy = "Vacant"
            elif truthy(row["Owner may live there"]):
                occupancy = "Occupied"
            else:
                occupancy = "Unknown"
            notes = [f"Screen rank {int(num(row['Rank']))}",
                     f"opening bid: {row['Opening bid basis']}",
                     f"comps {row['Comp confidence'] or 'n/a'}",
                     f"sale risk {row['Sale risk']}"]
            if row["ARV capped at 1.25x ZIP p75"] == "True":
                notes.append("ARV capped at 1.25x ZIP p75")
            if condo:
                notes.append(f"condo: HOA ${CONDO_HOA_MO}/mo is an estimate")
            if violations:
                notes.append(f"open L&I: {violations}")
            arv, asis = num(row["Est. ARV"]), num(row["Est. as-is value"], "")
            v = values.get(row["Auction ID"])
            if v:
                hot = v["hot_pocket"] == "Y"
                arv = num(v["arv_conservative"] if hot else v["arv"])
                asis = num(v["as_is_value"], asis)
                if not multi:
                    rent = num(v["hud_rent_at_beds"]) or num(v["hud_rent_3br"]) or rent
                notes[2] = f"comps {v['confidence'] or 'n/a'}"
                notes = [n for n in notes if not n.startswith("ARV capped")]
                if hot:
                    notes.append("hot pocket: conservative ARV used")
            lien_pos, surv, hoa_mo = "Unknown", "", CONDO_HOA_MO if condo else ""
            t = title.get(row["Auction ID"])
            if t:
                pos = t["Lien position of foreclosing mortgage"]
                lien_pos = "1st" if pos.endswith("1st") else "2nd" if "junior" in pos else "Unknown"
                surv = num(t["Surviving cost, worst case" if args.case == "worst" else "Surviving cost, base case"], 0)
                hoa = re.search(r"condo/HOA 6 mo \$([\d,]+)", t["Cost basis"] or "")
                if hoa:
                    six = num(hoa.group(1).replace(",", ""))
                    hoa_mo, surv = six / 6, surv - six
                notes.append(f"title: {t['Verdict']}")
            deals.append(dict(
                auction_id=row["Auction ID"], address=row["Address"], zip=zip_code,
                open_bid=num(row["Opening bid used"]), debt=num(row["Debt"], ""), lien_pos=lien_pos,
                bldg_sf=num(row["Livable sq ft"]), lot_sf=num(row["Lot sq ft"], ""),
                year_built=int(num(row["Year built"], 0)) or "", units=2 if multi else 1,
                opa_value=num(row["OPA market value"], ""), asis_value=asis,
                arv=arv, rent=rent, scope=scope_for(row), ext_adders=adders,
                occupancy=occupancy, surv_liens=surv, hoa_mo=hoa_mo,
                notes="; ".join(notes),
            ))
    with open(args.out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(deals[0].keys()))
        w.writeheader()
        w.writerows(deals)
    print(f"{len(deals)} finalists")


if __name__ == "__main__":
    main()
