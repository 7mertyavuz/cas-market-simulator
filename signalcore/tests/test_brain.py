from signalcore.brain import analyze
from signalcore.core.types import FactorVote
from signalcore.feeds import synthetic_ohlcv


def test_analyze_returns_card():
    bars = synthetic_ohlcv(300, seed=10)
    card = analyze("SIM/USDT", bars)
    assert card.symbol == "SIM/USDT"
    assert card.direction in ("LONG", "SHORT", "NEUTRAL")
    assert 0.0 <= card.confidence <= 1.0
    assert len(card.votes) >= 3  # trend + momentum + volatility


def test_analyze_includes_extra_factors():
    bars = synthetic_ohlcv(300, seed=11)
    extra = {"sentiment": FactorVote(name="sentiment", vote=0.9, weight=0.15)}
    card = analyze("SIM/USDT", bars, extra_factors=extra)
    names = [v.name for v in card.votes]
    assert "sentiment" in names


def test_analyze_handles_short_series_gracefully():
    bars = synthetic_ohlcv(3, seed=12)
    card = analyze("SIM/USDT", bars)
    assert card.direction == "NEUTRAL"


def test_analyze_uses_regime_router_by_default():
    from signalcore.feeds import synthetic_ohlcv as _syn

    bars = _syn(300, seed=20)
    card = analyze("SIM/USDT", bars, use_regime_router=True)
    assert 0.0 <= card.confidence <= 1.0


def test_analyze_can_disable_regime_router():
    from signalcore.feeds import synthetic_ohlcv as _syn

    bars = _syn(300, seed=21)
    card = analyze("SIM/USDT", bars, use_regime_router=False)
    assert 0.0 <= card.confidence <= 1.0


def test_analyze_populates_risk_when_directional():
    from signalcore.feeds import synthetic_ohlcv as _syn

    bars = _syn(300, seed=30)
    card = analyze("SIM/USDT", bars)
    assert "size_pct" in card.risk
    if card.direction in ("LONG", "SHORT"):
        assert card.risk["stop"] is not None
        assert card.risk["size_pct"] >= 0.0
    else:
        assert card.risk["size_pct"] == 0.0


def test_analyze_populates_patterns():
    from signalcore.feeds import synthetic_ohlcv as _syn

    bars = _syn(300, seed=40)
    card = analyze("SIM/USDT", bars)
    assert isinstance(card.patterns, list)
    # sentetik seride formasyon olsun/olmasin -- tip ve kart butunlugu bozulmamali
    for p in card.patterns:
        assert p.direction in ("bull", "bear", "neutral")


def test_analyze_can_disable_patterns():
    from signalcore.feeds import synthetic_ohlcv as _syn

    bars = _syn(300, seed=41)
    card = analyze("SIM/USDT", bars, use_patterns=False)
    assert card.patterns == []
    names = [v.name for v in card.votes]
    assert "patterns" not in names


def test_analyze_includes_sensor_votes():
    from signalcore.feeds import synthetic_ohlcv as _syn
    from signalcore.indicators.derivatives import SimDerivativesFeed
    from signalcore.indicators.orderbook import SimOrderbookFeed

    bars = _syn(300, seed=50)
    sensor_states = {
        "derivatives": SimDerivativesFeed(seed=1).latest("SIM"),
        "orderbook": SimOrderbookFeed(seed=2).latest("SIM"),
    }
    card = analyze("SIM/USDT", bars, sensor_states=sensor_states)
    names = [v.name for v in card.votes]
    assert "derivatives" in names
    assert "orderbook" in names


def test_analyze_without_sensor_states_unaffected():
    from signalcore.feeds import synthetic_ohlcv as _syn

    bars = _syn(300, seed=51)
    card = analyze("SIM/USDT", bars, sensor_states=None)
    names = [v.name for v in card.votes]
    assert "derivatives" not in names
