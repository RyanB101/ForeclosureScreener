# 2112 Christian St Unit C (OPA 888303722): docket, title chain, occupancy context

Researched 2026-10-21. Sources: FJD Civil Docket Access (fjdefile.phila.gov, public docket report, name search, and judgment search), the City of Philadelphia Carto API (rtt_summary, opa_properties_public, business_licenses, violations, case_investigations), and web searches.

## 1. Foreclosure docket: PHFA v. Shellenberger, No. 250503717 (VERIFIED from the FJD docket)

- **Plaintiff:** Pennsylvania Housing Finance Agency (PHFA), 211 N Front St, Harrisburg. PHFA is the actual holder. The law firm is RAS (raslg.com, Mount Laurel NJ). Attorneys of record include Hunsberger, Freedman, Harris and Cordero. Queen Stewart of Pincus Law and Danielle Coleman also appear for the plaintiff.
- **Case type:** Residential Owner Occupied mortgage foreclosure. It was filed 29 May 2025, with $125,530.46 claimed in the complaint. The defendant's address of record is 2112 Christian St Apt C.
- **Service:** Personal service failed. On 30 Jul 2025 the court allowed alternative service by posting and mail, and service was made on 19 Aug 2025.
- **Diversion program:**
  - The first conciliation conference was in Sep 2025. The defendant **appeared**.
  - The 10 Oct 2025 order notes "PENDING DEFENDANT TO RETURN EXECUTED LOAN MODIFICATION DOCUMENTS", which means a loan modification was offered.
  - The second conference was 20 Nov 2025. The defendant **failed to appear**, and on 5 Dec 2025 the case was removed from the program. His answer deadline was 19 Jan 2026.
- **Judgment:** Default judgment for failure to answer, entered **16 Feb 2026, $127,712.24**. The writ of execution issued the same day.
- **Notice of sale:** Served by posting and mail on 27 Feb 2026.
- **Sale postponements** (all filed by the plaintiff, none by the defendant):
  - 5 May 2026 was continued to 7 Jul 2026.
  - 7 Jul 2026 was continued to 1 Sep 2026.
  - 1 Sep 2026: on 26 Aug 2026 the plaintiff filed a motion to postpone ("Executed MTPP"). Judge Garcia's order of 27 Aug 2026 moved the sale to **3 Nov 2026**, and a notice of continuance was filed 17 Sep 2026.
- **Defendant activity:** In this case the defendant has no attorney and has filed nothing: no answer, no petition to postpone, no petition to set aside. There are no motions on the case motions list.
- **Bankruptcy:** No suggestion of bankruptcy is on the docket as of the last entry (17 Sep 2026).

### Prior foreclosure: PHFA v. Shellenberger, No. 230601895 (VERIFIED)
- Filed 20 Jun 2023, with $128,368.85 claimed. It went through alternative service and the diversion program.
- The 29 Apr 2024 order said "parties are attempting to reach an agreement".
- **Discontinued without prejudice on 10 Jun 2024.**
- Inference: the 2023 default was cured, probably by a loan modification, and the loan defaulted again within about a year.

### Condo association case: 2102,12 Christian St Condominium Assn v. Shellenberger, No. 221201846 (VERIFIED)
- Confession of judgment for $8,513.51 for unpaid assessments, filed 20 Dec 2022. He was personally served at the unit on 3 Apr 2023.
- He filed **pro se** as "Richard L Shellenberger Jr" and petitioned to open or strike. The judgment was **STRICKEN** (Padilla, J., orders of 6/12/2023 and 7/12/2023, after reconsideration).
- No later association suit appears in the FJD name search. The judgment search shows the condo entry as a judgment, but it was stricken.
- This shows the owner can litigate on his own. Condo assessments were in dispute in 2022, so current HOA arrears are possible but unknown.

### Other FJD name hits
- 2017–2018 cases name a "Richard Shellenberger" of Manheim, PA (Lancaster County) as plaintiff against Kreider Farms and Clark-Reliance. A 2013 case lists a Richard Shellenberger at 640 N Broad St #831. **Not confirmed to be the same person.** Do not rely on them.

## 2. Title chain (VERIFIED from Carto rtt_summary)

| Date | Doc | Parties | Doc ID / consideration |
|---|---|---|---|
| 2007-04-17 | Condo amendment creating units 2112A/B/C | 2000/2100 Christian Street Associates LP | 51672668 |
| 2009-04-17 | Deed for Unit C (developer sale) | 2000/2100 Christian St Assoc LP to Charles D McCall III | 52053385, $111,325 |
| 2009-04-21 | Mortgage | McCall to MERS/TD Bank | 52053388 (satisfied 2012) |
| 2011-05-26 | Deed | McCall to Charles D III and Elizabeth McCall | 52369058, $1 |
| 2012-01-13 | Mortgage | McCalls to MERS/TD Bank | 52434808 (satisfied 2021-06-15) |
| 2021-04-05 | **Deed** | McCalls to **Richard L Shellenberger** | 53841352, **$180,000** |
| 2021 (display date 2021-06-02) | **Mortgage** | Shellenberger to **Guaranteed Rate Inc** | 53841353 (ID follows the deed directly) |
| 2021-07-28 | **Assignment** | Guaranteed Rate to **PHFA** | 53862435 |

- The inferred chain is confirmed: a Guaranteed Rate purchase-money mortgage assigned to PHFA, which is the plaintiff.
- **No second mortgage** (PHFA assistance or otherwise), **no later deed**, and no other recorded mortgage or lien instrument on Unit C appears in rtt_summary.
- Developer-era building-level PHFA, RDA and PHDC mortgages are all released or satisfied (2006–2022).
- The mortgage principal is not shown in RTT.
- Caveat: rtt_summary does not list judgment liens or municipal liens. Those are indexed separately, and only the FJD hits above were found.

## 3. Bankruptcy
- No public mention was found of a bankruptcy by Richard L. Shellenberger in E.D. Pa. Web searches returned nothing relevant.
- The CourtListener RECAP API rate-limited me (HTTP 429), so I could not check it.
- The foreclosure docket has no bankruptcy suggestion, which is the strongest available signal. A filing before 3 Nov would still stay the sale. Check PACER the day before the sale.

## 4. Occupancy and possession signals
- **VERIFIED, signals that he lives at the unit:**
  - OPA owner mailing address is 2112 Christian St Unit C.
  - The $100,000 homestead exemption is active.
  - Both foreclosures are coded "Residential Owner Occupied".
  - He was personally served at the unit on 3 Apr 2023, and his own pro se filings in 2023 list Apt C.
  - He attended a diversion conference in Sep 2025.
- **Rental licenses (business_licenses):**
  - Charles McCall held license 703288 on 2112 Christian St (no unit given; 2016 to May 2021, now closed). Unit C was likely a rental under the prior owner. That license closed when the unit was sold to Shellenberger.
  - License 863293 (2021, inactive since 2022) carries the business name "2112 Christian St #C" but is filed under unit "# B", OPA 888303720, by Victor Lobanov, then owner of Unit B. This looks like a naming quirk tied to Unit B, not Unit C.
  - **No rental license for Shellenberger or for Unit C under his ownership.**
- **VERIFIED, signals of absence:** Personal service failed in both foreclosures (2023 and 2025), and the condo association could not find him on 3 Jan 2023. Process servers did not reach him, but these failures do not show that the unit is vacant.
- **Artist and web presence:** Web searches found no public artist website, gallery listing or social profile tied to this Richard Shellenberger. The bidder's "artist" information could not be corroborated.
- **L&I:** There are no violations or case investigations at 2112 Christian St in Carto.
- **Inference:** He most likely still occupies the unit as his home. He is an owner-occupant who has engaged with the court in the past (he won his pro se fight with the condo association) and has twice pursued loan modifications. Expect him in possession after the sale. That means a possibility of a last-minute bankruptcy or a petition to set aside the sale, and an ejectment action if he does not leave voluntarily. There is no evidence of a tenant.

## 5. Real estate tax and water
- **Not found.**
  - The Carto table real_estate_tax_balances is stale (latest tax period is 2016) and has no rows for this parcel.
  - real_estate_tax_delinquencies returned "permission denied".
  - The Revenue API (api.phila.gov/tips) returned HTTP 503.
  - The OPA record shows market value $201,800 and the homestead exemption.
  - Check the balance manually at phila.gov/revenue/realestatetax before bidding.
- **PWD water:** No public data source was found. No water shutoff or lien signal was located.
- The Unit C condo assessment balance is unknown. In PA, a buyer at a sheriff sale may inherit up to 6 months of assessments under the Uniform Condominium Act lien priority. Ask the association.

## Could not find or verify
- The original mortgage amount and the terms of any modification.
- The current tax, water and HOA balances.
- A PACER bankruptcy check.
- Any public artist or online presence.
- The text of the plaintiff's Aug 2026 postponement motion. The filename "Executed MTPP" suggests the defendant may have consented or been working on loss mitigation, but that is unconfirmed. The PDF is behind a paywall at $5 or more.
