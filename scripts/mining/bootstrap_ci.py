from __future__ import annotations
import csv
import sys
from pathlib import Path
import numpy as np

def load_counts(data_dir: Path, run_dir: Path, manifest: dict) -> dict[str, tuple[float, float, float, float, str]]:
    """Per patch: (tp, fp, fn, pixels, block) rebuilt from IoU, pred% and label%."""
    any_file = next(iter(manifest.values()))["file"]
    pixels = float(np.load(data_dir / any_file)["mask"].size)
    out = {}
    for r in csv.DictReader(open(run_dir / "test_per_patch.csv")):
        iou, p, m = float(r["iou"]), float(r["pred_fraction"]) * pixels, float(r["mask_fraction"]) * pixels
        tp = iou * (p + m) / (1.0 + iou)      
        out[r["patch_id"]] = (tp, p - tp, m - tp, pixels, manifest[r["patch_id"]]["block_id"])
    return out

def pooled_iou(tp: float, fp: float, fn: float) -> float:
    return tp / max(tp + fp + fn, 1e-9)

def main(data_dir: str, run_dirs: list[str]) -> None:
    data = Path(data_dir)
    manifest = {r["patch_id"]: r for r in csv.DictReader(open(data / "manifest.csv"))}
    runs = [load_counts(data, Path(r), manifest) for r in run_dirs]
    ids = sorted(runs[0])
    table = np.array([[np.mean([run[i][k] for run in runs]) for k in range(4)] for i in ids])
    blocks = np.array([runs[0][i][4] for i in ids])
    tp, fp, fn, px = table.T

    point = pooled_iou(tp.sum(), fp.sum(), fn.sum())
    baseline = (tp + fn).sum() / px.sum()           # IoU of "everything is mine"
    print(f"Test patches: {len(ids)} in {len(set(blocks))} spatial blocks")
    for name, run in zip(run_dirs, runs):
        a = np.array([run[i][:3] for i in ids]).sum(0)
        print(f"  {name}: pooled test IoU {pooled_iou(*a):.3f}")
    print(f"Mean over runs: {point:.3f}")
    print(f"All-mine baseline on this test set: {baseline:.3f}")

    rng = np.random.default_rng(0)
    uniq = np.unique(blocks)
    index = {b: np.flatnonzero(blocks == b) for b in uniq}
    boots = []
    for _ in range(2000):
        pick = rng.choice(uniq, size=len(uniq), replace=True)
        rows = np.concatenate([index[b] for b in pick])
        boots.append(pooled_iou(tp[rows].sum(), fp[rows].sum(), fn[rows].sum()))
    lo, hi = np.percentile(boots, [2.5, 97.5])
    print(f"95% interval (resampling blocks, 2000 times): {lo:.3f} to {hi:.3f}")
    print("Note: the trained models and the split are fixed; this covers test-sample uncertainty only.")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        raise SystemExit(__doc__)
    main(sys.argv[1], sys.argv[2:])