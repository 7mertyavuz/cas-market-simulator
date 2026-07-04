"""Kalibrasyon: uretilen (sentetik veya simule) piyasa, stilize gerceklerle uyumlu mu?

Kural (FAZ-PLANI.md Faz 9): "Uymuyorsa emergence yanıltıcıdır." Bu
modul uc klasik stilize gercegi test eder:
  1. Fat tails (kalin kuyruklar): getiri dagiliminin fazladan basikligi
     (excess kurtosis) normal dagilimdan (0) belirgin sekilde buyuk mu?
  2. Volatility clustering: buyuk hareketleri buyuk hareketler mi takip
     ediyor? (|getiri| veya getiri^2'nin lag-1 otokorelasyonu > 0)
  3. Leverage effect: dususler, sonraki oynakligi arttiriyor mu?
     (getiri_t ile oynaklik_{t+1} arasindaki korelasyon TIPIK OLARAK
     NEGATIF -- dusen fiyat, sonraki oynakligi yukseltir)
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class CalibrationReport:
    n: int
    excess_kurtosis: float
    vol_clustering_autocorr: float
    leverage_effect_corr: float
    is_fat_tailed: bool
    has_vol_clustering: bool
    has_leverage_effect: bool

    @property
    def stylized_facts_passed(self) -> int:
        return sum([self.is_fat_tailed, self.has_vol_clustering, self.has_leverage_effect])


def _returns_from_prices(prices: np.ndarray) -> np.ndarray:
    prices = np.asarray(prices, dtype=float)
    return np.diff(prices) / prices[:-1]


def _excess_kurtosis(x: np.ndarray) -> float:
    x = x - np.mean(x)
    std = np.std(x)
    if std == 0:
        return 0.0
    return float(np.mean(x**4) / std**4 - 3.0)


def _autocorr_lag1(x: np.ndarray) -> float:
    if len(x) < 3:
        return 0.0
    a, b = x[:-1], x[1:]
    if np.std(a) == 0 or np.std(b) == 0:
        return 0.0
    return float(np.corrcoef(a, b)[0, 1])


def compute_calibration_report(
    prices: list[float],
    *,
    fat_tail_threshold: float = 1.0,
    clustering_threshold: float = 0.05,
    leverage_threshold: float = -0.05,
) -> CalibrationReport:
    prices_arr = np.asarray(prices, dtype=float)
    if len(prices_arr) < 5:
        return CalibrationReport(
            n=len(prices_arr), excess_kurtosis=0.0, vol_clustering_autocorr=0.0,
            leverage_effect_corr=0.0, is_fat_tailed=False, has_vol_clustering=False,
            has_leverage_effect=False,
        )

    returns = _returns_from_prices(prices_arr)
    excess_kurt = _excess_kurtosis(returns)

    sq_returns = returns**2
    vol_autocorr = _autocorr_lag1(sq_returns)

    leverage_corr = 0.0
    if len(returns) >= 3:
        r_t = returns[:-1]
        vol_t1 = np.abs(returns[1:])
        if np.std(r_t) > 0 and np.std(vol_t1) > 0:
            leverage_corr = float(np.corrcoef(r_t, vol_t1)[0, 1])

    return CalibrationReport(
        n=len(prices_arr),
        excess_kurtosis=excess_kurt,
        vol_clustering_autocorr=vol_autocorr,
        leverage_effect_corr=leverage_corr,
        is_fat_tailed=excess_kurt >= fat_tail_threshold,
        has_vol_clustering=vol_autocorr >= clustering_threshold,
        has_leverage_effect=leverage_corr <= leverage_threshold,
    )
