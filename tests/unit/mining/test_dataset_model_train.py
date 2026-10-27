import json
import numpy as np
import pytest
torch = pytest.importorskip("torch")
from torch.utils.data import DataLoader
from src.mining.config import TrainConfig
from src.mining.dataset import PatchDataset, compute_channel_stats, read_manifest
from src.mining.losses import combined_loss, soft_dice_loss
from src.mining.model import UNet, count_parameters


def test_manifest_has_all_three_splits_and_no_block_in_two_splits(synthetic_dir):
    rows = read_manifest(synthetic_dir)
    assert {r["split"] for r in rows} == {"train", "val", "test"}
    blocks = {}
    for r in rows:
        blocks.setdefault(r["block_id"], set()).add(r["split"])
    assert all(len(v) == 1 for v in blocks.values())

def test_stats_come_from_train_only(synthetic_dir):
    rows = read_manifest(synthetic_dir)
    stats_train = compute_channel_stats(synthetic_dir, rows)
    only_val_test = [r for r in rows if r["split"] != "train"]
    with pytest.raises(ValueError, match="No training"):
        compute_channel_stats(synthetic_dir, only_val_test)
    assert len(stats_train["mean"]) == 6 and all(s > 0 for s in stats_train["std"])

def test_item_shapes_and_normalisation(synthetic_dir):
    rows = read_manifest(synthetic_dir)
    stats = compute_channel_stats(synthetic_dir, rows)
    ds = PatchDataset(synthetic_dir, "val", stats)
    item = ds[0]
    assert item["image"].shape == (6, 32, 32) and item["image"].dtype == torch.float32
    assert item["mask"].shape == (1, 32, 32)
    assert set(item["mask"].unique().tolist()) <= {0.0, 1.0}

def test_augmentation_keeps_image_and_mask_aligned(tmp_path):
    from src.mining.build_dataset import write_manifest, write_patch
    from src.mining.sampling import Site
    rng = np.random.default_rng(0)
    rows = []
    for i in range(3):
        mask = (rng.random((16, 16)) > 0.5).astype(np.uint8)
        image = np.stack([mask.astype(np.float32)] * 6)
        site = Site(f"a{i}", 0, 0, "X", False, block_id=f"b{i}", split="train")
        rows.append(write_patch(tmp_path, site, image, mask, 1.0))
    write_manifest(tmp_path, rows)
    stats = {"mean": [0.0] * 6, "std": [1.0] * 6}
    ds = PatchDataset(tmp_path, "train", stats, augment=True, seed=3)
    for _ in range(20):
        for i in range(len(ds)):
            item = ds[i]
            assert torch.equal(item["image"][0], item["mask"][0])


def test_val_and_test_are_never_augmented(synthetic_dir):
    stats = {"mean": [0.0] * 6, "std": [1.0] * 6}
    for split in ("val", "test"):
        ds = PatchDataset(synthetic_dir, split, stats)
        assert ds.augment is False
        assert torch.equal(ds[0]["image"], ds[0]["image"])

def test_unet_output_shape_and_gradients():
    model = UNet(in_channels=6, base=8)
    x = torch.randn(2, 6, 32, 32)
    out = model(x)
    assert out.shape == (2, 1, 32, 32)
    out.mean().backward()
    assert all(p.grad is not None for p in model.parameters())
    assert count_parameters(model) > 10_000

def test_unet_rejects_sizes_not_divisible_by_eight():
    with pytest.raises(ValueError, match="divisible by 8"):
        UNet(6, 8)(torch.randn(1, 6, 30, 30))

def test_loss_is_small_for_a_perfect_guess_and_large_for_a_wrong_one():
    target = torch.zeros(2, 1, 8, 8); target[:, :, :4] = 1
    good = (target * 2 - 1) * 12           
    bad = -good
    assert combined_loss(good, target).item() < 0.05
    assert combined_loss(bad, target).item() > 1.0
    assert 0.0 <= soft_dice_loss(good, target).item() <= 1.0

@pytest.mark.slow
def test_training_runs_end_to_end_and_writes_all_outputs(synthetic_dir, tmp_path):
    from src.mining.train import train
    cfg = TrainConfig(data_dir=str(synthetic_dir), run_dir=str(tmp_path / "run"), epochs=6, batch_size=8, base_channels=8, lr=3e-3, patience=6, seed=5)
    result = train(cfg)
    run = tmp_path / "run"
    for name in ("best.pt", "config.json", "history.csv", "metrics.json", "results.md", "test_per_patch.csv", "channel_stats.json"):
        assert (run / name).exists(), name
    assert 0.0 <= result["test"]["iou"] <= 1.0
    assert result["val"]["iou"] > 0.3          
    saved = json.loads((run / "metrics.json").read_text())
    assert saved["n_patches"] == {"train": 24, "val": 8, "test": 8}

@pytest.mark.slow
def test_same_seed_gives_same_result(synthetic_dir, tmp_path):
    from src.mining.train import train
    scores = []
    for i in range(2):
        cfg = TrainConfig(data_dir=str(synthetic_dir), run_dir=str(tmp_path / f"r{i}"), epochs=3, batch_size=8, base_channels=8, seed=11)
        scores.append(train(cfg)["val"]["iou"])
    assert scores[0] == pytest.approx(scores[1], abs=1e-6)

@pytest.mark.slow
def test_evaluate_run_reloads_the_checkpoint(synthetic_dir, tmp_path):
    from src.mining.evaluate import evaluate_run
    from src.mining.train import train
    cfg = TrainConfig(data_dir=str(synthetic_dir), run_dir=str(tmp_path / "run"), epochs=2, batch_size=8, base_channels=8, seed=2)
    result = train(cfg)
    again = evaluate_run(tmp_path / "run", synthetic_dir, "test")
    assert again["iou"] == pytest.approx(result["test"]["iou"], abs=1e-6)