"""Emergence metrikleri: beliren rejim olculebilir mi?

Faz 6 amaci: "scriptli bir sok, olculebilir bir kaskad/ralli belirtiyor"
(bkz. FAZ-PLANI.md). Bu modul, Engine.run() sonuclarindan (TickResult
listesi) dort metrik hesaplar:
  - cascade_size: en buyuk N-tick'lik kumulatif fiyat hareketi (kaskad buyuklugu)
  - agent_synchronization: ajanlarin ayni yonde emir verme egilimi (surme/herding)
  - return_autocorrelation: getirilerin lag-1 otokorelasyonu (momentum/mean-revert egilimi)
  - flash_crash_frequency: |tek-tick getiri| esigi asan tick orani
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class EmergenceReport:
    n_ticks: int
    cascade_size_pct: float           # en buyuk N-tick'lik kumulatif hareket (yuzde, isaretli)
    cascade_window: int
    agent_synchronization: float       # 0..1, 1 = tum ajanlar hep ayni yonde
    return_autocorrelation: float       # [-1,1]
    flash_crash_frequency: float         # 0..1, esik asan tick orani
    max_single_tick_return_pct: float
    min_single_tick_return_pct: float


def _returns(prices: list[float]) -> list[float]:
    return [(prices[i] - prices[i - 1]) / prices[i - 1] for i in range(1, len(prices)) if prices[i - 1] != 0]


def _max_abs_windowed_move(prices: list[float], window: int) -> float:
    if len(prices) <= window:
        window = max(1, len(prices) - 1)
    best = 0.0
    for i in range(len(prices) - window):
        start, end = prices[i], prices[i + window]
        if start == 0:
            continue
        move = (end - start) / start
        if abs(move) > abs(best):
            best = move
    return best


def _autocorrelation_lag1(returns: list[float]) -> float:
    import numpy as np

    if len(returns) < 3:
        return 0.0
    arr = np.array(returns)
    a, b = arr[:-1], arr[1:]
    if np.std(a) == 0 or np.std(b) == 0:
        return 0.0
    return float(np.corrcoef(a, b)[0, 1])


def compute_emergence(
    results: list,
    *,
    cascade_window: int = 10,
    flash_crash_threshold_pct: float = 0.01,
) -> EmergenceReport:
    """`results`: Engine.run() ciktisi (TickResult listesi). Yalnizca
    `.state.price` ve `.agent_orders`/order yonu bilgisi kullanilir --
    agent_synchronization icin caller `agent_directions` (tick basi
    {agent_id: side}) sagliyorsa daha dogru olur; saglanmazsa 0 doner
    (bkz. compute_emergence_from_engine)."""
    prices = [r.state.price for r in results]
    if len(prices) < 2:
        return EmergenceReport(
            n_ticks=len(results), cascade_size_pct=0.0, cascade_window=cascade_window,
            agent_synchronization=0.0, return_autocorrelation=0.0, flash_crash_frequency=0.0,
            max_single_tick_return_pct=0.0, min_single_tick_return_pct=0.0,
        )

    returns = _returns(prices)
    cascade = _max_abs_windowed_move(prices, cascade_window)
    autocorr = _autocorrelation_lag1(returns)
    flash_freq = (
        sum(1 for r in returns if abs(r) >= flash_crash_threshold_pct) / len(returns) if returns else 0.0
    )

    return EmergenceReport(
        n_ticks=len(results),
        cascade_size_pct=cascade,
        cascade_window=cascade_window,
        agent_synchronization=0.0,
        return_autocorrelation=autocorr,
        flash_crash_frequency=flash_freq,
        max_single_tick_return_pct=max(returns) if returns else 0.0,
        min_single_tick_return_pct=min(returns) if returns else 0.0,
    )


def crowd_emergence_score(
    report: EmergenceReport,
    *,
    cascade_scale_pct: float = 0.05,
) -> float:
    """EmergenceReport'u TEK bir isaretli skora [-1,1] indirger --
    Faz 7'nin geri besleme sinyali: "kalabalik cokmeye mi gidiyor?".

    Isaret, kaskadin yonunden gelir (negatif = asagi yonlu kaskad/panik,
    pozitif = yukari yonlu ralli/euphoria). Buyukluk, ajan senkronizasyonu
    ile olceklenir -- dagitik/gurultulu hareketler (dusuk sync) sinyali
    zayiflatir, senkronize (surme) hareketler guclendirir. Bu skor
    dogrudan signalcore'a extra_factors["crowd_emergence"] olarak
    (dusuk agirlikla) geri beslenir (bkz. adapters/factor_brain.py).
    """
    base = max(-1.0, min(1.0, report.cascade_size_pct / cascade_scale_pct))
    sync_multiplier = 0.4 + 0.6 * report.agent_synchronization  # sync=0 -> 0.4x, sync=1 -> 1.0x
    return max(-1.0, min(1.0, base * sync_multiplier))


def compute_emergence_from_engine(
    results: list,
    *,
    cascade_window: int = 10,
    flash_crash_threshold_pct: float = 0.01,
) -> EmergenceReport:
    """Engine.run() ciktisini (TickResult.agent_orders dahil) dogrudan
    alip tum metrikleri (agent_synchronization dahil) doldurur --
    demo/CLI icin onerilen giris noktasi."""
    report = compute_emergence(
        results, cascade_window=cascade_window, flash_crash_threshold_pct=flash_crash_threshold_pct
    )
    sync = agent_synchronization_from_directions([r.agent_orders for r in results])
    report.agent_synchronization = sync
    return report


def agent_synchronization_from_directions(agent_directions_per_tick: list[dict]) -> float:
    """agent_directions_per_tick: her tick icin {agent_id: "buy"|"sell"}
    (yalnizca emir verenler). Her tick'te cogunluk yonundeki ajan
    oranini hesaplar, tum ticklerin ortalamasini doner. Emir vermeyen
    tick'ler (bos dict) hesaba katilmaz."""
    ratios = []
    for directions in agent_directions_per_tick:
        if not directions:
            continue
        buys = sum(1 for s in directions.values() if s == "buy")
        sells = len(directions) - buys
        majority = max(buys, sells)
        ratios.append(majority / len(directions))
    if not ratios:
        return 0.0
    return sum(ratios) / len(ratios)
