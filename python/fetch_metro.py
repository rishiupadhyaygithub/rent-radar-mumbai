"""
Fetch metro/subway station + route data from Overpass API for any Indian city.
Saves per-city GeoJSON + JSON files used by the frontend.

Usage:
    python3 fetch_metro.py                    # all cities
    python3 fetch_metro.py --city mumbai      # single city
    python3 fetch_metro.py --city delhi --dry-run
"""

import json, ssl, urllib.request, urllib.parse, argparse, time
from pathlib import Path

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

# ── City configs ──────────────────────────────────────────────────────────────
# bbox: (south, west, north, east)
CITY_CONFIGS = {
    "mumbai": {
        "network_pattern": "Mumbai",
        "bbox": (18.8, 72.7, 19.4, 73.1),
        "line_meta": {
            "1":  {"name": "Line 1 — Versova–Andheri–Ghatkopar", "color": "#0057A8", "status": "open",              "open_year": 2014},
            "2A": {"name": "Line 2A — Dahisar–D N Nagar",         "color": "#F7C300", "status": "open",              "open_year": 2022},
            "2B": {"name": "Line 2B — D N Nagar–Mandale",         "color": "#F7C300", "status": "partial",           "open_year": 2024},
            "3":  {"name": "Line 3 Aqua — Aarey–Cuffe Parade",    "color": "#00AEEF", "status": "open",              "open_year": 2024},
            "7":  {"name": "Line 7 — Andheri E–Dahisar E",        "color": "#E4002B", "status": "open",              "open_year": 2022},
            "9":  {"name": "Line 9 — Kashigaon–Dahisar E",        "color": "#E4002B", "status": "planned",           "open_year": 2027},
            "N1": {"name": "Navi Mumbai Metro Line 1",             "color": "#77248B", "status": "under_construction","open_year": 2025},
        },
    },
    "delhi": {
        "network_pattern": "Delhi Metro",
        "bbox": (28.4, 76.8, 28.95, 77.55),
        "line_meta": {
            "1":  {"name": "Red Line — Shahdag Marg–Rithala",        "color": "#E31837", "status": "open", "open_year": 2002},
            "2":  {"name": "Yellow Line — Samaypur Badli–HUDA City", "color": "#FFC72C", "status": "open", "open_year": 2004},
            "3":  {"name": "Blue Line — Noida–Dwarka",               "color": "#005DA0", "status": "open", "open_year": 2005},
            "4":  {"name": "Green Line — Inderlok–Brigadier Hoshiyar","color": "#00A550","status": "open", "open_year": 2010},
            "5":  {"name": "Violet Line — Kashmere Gate–Escorts Mujesar","color": "#8B008B","status": "open","open_year": 2010},
            "6":  {"name": "Orange Line — IGI Airport",              "color": "#FF6600", "status": "open", "open_year": 2011},
            "7":  {"name": "Pink Line — Majlis Park–Shiv Vihar",     "color": "#FF69B4", "status": "open", "open_year": 2018},
            "8":  {"name": "Magenta Line — Janakpuri West–Botanical", "color": "#9B2335","status": "open", "open_year": 2017},
            "9":  {"name": "Grey Line — Dwarka–Najafgarh",           "color": "#808080", "status": "open", "open_year": 2019},
        },
    },
    "bangalore": {
        "network_pattern": "Namma Metro|BMRCL",
        "bbox": (12.7, 77.4, 13.2, 77.8),
        "line_meta": {
            "Purple": {"name": "Purple Line — Challaghatta–Baiyappanahalli", "color": "#7B2D8B", "status": "open", "open_year": 2011},
            "Green":  {"name": "Green Line — Nagasandra–Silk Institute",     "color": "#008000", "status": "open", "open_year": 2014},
            "Yellow": {"name": "Yellow Line — RV Road–Bommasandra",          "color": "#FFC72C", "status": "under_construction", "open_year": 2025},
            "Pink":   {"name": "Pink Line — Kalena Agrahara–Nagawara",       "color": "#FF69B4", "status": "planned", "open_year": 2026},
        },
    },
    "hyderabad": {
        "network_pattern": "Hyderabad Metro|HMRL|L-MRTS",
        "bbox": (17.2, 78.2, 17.6, 78.7),
        "line_meta": {
            "Red":   {"name": "Red Line — Miyapur–LB Nagar",      "color": "#E31837", "status": "open", "open_year": 2017},
            "Blue":  {"name": "Blue Line — Nagole–Raidurg",        "color": "#005DA0", "status": "open", "open_year": 2017},
            "Green": {"name": "Green Line — JBS–MGBS–Falaknuma",   "color": "#008000", "status": "open", "open_year": 2018},
        },
    },
    "pune": {
        "network_pattern": "Pune Metro|MahaMetro",
        "bbox": (18.3, 73.6, 18.8, 74.0),
        "line_meta": {
            "1": {"name": "Line 1 — PCMC–Swargate",      "color": "#E31837", "status": "open",              "open_year": 2022},
            "2": {"name": "Line 2 — Vanaz–Ramwadi",      "color": "#005DA0", "status": "open",              "open_year": 2022},
            "3": {"name": "Line 3 — Hinjewadi–Shivajinagar","color": "#008000","status": "under_construction","open_year": 2025},
        },
    },
    "kolkata": {
        "network_pattern": "Kolkata Metro|KMRC",
        "bbox": (22.4, 88.2, 22.85, 88.55),
        "line_meta": {
            "1": {"name": "Blue Line — Dakshineswar–Kavi Subhas",  "color": "#005DA0", "status": "open", "open_year": 1984},
            "2": {"name": "Green Line — Howrah Maidan–Salt Lake",  "color": "#008000", "status": "open", "open_year": 2020},
            "3": {"name": "Orange Line — Noapara–Airport–Barasat", "color": "#FF6600", "status": "under_construction", "open_year": 2026},
            "4": {"name": "Purple Line — Howrah–Joka",             "color": "#7B2D8B", "status": "partial", "open_year": 2022},
            "6": {"name": "Yellow Line — New Garia–Airport",       "color": "#FFC72C", "status": "partial", "open_year": 2023},
        },
    },
    "chennai": {
        "network_pattern": "Chennai Metro|CMRL",
        "bbox": (12.8, 80.1, 13.25, 80.35),
        "line_meta": {
            "1": {"name": "Blue Line — Wimco Nagar–St Thomas Mount", "color": "#005DA0", "status": "open", "open_year": 2015},
            "2": {"name": "Green Line — Chennai Airport–Washermenpet","color": "#008000", "status": "open", "open_year": 2015},
            "3": {"name": "Line 3 — Madhavaram–SIPCOT",             "color": "#E31837", "status": "under_construction", "open_year": 2026},
            "4": {"name": "Line 4 — Poonamallee–Light House",       "color": "#FFC72C", "status": "planned", "open_year": 2027},
        },
    },
}


def fetch_overpass(cfg: dict) -> dict:
    s, w, n, e = cfg["bbox"]
    pat = cfg["network_pattern"]
    query = f"""[out:json][timeout:90];
(
  relation["route"~"subway|monorail"]["network"~"{pat}"]({s},{w},{n},{e});
  node["station"="subway"]["network"~"{pat}"]({s},{w},{n},{e});
  node["railway"="station"]["network"~"{pat}"]({s},{w},{n},{e});
  node["railway"="subway_entrance"]["network"~"{pat}"]({s},{w},{n},{e});
);
out geom;"""
    data = urllib.parse.urlencode({"data": query}).encode()
    req = urllib.request.Request(
        "https://overpass-api.de/api/interpreter",
        data=data,
        headers={"User-Agent": "maps-for-flats/1.0", "Content-Type": "application/x-www-form-urlencoded"},
    )
    with urllib.request.urlopen(req, timeout=100, context=ctx) as r:
        return json.loads(r.read())


def build_stations(raw: dict) -> list[dict]:
    seen: dict[str, dict] = {}
    for e in raw.get("elements", []):
        if e["type"] != "node":
            continue
        t = e.get("tags", {})
        name = t.get("name") or t.get("name:en", "")
        if not name or t.get("railway") == "subway_entrance":
            continue
        key = name.strip().lower()
        if key not in seen:
            lines = t.get("line", t.get("lines", "")).split(";")
            seen[key] = {
                "name": name.strip(),
                "lat":  e["lat"],
                "lng":  e["lon"],
                "lines": [l.strip() for l in lines if l.strip()],
                "is_interchange": len([l for l in lines if l.strip()]) > 1,
            }
    return list(seen.values())


def build_geojson_lines(raw: dict, line_meta: dict) -> dict:
    features = []
    seen_refs: set = set()
    for e in raw.get("elements", []):
        if e["type"] != "relation":
            continue
        t   = e.get("tags", {})
        ref = t.get("ref", t.get("colour", "?"))
        if ref in seen_refs:
            continue
        seen_refs.add(ref)
        meta = line_meta.get(ref, {})
        coords: list[list[float]] = []
        for member in e.get("members", []):
            if member.get("type") == "way" and "geometry" in member:
                for pt in member["geometry"]:
                    coords.append([pt["lon"], pt["lat"]])
        if not coords:
            continue
        features.append({
            "type": "Feature",
            "properties": {
                "ref":       ref,
                "name":      meta.get("name", t.get("name", f"Line {ref}")),
                "color":     meta.get("color", t.get("colour", "#6366f1")),
                "status":    meta.get("status", "unknown"),
                "open_year": meta.get("open_year"),
            },
            "geometry": {"type": "LineString", "coordinates": coords},
        })
    return {"type": "FeatureCollection", "features": features}


def fetch_city(city_slug: str, dry_run: bool = False) -> None:
    cfg = CITY_CONFIGS[city_slug]
    print(f"\n🚇 [{city_slug}] Fetching from Overpass…")
    try:
        raw      = fetch_overpass(cfg)
        stations = build_stations(raw)
        geojson  = build_geojson_lines(raw, cfg["line_meta"])
        print(f"   {len(stations)} stations | {len(geojson['features'])} route lines")
    except Exception as ex:
        print(f"   ❌ Overpass failed: {ex}")
        # Write empty fallback files so the clean step doesn't crash on a missing file
        stations = []
        geojson  = {"type": "FeatureCollection", "features": []}

    if dry_run:
        print("   Dry run — not saving")
        return

    out_dir = Path(__file__).parent.parent / "data" / "geo"
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / f"metro_lines_{city_slug}.geojson", "w") as f:
        json.dump(geojson, f)
    with open(out_dir / f"metro_stations_{city_slug}.json", "w") as f:
        json.dump(stations, f)
    print(f"   Saved → data/geo/metro_lines_{city_slug}.geojson + metro_stations_{city_slug}.json")
    for s in stations[:3]:
        print(f"     {s['name']} ({s['lat']:.4f}, {s['lng']:.4f})")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--city", choices=list(CITY_CONFIGS.keys()), help="Fetch single city (default: all)")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    cities = [args.city] if args.city else list(CITY_CONFIGS.keys())
    print(f"Fetching metro data for: {', '.join(cities)}")

    for i, city in enumerate(cities):
        fetch_city(city, dry_run=args.dry_run)
        if i < len(cities) - 1:
            time.sleep(2)   # be kind to Overpass

    print("\n✅ Done")
