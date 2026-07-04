from signalcore.validation.deflated_sharpe import (
    deflated_sharpe_ratio,
    expected_max_sharpe_under_null,
    probabilistic_sharpe_ratio,
)


def test_psr_at_benchmark_is_half():
    psr = probabilistic_sharpe_ratio(1.0, 1.0, n_observations=252)
    assert abs(psr - 0.5) < 1e-6


def test_psr_higher_sharpe_higher_probability():
    low = probabilistic_sharpe_ratio(0.5, 0.0, n_observations=252)
    high = probabilistic_sharpe_ratio(2.0, 0.0, n_observations=252)
    assert high > low


def test_psr_bounded_0_1():
    psr = probabilistic_sharpe_ratio(5.0, 0.0, n_observations=252)
    assert 0.0 <= psr <= 1.0
    psr2 = probabilistic_sharpe_ratio(-5.0, 0.0, n_observations=252)
    assert 0.0 <= psr2 <= 1.0


def test_expected_max_sharpe_increases_with_trials():
    low = expected_max_sharpe_under_null(n_trials=5, variance_of_sharpes=1.0)
    high = expected_max_sharpe_under_null(n_trials=500, variance_of_sharpes=1.0)
    assert high > low


def test_expected_max_sharpe_zero_for_single_trial():
    assert expected_max_sharpe_under_null(n_trials=1, variance_of_sharpes=1.0) == 0.0


def test_deflated_sharpe_ratio_penalizes_many_trials():
    result_few = deflated_sharpe_ratio(
        observed_sharpe=1.5, n_trials=5, variance_of_sharpes=0.25, n_observations=252
    )
    result_many = deflated_sharpe_ratio(
        observed_sharpe=1.5, n_trials=500, variance_of_sharpes=0.25, n_observations=252
    )
    assert result_many.dsr < result_few.dsr
    assert result_many.expected_max_sharpe_under_null > result_few.expected_max_sharpe_under_null


def test_deflated_sharpe_high_sharpe_still_significant_with_few_trials():
    result = deflated_sharpe_ratio(
        observed_sharpe=3.0, n_trials=3, variance_of_sharpes=0.1, n_observations=500
    )
    assert result.is_significant


def test_deflated_sharpe_low_sharpe_many_trials_not_significant():
    result = deflated_sharpe_ratio(
        observed_sharpe=0.3, n_trials=1000, variance_of_sharpes=0.5, n_observations=100
    )
    assert not result.is_significant
