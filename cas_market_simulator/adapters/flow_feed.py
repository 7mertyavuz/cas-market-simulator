"""FlowFeed adaptoru.

Faz 0: stub -- microstructure-analyzer'a henuz baglanmiyor. Faz 3'te
simulasyon moduna baglanacak.
"""
from __future__ import annotations

from datetime import datetime, timezone

from .contracts import FlowState


def _convert_micro_flow(src) -> FlowState:
    """microstructure-analyzer `src.models.FlowState` -> simulator
    `FlowState`. Alan adlari birebir ayni; bu yalnizca siniflar arasi
    gevsek baglama katidir.
    """
    return FlowState(
        token=src.token,
        flow_imbalance=src.flow_imbalance,
        vpin_toxicity=src.vpin_toxicity,
        whale_net_usd=src.whale_net_usd,
        actor_mix=dict(getattr(src, "actor_mix", {})),
        direction_prob_up=src.direction_prob_up,
        lead_lag_spread=src.lead_lag_spread,
        regime=src.regime,
        ts=src.ts if isinstance(src.ts, datetime) else datetime.now(timezone.utc),
    )


class StubFlowFeed:
    """FlowFeed Protocol'unu implemente eden sahte besleme."""

    def __init__(self, *, seed: int | None = None) -> None:
        self._seed = seed

    def latest(self, token: str) -> FlowState:
        return FlowState(
            token=token,
            flow_imbalance=0.0,
            vpin_toxicity=0.1,
            whale_net_usd=0.0,
            actor_mix={"WHALE": 0.1, "MEV_BOT": 0.1, "RETAIL": 0.8},
            direction_prob_up=0.5,
            lead_lag_spread=0.0,
            regime="normal",
            ts=datetime.now(timezone.utc),
        )


class SimFlowFeed:
    """Simulasyon-modu FlowFeed: microstructure-analyzer'a bagli degil
    (bu oturumda o repoya erisim yoktu) -- deterministik, seed'li bir
    mean-reverting surecle flow_imbalance/vpin_toxicity uretir. Gercek
    repo baglandiginda (Faz 3+ ileri iterasyon) ayni Protocol korunarak
    degistirilebilir.
    """

    def __init__(
        self,
        *,
        seed: int | None = 11,
        mean_reversion: float = 0.08,
        vol: float = 0.05,
    ) -> None:
        import numpy as np

        self._rng = np.random.default_rng(seed)
        self._mean_reversion = mean_reversion
        self._vol = vol
        self._flow_imbalance = 0.0
        self._whale_net_usd = 0.0

    def latest(self, token: str) -> FlowState:
        step = -self._mean_reversion * self._flow_imbalance + self._vol * self._rng.normal()
        self._flow_imbalance = max(-1.0, min(1.0, self._flow_imbalance + step))

        self._whale_net_usd += self._rng.normal(0, 1000.0) + self._flow_imbalance * 2000.0
        vpin = max(0.0, min(1.0, 0.15 + abs(self._flow_imbalance) * 0.3 + self._rng.normal(0, 0.03)))

        retail = max(0.0, min(1.0, 0.7 - abs(self._flow_imbalance) * 0.2))
        whale = max(0.0, min(1.0, 0.15 + abs(self._flow_imbalance) * 0.15))
        mev = max(0.0, 1.0 - retail - whale)

        regime = "toxic" if vpin > 0.5 else ("highvol" if abs(self._flow_imbalance) > 0.6 else "normal")

        return FlowState(
            token=token,
            flow_imbalance=self._flow_imbalance,
            vpin_toxicity=vpin,
            whale_net_usd=self._whale_net_usd,
            actor_mix={"WHALE": whale, "MEV_BOT": mev, "RETAIL": retail},
            direction_prob_up=0.5 + self._flow_imbalance * 0.4,
            lead_lag_spread=self._rng.normal(0, 0.01),
            regime=regime,
            ts=datetime.now(timezone.utc),
        )


class MicrostructureFlowFeed:
    """Gercek microstructure-analyzer FlowFeed sarici.

    microstructure-analyzer reposu kurulu oldugunda calisir; yoksa
    ImportError verir (bu sinifi kullanmadan once kurulum yapilmali).
    Sim modu birinci siniftir -- WSS_URL bos ise deterministik sentetik
    akis uretir, harici bagimlilik gerektirmez.
    """

    def __init__(self, **kwargs) -> None:
        # Paket adi `src` -> `lob_microstructure` olarak degisti.
        from lob_microstructure.api.flow_feed import FlowFeed as _FlowFeed

        self._feed = _FlowFeed(**kwargs)

    def latest(self, token: str) -> FlowState:
        return _convert_micro_flow(self._feed.latest(token))
