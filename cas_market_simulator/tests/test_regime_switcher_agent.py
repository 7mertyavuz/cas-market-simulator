from datetime import datetime, timezone

from cas_market_simulator.agents.regime_switcher import RegimeSwitcherAgent
from cas_market_simulator.environment.base import EnvironmentState


def state(price, tick):
    return EnvironmentState(symbol="SIM/USDT", price=price, tick=tick, ts=datetime.now(timezone.utc))


def test_no_order_before_lookback_filled():
    agent = RegimeSwitcherAgent(lookback=10)
    agent.observe(state(100, 0))
    assert agent.decide() is None


def test_detects_trend_regime_on_monotonic_move():
    agent = RegimeSwitcherAgent(lookback=10, efficiency_threshold=0.5)
    for i in range(10):
        agent.observe(state(100 + i, i))
    assert agent.current_mode == "trend"


def test_detects_mean_revert_regime_on_choppy_move():
    agent = RegimeSwitcherAgent(lookback=10, efficiency_threshold=0.5)
    prices = [100, 102, 99, 103, 98, 104, 97, 105, 96, 100]
    for i, p in enumerate(prices):
        agent.observe(state(p, i))
    assert agent.current_mode == "mean_revert"


def test_trend_mode_buys_on_uptrend():
    agent = RegimeSwitcherAgent(lookback=5, efficiency_threshold=0.3)
    for i in range(5):
        agent.observe(state(100 + i * 2, i))
    assert agent.current_mode == "trend"
    order = agent.decide()
    assert order is not None
    assert order.side == "buy"


def test_mean_revert_mode_sells_when_extended_up():
    agent = RegimeSwitcherAgent(lookback=6, efficiency_threshold=0.9)
    prices = [100, 102, 99, 101, 98, 115]  # cirpinti + son barda asiri sicrama
    for i, p in enumerate(prices):
        agent.observe(state(p, i))
    assert agent.current_mode == "mean_revert"
    order = agent.decide()
    assert order is not None
    assert order.side == "sell"
