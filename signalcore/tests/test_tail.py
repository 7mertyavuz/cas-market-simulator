import numpy as np

from signalcore.risk.tail import (
    TailRiskReport,
    compute_tail_risk_report,
    evt_var,
    hill_estimator,
    historical_cvar,
    historical_var,
    tail_risk_cap,
)


def _fat_tailed_returns(seed=0, n=500):
    rng = np.random.default_rng(seed)
    # student-t benzeri agir kuyruk: normal / sqrt(chi2/df)
    df = 3
    normal = rng.normal(0, 0.01, n)
    chi2 = rng.chisquare(df, n)
    t_like = normal / np.sqrt(chi2 / df)
    return t_like


def test_historical_var_is_negative_for_normal_returns():
    rng = np.random.default_rng(1)
    returns = rng.normal(0, 0.02, 1000)
    var95 = historical_var(returns, alpha=0.05)
    assert var95 < 0


def test_historical_cvar_worse_than_var():
    rng = np.random.default_rng(1)
    returns = rng.normal(0, 0.02, 1000)
    var95 = historical_var(returns, alpha=0.05)
    cvar95 = historical_cvar(returns, alpha=0.05)
    assert cvar95 <= var95


def test_historical_var_empty_returns_zero():
    assert historical_var(np.array([])) == 0.0
    assert historical_cvar(np.array([])) == 0.0


def test_hill_estimator_nan_for_too_few_losses():
    returns = np.array([0.01, 0.02, 0.01, -0.005])
    xi = hill_estimator(returns)
    assert np.isnan(xi)


def test_hill_estimator_positive_for_fat_tailed_data():
    returns = _fat_tailed_returns()
    xi = hill_estimator(returns, tail_fraction=0.1)
    assert not np.isnan(xi)
    assert xi > 0


def test_evt_var_falls_back_to_historical_when_insufficient_data():
    returns = np.array([0.01, 0.02, 0.01, -0.005])
    evt = evt_var(returns, alpha=0.05)
    hist = historical_var(returns, alpha=0.05)
    assert evt == hist


def test_evt_var_negative_for_fat_tailed_data():
    returns = _fat_tailed_returns()
    evt99 = evt_var(returns, alpha=0.01, tail_fraction=0.1)
    assert evt99 < 0


def test_compute_tail_risk_report_basic():
    prices = 100 * np.cumprod(1 + _fat_tailed_returns(seed=2, n=300))
    report = compute_tail_risk_report(prices)
    assert isinstance(report, TailRiskReport)
    assert report.n == 299
    assert report.historical_var_95 < 0
    assert report.evt_var_99 <= report.evt_var_95  # 99% VaR daha derin olmali (daha negatif)


def test_compute_tail_risk_report_empty_prices():
    report = compute_tail_risk_report(np.array([100.0]))
    assert report.n == 0
    assert report.historical_var_95 == 0.0


def test_tail_risk_cap_reduces_size_when_cvar_high():
    report = TailRiskReport(
        n=100,
        historical_var_95=-0.15,
        historical_cvar_95=-0.20,
        hill_tail_index=0.4,
        evt_var_95=-0.18,
        evt_var_99=-0.25,
        is_fat_tailed=True,
    )
    capped = tail_risk_cap(1.0, report, max_cvar_loss_pct=0.1)
    assert capped == 0.5  # 0.10 / 0.20


def test_tail_risk_cap_noop_when_cvar_zero():
    report = TailRiskReport(
        n=0, historical_var_95=0.0, historical_cvar_95=0.0,
        hill_tail_index=float("nan"), evt_var_95=0.0, evt_var_99=0.0,
        is_fat_tailed=False,
    )
    assert tail_risk_cap(0.3, report) == 0.3


def test_tail_risk_cap_never_below_zero_or_negative_size():
    report = TailRiskReport(
        n=10, historical_var_95=-0.1, historical_cvar_95=-0.1,
        hill_tail_index=0.5, evt_var_95=-0.1, evt_var_99=-0.15,
        is_fat_tailed=False,
    )
    assert tail_risk_cap(-0.5, report) >= 0.0
