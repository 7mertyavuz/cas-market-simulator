"""D7 — Emir defteri çevresi testleri."""
from __future__ import annotations

import pytest

from cas_market_simulator.environment.orderbook import (
    OrderBook,
    OrderBookEnvironment,
    LimitOrder,
    MarketOrder,
)
from cas_market_simulator.environment.base import Order as BaseOrder


class TestOrderBook:
    def test_limit_orders_form_bid_ask(self):
        book = OrderBook("BTC")
        book.submit(LimitOrder("a", "BTC", "buy", 99.0, 1.0))
        book.submit(LimitOrder("b", "BTC", "sell", 101.0, 1.0))
        assert book.mid == pytest.approx(100.0)
        assert book.spread == pytest.approx(2.0)

    def test_market_buy_matches_best_ask(self):
        book = OrderBook("BTC")
        book.submit(LimitOrder("a", "BTC", "sell", 101.0, 1.0))
        fills = book.submit(MarketOrder("b", "BTC", "buy", 1.0))
        assert len(fills) == 1
        assert fills[0].price == pytest.approx(101.0)
        assert fills[0].size == pytest.approx(1.0)

    def test_aggressive_limit_matches_and_rest(self):
        book = OrderBook("BTC")
        book.submit(LimitOrder("a", "BTC", "sell", 101.0, 1.0))
        fills = book.submit(LimitOrder("b", "BTC", "buy", 102.0, 2.0))
        assert len(fills) == 1
        assert fills[0].price == pytest.approx(101.0)
        assert fills[0].size == pytest.approx(1.0)
        assert book.mid > 100.0


class TestOrderBookEnvironment:
    def test_initial_mid_near_start_price(self):
        env = OrderBookEnvironment("BTC", 100.0)
        assert env.state.price == pytest.approx(100.0, abs=0.1)

    def test_market_order_moves_price(self):
        env = OrderBookEnvironment("BTC", 100.0)
        env.submit(MarketOrder("whale", "BTC", "sell", 500.0))
        before = env.state.price
        env.step()
        after = env.state.price
        assert after < before

    def test_compatible_with_base_order(self):
        env = OrderBookEnvironment("BTC", 100.0)
        env.submit(BaseOrder("agent", "BTC", "sell", 100.0))
        env.step()
        assert env.state.tick == 1

    def test_liquidation_sweep_crashes_price(self):
        env = OrderBookEnvironment("BTC", 100.0)
        # Büyük satis emri defteri süpürür
        env.submit(MarketOrder("liq", "BTC", "sell", 2_000.0))
        env.step()
        assert env.state.price < 100.0
