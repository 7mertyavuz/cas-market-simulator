"""D8 — Journal tag'leme ve istatistik testleri."""
from __future__ import annotations

from datetime import datetime, timezone

from cas_market_simulator.analysis.journal import Journal
from cas_market_simulator.analysis.execution import PaperFill


def _fill(side: str = "buy") -> PaperFill:
    return PaperFill(symbol="BTC", side=side, requested_price=100.0,
                     fill_price=100.0, size_pct=0.1, cost_pct=0.001,
                     ts=datetime.now(timezone.utc))


def test_journal_records_tags():
    journal = Journal(horizon_ticks=2)
    entry = journal.record(_fill("buy"), tick=0, tags=["book", "flow"])
    assert "book" in entry.tags
    assert "flow" in entry.tags


def test_stats_by_tag():
    journal = Journal(horizon_ticks=1)
    journal.record(_fill("buy"), tick=0, tags=["book"])
    journal.record(_fill("buy"), tick=0, tags=["flow"])
    journal.record(_fill("sell"), tick=0, tags=["book"])

    # Fiyat yukselirse buy'lar kazanir
    journal.resolve_due(current_tick=2, current_price=110.0)

    by_tag = journal.stats_by_tag()
    assert "book" in by_tag
    assert "flow" in by_tag
    assert by_tag["book"]["n"] == 2
    assert by_tag["flow"]["n"] == 1
