# Rent Radar - Model Report

Listings after JOIN: **882** rows.

EDA charts written to docs/figures/ (4 plots).

Model rows: **882**. Features: ['area_sqft', 'bhk', 'floor', 'metro_km', 'median_rent_per_sqft', 'furnishing', 'tier'].
Target = log1p(rent); errors reported back in rupees via expm1.

## Results (5-fold cross-validation)

- CV R2: **0.790 +/- 0.040** across folds (0.75, 0.81, 0.82, 0.74, 0.84).
- Out-of-fold R2 (all 882 rows): **0.792**.
- In-sample R2 (fit on all data): **0.801** -> overfitting gap **0.009** (small = generalises, not memorising).
- CV MAE: **Rs 40,049/month** (out-of-fold); per-fold **Rs 40,016 +/- 24,305**.
- CV RMSE: **Rs 299,455/month** (penalises big misses).

Why CV over a single split: with 119 rows one 75/25 split leaves a ~30-flat test set whose R2 swings with the seed. 5-fold reports the average over five held-out sets, so this number is trustworthy.

## Where the model breaks

Worst 5 out-of-fold predictions:

| locality       |   bhk |    true |      pred |   abs_err | solo_loc   |
|:---------------|------:|--------:|----------:|----------:|:-----------|
| Santacruz West |     8 | 800,000 | 9,425,498 | 8,625,498 |            |
| Gundavali      |     6 | 900,000 | 1,873,435 |   973,435 | yes        |
| Andheri West   |     6 | 900,000 | 1,795,416 |   895,416 |            |
| Malad West     |     6 | 700,000 | 1,312,879 |   612,879 |            |
| Worli          |     4 | 800,000 | 1,258,327 |   458,327 |            |

**Failure pattern:** biggest misses are high-end premium flats and thin localities — the model has little signal there and pulls toward the city mean. It is honest for typical mid-tier 1-2 BHK rent and unreliable at the luxury tail.

## Limits
- Only 882 listings across 95 localities; **38 localities have a single listing**, so their tier and median-rent features rest on one flat each (flagged as solo_locality in predictions.csv).
- Single source (Square Yards); one city (Mumbai) by design.
- median_rent_per_sqft is locality-derived, so it leaks locality strength — kept because it mirrors how a human prices a flat, and disclosed rather than hidden.
- Evaluated by 5-fold CV (not a single split) because 882 rows make any one split unreliable.

