"""Veri besleme katmani.

Kural (00-ORTAK-SOZLESME.md #1): simulasyon modu birinci sinif olmali
-- harici API/anahtar olmadan deterministik sentetik veri uretilebilmeli.
Gercek veri (ccxt/yfinance) baglantisi ileride burada, ayni fonksiyon
imzasi altinda eklenecek; simulator/testler sentetik uretecine bagimli
kalacak sekilde tasarlandi.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import numpy as np

from .core.types import OHLCVBar


class Regime:
    TREND_UP = "trend_up"
    TREND_DOWN = "trend_down"
    MEAN_REVERT = "mean_revert"
    HIGH_VOL = "high_vol"


_REGIME_PARAMS = {
    # (yillik drift mu, yillik volatilite sigma)
    Regime.TREND_UP: (0.60, 0.35),
    Regime.TREND_DOWN: (-0.60, 0.40),
    Regime.MEAN_REVERT: (0.0, 0.25),
    Regime.HIGH_VOL: (0.0, 0.90),
}

_DEFAULT_TRANSITION = {
    Regime.TREND_UP: {Regime.TREND_UP: 0.92, Regime.MEAN_REVERT: 0.05, Regime.HIGH_VOL: 0.02, Regime.TREND_DOWN: 0.01},
    Regime.TREND_DOWN: {Regime.TREND_DOWN: 0.90, Regime.MEAN_REVERT: 0.05, Regime.HIGH_VOL: 0.04, Regime.TREND_UP: 0.01},
    Regime.MEAN_REVERT: {Regime.MEAN_REVERT: 0.90, Regime.TREND_UP: 0.04, Regime.TREND_DOWN: 0.04, Regime.HIGH_VOL: 0.02},
    Regime.HIGH_VOL: {Regime.HIGH_VOL: 0.80, Regime.MEAN_REVERT: 0.10, Regime.TREND_UP: 0.05, Regime.TREND_DOWN: 0.05},
}


def synthetic_ohlcv(
    n_bars: int,
    *,
    symbol: str = "SIM/USDT",
    start_price: float = 100.0,
    interval: timedelta = timedelta(minutes=1),
    start_ts: datetime | None = None,
    seed: int | None = 42,
    initial_regime: str = Regime.MEAN_REVERT,
    bars_per_year: float = 365 * 24 * 60,  # 1dk barlarina gore
) -> list[OHLCVBar]:
    """Rejim-anahtarlamali GBM ile deterministik sentetik OHLCV uretir.

    API anahtari / ag erisimi gerektirmez -- gelistirme ve simulator
    icin birinci sinif veri kaynagi budur.
    """
    if n_bars <= 0:
        raise ValueError("n_bars > 0 olmali")

    rng = np.random.default_rng(seed)
    start_ts = start_ts or datetime.now(timezone.utc)
    dt = 1.0 / bars_per_year

    bars: list[OHLCVBar] = []
    price = start_price
    regime = initial_regime

    for i in range(n_bars):
        # rejim gecisi
        trans = _DEFAULT_TRANSITION[regime]
        regime = rng.choice(list(trans.keys()), p=list(trans.values()))
        mu, sigma = _REGIME_PARAMS[regime]

        # GBM adimi (log-normal getiri)
        shock = rng.normal(0.0, 1.0)
        log_ret = (mu - 0.5 * sigma**2) * dt + sigma * np.sqrt(dt) * shock
        open_price = price
        close_price = max(open_price * float(np.exp(log_ret)), 1e-8)

        # bar ici high/low: open-close araligi + kucuk ekstra wick
        intrabar_vol = sigma * np.sqrt(dt) * open_price
        wick_up = abs(rng.normal(0.0, intrabar_vol * 0.6))
        wick_down = abs(rng.normal(0.0, intrabar_vol * 0.6))
        high = max(open_price, close_price) + wick_up
        low = max(min(open_price, close_price) - wick_down, 1e-8)

        volume = abs(rng.normal(1000.0, 300.0)) * (1.0 + (sigma / 0.35))

        bars.append(
            OHLCVBar(
                ts=start_ts + i * interval,
                open=round(open_price, 8),
                high=round(high, 8),
                low=round(low, 8),
                close=round(close_price, 8),
                volume=round(max(volume, 0.0), 4),
            )
        )
        price = close_price

    return bars
