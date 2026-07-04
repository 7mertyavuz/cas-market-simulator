from datetime import datetime, timezone

from cas_market_simulator.agents.liquidation_engine import LeveragedPosition, LiquidationEngineAgent
from cas_market_simulator.environment.base import EnvironmentState


def state(price, tick):
    return EnvironmentState(symbol="SIM/USDT", price=price, tick=tick, ts=datetime.now(timezone.utc))


def test_leveraged_position_long_triggers_on_drop():
    pos = LeveragedPosition(side="long", entry_price=100.0, size=1.0, leverage=10.0, maintenance_margin=0.0)
    assert not pos.liquidation_triggered(95.0)  # %5 dusus, esik %10
    assert pos.liquidation_triggered(89.0)       # %11 dusus, esigi asti


def test_leveraged_position_short_triggers_on_rise():
    pos = LeveragedPosition(side="short", entry_price=100.0, size=1.0, leverage=10.0, maintenance_margin=0.0)
    assert not pos.liquidation_triggered(105.0)
    assert pos.liquidation_triggered(111.0)


def test_engine_never_opens_without_price():
    engine = LiquidationEngineAgent(open_probability=1.0)
    assert engine.decide() is None  # observe hic cagrilmadi


def test_engine_opens_positions_over_time():
    engine = LiquidationEngineAgent(open_probability=1.0, seed=1)
    for i in range(5):
        engine.observe(state(100.0, i))
        engine.decide()
    assert len(engine.positions) > 0


def test_engine_never_opens_with_zero_probability():
    engine = LiquidationEngineAgent(open_probability=0.0, seed=1)
    for i in range(10):
        engine.observe(state(100.0, i))
        engine.decide()
    assert len(engine.positions) == 0


def test_engine_liquidates_long_on_crash_and_sells():
    engine = LiquidationEngineAgent(open_probability=0.0, seed=1)
    engine.positions.append(LeveragedPosition(side="long", entry_price=100.0, size=2.0, leverage=10.0, maintenance_margin=0.0))
    engine.observe(state(85.0, 0))  # %15 dusus, 10x kaldiracta esik asildi
    order = engine.decide()
    assert order is not None
    assert order.side == "sell"
    assert engine.liquidation_events == 1
    assert len(engine.positions) == 0


def test_engine_liquidates_short_on_rally_and_buys():
    engine = LiquidationEngineAgent(open_probability=0.0, seed=1)
    engine.positions.append(LeveragedPosition(side="short", entry_price=100.0, size=2.0, leverage=10.0, maintenance_margin=0.0))
    engine.observe(state(116.0, 0))
    order = engine.decide()
    assert order is not None
    assert order.side == "buy"


def test_engine_on_fill_is_noop():
    from cas_market_simulator.environment.base import Order

    engine = LiquidationEngineAgent()
    engine.on_fill(Order(agent_id="x", symbol="SIM/USDT", side="buy", size=1.0), fill_price=100.0)
    assert engine.position == 0.0  # taban sinif PnL'i etkilenmedi
