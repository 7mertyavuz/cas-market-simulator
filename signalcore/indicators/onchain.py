"""On-chain fundamental faktoru: borsa netflow, stablecoin arzi, aktif adres, NVT, ETF akisi.

Orta-vade arz/talep rejimi; sentiment'ten bagimsiz bir eksen (bkz.
04-yeni-agent-onerileri.md). Sim mod: gercek zincir verisi (Glassnode/
Dune vb.) erisimi yok, deterministik sentetik ureteç kullanilir.
"""
from __future__ import annotations

from dataclasses import dataclass

from ..core.types import FactorVote


@dataclass
class OnchainState:
    exchange_netflow_usd: float         # + = borsaya giris (satis baskisi), - = cikis (biriktirme)
    stablecoin_supply_change_pct: float  # + = kuru barut artiyor (potansiyel alim gucu)
    active_addresses_change_pct: float
    nvt_zscore: float                     # + = fiyat, network kullanimina gore "pahali"
    etf_flow_usd: float                    # + = net ETF girisi


def onchain_factor(
    state: OnchainState,
    *,
    netflow_scale_usd: float = 5_000_000.0,
    etf_scale_usd: float = 10_000_000.0,
    weight: float = 1.0,
) -> FactorVote:
    netflow_component = -max(-1.0, min(1.0, state.exchange_netflow_usd / netflow_scale_usd))
    stablecoin_component = max(-1.0, min(1.0, state.stablecoin_supply_change_pct * 10))
    nvt_component = -max(-1.0, min(1.0, state.nvt_zscore / 2.0))
    etf_component = max(-1.0, min(1.0, state.etf_flow_usd / etf_scale_usd))

    vote = max(-1.0, min(1.0, 0.4 * netflow_component + 0.2 * stablecoin_component + 0.2 * nvt_component + 0.2 * etf_component))
    return FactorVote(name="onchain", vote=vote, weight=weight)


class SimOnchainFeed:
    def __init__(self, *, seed: int | None = 23) -> None:
        import numpy as np

        self._rng = np.random.default_rng(seed)
        self._netflow = 0.0
        self._stable_supply = 0.0
        self._active_addr = 0.0
        self._nvt = 0.0
        self._etf = 0.0

    def latest(self, symbol: str) -> OnchainState:
        self._netflow = self._netflow * 0.7 + self._rng.normal(0, 3_000_000.0)
        self._stable_supply = max(-0.05, min(0.05, self._stable_supply - 0.1 * self._stable_supply + self._rng.normal(0, 0.005)))
        self._active_addr = max(-0.1, min(0.1, self._active_addr - 0.15 * self._active_addr + self._rng.normal(0, 0.01)))
        self._nvt = max(-3.0, min(3.0, self._nvt - 0.1 * self._nvt + self._rng.normal(0, 0.3)))
        self._etf = self._etf * 0.7 + self._rng.normal(0, 5_000_000.0)

        return OnchainState(
            exchange_netflow_usd=self._netflow,
            stablecoin_supply_change_pct=self._stable_supply,
            active_addresses_change_pct=self._active_addr,
            nvt_zscore=self._nvt,
            etf_flow_usd=self._etf,
        )
