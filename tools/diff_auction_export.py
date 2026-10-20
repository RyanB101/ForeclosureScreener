#!/usr/bin/env python3
"""Compare a fresh Bid4Assets Philadelphia sheriff-sale export against a baseline.

The Bid4Assets export hides postponed and stayed lots, so a lot that gets pulled
simply disappears. Postponed lots also come back under a new Auction ID, so lots
are matched on Book/Writ (stable across postponements), falling back to OPA.

Usage:
    python3 diff_auction_export.py BASELINE NEW [-o OUT.xlsx]

BASELINE and NEW can each be a raw Bid4Assets export (.xlsx with the 2-line
report header) or the cleaned master (.csv/.xlsx with a "Master" sheet).
"""
import argparse
import sys

import pandas as pd

RAW_COLS = ["Auction ID", "Status", "Minimum Bid", "Close", "Open", "Attorney",
            "Debt Amount", "Book/Writ", "OPA", "Address", "County", "Sale Type"]


def load(path):
    if path.lower().endswith(".csv"):
        df = pd.read_csv(path, dtype=str)
    else:
        sheets = pd.ExcelFile(path).sheet_names
        if "Master" in sheets:
            df = pd.read_excel(path, sheet_name="Master", dtype=str)
        else:
            raw = pd.read_excel(path, header=None, dtype=str)
            hdr = raw.index[raw[0].astype(str).str.strip() == "Auction ID"][0]
            df = raw.iloc[hdr + 1:].copy()
            df.columns = RAW_COLS[:df.shape[1]]
            # The export has two columns both named "Bidding Open Date/Time":
            # one is the 10:00 AM open, the other the staggered close. Keep the later one.
            a, b = pd.to_datetime(df["Close"]), pd.to_datetime(df["Open"])
            df["Close"], df["Open"] = a.where(a > b, b), a.where(a <= b, b)
            df = df.dropna(subset=["Auction ID"])
    rename = {"Book/Writ (as exported)": "Book/Writ", "Minimum bid": "Minimum Bid",
              "Bidding closes": "Close", "Address (as exported)": "Address",
              "OPA (all parcels)": "OPA", "B4A status": "Status", "Debt amount": "Debt Amount"}
    df = df.rename(columns={k: v for k, v in rename.items() if k in df.columns and v not in df.columns})
    keep = ["Auction ID", "Book/Writ", "OPA", "Address", "Status", "Minimum Bid", "Debt Amount", "Close"]
    df = df[[c for c in keep if c in df.columns]].copy()
    df["Auction ID"] = df["Auction ID"].astype(str).str.replace(r"\.0$", "", regex=True)
    df["Minimum Bid"] = pd.to_numeric(df["Minimum Bid"], errors="coerce")
    df["Close"] = pd.to_datetime(df["Close"], errors="coerce").dt.strftime("%-I:%M %p")
    df["key"] = df["Book/Writ"].fillna(df["OPA"]).astype(str).str.strip()
    return df


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("baseline")
    ap.add_argument("new")
    ap.add_argument("-o", "--out", default="auction_diff.xlsx")
    args = ap.parse_args()

    old, new = load(args.baseline), load(args.new)
    m = old.merge(new, on="key", how="outer", suffixes=(" (old)", " (new)"), indicator=True)

    dropped = m[m["_merge"] == "left_only"]
    added = m[m["_merge"] == "right_only"]
    both = m[m["_merge"] == "both"]
    bid = both[both["Minimum Bid (old)"].fillna(-1) != both["Minimum Bid (new)"].fillna(-1)].copy()
    bid["Was $1 placeholder"] = bid["Minimum Bid (old)"] == 1
    close = both[both["Close (old)"] != both["Close (new)"]]
    new_id = both[both["Auction ID (old)"] != both["Auction ID (new)"]]
    status = both[both["Status (old)"].fillna("") != both["Status (new)"].fillna("")] \
        if "Status (old)" in both else both.iloc[0:0]

    def cols(df, side):
        c = [f"{x} ({side})" for x in ["Auction ID", "Book/Writ", "Address", "Minimum Bid", "Close"]]
        return df[[x for x in c if x in df.columns]]

    sheets = {
        "Dropped (postponed-stayed)": cols(dropped, "old"),
        "Added": cols(added, "new"),
        "Min bid changed": bid[["Auction ID (new)", "Book/Writ (new)", "Address (new)",
                                "Minimum Bid (old)", "Minimum Bid (new)", "Was $1 placeholder"]],
        "Close time changed": close[["Auction ID (new)", "Address (new)", "Close (old)", "Close (new)"]],
        "New Auction ID": new_id[["Book/Writ (new)", "Address (new)", "Auction ID (old)", "Auction ID (new)"]],
        "Status changed": status[[c for c in ["Auction ID (new)", "Address (new)", "Status (old)", "Status (new)"]
                                  if c in status.columns]],
    }
    with pd.ExcelWriter(args.out) as xw:
        summary = pd.DataFrame({"Check": list(sheets), "Lots": [len(v) for v in sheets.values()]})
        summary.loc[len(summary)] = ["Baseline lots", len(old)]
        summary.loc[len(summary)] = ["New export lots", len(new)]
        summary.to_excel(xw, sheet_name="Summary", index=False)
        for name, df in sheets.items():
            df.to_excel(xw, sheet_name=name[:31], index=False)
    print(summary.to_string(index=False))
    print(f"\nWrote {args.out}")


if __name__ == "__main__":
    sys.exit(main())
