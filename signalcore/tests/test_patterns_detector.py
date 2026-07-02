from datetime import datetime, timedelta, timezone

from signalcore.core.types import FactorVote, OHLCVBar, PatternHit
from signalcore.patterns.detector import detect_patterns, patterns_to_vote

T0 = datetime(2026, 1, 1, tzinfo=timezone.utc)


def bar(i, o, h, l, c, v=100):
    return OHLCVBar(ts=T0 + timedelta(minutes=i), open=o, high=h, low=l, close=c, volume=v)


def test_detect_patterns_finds_doji():
    bars = [bar(0, 100, 102, 98, 100.05)]
    hits = detect_patterns(bars)
    assert any(h.name == "doji" for h in hits)


def test_patterns_to_vote_empty_neutral():
    v = patterns_to_vote([])
    assert v.vote == 0.0
    assert v.name == "patterns"


def test_patterns_to_vote_bullish_dominant():
    hits = [
        PatternHit(name="hammer", direction="bull", strength=0.8),
        PatternHit(name="doji", direction="neutral", strength=0.2),
    ]
    v = patterns_to_vote(hits)
    assert v.vote > 0


def test_patterns_to_vote_conflicting_cancel_out():
    hits = [
        PatternHit(name="bullish_engulfing", direction="bull", strength=0.5),
        PatternHit(name="bearish_engulfing", direction="bear", strength=0.5),
    ]
    v = patterns_to_vote(hits)
    assert abs(v.vote) < 1e-9
