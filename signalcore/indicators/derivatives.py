"""Turev piyasasi faktoru: funding, OI, basis, IV, put/call.

Kaynak: 04-yeni-agent-onerileri.md -- "en guclu erken sinyal" (kripto
yon icin). Bu oturumda gercek borsa/veri saglayici API'sine erisim
yok; `SimDerivativesFeed` deterministik, seed'li bir sim mod uretir
(bkz. 00-ORTAK-SOZLESME.md kural #1: simulasyon modu birinci sinif).
Gercek veri baglandiginda `DerivativesState` sozlesmesi + `derivatives_factor`
imzasi sabit kalmali, yalnizca besleme (feed) degisir.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from ..core.types import FactorVote


@dataclass
class DerivativesState:
    funding_rate: float          # tipik araligi ~[-0.01, 0.01] (8s funding)
    oi_change_pct: float          # son periyotta open interest degisimi
    basis_pct: float               # vadeli-spot farki (contango + / backwardation -)
    iv_percentile: float            # 0..100, tarihsel IV siralamasi
    put_call_ratio: float           # >1 = put agirlikli (korku), <1 = call agirlikli


def derivatives_factor(
    state: DerivativesState,
    *,
    funding_extreme: float = 0.005,
    basis_extreme_pct: float = 0.05,
    weight: float = 1.0,
) -> FactorVote:
    """Funding+OI birlikte yorumlanir: ayni yonde buyuyen OI + funding =
    kaldiracli pozisyon birikimi (devam sinyali, ama asiri ise kalabalik
    riski -- vote'u sonlendirmiyoruz, magnitude'u kisitliyoruz).
    Basis (contango/backwardation) trend teyidi olarak eklenir.
    Put/call>1.2 hafif ayi, <0.8 hafif boga egilimi olarak katilir.
    """
    funding_component = max(-1.0, min(1.0, state.funding_rate / funding_extreme))
    oi_confirms = 1.0 if (state.oi_change_pct > 0) == (state.funding_rate > 0) else 0.6
    funding_component *= oi_confirms

    basis_component = max(-1.0, min(1.0, state.basis_pct / basis_extreme_pct))

    pc = state.put_call_ratio
    pc_component = 0.0
    if pc > 1.2:
        pc_component = -min(1.0, (pc - 1.0))
    elif pc < 0.8:
        pc_component = min(1.0, (1.0 - pc))

    vote = max(-1.0, min(1.0, 0.5 * funding_component + 0.3 * basis_component + 0.2 * pc_component))
    return FactorVote(name="derivatives", vote=vote, weight=weight)


class SimDerivativesFeed:
    """Deterministik, mean-reverting sentetik turev veri ureteci."""

    def __init__(self, *, seed: int | None = 21) -> None:
        import numpy as np

        self._rng = np.random.default_rng(seed)
        self._funding = 0.0
        self._oi_change = 0.0
        self._basis = 0.0
        self._iv_pct = 50.0
        self._put_call = 1.0

    def latest(self, symbol: str) -> DerivativesState:
        self._funding = max(-0.02, min(0.02, self._funding - 0.1 * self._funding + self._rng.normal(0, 0.002)))
        self._oi_change = max(-0.2, min(0.2, self._oi_change - 0.2 * self._oi_change + self._rng.normal(0, 0.02)))
        self._basis = max(-0.1, min(0.1, self._basis - 0.1 * self._basis + self._rng.normal(0, 0.005)))
        self._iv_pct = max(0.0, min(100.0, self._iv_pct + self._rng.normal(0, 3.0)))
        self._put_call = max(0.3, min(3.0, self._put_call - 0.1 * (self._put_call - 1.0) + self._rng.normal(0, 0.05)))

        return DerivativesState(
            funding_rate=self._funding,
            oi_change_pct=self._oi_change,
            basis_pct=self._basis,
            iv_percentile=self._iv_pct,
            put_call_ratio=self._put_call,
        )
