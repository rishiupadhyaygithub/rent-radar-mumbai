# Decision Memo — Fair-Rent Pricing, Mumbai

**To:** Pricing Team
**From:** Analytics
**Re:** What drives Mumbai rent, where listings look mispriced, and what to fix next
**Basis:** 882 cleaned Square Yards listings across 95 localities; one linear regression, evaluated by 5-fold cross-validation.

---

## Bottom line

Rent in Mumbai is driven first by **locality**, then by **size**, with a modest, real **metro premium** on top. A one-model baseline predicts rent within a typical **±₹29,000/month** and explains about **81%** of the variation (cross-validated R² 0.81 ± 0.04 — tight across folds). It is trustworthy for mid-tier 1–3 BHK flats — the bulk of the market — and weakest on rare large flats and single-listing localities. **Use it to triage listings, not to auto-price the top end.**

## What drives rent (in plain words)

1. **Locality tier is the biggest lever.** Premium localities command ~**2× the rent-per-sqft** of budget ones (₹185 vs ₹93/sqft for a 2BHK). Worli leads the city at ₹252/sqft, ₹128 above the city average.
2. **Size (area + BHK) is the second lever** and behaves predictably within a tier.
3. **Metro proximity adds a genuine but smaller premium:** ₹137/sqft within 1.5 km of a metro vs ₹131/sqft beyond — roughly a **5% uplift**, not the headline driver some assume.
4. Furnishing and floor contribute at the margin.

## Where listings look mispriced

The model's largest gaps are the places to look first for pricing errors — or for genuinely unusual flats:

| Flat | Listed | Model says | Read |
|---|---|---|---|
| Gundavali 6BHK | ₹9.0L | ~₹4.3L | Solo locality → model **under**-prices a rare 6BHK — **human check** |
| Santacruz West 8BHK | ₹8.0L | ~₹12.5L | Lone 8BHK — model over-reaches, but a sane band now (was ₹1.27Cr) — **human check** |
| Worli 5BHK | ₹10.0L | ~₹6.2L | Luxury 5BHK, thin signal — model **under**-prices — **human check** |
| Andheri West 6BHK | ₹9.0L | ~₹5.6L | Rare 6BHK config — **under**-priced, thin signal — **human check** |
| Pali Hill 4BHK | ₹6.0L | ~₹2.7L | Solo locality → city-median fallback **under**-prices it — **human check** |

The pattern: disagreements now cluster at **rare large flats (5+ BHK) and thin single-listing localities** — no longer the order-of-magnitude blow-ups the old raw-area model produced (biggest miss ₹4.7L, not ₹12M). That is exactly where a pricing analyst's judgment adds the most value — so route those to a human, and let the model auto-clear the mid-market.

## Recommendation (prioritised)

1. **Deploy the model as a triage filter now** for 1–3 BHK flats in localities with ≥5 listings — auto-flag anything more than ±₹29k off the prediction for review. Low risk, immediate value.
2. **Exclude 4+ BHK and single-listing localities from auto-pricing** until data thickens; price those by hand.
3. **Fund data collection before model complexity.** The single highest-return investment is **more listings per locality** — the errors above are data-sparsity, not model choice. A second source (99acres/MagicBricks) to cross-check Square Yards is next.
4. **Capture amenity fields** (building age, lift, parking, balcony) at ingestion — the market prices them; we currently can't see them.

## Trade-off stated plainly

A richer model on today's 882 rows would fit the luxury tail better in-sample and generalise worse — the honest ceiling here is the **data, not the algorithm**. Spend the next rupee on rows, not on a second model.
