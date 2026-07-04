from datetime import datetime, timezone

from cas_market_simulator.adapters.contracts import (
    Card,
    FactorVote,
    FlowState,
    PatternHit,
    SentimentState,
    ShockEvent,
)


def test_card_defaults():
    card = Card(symbol="BTC/USDT", direction="NEUTRAL", confidence=0.0)
    assert card.votes == []
    assert card.patterns == []
    assert card.risk == {}


def test_factor_vote_roundtrip():
    v = FactorVote(name="trend", vote=0.4, weight=1.0)
    assert v.market == "crypto"


def test_pattern_hit_optional_invalidation():
    p = PatternHit(name="engulfing", direction="bull", strength=0.7)
    assert p.invalidation is None


def test_sentiment_state_defaults():
    s = SentimentState(entity="BTC", polarity=0.1, intensity=5.0)
    assert s.emotion == {}
    assert s.fed_tone is None


def test_shock_event_fields():
    e = ShockEvent(kind="panic", entity="BTC", magnitude=0.8, decay_halflife_s=300.0)
    assert e.kind == "panic"


def test_flow_state_defaults():
    f = FlowState(token="BTC", flow_imbalance=0.0, vpin_toxicity=0.1, whale_net_usd=0.0)
    assert f.regime == "normal"
