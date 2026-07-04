"""Arbitraj ajani: tek kural -- iki varlik/borsa farkini kapat.

Kural (04-yeni-agent-onerileri.md): "Fiyat yakinsamasi, lead-lag
transferi." Bu simulasyonda ikinci bir gercek borsa yok; onun yerine
kendi basina yavas evrilen bagimsiz bir "referans fiyat" (fair value)
sureci tutulur ve Environment fiyati bundan saptikca kapatma yonunde
islem yapilir -- bu, simulasyondaki arbitraj ajaninin gercek-veri
karsiligi (gercek borsa fiyati baglaninca referans sureci onunla
degistirilecek).
"""
from __future__ import annotations

from typing import Optional

from ..environment.base import EnvironmentState, Order
from .base import Agent


class ArbitrageAgent(Agent):
    def __init__(
        self,
        agent_id: str = "arbitrage-0",
        *,
        seed: int | None = 50,
        reference_vol_pct: float = 0.0015,
        deviation_threshold_pct: float = 0.01,
        size: float = 1.0,
    ) -> None:
        super().__init__(agent_id)
        import random

        self._rng = random.Random(seed)
        self.reference_vol_pct = reference_vol_pct
        self.deviation_threshold_pct = deviation_threshold_pct
        self.size = size
        self._reference_price: float | None = None
        self._last_state: Optional[EnvironmentState] = None

    def observe(self, state: EnvironmentState) -> None:
        self._last_state = state
        if self._reference_price is None:
            self._reference_price = state.price
        else:
            step = self._rng.gauss(0.0, self.reference_vol_pct)
            self._reference_price = max(1e-8, self._reference_price * (1.0 + step))

    def decide(self) -> Optional[Order]:
        if self._last_state is None or self._reference_price is None:
            return None
        deviation = (self._last_state.price - self._reference_price) / self._reference_price
        if abs(deviation) < self.deviation_threshold_pct:
            return None
        side = "sell" if deviation > 0 else "buy"  # cevre pahali/ucuzsa referansa dogru kapat
        return Order(agent_id=self.agent_id, symbol=self._last_state.symbol, side=side, size=self.size)
