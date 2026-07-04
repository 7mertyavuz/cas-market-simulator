from datetime import datetime, timezone

from cas_market_simulator.adapters.contracts import ShockEvent
from cas_market_simulator.agents.noop import NoopAgent
from cas_market_simulator.agents.news_reactor import NewsReactorAgent
from cas_market_simulator.engine.loop import Engine, SimulationConfig


def test_scripted_panic_shock_pushes_price_down():
    shock = ShockEvent(kind="panic", entity="market", magnitude=1.0, decay_halflife_s=300.0, ts=datetime.now(timezone.utc))
    config = SimulationConfig(symbol="SIM/USDT", n_ticks=1, start_price=100.0, shock_impact_scale=50.0)
    engine = Engine(config, agents=[NoopAgent()], scripted_shocks={0: shock})
    results = engine.run()
    assert results[0].state.price < 100.0
    assert results[0].active_shock_magnitude > 0.0


def test_scripted_euphoria_shock_pushes_price_up():
    shock = ShockEvent(kind="euphoria", entity="market", magnitude=1.0, decay_halflife_s=300.0, ts=datetime.now(timezone.utc))
    config = SimulationConfig(symbol="SIM/USDT", n_ticks=1, start_price=100.0, shock_impact_scale=50.0)
    engine = Engine(config, agents=[NoopAgent()], scripted_shocks={0: shock})
    results = engine.run()
    assert results[0].state.price > 100.0


def test_shock_decays_over_ticks():
    shock = ShockEvent(kind="panic", entity="market", magnitude=1.0, decay_halflife_s=60.0, ts=datetime.now(timezone.utc))
    config = SimulationConfig(symbol="SIM/USDT", n_ticks=20, start_price=100.0, shock_impact_scale=50.0, seconds_per_tick=60.0)
    engine = Engine(config, agents=[NoopAgent()], scripted_shocks={0: shock})
    results = engine.run()
    # halflife=60s, seconds_per_tick=60s -> her tick yarilanir; sonunda etkisiz kalmali
    assert results[-1].active_shock_magnitude < results[0].active_shock_magnitude
    assert results[-1].active_shock_magnitude == 0.0


def test_no_shock_no_price_impact_beyond_orders():
    config = SimulationConfig(symbol="SIM/USDT", n_ticks=5, start_price=100.0)
    engine = Engine(config, agents=[NoopAgent()])
    results = engine.run()
    assert all(r.state.price == 100.0 for r in results)
    assert all(r.active_shock_magnitude == 0.0 for r in results)


def test_news_reactor_receives_scripted_shock_and_reacts():
    shock = ShockEvent(kind="panic", entity="market", magnitude=0.9, decay_halflife_s=300.0, ts=datetime.now(timezone.utc))
    config = SimulationConfig(symbol="SIM/USDT", n_ticks=2, start_price=100.0, shock_impact_scale=0.0)
    reactor = NewsReactorAgent(react_threshold=0.05, base_size=5.0)
    engine = Engine(config, agents=[reactor], scripted_shocks={0: shock})
    engine.run()
    # sok reactor'e ulasti ve pozisyon aldi (satti) -- position negatif olmali
    assert reactor.position < 0.0


def test_feed_shocks_are_collected():
    class StubShockFeed:
        def __init__(self):
            self.calls = 0

        def latest(self, entity):
            raise NotImplementedError

        def shocks(self, since):
            self.calls += 1
            if self.calls == 1:
                return [ShockEvent(kind="euphoria", entity="market", magnitude=0.5, decay_halflife_s=120.0, ts=datetime.now(timezone.utc))]
            return []

    config = SimulationConfig(symbol="SIM/USDT", n_ticks=3, start_price=100.0, shock_impact_scale=50.0)
    engine = Engine(config, agents=[NoopAgent()], sentiment_feed=StubShockFeed())
    results = engine.run()
    assert results[0].state.price > 100.0
