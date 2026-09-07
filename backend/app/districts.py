"""
District registry.

Kamrup is the required district for the hackathon problem statement; the
others are added for a broader demo. The shape here makes it trivial to add
more later — just add another entry with a `climate` zone (see
app/engine/seasonal.py for what each zone means).

`boundary` is stored as [lat, lng] pairs (matches Leaflet's convention). For
every district except Kamrup, this is a deterministic, algorithmically
generated polygon (a jittered ring around the district's centroid, scaled to
its approximate area) — NOT a survey-accurate shape. It's a stand-in so the
map has something reasonable to draw for each district today.

To get an accurate boundary for any district: download the geoBoundaries
ADM2 GeoJSON for India, extract that district's feature, and save it as
`data/boundaries/<key>.geojson`. `boundary_to_geojson()` below checks for
that file first and uses it automatically if present — no code changes
needed. The static polygon here is only the fallback.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, TypedDict

from app.config import settings


class District(TypedDict):
    name: str
    state: str
    area_km2: float
    centroid: List[float]  # [lat, lng]
    climate: str  # see app/engine/seasonal.py CLIMATE_PROFILES
    boundary: List[List[float]]  # [[lat, lng], ...] — approximate fallback


DISTRICTS: Dict[str, District] = {
    "kamrup": {
        "name": "Kamrup",
        "state": "Assam",
        "area_km2": 4345.0,
        "centroid": [26.14, 91.73],
        "climate": "northeast_monsoon",
        "boundary": [
            [26.33, 91.30],
            [26.43, 91.50],
            [26.39, 91.82],
            [26.30, 92.05],
            [26.10, 92.08],
            [25.96, 91.90],
            [25.92, 91.58],
            [26.02, 91.34],
            [26.18, 91.24],
        ],
    },
    "pune": {
        "name": "Pune",
        "state": "Maharashtra",
        "area_km2": 15642.0,
        "centroid": [18.52, 73.85],
        "climate": "deccan_plateau",
        "boundary": [
            [19.302, 73.85],
            [19.126, 74.387],
            [18.627, 74.493],
            [18.267, 74.312],
            [17.924, 74.079],
            [17.878, 73.604],
            [18.213, 73.29],
            [18.648, 73.084],
            [18.966, 73.456],
        ],
    },
    "nagpur": {
        "name": "Nagpur",
        "state": "Maharashtra",
        "area_km2": 9892.0,
        "centroid": [21.15, 79.09],
        "climate": "deccan_plateau",
        "boundary": [
            [21.568, 79.09],
            [21.452, 79.361],
            [21.216, 79.492],
            [20.96, 79.442],
            [20.635, 79.291],
            [20.781, 78.946],
            [20.948, 78.714],
            [21.243, 78.525],
            [21.448, 78.822],
        ],
    },
    "bengaluru_urban": {
        "name": "Bengaluru Urban",
        "state": "Karnataka",
        "area_km2": 2196.0,
        "centroid": [12.97, 77.59],
        "climate": "deccan_plateau",
        "boundary": [
            [13.259, 77.59],
            [13.17, 77.762],
            [13.006, 77.798],
            [12.868, 77.772],
            [12.743, 77.675],
            [12.732, 77.501],
            [12.866, 77.405],
            [13.009, 77.364],
            [13.179, 77.41],
        ],
    },
    "varanasi": {
        "name": "Varanasi",
        "state": "Uttar Pradesh",
        "area_km2": 1535.0,
        "centroid": [25.32, 82.97],
        "climate": "gangetic_plain",
        "boundary": [
            [25.486, 82.97],
            [25.474, 83.113],
            [25.349, 83.151],
            [25.244, 83.115],
            [25.141, 83.042],
            [25.156, 82.904],
            [25.211, 82.762],
            [25.357, 82.736],
            [25.505, 82.798],
        ],
    },
    "ernakulam": {
        "name": "Ernakulam",
        "state": "Kerala",
        "area_km2": 2407.0,
        "centroid": [10.05, 76.35],
        "climate": "kerala_coast",
        "boundary": [
            [10.346, 76.35],
            [10.272, 76.539],
            [10.095, 76.611],
            [9.898, 76.618],
            [9.867, 76.418],
            [9.863, 76.281],
            [9.931, 76.142],
            [10.085, 76.15],
            [10.207, 76.216],
        ],
    },
}


def get_district(district_key: str) -> Optional[District]:
    return DISTRICTS.get(district_key.strip().lower())


def _real_boundary_geojson(district_key: str) -> Optional[dict]:
    """If a real geoBoundaries file has been dropped in data/boundaries/,
    use it instead of the static approximate polygon."""
    path = Path(settings.data_dir) / "boundaries" / f"{district_key}.geojson"
    if not path.exists():
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            geojson = json.load(f)
        # Normalize FeatureCollections down to their first Feature.
        if geojson.get("type") == "FeatureCollection":
            features = geojson.get("features", [])
            return features[0] if features else None
        return geojson
    except Exception:
        return None


def boundary_to_geojson(district_key: str) -> Optional[dict]:
    district = get_district(district_key)
    if district is None:
        return None

    real = _real_boundary_geojson(district_key)
    if real is not None:
        return real

    # Fallback: build a GeoJSON Feature from the static [lat, lng] ring.
    # GeoJSON wants [lng, lat], and the ring must be closed.
    ring = [[lng, lat] for lat, lng in district["boundary"]]
    ring.append(ring[0])

    return {
        "type": "Feature",
        "properties": {
            "district": district["name"],
            "state": district["state"],
            "source": "approximate",
        },
        "geometry": {
            "type": "Polygon",
            "coordinates": [ring],
        },
    }
