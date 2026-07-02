"""Risk seviyeleri: ATR-stop, TP, gecersizlik.

Kural: seviyeler her zaman GORUNUR ve parametrik olmali (sezgiyle
"buraya koy" degil). ATR carpanlari varsayilan degerlerdir, disaridan
override edilebilir.
"""
from __future__ import annotations

from dataclasses import dataclass

from ..core.ohlcv import to_arrays
from ..core.types import OHLCVBar
from ..indicators import _math


@dataclass
class RiskLevels:
    entry: float
    stop: float
    take_profit: float
    invalidation: float
    atr: float
    direction: str   # "LONG" | "SHORT"


def atr_stop_tp(
    bars: list[OHLCVBar],
    direction: str,
    *,
    atr_period: int = 14,
    stop_mult: float = 1.5,
    tp_mult: float = 3.0,
) -> RiskLevels | None:
    """direction 'LONG' ise stop asagida/TP yukarida, 'SHORT' ise tersi.
    'NEUTRAL' icin None doner (risk seviyesi tanimsiz)."""
    if direction not in ("LONG", "SHORT"):
        return None

    arrs = to_arrays(bars)
    close, high, low = arrs["close"], arrs["high"], arrs["low"]
    if len(close) < atr_period + 2:
        return None

    atr_vals = _math.atr(high, low, close, atr_period)
    atr_last = atr_vals[-1]
    if atr_last != atr_last:  # NaN kontrolu
        return None

    entry = float(close[-1])

    if direction == "LONG":
        stop = entry - stop_mult * atr_last
        tp = entry + tp_mult * atr_last
        invalidation = stop
    else:
        stop = entry + stop_mult * atr_last
        tp = entry - tp_mult * atr_last
        invalidation = stop

    return RiskLevels(
        entry=entry,
        stop=float(stop),
        take_profit=float(tp),
        invalidation=float(invalidation),
        atr=float(atr_last),
        direction=direction,
    )


def to_risk_dict(size_pct: float, levels: RiskLevels | None) -> dict:
    """Card.risk alanina konacak sozluk (00-ORTAK-SOZLESME.md: {"size_pct","stop","tp","cvar",...})."""
    if levels is None:
        return {"size_pct": 0.0, "stop": None, "tp": None, "invalidation": None}
    return {
        "size_pct": size_pct,
        "stop": levels.stop,
        "tp": levels.take_profit,
        "invalidation": levels.invalidation,
        "atr": levels.atr,
    }
