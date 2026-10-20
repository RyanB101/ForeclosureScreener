"""Build the sheriff-sale underwriting workbook.

The workbook is formula driven: every assumption lives on the Assumptions
sheet as a named cell, every property input on the Deals sheet, so the
numbers can be changed in Excel without re-running this script.

Usage:
    python build_model.py [deals.csv] [-o output.xlsx]

deals.csv uses the column keys in DEAL_COLUMNS. Without it the Deals sheet
gets three illustrative example rows.
"""

import argparse
import csv
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.workbook.defined_name import DefinedName
from openpyxl.worksheet.datavalidation import DataValidation

HERE = Path(__file__).parent

INPUT_FILL = PatternFill("solid", fgColor="FFF2CC")
HEAD_FILL = PatternFill("solid", fgColor="1F3864")
GROUP_FILL = PatternFill("solid", fgColor="D9E1F2")
KEY_FILL = PatternFill("solid", fgColor="E2EFDA")
HEAD_FONT = Font(bold=True, color="FFFFFF")
BOLD = Font(bold=True)
THIN = Border(bottom=Side(style="thin", color="BFBFBF"))

USD = '"$"#,##0;[Red]-"$"#,##0'
PCT = "0.0%"
NUM = "#,##0"
MO = '0.0" mo"'

FIRST_ROW = 3          # first data row on Deals / Underwriting / Ladder / Portfolio
MAX_DEALS = 40         # spare formula rows so new deals can be typed in

# ---------------------------------------------------------------------------
# Assumptions: (name, label, value, format, note). None name = section header.
# ---------------------------------------------------------------------------
ASSUMPTIONS = [
    (None, "Targets (ryan's buy box)"),
    ("FlipTarget", "Flip: minimum profit", 50000, USD, "ryan's target: $50k profit per flip"),
    ("FlipMinAnnROI", "Flip: minimum annualized return on cash (0 = off)", 0.15, PCT,
     "Second test so big-ticket flips can't pass on $50k alone over a 2-year hold. "
     "Simple annualized: profit / peak cash / years held. ryan confirmed 15% on Oct 20"),
    ("FlipCeiling", "Flip: all-in cost ceiling (bid + rehab + costs)", 300000, USD,
     "Ideal box. A deal over this is flagged, not excluded"),
    ("HoldTarget", "Value-add: target annual return", 0.12, PCT, "ryan's target: 12%"),
    ("HoldMeasure", "Value-add: measure the 12% is tested on", "Yield on cost", None,
     "Yield on cost = stabilized NOI / all-in cost (unlevered). "
     "Cash-on-cash = cash flow after refi debt service / cash left in after refi"),
    ("CapitalCap", "Total cash available", 1000000, USD, "ryan's maximum cash"),

    (None, "Sale terms (Philadelphia Sheriff, Nov 3 2026)"),
    ("BuyerPremium", "Buyer's premium", 0.015, PCT, "1.5% of price, paid with the 10% down"),
    ("DownPct", "Down payment due Nov 4", 0.10, PCT, "10% + premium by 5 PM Nov 4; $10k deposit counts toward it"),
    ("SheriffFees", "Sheriff / Bid4Assets fees per lot", 70, USD, "$35 processing + $35 balance fee"),
    ("BidderDeposit", "Bidder deposit (credited to the Nov 4 down payment)", 5000, USD,
     "$5,000 + $35 fee, received by Bid4Assets 4 PM ET Oct 27 (wire, certified check, money order)"),
    ("RTTPurchase", "Realty transfer tax taken out of the bid", 0.04578, "0.000%",
     "Sheriff pays it from the price, before city claims"),
    ("SheriffCostsFromBid", "Sheriff costs paid from the bid before city claims", 2500, USD,
     "Poundage, advertising, service. Estimate; check the distribution schedule"),
    ("PurchaseTitle", "Title insurance and recording after deed", 2000, USD,
     "Transfer tax on purchase is paid from the bid, so $0 here"),
    ("CompelDeedLegal", "Legal: petition to compel deed / docket review", 2500, USD,
     "Deeds running 12+ months; budget counsel on every lot"),

    (None, "Timeline (months)"),
    ("DeedMonths", "Sale to recorded deed", 12, MO, "Rules research: 9-15 months, base 12"),
    ("EjectMonths", "Deed to vacant possession if occupied", 5, MO, "Ejectment 3-6 months if uncontested"),
    ("UnknownAsOccupied", "Treat unknown occupancy as occupied? (Y/N)", "Y", None,
     "Conservative default until the drive-by"),
    ("SellMonths", "Flip: list to closed sale", 3, MO, ""),
    ("LeaseUpMonths", "Hold: rehab done to rent starts", 2, MO, ""),

    (None, "Carry while waiting / rehabbing (per month)"),
    ("TaxRate", "Real estate tax rate (of OPA market value)", 0.013998, "0.0000%", "Philadelphia 2026"),
    ("VacantInsMo", "Vacant-property insurance", 175, USD, ""),
    ("SecuringMo", "Securing, lawn, trash, inspections", 150, USD, "Includes L&I vacant-property upkeep"),
    ("UtilitiesMo", "Utilities", 100, USD, ""),
    ("HOAArrearsMonths", "Condo/HOA arrears that survive (months)", 6, MO, "68 Pa.C.S. 3315 / 5315"),

    (None, "Possession"),
    ("PossessionCost", "Possession cost if occupied", 5000, USD,
     "Ejectment counsel + $325 writ + lockout/trash-out, or cash for keys"),

    (None, "Rehab (interior unseen)"),
    ("Contingency", "Blind-interior contingency on $/sf budget", 0.20, PCT, "No interior access before purchase"),
    ("BlindAllowance", "Fixed allowance per property", 10000, USD,
     "Cleanout, permits, lead/asbestos test, utility reconnects, systems surprises"),

    (None, "Flip exit"),
    ("BrokerPct", "Listing + buyer agent commission", 0.05, PCT, ""),
    ("SellerRTT", "Seller share of realty transfer tax", 0.02289, "0.000%", "Half of 4.578%"),
    ("SellClosingPct", "Other seller closing costs", 0.01, PCT, ""),
    ("ConcessionsPct", "Buyer concessions / price cuts", 0.01, PCT, ""),

    (None, "Value-add hold / BRRRR exit"),
    ("Vacancy", "Vacancy and credit loss", 0.07, PCT, "Of gross rent"),
    ("MgmtPct", "Property management", 0.08, PCT, "Of collected rent"),
    ("MaintPct", "Repairs and maintenance", 0.07, PCT, "Of collected rent"),
    ("CapexPct", "Capital reserve", 0.05, PCT, "Of collected rent"),
    ("InsPerUnit", "Landlord insurance per unit per year", 1200, USD, ""),
    ("WaterPerUnit", "Water/sewer, license, other per unit per year", 700, USD,
     "Landlord usually carries water in Philly; rental license ~$75/unit"),
    ("RefiLTV", "Refi loan-to-value (of ARV)", 0.75, PCT, "DSCR lender, after the deed records"),
    ("RefiRate", "Refi interest rate", 0.0725, "0.00%", ""),
    ("RefiTerm", "Refi amortization (years)", 30, "0", ""),
    ("RefiDSCR", "Minimum debt service coverage", 1.20, "0.00x", "Loan is sized down if NOI is thin"),
    ("RefiCostPct", "Refi closing costs (of loan)", 0.03, PCT, ""),

    (None, "Wholesale (assign the bid)"),
    ("BuyerMarginPct", "End buyer's required profit (of ARV)", 0.15, PCT,
     "Assign by notarized assignment of bid within 15 days; you stay on the hook if they default"),
    ("WholesaleMinFee", "Your minimum assignment fee", 15000, USD, ""),

    (None, "Teardown / added units"),
    ("DemoCost", "Demolition and site prep", 30000, USD, ""),
    ("BuildCostPSF", "New construction hard cost per sf", 225, USD, ""),
    ("SoftCostPct", "Soft costs (design, permits, zoning, financing)", 0.15, PCT, "Of hard cost"),
    ("BuildMonths", "Permit + build months", 14, MO, ""),
    ("DevMarginPct", "Developer profit target (of sale revenue)", 0.15, PCT, "Or the flip target, whichever is higher"),
]

# Rehab scope table: name, $/sf, months, description.
SCOPES = [
    ("Light", 30, 2, "Paint, floors, fixtures, minor kitchen/bath refresh"),
    ("Medium", 55, 3, "New kitchen and bath, some systems, windows"),
    ("Heavy", 85, 5, "All systems, kitchen, baths, drywall, roof repair"),
    ("Gut", 125, 7, "Down to studs: structure, roof, all systems, full finishes"),
]

# Deals sheet inputs: (key, header, format, width, note)
DEAL_COLUMNS = [
    ("auction_id", "Auction ID", "0", 11, ""),
    ("address", "Address", None, 22, ""),
    ("zip", "ZIP", "0", 7, ""),
    ("open_bid", "Opening bid", USD, 11, "No reserve: the minimum bid is the floor. $1 = awaiting minimum bid"),
    ("debt", "Judgment / debt", USD, 11, ""),
    ("lien_pos", "Plaintiff lien position", None, 10, "1st / 2nd / Unknown (title check)"),
    ("bldg_sf", "Building sf", NUM, 9, ""),
    ("lot_sf", "Lot sf", NUM, 8, ""),
    ("year_built", "Year built", "0", 7, ""),
    ("units", "Units (after rehab)", "0", 7, ""),
    ("opa_value", "OPA market value", USD, 11, "Drives taxes while waiting"),
    ("asis_value", "As-is value", USD, 11, "Comps thread"),
    ("arv", "ARV", USD, 11, "After-repair value, comps thread"),
    ("rent", "Market rent / mo (all units)", USD, 11, "Rent comps, after rehab"),
    ("scope", "Rehab scope", None, 9, "Light / Medium / Heavy / Gut"),
    ("ext_adders", "Exterior / known adders", USD, 11, "Roof, facade, structural seen from street"),
    ("occupancy", "Occupancy", None, 10, "Vacant / Occupied / Unknown"),
    ("surv_liens", "Surviving liens not covered by bid", USD, 11,
     "Senior mortgage if plaintiff is 2nd, uncovered city claims, IRS"),
    ("city_claims", "City claims owed (RE tax, water/sewer, other)", USD, 11,
     "Paid from the bid first; any part the bid doesn't cover survives. Title check"),
    ("hoa_mo", "Condo/HOA dues / mo", USD, 9, ""),
    ("td_units", "Teardown: units possible", "0", 9, "Leave blank if not a build site"),
    ("td_sf", "Teardown: new-build sf", NUM, 9, ""),
    ("td_value_unit", "Teardown: sale value / unit", USD, 11, ""),
    ("notes", "Data status / notes", None, 40, ""),
]

EXAMPLE_DEALS = [
    dict(auction_id="EXAMPLE 1", address="Rowhouse, light-medium flip", zip=19134, open_bid=25000,
         debt=120000, lien_pos="1st", bldg_sf=1100, lot_sf=800, year_built=1925, units=1,
         opa_value=120000, asis_value=110000, arv=230000, rent=1700, scope="Medium", ext_adders=0,
         occupancy="Unknown", surv_liens=0, hoa_mo=0, notes="Illustrative inputs only, not a real lot"),
    dict(auction_id="EXAMPLE 2", address="Duplex, light rehab hold", zip=19144, open_bid=40000,
         debt=210000, lien_pos="1st", bldg_sf=2200, lot_sf=1600, year_built=1915, units=2,
         opa_value=190000, asis_value=170000, arv=320000, rent=3300, scope="Light", ext_adders=8000,
         occupancy="Occupied", surv_liens=0, hoa_mo=0, notes="Illustrative inputs only, not a real lot"),
    dict(auction_id="EXAMPLE 3", address="Shell on wide lot", zip=19121, open_bid=1,
         debt=90000, lien_pos="1st", bldg_sf=1300, lot_sf=2400, year_built=1900, units=1,
         opa_value=80000, asis_value=60000, arv=260000, rent=1600, scope="Gut", ext_adders=15000,
         occupancy="Vacant", surv_liens=0, city_claims=9000, hoa_mo=0, td_units=3, td_sf=3600, td_value_unit=330000,
         notes="Illustrative inputs only, not a real lot"),
]


def style_header(ws, row, ncols):
    for c in range(1, ncols + 1):
        cell = ws.cell(row=row, column=c)
        cell.fill = HEAD_FILL
        cell.font = HEAD_FONT
        cell.alignment = Alignment(wrap_text=True, vertical="center", horizontal="center")
    ws.row_dimensions[row].height = 45


def add_name(wb, name, ref):
    wb.defined_names[name] = DefinedName(name, attr_text=ref)


def build_assumptions(wb):
    ws = wb.create_sheet("Assumptions")
    ws["A1"] = "Assumptions (yellow cells are inputs; every sheet reads from here)"
    ws["A1"].font = Font(bold=True, size=14)
    ws.append([])
    ws.append(["Assumption", "Value", "Note"])
    style_header(ws, 3, 3)
    for item in ASSUMPTIONS:
        if item[0] is None:
            ws.append([item[1]])
            r = ws.max_row
            for c in range(1, 4):
                ws.cell(r, c).fill = GROUP_FILL
            ws.cell(r, 1).font = BOLD
            continue
        name, label, value, fmt, note = item
        ws.append([label, value, note])
        r = ws.max_row
        cell = ws.cell(r, 2)
        cell.fill = INPUT_FILL
        if fmt:
            cell.number_format = fmt
        add_name(wb, name, f"Assumptions!$B${r}")
        if name == "HoldMeasure":
            dv = DataValidation(type="list", formula1='"Yield on cost,Cash-on-cash"', allow_blank=False)
            ws.add_data_validation(dv)
            dv.add(cell)
        if name == "UnknownAsOccupied":
            dv = DataValidation(type="list", formula1='"Y,N"', allow_blank=False)
            ws.add_data_validation(dv)
            dv.add(cell)

    ws.append([])
    ws.append(["Rehab scope table", "$/sf", "Months", "What it covers"])
    hr = ws.max_row
    style_header(ws, hr, 4)
    for name, psf, months, desc in SCOPES:
        ws.append([name, psf, months, desc])
        r = ws.max_row
        ws.cell(r, 2).fill = INPUT_FILL
        ws.cell(r, 2).number_format = USD
        ws.cell(r, 3).fill = INPUT_FILL
        ws.cell(r, 3).number_format = MO
    first, last = hr + 1, ws.max_row
    add_name(wb, "ScopeNames", f"Assumptions!$A${first}:$A${last}")
    add_name(wb, "ScopePSF", f"Assumptions!$B${first}:$B${last}")
    add_name(wb, "ScopeMonths", f"Assumptions!$C${first}:$C${last}")
    ws.row_dimensions[hr].height = 20

    ws.column_dimensions["A"].width = 52
    ws.column_dimensions["B"].width = 16
    ws.column_dimensions["C"].width = 90
    ws.column_dimensions["D"].width = 60
    ws.freeze_panes = "A4"


def build_deals(wb, deals):
    ws = wb.create_sheet("Deals")
    ws["A1"] = ("Property inputs. One row per property; yellow cells are inputs. "
                "Rows flow automatically to Underwriting, Bid Ladder and Portfolio.")
    ws["A1"].font = BOLD
    for i, (key, header, fmt, width, note) in enumerate(DEAL_COLUMNS, start=1):
        ws.cell(2, i, header)
        ws.column_dimensions[get_column_letter(i)].width = width
        if note:
            from openpyxl.comments import Comment
            ws.cell(2, i).comment = Comment(note, "model")
    style_header(ws, 2, len(DEAL_COLUMNS))
    for r in range(FIRST_ROW, FIRST_ROW + MAX_DEALS):
        for i, (key, header, fmt, width, note) in enumerate(DEAL_COLUMNS, start=1):
            cell = ws.cell(r, i)
            cell.fill = INPUT_FILL
            if fmt:
                cell.number_format = fmt
    for offset, deal in enumerate(deals):
        r = FIRST_ROW + offset
        for i, (key, *_rest) in enumerate(DEAL_COLUMNS, start=1):
            v = deal.get(key, "")
            if v in ("", None):
                continue
            ws.cell(r, i, v)
    rng = lambda key: f"{col_of(key)}{FIRST_ROW}:{col_of(key)}{FIRST_ROW + MAX_DEALS - 1}"
    for key, opts in [("scope", "Light,Medium,Heavy,Gut"),
                      ("occupancy", "Vacant,Occupied,Unknown"),
                      ("lien_pos", "1st,2nd,Unknown")]:
        dv = DataValidation(type="list", formula1=f'"{opts}"', allow_blank=True)
        ws.add_data_validation(dv)
        dv.add(rng(key))
    ws.freeze_panes = "C3"


DEAL_COL = {key: get_column_letter(i) for i, (key, *_r) in enumerate(DEAL_COLUMNS, start=1)}


def col_of(key):
    return DEAL_COL[key]


CLAIMS = "N(Deals!{d:city_claims})"


def bid_cost(b):
    """Cash cost of winning at bid b: price + premium + city claims the bid leaves unpaid.

    The Sheriff pays transfer tax and its costs out of the price, then city
    claims; whatever the remaining proceeds don't cover stays with the property.
    """
    return (f"(({b})*(1+BuyerPremium)+IF({CLAIMS}=0,0,MIN({CLAIMS},"
            f"MAX(0,{CLAIMS}+SheriffCostsFromBid-({b})*(1-RTTPurchase)))))")


def bid_for(x):
    """Highest bid whose bid_cost is at most x (bid_cost rises with the bid, so this inverts it)."""
    covered = f"({CLAIMS}+SheriffCostsFromBid)/(1-RTTPurchase)*(1+BuyerPremium)"
    return (f"IF({CLAIMS}=0,MAX(0,({x})/(1+BuyerPremium)),IF(({x})>={covered},({x})/(1+BuyerPremium),"
            f"MAX(0,(({x})-{CLAIMS}-SheriffCostsFromBid)/(BuyerPremium+RTTPurchase))))")


# Underwriting columns: (key, header, formula, format, group). In formulas,
# {d:key} -> Deals cell, {u:key} -> Underwriting cell on the same row.
UW_COLUMNS = [
    ("id", "Auction ID", "=IF(Deals!{d:auction_id}=\"\",\"\",Deals!{d:auction_id})", "0", "Property"),
    ("address", "Address", "=IF({u:id}=\"\",\"\",Deals!{d:address})", None, "Property"),
    # Result block first so it is visible without scrolling.
    ("best", "Best exit", "", None, "Result"),
    ("rec_max", "Max bid that hits target", "", USD, "Result"),
    ("open_check", "Check vs opening bid", "", None, "Result"),
    ("rec_cash", "All-in cash at max bid", "", USD, "Result"),
    ("rec_profit", "Profit / return at max bid", "", None, "Result"),
    ("box", "Buy box", "", None, "Result"),
    ("alt", "Other exits", "", None, "Result"),
    ("flags", "Flags", "", None, "Result"),

    ("occ", "Occupied? (1 = yes)",
     "=IF({u:id}=\"\",\"\",IF(OR(Deals!{d:occupancy}=\"Occupied\",AND(Deals!{d:occupancy}<>\"Vacant\",UnknownAsOccupied=\"Y\")),1,0))",
     "0", "Timeline"),
    ("rehab_m", "Rehab months",
     "=IF({u:id}=\"\",\"\",IFERROR(INDEX(ScopeMonths,MATCH(Deals!{d:scope},ScopeNames,0)),INDEX(ScopeMonths,3)))",
     MO, "Timeline"),
    ("flip_m", "Flip: sale to sold",
     "=IF({u:id}=\"\",\"\",DeedMonths+{u:occ}*EjectMonths+{u:rehab_m}+SellMonths)", MO, "Timeline"),
    ("hold_m", "Hold: sale to rent start",
     "=IF({u:id}=\"\",\"\",DeedMonths+{u:occ}*EjectMonths+{u:rehab_m}+LeaseUpMonths)", MO, "Timeline"),

    ("rehab", "Rehab budget (blind)",
     "=IF({u:id}=\"\",\"\",N(Deals!{d:bldg_sf})*IFERROR(INDEX(ScopePSF,MATCH(Deals!{d:scope},ScopeNames,0)),INDEX(ScopePSF,3))*(1+Contingency)+BlindAllowance+N(Deals!{d:ext_adders}))",
     USD, "Costs"),
    ("carry_mo", "Carry / month",
     "=IF({u:id}=\"\",\"\",IF(N(Deals!{d:opa_value})>0,Deals!{d:opa_value},N(Deals!{d:arv}))*TaxRate/12+VacantInsMo+SecuringMo+UtilitiesMo+N(Deals!{d:hoa_mo}))",
     USD, "Costs"),
    ("common", "Fixed deal costs (fees, legal, possession, liens)",
     "=IF({u:id}=\"\",\"\",SheriffFees+PurchaseTitle+CompelDeedLegal+{u:occ}*PossessionCost+N(Deals!{d:surv_liens})+N(Deals!{d:hoa_mo})*HOAArrearsMonths)",
     USD, "Costs"),

    ("sell_cost", "Flip: selling costs",
     "=IF({u:id}=\"\",\"\",N(Deals!{d:arv})*(BrokerPct+SellerRTT+SellClosingPct+ConcessionsPct))", USD, "Flip"),
    ("f_flip", "Flip: costs other than bid (pre-sale)",
     "=IF({u:id}=\"\",\"\",{u:common}+{u:rehab}+{u:carry_mo}*{u:flip_m})", USD, "Flip"),
    ("flip_const", "Flip: profit before bid",
     "=IF({u:id}=\"\",\"\",N(Deals!{d:arv})-{u:sell_cost}-{u:f_flip})", USD, "Flip"),
    ("flip_x", "Flip: most the bid may cost (incl. premium, unpaid claims)",
     "=IF({u:id}=\"\",\"\",MIN({u:flip_const}-FlipTarget,"
     "({u:flip_const}-FlipMinAnnROI*{u:flip_m}/12*{u:f_flip})/(1+FlipMinAnnROI*{u:flip_m}/12)))", USD, "Flip"),
    ("flip_max", "Flip: max bid",
     "=IF({u:id}=\"\",\"\"," + bid_for("{u:flip_x}") + ")", USD, "Flip"),
    ("flip_cash", "Flip: peak cash at max bid",
     "=IF({u:id}=\"\",\"\"," + bid_cost("{u:flip_max}") + "+{u:f_flip})", USD, "Flip"),
    ("flip_profit", "Flip: profit at max bid",
     "=IF({u:id}=\"\",\"\",{u:flip_const}-" + bid_cost("{u:flip_max}") + ")", USD, "Flip"),
    ("flip_ann", "Flip: annualized return at max bid",
     "=IF({u:id}=\"\",\"\",IFERROR({u:flip_profit}/{u:flip_cash}/({u:flip_m}/12),0))", PCT, "Flip"),

    ("noi", "Hold: stabilized NOI / yr",
     "=IF({u:id}=\"\",\"\",N(Deals!{d:rent})*12*(1-Vacancy)*(1-MgmtPct-MaintPct-CapexPct)"
     "-N(Deals!{d:arv})*TaxRate-MAX(1,N(Deals!{d:units}))*(InsPerUnit+WaterPerUnit)-N(Deals!{d:hoa_mo})*12)",
     USD, "Hold"),
    ("f_hold", "Hold: costs other than bid",
     "=IF({u:id}=\"\",\"\",{u:common}+{u:rehab}+{u:carry_mo}*{u:hold_m})", USD, "Hold"),
    ("loan", "Hold: refi loan",
     "=IF({u:id}=\"\",\"\",MAX(0,MIN(RefiLTV*N(Deals!{d:arv}),{u:noi}/(RefiDSCR*12*PMT(RefiRate/12,RefiTerm*12,-1)))))",
     USD, "Hold"),
    ("cf", "Hold: cash flow after debt / yr",
     "=IF({u:id}=\"\",\"\",{u:noi}-{u:loan}*12*PMT(RefiRate/12,RefiTerm*12,-1))", USD, "Hold"),
    ("hold_max_yoc", "Hold: max bid at target yield on cost",
     "=IF({u:id}=\"\",\"\"," + bid_for("{u:noi}/HoldTarget-{u:f_hold}") + ")", USD, "Hold"),
    ("hold_max_coc", "Hold: max bid at target cash-on-cash",
     "=IF({u:id}=\"\",\"\",IF({u:cf}<=0,0," + bid_for("{u:cf}/HoldTarget+{u:loan}*(1-RefiCostPct)-{u:f_hold}") + "))",
     USD, "Hold"),
    ("hold_max", "Hold: max bid (selected measure)",
     "=IF({u:id}=\"\",\"\",IF(HoldMeasure=\"Cash-on-cash\",{u:hold_max_coc},{u:hold_max_yoc}))", USD, "Hold"),
    ("hold_cost", "Hold: all-in cost at max bid",
     "=IF({u:id}=\"\",\"\"," + bid_cost("{u:hold_max}") + "+{u:f_hold})", USD, "Hold"),
    ("hold_yoc", "Hold: yield on cost at max bid",
     "=IF({u:id}=\"\",\"\",IFERROR({u:noi}/{u:hold_cost},0))", PCT, "Hold"),
    ("hold_left", "Hold: cash left in after refi",
     "=IF({u:id}=\"\",\"\",{u:hold_cost}-{u:loan}*(1-RefiCostPct))", USD, "Hold"),
    ("hold_coc", "Hold: cash-on-cash after refi",
     "=IF({u:id}=\"\",\"\",IF({u:hold_left}<=0,\"All cash out\",{u:cf}/{u:hold_left}))", PCT, "Hold"),

    ("ws_max", "Wholesale: max bid (assign to a flipper, keep the fee)",
     "=IF({u:id}=\"\",\"\"," + bid_for("{u:flip_const}-BuyerMarginPct*N(Deals!{d:arv})-WholesaleMinFee") + ")",
     USD, "Wholesale"),

    ("td_rev", "Teardown: sale revenue",
     "=IF(OR({u:id}=\"\",N(Deals!{d:td_units})=0),\"\",Deals!{d:td_units}*N(Deals!{d:td_value_unit}))", USD, "Teardown"),
    ("td_cost", "Teardown: costs other than bid",
     "=IF({u:td_rev}=\"\",\"\",DemoCost+N(Deals!{d:td_sf})*BuildCostPSF*(1+SoftCostPct)"
     "+{u:carry_mo}*(DeedMonths+{u:occ}*EjectMonths+BuildMonths+SellMonths)+{u:common}"
     "+{u:td_rev}*(BrokerPct+SellerRTT+SellClosingPct+ConcessionsPct))", USD, "Teardown"),
    ("td_max", "Teardown: max bid",
     "=IF({u:td_rev}=\"\",\"\"," + bid_for("{u:td_rev}-{u:td_cost}-MAX(FlipTarget,DevMarginPct*{u:td_rev})") + ")",
     USD, "Teardown"),
]

RESULT_FORMULAS = {
    "best": "=IF({u:id}=\"\",\"\",IF(MAX({u:flip_max},{u:hold_max})<=0,\"Pass\",IF({u:flip_max}>={u:hold_max},\"Flip\",\"Value-add hold\")))",
    "rec_max": "=IF({u:id}=\"\",\"\",MAX({u:flip_max},{u:hold_max}))",
    "open_check": "=IF({u:id}=\"\",\"\",IF({u:rec_max}<=0,\"Pass\",IF(N(Deals!{d:open_bid})<=1,\"$1 = awaiting minimum bid; re-check the morning of Nov 3\","
                  "IF({u:rec_max}<Deals!{d:open_bid},\"Max bid below opening bid: pass\",\"Room of \"&TEXT({u:rec_max}-Deals!{d:open_bid},\"$#,##0\")&\" over opening bid\"))))",
    "rec_cash": "=IF({u:id}=\"\",\"\",IF({u:best}=\"Flip\",{u:flip_cash},IF({u:best}=\"Value-add hold\",{u:hold_cost},0)))",
    "rec_profit": "=IF({u:id}=\"\",\"\",IF({u:best}=\"Flip\",TEXT({u:flip_profit},\"$#,##0\")&\" profit, \"&TEXT({u:flip_ann},\"0%\")&\"/yr over \"&TEXT({u:flip_m},\"0\")&\" mo\","
                  "IF({u:best}=\"Value-add hold\",TEXT({u:hold_yoc},\"0.0%\")&\" yield on cost; \"&IF(ISNUMBER({u:hold_coc}),TEXT({u:hold_coc},\"0.0%\")&\" cash-on-cash after refi\",\"all cash out at refi\"),\"\")))",
    "box": "=IF({u:id}=\"\",\"\",IF({u:best}=\"Flip\",IF({u:flip_cash}<=FlipCeiling,\"In $300k flip box\",\"Over flip ceiling: needs to be exceptional\"),IF({u:best}=\"Value-add hold\",\"Value-add\",\"\")))",
    "alt": "=IF({u:id}=\"\",\"\",TRIM(IF({u:ws_max}>{u:rec_max},\"Wholesale assignment supports \"&TEXT({u:ws_max},\"$#,##0\")&\". \",\"\")"
           "&IF(AND(ISNUMBER({u:td_max}),N({u:td_max})>{u:rec_max}),\"Teardown/new units supports \"&TEXT({u:td_max},\"$#,##0\")&\".\",\"\")))",
    "flags": "=IF({u:id}=\"\",\"\",TRIM(IF(Deals!{d:lien_pos}=\"2nd\",\"Plaintiff is 2nd: add senior mortgage to surviving liens. \",IF(Deals!{d:lien_pos}<>\"1st\",\"Lien position unconfirmed. \",\"\"))"
             "&IF(N(Deals!{d:arv})=0,\"No ARV yet. \",\"\")&IF(N(Deals!{d:bldg_sf})=0,\"No building sf: rehab is allowance only. \",\"\")"
             "&IF(AND(N(Deals!{d:city_claims})>0,{u:rec_max}>0,{u:rec_max}*(1-RTTPurchase)-SheriffCostsFromBid<N(Deals!{d:city_claims})),\"City claims not fully paid at max bid; unpaid part is counted as cost. \",\"\")&IF({u:occ}=1,\"Occupancy assumed: +\"&TEXT(EjectMonths,\"0\")&\" mo and possession cost. \",\"\")))",
}


def build_underwriting(wb):
    ws = wb.create_sheet("Underwriting")
    ucol = {key: get_column_letter(i) for i, (key, *_r) in enumerate(UW_COLUMNS, start=1)}

    def render(template, r):
        out = template
        for key, letter in ucol.items():
            out = out.replace("{u:" + key + "}", f"{letter}{r}")
        for key, letter in DEAL_COL.items():
            out = out.replace("{d:" + key + "}", f"{letter}{r}")
        assert "{" not in out, out
        return out

    # Group banner row 1, headers row 2.
    prev = None
    for i, (key, header, formula, fmt, group) in enumerate(UW_COLUMNS, start=1):
        ws.cell(2, i, header)
        if group != prev:
            ws.cell(1, i, group).font = BOLD
            prev = group
        ws.cell(1, i).fill = KEY_FILL if group == "Result" else GROUP_FILL
        ws.column_dimensions[get_column_letter(i)].width = 13
    style_header(ws, 2, len(UW_COLUMNS))
    for key, width in [("address", 22), ("open_check", 30), ("rec_profit", 38), ("box", 22),
                       ("alt", 34), ("flags", 45), ("best", 13)]:
        ws.column_dimensions[ucol[key]].width = width

    for r in range(FIRST_ROW, FIRST_ROW + MAX_DEALS):
        for i, (key, header, formula, fmt, group) in enumerate(UW_COLUMNS, start=1):
            template = RESULT_FORMULAS.get(key, formula)
            cell = ws.cell(r, i, render(template, r))
            if fmt:
                cell.number_format = fmt
            if group == "Result":
                cell.fill = KEY_FILL
            if key in ("open_check", "rec_profit", "alt", "flags"):
                cell.alignment = Alignment(wrap_text=True, vertical="top")
    ws.freeze_panes = "C3"
    return ucol


def cost_at(b, r):
    return bid_cost(b).replace("{d:city_claims}", f"{DEAL_COL['city_claims']}{r}")


LADDER_PCTS = [0.20, 0.30, 0.40, 0.50, 0.60, 0.70]


def build_ladder(wb, ucol):
    ws = wb.create_sheet("Bid Ladder")
    ws["A1"] = "Profit and return at several bids. Change the % of ARV in row 2 (yellow) to move the ladder."
    ws["A1"].font = BOLD
    U = lambda key, r: f"Underwriting!${ucol[key]}{r}"
    headers = ["Auction ID", "Address", "ARV", "Opening bid", "Max bid"]
    ws.append([])
    ws.append(headers)
    # Each step: bid, flip profit, flip annualized, hold yield on cost.
    step_cols = []
    col = len(headers) + 1
    for label_pct in ["open"] + LADDER_PCTS + ["max"]:
        step_cols.append((label_pct, col))
        if label_pct == "open":
            title = "At opening bid"
        elif label_pct == "max":
            title = "At max bid"
        else:
            title = None
        ws.cell(2, col, title if title else label_pct)
        if title is None:
            ws.cell(2, col).fill = INPUT_FILL
            ws.cell(2, col).number_format = '0%" of ARV"'
        else:
            ws.cell(2, col).font = BOLD
        for j, sub in enumerate(["Bid", "Flip profit", "Flip ann. return", "Hold yield on cost"]):
            ws.cell(3, col + j, sub)
        col += 4
    style_header(ws, 3, col - 1)
    ws.row_dimensions[2].height = 18

    for r in range(FIRST_ROW, FIRST_ROW + MAX_DEALS):
        lr = r + 1   # ladder data starts one row lower (extra header row)
        idref = U("id", r)
        ws.cell(lr, 1, f"={idref}")
        ws.cell(lr, 2, f"={U('address', r)}")
        ws.cell(lr, 3, f"=IF({idref}=\"\",\"\",N(Deals!{DEAL_COL['arv']}{r}))").number_format = USD
        ws.cell(lr, 4, f"=IF({idref}=\"\",\"\",N(Deals!{DEAL_COL['open_bid']}{r}))").number_format = USD
        ws.cell(lr, 5, f"=IF({idref}=\"\",\"\",{U('rec_max', r)})").number_format = USD
        for label_pct, c in step_cols:
            if label_pct == "open":
                bid = f"$D{lr}"
            elif label_pct == "max":
                bid = f"$E{lr}"
            else:
                bid = f"ROUND({get_column_letter(c)}$2*$C{lr},-3)"
            b = get_column_letter(c)
            ws.cell(lr, c, f"=IF({idref}=\"\",\"\",{bid})").number_format = USD
            ws.cell(lr, c + 1, f"=IF({idref}=\"\",\"\",{U('flip_const', r)}-{cost_at(f'{b}{lr}', r)})").number_format = USD
            ws.cell(lr, c + 2,
                    f"=IF({idref}=\"\",\"\",IFERROR({get_column_letter(c + 1)}{lr}/({cost_at(f'{b}{lr}', r)}+{U('f_flip', r)})/({U('flip_m', r)}/12),0))"
                    ).number_format = PCT
            ws.cell(lr, c + 3,
                    f"=IF({idref}=\"\",\"\",IFERROR({U('noi', r)}/({cost_at(f'{b}{lr}', r)}+{U('f_hold', r)}),0))"
                    ).number_format = PCT
    for i in range(1, col):
        ws.column_dimensions[get_column_letter(i)].width = 11
    ws.column_dimensions["B"].width = 22
    ws.freeze_panes = "C4"


def build_portfolio(wb, ucol):
    ws = wb.create_sheet("Portfolio")
    ws["A1"] = ("Capital plan. Planned bid defaults to the max bid; overwrite it (yellow) with what you intend to bid. "
                "Include = Y to count it against the cash cap.")
    ws["A1"].font = BOLD
    headers = ["Auction ID", "Address", "Best exit", "Max bid", "Planned bid", "Include? (Y/N)",
               "Due Nov 4 (10% + premium)", "Due Nov 18 (90%)", "Cash after the sale (rehab, carry, legal, liens, unpaid city claims)",
               "Total cash in", "Running total (included)", "Profit / return at planned bid"]
    for i, h in enumerate(headers, start=1):
        ws.cell(2, i, h)
    style_header(ws, 2, len(headers))
    U = lambda key, r: f"Underwriting!${ucol[key]}{r}"
    last = FIRST_ROW + MAX_DEALS - 1
    for r in range(FIRST_ROW, last + 1):
        idref = U("id", r)
        ws.cell(r, 1, f"={idref}")
        ws.cell(r, 2, f"={U('address', r)}")
        ws.cell(r, 3, f"={U('best', r)}")
        ws.cell(r, 4, f"={U('rec_max', r)}").number_format = USD
        c = ws.cell(r, 5, f"=IF({idref}=\"\",\"\",{U('rec_max', r)})")
        c.number_format = USD
        c.fill = INPUT_FILL
        c = ws.cell(r, 6, f"=IF({idref}=\"\",\"\",IF({U('rec_max', r)}>0,\"Y\",\"N\"))")
        c.fill = INPUT_FILL
        ws.cell(r, 7, f"=IF({idref}=\"\",\"\",N(E{r})*(DownPct+BuyerPremium))").number_format = USD
        ws.cell(r, 8, f"=IF({idref}=\"\",\"\",IF(N(E{r})>0,N(E{r})*(1-DownPct)+35,0))").number_format = USD
        ws.cell(r, 9, f"=IF({idref}=\"\",\"\",IF(C{r}=\"Value-add hold\",{U('f_hold', r)},{U('f_flip', r)})"
                f"+{cost_at(f'N(E{r})', r)}-N(E{r})*(1+BuyerPremium))").number_format = USD
        ws.cell(r, 10, f"=IF({idref}=\"\",\"\",G{r}+H{r}+I{r})").number_format = USD
        ws.cell(r, 11, f"=IF({idref}=\"\",\"\",SUMIF($F${FIRST_ROW}:F{r},\"Y\",$J${FIRST_ROW}:J{r}))").number_format = USD
        ws.cell(r, 12,
                f"=IF({idref}=\"\",\"\",IF(C{r}=\"Value-add hold\","
                f"TEXT(IFERROR({U('noi', r)}/({cost_at(f'N(E{r})', r)}+{U('f_hold', r)}),0),\"0.0%\")&\" yield on cost\","
                f"TEXT({U('flip_const', r)}-{cost_at(f'N(E{r})', r)},\"$#,##0\")&\" flip profit\"))")
    t = last + 2
    rows = [
        ("Cash due Nov 4 (included lots, less the bidder deposit)",
         f"=MAX(0,SUMIF(F{FIRST_ROW}:F{last},\"Y\",G{FIRST_ROW}:G{last})-BidderDeposit)"),
        ("Bidder deposit (wired before the sale)", "=BidderDeposit"),
        ("Cash due Nov 18 (included lots)", f"=SUMIF(F{FIRST_ROW}:F{last},\"Y\",H{FIRST_ROW}:H{last})"),
        ("Cash after the sale (included lots)", f"=SUMIF(F{FIRST_ROW}:F{last},\"Y\",I{FIRST_ROW}:I{last})"),
        ("Total cash if every included lot is won", f"=SUMIF(F{FIRST_ROW}:F{last},\"Y\",J{FIRST_ROW}:J{last})"),
        ("Cash cap", "=CapitalCap"),
        ("Room under cap", f"=B{t + 5}-B{t + 4}"),
    ]
    for i, (label, f) in enumerate(rows):
        ws.cell(t + i, 1, label).font = BOLD
        ws.cell(t + i, 2, f).number_format = USD
    ws.column_dimensions["A"].width = 44
    ws.column_dimensions["B"].width = 22
    for c in "CDEFGHIJK":
        ws.column_dimensions[c].width = 14
    ws.column_dimensions["L"].width = 30
    ws.freeze_panes = "C3"


README_LINES = [
    ("Sheriff Sale Underwriting Model, Philadelphia Nov 3 2026", True),
    ("", False),
    ("How to use", True),
    ("1. Put each property on the Deals sheet (yellow cells). ARV and rent come from the comps work; liens and lien position from the title check.", False),
    ("2. Change any assumption on the Assumptions sheet. Every number in the model reads from there.", False),
    ("3. Underwriting shows the best exit, the highest bid that still hits the target, and the cash it takes.", False),
    ("4. Bid Ladder shows profit and return at a range of bids. Portfolio adds up the cash against the $1M cap.", False),
    ("", False),
    ("How the max bid is found", True),
    ("Flip: highest bid where ARV minus selling costs, rehab, carry, legal, possession, liens, fees and the 1.5% premium still leaves the $50k target.", False),
    ("Value-add hold: highest bid where stabilized NOI divided by all-in cost is at least 12% (yield on cost, unlevered). "
     "Switch Assumptions > 'Value-add: measure' to Cash-on-cash to test levered cash flow after a refi on the cash left in instead.", False),
    ("Wholesale: bid you could pay and still assign the bid to a flipper who needs 15% of ARV, keeping a $15k fee. Shown as an alternative only.", False),
    ("Teardown: new units sold at the per-unit value you enter, less demo, build, soft costs and carry, with a 15% developer margin.", False),
    ("", False),
    ("Sale rules built in", True),
    ("All cash: 10% of bid + 1.5% premium due Nov 4, 90% due Nov 18. Transfer tax comes out of the bid.", False),
    ("Sale to recorded deed 12 months (range 9-15). No work, renting or eviction until then. Occupied adds 5 months and a possession cost.", False),
    ("City taxes, water/sewer and municipal claims survive if the bid does not cover them; 6 months of condo/HOA dues survive; a senior mortgage survives a 2nd-lien sale. Enter these as surviving liens.", False),
    ("Rehab is a blind budget: $/sf by scope plus a 20% contingency plus a $10k fixed allowance, plus anything visible from the street.", False),
    ("", False),
    ("Not modeled", True),
    ("Risk the sale is pulled, set aside or voided by bankruptcy (cash is tied up but returned). IRS 120-day redemption. Opportunity cost of cash. Price changes during the long hold.", False),
]


def build_readme(wb):
    ws = wb.active
    ws.title = "Read me"
    for i, (text, bold) in enumerate(README_LINES, start=1):
        c = ws.cell(i, 1, text)
        c.alignment = Alignment(wrap_text=True, vertical="top")
        if bold:
            c.font = Font(bold=True, size=14 if i == 1 else 11)
    ws.column_dimensions["A"].width = 140


def load_deals(path):
    numeric = {k for k, h, fmt, *_ in DEAL_COLUMNS if fmt not in (None,)} - {"auction_id"}
    deals = []
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            deal = {}
            for key, value in row.items():
                value = (value or "").strip()
                if value == "":
                    continue
                if key in numeric:
                    try:
                        value = float(value.replace("$", "").replace(",", ""))
                    except ValueError:
                        pass
                deal[key] = value
            deals.append(deal)
    return deals


def set_assumptions(overrides):
    """Apply NAME=value overrides to the assumption defaults."""
    for i, item in enumerate(ASSUMPTIONS):
        if item[0] in overrides:
            name, label, value, fmt, note = item
            new = overrides.pop(name)
            ASSUMPTIONS[i] = (name, label, new if isinstance(value, str) else float(new), fmt, note)
    if overrides:
        raise SystemExit(f"Unknown assumptions: {', '.join(overrides)}")


def build(deals, out):
    global MAX_DEALS
    MAX_DEALS = max(MAX_DEALS, len(deals) + 10)
    wb = Workbook()
    build_readme(wb)
    build_assumptions(wb)
    build_deals(wb, deals)
    ucol = build_underwriting(wb)
    build_ladder(wb, ucol)
    build_portfolio(wb, ucol)
    wb.save(out)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("deals", nargs="?", help="CSV of deals keyed by DEAL_COLUMNS")
    ap.add_argument("-o", "--out", default=str(HERE / "underwriting_model.xlsx"))
    args = ap.parse_args()
    deals = load_deals(args.deals) if args.deals else EXAMPLE_DEALS
    print(build(deals, args.out))


if __name__ == "__main__":
    main()
