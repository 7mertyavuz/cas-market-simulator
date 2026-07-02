"""Ortak sozlesme veri tipleri (bkz. 00-ORTAK-SOZLESME.md).

Bu modul, cas-market-simulator/adapters/contracts.py ile birebir ayni
alanlara sahip olmali; signalcore bunlari kendi tarafinda ISLER ve
uretir, simulator tarafi ayni tipleri ITHAL/YENIDEN TANIMLAR (adapter
katmaninda). Cift kaynak-of-truth riskini onlemek icin simulator
adapters/contracts.py bu dosyadaki tanimlarla senkron tutulmalidir.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class OHLCVBar:
    ts: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass
class FactorVote:
    name: str
    vote: float          # [-1, +1] yon oyu
    weight: float         # baslangic agirligi
    market: str = "crypto"  # "crypto" | "us" | "bist"

    def __post_init__(self) -> None:
        if not -1.0 <= self.vote <= 1.0:
            raise ValueError(f"vote [-1,1] araliginda olmali, geldi: {self.vote}")
        if self.weight < 0:
            raise ValueError(f"weight negatif olamaz: {self.weight}")


@dataclass
class PatternHit:
    name: str                       # "engulfing", "double_top", "triangle", ...
    direction: str                  # "bull" | "bear" | "neutral"
    strength: float                 # 0..1
    invalidation: float | None = None  # gecersizlik fiyati (varsa)

    def __post_init__(self) -> None:
        if self.direction not in ("bull", "bear", "neutral"):
            raise ValueError(f"gecersiz direction: {self.direction}")
        if not 0.0 <= self.strength <= 1.0:
            raise ValueError(f"strength [0,1] araliginda olmali: {self.strength}")


@dataclass
class Card:
    symbol: str
    direction: str                  # "LONG" | "SHORT" | "NEUTRAL"
    confidence: float                # 0..1
    votes: list[FactorVote] = field(default_factory=list)
    patterns: list[PatternHit] = field(default_factory=list)
    risk: dict = field(default_factory=dict)   # {"size_pct","stop","tp","cvar", ...}
    ts: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self) -> None:
        if self.direction not in ("LONG", "SHORT", "NEUTRAL"):
            raise ValueError(f"gecersiz direction: {self.direction}")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"confidence [0,1] araliginda olmali: {self.confidence}")
