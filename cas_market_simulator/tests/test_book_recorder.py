"""D8 — BookRecorder kayit/replay testleri."""
from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from cas_market_simulator.environment.orderbook import OrderBookEnvironment
from cas_market_simulator.environment.recorder import BookRecorder


def test_recorder_writes_and_replays():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "book.jsonl"
        recorder = BookRecorder(path)
        env = OrderBookEnvironment("BTC", 100.0)
        env.step()
        recorder.record(env)
        env.step()
        recorder.record(env)

        assert path.exists()
        snapshots = list(recorder.replay())
        assert len(snapshots) == 2
        assert snapshots[0].mid == pytest.approx(100.0, abs=0.1)
