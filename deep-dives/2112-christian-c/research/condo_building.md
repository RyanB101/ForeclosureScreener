# 2112 Christian St, Phila PA 19146: condo association and building research
Researched 2026-10-21. Sources: Carto (phl.carto.com) tables opa_properties_public, rtt_summary, permits, violations, case_investigations, business_licenses; AIS (api.phila.gov/ais); web listings (Compass, Coldwell Banker, Trulia).

## Correction to the inputs
- OPA account numbers: **Unit A = 888303718**, Unit B = 888303720, Unit C = 888303722. 888303720 is Unit B, not A.
- AIS: base address 2112 Christian St, DOR parcel 007S070080, PWD parcel / L&I parcel 127496, Eclipse location 128983782, BIN 1391070, zoning RM-1. 4 PWD water accounts (2306002112001-004). There are also AIS unit aliases "#2" and "#3", which may be old floor-based unit numbers. Zoning archive document id 219-122293 is not retrieved.

## 1. Condominium regime (VERIFIED from rtt_summary)
- **Condo name:** "2102,12 Christian Street Condominiums". This is one **two-building, 6-unit condo**: 2102 Christian (units A, B, C) plus 2112 Christian (units A, B, C). It is not a 3-unit stand-alone condo. Listings call the association "2102, 12 Christian St Condo Association" (Unit C 2021 MLS) and "2102,2112 Christian Street Condominiums" (Unit A 2024 MLS).
- **Recorded instrument:** **Doc ID 51672668**, recorded **2007-04-17**, type "AMENDMENT TO CONDOMINIUM". The grantor is 2000/2100 Christian Street Associates LP and the grantee is "2102,12 Christian Street Condominiums". It is indexed against 2102A/B/C and 2112A/B/C.
- No "DECLARATION OF CONDOMINIUM" row exists for 2102/2112 in rtt_summary. **Inference:** the 2007-04-17 instrument is either the declaration itself, indexed as an amendment, or an amendment adding these buildings to an earlier declaration. Sister phases by the same developer were recorded as follows: 2016-26 Christian (doc 51469302, 2006-06-22, coded "DEED MISCELLANEOUS"), 2015/17/35 Christian declaration (doc 51554803, 2006-10-19), 2113-26 Christian declaration (doc 51942601, 2008-07-25), and 2124 Christian declaration (doc 52186422, 2010-03-12).
- Gary S. Reuben (likely the developer's attorney or escrow agent) recorded "DEED MISCELLANEOUS" doc 51757361 on 2007-08-20 for "2102-12 Christian St Unit B" (grantee: developer and "Constandino Associates LP"). The contents are unknown.
- **Text access:** The declaration, plats/plans and LCE assignments are only on **PhilaDox** (Phila Recorder of Deeds), a paid subscription service. They were not accessible here and I did not read them. No web copy was found.

## 2. Conversion / developer (VERIFIED)
- Developer: **2000/2100 Christian Street Associates LP** with **Costandino (variously "Constandino") Development Associates**. Lender and subsidy parties: PHFA, Redevelopment Authority (RDA), PHDC, Ingerman Regis Corp. This was a publicly subsidized scattered-site rehab program covering about 20 buildings in the 2000-2100 blocks of Christian, from 2006 to 2010.
- Subsidy mortgages on 2112 were released or satisfied as follows: RDA release 51845702 (2008-01-25), Ingerman releases at each unit sale, RDA satisfaction 53937870 (2022-01-08), and Ingerman satisfaction 53947135 (2022-01-18, other addresses). **Inference:** the original deeds may carry affordability or resale covenants. Unit C's low first price ($111,325) suggests it may have been an affordable-priced unit. Have the title search confirm that no covenant survives.
- **Original sales from the developer:**
  - B: 2008-01-24, $169,900, to Ariel Feinberg (doc 51845704).
  - C: 2009-04-17, $111,325, to Charles D. McCall III (doc 52053385).
  - A: 2009-11-24, $185,400, to Kelly Celenza (doc 52152998). It was listed in 2007 at $212k, failed to sell, and was relisted.
- **Unit C chain:** McCall III → McCall III & Elizabeth McCall (2011-05-26, $1) → **Richard L. Shellenberger, 2021-04-05, $180,000** (doc 53841352). Shellenberger's mortgage is to Guaranteed Rate (53841353, 2021-06-02) and was assigned to **PHFA** (53862435, 2021-07-28). PHFA is probably the foreclosing lender, but this is not confirmed here.
- **Unit B chain:** Feinberg → Drobnes (2013) → Victor Lobanov (2016, $174k) → Tumu (2022 mortgage; the deed into Tumu is missing from rtt) → Pooja Pahwa, 2024-09-20, $260k.
- **Unit A chain:** Celenza → Pooja Pahwa, 2024-05-28, $280k.
- **Inference:** Pahwa now owns 2 of the 3 units at 2112, and 2 of the 6 units in the association. She has meaningful voting weight.
- No conversion-era building permits appear in the open-data permits table. That table starts in about 2007 or later, so older Hansen records may be absent.

## 3. L&I permits, violations, cases (VERIFIED)
- **ZP-2021-013070 (Zoning), issued 2021-11-04, status "Issued" (never marked completed):** "FOR THE ERECTION OF A ROOF DECK ON THE THIRD FLOOR LEVEL, ACCESSORY TO EXISTING HOUSEHOLD LIVING." It is recorded against the base address with no unit. Applicant: Elizabeth Johnson, West Chester PA. Area of disturbance: 144 sf. Use category: multi-family.
- **No building permit** for a deck at 2112 exists in open data. That means no CP- or RP- permit, no inspection and no certificate of occupancy. **Inference:** either the deck was never built under this approval, or it was built without the required building permit. The bidder should treat deck legality as unverified.
- The deck pre-dates the zoning permit: the Jan-2021 MLS listing already mentioned a "PRIVATE DECK". The 2021 zoning permit may be for a new or replacement deck or a legalization.
- Sister building 2102 Unit C (also a 3rd-floor unit) received the following permits:
  - **CP-2021-008568**, roof deck above 2nd-floor roof accessed via existing 3rd-floor wall opening, issued 2022-02-22, completed with CO on 2022-04-29.
  - **CP-2022-006489**, pergola on rear roof deck, completed 2023-02-07.
  - This is the likely analogue: a deck on the rear 2nd-story (ell) roof, entered from the 3rd-floor unit.
- Other 2102 permit: 2019 plumbing permit (2102 A).
- **Violations: none. Case investigations: none.** The search covered 2112 Christian by address and by all three OPA numbers.

## 4. Rental licenses (VERIFIED, business_licenses)
- **#703288:** Charles McCall (then owner of Unit C). Address 2112 Christian St, no unit listed. Initial issue 2016-05-29, last issued 2020-04-16, expired 2021-05-28, status Closed. Mailing address 759 S Mole St. **This was Unit C's rental history from 2016 to 2021**, consistent with the MLS statement that the unit "has been successfully rented... last tenant paid $1,295/month."
- **#863293:** Indexed to **Unit B** (OPA 888303720, Lobanov as licensee), but its business/legal name is "2112 Christian St #C". Issued 2021-03-10, expired 2022-03-09, inactive since 2022-05-07. **Ambiguous:** this is probably Lobanov's unit-B license with a mislabeled name, but it is possible it relates to C.
- **No active rental license exists on any unit.** None has been issued under Shellenberger or Pahwa. Occupancy of C today is unknown.

## 5. Association: dues, management, assessments
- **Dues (from listings, VERIFIED as listing data):**
  - Unit C: $212/mo (Jan-2021 MLS), covering water, gas, common-area maintenance and exterior building maintenance.
  - Unit A: $394/mo (2024 MLS), covering water/sewer, gas (heat and cooking), master policy, snow removal and shared utilities.
  - 2102 C: $281/mo (Aug-2026 MLS).
  - **Inference:** dues have risen. Unit C is probably about $230-300/mo now, but get the current figure from the association.
- **Utilities shared:** gas and water are paid by the association, which means common meters. Unpaid dues therefore matter, and a PA condo lien has priority for 6 months of assessments, 68 Pa.C.S. 3315. The bidder should get a payoff or estoppel.
- **Management company:** not found. **Inference:** this is likely self-managed.
- **Special assessments:** none found in any public source.
- **PA DOS corporate registration:** not found. A web search found no entity. The aggregator filed.dev rate-limited the probe, and the PA DOS site was not queried directly.

## 6. Deck: limited common element (LCE) or common element?
- **VERIFIED:** The Unit C 2021 MLS remarks say: "Enter on the second floor, up the steps to a wide open plan... Easy access to PRIVATE DECK." Unit C is the 3rd-floor unit. Listings do not use the words "limited common element". Unit A has a private rear patio (ground level, fenced), described as "private".
- **NOT VERIFIED:** whether the deck is an LCE assigned to C, part of the unit, or a general common element. The answer is only in the declaration and plats (doc 51672668 and any related instrument) on PhilaDox.
- **Inference:** a roof deck on the shared roof or ell, reachable only from Unit C, is commonly designated an LCE for that unit. But the deck pre-dates the 2021 zoning permit and post-dates the 2007 declaration. If it was added after 2007 without a recorded amendment assigning it, it may legally be a general common element that C merely has exclusive practical access to, possibly with association-approval issues. A roof deck has no completed building permit or CO.
- **Recommended:** buy doc 51672668 and any later amendment from PhilaDox (a few dollars per page). Request from the association: the resale certificate (68 Pa.C.S. 3407), the board's deck approval if any, the budget, the reserve figure, and arrears for Unit C.

## Not found
- Original declaration text and plats.
- Association EIN or corporation.
- Management company.
- Current dues and arrears.
- Special assessments.
- Any web copy calling the deck an LCE.
- Building permit or CO for the 2112 deck.
- Auction.com page details (the fetch returned an empty page). Trulia shows an Auction.com listing posted 2026-10-20 with an estimate of $194.6k.

Sources: phl.carto.com SQL API; api.phila.gov/ais/v1/search/2112 christian st; compass.com/listing/2112-christian-street-unit-c-philadelphia-pa-19146/688459846056077529/; compass.com/homedetails/2112-Christian-St-Unit-A-Philadelphia-PA-19146/1526941172541272297_lid/; coldwellbankerhomes.com/pa/philadelphia/2102-christian-st-c/pid_72992348/; trulia.com/home/2112-christian-st-c-philadelphia-pa-19146-87763347
