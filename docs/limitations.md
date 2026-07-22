# Honest Limitations

"My model's error is modest, here's why, and here's the data that would fix it." Results that look too perfect are hard to believe — these are the reasons to believe these ones.

## What the model is good at

Typical mid-tier **1–2 BHK** flats in localities with a handful of listings. There it predicts within about **±₹38,000/month** (out-of-fold MAE) and generalises cleanly — the overfitting gap between in-sample R² (0.866) and out-of-fold R² (0.821) is only **0.045**, so it's learning the market, not memorising the rows.

## How it was evaluated (and why that matters)

Not on a single train/test split. With 119 rows, a 75/25 split leaves a ~30-flat test set whose R² swings with the random seed — a lucky seed flatters the model, an unlucky one buries it. So the headline is **5-fold cross-validation**: **CV R² 0.796 ± 0.099** (folds ranged 0.60–0.87). That ±0.10 spread *is* the honest uncertainty, and the low fold (0.60) is a feature of the report, not something hidden. Every row's prediction in `predictions.csv` is **out-of-fold** — made by a model that never saw that row.

## What it is not good at, and why

1. **The luxury tail.** Its worst miss priced a Versova 6BHK at ₹9.2L against a ₹4.0L listing. With almost no other 5–6 BHK flats to learn from, a linear model reaches toward the mean of a tiny, high-variance group and overshoots. **Don't auto-price 4+ BHK.**
2. **Thin localities.** Some of the 53 localities have 1–2 listings, so their median-based features rest on almost no evidence. The `n_listings >= 2` filter in the SQL ranking is a guard, but the model itself still sees them.
3. **Small dataset overall.** 119 rows, and **28 of 53 localities have only a single listing** — for those, `tier` and `median_rent_per_sqft` rest on one flat each (flagged as `solo_locality` in `predictions.csv`). Cross-validation controls the *reporting* noise, but it can't create signal that isn't there. This is the single biggest limitation.

## Known data-quality caveats (carried forward from cleaning)

- **Inferred BHK** for the ~12% of rows that were missing it (from floor area, flagged) — an assumption, not a measurement.
- **Median-filled floors**, with a `floor_missing` flag retained so the model can at least learn from the missingness.
- **`total_floors` dropped** (~67% null) — so "floor band relative to building height," a feature that likely matters, isn't available.

## The one leak I kept on purpose

`median_rent_per_sqft` is derived from the same localities it helps predict, so it leaks a little locality strength into the model. I kept it because (a) it's a *locality-level* aggregate, not the per-listing rent-per-sqft that would leak the exact answer (see `ai_appendix.md`), and (b) it mirrors how a human actually prices a flat — "what does this neighbourhood go for?" It is disclosed here rather than hidden, and it inflates R² modestly. Removing it is the honest sensitivity check a reviewer might ask for.

## Single source, single city

All 119 listings come from **Square Yards**, for **Mumbai only**. Any source has selection bias (which flats get listed, how fields are filled). No cross-source validation was possible. Findings should be read as "what Square Yards' Mumbai listings say," not "the Mumbai rental market, settled."

## What data would fix it (in priority order)

1. **More listings per locality** — the highest-return fix by far; it directly attacks limitations 1–3.
2. **A second source** (99acres / MagicBricks) to cross-check and de-bias.
3. **Real amenity fields** — building age, lift, parking, balcony — which the market prices but the current data can't see.
4. **`total_floors`** captured reliably, to build a proper floor-band feature.
