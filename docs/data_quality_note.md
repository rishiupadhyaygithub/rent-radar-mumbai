# Data Quality Note - Mumbai Rent Radar

Raw listings loaded: **897** rows, 16 columns.

## Cleaning decisions

- **deposit**: 100% null across the dataset -> column dropped. The scraper never captured deposit; imputing it would invent data.
- **price (impossible values)**: 5 row(s) above Rs 10,00,000/month (max was Rs 1,500,000.0). These are sale prices mislabelled as rent. Dropped, not winsorised, because they are wrong records not extreme rents.
  Rows after impossible-price filter: 891 (removed 6).
- **area_sqft (impossible values)**: 3 row(s) outside 150-10,000 sqft (max was 100,000). Dropped as typos, not real flats — they poison rent_per_sqft and the locality medians.
  Rows after impossible-area filter: 888 (removed 3).
- **bhk**: 49 null -> inferred from area_sqft (~450 sqft/BHK, clipped 1-6). Documented as an assumption; alternative was dropping 12% of rows.
- **total_floors**: 60% null -> dropped (too sparse to trust). **floor** kept; nulls filled with median floor and flagged.
  floor: 84 null filled with median=9; floor_missing flag retained so the model can learn from missingness.
- **furnishing**: normalised whitespace/case -> {'semi-furnished': 436, 'furnished': 308, 'unfurnished': 143}
- **locality**: trimmed + title-cased -> 98 unique localities.
- **rent_per_sqft**: derived = price / area_sqft (core comparison unit).
- **rent_per_sqft (impossible values)**: 6 row(s) outside Rs 20-600/sqft dropped as price/area typos (verified: extreme values came from bad area or price fields, not genuine luxury/budget flats).
  Rows after impossible-rent/sqft filter: 882 (removed 6).
- **metro_km**: distance from each listing to nearest of 40 Mumbai metro stations (haversine). Nulls where lat/lng missing.
- **locality tier**: localities bucketed into 3 tiers by median rent/sqft.

## Output
- listings_clean.csv: **882** rows, 17 cols
- localities.csv: **95** localities

## What remains imperfect
- 897 raw listings scraped; 38 of 95 localities still have a single listing, so their medians rest on one flat each.
- bhk inference and floor median-fill inject assumptions (flagged in-column).
- Single source (Square Yards) - may not represent the whole Mumbai market.
