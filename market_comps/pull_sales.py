"""Pull arm's-length residential sales from the city's transfer records.

Joins Real Estate Transfer Tax deeds (rtt_summary) to OPA property
characteristics (opa_properties_public) so each sale carries size, beds,
year built, condition and coordinates.

Usage:
    python pull_sales.py --zips 19143 19140 --since 2024-10-01 --out sales.csv
    python pull_sales.py --auction-csv nov3_2026_auction_parcels.csv --out sales.csv
"""
import argparse
import csv
import sys

from carto import query, sql_list

# Deeds that are not open-market sales: sheriff, tax claim, condemnation, etc.
# Only plain DEED documents are kept, then filtered further by price and parties.
MIN_PRICE = 10_000

SQL = """
SELECT
  r.document_id,
  r.display_date::date AS sale_date,
  r.street_address,
  r.zip_code,
  r.opa_account_num AS opa,
  r.total_consideration AS price,
  r.grantors,
  r.grantees,
  o.category_code_description AS category,
  o.building_code_description AS building,
  o.total_livable_area AS sqft,
  o.total_area AS lot_sqft,
  o.number_of_bedrooms AS beds,
  o.number_of_bathrooms AS baths,
  o.number_stories AS stories,
  o.year_built,
  o.exterior_condition,
  o.interior_condition,
  o.market_value,
  ST_Y(o.the_geom) AS lat,
  ST_X(o.the_geom) AS lng
FROM rtt_summary r
JOIN opa_properties_public o ON o.parcel_number = r.opa_account_num
WHERE r.document_type = 'DEED'
  AND r.display_date >= '{since}'
  AND r.total_consideration >= {min_price}
  AND left(r.zip_code, 5) IN ({zips})
  AND o.category_code_description IN ('SINGLE FAMILY', 'MULTI FAMILY', 'MIXED USE')
"""

# Grantee/grantor names that usually mean a non-market transfer.
NON_MARKET = ("SHERIFF", "SECRETARY OF HOUSING", "FEDERAL NATIONAL MORTGAGE",
              "FEDERAL HOME LOAN MORTGAGE", "LAND BANK", "REDEVELOPMENT AUTHORITY",
              "CITY OF PHILADELPHIA", "ESTATE OF")


def is_market(row):
    parties = f"{row.get('grantors') or ''} {row.get('grantees') or ''}".upper()
    return not any(k in parties for k in NON_MARKET)


def pull(zips, since):
    rows = query(SQL.format(since=since, min_price=MIN_PRICE, zips=sql_list(zips)))
    out = []
    for r in rows:
        if not is_market(r):
            continue
        sqft = float(r["sqft"] or 0)
        r["price_per_sqft"] = round(float(r["price"]) / sqft, 2) if sqft > 300 else ""
        r["zip_code"] = str(r["zip_code"])[:5]
        out.append(r)
    return out


def zips_from_auction(path):
    with open(path) as f:
        return sorted({r["ZIP"] for r in csv.DictReader(f) if r["ZIP"]})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--zips", nargs="*")
    ap.add_argument("--auction-csv")
    ap.add_argument("--since", default="2024-10-01")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    zips = a.zips or zips_from_auction(a.auction_csv)
    rows = pull(zips, a.since)
    if not rows:
        sys.exit("No sales returned")
    with open(a.out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"{len(rows)} sales across {len(zips)} ZIPs -> {a.out}")


if __name__ == "__main__":
    main()
