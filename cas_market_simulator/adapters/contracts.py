"""Ortak sozlesme (bkz. prompts/00-ORTAK-SOZLESME.md).

Bu dosya, uc bilesenin (macro-sentiment-agent, microstructure-analyzer,
signalcore) uretecegi veri tiplerini VE simulatorun bunlara erismek
icin kullandigi Protocol arayuzlerini sabitler. cas-market-simulator
yalnizca bu tiplere bagimlidir -- her bilesen kendi reposunda gelisir.

Not (Faz 0): signalcore su an ayni workspace icinde bir alt-paket
olarak barinsa da (bkz. /signalcore), sozlesme acisindan bagimsiz bir
bilesen gibi ele alinir -- adapters/factor_brain.py disinda hicbir yer
signalcore'un ic modullerine dogrudan bagli olmamalidir.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Protocol


# ── macro-sentiment-agent uretir ──────────────────────────────────
@dataclass
class SentimentState:
    entity: str
    polarity: float            # [-1,+1] genel duyarlilik
    intensity: float           # 0..100 siddet
    emotion: dict = field(default_factory=dict)   # {"fear","greed","uncertainty"} -> 0..1
    confidence: float = 0.0    # 0..1
    fed_tone: float | None = None   # hawkish(+1)/dovish(-1); yoksa None
    source_breakdown: dict = field(default_factory=dict)  # {"news","social","fed"} -> polarite
    ts: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ShockEvent:
    kind: str                  # "panic" | "euphoria" | "fed_tone" | "narrative_shift"
    entity: str
    magnitude: float           # 0..1
    decay_halflife_s: float
    ts: datetime = field(default_factory=datetime.utcnow)


# ── microstructure-analyzer uretir ────────────────────────────────
@dataclass
class FlowState:
    token: str
    flow_imbalance: float      # [-1,+1]
    vpin_toxicity: float       # 0..1
    whale_net_usd: float
    actor_mix: dict = field(default_factory=dict)   # {"WHALE","MEV_BOT","RETAIL"} -> oran
    direction_prob_up: float = 0.5   # 0..1
    lead_lag_spread: float = 0.0
    regime: str = "normal"     # "normal" | "toxic" | "highvol"
    ts: datetime = field(default_factory=datetime.utcnow)


# ── microstructure-analyzer uretir (defter okuma) ─────────────────
@dataclass
class BookState:
    """L2/L3 defter okuma ciktisi (bkz. microstructure-analyzer
    docs/00-ORTAK-SOZLESME.md BookState).

    Ham/temiz metrik verir; agirlik karari motor tarafinda verilir.
    `iceberg_score`/`spoof_score` kanit degil suphedir -- guven
    carpani olarak kullanilir.
    """
    symbol: str
    spread_bps: float          # >=0
    microprice: float          # >0
    depth_imbalance: float     # [-1,1]
    ofi: float                 # serbest
    queue_imbalance: float     # [-1,1]
    book_slope: float          # >=0
    kyle_lambda: float         # >=0
    # `mid` olmadan microprice sapmasi HESAPLANAMAZ. Yoklugu, asagidaki
    # to_signalcore_orderbook_state()'in sapmayi her zaman tam 0.0 uretmesine
    # yol aciyordu -- sessiz bir olu yol.
    mid: float = 0.0            # >0, en iyi alis-satis orta noktasi
    iceberg_score: float = 0.0  # [0,1]
    spoof_score: float = 0.0    # [0,1]
    absorption: float = 0.0     # [-1,1]
    liq_map_skew: float = 0.0   # [-1,1]
    ts: datetime = field(default_factory=datetime.utcnow)


# ── signalcore (yeni indikator+formasyon motoru) uretir ───────────
@dataclass
class FactorVote:
    name: str
    vote: float                # [-1,+1]
    weight: float
    market: str = "crypto"     # "crypto" | "us" | "bist"


@dataclass
class PatternHit:
    name: str
    direction: str              # "bull" | "bear" | "neutral"
    strength: float              # 0..1
    invalidation: float | None = None


@dataclass
class Card:
    symbol: str
    direction: str               # "LONG" | "SHORT" | "NEUTRAL"
    confidence: float             # 0..1
    votes: list[FactorVote] = field(default_factory=list)
    patterns: list[PatternHit] = field(default_factory=list)
    risk: dict = field(default_factory=dict)
    ts: datetime = field(default_factory=datetime.utcnow)


# ── Adaptor Protocol'leri (simulator tarafinda) ───────────────────
class SentimentFeed(Protocol):
    def latest(self, entity: str) -> SentimentState: ...
    def shocks(self, since: datetime) -> list[ShockEvent]: ...


class FlowFeed(Protocol):
    def latest(self, token: str) -> FlowState: ...


class BookFeed(Protocol):
    def latest(self, symbol: str) -> BookState: ...


class FactorBrain(Protocol):
    def analyze(self, symbol: str, ohlcv, extra_factors: dict) -> Card: ...
    # extra_factors: {"flow": FlowState, "sentiment": SentimentState, "crowd_emergence": float}
