from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import csv
import sys
from pathlib import Path
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from src.mining.metrics import Confusion
BANDS = ["B2", "B3", "B4", "B8", "B11", "B12"]


def features(image: np.ndarray) -> np.ndarray:
    """(C, H, W) reflectance -> (H*W, F): 6 bands + two simple indices."""
    x = image.astype(np.float32)
    b4, b8, b11, b12 = x[2], x[3], x[4], x[5]
    ndvi = (b8 - b4) / (b8 + b4 + 1e-6)
    nbr = (b8 - b12) / (b8 + b12 + 1e-6)
    stack = np.concatenate([x, ndvi[None], nbr[None]], axis=0)
    return stack.reshape(stack.shape[0], -1).T

def load_split(data: Path, rows: list[dict]):
    xs, ys = [], []
    for r in rows:
        z = np.load(data / r["file"])
        xs.append(features(z["image"])); ys.append(z["mask"].reshape(-1))
    return xs, ys

def main(data_dir: str, max_train_pixels: int = 400_000) -> None:
    data = Path(data_dir)
    rows = list(csv.DictReader(open(data / "manifest.csv")))
    by = {s: [r for r in rows if r["split"] == s] for s in ("train", "val", "test")}
    rng = np.random.default_rng(0)

    xtr, ytr = load_split(data, by["train"])
    X, y = np.concatenate(xtr), np.concatenate(ytr)
    keep = rng.choice(len(y), size=min(max_train_pixels, len(y)), replace=False)
    print(f"Training the forest on {len(keep):,} pixels from {len(by['train'])} patches ...")
    rf = RandomForestClassifier(n_estimators=100, max_depth=12, min_samples_leaf=5,
                                class_weight="balanced_subsample", n_jobs=-1, random_state=0)
    rf.fit(X[keep], y[keep])

    def probs(split):
        xs, ys = load_split(data, by[split])
        return np.concatenate([rf.predict_proba(x)[:, 1] for x in xs]), np.concatenate(ys)

    pv, yv = probs("val"); pt, yt = probs("test")

    def scores(p, y, t):
        c = Confusion(); c.update((p >= t).astype(np.uint8), y); return c.scores()

    grid = np.round(np.arange(0.1, 0.91, 0.05), 2)
    best = max(grid, key=lambda t: scores(pv, yv, t)["iou"])
    s05, sb = scores(pt, yt, 0.5), scores(pt, yt, best)
    print(f"Random Forest TEST IoU at 0.50: {s05['iou']:.3f} (precision {s05['precision']:.3f}, recall {s05['recall']:.3f})")
    print(f"Random Forest TEST IoU at val-best threshold {best:.2f}: {sb['iou']:.3f} "
          f"(precision {sb['precision']:.3f}, recall {sb['recall']:.3f})")
    print(f"All-mine baseline on test: {yt.mean():.3f}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    main(sys.argv[1])