from __future__ import annotations
import csv
import json
from pathlib import Path
import numpy as np
import torch
from torch.utils.data import Dataset

def read_manifest(data_dir: str | Path) -> list[dict]:
    path = Path(data_dir) / "manifest.csv"
    if not path.exists():
        raise FileNotFoundError(f"{path} not found. Run the dataset build step first.")
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def compute_channel_stats(data_dir: str | Path, rows: list[dict]) -> dict[str, list[float]]:
    train = [r for r in rows if r["split"] == "train"]
    if not train:
        raise ValueError("No training patches in the manifest.")
    total = None
    total_sq = None
    count = 0
    for r in train:
        with np.load(Path(data_dir) / r["file"]) as z:
            x = z["image"].astype(np.float64)
        c = x.shape[0]
        flat = x.reshape(c, -1)
        total = flat.sum(1) if total is None else total + flat.sum(1)
        total_sq = (flat ** 2).sum(1) if total_sq is None else total_sq + (flat ** 2).sum(1)
        count += flat.shape[1]
    mean = total / count
    std = np.sqrt(np.maximum(total_sq / count - mean ** 2, 1e-12))
    return {"mean": mean.tolist(), "std": std.tolist()}


def load_or_make_stats(data_dir: str | Path, rows: list[dict]) -> dict[str, list[float]]:
    path = Path(data_dir) / "channel_stats.json"
    if path.exists():
        return json.loads(path.read_text())
    stats = compute_channel_stats(data_dir, rows)
    path.write_text(json.dumps(stats, indent=2))
    return stats


class PatchDataset(Dataset):

    def __init__(self, data_dir: str | Path, split: str, stats: dict[str, list[float]], augment: bool | None = None, seed: int = 0):
        self.data_dir = Path(data_dir)
        self.rows = [r for r in read_manifest(self.data_dir) if r["split"] == split]
        if not self.rows:
            raise ValueError(f"No patches for split '{split}'.")
        self.mean = np.asarray(stats["mean"], dtype=np.float32)[:, None, None]
        self.std = np.asarray(stats["std"], dtype=np.float32)[:, None, None]
        self.augment = (split == "train") if augment is None else augment
        self.rng = np.random.default_rng(seed)

    def __len__(self) -> int:
        return len(self.rows)

    def __getitem__(self, idx: int) -> dict:
        row = self.rows[idx]
        with np.load(self.data_dir / row["file"]) as z:
            image = z["image"].astype(np.float32)
            mask = z["mask"].astype(np.float32)
        image = (image - self.mean) / self.std
        if self.augment:
            image, mask = self._augment(image, mask)
        return {
            "image": torch.from_numpy(np.ascontiguousarray(image)),
            "mask": torch.from_numpy(np.ascontiguousarray(mask))[None],
            "patch_id": row["patch_id"],
        }

    def _augment(self, image: np.ndarray, mask: np.ndarray):
        k = int(self.rng.integers(4))
        image = np.rot90(image, k, axes=(1, 2))
        mask = np.rot90(mask, k, axes=(0, 1))
        if self.rng.random() < 0.5:
            image, mask = image[:, :, ::-1], mask[:, ::-1]
        return image, mask