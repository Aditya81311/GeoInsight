# Dropping in real datasets

Right now this folder is empty, so the API uses seasonally-realistic
synthetic numbers (see `app/engine/seasonal.py`). Nothing needs to change in
the code — just add files here with these exact names and the real
computation in `app/engine/geoprocessing.py` takes over automatically,
indicator by indicator.

```
data/
  boundaries/
    kamrup.geojson                    # district polygon, EPSG:4326 (from geoBoundaries)
  sentinel2/
    kamrup_2026-06_ndvi.tif           # NDVI raster for June 2026
    kamrup_2026-05_ndvi.tif           # ...one file per month you support
  chirps/
    kamrup_2026-06_rainfall.tif       # monthly accumulated rainfall (mm)
  surface_water/
    kamrup_water_occurrence.tif       # JRC occurrence layer (0-100), not month-specific
```

Notes:

- If the organizers give you raw Sentinel-2 bands (B04 red, B08 NIR) instead
  of a ready NDVI raster, compute NDVI once yourself with rasterio:
  `NDVI = (NIR - RED) / (NIR + RED)`, then save the result as
  `kamrup_<month>_ndvi.tif` here.
- The boundary file is what everything gets clipped/masked against. Without
  it, real raster processing is skipped entirely for that district (falls
  back to synthetic), since there's nothing to clip to.
- You can add real data for just one indicator (e.g. only NDVI) — the API
  will mix real + synthetic and report `"meta": {"data_source": "mixed"}` so
  you always know what you're looking at.
