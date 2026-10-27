from __future__ import annotations
import math
from dataclasses import dataclass
import numpy as np

@dataclass(frozen=True)
class Site:
    patch_id: str
    lon: float
    lat: float
    iso3: str
    is_negative: bool
    block_id: str = ""
    split: str = ""


def block_id_for(lon: float, lat: float, block_deg: float) -> str:
    bx = math.floor(lon / block_deg)
    by = math.floor(lat / block_deg)
    return f"{bx}_{by}"


def assign_splits(
    block_ids: list[str],
    val_fraction: float,
    test_fraction: float,
    seed: int,
) -> dict[str, str]:
    unique = sorted(set(block_ids))
    if len(unique) < 3:
        raise ValueError(
            f"Need at least 3 spatial blocks to make train/val/test, got {len(unique)}. "
            "Use more sites or a smaller block size."
        )
    if val_fraction + test_fraction >= 1.0:
        raise ValueError("val_fraction + test_fraction must be below 1.")

    rng = np.random.default_rng(seed)
    order = rng.permutation(len(unique))
    n = len(unique)
    n_test = max(1, round(n * test_fraction))
    n_val = max(1, round(n * val_fraction))
    if n_test + n_val >= n:  
        n_test, n_val = 1, 1

    mapping: dict[str, str] = {}
    for rank, idx in enumerate(order):
        if rank < n_test:
            mapping[unique[idx]] = "test"
        elif rank < n_test + n_val:
            mapping[unique[idx]] = "val"
        else:
            mapping[unique[idx]] = "train"
    return mapping


def check_no_block_leak(sites: list[Site]) -> None:
    seen: dict[str, str] = {}
    for s in sites:
        previous = seen.setdefault(s.block_id, s.split)
        if previous != s.split:
            raise AssertionError(
                f"Spatial leakage: block {s.block_id} is in both '{previous}' and '{s.split}'."
            )


def pick_positive_sites(gdf, n_sites: int, min_area_km2: float, max_area_km2: float, seed: int) -> list[Site]:
    rng = np.random.default_rng(seed)
    area = gdf["AREA"].to_numpy(dtype=float)
    keep = np.flatnonzero((area >= min_area_km2) & (area <= max_area_km2))
    if keep.size == 0:
        raise ValueError("No polygons match the area limits.")

    by_country: dict[str, list[int]] = {}
    for i in keep:
        by_country.setdefault(str(gdf["ISO3_CODE"].iloc[i]), []).append(int(i))
    for rows in by_country.values():
        rng.shuffle(rows)

    countries = sorted(by_country)
    rng.shuffle(countries)
    chosen: list[int] = []
    while len(chosen) < n_sites and any(by_country.values()):
        for c in countries:
            if by_country[c] and len(chosen) < n_sites:
                chosen.append(by_country[c].pop())

    sites = []
    for k, i in enumerate(chosen):
        centroid = gdf.geometry.iloc[i].representative_point()
        sites.append(Site(
            patch_id=f"pos_{k:05d}",
            lon=float(centroid.x), lat=float(centroid.y),
            iso3=str(gdf["ISO3_CODE"].iloc[i]), is_negative=False,
        ))
    return sites


def pick_negative_sites(gdf, n_neg: int, min_distance_deg: float, seed: int, positives: list[Site]) -> list[Site]:
    if n_neg <= 0 or not positives:
        return []
    rng = np.random.default_rng(seed + 1)
    sindex = gdf.sindex
    sites: list[Site] = []
    attempts = 0
    while len(sites) < n_neg and attempts < n_neg * 200:
        attempts += 1
        base = positives[int(rng.integers(len(positives)))]
        angle = rng.uniform(0, 2 * math.pi)
        dist = rng.uniform(0.2, 0.8)
        lon = base.lon + dist * math.cos(angle)
        lat = base.lat + dist * math.sin(angle)
        if not (-180 <= lon <= 180 and -80 <= lat <= 80):
            continue
        near = sindex.query(
            _bbox(lon, lat, min_distance_deg), predicate="intersects"
        )
        if len(near) > 0:
            continue
        sites.append(Site(
            patch_id=f"neg_{len(sites):05d}", lon=float(lon), lat=float(lat),
            iso3=base.iso3, is_negative=True,
        ))
    return sites


def _bbox(lon: float, lat: float, half_deg: float):
    from shapely.geometry import box
    return box(lon - half_deg, lat - half_deg, lon + half_deg, lat + half_deg)


def finalize_sites(sites: list[Site], block_deg: float, val_fraction: float, test_fraction: float, seed: int) -> list[Site]:
    with_blocks = [
        Site(**{**s.__dict__, "block_id": block_id_for(s.lon, s.lat, block_deg)})
        for s in sites
    ]
    mapping = assign_splits([s.block_id for s in with_blocks], val_fraction, test_fraction, seed)
    final = [Site(**{**s.__dict__, "split": mapping[s.block_id]}) for s in with_blocks]
    check_no_block_leak(final)
    return final