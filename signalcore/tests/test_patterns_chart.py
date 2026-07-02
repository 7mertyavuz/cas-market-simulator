from datetime import datetime, timedelta, timezone

from signalcore.core.types import OHLCVBar
from signalcore.patterns.chart import (
    detect_all_chart_patterns,
    detect_double_bottom,
    detect_double_top,
    detect_flag_or_wedge,
    detect_head_and_shoulders,
    detect_triangle,
)
from signalcore.patterns.levels import (
    classic_pivot_points,
    find_swing_points,
    nearest_liquidity_levels,
    support_resistance,
)

T0 = datetime(2026, 1, 1, tzinfo=timezone.utc)


def zigzag_bars(anchors: list[float], bars_per_leg: int = 4) -> list[OHLCVBar]:
    """anchors arasinda dogrusal interpolasyonla bar dizisi uretir --
    her anchor bir yerel tepe/dip olur (swing noktasi testleri icin)."""
    bars: list[OHLCVBar] = []
    idx = 0
    prev_price = anchors[0]
    for leg_i in range(len(anchors) - 1):
        start, end = anchors[leg_i], anchors[leg_i + 1]
        for step in range(1, bars_per_leg + 1):
            price = start + (end - start) * step / bars_per_leg
            o = prev_price
            c = price
            h = c + 0.01
            l = c - 0.01
            bars.append(OHLCVBar(ts=T0 + timedelta(minutes=idx), open=o, high=h, low=l, close=c, volume=100))
            prev_price = price
            idx += 1
    return bars


def test_double_top_detected():
    # 100 -> 120 (tepe1) -> 105 (dip) -> 120 (tepe2, benzer) -> 108
    bars = zigzag_bars([100, 120, 105, 120, 108], bars_per_leg=4)
    hit = detect_double_top(bars, order=2)
    assert hit is not None
    assert hit.direction == "bear"


def test_double_bottom_detected():
    bars = zigzag_bars([120, 100, 115, 100, 112], bars_per_leg=4)
    hit = detect_double_bottom(bars, order=2)
    assert hit is not None
    assert hit.direction == "bull"


def test_no_double_top_when_peaks_differ_too_much():
    bars = zigzag_bars([100, 120, 105, 140, 108], bars_per_leg=4)
    hit = detect_double_top(bars, order=2)
    assert hit is None


def test_head_and_shoulders_detected():
    # sol omuz(110) - bas(130) - sag omuz(111), aralarinda dipler
    bars = zigzag_bars([100, 110, 95, 130, 96, 111, 90], bars_per_leg=4)
    hit = detect_head_and_shoulders(bars, order=2)
    assert hit is not None
    assert hit.name == "head_and_shoulders"
    assert hit.direction == "bear"


def test_inverse_head_and_shoulders_detected():
    bars = zigzag_bars([120, 110, 130, 90, 129, 109, 135], bars_per_leg=4)
    hit = detect_head_and_shoulders(bars, order=2)
    assert hit is not None
    assert hit.name == "inverse_head_and_shoulders"
    assert hit.direction == "bull"


def test_ascending_triangle_detected():
    # ust seviye sabit (~130), alt seviye yukseliyor
    bars = zigzag_bars([100, 130, 110, 129, 118, 130, 122], bars_per_leg=4)
    hit = detect_triangle(bars, order=2)
    assert hit is not None
    assert hit.name in ("ascending_triangle", "symmetric_triangle")


def test_bull_flag_detected():
    # guclu yukselis (impuls) + daralan konsolidasyon
    impulse = [100 + i * 2 for i in range(20)]  # 100 -> 138
    consolidation = [138 + ((-1) ** i) * 0.5 for i in range(10)]
    closes = impulse + consolidation
    bars = []
    prev = closes[0]
    for i, c in enumerate(closes):
        o = prev
        h = max(o, c) + 0.2
        l = min(o, c) - 0.2
        bars.append(OHLCVBar(ts=T0 + timedelta(minutes=i), open=o, high=h, low=l, close=c, volume=100))
        prev = c
    hit = detect_flag_or_wedge(bars, impulse_lookback=20, consolidation_window=10)
    assert hit is not None
    assert hit.direction == "bull"


def test_detect_all_chart_patterns_returns_list():
    bars = zigzag_bars([100, 120, 105, 120, 108], bars_per_leg=4)
    hits = detect_all_chart_patterns(bars, order=2)
    assert isinstance(hits, list)


def test_find_swing_points_basic():
    bars = zigzag_bars([100, 120, 105, 118, 108], bars_per_leg=4)
    swings = find_swing_points(bars, order=2)
    assert any(s.kind == "high" for s in swings)
    assert any(s.kind == "low" for s in swings)


def test_support_resistance_requires_min_touches():
    bars = zigzag_bars([100, 120, 105, 120, 108, 121, 106], bars_per_leg=4)
    levels = support_resistance(bars, order=2, min_touches=2)
    assert all(lv.touches >= 2 for lv in levels)


def test_classic_pivot_points():
    bars = zigzag_bars([100, 110], bars_per_leg=3)
    pivots = classic_pivot_points(bars)
    assert pivots is not None
    assert pivots.r1 > pivots.pivot > pivots.s1


def test_classic_pivot_points_empty_bars():
    assert classic_pivot_points([]) is None


def test_nearest_liquidity_levels_shape():
    bars = zigzag_bars([100, 120, 105, 120, 108, 121, 106], bars_per_leg=4)
    result = nearest_liquidity_levels(bars, current_price=110, order=2)
    assert "nearest_support" in result
    assert "nearest_resistance" in result
