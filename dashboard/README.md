# Dashboard — Build Guide (Tableau Public)

The dashboard answers one question at a glance: **"What should this flat cost — and where do we trust the model?"** Everything below is built from CSVs already in the repo. No live connection needed.

## Data sources (connect all three as text-file sources)

| File | Grain | Use for |
|---|---|---|
| `data/clean/localities.csv` | one row per locality | ranking + map |
| `data/clean/listings_clean.csv` | one row per listing | distributions, drill-down |
| `data/clean/predictions.csv` | one row per listing | predicted-vs-actual, error |

Relate `listings_clean` and `predictions` to `localities` on **locality** (left join).

## Four sheets → one dashboard

1. **Locality ranking (bar).** `localities`: bar of `median_rent_per_sqft` by `locality`, sorted descending, coloured by `tier`. Filter `n_listings >= 2`. This is the "which areas are expensive" answer — Worli on top (₹252/sqft).

2. **Rent-per-sqft by tier (box).** `listings_clean`: box plot of `rent_per_sqft` split by `tier` (budget/mid/premium). Shows the ~3× premium spread in one glance.

3. **Predicted vs actual (scatter) — the trust chart.** `predictions`: `actual_rent` (x) vs `predicted_rent` (y). Add a 45° reference line (Analytics → reference line, or a calculated `[actual_rent]` diagonal). Points on the line = model agrees; far from it = mispriced or model breaks. Colour by `tier`, size by `abs_pct_error`. The luxury-tail outliers pop visually here.

4. **Metro premium (bar, optional).** Two-bar summary: avg `rent_per_sqft` for near-metro (≤1.5 km) vs far — mirrors the SQL CTE result (₹137.0 vs ₹130.8).

## Dashboard layout

- Top strip: 2–3 BAN (big-number) tiles — CV R² **0.77**, typical error **±₹44k**, localities covered **95**.
- Left: locality ranking (sheet 1). Right: predicted-vs-actual (sheet 3).
- Bottom: tier box plot (sheet 2) + metro bars (sheet 4).
- Add a **tier** filter and a **BHK** filter, applied dashboard-wide, so the pricing team can slice to their question.

## Language for the pricing team (put in a caption)

> "Points below the diagonal are listings priced **above** what the model expects — check for overpricing. Points above are potential **underpricing**. The cluster tightens for 1–2 BHK; it fans out for 4+ BHK, where we don't yet trust it."

## Publish

File → Save to Tableau Public. Paste the public URL into the root `README.md` and mention it in the 3-minute walkthrough.
