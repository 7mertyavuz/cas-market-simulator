"""Trend-kirici / kontra fon ajan: tek kural -- asiri kalabalıklasmada ters pozisyon.

Kural (04-yeni-agent-onerileri.md): "Tepe olusumu, ralli sonu." Fiyatin
hareketli ortalamadan sapmasi (z-score benzeri basit olcum) asiri
bolgeye girdiginde, TERS yonde pozisyon alir -- momentum'un aynasi.
"""
from __future__ import annotations

from collections import deque
from typing import Optional

from ..environment.base import EnvironmentState, Order
from .base import Agent


class ContrarianAgent(Agent):
    def __init__(
        self,
        agent_id: str = "contrarian-0",
        *,
        lookback: int = 20,
        extension_threshold_pct: float = 0.04,
        size: float = 1.5,
    ) -> None:
        super().__init__(agent_id)
        self.lookback = lookback
        self.extension_threshold_pct = extension_threshold_pct
        self.size = size
        self._prices: deque[float] = deque(maxlen=lookback)
        self._last_state: Optional[EnvironmentState] = None

    def observe(self, state: EnvironmentState) -> None:
        self._last_state = state
        self._prices.append(state.price)

    def decide(self) -> Optional[Order]:
        if self._last_state is None or len(self._prices) < self._prices.maxlen:
            return None
        mean_price = sum(self._prices) / len(self._prices)
        if mean_price == 0:
            return None
        extension = (self._last_state.price - mean_price) / mean_price
        if extension > self.extension_threshold_pct:
            return Order(agent_id=self.agent_id, symbol=self._last_state.symbol, side="sell", size=self.size)
        if extension < -self.extension_threshold_pct:
            return Order(agent_id=self.agent_id, symbol=self._last_state.symbol, side="buy", size=self.size)
        return None
