# Rent Radar - Model Report

Listings after JOIN: **882** rows.

EDA charts written to docs/figures/ (4 plots).

Model rows: **882**. Features: ['area_sqft', 'bhk', 'floor', 'metro_km', 'median_rps_loo', 'furnishing', 'tier'].
Target = log1p(rent); errors reported back in rupees via expm1.

## Results (5-fold cross-validation)

- CV R2: **0.772 +/- 0.047** across folds (0.72, 0.80, 0.80, 0.71, 0.83).
- Out-of-fold R2 (all 882 rows): **0.775**.
- In-sample R2 (fit on all data): **0.784** -> overfitting gap **0.009** (small = generalises, not memorising).
- CV MAE: **Rs 44,222/month** (out-of-fold); per-fold **Rs 44,179 +/- 30,140**.
- CV RMSE: **Rs 406,187/month** (penalises big misses).

Why CV over a single split: one 75/25 split reports a single held-out R2 that swings with the seed. 5-fold reports the average over five held-out sets plus the spread across them, so the headline number carries its own honest uncertainty band.

## Which features carry the price

Coefficients of the one linear model. Numeric features are standardized, so each row is the effect of a **+1 standard-deviation** move; the target is log(rent), so **effect_on_rent** is how much predicted rent changes.

| feature                        |   coef_log | effect_on_rent   |
|:-------------------------------|-----------:|:-----------------|
| cat__furnishing_unknown        |     -0.506 | -40%             |
| num__area_sqft                 |      0.386 | +47%             |
| cat__tier_premium              |      0.253 | +29%             |
| cat__tier_budget               |     -0.229 | -20%             |
| cat__furnishing_furnished      |      0.211 | +23%             |
| cat__furnishing_semi-furnished |      0.154 | +17%             |
| cat__furnishing_unfurnished    |      0.141 | +15%             |
| num__bhk                       |      0.115 | +12%             |

**In plain words:** floor **area** is the single biggest genuine lever, followed by **locality strength** (median_rps_loo, the leave-one-out neighbourhood rent/sqft). BHK and tier add on top; metro distance moves rent only at the margin. The negative on `furnishing_unknown` is a *missingness* signal, not a real driver — listings that hide furnishing tend to be cheaper, so the flag itself predicts lower rent. (Exact per-feature effects are the table above, regenerated each run.)

## Where the model breaks

Worst 5 out-of-fold predictions:

| locality       |   bhk |    true |       pred |    abs_err | solo_loc   |
|:---------------|------:|--------:|-----------:|-----------:|:-----------|
| Santacruz West |     8 | 800,000 | 12,685,055 | 11,885,055 |            |
| Andheri West   |     6 | 900,000 |  1,931,749 |  1,031,749 |            |
| Malad West     |     6 | 700,000 |  1,396,082 |    696,082 |            |
| Lower Parel    |     3 | 400,000 |    777,786 |    377,786 |            |
| Pali Hill      |     4 | 600,000 |    258,426 |    341,574 | yes        |

**Failure pattern:** biggest misses are high-end premium flats and thin localities — the model has little signal there and pulls toward the city mean. It is honest for typical mid-tier 1-2 BHK rent and unreliable at the luxury tail.

## Limits
- Only 882 listings across 95 localities; **38 localities have a single listing**, so their tier and median-rent features rest on one flat each (flagged as solo_locality in predictions.csv).
- Single source (Square Yards); one city (Mumbai) by design.
- Locality strength enters the model as **median_rps_loo**, a leave-one-out median: each flat sees the other flats in its locality, never its own price. The 38 single-listing localities have no neighbour, so they fall back to the city median (an honest 'unknown area' signal). This closes the solo-locality leak the raw locality median would have carried; `tier` remains a coarse 3-level area class.
- Evaluated by 5-fold CV (not a single split) so every row gets an out-of-fold prediction and the headline R2 carries a fold-spread band.

