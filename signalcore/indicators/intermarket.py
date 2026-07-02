"""Piyasalar-arasi (intermarket) faktor: DXY, altin, 10Y, S&P, risk-on/off.

Kripto tek basina hareket etmez -- makro baglam guven carpani (bkz.
04-yeni-agent-onerileri.md). Sim mod: gercek piyasa veri saglayicisina
erisim yok, deterministik sentetik ureteç kullanilir.
"""
from __future__ import annotations

from dataclasses import dataclass

from ..core.types import FactorVote


@dataclass
class IntermarketState:
    dxy_change_pct: float        # dolar endeksi degisimi (+ guclu dolar, risk varliklar icin olumsuz)
    gold_change_pct: float
    us10y_change_bps: float       # 10Y getiri degisimi (+ sikilasan finansal kosullar)
    spx_change_pct: float
    risk_on_off_score: float       # [-1,1]: + = risk-on rejim


def intermarket_factor(
    state: IntermarketState,
    *,
    dxy_scale_pct: float = 1.0,
    us10y_scale_bps: float = 15.0,
    weight: float = 1.0,
) -> FactorVote:
    dxy_component = -max(-1.0, min(1.0, state.dxy_change_pct / dxy_scale_pct))
    rates_component = -max(-1.0, min(1.0, state.us10y_change_bps / us10y_scale_bps))
    spx_component = max(-1.0, min(1.0, state.spx_change_pct / dxy_scale_pct))
    risk_component = state.risk_on_off_score

    vote = max(-1.0, min(1.0, 0.3 * dxy_component + 0.2 * rates_component + 0.2 * spx_component + 0.3 * risk_component))
    return FactorVote(name="intermarket", vote=vote, weight=weight)


class SimIntermarketFeed:
    def __init__(self, *, seed: int | None = 24) -> None:
        import numpy as np

        self._rng = np.random.default_rng(seed)
        self._dxy = 0.0
        self._gold = 0.0
        self._us10y = 0.0
        self._spx = 0.0
        self._risk = 0.0

    def latest(self, symbol: str) -> IntermarketState:
        self._dxy = max(-2.0, min(2.0, self._dxy - 0.2 * self._dxy + self._rng.normal(0, 0.15)))
        self._gold = max(-2.0, min(2.0, self._gold - 0.2 * self._gold + self._rng.normal(0, 0.2)))
        self._us10y = max(-30.0, min(30.0, self._us10y - 0.2 * self._us10y + self._rng.normal(0, 3.0)))
        self._spx = max(-2.0, min(2.0, self._spx - 0.2 * self._spx + self._rng.normal(0, 0.3)))
        self._risk = max(-1.0, min(1.0, self._risk - 0.1 * self._risk + self._rng.normal(0, 0.08)))

        return IntermarketState(
            dxy_change_pct=self._dxy,
            gold_change_pct=self._gold,
            us10y_change_bps=self._us10y,
            spx_change_pct=self._spx,
            risk_on_off_score=self._risk,
        )
