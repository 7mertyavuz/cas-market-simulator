"""Minimal Environment.

Faz 0: yalnizca bir fiyat durumu tutan, ajan emirlerini kabul edip
naif bir sekilde fiyata yansitan boru-hatti iskeleti. Faz 5'te
microstructure-analyzer'in simulasyon modu "cevre" olarak buraya
takilacak (order book / eslesme motoru); simdilik sozlesme sabit
kalsin diye kasitli olarak kaba/basit.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class Order:
    agent_id: str
    symbol: str
    side: str        # "buy" | "sell"
    size: float       # >0

    def __post_init__(self) -> None:
        if self.side not in ("buy", "sell"):
            raise ValueError(f"gecersiz side: {self.side}")
        if self.size <= 0:
            raise ValueError("size > 0 olmali")


@dataclass
class EnvironmentState:
    symbol: str
    price: float
    tick: int
    ts: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class Environment:
    """En basit geri-bildirim dongusu: net emir dengesizligi fiyati iter.

    Bu bir order book DEGIL -- Faz 5'e kadar yer tutucu. Amac: ajan
    emri -> cevre guncellemesi -> yeni gozlem dongusunun uctan uca
    calistigini kanitlamak.
    """

    def __init__(self, symbol: str, start_price: float, *, impact: float = 0.001) -> None:
        if start_price <= 0:
            raise ValueError("start_price > 0 olmali")
        self.symbol = symbol
        self._price = start_price
        self._tick = 0
        self._impact = impact
        self._pending: list[Order] = []
        self.history: list[EnvironmentState] = [self._snapshot()]

    def _snapshot(self) -> EnvironmentState:
        return EnvironmentState(symbol=self.symbol, price=self._price, tick=self._tick)

    def submit(self, order: Order) -> None:
        if order.symbol != self.symbol:
            raise ValueError(f"sembol uyumsuz: {order.symbol} != {self.symbol}")
        self._pending.append(order)

    def step(self) -> EnvironmentState:
        """Bekleyen emirleri uygular, fiyati gunceller, tick'i ilerletir."""
        net = sum(o.size if o.side == "buy" else -o.size for o in self._pending)
        self._price = max(self._price * (1.0 + self._impact * net), 1e-8)
        self._tick += 1
        self._pending.clear()
        snap = self._snapshot()
        self.history.append(snap)
        return snap

    @property
    def state(self) -> EnvironmentState:
        return self._snapshot()
