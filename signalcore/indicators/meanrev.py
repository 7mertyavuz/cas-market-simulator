"""Ortalama-donus (mean-reversion) faktoru: Bollinger %B + z-score + basit OU-spread.

Rejim-kapili olmasi gerekir (trendle savasmamali) -- rejim kapisi
Faz 1d'de combine/regime_router.py'de uygulanacak; bu faktor kendi
basina yalnizca "asiri sapma" oyu verir.
"""
from __future__ import annotations

import numpy as np

from ..core.ohlcv import to_arrays
from ..core.types import FactorVote, OHLCVBar
from . import _math


def meanrev_factor(
    bars: list[OHLCVBar],
    *,
    bb_period: int = 20,
    zscore_period: int = 20,
    weight: float = 1.0,
) -> FactorVote:
    arrs = to_arrays(bars)
    close = arrs["close"]

    if len(close) < max(bb_period, zscore_period) + 2:
        return FactorVote(name="meanrev", vote=0.0, weight=weight)

    _, _, _, pct_b = _math.bollinger(close, bb_period, 2.0)
    pct_b_last = pct_b[-1]
    # %B: 0=alt bant, 1=ust bant, 0.5=orta. Asiri sapmada TERS pozisyon.
    bb_signal = 0.0
    if not np.isnan(pct_b_last):
        bb_signal = max(-1.0, min(1.0, (0.5 - pct_b_last) * 2.0))

    z = _math.zscore(close, zscore_period)
    z_last = z[-1]
    z_signal = 0.0
    if not np.isnan(z_last):
        z_signal = max(-1.0, min(1.0, -z_last / 2.5))

    vote = max(-1.0, min(1.0, 0.5 * bb_signal + 0.5 * z_signal))
    return FactorVote(name="meanrev", vote=vote, weight=weight)
