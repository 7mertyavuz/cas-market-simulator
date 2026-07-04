"""Panikci/retail ajan: tek kural -- dususte GEC tepki ile sat (kapitulasyon).

Kural (04-yeni-agent-onerileri.md): "Sentiment soku + duguste gec sat"
-> kaskad, kapitulasyon dibi besler. "Gec tepki" burada N ardisik
negatif getirili tick sonrasi (aninda degil) tetiklenen bir esik
olarak modelleniyor -- retail'in trendi hemen degil, dogrulandiktan
sonra fark etmesini taklit eder.
"""
from __future__ import annotations

from typing import Optional

from ..environment.base import EnvironmentState, Order
from .base import Agent


class PanicAgent(Agent):
    def __init__(
        self,
        agent_id: str = "panic-0",
        *,
        drawdown_threshold_pct: float = 0.02,
        confirmation_ticks: int = 3,
        size: float = 2.0,
    ) -> None:
        super().__init__(agent_id)
        self.drawdown_threshold_pct = drawdown_threshold_pct
        self.confirmation_ticks = confirmation_ticks
        self.size = size
        self._peak_price: float | None = None
        self._consecutive_down_ticks = 0
        self._last_price: float | None = None
        self._last_state: Optional[EnvironmentState] = None

    def observe(self, state: EnvironmentState) -> None:
        self._last_state = state
        if self._peak_price is None or state.price > self._peak_price:
            self._peak_price = state.price

        if self._last_price is not None and state.price < self._last_price:
            self._consecutive_down_ticks += 1
        else:
            self._consecutive_down_ticks = 0
        self._last_price = state.price

    def decide(self) -> Optional[Order]:
        if self._last_state is None or self._peak_price is None:
            return None

        drawdown = (self._peak_price - self._last_state.price) / self._peak_price
        confirmed = self._consecutive_down_ticks >= self.confirmation_ticks

        if self.position > 0 and drawdown >= self.drawdown_threshold_pct and confirmed:
            sell_size = min(self.size, self.position)
            return Order(agent_id=self.agent_id, symbol=self._last_state.symbol, side="sell", size=sell_size)

        # retail'in klasik davranisi: kapitulasyon YOK iken, fiyat yeni zirve
        # yapinca (euphoria) hafifce alici olur -- gec tepkinin diger yarisi.
        if drawdown == 0.0 and self.position < self.size * 2:
            return Order(agent_id=self.agent_id, symbol=self._last_state.symbol, side="buy", size=self.size * 0.25)

        return None
