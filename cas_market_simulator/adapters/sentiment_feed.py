"""SentimentFeed adaptoru.

Faz 0: stub -- macro-sentiment-agent'a henuz baglanmiyor, deterministik
sahte veri dondurur. Faz 3'te gercek/simulasyon moduna baglanacak
(bkz. FAZ-PLANI.md Faz 3).
"""
from __future__ import annotations

from datetime import datetime, timezone

from .contracts import SentimentState, ShockEvent


def _convert_macro_sentiment(src) -> SentimentState:
    """macro-sentiment-agent `SentimentState` -> simulator `SentimentState`."""
    return SentimentState(
        entity=src.entity,
        polarity=src.polarity,
        intensity=src.intensity,
        emotion=dict(getattr(src, "emotion", {})),
        confidence=src.confidence,
        fed_tone=src.fed_tone,
        source_breakdown=dict(getattr(src, "source_breakdown", {})),
        ts=src.ts if isinstance(src.ts, datetime) else datetime.now(timezone.utc),
    )


def _convert_macro_shock(src) -> ShockEvent:
    """macro-sentiment-agent `ShockEvent` -> simulator `ShockEvent`."""
    return ShockEvent(
        kind=src.kind,
        entity=src.entity,
        magnitude=src.magnitude,
        decay_halflife_s=src.decay_halflife_s,
        ts=src.ts if isinstance(src.ts, datetime) else datetime.now(timezone.utc),
    )


class StubSentimentFeed:
    """SentimentFeed Protocol'unu implemente eden sahte besleme.

    Sabit/hafif rastgele degerler dondurur; boru hattinin uctan uca
    calistigini dogrulamak icindir, gercek sinyal tasimaz.
    """

    def __init__(self, *, seed: int | None = None) -> None:
        self._seed = seed

    def latest(self, entity: str) -> SentimentState:
        return SentimentState(
            entity=entity,
            polarity=0.0,
            intensity=10.0,
            emotion={"fear": 0.2, "greed": 0.2, "uncertainty": 0.3},
            confidence=0.3,
            fed_tone=None,
            source_breakdown={"news": 0.0, "social": 0.0, "fed": 0.0},
            ts=datetime.now(timezone.utc),
        )

    def shocks(self, since: datetime) -> list[ShockEvent]:
        return []


class SimSentimentFeed:
    """Simulasyon-modu SentimentFeed: macro-sentiment-agent'a bagli degil
    (bu oturumda o repoya erisim yoktu) -- deterministik, seed'li bir
    Ornstein-Uhlenbeck sureci ile polarity/intensity uretir. Amac,
    gercek repo baglandiginda (Faz 3+) ayni Protocol'u koruyarak
    degistirilebilecek, gerceci-gorunumlu bir yer tutucu saglamak.

    Her `latest()` cagrisi ic durumu bir adim ilerletir (bir "tick"
    kabul edilir); boylece Engine dongusunde zaman icinde degisen,
    ama tekrarlanabilir bir sentiment sureci elde edilir.
    """

    def __init__(
        self,
        *,
        seed: int | None = 7,
        mean_reversion: float = 0.05,
        vol: float = 0.03,
        shock_probability: float = 0.01,
    ) -> None:
        import numpy as np

        self._rng = np.random.default_rng(seed)
        self._mean_reversion = mean_reversion
        self._vol = vol
        self._shock_probability = shock_probability
        self._polarity = 0.0
        self._intensity = 10.0

    def latest(self, entity: str) -> SentimentState:
        step = -self._mean_reversion * self._polarity + self._vol * self._rng.normal()
        self._polarity = max(-1.0, min(1.0, self._polarity + step))
        self._intensity = max(0.0, min(100.0, self._intensity + self._rng.normal(0, 2.0)))

        fear = max(0.0, min(1.0, 0.3 - self._polarity * 0.3 + self._rng.normal(0, 0.05)))
        greed = max(0.0, min(1.0, 0.3 + self._polarity * 0.3 + self._rng.normal(0, 0.05)))
        uncertainty = max(0.0, min(1.0, 0.4 - abs(self._polarity) * 0.2))

        return SentimentState(
            entity=entity,
            polarity=self._polarity,
            intensity=self._intensity,
            emotion={"fear": fear, "greed": greed, "uncertainty": uncertainty},
            confidence=min(1.0, self._intensity / 100.0 + 0.2),
            fed_tone=None,
            source_breakdown={"news": self._polarity, "social": self._polarity * 0.8, "fed": 0.0},
            ts=datetime.now(timezone.utc),
        )

    def shocks(self, since: datetime) -> list[ShockEvent]:
        if self._rng.random() >= self._shock_probability:
            return []
        kind = "panic" if self._polarity < 0 else "euphoria"
        return [
            ShockEvent(
                kind=kind,
                entity="market",
                magnitude=float(min(1.0, abs(self._polarity) + 0.3)),
                decay_halflife_s=300.0,
                ts=datetime.now(timezone.utc),
            )
        ]


class MacroSentimentFeed:
    """Gercek macro-sentiment-agent SentimentFeed sarici.

    macro-sentiment-agent reposu kurulu oldugunda calisir; offline modu
    varsayilandir -- harici API/anahtar olmadan deterministik senaryo
    replay veya varlik adindan turetilmis sentetik durum uretir.
    """

    def __init__(self, **kwargs) -> None:
        from macro_sentiment.api.sentiment_feed import SentimentFeed as _SentimentFeed

        self._feed = _SentimentFeed(**kwargs)

    def latest(self, entity: str) -> SentimentState:
        return _convert_macro_sentiment(self._feed.latest(entity))

    def shocks(self, since: datetime) -> list[ShockEvent]:
        return [_convert_macro_shock(s) for s in self._feed.shocks(since)]
