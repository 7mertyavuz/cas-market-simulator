from datetime import datetime, timezone

from cas_market_simulator.adapters.flow_feed import SimFlowFeed
from cas_market_simulator.adapters.sentiment_feed import SimSentimentFeed


def test_sim_sentiment_feed_bounds():
    feed = SimSentimentFeed(seed=1)
    for _ in range(50):
        s = feed.latest("BTC")
        assert -1.0 <= s.polarity <= 1.0
        assert 0.0 <= s.intensity <= 100.0
        assert 0.0 <= s.confidence <= 1.0
        for v in s.emotion.values():
            assert 0.0 <= v <= 1.0


def test_sim_sentiment_feed_deterministic_with_seed():
    a = SimSentimentFeed(seed=42)
    b = SimSentimentFeed(seed=42)
    seq_a = [a.latest("BTC").polarity for _ in range(20)]
    seq_b = [b.latest("BTC").polarity for _ in range(20)]
    assert seq_a == seq_b


def test_sim_sentiment_feed_evolves_over_calls():
    feed = SimSentimentFeed(seed=3)
    values = [feed.latest("BTC").polarity for _ in range(10)]
    assert len(set(values)) > 1  # sabit kalmiyor, evrim gecikiyor


def test_sim_sentiment_feed_shocks_bounded_probability():
    feed = SimSentimentFeed(seed=5, shock_probability=1.0)  # her zaman sok uret
    shocks = feed.shocks(datetime.now(timezone.utc))
    assert len(shocks) == 1
    assert shocks[0].kind in ("panic", "euphoria")
    assert 0.0 <= shocks[0].magnitude <= 1.0


def test_sim_sentiment_feed_no_shocks_when_probability_zero():
    feed = SimSentimentFeed(seed=6, shock_probability=0.0)
    assert feed.shocks(datetime.now(timezone.utc)) == []


def test_sim_flow_feed_bounds():
    feed = SimFlowFeed(seed=1)
    for _ in range(50):
        f = feed.latest("BTC")
        assert -1.0 <= f.flow_imbalance <= 1.0
        assert 0.0 <= f.vpin_toxicity <= 1.0
        assert f.regime in ("normal", "toxic", "highvol")
        assert abs(sum(f.actor_mix.values()) - 1.0) < 1e-6


def test_sim_flow_feed_deterministic_with_seed():
    a = SimFlowFeed(seed=9)
    b = SimFlowFeed(seed=9)
    seq_a = [a.latest("BTC").flow_imbalance for _ in range(20)]
    seq_b = [b.latest("BTC").flow_imbalance for _ in range(20)]
    assert seq_a == seq_b


def test_sim_flow_feed_direction_prob_bounds():
    feed = SimFlowFeed(seed=2)
    for _ in range(30):
        f = feed.latest("BTC")
        assert 0.0 <= f.direction_prob_up <= 1.0
