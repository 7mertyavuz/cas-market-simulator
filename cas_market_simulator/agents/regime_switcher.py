"""Rejim-degistiren ajan: tek kural -- volatilite/verimlilik rejimine gore momentum<->ortalama-donus arasi gecis.

Kural (04-yeni-agent-onerileri.md, meta ajanlar / FAZ-PLANI.md Faz 8):
"Volatilite rejimine gore momentum<->MR arasi gecis yapar." Kendi
basit "verimlilik orani" (efficiency ratio) olcumunu tutar: net fiyat
hareketi / toplam kat edilen yol. Oran yuksekse (duz, tek yonlu
hareket) TREND rejimi -> momentum kurali; dusukse (cirpinti/gel-git)
MEAN_REVERT rejimi -> son kisa-vade ortalamadan sapmaya ters pozisyon.
signalcore'un Hurst/ER faktorune BAGIMLI DEGIL (ajanlar basit ve
bagimsiz kalmali) -- kendi kaba analogu.
"""
from __future__ import annotations

from collections import deque
from typing import Optional

from ..environment.base import EnvironmentState, Order
from .base import Agent


class RegimeSwitcherAgent(Agent):
    def __init__(
        self,
        agent_id: str = "regime_switcher-0",
        *,
        lookback: int = 15,
        efficiency_threshold: float = 0.4,
        size: float = 1.0,
    ) -> None:
        super().__init__(agent_id)
        self.lookback = lookback
        self.efficiency_threshold = efficiency_threshold
        self.size = size
        self._prices: deque[float] = deque(maxlen=lookback)
        self._last_state: Optional[EnvironmentState] = None
        self.current_mode = "mean_revert"  # "trend" | "mean_revert" -- baslangicta notr varsayim

    def observe(self, state: EnvironmentState) -> None:
        self._last_state = state
        self._prices.append(state.price)
        if len(self._prices) == self._prices.maxlen:
            self.current_mode = self._detect_regime()

    def _detect_regime(self) -> str:
        prices = list(self._prices)
        net_change = abs(prices[-1] - prices[0])
        path = sum(abs(prices[i] - prices[i - 1]) for i in range(1, len(prices)))
        efficiency = 0.0 if path == 0 else net_change / path
        return "trend" if efficiency >= self.efficiency_threshold else "mean_revert"

    def decide(self) -> Optional[Order]:
        if self._last_state is None or len(self._prices) < self._prices.maxlen:
            return None

        prices = list(self._prices)
        mean_price = sum(prices) / len(prices)
        cur = prices[-1]

        if self.current_mode == "trend":
            direction = 1.0 if cur > prices[0] else -1.0
        else:
            if mean_price == 0:
                return None
            extension = (cur - mean_price) / mean_price
            if abs(extension) < 0.005:
                return None
            direction = -1.0 if extension > 0 else 1.0  # asiri sapmada TERS

        side = "buy" if direction > 0 else "sell"
        return Order(agent_id=self.agent_id, symbol=self._last_state.symbol, side=side, size=self.size)
