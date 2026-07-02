"""Paper execution: sinyali (Card) simule edilmis bir emre cevirir.

Kural (FAZ-PLANI.md Faz 3): forward-test omurgasi olmadan sensorler
gurultudur. Bu modul gercek para hareket ettirmez -- yalnizca slipaj +
islem maliyeti modeliyle "gerceginde ne olurdu" sorusuna kaba bir
cevap uretir.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from ..adapters.contracts import Card


@dataclass
class PaperFill:
    symbol: str
    side: str            # "buy" | "sell"
    requested_price: float
    fill_price: float      # slipaj uygulanmis fiyat
    size_pct: float
    cost_pct: float         # komisyon+slipaj toplami (fiyatin yuzdesi)
    ts: datetime


class PaperExecutor:
    """Sabit-oranli slipaj + komisyon modeli. Gercek borsa mikroyapisi
    (defter derinligi vb.) Faz 5+'ta Environment/microstructure
    baglandiginda burasi zenginlestirilebilir; imza sabit kalmali."""

    def __init__(self, *, slippage_bps: float = 5.0, fee_bps: float = 4.0) -> None:
        self.slippage_bps = slippage_bps
        self.fee_bps = fee_bps

    def execute(self, card: Card, current_price: float) -> PaperFill | None:
        if card.direction not in ("LONG", "SHORT"):
            return None
        size_pct = float(card.risk.get("size_pct", 0.0) or 0.0)
        if size_pct <= 0.0:
            return None

        side = "buy" if card.direction == "LONG" else "sell"
        slip_mult = 1.0 + (self.slippage_bps / 10_000.0) * (1 if side == "buy" else -1)
        fill_price = current_price * slip_mult
        cost_pct = (self.slippage_bps + self.fee_bps) / 10_000.0

        return PaperFill(
            symbol=card.symbol,
            side=side,
            requested_price=current_price,
            fill_price=fill_price,
            size_pct=size_pct,
            cost_pct=cost_pct,
            ts=datetime.now(timezone.utc),
        )
