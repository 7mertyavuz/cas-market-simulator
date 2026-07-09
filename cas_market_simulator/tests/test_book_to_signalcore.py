"""D6 — BookState -> signalcore OrderbookState entegrasyon testleri."""
from __future__ import annotations

from datetime import datetime, timezone

from cas_market_simulator.adapters.book_feed import (
    to_signalcore_orderbook_state,
    MicrostructureBookFeed,
)
from cas_market_simulator.adapters.contracts import BookState
from signalcore.indicators.orderbook import orderbook_factor


def test_book_state_to_signalcore_conversion():
    book = BookState(
        symbol="ETHUSDT",
        spread_bps=8.0,
        microprice=3_001.0,
        depth_imbalance=0.4,
        ofi=5.0,
        queue_imbalance=0.3,
        book_slope=2.0,
        kyle_lambda=1e-6,
        iceberg_score=0.3,
        spoof_score=0.1,
        absorption=0.4,
        liq_map_skew=-0.2,
        ts=datetime.now(timezone.utc),
    )
    ob = to_signalcore_orderbook_state(book)
    assert ob.spread_bps == 8.0
    assert ob.depth_imbalance == 0.4
    assert ob.liquidation_map_skew == -0.2
    assert ob.ofi == 5.0
    assert ob.spoof_score == 0.1
    assert ob.absorption == 0.4
    assert ob.iceberg_score == 0.3


def test_orderbook_factor_uses_book_state():
    book = BookState(
        symbol="ETHUSDT",
        spread_bps=5.0,
        microprice=3_000.0,
        depth_imbalance=0.6,
        ofi=2.0,
        queue_imbalance=0.5,
        book_slope=1.0,
        kyle_lambda=1e-6,
        iceberg_score=0.4,
        spoof_score=0.0,
        absorption=0.5,
        liq_map_skew=0.1,
        ts=datetime.now(timezone.utc),
    )
    ob = to_signalcore_orderbook_state(book)
    vote = orderbook_factor(ob)
    assert -1.0 <= vote.vote <= 1.0
    assert vote.name == "orderbook"


def test_spoof_reduces_orderbook_vote():
    base = BookState(
        symbol="ETHUSDT",
        spread_bps=5.0,
        microprice=3_000.0,
        depth_imbalance=0.6,
        ofi=0.0,
        queue_imbalance=0.5,
        book_slope=1.0,
        kyle_lambda=1e-6,
        iceberg_score=0.0,
        spoof_score=0.0,
        absorption=0.0,
        liq_map_skew=0.0,
        ts=datetime.now(timezone.utc),
    )
    clean = to_signalcore_orderbook_state(base)
    spoofed = to_signalcore_orderbook_state(
        BookState(**{**base.__dict__, "spoof_score": 0.9})
    )
    assert abs(orderbook_factor(clean).vote) > abs(orderbook_factor(spoofed).vote)


def test_microstructure_book_feed_to_signalcore():
    feed = MicrostructureBookFeed(mode="simulation", seed=5, base_price=3_000.0)
    book = feed.latest("ETHUSDT")
    ob = to_signalcore_orderbook_state(book)
    vote = orderbook_factor(ob)
    assert -1.0 <= vote.vote <= 1.0
