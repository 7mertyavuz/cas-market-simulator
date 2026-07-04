"""Faz 0 demo: stub feed -> ajan -> environment -> log basan tick dongusu.

Calistir:
    PYTHONPATH=. python3 scripts/run_faz0_demo.py
"""
from __future__ import annotations

import logging

from cas_market_simulator.adapters.factor_brain import StubFactorBrain
from cas_market_simulator.adapters.flow_feed import StubFlowFeed
from cas_market_simulator.adapters.sentiment_feed import StubSentimentFeed
from cas_market_simulator.agents.noop import NoopAgent
from cas_market_simulator.engine.loop import Engine, SimulationConfig

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s")


def main() -> None:
    config = SimulationConfig(symbol="BTC/USDT", n_ticks=10, start_price=65000.0)
    engine = Engine(
        config,
        agents=[NoopAgent("noop-0")],
        sentiment_feed=StubSentimentFeed(),
        flow_feed=StubFlowFeed(),
        factor_brain=StubFactorBrain(),
    )
    engine.run()


if __name__ == "__main__":
    main()
