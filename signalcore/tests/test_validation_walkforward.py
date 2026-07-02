from signalcore.feeds import synthetic_ohlcv
from signalcore.indicators.trend import trend_factor
from signalcore.validation.walkforward import walk_forward_eval


def test_walk_forward_returns_report():
    bars = synthetic_ohlcv(400, seed=1)
    report = walk_forward_eval(trend_factor, bars, min_window=60, forward_horizon=5, step=5)
    assert report.n > 0
    assert -1.0 <= report.ic <= 1.0
    assert 0.0 <= report.hit_rate <= 1.0


def test_walk_forward_is_causal_no_future_bars_used():
    """Faktor fonksiyonuna her adimda SADECE bars[:i+1] verildigini,
    yani gelecek barlarin hic gorulmedigini dogrular."""
    bars = synthetic_ohlcv(200, seed=2)
    seen_lengths = []

    def spy_factor(causal_bars):
        seen_lengths.append(len(causal_bars))
        return trend_factor(causal_bars)

    report = walk_forward_eval(spy_factor, bars, min_window=60, forward_horizon=5, step=10)
    for i, sample in enumerate(report.samples):
        # cagrilan bar sayisi index+1 olmali (gelecek barlar YOK)
        assert seen_lengths[i] == sample.index + 1


def test_walk_forward_too_short_series():
    bars = synthetic_ohlcv(20, seed=3)
    report = walk_forward_eval(trend_factor, bars, min_window=60, forward_horizon=5)
    assert report.n == 0
