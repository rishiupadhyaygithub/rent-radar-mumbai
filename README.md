# Rent Radar — What should this flat actually cost?

**A fair-rent model for Mumbai, built from messy public rental listings.**

Every tenant in Mumbai asks the same question: is this flat priced fairly, or am I being overcharged? Listings are noisy — the same 2BHK is priced wildly differently across localities, floors, and furnishing. This project builds the model a pricing team would use to answer "what should this flat cost?", and — just as importantly — says out loud where that model stops being trustworthy.

## The question

Given a flat's locality, size, BHK, floor, furnishing, and distance to a metro station, predict a fair monthly rent — and flag listings that look mispriced against it.

## The data

- **Listings:** 122 raw Mumbai rental listings scraped from Square Yards, cleaned down to **119** usable rows across **53 localities**. One source, one city — scope held deliberately narrow so the effort goes into features, not breadth.
- **Locality attributes (the enrichment):** a second table built from public sources — median rent, median rent-per-sqft, a budget/mid/premium tier, and average distance to the nearest of Mumbai's metro stations (computed by haversine from OpenStreetMap/Overpass station coordinates).

The two tables are loaded into SQLite and **joined** on locality, so every listing carries its neighbourhood's characteristics.

## The approach

1. **SQL first** (`sql/`) — schema, load, and analysis. Before any Python, the queries answer the first questions: rent by tier and BHK (JOIN + GROUP BY), a locality ranking by rent-per-sqft with each area's gap to the city average (window functions), and a near-metro vs far-metro comparison (CTE).
2. **Clean and explore** (`python/pipeline/01_clean.py`) — every cleaning decision is logged with its reasoning to `docs/data_quality_note.md`: dropping a 100%-null deposit column, removing sale prices that leaked in as ₹60L "rent", inferring missing BHK from floor area, flagging imputed floors, and keeping genuine luxury outliers rather than deleting them.
3. **Model once** (`python/pipeline/02_model.py`) — **one** linear regression predicting `log(rent)`, on a proper train/test split, with the error reported back in rupees.

## The findings

- **Locality is the price.** Premium localities rent for roughly **3× per square foot** what budget localities do (₹225/sqft vs ₹77/sqft for a typical 2BHK). **Bandra East** tops the city at ₹260/sqft — about **₹139/sqft above** the city average.
- **Metro access carries a real but modest premium:** localities within 1.5 km of a metro average **₹141.6/sqft** vs **₹130.4/sqft** for those farther out.
- **The model explains most of the variation it sees.** Evaluated by **5-fold cross-validation** (not a single lucky split, because 119 rows make one split unreliable): CV R² **0.796 ± 0.099**, out-of-fold R² **0.821**. In-sample R² is 0.866, so the overfitting gap is a small **0.045** — it generalises. Typical miss is **₹38,000/month** (out-of-fold MAE); RMSE ₹79,400, dragged up by a few large misses.

## Where it breaks (the honest part)

The model is reliable for typical mid-tier 1–2 BHK flats and **unreliable at the luxury tail and in thin localities**. Its worst prediction: a 6BHK in Versova listed at ₹4,00,000 that the model priced at ~₹9,00,000 — because it had almost no other 6BHKs to learn from and reached toward the mean of a sparse, high-variance group. Of the 53 localities, **28 have only a single listing**, flagged as `solo_locality` in `predictions.csv`. Full failure analysis in `docs/model_report.md`; honest limits in `docs/limitations.md`.

## What would make it better

More listings per locality (the single biggest fix — 119 rows is thin), a second source to cross-check Square Yards, and real amenity data (age of building, lift, parking, balcony) that listings hint at but rarely record cleanly.

## Repo map

```
sql/         01_schema · 02_load · 03_analysis      (run in order)
python/
  pipeline/  01_clean.py → 02_model.py              (the pipeline)
  scraper.py, fetch_metro.py, fetch_wards.py        (data provenance)
data/        raw/ · clean/ · geo/
docs/        data_quality_note · model_report · limitations · ai_appendix · figures/
memo/        pricing_memo.md                        (one-page decision memo)
models/      rent_model.pkl
dashboard/   Tableau workbook + guidance
```

## Reproduce it

```bash
python3 -m pip install -r python/requirements.txt
python3 python/pipeline/01_clean.py
sqlite3 rent_radar.db < sql/01_schema.sql
sqlite3 rent_radar.db < sql/02_load.sql
sqlite3 rent_radar.db < sql/03_analysis.sql
python3 python/pipeline/02_model.py
```
