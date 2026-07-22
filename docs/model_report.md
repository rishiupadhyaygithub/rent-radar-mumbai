# Rent Radar - Model Report

Listings after JOIN: **119** rows.

EDA charts written to docs/figures/ (4 plots).

Model rows: **119**. Features: ['area_sqft', 'bhk', 'floor', 'metro_km', 'median_rent_per_sqft', 'furnishing', 'tier'].
Target = log1p(rent); errors reported back in rupees via expm1.

## Results (5-fold cross-validation)

- CV R2: **0.796 +/- 0.099** across folds (0.86, 0.80, 0.60, 0.84, 0.87).
- Out-of-fold R2 (all 119 rows): **0.821**.
- In-sample R2 (fit on all data): **0.866** -> overfitting gap **0.045** (small = generalises, not memorising).
- CV MAE: **Rs 38,364/month** (out-of-fold); per-fold **Rs 38,507 +/- 13,756**.
- CV RMSE: **Rs 79,360/month** (penalises big misses).

Why CV over a single split: with 119 rows one 75/25 split leaves a ~30-flat test set whose R2 swings with the seed. 5-fold reports the average over five held-out sets, so this number is trustworthy.

## Where the model breaks

Worst 5 out-of-fold predictions:

| locality    |   bhk |    true |    pred |   abs_err | solo_loc   |
|:------------|------:|--------:|--------:|----------:|:-----------|
| Versova     |     6 | 400,000 | 903,612 |   503,612 |            |
| Bandra East |     4 | 500,000 | 936,717 |   436,717 |            |
| Dadar West  |     2 | 310,000 | 550,398 |   240,398 | yes        |
| Bandra East |     4 | 300,000 | 479,584 |   179,584 |            |
| Juhu        |     5 | 550,000 | 383,311 |   166,689 |            |

**Failure pattern:** biggest misses are high-end premium flats and thin localities — the model has little signal there and pulls toward the city mean. It is honest for typical mid-tier 1-2 BHK rent and unreliable at the luxury tail.

## Limits
- Only 119 listings across 53 localities; **28 localities have a single listing**, so their tier and median-rent features rest on one flat each (flagged as solo_locality in predictions.csv).
- Single source (Square Yards); one city (Mumbai) by design.
- median_rent_per_sqft is locality-derived, so it leaks locality strength — kept because it mirrors how a human prices a flat, and disclosed rather than hidden.
- Evaluated by 5-fold CV (not a single split) because 119 rows make any one split unreliable.

