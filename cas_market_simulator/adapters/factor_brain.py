"""Gercek FactorBrain adaptoru: signalcore.brain.analyze()'i sarar.

Faz 0'daki StubFactorBrain'in yerini alir (StubFactorBrain hala testler
icin mevcut). Iki yonlu ceviri yapar:
  1. extra_factors (SentimentState/FlowState/float) -> signalcore
     FactorVote (dusuk agirlikla, cift-sayim riski factor_tracker'in
     isi -- bkz. FAZ-PLANI.md kritik kural #3).
  2. signalcore.core.types.Card -> adapters.contracts.Card (ayni
     alanlara sahip ama farkli siniflar; signalcore bagimsiz kalmali).
"""
from __future__ import annotations

from signalcore.brain import analyze as signalcore_analyze
from signalcore.core.types import FactorVote as SCFactorVote
from signalcore.core.types import OHLCVBar as SCBar

from .contracts import Card, FactorVote, FlowState, PatternHit, SentimentState

DEFAULT_EXTRA_WEIGHT = 0.15  # bkz. FAZ-PLANI.md kural #3: disaridan gelen sinyal dusuk agirlikla girer


def _clamp(x: float, lo: float = -1.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, x))


class SignalCoreFactorBrain:
    """FactorBrain Protocol implementasyonu (bkz. adapters/contracts.py)."""

    def __init__(self, *, min_bars: int = 30, extra_weight: float = DEFAULT_EXTRA_WEIGHT) -> None:
        self.min_bars = min_bars
        self.extra_weight = extra_weight

    def analyze(self, symbol: str, ohlcv: list[SCBar], extra_factors: dict) -> Card:
        bars = ohlcv or []
        if len(bars) < self.min_bars:
            return Card(symbol=symbol, direction="NEUTRAL", confidence=0.0, votes=[], patterns=[], risk={})

        sc_extra = self._convert_extra_factors(extra_factors)
        sc_card = signalcore_analyze(symbol, bars, extra_factors=sc_extra)
        return self._to_sim_card(sc_card)

    def _convert_extra_factors(self, extra_factors: dict | None) -> dict[str, SCFactorVote]:
        out: dict[str, SCFactorVote] = {}
        if not extra_factors:
            return out

        sentiment = extra_factors.get("sentiment")
        if isinstance(sentiment, SentimentState):
            out["sentiment"] = SCFactorVote(
                name="sentiment", vote=_clamp(sentiment.polarity), weight=self.extra_weight
            )

        flow = extra_factors.get("flow")
        if isinstance(flow, FlowState):
            out["flow"] = SCFactorVote(
                name="flow", vote=_clamp(flow.flow_imbalance), weight=self.extra_weight
            )

        crowd_emergence = extra_factors.get("crowd_emergence")
        if isinstance(crowd_emergence, (int, float)):
            out["crowd_emergence"] = SCFactorVote(
                name="crowd_emergence", vote=_clamp(float(crowd_emergence)), weight=self.extra_weight
            )

        return out

    @staticmethod
    def _to_sim_card(sc_card) -> Card:
        votes = [
            FactorVote(name=v.name, vote=v.vote, weight=v.weight, market=v.market)
            for v in sc_card.votes
        ]
        patterns = [
            PatternHit(name=p.name, direction=p.direction, strength=p.strength, invalidation=p.invalidation)
            for p in sc_card.patterns
        ]
        return Card(
            symbol=sc_card.symbol,
            direction=sc_card.direction,
            confidence=sc_card.confidence,
            votes=votes,
            patterns=patterns,
            risk=dict(sc_card.risk),
            ts=sc_card.ts,
        )


class StubFactorBrain:
    """Faz 0 stub -- geriye uyumluluk icin korunuyor (testler kullanir).

    Her zaman NEUTRAL, dusuk guvenli bos bir kart dondurur; signalcore'a
    bagimli degildir.
    """

    def analyze(self, symbol: str, ohlcv, extra_factors: dict) -> Card:
        return Card(symbol=symbol, direction="NEUTRAL", confidence=0.0, votes=[], patterns=[], risk={})
