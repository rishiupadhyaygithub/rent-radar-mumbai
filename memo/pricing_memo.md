# Decision Memo — Fair-Rent Pricing, Mumbai

**To:** Pricing Team
**From:** Analytics
**Re:** What drives Mumbai rent, where listings look mispriced, and what to fix next
**Basis:** 119 cleaned Square Yards listings across 53 localities; one linear regression, evaluated by 5-fold cross-validation.

---

## Bottom line

Rent in Mumbai is driven first by **locality**, then by **size**, with a modest, real **metro premium** on top. A one-model baseline predicts rent within a typical **±₹38,000/month** and explains about **80%** of the variation (cross-validated R² 0.80 ± 0.10). It is trustworthy for mid-tier 1–2 BHK flats — the bulk of the market — and unreliable for luxury and rare configurations. **Use it to triage listings, not to auto-price the top end.**

## What drives rent (in plain words)

1. **Locality tier is the biggest lever.** Premium localities command ~**3× the rent-per-sqft** of budget ones (₹225 vs ₹77/sqft for a 2BHK). Bandra East leads the city at ₹260/sqft, ₹139 above the city average.
2. **Size (area + BHK) is the second lever** and behaves predictably within a tier.
3. **Metro proximity adds a genuine but smaller premium:** ₹141.6/sqft within 1.5 km of a metro vs ₹130.4/sqft beyond — roughly an **8% uplift**, not the headline driver some assume.
4. Furnishing and floor contribute at the margin.

## Where listings look mispriced

The model's largest gaps are the places to look first for pricing errors — or for genuinely unusual flats:

| Flat | Listed | Model says | Read |
|---|---|---|---|
| Versova 6BHK | ₹4.0L | ~₹9.0L | Model over-reaches on a rare config — **trust the listing** |
| Bandra East 4BHK | ₹5.0L | ₹9.4L | Rare premium config, thin signal — **human check** |
| Dadar West 2BHK | ₹3.1L | ₹5.5L | Single-listing locality — feature rests on one flat |
| Juhu 5BHK | ₹5.5L | ₹3.8L | Possible **underpricing**, worth a human check |

The pattern: disagreements cluster at the **luxury tail and in thin localities** (several are single-listing areas). That is exactly where a pricing analyst's judgment adds the most value — so route those to a human, and let the model auto-clear the mid-market.

## Recommendation (prioritised)

1. **Deploy the model as a triage filter now** for 1–3 BHK flats in localities with ≥5 listings — auto-flag anything more than ±₹38k off the prediction for review. Low risk, immediate value.
2. **Exclude 4+ BHK and single-listing localities from auto-pricing** until data thickens; price those by hand.
3. **Fund data collection before model complexity.** The single highest-return investment is **more listings per locality** — the errors above are data-sparsity, not model choice. A second source (99acres/MagicBricks) to cross-check Square Yards is next.
4. **Capture amenity fields** (building age, lift, parking, balcony) at ingestion — the market prices them; we currently can't see them.

## Trade-off stated plainly

A richer model on today's 119 rows would fit the luxury tail better in-sample and generalise worse — the honest ceiling here is the **data, not the algorithm**. Spend the next rupee on rows, not on a second model.
