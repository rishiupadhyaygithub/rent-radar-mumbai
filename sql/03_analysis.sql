-- ============================================================
-- Rent Radar — Analysis queries.
-- Demonstrates: JOIN, GROUP BY, window functions, and a CTE.
-- Each block prints a labelled result so the script reads top-to-bottom.
-- ============================================================
.mode column
.headers on

-- ------------------------------------------------------------
-- Q1. JOIN + GROUP BY
-- Average rent per BHK within each locality tier.
-- Joins each listing to its locality's tier, then aggregates.
-- ------------------------------------------------------------
SELECT '--- Q1: avg rent by tier x bhk ---' AS section;
SELECT
    loc.tier,
    l.bhk,
    COUNT(*)                       AS n,
    ROUND(AVG(l.price))            AS avg_rent,
    ROUND(AVG(l.rent_per_sqft), 1) AS avg_rent_psf
FROM listings   l
JOIN localities loc ON l.locality = loc.locality
WHERE loc.tier IS NOT NULL
GROUP BY loc.tier, l.bhk
ORDER BY
    CASE loc.tier WHEN 'budget' THEN 1 WHEN 'mid' THEN 2 ELSE 3 END,
    l.bhk;

-- ------------------------------------------------------------
-- Q2. WINDOW FUNCTION
-- Rank localities by median rent/sqft, and show each locality's
-- gap to the city-wide median (window AVG over all rows).
-- ------------------------------------------------------------
SELECT '--- Q2: locality ranking (window) ---' AS section;
SELECT
    locality,
    tier,
    n_listings,
    median_rent_per_sqft,
    RANK() OVER (ORDER BY median_rent_per_sqft DESC) AS psf_rank,
    ROUND(median_rent_per_sqft
          - AVG(median_rent_per_sqft) OVER (), 1)    AS gap_to_city_avg
FROM localities
WHERE n_listings >= 2          -- ignore single-listing localities (thin)
ORDER BY psf_rank
LIMIT 15;

-- ------------------------------------------------------------
-- Q3. CTE
-- Use a CTE to isolate metro-proximate localities (<= 1.5 km),
-- then compare their rent/sqft against far ones.
-- Tests the "metro access commands a premium" hypothesis.
-- ------------------------------------------------------------
SELECT '--- Q3: metro proximity premium (CTE) ---' AS section;
WITH metro_band AS (
    SELECT
        locality,
        median_rent_per_sqft,
        CASE WHEN avg_metro_km <= 1.5 THEN 'near_metro'
             ELSE 'far_metro' END AS band
    FROM localities
    WHERE avg_metro_km IS NOT NULL
)
SELECT
    band,
    COUNT(*)                        AS n_localities,
    ROUND(AVG(median_rent_per_sqft), 1) AS avg_rent_psf
FROM metro_band
GROUP BY band
ORDER BY avg_rent_psf DESC;
