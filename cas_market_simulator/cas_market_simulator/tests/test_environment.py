import pytest

from cas_market_simulator.environment.base import Environment, Order


def test_environment_init_state():
    env = Environment("SIM/USDT", 100.0)
    assert env.state.price == 100.0
    assert env.state.tick == 0


def test_environment_rejects_bad_start_price():
    with pytest.raises(ValueError):
        Environment("SIM/USDT", 0.0)


def test_order_validates_side():
    with pytest.raises(ValueError):
        Order(agent_id="a", symbol="SIM/USDT", side="hold", size=1.0)


def test_order_validates_size():
    with pytest.raises(ValueError):
        Order(agent_id="a", symbol="SIM/USDT", side="buy", size=0.0)


def test_step_with_no_orders_keeps_price():
    env = Environment("SIM/USDT", 100.0)
    state = env.step()
    assert state.price == 100.0
    assert state.tick == 1


def test_buy_pressure_increases_price():
    env = Environment("SIM/USDT", 100.0, impact=0.01)
    env.submit(Order(agent_id="a", symbol="SIM/USDT", side="buy", size=5.0))
    state = env.step()
    assert state.price > 100.0


def test_sell_pressure_decreases_price():
    env = Environment("SIM/USDT", 100.0, impact=0.01)
    env.submit(Order(agent_id="a", symbol="SIM/USDT", side="sell", size=5.0))
    state = env.step()
    assert state.price < 100.0


def test_submit_rejects_wrong_symbol():
    env = Environment("SIM/USDT", 100.0)
    with pytest.raises(ValueError):
        env.submit(Order(agent_id="a", symbol="OTHER/USDT", side="buy", size=1.0))


def test_history_accumulates():
    env = Environment("SIM/USDT", 100.0)
    for _ in range(3):
        env.step()
    assert len(env.history) == 4  # baslangic + 3 step
