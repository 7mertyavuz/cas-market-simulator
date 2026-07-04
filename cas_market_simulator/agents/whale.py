"""Balina ajan: tek kural -- seyrek, buyuk, fiyati iten emir.

Kural (04-yeni-agent-onerileri.md): "Ani kaymalar, stop avi" besler.
Coğu tick'te sessiz kalir; dusuk olasilikla agir-kuyruklu (heavy-tail)
buyuklukte tek yonlu bir emir verir.
"""
from __future__ import annotations

from typing import Optional

from ..environment.base import EnvironmentState, Order
from .base import Agent


class WhaleAgent(Agent):
    def __init__(
        self,
        agent_id: str = "whale-0",
        *,
        seed: int | None = 40,
        trade_probability: float = 0.03,
        size_range: tuple[float, float] = (8.0, 25.0),
    ) -> None:
        super().__init__(agent_id)
        import random

        self._rng = random.Random(seed)
        self.trade_probability = trade_probability
        self.size_range = size_range
        self._last_state: Optional[EnvironmentState] = None

    def observe(self, state: EnvironmentState) -> None:
        self._last_state = state

    def decide(self) -> Optional[Order]:
        if self._last_state is None or self._rng.random() >= self.trade_probability:
            return None
        side = "buy" if self._rng.random() < 0.5 else "sell"
        size = self._rng.uniform(*self.size_range)
        return Order(agent_id=self.agent_id, symbol=self._last_state.symbol, side=side, size=size)
