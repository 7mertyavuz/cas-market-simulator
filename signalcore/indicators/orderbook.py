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
    # D6: microstructure-analyzer BookState'den gelen ek okumalar
    microprice_dev: float = 0.0       # microprice / mid - 1 (bps cinsinden degil, kesir)
    ofi: float = 0.0                  # event-bazli order flow imbalance
    spoof_score: float = 0.0          # [0,1]: yuksekse derinlik sinyaline guven azalir
    absorption: float = 0.0           # [-1,1]: + = satis baskisi emiliyor (bid guclu)
    iceberg_score: float = 0.0        # [0,1]: gizli likidite sezisi, teyit edici


def orderbook_factor(
    state: OrderbookState,
    *,
    spread_penalty_bps: float = 20.0,
    weight: float = 1.0,
) -> FactorVote:
    """Derinlik dengesizligi ana yon bileseni; likidasyon haritasi
    (magnet etkisi -- fiyat yogun likidasyon bolgesine cekilir) ikincil.

    D6: absorption ve iceberg teyit edici; spoof_score cezalandirici.
    microprice_dev ve OFI vote'a hafif ek katki verir.
    """
    base = (
        0.55 * state.depth_imbalance
        + 0.25 * state.liquidation_map_skew
        + 0.10 * state.microprice_dev * 100.0  # bps -> ~[-1,1]
        + 0.05 * _clamp(state.ofi / 20.0, -1.0, 1.0)
    )
    # Teyit / ceza
    confirmation = 1.0 + 0.2 * state.iceberg_score + 0.15 * _clamp(state.absorption, 0.0, 1.0)
    spoof_penalty = max(0.4, 1.0 - state.spoof_score)
    adjusted = base * confirmation * spoof_penalty

    liquidity_penalty = max(0.2, 1.0 - min(1.0, state.spread_bps / spread_penalty_bps))
    vote = max(-1.0, min(1.0, adjusted * liquidity_penalty))
    return FactorVote(name="orderbook", vote=vote, weight=weight)


def _clamp(x: float, lo: float, hi: float) -> float:
    return lo if x < lo else hi if x > hi else x


class SimOrderbookFeed:
    def __init__(self, *, seed: int | None = 22) -> None:
        import numpy as np

        self._rng = np.random.default_rng(seed)
        self._spread = 5.0
        self._imbalance = 0.0
        self._liq_skew = 0.0
        self._microprice_dev = 0.0
        self._ofi = 0.0
        self._spoof = 0.0
        self._absorption = 0.0
        self._iceberg = 0.0

    def latest(self, symbol: str) -> OrderbookState:
        self._spread = max(0.5, min(50.0, self._spread + self._rng.normal(0, 1.0)))
        self._imbalance = max(-1.0, min(1.0, self._imbalance - 0.15 * self._imbalance + self._rng.normal(0, 0.08)))
        self._liq_skew = max(-1.0, min(1.0, self._liq_skew - 0.1 * self._liq_skew + self._rng.normal(0, 0.06)))
        self._microprice_dev = max(-0.001, min(0.001, self._microprice_dev + self._rng.normal(0, 0.0002)))
        self._ofi = max(-20.0, min(20.0, self._ofi + self._rng.normal(0, 2.0)))
        self._spoof = max(0.0, min(1.0, self._spoof + self._rng.normal(0, 0.05)))
        self._absorption = max(-1.0, min(1.0, self._absorption + self._rng.normal(0, 0.1)))
        self._iceberg = max(0.0, min(1.0, self._iceberg + self._rng.normal(0, 0.05)))

        return OrderbookState(
            spread_bps=self._spread,
            depth_imbalance=self._imbalance,
            liquidation_map_skew=self._liq_skew,
            microprice_dev=self._microprice_dev,
            ofi=self._ofi,
            spoof_score=self._spoof,
            absorption=self._absorption,
            iceberg_score=self._iceberg,
        )
