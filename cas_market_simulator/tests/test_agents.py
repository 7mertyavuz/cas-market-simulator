from cas_market_simulator.agents.noop import NoopAgent
from cas_market_simulator.environment.base import Environment


def test_noop_agent_never_submits_order():
    env = Environment("SIM/USDT", 100.0)
    agent = NoopAgent()
    agent.observe(env.state)
    assert agent.decide() is None
    agent.act(env)
    state = env.step()
    assert state.price == 100.0  # emirsiz, fiyat sabit


def test_noop_agent_tracks_last_seen():
    env = Environment("SIM/USDT", 100.0)
    agent = NoopAgent()
    agent.observe(env.state)
    assert agent.last_seen is not None
    assert agent.last_seen.price == 100.0
