"""
Optional enhancement #1 from the problem statement: a data-grounded
environmental insight sentence.

Uses OpenRouter if OPENROUTER_API_KEY is set (matching your usual stack),
with a strict instruction to only restate the given numbers — no invented
facts. If no key is configured, or the call fails for any reason, a
rule-based template takes over so this endpoint never breaks the demo.
"""

import calendar
import logging

import requests

from app.config import settings

logger = logging.getLogger("geoinsight.insight")

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


def _month_label(month: str) -> str:
    try:
        year, month_num = month.split("-")
        return f"{calendar.month_name[int(month_num)]} {year}"
    except Exception:
        return month


def _ndvi_label(ndvi: float) -> str:
    if ndvi < 0.35:
        return "low"
    if ndvi < 0.55:
        return "moderate"
    return "healthy"


def _template_insight(payload: dict) -> str:
    district = payload["district"]
    month_label = _month_label(payload["month"])
    ndvi = payload["vegetation"]["average_ndvi"]
    rainfall = payload["rainfall"]["value_mm"]
    water_pct = payload["surface_water"]["coverage_percent"]

    return (
        f"{district} recorded {_ndvi_label(ndvi)} vegetation health in "
        f"{month_label}, with an average NDVI of {ndvi}. The district saw "
        f"{rainfall} mm of rainfall over the month, and surface water "
        f"covered {water_pct}% of its area."
    )


def _openrouter_insight(payload: dict) -> str:
    district = payload["district"]
    month_label = _month_label(payload["month"])
    ndvi = payload["vegetation"]["average_ndvi"]
    rainfall = payload["rainfall"]["value_mm"]
    water_pct = payload["surface_water"]["coverage_percent"]

    prompt = (
        "Write one concise sentence (max 40 words) summarizing these "
        "environmental indicators. Use ONLY the numbers given below — do "
        "not invent, estimate, or add any fact not listed.\n\n"
        f"District: {district}\n"
        f"Month: {month_label}\n"
        f"Average NDVI: {ndvi}\n"
        f"Average rainfall: {rainfall} mm\n"
        f"Surface water coverage: {water_pct}%"
    )

    response = requests.post(
        OPENROUTER_URL,
        headers={"Authorization": f"Bearer {settings.openrouter_api_key}"},
        json={
            "model": settings.openrouter_model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 120,
            "temperature": 0.4,
        },
        timeout=15,
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"].strip()


def generate_insight(payload: dict) -> str:
    if settings.openrouter_api_key:
        try:
            return _openrouter_insight(payload)
        except Exception:
            logger.exception("OpenRouter insight generation failed, using template fallback")

    return _template_insight(payload)
