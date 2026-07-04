"""signalcore Faz 1 demo: sentetik OHLCV -> brain.analyze() -> Card,
+ her faktor icin walk-forward IC/hit-rate raporu (factor_tracker'a kayit).

Calistir:
    PYTHONPATH=. python3 scripts/run_signalcore_brain_demo.py
"""
from __future__ import annotations

from signalcore.brain import analyze
from signalcore.combine.registry_setup import register_defaults
from signalcore.core.registry import default_registry
from signalcore.feeds import synthetic_ohlcv
from signalcore.indicators.cross_exchange import SimCrossExchangeFeed
from signalcore.indicators.derivatives import SimDerivativesFeed
from signalcore.indicators.intermarket import SimIntermarketFeed
from signalcore.indicators.onchain import SimOnchainFeed
from signalcore.indicators.orderbook import SimOrderbookFeed
from signalcore.indicators.sensors import compute_sensor_votes
from signalcore.validation.factor_tracker import FactorTracker
from signalcore.validation.leakage import assert_no_lookahead
from signalcore.validation.walkforward import walk_forward_eval


def main() -> None:
    bars = synthetic_ohlcv(600, symbol="SIM/USDT", seed=7)

    sensor_feeds = {
        "derivatives": SimDerivativesFeed(seed=1),
        "orderbook": SimOrderbookFeed(seed=2),
        "onchain": SimOnchainFeed(seed=3),
        "intermarket": SimIntermarketFeed(seed=4),
        "cross_exchange": SimCrossExchangeFeed(seed=5),
    }
    sensor_states = {name: feed.latest("SIM") for name, feed in sensor_feeds.items()}

    card = analyze("SIM/USDT", bars, sensor_states=sensor_states)
    print(f"Card: {card.symbol} {card.direction} guven={card.confidence:.2f}")
    for v in card.votes:
        print(f"  faktor={v.name:<12} oy={v.vote:+.2f} agirlik={v.weight:.2f}")
    print(f"  risk: {card.risk}")
    print(f"  formasyonlar ({len(card.patterns)}):")
    for p in card.patterns:
        print(f"    {p.name:<24} yon={p.direction:<8} guc={p.strength:.2f} gecersizlik={p.invalidation}")

    print("\n--- validation (Faz 1b): cekirdek OHLCV faktorleri ---")
    reg = register_defaults(default_registry)
    tracker = FactorTracker(min_samples=20)

    for spec in reg.all():
        leak = assert_no_lookahead(spec.fn, bars, min_window=60, check_every=30)
        wf = walk_forward_eval(spec.fn, bars, min_window=60, forward_horizon=5, step=3)
        for s in wf.samples:
            tracker.record(spec.name, s.vote, s.forward_return)
        allow = tracker.allows_weight_increase(spec.name)
        print(
            f"  {spec.name:<12} leakage_ok={leak.ok!s:<5} "
            f"IC={wf.ic:+.3f} hit_rate={wf.hit_rate:.2f} n={wf.n:<4} "
            f"agirlik_artisina_izin={allow}"
        )

    print("\n--- Faz 4: sensor faktorleri (dusuk agirlik, factor_tracker olcer) ---")
    for name, feed in sensor_feeds.items():
        feed.__init__(seed={"derivatives": 1, "orderbook": 2, "onchain": 3, "intermarket": 4, "cross_exchange": 5}[name])

    horizon = 5
    for i in range(60, len(bars) - horizon, 3):
        states = {name: feed.latest("SIM") for name, feed in sensor_feeds.items()}
        votes = compute_sensor_votes(states)
        price_now, price_future = bars[i].close, bars[i + horizon].close
        forward_return = (price_future - price_now) / price_now if price_now else 0.0
        for v in votes:
            tracker.record(v.name, v.vote, forward_return)

    for name in sensor_feeds:
        stats = tracker.stats(name)
        allow = tracker.allows_weight_increase(name)
        print(
            f"  {name:<14} IC={stats['ic']:+.3f} hit_rate={stats['hit_rate']:.2f} "
            f"n={stats['n']:<4} agirlik_artisina_izin={allow}"
        )


if __name__ == "__main__":
    main()
