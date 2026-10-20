"""Turn the screen's shortlist into a deals CSV for the model.

Uses the screen's property data (size, condition, violations, vacancy, capped
ARV) and HUD Small Area FMR rents, with blind-rehab rules:
- L&I unsafe -> Gut. Light band -> Medium (interior unseen).
- Pre-1980 -> Heavy unless the OPA exterior grade is good (3 or better), then Medium.
- Open roof/structure violations add $15k; a city vacancy flag adds $5k for
  boarding, cleanout and break-in damage.
Occupancy: vacancy flag -> Vacant, owner may live there -> Occupied, else Unknown.

Usage:
    python finalist_inputs.py SHORTLIST_CSV RENTS_CSV -o deals.csv
"""

import argparse
import csv

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
    ap.add_argument("-o", "--out", required=True)
    args = ap.parse_args()
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
            deals.append(dict(
                auction_id=row["Auction ID"], address=row["Address"], zip=zip_code,
                open_bid=num(row["Opening bid used"]), debt=num(row["Debt"], ""), lien_pos="Unknown",
                bldg_sf=num(row["Livable sq ft"]), lot_sf=num(row["Lot sq ft"], ""),
                year_built=int(num(row["Year built"], 0)) or "", units=2 if multi else 1,
                opa_value=num(row["OPA market value"], ""), asis_value=num(row["Est. as-is value"], ""),
                arv=num(row["Est. ARV"]), rent=rent, scope=scope_for(row), ext_adders=adders,
                occupancy=occupancy, hoa_mo=CONDO_HOA_MO if condo else "",
                notes="; ".join(notes),
            ))
    with open(args.out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(deals[0].keys()))
        w.writeheader()
        w.writerows(deals)
    print(f"{len(deals)} finalists")


if __name__ == "__main__":
    main()
