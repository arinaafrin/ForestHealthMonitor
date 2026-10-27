import numpy as np
import pytest
from src.mining.metrics import Confusion, image_iou

def test_known_confusion_counts_and_scores():
    pred = np.array([[1, 1, 0, 0]])
    target = np.array([[1, 0, 1, 0]])
    c = Confusion()
    c.update(pred, target)
    assert (c.tp, c.fp, c.fn, c.tn) == (1, 1, 1, 1)
    s = c.scores()
    assert s["iou"] == pytest.approx(1 / 3, abs=1e-6)
    assert s["f1"] == pytest.approx(0.5, abs=1e-6)
    assert s["precision"] == pytest.approx(0.5, abs=1e-6)
    assert s["recall"] == pytest.approx(0.5, abs=1e-6)
    assert s["pixel_accuracy"] == pytest.approx(0.5, abs=1e-6)

def test_perfect_prediction_has_iou_one():
    x = (np.random.default_rng(0).random((4, 16, 16)) > 0.7).astype(np.uint8)
    c = Confusion(); c.update(x, x)
    assert c.scores()["iou"] == pytest.approx(1.0, abs=1e-6)

def test_counts_add_up_over_batches():
    c = Confusion()
    c.update(np.ones((2, 2)), np.ones((2, 2)))
    c.update(np.zeros((2, 2)), np.ones((2, 2)))
    assert c.tp == 4 and c.fn == 4
    assert c.scores()["recall"] == pytest.approx(0.5, abs=1e-6)

def test_shape_mismatch_is_an_error():
    with pytest.raises(ValueError):
        Confusion().update(np.zeros((2, 2)), np.zeros((3, 3)))

def test_empty_vs_empty_image_iou_is_one_and_empty_vs_something_is_zero():
    z = np.zeros((8, 8))
    assert image_iou(z, z) == 1.0
    o = z.copy(); o[0, 0] = 1
    assert image_iou(z, o) == 0.0