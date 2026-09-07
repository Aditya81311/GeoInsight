"""
Real geospatial processing pipeline (Sentinel-2 NDVI, CHIRPS rainfall,
JRC surface water), clipped to a district boundary.

This module does nothing until you actually drop matching files into
`data/` (see data/README.md for exact filenames). Every function here
returns `None` when its required file is missing, and the caller
(app/service.py) falls back to the seasonal synthetic estimate in that case.
That means:

  - Today, with no datasets: the API works using synthetic fallback values.
  - Later, once you copy the hackathon-provided datasets into `data/`:
    the real computation kicks in automatically, per-district and
    per-month, with zero code changes needed anywhere else.

Expected file layout under DATA_DIR (default: "data/"):

    data/
      boundaries/
        <district>.geojson                     # district polygon, EPSG:4326
      sentinel2/
        <district>_<YYYY-MM>_ndvi.tif           # pre-computed NDVI raster
      chirps/
        <district>_<YYYY-MM>_rainfall.tif       # monthly accumulated rainfall (mm)
      surface_water/
        <district>_water_occurrence.tif         # JRC occurrence raster (0-100)

If you only have raw Sentinel-2 bands (B04/B08) instead of a precomputed
NDVI raster, compute NDVI = (NIR - RED) / (NIR + RED) once with rasterio and
save it as the expected .tif — keeps this module simple and fast.
"""

import logging
from pathlib import Path
from typing import Optional

from app.config import settings

logger = logging.getLogger("geoinsight.geoprocessing")

try:
    import geopandas as gpd
    import numpy as np
    from rasterstats import zonal_stats

    GEO_LIBS_AVAILABLE = True
except ImportError:  # pragma: no cover - environment-dependent
    GEO_LIBS_AVAILABLE = False
    logger.warning(
        "geopandas/rasterio/rasterstats not installed — real raster "
        "processing is disabled, synthetic fallback will be used for "
        "every request. Install them (see requirements.txt) to enable "
        "real dataset processing."
    )

# Water-occurrence threshold (%) above which a JRC pixel counts as "water".
WATER_OCCURRENCE_THRESHOLD = 50


def _data_path(*parts: str) -> Path:
    return Path(settings.data_dir).joinpath(*parts)


def load_boundary(district_key: str):
    """Load a district boundary as a GeoDataFrame, or None if unavailable."""
    if not GEO_LIBS_AVAILABLE:
        return None

    path = _data_path("boundaries", f"{district_key}.geojson")
    if not path.exists():
        return None

    try:
        return gpd.read_file(path)
    except Exception:
        logger.exception("Failed to read boundary file %s", path)
        return None


def compute_ndvi(district_key: str, month: str, boundary_gdf) -> Optional[float]:
    """Mean NDVI over the district for the given month, from a real raster."""
    if not GEO_LIBS_AVAILABLE or boundary_gdf is None:
        return None

    raster_path = _data_path("sentinel2", f"{district_key}_{month}_ndvi.tif")
    if not raster_path.exists():
        return None

    try:
        stats = zonal_stats(
            boundary_gdf, str(raster_path), stats=["mean"], nodata=np.nan
        )
        mean_ndvi = stats[0]["mean"]
        return round(float(mean_ndvi), 3) if mean_ndvi is not None else None
    except Exception:
        logger.exception("NDVI computation failed for %s / %s", district_key, month)
        return None


def compute_rainfall(district_key: str, month: str, boundary_gdf) -> Optional[float]:
    """Mean monthly rainfall (mm) over the district, from a real CHIRPS raster."""
    if not GEO_LIBS_AVAILABLE or boundary_gdf is None:
        return None

    raster_path = _data_path("chirps", f"{district_key}_{month}_rainfall.tif")
    if not raster_path.exists():
        return None

    try:
        stats = zonal_stats(
            boundary_gdf, str(raster_path), stats=["mean"], nodata=np.nan
        )
        mean_rainfall = stats[0]["mean"]
        return round(float(mean_rainfall), 1) if mean_rainfall is not None else None
    except Exception:
        logger.exception("Rainfall computation failed for %s / %s", district_key, month)
        return None


def compute_surface_water(district_key: str, boundary_gdf) -> Optional[float]:
    """Surface-water coverage (% of district area), from a real JRC raster.

    Uses the JRC Global Surface Water *occurrence* layer: a pixel counts as
    water if its historical occurrence exceeds WATER_OCCURRENCE_THRESHOLD.
    Coverage % = (water pixel count / total valid pixel count) * 100.
    """
    if not GEO_LIBS_AVAILABLE or boundary_gdf is None:
        return None

    raster_path = _data_path("surface_water", f"{district_key}_water_occurrence.tif")
    if not raster_path.exists():
        return None

    try:
        stats = zonal_stats(
            boundary_gdf,
            str(raster_path),
            stats=["count"],
            add_stats={
                "water_count": lambda arr: int(
                    np.sum(arr[~arr.mask] > WATER_OCCURRENCE_THRESHOLD)
                )
                if hasattr(arr, "mask")
                else int(np.sum(arr > WATER_OCCURRENCE_THRESHOLD))
            },
            nodata=np.nan,
        )
        total = stats[0]["count"]
        water = stats[0]["water_count"]
        if not total:
            return None
        return round((water / total) * 100, 1)
    except Exception:
        logger.exception("Surface water computation failed for %s", district_key)
        return None
