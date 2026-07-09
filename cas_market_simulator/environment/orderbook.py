"""Fiyat-zaman öncelikli emir defteri çevresi (D7).

Mevcut `Environment`'in yerini alabilen ama ayni `submit/order/step`
arayuzuyle calisan basit bir limit/market eslesme motoru. Amac:
- Gercek emir defteri mekanigiyle flash crash/kaskad uretmek.
- `market_maker` gercek kotasyon versin, `liquidation_engine` defteri
  supursun.
- Ajanlarin emirleri agirlikli ortalama fiyatlarla (VWAP) dolsun.

Kasitli olarak basit tutuldu (~250 satir); gercek bir borsa defteri
degil, ama emergence ve slipaj kalibrasyonu icin yeterli.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from heapq import heappush, heappop
from typing import NamedTuple

from .base import EnvironmentState, Order as BaseOrder


class Fill(NamedTuple):
    price: float
    size: float
    side: str
    agent_id: str


@dataclass
class LimitOrder:
    agent_id: str
    symbol: str
    side: str          # "buy" | "sell"
    price: float
    size: float
    ts: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    _seq: int = field(default=0, repr=False)

    def __post_init__(self):
        if self.side not in ("buy", "sell"):
            raise ValueError(f"gecersiz side: {self.side}")
        if self.price <= 0 or self.size <= 0:
            raise ValueError("price ve size > 0 olmali")


@dataclass
class MarketOrder:
    agent_id: str
    symbol: str
    side: str
    size: float


Order = LimitOrder | MarketOrder


@dataclass
class _Level:
    """Tek fiyat seviyesi: (zaman, kalan_miktar, agent_id) kuyrugu."""
    price: float
    orders: list[tuple[int, float, str]] = field(default_factory=list)


class OrderBook:
    """İki tarafli limit defteri + market emri eslestirme."""

    def __init__(self, symbol: str, tick_size: float = 0.01):
        self.symbol = symbol
        self.tick_size = tick_size
        self._bids: dict[float, _Level] = {}  # fiyat -> level
        self._asks: dict[float, _Level] = {}
        self._seq = 0
        self._trades: list[Fill] = []

    # ---------- emir ekleme ----------
    def submit(self, order: Order) -> list[Fill]:
        self._seq += 1
        if isinstance(order, MarketOrder):
            return self._match_market(order)
        return self._add_limit(order)

    def _add_limit(self, order: LimitOrder) -> list[Fill]:
        # Fiyat once eslestirmeyi dene (agresif limit)
        fills = []
        if order.side == "buy":
            fills = self._match_ask(order)
            if order._seq == 0:
                order._seq = self._seq
            if order.size > 1e-12:
                level = self._bids.setdefault(order.price, _Level(order.price))
                level.orders.append((order._seq, order.size, order.agent_id))
        else:
            fills = self._match_bid(order)
            if order._seq == 0:
                order._seq = self._seq
            if order.size > 1e-12:
                level = self._asks.setdefault(order.price, _Level(order.price))
                level.orders.append((order._seq, order.size, order.agent_id))
        return fills

    def _match_market(self, order: MarketOrder) -> list[Fill]:
        if order.side == "buy":
            return self._match_ask(order)
        return self._match_bid(order)

    def _match_ask(self, aggressive: Order) -> list[Fill]:
        fills = []
        remaining = aggressive.size
        while remaining > 1e-12:
            best_ask = self._best_ask()
            if best_ask is None:
                break
            price = best_ask.price
            if isinstance(aggressive, LimitOrder) and aggressive.price < price:
                break
            level = self._asks[price]
            while level.orders and remaining > 1e-12:
                seq, qty, agent_id = level.orders[0]
                take = min(qty, remaining)
                fills.append(Fill(price, take, aggressive.side, aggressive.agent_id))
                level.orders[0] = (seq, qty - take, agent_id)
                if level.orders[0][1] <= 1e-12:
                    level.orders.pop(0)
                remaining -= take
            if not level.orders:
                del self._asks[price]
        return fills

    def _match_bid(self, aggressive: Order) -> list[Fill]:
        fills = []
        remaining = aggressive.size
        while remaining > 1e-12:
            best_bid = self._best_bid()
            if best_bid is None:
                break
            price = best_bid.price
            if isinstance(aggressive, LimitOrder) and aggressive.price > price:
                break
            level = self._bids[price]
            while level.orders and remaining > 1e-12:
                seq, qty, agent_id = level.orders[0]
                take = min(qty, remaining)
                fills.append(Fill(price, take, aggressive.side, aggressive.agent_id))
                level.orders[0] = (seq, qty - take, agent_id)
                if level.orders[0][1] <= 1e-12:
                    level.orders.pop(0)
                remaining -= take
            if not level.orders:
                del self._bids[price]
        return fills

    # ---------- gorunum ----------
    def _best_bid(self) -> _Level | None:
        if not self._bids:
            return None
        return max(self._bids.values(), key=lambda lvl: lvl.price)

    def _best_ask(self) -> _Level | None:
        if not self._asks:
            return None
        return min(self._asks.values(), key=lambda lvl: lvl.price)

    @property
    def mid(self) -> float:
        bb = self._best_bid()
        ba = self._best_ask()
        if bb and ba:
            return (bb.price + ba.price) / 2.0
        if bb:
            return bb.price
        if ba:
            return ba.price
        return 0.0

    @property
    def spread(self) -> float:
        bb = self._best_bid()
        ba = self._best_ask()
        if bb and ba:
            return ba.price - bb.price
        return 0.0

    def top(self, n: int = 10) -> tuple[list[tuple[float, float]], list[tuple[float, float]]]:
        bids = sorted(self._bids.values(), key=lambda lvl: lvl.price, reverse=True)[:n]
        asks = sorted(self._asks.values(), key=lambda lvl: lvl.price)[:n]
        def total(q):
            return sum(qty for _, qty, _ in q.orders)
        return ([(lvl.price, total(lvl)) for lvl in bids],
                [(lvl.price, total(lvl)) for lvl in asks])

    def cancel(self, agent_id: str, side: str, price: float) -> None:
        levels = self._bids if side == "buy" else self._asks
        level = levels.get(price)
        if level is None:
            return
        level.orders = [(s, q, a) for s, q, a in level.orders if a != agent_id]
        if not level.orders:
            del levels[price]


@dataclass
class OrderBookEnvironment:
    """`Environment` ile ayni arayuzu saglayan defter tabanli cevre."""

    symbol: str
    start_price: float
    tick_size: float = 0.01
    price_impact_per_lot: float = 0.0001
    _tick: int = field(default=0, init=False)
    _book: OrderBook = field(default=None, init=False)  # type: ignore[assignment]
    _pending: list[Order] = field(default_factory=list, init=False)
    history: list[EnvironmentState] = field(default_factory=list, init=False)

    def __post_init__(self):
        if self.start_price <= 0:
            raise ValueError("start_price > 0 olmali")
        self._book = OrderBook(self.symbol, self.tick_size)
        # Ilk likidite: iki yönlü kotasyon
        self._book.submit(LimitOrder("__mm__", self.symbol, "buy",
                                     self.start_price * 0.9995, 1_000.0))
        self._book.submit(LimitOrder("__mm__", self.symbol, "sell",
                                     self.start_price * 1.0005, 1_000.0))
        snap = self._snapshot()
        self.history = [snap]

    def _snapshot(self) -> EnvironmentState:
        return EnvironmentState(
            symbol=self.symbol,
            price=self._book.mid,
            tick=self._tick,
            ts=datetime.now(timezone.utc),
        )

    def submit(self, order: Order | BaseOrder) -> None:
        if order.symbol != self.symbol:
            raise ValueError(f"sembol uyumsuz: {order.symbol} != {self.symbol}")
        if isinstance(order, BaseOrder) and not isinstance(order, (LimitOrder, MarketOrder)):
            order = MarketOrder(order.agent_id, order.symbol, order.side, order.size)
        self._pending.append(order)

    def step(self, *, extra_impact: float = 0.0) -> EnvironmentState:
        """Bekleyen emirleri eslestir; ekstra sok fiyatini iter."""
        all_fills: list[Fill] = []
        for order in self._pending:
            fills = self._book.submit(order)
            all_fills.extend(fills)

        # Ekstra sok: piyasa emri olarak isle (yonsuz basin)
        if extra_impact != 0.0:
            side = "sell" if extra_impact < 0 else "buy"
            shock_order = MarketOrder("__shock__", self.symbol, side,
                                      abs(extra_impact) * 100.0)
            all_fills.extend(self._book.submit(shock_order))

        # Fiyat: son islemlerin VWAP'i yoksa mid
        if all_fills:
            vwap = sum(f.price * f.size for f in all_fills) / sum(f.size for f in all_fills)
            if vwap > 0:
                # Mid'i VWAP'e yavasca cek
                self._book._bids.clear()
                self._book._asks.clear()
                self._book.submit(LimitOrder("__mm__", self.symbol, "buy",
                                             vwap * (1.0 - 0.0005), 1_000.0))
                self._book.submit(LimitOrder("__mm__", self.symbol, "sell",
                                             vwap * (1.0 + 0.0005), 1_000.0))

        self._tick += 1
        self._pending.clear()
        snap = self._snapshot()
        self.history.append(snap)
        return snap

    @property
    def state(self) -> EnvironmentState:
        return self._snapshot()
