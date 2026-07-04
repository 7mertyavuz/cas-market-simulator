from datetime import datetime, timezone

from cas_market_simulator.adapters.factor_brain import StubFactorBrain
from cas_market_simulator.adapters.flow_feed import StubFlowFeed
from cas_market_simulator.adapters.sentiment_feed import StubSentimentFeed


def test_stub_sentiment_feed_latest():
    feed = StubSentimentFeed()
    s = feed.latest("BTC")
    assert s.entity == "BTC"
    assert -1.0 <= s.polarity <= 1.0


def test_stub_sentiment_feed_shocks_empty():
    feed = StubSentimentFeed()
    assert feed.shocks(datetime.now(timezone.utc)) == []


def test_stub_flow_feed_latest():
    feed = StubFlowFeed()
    f = feed.latest("BTC")
    assert f.token == "BTC"
    assert sum(f.actor_mix.values()) == 1.0


def test_stub_factor_brain_neutral():
    brain = StubFactorBrain()
    card = brain.analyze("BTC/USDT", None, {})
    assert card.direction == "NEUTRAL"
    assert card.confidence == 0.0
