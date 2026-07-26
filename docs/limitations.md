# Honest Limitations

"My model's error is modest, here's why, and here's the data that would fix it." Results that look too perfect are hard to believe — these are the reasons to believe these ones.

## What the model is good at

Typical mid-tier **1–3 BHK** flats in localities with a handful of listings. There it predicts within about **±₹28,700/month** (out-of-fold MAE) and generalises cleanly — the overfitting gap between in-sample R² (0.818) and out-of-fold R² (0.812) is only **0.006**, so it's learning the market, not memorising the rows.

## How it was evaluated (and why that matters)

Not on a single train/test split. A 75/25 split leaves a test set whose R² swings with the random seed — a lucky seed flatters the model, an unlucky one buries it. So the headline is **5-fold cross-validation**: **CV R² 0.807 ± 0.042** (folds ranged 0.73–0.86). That tight ±0.04 spread across folds *is* the honest uncertainty — and it is far tighter than the ±0.10 we saw on the earlier 119-row dataset, which is exactly what 7× more data buys you. Every row's prediction in `predictions.csv` is **out-of-fold** — made by a model that never saw that row.

## What it is not good at, and why

1. **Rare large flats.** With area entered on a **log scale** (a constant-elasticity term) the luxury tail no longer explodes: the lone 8BHK that the earlier raw-area model priced at ~₹1.27Cr now lands near ₹12.5L against its ₹8.0L listing. What remains are ordinary over/under-shoots on 5+ BHK flats and thin localities — the worst miss across all 882 rows is ₹4.7L on a rare 6BHK, not an order-of-magnitude blow-up. RMSE (₹57k) now sits close to MAE (₹29k) instead of ~9× above it. Still: **treat 5+ BHK as advisory, not auto-priced** — the comparable signal there is thin.
2. **Thin localities.** Many of the 95 localities have 1–2 listings, so their median-based features rest on almost no evidence. The `n_listings >= 2` filter in the SQL ranking is a guard, but the model itself still sees them.
3. **Dataset still uneven.** 882 rows is a real improvement over the first 119, but **38 of 95 localities still have only a single listing** — for those, `tier` and `median_rent_per_sqft` rest on one flat each (flagged as `solo_locality` in `predictions.csv`). Cross-validation controls the *reporting* noise, but it can't create signal that isn't there. This is the single biggest remaining limitation.

## Known data-quality caveats (carried forward from cleaning)

- **Inferred BHK** for the ~12% of rows that were missing it (from floor area, flagged) — an assumption, not a measurement.
- **Median-filled floors**, with a `floor_missing` flag retained so the model can at least learn from the missingness.
- **`total_floors` dropped** (~67% null) — so "floor band relative to building height," a feature that likely matters, isn't available.

## The leak I closed

An earlier version fed each flat its locality's median rent/sqft computed over *all* flats in that locality — including itself. For the 38 single-listing localities that median simply *was* the flat's own rent/sqft: a hard leak that flattered the score. The model now uses **`median_rps_loo`**, a *leave-one-out* median — each flat sees the median of the *other* flats in its locality, never its own price; single-listing localities have no neighbour and fall back to the city median (an honest "unknown area" signal). Closing this leak lowered the score by design — a leak inflates, so the honest number is the lower one. (Combined with modelling area on a log scale, the final honest model reports OOF R² **0.812** / MAE **₹28,700**.) The residual is `tier` (a coarse premium/mid/budget class a human could assign from the neighbourhood name alone) — a defensible proxy, disclosed.

## Single source, single city

All 882 listings come from **Square Yards**, for **Mumbai only**. Any source has selection bias (which flats get listed, how fields are filled). No cross-source validation was possible. Findings should be read as "what Square Yards' Mumbai listings say," not "the Mumbai rental market, settled."

## What data would fix it (in priority order)

1. **More listings per locality** — the highest-return fix by far; it directly attacks limitations 1–3.
2. **A second source** (99acres / MagicBricks) to cross-check and de-bias.
3. **Real amenity fields** — building age, lift, parking, balcony — which the market prices but the current data can't see.
4. **`total_floors`** captured reliably, to build a proper floor-band feature.
