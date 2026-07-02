"""Volatilite faktoru: ATR rejimi + Bollinger/Keltner sikismasi (squeeze).

Bu faktor yon vermez -- boyut/guven carpani niteligindedir; squeeze
kirilma yonunu son barin momentumundan tahmin eder (zayif oy).
"""
from __future__ import annotations

import numpy as np

from ..core.ohlcv import to_arrays
from ..core.types import FactorVote, OHLCVBar
from . import _math


def volatility_factor(
    bars: list[OHLCVBar],
    *,
    atr_period: int = 14,
    bb_period: int = 20,
    weight: float = 1.0,
) -> FactorVote:
    arrs = to_arrays(bars)
    close, high, low = arrs["close"], arrs["high"], arrs["low"]

    if len(close) < max(atr_period, bb_period) + 2:
        return FactorVote(name="volatility", vote=0.0, weight=weight)

    atr_vals = _math.atr(high, low, close, atr_period)
    _, upper, lower, _ = _math.bollinger(close, bb_period, 2.0)

    bandwidth = (upper - lower) / np.where(close == 0, np.nan, close)
    bw_last = bandwidth[-1]
    bw_hist = bandwidth[-(bb_period * 3):]
    bw_hist = bw_hist[~np.isnan(bw_hist)]

    squeeze = False
    if len(bw_hist) > 5 and not np.isnan(bw_last):
        squeeze = bw_last <= np.percentile(bw_hist, 20)

    recent_move = close[-1] - close[-2] if len(close) > 1 else 0.0
    direction = 1.0 if recent_move > 0 else (-1.0 if recent_move < 0 else 0.0)

    # Sikismada kirilma yonune zayif oy; sikisma yoksa notr (bu faktor esas
    # olarak diger faktorler icin boyut/guven girdisi saglar).
    vote = 0.3 * direction if squeeze else 0.0
    return FactorVote(name="volatility", vote=vote, weight=weight)
