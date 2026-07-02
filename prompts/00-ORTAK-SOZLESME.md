# Ortak Sözleşmeler (tüm bileşenler buna uyar)

> Bu dosya, `cas-market-simulator`'ın üç bileşenden beklediği **adaptör arayüzlerini** sabitler. Üç prompt (microstructure, macro-sentiment, yeni indikatör motoru) da bu sözleşmelere göre yazıldı. Her repo kendi reposunda gelişir; simülatör yalnızca bu veri tiplerine bağımlıdır (gevşek bağlılık).

```python
# Hedef veri tipleri — her bileşen kendi tarafında bunları ÜRETİR.
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime

# ── macro-sentiment-agent üretir ──────────────────────────────
@dataclass
class SentimentState:
    entity: str
    polarity: float            # [-1,+1] genel duyarlılık
    intensity: float           # 0..100 şiddet
    emotion: dict              # {"fear","greed","uncertainty"} her biri 0..1
    confidence: float          # 0..1
    fed_tone: float | None     # hawkish(+1)/dovish(-1) ekseni; yoksa None
    source_breakdown: dict     # {"news","social","fed"} -> polarite
    ts: datetime

@dataclass
class ShockEvent:              # simülasyona "dışsal şok" olarak enjekte edilir
    kind: str                  # "panic" | "euphoria" | "fed_tone" | "narrative_shift"
    entity: str
    magnitude: float           # 0..1 (şok büyüklüğü)
    decay_halflife_s: float    # şokun yarılanma süresi (sönümlenme)
    ts: datetime

# ── microstructure-analyzer üretir ────────────────────────────
@dataclass
class FlowState:
    token: str
    flow_imbalance: float      # [-1,+1] aktör-ağırlıklı emir akışı dengesizliği
    vpin_toxicity: float       # 0..1 akış toksisitesi
    whale_net_usd: float       # net balina akışı (USD)
    actor_mix: dict            # {"WHALE","MEV_BOT","RETAIL"} -> oran (toplam 1)
    direction_prob_up: float   # 0..1 kısa-vade yukarı olasılığı
    lead_lag_spread: float     # CEX-DEX lead-lag spread
    regime: str                # "normal" | "toxic" | "highvol"
    ts: datetime

# ── yeni indikatör+formasyon motoru üretir ────────────────────
@dataclass
class FactorVote:
    name: str
    vote: float                # [-1,+1] yön oyu
    weight: float              # başlangıç ağırlığı
    market: str                # "crypto" | "us" | "bist"

@dataclass
class PatternHit:
    name: str                  # "engulfing", "double_top", "triangle", ...
    direction: str             # "bull" | "bear" | "neutral"
    strength: float            # 0..1
    invalidation: float | None # geçersizlik fiyatı (varsa)

@dataclass
class Card:                    # tek sembol nihai analiz kartı
    symbol: str
    direction: str             # "LONG" | "SHORT" | "NEUTRAL"
    confidence: float          # 0..1
    votes: list[FactorVote]
    patterns: list[PatternHit]
    risk: dict                 # {"size_pct","stop","tp","cvar", ...}
    ts: datetime
```

## Adaptör Protocol'leri (simülatör tarafında)

```python
class SentimentFeed(Protocol):
    def latest(self, entity: str) -> SentimentState: ...
    def shocks(self, since: datetime) -> list[ShockEvent]: ...

class FlowFeed(Protocol):
    def latest(self, token: str) -> FlowState: ...

class FactorBrain(Protocol):
    def analyze(self, symbol: str, ohlcv, extra_factors: dict) -> Card: ...
    # extra_factors: {"flow": FlowState, "sentiment": SentimentState, "crowd_emergence": float}
```

## Genel kurallar (üçü için de)
1. **Simülasyon modu birinci sınıf olmalı:** Her bileşen, harici API/RPC/anahtar olmadan deterministik sentetik veri üretebilmeli (geliştirme + simülatör için).
2. **Saf programatik API:** `print` değil, çağrılabilir fonksiyon/sınıf döndür. CLI ayrı bir ince katman.
3. **Geriye uyum:** Mevcut testler kırılmaz; yeni yetenek ek olarak gelir.
4. **Konum:** "Karar destek / araştırma — yatırım tavsiyesi değildir." Bu ibare korunur.
5. **Zaman:** Tüm zaman damgaları UTC, `datetime` (tz-aware).
