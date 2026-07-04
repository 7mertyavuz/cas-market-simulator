"""Faz 8 demo: adaptasyon / evrim.

Faz 6/7'nin scriptli-panik senaryosu tekrar kullanilir, ama artik
popülasyonda meta ajanlar var:
  - 10x RegimeSwitcherAgent -- rejim degisince (sok sonrasi guclu
    tek-yonlu hareket = 'trend') ne kadari mod degistiriyor, ORAN
    olarak izlenir ("populasyon kompozisyonu kayiyor mu?").
  - 2x AdaptiveAgent -- zarar ettikce parametre mutasyonu (evrim).
  - 1x HerdAgent -- en karli ajani (pozisyon yonunu) taklit eder.

Calistir:
    PYTHONPATH=. python3 scripts/run_faz8_demo.py
"""
from __future__ import annotations

import logging
import statistics
from datetime import datetime, timezone

from cas_market_simulator.adapters.contracts import ShockEvent
from cas_market_simulator.agents.adaptive import AdaptiveAgent
from cas_market_simulator.agents.herd import HerdAgent
from cas_market_simulator.agents.liquidation_engine import LiquidationEngineAgent
from cas_market_simulator.agents.momentum import MomentumAgent
from cas_market_simulator.agents.panic import PanicAgent
from cas_market_simulator.agents.regime_switcher import RegimeSwitcherAgent
from cas_market_simulator.engine.loop import Engine, SimulationConfig

logging.basicConfig(level=logging.WARNING, format="%(asctime)s %(name)s %(message)s")

SHOCK_TICK = 100
N_SWITCHERS = 10


def main() -> None:
    switchers = [
        RegimeSwitcherAgent(f"switcher-{i}", lookback=12 + i, efficiency_threshold=0.35, size=0.5)
        for i in range(N_SWITCHERS)
    ]
    adaptives = [
        AdaptiveAgent(f"adaptive-{i}", seed=70 + i, evaluation_interval=15, threshold_pct=0.004, size=1.0)
        for i in range(2)
    ]
    core = [
        MomentumAgent("momentum-1", lookback=5, threshold_pct=0.004, size=1.0),
        PanicAgent("panic-1", drawdown_threshold_pct=0.015, confirmation_ticks=2, size=2.0),
        LiquidationEngineAgent("liquidation-0", open_probability=0.2, seed=7),
    ]
    herd = HerdAgent("herd-0", size=0.8)
    herd.set_peers(switchers + adaptives + core)

    agents = switchers + adaptives + core + [herd]

    scripted_panic = ShockEvent(
        kind="panic", entity="market", magnitude=1.0, decay_halflife_s=180.0,
        ts=datetime.now(timezone.utc),
    )
    config = SimulationConfig(
        symbol="SIM/USDT", n_ticks=220, start_price=100.0, log_every=220,
        shock_impact_scale=30.0, seconds_per_tick=30.0,
    )
    engine = Engine(config, agents=agents, scripted_shocks={SHOCK_TICK: scripted_panic})

    # Not: RegimeSwitcherAgent.current_mode her tick'te YENIDEN yaziliyor
    # (kalici bir gecmis tutmuyor) -- kompozisyonu tick-tick izlemek icin
    # Engine._tick()'i (private ama demo amacli meşru bir kullanim) elle
    # cagiriyoruz, engine.run()'un tek-seferlik dongusu yerine.
    trend_fraction_by_tick: list[float] = []
    results = []
    for i in range(config.n_ticks):
        result = engine._tick()
        engine.results.append(result)
        results.append(result)
        trend_count = sum(1 for s in switchers if s.current_mode == "trend")
        trend_fraction_by_tick.append(trend_count / len(switchers))

    def avg_fraction(a: int, b: int) -> float:
        window = trend_fraction_by_tick[a:b]
        return statistics.mean(window) if window else 0.0

    print("--- RegimeSwitcherAgent populasyon kompozisyonu ('trend' modda olan oran) ---")
    print(f"  sok oncesi   (tick   0-{SHOCK_TICK - 10}):  {avg_fraction(0, SHOCK_TICK - 10):.2f}")
    print(f"  sok sirasi   (tick {SHOCK_TICK}-{SHOCK_TICK + 20}): {avg_fraction(SHOCK_TICK, SHOCK_TICK + 20):.2f}")
    print(f"  sok sonrasi  (tick {SHOCK_TICK + 60}-{SHOCK_TICK + 100}): {avg_fraction(SHOCK_TICK + 60, SHOCK_TICK + 100):.2f}")

    print("\n--- AdaptiveAgent evrimi ---")
    for a in adaptives:
        first_t, first_s = a.param_history[0]
        print(
            f"  {a.agent_id:<12} mutasyon_sayisi={a.mutation_count:<3} "
            f"baslangic(th={first_t:.4f}, size={first_s:.2f}) -> "
            f"son(th={a.threshold_pct:.4f}, size={a.size:.2f})"
        )

    print("\n--- HerdAgent taklit istatistikleri ---")
    print(f"  toplam taklit sayisi: {herd.imitation_count}")
    print(f"  son taklit edilen ajan: {herd.last_imitated_agent_id}")

    prices = [r.state.price for r in results]
    print(f"\nFiyat: baslangic={prices[0]:.2f}  bitis={prices[-1]:.2f}  min={min(prices):.2f}  max={max(prices):.2f}")

    print(
        "\nNot: RegimeSwitcherAgent'lar farkli lookback pencereleri kullandigi icin ayni"
        " anda hepsi ayni moda gecmiyor (gercekci bir populasyon cesitliligi) -- ama sok"
        " sonrasi guclu tek-yonlu harekette 'trend' modundaki oranin artmasi beklenir."
        " AdaptiveAgent'lar zarar ettikce parametrelerini degistiriyor; HerdAgent en karli"
        " ajanin pozisyon yonunu takip ederek surme davranisini modelliyor."
    )


if __name__ == "__main__":
    main()
