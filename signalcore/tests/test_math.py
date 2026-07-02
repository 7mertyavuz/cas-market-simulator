import numpy as np

from signalcore.indicators import _math


def test_ema_matches_sma_seed():
    x = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    out = _math.ema(x, 3)
    assert np.isnan(out[0]) and np.isnan(out[1])
    assert out[2] == np.mean(x[:3])


def test_rsi_bounds():
    rng = np.random.default_rng(0)
    x = np.cumsum(rng.normal(0, 1, 100)) + 100
    out = _math.rsi(x, 14)
    valid = out[~np.isnan(out)]
    assert np.all((valid >= 0) & (valid <= 100))


def test_rsi_all_up_near_100():
    x = np.arange(1, 30, dtype=float)
    out = _math.rsi(x, 14)
    assert out[-1] > 90


def test_atr_nonnegative():
    rng = np.random.default_rng(1)
    close = np.cumsum(rng.normal(0, 1, 60)) + 100
    high = close + np.abs(rng.normal(0, 1, 60))
    low = close - np.abs(rng.normal(0, 1, 60))
    out = _math.atr(high, low, close, 14)
    valid = out[~np.isnan(out)]
    assert np.all(valid >= 0)


def test_hurst_random_walk_near_half():
    rng = np.random.default_rng(2)
    x = np.cumsum(rng.normal(0, 1, 500)) + 100
    h = _math.hurst_exponent(x)
    assert 0.3 < h < 0.7


def test_efficiency_ratio_bounds():
    rng = np.random.default_rng(3)
    close = np.cumsum(rng.normal(0, 1, 100)) + 100
    out = _math.efficiency_ratio(close, 10)
    valid = out[~np.isnan(out)]
    assert np.all((valid >= 0) & (valid <= 1.0001))


def test_bollinger_upper_above_lower():
    rng = np.random.default_rng(4)
    close = np.cumsum(rng.normal(0, 1, 60)) + 100
    mid, upper, lower, pct_b = _math.bollinger(close, 20)
    valid = ~np.isnan(upper)
    assert np.all(upper[valid] >= lower[valid])
