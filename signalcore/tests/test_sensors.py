from signalcore.indicators.cross_exchange import (
    CrossExchangeState,
    SimCrossExchangeFeed,
    cross_exchange_factor,
)
from signalcore.indicators.derivatives import DerivativesState, SimDerivativesFeed, derivatives_factor
from signalcore.indicators.intermarket import IntermarketState, SimIntermarketFeed, intermarket_factor
from signalcore.indicators.onchain import OnchainState, SimOnchainFeed, onchain_factor
from signalcore.indicators.orderbook import OrderbookState, SimOrderbookFeed, orderbook_factor
from signalcore.indicators.sensors import compute_sensor_votes


def test_derivatives_factor_bounds_and_sim_feed():
    feed = SimDerivativesFeed(seed=1)
    for _ in range(30):
        state = feed.latest("BTC")
        v = derivatives_factor(state)
        assert -1.0 <= v.vote <= 1.0
        assert v.name == "derivatives"


def test_derivatives_factor_direction_with_positive_funding_and_oi():
    state = DerivativesState(funding_rate=0.01, oi_change_pct=0.1, basis_pct=0.02, iv_percentile=50, put_call_ratio=1.0)
    v = derivatives_factor(state, funding_extreme=0.005)
    assert v.vote > 0


def test_orderbook_factor_bounds_and_sim_feed():
    feed = SimOrderbookFeed(seed=2)
    for _ in range(30):
        state = feed.latest("BTC")
        v = orderbook_factor(state)
        assert -1.0 <= v.vote <= 1.0


def test_orderbook_factor_wide_spread_reduces_magnitude():
    narrow = OrderbookState(spread_bps=1.0, depth_imbalance=0.8, liquidation_map_skew=0.0)
    wide = OrderbookState(spread_bps=100.0, depth_imbalance=0.8, liquidation_map_skew=0.0)
    v_narrow = orderbook_factor(narrow)
    v_wide = orderbook_factor(wide)
    assert abs(v_wide.vote) < abs(v_narrow.vote)


def test_onchain_factor_bounds_and_sim_feed():
    feed = SimOnchainFeed(seed=3)
    for _ in range(30):
        state = feed.latest("BTC")
        v = onchain_factor(state)
        assert -1.0 <= v.vote <= 1.0


def test_onchain_factor_outflow_is_bullish():
    outflow = OnchainState(exchange_netflow_usd=-6_000_000, stablecoin_supply_change_pct=0, active_addresses_change_pct=0, nvt_zscore=0, etf_flow_usd=0)
    v = onchain_factor(outflow)
    assert v.vote > 0


def test_intermarket_factor_bounds_and_sim_feed():
    feed = SimIntermarketFeed(seed=4)
    for _ in range(30):
        state = feed.latest("BTC")
        v = intermarket_factor(state)
        assert -1.0 <= v.vote <= 1.0


def test_intermarket_factor_risk_on_is_bullish():
    state = IntermarketState(dxy_change_pct=0, gold_change_pct=0, us10y_change_bps=0, spx_change_pct=0, risk_on_off_score=0.9)
    v = intermarket_factor(state)
    assert v.vote > 0


def test_cross_exchange_factor_bounds_and_sim_feed():
    feed = SimCrossExchangeFeed(seed=5)
    for _ in range(30):
        state = feed.latest("BTC")
        v = cross_exchange_factor(state)
        assert -1.0 <= v.vote <= 1.0


def test_cross_exchange_factor_positive_premium_is_bullish():
    state = CrossExchangeState(coinbase_premium_bps=20.0, lead_lag_spread=0.0, price_diff_pct=0.0)
    v = cross_exchange_factor(state)
    assert v.vote > 0


def test_compute_sensor_votes_empty():
    assert compute_sensor_votes(None) == []
    assert compute_sensor_votes({}) == []


def test_compute_sensor_votes_all_five():
    states = {
        "derivatives": SimDerivativesFeed(seed=1).latest("BTC"),
        "orderbook": SimOrderbookFeed(seed=2).latest("BTC"),
        "onchain": SimOnchainFeed(seed=3).latest("BTC"),
        "intermarket": SimIntermarketFeed(seed=4).latest("BTC"),
        "cross_exchange": SimCrossExchangeFeed(seed=5).latest("BTC"),
    }
    votes = compute_sensor_votes(states)
    assert len(votes) == 5
    names = {v.name for v in votes}
    assert names == {"derivatives", "orderbook", "onchain", "intermarket", "cross_exchange"}
    for v in votes:
        assert v.weight == 0.2


def test_compute_sensor_votes_ignores_unknown_key():
    votes = compute_sensor_votes({"unknown_sensor": object()})
    assert votes == []


def test_compute_sensor_votes_ignores_type_mismatch():
    votes = compute_sensor_votes({"derivatives": OrderbookState(spread_bps=1, depth_imbalance=0, liquidation_map_skew=0)})
    assert votes == []
