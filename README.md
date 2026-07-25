# Rent Radar — What should this flat actually cost?

**A fair-rent model for Mumbai, built from messy public rental listings.**

Every tenant in Mumbai asks the same question: is this flat priced fairly, or am I being overcharged? Listings are noisy — the same 2BHK is priced wildly differently across localities, floors, and furnishing. This project builds the model a pricing team would use to answer "what should this flat cost?", and — just as importantly — says out loud where that model stops being trustworthy.

## The question

Given a flat's locality, size, BHK, floor, furnishing, and distance to a metro station, predict a fair monthly rent — and flag listings that look mispriced against it.

## The data

- **Listings:** 897 raw Mumbai rental listings scraped from Square Yards, cleaned down to **882** usable rows across **95 localities**. One source, one city — scope held deliberately narrow so the effort goes into features, not breadth.
- **Locality attributes (the enrichment):** a second table built from public sources — median rent, median rent-per-sqft, a budget/mid/premium tier, and average distance to the nearest of Mumbai's metro stations (computed by haversine from OpenStreetMap/Overpass station coordinates).

The two tables are loaded into SQLite and **joined** on locality, so every listing carries its neighbourhood's characteristics.

## The approach

1. **SQL first** (`sql/`) — schema, load, and analysis. Before any Python, the queries answer the first questions: rent by tier and BHK (JOIN + GROUP BY), a locality ranking by rent-per-sqft with each area's gap to the city average (window functions), and a near-metro vs far-metro comparison (CTE).
2. **Clean and explore** (`python/pipeline/01_clean.py`) — every cleaning decision is logged with its reasoning to `docs/data_quality_note.md`: dropping a 100%-null deposit column, removing sale prices that leaked in as ₹60L "rent", inferring missing BHK from floor area, flagging imputed floors, and keeping genuine luxury outliers rather than deleting them.
3. **Model once** (`python/pipeline/02_model.py`) — **one** linear regression predicting `log(rent)`, evaluated by 5-fold cross-validation, with the error reported back in rupees.

## The findings

- **Locality is the price.** Premium localities rent for roughly **2× per square foot** what budget localities do (₹185/sqft vs ₹93/sqft for a typical 2BHK). **Worli** tops the city at ₹252/sqft — about **₹128/sqft above** the city average.
- **Metro access carries a real but modest premium:** localities within 1.5 km of a metro average **₹137.0/sqft** vs **₹130.8/sqft** for those farther out — a ~5% uplift, not the headline driver.
- **The model explains most of the variation it sees.** Evaluated by **5-fold cross-validation** (not a single lucky split): CV R² **0.790 ± 0.040** (folds tight, 0.74–0.84), out-of-fold R² **0.792**. In-sample R² is 0.801, so the overfitting gap is a tiny **0.009** — it generalises cleanly. Typical miss is **₹40,000/month** (out-of-fold MAE); RMSE is ₹299,000, dragged up by a handful of luxury-tail misses.

## Where it breaks (the honest part)

The model is reliable for typical mid-tier 1–2 BHK flats and **unreliable at the luxury tail and in thin localities**. Its worst prediction: an 8BHK in Santacruz West listed at ₹8,00,000 that the model priced at ~₹94,00,000 (₹9.4 million) — the lone 8BHK in the data, so the model had no comparable to learn from and extrapolated wildly. Of the 95 localities, **38 have only a single listing**, flagged as `solo_locality` in `predictions.csv`. Full failure analysis in `docs/model_report.md`; honest limits in `docs/limitations.md`.

## What would make it better

More listings per locality (38 of 95 localities still have just one), a second source to cross-check Square Yards, and real amenity data (age of building, lift, parking, balcony) that listings hint at but rarely record cleanly.

## Repo map

```
sql/         01_schema · 02_load · 03_analysis      (run in order)
notebooks/   rent_radar_analysis.ipynb              (narrative: cleaning + EDA + model)
python/
  pipeline/  01_clean.py → 02_model.py              (reproducible pipeline)
  scraper.py, fetch_metro.py, fetch_wards.py        (data provenance)
data/        raw/ · clean/ · geo/
docs/        data_quality_note · model_report · limitations · ai_appendix · figures/
memo/        pricing_memo.md                        (one-page decision memo)
models/      rent_model.pkl
dashboard/   Tableau build guide + predictions.csv
```

The **notebook** (`notebooks/rent_radar_analysis.ipynb`) is the readable story —
every cleaning decision documented as it's made, EDA, the model, coefficients, and
failure analysis. The **`python/pipeline/` scripts** are the reproducible version
that regenerates every artifact below.

## Reproduce it

```bash
python3 -m pip install -r python/requirements.txt
python3 python/pipeline/01_clean.py
sqlite3 rent_radar.db < sql/01_schema.sql
sqlite3 rent_radar.db < sql/02_load.sql
sqlite3 rent_radar.db < sql/03_analysis.sql
python3 python/pipeline/02_model.py

# read the narrative notebook
jupyter notebook notebooks/rent_radar_analysis.ipynb
```
