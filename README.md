# ForeclosureScreener

First-pass screen for Philadelphia Sheriff's Office mortgage-foreclosure sales on
Bid4Assets. It takes the cleaned auction list, adds Philadelphia public-record
data per parcel, estimates value, scores every lot and cuts to a ranked
shortlist plus a kill list with a reason for each cut.

## Run

```
pip install -r requirements.txt
python -m screener \
  --master nov3_2026_auction_master.csv \
  --parcels nov3_2026_auction_parcels.csv \
  --out-dir out/            # writes screen.xlsx and screen_shortlist.csv
```

`--rents zip_rents.csv` (columns `zip,rent_per_unit`) adds the value-add hold case
(12% yearly cash return) next to the flip case.

Network access needed: `phl.carto.com` (OPA properties, L&I violations, permits,
unsafe and imminently dangerous lists, recorded deeds, ZIP sales) and
`services.arcgis.com` or `hazards.fema.gov` (flood zone, city vacancy flags).
Responses are cached in `data/cache/`. A source that can't be reached is logged
and its fields are left blank (unknown), never zero.

## How it scores

| Part | Weight | What drives it |
|---|---|---|
| Financial | 40% | Headroom: max bid that still clears the target, minus the opening bid, as a share of ARV. Scaled down when all-in cost is over $300k, zero over $1M |
| Physical | 20% | OPA condition, age, open L&I violations, unsafe listing, recent permits, flood zone |
| Market | 20% | ZIP sales volume (liquidity), 1-year $/sf change, $/sf level |
| Upside | 20% | ARV vs as-is spread, zoning that allows more units, spare lot, multi-family |

Elevated sale risk (repeat postponements, duplicate writs) and "watch" lots lose a
few points. Lots are killed for: no OPA match, industrial or special-purpose use,
L&I imminently dangerous, no value estimate, all-in over $1M at the opening bid,
or a max bid below the opening bid.

Max bid (flip) = (ARV x (1 - 8.3% selling costs) - rehab - carry - legal and
occupancy reserve - $50k profit) / 1.015 buyer's premium. Carry runs 18 months
(12 to deed, 6 to rehab and sell) plus 4 for ejectment unless the city flags the
building vacant. Rehab is by condition band at $40 to $130 per sq ft plus 15%
because the interior is unseen. All assumptions are in `screener/config.py` and
come from the sale-rules brief.

$1 opening bids (lender's bid not posted yet) are replaced with an estimate:
the 75th percentile of opening bid / debt across lots that have a real bid.

## Tests

```
python -m pytest tests
```
