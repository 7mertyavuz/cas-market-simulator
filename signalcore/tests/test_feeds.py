from datetime import timedelta

from signalcore.core.ohlcv import validate_series
from signalcore.feeds import synthetic_ohlcv


def test_synthetic_ohlcv_basic_shape():
    bars = synthetic_ohlcv(200, seed=1)
    assert len(bars) == 200
    for b in bars:
        assert b.low <= b.open <= b.high
        assert b.low <= b.close <= b.high
        assert b.volume >= 0


def test_synthetic_ohlcv_passes_validation():
    bars = synthetic_ohlcv(100, seed=7, interval=timedelta(minutes=1))
    validate_series(bars, expected_interval=timedelta(minutes=1))


def test_synthetic_ohlcv_deterministic_with_seed():
    a = synthetic_ohlcv(50, seed=123)
    b = synthetic_ohlcv(50, seed=123)
    assert [x.close for x in a] == [x.close for x in b]


def test_synthetic_ohlcv_different_seeds_diverge():
    a = synthetic_ohlcv(50, seed=1)
    b = synthetic_ohlcv(50, seed=2)
    assert [x.close for x in a] != [x.close for x in b]
