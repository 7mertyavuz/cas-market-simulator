"""Momentum/trend takipci ajan: tek kural -- fiyat yukseliyorsa al.

Kural (04-yeni-agent-onerileri.md): "Fiyat yukseliyorsa al" ->
ralli/balon, pozitif geri-besleme besler. Karar kurali signalcore'un
trend faktorunden ODUNC alinir (basit versiyon: son N tick'lik getiri
isareti), tam faktor kutuphanesi degil -- ajan basit kalmali (bkz.
FAZ-PLANI.md kritik kural #2).
"""
from __future__ import annotations

from collections import deque
from typing import Optional

from ..environment.base import EnvironmentState, Order
from .base import Agent


class MomentumAgent(Agent):
    def __init__(
        self,
        agent_id: str = "momentum-0",
        *,
        lookback: int = 5,
        threshold_pct: float = 0.002,
        size: float = 1.0,
    ) -> None:
        super().__init__(agent_id)
        self.lookback = lookback
        self.threshold_pct = threshold_pct
        self.size = size
        self._prices: deque[float] = deque(maxlen=lookback + 1)
        self._last_state: Optional[EnvironmentState] = None

    def observe(self, state: EnvironmentState) -> None:
        self._last_state = state
        self._prices.append(state.price)

    def decide(self) -> Optional[Order]:
        if self._last_state is None or len(self._prices) < self._prices.maxlen:
            return None

        change_pct = (self._prices[-1] - self._prices[0]) / self._prices[0]
        if change_pct > self.threshold_pct:
            return Order(agent_id=self.agent_id, symbol=self._last_state.symbol, side="buy", size=self.size)
        if change_pct < -self.threshold_pct:
            return Order(agent_id=self.agent_id, symbol=self._last_state.symbol, side="sell", size=self.size)
        return None
