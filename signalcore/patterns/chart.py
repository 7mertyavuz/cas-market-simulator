"""Grafik formasyonlari: cift dip/tepe, ucgen, omuz-bas-omuz, bayrak/kama.

Hepsi `patterns/levels.py::find_swing_points` uzerine kuruludur --
"gozle gordum" sezgisi degil, parametrik swing-noktasi geometrisi.
Her formasyon `PatternHit(name, direction, strength, invalidation)`
doner; `invalidation`, formasyonun bozuldugu kabul edilen fiyattir.
"""
from __future__ import annotations

import numpy as np

from ..core.ohlcv import to_arrays
from ..core.types import OHLCVBar, PatternHit
from .levels import SwingPoint, find_swing_points


def _swings_by_kind(swings: list[SwingPoint], kind: str) -> list[SwingPoint]:
    return [s for s in swings if s.kind == kind]


def detect_double_top(
    bars: list[OHLCVBar], *, order: int = 3, tolerance_pct: float = 0.015
) -> PatternHit | None:
    swings = find_swing_points(bars, order=order)
    highs = _swings_by_kind(swings, "high")
    lows = _swings_by_kind(swings, "low")
    if len(highs) < 2 or not lows:
        return None

    h1, h2 = highs[-2], highs[-1]
    between_lows = [l for l in lows if h1.index < l.index < h2.index]
    if not between_lows:
        return None
    trough = min(between_lows, key=lambda l: l.price)

    similar = abs(h1.price - h2.price) / max(h1.price, 1e-9) <= tolerance_pct
    valley_deep_enough = trough.price < min(h1.price, h2.price) * (1 - tolerance_pct)

    if similar and valley_deep_enough:
        strength = 1.0 - abs(h1.price - h2.price) / max(h1.price, 1e-9) / tolerance_pct
        return PatternHit(
            name="double_top", direction="bear",
            strength=max(0.0, min(1.0, strength)),
            invalidation=max(h1.price, h2.price),
        )
    return None


def detect_double_bottom(
    bars: list[OHLCVBar], *, order: int = 3, tolerance_pct: float = 0.015
) -> PatternHit | None:
    swings = find_swing_points(bars, order=order)
    lows = _swings_by_kind(swings, "low")
    highs = _swings_by_kind(swings, "high")
    if len(lows) < 2 or not highs:
        return None

    l1, l2 = lows[-2], lows[-1]
    between_highs = [h for h in highs if l1.index < h.index < l2.index]
    if not between_highs:
        return None
    peak = max(between_highs, key=lambda h: h.price)

    similar = abs(l1.price - l2.price) / max(l1.price, 1e-9) <= tolerance_pct
    peak_high_enough = peak.price > max(l1.price, l2.price) * (1 + tolerance_pct)

    if similar and peak_high_enough:
        strength = 1.0 - abs(l1.price - l2.price) / max(l1.price, 1e-9) / tolerance_pct
        return PatternHit(
            name="double_bottom", direction="bull",
            strength=max(0.0, min(1.0, strength)),
            invalidation=min(l1.price, l2.price),
        )
    return None


def detect_head_and_shoulders(
    bars: list[OHLCVBar], *, order: int = 3, shoulder_tolerance_pct: float = 0.03
) -> PatternHit | None:
    """Klasik (bearish) omuz-bas-omuz: sol omuz < bas > sag omuz, omuzlar
    birbirine yakin. Ters (bullish) icin diplerle simetrik mantik."""
    swings = find_swing_points(bars, order=order)
    highs = _swings_by_kind(swings, "high")
    lows = _swings_by_kind(swings, "low")

    if len(highs) >= 3:
        l_sh, head, r_sh = highs[-3], highs[-2], highs[-1]
        if head.price > l_sh.price and head.price > r_sh.price:
            shoulder_diff = abs(l_sh.price - r_sh.price) / max(l_sh.price, 1e-9)
            if shoulder_diff <= shoulder_tolerance_pct:
                neckline_points = [l for l in lows if l_sh.index < l.index < r_sh.index]
                neckline = min((p.price for p in neckline_points), default=min(l_sh.price, r_sh.price))
                strength = min(1.0, (head.price - max(l_sh.price, r_sh.price)) / max(head.price, 1e-9) * 10)
                return PatternHit(
                    name="head_and_shoulders", direction="bear",
                    strength=max(0.0, min(1.0, strength)), invalidation=neckline,
                )

    if len(lows) >= 3:
        l_sh, head, r_sh = lows[-3], lows[-2], lows[-1]
        if head.price < l_sh.price and head.price < r_sh.price:
            shoulder_diff = abs(l_sh.price - r_sh.price) / max(l_sh.price, 1e-9)
            if shoulder_diff <= shoulder_tolerance_pct:
                neckline_points = [h for h in highs if l_sh.index < h.index < r_sh.index]
                neckline = max((p.price for p in neckline_points), default=max(l_sh.price, r_sh.price))
                strength = min(1.0, (min(l_sh.price, r_sh.price) - head.price) / max(head.price, 1e-9) * 10)
                return PatternHit(
                    name="inverse_head_and_shoulders", direction="bull",
                    strength=max(0.0, min(1.0, strength)), invalidation=neckline,
                )
    return None


def detect_triangle(
    bars: list[OHLCVBar], *, order: int = 3, min_points: int = 2, flat_slope_pct: float = 0.001
) -> PatternHit | None:
    """Son birkac swing high/low uzerinden regresyon egimine bakar:
    ust egim < 0 & alt egim > 0 -> simetrik; ust~duz & alt egim>0 -> yukselen;
    ust egim<0 & alt~duz -> alcalan."""
    swings = find_swing_points(bars, order=order)
    highs = _swings_by_kind(swings, "high")[-max(min_points, 3):]
    lows = _swings_by_kind(swings, "low")[-max(min_points, 3):]
    if len(highs) < min_points or len(lows) < min_points:
        return None

    hx = np.array([h.index for h in highs], dtype=float)
    hy = np.array([h.price for h in highs], dtype=float)
    lx = np.array([l.index for l in lows], dtype=float)
    ly = np.array([l.price for l in lows], dtype=float)

    upper_slope = float(np.polyfit(hx, hy, 1)[0]) / max(np.mean(hy), 1e-9)
    lower_slope = float(np.polyfit(lx, ly, 1)[0]) / max(np.mean(ly), 1e-9)

    upper_falling = upper_slope < -flat_slope_pct
    upper_flat = abs(upper_slope) <= flat_slope_pct
    lower_rising = lower_slope > flat_slope_pct
    lower_flat = abs(lower_slope) <= flat_slope_pct

    last_price = bars[-1].close
    invalidation_up = float(hy[-1])
    invalidation_down = float(ly[-1])

    if upper_falling and lower_rising:
        return PatternHit(name="symmetric_triangle", direction="neutral", strength=0.5, invalidation=None)
    if upper_flat and lower_rising:
        return PatternHit(name="ascending_triangle", direction="bull", strength=0.6, invalidation=invalidation_down)
    if upper_falling and lower_flat:
        return PatternHit(name="descending_triangle", direction="bear", strength=0.6, invalidation=invalidation_up)
    return None


def detect_flag_or_wedge(
    bars: list[OHLCVBar],
    *,
    impulse_lookback: int = 20,
    consolidation_window: int = 10,
    impulse_min_move_pct: float = 0.05,
    contraction_max_ratio: float = 0.5,
) -> PatternHit | None:
    """Guclu bir hareket (impuls) sonrasi daralan bir konsolidasyon --
    bayrak/kama devam formasyonu. Yon, impuls yonunun devami olarak
    varsayilir (klasik devam formasyonu tanimi)."""
    n = len(bars)
    if n < impulse_lookback + consolidation_window:
        return None

    arrs = to_arrays(bars)
    close, high, low = arrs["close"], arrs["high"], arrs["low"]

    impulse_start = n - impulse_lookback - consolidation_window
    impulse_end = n - consolidation_window
    impulse_move = (close[impulse_end - 1] - close[impulse_start]) / max(close[impulse_start], 1e-9)

    if abs(impulse_move) < impulse_min_move_pct:
        return None

    impulse_range = np.max(high[impulse_start:impulse_end]) - np.min(low[impulse_start:impulse_end])
    consolidation_range = np.max(high[impulse_end:]) - np.min(low[impulse_end:])

    if impulse_range <= 0:
        return None
    contraction_ratio = consolidation_range / impulse_range
    if contraction_ratio > contraction_max_ratio:
        return None  # yeterince daralmadi

    direction = "bull" if impulse_move > 0 else "bear"
    name = "bull_flag" if direction == "bull" else "bear_flag"
    invalidation = float(np.min(low[impulse_end:])) if direction == "bull" else float(np.max(high[impulse_end:]))
    strength = max(0.0, min(1.0, 1.0 - contraction_ratio))
    return PatternHit(name=name, direction=direction, strength=strength, invalidation=invalidation)


def detect_all_chart_patterns(bars: list[OHLCVBar], *, order: int = 3) -> list[PatternHit]:
    hits = []
    for fn in (
        detect_double_top,
        detect_double_bottom,
        detect_head_and_shoulders,
        detect_triangle,
        detect_flag_or_wedge,
    ):
        try:
            hit = fn(bars, order=order) if fn is not detect_flag_or_wedge else fn(bars)
        except TypeError:
            hit = fn(bars)
        if hit is not None:
            hits.append(hit)
    return hits
