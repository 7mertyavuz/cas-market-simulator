from cas_market_simulator.analysis.execution import PaperFill
from cas_market_simulator.analysis.journal import Journal
from datetime import datetime, timezone


def fill(side="buy", price=100.0, size=0.05, cost=0.001):
    return PaperFill(
        symbol="SIM/USDT", side=side, requested_price=price, fill_price=price,
        size_pct=size, cost_pct=cost, ts=datetime.now(timezone.utc),
    )


def test_record_creates_open_entry():
    j = Journal(horizon_ticks=5)
    j.record(fill(), tick=0)
    assert len(j.entries) == 1
    assert not j.entries[0].resolved


def test_resolve_due_before_horizon_does_nothing():
    j = Journal(horizon_ticks=5)
    j.record(fill(price=100.0), tick=0)
    resolved = j.resolve_due(current_tick=3, current_price=110.0)
    assert resolved == []
    assert not j.entries[0].resolved


def test_resolve_due_long_profitable():
    j = Journal(horizon_ticks=5)
    j.record(fill(side="buy", price=100.0, cost=0.001), tick=0)
    resolved = j.resolve_due(current_tick=5, current_price=110.0)
    assert len(resolved) == 1
    e = resolved[0]
    assert e.resolved
    assert e.pnl_pct == pytest_approx(0.10 - 0.001)


def pytest_approx(x, tol=1e-9):
    class _Approx(float):
        def __eq__(self, other):
            return abs(other - x) < tol
    return _Approx(x)


def test_resolve_due_short_profitable_on_price_drop():
    j = Journal(horizon_ticks=5)
    j.record(fill(side="sell", price=100.0, cost=0.001), tick=0)
    resolved = j.resolve_due(current_tick=5, current_price=90.0)
    e = resolved[0]
    assert e.pnl_pct > 0  # fiyat dustu, short kazandi


def test_stats_empty_journal():
    j = Journal()
    s = j.stats()
    assert s["n"] == 0
    assert s["open"] == 0


def test_stats_with_mixed_outcomes():
    j = Journal(horizon_ticks=1)
    j.record(fill(side="buy", price=100.0), tick=0)
    j.record(fill(side="buy", price=100.0), tick=0)
    j.resolve_due(current_tick=1, current_price=110.0)  # kazanan
    j2_price = 90.0
    # ikinci kaydi ayri tick'te kapatalim ki iki farkli sonuc gorelim
    j.entries[1].entry_tick = 0
    j.resolve_due(current_tick=1, current_price=90.0)
    stats = j.stats()
    assert stats["n"] == 2
    assert stats["open"] == 0


def test_stats_tracks_open_entries():
    j = Journal(horizon_ticks=10)
    j.record(fill(), tick=0)
    stats = j.stats()
    assert stats["open"] == 1
    assert stats["n"] == 0


def test_forward_return_samples_shape():
    j = Journal(horizon_ticks=1)
    j.record(fill(side="buy", price=100.0), tick=0)
    j.resolve_due(current_tick=1, current_price=105.0)
    samples = j.forward_return_samples()
    assert len(samples) == 1
    sign, ret = samples[0]
    assert sign == 1.0
    assert ret > 0
