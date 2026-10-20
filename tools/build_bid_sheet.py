#!/usr/bin/env python3
"""Turn underwriting verdicts into a sale-day bid sheet workbook.

Reads one or more finalist_verdicts.csv files (shortlist, bench, ...), keeps the lots
whose verdict starts with "Bid", joins the auction master for close times and sale risk,
adds a walk-away price, ranks lots inside each close batch, and writes a workbook with
Won / Final price columns and a live headroom total against the capital cap.

Walk-away is a looser ceiling for overtime decisions, set by a lower target:
  flip - the bid where profit falls to --flip-walk-profit (default $25k, vs $50k at max_bid)
  hold - the bid where yield on cost falls to --hold-walk-yield (default 10%, vs 12% at max_bid)
Bids are rounded down to the $1,000 increment.

Usage:
    python3 build_bid_sheet.py MASTER.csv VERDICTS.csv [VERDICTS.csv ...] [-o bid_sheet.xlsx]
    A verdicts path can carry a label: bench=path/to/bench_verdicts.csv
"""
import argparse
import math

import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

PREMIUM = 0.015
INCREMENT = 1000


def floor_inc(x):
    return math.floor(x / INCREMENT) * INCREMENT if pd.notna(x) else None


def walk_away(row, flip_target, flip_walk, hold_target, hold_walk):
    mb, cash = row["max_bid_raw"], row["all_in_cash"]
    if str(row["best_exit"]).lower().startswith("flip"):
        # Each extra $1 of bid costs $1.015 of profit.
        return floor_inc(mb + (flip_target - flip_walk) / (1 + PREMIUM))
    # Same NOI at a lower yield supports a larger all-in cost.
    return floor_inc(mb + (cash * hold_target / hold_walk - cash) / (1 + PREMIUM))


def load_verdicts(specs, base_case_paths):
    frames = []
    for spec in specs:
        label, _, path = spec.rpartition("=")
        v = pd.read_csv(path)
        v["list"] = label or "shortlist"
        frames.append(v)
    # A lot can sit on more than one list; the first list given wins.
    v = pd.concat(frames, ignore_index=True).drop_duplicates("auction_id", keep="first")
    v["docket_check"] = ""
    hold = v["verdict"].fillna("").str.startswith("Hold") & (v.get("base_case_max_bid", 0) > v["opening_bid"])
    if hold.any() and base_case_paths:
        # "Hold: verify docket" lots are bid at the base-case max (plaintiff holds the 1st),
        # and only once the docket confirms it.
        b = pd.concat([pd.read_csv(p) for p in base_case_paths]).drop_duplicates("auction_id")
        b = b.set_index("auction_id")[["max_bid", "all_in_cash", "result_at_max", "best_exit"]]
        ids = v.loc[hold, "auction_id"]
        v.loc[hold, "docket_check"] = ("REQUIRED. If a senior mortgage survives, max bid is $"
                                       + v.loc[hold, "max_bid"].fillna(0).astype(int).map("{:,}".format))
        for col in b.columns:
            v.loc[hold, col] = ids.map(b[col]).values
        v.loc[hold, "verdict"] = "Hold: verify docket" + v.loc[hold, "all_in_cash"].map(
            lambda x: "" if x <= 300_000 else " (over the $300k box)")
    keep = v["verdict"].fillna("").str.startswith("Bid") | (hold & bool(base_case_paths))
    return v[keep].copy()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("master")
    ap.add_argument("verdicts", nargs="+")
    ap.add_argument("-o", "--out", default="bid_sheet.xlsx")
    ap.add_argument("--cap", type=float, default=900_000)
    ap.add_argument("--flip-target", type=float, default=50_000)
    ap.add_argument("--flip-walk-profit", type=float, default=25_000)
    ap.add_argument("--hold-target", type=float, default=0.12)
    ap.add_argument("--hold-walk-yield", type=float, default=0.10)
    ap.add_argument("--base-case", nargs="*", default=[],
                    help="max_bids_base_case.csv files; Hold-verify-docket lots are bid at these numbers")
    ap.add_argument("--title", help="title/lien check CSV; KILL lots are dropped, VERIFY lots rank last in their batch")
    args = ap.parse_args()

    df = load_verdicts(args.verdicts, args.base_case)
    master = pd.read_csv(args.master, usecols=["Auction ID", "Bidding closes", "Close slot",
                                               "Sale risk", "Flags", "OPA (primary)"])
    df = df.merge(master, left_on="auction_id", right_on="Auction ID", how="left")
    df["Title"], df["Surviving base"], df["Surviving worst"] = "Not checked", None, None
    killed = []
    if args.title:
        t = pd.read_csv(args.title).rename(columns={"Auction ID": "auction_id"})
        t = t[["auction_id", "Verdict", "Surviving cost, base case", "Surviving cost, worst case"]]
        df = df.merge(t, on="auction_id", how="left")
        df["Title"] = df["Verdict"].fillna("Not checked")
        df["Surviving base"] = df["Surviving cost, base case"]
        df["Surviving worst"] = df["Surviving cost, worst case"]
        killed = df.loc[df["Title"] == "KILL", "address"].tolist()
        df = df[df["Title"] != "KILL"].copy()
    df["title_ok"] = ~df["Title"].str.startswith(("VERIFY", "Not checked"))
    df["max_bid_raw"] = df["max_bid"]
    df["max_bid"] = df["max_bid_raw"].map(floor_inc)
    df["walk_away"] = df.apply(walk_away, axis=1, args=(args.flip_target, args.flip_walk_profit,
                                                         args.hold_target, args.hold_walk_yield))
    df["in_box"] = ~df["verdict"].str.contains("over")
    df["room"] = df["max_bid"] - df["opening_bid"]
    dup = df["OPA (primary)"].duplicated(keep=False)
    df.loc[dup, "Flags"] = "SAME PROPERTY ON TWO WRITS: bid on one only, after title confirms which writ is the 1st mortgage; " + df.loc[dup, "Flags"].fillna("")
    # Within a batch: in-box first, normal postponement risk first, posted opening bid first, most room.
    df = df.sort_values(["Bidding closes", "in_box", "title_ok", "Sale risk", "opening_bid_estimated", "room"],
                        ascending=[True, False, False, False, True, False])
    df["priority"] = df.groupby("Close slot").cumcount() + 1

    wb = Workbook()
    ws = wb.active
    ws.title = "Bid sheet"
    hdr = ["Close", "Priority in batch", "Address", "Auction ID", "List", "Verdict", "Exit", "Opening bid",
           "Opening bid estimated?", "Max bid (proxy)", "Walk-away", "All-in cash at max", "Result at max",
           "Due Nov 4 at max", "Due Nov 18 at max", "Sale risk", "Flags", "Docket check", "Title check",
           "Surviving liens (base)", "Surviving liens (worst)", "Won? (Y/N)", "Final price",
           "Committed (live)"]
    ws.append(hdr)
    for i, r in enumerate(df.itertuples(index=False), start=2):
        ws.append([r[df.columns.get_loc("Close slot")], r.priority, r.address, r.auction_id, r.list, r.verdict,
                   r.best_exit, r.opening_bid, "Yes" if r.opening_bid_estimated else "No", r.max_bid,
                   r.walk_away, r.all_in_cash, r.result_at_max, round(r.max_bid * (0.10 + PREMIUM)),
                   round(r.max_bid * 0.90 + 35), r[df.columns.get_loc("Sale risk")], r.Flags, r.docket_check, r.Title,
                   r[df.columns.get_loc("Surviving base")], r[df.columns.get_loc("Surviving worst")], None, None,
                   f'=IF(V{i}="Y",W{i}*{1 + PREMIUM}+(L{i}-J{i}*{1 + PREMIUM}),0)'])
    n = len(df) + 1
    ws["Z1"], ws["AA1"] = "Cap", args.cap
    ws["Z2"], ws["AA2"] = "Committed so far", f"=SUM(X2:X{n})"
    ws["Z3"], ws["AA3"] = "Headroom", "=AA1-AA2"
    ws["Z5"] = "Committed (live) = final price x 1.015 plus the rest of that lot's all-in budget."
    if killed:
        ws["Z8"] = "Dropped by title check (do not bid): " + ", ".join(killed)
    ws["Z7"] = "VERIFY lots: check the plaintiff on the court docket before bidding; worst case adds the surviving lien."
    ws["Z6"] = "While a lot is still open and you lead, count its full all-in cash at max against headroom."
    for c in ws[1]:
        c.font = Font(bold=True, color="FFFFFF")
        c.fill = PatternFill("solid", fgColor="1F3A5F")
        c.alignment = Alignment(wrap_text=True, vertical="top")
    for col in ("H", "J", "K", "L", "N", "O", "T", "U", "W", "X", "AA"):
        for cell in ws[col][1:]:
            cell.number_format = "$#,##0"
    ws["AA1"].number_format = "$#,##0"
    for c in ("Z1", "Z2", "Z3"):
        ws[c].font = Font(bold=True)
    widths = [8, 9, 22, 11, 10, 22, 14, 12, 11, 13, 12, 14, 34, 12, 13, 10, 60, 40, 22, 12, 12, 10, 12, 14, 2, 18, 14]
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w
    ws.freeze_panes = "D2"
    yellow = PatternFill("solid", fgColor="FFF2CC")
    for i in range(2, n + 1):
        for col in "VW":
            ws[f"{col}{i}"].fill = yellow
    wb.save(args.out)
    print(df[["Close slot", "priority", "address", "list", "verdict", "Title", "max_bid", "walk_away",
              "all_in_cash", "Surviving worst"]].to_string(index=False))
    if killed:
        print("Dropped by title check:", ", ".join(killed))
    print(f"\n{len(df)} lots, all-in at max ${df['all_in_cash'].sum():,.0f}. Wrote {args.out}")


if __name__ == "__main__":
    main()
