"""FactorBrain: analyze(symbol, ohlcv, extra_factors) -> Card.

Faz 1a: registry faktorlerini calistirir + aggregator ile birlestirir.
Faz 1d: regime_router devreye girdi -- trend/MR agirliklari rejime gore
olceklenir, RANDOM rejimde guven kisilir.
Faz 1e: risk motoru eklendi. Faz 2: patterns/detector.py devreye girdi --
tespit edilen formasyonlar hem Card.patterns'e (gorsel liste) hem de
aggregator'a tek bir ek oy olarak (patterns_to_vote) gidiyor.

extra_factors: dict[str, FactorVote]. Not: 00-ORTAK-SOZLESME.md'deki
FactorBrain.analyze imzasinda extra_factors icinde FlowState/
SentimentState gibi zengin tipler de olabilir -- ama signalcore o
tiplere BAGIMLI OLMAMALI (bagimlilik yonu: simulator -> signalcore).
Bu yuzden burada extra_factors ALREADY-CONVERTED FactorVote bekler;
zengin tipten FactorVote'a cevirme islemi cas-market-simulator
tarafindaki adaptor katmaninin (Faz 3, adapters/factor_brain.py) isidir.
"""
from __future__ import annotations

from datetime import datetime, timezone

from .combine.aggregator import aggregate
from .combine.regime_router import apply_regime, decide_regime
from .combine.registry_setup import register_defaults
from .core.registry import FactorRegistry, default_registry
from .core.types import Card, FactorVote, OHLCVBar
from .indicators.sensors import compute_sensor_votes
from .patterns.detector import detect_patterns, patterns_to_vote
from .risk.levels import atr_stop_tp, to_risk_dict
from .risk.sizing import half_kelly_size

EXTRA_FACTOR_DEFAULT_WEIGHT = 0.15  # dusuk agirlik (cift sayim riski, bkz. FAZ-PLANI.md kural #3)


def analyze(
    symbol: str,
    bars: list[OHLCVBar],
    extra_factors: dict[str, FactorVote] | None = None,
    *,
    registry: FactorRegistry | None = None,
    neutral_band: float = 0.1,
    use_regime_router: bool = True,
    use_patterns: bool = True,
    sensor_states: dict[str, object] | None = None,
) -> Card:
    reg = registry if registry is not None else register_defaults(default_registry)
    axis_of = {spec.name: spec.axis for spec in reg.all(enabled_only=True)}

    votes: list[FactorVote] = []
    for spec in reg.all(enabled_only=True):
        try:
            vote = spec.fn(bars, weight=spec.initial_weight)
        except Exception:
            # Bir faktor patlarsa butun karti dusurmez -- notr oy ile devam.
            vote = FactorVote(name=spec.name, vote=0.0, weight=spec.initial_weight)
        votes.append(vote)

    confidence_multiplier = 1.0
    if use_regime_router and bars:
        decision = decide_regime(bars)
        votes = apply_regime(votes, decision, axis_of=axis_of)
        confidence_multiplier = decision.confidence_multiplier

    patterns: list = []
    if use_patterns and bars:
        patterns = detect_patterns(bars)
        if patterns:
            votes.append(patterns_to_vote(patterns))

    votes.extend(compute_sensor_votes(sensor_states))

    if extra_factors:
        for key, vote in extra_factors.items():
            if vote is None:
                continue
            votes.append(vote)

    result = aggregate(votes, neutral_band=neutral_band)
    confidence = max(0.0, min(1.0, result.confidence * confidence_multiplier))
    direction = result.direction if confidence > 0.0 else "NEUTRAL"

    risk: dict = {"size_pct": 0.0, "stop": None, "tp": None, "invalidation": None}
    if direction in ("LONG", "SHORT") and bars:
        sizing = half_kelly_size(confidence)
        levels = atr_stop_tp(bars, direction)
        risk = to_risk_dict(sizing.size_pct, levels)

    return Card(
        symbol=symbol,
        direction=direction,
        confidence=confidence,
        votes=votes,
        patterns=patterns,
        risk=risk,
        ts=datetime.now(timezone.utc),
    )
