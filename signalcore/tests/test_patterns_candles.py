from datetime import datetime, timedelta, timezone

from signalcore.core.types import OHLCVBar
from signalcore.patterns.candles import (
    detect_all_candles,
    detect_doji,
    detect_engulfing,
    detect_hammer_shooting_star,
    detect_morning_evening_star,
)

T0 = datetime(2026, 1, 1, tzinfo=timezone.utc)


def bar(i, o, h, l, c, v=100):
    return OHLCVBar(ts=T0 + timedelta(minutes=i), open=o, high=h, low=l, close=c, volume=v)


def test_bullish_engulfing_detected():
    bars = [
        bar(0, 100, 101, 98, 99),    # bear, govde=1
        bar(1, 98.5, 103, 98, 102),  # bull, govde=3.5, oncekini sarar
    ]
    hit = detect_engulfing(bars)
    assert hit is not None
    assert hit.name == "bullish_engulfing"
    assert hit.direction == "bull"


def test_bearish_engulfing_detected():
    bars = [
        bar(0, 99, 101, 98, 100),     # bull, govde=1
        bar(1, 100.5, 101, 96, 97),   # bear, govde=3.5, oncekini sarar
    ]
    hit = detect_engulfing(bars)
    assert hit is not None
    assert hit.name == "bearish_engulfing"
    assert hit.direction == "bear"


def test_no_engulfing_when_body_too_small():
    bars = [
        bar(0, 100, 105, 95, 104),   # buyuk govde
        bar(1, 104.2, 104.5, 103.5, 104.1),  # kucuk govde, sarma yok
    ]
    assert detect_engulfing(bars) is None


def test_hammer_detected_after_downtrend():
    downtrend = [bar(i, 110 - i, 110 - i + 0.5, 109 - i, 109.2 - i) for i in range(5)]
    hammer = bar(5, 105, 105.3, 100, 105.1)  # uzun alt fitil, kucuk govde
    bars = downtrend + [hammer]
    hit = detect_hammer_shooting_star(bars)
    assert hit is not None
    assert hit.name == "hammer"
    assert hit.direction == "bull"


def test_shooting_star_detected_after_uptrend():
    uptrend = [bar(i, 100 + i, 101 + i, 99.5 + i, 100.8 + i) for i in range(5)]
    star = bar(5, 105, 110, 104.8, 105.2)  # uzun ust fitil
    bars = uptrend + [star]
    hit = detect_hammer_shooting_star(bars)
    assert hit is not None
    assert hit.name == "shooting_star"
    assert hit.direction == "bear"


def test_doji_detected():
    bars = [bar(0, 100, 102, 98, 100.05)]
    hit = detect_doji(bars)
    assert hit is not None
    assert hit.direction == "neutral"


def test_doji_not_detected_for_large_body():
    bars = [bar(0, 100, 105, 95, 104)]
    assert detect_doji(bars) is None


def test_morning_star_detected():
    bars = [
        bar(0, 105, 106, 100, 101),   # buyuk bear
        bar(1, 100.5, 101, 99.5, 100.7),  # kucuk govde
        bar(2, 101, 105, 100.5, 104.5),   # buyuk bull, geri alir
    ]
    hit = detect_morning_evening_star(bars)
    assert hit is not None
    assert hit.name == "morning_star"


def test_evening_star_detected():
    bars = [
        bar(0, 100, 106, 99, 105),        # buyuk bull
        bar(1, 105.2, 105.8, 104.8, 105.3),  # kucuk govde
        bar(2, 105, 101, 100, 101.5),      # buyuk bear, geri alir
    ]
    hit = detect_morning_evening_star(bars)
    assert hit is not None
    assert hit.name == "evening_star"


def test_detect_all_candles_returns_list():
    bars = [bar(0, 100, 102, 98, 100.05)]
    hits = detect_all_candles(bars)
    assert isinstance(hits, list)
    assert any(h.name == "doji" for h in hits)
