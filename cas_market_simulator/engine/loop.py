"""Senkron tick dongusu (engine).

Faz 0: stub feed -> ajan(lar) -> environment -> log basan bir dongu.
Faz 3: gercek boru hatti -- her tick'te Environment gecmisinden OHLCV
bar'i turetilir (adapters/bars.py), FactorBrain'e (artik gercek
SignalCoreFactorBrain olabilir) verilir; kart LONG/SHORT ise
PaperExecutor ile paper emir uretilir ve Journal'a kaydedilir; onceki
kayitlarin ufku dolmussa Journal cozer (forward-test).
Faz 5: ajan emirleri artik decide()+submit()+on_fill() akisiyla
isleniyor (act() yerine) -- boylece her ajanin PnL'i tick basi
guncelleniyor ve TickResult.agent_pnls'te goruluyor (bkz.
agents/base.py::on_fill). Fill fiyati, o tick'in NET fiyat etkisi
sonrasi olusan yeni fiyattir (bkz. environment/base.py notu: gercek
emir defteri yok, hepsi ayni tick-sonu fiyattan 'doluyor' varsayimi --
Faz 5+'ta microstructure baglaninca zenginlesecek).
Faz 6: dissal sok enjeksiyonu -- SentimentFeed.shocks() (veya
`scripted_shocks` ile deterministik senaryo replay) her tick'te aktif
soklari toplar, ussel sonumle agirliklandirip Environment'a
`extra_impact` olarak ekler VE NewsReactorAgent gibi `on_shock`
metoduna sahip ajanlara besler.
Faz 7: GERI BESLEME -- Katman 2 (bu simulasyon) kendi son N tick'lik
gecmisinden bir crowd_emergence_score hesaplar (analysis/emergence.py)
ve bunu extra_factors["crowd_emergence"] olarak Katman 1'e (FactorBrain
-> signalcore) geri besler. Boylece "kalabalik cokmeye mi gidiyor?"
okumasi, karttaki dusuk-agirlikli bir faktore donusur -- iki katman
kapali bir dongu olusturur."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone

from ..adapters.bars import ohlcv_from_history
from ..adapters.contracts import Card, FactorBrain, FlowFeed, SentimentFeed, ShockEvent
from ..agents.base import Agent
from ..analysis.emergence import compute_emergence_from_engine, crowd_emergence_score
from ..analysis.execution import PaperExecutor
from ..analysis.journal import Journal
from ..environment.base import Environment, EnvironmentState

logger = logging.getLogger("cas.engine")

SHOCK_DIRECTION_SIGN = {"panic": -1.0, "euphoria": 1.0}  # fed_tone/narrative_shift: yonsuz, atlanir
SHOCK_MIN_ACTIVE_MAGNITUDE = 1e-4


@dataclass
class TickResult:
    tick: int
    state: EnvironmentState
    card_direction: str
    card_confidence: float
    card: Card | None = None
    agent_pnls: dict = field(default_factory=dict)
    active_shock_magnitude: float = 0.0
    agent_orders: dict = field(default_factory=dict)  # agent_id -> "buy"|"sell" (bu tick emir verenler)
    crowd_emergence_score: float = 0.0  # [-1,1], Faz 7 geri besleme sinyali (bkz. modul docstring'i)


@dataclass
class SimulationConfig:
    symbol: str
    n_ticks: int
    start_price: float = 100.0
    log_every: int = 1
    min_bars_for_brain: int = 30
    shock_impact_scale: float = 20.0  # magnitude [0,1] -> fiyat-etki "birim" olcegi
    seconds_per_tick: float = 60.0     # sok yarilanma-suresi hesaplarini tick'e cevirmek icin
    crowd_emergence_window: int = 60     # geri besleme skorunu hesaplarken bakilacak son N tick
    crowd_emergence_min_ticks: int = 20  # bu kadar tick birikmeden skor hesaplanmaz (0.0 doner)


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
        scripted_shocks: dict[int, ShockEvent] | None = None,
    ) -> None:
        self.config = config
        self.agents = agents
        self.env = Environment(config.symbol, config.start_price)
        self.sentiment_feed = sentiment_feed
        self.flow_feed = flow_feed
        self.factor_brain = factor_brain
        self.executor = executor
        self.journal = journal
        self.scripted_shocks = scripted_shocks or {}
        self._active_shocks: list[tuple[ShockEvent, int]] = []  # (shock, olusturuldugu tick)
        self._last_shock_check: datetime | None = None
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

        decisions = [(agent, agent.decide()) for agent in self.agents]
        for agent, order in decisions:
            if order is not None:
                self.env.submit(order)

        extra_impact = self._collect_and_apply_shocks(state)
        new_state = self.env.step(extra_impact=extra_impact)

        # Basitlestirilmis fill modeli: tum bu tick'te verilen emirler,
        # tick-sonu fiyatindan (net etki uygulandiktan sonra) doluyor
        # varsayilir (bkz. modul docstring'i).
        for agent, order in decisions:
            if order is not None:
                agent.on_fill(order, new_state.price)

        agent_pnls = {agent.agent_id: agent.total_pnl(new_state.price) for agent in self.agents}
        agent_orders = {agent.agent_id: order.side for agent, order in decisions if order is not None}

        card: Card | None = None
        direction, confidence = "NEUTRAL", 0.0

        crowd_score = self._compute_crowd_emergence_score()

        if self.factor_brain is not None:
            bars = ohlcv_from_history(self.env.history)
            extra_factors: dict = {}
            if self.sentiment_feed is not None:
                extra_factors["sentiment"] = self.sentiment_feed.latest(self.config.symbol)
            if self.flow_feed is not None:
                extra_factors["flow"] = self.flow_feed.latest(self.config.symbol)
            extra_factors["crowd_emergence"] = crowd_score

            card = self.factor_brain.analyze(self.config.symbol, bars, extra_factors)
            direction, confidence = card.direction, card.confidence

            if self.journal is not None:
                self.journal.resolve_due(current_tick=new_state.tick, current_price=new_state.price)
                if self.executor is not None and direction in ("LONG", "SHORT"):
                    fill = self.executor.execute(card, new_state.price)
                    if fill is not None:
                        self.journal.record(fill, tick=new_state.tick)

        active_magnitude = sum(s.magnitude for s, _ in self._active_shocks)

        return TickResult(
            tick=new_state.tick,
            state=new_state,
            card_direction=direction,
            card_confidence=confidence,
            card=card,
            agent_pnls=agent_pnls,
            active_shock_magnitude=active_magnitude,
            agent_orders=agent_orders,
            crowd_emergence_score=crowd_score,
        )

    def _compute_crowd_emergence_score(self) -> float:
        """Son `crowd_emergence_window` tick'e bakip crowd_emergence_score
        hesaplar (Faz 7 geri besleme). Yeterli gecmis birikmeden 0.0
        doner (notr -- henuz bir okuma yok, "belirsiz" degil "yok")."""
        if len(self.results) < self.config.crowd_emergence_min_ticks:
            return 0.0
        window = self.results[-self.config.crowd_emergence_window :]
        report = compute_emergence_from_engine(
            window, cascade_window=min(10, max(1, len(window) - 1)), flash_crash_threshold_pct=0.01
        )
        return crowd_emergence_score(report)

    def _collect_and_apply_shocks(self, state: EnvironmentState) -> float:
        """Bu tick'te aktif olan soklari toplar (feed + scripted), ussel
        sonumle (TICK bazinda, gercek saat degil -- bir simulasyon
        birkac saniyede binlerce tick isleyebilir, gercek-saat sonumu
        soklari hic sondurmezdi) agirliklandirir, NewsReactorAgent'lara
        besler ve Environment'a verilecek toplam extra_impact'i dondurur.
        """
        new_shocks: list[ShockEvent] = []

        if self.sentiment_feed is not None:
            since = self._last_shock_check or state.ts
            new_shocks.extend(self.sentiment_feed.shocks(since))
        self._last_shock_check = state.ts

        scripted = self.scripted_shocks.get(state.tick)
        if scripted is not None:
            new_shocks.append(scripted)

        for shock in new_shocks:
            self._active_shocks.append((shock, state.tick))
            for agent in self.agents:
                on_shock = getattr(agent, "on_shock", None)
                if callable(on_shock):
                    on_shock(shock, now=state.ts)

        total_impact = 0.0
        still_active: list[tuple[ShockEvent, int]] = []
        for shock, tick_created in self._active_shocks:
            sign = SHOCK_DIRECTION_SIGN.get(shock.kind, 0.0)
            age_s = max(0.0, (state.tick - tick_created)) * self.config.seconds_per_tick
            decayed = shock.magnitude * (0.5 ** (age_s / max(shock.decay_halflife_s, 1e-6)))
            if decayed < SHOCK_MIN_ACTIVE_MAGNITUDE:
                continue
            still_active.append((shock, tick_created))
            total_impact += sign * decayed * self.config.shock_impact_scale

        self._active_shocks = still_active
        return total_impact
