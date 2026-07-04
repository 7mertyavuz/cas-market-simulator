from datetime import datetime, timezone

from cas_market_simulator.agents.market_maker import MarketMakerAgent
from cas_market_simulator.agents.momentum import MomentumAgent
from cas_market_simulator.agents.panic import PanicAgent
from cas_market_simulator.environment.base import EnvironmentState


def state(price, tick):
    return EnvironmentState(symbol="SIM/USDT", price=price, tick=tick, ts=datetime.now(timezone.utc))


def test_momentum_no_order_before_lookback_filled():
    agent = MomentumAgent(lookback=5)
    agent.observe(state(100, 0))
    assert agent.decide() is None


def test_momentum_buys_on_uptrend():
    agent = MomentumAgent(lookback=3, threshold_pct=0.001)
    for i, p in enumerate([100, 101, 102, 103]):
        agent.observe(state(p, i))
    order = agent.decide()
    assert order is not None
    assert order.side == "buy"


def test_momentum_sells_on_downtrend():
    agent = MomentumAgent(lookback=3, threshold_pct=0.001)
    for i, p in enumerate([100, 99, 98, 97]):
        agent.observe(state(p, i))
    order = agent.decide()
    assert order is not None
    assert order.side == "sell"


def test_momentum_flat_market_no_order():
    agent = MomentumAgent(lookback=3, threshold_pct=0.01)
    for i, p in enumerate([100, 100.1, 99.9, 100.0]):
        agent.observe(state(p, i))
    assert agent.decide() is None


def test_market_maker_quotes_when_calm():
    mm = MarketMakerAgent(vol_lookback=5, vol_pull_threshold_pct=0.5)
    for i in range(5):
        mm.observe(state(100 + i * 0.01, i))
    assert mm.decide() is not None


def test_market_maker_pulls_back_on_high_volatility():
    mm = MarketMakerAgent(vol_lookback=5, vol_pull_threshold_pct=0.01)
    prices = [100, 105, 95, 110, 90]  # yuksek oynaklik
    for i, p in enumerate(prices):
        mm.observe(state(p, i))
    assert mm.decide() is None


def test_market_maker_reduces_inventory_when_limit_hit():
    mm = MarketMakerAgent(vol_lookback=5, vol_pull_threshold_pct=0.5, inventory_limit=2.0)
    for i in range(5):
        mm.observe(state(100, i))
    mm.position = 3.0  # envanter siniri asildi (long)
    order = mm.decide()
    assert order is not None
    assert order.side == "sell"


def test_panic_no_position_no_drawdown_buys_euphoria():
    agent = PanicAgent()
    agent.observe(state(100, 0))
    order = agent.decide()
    assert order is not None
    assert order.side == "buy"


def test_panic_sells_after_confirmed_drawdown():
    agent = PanicAgent(drawdown_threshold_pct=0.02, confirmation_ticks=2, size=1.0)
    agent.position = 5.0
    agent.avg_entry_price = 100.0
    prices = [100, 100, 99, 97, 95]  # zirve 100, sonra ardisik dususler
    for i, p in enumerate(prices):
        agent.observe(state(p, i))
    order = agent.decide()
    assert order is not None
    assert order.side == "sell"


def test_panic_does_not_sell_without_confirmation():
    agent = PanicAgent(drawdown_threshold_pct=0.01, confirmation_ticks=5)
    agent.position = 5.0
    agent.avg_entry_price = 100.0
    prices = [100, 99, 98]  # dusus var ama yeterince ardisik degil
    for i, p in enumerate(prices):
        agent.observe(state(p, i))
    order = agent.decide()
    assert order is None or order.side == "buy"  # satis tetiklenmemis olmali
