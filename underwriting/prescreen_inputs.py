"""Turn the auction list and first-pass comps into a deals CSV for the model.

Joins the cleaned auction list (opening bid, debt) to the Market and comps
values (sqft, beds, ARV) and HUD Small Area FMR rents. Only single-parcel,
residential lots with comps are kept; everything else is listed as skipped.

Usage:
    python prescreen_inputs.py PROJECT_FILES_DIR -o deals.csv
"""

import argparse
import csv
from pathlib import Path

RESIDENTIAL = {"SINGLE FAMILY": 1, "MULTI FAMILY": 2}


def num(v):
    try:
        return float(str(v).replace("$", "").replace(",", ""))
    except ValueError:
        return None


def rent_for(rents, zip_code, beds, category):
    row = rents.get(zip_code)
    if not row:
        return None
    if category == "MULTI FAMILY":
        # Unit mix unknown: assume two units, 1BR each if 3 beds or fewer in total, else 2BR each.
        per_unit = row["safmr_1br"] if (beds or 3) <= 3 else row["safmr_2br"]
        return 2 * num(per_unit)
    b = 3 if beds is None else int(min(max(beds, 0), 4))
    return num(row[f"safmr_{b}br"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("project_files")
    ap.add_argument("-o", "--out", required=True)
    ap.add_argument("--skipped", help="CSV of lots left out and why")
    args = ap.parse_args()
    root = Path(args.project_files)

    with open(root / "nov3-auction/nov3_2026_auction_master.csv", newline="") as f:
        lots = list(csv.DictReader(f))
    with open(root / "market-comps/all_parcels_values.csv", newline="") as f:
        values = {r["opa"].zfill(9): r for r in csv.DictReader(f)}
    with open(root / "market-comps/zip_rents_fy27_safmr.csv", newline="") as f:
        rents = {r["zip"]: r for r in csv.DictReader(f)}

    deals, skipped = [], []
    for lot in lots:
        aid = lot["Auction ID"]
        why = None
        v = values.get(str(lot["OPA (primary)"]).zfill(9))
        if lot["Parcels"] != "1":
            why = "Package lot (multiple parcels): underwrite by hand"
        elif not v:
            why = "No OPA match in comps"
        elif v["category"] not in RESIDENTIAL:
            why = f"{v['category'].title()}: not modeled as a house"
        elif not num(v["arv"]) or not num(v["sqft"]):
            why = "No comps / no ARV"
        if why:
            skipped.append({"auction_id": aid, "address": lot["Address (OPA style)"], "reason": why})
            continue
        beds = num(v["beds"])
        year = num(v["year_built"]) or 0
        zip_code = lot["ZIP"][:5]
        deals.append(dict(
            auction_id=aid,
            address=lot["Address (OPA style)"],
            zip=zip_code,
            open_bid=num(lot["Minimum bid"]),
            debt=num(lot["Debt amount"]) or "",
            lien_pos="Unknown",
            bldg_sf=num(v["sqft"]),
            year_built=int(year) if year else "",
            units=RESIDENTIAL[v["category"]],
            opa_value=num(v["opa_market_value"]) or "",
            asis_value=num(v["as_is_value"]) or "",
            arv=num(v["arv"]),
            rent=rent_for(rents, zip_code, beds, v["category"]) or "",
            scope="Medium" if year >= 1990 else "Heavy",
            occupancy="Unknown",
            notes=f"Pre-screen: {v['category'].lower()}, {int(beds) if beds is not None else '?'} bd, "
                  f"comps {v['confidence'] or 'n/a'}; rent = HUD SAFMR; sale risk {lot['Sale risk']}",
        ))

    keys = list(deals[0].keys())
    with open(args.out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        w.writerows(deals)
    if args.skipped:
        with open(args.skipped, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["auction_id", "address", "reason"])
            w.writeheader()
            w.writerows(skipped)
    print(f"{len(deals)} deals, {len(skipped)} skipped")


if __name__ == "__main__":
    main()
