import pytest

from signalcore.core.registry import FactorRegistry
from signalcore.core.types import FactorVote


def dummy_factor(ohlcv=None, **kwargs) -> FactorVote:
    return FactorVote(name="dummy", vote=0.5, weight=1.0)


def test_register_and_get():
    reg = FactorRegistry()
    reg.register("dummy", dummy_factor, initial_weight=0.8, axis="trend")
    assert "dummy" in reg
    spec = reg.get("dummy")
    assert spec.initial_weight == 0.8
    assert spec.axis == "trend"


def test_register_duplicate_raises():
    reg = FactorRegistry()
    reg.register("dummy", dummy_factor)
    with pytest.raises(ValueError):
        reg.register("dummy", dummy_factor)


def test_all_respects_enabled_only():
    reg = FactorRegistry()
    reg.register("a", dummy_factor, enabled=True)
    reg.register("b", dummy_factor, enabled=False)
    assert [s.name for s in reg.all(enabled_only=True)] == ["a"]
    assert {s.name for s in reg.all(enabled_only=False)} == {"a", "b"}


def test_set_weight():
    reg = FactorRegistry()
    reg.register("a", dummy_factor, initial_weight=1.0)
    reg.set_weight("a", 0.3)
    assert reg.get("a").initial_weight == 0.3
