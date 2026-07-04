"""Kuyruk riski: historik VaR/CVaR ve EVT (Hill tahmincisi) tabanli tavan.

Kural: pozisyon boyutu yalnizca Kelly/edge'e degil, kuyruk riskine de
tabi olmali. Normal dagilim varsayimi kripto icin gecersizdir (fat
tail) -- bu yuzden hem historik (parametrik olmayan) hem de EVT
(Extreme Value Theory, Hill tahmincisi) tabanli tahminler sunulur.

Bagimlilik: yalnizca numpy. scipy YOK.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np


def _returns_from_prices(prices: np.ndarray) -> np.ndarray:
    prices = np.asarray(prices, dtype=float)
    if prices.size < 2:
        return np.array([])
    return prices[1:] / prices[:-1] - 1.0


def historical_var(returns: np.ndarray, *, alpha: float = 0.05) -> float:
    """Historik Value-at-Risk: getiri dagiliminin alpha-yuzdelik dilimi.

    Negatif bir sayi doner (kayip tarafi). alpha=0.05 -> %95 guven VaR.
    """
    returns = np.asarray(returns, dtype=float)
    if returns.size == 0:
        return 0.0
    return float(np.percentile(returns, alpha * 100.0))


def historical_cvar(returns: np.ndarray, *, alpha: float = 0.05) -> float:
    """Historik Conditional VaR (Expected Shortfall): VaR esiginin
    otesindeki kayiplarin ortalamasi. VaR'dan daha kotumser (kuyruk-duyarli).
    """
    returns = np.asarray(returns, dtype=float)
    if returns.size == 0:
        return 0.0
    var = historical_var(returns, alpha=alpha)
    tail = returns[returns <= var]
    if tail.size == 0:
        return var
    return float(np.mean(tail))


def hill_estimator(returns: np.ndarray, *, tail_fraction: float = 0.1) -> float:
    """Hill tahmincisi: kuyruk endeksi (tail index) xi tahmini.

    Kayiplarin (negatif getirilerin) buyukluklerini kullanir. Kucuk
    xi -> daha kalin/agir kuyruk (daha yuksek kuyruk riski). xi'nin
    tersi kabaca Pareto kuyruk-uzunlugu parametresidir.

    tail_fraction: en kotu getirilerin hangi orani kuyruk olarak
    kullanilsin (varsayilan %10).
    """
    returns = np.asarray(returns, dtype=float)
    losses = -returns[returns < 0]
    losses = losses[losses > 0]
    n = losses.size
    if n < 5:
        return float("nan")

    k = max(1, int(math.ceil(n * tail_fraction)))
    k = min(k, n - 1)
    if k < 1:
        return float("nan")

    sorted_losses = np.sort(losses)[::-1]  # buyukten kucuge
    threshold = sorted_losses[k]
    if threshold <= 0:
        return float("nan")

    top_k = sorted_losses[:k]
    log_ratios = np.log(top_k / threshold)
    xi = float(np.mean(log_ratios))
    if xi <= 0:
        return float("nan")
    return xi


def evt_var(
    returns: np.ndarray,
    *,
    alpha: float = 0.05,
    tail_fraction: float = 0.1,
) -> float:
    """EVT (Peaks-over-Threshold / Hill) tabanli VaR tahmini.

    Historik VaR'dan farkli olarak kuyruk davranisini Pareto-benzeri
    bir modelle ekstrapole eder -- ozellikle alpha kucukken (ornegin
    %1) az veri noktasi oldugunda historik yontemden daha stabildir.

    Hesaplanamazsa (yetersiz veri / xi tanimsiz) historical_var'a
    duser (guvenli varsayilan).
    """
    returns = np.asarray(returns, dtype=float)
    losses = -returns[returns < 0]
    losses = losses[losses > 0]
    n_total = returns.size
    n_losses = losses.size

    xi = hill_estimator(returns, tail_fraction=tail_fraction)
    if math.isnan(xi) or n_losses < 5 or n_total == 0:
        return historical_var(returns, alpha=alpha)

    k = max(1, int(math.ceil(n_losses * tail_fraction)))
    k = min(k, n_losses - 1)
    if k < 1:
        return historical_var(returns, alpha=alpha)

    sorted_losses = np.sort(losses)[::-1]
    threshold = sorted_losses[k]
    if threshold <= 0:
        return historical_var(returns, alpha=alpha)

    n_exceed_ratio = k / n_total
    if alpha >= n_exceed_ratio:
        # alpha kuyruk-esik oranindan buyukse EVT ekstrapolasyonu
        # gerekmez, historik tahmin yeterince veriye dayanir.
        return historical_var(returns, alpha=alpha)

    # Peaks-over-threshold VaR formulu: threshold * (n_exceed_ratio/alpha)^xi
    var_magnitude = threshold * (n_exceed_ratio / alpha) ** xi
    return float(-var_magnitude)


@dataclass
class TailRiskReport:
    n: int
    historical_var_95: float
    historical_cvar_95: float
    hill_tail_index: float
    evt_var_95: float
    evt_var_99: float
    is_fat_tailed: bool          # hill_tail_index dusuk (<0.5) -> agir kuyruk


def compute_tail_risk_report(
    prices: np.ndarray,
    *,
    alpha_95: float = 0.05,
    alpha_99: float = 0.01,
    tail_fraction: float = 0.1,
    fat_tail_xi_threshold: float = 0.5,
) -> TailRiskReport:
    returns = _returns_from_prices(np.asarray(prices, dtype=float))
    if returns.size == 0:
        return TailRiskReport(
            n=0,
            historical_var_95=0.0,
            historical_cvar_95=0.0,
            hill_tail_index=float("nan"),
            evt_var_95=0.0,
            evt_var_99=0.0,
            is_fat_tailed=False,
        )

    xi = hill_estimator(returns, tail_fraction=tail_fraction)
    is_fat = (not math.isnan(xi)) and xi < fat_tail_xi_threshold

    return TailRiskReport(
        n=int(returns.size),
        historical_var_95=historical_var(returns, alpha=alpha_95),
        historical_cvar_95=historical_cvar(returns, alpha=alpha_95),
        hill_tail_index=xi,
        evt_var_95=evt_var(returns, alpha=alpha_95, tail_fraction=tail_fraction),
        evt_var_99=evt_var(returns, alpha=alpha_99, tail_fraction=tail_fraction),
        is_fat_tailed=is_fat,
    )


def tail_risk_cap(
    proposed_size_pct: float,
    tail_report: TailRiskReport,
    *,
    max_cvar_loss_pct: float = 0.1,
) -> float:
    """CVaR tabanli pozisyon boyutu tavani.

    Beklenen kuyruk kaybi (CVaR) * pozisyon boyutu, sermayenin
    max_cvar_loss_pct'ini asmayacak sekilde proposed_size_pct'i kirpar.

    Ornek: CVaR = -%20 (tek islemlik getiri), max_cvar_loss_pct = %10
    -> boyut en fazla 0.10/0.20 = %50 olabilir.
    """
    proposed_size_pct = max(0.0, proposed_size_pct)
    cvar_loss = abs(tail_report.historical_cvar_95)
    if cvar_loss <= 1e-9:
        return proposed_size_pct

    max_size_from_cvar = max_cvar_loss_pct / cvar_loss
    return float(min(proposed_size_pct, max_size_from_cvar))
