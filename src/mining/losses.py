from __future__ import annotations
import torch
import torch.nn.functional as F


def soft_dice_loss(logits: torch.Tensor, target: torch.Tensor, eps: float = 1.0) -> torch.Tensor:
    prob = torch.sigmoid(logits)
    dims = (1, 2, 3)
    inter = (prob * target).sum(dims)
    total = prob.sum(dims) + target.sum(dims)
    return (1.0 - (2.0 * inter + eps) / (total + eps)).mean()


def combined_loss(logits: torch.Tensor, target: torch.Tensor, dice_weight: float = 0.5) -> torch.Tensor:
    bce = F.binary_cross_entropy_with_logits(logits, target)
    return (1.0 - dice_weight) * bce + dice_weight * soft_dice_loss(logits, target)