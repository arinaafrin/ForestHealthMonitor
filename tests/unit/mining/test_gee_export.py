import io
from unittest.mock import MagicMock
import numpy as np
import pytest
pytest.importorskip("pyproj")
from src.mining.config import S2_BANDS
from src.mining.gee_export import fetch_patch, structured_to_array, to_reflectance, valid_fraction
from src.mining.geo import grid_around

def _structured(h=8, w=8, order=S2_BANDS, offset=0):
    dtype = [(b, "<f4") for b in order]
    arr = np.zeros((h, w), dtype=dtype)
    for b in order:
        arr[b] = (S2_BANDS.index(b) + 1) * 1000 + offset   
    return arr

def test_bands_come_out_in_our_order_even_if_earth_engine_shuffles_them():
    shuffled = tuple(reversed(S2_BANDS))
    out = structured_to_array(_structured(order=shuffled))
    assert out.shape == (6, 8, 8)
    assert out[0, 0, 0] == 1000 and out[5, 0, 0] == 6000   

def test_missing_band_is_reported():
    with pytest.raises(ValueError, match="B12"):
        structured_to_array(_structured(order=S2_BANDS[:-1]))

def test_reflectance_is_scaled_clipped_and_nan_safe():
    dn = np.array([[[0.0, 5000.0, 20000.0, np.nan]]], dtype=np.float32)
    out = to_reflectance(dn)
    assert out.tolist() == [[[0.0, 0.5, 1.0, 0.0]]]

def test_valid_fraction_counts_pixels_with_all_bands():
    dn = np.ones((6, 4, 4), dtype=np.float32)
    dn[2, :2, :] = np.nan
    assert valid_fraction(dn) == pytest.approx(0.5)

def test_fetch_patch_builds_an_exact_grid_request_and_decodes_the_reply():
    grid = grid_around(24.95, 60.17, 8, 10.0)
    buffer = io.BytesIO(); np.save(buffer, _structured(8, 8))
    ee = MagicMock()
    ee.data.computePixels.return_value = buffer.getvalue()
    out = fetch_patch(ee, 24.95, 60.17, grid, year=2019, max_cloud_percent=40)
    assert out.shape == (6, 8, 8)
    request = ee.data.computePixels.call_args[0][0]
    assert request["fileFormat"] == "NPY"
    assert request["grid"]["crsCode"] == f"EPSG:{grid.epsg}"
    assert request["grid"]["dimensions"] == {"width": 8, "height": 8}
    assert request["grid"]["affineTransform"]["scaleY"] == -10.0
    assert request["grid"]["affineTransform"]["translateX"] == grid.x_min

def test_wrong_shape_from_earth_engine_is_rejected():
    grid = grid_around(24.95, 60.17, 8, 10.0)
    buffer = io.BytesIO(); np.save(buffer, _structured(4, 4))
    ee = MagicMock(); ee.data.computePixels.return_value = buffer.getvalue()
    with pytest.raises(ValueError, match="Unexpected patch shape"):
        fetch_patch(ee, 24.95, 60.17, grid, 2019, 40)