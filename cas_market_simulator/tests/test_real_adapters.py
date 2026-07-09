"""Gercek repo adaptörlerinin entegrasyon testleri.

Bu testler, ayni workspace icinde microstructure-analyzer ve
macro-sentiment-agent repolarinin kurulu oldugunu varsayar
(`pip install -e ...`). Kurulu degilse ImportError ile kolleksiyon
hatasi verir -- bu kasıtlidir; cas-market-simulator cekirdek testleri
(test_stub_feeds.py vb.) hala bagimsiz calisir.
"""
from __future__ import annotations

from datetime import datetime, timezone, timedelta

import pytest

from cas_market_simulator.adapters import (
    MicrostructureFlowFeed,
    MicrostructureBookFeed,
    MacroSentimentFeed,
    FlowState,
    BookState,
    SentimentState,
    ShockEvent,
)


class TestMicrostructureFlowFeed:
    def test_latest_returns_flow_state(self):
        feed = MicrostructureFlowFeed(mode="simulation", seed=42)
        state = feed.latest("UniswapV2")
        assert isinstance(state, FlowState)
        assert state.token == "UniswapV2"
        assert -1.0 <= state.flow_imbalance <= 1.0
        assert 0.0 <= state.vpin_toxicity <= 1.0
        assert 0.0 <= state.direction_prob_up <= 1.0
        assert state.regime in ("normal", "toxic", "highvol")
        assert set(state.actor_mix.keys()).issubset({"WHALE", "MEV_BOT", "RETAIL"})
        assert abs(sum(state.actor_mix.values()) - 1.0) < 1e-6

    def test_determinism_with_same_seed(self):
        f1 = MicrostructureFlowFeed(mode="simulation", seed=7)
        f2 = MicrostructureFlowFeed(mode="simulation", seed=7)
        for _ in range(5):
            s1, s2 = f1.latest("UniswapV2"), f2.latest("UniswapV2")
            # ts zaman damgasi oldugu icin determinizm disinda tutulur
            assert s1.token == s2.token
            assert s1.flow_imbalance == s2.flow_imbalance
            assert s1.vpin_toxicity == s2.vpin_toxicity
            assert s1.direction_prob_up == s2.direction_prob_up
            assert s1.regime == s2.regime
            assert s1.actor_mix == s2.actor_mix


class TestMicrostructureBookFeed:
    def test_latest_returns_book_state(self):
        feed = MicrostructureBookFeed(mode="simulation", seed=42, base_price=30_000.0)
        state = feed.latest("BTCUSDT")
        assert isinstance(state, BookState)
        assert state.symbol == "BTCUSDT"
        assert state.spread_bps >= 0.0
        assert state.microprice > 0.0
        assert -1.0 <= state.depth_imbalance <= 1.0
        assert -1.0 <= state.queue_imbalance <= 1.0
        assert state.book_slope >= 0.0
        assert state.kyle_lambda >= 0.0
        assert 0.0 <= state.iceberg_score <= 1.0
        assert 0.0 <= state.spoof_score <= 1.0
        assert -1.0 <= state.absorption <= 1.0
        assert -1.0 <= state.liq_map_skew <= 1.0

    def test_determinism_with_same_seed(self):
        f1 = MicrostructureBookFeed(mode="simulation", seed=11, base_price=30_000.0)
        f2 = MicrostructureBookFeed(mode="simulation", seed=11, base_price=30_000.0)
        for _ in range(5):
            s1, s2 = f1.latest("BTCUSDT"), f2.latest("BTCUSDT")
            assert s1.symbol == s2.symbol
            assert s1.spread_bps == s2.spread_bps
            assert s1.depth_imbalance == s2.depth_imbalance
            assert s1.iceberg_score == s2.iceberg_score
            assert s1.spoof_score == s2.spoof_score
            assert s1.liq_map_skew == s2.liq_map_skew


class TestMacroSentimentFeed:
    def test_latest_returns_sentiment_state(self):
        feed = MacroSentimentFeed(mode="offline")
        state = feed.latest("BTC")
        assert isinstance(state, SentimentState)
        assert state.entity == "BTC"
        assert -1.0 <= state.polarity <= 1.0
        assert 0.0 <= state.intensity <= 100.0
        assert 0.0 <= state.confidence <= 1.0

    def test_shocks_returns_list_of_shock_events(self):
        feed = MacroSentimentFeed(mode="offline")
        since = datetime.now(timezone.utc) - timedelta(hours=1)
        shocks = feed.shocks(since)
        assert isinstance(shocks, list)
        for shock in shocks:
            assert isinstance(shock, ShockEvent)
            assert shock.kind in ("panic", "euphoria", "fed_tone", "narrative_shift")
            assert 0.0 <= shock.magnitude <= 1.0
            assert shock.decay_halflife_s > 0.0
