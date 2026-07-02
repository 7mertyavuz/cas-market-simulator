from signalcore.combine.regime_router import apply_regime, decide_regime
from signalcore.core.types import FactorVote
from signalcore.feeds import Regime, synthetic_ohlcv


def test_decide_regime_valid_label():
    bars = synthetic_ohlcv(300, seed=1)
    decision = decide_regime(bars)
    assert decision.regime in ("trend", "mean_revert", "random")


def test_decide_regime_random_reduces_confidence():
    bars = synthetic_ohlcv(300, seed=1, initial_regime=Regime.MEAN_REVERT)
    decision = decide_regime(bars)
    if decision.regime == "random":
        assert decision.confidence_multiplier < 1.0
    else:
        assert decision.confidence_multiplier == 1.0


def test_apply_regime_scales_matching_axis():
    votes = [FactorVote(name="trend", vote=0.5, weight=1.0), FactorVote(name="meanrev", vote=0.3, weight=1.0)]
    from signalcore.combine.regime_router import RegimeDecision

    decision = RegimeDecision(regime="trend", axis_multipliers={"trend": 1.3, "meanrev": 0.5}, confidence_multiplier=1.0)
    axis_of = {"trend": "trend", "meanrev": "meanrev"}
    out = apply_regime(votes, decision, axis_of=axis_of)
    trend_v = next(v for v in out if v.name == "trend")
    mr_v = next(v for v in out if v.name == "meanrev")
    assert trend_v.weight == 1.3
    assert mr_v.weight == 0.5


def test_apply_regime_does_not_mutate_input():
    votes = [FactorVote(name="trend", vote=0.5, weight=1.0)]
    from signalcore.combine.regime_router import RegimeDecision

    decision = RegimeDecision(regime="trend", axis_multipliers={"trend": 1.3}, confidence_multiplier=1.0)
    apply_regime(votes, decision, axis_of={"trend": "trend"})
    assert votes[0].weight == 1.0  # orijinal degismedi
