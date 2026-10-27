from __future__ import annotations
import json
from pathlib import Path
import torch
from torch.utils.data import DataLoader
from src.mining.dataset import PatchDataset
from src.mining.model import UNet
from src.mining.train import evaluate_split, pick_device, write_per_patch

def load_model(run_dir: str | Path, device: torch.device) -> UNet:
    ckpt = torch.load(Path(run_dir) / "best.pt", map_location=device)
    model = UNet(in_channels=ckpt["in_channels"], base=ckpt["base"]).to(device)
    model.load_state_dict(ckpt["model"])
    return model.eval()

def evaluate_run(run_dir: str | Path, data_dir: str | Path, split: str = "test", threshold: float = 0.5, batch_size: int = 8) -> dict:
    run_dir = Path(run_dir)
    device = pick_device()
    stats = json.loads((run_dir / "channel_stats.json").read_text())
    dataset = PatchDataset(data_dir, split, stats)
    loader = DataLoader(dataset, batch_size=batch_size)
    scores, per_patch = evaluate_split(load_model(run_dir, device), loader, device, threshold)
    write_per_patch(run_dir / f"{split}_per_patch.csv", per_patch)
    (run_dir / f"{split}_scores.json").write_text(json.dumps(scores, indent=2))
    return scores