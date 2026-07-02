from datetime import datetime, timedelta, timezone

import pytest

from signalcore.core.ohlcv import OHLCVValidationError, validate_bar, validate_series
from signalcore.core.types import OHLCVBar


def make_bar(ts, o=100, h=101, l=99, c=100.5, v=10):
    return OHLCVBar(ts=ts, open=o, high=h, low=l, close=c, volume=v)


def test_validate_bar_ok():
    validate_bar(make_bar(datetime.now(timezone.utc)))


def test_validate_bar_high_low_inverted():
    with pytest.raises(OHLCVValidationError):
        validate_bar(make_bar(datetime.now(timezone.utc), h=90, l=99))


def test_validate_bar_open_outside_range():
    with pytest.raises(OHLCVValidationError):
        validate_bar(make_bar(datetime.now(timezone.utc), o=200))


def test_validate_bar_negative_volume():
    with pytest.raises(OHLCVValidationError):
        validate_bar(make_bar(datetime.now(timezone.utc), v=-1))


def test_validate_series_detects_gap():
    t0 = datetime.now(timezone.utc)
    bars = [make_bar(t0), make_bar(t0 + timedelta(minutes=2))]
    with pytest.raises(OHLCVValidationError):
        validate_series(bars, expected_interval=timedelta(minutes=1))


def test_validate_series_ok_with_interval():
    t0 = datetime.now(timezone.utc)
    bars = [make_bar(t0 + timedelta(minutes=i)) for i in range(5)]
    validate_series(bars, expected_interval=timedelta(minutes=1))


def test_validate_series_rejects_non_increasing_ts():
    t0 = datetime.now(timezone.utc)
    bars = [make_bar(t0), make_bar(t0)]
    with pytest.raises(OHLCVValidationError):
        validate_series(bars)


def test_validate_series_empty_raises():
    with pytest.raises(OHLCVValidationError):
        validate_series([])
