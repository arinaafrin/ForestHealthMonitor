from __future__ import annotations
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

# Sentinel-2 bands used as model input
S2_BANDS: tuple[str, ...] = ("B2", "B3", "B4", "B8", "B11", "B12")
S2_COLLECTION = "COPERNICUS/S2_SR_HARMONIZED"
SCL_BAD_CLASSES: tuple[int, ...] = (1, 3, 8, 9, 10)


@dataclass
class DataConfig:
    polygons_path: str = "data/raw/global_mining_polygons_v2.gpkg"
    out_dir: str = "data/mining_patches"
    year: int = 2019
    patch_px: int = 256          
    pixel_size_m: float = 10.0
    n_sites: int = 120           
    neg_ratio: float = 0.25      
    neg_min_distance_deg: float = 0.15  
    min_area_km2: float = 0.05
    max_area_km2: float = 50.0
    block_deg: float = 1.0       
    val_fraction: float = 0.15
    test_fraction: float = 0.15
    max_cloud_percent: float = 40.0
    seed: int = 42


@dataclass
class TrainConfig:
    data_dir: str = "data/mining_patches"
    run_dir: str = "runs/mining_baseline"
    epochs: int = 30
    batch_size: int = 8
    lr: float = 1e-3
    weight_decay: float = 1e-4
    base_channels: int = 16
    dice_weight: float = 0.5
    patience: int = 8           
    threshold: float = 0.5
    num_workers: int = 0
    seed: int = 42
    deterministic: bool = True


@dataclass
class Config:
    data: DataConfig = field(default_factory=DataConfig)
    train: TrainConfig = field(default_factory=TrainConfig)


def save_config(cfg: object, path: str | Path) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(asdict(cfg), indent=2), encoding="utf-8")