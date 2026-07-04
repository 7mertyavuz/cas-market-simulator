from datetime import datetime, timezone

from cas_market_simulator.adapters.bars import ohlcv_from_history
from cas_market_simulator.environment.base import EnvironmentState


def state(price, tick):
    return EnvironmentState(symbol="SIM/USDT", price=price, tick=tick, ts=datetime.now(timezone.utc))


def test_ohlcv_from_history_needs_at_least_two_points():
    assert ohlcv_from_history([state(100, 0)]) == []


def test_ohlcv_from_history_basic_shape():
    hist = [state(100, 0), state(102, 1), state(101, 2)]
    bars = ohlcv_from_history(hist)
    assert len(bars) == 2
    assert bars[0].open == 100
    assert bars[0].close == 102
    assert bars[0].high == 102
    assert bars[0].low == 100
    assert bars[1].open == 102
    assert bars[1].close == 101


def test_ohlcv_from_history_volume_default():
    hist = [state(100, 0), state(101, 1)]
    bars = ohlcv_from_history(hist, default_volume=5.0)
    assert bars[0].volume == 5.0
