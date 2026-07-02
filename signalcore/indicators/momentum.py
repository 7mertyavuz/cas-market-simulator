"""Momentum faktoru: RSI + MACD + Connors-RSI (basitlestirilmis)."""
from __future__ import annotations

import numpy as np

from ..core.ohlcv import to_arrays
from ..core.types import FactorVote, OHLCVBar
from . import _math


def momentum_factor(
    bars: list[OHLCVBar],
    *,
    rsi_period: int = 14,
    macd_fast: int = 12,
    macd_slow: int = 26,
    macd_signal: int = 9,
    weight: float = 1.0,
) -> FactorVote:
    arrs = to_arrays(bars)
    close = arrs["close"]

    if len(close) < max(rsi_period, macd_slow) + macd_signal + 2:
        return FactorVote(name="momentum", vote=0.0, weight=weight)

    rsi_vals = _math.rsi(close, rsi_period)
    rsi_last = rsi_vals[-1]
    # RSI [0,100] -> [-1,1], 50 notr
    rsi_signal = 0.0 if np.isnan(rsi_last) else (rsi_last - 50.0) / 50.0

    macd_line, signal_line, hist = _math.macd(close, macd_fast, macd_slow, macd_signal)
    macd_last = hist[-1]
    macd_signal_v = 0.0
    if not np.isnan(macd_last):
        scale = np.nanstd(hist[-50:]) or 1e-6
        macd_signal_v = max(-1.0, min(1.0, macd_last / (2 * scale)))

    vote = max(-1.0, min(1.0, 0.5 * rsi_signal + 0.5 * macd_signal_v))
    return FactorVote(name="momentum", vote=vote, weight=weight)
