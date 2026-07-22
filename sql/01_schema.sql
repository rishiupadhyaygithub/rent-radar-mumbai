-- ============================================================
-- Rent Radar — Schema (SQLite)
-- Two related tables. listings.locality is a FK into localities.locality.
-- Run order: 01_schema.sql -> 02_load.sql -> 03_analysis.sql
-- ============================================================

DROP TABLE IF EXISTS listings;
DROP TABLE IF EXISTS localities;

-- Parent table: one row per locality (the attributes we JOIN against).
CREATE TABLE localities (
    locality              TEXT PRIMARY KEY,
    n_listings            INTEGER NOT NULL,
    median_rent           REAL,
    median_rent_per_sqft  REAL,
    avg_metro_km          REAL,
    tier                  TEXT CHECK (tier IN ('budget','mid','premium'))
);

-- Child table: one row per rental listing.
CREATE TABLE listings (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    source          TEXT,
    locality        TEXT REFERENCES localities(locality),
    city            TEXT,
    bhk             INTEGER,
    price           INTEGER NOT NULL,      -- monthly rent in rupees
    price_unit      TEXT,
    area_sqft       REAL,
    floor           REAL,
    furnishing      TEXT,
    url             TEXT,
    scraped_locality TEXT,
    lat             REAL,
    lng             REAL,
    location_exact  INTEGER,
    floor_missing   INTEGER,               -- 1 = floor was imputed
    rent_per_sqft   REAL,
    metro_km        REAL                   -- km to nearest metro station
);

CREATE INDEX idx_listings_locality ON listings(locality);
CREATE INDEX idx_listings_bhk      ON listings(bhk);
