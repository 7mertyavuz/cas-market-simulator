from datetime import datetime, timezone

from cas_market_simulator.agents.herd import HerdAgent
from cas_market_simulator.agents.noop import NoopAgent
from cas_market_simulator.environment.base import EnvironmentState


def state(price, tick):
    return EnvironmentState(symbol="SIM/USDT", price=price, tick=tick, ts=datetime.now(timezone.utc))


def test_no_order_without_peers():
    agent = HerdAgent()
    agent.observe(state(100, 0))
    assert agent.decide() is None


def test_no_order_when_all_peers_flat():
    peer = NoopAgent("p1")
    agent = HerdAgent(peers=[peer])
    agent.observe(state(100, 0))
    assert agent.decide() is None


def test_imitates_most_profitable_long_peer():
    winner = NoopAgent("winner")
    winner.position = 3.0
    winner.avg_entry_price = 90.0  # fiyat 100'de, buyuk kazanc

    loser = NoopAgent("loser")
    loser.position = -2.0
    loser.avg_entry_price = 95.0  # short pozisyonda, fiyat yukseldigi icin zararda

    agent = HerdAgent(peers=[winner, loser])
    agent.observe(state(100, 0))
    order = agent.decide()
    assert order is not None
    assert order.side == "buy"
    assert agent.last_imitated_agent_id == "winner"


def test_imitates_most_profitable_short_peer():
    winner = NoopAgent("winner")
    winner.position = -3.0
    winner.avg_entry_price = 110.0  # short, fiyat 100'e dustu -> kazancta

    agent = HerdAgent(peers=[winner])
    agent.observe(state(100, 0))
    order = agent.decide()
    assert order is not None
    assert order.side == "sell"


def test_set_peers_after_construction():
    agent = HerdAgent()
    peer = NoopAgent("p1")
    peer.position = 1.0
    peer.avg_entry_price = 90.0
    agent.set_peers([peer])
    agent.observe(state(100, 0))
    order = agent.decide()
    assert order is not None


def test_imitation_count_increments():
    peer = NoopAgent("p1")
    peer.position = 1.0
    peer.avg_entry_price = 90.0
    agent = HerdAgent(peers=[peer])
    for i in range(3):
        agent.observe(state(100, i))
        agent.decide()
    assert agent.imitation_count == 3
