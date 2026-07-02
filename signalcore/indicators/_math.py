"""Faktorler arasi paylasilan saf-numpy matematik yardimcilari.

Hicbiri yan etkili degil; hepsi dizi al, dizi/skaler don. Ag erisimi
yok. `NaN` degerler, yeterli veri olmayan baslangic barlarini isaretler
(caller ilgili barlari atlamali).
"""
from __future__ import annotations

import numpy as np


def sma(x: np.ndarray, period: int) -> np.ndarray:
    out = np.full_like(x, np.nan, dtype=float)
    if period <= 0 or len(x) < period:
        return out
    csum = np.cumsum(np.insert(x, 0, 0.0))
    out[period - 1:] = (csum[period:] - csum[:-period]) / period
    return out


def ema(x: np.ndarray, period: int) -> np.ndarray:
    out = np.full_like(x, np.nan, dtype=float)
    if period <= 0 or len(x) < period:
        return out
    alpha = 2.0 / (period + 1.0)
    out[period - 1] = np.mean(x[:period])
    for i in range(period, len(x)):
        out[i] = alpha * x[i] + (1 - alpha) * out[i - 1]
    return out


def true_range(high: np.ndarray, low: np.ndarray, close: np.ndarray) -> np.ndarray:
    prev_close = np.roll(close, 1)
    prev_close[0] = close[0]
    return np.maximum.reduce([
        high - low,
        np.abs(high - prev_close),
        np.abs(low - prev_close),
    ])


def atr(high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int = 14) -> np.ndarray:
    tr = true_range(high, low, close)
    return ema(tr, period)


def rsi(close: np.ndarray, period: int = 14) -> np.ndarray:
    delta = np.diff(close, prepend=close[0])
    gain = np.where(delta > 0, delta, 0.0)
    loss = np.where(delta < 0, -delta, 0.0)
    avg_gain = np.full_like(close, np.nan, dtype=float)
    avg_loss = np.full_like(close, np.nan, dtype=float)
    if len(close) <= period:
        return np.full_like(close, np.nan, dtype=float)
    avg_gain[period] = np.mean(gain[1:period + 1])
    avg_loss[period] = np.mean(loss[1:period + 1])
    for i in range(period + 1, len(close)):
        avg_gain[i] = (avg_gain[i - 1] * (period - 1) + gain[i]) / period
        avg_loss[i] = (avg_loss[i - 1] * (period - 1) + loss[i]) / period
    rs = np.where(avg_loss == 0, np.inf, avg_gain / np.where(avg_loss == 0, 1, avg_loss))
    out = 100.0 - (100.0 / (1.0 + rs))
    out[:period] = np.nan
    return out


def macd(close: np.ndarray, fast: int = 12, slow: int = 26, signal: int = 9):
    ema_fast = ema(close, fast)
    ema_slow = ema(close, slow)
    macd_line = ema_fast - ema_slow
    valid = ~np.isnan(macd_line)
    signal_line = np.full_like(close, np.nan, dtype=float)
    if valid.sum() >= signal:
        vals = macd_line[valid]
        sig_vals = ema(vals, signal)
        signal_line[valid] = sig_vals
    hist = macd_line - signal_line
    return macd_line, signal_line, hist


def adx(high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int = 14) -> np.ndarray:
    up_move = np.diff(high, prepend=high[0])
    down_move = -np.diff(low, prepend=low[0])
    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)
    tr = true_range(high, low, close)
    atr_ = ema(tr, period)
    plus_di = 100 * ema(plus_dm, period) / np.where(atr_ == 0, np.nan, atr_)
    minus_di = 100 * ema(minus_dm, period) / np.where(atr_ == 0, np.nan, atr_)
    dx = 100 * np.abs(plus_di - minus_di) / np.where(
        (plus_di + minus_di) == 0, np.nan, (plus_di + minus_di)
    )
    return ema(dx, period)


def supertrend(high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int = 10, multiplier: float = 3.0):
    """Basitlestirilmis Supertrend: dondurdugu 'direction' dizisi +1 (yukselen
    trend/destek altinda fiyat) veya -1 (dusen trend/direnc ustunde fiyat)."""
    atr_ = atr(high, low, close, period)
    hl2 = (high + low) / 2.0
    upperband = hl2 + multiplier * atr_
    lowerband = hl2 - multiplier * atr_

    direction = np.full(len(close), np.nan)
    final_upper = upperband.copy()
    final_lower = lowerband.copy()

    start = period
    if start >= len(close):
        return direction
    direction[start] = 1.0
    for i in range(start + 1, len(close)):
        if np.isnan(upperband[i]) or np.isnan(lowerband[i]):
            direction[i] = direction[i - 1]
            continue
        final_upper[i] = min(upperband[i], final_upper[i - 1]) if close[i - 1] <= final_upper[i - 1] else upperband[i]
        final_lower[i] = max(lowerband[i], final_lower[i - 1]) if close[i - 1] >= final_lower[i - 1] else lowerband[i]

        if close[i] > final_upper[i - 1]:
            direction[i] = 1.0
        elif close[i] < final_lower[i - 1]:
            direction[i] = -1.0
        else:
            direction[i] = direction[i - 1]
    return direction


def bollinger(close: np.ndarray, period: int = 20, num_std: float = 2.0):
    mid = sma(close, period)
    std = np.full_like(close, np.nan, dtype=float)
    for i in range(period - 1, len(close)):
        std[i] = np.std(close[i - period + 1:i + 1])
    upper = mid + num_std * std
    lower = mid - num_std * std
    pct_b = (close - lower) / np.where((upper - lower) == 0, np.nan, (upper - lower))
    return mid, upper, lower, pct_b


def zscore(x: np.ndarray, period: int = 20) -> np.ndarray:
    mean = sma(x, period)
    out = np.full_like(x, np.nan, dtype=float)
    for i in range(period - 1, len(x)):
        window = x[i - period + 1:i + 1]
        std = np.std(window)
        out[i] = 0.0 if std == 0 else (x[i] - mean[i]) / std
    return out


def hurst_exponent(x: np.ndarray, max_lag: int = 20) -> float:
    """Basit R/S tabanli Hurst tahmini. >0.5 trend, <0.5 mean-revert, ~0.5 random."""
    x = np.asarray(x, dtype=float)
    n = len(x)
    if n < max_lag * 2:
        return 0.5
    lags = range(2, max_lag)
    tau = []
    for lag in lags:
        diffs = x[lag:] - x[:-lag]
        std = np.std(diffs)
        tau.append(std if std > 0 else 1e-8)
    log_lags = np.log(list(lags))
    log_tau = np.log(tau)
    slope, _ = np.polyfit(log_lags, log_tau, 1)
    return float(slope)


def efficiency_ratio(close: np.ndarray, period: int = 10) -> np.ndarray:
    out = np.full_like(close, np.nan, dtype=float)
    for i in range(period, len(close)):
        window = close[i - period:i + 1]
        net_change = abs(window[-1] - window[0])
        path = np.sum(np.abs(np.diff(window)))
        out[i] = 0.0 if path == 0 else net_change / path
    return out


def cmf(high: np.ndarray, low: np.ndarray, close: np.ndarray, volume: np.ndarray, period: int = 20) -> np.ndarray:
    rng = high - low
    mf_mult = np.where(rng == 0, 0.0, ((close - low) - (high - close)) / np.where(rng == 0, 1, rng))
    mf_vol = mf_mult * volume
    out = np.full_like(close, np.nan, dtype=float)
    for i in range(period - 1, len(close)):
        vol_sum = np.sum(volume[i - period + 1:i + 1])
        out[i] = 0.0 if vol_sum == 0 else np.sum(mf_vol[i - period + 1:i + 1]) / vol_sum
    return out


def obv(close: np.ndarray, volume: np.ndarray) -> np.ndarray:
    direction = np.sign(np.diff(close, prepend=close[0]))
    return np.cumsum(direction * volume)
