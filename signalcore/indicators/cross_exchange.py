"""Borsalar-arasi faktor: coinbase premium, lead-lag, fiyat farki.

Simulasyondaki arbitraj ajaninin gercek-veri karsiligi (bkz.
04-yeni-agent-onerileri.md). Sim mod: gercek coklu-borsa veri akisina
erisim yok, deterministik sentetik ureteç kullanilir.
"""
from __future__ import annotations

from dataclasses import dataclass

from ..core.types import FactorVote


@dataclass
class CrossExchangeState:
    coinbase_premium_bps: float     # + = ABD (spot/kurumsal) talebi one cikiyor
    lead_lag_spread: float           # + = bu borsa liderlik ediyor (fiyat oncu)
    price_diff_pct: float             # borsalar arasi ham fiyat farki


def cross_exchange_factor(
    state: CrossExchangeState,
    *,
    premium_scale_bps: float = 15.0,
    weight: float = 1.0,
) -> FactorVote:
    premium_component = max(-1.0, min(1.0, state.coinbase_premium_bps / premium_scale_bps))
    lead_component = max(-1.0, min(1.0, state.lead_lag_spread))

    vote = max(-1.0, min(1.0, 0.6 * premium_component + 0.4 * lead_component))
    return FactorVote(name="cross_exchange", vote=vote, weight=weight)


class SimCrossExchangeFeed:
    def __init__(self, *, seed: int | None = 25) -> None:
        import numpy as np

        self._rng = np.random.default_rng(seed)
        self._premium = 0.0
        self._lead_lag = 0.0
        self._price_diff = 0.0

    def latest(self, symbol: str) -> CrossExchangeState:
        self._premium = max(-50.0, min(50.0, self._premium - 0.2 * self._premium + self._rng.normal(0, 4.0)))
        self._lead_lag = max(-1.0, min(1.0, self._lead_lag - 0.2 * self._lead_lag + self._rng.normal(0, 0.1)))
        self._price_diff = max(-0.5, min(0.5, self._price_diff - 0.3 * self._price_diff + self._rng.normal(0, 0.03)))

        return CrossExchangeState(
            coinbase_premium_bps=self._premium,
            lead_lag_spread=self._lead_lag,
            price_diff_pct=self._price_diff,
        )
