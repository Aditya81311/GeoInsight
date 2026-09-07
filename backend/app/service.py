"""
Core orchestration: for a given district + month, try real raster
processing first, fall back to the seasonal synthetic estimate for
whichever indicator doesn't have real data available yet.
"""

from app.districts import get_district
from app.engine.geoprocessing import (
    compute_ndvi,
    compute_rainfall,
    compute_surface_water,
    load_boundary,
)
from app.engine.seasonal import synthetic_indicators


def get_environment(district_key: str, month: str) -> dict:
    district = get_district(district_key)
    if district is None:
        raise ValueError(f"Unknown district: {district_key}")

    boundary_gdf = load_boundary(district_key)

    real_ndvi = compute_ndvi(district_key, month, boundary_gdf)
    real_rainfall = compute_rainfall(district_key, month, boundary_gdf)
    real_water_pct = compute_surface_water(district_key, boundary_gdf)

    fallback = synthetic_indicators(district_key, month, climate=district.get("climate", ""))

    ndvi = real_ndvi if real_ndvi is not None else fallback["average_ndvi"]
    rainfall = real_rainfall if real_rainfall is not None else fallback["rainfall_mm"]
    water_pct = (
        real_water_pct if real_water_pct is not None else fallback["water_coverage_percent"]
    )

    real_count = sum(x is not None for x in (real_ndvi, real_rainfall, real_water_pct))
    if real_count == 3:
        data_source = "real"
    elif real_count == 0:
        data_source = "synthetic"
    else:
        data_source = "mixed"

    water_area_km2 = round((water_pct / 100) * district["area_km2"], 1)

    return {
        "district": district["name"],
        "state": district["state"],
        "month": month,
        "vegetation": {"average_ndvi": ndvi},
        "rainfall": {"value_mm": rainfall, "metric": "Average rainfall"},
        "surface_water": {"coverage_percent": water_pct, "area_km2": water_area_km2},
        "meta": {"data_source": data_source},
    }
