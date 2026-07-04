"""Deflated Sharpe Ratio (DSR) -- coklu test/sans duzeltmesi.

Kural (FAZ-PLANI.md Faz 9): faktor seti buyudukce, "en iyi" faktorun
Sharpe'i sans eseri yuksek cikmis olabilir (coklu deneme sorunu).
Bailey & Lopez de Prado (2014) yontemi: N deneme arasindan en iyisinin
BEKLENEN MAKSIMUM Sharpe'ini (sans altinda) tahmin edip, gozlenen
Sharpe'in bunu asma OLASILIGINI (DSR) hesaplar. DSR ~1.0 -> gercek edge
guclu; DSR ~0.5 -> sans ile ayirt edilemez.

PSR (Probabilistic Sharpe Ratio), DSR'nin temel tasidir: gozlenen
Sharpe'in belirli bir benchmark'i (SR*) asma olasiligi, getiri
carpikligi (skewness) ve basikligini (kurtosis) hesaba katarak.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from ._stats import inv_norm_cdf, norm_cdf

EULER_MASCHERONI = 0.5772156649015329


@dataclass
class DeflatedSharpeResult:
    observed_sharpe: float
    n_trials: int
    n_observations: int
    expected_max_sharpe_under_null: float
    psr: float   # Probabilistic Sharpe Ratio (SR* = 0 karsi)
    dsr: float   # Deflated Sharpe Ratio (SR* = beklenen-maks-sans karsi)

    @property
    def is_significant(self) -> bool:
        return self.dsr >= 0.95


def probabilistic_sharpe_ratio(
    observed_sharpe: float,
    benchmark_sharpe: float,
    n_observations: int,
    *,
    skew: float = 0.0,
    kurtosis: float = 3.0,
) -> float:
    """PSR = Phi( (SR_hat - SR*) * sqrt(n-1) / sqrt(1 - skew*SR_hat + (kurt-1)/4 * SR_hat^2) )."""
    if n_observations < 2:
        return 0.5
    numerator = (observed_sharpe - benchmark_sharpe) * math.sqrt(n_observations - 1)
    denom_sq = 1.0 - skew * observed_sharpe + ((kurtosis - 1.0) / 4.0) * observed_sharpe**2
    denominator = math.sqrt(max(denom_sq, 1e-12))
    z = numerator / denominator
    return norm_cdf(z)


def expected_max_sharpe_under_null(n_trials: int, variance_of_sharpes: float) -> float:
    """N bagimsiz "sans" Sharpe denemesi arasindan beklenen maksimum
    (Bailey & Lopez de Prado, extreme value theory yaklasimi)."""
    if n_trials <= 1 or variance_of_sharpes <= 0:
        return 0.0
    sigma = math.sqrt(variance_of_sharpes)
    term1 = (1.0 - EULER_MASCHERONI) * inv_norm_cdf(1.0 - 1.0 / n_trials)
    term2 = EULER_MASCHERONI * inv_norm_cdf(1.0 - 1.0 / (n_trials * math.e))
    return sigma * (term1 + term2)


def deflated_sharpe_ratio(
    observed_sharpe: float,
    *,
    n_trials: int,
    variance_of_sharpes: float,
    n_observations: int,
    skew: float = 0.0,
    kurtosis: float = 3.0,
) -> DeflatedSharpeResult:
    benchmark = expected_max_sharpe_under_null(n_trials, variance_of_sharpes)
    psr = probabilistic_sharpe_ratio(observed_sharpe, 0.0, n_observations, skew=skew, kurtosis=kurtosis)
    dsr = probabilistic_sharpe_ratio(observed_sharpe, benchmark, n_observations, skew=skew, kurtosis=kurtosis)
    return DeflatedSharpeResult(
        observed_sharpe=observed_sharpe,
        n_trials=n_trials,
        n_observations=n_observations,
        expected_max_sharpe_under_null=benchmark,
        psr=psr,
        dsr=dsr,
    )
