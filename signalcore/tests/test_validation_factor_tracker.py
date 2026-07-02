from signalcore.validation.factor_tracker import FactorTracker


def test_tracker_insufficient_samples_blocks_increase():
    tracker = FactorTracker(min_samples=30)
    tracker.record("trend", 0.5, 0.01)
    assert not tracker.allows_weight_increase("trend")


def test_tracker_positive_ic_allows_increase():
    tracker = FactorTracker(min_samples=10, min_ic=0.0)
    for i in range(20):
        v = 0.5 if i % 2 == 0 else -0.5
        r = 0.01 if i % 2 == 0 else -0.01
        tracker.record("trend", v, r)
    assert tracker.allows_weight_increase("trend")
    stats = tracker.stats("trend")
    assert stats["ic"] > 0.9


def test_tracker_negative_ic_blocks_increase():
    tracker = FactorTracker(min_samples=10, min_ic=0.0)
    for i in range(20):
        v = 0.5 if i % 2 == 0 else -0.5
        r = -0.01 if i % 2 == 0 else 0.01  # ters yonlu
        tracker.record("trend", v, r)
    assert not tracker.allows_weight_increase("trend")


def test_suggest_weight_reduces_on_negative_ic():
    tracker = FactorTracker(min_samples=10, min_ic=0.0)
    for i in range(20):
        v = 0.5 if i % 2 == 0 else -0.5
        r = -0.01 if i % 2 == 0 else 0.01
        tracker.record("trend", v, r)
    new_w = tracker.suggest_weight("trend", 1.0)
    assert new_w < 1.0


def test_suggest_weight_unchanged_without_enough_data():
    tracker = FactorTracker(min_samples=30)
    tracker.record("trend", 0.5, 0.01)
    assert tracker.suggest_weight("trend", 1.0) == 1.0
