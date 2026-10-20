"""Run the first-pass screen.

    python -m screener --master nov3_2026_auction_master.csv \
        --parcels nov3_2026_auction_parcels.csv --out-dir out/
"""

import argparse
import logging
from pathlib import Path

import pandas as pd

from . import report, screen, sources


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--master", required=True, help="cleaned auction list, one row per lot")
    ap.add_argument("--parcels", required=True, help="one row per OPA number")
    ap.add_argument("--rents", help="optional CSV of zip,rent_per_unit for the value-add case")
    ap.add_argument("--out-dir", default="out")
    ap.add_argument("--prefix", default="screen")
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

    status = sources.check_access()
    logging.info("access: %s", status)
    master, parcels = screen.load(args.master, args.parcels)
    par = screen.enrich(parcels)
    market = sources.zip_market(parcels["ZIP"].unique(), screen.C)
    par = screen.value(par, market)
    rents = pd.read_csv(args.rents) if args.rents else None
    lots = screen.cut(screen.score(screen.lots(master, par, rents)))

    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    xlsx, csv = out / f"{args.prefix}.xlsx", out / f"{args.prefix}_shortlist.csv"
    report.write(lots, par, xlsx, csv, status)
    print(lots["list"].value_counts().to_string() if "list" in lots else "not scored")
    print(f"wrote {xlsx} and {csv}")


if __name__ == "__main__":
    main()
