from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import json
import sys
from pathlib import Path
import numpy as np
import torch
from torch.utils.data import DataLoader
from src.mining.dataset import PatchDataset
from src.mining.evaluate import load_model
from src.mining.metrics import Confusion
from src.mining.train import pick_device

@torch.no_grad()
def probabilities(model, ds, device):
    probs, masks = [], []
    for batch in DataLoader(ds, batch_size=8):
        probs.append(torch.sigmoid(model(batch["image"].to(device))).cpu().numpy().astype(np.float32))
        masks.append(batch["mask"].numpy().astype(np.uint8))
    return np.concatenate(probs), np.concatenate(masks)

def iou_at(prob, mask, t):
    c = Confusion(); c.update((prob >= t).astype(np.uint8), mask)
    return c.scores()

def main(run_dir: str, data_dir: str) -> None:
    run = Path(run_dir)
    stats = json.load(open(run / "channel_stats.json"))
    device = pick_device()
    model = load_model(run, device)
    pv, mv = probabilities(model, PatchDataset(data_dir, "val", stats), device)
    pt, mt = probabilities(model, PatchDataset(data_dir, "test", stats), device)
    grid = np.round(np.arange(0.10, 0.91, 0.05), 2)
    val = {float(t): iou_at(pv, mv, t) for t in grid}
    best = max(val, key=lambda t: val[t]["iou"])
    print("threshold   val IoU   val precision   val recall")
    for t in grid:
        s = val[float(t)]
        print(f"   {t:.2f}     {s['iou']:.3f}      {s['precision']:.3f}          {s['recall']:.3f}")
    s05, sbest = iou_at(pt, mt, 0.5), iou_at(pt, mt, best)
    print(f"\nBest validation threshold: {best:.2f}")
    print(f"TEST at 0.50: IoU {s05['iou']:.3f} (precision {s05['precision']:.3f}, recall {s05['recall']:.3f})")
    print(f"TEST at {best:.2f}: IoU {sbest['iou']:.3f} (precision {sbest['precision']:.3f}, recall {sbest['recall']:.3f})")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    main(sys.argv[1], sys.argv[2])