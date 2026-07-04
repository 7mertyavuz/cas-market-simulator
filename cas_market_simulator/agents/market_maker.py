"""Market-maker ajan: tek kural -- iki yonlu kucuk kotasyon ver;
envanter birikince dengeleyici yone kay; oynaklik artinca TAMAMEN CEKIL.

Kural (04-yeni-agent-onerileri.md): likidite kurumasi -> flash crash
tetigi. Bu basit Environment gercek bir emir defteri/eslesme motoru
degil (bkz. environment/base.py Faz 0 notu), bu yuzden "iki yonlu
kotasyon" burada her tick alternatif yonde kucuk bir emir olarak
modelleniyor -- gercek karsi taraf eslesmesi Faz 5+'ta microstructure-
analyzer baglaninca gelecek. Onemli olan davranissal kural: oynaklik
esigi asilinca ajan TAMAMEN PASIF kalir (emir vermez) -- likidite
cekilmesini budur temsil eden.
"""
from __future__ import annotations

from collections import deque
from typing import Optional

from ..environment.base import EnvironmentState, Order
from .base import Agent


class MarketMakerAgent(Agent):
    def __init__(
        self,
        agent_id: str = "market_maker-0",
        *,
        vol_lookback: int = 10,
        vol_pull_threshold_pct: float = 0.01,
        inventory_limit: float = 5.0,
        quote_size: float = 0.5,
    ) -> None:
        super().__init__(agent_id)
        self.vol_lookback = vol_lookback
        self.vol_pull_threshold_pct = vol_pull_threshold_pct
        self.inventory_limit = inventory_limit
        self.quote_size = quote_size
        self._prices: deque[float] = deque(maxlen=vol_lookback)
        self._last_state: Optional[EnvironmentState] = None
        self._toggle_buy = True

    def observe(self, state: EnvironmentState) -> None:
        self._last_state = state
        self._prices.append(state.price)

    def _recent_volatility_pct(self) -> float:
        if len(self._prices) < 2:
            return 0.0
        return (max(self._prices) - min(self._prices)) / min(self._prices)

    def decide(self) -> Optional[Order]:
        if self._last_state is None:
            return None

        if self._recent_volatility_pct() > self.vol_pull_threshold_pct:
            return None  # oynaklik yuksek -- likidite cek (kotasyon verme)

        if abs(self.position) >= self.inventory_limit:
            side = "sell" if self.position > 0 else "buy"  # envanteri dengele
        else:
            side = "sell" if self._toggle_buy else "buy"   # iki yonlu kotasyon
            self._toggle_buy = not self._toggle_buy

        return Order(agent_id=self.agent_id, symbol=self._last_state.symbol, side=side, size=self.quote_size)
