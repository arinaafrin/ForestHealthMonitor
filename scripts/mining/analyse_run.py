from __future__ import annotations
import csv
import json
import statistics
import sys
from pathlib import Path


def main(run_dir: str, data_dir: str) -> None:
    run, data = Path(run_dir), Path(data_dir)
    manifest = {r["patch_id"]: r for r in csv.DictReader(open(data / "manifest.csv"))}
    rows = list(csv.DictReader(open(run / "test_per_patch.csv")))
    for r in rows:
        m = manifest[r["patch_id"]]
        r.update(iso3=m["iso3"], is_negative=m["is_negative"] == "1", iou=float(r["iou"]), pred=float(r["pred_fraction"]), mask=float(r["mask_fraction"]))

    pos = [r for r in rows if not r["is_negative"]]
    neg = [r for r in rows if r["is_negative"]]
    metrics = json.load(open(run / "metrics.json"))
    print(f"Test patches: {len(rows)} ({len(pos)} with a mapped mine, {len(neg)} 'negative')")
    print(f"Pooled test IoU: {metrics['test']['iou']:.3f}  "
          f"(precision {metrics['test']['precision']:.3f}, recall {metrics['test']['recall']:.3f})")
    print(f"All-mine baseline IoU on test: about {statistics.mean(r['mask'] for r in rows):.3f}")
    if pos:
        ious = sorted(r["iou"] for r in pos)
        print(f"Per-patch IoU, mapped-mine patches: median {statistics.median(ious):.3f}, "
              f"min {ious[0]:.3f}, max {ious[-1]:.3f}")
        missed = [r for r in pos if r["pred"] < 0.2 * r["mask"]]
        print(f"Mapped mines almost missed (predicted area < 20% of label): {len(missed)} of {len(pos)}")
    if neg:
        fp = [r for r in neg if r["pred"] > 0.01]
        print(f"'Negative' patches where >1% of pixels are marked mine: {len(fp)} of {len(neg)}  "
              "(check these by eye: unmapped mine, or a real false alarm?)")

    print("\nWorst 8 patches (for 'negative' patches IoU is 0 if even one pixel is marked):")
    print(f"{'patch':<11}{'country':<8}{'type':<9}{'label%':>8}{'pred%':>8}{'IoU':>7}")
    for r in sorted(rows, key=lambda r: r["iou"])[:8]:
        kind = "negative" if r["is_negative"] else "mine"
        print(f"{r['patch_id']:<11}{r['iso3']:<8}{kind:<9}{r['mask']*100:>8.1f}{r['pred']*100:>8.1f}{r['iou']:>7.3f}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    main(sys.argv[1], sys.argv[2])