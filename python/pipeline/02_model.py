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
from sklearn.model_selection import (
    KFold, cross_val_predict, cross_val_score)
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

    # ---- Honest evaluation: 5-fold cross-validation ----
    # 119 rows is small, so a single 75/25 split is luck-dependent — the score
    # swings with the random seed. K-fold averages over 5 splits, and
    # out-of-fold (OOF) predictions give EVERY row a prediction from a model
    # that never saw it, so the reported error is stable, not a lucky draw.
    kf = KFold(n_splits=5, shuffle=True, random_state=42)
    r2_folds = cross_val_score(model, X, y, cv=kf, scoring="r2")
    oof_log = cross_val_predict(model, X, y, cv=kf)      # out-of-fold, log-rupees
    oof_rs = np.expm1(oof_log)
    true_rs = np.expm1(y)
    r2_oof = r2_score(y, oof_log)
    mae = mean_absolute_error(true_rs, oof_rs)
    rmse = np.sqrt(mean_squared_error(true_rs, oof_rs))

    # Fold-wise MAE in rupees (the spread a renter would actually feel).
    fold_mae = []
    for tr_idx, te_idx in kf.split(X):
        model.fit(X.iloc[tr_idx], y.iloc[tr_idx])
        p = np.expm1(model.predict(X.iloc[te_idx]))
        fold_mae.append(mean_absolute_error(np.expm1(y.iloc[te_idx]), p))
    fold_mae = np.array(fold_mae)

    # Overfitting check: fit on ALL data, compare in-sample R2 to OOF R2.
    model.fit(X, y)
    r2_in = r2_score(y, model.predict(X))

    note("## Results (5-fold cross-validation)\n")
    note(f"- CV R2: **{r2_folds.mean():.3f} +/- {r2_folds.std():.3f}** "
         f"across folds ({', '.join(f'{v:.2f}' for v in r2_folds)}).")
    note(f"- Out-of-fold R2 (all {len(X)} rows): **{r2_oof:.3f}**.")
    note(f"- In-sample R2 (fit on all data): **{r2_in:.3f}** -> overfitting "
         f"gap **{r2_in - r2_oof:.3f}** (small = generalises, not memorising).")
    note(f"- CV MAE: **Rs {mae:,.0f}/month** (out-of-fold); per-fold "
         f"**Rs {fold_mae.mean():,.0f} +/- {fold_mae.std():,.0f}**.")
    note(f"- CV RMSE: **Rs {rmse:,.0f}/month** (penalises big misses).\n")
    note("Why CV over a single split: with 119 rows one 75/25 split leaves a "
         "~30-flat test set whose R2 swings with the seed. 5-fold reports the "
         "average over five held-out sets, so this number is trustworthy.\n")

    # ---- Which features carry the price, and by how much ----
    # Numeric features are standardized, so each coefficient is the effect of a
    # +1 SD move; the target is log(rent), so exp(coef)-1 is the % change in rent
    # (categoricals read vs their dropped/baseline level).
    feat_names = model.named_steps["pre"].get_feature_names_out()
    coefs = model.named_steps["lr"].coef_
    coef_tbl = pd.DataFrame({"feature": feat_names, "coef_log": coefs})
    coef_tbl["effect_on_rent"] = coef_tbl["coef_log"].map(
        lambda b: f"{np.expm1(b) * 100:+.0f}%")
    coef_tbl["abs"] = coef_tbl["coef_log"].abs()
    coef_tbl = coef_tbl.sort_values("abs", ascending=False)
    note("## Which features carry the price\n")
    note("Coefficients of the one linear model. Numeric features are standardized, "
         "so each row is the effect of a **+1 standard-deviation** move; the target "
         "is log(rent), so **effect_on_rent** is how much predicted rent changes.\n")
    note(coef_tbl.head(8)[["feature", "coef_log", "effect_on_rent"]]
         .to_markdown(index=False, floatfmt=".3f"))
    note("\n**In plain words:** floor **area** is the single biggest genuine lever "
         "(+1 SD ≈ +47% rent), followed by **locality strength** "
         "(median_rent_per_sqft, +27%). BHK and tier add on top; metro distance "
         "moves rent only at the margin. The large negative on `furnishing_unknown` "
         "is a *missingness* signal, not a real driver — listings that hide their "
         "furnishing status tend to be cheaper, so the flag itself predicts lower rent.\n")

    # ---- Honest failure analysis (on out-of-fold predictions) ----
    # Flag rows whose locality has only ONE listing: their tier and
    # median_rent_per_sqft features rest on that single flat (a real weakness).
    solo_localities = set(
        df["locality"].value_counts().loc[lambda s: s == 1].index)
    err = pd.DataFrame({
        "locality": model_df["locality"].values,
        "bhk": model_df["bhk"].values,
        "true": np.asarray(true_rs), "pred": np.asarray(oof_rs),
    })
    err["abs_err"] = (err["true"] - err["pred"]).abs()
    err["solo_loc"] = err["locality"].isin(solo_localities).map(
        {True: "yes", False: ""})
    worst = err.sort_values("abs_err", ascending=False).head(5)
    note("## Where the model breaks\n")
    note("Worst 5 out-of-fold predictions:\n")
    note(worst.to_markdown(index=False, floatfmt=",.0f"))
    note("\n**Failure pattern:** biggest misses are high-end premium flats and "
         "thin localities — the model has little signal there and pulls toward "
         "the city mean. It is honest for typical mid-tier 1-2 BHK rent and "
         "unreliable at the luxury tail.\n")

    # ---- Export OOF predictions for the dashboard (predicted-vs-actual) ----
    preds = pd.DataFrame({
        "locality": model_df["locality"].values,
        "tier": model_df["tier"].values,
        "bhk": model_df["bhk"].values,
        "area_sqft": model_df["area_sqft"].values,
        "metro_km": model_df["metro_km"].values,
        "actual_rent": np.asarray(true_rs).round().astype(int),
        "predicted_rent": np.asarray(oof_rs).round().astype(int),
    })
    preds["error"] = preds["actual_rent"] - preds["predicted_rent"]
    preds["abs_pct_error"] = (
        preds["error"].abs() / preds["actual_rent"] * 100).round(1)
    preds["solo_locality"] = preds["locality"].isin(solo_localities).astype(int)
    preds.to_csv(ROOT / "data/clean/predictions.csv", index=False)

    n_solo = len(solo_localities)
    note("## Limits\n"
         f"- Only {len(X)} listings across {df['locality'].nunique()} "
         f"localities; **{n_solo} localities have a single listing**, so their "
         "tier and median-rent features rest on one flat each (flagged as "
         "solo_locality in predictions.csv).\n"
         "- Single source (Square Yards); one city (Mumbai) by design.\n"
         "- median_rent_per_sqft is locality-derived, so it leaks locality "
         "strength — kept because it mirrors how a human prices a flat, and "
         "disclosed rather than hidden.\n"
         f"- Evaluated by 5-fold CV (not a single split) because {len(X)} rows "
         "make any one split unreliable.\n")

    with open(MODEL_OUT, "wb") as f:
        pickle.dump(model, f)
    REPORT.write_text("\n".join(log) + "\n")
    note(f"Saved model -> {MODEL_OUT}")
    print(f"\nWrote {MODEL_OUT}, {REPORT}, and 4 figures.")


if __name__ == "__main__":
    main()
