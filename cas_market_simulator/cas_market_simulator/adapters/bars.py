"""Environment tick gecmisini signalcore OHLCVBar dizisine cevirir.

Environment su an tam bir order book/OHLC uretmiyor (bkz. Faz 0 notu:
`environment/base.py` yalnizca net emir dengesizligine gore fiyat
iten yer tutucu bir modeldir). Bu yuzden her tick, ac/kapan-ayni bar
gibi ele alinir: open=onceki fiyat, close=guncel fiyat, high/low bu
ikisinin ust/alt siniri. Faz 5'te microstructure-analyzer'in
simulasyon modu "cevre" olarak baglandiginda bu adaptor gercek
OHLCV'ye (veya dogrudan gercek bar akisina) baglanacak sekilde
degistirilecek; imza (list[EnvironmentState] -> list[OHLCVBar]) sabit
kalmali.
"""
from __future__ import annotations

from signalcore.core.types import OHLCVBar as SCBar

from ..environment.base import EnvironmentState


def ohlcv_from_history(
    history: list[EnvironmentState],
    *,
    default_volume: float = 1.0,
) -> list[SCBar]:
    if len(history) < 2:
        return []

    bars: list[SCBar] = []
    for prev, cur in zip(history[:-1], history[1:]):
        o, c = prev.price, cur.price
        bars.append(
            SCBar(
                ts=cur.ts,
                open=o,
                high=max(o, c),
                low=min(o, c),
                close=c,
                volume=default_volume,
            )
        )
    return bars
