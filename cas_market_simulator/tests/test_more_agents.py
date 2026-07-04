from datetime import datetime, timedelta, timezone

from cas_market_simulator.adapters.contracts import ShockEvent
from cas_market_simulator.agents.arbitrage import ArbitrageAgent
from cas_market_simulator.agents.contrarian import ContrarianAgent
from cas_market_simulator.agents.mev import MevAgent
from cas_market_simulator.agents.news_reactor import NewsReactorAgent
from cas_market_simulator.agents.whale import WhaleAgent
from cas_market_simulator.environment.base import EnvironmentState


def state(price, tick):
    return EnvironmentState(symbol="SIM/USDT", price=price, tick=tick, ts=datetime.now(timezone.utc))


def test_whale_mostly_silent():
    agent = WhaleAgent(seed=1, trade_probability=0.03)
    orders = []
    for i in range(200):
        agent.observe(state(100.0, i))
        o = agent.decide()
        if o is not None:
            orders.append(o)
    assert 0 < len(orders) < 40  # nadir ama sifir degil


def test_whale_never_trades_zero_probability():
    agent = WhaleAgent(seed=1, trade_probability=0.0)
    for i in range(50):
        agent.observe(state(100.0, i))
        assert agent.decide() is None


def test_arbitrage_no_order_when_close_to_reference():
    agent = ArbitrageAgent(seed=1, deviation_threshold_pct=0.5)
    agent.observe(state(100.0, 0))
    assert agent.decide() is None


def test_arbitrage_sells_when_price_above_reference():
    agent = ArbitrageAgent(seed=1, deviation_threshold_pct=0.01, reference_vol_pct=0.0)
    agent.observe(state(100.0, 0))
    agent.observe(state(103.0, 1))  # referans hala ~100, fiyat %3 yukarida
    order = agent.decide()
    assert order is not None
    assert order.side == "sell"


def test_arbitrage_buys_when_price_below_reference():
    agent = ArbitrageAgent(seed=1, deviation_threshold_pct=0.01, reference_vol_pct=0.0)
    agent.observe(state(100.0, 0))
    agent.observe(state(97.0, 1))
    order = agent.decide()
    assert order is not None
    assert order.side == "buy"


def test_mev_no_order_before_two_prices():
    agent = MevAgent()
    agent.observe(state(100.0, 0))
    assert agent.decide() is None


def test_mev_follows_recent_move_up():
    agent = MevAgent(min_move_pct=0.001)
    agent.observe(state(100.0, 0))
    agent.observe(state(101.0, 1))
    order = agent.decide()
    assert order is not None
    assert order.side == "buy"


def test_mev_follows_recent_move_down():
    agent = MevAgent(min_move_pct=0.001)
    agent.observe(state(100.0, 0))
    agent.observe(state(99.0, 1))
    order = agent.decide()
    assert order is not None
    assert order.side == "sell"


def test_news_reactor_ignores_below_threshold():
    agent = NewsReactorAgent(react_threshold=0.05)
    agent.observe(state(100.0, 0))
    shock = ShockEvent(kind="panic", entity="market", magnitude=0.01, decay_halflife_s=300.0, ts=datetime.now(timezone.utc))
    agent.on_shock(shock)
    assert agent.decide() is None


def test_news_reactor_sells_on_panic():
    agent = NewsReactorAgent(react_threshold=0.05, base_size=10.0)
    agent.observe(state(100.0, 0))
    shock = ShockEvent(kind="panic", entity="market", magnitude=0.8, decay_halflife_s=300.0, ts=datetime.now(timezone.utc))
    agent.on_shock(shock)
    order = agent.decide()
    assert order is not None
    assert order.side == "sell"


def test_news_reactor_buys_on_euphoria():
    agent = NewsReactorAgent(react_threshold=0.05, base_size=10.0)
    agent.observe(state(100.0, 0))
    shock = ShockEvent(kind="euphoria", entity="market", magnitude=0.8, decay_halflife_s=300.0, ts=datetime.now(timezone.utc))
    agent.on_shock(shock)
    order = agent.decide()
    assert order is not None
    assert order.side == "buy"


def test_news_reactor_decays_over_time():
    agent = NewsReactorAgent(react_threshold=0.05, base_size=10.0)
    agent.observe(state(100.0, 0))
    old_shock = ShockEvent(
        kind="panic", entity="market", magnitude=0.5, decay_halflife_s=1.0,
        ts=datetime.now(timezone.utc) - timedelta(seconds=100),
    )
    agent.on_shock(old_shock)
    assert agent.decide() is None  # cok eski, magnitude sifira yakin sondu


def test_contrarian_no_order_before_lookback():
    agent = ContrarianAgent(lookback=5)
    agent.observe(state(100.0, 0))
    assert agent.decide() is None


def test_contrarian_sells_when_overextended_up():
    agent = ContrarianAgent(lookback=3, extension_threshold_pct=0.02)
    for i, p in enumerate([100, 100, 100]):
        agent.observe(state(p, i))
    agent.observe(state(110.0, 3))
    order = agent.decide()
    assert order is not None
    assert order.side == "sell"


def test_contrarian_buys_when_overextended_down():
    agent = ContrarianAgent(lookback=3, extension_threshold_pct=0.02)
    for i, p in enumerate([100, 100, 100]):
        agent.observe(state(p, i))
    agent.observe(state(90.0, 3))
    order = agent.decide()
    assert order is not None
    assert order.side == "buy"
