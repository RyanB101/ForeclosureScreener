# market_comps

Sold comps and ZIP market stats for Philadelphia sheriff-sale properties, from the city's public data on `phl.carto.com` (Real Estate Transfer Tax deeds joined to OPA property records). Stdlib Python only.

Needs network access to `phl.carto.com`. Check with `python -c "import carto; print(carto.check())"`.

```sh
# 1. Arm's-length sales for every ZIP on the auction list, last 2 years
python pull_sales.py --auction-csv /mnt/project-files/nov3-auction/nov3_2026_auction_parcels.csv \
    --since 2024-10-01 --out sales.csv

# 2. ZIP medians, $/sqft and year-over-year change
python zip_stats.py sales.csv --out zip_stats.csv

# 2b. Merge with HUD Small Area FMRs into one ZIP table with a suggested play
python build_zip_market.py --stats zip_stats.csv --rents zip_rents_fy27_safmr.csv \
    --auction-csv nov3_2026_auction_parcels.csv --out zip_market.csv

# 3. As-is value and ARV for a shortlist (CSV with an OPA column)
python comps.py --sales sales.csv --subjects shortlist.csv --out values.csv

python -m unittest test_comps
```

## Method

Interiors can't be inspected before a sheriff sale, so values come from the spread of nearby sold $/sqft:

| Output | Basis |
|---|---|
| As-is value | 25th percentile $/sqft of comps × subject sqft |
| Market value | Median $/sqft × subject sqft |
| ARV | 80th percentile $/sqft × subject sqft |

Comps are the 30 nearest same-category (single family, multi family, mixed use) open-market resales of $10k+ from the last 18 months, living area within ±35%, in a radius that widens from 0.35 to 1.0 mile until at least 6 are found. Sheriff, GSE, HUD, Land Bank, city and estate transfers are dropped.

Values are today's. Sheriff deeds are taking 9 to 15 months, so apply any growth assumption at the underwriting step.

HUD's site blocks plain HTTP clients, so the FY2027 SAFMR workbook was downloaded through headless Chromium and the Philadelphia ZIPs extracted to `zip_rents_fy27_safmr.csv`.
