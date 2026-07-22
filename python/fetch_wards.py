"""
Fetch Mumbai BMC ward GeoJSON → annotate with flood risk → save for frontend.
Flood risk levels based on BMC Disaster Management data + NDMA reports.

Usage:
    python3 fetch_wards.py
"""

import json, ssl, urllib.request
from pathlib import Path

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

# ── BMC ward flood risk (sourced from BMC DPAR + NDMA 2017/2023 reports) ─────
# Very high = chronic flooding, documented inundation > 1m in heavy rain
# High      = frequent waterlogging, low-lying areas
# Medium    = occasional waterlogging
# Low       = elevated / well-drained

FLOOD_RISK: dict[str, dict] = {
    "A":  {"risk": "low",       "label": "Colaba / Churchgate",       "notes": "Coastal but well-drained"},
    "B":  {"risk": "medium",    "label": "Dongri / Mandvi",           "notes": "Low-lying pockets near sea"},
    "C":  {"risk": "medium",    "label": "Byculla / Nagpada",         "notes": "Mithi River proximity"},
    "D":  {"risk": "medium",    "label": "Worli / Prabhadevi",        "notes": "Coastal flooding risk"},
    "E":  {"risk": "very_high", "label": "Sion / Dharavi",            "notes": "Mithi River flood plain — chronic"},
    "F/N":{"risk": "high",      "label": "Matunga / Wadala",          "notes": "Low-lying, drainage issues"},
    "F/S":{"risk": "medium",    "label": "Dadar / Matunga West",      "notes": "Better drainage"},
    "G/N":{"risk": "very_high", "label": "Goregaon / Malad",          "notes": "Dahisar River + chronic spots"},
    "G/S":{"risk": "high",      "label": "Goregaon South / Versova",  "notes": "Seasonal flooding"},
    "H/E":{"risk": "very_high", "label": "Bandra East / Kurla",       "notes": "Mithi River — worst flood zone"},
    "H/W":{"risk": "high",      "label": "Bandra West",               "notes": "Coastal + drainage risk"},
    "K/E":{"risk": "very_high", "label": "Andheri East / Sahar",      "notes": "Airport area, chronic flooding"},
    "K/W":{"risk": "high",      "label": "Andheri West / Versova",    "notes": "Low-lying pockets"},
    "L":  {"risk": "medium",    "label": "Kurla / Ghatkopar",         "notes": "Partial Mithi flood risk"},
    "M/E":{"risk": "medium",    "label": "Chembur East",              "notes": "Elevated areas"},
    "M/W":{"risk": "medium",    "label": "Chembur West / Govandi",    "notes": "Some low-lying areas"},
    "N":  {"risk": "low",       "label": "Ghatkopar / Vikhroli",      "notes": "Elevated terrain"},
    "P/N":{"risk": "medium",    "label": "Borivali North",            "notes": "Dahisar River proximity"},
    "P/S":{"risk": "medium",    "label": "Borivali South / Kandivali","notes": "Occasional waterlogging"},
    "R/C":{"risk": "high",      "label": "Dahisar / Kandivali East",  "notes": "Dahisar River flood zone"},
    "R/N":{"risk": "high",      "label": "Dahisar North",             "notes": "Dahisar River upstream"},
    "R/S":{"risk": "medium",    "label": "Malad East / Kandivali",    "notes": "Partial flood risk"},
    "S":  {"risk": "low",       "label": "Mulund / Bhandup",          "notes": "Elevated Ghat terrain"},
    "T":  {"risk": "low",       "label": "Powai / Vikhroli East",     "notes": "Powai lake drainage"},
}

RISK_COLORS = {
    "very_high": "#dc2626",  # red
    "high":      "#ea580c",  # orange
    "medium":    "#ca8a04",  # amber
    "low":       "#16a34a",  # green
}

RISK_LABELS = {
    "very_high": "Very High Flood Risk",
    "high":      "High Flood Risk",
    "medium":    "Moderate Flood Risk",
    "low":       "Low Flood Risk",
}


def fetch_ward_geojson() -> dict:
    url = "https://raw.githubusercontent.com/datameet/Municipal_Spatial_Data/master/Mumbai/BMC_Wards.geojson"
    req = urllib.request.Request(url, headers={"User-Agent": "maps-for-flats/1.0"})
    with urllib.request.urlopen(req, timeout=30, context=ctx) as r:
        return json.loads(r.read())


def annotate(geojson: dict) -> dict:
    """Add flood risk data to each ward feature."""
    for feature in geojson.get("features", []):
        props = feature.get("properties", {})
        ward  = str(props.get("name", "")).strip().upper()

        # Try exact match first, then prefix match
        meta = FLOOD_RISK.get(ward)
        if not meta:
            for key in FLOOD_RISK:
                if ward.startswith(key) or key.startswith(ward):
                    meta = FLOOD_RISK[key]
                    break

        if meta:
            risk  = meta["risk"]
            props.update({
                "flood_risk":   risk,
                "flood_color":  RISK_COLORS[risk],
                "flood_label":  RISK_LABELS[risk],
                "ward_label":   meta["label"],
                "flood_notes":  meta["notes"],
            })
        else:
            props.update({
                "flood_risk":  "medium",
                "flood_color": RISK_COLORS["medium"],
                "flood_label": RISK_LABELS["medium"],
                "ward_label":  ward,
                "flood_notes": "",
            })

        feature["properties"] = props

    return geojson


if __name__ == "__main__":
    print("🌊 Fetching BMC ward boundaries…")
    geojson = fetch_ward_geojson()
    features = geojson.get("features", [])
    print(f"   {len(features)} wards fetched")

    annotated = annotate(geojson)

    out_dir = Path(__file__).parent.parent / "public" / "data"
    out_dir.mkdir(parents=True, exist_ok=True)

    with open(out_dir / "ward_flood_risk.geojson", "w") as f:
        json.dump(annotated, f)

    print(f"   Saved → public/data/ward_flood_risk.geojson")

    # Summary
    from collections import Counter
    counts = Counter(
        f["properties"]["flood_risk"]
        for f in annotated["features"]
    )
    for risk in ["very_high", "high", "medium", "low"]:
        print(f"   {RISK_LABELS[risk]}: {counts.get(risk, 0)} wards")
