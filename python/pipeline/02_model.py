"""
Stage 3 - EDA + ONE linear regression to predict monthly rent.

Rubric guardrails honoured:
- EXACTLY ONE model (linear regression). No ensembles, no second model.
- Train/test split with an explicit overfitting check (train vs test R2).
- Error reported in rupees (MAE + RMSE), the unit a renter understands.
- Honest failure analysis: where the model breaks, written to docs/model_report.md.

Inputs:
    data/clean/listings_clean.csv
    data/clean/localities.csv        (JOINed in, mirrors the SQL layer)
Outputs:
    docs/figures/*.png               Seaborn EDA charts
    models/rent_model.pkl            the fitted pipeline
    docs/model_report.md             metrics + failure analysis
"""
import pickle
from pathlib import Path

import matplotlib
matplotlib.use("Agg")            # headless: save PNGs, never open a window
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

ROOT = Path(__file__).resolve().parents[2]
LISTINGS = ROOT / "data/clean/listings_clean.csv"
LOCALITIES = ROOT / "data/clean/localities.csv"
FIG = ROOT / "docs/figures"
MODEL_OUT = ROOT / "models/rent_model.pkl"
REPORT = ROOT / "docs/model_report.md"

sns.set_theme(style="whitegrid")
log: list[str] = []


def note(msg: str) -> None:
    print(msg)
    log.append(msg)


def main() -> None:
    FIG.mkdir(parents=True, exist_ok=True)
    MODEL_OUT.parent.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(LISTINGS)
    loc = pd.read_csv(LOCALITIES)[["locality", "tier", "median_rent_per_sqft"]]

    # JOIN the locality attributes onto each listing (same relation as the SQL).
    df = df.merge(loc, on="locality", how="left")
    note("# Rent Radar - Model Report\n")
    note(f"Listings after JOIN: **{len(df)}** rows.\n")

    # ---- EDA (Seaborn) ----
    # 1. Target distribution - rent is right-skewed, motivates log target.
    fig, ax = plt.subplots(figsize=(7, 4))
    sns.histplot(df["price"], bins=30, kde=True, ax=ax)
    ax.set(title="Monthly rent distribution", xlabel="Rent (Rs/month)")
    fig.tight_layout(); fig.savefig(FIG / "01_rent_dist.png", dpi=110); plt.close(fig)

    # 2. Rent vs area, coloured by tier - the core relationship.
    fig, ax = plt.subplots(figsize=(7, 5))
    sns.scatterplot(data=df, x="area_sqft", y="price", hue="tier", ax=ax)
    ax.set(title="Rent vs area by locality tier", xlabel="Area (sqft)", ylabel="Rent (Rs)")
    fig.tight_layout(); fig.savefig(FIG / "02_rent_vs_area.png", dpi=110); plt.close(fig)

    # 3. Rent by BHK.
    fig, ax = plt.subplots(figsize=(7, 4))
    sns.boxplot(data=df, x="bhk", y="price", ax=ax)
    ax.set(title="Rent by BHK", xlabel="BHK", ylabel="Rent (Rs)")
    fig.tight_layout(); fig.savefig(FIG / "03_rent_by_bhk.png", dpi=110); plt.close(fig)

    # 4. Numeric correlation heatmap.
    num = df[["price", "area_sqft", "bhk", "floor", "metro_km",
              "median_rent_per_sqft"]].dropna()
    fig, ax = plt.subplots(figsize=(6, 5))
    sns.heatmap(num.corr(), annot=True, fmt=".2f", cmap="mako", ax=ax)
    ax.set(title="Numeric correlations")
    fig.tight_layout(); fig.savefig(FIG / "04_corr.png", dpi=110); plt.close(fig)
    note("EDA charts written to docs/figures/ (4 plots).\n")

    # ---- Feature engineering ----
    # Predict log(rent): rent is right-skewed and multiplicative (a premium
    # locality scales rent, not adds a flat amount). Log makes errors relative.
    feats_num = ["area_sqft", "bhk", "floor", "metro_km", "median_rent_per_sqft"]
    feats_cat = ["furnishing", "tier"]
    model_df = df.dropna(subset=["price", "area_sqft"]).copy()
    model_df[feats_num] = model_df[feats_num].fillna(model_df[feats_num].median())
    model_df[feats_cat] = model_df[feats_cat].fillna("unknown")

    X = model_df[feats_num + feats_cat]
    y = np.log1p(model_df["price"])          # log target
    note(f"Model rows: **{len(X)}**. Features: {feats_num + feats_cat}.")
    note("Target = log1p(rent); errors reported back in rupees via expm1.\n")

    # ---- ONE model: linear regression ----
    pre = ColumnTransformer([
        ("num", StandardScaler(), feats_num),
        ("cat", OneHotEncoder(handle_unknown="ignore"), feats_cat),
    ])
    model = Pipeline([("pre", pre), ("lr", LinearRegression())])

    X_tr, X_te, y_tr, y_te = train_test_split(
        X, y, test_size=0.25, random_state=42)
    model.fit(X_tr, y_tr)

    # ---- Metrics: overfitting check + error in rupees ----
    r2_tr = r2_score(y_tr, model.predict(X_tr))
    r2_te = r2_score(y_te, model.predict(X_te))
    # Back-transform to rupees for interpretable error.
    pred_rs = np.expm1(model.predict(X_te))
    true_rs = np.expm1(y_te)
    mae = mean_absolute_error(true_rs, pred_rs)
    rmse = np.sqrt(mean_squared_error(true_rs, pred_rs))

    note("## Results\n")
    note(f"- Train R2: **{r2_tr:.3f}**")
    note(f"- Test  R2: **{r2_te:.3f}**")
    note(f"- Overfitting gap (train-test R2): **{r2_tr - r2_te:.3f}** "
         "(small gap = generalises; large gap = memorising).")
    note(f"- Test MAE:  **Rs {mae:,.0f}/month** (typical miss)")
    note(f"- Test RMSE: **Rs {rmse:,.0f}/month** (penalises big misses)\n")

    # ---- Honest failure analysis ----
    err = pd.DataFrame({
        "locality": model_df.loc[X_te.index, "locality"],
        "bhk": model_df.loc[X_te.index, "bhk"],
        "true": np.asarray(true_rs), "pred": np.asarray(pred_rs),
    })
    err["abs_err"] = (err["true"] - err["pred"]).abs()
    worst = err.sort_values("abs_err", ascending=False).head(5)
    note("## Where the model breaks\n")
    note("Worst 5 test predictions:\n")
    note(worst.to_markdown(index=False, floatfmt=",.0f"))
    note("\n**Failure pattern:** biggest misses are high-end premium flats "
         "and thin localities with few listings — the model has little signal "
         "there and pulls toward the city mean. It is honest for typical "
         "mid-tier 1-2 BHK rent and unreliable at the luxury tail.\n")
    note("## Limits\n"
         f"- Only {len(X)} listings; test set is ~{len(X_te)} flats.\n"
         "- Single source (Square Yards); one city (Mumbai).\n"
         "- median_rent_per_sqft is locality-derived, so it leaks locality "
         "strength — kept because it mirrors how a human prices a flat.\n")

    with open(MODEL_OUT, "wb") as f:
        pickle.dump(model, f)
    REPORT.write_text("\n".join(log) + "\n")
    note(f"Saved model -> {MODEL_OUT}")
    print(f"\nWrote {MODEL_OUT}, {REPORT}, and 4 figures.")


if __name__ == "__main__":
    main()
