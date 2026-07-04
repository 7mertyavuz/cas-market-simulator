"""Suru/kopyalayici ajan: tek kural -- en karli ajani taklit et.

Kural (04-yeni-agent-onerileri.md, meta ajanlar / FAZ-PLANI.md Faz 8):
"En karli ajani taklit eder -> suru davranisi, balon buyutme." Bu ajan,
kurulusta verilen `peers` (diger ajan nesnelerinin referanslari,
Agent taban sinifindan PnL/pozisyon bilgisine sahip) listesinden en
yuksek `total_pnl(current_price)` degerine sahip olani bulur ve o
ajanin GUNCEL POZISYON YONUNU (uzun/kisa) taklit eder -- gercek bir
"son emri kopyala" degil, "kazanani takip et" davranisidir (basit ve
saglam: peer'in o an hicbir pozisyonu yoksa taklit edilecek bir sey
yoktur).
"""
from __future__ import annotations

from typing import Optional

from ..environment.base import EnvironmentState, Order
from .base import Agent


class HerdAgent(Agent):
    def __init__(
        self,
        agent_id: str = "herd-0",
        *,
        peers: list[Agent] | None = None,
        size: float = 1.0,
    ) -> None:
        super().__init__(agent_id)
        self.peers = peers or []
        self.size = size
        self._last_state: Optional[EnvironmentState] = None
        self.imitation_count = 0
        self.last_imitated_agent_id: str | None = None

    def set_peers(self, peers: list[Agent]) -> None:
        """Ajan nesneleri Engine'e verilmeden once olusturuldugu icin,
        peers genelde constructor sonrasi bu metotla baglanir (bkz.
        demo scriptleri)."""
        self.peers = peers

    def observe(self, state: EnvironmentState) -> None:
        self._last_state = state

    def decide(self) -> Optional[Order]:
        if self._last_state is None or not self.peers:
            return None

        price = self._last_state.price
        candidates = [p for p in self.peers if p.position != 0]
        if not candidates:
            return None

        leader = max(candidates, key=lambda p: p.total_pnl(price))
        target_side = "buy" if leader.position > 0 else "sell"

        self.imitation_count += 1
        self.last_imitated_agent_id = leader.agent_id

        return Order(agent_id=self.agent_id, symbol=self._last_state.symbol, side=target_side, size=self.size)
