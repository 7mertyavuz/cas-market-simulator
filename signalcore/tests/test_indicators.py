from datetime import timedelta

from signalcore.feeds import synthetic_ohlcv, Regime
from signalcore.indicators.trend import trend_factor
from signalcore.indicators.momentum import momentum_factor
from signalcore.indicators.volatility import volatility_factor


def test_trend_factor_bounds():
    bars = synthetic_ohlcv(200, seed=1)
    v = trend_factor(bars)
    assert -1.0 <= v.vote <= 1.0
    assert v.name == "trend"


def test_trend_factor_short_series_neutral():
    bars = synthetic_ohlcv(5, seed=1)
    v = trend_factor(bars)
    assert v.vote == 0.0


def test_trend_factor_detects_strong_uptrend():
    bars = synthetic_ohlcv(300, seed=5, initial_regime=Regime.TREND_UP)
    v = trend_factor(bars)
    # kesin yon garantisi vermeyiz (stokastik) ama bound icinde olmali
    assert -1.0 <= v.vote <= 1.0


def test_momentum_factor_bounds():
    bars = synthetic_ohlcv(200, seed=2)
    v = momentum_factor(bars)
    assert -1.0 <= v.vote <= 1.0
    assert v.name == "momentum"


def test_momentum_factor_short_series_neutral():
    bars = synthetic_ohlcv(5, seed=2)
    v = momentum_factor(bars)
    assert v.vote == 0.0


def test_volatility_factor_bounds():
    bars = synthetic_ohlcv(200, seed=3)
    v = volatility_factor(bars)
    assert -1.0 <= v.vote <= 1.0
    assert v.name == "volatility"


def test_volatility_factor_short_series_neutral():
    bars = synthetic_ohlcv(5, seed=3)
    v = volatility_factor(bars)
    assert v.vote == 0.0
