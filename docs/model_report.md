# Rent Radar - Model Report

Listings after JOIN: **882** rows.

EDA charts written to docs/figures/ (4 plots).

Model rows: **882**. Features: ['log_area', 'bhk', 'floor', 'floor_missing', 'metro_km', 'median_rps_loo', 'furnishing', 'tier'].
Target = log1p(rent); errors reported back in rupees via expm1.

## Results (5-fold cross-validation)

- CV R2: **0.813 +/- 0.033** across folds (0.83, 0.83, 0.82, 0.75, 0.84).
- Out-of-fold R2 (all 882 rows): **0.818**.
- In-sample R2 (fit on all data): **0.827** -> overfitting gap **0.009** (small = generalises, not memorising).
- CV MAE: **Rs 28,683/month** (out-of-fold); per-fold **Rs 28,680 +/- 5,757**.
- CV RMSE: **Rs 55,717/month** (penalises big misses).

Why CV over a single split: one 75/25 split reports a single held-out R2 that swings with the seed. 5-fold reports the average over five held-out sets plus the spread across them, so the headline number carries its own honest uncertainty band.

## Which features carry the price

Coefficients of the one linear model. Numeric features are standardized, so each row is the effect of a **+1 standard-deviation** move; the target is log(rent), so **effect_on_rent** is how much predicted rent changes.

| feature                   |   coef_log | effect_on_rent   |
|:--------------------------|-----------:|:-----------------|
| num__log_area             |      0.446 | +56%             |
| cat__tier_premium         |      0.252 | +29%             |
| cat__tier_budget          |     -0.221 | -20%             |
| cat__furnishing_unknown   |     -0.145 | -13%             |
| num__median_rps_loo       |      0.106 | +11%             |
| cat__furnishing_furnished |      0.089 | +9%              |
| num__floor_missing        |      0.064 | +7%              |
| num__bhk                  |      0.056 | +6%              |

**In plain words:** **area** is the single biggest genuine lever (now entered as **log-area**, so its effect reads as an elasticity — a *percent* change in size maps to a percent change in rent), then **locality tier** (premium vs budget). With the continuous locality median now computed leave-one-out, most of the neighbourhood signal loads onto the collinear tier dummies rather than median_rps_loo. BHK adds on top; metro distance moves rent only at the margin. The negative on `furnishing_unknown` is a *missingness* signal, not a real driver — listings that hide furnishing tend to be cheaper. (Exact per-feature effects are the table above, regenerated each run.)

## Where the model breaks

Worst 5 out-of-fold predictions:

| locality       |   bhk |      true |      pred |   abs_err | solo_loc   |
|:---------------|------:|----------:|----------:|----------:|:-----------|
| Santacruz West |     8 |   800,000 | 1,244,017 |   444,017 |            |
| Gundavali      |     6 |   900,000 |   500,272 |   399,728 | yes        |
| Worli          |     5 | 1,000,000 |   626,016 |   373,984 |            |
| Andheri West   |     6 |   900,000 |   553,807 |   346,193 |            |
| Prabhadevi     |     5 |   750,000 |   438,949 |   311,051 |            |

**Failure pattern:** with area entered as log-area the luxury tail no longer explodes — the worst miss is now a plausible over/under-shoot, not the order-of-magnitude blow-up the raw-area model produced. Residual misses are rare large flats and thin single-listing localities, where the model has little comparable signal and pulls toward the tier mean. It is reliable for typical 1-3 BHK rent; treat 5+ BHK and solo localities as advisory, not automatic.

## Limits
- Only 882 listings across 95 localities; **38 localities have a single listing**, so their tier and median-rent features rest on one flat each (flagged as solo_locality in predictions.csv).
- Single source (Square Yards); one city (Mumbai) by design.
- Locality strength enters the model as **median_rps_loo**, a leave-one-out median: each flat sees the other flats in its locality, never its own price. The 38 single-listing localities have no neighbour, so they fall back to the city median (an honest 'unknown area' signal). This closes the solo-locality leak the raw locality median would have carried; `tier` remains a coarse 3-level area class.
- Evaluated by 5-fold CV (not a single split) so every row gets an out-of-fold prediction and the headline R2 carries a fold-spread band.

Dashboard datasets -> data/clean/{dashboard_data, locality_ranking, coefficients, model_metrics}.csv

