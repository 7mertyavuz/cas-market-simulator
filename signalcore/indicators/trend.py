"""Trend faktoru: EMA capraz + Supertrend + ADX.

Yon omurgasi (bkz. 03-PROMPT Bolum 3). ADX yon vermez, gucu (dolayisiyla
guven carpanini) belirler.
"""
from __future__ import annotations

import numpy as np

from ..core.ohlcv import to_arrays
from ..core.types import FactorVote, OHLCVBar
from . import _math


def trend_factor(
    bars: list[OHLCVBar],
    *,
    ema_fast: int = 12,
    ema_slow: int = 26,
    st_period: int = 10,
    st_mult: float = 3.0,
    adx_period: int = 14,
    weight: float = 1.0,
) -> FactorVote:
    arrs = to_arrays(bars)
    close, high, low = arrs["close"], arrs["high"], arrs["low"]

    if len(close) < max(ema_slow, st_period, adx_period) + 2:
        return FactorVote(name="trend", vote=0.0, weight=weight)

    fast = _math.ema(close, ema_fast)
    slow = _math.ema(close, ema_slow)
    ema_signal = 1.0 if fast[-1] > slow[-1] else -1.0

    st_dir = _math.supertrend(high, low, close, st_period, st_mult)
    st_signal = 0.0 if np.isnan(st_dir[-1]) else float(st_dir[-1])

    adx_vals = _math.adx(high, low, close, adx_period)
    adx_last = adx_vals[-1]
    strength = 0.5 if np.isnan(adx_last) else min(max(adx_last / 50.0, 0.0), 1.0)

    raw = (ema_signal + st_signal) / 2.0
    vote = max(-1.0, min(1.0, raw * strength))
    return FactorVote(name="trend", vote=vote, weight=weight)
