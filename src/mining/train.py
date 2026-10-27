from __future__ import annotations
import csv
import json
import logging
import random
import time
from dataclasses import asdict
from pathlib import Path
import numpy as np
import torch
from torch.utils.data import DataLoader
from src.mining.config import TrainConfig, save_config
from src.mining.dataset import PatchDataset, load_or_make_stats, read_manifest
from src.mining.losses import combined_loss
from src.mining.metrics import Confusion, image_iou
from src.mining.model import UNet, count_parameters

log = logging.getLogger(__name__)


def set_seed(seed: int, deterministic: bool = True) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    if deterministic:
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False


def pick_device() -> torch.device:
    return torch.device("cuda" if torch.cuda.is_available() else "cpu")


@torch.no_grad()
def evaluate_split(model: torch.nn.Module, loader: DataLoader, device: torch.device, threshold: float = 0.5, dice_weight: float = 0.5) -> tuple[dict, list[dict]]:
    model.eval()
    confusion = Confusion()
    per_patch: list[dict] = []
    total_loss, n = 0.0, 0
    for batch in loader:
        x = batch["image"].to(device)
        y = batch["mask"].to(device)
        logits = model(x)
        total_loss += combined_loss(logits, y, dice_weight).item() * x.shape[0]
        n += x.shape[0]
        pred = (torch.sigmoid(logits) >= threshold).cpu().numpy().astype(np.uint8)
        target = y.cpu().numpy().astype(np.uint8)
        confusion.update(pred, target)
        for i, pid in enumerate(batch["patch_id"]):
            per_patch.append({
                "patch_id": pid,
                "iou": image_iou(pred[i], target[i]),
                "pred_fraction": float(pred[i].mean()),
                "mask_fraction": float(target[i].mean()),
            })
    scores = confusion.scores()
    scores["loss"] = total_loss / max(n, 1)
    return scores, per_patch


def _train_one_epoch(model, loader, optimizer, device, dice_weight) -> float:
    model.train()
    total, n = 0.0, 0
    for batch in loader:
        x = batch["image"].to(device)
        y = batch["mask"].to(device)
        optimizer.zero_grad(set_to_none=True)
        loss = combined_loss(model(x), y, dice_weight)
        loss.backward()
        optimizer.step()
        total += loss.item() * x.shape[0]
        n += x.shape[0]
    return total / max(n, 1)

def train(cfg: TrainConfig) -> dict:
    run_dir = Path(cfg.run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)
    save_config(cfg, run_dir / "config.json")
    set_seed(cfg.seed, cfg.deterministic)
    device = pick_device()

    rows = read_manifest(cfg.data_dir)
    stats = load_or_make_stats(cfg.data_dir, rows)
    (run_dir / "channel_stats.json").write_text(json.dumps(stats, indent=2))

    train_ds = PatchDataset(cfg.data_dir, "train", stats, seed=cfg.seed)
    val_ds = PatchDataset(cfg.data_dir, "val", stats)
    test_ds = PatchDataset(cfg.data_dir, "test", stats)
    gen = torch.Generator().manual_seed(cfg.seed)
    train_loader = DataLoader(train_ds, batch_size=cfg.batch_size, shuffle=True, num_workers=cfg.num_workers, generator=gen)
    val_loader = DataLoader(val_ds, batch_size=cfg.batch_size, num_workers=cfg.num_workers)
    test_loader = DataLoader(test_ds, batch_size=cfg.batch_size, num_workers=cfg.num_workers)

    in_ch = len(stats["mean"])
    model = UNet(in_channels=in_ch, base=cfg.base_channels).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=cfg.lr, weight_decay=cfg.weight_decay)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=cfg.epochs)
    log.info("Device=%s params=%d train=%d val=%d test=%d", device, count_parameters(model), len(train_ds), len(val_ds), len(test_ds))

    best_iou, best_epoch, stale = -1.0, 0, 0
    history: list[dict] = []
    start = time.time()
    for epoch in range(1, cfg.epochs + 1):
        train_loss = _train_one_epoch(model, train_loader, optimizer, device, cfg.dice_weight)
        val_scores, _ = evaluate_split(model, val_loader, device, cfg.threshold, cfg.dice_weight)
        scheduler.step()
        history.append({"epoch": epoch, "train_loss": train_loss,
                        "val_loss": val_scores["loss"], "val_iou": val_scores["iou"],
                        "val_f1": val_scores["f1"]})
        log.info("epoch %02d train_loss=%.4f val_iou=%.4f", epoch, train_loss, val_scores["iou"])
        if val_scores["iou"] > best_iou:
            best_iou, best_epoch, stale = val_scores["iou"], epoch, 0
            torch.save({"model": model.state_dict(), "in_channels": in_ch,
                        "base": cfg.base_channels, "epoch": epoch}, run_dir / "best.pt")
        else:
            stale += 1
            if stale >= cfg.patience:
                log.info("Early stop at epoch %d", epoch)
                break

    with (run_dir / "history.csv").open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(history[0]))
        writer.writeheader()
        writer.writerows(history)

    ckpt = torch.load(run_dir / "best.pt", map_location=device)
    model.load_state_dict(ckpt["model"])
    val_scores, _ = evaluate_split(model, val_loader, device, cfg.threshold, cfg.dice_weight)
    test_scores, per_patch = evaluate_split(model, test_loader, device, cfg.threshold, cfg.dice_weight)

    result = {
        "best_epoch": best_epoch, "seconds": round(time.time() - start, 1),
        "device": str(device), "parameters": count_parameters(model),
        "n_patches": {"train": len(train_ds), "val": len(val_ds), "test": len(test_ds)},
        "val": val_scores, "test": test_scores, "config": asdict(cfg),
    }
    (run_dir / "metrics.json").write_text(json.dumps(result, indent=2))
    write_per_patch(run_dir / "test_per_patch.csv", per_patch)
    write_results_table(run_dir / "results.md", result)
    return result


def write_per_patch(path: Path, per_patch: list[dict]) -> None:
    ordered = sorted(per_patch, key=lambda r: r["iou"]) 
    with path.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["patch_id", "iou", "pred_fraction", "mask_fraction"])
        writer.writeheader()
        writer.writerows(ordered)


def write_results_table(path: Path, result: dict) -> None:
    v, t = result["val"], result["test"]
    lines = [
        "| Split | Patches | IoU | F1 | Precision | Recall |",
        "|---|---|---|---|---|---|",
        f"| val | {result['n_patches']['val']} | {v['iou']:.3f} | {v['f1']:.3f} | {v['precision']:.3f} | {v['recall']:.3f} |",
        f"| test | {result['n_patches']['test']} | {t['iou']:.3f} | {t['f1']:.3f} | {t['precision']:.3f} | {t['recall']:.3f} |",
        "",
        f"Best epoch: {result['best_epoch']}. Parameters: {result['parameters']:,}. Device: {result['device']}.",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")