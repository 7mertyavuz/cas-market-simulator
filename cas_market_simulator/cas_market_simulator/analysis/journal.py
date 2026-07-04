"""Forward-test defteri: sinyali kaydeder, N tick sonra sonucu olcer.

04-A #1 onceligi (bkz. FAZ-PLANI.md Faz 3): "Bu olmadan sonraki
sensorler gurultudur." Journal, PaperExecutor'un ciktisini alir, bir
ufuk (horizon_ticks) sonra fiyati okuyup gerceklesen getiriyi
(maliyet dahil) kaydeder. Bu defter, ileride signalcore'un
factor_tracker'ina (Faz 1b) forward-return kaynagi olarak baglanabilir
-- boylece "gercek win-rate" varsayim degil olculen bir sey olur.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from .execution import PaperFill


@dataclass
class JournalEntry:
    entry_tick: int
    symbol: str
    side: str            # "buy" | "sell"
    entry_price: float
    size_pct: float
    cost_pct: float
    horizon_ticks: int
    resolved: bool = False
    exit_price: float | None = None
    pnl_pct: float | None = None
    entry_ts: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    exit_ts: datetime | None = None


class Journal:
    """Acik/kapali sinyal defteri. Sermaye simule etmez -- yalnizca
    getiri yuzdesi (maliyet dusulmus) kaydeder; portfoy boyutlandirma
    Faz 9'da analysis/portfolio.py'nin isidir."""

    def __init__(self, *, horizon_ticks: int = 10) -> None:
        self.horizon_ticks = horizon_ticks
        self.entries: list[JournalEntry] = []

    def record(self, fill: PaperFill, *, tick: int) -> JournalEntry:
        entry = JournalEntry(
            entry_tick=tick,
            symbol=fill.symbol,
            side=fill.side,
            entry_price=fill.fill_price,
            size_pct=fill.size_pct,
            cost_pct=fill.cost_pct,
            horizon_ticks=self.horizon_ticks,
        )
        self.entries.append(entry)
        return entry

    def resolve_due(self, *, current_tick: int, current_price: float) -> list[JournalEntry]:
        """horizon_ticks'i dolmus, henuz cozulmemis kayitlari fiyatla
        kapatir ve maliyet dahil pnl_pct hesaplar."""
        newly_resolved: list[JournalEntry] = []
        for e in self.entries:
            if e.resolved or (current_tick - e.entry_tick) < e.horizon_ticks:
                continue
            raw_return = (
                (current_price - e.entry_price) / e.entry_price
                if e.side == "buy"
                else (e.entry_price - current_price) / e.entry_price
            )
            e.exit_price = current_price
            e.pnl_pct = raw_return - e.cost_pct
            e.resolved = True
            e.exit_ts = datetime.now(timezone.utc)
            newly_resolved.append(e)
        return newly_resolved

    def stats(self) -> dict:
        resolved = [e for e in self.entries if e.resolved]
        n = len(resolved)
        open_count = len(self.entries) - n
        if n == 0:
            return {"n": 0, "win_rate": 0.0, "avg_pnl_pct": 0.0, "total_pnl_pct": 0.0, "open": open_count}

        wins = sum(1 for e in resolved if (e.pnl_pct or 0.0) > 0)
        total = sum(e.pnl_pct or 0.0 for e in resolved)
        return {
            "n": n,
            "win_rate": wins / n,
            "avg_pnl_pct": total / n,
            "total_pnl_pct": total,
            "open": open_count,
        }

    def forward_return_samples(self) -> list[tuple[float, float]]:
        """(vote-yonlu isaret, gerceklesen getiri) ciftleri -- signalcore
        factor_tracker'a kayit icin uygun format (Faz 3+ entegrasyonu)."""
        resolved = [e for e in self.entries if e.resolved]
        sign = {"buy": 1.0, "sell": -1.0}
        return [(sign[e.side], e.pnl_pct or 0.0) for e in resolved]
