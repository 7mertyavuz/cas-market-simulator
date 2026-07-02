import numpy as np

from signalcore.feeds import synthetic_ohlcv
from signalcore.indicators.meanrev import meanrev_factor
from signalcore.indicators.structure import fracdiff, regime_from_hurst, structure_factor
from signalcore.indicators.volume import volume_factor


def test_meanrev_factor_bounds():
    bars = synthetic_ohlcv(200, seed=1)
    v = meanrev_factor(bars)
    assert -1.0 <= v.vote <= 1.0
    assert v.name == "meanrev"


def test_meanrev_short_series_neutral():
    bars = synthetic_ohlcv(5, seed=1)
    v = meanrev_factor(bars)
    assert v.vote == 0.0


def test_volume_factor_bounds():
    bars = synthetic_ohlcv(200, seed=2)
    v = volume_factor(bars)
    assert -1.0 <= v.vote <= 1.0
    assert v.name == "volume"


def test_volume_short_series_neutral():
    bars = synthetic_ohlcv(5, seed=2)
    v = volume_factor(bars)
    assert v.vote == 0.0


def test_structure_factor_bounds():
    bars = synthetic_ohlcv(200, seed=3)
    v = structure_factor(bars)
    assert -1.0 <= v.vote <= 1.0
    assert v.name == "structure"


def test_regime_from_hurst_valid_labels():
    bars = synthetic_ohlcv(300, seed=4)
    regime = regime_from_hurst(bars)
    assert regime in ("trend", "mean_revert", "random")


def test_regime_from_hurst_short_series_random():
    bars = synthetic_ohlcv(5, seed=4)
    assert regime_from_hurst(bars) == "random"


def test_fracdiff_produces_finite_tail():
    rng = np.random.default_rng(0)
    x = np.cumsum(rng.normal(0, 1, 200)) + 100
    out = fracdiff(x, d=0.4)
    assert np.isfinite(out[-1])
    assert np.isnan(out[0])  # baslangicta pencere dolmadan NaN
