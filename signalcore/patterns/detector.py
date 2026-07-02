"""Formasyoncu: mum + grafik formasyonlarinin hepsini tarar.

`detect_patterns` -> list[PatternHit] (Card.patterns'e dogrudan gider).
`patterns_to_vote` -> formasyonlari TEK bir FactorVote'a indirger
(combine/aggregator'a ayri bir "patterns" oyu olarak girer, bkz.
FAZ-PLANI.md Faz 2 'Bitti': "combine'a ayri oy + kartta gorsel liste").
"""
from __future__ import annotations

from ..core.types import FactorVote, OHLCVBar, PatternHit
from .candles import detect_all_candles
from .chart import detect_all_chart_patterns

_DIRECTION_SIGN = {"bull": 1.0, "bear": -1.0, "neutral": 0.0}


def detect_patterns(bars: list[OHLCVBar], *, swing_order: int = 3) -> list[PatternHit]:
    hits: list[PatternHit] = []
    hits.extend(detect_all_candles(bars))
    hits.extend(detect_all_chart_patterns(bars, order=swing_order))
    return hits


def patterns_to_vote(patterns: list[PatternHit], *, weight: float = 0.7) -> FactorVote:
    """Formasyon listesini agirlikli-ortalama tek bir oya indirger.

    Guclu formasyonlar (strength yuksek) toplam oyu daha cok etkiler;
    cakisan zit formasyonlar birbirini iptal eder (ki bu istenen
    davranistir -- celiskili formasyonlar dusuk net sinyal uretmeli).
    """
    if not patterns:
        return FactorVote(name="patterns", vote=0.0, weight=weight)

    total_strength = sum(p.strength for p in patterns)
    if total_strength == 0:
        return FactorVote(name="patterns", vote=0.0, weight=weight)

    signed = sum(_DIRECTION_SIGN[p.direction] * p.strength for p in patterns)
    vote = max(-1.0, min(1.0, signed / total_strength))
    return FactorVote(name="patterns", vote=vote, weight=weight)
