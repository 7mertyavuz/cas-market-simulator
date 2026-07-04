"""Faz 6 demo: zenginlestirilmis emergence + likidasyon kaskadi.

Zengin bir ajan populasyonu (momentum, market-maker, panik, likidasyon
motoru, balina, arbitraj, MEV, haber-tepkicisi, kontra) + tick 100'de
scriptli bir panik soku enjekte edilir. Beklenen: sok, panik ajanlarini
ve likidasyon motorunu tetikler -> olculebilir bir asagi-yonlu kaskad
(bkz. FAZ-PLANI.md Faz 6 'Bitti' kriteri).

Calistir:
    PYTHONPATH=. python3 scripts/run_faz6_demo.py
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from cas_market_simulator.adapters.contracts import ShockEvent
from cas_market_simulator.agents.arbitrage import ArbitrageAgent
from cas_market_simulator.agents.contrarian import ContrarianAgent
from cas_market_simulator.agents.liquidation_engine import LiquidationEngineAgent
from cas_market_simulator.agents.market_maker import MarketMakerAgent
from cas_market_simulator.agents.mev import MevAgent
from cas_market_simulator.agents.momentum import MomentumAgent
from cas_market_simulator.agents.news_reactor import NewsReactorAgent
from cas_market_simulator.agents.panic import PanicAgent
from cas_market_simulator.agents.whale import WhaleAgent
from cas_market_simulator.analysis.emergence import compute_emergence_from_engine
from cas_market_simulator.engine.loop import Engine, SimulationConfig

logging.basicConfig(level=logging.WARNING, format="%(asctime)s %(name)s %(message)s")

SHOCK_TICK = 100


def main() -> None:
    agents = [
        MomentumAgent("momentum-1", lookback=5, threshold_pct=0.004, size=1.0),
        MarketMakerAgent("mm-1", vol_lookback=8, vol_pull_threshold_pct=0.015, quote_size=0.5),
        MarketMakerAgent("mm-2", vol_lookback=15, vol_pull_threshold_pct=0.02, quote_size=0.8),
        PanicAgent("panic-1", drawdown_threshold_pct=0.015, confirmation_ticks=2, size=2.0),
        PanicAgent("panic-2", drawdown_threshold_pct=0.025, confirmation_ticks=2, size=1.5),
        LiquidationEngineAgent("liquidation-0", open_probability=0.2, seed=7),
        WhaleAgent("whale-0", seed=8, trade_probability=0.02),
        ArbitrageAgent("arb-0", seed=9, deviation_threshold_pct=0.008),
        MevAgent("mev-0"),
        ContrarianAgent("contrarian-0", lookback=15, extension_threshold_pct=0.03),
        NewsReactorAgent("news-0", base_size=4.0, react_threshold=0.05),
    ]

    scripted_panic = ShockEvent(
        kind="panic", entity="market", magnitude=1.0, decay_halflife_s=180.0,
        ts=datetime.now(timezone.utc),
    )

    config = SimulationConfig(
        symbol="SIM/USDT", n_ticks=250, start_price=100.0, log_every=250,
        shock_impact_scale=30.0, seconds_per_tick=30.0,
    )
    engine = Engine(config, agents=agents, scripted_shocks={SHOCK_TICK: scripted_panic})
    results = engine.run()

    prices = [r.state.price for r in results]
    pre_shock = prices[SHOCK_TICK - 1]
    post_shock_min = min(prices[SHOCK_TICK:SHOCK_TICK + 20])
    crash_pct = (post_shock_min - pre_shock) / pre_shock

    print(f"Sok oncesi fiyat (tick {SHOCK_TICK - 1}): {pre_shock:.2f}")
    print(f"Sok sonrasi 20 tick icindeki en dusuk fiyat: {post_shock_min:.2f}  ({crash_pct:+.2%})")

    liq_agent = next(a for a in agents if isinstance(a, LiquidationEngineAgent))
    print(f"Likidasyon motoru: {liq_agent.liquidation_events} pozisyon likide edildi, "
          f"toplam notional={liq_agent.total_liquidated_notional:,.0f}")

    report = compute_emergence_from_engine(results, cascade_window=10, flash_crash_threshold_pct=0.01)
    print("\n--- emergence metrikleri (tum simulasyon) ---")
    print(f"  kaskad_buyuklugu (en kotu {report.cascade_window}-tick hareket): {report.cascade_size_pct:+.2%}")
    print(f"  ajan_senkronizasyonu: {report.agent_synchronization:.2f}  (1.0 = hep ayni yonde)")
    print(f"  getiri_otokorelasyonu (lag-1): {report.return_autocorrelation:+.3f}")
    print(f"  ani_cokus_frekansi (|getiri|>=1%): {report.flash_crash_frequency:.2%}")
    print(f"  tek_tick_en_kotu / en_iyi: {report.min_single_tick_return_pct:+.2%} / {report.max_single_tick_return_pct:+.2%}")

    print(
        "\nNot: sok, hem Environment'a dogrudan (extra_impact) hem de NewsReactorAgent'a"
        " enjekte edildi; panik/likidasyon ajanlarinin tetiklenmesiyle kaskad zenginlesti."
        " Bu kalibre edilmemis bir ortam -- kaskadin BUYUKLUGU degil, VAR OLUP OLMADIGI ve"
        " OLCULEBILIR olmasi Faz 6'nin hedefi (bkz. FAZ-PLANI.md kural #5)."
    )


if __name__ == "__main__":
    main()
