"""Yapi faktoru: Hurst / Efficiency-Ratio (trend mi MR mi) + fracdiff.

Bu faktor yon vermez -- rejim tespiti icin girdi saglar (Faz 1d
regime_router burayi kullanacak). Yine de combine icinde zayif bir
"trend gucu" oyu olarak da katkida bulunur: ER yuksekse mevcut fiyat
yonunu hafifce teyit eder.
"""
from __future__ import annotations

import numpy as np

from ..core.ohlcv import to_arrays
from ..core.types import FactorVote, OHLCVBar
from . import _math


def structure_factor(
    bars: list[OHLCVBar],
    *,
    hurst_lag: int = 20,
    er_period: int = 10,
    weight: float = 0.5,
) -> FactorVote:
    arrs = to_arrays(bars)
    close = arrs["close"]

    if len(close) < max(hurst_lag * 2, er_period) + 2:
        return FactorVote(name="structure", vote=0.0, weight=weight)

    er_vals = _math.efficiency_ratio(close, er_period)
    er_last = er_vals[-1]
    er_last = 0.0 if np.isnan(er_last) else er_last

    recent_move = close[-1] - close[-1 - er_period]
    direction = 1.0 if recent_move > 0 else (-1.0 if recent_move < 0 else 0.0)

    vote = max(-1.0, min(1.0, direction * er_last))
    return FactorVote(name="structure", vote=vote, weight=weight)


def regime_from_hurst(bars: list[OHLCVBar], *, hurst_lag: int = 20) -> str:
    """'trend' | 'mean_revert' | 'random' dondurur (regime_router icin, Faz 1d)."""
    arrs = to_arrays(bars)
    close = arrs["close"]
    if len(close) < hurst_lag * 2:
        return "random"
    h = _math.hurst_exponent(close, hurst_lag)
    if h > 0.55:
        return "trend"
    if h < 0.45:
        return "mean_revert"
    return "random"


def fracdiff(x: np.ndarray, d: float = 0.4, threshold: float = 1e-4, max_width: int = 100) -> np.ndarray:
    """Kesirli fark alma (fractional differencing, Lopez de Prado stili).

    Fiyat serisini durgunlastirir (stationarity) ama hafizayi (uzun-vade
    bagimliligi) tamamen yok etmez -- ML/istatistiksel testler icin
    kullanislidir. Sabit pencereli (fixed-width) yaklasik uygulama.

    Agirliklar d<0.5 icin yavas soner (~k^(-1-d)); bu yuzden pencere
    genisligi `max_width` ile de sinirlanir (esik hicbir zaman
    gecilmeyebilir).
    """
    weights = [1.0]
    k = 1
    cap = max(1, min(max_width, len(x) - 1))
    while k <= cap:
        w_k = -weights[-1] / k * (d - k + 1)
        if abs(w_k) < threshold:
            break
        weights.append(w_k)
        k += 1
    weights = np.array(weights[::-1])
    width = len(weights)

    out = np.full_like(x, np.nan, dtype=float)
    for i in range(width - 1, len(x)):
        window = x[i - width + 1: i + 1]
        out[i] = float(np.dot(weights, window))
    return out
