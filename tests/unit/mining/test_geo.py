import numpy as np
import pytest
pytest.importorskip("pyproj")
from src.mining.geo import grid_around, lonlat_box, utm_epsg

def test_utm_zone_for_known_places():
    assert utm_epsg(24.95, 60.17) == 32635    
    assert utm_epsg(-70.0, -23.0) == 32719    
    assert utm_epsg(179.9, 10.0) == 32660     
    assert utm_epsg(-179.9, 10.0) == 32601

def test_grid_is_centred_and_snapped():
    grid = grid_around(24.95, 60.17, size_px=64, pixel_m=10.0)
    assert grid.shape == (64, 64)
    assert grid.x_min % 10 == 0 and grid.y_max % 10 == 0
    x0, y0, x1, y1 = grid.bounds
    assert x1 - x0 == pytest.approx(640) and y1 - y0 == pytest.approx(640)

def test_grid_box_in_lonlat_contains_the_centre_point():
    grid = grid_around(24.95, 60.17, size_px=64, pixel_m=10.0)
    assert lonlat_box(grid).contains(__import__("shapely").geometry.Point(24.95, 60.17))

def test_pixel_centres_run_left_to_right_and_top_to_bottom():
    grid = grid_around(10.0, 50.0, size_px=8, pixel_m=10.0)
    xs, ys = grid.pixel_centres()
    assert xs.shape == (8, 8)
    assert np.all(np.diff(xs[0]) == 10.0)       
    assert np.all(np.diff(ys[:, 0]) == -10.0)   