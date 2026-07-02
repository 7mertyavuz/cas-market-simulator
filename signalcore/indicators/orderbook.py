"""CEX emir defteri faktoru: spread, derinlik dengesizligi, likidasyon haritasi.

microstructure-analyzer'in DEX/mempool tarafini tamamlar (bkz.
04-yeni-agent-onerileri.md). Bu oturumda gercek borsa defteri erisimi
yok; `SimOrderbookFeed` deterministik sim mod uretir.
"""
from __future__ import annotations

from dataclasses import dataclass

from ..core.types import FactorVote


@dataclass
class OrderbookState:
    spread_bps: float                # bid-ask spread, baz puan
    depth_imbalance: float            # [-1,1]: + = bid tarafinda daha fazla derinlik
    liquidation_map_skew: float        # [-1,1]: + = ustte (kisa likidasyonlari) daha yogun likidite


def orderbook_factor(
    state: OrderbookState,
    *,
    spread_penalty_bps: float = 20.0,
    weight: float = 1.0,
) -> FactorVote:
    """Derinlik dengesizligi ana yon bileseni; likidasyon haritasi
    (magnet etkisi -- fiyat yogun likidasyon bolgesine cekilir) ikincil.
    Genis spread (dusuk likidite/yuksek belirsizlik) guveni/vote'u kisar.
    """
    base = 0.7 * state.depth_imbalance + 0.3 * state.liquidation_map_skew
    liquidity_penalty = max(0.2, 1.0 - min(1.0, state.spread_bps / spread_penalty_bps))
    vote = max(-1.0, min(1.0, base * liquidity_penalty))
    return FactorVote(name="orderbook", vote=vote, weight=weight)


class SimOrderbookFeed:
    def __init__(self, *, seed: int | None = 22) -> None:
        import numpy as np

        self._rng = np.random.default_rng(seed)
        self._spread = 5.0
        self._imbalance = 0.0
        self._liq_skew = 0.0

    def latest(self, symbol: str) -> OrderbookState:
        self._spread = max(0.5, min(50.0, self._spread + self._rng.normal(0, 1.0)))
        self._imbalance = max(-1.0, min(1.0, self._imbalance - 0.15 * self._imbalance + self._rng.normal(0, 0.08)))
        self._liq_skew = max(-1.0, min(1.0, self._liq_skew - 0.1 * self._liq_skew + self._rng.normal(0, 0.06)))

        return OrderbookState(
            spread_bps=self._spread,
            depth_imbalance=self._imbalance,
            liquidation_map_skew=self._liq_skew,
        )
