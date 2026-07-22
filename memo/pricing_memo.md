# Decision Memo — Fair-Rent Pricing, Mumbai

**To:** Pricing Team
**From:** Analytics
**Re:** What drives Mumbai rent, where listings look mispriced, and what to fix next
**Basis:** 119 cleaned Square Yards listings across 53 localities; one linear regression on a train/test split.

---

## Bottom line

Rent in Mumbai is driven first by **locality**, then by **size**, with a modest, real **metro premium** on top. A one-model baseline already predicts rent within a typical **±₹47,000/month** and explains **~85%** of the variation it sees (Test R² 0.848). It is trustworthy for mid-tier 1–2 BHK flats — the bulk of the market — and unreliable for luxury and rare configurations. **Use it to triage listings, not to auto-price the top end.**

## What drives rent (in plain words)

1. **Locality tier is the biggest lever.** Premium localities command ~**3× the rent-per-sqft** of budget ones (₹225 vs ₹77/sqft for a 2BHK). Bandra East leads the city at ₹260/sqft, ₹139 above the city average.
2. **Size (area + BHK) is the second lever** and behaves predictably within a tier.
3. **Metro proximity adds a genuine but smaller premium:** ₹141.6/sqft within 1.5 km of a metro vs ₹130.4/sqft beyond — roughly an **8% uplift**, not the headline driver some assume.
4. Furnishing and floor contribute at the margin.

## Where listings look mispriced

The model's largest gaps are the places to look first for pricing errors — or for genuinely unusual flats:

| Flat | Listed | Model says | Read |
|---|---|---|---|
| Versova 6BHK | ₹4.0L | ₹9.2L | Model over-reaches on a rare config — **trust the listing** |
| Juhu 5BHK | ₹5.5L | ₹3.7L | Possible **underpricing**, worth a human check |
| Bandra East 4BHK | ₹3.0L | ₹4.7L | Possible **underpricing** in a premium area |
| Prabhadevi 2BHK | ₹2.3L | ₹1.1L | Listing looks **high** for its locality/size |

The pattern: disagreements cluster at the **luxury tail and in thin localities**. That is exactly where a pricing analyst's judgment adds the most value — so route those to a human, and let the model auto-clear the mid-market.

## Recommendation (prioritised)

1. **Deploy the model as a triage filter now** for 1–3 BHK flats in localities with ≥5 listings — auto-flag anything more than ±₹47k off the prediction for review. Low risk, immediate value.
2. **Exclude 4+ BHK and single-listing localities from auto-pricing** until data thickens; price those by hand.
3. **Fund data collection before model complexity.** The single highest-return investment is **more listings per locality** — the errors above are data-sparsity, not model choice. A second source (99acres/MagicBricks) to cross-check Square Yards is next.
4. **Capture amenity fields** (building age, lift, parking, balcony) at ingestion — the market prices them; we currently can't see them.

## Trade-off stated plainly

A richer model on today's 119 rows would fit the luxury tail better in-sample and generalise worse — the honest ceiling here is the **data, not the algorithm**. Spend the next rupee on rows, not on a second model.
