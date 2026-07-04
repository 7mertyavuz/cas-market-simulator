"""Faz 7 demo: geri besleme -- iki katman kapali dongude.

Faz 6'nin scriptli-panik senaryosu tekrarlanir, ama artik gercek
SignalCoreFactorBrain baglidir. Amac: kaskad olustukca, simulasyonun
KENDI URETTIGI crowd_emergence_score'un, signalcore kartina
"crowd_emergence" adinda dusuk-agirlikli bir faktor olarak girdigini
VE kaskad sirasinda negatife donduğünü gostermek -- "kalabalik cokmeye
mi gidiyor?" okumasi artik karttaki bir faktor.

Calistir:
    PYTHONPATH=. python3 scripts/run_faz7_demo.py
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from cas_market_simulator.adapters.contracts import ShockEvent
from cas_market_simulator.adapters.factor_brain import SignalCoreFactorBrain
from cas_market_simulator.agents.arbitrage import ArbitrageAgent
from cas_market_simulator.agents.contrarian import ContrarianAgent
from cas_market_simulator.agents.liquidation_engine import LiquidationEngineAgent
from cas_market_simulator.agents.market_maker import MarketMakerAgent
from cas_market_simulator.agents.mev import MevAgent
from cas_market_simulator.agents.momentum import MomentumAgent
from cas_market_simulator.agents.news_reactor import NewsReactorAgent
from cas_market_simulator.agents.panic import PanicAgent
from cas_market_simulator.agents.whale import WhaleAgent
from cas_market_simulator.engine.loop import Engine, SimulationConfig

logging.basicConfig(level=logging.WARNING, format="%(asctime)s %(name)s %(message)s")

SHOCK_TICK = 100


def main() -> None:
    agents = [
        MomentumAgent("momentum-1", lookback=5, threshold_pct=0.004, size=1.0),
        MarketMakerAgent("mm-1", vol_lookback=8, vol_pull_threshold_pct=0.015, quote_size=0.5),
        PanicAgent("panic-1", drawdown_threshold_pct=0.015, confirmation_ticks=2, size=2.0),
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
        symbol="SIM/USDT", n_ticks=200, start_price=100.0, log_every=200,
        shock_impact_scale=30.0, seconds_per_tick=30.0,
        min_bars_for_brain=30, crowd_emergence_min_ticks=20, crowd_emergence_window=60,
    )
    engine = Engine(
        config, agents=agents, factor_brain=SignalCoreFactorBrain(min_bars=30),
        scripted_shocks={SHOCK_TICK: scripted_panic},
    )
    results = engine.run()

    print(f"{'tick':>5} {'fiyat':>9} {'yon':>8} {'guven':>6} {'crowd_score':>12} {'crowd_oy(karti)':>16}")
    for r in results:
        if r.tick % 10 != 0 and not (SHOCK_TICK - 5 <= r.tick <= SHOCK_TICK + 30):
            continue
        crowd_vote = None
        if r.card is not None:
            crowd_vote = next((v.vote for v in r.card.votes if v.name == "crowd_emergence"), None)
        crowd_vote_str = f"{crowd_vote:+.2f}" if crowd_vote is not None else "  -  "
        print(f"{r.tick:>5} {r.state.price:>9.2f} {r.card_direction:>8} {r.card_confidence:>6.2f} "
              f"{r.crowd_emergence_score:>+12.2f} {crowd_vote_str:>16}")

    min_score_tick = min(results, key=lambda r: r.crowd_emergence_score)
    print(f"\nEn negatif crowd_emergence_score: {min_score_tick.crowd_emergence_score:+.2f} @ tick={min_score_tick.tick}")
    print(
        "\nNot: crowd_emergence_score, simulasyonun SON 60 tick'inden hesaplanan bir "
        "kaskad+senkronizasyon olcumu; bu skor dogrudan signalcore'a extra_factors olarak "
        "geri besleniyor ve kartta 'crowd_emergence' adinda, dusuk agirlikli (0.15) bir "
        "faktor olarak goruluyor -- iki katman (analist cekirdegi + CAS simulasyonu) artik "
        "kapali bir dongu (bkz. FAZ-PLANI.md Faz 7 'Bitti' kriteri)."
    )


if __name__ == "__main__":
    main()
