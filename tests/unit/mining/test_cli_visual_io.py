import numpy as np
import pytest
from src.mining.build_dataset import MANIFEST_FIELDS, write_manifest, write_patch
from src.mining.sampling import Site
from src.mining.visualise import make_rgb

def test_patch_and_manifest_round_trip(tmp_path):
    site = Site("pos_00001", 10.123456789, 20.5, "CHL", False, block_id="10_20", split="train")
    image = np.random.default_rng(0).random((6, 16, 16)).astype(np.float32)
    mask = (image[0] > 0.5).astype(np.uint8)
    row = write_patch(tmp_path, site, image, mask, valid=0.97)
    write_manifest(tmp_path, [row])
    assert list(row) == MANIFEST_FIELDS
    with np.load(tmp_path / row["file"]) as z:
        assert z["image"].dtype == np.float16 and z["mask"].dtype == np.uint8
        assert np.allclose(z["image"].astype(np.float32), image, atol=2e-3)
        assert np.array_equal(z["mask"], mask)
    assert row["mask_fraction"] == pytest.approx(mask.mean(), abs=1e-6)

def test_make_rgb_returns_uint8_and_handles_flat_images():
    img = np.random.default_rng(1).random((6, 16, 16)).astype(np.float32)
    rgb = make_rgb(img)
    assert rgb.shape == (16, 16, 3) and rgb.dtype == np.uint8
    assert make_rgb(np.zeros((6, 8, 8), dtype=np.float32)).max() == 0

def test_cli_synthetic_command(tmp_path, capsys):
    pytest.importorskip("torch")
    from src.mining.cli import main
    assert main(["synthetic", "--out", str(tmp_path / "d")]) == 0
    assert (tmp_path / "d" / "manifest.csv").exists()

def test_cli_reads_defaults_from_the_config_dataclasses():
    from src.mining.cli import _add_dataclass_args, _from_args
    from src.mining.config import DataConfig
    import argparse
    p = argparse.ArgumentParser(); _add_dataclass_args(p, DataConfig)
    cfg = _from_args(DataConfig, p.parse_args(["--n-sites", "7", "--year", "2020"]))
    assert cfg.n_sites == 7 and cfg.year == 2020 and cfg.patch_px == 256