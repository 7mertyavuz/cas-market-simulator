from datetime import datetime, timezone

from cas_market_simulator.agents.adaptive import AdaptiveAgent
from cas_market_simulator.environment.base import EnvironmentState


def state(price, tick):
    return EnvironmentState(symbol="SIM/USDT", price=price, tick=tick, ts=datetime.now(timezone.utc))


def test_no_mutation_before_evaluation_interval():
    agent = AdaptiveAgent(evaluation_interval=100, seed=1)
    for i in range(10):
        agent.observe(state(100.0, i))
    assert agent.mutation_count == 0


def test_mutates_after_losing_window():
    agent = AdaptiveAgent(evaluation_interval=5, seed=1, threshold_pct=0.003, size=1.0)
    # elle zarar yazdiralim (bir pozisyon acip fiyat aleyhine gitsin)
    agent.position = 2.0
    agent.avg_entry_price = 100.0
    for i in range(5):
        agent.observe(state(90.0, i))  # zarar durumu (unrealized negatif)
    assert agent.mutation_count == 1
    assert agent.param_history[-1] != agent.param_history[0]


def test_no_mutation_when_winning():
    agent = AdaptiveAgent(evaluation_interval=5, seed=1, threshold_pct=0.003, size=1.0)
    agent.position = 2.0
    agent.avg_entry_price = 100.0
    for i in range(5):
        agent.observe(state(110.0, i))  # kazanc durumu
    assert agent.mutation_count == 0
    assert agent.threshold_pct == 0.003
    assert agent.size == 1.0


def test_threshold_never_below_minimum():
    agent = AdaptiveAgent(evaluation_interval=1, seed=2, threshold_pct=0.001, min_threshold_pct=0.0009, mutation_scale=0.9)
    agent.position = 1.0
    agent.avg_entry_price = 100.0
    for i in range(20):
        agent.observe(state(50.0, i))  # surekli zarar -> surekli mutasyon
    assert agent.threshold_pct >= 0.0009


def test_size_never_exceeds_max():
    agent = AdaptiveAgent(evaluation_interval=1, seed=3, size=1.0, max_size=2.0, mutation_scale=0.9)
    agent.position = 1.0
    agent.avg_entry_price = 100.0
    for i in range(30):
        agent.observe(state(50.0, i))
    assert agent.size <= 2.0


def test_decide_follows_current_threshold():
    agent = AdaptiveAgent(lookback=3, threshold_pct=0.001, size=1.0, evaluation_interval=1000)
    for i, p in enumerate([100, 101, 102, 103]):
        agent.observe(state(p, i))
    order = agent.decide()
    assert order is not None
    assert order.side == "buy"
