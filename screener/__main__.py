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
    ap.add_argument("--comps", help="optional per-OPA sold-comp values (opa, as_is_value, arv, confidence)")
    ap.add_argument("--refined", nargs="*", default=[],
                    help="closer per-lot values (opa, as_is_value, arv, arv_conservative); "
                         "arv_conservative is used where given, and the ZIP ARV cap is skipped")
    ap.add_argument("--zip-market", help="optional ZIP stats from city deeds (zip, sales_last_12m, "
                                         "median_ppsf_last_12m, ppsf_yoy_pct); overrides OPA last-sale stats")
    ap.add_argument("--underwriting", help="optional underwriting max bids (auction_id, best_exit, max_bid) "
                                           "shown as a cross-check")
    ap.add_argument("--out-dir", default="out")
    ap.add_argument("--prefix", default="screen")
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

    status = sources.check_access()
    logging.info("access: %s", status)
    master, parcels = screen.load(args.master, args.parcels)
    par = screen.enrich(parcels)
    market = sources.zip_market(parcels["ZIP"].unique(), screen.C)
    if args.zip_market and market is not None:
        zm = pd.read_csv(args.zip_market, dtype={"zip": str})
        zm = pd.DataFrame({"zip": zm["zip"].str.zfill(5), "n": zm["sales_last_12m"],
                           "psf_med": zm["median_ppsf_last_12m"],
                           "psf_med_prev": zm["median_ppsf_last_12m"] / (1 + zm["ppsf_yoy_pct"] / 100),
                           "zip_p75_price": zm["p75_price_last_12m"]})
        market = market.drop(columns=["n", "psf_med", "psf_med_prev"]).merge(zm, on="zip", how="left")
    comps = pd.read_csv(args.comps, dtype={"opa": str}) if args.comps else None
    refined = None
    if args.refined:
        refined = pd.concat([pd.read_csv(f, dtype={"opa": str}) for f in args.refined])
        if "arv_conservative" in refined:
            refined["arv"] = refined["arv_conservative"].fillna(refined["arv"])
    par = screen.value(par, market, comps, refined)
    rents = pd.read_csv(args.rents) if args.rents else None
    uw = pd.read_csv(args.underwriting) if args.underwriting else None
    lots = screen.cut(screen.score(screen.lots(master, par, rents, uw)))

    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    xlsx, csv = out / f"{args.prefix}.xlsx", out / f"{args.prefix}_shortlist.csv"
    report.write(lots, par, xlsx, csv, status)
    print(lots["list"].value_counts().to_string() if "list" in lots else "not scored")
    print(f"wrote {xlsx} and {csv}")


if __name__ == "__main__":
    main()
