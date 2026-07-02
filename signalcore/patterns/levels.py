"""Destek/direnc, pivot, likidite seviyeleri.

`find_swing_points` diger tum grafik formasyon detektorlerinin (chart.py)
temelidir -- yerel tepe/dip noktalarini bulur. Kurallar parametrik:
bir bar, kendisinden `order` bar once ve sonraki barlarin hepsinden
yuksek/dusukse swing high/low sayilir.
"""
from __future__ import annotations

from dataclasses import dataclass

from ..core.ohlcv import to_arrays
from ..core.types import OHLCVBar


@dataclass
class SwingPoint:
    index: int
    price: float
    kind: str   # "high" | "low"


@dataclass
class SupportResistanceLevel:
    price: float
    touches: int
    kind: str   # "support" | "resistance"


@dataclass
class PivotPoints:
    pivot: float
    r1: float
    r2: float
    s1: float
    s2: float


def find_swing_points(bars: list[OHLCVBar], *, order: int = 3) -> list[SwingPoint]:
    arrs = to_arrays(bars)
    high, low = arrs["high"], arrs["low"]
    n = len(bars)
    points: list[SwingPoint] = []

    for i in range(order, n - order):
        window_high = high[i - order: i + order + 1]
        window_low = low[i - order: i + order + 1]
        if high[i] == window_high.max() and (window_high == window_high.max()).sum() == 1:
            points.append(SwingPoint(index=i, price=float(high[i]), kind="high"))
        if low[i] == window_low.min() and (window_low == window_low.min()).sum() == 1:
            points.append(SwingPoint(index=i, price=float(low[i]), kind="low"))

    return points


def support_resistance(
    bars: list[OHLCVBar],
    *,
    order: int = 3,
    cluster_tolerance_pct: float = 0.005,
    min_touches: int = 2,
) -> list[SupportResistanceLevel]:
    """Swing noktalarini fiyat yakinligina gore kumeler; en az `min_touches`
    kez dokunulan seviyeleri destek/direnc olarak doner."""
    swings = find_swing_points(bars, order=order)
    if not swings:
        return []

    levels: list[SupportResistanceLevel] = []
    for kind in ("high", "low"):
        points = sorted([s.price for s in swings if s.kind == kind])
        if not points:
            continue
        cluster = [points[0]]
        for p in points[1:]:
            if abs(p - cluster[-1]) / max(cluster[-1], 1e-9) <= cluster_tolerance_pct:
                cluster.append(p)
            else:
                if len(cluster) >= min_touches:
                    levels.append(
                        SupportResistanceLevel(
                            price=sum(cluster) / len(cluster),
                            touches=len(cluster),
                            kind="resistance" if kind == "high" else "support",
                        )
                    )
                cluster = [p]
        if len(cluster) >= min_touches:
            levels.append(
                SupportResistanceLevel(
                    price=sum(cluster) / len(cluster),
                    touches=len(cluster),
                    kind="resistance" if kind == "high" else "support",
                )
            )
    return levels


def classic_pivot_points(bars: list[OHLCVBar]) -> PivotPoints | None:
    """Son tamamlanmis bardan klasik (floor trader) pivot noktalari."""
    if not bars:
        return None
    last = bars[-1]
    pivot = (last.high + last.low + last.close) / 3.0
    r1 = 2 * pivot - last.low
    s1 = 2 * pivot - last.high
    r2 = pivot + (last.high - last.low)
    s2 = pivot - (last.high - last.low)
    return PivotPoints(pivot=pivot, r1=r1, r2=r2, s1=s1, s2=s2)


def nearest_liquidity_levels(
    bars: list[OHLCVBar], current_price: float, *, order: int = 3, cluster_tolerance_pct: float = 0.005
) -> dict:
    """Guncel fiyata en yakin destek (asagida) ve direnc (yukarida) seviyesi."""
    levels = support_resistance(bars, order=order, cluster_tolerance_pct=cluster_tolerance_pct, min_touches=2)
    supports = sorted([lv.price for lv in levels if lv.kind == "support" and lv.price < current_price], reverse=True)
    resistances = sorted([lv.price for lv in levels if lv.kind == "resistance" and lv.price > current_price])
    return {
        "nearest_support": supports[0] if supports else None,
        "nearest_resistance": resistances[0] if resistances else None,
    }
