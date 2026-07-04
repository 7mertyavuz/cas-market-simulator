import numpy as np
import pytest

from cas_market_simulator.analysis.portfolio import (
    PortfolioAllocation,
    apply_correlation_limit,
    build_portfolio,
    hrp_weights,
    scale_to_risk_budget,
)


def _synthetic_returns(n_obs=500, n_assets=4, seed=0):
    rng = np.random.default_rng(seed)
    # ortak faktor + varlik-ozel gurultu -> gerceci pozitif korelasyon
    common = rng.normal(0, 0.01, n_obs)
    idio = rng.normal(0, 0.008, (n_obs, n_assets))
    returns = idio + common.reshape(-1, 1) * 0.6
    return returns


def test_hrp_weights_single_asset():
    w = hrp_weights(np.random.default_rng(0).normal(0, 0.01, 100), symbols=["BTC"])
    assert w == {"BTC": 1.0}


def test_hrp_weights_sum_to_one():
    returns = _synthetic_returns()
    symbols = ["BTC", "ETH", "SOL", "AVAX"]
    w = hrp_weights(returns, symbols)
    assert set(w.keys()) == set(symbols)
    assert abs(sum(w.values()) - 1.0) < 1e-9
    for v in w.values():
        assert v > 0.0


def test_hrp_weights_requires_matching_symbol_count():
    returns = _synthetic_returns(n_assets=3)
    with pytest.raises(ValueError):
        hrp_weights(returns, symbols=["A", "B"])


def test_hrp_diversifies_low_corr_more_than_naive_equal_weight_bias():
    # birbiriyle dusuk korelasyonlu iki varlik + birbiriyle yuksek korelasyonlu iki varlik
    rng = np.random.default_rng(1)
    n = 400
    a = rng.normal(0, 0.01, n)
    b = a + rng.normal(0, 0.001, n)  # b, a ile neredeyse ayni (yuksek korelasyon)
    c = rng.normal(0, 0.01, n)       # bagimsiz
    d = rng.normal(0, 0.01, n)       # bagimsiz
    returns = np.column_stack([a, b, c, d])
    w = hrp_weights(returns, ["A", "B", "C", "D"])
    # yuksek-korelasyonlu A,B ciftinin toplam agirligi, HRP'nin kume-farkindaligi
    # sayesinde naif esit-agirligin (0.5) altinda kalmali
    assert w["A"] + w["B"] < 0.55


def test_apply_correlation_limit_caps_single_weight():
    symbols = ["A", "B", "C"]
    weights = {"A": 0.7, "B": 0.2, "C": 0.1}
    corr = np.eye(3)
    limited = apply_correlation_limit(weights, corr, symbols, max_single_weight=0.4)
    assert limited["A"] <= 0.4 + 1e-9
    # kirpilan fazlalik baska varliklara geri dagitilmaz (nakit kalir) ->
    # toplam artik 1.0'dan kucuk olmali
    assert sum(limited.values()) < 1.0 - 1e-9


def test_apply_correlation_limit_caps_combined_high_corr_pair():
    symbols = ["A", "B", "C"]
    weights = {"A": 0.4, "B": 0.4, "C": 0.2}
    corr = np.array([
        [1.0, 0.95, 0.1],
        [0.95, 1.0, 0.1],
        [0.1, 0.1, 1.0],
    ])
    limited = apply_correlation_limit(
        weights, corr, symbols, max_pairwise_corr=0.85, max_combined_weight=0.35
    )
    # A+B toplami 0.35 tavanina kirpilmis olmali; fazlalik nakit kalir
    # (baska varliklara dagitilmaz), bu yuzden toplam < 1.0
    assert limited["A"] + limited["B"] <= 0.35 + 1e-9
    assert sum(limited.values()) < 1.0 - 1e-9


def test_scale_to_risk_budget_shrinks_when_above_target():
    symbols = ["A", "B"]
    weights = {"A": 0.5, "B": 0.5}
    cov = np.array([[0.04, 0.0], [0.0, 0.04]])  # yuksek varyans -> ~%20 gunluk vol
    scaled, scale = scale_to_risk_budget(weights, cov, symbols, target_daily_vol=0.02)
    assert scale < 1.0
    w_vec = np.array([scaled[s] for s in symbols])
    port_vol = float(np.sqrt(w_vec @ cov @ w_vec))
    assert port_vol <= 0.02 + 1e-6


def test_scale_to_risk_budget_noop_when_below_target():
    symbols = ["A", "B"]
    weights = {"A": 0.5, "B": 0.5}
    cov = np.array([[0.0001, 0.0], [0.0, 0.0001]])  # dusuk varyans
    scaled, scale = scale_to_risk_budget(weights, cov, symbols, target_daily_vol=0.5)
    assert scale == 1.0
    assert scaled == weights


def test_scale_to_risk_budget_zero_vol_returns_unscaled():
    symbols = ["A"]
    weights = {"A": 1.0}
    cov = np.array([[0.0]])
    scaled, scale = scale_to_risk_budget(weights, cov, symbols, target_daily_vol=0.02)
    assert scale == 1.0
    assert scaled == weights


def test_build_portfolio_end_to_end():
    returns = _synthetic_returns()
    symbols = ["BTC", "ETH", "SOL", "AVAX"]
    alloc = build_portfolio(returns, symbols, target_daily_vol=0.005)
    assert isinstance(alloc, PortfolioAllocation)
    assert set(alloc.final_weights.keys()) == set(symbols)
    assert alloc.portfolio_daily_vol <= 0.005 + 1e-6
    assert alloc.risk_scale <= 1.0


def test_build_portfolio_single_asset_no_crash():
    returns = np.random.default_rng(0).normal(0, 0.01, 200)
    alloc = build_portfolio(returns, ["BTC"], target_daily_vol=0.5)
    assert alloc.final_weights["BTC"] == pytest.approx(1.0)
    assert "korelasyon limiti anlamsiz" in alloc.warnings[0]
