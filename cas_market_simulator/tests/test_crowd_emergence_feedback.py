from cas_market_simulator.adapters.contracts import ShockEvent
from cas_market_simulator.adapters.factor_brain import SignalCoreFactorBrain
from cas_market_simulator.agents.liquidation_engine import LiquidationEngineAgent
from cas_market_simulator.agents.noop import NoopAgent
from cas_market_simulator.agents.panic import PanicAgent
from cas_market_simulator.engine.loop import Engine, SimulationConfig
from datetime import datetime, timezone


def test_crowd_emergence_zero_before_min_ticks():
    config = SimulationConfig(symbol="SIM/USDT", n_ticks=5, start_price=100.0, crowd_emergence_min_ticks=20)
    engine = Engine(config, agents=[NoopAgent()])
    results = engine.run()
    assert all(r.crowd_emergence_score == 0.0 for r in results)


def test_crowd_emergence_score_present_after_min_ticks():
    config = SimulationConfig(symbol="SIM/USDT", n_ticks=40, start_price=100.0, crowd_emergence_min_ticks=20)
    engine = Engine(config, agents=[NoopAgent()])
    results = engine.run()
    assert all(-1.0 <= r.crowd_emergence_score <= 1.0 for r in results)


def test_crowd_emergence_feeds_into_card_as_factor():
    """Faz 7 'Bitti' kriteri: kalabalik okumasi karttaki bir faktor
    haline geliyor mu? scriptli bir panik soku + likidasyon motoruyle
    gercek bir kaskad uretip, kartta 'crowd_emergence' adinda bir oy
    olustugunu dogrular."""
    shock = ShockEvent(kind="panic", entity="market", magnitude=1.0, decay_halflife_s=180.0, ts=datetime.now(timezone.utc))
    config = SimulationConfig(
        symbol="SIM/USDT", n_ticks=150, start_price=100.0,
        shock_impact_scale=30.0, seconds_per_tick=30.0,
        crowd_emergence_min_ticks=20, min_bars_for_brain=30,
    )
    agents = [
        PanicAgent("panic-1", drawdown_threshold_pct=0.015, confirmation_ticks=2, size=2.0),
        LiquidationEngineAgent("liq-0", open_probability=0.2, seed=7),
    ]
    engine = Engine(
        config, agents=agents, factor_brain=SignalCoreFactorBrain(min_bars=30),
        scripted_shocks={80: shock},
    )
    results = engine.run()

    cards_with_crowd_vote = [
        r for r in results
        if r.card is not None and any(v.name == "crowd_emergence" for v in r.card.votes)
    ]
    assert len(cards_with_crowd_vote) > 0

    # kaskad sonrasi donemde en az bir tick'te crowd_emergence oyu negatif olmali
    # (asagi yonlu kaskad -> negatif skor -> negatif oy)
    post_shock = [r for r in results if r.tick > 80]
    crowd_votes = [
        v.vote for r in post_shock if r.card is not None
        for v in r.card.votes if v.name == "crowd_emergence"
    ]
    assert any(v < 0 for v in crowd_votes)


def test_crowd_emergence_low_weight_in_card():
    config = SimulationConfig(symbol="SIM/USDT", n_ticks=60, start_price=100.0, min_bars_for_brain=30, crowd_emergence_min_ticks=20)
    engine = Engine(config, agents=[NoopAgent()], factor_brain=SignalCoreFactorBrain(min_bars=30))
    results = engine.run()
    for r in results:
        if r.card is None:
            continue
        for v in r.card.votes:
            if v.name == "crowd_emergence":
                assert v.weight == 0.15  # SignalCoreFactorBrain.DEFAULT_EXTRA_WEIGHT
