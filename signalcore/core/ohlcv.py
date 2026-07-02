"""OHLCV bar dogrulama yardimcilari.

Amac: eksik/cakisik/ardisik-olmayan bar tespiti (leakage/validation
katmaninin ilk savunma hatti). Faz 1b'deki validation/leakage.py bu
temeli kullanacak.
"""
from __future__ import annotations

from datetime import timedelta

from .types import OHLCVBar


class OHLCVValidationError(ValueError):
    pass


def validate_bar(bar: OHLCVBar) -> None:
    if bar.high < bar.low:
        raise OHLCVValidationError(f"high < low @ {bar.ts}: {bar.high} < {bar.low}")
    if not (bar.low <= bar.open <= bar.high):
        raise OHLCVValidationError(f"open bar disinda @ {bar.ts}: {bar.open}")
    if not (bar.low <= bar.close <= bar.high):
        raise OHLCVValidationError(f"close bar disinda @ {bar.ts}: {bar.close}")
    if bar.volume < 0:
        raise OHLCVValidationError(f"negatif volume @ {bar.ts}: {bar.volume}")


def validate_series(bars: list[OHLCVBar], expected_interval: timedelta | None = None) -> None:
    """Bar dizisini dogrular: her bar OHLC tutarli mi, zaman artan mi,
    eksik/cakisik bar var mi (expected_interval verilirse).
    """
    if not bars:
        raise OHLCVValidationError("bos seri dogrulanamaz")

    for bar in bars:
        validate_bar(bar)

    for i in range(1, len(bars)):
        prev, cur = bars[i - 1], bars[i]
        if cur.ts <= prev.ts:
            raise OHLCVValidationError(
                f"zaman artan degil @ index {i}: {prev.ts} -> {cur.ts}"
            )
        if expected_interval is not None:
            gap = cur.ts - prev.ts
            if gap != expected_interval:
                raise OHLCVValidationError(
                    f"beklenmeyen bar araligi @ index {i}: {gap} != {expected_interval} "
                    f"(eksik veya cakisik bar olabilir)"
                )


def to_close_array(bars: list[OHLCVBar]):
    import numpy as np

    return np.array([b.close for b in bars], dtype=float)


def to_arrays(bars: list[OHLCVBar]) -> dict:
    """OHLCV listesini numpy dizilerine cevirir: open/high/low/close/volume."""
    import numpy as np

    return {
        "open": np.array([b.open for b in bars], dtype=float),
        "high": np.array([b.high for b in bars], dtype=float),
        "low": np.array([b.low for b in bars], dtype=float),
        "close": np.array([b.close for b in bars], dtype=float),
        "volume": np.array([b.volume for b in bars], dtype=float),
    }
