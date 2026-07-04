"""Likidasyon motoru ajani: kaldiracli pozisyon esigi kirilinca zorunlu satis.

Kural (04-yeni-agent-onerileri.md): "yildiz ajan -- flash crash'i en
net ureten ajan." Diger ajanlardan farkli olarak TEK bir yon/pozisyon
degil, KENDI ic havuzunda bir dizi sentetik kaldiracli pozisyon tutar
(piyasadaki toplam kaldiracli acik pozisyonun soyutlamasi). Her tick:
1) belirli bir olasilikla yeni bir kaldiracli pozisyon acilir (piyasa
   ilgisinin buyumesi), 2) mevcut pozisyonlardan fiyat, giris fiyatina
   gore likidasyon esigini (yaklasik 1/kaldirac) kirmis olanlar ZORUNLU
   kapatilir -- bu kapanislar ayni yonde YIGILIRSA (cogu long ise hepsi
   satar) fiyati daha da iter, bu da yeni likidasyonlari tetikleyebilir:
   KASKAD budur.

Tek kural: "esik kirilinca kapat." Havuz yonetimi bu kuralin ic
detayidir, disaridan gorunen davranis basit kalir.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from ..environment.base import EnvironmentState, Order
from .base import Agent


@dataclass
class LeveragedPosition:
    side: str          # "long" | "short"
    entry_price: float
    size: float
    leverage: float
    maintenance_margin: float = 0.1  # kalan teminat orani (esigi biraz erken tetikler)

    def liquidation_triggered(self, price: float) -> bool:
        threshold = (1.0 - self.maintenance_margin) / self.leverage
        if self.side == "long":
            return (self.entry_price - price) / self.entry_price >= threshold
        return (price - self.entry_price) / self.entry_price >= threshold


class LiquidationEngineAgent(Agent):
    def __init__(
        self,
        agent_id: str = "liquidation_engine-0",
        *,
        seed: int | None = 30,
        open_probability: float = 0.15,
        leverage_choices: tuple[float, ...] = (5.0, 10.0, 20.0, 50.0),
        size_range: tuple[float, float] = (0.5, 3.0),
    ) -> None:
        super().__init__(agent_id)
        import random

        self._rng = random.Random(seed)
        self.open_probability = open_probability
        self.leverage_choices = leverage_choices
        self.size_range = size_range
        self.positions: list[LeveragedPosition] = []
        self.liquidation_events = 0
        self.total_liquidated_notional = 0.0
        self._last_state: Optional[EnvironmentState] = None

    def observe(self, state: EnvironmentState) -> None:
        self._last_state = state

    def decide(self) -> Optional[Order]:
        if self._last_state is None:
            return None
        price = self._last_state.price

        if self._rng.random() < self.open_probability:
            side = "long" if self._rng.random() < 0.5 else "short"
            size = self._rng.uniform(*self.size_range)
            leverage = self._rng.choice(self.leverage_choices)
            self.positions.append(LeveragedPosition(side=side, entry_price=price, size=size, leverage=leverage))

        triggered = [p for p in self.positions if p.liquidation_triggered(price)]
        if not triggered:
            return None

        self.positions = [p for p in self.positions if p not in triggered]
        self.liquidation_events += len(triggered)

        net = sum(p.size if p.side == "short" else -p.size for p in triggered)
        # long likidasyonu -> zorunlu SATIS (fiyati asagi iter)
        # short likidasyonu -> zorunlu ALIS (fiyati yukari iter)
        self.total_liquidated_notional += sum(p.size * price for p in triggered)

        if net == 0:
            return None
        side = "buy" if net > 0 else "sell"
        return Order(agent_id=self.agent_id, symbol=self._last_state.symbol, side=side, size=abs(net))

    def on_fill(self, order: Order, fill_price: float) -> None:
        # Motorun kendi PnL'i anlamli degil (havuz baskasina ait) -- takip etmiyoruz.
        pass
