"""
Response schemas.

These match the shape already consumed by the frontend's App.jsx (see
DEMO_DATA and how `data.vegetation.average_ndvi` etc. are read), plus one
extra `meta` block so you can tell whether a given number came from a real
raster or the synthetic fallback.
"""

from pydantic import BaseModel


class VegetationData(BaseModel):
    average_ndvi: float


class RainfallData(BaseModel):
    value_mm: float
    metric: str = "Average rainfall"


class SurfaceWaterData(BaseModel):
    coverage_percent: float
    area_km2: float


class MetaData(BaseModel):
    # "real" -> every indicator came from an actual raster in data/
    # "synthetic" -> every indicator came from the seasonal fallback
    # "mixed" -> some real, some synthetic (e.g. you only added NDVI rasters)
    data_source: str


class EnvironmentResponse(BaseModel):
    district: str
    state: str
    month: str
    vegetation: VegetationData
    rainfall: RainfallData
    surface_water: SurfaceWaterData
    meta: MetaData


class InsightResponse(BaseModel):
    district: str
    month: str
    insight: str


class CompareChanges(BaseModel):
    ndvi_percent_change: float | None
    rainfall_percent_change: float | None
    water_coverage_percent_change: float | None


class CompareResponse(BaseModel):
    district: str
    period_a: str
    period_b: str
    changes: CompareChanges
    period_a_data: EnvironmentResponse
    period_b_data: EnvironmentResponse
