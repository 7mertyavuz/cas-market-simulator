from signalcore.feeds import synthetic_ohlcv
from signalcore.risk.levels import atr_stop_tp, to_risk_dict
from signalcore.risk.sizing import edge_from_confidence, half_kelly_size, kelly_fraction


def test_kelly_fraction_zero_win_loss_ratio():
    assert kelly_fraction(0.6, 0.0) == 0.0


def test_kelly_fraction_positive_edge():
    f = kelly_fraction(0.6, 1.5)
    assert f > 0.0


def test_kelly_fraction_never_negative():
    f = kelly_fraction(0.1, 1.0)
    assert f == 0.0


def test_half_kelly_size_bounds():
    r = half_kelly_size(0.8, max_size_pct=0.1)
    assert 0.0 <= r.size_pct <= 0.1


def test_half_kelly_size_zero_confidence():
    r = half_kelly_size(0.0)
    assert r.size_pct >= 0.0


def test_edge_from_confidence_increases_with_confidence():
    low = edge_from_confidence(0.1)
    high = edge_from_confidence(0.9)
    assert high > low


def test_atr_stop_tp_long_direction():
    bars = synthetic_ohlcv(100, seed=1)
    levels = atr_stop_tp(bars, "LONG")
    assert levels is not None
    assert levels.stop < levels.entry < levels.take_profit


def test_atr_stop_tp_short_direction():
    bars = synthetic_ohlcv(100, seed=1)
    levels = atr_stop_tp(bars, "SHORT")
    assert levels is not None
    assert levels.take_profit < levels.entry < levels.stop


def test_atr_stop_tp_neutral_returns_none():
    bars = synthetic_ohlcv(100, seed=1)
    assert atr_stop_tp(bars, "NEUTRAL") is None


def test_atr_stop_tp_short_series_returns_none():
    bars = synthetic_ohlcv(5, seed=1)
    assert atr_stop_tp(bars, "LONG") is None


def test_to_risk_dict_none_levels():
    d = to_risk_dict(0.05, None)
    assert d["size_pct"] == 0.0
    assert d["stop"] is None


def test_to_risk_dict_with_levels():
    bars = synthetic_ohlcv(100, seed=2)
    levels = atr_stop_tp(bars, "LONG")
    d = to_risk_dict(0.05, levels)
    assert d["size_pct"] == 0.05
    assert d["stop"] == levels.stop
