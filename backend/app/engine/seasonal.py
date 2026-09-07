"""
Synthetic-but-realistic fallback indicators.

Until real Sentinel-2 / CHIRPS / JRC rasters exist for a district+month (see
engine/geoprocessing.py and data/README.md), this module produces
deterministic, seasonally-plausible numbers so the API and frontend work
end-to-end today.

Deterministic: the same (district, month) always returns the same numbers
(seeded from a hash of the two), so repeated requests are stable instead of
jumping around on every refresh.

Different districts have different climates, so profiles are keyed by a
`climate` zone (set per-district in app/districts.py), not applied uniformly:

  - northeast_monsoon : Assam-style — very wet Jun-Sep, dry winter
  - deccan_plateau     : Maharashtra/Karnataka plateau — moderate monsoon,
                         hot dry summer, mild winter
  - gangetic_plain     : UP-style — hot dry pre-monsoon, monsoon Jul-Sep,
                         cool winter
  - kerala_coast       : two monsoons (SW Jun-Sep heavy, NE Oct-Nov), high
                         NDVI and water coverage nearly year-round

IMPORTANT: this is clearly a placeholder, not measured data. Once real
rasters are present for a district+month, geoprocessing.py computes real
stats and this module is skipped automatically for that indicator — no code
changes needed elsewhere.
"""

import hashlib
import random

CLIMATE_PROFILES = {
    "northeast_monsoon": {
        "01": {"rain": (5, 20), "ndvi": (0.25, 0.35), "water": (1.0, 2.0)},
        "02": {"rain": (10, 30), "ndvi": (0.28, 0.38), "water": (1.2, 2.2)},
        "03": {"rain": (30, 70), "ndvi": (0.32, 0.44), "water": (1.5, 2.8)},
        "04": {"rain": (90, 160), "ndvi": (0.38, 0.50), "water": (2.0, 3.5)},
        "05": {"rain": (200, 300), "ndvi": (0.46, 0.58), "water": (3.0, 5.0)},
        "06": {"rain": (350, 480), "ndvi": (0.55, 0.68), "water": (4.5, 7.5)},
        "07": {"rain": (380, 500), "ndvi": (0.58, 0.70), "water": (5.5, 9.0)},
        "08": {"rain": (300, 420), "ndvi": (0.56, 0.68), "water": (5.0, 8.0)},
        "09": {"rain": (200, 320), "ndvi": (0.52, 0.64), "water": (4.0, 6.5)},
        "10": {"rain": (90, 180), "ndvi": (0.44, 0.56), "water": (2.8, 4.5)},
        "11": {"rain": (15, 40), "ndvi": (0.35, 0.46), "water": (1.8, 3.0)},
        "12": {"rain": (5, 25), "ndvi": (0.28, 0.38), "water": (1.2, 2.2)},
    },
    "deccan_plateau": {
        "01": {"rain": (2, 10), "ndvi": (0.18, 0.28), "water": (0.5, 1.2)},
        "02": {"rain": (2, 12), "ndvi": (0.16, 0.26), "water": (0.5, 1.0)},
        "03": {"rain": (5, 20), "ndvi": (0.15, 0.24), "water": (0.4, 0.9)},
        "04": {"rain": (10, 35), "ndvi": (0.16, 0.25), "water": (0.4, 0.9)},
        "05": {"rain": (25, 60), "ndvi": (0.20, 0.30), "water": (0.6, 1.3)},
        "06": {"rain": (100, 180), "ndvi": (0.32, 0.45), "water": (1.5, 2.8)},
        "07": {"rain": (150, 240), "ndvi": (0.42, 0.56), "water": (2.2, 3.8)},
        "08": {"rain": (130, 210), "ndvi": (0.44, 0.58), "water": (2.4, 4.0)},
        "09": {"rain": (100, 170), "ndvi": (0.40, 0.54), "water": (2.0, 3.4)},
        "10": {"rain": (60, 120), "ndvi": (0.32, 0.46), "water": (1.4, 2.5)},
        "11": {"rain": (15, 40), "ndvi": (0.24, 0.36), "water": (0.9, 1.8)},
        "12": {"rain": (3, 15), "ndvi": (0.19, 0.29), "water": (0.6, 1.3)},
    },
    "gangetic_plain": {
        "01": {"rain": (10, 30), "ndvi": (0.28, 0.40), "water": (2.0, 3.5)},
        "02": {"rain": (8, 25), "ndvi": (0.30, 0.42), "water": (1.8, 3.2)},
        "03": {"rain": (5, 20), "ndvi": (0.26, 0.38), "water": (1.5, 2.8)},
        "04": {"rain": (5, 20), "ndvi": (0.20, 0.30), "water": (1.2, 2.3)},
        "05": {"rain": (15, 40), "ndvi": (0.16, 0.26), "water": (1.0, 2.0)},
        "06": {"rain": (60, 130), "ndvi": (0.22, 0.34), "water": (1.5, 2.8)},
        "07": {"rain": (200, 300), "ndvi": (0.40, 0.54), "water": (3.0, 5.0)},
        "08": {"rain": (220, 320), "ndvi": (0.44, 0.58), "water": (3.5, 5.5)},
        "09": {"rain": (140, 230), "ndvi": (0.40, 0.54), "water": (3.0, 4.8)},
        "10": {"rain": (30, 70), "ndvi": (0.32, 0.44), "water": (2.2, 3.8)},
        "11": {"rain": (5, 20), "ndvi": (0.28, 0.40), "water": (2.0, 3.4)},
        "12": {"rain": (5, 20), "ndvi": (0.26, 0.38), "water": (2.0, 3.4)},
    },
    "kerala_coast": {
        "01": {"rain": (10, 30), "ndvi": (0.55, 0.68), "water": (4.0, 6.0)},
        "02": {"rain": (15, 35), "ndvi": (0.54, 0.66), "water": (3.8, 5.8)},
        "03": {"rain": (30, 60), "ndvi": (0.54, 0.66), "water": (3.8, 5.8)},
        "04": {"rain": (80, 140), "ndvi": (0.56, 0.68), "water": (4.2, 6.2)},
        "05": {"rain": (180, 260), "ndvi": (0.58, 0.70), "water": (5.0, 7.5)},
        "06": {"rain": (500, 650), "ndvi": (0.62, 0.74), "water": (7.0, 10.5)},
        "07": {"rain": (400, 560), "ndvi": (0.62, 0.74), "water": (7.5, 11.0)},
        "08": {"rain": (280, 400), "ndvi": (0.60, 0.72), "water": (6.5, 9.5)},
        "09": {"rain": (200, 320), "ndvi": (0.58, 0.70), "water": (5.8, 8.5)},
        "10": {"rain": (250, 380), "ndvi": (0.58, 0.70), "water": (6.0, 9.0)},
        "11": {"rain": (140, 240), "ndvi": (0.56, 0.68), "water": (5.2, 7.8)},
        "12": {"rain": (30, 70), "ndvi": (0.55, 0.67), "water": (4.4, 6.5)},
    },
}

_DEFAULT_PROFILE = {"rain": (50, 150), "ndvi": (0.35, 0.50), "water": (2.0, 4.0)}


def _seeded_rng(district_key: str, month: str) -> random.Random:
    digest = hashlib.sha256(f"{district_key}:{month}".encode("utf-8")).hexdigest()
    return random.Random(int(digest[:12], 16))


def synthetic_indicators(district_key: str, month: str, climate: str = "") -> dict:
    """Returns {'average_ndvi', 'rainfall_mm', 'water_coverage_percent'}."""
    month_num = month.split("-")[1] if "-" in month else "06"
    zone = CLIMATE_PROFILES.get(climate, {})
    profile = zone.get(month_num, _DEFAULT_PROFILE)
    rng = _seeded_rng(district_key, month)

    return {
        "average_ndvi": round(rng.uniform(*profile["ndvi"]), 2),
        "rainfall_mm": round(rng.uniform(*profile["rain"])),
        "water_coverage_percent": round(rng.uniform(*profile["water"]), 1),
    }
