"""Haber-tepkicisi ajan: tek kural -- ShockEvent gelince yon al.

Kural (04-yeni-agent-onerileri.md): "Dissal sokun icsellesmesi, asiri
tepki." SentimentFeed.shocks() akisindan (panic/euphoria) beslenir;
sok buyuklugu (magnitude) ile orantili boyutta, sokun yonunde emir
verir. Yarilanma suresi (decay_halflife_s) kadar zaman gectikce
etkisini "unutur" (basit ussel sonum).
"""
from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Optional

from ..adapters.contracts import ShockEvent
from ..environment.base import EnvironmentState, Order
from .base import Agent

_SHOCK_DIRECTION = {"panic": "sell", "euphoria": "buy", "fed_tone": None, "narrative_shift": None}


class NewsReactorAgent(Agent):
    def __init__(self, agent_id: str = "news_reactor-0", *, base_size: float = 3.0, react_threshold: float = 0.05) -> None:
        super().__init__(agent_id)
        self.base_size = base_size
        self.react_threshold = react_threshold
        self._active_magnitude = 0.0
        self._active_side: str | None = None
        self._last_state: Optional[EnvironmentState] = None

    def observe(self, state: EnvironmentState) -> None:
        self._last_state = state

    def on_shock(self, shock: ShockEvent, *, now: datetime | None = None) -> None:
        """Engine, o tick'teki aktif soklari buraya besler (bkz. engine/loop.py)."""
        side = _SHOCK_DIRECTION.get(shock.kind)
        if side is None:
            return
        now = now or datetime.now(timezone.utc)
        age_s = max(0.0, (now - shock.ts).total_seconds())
        decayed = shock.magnitude * (0.5 ** (age_s / max(shock.decay_halflife_s, 1e-6)))
        if decayed > self._active_magnitude:
            self._active_magnitude = decayed
            self._active_side = side

    def decide(self) -> Optional[Order]:
        if self._last_state is None or self._active_magnitude < self.react_threshold:
            return None
        size = self.base_size * self._active_magnitude
        order = Order(agent_id=self.agent_id, symbol=self._last_state.symbol, side=self._active_side, size=size)
        self._active_magnitude *= 0.5  # tepki verdikten sonra etkisi hizla soner
        return order
