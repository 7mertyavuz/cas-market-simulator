from cas_market_simulator.agents.noop import NoopAgent
from cas_market_simulator.environment.base import Order


def buy(size=1.0):
    return Order(agent_id="a", symbol="SIM/USDT", side="buy", size=size)


def sell(size=1.0):
    return Order(agent_id="a", symbol="SIM/USDT", side="sell", size=size)


def test_initial_state_flat():
    agent = NoopAgent()
    assert agent.position == 0.0
    assert agent.realized_pnl == 0.0
    assert agent.total_pnl(100.0) == 0.0


def test_single_buy_sets_position_and_entry():
    agent = NoopAgent()
    agent.on_fill(buy(2.0), fill_price=100.0)
    assert agent.position == 2.0
    assert agent.avg_entry_price == 100.0


def test_unrealized_pnl_long_position():
    agent = NoopAgent()
    agent.on_fill(buy(2.0), fill_price=100.0)
    assert agent.unrealized_pnl(110.0) == 20.0
    assert agent.unrealized_pnl(90.0) == -20.0


def test_adding_to_position_averages_entry_price():
    agent = NoopAgent()
    agent.on_fill(buy(1.0), fill_price=100.0)
    agent.on_fill(buy(1.0), fill_price=110.0)
    assert agent.position == 2.0
    assert agent.avg_entry_price == 105.0


def test_partial_close_realizes_pnl():
    agent = NoopAgent()
    agent.on_fill(buy(2.0), fill_price=100.0)
    agent.on_fill(sell(1.0), fill_price=110.0)
    assert agent.position == 1.0
    assert agent.realized_pnl == 10.0
    assert agent.avg_entry_price == 100.0  # kalan pozisyonun maliyeti degismez


def test_full_close_flattens_position():
    agent = NoopAgent()
    agent.on_fill(buy(2.0), fill_price=100.0)
    agent.on_fill(sell(2.0), fill_price=105.0)
    assert agent.position == 0.0
    assert agent.avg_entry_price is None
    assert agent.realized_pnl == 10.0


def test_position_flip_realizes_and_reopens():
    agent = NoopAgent()
    agent.on_fill(buy(1.0), fill_price=100.0)
    agent.on_fill(sell(3.0), fill_price=110.0)  # 1 birim kapanir, 2 birim short acilir
    assert agent.position == -2.0
    assert agent.realized_pnl == 10.0
    assert agent.avg_entry_price == 110.0


def test_short_position_pnl_direction():
    agent = NoopAgent()
    agent.on_fill(sell(1.0), fill_price=100.0)
    assert agent.position == -1.0
    assert agent.unrealized_pnl(90.0) == 10.0  # fiyat dustu, short kazandi
    assert agent.unrealized_pnl(110.0) == -10.0


def test_total_pnl_combines_realized_and_unrealized():
    agent = NoopAgent()
    agent.on_fill(buy(2.0), fill_price=100.0)
    agent.on_fill(sell(1.0), fill_price=110.0)  # +10 gerceklesen
    assert agent.total_pnl(120.0) == 10.0 + 20.0  # kalan 1 birim @120 = +20 anlik
