import csv
import json
from unittest.mock import MagicMock
import numpy as np
import pytest
gpd = pytest.importorskip("geopandas")
pytest.importorskip("pyogrio")
pytest.importorskip("torch")
from shapely.geometry import box
from src.mining import build_dataset as bd
from src.mining.config import DataConfig
from src.mining.sampling import Site, pick_negative_sites

def _make_gpkg(path, n=12):
    """n small mines, 10 degrees apart, in 3 countries; each 0.6 km wide."""
    rows = []
    for i in range(n):
        lon, lat = -100 + 10 * i, 5.0
        d = 0.003
        rows.append((["AAA", "BBB", "CCC"][i % 3], 0.4, box(lon - d, lat - d, lon + d, lat + d)))
    gpd.GeoDataFrame({"ISO3_CODE": [r[0] for r in rows], "AREA": [r[1] for r in rows]}, geometry=[r[2] for r in rows], crs=4326).to_file(path, driver="GPKG")

def _cfg(tmp_path, **kw):
    _make_gpkg(tmp_path / "mines.gpkg")
    base = dict(polygons_path=str(tmp_path / "mines.gpkg"), out_dir=str(tmp_path / "out"),
                patch_px=64, n_sites=10, neg_ratio=0.2, seed=3)
    base.update(kw)
    return DataConfig(**base)

@pytest.fixture()
def fake_ee(monkeypatch):
    monkeypatch.setattr(bd, "_connect_earth_engine", lambda: MagicMock())
    calls = {"n": 0}

    def fake_fetch(ee, lon, lat, grid, year, max_cloud):
        calls["n"] += 1
        return np.full((6, grid.size_px, grid.size_px), 2000.0, dtype=np.float32)

    monkeypatch.setattr(bd, "fetch_patch", fake_fetch)
    return calls

def test_export_writes_patches_manifest_and_summary(tmp_path, fake_ee):
    cfg = _cfg(tmp_path)
    manifest = bd.build_dataset(cfg)
    rows = list(csv.DictReader(open(manifest)))
    assert len(rows) == 12                                  
    assert {r["split"] for r in rows} == {"train", "val", "test"}
    summary = json.loads((tmp_path / "out" / "summary.json").read_text())
    assert summary["patches"] == 12 and summary["skipped"] == 0
    assert "10.1594/PANGAEA.942325" in summary["label_source"]

def test_positive_patches_contain_mine_pixels_and_negative_patches_do_not(tmp_path, fake_ee):
    rows = list(csv.DictReader(open(bd.build_dataset(_cfg(tmp_path)))))
    pos = [float(r["mask_fraction"]) for r in rows if r["is_negative"] == "0"]
    neg = [float(r["mask_fraction"]) for r in rows if r["is_negative"] == "1"]
    assert len(neg) == 2
    assert all(f > 0.05 for f in pos)   
    assert all(f == 0.0 for f in neg)

def test_no_spatial_block_is_shared_between_splits_in_the_export(tmp_path, fake_ee):
    rows = list(csv.DictReader(open(bd.build_dataset(_cfg(tmp_path)))))
    seen = {}
    for r in rows:
        seen.setdefault(r["block_id"], set()).add(r["split"])
    assert all(len(v) == 1 for v in seen.values())

def test_limit_exports_only_the_first_sites(tmp_path, fake_ee):
    bd.build_dataset(_cfg(tmp_path), limit=4)
    assert fake_ee["n"] == 4

def test_patches_with_too_many_cloud_gaps_are_skipped(tmp_path, monkeypatch):
    monkeypatch.setattr(bd, "_connect_earth_engine", lambda: MagicMock())

    def cloudy(ee, lon, lat, grid, year, max_cloud):
        a = np.full((6, grid.size_px, grid.size_px), 2000.0, dtype=np.float32)
        a[:, :, : grid.size_px // 2] = np.nan         
        return a

    monkeypatch.setattr(bd, "fetch_patch", cloudy)
    manifest = bd.build_dataset(_cfg(tmp_path))
    assert list(csv.DictReader(open(manifest))) == []
    assert json.loads((tmp_path / "out" / "summary.json").read_text())["skipped"] == 12

def test_a_failed_download_is_skipped_not_fatal(tmp_path, monkeypatch):
    monkeypatch.setattr(bd, "_connect_earth_engine", lambda: MagicMock())
    state = {"n": 0}

    def flaky(ee, lon, lat, grid, year, max_cloud):
        state["n"] += 1
        if state["n"] == 3:
            raise RuntimeError("quota exceeded")
        return np.full((6, grid.size_px, grid.size_px), 2000.0, dtype=np.float32)

    monkeypatch.setattr(bd, "fetch_patch", flaky)
    manifest = bd.build_dataset(_cfg(tmp_path))
    assert len(list(csv.DictReader(open(manifest)))) == 11

def test_missing_credentials_give_a_clear_message(monkeypatch):
    monkeypatch.delenv("GEE_SERVICE_ACCOUNT_EMAIL", raising=False)
    monkeypatch.delenv("GOOGLE_APPLICATION_CREDENTIALS", raising=False)
    with pytest.raises(RuntimeError, match="GEE_SERVICE_ACCOUNT_EMAIL"):
        bd._connect_earth_engine()

def test_negative_sites_stay_away_from_every_mapped_polygon():
    from shapely.geometry import Point
    gdf = gpd.GeoDataFrame({"ISO3_CODE": ["A"] * 3, "AREA": [1.0] * 3}, geometry=[Point(0, 0).buffer(0.01), Point(0.5, 0).buffer(0.01),  Point(0, 0.5).buffer(0.01)], crs=4326)
    positives = [Site("p0", 0.0, 0.0, "A", False), Site("p1", 0.5, 0.0, "A", False)]
    negs = pick_negative_sites(gdf, 10, min_distance_deg=0.15, seed=1, positives=positives)
    assert len(negs) == 10 and all(s.is_negative for s in negs)
    for s in negs:
        window = box(s.lon - 0.15, s.lat - 0.15, s.lon + 0.15, s.lat + 0.15)
        assert not gdf.geometry.intersects(window).any()