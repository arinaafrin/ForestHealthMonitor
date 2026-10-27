import numpy as np
import pytest
from src.mining.sampling import (Site, assign_splits, block_id_for, check_no_block_leak, finalize_sites)


def _sites(n: int, seed: int = 0) -> list[Site]:
    rng = np.random.default_rng(seed)
    return [Site(f"p{i}", float(rng.uniform(-60, 60)), float(rng.uniform(-40, 40)), "XXX", False)
            for i in range(n)]

def test_block_id_handles_negative_coordinates():
    assert block_id_for(0.5, 0.5, 1.0) == "0_0"
    assert block_id_for(-0.5, -0.5, 1.0) == "-1_-1"
    assert block_id_for(10.99, 20.01, 1.0) == "10_20"

def test_splits_are_deterministic_and_cover_all_three():
    blocks = [f"b{i}" for i in range(20)]
    a = assign_splits(blocks, 0.15, 0.15, seed=7)
    b = assign_splits(blocks, 0.15, 0.15, seed=7)
    assert a == b
    assert set(a.values()) == {"train", "val", "test"}
    assert list(a.values()).count("train") > list(a.values()).count("test")

def test_different_seed_changes_the_split():
    blocks = [f"b{i}" for i in range(30)]
    assert assign_splits(blocks, 0.2, 0.2, 1) != assign_splits(blocks, 0.2, 0.2, 2)

def test_too_few_blocks_is_an_error():
    with pytest.raises(ValueError, match="at least 3"):
        assign_splits(["a", "b"], 0.15, 0.15, 0)

def test_bad_fractions_are_an_error():
    with pytest.raises(ValueError):
        assign_splits(["a", "b", "c", "d"], 0.6, 0.5, 0)

@pytest.mark.parametrize("seed", range(5))
def test_no_block_is_ever_shared_between_splits(seed):
    final = finalize_sites(_sites(200, seed), block_deg=2.0, val_fraction=0.15, test_fraction=0.15, seed=seed)
    check_no_block_leak(final)            # must not raise
    by_block = {}
    for s in final:
        by_block.setdefault(s.block_id, set()).add(s.split)
    assert all(len(v) == 1 for v in by_block.values())

def test_leak_check_catches_a_real_leak():
    leaky = [Site("a", 0, 0, "X", False, block_id="b1", split="train"), Site("b", 0, 0, "X", False, block_id="b1", split="test")]
    with pytest.raises(AssertionError, match="leakage"):
        check_no_block_leak(leaky)

def test_pick_positive_sites_spreads_over_countries():
    gpd = pytest.importorskip("geopandas")
    from shapely.geometry import Point
    rows = [("AAA", 1.0, Point(i, 0).buffer(0.01)) for i in range(30)] + [("BBB", 1.0, Point(i, 5).buffer(0.01)) for i in range(5)]
    gdf = gpd.GeoDataFrame({"ISO3_CODE": [r[0] for r in rows], "AREA": [r[1] for r in rows]}, geometry=[r[2] for r in rows], crs=4326)
    from src.mining.sampling import pick_positive_sites
    sites = pick_positive_sites(gdf, 8, 0.05, 50.0, seed=0)
    countries = [s.iso3 for s in sites]
    assert len(sites) == 8
    assert countries.count("BBB") >= 3       
    assert len({s.patch_id for s in sites}) == 8

def test_pick_positive_sites_respects_area_limits():
    gpd = pytest.importorskip("geopandas")
    from shapely.geometry import Point
    gdf = gpd.GeoDataFrame({"ISO3_CODE": ["A", "A"], "AREA": [0.001, 500.0]}, geometry=[Point(0, 0).buffer(0.01), Point(1, 1).buffer(0.01)], crs=4326)
    from src.mining.sampling import pick_positive_sites
    with pytest.raises(ValueError, match="area limits"):
        pick_positive_sites(gdf, 1, 0.05, 50.0, 0)