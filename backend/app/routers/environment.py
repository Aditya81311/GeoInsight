import re

from fastapi import APIRouter, HTTPException, Query

from app.districts import DISTRICTS, boundary_to_geojson, get_district
from app.insight import generate_insight
from app.schemas import CompareResponse, EnvironmentResponse, InsightResponse
from app.service import get_environment

router = APIRouter(prefix="/api/v1", tags=["environment"])

MONTH_PATTERN = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")


def _validate(district: str, month: str) -> str:
    district_key = district.strip().lower()
    if get_district(district_key) is None:
        supported = ", ".join(DISTRICTS.keys())
        raise HTTPException(
            status_code=404,
            detail=f"Unknown district '{district}'. Supported districts: {supported}",
        )
    if not MONTH_PATTERN.match(month):
        raise HTTPException(status_code=400, detail="month must be in YYYY-MM format, e.g. 2026-06")
    return district_key


@router.get("/districts")
def list_districts():
    """Districts the API currently supports (just Kamrup, per the problem statement)."""
    return [
        {
            "key": key,
            "name": d["name"],
            "state": d["state"],
            "centroid": d["centroid"],
            "area_km2": d["area_km2"],
        }
        for key, d in DISTRICTS.items()
    ]


@router.get("/environment", response_model=EnvironmentResponse)
def environment(
    district: str = Query(..., description="District key, e.g. 'kamrup'"),
    month: str = Query(..., description="Month as YYYY-MM, e.g. '2026-06'"),
):
    """Core endpoint the frontend calls: NDVI, rainfall and surface-water stats."""
    district_key = _validate(district, month)
    return get_environment(district_key, month)


@router.get("/boundary")
def boundary(district: str = Query(..., description="District key, e.g. 'kamrup'")):
    """District boundary as a GeoJSON Feature, for map layers."""
    district_key = district.strip().lower()
    geojson = boundary_to_geojson(district_key)
    if geojson is None:
        raise HTTPException(status_code=404, detail=f"Unknown district '{district}'")
    return geojson


@router.get("/insight", response_model=InsightResponse)
def insight(
    district: str = Query(...),
    month: str = Query(...),
):
    """Optional enhancement: AI-generated, data-grounded environmental summary."""
    district_key = _validate(district, month)
    payload = get_environment(district_key, month)
    return {
        "district": payload["district"],
        "month": month,
        "insight": generate_insight(payload),
    }


@router.get("/compare", response_model=CompareResponse)
def compare(
    district: str = Query(...),
    month_a: str = Query(..., description="Earlier month, YYYY-MM"),
    month_b: str = Query(..., description="Later month, YYYY-MM"),
):
    """Optional enhancement: historical comparison between two months."""
    district_key = _validate(district, month_a)
    _validate(district, month_b)

    data_a = get_environment(district_key, month_a)
    data_b = get_environment(district_key, month_b)

    def pct_change(new_value: float, old_value: float):
        if not old_value:
            return None
        return round((new_value - old_value) / old_value * 100, 1)

    return {
        "district": data_a["district"],
        "period_a": month_a,
        "period_b": month_b,
        "changes": {
            "ndvi_percent_change": pct_change(
                data_b["vegetation"]["average_ndvi"], data_a["vegetation"]["average_ndvi"]
            ),
            "rainfall_percent_change": pct_change(
                data_b["rainfall"]["value_mm"], data_a["rainfall"]["value_mm"]
            ),
            "water_coverage_percent_change": pct_change(
                data_b["surface_water"]["coverage_percent"],
                data_a["surface_water"]["coverage_percent"],
            ),
        },
        "period_a_data": data_a,
        "period_b_data": data_b,
    }
