"""Mum formasyonlari: engulfing, hammer/shooting-star, doji, morning/evening star.

Her fonksiyon barlarin SON birkacini inceler ve bulursa bir
`PatternHit`, bulamazsa `None` doner. Kurallar parametrik esikler
kullanir (sezgiyle "gozle gordum" degil) -- bkz. 03-PROMPT Bolum 4.
"""
from __future__ import annotations

from ..core.types import OHLCVBar, PatternHit


def _body(bar: OHLCVBar) -> float:
    return abs(bar.close - bar.open)


def _range(bar: OHLCVBar) -> float:
    return max(bar.high - bar.low, 1e-12)


def _upper_wick(bar: OHLCVBar) -> float:
    return bar.high - max(bar.open, bar.close)


def _lower_wick(bar: OHLCVBar) -> float:
    return min(bar.open, bar.close) - bar.low


def _is_bull(bar: OHLCVBar) -> bool:
    return bar.close > bar.open


def detect_engulfing(bars: list[OHLCVBar], *, min_body_ratio: float = 1.05) -> PatternHit | None:
    """Onceki mumun govdesini tamamen kapsayan, ters yonlu buyuk govde."""
    if len(bars) < 2:
        return None
    prev, cur = bars[-2], bars[-1]
    prev_body = _body(prev)
    cur_body = _body(cur)
    if prev_body == 0 or cur_body < prev_body * min_body_ratio:
        return None

    bull_engulf = (
        not _is_bull(prev) and _is_bull(cur)
        and cur.open <= prev.close and cur.close >= prev.open
    )
    bear_engulf = (
        _is_bull(prev) and not _is_bull(cur)
        and cur.open >= prev.close and cur.close <= prev.open
    )

    if bull_engulf:
        strength = min(1.0, cur_body / (prev_body * 2))
        return PatternHit(name="bullish_engulfing", direction="bull", strength=strength, invalidation=cur.low)
    if bear_engulf:
        strength = min(1.0, cur_body / (prev_body * 2))
        return PatternHit(name="bearish_engulfing", direction="bear", strength=strength, invalidation=cur.high)
    return None


def detect_hammer_shooting_star(
    bars: list[OHLCVBar],
    *,
    wick_to_body_ratio: float = 2.0,
    opposite_wick_max_ratio: float = 0.3,
    trend_lookback: int = 5,
) -> PatternHit | None:
    """Hammer: dusen trend sonrasi uzun alt fitil (tepki/donus). Shooting
    star: yukselen trend sonrasi uzun ust fitil."""
    if len(bars) < trend_lookback + 1:
        return None
    cur = bars[-1]
    body = _body(cur)
    if body == 0:
        return None
    rng = _range(cur)

    prior_close = bars[-trend_lookback - 1].close
    prior_trend_down = cur.close < prior_close
    prior_trend_up = cur.close > prior_close

    lower = _lower_wick(cur)
    upper = _upper_wick(cur)

    is_hammer_shape = lower >= body * wick_to_body_ratio and upper <= rng * opposite_wick_max_ratio
    is_star_shape = upper >= body * wick_to_body_ratio and lower <= rng * opposite_wick_max_ratio

    if is_hammer_shape and prior_trend_down:
        strength = min(1.0, lower / (body * wick_to_body_ratio * 2))
        return PatternHit(name="hammer", direction="bull", strength=strength, invalidation=cur.low)
    if is_star_shape and prior_trend_up:
        strength = min(1.0, upper / (body * wick_to_body_ratio * 2))
        return PatternHit(name="shooting_star", direction="bear", strength=strength, invalidation=cur.high)
    return None


def detect_doji(bars: list[OHLCVBar], *, max_body_to_range_ratio: float = 0.1) -> PatternHit | None:
    """Govde, toplam bar araliginin kucuk bir kesri (kararsizlik)."""
    if not bars:
        return None
    cur = bars[-1]
    rng = _range(cur)
    body = _body(cur)
    if body / rng <= max_body_to_range_ratio:
        strength = 1.0 - (body / rng) / max_body_to_range_ratio
        return PatternHit(name="doji", direction="neutral", strength=max(0.0, min(1.0, strength)), invalidation=None)
    return None


def detect_morning_evening_star(
    bars: list[OHLCVBar],
    *,
    star_body_max_ratio: float = 0.4,
) -> PatternHit | None:
    """3 barlik donus formasyonu: buyuk govde -> kucuk govde (star) -> ters
    yonlu buyuk govde, ilk barin gucunu geri alan."""
    if len(bars) < 3:
        return None
    first, star, third = bars[-3], bars[-2], bars[-1]
    first_body, star_body, third_body = _body(first), _body(star), _body(third)
    if first_body == 0 or third_body == 0:
        return None
    if star_body > first_body * star_body_max_ratio:
        return None  # ortadaki bar 'kucuk govdeli' degil

    morning = (
        not _is_bull(first) and _is_bull(third)
        and third.close > (first.open + first.close) / 2
    )
    evening = (
        _is_bull(first) and not _is_bull(third)
        and third.close < (first.open + first.close) / 2
    )

    if morning:
        strength = min(1.0, third_body / first_body)
        return PatternHit(name="morning_star", direction="bull", strength=strength, invalidation=min(first.low, star.low, third.low))
    if evening:
        strength = min(1.0, third_body / first_body)
        return PatternHit(name="evening_star", direction="bear", strength=strength, invalidation=max(first.high, star.high, third.high))
    return None


def detect_all_candles(bars: list[OHLCVBar]) -> list[PatternHit]:
    hits = []
    for fn in (detect_engulfing, detect_hammer_shooting_star, detect_doji, detect_morning_evening_star):
        hit = fn(bars)
        if hit is not None:
            hits.append(hit)
    return hits
