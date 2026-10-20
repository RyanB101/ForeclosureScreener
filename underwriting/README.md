# Underwriting model

Formula-driven Excel model for the Philadelphia Sheriff Sale (Nov 3, 2026). For each property it finds the
best exit (flip or value-add hold, with wholesale and teardown as alternatives), the highest bid that still
hits ryan's targets, and profit and return at a ladder of bids.

- `build_model.py` writes the workbook. All assumptions are named cells on the Assumptions sheet and all
  property inputs are on the Deals sheet, so everything can be changed in Excel.
- `run_model.py [deals.csv] --out-dir DIR` builds it, recalculates it with LibreOffice, and exports
  `max_bids.csv`.
- `deals_template.csv` lists the input columns. Without a CSV the workbook gets three illustrative rows.

## Targets and measures

| Exit | Test | Max bid is the highest bid where... |
|---|---|---|
| Flip | $50k profit and at least 15%/yr on cash (the 15% is adjustable; 0 turns it off) | ARV less selling costs, rehab, carry, legal, possession, liens, fees and premium leaves $50k |
| Value-add hold | 12% **yield on cost** by default (stabilized NOI / all-in cost, unlevered); switchable to cash-on-cash after a DSCR refi | NOI / all-in cost >= 12% |
| Wholesale | Assign the bid to a flipper who needs 15% of ARV; keep a $15k fee | Shown as an alternative |
| Teardown / added units | Greater of $50k or 15% of sale revenue | Shown when units possible is filled in |

## Sale rules built in

10% + 1.5% premium due Nov 4 and 90% Nov 18, all cash. Transfer tax (4.578%) comes out of the bid, then
Sheriff costs, then city claims: any claims the bid does not cover survive and are counted as cost. Sale to
recorded deed 12 months; occupied adds 5 months and a possession cost. Rehab is blind: $/sf by scope plus 20%
contingency plus a $10k allowance plus anything visible from the street.

## Pre-screen of the whole list

`prescreen_inputs.py PROJECT_FILES -o deals.csv --skipped skipped.csv` joins the auction list to the
Market and comps values and HUD rents for every single-parcel residential lot, with blind defaults
(Heavy rehab before 1990, Medium after; occupancy unknown, so treated as occupied; lien position unknown).
Run `run_model.py deals.csv` on it to rank the whole list before the title check.
