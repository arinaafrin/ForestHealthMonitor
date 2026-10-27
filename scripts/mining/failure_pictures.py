from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import csv
import json
import numpy as np
import torch
from src.mining.dataset import PatchDataset
from src.mining.evaluate import load_model
from src.mining.train import pick_device
from src.mining.visualise import save_triptych

def main(run_dir: str, data_dir: str, out_dir: str, patch_ids: list[str]) -> None:
    run, data, out = Path(run_dir), Path(data_dir), Path(out_dir)
    stats = json.load(open(run / "channel_stats.json"))
    ds = PatchDataset(data, "test", stats)
    ids = [r["patch_id"] for r in ds.rows]
    country = {r["patch_id"]: r["iso3"] for r in ds.rows}
    per_patch = {r["patch_id"]: r for r in csv.DictReader(open(run / "test_per_patch.csv"))}

    if not patch_ids:  
        patch_ids = list(per_patch)[:8]
    missing = [p for p in patch_ids if p not in ids]
    if missing:
        raise SystemExit(f"Not in the test split: {missing}")

    device = pick_device()
    model = load_model(run, device)
    for pid in patch_ids:
        item = ds[ids.index(pid)]
        with torch.no_grad():
            pred = (torch.sigmoid(model(item["image"][None].to(device)))[0, 0] >= 0.5).cpu().numpy()
        raw = np.load(data / ds.rows[ids.index(pid)]["file"])["image"].astype("float32")
        iou = float(per_patch[pid]["iou"])
        save_triptych(out / f"{pid}.png", raw, item["mask"][0].numpy(), pred,
                      f"{pid} ({country[pid]})  IoU {iou:.3f}")
        print(f"saved {out / f'{pid}.png'}")

    print("\nMarkdown for the docs:\n")
    for pid in patch_ids:
        print(f"**{pid}** ({country[pid]})\n\n![{pid}]({out.as_posix().replace('docs/', '')}/{pid}.png)\n")

if __name__ == "__main__":
    if len(sys.argv) < 4:
        raise SystemExit(__doc__)
    main(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4:])