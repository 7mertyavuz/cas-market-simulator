"""Hacim faktoru: CMF + OBV egilimi.

Imzali birikim/dagitim: fiyat hareketiyle hacmin ayni yonde olup
olmadigini olcer (uyumsuzluk = zayif sinyal).
"""
from __future__ import annotations

import numpy as np

from ..core.ohlcv import to_arrays
from ..core.types import FactorVote, OHLCVBar
from . import _math


def volume_factor(
    bars: list[OHLCVBar],
    *,
    cmf_period: int = 20,
    obv_trend_period: int = 20,
    weight: float = 1.0,
) -> FactorVote:
    arrs = to_arrays(bars)
    close, high, low, volume = arrs["close"], arrs["high"], arrs["low"], arrs["volume"]

    if len(close) < max(cmf_period, obv_trend_period) + 2:
        return FactorVote(name="volume", vote=0.0, weight=weight)

    cmf_vals = _math.cmf(high, low, close, volume, cmf_period)
    cmf_last = cmf_vals[-1]
    cmf_signal = 0.0 if np.isnan(cmf_last) else max(-1.0, min(1.0, cmf_last * 2.0))

    obv_vals = _math.obv(close, volume)
    obv_ema = _math.ema(obv_vals, obv_trend_period)
    obv_signal = 0.0
    if len(obv_ema) > 1 and not np.isnan(obv_ema[-1]) and not np.isnan(obv_ema[-2]):
        obv_signal = 1.0 if obv_ema[-1] > obv_ema[-2] else -1.0

    vote = max(-1.0, min(1.0, 0.6 * cmf_signal + 0.4 * obv_signal))
    return FactorVote(name="volume", vote=vote, weight=weight)
