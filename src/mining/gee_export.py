from __future__ import annotations
import io
import logging
import numpy as np
from src.mining.config import S2_BANDS, S2_COLLECTION, SCL_BAD_CLASSES
from src.mining.geo import PixelGrid

log = logging.getLogger(__name__)

def structured_to_array(raw: np.ndarray, band_order: tuple[str, ...] = S2_BANDS) -> np.ndarray:
    if raw.dtype.names:
        missing = [b for b in band_order if b not in raw.dtype.names]
        if missing:
            raise ValueError(f"Bands missing from Earth Engine response: {missing}")
        stacked = np.stack([raw[b] for b in band_order], axis=0)
    else:
        stacked = np.moveaxis(raw, -1, 0) if raw.ndim == 3 else raw[None]
    return stacked.astype(np.float32)


def to_reflectance(digital_numbers: np.ndarray) -> np.ndarray:
    out = np.nan_to_num(digital_numbers, nan=0.0) / 10000.0
    return np.clip(out, 0.0, 1.0).astype(np.float32)


def valid_fraction(digital_numbers: np.ndarray) -> float:
    ok = np.isfinite(digital_numbers).all(axis=0)
    return float(ok.mean())


def _cloud_mask(image):
    scl = image.select("SCL")
    bad = None
    for cls in SCL_BAD_CLASSES:
        flag = scl.eq(cls)
        bad = flag if bad is None else bad.Or(flag)
    return image.updateMask(bad.Not())


def build_composite(ee, grid_center_lonlat: tuple[float, float], year: int, max_cloud_percent: float):
    lon, lat = grid_center_lonlat
    point = ee.Geometry.Point([lon, lat])
    collection = (
        ee.ImageCollection(S2_COLLECTION)
        .filterBounds(point)
        .filterDate(f"{year}-01-01", f"{year + 1}-01-01")
        .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", max_cloud_percent))
        .map(_cloud_mask)
    )
    return collection.select(list(S2_BANDS)).median()


def fetch_patch(ee, lon: float, lat: float, grid: PixelGrid, year: int,
                max_cloud_percent: float) -> np.ndarray:
    image = build_composite(ee, (lon, lat), year, max_cloud_percent)
    request = {
        "expression": image,
        "fileFormat": "NPY",
        "grid": {
            "dimensions": {"width": grid.size_px, "height": grid.size_px},
            "affineTransform": {
                "scaleX": grid.pixel_m, "shearX": 0, "translateX": grid.x_min,
                "shearY": 0, "scaleY": -grid.pixel_m, "translateY": grid.y_max,
            },
            "crsCode": f"EPSG:{grid.epsg}",
        },
    }
    raw_bytes = ee.data.computePixels(request)
    raw = np.load(io.BytesIO(raw_bytes), allow_pickle=False)
    array = structured_to_array(raw)
    if array.shape[1:] != grid.shape:
        raise ValueError(f"Unexpected patch shape {array.shape}, wanted (C, {grid.shape[0]}, {grid.shape[1]})")
    return array