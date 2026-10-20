"""Write a short business plan per finalist from the recalculated model.

Usage:
    python business_plans.py MODEL_XLSX DEALS_CSV SHORTLIST_CSV -o plans.md [--csv verdicts.csv]
        [--title TITLE_CSV --base-max-bids MAX_BIDS_CSV]

With --title, lots the title check kills become Pass, and lots it says to verify
become "Hold: verify docket", shown at their worst-case max bid alongside the
base-case max bid from --base-max-bids.
"""

import argparse
import csv

from openpyxl import load_workbook

import build_model

BP = 0.015


def money(v):
    return f"-${-v:,.0f}" if v < 0 else f"${v:,.0f}"


def load_assumptions(wb):
    ws = wb["Assumptions"]
    labels = {item[1]: item[0] for item in build_model.ASSUMPTIONS if item[0]}
    out = {}
    for label, value, *_ in ws.iter_rows(min_row=4, values_only=True):
        if label in labels:
            out[labels[label]] = value
    return out


def title_verdict(v, why, t, base_max, worst_max):
    if not t:
        return v, why
    tv = t["Verdict"]
    if tv.startswith("KILL"):
        return "Pass", "title check: the plaintiff likely holds the 2nd mortgage, so the 1st survives"
    if tv.startswith("VERIFY"):
        if "Old case" in (t["Red flags"] or "") and base_max == worst_max:
            return "Hold: verify docket", ("set-aside and title-insurance risk from an old case; get an attorney's read "
                                           f"before bidding (max bid {money(base_max)} if cleared)")
        return "Hold: verify docket", (f"bid only if the docket shows the plaintiff holds the 1st mortgage: then the max bid is "
                                       f"{money(base_max)}; if a senior mortgage survives it's {money(worst_max)}")
    return v, why


def verdict(u, deal):
    open_bid = deal["open_bid"] or 0
    mx = u["Max bid that hits target"] or 0
    estimated = "est." in deal["notes"]
    if mx <= 0 or mx < open_bid:
        return "Pass", "max bid is below the opening bid"
    room = mx - open_bid
    over_box = u["Best exit"] == "Flip" and u["All-in cash at max bid"] > 300000
    if room < 15000 or mx < 1.5 * open_bid:
        return "Marginal", f"only {money(room)} of room over the {'estimated ' if estimated else ''}opening bid"
    if over_box:
        return "Bid (over the $300k box)", "all-in cost is above the ideal ceiling, but the profit is large"
    return "Bid", f"{money(room)} of room over the {'estimated ' if estimated else ''}opening bid"


def checks(deal, s, u, t=None):
    out = []
    occ = deal["occupancy"]
    if occ == "Occupied":
        out.append("Owner may still live there: look for cars, lights, mail, curtains; plan cash for keys")
    elif occ == "Unknown":
        out.append("Occupancy unknown (modeled as occupied): confirm at the door and with neighbors")
    else:
        out.append("City flags it vacant: check it's sealed and look for squatters or break-ins")
    v = s["Open violation types"] or ""
    if "ROOF" in v or "STRUCT" in v:
        out.append(f"Open L&I violation ({v.lower()}): look at the roofline, parapet, gutters and rear wall")
    else:
        out.append("Roof, front wall, cornice and windows from the street and the rear alley")
    if "CONDO" in s["Building type"]:
        out.append("Condo: get the HOA's monthly dues and 6 months of arrears (they survive); $250/mo is a placeholder")
    if deal["units"] == 2:
        out.append("Count meters and doorbells to confirm two units, and check the rental license and zoning use")
    if "hot pocket" in deal["notes"]:
        out.append("Hot pocket: the ARV used is the conservative one. See whether the block itself has renovated houses; "
                   "if it does, the full ARV may hold and the max bid rises")
    elif "comps Medium" in deal["notes"] or "comps Low" in deal["notes"] or "capped" in deal["notes"]:
        out.append("ARV is soft (medium-confidence comps): walk the block for renovated sales and list prices")
    if "VACANT LAND" in s["Building type"]:
        out.append("City records call this parcel vacant industrial land: confirm a house actually stands on it")
    if "est." in deal["notes"]:
        out.append("Opening bid not posted yet (21% of debt used): re-check the minimum the morning of Nov 3")
    if t:
        flags = [f for f in (t["Red flags"] or "").split(" | ") if f]
        for f in flags:
            out.append(f"Title: {f}")
        if "federal junior" in t["Verdict"]:
            out.append("Junior HUD lien: the U.S. can redeem for 1 year after the sale. The 12-month deed wait already "
                       "covers that year; if the deed comes early, don't start the rehab before month 12. "
                       "Check the docket shows the U.S. was served")
        if t["Case ID (FJD docket search)"]:
            out.append(f"Docket (fjdefile.phila.gov, Case ID {t['Case ID (FJD docket search)']}): plaintiff's name, "
                       "stays, bankruptcy suggestions")
        out.append("Live tax and water balances on phila.gov; IRS liens and judgments (title company O&E search); "
                   "PACER for bankruptcy the morning of the sale")
    else:
        out.append("Title check: plaintiff in 1st position, tax and water balances, IRS liens, bankruptcy")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("model")
    ap.add_argument("deals")
    ap.add_argument("shortlist")
    ap.add_argument("-o", "--out", required=True)
    ap.add_argument("--csv")
    ap.add_argument("--title")
    ap.add_argument("--base-max-bids")
    args = ap.parse_args()
    title, base_max = {}, {}
    if args.title:
        with open(args.title, newline="") as f:
            title = {r["Auction ID"]: r for r in csv.DictReader(f)}
    if args.base_max_bids:
        with open(args.base_max_bids, newline="") as f:
            base_max = {r["auction_id"]: float(r["max_bid"] or 0) for r in csv.DictReader(f)}

    wb = load_workbook(args.model, data_only=True)
    a = load_assumptions(wb)
    ws = wb["Underwriting"]
    headers = [c.value for c in ws[2]]
    uw = {}
    for row in ws.iter_rows(min_row=3, values_only=True):
        if row[0]:
            uw[str(row[0])] = dict(zip(headers, row))
    with open(args.deals, newline="") as f:
        deals = {r["auction_id"]: {k: ((float(v) if v else 0.0) if k in ("open_bid", "arv", "rent", "bldg_sf", "units") else v)
                                   for k, v in r.items()} for r in csv.DictReader(f)}
    with open(args.shortlist, newline="") as f:
        shortlist = {r["Auction ID"]: r for r in csv.DictReader(f)}

    order = {"Bid": 0, "Bid (over the $300k box)": 1, "Hold: verify docket": 2, "Marginal": 3, "Pass": 4}
    rows = []
    for aid, deal in deals.items():
        u = uw[aid]
        v, why = verdict(u, deal)
        mx = u["Max bid that hits target"] or 0
        v, why = title_verdict(v, why, title.get(aid), base_max.get(aid, mx), mx)
        rows.append((order[v], -(u["Max bid that hits target"] or 0), aid, v, why))
    rows.sort()

    lines = ["# Business plans: Nov 3, 2026 sheriff sale finalists", "",
             "Prepared Oct 20, 2026 from the underwriting model (`underwriting_model.xlsx`, same folder). "
             "Values are today's sold comps held flat; rents are HUD FY2027 Small Area FMRs; rehab is a blind budget. "
             "Max bid is the most you can pay and still make $50k and 15%/yr on cash on a flip, or 12% yield on cost on a hold. "
             "It's a ceiling, not a target. "
             + ("Surviving liens come from the title and lien check (`title-liens/`): base case for clean lots, worst case "
                "for lots still to verify on the docket. IRS liens, judgments and bankruptcy weren't checkable."
                if title else "It assumes no title surprises."), "",
             "## Summary", "",
             "| # | Address | Verdict | Exit | Opening bid | Max bid | All-in cash | Return at max bid |",
             "|---|---|---|---|---|---|---|---|"]
    bid_cash = 0
    for n, (_, _, aid, v, why) in enumerate(rows, start=1):
        u, d = uw[aid], deals[aid]
        ob = money(d["open_bid"]) + ("*" if "est." in d["notes"] else "")
        lines.append(f"| {n} | {u['Address']} | {v} | {u['Best exit']} | {ob} | {money(u['Max bid that hits target'])} | "
                     f"{money(u['All-in cash at max bid'])} | {u['Profit / return at max bid'] or ''} |")
        if v.startswith("Bid"):
            bid_cash += u["All-in cash at max bid"]
    n_bid = sum(1 for r in rows if r[3].startswith("Bid"))
    lines += ["", "\\* Opening bid not posted yet; 21% of the debt is used as an estimate.", "",
              f"Winning all {n_bid} \"Bid\" lots at their max bids would take about {money(bid_cash)} of cash "
              "over two years, against the $1M cap, so the bidding plan has to pick. "
              "You won't win them all at the max, and many will be postponed.", "",
              "## Plans", ""]

    csv_rows = []
    for n, (_, _, aid, v, why) in enumerate(rows, start=1):
        u, d, s = uw[aid], deals[aid], shortlist[aid]
        occ = int(u["Occupied? (1 = yes)"])
        exit_ = u["Best exit"]
        mx = u["Max bid that hits target"] or 0
        lines.append(f"### {n}. {u['Address']} ({d['zip']}), auction {aid}: {v}")
        lines.append("")
        lines.append(f"{s['Building type'].title()}, {d['bldg_sf']:,.0f} sf, built {d['year_built'] or '?'}, "
                     f"{int(d['units'])} unit{'s' if d['units'] > 1 else ''}. As-is about {money(float(d['asis_value'] or 0))}, "
                     f"ARV {money(d['arv'])}. Verdict: **{v}**, {why}.")
        lines.append("")
        if exit_ == "Pass":
            lines.append("- **Exit:** none hits the targets at any bid above the opening bid.")
        else:
            lines.append(f"- **Best exit:** {exit_}. " + (u["Other exits"] or ""))
        lines.append(f"- **Rehab scope:** {d['scope']}, blind budget {money(u['Rehab budget (blind)'])} "
                     f"(includes 20% contingency and the $10k allowance"
                     + (f", plus {money(float(d['ext_adders']))} for exterior/vacancy" if float(d['ext_adders'] or 0) else "") + ").")
        surv = float(d.get("surv_liens") or 0) + float(d.get("hoa_mo") or 0) * a["HOAArrearsMonths"]
        if title.get(aid):
            lines.append(f"- **Surviving liens budgeted:** {money(surv)} ({title[aid]['Cost basis']}"
                         + ("; includes a possible senior mortgage" if v.startswith("Hold") and surv > 10000
                            and "worst case" not in title[aid]["Cost basis"] else "")
                         + f"). Title verdict: {title[aid]['Verdict']}.")
        deed, ej, rm = a["DeedMonths"], a["EjectMonths"] * occ, u["Rehab months"]
        if exit_ == "Value-add hold":
            tl = (f"{deed:.0f} mo to deed" + (f", {ej:.0f} mo to get possession" if ej else "")
                  + f", {rm:.0f} mo rehab, {a['LeaseUpMonths']:.0f} mo to lease: rent starts about month {u['Hold: sale to rent start']:.0f}.")
        else:
            tl = (f"{deed:.0f} mo to deed" + (f", {ej:.0f} mo to get possession" if ej else "")
                  + f", {rm:.0f} mo rehab, {a['SellMonths']:.0f} mo to sell: about {u['Flip: sale to sold']:.0f} months sale to sale.")
        lines.append(f"- **Timeline:** {tl}")
        # Returns at a few bids
        bids = sorted({round(d["open_bid"] or 0, -2), round(mx / 2, -2) if mx else 0, round(mx, -2)})
        cells = []
        for b in bids:
            if b <= 0 and mx <= 0:
                continue
            flip_p = u["Flip: profit before bid"] - b * (1 + BP)
            cash_f = b * (1 + BP) + u["Flip: costs other than bid (pre-sale)"]
            ann = flip_p / cash_f / (u["Flip: sale to sold"] / 12)
            yoc = u["Hold: stabilized NOI / yr"] / (b * (1 + BP) + u["Hold: costs other than bid"])
            cells.append(f"{money(b)} bid: flip {money(flip_p)} ({ann:.0%}/yr), hold {yoc:.1%} yield on cost")
        lines.append("- **Returns:** " + "; ".join(cells) + ".")
        lines.append(f"- **Rent assumed:** {money(d['rent'])}/mo (HUD SAFMR), NOI {money(u['Hold: stabilized NOI / yr'])}/yr.")
        lines.append("- **Check in person and at the courthouse:**")
        for c in checks(d, s, u, title.get(aid)):
            lines.append(f"  - {c}")
        lines.append("")
        csv_rows.append(dict(auction_id=aid, address=u["Address"], verdict=v, reason=why, best_exit=exit_,
                             opening_bid=d["open_bid"], opening_bid_estimated="est." in d["notes"],
                             max_bid=round(mx), base_case_max_bid=round(base_max.get(aid, mx)),
                             title_verdict=(title.get(aid) or {}).get("Verdict", ""), all_in_cash=round(u["All-in cash at max bid"] or 0),
                             result_at_max=u["Profit / return at max bid"] or ""))

    lines += ["## What would change these numbers", "",
              "- **Rehab.** Every plan assumes an interior we haven't seen. Heavy is $85/sf plus 20%. If the drive-by shows a "
              "well-kept exterior, Medium ($55/sf) adds roughly $30k to $50k to the max bid on a 1,200 sf house.",
              "- **Occupancy.** Unknown is modeled as occupied (+5 months, +$5k). Confirmed vacant raises most max bids by $10k to $15k.",
              "- **The 15%/yr floor.** Without it, max bids on the bigger houses rise a lot, but the return on cash drops into single digits.",
              "- **Title.** A 2nd-position plaintiff, unpaid city claims above the bid, or an IRS lien comes straight off the max bid.",
              ""]
    with open(args.out, "w") as f:
        f.write("\n".join(lines))
    if args.csv:
        with open(args.csv, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(csv_rows[0].keys()))
            w.writeheader()
            w.writerows(csv_rows)
    print(args.out)


if __name__ == "__main__":
    main()
