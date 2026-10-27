"""Build the patch dataset: images from Earth Engine, masks from polygons."""
from __future__ import annotations

import csv
import json
import logging
from dataclasses import asdict
from pathlib import Path

import numpy as np

from src.mining.config import DataConfig, S2_BANDS, save_config
from src.mining.geo import grid_around, lonlat_box
from src.mining.gee_export import fetch_patch, to_reflectance, valid_fraction
from src.mining.labels import load_polygons, polygons_to_mask
from src.mining.sampling import (Site, finalize_sites, pick_negative_sites,pick_positive_sites)

log = logging.getLogger(__name__)

MANIFEST_FIELDS = ["patch_id", "split", "block_id", "iso3", "lon", "lat", "is_negative", "mask_fraction", "valid_fraction", "file"]


def write_patch(out_dir: Path, site: Site, image: np.ndarray, mask: np.ndarray,
                valid: float) -> dict:
    """Save one patch as compressed npz and return its manifest row."""
    rel = f"patches/{site.split}/{site.patch_id}.npz"
    path = out_dir / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(path, image=image.astype(np.float16), mask=mask.astype(np.uint8))
    return {
        "patch_id": site.patch_id, "split": site.split, "block_id": site.block_id,
        "iso3": site.iso3, "lon": round(site.lon, 6), "lat": round(site.lat, 6),
        "is_negative": int(site.is_negative),
        "mask_fraction": round(float(mask.mean()), 6),
        "valid_fraction": round(valid, 4), "file": rel,
    }


def write_manifest(out_dir: Path, rows: list[dict]) -> Path:
    path = out_dir / "manifest.csv"
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=MANIFEST_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    return path


def _connect_earth_engine():
    import os

    email = os.getenv("GEE_SERVICE_ACCOUNT_EMAIL")
    key_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if not email or not key_path:
        raise RuntimeError(
            "Set GEE_SERVICE_ACCOUNT_EMAIL and GOOGLE_APPLICATION_CREDENTIALS "
            "(path to the service-account key file) before building the dataset."
        )
    import ee

    from src.ingestion.earth_engine_client import connect_to_satellite_service

    connect_to_satellite_service(email, key_path)
    return ee


def build_dataset(cfg: DataConfig, limit: int | None = None, min_valid: float = 0.9) -> Path:
    ee = _connect_earth_engine()

    out_dir = Path(cfg.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    save_config(cfg, out_dir / "data_config.json")

    gdf = load_polygons(cfg.polygons_path)
    positives = pick_positive_sites(gdf, cfg.n_sites, cfg.min_area_km2, cfg.max_area_km2, cfg.seed)
    negatives = pick_negative_sites(gdf, int(len(positives) * cfg.neg_ratio),
                                    cfg.neg_min_distance_deg, cfg.seed, positives)
    sites = finalize_sites(positives + negatives, cfg.block_deg, cfg.val_fraction, cfg.test_fraction, cfg.seed)
    if limit:
        sites = sites[:limit]
    log.info("Sites: %d (%d negative)", len(sites), sum(s.is_negative for s in sites))

    rows, skipped = [], 0
    for i, site in enumerate(sites, 1):
        grid = grid_around(site.lon, site.lat, cfg.patch_px, cfg.pixel_size_m)
        try:
            raw = fetch_patch(ee, site.lon, site.lat, grid, cfg.year, cfg.max_cloud_percent)
        except Exception as exc:  
            log.warning("Skipping %s: %s", site.patch_id, exc)
            skipped += 1
            continue
        valid = valid_fraction(raw)
        if valid < min_valid:
            log.info("Skipping %s: only %.0f%% valid pixels", site.patch_id, valid * 100)
            skipped += 1
            continue
        near = gdf.iloc[list(gdf.sindex.query(lonlat_box(grid), predicate="intersects"))]
        mask = polygons_to_mask(list(near.geometry), grid)
        rows.append(write_patch(out_dir, site, to_reflectance(raw), mask, valid))
        if i % 10 == 0:
            log.info("Exported %d / %d", i, len(sites))

    manifest = write_manifest(out_dir, rows)
    (out_dir / "summary.json").write_text(json.dumps({
        "patches": len(rows), "skipped": skipped, "bands": list(S2_BANDS),
        "label_source": "Maus et al. 2022, Global-scale mining polygons v2, doi:10.1594/PANGAEA.942325",
        "config": asdict(cfg),
    }, indent=2), encoding="utf-8")
    log.info("Done: %d patches, %d skipped. Manifest: %s", len(rows), skipped, manifest)
    return manifest