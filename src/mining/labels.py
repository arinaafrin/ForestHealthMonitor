from __future__ import annotations
from collections.abc import Sequence
from pathlib import Path
import numpy as np
import shapely
from pyproj import Transformer
from shapely.geometry import box
from shapely.geometry.base import BaseGeometry
from src.mining.geo import PixelGrid

def load_polygons(path: str | Path):
    import geopandas as gpd 

    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(
            f"Polygon file not found: {p}. Download it from the PANGAEA record "
            "(doi 10.1594/PANGAEA.942325) and put it at this path."
        )
    gdf = gpd.read_file(p)
    if gdf.crs is None:
        raise ValueError("Polygon file has no CRS; expected WGS84 (EPSG:4326).")
    gdf = gdf.to_crs(4326)
    gdf = gdf[gdf.geometry.notna() & ~gdf.geometry.is_empty].copy()
    gdf["geometry"] = shapely.make_valid(gdf.geometry.values)
    gdf = gdf[gdf.geometry.geom_type.isin(["Polygon", "MultiPolygon"])].copy()
    return gdf.reset_index(drop=True)


def polygons_to_mask(polygons_lonlat: Sequence[BaseGeometry], grid: PixelGrid) -> np.ndarray:
    mask = np.zeros(grid.shape, dtype=np.uint8)
    if len(polygons_lonlat) == 0:
        return mask

    to_utm = Transformer.from_crs(4326, grid.epsg, always_xy=True).transform
    patch_box = box(*grid.bounds)
    xs, ys = grid.pixel_centres()

    for geom in polygons_lonlat:
        projected = shapely.transform(geom, lambda c: np.column_stack(to_utm(c[:, 0], c[:, 1])))
        if not projected.intersects(patch_box):
            continue
        inside = shapely.contains_xy(projected, xs, ys)
        mask |= inside.astype(np.uint8)
    return mask