from __future__ import annotations
from pathlib import Path
import numpy as np

def make_rgb(image: np.ndarray, rgb_channels: tuple[int, int, int] = (2, 1, 0)) -> np.ndarray:
    rgb = np.stack([image[c].astype(np.float32) for c in rgb_channels], axis=-1)
    lo, hi = np.percentile(rgb, 2), np.percentile(rgb, 98)
    if hi - lo < 1e-6:
        return np.zeros(rgb.shape, dtype=np.uint8)
    return (np.clip((rgb - lo) / (hi - lo), 0, 1) * 255).astype(np.uint8)


def save_triptych(path: str | Path, image: np.ndarray, mask: np.ndarray, pred: np.ndarray, title: str = "") -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 3, figsize=(9, 3.2))
    axes[0].imshow(make_rgb(image)); axes[0].set_title("Sentinel-2")
    axes[1].imshow(mask, cmap="gray", vmin=0, vmax=1); axes[1].set_title("Label")
    axes[2].imshow(pred, cmap="gray", vmin=0, vmax=1); axes[2].set_title("Prediction")
    for ax in axes:
        ax.axis("off")
    if title:
        fig.suptitle(title, fontsize=9)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)