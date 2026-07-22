-- ============================================================
-- Rent Radar — Load cleaned CSVs into SQLite.
-- Run from the project root with:
--   sqlite3 rent_radar.db < sql/01_schema.sql
--   sqlite3 rent_radar.db < sql/02_load.sql
--   sqlite3 rent_radar.db < sql/03_analysis.sql
-- ============================================================

.mode csv

-- Load parent first (localities), then children (listings).
-- .import --skip 1 skips the header row of each CSV.
.import --skip 1 data/clean/localities.csv localities

-- listings CSV has no id column; load into a temp shape then insert.
DROP TABLE IF EXISTS listings_stage;
CREATE TABLE listings_stage (
    source TEXT, locality TEXT, city TEXT, bhk TEXT, price TEXT,
    price_unit TEXT, area_sqft TEXT, floor TEXT, furnishing TEXT, url TEXT,
    scraped_locality TEXT, lat TEXT, lng TEXT, location_exact TEXT,
    floor_missing TEXT, rent_per_sqft TEXT, metro_km TEXT
);
.import --skip 1 data/clean/listings_clean.csv listings_stage

INSERT INTO listings
    (source, locality, city, bhk, price, price_unit, area_sqft, floor,
     furnishing, url, scraped_locality, lat, lng, location_exact,
     floor_missing, rent_per_sqft, metro_km)
SELECT
    source, locality, city,
    CAST(bhk AS INTEGER), CAST(price AS INTEGER), price_unit,
    CAST(area_sqft AS REAL), CAST(floor AS REAL), furnishing, url,
    scraped_locality,
    CAST(NULLIF(lat,'') AS REAL), CAST(NULLIF(lng,'') AS REAL),
    CAST(NULLIF(location_exact,'') AS INTEGER),
    CAST(floor_missing AS INTEGER), CAST(rent_per_sqft AS REAL),
    CAST(NULLIF(metro_km,'') AS REAL)
FROM listings_stage;

DROP TABLE listings_stage;

-- Sanity counts.
SELECT 'localities' AS tbl, COUNT(*) AS rows FROM localities
UNION ALL
SELECT 'listings',  COUNT(*) FROM listings;
