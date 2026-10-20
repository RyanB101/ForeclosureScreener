#!/usr/bin/env python3
"""Turn underwriting max bids into a sale-day bid sheet.

Joins max_bids.csv to the auction master for close times, adds a walk-away price,
orders lots by close batch and keeps a running committed-capital total against the cap.

Walk-away is a looser ceiling for overtime decisions, set by a lower target:
  flip - the bid where profit falls to --flip-walk-profit (default $25k, vs $50k at max_bid)
  hold - the bid where yield on cost falls to --hold-walk-yield (default 10%, vs 12% at max_bid)
Both are rounded down to the $1,000 bid increment.

Usage:
    python3 build_bid_sheet.py MAX_BIDS.csv MASTER.csv [-o bid_sheet.xlsx] [--cap 900000]
"""
import argparse
import math

import pandas as pd

PREMIUM = 0.015
INCREMENT = 1000


def floor_inc(x):
    return math.floor(x / INCREMENT) * INCREMENT if pd.notna(x) else None


def walk_away(row, flip_target, flip_walk, hold_target, hold_walk):
    mb, cash = row["max_bid"], row["all_in_cash"]
    if pd.isna(mb):
        return None
    if str(row["best_exit"]).lower().startswith("flip"):
        # Each extra $1 of bid costs $1.015 of profit.
        return floor_inc(mb + (flip_target - flip_walk) / (1 + PREMIUM))
    # Same NOI at a lower yield supports a larger all-in cost.
    if pd.isna(cash):
        return floor_inc(mb)
    return floor_inc(mb + (cash * hold_target / hold_walk - cash) / (1 + PREMIUM))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("max_bids")
    ap.add_argument("master")
    ap.add_argument("-o", "--out", default="bid_sheet.xlsx")
    ap.add_argument("--cap", type=float, default=900_000)
    ap.add_argument("--flip-target", type=float, default=50_000)
    ap.add_argument("--flip-walk-profit", type=float, default=25_000)
    ap.add_argument("--hold-target", type=float, default=0.12)
    ap.add_argument("--hold-walk-yield", type=float, default=0.10)
    args = ap.parse_args()

    bids = pd.read_csv(args.max_bids)
    if bids.empty:
        print("max_bids.csv has no rows yet")
        return
    master = pd.read_csv(args.master, usecols=["Auction ID", "Bidding closes", "Close slot",
                                               "Minimum bid", "Sale risk", "Bid4Assets link"])
    df = bids.merge(master, left_on="auction_id", right_on="Auction ID", how="left")
    df = df[pd.to_numeric(df["max_bid"], errors="coerce") > 0].copy()
    df["max_bid"] = df["max_bid"].map(floor_inc)
    df["walk_away"] = df.apply(walk_away, axis=1, args=(args.flip_target, args.flip_walk_profit,
                                                         args.hold_target, args.hold_walk_yield))
    df["below_opening"] = df["max_bid"] < df["Minimum bid"]
    df = df.sort_values(["Bidding closes", "max_bid"], ascending=[True, False])
    df["running_committed"] = df["all_in_cash"].cumsum()
    df["over_cap_if_all_won"] = df["running_committed"] > args.cap
    df["due_nov4_at_max"] = (df["max_bid"] * (0.10 + PREMIUM)).round()
    df["due_nov18_at_max"] = (df["max_bid"] * 0.90 + 35).round()

    cols = ["Close slot", "auction_id", "address", "best_exit", "Minimum bid", "max_bid", "walk_away",
            "all_in_cash", "running_committed", "over_cap_if_all_won", "due_nov4_at_max",
            "due_nov18_at_max", "below_opening", "Sale risk", "flags"]
    out = df[[c for c in cols if c in df.columns]]
    out.to_excel(args.out, index=False, sheet_name="Bid sheet")
    print(out.to_string(index=False))
    print(f"\nWrote {args.out}")


if __name__ == "__main__":
    main()
