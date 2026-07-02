from signalcore.combine.aggregator import aggregate
from signalcore.core.types import FactorVote


def test_aggregate_empty_neutral():
    r = aggregate([])
    assert r.direction == "NEUTRAL"
    assert r.confidence == 0.0


def test_aggregate_strong_agreement_long():
    votes = [FactorVote(name="a", vote=0.8, weight=1.0), FactorVote(name="b", vote=0.9, weight=1.0)]
    r = aggregate(votes)
    assert r.direction == "LONG"
    assert r.confidence > 0.5


def test_aggregate_conflicting_votes_lower_confidence():
    votes = [FactorVote(name="a", vote=0.9, weight=1.0), FactorVote(name="b", vote=-0.9, weight=1.0)]
    r = aggregate(votes)
    assert r.direction == "NEUTRAL"  # cancel out -> near zero raw_score


def test_aggregate_within_neutral_band():
    votes = [FactorVote(name="a", vote=0.05, weight=1.0)]
    r = aggregate(votes, neutral_band=0.1)
    assert r.direction == "NEUTRAL"


def test_aggregate_weight_zero_total_neutral():
    votes = [FactorVote(name="a", vote=0.9, weight=0.0)]
    r = aggregate(votes)
    assert r.direction == "NEUTRAL"


def test_aggregate_short_direction():
    votes = [FactorVote(name="a", vote=-0.8, weight=1.0)]
    r = aggregate(votes)
    assert r.direction == "SHORT"
