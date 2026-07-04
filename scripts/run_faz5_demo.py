"""Faz 5 demo: minimum CAS motoru -- ilk emergence gozlemi.

3 basit ajan (momentum, market_maker, panic) ayni Environment'ta
etkilesime girer; senkron tick dongusu fiyat serisi + ajan PnL
dagilimi uretir (bkz. FAZ-PLANI.md Faz 5 'Bitti' kriteri).

Calistir:
    PYTHONPATH=. python3 scripts/run_faz5_demo.py
"""
from __future__ import annotations

import logging
import statistics

from cas_market_simulator.agents.market_maker import MarketMakerAgent
from cas_market_simulator.agents.momentum import MomentumAgent
from cas_market_simulator.agents.panic import PanicAgent
from cas_market_simulator.engine.loop import Engine, SimulationConfig

logging.basicConfig(level=logging.WARNING, format="%(asctime)s %(name)s %(message)s")


def main() -> None:
    agents = [
        MomentumAgent("momentum-1", lookback=5, threshold_pct=0.003, size=1.0),
        MomentumAgent("momentum-2", lookback=10, threshold_pct=0.005, size=1.5),
        MarketMakerAgent("mm-1", vol_lookback=8, vol_pull_threshold_pct=0.015, quote_size=0.5),
        MarketMakerAgent("mm-2", vol_lookback=15, vol_pull_threshold_pct=0.02, quote_size=0.8),
        PanicAgent("panic-1", drawdown_threshold_pct=0.02, confirmation_ticks=3, size=2.0),
        PanicAgent("panic-2", drawdown_threshold_pct=0.03, confirmation_ticks=2, size=1.5),
    ]

    config = SimulationConfig(symbol="SIM/USDT", n_ticks=400, start_price=100.0, log_every=400)
    engine = Engine(config, agents=agents)
    results = engine.run()

    prices = [r.state.price for r in results]
    print(f"Fiyat serisi: baslangic={prices[0]:.2f}  bitis={prices[-1]:.2f}  "
          f"min={min(prices):.2f}  max={max(prices):.2f}")

    returns = [(prices[i] - prices[i - 1]) / prices[i - 1] for i in range(1, len(prices))]
    print(f"Getiri istatistikleri: std={statistics.pstdev(returns):.5f}  "
          f"max_tek_tick_dusus={min(returns):+.4f}  max_tek_tick_yukselis={max(returns):+.4f}")

    final_pnls = results[-1].agent_pnls
    print("\nAjan PnL dagilimi (son tick, mark-to-market):")
    for agent_id, pnl in sorted(final_pnls.items(), key=lambda kv: kv[1], reverse=True):
        print(f"  {agent_id:<12} pnl={pnl:+.2f}")

    pnl_values = list(final_pnls.values())
    print(f"\nPnL dagilim ozeti: ortalama={statistics.mean(pnl_values):+.2f}  "
          f"std={statistics.pstdev(pnl_values):.2f}  "
          f"en_iyi={max(pnl_values):+.2f}  en_kotu={min(pnl_values):+.2f}")

    print(
        "\nNot: 'Environment' henuz gercek bir emir defteri degil (bkz. README) --"
        " burada gozlenen davranis kolektif etkilesimin ISKELETI, kalibre edilmis"
        " gercekci bir piyasa degil (bkz. FAZ-PLANI.md kural #5)."
    )


if __name__ == "__main__":
    main()
