"""Senkron tick dongusu (engine).

Faz 0: stub feed -> ajan(lar) -> environment -> log basan bir dongu.
Faz 3: gercek boru hatti -- her tick'te Environment gecmisinden OHLCV
bar'i turetilir (adapters/bars.py), FactorBrain'e (artik gercek
SignalCoreFactorBrain olabilir) verilir; kart LONG/SHORT ise
PaperExecutor ile paper emir uretilir ve Journal'a kaydedilir; onceki
kayitlarin ufku dolmussa Journal cozer (forward-test).
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field

from ..adapters.bars import ohlcv_from_history
from ..adapters.contracts import Card, FactorBrain, FlowFeed, SentimentFeed
from ..agents.base import Agent
from ..analysis.execution import PaperExecutor
from ..analysis.journal import Journal
from ..environment.base import Environment, EnvironmentState

logger = logging.getLogger("cas.engine")


@dataclass
class TickResult:
    tick: int
    state: EnvironmentState
    card_direction: str
    card_confidence: float
    card: Card | None = None


@dataclass
class SimulationConfig:
    symbol: str
    n_ticks: int
    start_price: float = 100.0
    log_every: int = 1
    min_bars_for_brain: int = 30


class Engine:
    """Ajanlari, cevreyi, beyin/feed'leri ve forward-test defterini baglayan orkestrator."""

    def __init__(
        self,
        config: SimulationConfig,
        agents: list[Agent],
        *,
        sentiment_feed: SentimentFeed | None = None,
        flow_feed: FlowFeed | None = None,
        factor_brain: FactorBrain | None = None,
        executor: PaperExecutor | None = None,
        journal: Journal | None = None,
    ) -> None:
        self.config = config
        self.agents = agents
        self.env = Environment(config.symbol, config.start_price)
        self.sentiment_feed = sentiment_feed
        self.flow_feed = flow_feed
        self.factor_brain = factor_brain
        self.executor = executor
        self.journal = journal
        self.results: list[TickResult] = []

    def run(self) -> list[TickResult]:
        logger.info(
            "simulasyon basliyor: symbol=%s ticks=%d agents=%d",
            self.config.symbol,
            self.config.n_ticks,
            len(self.agents),
        )
        for i in range(self.config.n_ticks):
            result = self._tick()
            self.results.append(result)
            if self.config.log_every and i % self.config.log_every == 0:
                logger.info(
                    "tick=%d price=%.4f direction=%s confidence=%.2f",
                    result.tick,
                    result.state.price,
                    result.card_direction,
                    result.card_confidence,
                )
        logger.info("simulasyon bitti: son fiyat=%.4f", self.env.state.price)
        return self.results

    def _tick(self) -> TickResult:
        state = self.env.state

        for agent in self.agents:
            agent.observe(state)
        for agent in self.agents:
            agent.act(self.env)

        new_state = self.env.step()

        card: Card | None = None
        direction, confidence = "NEUTRAL", 0.0

        if self.factor_brain is not None:
            bars = ohlcv_from_history(self.env.history)
            extra_factors: dict = {}
            if self.sentiment_feed is not None:
                extra_factors["sentiment"] = self.sentiment_feed.latest(self.config.symbol)
            if self.flow_feed is not None:
                extra_factors["flow"] = self.flow_feed.latest(self.config.symbol)

            card = self.factor_brain.analyze(self.config.symbol, bars, extra_factors)
            direction, confidence = card.direction, card.confidence

            if self.journal is not None:
                self.journal.resolve_due(current_tick=new_state.tick, current_price=new_state.price)
                if self.executor is not None and direction in ("LONG", "SHORT"):
                    fill = self.executor.execute(card, new_state.price)
                    if fill is not None:
                        self.journal.record(fill, tick=new_state.tick)

        return TickResult(
            tick=new_state.tick,
            state=new_state,
            card_direction=direction,
            card_confidence=confidence,
            card=card,
        )
