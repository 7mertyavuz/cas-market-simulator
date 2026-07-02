from cas_market_simulator.adapters.contracts import Card
from cas_market_simulator.analysis.execution import PaperExecutor


def test_execute_returns_none_for_neutral():
    executor = PaperExecutor()
    card = Card(symbol="SIM/USDT", direction="NEUTRAL", confidence=0.0, risk={"size_pct": 0.0})
    assert executor.execute(card, 100.0) is None


def test_execute_returns_none_for_zero_size():
    executor = PaperExecutor()
    card = Card(symbol="SIM/USDT", direction="LONG", confidence=0.5, risk={"size_pct": 0.0})
    assert executor.execute(card, 100.0) is None


def test_execute_long_slippage_worse_than_requested():
    executor = PaperExecutor(slippage_bps=10.0, fee_bps=5.0)
    card = Card(symbol="SIM/USDT", direction="LONG", confidence=0.6, risk={"size_pct": 0.05})
    fill = executor.execute(card, 100.0)
    assert fill is not None
    assert fill.side == "buy"
    assert fill.fill_price > fill.requested_price  # alista slipaj aleyhte


def test_execute_short_slippage_worse_than_requested():
    executor = PaperExecutor(slippage_bps=10.0, fee_bps=5.0)
    card = Card(symbol="SIM/USDT", direction="SHORT", confidence=0.6, risk={"size_pct": 0.05})
    fill = executor.execute(card, 100.0)
    assert fill is not None
    assert fill.side == "sell"
    assert fill.fill_price < fill.requested_price  # satista slipaj aleyhte


def test_execute_cost_pct_is_slippage_plus_fee():
    executor = PaperExecutor(slippage_bps=10.0, fee_bps=5.0)
    card = Card(symbol="SIM/USDT", direction="LONG", confidence=0.6, risk={"size_pct": 0.05})
    fill = executor.execute(card, 100.0)
    assert abs(fill.cost_pct - 0.0015) < 1e-9
