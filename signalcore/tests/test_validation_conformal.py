import numpy as np

from signalcore.validation.conformal import (
    calibrate,
    confidence_from_interval_width,
    prediction_interval,
)


def test_calibrate_basic():
    rng = np.random.default_rng(0)
    preds = rng.normal(0, 1, 200)
    actuals = preds + rng.normal(0, 0.1, 200)
    cal = calibrate(preds, actuals, coverage=0.9)
    assert cal.n_calibration == 200
    assert cal.quantile > 0


def test_calibrate_empty():
    cal = calibrate([], [])
    assert cal.n_calibration == 0


def test_calibrate_mismatched_lengths_raises():
    import pytest

    with pytest.raises(ValueError):
        calibrate([1, 2], [1])


def test_prediction_interval_symmetric():
    from signalcore.validation.conformal import ConformalCalibration

    cal = ConformalCalibration(quantile=0.5, coverage=0.9, n_calibration=100)
    lo, hi = prediction_interval(1.0, cal)
    assert lo == 0.5
    assert hi == 1.5


def test_confidence_from_interval_width_narrower_is_more_confident():
    from signalcore.validation.conformal import ConformalCalibration

    narrow = ConformalCalibration(quantile=0.05, coverage=0.9, n_calibration=100)
    wide = ConformalCalibration(quantile=2.0, coverage=0.9, n_calibration=100)
    assert confidence_from_interval_width(narrow) > confidence_from_interval_width(wide)


def test_confidence_zero_for_empty_calibration():
    from signalcore.validation.conformal import ConformalCalibration

    empty = ConformalCalibration(quantile=float("inf"), coverage=0.9, n_calibration=0)
    assert confidence_from_interval_width(empty) == 0.0
