"""MEV/searcher ajan: tek kural -- kisa-vade momentumu agresifce takip et.

Kural (04-yeni-agent-onerileri.md): "Mempool'da kurban gor -> sandwich"
-> mikro-yapi bozulmasi, retail aleyhine surtunme. Bu Environment'ta
mempool/bekleyen-emir gorunurlugu yok (bkz. environment/base.py Faz 0
notu), bu yuzden gercek sandwich taklit edilemiyor. Yerine gecen basit
yaklasim: MEV ajani en son tick'teki fiyat hareketinin YONUNU agresifce
buyutur (bir onceki hareketi "kurban" olarak alip ustune biner) --
gercek sandwich'in kaba bir analogudur; gercek mempool erisimi
baglaninca bu ajan yeniden yazilmali.
"""
from __future__ import annotations

from collections import deque
from typing import Optional

from ..environment.base import EnvironmentState, Order
from .base import Agent


class MevAgent(Agent):
    def __init__(
        self,
        agent_id: str = "mev-0",
        *,
        min_move_pct: float = 0.001,
        size: float = 0.8,
    ) -> None:
        super().__init__(agent_id)
        self.min_move_pct = min_move_pct
        self.size = size
        self._prices: deque[float] = deque(maxlen=2)
        self._last_state: Optional[EnvironmentState] = None

    def observe(self, state: EnvironmentState) -> None:
        self._last_state = state
        self._prices.append(state.price)

    def decide(self) -> Optional[Order]:
        if self._last_state is None or len(self._prices) < 2:
            return None
        prev, cur = self._prices[0], self._prices[1]
        move_pct = (cur - prev) / prev if prev else 0.0
        if abs(move_pct) < self.min_move_pct:
            return None
        side = "buy" if move_pct > 0 else "sell"
        return Order(agent_id=self.agent_id, symbol=self._last_state.symbol, side=side, size=self.size)
