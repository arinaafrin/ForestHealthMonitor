import numpy as np
import pytest
pytest.importorskip("pyproj")
shapely = pytest.importorskip("shapely")
from shapely.geometry import Polygon, box
from src.mining.geo import grid_around
from src.mining.labels import polygons_to_mask

LON, LAT = 24.95, 60.17

def _square_lonlat(half_m: float):
    """A square around the grid centre, about ``half_m`` metres from the middle."""
    d_lat = half_m / 111_000.0
    d_lon = half_m / (111_000.0 * np.cos(np.radians(LAT)))
    return box(LON - d_lon, LAT - d_lat, LON + d_lon, LAT + d_lat)

def test_no_polygons_gives_empty_mask():
    grid = grid_around(LON, LAT, 64, 10.0)
    mask = polygons_to_mask([], grid)
    assert mask.shape == (64, 64) and mask.dtype == np.uint8 and mask.sum() == 0

def test_centre_square_fills_about_the_right_area():
    grid = grid_around(LON, LAT, 64, 10.0)           
    mask = polygons_to_mask([_square_lonlat(160)], grid)   
    assert int(mask.sum()) == pytest.approx(32 * 32, rel=0.12)
    assert mask[32, 32] == 1 and mask[0, 0] == 0

def test_polygon_far_away_is_ignored():
    grid = grid_around(LON, LAT, 64, 10.0)
    far = box(LON + 1, LAT + 1, LON + 1.01, LAT + 1.01)
    assert polygons_to_mask([far], grid).sum() == 0

def test_hole_stays_empty():
    grid = grid_around(LON, LAT, 64, 10.0)
    outer = _square_lonlat(250)
    hole = _square_lonlat(80)
    donut = Polygon(outer.exterior.coords, [hole.exterior.coords])
    mask = polygons_to_mask([donut], grid)
    assert mask[32, 32] == 0          
    assert mask[32, 32 - 20] == 1     

def test_two_overlapping_polygons_are_merged_not_double_counted():
    grid = grid_around(LON, LAT, 64, 10.0)
    a, b = _square_lonlat(160), _square_lonlat(120)
    both = polygons_to_mask([a, b], grid)
    assert set(np.unique(both)) <= {0, 1}
    assert int(both.sum()) == int(polygons_to_mask([a], grid).sum())

def test_load_polygons_reads_gpkg_and_repairs_bad_shapes(tmp_path):
    gpd = pytest.importorskip("geopandas")
    pytest.importorskip("pyogrio")
    from src.mining.labels import load_polygons
    bowtie = Polygon([(0, 0), (1, 1), (1, 0), (0, 1)])        
    good = box(5, 5, 6, 6)
    gdf = gpd.GeoDataFrame({"ISO3_CODE": ["AAA", "BBB"], "AREA": [1.0, 2.0]}, geometry=[bowtie, good], crs=4326)
    path = tmp_path / "mines.gpkg"
    gdf.to_file(path, driver="GPKG")
    loaded = load_polygons(path)
    assert len(loaded) == 2 and loaded.geometry.is_valid.all()
    assert loaded.crs.to_epsg() == 4326

def test_load_polygons_missing_file_gives_a_helpful_error(tmp_path):
    pytest.importorskip("geopandas")
    from src.mining.labels import load_polygons
    with pytest.raises(FileNotFoundError, match="PANGAEA"):
        load_polygons(tmp_path / "nope.gpkg")