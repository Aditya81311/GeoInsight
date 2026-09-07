# GeoInsight Backend

FastAPI backend for the GeoInsight hackathon problem statement (Kamrup
District, Assam). Matches the API contract your frontend already expects
(`API_BASE_URL = "http://localhost:8000"`, endpoint
`/api/v1/environment?district=kamrup&month=2026-06`) — no frontend changes
needed.

## What's inside

```
backend/
  app/
    main.py              FastAPI app + CORS
    config.py             settings (pydantic-settings, fixes the BaseSettings error)
    districts.py          district registry (Kamrup) + boundary geometry
    schemas.py             response models
    service.py             combines real + synthetic data per request
    insight.py              optional AI insight (OpenRouter, with template fallback)
    engine/
      geoprocessing.py    real rasterio/geopandas pipeline (used once you add real data)
      seasonal.py         seasonal synthetic fallback (used until then)
    routers/
      environment.py      all API routes
  data/                    put real datasets here later (see data/README.md)
  requirements.txt
  .env.example
```

There's no database — this problem is compute-on-request, not something you
need to persist, so the old `models.py` / `crud.py` / `database.py` from your
earlier scaffold are gone.

## Setup

Replace your current `backend/` folder with this one (or copy `app/`,
`data/`, `requirements.txt` in), then, from inside `backend/`:

```bash
# activate your existing venv first
pip install -r requirements.txt
```

If `geopandas` / `rasterio` fail to install (common on Windows without
GDAL), comment those four lines out in `requirements.txt` and reinstall —
the API still runs fully, just always using the synthetic fallback until you
sort out those wheels (e.g. via conda, which handles GDAL better than pip
on Windows).

## Run

```bash
uvicorn app.main:app --reload --port 8000
```

Then start your frontend as usual (`npm run dev`, Vite default port 5173).
The header badge should flip from "Demo Mode" to "API Online" once you hit
"Analyze District".

Interactive API docs: http://localhost:8000/docs

## Endpoints

- `GET /api/v1/environment?district=kamrup&month=2026-06` — the one the
  frontend calls. Returns NDVI, rainfall, and surface-water stats.
- `GET /api/v1/districts` — supported districts.
- `GET /api/v1/boundary?district=kamrup` — district polygon as GeoJSON, if
  you want to wire the map up to real boundary data instead of the
  hardcoded `kamrupDemoBoundary` in App.jsx.
- `GET /api/v1/insight?district=kamrup&month=2026-06` — optional
  enhancement #1: AI-generated (or template) environmental summary.
- `GET /api/v1/compare?district=kamrup&month_a=2025-06&month_b=2026-06` —
  optional enhancement #2: historical comparison between two months.

Valid months for the demo dropdown: `2026-06`, `2026-05`, `2026-04`,
`2025-06` (any `YYYY-MM` actually works — those four are just what's in the
frontend's `<select>`).

## About the numbers right now

No real Sentinel-2 / CHIRPS / JRC datasets exist locally yet, so every
number currently comes from a deterministic, seasonally-realistic synthetic
model (`app/engine/seasonal.py`) — not measured data. Every response says so
explicitly via `"meta": {"data_source": "synthetic"}`.

The full real pipeline (`app/engine/geoprocessing.py`) is already wired up
and does real zonal statistics with `rasterio` + `rasterstats` — it's just
waiting for actual files. Drop them into `data/` per `data/README.md` and
real numbers take over automatically, per-indicator, no code changes.

## Optional: AI insight

Set `OPENROUTER_API_KEY` in a `.env` file (copy `.env.example`) to make
`/api/v1/insight` use OpenRouter instead of the rule-based template. Not
required — the frontend doesn't currently call this endpoint at all (its
insight card is generated client-side from the numbers), but it satisfies
the "AI-Generated Environmental Insight" optional enhancement in the
problem statement if you want to wire it into the UI for extra points.
