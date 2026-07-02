"""Oy birlestirici: vote x weight -> yon + guven.

`extra_factors` (flow/sentiment/crowd_emergence) dahil TUM FactorVote
listesi buradan gecer -- disaridan gelen sinyaller icin ozel bir yol
yoktur, hepsi ayni agirlikli oylama mekanizmasindan gecer (cift sayim
riskini factor_tracker olcer, bkz. validation/factor_tracker.py).
"""
from __future__ import annotations

from dataclasses import dataclass

from ..core.types import FactorVote


@dataclass
class AggregateResult:
    direction: str        # "LONG" | "SHORT" | "NEUTRAL"
    confidence: float       # 0..1
    raw_score: float        # agirlikli ortalama, [-1,1]
    neutral_band: float


def aggregate(
    votes: list[FactorVote],
    *,
    neutral_band: float = 0.1,
) -> AggregateResult:
    """Agirlikli oylari birlestirir.

    raw_score = sum(vote*weight) / sum(weight), [-1,1] araliginda.
    |raw_score| <= neutral_band ise NEUTRAL (gurultu bandi).
    """
    if not votes:
        return AggregateResult(direction="NEUTRAL", confidence=0.0, raw_score=0.0, neutral_band=neutral_band)

    total_weight = sum(v.weight for v in votes)
    if total_weight <= 0:
        return AggregateResult(direction="NEUTRAL", confidence=0.0, raw_score=0.0, neutral_band=neutral_band)

    raw_score = sum(v.vote * v.weight for v in votes) / total_weight
    raw_score = max(-1.0, min(1.0, raw_score))

    if abs(raw_score) <= neutral_band:
        direction = "NEUTRAL"
    elif raw_score > 0:
        direction = "LONG"
    else:
        direction = "SHORT"

    # guven: sinyal gucu (bandin uzerindeki kisim) x oy tutarliligi (ayni
    # yonde oy veren agirlik orani)
    if direction == "NEUTRAL":
        confidence = 0.0
    else:
        strength = (abs(raw_score) - neutral_band) / (1.0 - neutral_band)
        same_dir_weight = sum(
            v.weight for v in votes if (v.vote > 0) == (raw_score > 0)
        )
        agreement = same_dir_weight / total_weight
        confidence = max(0.0, min(1.0, strength * agreement))

    return AggregateResult(
        direction=direction, confidence=confidence, raw_score=raw_score, neutral_band=neutral_band
    )
