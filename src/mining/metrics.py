from __future__ import annotations
from dataclasses import dataclass
import numpy as np
_EPS = 1e-9

@dataclass
class Confusion:
    tp: int = 0
    fp: int = 0
    fn: int = 0
    tn: int = 0

    def update(self, pred: np.ndarray, target: np.ndarray) -> None:
        if pred.shape != target.shape:
            raise ValueError(f"Shape mismatch: {pred.shape} vs {target.shape}")
        p = pred.astype(bool)
        t = target.astype(bool)
        self.tp += int(np.sum(p & t))
        self.fp += int(np.sum(p & ~t))
        self.fn += int(np.sum(~p & t))
        self.tn += int(np.sum(~p & ~t))

    def scores(self) -> dict[str, float]:
        precision = self.tp / (self.tp + self.fp + _EPS)
        recall = self.tp / (self.tp + self.fn + _EPS)
        return {
            "iou": self.tp / (self.tp + self.fp + self.fn + _EPS),
            "f1": 2 * self.tp / (2 * self.tp + self.fp + self.fn + _EPS),
            "precision": precision,
            "recall": recall,
            "pixel_accuracy": (self.tp + self.tn) / (self.tp + self.fp + self.fn + self.tn + _EPS),
            "pixels": self.tp + self.fp + self.fn + self.tn,
        }


def image_iou(pred: np.ndarray, target: np.ndarray) -> float:
    p, t = pred.astype(bool), target.astype(bool)
    union = np.sum(p | t)
    if union == 0:
        return 1.0
    return float(np.sum(p & t) / union)