from signalcore.core.types import FactorVote
from signalcore.feeds import synthetic_ohlcv
from signalcore.indicators.trend import trend_factor
from signalcore.validation.leakage import assert_no_lookahead


def test_trend_factor_passes_leakage_check():
    bars = synthetic_ohlcv(300, seed=1)
    result = assert_no_lookahead(trend_factor, bars, min_window=60, check_every=20)
    assert result.ok
    assert len(result.checked_indices) > 0


def test_leakage_check_flags_nondeterministic_factor():
    import random

    def flaky_factor(bars):
        return FactorVote(name="flaky", vote=random.choice([-0.5, 0.5]), weight=1.0)

    bars = synthetic_ohlcv(200, seed=2)
    result = assert_no_lookahead(flaky_factor, bars, min_window=60, check_every=20)
    assert not result.ok
    assert "belirlenimci degil" in result.detail
