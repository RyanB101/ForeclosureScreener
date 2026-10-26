# 80 W Sharpnack St (19119): deep dive and business plan

Auction 1312040, Book-Writ 2609-341, OPA 223035300, FJD case 260201685. Closes Nov 3, 2026 at 1:30 PM. Opening bid $18,400 (posted). Judgment $571,979.30.

Sources are in `sources/` (docket, PhilaDox, Zillow/MLS listing and photos); city records, comps notes and the model are in `research/`.

## Verdict

**Bid. Resell as-is-plus (light make-ready and permits). Walk away at $225,000. Target $175k to $200k.**

- **It's not a rehab, it's a finished flip.** An out-of-state LLC bought it for $225k in May 2024, gutted it (4 bed / 3.5 bath, finished basement, central air, quartz kitchen) and listed it in May 2026 at $499,900. It's now a **short sale at $399,900** after three cuts, unsold after 149 days.
- **Title is clean.** The screen's worst case (a senior Wildcat mortgage surviving) is gone. The plaintiff, LHOME Mortgage Trust 2025-RTL2, holds the 3/2025 Kiavi 1st. Wildcat released its loan 4/2/2025 (mis-indexed at PhilaDox, doc 54408619). No other liens, no US party, no individual defendants.
- **Walk-away $225k.** That is the probability-weighted max bid (70% vacant / 30% occupied, light make-ready plus permits, resale 30% at $385k / 50% at $425k / 20% at $475k) where profit after an 8%/yr cost of capital is still $50k. All-in cash at $225k is about $287k, inside the $300k box.
- **Target $175k to $200k:** about $121k to $146k profit in the base case (31% to 41% a year).
- **Expect a crowd.** This is the best-looking house on the list: staged MLS photos, a $399,900 Zillow ask and an $18,400 opening bid. I expect it to clear at $230k to $280k if it goes, which would be above our walk-away. Don't chase it.
- **~40% chance it's pulled.** If the short sale gets approved, LHOME postpones the sale. Check the B4A status and the MLS status (pending/under contract) the morning of 11/3.

## The property

- 3-story masonry twin, 1920, 20 x 100 lot, RSA-3, on the 80-104 W Sharpnack row of matching 3-story twins in West Mt Airy, a block from Germantown Ave. OPA: 1,878 sf above grade, 4 bed / 3 bath; MLS: "2,800 sf" counting the finished basement, 4 bed / 3 full + 1 half bath.
- **Renovation (31 MLS photos, summer 2026):** open first floor with LVP and recessed lights, powder room; kitchen with white shaker cabinets, quartz waterfall island, 6-burner range and pot filler, farmhouse sink; 2nd floor bedrooms and a double-vanity hall bath; whole 3rd floor owner's suite with en-suite glass shower; finished basement with family room, full bath with dog-wash shower and laundry; new rear patio, fenced yard. Hot-water gas heat plus central air. Typical investor-grade finishes, done well in the photos.
- **No permits at all** for any of it (L&I shows only a 2023 weeds notice). A retail buyer's inspector and lender will flag new baths and HVAC with no permits. Budget to legalize: an expediter, permits, opening a few walls for inspection, fixes.
- **Vacancy since ~spring 2026:** by the time we get possession it will have sat empty for over a year, including a winter. Frozen pipes, a failed boiler or theft of the AC condenser/appliances would push it to the medium or heavy scope.

## Comps and resale value

Comps are in `twin_comps_0.4mi.csv` and `same_model_twins_0.7mi.csv` (city deed records, 24 months).

| Comp | Sale | Read |
|---|---|---|
| **58 W Pomona, same model 1,920 sf 4/3, renovated** | **$515,000 (2/2026)** | Best match, 0.4 mi |
| 104 W Sharpnack, same row, 1,920 sf 4/3, renovated | $449,000 (1/2022) | Same block, older |
| 503 E Walnut Ln, 1,703 sf 5/4, renovated | $494,000 (6/2026) | 0.7 mi |
| 413 High St, 1,800 sf twin, renovated | $442,000 (5/2026) | 0.7 mi |
| 49 W Sharpnack, 1,710 sf row, flipped | $134k → $380,000 (11/2025) | Same street, smaller house |
| 40 W Sharpnack, 1,344 sf row, renovated | $359,900 (3/2026) | Same street, smaller house |
| 138 W Sharpnack, 2,688 sf, renovated | $620,000 (6/2026) | Same street, much bigger |
| Unrenovated same model: 60 W Pomona, 10 W Pomona, 6120 Baynton | $205k to $312k | As-is shell value |

- **Resale base $425k, range $385k to $475k.** The renovated comps say $440k to $515k, but this house hasn't sold at $499.9k → $399.9k in five months. Part of that is the short sale (lender approval scares buyers off) and part is the missing permits. With clean title, permits and fresh marketing, $425k is a reasonable resale, held flat for the 15 to 19 months to resale.
- **Rent:** Zillow's rent estimate is $3,612 a month. At a realistic $3,300, a hold yields only 8% to 10% on cost at $175k to $225k. It's a fallback, not the plan.

## Ownership and debt: why it's being sold

- **Owner:** HBCB Properties LLC. Its address is a mail drop in Wilmington DE, and it was personally served at 6213 Flores Del Mar, Margate FL. It owns nothing else in Philadelphia.
- **Before HBCB:** the house was in the Hedgman/Thornton family from at least 1985. In 2023 the Hedgmans deeded it for $1 to "Leios Corp" (Renair Gladden). After a lawsuit, a court-ordered deed put it back with Bertha Hedgman in March 2024, and the estate then sold to HBCB. This was likely deed theft or a failed wholesale deal. It's resolved of record, and two insured lenders lent past it, but the title company should confirm both lis pendens are closed.
- **Debt stack:** Wildcat hard-money purchase loan plus a Fire Opal gap 2nd (6/2024), refinanced into a Kiavi bridge/rehab loan (3/2025), sold to LHOME 2025-RTL2 (11/2025). The complaint (2/2026) was $545,562, so the Kiavi loan was probably $450k to $500k.
- **Court timeline (docket 260201685):** complaint 2/12/2026 → HBCB served in Florida 3/14 → occupants served at the house 3/30 → default judgment $558,162 (5/12) → damages $571,979 (5/20) → writ 6/2 → 9/1 sale continued to 11/3 by the plaintiff. No answer, no motions, no bankruptcy.
- **My read:** the flipper ran out of time and money. The loan was in default before the house was even listed, and the price has fallen $100k since. The lender is looking at a ~$170k+ loss either way and has kept the sheriff sale on the calendar as the backstop to a short sale. Nobody in this chain has a reason to fight the sale except a short-sale buyer getting there first.

## Sale risk

- **Postponement ~35-40%** (short-sale approval). **Bankruptcy ~5%.** **Goes ahead ~55-60%.**
- **Occupancy: probably vacant (70%).** It's staged, listed and investor-owned. Someone was at the door for service on 3/30/2026, likely a contractor. A finished, empty house over a winter can attract squatters, so the model carries a 30% occupied case (8.5 months and $10k to get possession).
- **Lender bidding:** the $18,400 minimum is only costs. LHOME may still bid on B4A to protect its collateral. If the bidding is driven by the plaintiff, let it go.
- **City claims:** taxes were billed on the old $234,700 value ($3,285 in 2025). Check live tax and water balances; $2,500 is reserved.

## Model results

From `80_w_sharpnack_scenarios.xlsx`, `80_w_sharpnack_max_bids.csv` and `research/model_80_w_sharpnack.py`. Max bid is the bid where profit is $50k after an 8%/yr cost of capital. The ceiling is the bid where profit after the 8% is zero. Assumptions: 12 months to deed, 9.29% selling costs, $521/mo taxes from the sale, and $300/mo insurance and upkeep from the deed.

**Vacant at deed (70%): max bid / ceiling**

| Scope (cost) | Resale $385k | Resale $425k | Resale $475k |
|---|---|---|---|
| Make-ready only ($20k) | $223k / $272k | $255k / $304k | $295k / $344k |
| **Light + permit legalization ($40k), base** | $202k / $251k | **$234k / $283k** | $274k / $323k |
| Medium: freeze/vacancy damage + permits ($75k) | $168k / $217k | $199k / $249k | $239k / $288k |
| Heavy: stripped or failed inspections ($130k) | $116k / $165k | $147k / $196k | $187k / $236k |

**Occupied, 8.5 months to possession (30%): max bid / ceiling**

| Scope (cost) | Resale $385k | Resale $425k | Resale $475k |
|---|---|---|---|
| Make-ready only ($20k) | $197k / $246k | $227k / $277k | $266k / $315k |
| **Light + permit legalization ($40k)** | $177k / $226k | **$207k / $257k** | $245k / $295k |
| Medium ($75k) | $144k / $194k | $174k / $224k | $212k / $262k |
| Heavy ($130k) | $95k / $144k | $125k / $174k | $162k / $212k |

**Base case returns (vacant, $40k scope, $425k resale, ~17 months sale to sale):**

| Bid | All-in cash | Profit | Annual return | Profit after 8% cost of capital |
|---|---|---|---|---|
| $175k | $237k | $146k | 41% | $110k |
| $200k | $262k | $121k | 31% | $84k |
| **$225k** | $287k | $95k | 22% | $59k |
| $250k | $313k | $70k | 15% | $34k |
| $275k | $338k | $45k | 9% | $8k |

## Business plan

**Plan A: resell (recommended).**

1. **Win at $175k to $225k.** Wire 10% plus the 1.5% premium on Nov 4 and the balance by Nov 18.
2. **Right after the sale:** go to the house. If it's empty, check that the heat is on and the pipes are winterized (you can't legally take possession before the deed, but you can ask the listing agent to keep the utilities on, and insure your interest). If someone is there, offer cash for keys ($3k to $5k) once you have the deed.
3. **Make-ready and legalize, about $40k in about 2 months:** a permit expediter for retroactive building, plumbing, electrical and mechanical permits (expect to open some walls), fix whatever a year of vacancy did, paint, punch list, re-stage.
4. **List at $425k to $449k** against 58 W Pomona ($515k) and 104 W Sharpnack ($449k). Advertise permitted work and a clean (non-short-sale) title. Expect about $425k.

**Plan B: rent** at about $3,300 a month if the resale market stalls. Yield is about 8% at a $225k bid, which is a weak fallback.

**Plan C: wholesale** right after the deed to a buyer who wants a finished house. A finished house with clean title should assign easily at $280k to $300k.

## Day-of checklist

- **Morning of 11/3:** check the B4A lot status and the MLS status (if Zillow shows "pending" or "contingent," a short sale is close and the lot may be pulled).
- **Drive-by:** lockbox, sign, staging visible, lights, mail, condenser still out back, any sign of someone living there.
- Live tax and water balances on phila.gov.
- Have the title company look at the 2023-24 Leios Corp lis pendens and confirm the Wildcat release (54408619).
- Bid in steps. Stop at $225k even if the bidding is still going.
