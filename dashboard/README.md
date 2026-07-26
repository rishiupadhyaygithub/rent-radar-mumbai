# Dashboard — Build Guide (Power BI)

The page answers one question at a glance: **"What should this flat cost — and where do we trust the model?"** It is built from four CSVs the pipeline writes (`python/pipeline/02_model.py`). No live connection, no database — import the text files and go.

## Ready-made Excel version (no build needed)

If you don't want to click a dashboard together, one is already generated:
**`dashboard/rent_radar_dashboard.xlsx`** — open it in Excel and it's done. It has a
**Dashboard** sheet (KPI tiles + locality-ranking bar + price-driver bar + predicted-vs-actual
scatter with a 45° line) plus `Ranking`, `Drivers`, `PredVsActual`, and `AllListings` data sheets.
Regenerate any time with:

```bash
python python/pipeline/02_model.py        # refresh the datasets
python python/pipeline/03_build_dashboard.py   # rebuild the .xlsx
```

The Power BI guide below is the higher-polish option (interactive slicers + a map). Use whichever you present.

> **Rebuild note.** The first cut (`DASHBOARD PROJECT.pbix`) was a descriptive view of the *raw* listings — count, average area, furnishing mix, price-vs-area — imported from `data/raw/mumbai_listings_raw.csv`. That answers *"what do the listings look like?"*, not the brief's *"what should this flat cost?"*. Rebuild it on the four files below so it shows **locality rankings, price drivers, and predicted-vs-actual** — the three things Part 4 asks for. Save the rebuilt file into `dashboard/` so the deliverable lives in the repo.

## Data sources (Home → Get data → Text/CSV, add all four)

| File | Grain | Feeds |
|---|---|---|
| `data/clean/dashboard_data.csv` | one row per listing (882) | KPI tiles, predicted-vs-actual, map, drill table |
| `data/clean/locality_ranking.csv` | one row per locality (95) | locality ranking bar |
| `data/clean/coefficients.csv` | one row per model feature (13) | price-driver bar |
| `data/clean/model_metrics.csv` | one row per KPI (8) | headline number tiles |

Every prediction in `dashboard_data.csv` is **out-of-fold** — each flat was priced by a model that never saw it during training, so predicted-vs-actual is honest, not a memorised fit.

**Relationships (Model view):** link `dashboard_data[locality]` → `locality_ranking[locality]` (many-to-one, single direction). `coefficients` and `model_metrics` are standalone lookup tables — no relationship needed.

## Five visuals + slicers → one page

1. **KPI cards (top strip).** Four Card visuals from `model_metrics` (put `value` in the field, filter `metric` to one each):
   - `cv_r2` → **Model accuracy (CV R²) ≈ 0.81**
   - `mae_rupees` → **Typical error ≈ ₹28,700/mo**
   - `n_listings` → **Listings 882**  ·  `n_localities` → **Localities 95**
   These are the "how much do we trust it" numbers, up front.

2. **Locality ranking (bar) — "which areas are expensive."** From `locality_ranking`: Y = `locality`, X = `median_rent_per_sqft`, sort descending, colour by `tier`. **Add a visual-level filter `n_listings >= 2`** — otherwise single-listing localities (Gundavali, Pali Hill) top the chart on one flat each. With the filter, **Worli leads (~₹252/sqft)**.

3. **Price drivers (bar) — "what moves rent."** From `coefficients`: Y = `feature`, X = `effect_pct`, sort by `effect_pct`. This is the model's own explanation: `log_area` +56%, `tier_premium` +29%, `tier_budget` −20%, down the list. (Numeric drivers are per +1 SD; the target is log-rent, so `effect_pct` reads as a % change in rent.)

4. **Predicted vs actual (scatter) — the trust chart.** From `dashboard_data`:
   - X = `actual_rent`, Y = `predicted_rent`
   - **Details = `listing_id`** (this makes each flat its own dot instead of one aggregated blob)
   - Legend / colour = `pricing_flag` (In line / Listed above / Listed below)
   - Tooltips: `locality`, `bhk`, `area_sqft`, `abs_pct_error`
   Points near the diagonal = model agrees; far off = mispriced or model breaks. The luxury tail (5+ BHK) fans out top-right — that's where we say "advisory, not automatic." *(Optional literal 45° line: the Analytics pane isn't reliable for y=x, so the `pricing_flag` colour already encodes above/below the line — that carries the same read.)*

5. **Map — where the mispricing is.** From `dashboard_data`: Latitude = `lat`, Longitude = `lng`, Legend = `pricing_flag`, Bubble size = `abs_pct_error`. Shows the over/under-priced clusters geographically.

**Slicers (apply to page):** `tier` and `bhk`, so the pricing team can slice to their question.

## Caption for the pricing team (add a textbox)

> "Dots below the diagonal are listings priced **above** what the model expects — check for overpricing (223 of 882). Dots above are potential **underpricing** (245). The cluster is tight for 1–3 BHK; it fans out for 5+ BHK and single-listing localities, where we don't yet trust it. Model accuracy is CV R² ≈ 0.81, typical miss ≈ ₹28,700/month."

## Publish

File → Save into `dashboard/` (commit the `.pbix`). Optional: Publish to Power BI Service and paste the link into the root `README.md`; mention it in the 3-minute walkthrough.
