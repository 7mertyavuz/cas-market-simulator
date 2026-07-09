"""D8 — Defter kayit/replay ve forward-test entegrasyonu.

`BookRecorder`: `OrderBookEnvironment` (veya `BookFeed`) uzerunden alinan
snapshot'lari JSONL olarak diske yazar. Ayni kayit deterministik olarak
oynatilabilir; boylece backtest ve factor_tracker beslemesi tekrarlanabilir.

Format (satir basi bir JSON):
  {"tick": int, "ts": ISO, "mid": float, "spread": float,
   "bids": [[price, qty], ...], "asks": [[price, qty], ...],
   "trades": [[price, qty, side], ...]}
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterator

from .orderbook import OrderBookEnvironment, OrderBook


@dataclass
class BookSnapshot:
    tick: int
    ts: str
    mid: float
    spread: float
    bids: list[list[float]]
    asks: list[list[float]]
    trades: list[list[float]]


class BookRecorder:
    """`OrderBookEnvironment` snapshot'larini JSONL olarak kaydeder."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self._ticks: list[int] = []

    def record(self, env: OrderBookEnvironment) -> None:
        snap = env.state
        bids, asks = env._book.top(20)
        row = {
            "tick": snap.tick,
            "ts": snap.ts.isoformat(),
            "mid": round(snap.price, 8),
            "spread": round(env._book.spread, 8),
            "bids": [[round(p, 8), round(q, 6)] for p, q in bids],
            "asks": [[round(p, 8), round(q, 6)] for p, q in asks],
            "trades": [
                [round(t.price, 8), round(t.size, 6), t.side]
                for t in getattr(env._book, "_trades", [])
            ],
        }
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
        self._ticks.append(snap.tick)

    def replay(self) -> Iterator[BookSnapshot]:
        if not self.path.exists():
            return
        with self.path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                raw = json.loads(line)
                yield BookSnapshot(
                    tick=raw["tick"],
                    ts=raw["ts"],
                    mid=raw["mid"],
                    spread=raw["spread"],
                    bids=raw["bids"],
                    asks=raw["asks"],
                    trades=raw.get("trades", []),
                )

    def reset(self) -> None:
        if self.path.exists():
            self.path.unlink()
        self._ticks.clear()
