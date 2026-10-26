# 80 W Sharpnack St: max bid by scope x resale x occupancy, 8%/yr cost of capital (same DCF method as 5248 Ridge / 1818 W Master)
# Run: python3 model_80_w_sharpnack.py -> prints tables, writes ../80_w_sharpnack_max_bids.csv, ../80_w_sharpnack_scenarios.xlsx,
#      ../80_w_sharpnack_return_matrix.csv
import math, csv, os
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.dirname(HERE)

R = 0.08; MR = (1 + R) ** (1 / 12) - 1
def df(m): return 1 / (1 + MR) ** m

OPA_MV = 446500                           # 2027 value (post-renovation)
TAX_MO = OPA_MV * 0.013998 / 12           # ~$521/mo from the sale date
INS_UPK_MO = 300                          # vacant-dwelling insurance ~$175 + upkeep/winterizing/lawn $125, from deed
UTIL_MO = 200                             # heat on through winter (3 stories), from possession
SELL_COST = 0.05 + 0.02289 + 0.01 + 0.01  # commission, seller transfer tax, closing, concessions = 9.29%
B4A_FEES = 70; DEED_LEGAL = 2500; TITLE = 2000; CITY_CLAIMS = 2500
SELL_MO = 3

# The house was fully renovated (unpermitted) and staged in spring 2026. "Scope" here is what it needs after ~13 months of
# sitting through a winter, plus getting the work permitted so a buyer's lender/inspector is satisfied.
SCOPES = {  # name: (cost incl. contingency, months)
    "Make-ready (paint, punch list, clean)": (20000, 1),
    "Light + permit legalization (base)": (40000, 2),
    "Medium: vacancy/freeze damage + legalization": (75000, 3),
    "Heavy: stripped or failed inspections": (130000, 4),
}
ARVS = {"Low $385k": 385000, "Base $425k": 425000, "High $475k": 475000}
OCC = {  # name: (deed months, possession months after deed, possession cost)
    "Vacant at deed": (12, 1, 2500),
    "Occupied (squatter/tenant): cash for keys / ejectment 8.5 mo": (12, 8.5, 10000),
}
BASE_SCOPE = "Light + permit legalization (base)"; BASE_ARV = "Base $425k"

def pv_ex_bid(arv, rehab, rmo, deed, poss, pcost):
    p = deed + poss; sale = p + rmo + SELL_MO
    pv = -B4A_FEES - DEED_LEGAL * df(deed / 2) - (TITLE + CITY_CLAIMS) * df(deed) - pcost * df(deed + poss / 2)
    nom = -B4A_FEES - DEED_LEGAL - TITLE - CITY_CLAIMS - pcost
    for m in range(math.ceil(sale)):
        c = TAX_MO + (INS_UPK_MO if m >= deed else 0) + (UTIL_MO if m >= p else 0)
        pv -= c * df(m + .5); nom -= c
    for k in range(rmo):
        pv -= rehab / rmo * df(p + k + .5); nom -= rehab / rmo
    net = arv * (1 - SELL_COST)
    pv += net * df(sale); nom += net
    return pv, nom, sale

K_PV = 0.115 * df(0) + 0.90 * df(0.5)    # 10% + 1.5% premium Nov 4, 90% Nov 18
K_NOM = 1.015

def max_bid(arv, scope, occ, target=50000):
    rehab, rmo = SCOPES[scope]; deed, poss, pcost = OCC[occ]
    pv, nom, sale = pv_ex_bid(arv, rehab, rmo, deed, poss, pcost)
    mb = (pv - target) / K_PV
    return mb, nom - mb * K_NOM, sale

def at_bid(bid, arv, scope, occ):
    rehab, rmo = SCOPES[scope]; deed, poss, pcost = OCC[occ]
    pv, nom, sale = pv_ex_bid(arv, rehab, rmo, deed, poss, pcost)
    cash = bid * K_NOM + rehab + pcost + B4A_FEES + DEED_LEGAL + TITLE + CITY_CLAIMS + TAX_MO * sale
    return nom - bid * K_NOM, pv - bid * K_PV, sale, cash

BIDS = (175000, 200000, 225000, 250000, 275000)
rows = []
for occ in OCC:
    for scope in SCOPES:
        for an, arv in ARVS.items():
            mb, prof, sale = max_bid(arv, scope, occ)
            be, _, _ = max_bid(arv, scope, occ, target=0)
            r = dict(occupancy=occ, scope=scope, rehab=SCOPES[scope][0], arv=arv, sale_month=round(sale, 1),
                     max_bid_npv50k=round(mb, -3), nominal_profit_at_max=round(prof, -3), ceiling_npv0=round(be, -3))
            for b in BIDS:
                p, npv, _, _ = at_bid(b, arv, scope, occ)
                r[f"profit_at_{b//1000}k"] = round(p, -3); r[f"npv8_at_{b//1000}k"] = round(npv, -3)
            rows.append(r)

for occ in OCC:
    print(f"\n{occ}: max bid (NPV@8% = $50k) / ceiling (NPV 0)")
    print(f"{'scope':48s}" + "".join(f"{a:>20s}" for a in ARVS))
    for scope in SCOPES:
        cells = [r for r in rows if r['occupancy'] == occ and r['scope'] == scope]
        print(f"{scope:48s}" + "".join(f"{c['max_bid_npv50k']/1e3:>11.0f}k / {c['ceiling_npv0']/1e3:.0f}k" for c in cells))

W_ARV = {"Low $385k": .3, "Base $425k": .5, "High $475k": .2}
P_VAC = 0.7
pw = sum(W_ARV[a] * (P_VAC * max_bid(ARVS[a], BASE_SCOPE, list(OCC)[0])[0] + (1 - P_VAC) * max_bid(ARVS[a], BASE_SCOPE, list(OCC)[1])[0]) for a in ARVS)
print(f"\nProbability-weighted max bid (70% vacant, base scope, ARV 30/50/20): {pw/1e3:.0f}k")

# return matrix: base occupancy mix shown separately, bids x scope at base ARV
ret = []
for occ in OCC:
    for scope in SCOPES:
        for b in BIDS:
            p, npv, sale, cash = at_bid(b, ARVS[BASE_ARV], scope, occ)
            ret.append(dict(occupancy=occ, scope=scope, arv=ARVS[BASE_ARV], months_sale_to_sale=round(sale, 1), bid=b,
                            all_in_cash=round(cash, -2), profit=round(p, -2), annual_return_on_cash=round(p / cash * 12 / sale, 3),
                            npv_at_8pct=round(npv, -2)))
print("\nBase ARV $425k, Light+permits, vacant: profit / NPV@8% by bid")
for x in ret:
    if x['scope'] == BASE_SCOPE and x['occupancy'].startswith("Vacant"):
        print(f"  bid {x['bid']/1e3:.0f}k: all-in {x['all_in_cash']/1e3:.0f}k, profit {x['profit']/1e3:.0f}k ({x['annual_return_on_cash']:.0%}/yr), NPV8 {x['npv_at_8pct']/1e3:.0f}k")

# hold: rent ~$3,300 (below the $3,612 Rent Zestimate), yield on cost
def hold_yield(bid, rent_mo=3300, rehab=40000, occ="Vacant at deed"):
    deed, poss, pcost = OCC[occ]
    gross = rent_mo * 12
    noi = gross * 0.95 - (OPA_MV * 0.013998 + 2200 + gross * 0.08 + gross * 0.05)
    carry = TAX_MO * (deed + poss + 2) + INS_UPK_MO * (poss + 2)
    cost = bid * K_NOM + rehab + B4A_FEES + DEED_LEGAL + TITLE + CITY_CLAIMS + pcost + carry
    return noi, cost, noi / cost
hold = []
for b in BIDS:
    noi, cost, y = hold_yield(b); hold.append((b, noi, cost, y))
    print(f"Hold at ${b/1e3:.0f}k: NOI ${noi/1e3:.1f}k on ${cost/1e3:.0f}k all-in = {y:.1%} yield on cost")

with open(os.path.join(OUT, "80_w_sharpnack_max_bids.csv"), "w", newline="") as f:
    wr = csv.DictWriter(f, fieldnames=list(rows[0])); wr.writeheader(); wr.writerows(rows)
with open(os.path.join(OUT, "80_w_sharpnack_return_matrix.csv"), "w", newline="") as f:
    wr = csv.DictWriter(f, fieldnames=list(ret[0])); wr.writeheader(); wr.writerows(ret)

# ---- workbook
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
wb = Workbook(); ws = wb.active; ws.title = "Matrix"
bold = Font(bold=True); hdr = PatternFill("solid", fgColor="DDE7F0"); basef = PatternFill("solid", fgColor="FFF2CC")
ws["A1"] = "80 W Sharpnack St (auction 1312040): max bid = NPV at 8%/yr equals $50k; ceiling = NPV 0"; ws["A1"].font = Font(bold=True, size=12)
ws["A2"] = "Already renovated (unpermitted) and listed as a short sale at $399,900. Plaintiff holds the 1st (Wildcat released). Deed 12 mo. Selling costs 9.29%. Bid paid 11.5% Nov 4, 90% Nov 18."
r0 = 4
for occ in OCC:
    ws.cell(r0, 1, occ).font = bold
    ws.cell(r0 + 1, 1, "Scope (cost)").font = bold
    for j, a in enumerate(ARVS):
        c = ws.cell(r0 + 1, 2 + j, f"Resale {a}: max / ceiling"); c.font = bold; c.fill = hdr
    for i, scope in enumerate(SCOPES):
        ws.cell(r0 + 2 + i, 1, f"{scope} ${SCOPES[scope][0]/1e3:.0f}k")
        for j, a in enumerate(ARVS):
            rr = [x for x in rows if x['occupancy'] == occ and x['scope'] == scope and x['arv'] == ARVS[a]][0]
            c = ws.cell(r0 + 2 + i, 2 + j, f"${rr['max_bid_npv50k']/1e3:.0f}k / ${rr['ceiling_npv0']/1e3:.0f}k")
            if scope == BASE_SCOPE and a == BASE_ARV: c.fill = basef
    r0 += 2 + len(SCOPES) + 1
ws.cell(r0, 1, f"Probability-weighted walk-away (70% vacant / 30% occupied, base scope, resale 30/50/20): ${pw/1e3:.0f}k").font = bold
ws.column_dimensions["A"].width = 58
for col in "BCD": ws.column_dimensions[col].width = 28

d = wb.create_sheet("Detail"); d.append(list(rows[0].keys()))
for r in rows: d.append(list(r.values()))
for c in d[1]: c.font = bold; c.fill = hdr
rm = wb.create_sheet("Returns by bid"); rm.append(list(ret[0].keys()))
for r in ret: rm.append(list(r.values()))
for c in rm[1]: c.font = bold; c.fill = hdr
h = wb.create_sheet("Hold"); h.append(["bid", "NOI ($3,300/mo rent)", "all-in cost", "yield on cost"])
for b, noi, cost, y in hold: h.append([b, round(noi), round(cost), round(y, 3)])

c = wb.create_sheet("Calculator")
inputs = [("Bid", 225000), ("ARV (resale)", 425000), ("Rehab / make-ready incl. contingency", 40000), ("Months to deed", 12),
          ("Months to possession after deed", 1), ("Possession cost (cash for keys / ejectment)", 2500), ("Rehab months", 2),
          ("Months to sell", SELL_MO), ("City claims reserve", CITY_CLAIMS), ("Legal to compel deed", DEED_LEGAL),
          ("Title / recording", TITLE), ("B4A fees", B4A_FEES), ("RE tax per month", round(TAX_MO)),
          ("Insurance + upkeep per month (from deed)", INS_UPK_MO), ("Utilities per month (from possession)", UTIL_MO),
          ("Selling costs % of ARV", SELL_COST), ("Buyer's premium %", 0.015), ("Opportunity cost %/yr", R)]
c["A1"] = "Calculator (edit column B)"; c["A1"].font = Font(bold=True, size=12)
for i, (k, v) in enumerate(inputs, start=3):
    c.cell(i, 1, k); c.cell(i, 2, v).fill = basef
B = {k: f"B{i}" for i, (k, _) in enumerate(inputs, start=3)}
o = 3 + len(inputs) + 1
RH = B['Rehab / make-ready incl. contingency']
calc = [
    ("Sale month", f"={B['Months to deed']}+{B['Months to possession after deed']}+{B['Rehab months']}+{B['Months to sell']}"),
    ("Cash at auction (bid + premium)", f"={B['Bid']}*(1+{B["Buyer's premium %"]})"),
    ("Carry (tax, insurance, upkeep, utilities)", f"={B['RE tax per month']}*B{o}+{B['Insurance + upkeep per month (from deed)']}*(B{o}-{B['Months to deed']})+{B['Utilities per month (from possession)']}*(B{o}-{B['Months to deed']}-{B['Months to possession after deed']})"),
    ("Fixed costs (legal, title, claims, fees, possession)", f"={B['Legal to compel deed']}+{B['Title / recording']}+{B['City claims reserve']}+{B['B4A fees']}+{B['Possession cost (cash for keys / ejectment)']}"),
    ("Net sale proceeds (after selling costs)", f"={B['ARV (resale)']}*(1-{B['Selling costs % of ARV']})"),
    ("Profit before cost of capital", f"=B{o+4}-B{o+1}-B{o+2}-B{o+3}-{RH}"),
    ("Approx. 8% charge on cash tied up", f"=(B{o+1}*B{o}+{RH}*({B['Rehab months']}/2+{B['Months to sell']})+(B{o+2}+B{o+3})*B{o}/2)*{B['Opportunity cost %/yr']}/12"),
    ("Profit after cost of capital", f"=B{o+5}-B{o+6}"),
    ("Annualized return on peak cash", f"=B{o+5}/(B{o+1}+B{o+2}+B{o+3}+{RH})*12/B{o}"),
]
for i, (k, f_) in enumerate(calc):
    c.cell(o + i, 1, k).font = bold; c.cell(o + i, 2, f_)
    c.cell(o + i, 2).number_format = "0.0%" if "Annualized" in k else "#,##0"
for i in range(3, 3 + len(inputs)):
    v = c.cell(i, 2).value; c.cell(i, 2).number_format = "0.0%" if isinstance(v, float) and v < 1 else "#,##0"
c.column_dimensions["A"].width = 52; c.column_dimensions["B"].width = 16
wb.save(os.path.join(OUT, "80_w_sharpnack_scenarios.xlsx"))
print("wrote csv + xlsx")
