from __future__ import annotations
from dataclasses import dataclass
import numpy as np
from pyproj import Transformer


def utm_epsg(lon: float, lat: float) -> int:
    zone = int((lon + 180.0) // 6.0) + 1
    zone = min(max(zone, 1), 60)
    return (32600 if lat >= 0 else 32700) + zone


@dataclass(frozen=True)
class PixelGrid:
    epsg: int
    x_min: float      
    y_max: float      
    size_px: int
    pixel_m: float

    @property
    def shape(self) -> tuple[int, int]:
        return (self.size_px, self.size_px)

    @property
    def bounds(self) -> tuple[float, float, float, float]:
        """(x_min, y_min, x_max, y_max) in metres."""
        extent = self.size_px * self.pixel_m
        return (self.x_min, self.y_max - extent, self.x_min + extent, self.y_max)

    def pixel_centres(self) -> tuple[np.ndarray, np.ndarray]:
        """x and y coordinates (metres) of every pixel centre, shape (H, W)."""
        cols = self.x_min + (np.arange(self.size_px) + 0.5) * self.pixel_m
        rows = self.y_max - (np.arange(self.size_px) + 0.5) * self.pixel_m
        return np.meshgrid(cols, rows)


def grid_around(lon: float, lat: float, size_px: int, pixel_m: float) -> PixelGrid:
    epsg = utm_epsg(lon, lat)
    to_utm = Transformer.from_crs(4326, epsg, always_xy=True)
    x, y = to_utm.transform(lon, lat)
    half = size_px * pixel_m / 2.0
    x_min = np.floor((x - half) / pixel_m) * pixel_m
    y_max = np.ceil((y + half) / pixel_m) * pixel_m
    return PixelGrid(epsg=epsg, x_min=float(x_min), y_max=float(y_max), size_px=size_px, pixel_m=pixel_m)


def lonlat_box(grid: PixelGrid):
    from shapely.geometry import box

    to_lonlat = Transformer.from_crs(grid.epsg, 4326, always_xy=True)
    x0, y0, x1, y1 = grid.bounds
    corners = [to_lonlat.transform(x, y) for x, y in ((x0, y0), (x0, y1), (x1, y0), (x1, y1))]
    lons, lats = zip(*corners)
    return box(min(lons), min(lats), max(lons), max(lats))