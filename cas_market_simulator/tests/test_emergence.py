from cas_market_simulator.analysis.emergence import (
    agent_synchronization_from_directions,
    compute_emergence,
    compute_emergence_from_engine,
)
from cas_market_simulator.adapters.contracts import ShockEvent
from cas_market_simulator.agents.noop import NoopAgent
from cas_market_simulator.agents.momentum import MomentumAgent
from cas_market_simulator.engine.loop import Engine, SimulationConfig
from datetime import datetime, timezone


def test_compute_emergence_too_short_returns_zeros():
    report = compute_emergence([])
    assert report.cascade_size_pct == 0.0
    assert report.n_ticks == 0


def test_compute_emergence_flat_price_no_flash_crash():
    config = SimulationConfig(symbol="SIM/USDT", n_ticks=20, start_price=100.0)
    engine = Engine(config, agents=[NoopAgent()])
    results = engine.run()
    report = compute_emergence(results, flash_crash_threshold_pct=0.01)
    assert report.flash_crash_frequency == 0.0
    assert report.cascade_size_pct == 0.0


def test_compute_emergence_detects_scripted_crash_cascade():
    shock = ShockEvent(kind="panic", entity="market", magnitude=1.0, decay_halflife_s=600.0, ts=datetime.now(timezone.utc))
    config = SimulationConfig(symbol="SIM/USDT", n_ticks=15, start_price=100.0, shock_impact_scale=50.0, seconds_per_tick=60.0)
    engine = Engine(config, agents=[NoopAgent()], scripted_shocks={0: shock})
    results = engine.run()
    report = compute_emergence(results, cascade_window=5, flash_crash_threshold_pct=0.01)
    assert report.cascade_size_pct < 0.0  # asagi yonlu kaskad
    assert report.min_single_tick_return_pct < 0.0


def test_agent_synchronization_all_same_direction():
    ticks = [{"a": "buy", "b": "buy", "c": "buy"}] * 5
    sync = agent_synchronization_from_directions(ticks)
    assert sync == 1.0


def test_agent_synchronization_split_evenly():
    ticks = [{"a": "buy", "b": "sell"}] * 5
    sync = agent_synchronization_from_directions(ticks)
    assert sync == 0.5


def test_agent_synchronization_ignores_empty_ticks():
    ticks = [{}, {}, {"a": "buy", "b": "buy"}]
    sync = agent_synchronization_from_directions(ticks)
    assert sync == 1.0


def test_agent_synchronization_no_data_returns_zero():
    assert agent_synchronization_from_directions([]) == 0.0
    assert agent_synchronization_from_directions([{}, {}]) == 0.0


def test_compute_emergence_from_engine_fills_synchronization():
    agents = [MomentumAgent(f"m{i}", lookback=3, threshold_pct=0.0005) for i in range(4)]
    config = SimulationConfig(symbol="SIM/USDT", n_ticks=30, start_price=100.0)
    engine = Engine(config, agents=agents)
    results = engine.run()
    report = compute_emergence_from_engine(results)
    assert 0.0 <= report.agent_synchronization <= 1.0


def test_crowd_emergence_score_negative_for_crash():
    from cas_market_simulator.analysis.emergence import EmergenceReport, crowd_emergence_score

    report = EmergenceReport(
        n_ticks=50, cascade_size_pct=-0.10, cascade_window=10,
        agent_synchronization=0.9, return_autocorrelation=0.5,
        flash_crash_frequency=0.1, max_single_tick_return_pct=0.01,
        min_single_tick_return_pct=-0.03,
    )
    score = crowd_emergence_score(report, cascade_scale_pct=0.05)
    assert score < 0


def test_crowd_emergence_score_positive_for_rally():
    from cas_market_simulator.analysis.emergence import EmergenceReport, crowd_emergence_score

    report = EmergenceReport(
        n_ticks=50, cascade_size_pct=0.10, cascade_window=10,
        agent_synchronization=0.9, return_autocorrelation=0.5,
        flash_crash_frequency=0.1, max_single_tick_return_pct=0.03,
        min_single_tick_return_pct=-0.01,
    )
    score = crowd_emergence_score(report, cascade_scale_pct=0.05)
    assert score > 0


def test_crowd_emergence_score_bounded():
    from cas_market_simulator.analysis.emergence import EmergenceReport, crowd_emergence_score

    report = EmergenceReport(
        n_ticks=50, cascade_size_pct=-0.9, cascade_window=10,
        agent_synchronization=1.0, return_autocorrelation=0.9,
        flash_crash_frequency=0.5, max_single_tick_return_pct=0.01,
        min_single_tick_return_pct=-0.2,
    )
    score = crowd_emergence_score(report, cascade_scale_pct=0.05)
    assert -1.0 <= score <= 1.0


def test_crowd_emergence_score_muted_by_low_synchronization():
    from cas_market_simulator.analysis.emergence import EmergenceReport, crowd_emergence_score

    high_sync = EmergenceReport(
        n_ticks=50, cascade_size_pct=-0.05, cascade_window=10,
        agent_synchronization=1.0, return_autocorrelation=0.0,
        flash_crash_frequency=0.0, max_single_tick_return_pct=0.0,
        min_single_tick_return_pct=-0.01,
    )
    low_sync = EmergenceReport(
        n_ticks=50, cascade_size_pct=-0.05, cascade_window=10,
        agent_synchronization=0.0, return_autocorrelation=0.0,
        flash_crash_frequency=0.0, max_single_tick_return_pct=0.0,
        min_single_tick_return_pct=-0.01,
    )
    assert abs(crowd_emergence_score(high_sync)) > abs(crowd_emergence_score(low_sync))


def test_crowd_emergence_score_zero_cascade_is_zero():
    from cas_market_simulator.analysis.emergence import EmergenceReport, crowd_emergence_score

    report = EmergenceReport(
        n_ticks=50, cascade_size_pct=0.0, cascade_window=10,
        agent_synchronization=0.8, return_autocorrelation=0.0,
        flash_crash_frequency=0.0, max_single_tick_return_pct=0.0,
        min_single_tick_return_pct=0.0,
    )
    assert crowd_emergence_score(report) == 0.0
