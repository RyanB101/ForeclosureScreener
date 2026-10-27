# 1234 E Columbia Ave (19125, Fishtown): deep dive and business plan

Auction 1309707 · Book/Writ 2508-384 · OPA 181094000 · CP Aug 2023 No. 02797 · was set to close 1:50 PM Nov 3, 2026 · opening bid $48,900
Prepared Oct 27, 2026 from city records (OPA, RTT index, permits, L&I, 311), the FJD docket (this case plus the owner's other cases), and project comps. Raw notes: `research/notes.md`. Docket: `sources/docket_230802797.md`. Scenarios: `1234_e_columbia_scenarios.xlsx` (sheet "Matrix 8pct DCF" plus the standard model) and `research/dcf_matrix_8pct.csv`.

## Bottom line

- **Not selling Nov 3.** On Oct 19 the court granted the plaintiff's motion and moved the sale to **Feb 2, 2027**. The sheriff will announce the postponement on Nov 3. Take it off the Nov 3 bid sheet.
- **Do not bid on Feb 2 either unless two title problems are fixed first.**
  1. **Sarah Shensky is not a defendant.** She is on the 2002 deed and signed the 2004 mortgage being foreclosed, and she is alive (named on the city's Jan 2026 tax lien; a 2023 city filing has her at 1246 E Susquehanna Ave, so the couple may be separated). Only Gregg was sued. A sheriff sale that leaves out a record owner and mortgagor does not wipe out her interest. We could pay $350k and end up co-owning the house with her, or have the sale set aside.
  2. **The IRS was not named.** There is a 2010 federal tax lien against both spouses. The sale doesn't touch a federal lien when the US isn't a party. It is probably expired (10-year life, no refiling found), but that is unconfirmed.
- **Bankruptcy in the background.** Gregg filed bankruptcy 25-14442-PMM (EDPA) in Nov 2025. Since then the lender has postponed every two months, which looks like a Chapter 13 plan in progress. If the plan is being paid, the house may never come to sale.
- **The deal itself is excellent if title gets cleaned up.** Base case: buy at about $350k, put in a ~$209k medium rehab, sell at about $820k. That nets around $138k nominal over ~28 months, even under ryan's 8.5-month occupied rule.

## Max bid (8%/yr cost of capital, $50k left after every cost)

Same method as 2321 Madison Sq: every cash flow discounted at 8%/yr; 11.5% due Nov 4 and 90% two weeks later; legal $2.5k, title $2k, city claims reserve $2.5k; RE tax from sale (full $560k OPA, homestead ends); insurance and upkeep from deed; 9.3% selling costs; deed 12 months; rehab blind at $40/$65/$95 per sf x 1.2 + $10k on 2,556 sf; resale 3 months.

| Scope (rehab) | ARV $750k | **ARV $820k** | ARV $900k | Walk-away (NPV 0) at $820k |
|---|---|---|---|---|
| **Owner leaves on cash for keys (3 mo, $10k)** | | | | |
| Light ($133k) | $388k | $443k | $506k | $493k |
| Medium ($209k) | $317k | $371k | $434k | $421k |
| Heavy ($301k) | $231k | $286k | $347k | $335k |
| **Occupied, ryan's rule (8.5 mo, $12k)** | | | | |
| Light ($133k) | $366k | $419k | $479k | $468k |
| **Medium ($209k)** | $296k | **$349k** | $409k | $398k |
| Heavy ($301k) | $214k | $266k | $326k | $316k |

A 15-month deed takes about $10k off each cell. The standard underwriting model (8% simple on peak cash, same scopes) gives $365k for the base (`1234_e_columbia_max_bids.csv`); the screen's $342k matches the DCF.

**If it comes back clean for Feb 2:** walk-away **$350k**, target **$300-325k**, and never above $400k under any scope. All-in at $350k is about **$600k**, double the $300k box but inside the $1M cap. That is why this one has to be exceptional, and on numbers alone it is: about $140k profit at the max bid.

**Hold?** No. A renovated 2,556 sf Fishtown row rents for about $4,000-4,500 a month (HUD 5BR $3,040). On ~$600k all-in that yields 5-6%, half the 12% target.

## The property

- 3-story brick row, 2,556 sf, about 1915. The lot is 20 x 104 ft, the deepest on the block, with a 347 sf open rear area. Zoned RSA5 (single family). No central air.
- OPA rates it 4/4 (below average). The owner's recent permits are small: a roof replacement permit (Nov 2024, expired, maybe never finaled), a toilet and shower swap with underfloor piping (Apr 2025), and 3 switches, a GFCI and smoke detectors (May 2025). That reads as patching for an inspection or refinance, not a renovation. Budget **Medium** ($209k). Light ($133k) is the upside if the roof and bath work hold up.
- No open L&I cases and no rental or vacant license. The owner has been there since 2002 and has a homestead exemption.

## ARV: $820k (range $750-900k)

Same street, same kind of house:
- **1409 E Columbia**, 2,910 sf: estate sale $460k (Oct 2023), full rehab (rewire, 14 fixtures, ductwork), then sold **$987k** (Nov 2024, $339/sf). This is the template.
- **1306 E Columbia**, 2,456 sf, average condition: **$740k** (Jul 2026, $301/sf).
- 1418 E Columbia, 1,903 sf, renovated: $651.5k (Jan 2026, $342/sf). 1450 E Columbia, 2,112 sf: $615k (Nov 2025). 1438 E Columbia, unrenovated: $515k (May 2025).
- Nearby older 3-story brick: 1342 Marlborough 2,522 sf $790k; 1313 Frankford $830k; 1626 E Eyre $825k.

$820k is $321/sf: below the 1409 flip and above 1306's average-condition sale. As-is is about $600k. 19125 prices are flat (-1.4% $/sf YoY) but liquid: 70+ row sales of this size within 0.4 mi in two years (`row_comps_0.4mi.csv`).

## Why it's being sold, and why it keeps not selling

| Date | Event |
|---|---|
| Aug 2023 | US Bank Trust (LB-Igloo, a non-performing-loan trust) files on the 2004 Fleet/BofA mortgage: $182k |
| Aug 2023 | City files a tax-sale petition for $55.6k of unpaid RE tax; withdrawn Oct 2023 |
| Dec 2023-Dec 2024 | Four diversion conferences, "attempting to reach an agreement"; none reached |
| Apr 2025 | Default judgment **$203,262** |
| Aug and Oct 2025 | Gregg (pro se, in forma pauperis) gets two postponements |
| Nov 2025 | Gregg files bankruptcy 25-14442-PMM |
| Jan-Oct 2026 | Lender postpones every sale date: Jan, Mar, May, Jul, Sep, Nov 2026 |
| Oct 19 2026 | Nov 3 sale moved to **Feb 2, 2027** |

The owner, Gregg Shensky, has been a Fishtown local since 1981 and a small investor. He bought 413 Moyer at a 2003 sheriff sale and resold it, and he **lost 710 Miller St at sheriff sale in Oct 2016** ($165k, BNY Mellon). There is a 2010 IRS lien and a 2016 student-loan suit, and the city has filed an RE tax lien every year since 2015. He has $250k+ of equity here (more if the IRS lien is dead), so he has every reason to keep stalling. Even so, he has let a house go before.

## Liens and the waterfall

Paid out of the bid, in order: 4.578% transfer tax, ~$2.5k sheriff costs, city claims (likely $65-75k of RE tax and water; unverified because the tax balance lookup is closed), then the plaintiff (~$215-225k by Feb 2027). The bid has to clear **about $300-315k** before anything is left over for the owner. Anyone who bids under ~$300k doesn't pay everything off, but the buyer still takes the property free of the mortgage and city claims. City claims are paid only as far as the bid covers them; the model counts anything unpaid as a cost.

**Not wiped out by this sale:** Sarah's ownership share and the IRS lien (see Bottom line).

## What would change the answer before Feb 2, 2027

1. **Docket:** watch for an amended complaint or a new action that adds Sarah Shensky (and the US). Without that, pass.
2. **PACER 25-14442-PMM:** check whether the plan is confirmed and being paid (the sale likely never happens), whether the lender got relief from stay, or whether the case was dismissed.
3. **IRS lien image (FJD 101020088, $5):** get the assessment dates to confirm it has lapsed.
4. **RE tax balance** (city revenue lookup) to firm up the waterfall.
5. **Drive-by:** confirm the roof, whether anyone lives there, and what's on the 104-ft rear.

## Verdict

**Pass for Nov 3: it's postponed.** Re-run for Feb 2, 2027 only if Sarah Shensky is added as a defendant (or her interest is otherwise resolved of record) and the IRS lien is confirmed lapsed or the US is joined. If both are fixed, bid with walk-away **$350k** and target **$300-325k**.
