from __future__ import annotations
import json
from pathlib import Path
import numpy as np
from src.mining.build_dataset import MANIFEST_FIELDS, write_manifest, write_patch
from src.mining.sampling import Site

def make_synthetic_patch(rng: np.random.Generator, size: int = 64, with_mine: bool = True, bands: int = 6) -> tuple[np.ndarray, np.ndarray]:
    base = rng.uniform(0.05, 0.15, size=(bands, 1, 1))
    image = base + rng.normal(0, 0.02, size=(bands, size, size))
    mask = np.zeros((size, size), dtype=np.uint8)
    if with_mine:
        cy, cx = rng.integers(size // 4, 3 * size // 4, size=2)
        ry, rx = rng.integers(size // 8, size // 3, size=2)
        yy, xx = np.mgrid[:size, :size]
        mask = (((yy - cy) / ry) ** 2 + ((xx - cx) / rx) ** 2 <= 1.0).astype(np.uint8)
        signature = rng.uniform(0.15, 0.30, size=(bands, 1, 1))
        image = np.where(mask[None] == 1, signature + rng.normal(0, 0.02, image.shape), image)
    return np.clip(image, 0, 1).astype(np.float32), mask

def make_synthetic_dataset(out_dir: str | Path, per_split: dict[str, int] | None = None, size: int = 64, seed: int = 0) -> Path:
    per_split = per_split or {"train": 24, "val": 8, "test": 8}
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(seed)
    rows, counter = [], 0
    for split, n in per_split.items():
        for j in range(n):
            has_mine = bool(rng.random() < 0.8)
            image, mask = make_synthetic_patch(rng, size, has_mine)
            site = Site(patch_id=f"syn_{counter:05d}", lon=float(counter), lat=0.0, iso3="SYN",
                        is_negative=not has_mine, block_id=f"{split}_block_{j % 3}", split=split)
            rows.append(write_patch(out, site, image, mask, valid=1.0))
            counter += 1
    write_manifest(out, rows)
    (out / "summary.json").write_text(json.dumps({"SYNTHETIC": True, "patches": len(rows)}, indent=2))
    return out / "manifest.csv"