"""Sensor faktorlerini (Faz 4) tek bir yerden birlestirir.

Bu bes sensor (derivatives/orderbook/onchain/intermarket/cross_exchange)
OHLCV degil, kendi alan-ozel durum tiplerini (State) girdi alir --
core 6 faktorden (trend/momentum/...) farkli olarak core.registry
uzerinden DEGIL, `sensor_states` sozlugu araciligiyla brain.analyze()'e
girer (bkz. brain.py). Hepsi DUSUK agirlikla (SENSOR_DEFAULT_WEIGHT)
oy verir -- cift sayim riski, gercek katki factor_tracker ile olculur
(bkz. FAZ-PLANI.md Faz 4 kurali).
"""
from __future__ import annotations

from ..core.types import FactorVote
from .cross_exchange import CrossExchangeState, cross_exchange_factor
from .derivatives import DerivativesState, derivatives_factor
from .intermarket import IntermarketState, intermarket_factor
from .onchain import OnchainState, onchain_factor
from .orderbook import OrderbookState, orderbook_factor

SENSOR_DEFAULT_WEIGHT = 0.2

_FACTOR_FN_BY_KEY = {
    "derivatives": derivatives_factor,
    "orderbook": orderbook_factor,
    "onchain": onchain_factor,
    "intermarket": intermarket_factor,
    "cross_exchange": cross_exchange_factor,
}

_STATE_TYPE_BY_KEY = {
    "derivatives": DerivativesState,
    "orderbook": OrderbookState,
    "onchain": OnchainState,
    "intermarket": IntermarketState,
    "cross_exchange": CrossExchangeState,
}


def compute_sensor_votes(
    sensor_states: dict[str, object] | None,
    *,
    weight: float = SENSOR_DEFAULT_WEIGHT,
) -> list[FactorVote]:
    """sensor_states: {"derivatives": DerivativesState(...), "orderbook": OrderbookState(...), ...}.
    Taninmayan anahtarlar veya tip uyusmazligi sessizce atlanir (brain
    tek bir bozuk sensor yuzunden cokmemeli)."""
    if not sensor_states:
        return []

    votes: list[FactorVote] = []
    for key, state in sensor_states.items():
        fn = _FACTOR_FN_BY_KEY.get(key)
        expected_type = _STATE_TYPE_BY_KEY.get(key)
        if fn is None or expected_type is None or not isinstance(state, expected_type):
            continue
        try:
            votes.append(fn(state, weight=weight))
        except Exception:
            continue
    return votes
