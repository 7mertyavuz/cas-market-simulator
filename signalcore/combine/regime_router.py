"""Rejim yonlendirici: Hurst/ER ile trend<->MR agirliklarini yonlendirir.

Kural (03-PROMPT Bolum 5): RANDOM rejimde guveni kis. Bu modul faktor
agirliklarini DEGISTIRMEZ (registry sabit kalir) -- yalnizca aggregate
asamasindan ONCE, gecici bir agirlik carpani seti uretir. Boylece
factor_tracker'in olctugu "gercek" agirliklar bozulmaz.
"""
from __future__ import annotations

from dataclasses import dataclass

from ..core.types import FactorVote, OHLCVBar
from ..indicators.structure import regime_from_hurst

TREND_AXES = {"trend"}
MEANREV_AXES = {"meanrev"}


@dataclass
class RegimeDecision:
    regime: str                   # "trend" | "mean_revert" | "random"
    axis_multipliers: dict         # axis -> carpan
    confidence_multiplier: float    # RANDOM rejimde < 1.0


def decide_regime(bars: list[OHLCVBar], *, hurst_lag: int = 20) -> RegimeDecision:
    regime = regime_from_hurst(bars, hurst_lag=hurst_lag)

    if regime == "trend":
        multipliers = {"trend": 1.3, "meanrev": 0.5}
        confidence_multiplier = 1.0
    elif regime == "mean_revert":
        multipliers = {"trend": 0.5, "meanrev": 1.3}
        confidence_multiplier = 1.0
    else:  # random
        multipliers = {"trend": 0.7, "meanrev": 0.7}
        confidence_multiplier = 0.5  # RANDOM'da guveni kis

    return RegimeDecision(regime=regime, axis_multipliers=multipliers, confidence_multiplier=confidence_multiplier)


def apply_regime(
    votes: list[FactorVote],
    decision: RegimeDecision,
    *,
    axis_of: dict | None = None,
) -> list[FactorVote]:
    """Her oyun agirligini, faktorun ekseni regime_decision'daki carpana
    gore olceklendirerek YENI bir FactorVote listesi doner (orijinali
    mutasyona ugratmaz).
    """
    axis_of = axis_of or {}
    out: list[FactorVote] = []
    for v in votes:
        axis = axis_of.get(v.name)
        mult = decision.axis_multipliers.get(axis, 1.0)
        out.append(FactorVote(name=v.name, vote=v.vote, weight=v.weight * mult, market=v.market))
    return out
