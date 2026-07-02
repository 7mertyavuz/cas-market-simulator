from datetime import datetime, timezone

from cas_market_simulator.adapters.contracts import FlowState, SentimentState
from cas_market_simulator.adapters.factor_brain import SignalCoreFactorBrain
from signalcore.feeds import synthetic_ohlcv


def test_returns_neutral_when_not_enough_bars():
    brain = SignalCoreFactorBrain(min_bars=60)
    bars = synthetic_ohlcv(10, seed=1)
    card = brain.analyze("SIM/USDT", bars, {})
    assert card.direction == "NEUTRAL"
    assert card.confidence == 0.0


def test_analyze_returns_valid_card():
    brain = SignalCoreFactorBrain(min_bars=30)
    bars = synthetic_ohlcv(300, seed=2)
    card = brain.analyze("SIM/USDT", bars, {})
    assert card.direction in ("LONG", "SHORT", "NEUTRAL")
    assert 0.0 <= card.confidence <= 1.0
    assert len(card.votes) >= 6  # 6 cekirdek faktor + olasi patterns


def test_analyze_includes_sentiment_as_low_weight_vote():
    brain = SignalCoreFactorBrain(min_bars=30, extra_weight=0.15)
    bars = synthetic_ohlcv(300, seed=3)
    sentiment = SentimentState(entity="SIM", polarity=0.8, intensity=50.0)
    card = brain.analyze("SIM/USDT", bars, {"sentiment": sentiment})
    sentiment_votes = [v for v in card.votes if v.name == "sentiment"]
    assert len(sentiment_votes) == 1
    assert sentiment_votes[0].weight == 0.15
    assert sentiment_votes[0].vote > 0


def test_analyze_includes_flow_as_low_weight_vote():
    brain = SignalCoreFactorBrain(min_bars=30, extra_weight=0.15)
    bars = synthetic_ohlcv(300, seed=4)
    flow = FlowState(token="SIM", flow_imbalance=-0.6, vpin_toxicity=0.2, whale_net_usd=0.0)
    card = brain.analyze("SIM/USDT", bars, {"flow": flow})
    flow_votes = [v for v in card.votes if v.name == "flow"]
    assert len(flow_votes) == 1
    assert flow_votes[0].vote < 0


def test_analyze_includes_crowd_emergence_scalar():
    brain = SignalCoreFactorBrain(min_bars=30)
    bars = synthetic_ohlcv(300, seed=5)
    card = brain.analyze("SIM/USDT", bars, {"crowd_emergence": 0.5})
    ce_votes = [v for v in card.votes if v.name == "crowd_emergence"]
    assert len(ce_votes) == 1
    assert ce_votes[0].vote == 0.5


def test_analyze_card_uses_sim_contract_types():
    from cas_market_simulator.adapters.contracts import Card as SimCard
    from cas_market_simulator.adapters.contracts import FactorVote as SimFactorVote

    brain = SignalCoreFactorBrain(min_bars=30)
    bars = synthetic_ohlcv(300, seed=6)
    card = brain.analyze("SIM/USDT", bars, {})
    assert isinstance(card, SimCard)
    assert all(isinstance(v, SimFactorVote) for v in card.votes)


def test_analyze_extra_factors_none_ok():
    brain = SignalCoreFactorBrain(min_bars=30)
    bars = synthetic_ohlcv(300, seed=7)
    card = brain.analyze("SIM/USDT", bars, None)
    assert card.direction in ("LONG", "SHORT", "NEUTRAL")
