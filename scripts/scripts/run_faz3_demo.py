"""Faz 3 demo: Katman 1 (analist cekirdegi) uctan uca.

NoopAgent yerine fiyati hareket ettiren basit bir "random walk" ajani
kullanir (aksi halde fiyat sabit kalir, brain hep NEUTRAL doner) --
Faz 5'te bunun yerini gercek sim ajanlari (momentum/MM/panic) alacak.

Calistir:
    PYTHONPATH=. python3 scripts/run_faz3_demo.py
"""
from __future__ import annotations

import logging
import random
from typing import Optional

from cas_market_simulator.adapters.factor_brain import SignalCoreFactorBrain
from cas_market_simulator.adapters.flow_feed import SimFlowFeed
from cas_market_simulator.adapters.sentiment_feed import SimSentimentFeed
from cas_market_simulator.agents.base import Agent
from cas_market_simulator.analysis.execution import PaperExecutor
from cas_market_simulator.analysis.journal import Journal
from cas_market_simulator.engine.loop import Engine, SimulationConfig
from cas_market_simulator.environment.base import EnvironmentState, Order

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s")


class RandomWalkAgent(Agent):
    """Faz 5'e kadar yer tutucu: Environment'a fiyati hareket ettirecek
    rastgele emirler gonderir (aksi halde signalcore hep duz bir seri
    gorur ve hicbir faktor sinyal uretmez)."""

    def __init__(self, agent_id: str = "randomwalk-0", *, seed: int = 1, size: float = 3.0) -> None:
        super().__init__(agent_id)
        self._rng = random.Random(seed)
        self._size = size
        self._last_state: Optional[EnvironmentState] = None

    def observe(self, state: EnvironmentState) -> None:
        self._last_state = state

    def decide(self) -> Optional[Order]:
        if self._last_state is None:
            return None
        side = "buy" if self._rng.random() > 0.5 else "sell"
        return Order(agent_id=self.agent_id, symbol=self._last_state.symbol, side=side, size=self._size)


def main() -> None:
    config = SimulationConfig(symbol="SIM/USDT", n_ticks=200, start_price=100.0, log_every=50, min_bars_for_brain=35)
    journal = Journal(horizon_ticks=10)
    engine = Engine(
        config,
        agents=[RandomWalkAgent(seed=42)],
        sentiment_feed=SimSentimentFeed(seed=7),
        flow_feed=SimFlowFeed(seed=11),
        factor_brain=SignalCoreFactorBrain(min_bars=30),
        executor=PaperExecutor(slippage_bps=5.0, fee_bps=4.0),
        journal=journal,
    )
    results = engine.run()

    last = results[-1]
    print(f"\nSon kart: {last.card_direction} guven={last.card_confidence:.2f}")
    if last.card is not None:
        print(f"  oy sayisi: {len(last.card.votes)}  formasyon sayisi: {len(last.card.patterns)}")
        print(f"  risk: {last.card.risk}")

    print("\n--- forward-test defteri (Journal) ---")
    stats = journal.stats()
    print(f"  cozulen kayit: {stats['n']}  acik kayit: {stats['open']}")
    if stats["n"] > 0:
        print(f"  win_rate={stats['win_rate']:.2f}  avg_pnl_pct={stats['avg_pnl_pct']:+.4f}  total_pnl_pct={stats['total_pnl_pct']:+.4f}")
    else:
        print("  henuz cozulen kayit yok (ufuk dolmadi veya hic sinyal yoktu)")


if __name__ == "__main__":
    main()
