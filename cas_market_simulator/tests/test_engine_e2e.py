import logging

from cas_market_simulator.adapters.factor_brain import StubFactorBrain
from cas_market_simulator.adapters.flow_feed import StubFlowFeed
from cas_market_simulator.adapters.sentiment_feed import StubSentimentFeed
from cas_market_simulator.agents.noop import NoopAgent
from cas_market_simulator.engine.loop import Engine, SimulationConfig


def test_e2e_tick_loop_runs_and_logs(caplog):
    """Faz 0 'Bitti' kriteri: stub feed -> tek bos ajan -> bos environment
    -> log basan bir tick dongusu calisiyor."""
    config = SimulationConfig(symbol="SIM/USDT", n_ticks=5, start_price=100.0)
    engine = Engine(
        config,
        agents=[NoopAgent()],
        sentiment_feed=StubSentimentFeed(),
        flow_feed=StubFlowFeed(),
        factor_brain=StubFactorBrain(),
    )

    with caplog.at_level(logging.INFO, logger="cas.engine"):
        results = engine.run()

    assert len(results) == 5
    assert all(r.card_direction == "NEUTRAL" for r in results)
    assert results[-1].tick == 5
    # noop ajan emirsiz oldugu icin fiyat sabit kalmali
    assert all(r.state.price == 100.0 for r in results)
    assert "simulasyon basliyor" in caplog.text
    assert "simulasyon bitti" in caplog.text


def test_e2e_without_brain_defaults_neutral():
    config = SimulationConfig(symbol="SIM/USDT", n_ticks=3, start_price=50.0)
    engine = Engine(config, agents=[NoopAgent()])
    results = engine.run()
    assert all(r.card_direction == "NEUTRAL" and r.card_confidence == 0.0 for r in results)


def test_e2e_multiple_agents():
    config = SimulationConfig(symbol="SIM/USDT", n_ticks=2, start_price=100.0)
    agents = [NoopAgent("a1"), NoopAgent("a2"), NoopAgent("a3")]
    engine = Engine(config, agents=agents)
    results = engine.run()
    assert len(results) == 2
    assert len(engine.agents) == 3
