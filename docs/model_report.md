# Rent Radar - Model Report

Listings after JOIN: **119** rows.

EDA charts written to docs/figures/ (4 plots).

Model rows: **119**. Features: ['area_sqft', 'bhk', 'floor', 'metro_km', 'median_rent_per_sqft', 'furnishing', 'tier'].
Target = log1p(rent); errors reported back in rupees via expm1.

## Results

- Train R2: **0.869**
- Test  R2: **0.848**
- Overfitting gap (train-test R2): **0.020** (small gap = generalises; large gap = memorising).
- Test MAE:  **Rs 47,091/month** (typical miss)
- Test RMSE: **Rs 109,198/month** (penalises big misses)

## Where the model breaks

Worst 5 test predictions:

| locality     |   bhk |    true |    pred |   abs_err |
|:-------------|------:|--------:|--------:|----------:|
| Versova      |     6 | 400,000 | 921,682 |   521,682 |
| Juhu         |     5 | 550,000 | 374,636 |   175,364 |
| Bandra East  |     4 | 300,000 | 468,360 |   168,360 |
| Prabhadevi   |     2 | 230,000 | 112,235 |   117,765 |
| Andheri West |     2 | 210,000 | 147,871 |    62,129 |

**Failure pattern:** biggest misses are high-end premium flats and thin localities with few listings — the model has little signal there and pulls toward the city mean. It is honest for typical mid-tier 1-2 BHK rent and unreliable at the luxury tail.

## Limits
- Only 119 listings; test set is ~30 flats.
- Single source (Square Yards); one city (Mumbai).
- median_rent_per_sqft is locality-derived, so it leaks locality strength — kept because it mirrors how a human prices a flat.

