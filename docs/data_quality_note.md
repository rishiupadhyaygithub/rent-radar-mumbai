# Data Quality Note - Mumbai Rent Radar

Raw listings loaded: **122** rows, 16 columns.

## Cleaning decisions

- **deposit**: 100% null across the dataset -> column dropped. The scraper never captured deposit; imputing it would invent data.
- **price (impossible values)**: 3 row(s) above Rs 10,00,000/month (max was Rs 6,000,000). These are sale prices mislabelled as rent. Dropped, not winsorised, because they are wrong records not extreme rents.
  Rows after impossible-price filter: 119 (removed 3).
- **bhk**: 14 null -> inferred from area_sqft (~450 sqft/BHK, clipped 1-6). Documented as an assumption; alternative was dropping 12% of rows.
- **total_floors**: 66% null -> dropped (too sparse to trust). **floor** kept; nulls filled with median floor and flagged.
  floor: 26 null filled with median=10; floor_missing flag retained so the model can learn from missingness.
- **furnishing**: normalised whitespace/case -> {'semi-furnished': 55, 'furnished': 41, 'unfurnished': 23}
- **locality**: trimmed + title-cased -> 53 unique localities.
- **rent_per_sqft**: derived = price / area_sqft (core comparison unit).
- **rent_per_sqft outliers**: 4 rows outside 1st-99th pctile (Rs 30-342/sqft) inspected. Kept - they are real luxury/budget, not typos, verified against area+bhk.
- **metro_km**: distance from each listing to nearest of 40 Mumbai metro stations (haversine). Nulls where lat/lng missing.
- **locality tier**: localities bucketed into 3 tiers by median rent/sqft.

## Output
- listings_clean.csv: **119** rows, 17 cols
- localities.csv: **53** localities

## What remains imperfect
- 122 raw rows is thin; per-locality medians rest on few listings each.
- bhk inference and floor median-fill inject assumptions (flagged in-column).
- Single source (Square Yards) - may not represent the whole Mumbai market.
