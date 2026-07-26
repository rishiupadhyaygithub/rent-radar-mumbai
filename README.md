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

## Tech stack

One language family, **one model**, standard tools — kept deliberately minimal (depth over tool sprawl).

| Layer | Tools |
|---|---|
| Language | Python 3 · SQL |
| Data wrangling | pandas · numpy |
| Database | SQLite — two related tables joined on `locality`; JOIN + GROUP BY, window functions, and a CTE (`sql/`) |
| Modelling | scikit-learn — a **single** `LinearRegression` in a `Pipeline` (`StandardScaler` for numerics + `OneHotEncoder` for categoricals), evaluated by 5-fold cross-validation |
| Visualisation | seaborn · matplotlib (EDA figures) · Power BI (decision dashboard) |
| Narrative | Jupyter |

**One model, on purpose.** No ensemble, no gradient boosting, no second algorithm bolted on for a benchmark — a linear regression on `log(rent)` stays interpretable (every coefficient is a rupee lever a pricing team can read straight off), and being honest about where that one model breaks is the point of the write-up.

## The findings

- **Locality is the price.** Premium localities rent for roughly **2× per square foot** what budget localities do (₹185/sqft vs ₹93/sqft for a typical 2BHK). **Worli** tops the city at ₹252/sqft — about **₹128/sqft above** the city average.
- **Metro access carries a real but modest premium:** localities within 1.5 km of a metro average **₹137.0/sqft** vs **₹130.8/sqft** for those farther out — a ~5% uplift, not the headline driver.
- **The model explains most of the variation it sees.** Evaluated by **5-fold cross-validation** (not a single lucky split): CV R² **0.813 ± 0.033** (folds tight, 0.75–0.84), out-of-fold R² **0.818**. In-sample R² is 0.827, so the overfitting gap is a tiny **0.009** — it generalises cleanly. Typical miss is **₹28,700/month** (out-of-fold MAE); RMSE is **₹56,000** — now close to the MAE, because area is modelled on a log scale so no single flat can blow the error up.

## Where it breaks (the honest part)

The model is reliable for typical 1–3 BHK flats and **weakest on rare large flats and thin localities**. Modelling area on a **log scale** (a constant-elasticity term) killed the old blow-up: the lone 8BHK in Santacruz West — once priced at an absurd ~₹1.27 crore — now lands near ₹12.4 lakh against its ₹8,00,000 listing — a ₹4.4-lakh over-shoot, the worst miss across all 882 rows, but a plausible band, not an order-of-magnitude error. That single fix cut RMSE from ₹406,000 to ₹56,000. Of the 95 localities, **38 have only a single listing**, flagged as `solo_locality` in `predictions.csv`. Full failure analysis in `docs/model_report.md`; honest limits in `docs/limitations.md`.

## The decision dashboard

`dashboard/` holds the answer to *"what should this flat cost?"* in a form a pricing analyst can read at a glance:

- **`DASHBOARD PROJECT.pbix`** (Power BI) — the built page: a **predicted-vs-actual** trust chart (each listing plotted against what the model expects, sized by error), a rent KPI, a geo map of Mumbai listings, and furnishing/price cuts.
- **`rent_radar_dashboard.xlsx`** (Excel, auto-generated by `python/pipeline/03_build_dashboard.py`) — a second, self-contained view with all four Part-4 visuals: KPI tiles, locality ranking, price drivers, and predicted-vs-actual with a 45° line. A PDF preview sits beside it.

`dashboard/README.md` documents how each visual is built and which dataset feeds it. **No web frontend** — the deliverable is a BI dashboard, by design and by brief.

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
dashboard/   DASHBOARD PROJECT.pbix (Power BI) · rent_radar_dashboard.xlsx (Excel) · build guide
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
python3 python/pipeline/03_build_dashboard.py   # regenerate the Excel dashboard

# read the narrative notebook
jupyter notebook notebooks/rent_radar_analysis.ipynb
```

Open `dashboard/DASHBOARD PROJECT.pbix` in Power BI, or `dashboard/rent_radar_dashboard.xlsx` in Excel, for the decision view.
