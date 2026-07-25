"""
Square Yards Multi-City Scraper — parses schema.org JSON-LD (no browser needed)
Square Yards embeds structured listing data directly in HTML — reliable, fast.

Usage:
    python3 scraper.py                                   # Mumbai, 5 pages
    python3 scraper.py --city delhi --pages 10
    python3 scraper.py --city bangalore --pages 8
    python3 scraper.py --debug --city hyderabad

Supported cities: mumbai, delhi, pune, bangalore, hyderabad, kolkata, chennai
"""
from __future__ import annotations   # lazy annotations: run on Python 3.9

import csv
import json
import re
import time
import random
import argparse
import urllib.request
import urllib.error
import ssl
from pathlib import Path

# ── SSL fix (macOS Python 3.10) ────────────────────────────────────────────────

_SSL = ssl.create_default_context()
_SSL.check_hostname = False
_SSL.verify_mode = ssl.CERT_NONE

# ── City URL slugs on Square Yards ─────────────────────────────────────────────
CITY_URL_SLUGS = {
    "mumbai":    "mumbai",
    "delhi":     "delhi",
    "noida":     "noida",
    "gurgaon":   "gurgaon",
    "pune":      "pune",
    "bangalore": "bangalore",
    "hyderabad": "hyderabad",
    "kolkata":   "kolkata",
    "chennai":   "chennai",
}

# Supabase city name (must match CITIES[slug].dbName in utils.ts)
CITY_DB_NAMES = {
    "mumbai":    "Mumbai",
    "delhi":     "Delhi",
    "noida":     "Delhi",    # Noida → stored as Delhi (same metro, same city filter)
    "gurgaon":   "Delhi",
    "pune":      "Pune",
    "bangalore": "Bangalore",
    "hyderabad": "Hyderabad",
    "kolkata":   "Kolkata",
    "chennai":   "Chennai",
}

# Config built at runtime from --city arg
BASE_URL      = ""
OUTPUT_FILE   = ""
_CITY_DB_NAME = "Mumbai"   # overridden by __main__

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-IN,en;q=0.9",
    "Accept-Encoding": "gzip, deflate",
}

# ── Fetcher ────────────────────────────────────────────────────────────────────

def fetch_html(url: str) -> str | None:
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=20, context=_SSL) as r:
            raw = r.read()
            # handle gzip
            if r.headers.get("Content-Encoding") == "gzip":
                import gzip
                raw = gzip.decompress(raw)
            return raw.decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        print(f"  HTTP {e.code} for {url}")
        return None
    except Exception as e:
        print(f"  Error fetching {url}: {e}")
        return None

# ── Parser ─────────────────────────────────────────────────────────────────────

def parse_price(text: str) -> tuple[int | None, str]:
    """Returns (price_int, unit). Unit = per_month or total."""
    if not text:
        return None, "per_month"
    t = str(text).replace(",", "").replace("₹", "").replace("₹", "").strip()
    m = re.search(r"[\d.]+", t)
    if not m:
        return None, "per_month"
    num = float(m.group())
    t_lower = t.lower()
    if "cr" in t_lower:
        return int(num * 10_000_000), "total"
    if "lakh" in t_lower or (" l" in t_lower and "floor" not in t_lower):
        return int(num * 100_000), "per_month"
    if "k" in t_lower:
        return int(num * 1_000), "per_month"
    return int(num), "per_month"

def parse_bhk(text: str) -> int | None:
    m = re.search(r"(\d+)\s*(?:BHK|bhk|bed)", str(text))
    return int(m.group(1)) if m else None

def parse_area(text: str) -> int | None:
    m = re.search(r"(\d[\d,]*)\s*(?:sq\.?\s*ft|sqft|square feet)", str(text), re.IGNORECASE)
    if m:
        return int(m.group(1).replace(",", ""))
    return None

def parse_floor(text: str) -> tuple[int | None, int | None]:
    m = re.search(r"(\d+)\s*(?:of|/)\s*(\d+)", str(text))
    if m:
        return int(m.group(1)), int(m.group(2))
    m = re.search(r"(\d+)\s*(?:st|nd|rd|th)?\s*floor", str(text), re.IGNORECASE)
    if m:
        return int(m.group(1)), None
    return None, None

def furnish_label(text: str) -> str | None:
    t = str(text).lower()
    if "semi" in t:
        return "semi-furnished"
    if "unfurnished" in t:
        return "unfurnished"
    if "furnished" in t:
        return "furnished"
    return None

def parse_btn_attrs(html: str) -> dict[str, dict]:
    """
    Parse data-* attributes from div.favorite-btn elements.
    Returns dict keyed by URL → {price, locality, bhk, area, furnishing, floor}.
    Price lives in data-price (integer rupees). Geo lives only in schema.org.
    """
    btn_re  = re.compile(r'<div class="favorite-btn[^"]*"([^>]+)>', re.IGNORECASE)
    attr_re = re.compile(r'data-([\w-]+)="([^"]*)"')
    result: dict[str, dict] = {}

    for m in btn_re.finditer(html):
        attrs = dict(attr_re.findall(m.group(1)))
        url = attrs.get("url", "").strip()
        if not url:
            continue
        price_raw = attrs.get("price", "")
        price = int(price_raw) if price_raw.isdigit() else None
        result[url] = {
            "price":      price,
            "locality":   attrs.get("sublocalityname", "").split(",")[0].strip(),
            "bhk":        parse_bhk(attrs.get("unittype", "")),
            "area_sqft":  parse_area(attrs.get("area", "")),
            "furnishing": furnish_label(attrs.get("propstatus", "")),
        }
    return result


def extract_from_schema(blob: dict) -> dict | None:
    """Extract geo+floor from schema.org Apartment blob. Price comes from btn attrs."""
    try:
        name  = blob.get("name", "")
        desc  = blob.get("description", "")
        addr  = blob.get("address", {})
        geo   = blob.get("geo", {})
        url   = blob.get("url", "")

        locality = addr.get("streetAddress") or addr.get("addressLocality") or ""
        lat      = float(geo["latitude"])  if geo.get("latitude")  else None
        lng      = float(geo["longitude"]) if geo.get("longitude") else None

        # Floor: prefer explicit floorlevel field, fall back to description
        floor_raw = blob.get("floorlevel")
        if floor_raw is not None:
            floor = int(floor_raw)
            total_floors = None
            # Try getting total floors from description ("12th floor of the 39-story")
            m = re.search(r"(\d+)-stor", desc, re.IGNORECASE)
            if m:
                total_floors = int(m.group(1))
        else:
            floor, total_floors = parse_floor(desc)

        # Area from floorSize field (more reliable than description)
        area_raw = blob.get("floorSize", "")
        area = parse_area(area_raw) or parse_area(desc)

        if not url:
            return None

        return {
            "_url":         url,
            "lat":          lat,
            "lng":          lng,
            "floor":        floor,
            "total_floors": total_floors,
            "area_sqft":    area,
            "bhk_fallback": parse_bhk(name) or parse_bhk(desc),
            "loc_fallback": locality.split(",")[0].strip(),
            "furn_fallback":furnish_label(desc) or furnish_label(name),
        }
    except Exception:
        return None


def parse_page(html: str) -> list[dict]:
    """Merge schema.org geo data with favorite-btn price/locality data."""
    # Step 1: parse price/locality from HTML data attrs
    btn_data = parse_btn_attrs(html)

    # Step 2: parse schema.org blobs for geo + floor
    schema_data: dict[str, dict] = {}
    pattern = re.compile(
        r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
        re.DOTALL | re.IGNORECASE,
    )
    for match in pattern.finditer(html):
        raw = match.group(1).strip()
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            continue
        items = data if isinstance(data, list) else [data]
        if isinstance(data, dict) and "@graph" in data:
            items = data["@graph"]
        for item in items:
            t = item.get("@type", "")
            if any(x in str(t) for x in ["Apartment", "Residence", "House", "RealEstate"]):
                geo_rec = extract_from_schema(item)
                if geo_rec:
                    schema_data[geo_rec["_url"]] = geo_rec

    # Step 3: merge
    listings: list[dict] = []
    all_urls = set(btn_data) | set(schema_data)

    for url in all_urls:
        btn  = btn_data.get(url, {})
        geo  = schema_data.get(url, {})

        price    = btn.get("price")
        bhk      = btn.get("bhk") or geo.get("bhk_fallback")
        locality = btn.get("locality") or geo.get("loc_fallback") or "Mumbai"
        area     = btn.get("area_sqft") or geo.get("area_sqft")
        furn     = btn.get("furnishing") or geo.get("furn_fallback")

        if not bhk and not price:
            continue

        slug = url.rstrip("/").split("/")[-1]

        listings.append({
            "source":          "squareyards",
            "locality":        locality,
            "city":            _CITY_DB_NAME,
            "bhk":             bhk,
            "price":           price,
            "price_unit":      "per_month",
            "deposit":         None,
            "area_sqft":       area,
            "floor":           geo.get("floor"),
            "total_floors":    geo.get("total_floors"),
            "furnishing":      furn,
            "url":             url,
            "scraped_locality": locality,
            "lat":             geo.get("lat"),
            "lng":             geo.get("lng"),
            "location_exact":  geo.get("lat") is not None,
        })

    return listings

# ── Main ───────────────────────────────────────────────────────────────────────

def scrape(pages: int, output: str) -> None:
    all_listings: list[dict] = []
    seen_ids: set[str] = set()

    for page_num in range(1, pages + 1):
        url = BASE_URL if page_num == 1 else f"{BASE_URL}?page={page_num}"
        print(f"  Page {page_num}/{pages}: {url} … ", end="", flush=True)

        html = fetch_html(url)
        if not html:
            print("failed")
            break

        batch = parse_page(html)

        # Deduplicate
        new = []
        for l in batch:
            key = l.get("url") or f"{l.get('lat')},{l.get('lng')},{l.get('price')}"
            if key not in seen_ids:
                seen_ids.add(key)
                new.append(l)

        all_listings.extend(new)
        print(f"{len(new)} listings (total: {len(all_listings)})")

        if page_num < pages:
            time.sleep(random.uniform(1.2, 2.5))

    if not all_listings:
        print("\n⚠️  0 listings. Run with --debug to inspect the page.")
        return

    fieldnames = [
        "source", "locality", "city", "bhk", "price", "price_unit",
        "deposit", "area_sqft", "floor", "total_floors", "furnishing",
        "url", "scraped_locality", "lat", "lng", "location_exact",
    ]
    with open(output, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(all_listings)

    print(f"\n✅ {len(all_listings)} listings → {output}")

    # Price stats
    prices = [l["price"] for l in all_listings if l.get("price")]
    if prices:
        print(f"   Price range : ₹{min(prices):,} – ₹{max(prices):,}/mo")
        print(f"   Avg rent    : ₹{sum(prices)//len(prices):,}/mo")

    bhks = {}
    for l in all_listings:
        b = str(l.get("bhk") or "?")
        bhks[b] = bhks.get(b, 0) + 1
    print(f"   BHK mix     : {dict(sorted(bhks.items()))}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Square Yards multi-city scraper")
    parser.add_argument("--city",   default="mumbai", choices=list(CITY_URL_SLUGS.keys()),
                        help="City to scrape (default: mumbai)")
    parser.add_argument("--pages",  type=int, default=5, help="Pages to scrape (each ~20 listings)")
    parser.add_argument("--output", default=None, help="CSV output filename")
    parser.add_argument("--debug",  action="store_true", help="Print first page schema.org blobs")
    args = parser.parse_args()

    city_slug = args.city
    url_slug  = CITY_URL_SLUGS[city_slug]
    import sys as _sys
    # Update module-level globals used by parse_page + scrape
    _this = _sys.modules[__name__]
    _this.BASE_URL      = f"https://www.squareyards.com/rent/property-for-rent-in-{url_slug}"
    _this._CITY_DB_NAME = CITY_DB_NAMES[city_slug]
    BASE_URL = _this.BASE_URL
    output   = args.output or f"{city_slug}_flats.csv"

    if args.debug:
        html = fetch_html(BASE_URL)
        if not html:
            raise SystemExit(1)
        listings = parse_page(html)
        print(f"\nFound {len(listings)} listings on page 1. First 2:\n")
        for l in listings[:2]:
            print(json.dumps(l, indent=2))
        raise SystemExit(0)

    print(f"\n🏠 Square Yards Scraper — {CITY_DB_NAMES[city_slug]}")
    print(f"   URL    : {BASE_URL}")
    print(f"   Pages  : {args.pages} (~{args.pages * 20} listings)")
    print(f"   Output : {output}\n")

    scrape(args.pages, output)
