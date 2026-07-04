"""Faz 9 demo: istatistiksel dogrulama + portfoy insasi.

Dort parcayi tek bir akista birlikte gosterir:
  1. calibration.py    -- sentetik fiyat serisinin "stylized facts"i
                           (kalin kuyruk, volatilite kumelenmesi, kaldirac
                           etkisi) gercekci mi?
  2. cpcv.py            -- basit bir hareketli-ortalama kesisim stratejisi
                           icin CPCV (Combinatorial Purged CV) ile
                           out-of-sample skor dagilimi + overfit orani.
  3. deflated_sharpe.py -- gozlemlenen Sharpe, kac parametre varyanti
                           denendigine (n_trials) gore deflate ediliyor mu?
  4. risk/tail.py +
     analysis/portfolio.py -- 4 sentetik varlik icin VaR/CVaR/Hill/EVT
                           kuyruk raporu ve HRP + korelasyon limiti +
                           gunluk risk butcesi ile portfoy insasi.

Calistir:
    PYTHONPATH=. python3 scripts/run_faz9_demo.py
"""
from __future__ import annotations

import numpy as np

from cas_market_simulator.analysis.portfolio import build_portfolio
from signalcore.feeds import Regime, synthetic_ohlcv
from signalcore.risk.tail import compute_tail_risk_report
from signalcore.validation.calibration import compute_calibration_report
from signalcore.validation.cpcv import run_cpcv
from signalcore.validation.deflated_sharpe import deflated_sharpe_ratio


def _closes_from_bars(bars) -> np.ndarray:
    return np.array([b.close for b in bars], dtype=float)


def _ma_crossover_returns(closes: np.ndarray, fast: int, slow: int) -> np.ndarray:
    """Basit bir araç-strateji: hizli MA > yavas MA -> long, aksi -> flat.
    Gercek bir alfa iddiasi degil, CPCV/DSR mekanigini gostermek icindir.
    """
    if slow >= len(closes):
        return np.zeros(0)
    fast_ma = np.convolve(closes, np.ones(fast) / fast, mode="valid")
    slow_ma = np.convolve(closes, np.ones(slow) / slow, mode="valid")
    offset = len(fast_ma) - len(slow_ma)
    fast_ma = fast_ma[offset:]
    signal = np.where(fast_ma > slow_ma, 1.0, -1.0)
    rets = closes[1:] / closes[:-1] - 1.0
    rets = rets[-len(signal):]
    strat_rets = signal[:-1] * rets[1:]
    return strat_rets


def _sharpe(returns: np.ndarray) -> float:
    if returns.size < 2 or np.std(returns) < 1e-12:
        return 0.0
    return float(np.mean(returns) / np.std(returns, ddof=1) * np.sqrt(365 * 24 * 60))


def main() -> None:
    print("=" * 70)
    print("FAZ 9 -- Istatistiksel Dogrulama + Portfoy Insasi")
    print("=" * 70)

    # ── 1) Kalibrasyon: stylized facts ──────────────────────────────
    bars = synthetic_ohlcv(3000, symbol="SIM/USDT", seed=11, initial_regime=Regime.HIGH_VOL)
    closes = _closes_from_bars(bars)
    calib = compute_calibration_report(closes)

    print("\n[1] Kalibrasyon raporu (stylized facts):")
    print(f"    n = {calib.n}")
    print(f"    excess kurtosis        = {calib.excess_kurtosis:.3f} (fat-tailed: {calib.is_fat_tailed})")
    print(f"    vol clustering autocorr = {calib.vol_clustering_autocorr:.3f} (var: {calib.has_vol_clustering})")
    print(f"    leverage effect corr   = {calib.leverage_effect_corr:.3f} (var: {calib.has_leverage_effect})")
    print(f"    gecen stylized facts    = {calib.stylized_facts_passed}/3")

    # ── 2) CPCV: basit MA-kesisim stratejisinin out-of-sample skoru ──
    strat_returns = _ma_crossover_returns(closes, fast=10, slow=30)
    n = len(strat_returns)

    def score_fn(train_idx: np.ndarray, test_idx: np.ndarray) -> float:
        test_rets = strat_returns[test_idx]
        return _sharpe(test_rets)

    cpcv_result = run_cpcv(n, score_fn, n_groups=6, n_test_groups=2, embargo=20)

    print("\n[2] CPCV (out-of-sample skor dagilimi):")
    print(f"    n_splits           = {cpcv_result.n_splits}")
    print(f"    mean score (Sharpe) = {cpcv_result.mean_score:.3f}")
    print(f"    std score           = {cpcv_result.std_score:.3f}")
    print(f"    negatif skor orani   = {cpcv_result.negative_score_ratio:.2%}")
    print(f"    overfit gorunumu?    = {cpcv_result.looks_overfit}")

    # ── 3) Deflated Sharpe Ratio: coklu deneme cezasi ─────────────────
    observed_sharpe = _sharpe(strat_returns)
    variance_of_sharpes = max(cpcv_result.std_score ** 2, 1e-6)
    n_trials = 20  # varsayim: 20 (fast, slow) parametre kombinasyonu denendi

    dsr_result = deflated_sharpe_ratio(
        observed_sharpe,
        n_trials=n_trials,
        variance_of_sharpes=variance_of_sharpes,
        n_observations=n,
    )

    print("\n[3] Deflated Sharpe Ratio (coklu-deneme duzeltmesi):")
    print(f"    observed Sharpe (yillik)     = {dsr_result.observed_sharpe:.3f}")
    print(f"    n_trials                      = {dsr_result.n_trials}")
    print(f"    expected max Sharpe (null)    = {dsr_result.expected_max_sharpe_under_null:.3f}")
    print(f"    PSR                           = {dsr_result.psr:.3f}")
    print(f"    DSR                           = {dsr_result.dsr:.3f}")
    print(f"    anlamli mi? (DSR >= 0.95)      = {dsr_result.is_significant}")

    # ── 4) Kuyruk riski + HRP portfoy insasi (4 sentetik varlik) ─────
    symbols = ["SIM-A", "SIM-B", "SIM-C", "SIM-D"]
    regimes = [Regime.TREND_UP, Regime.TREND_UP, Regime.MEAN_REVERT, Regime.HIGH_VOL]
    seeds = [101, 102, 201, 301]

    all_closes = []
    for sym, regime, seed in zip(symbols, regimes, seeds):
        b = synthetic_ohlcv(1500, symbol=sym, seed=seed, initial_regime=regime)
        all_closes.append(_closes_from_bars(b))

    min_len = min(len(c) for c in all_closes)
    price_matrix = np.column_stack([c[-min_len:] for c in all_closes])
    returns_matrix = price_matrix[1:] / price_matrix[:-1] - 1.0

    print("\n[4a] Kuyruk riski raporu (varlik basina):")
    for i, sym in enumerate(symbols):
        tail_report = compute_tail_risk_report(price_matrix[:, i])
        print(
            f"    {sym:8s} VaR95={tail_report.historical_var_95:+.4f}  "
            f"CVaR95={tail_report.historical_cvar_95:+.4f}  "
            f"Hill xi={tail_report.hill_tail_index:.3f}  "
            f"fat-tailed={tail_report.is_fat_tailed}"
        )

    alloc = build_portfolio(returns_matrix, symbols, target_daily_vol=0.03)

    print("\n[4b] HRP portfoy insasi:")
    print(f"    HRP agirliklari      : {{ {', '.join(f'{k}: {v:.3f}' for k, v in alloc.hrp_weights.items())} }}")
    print(f"    Limit-sonrasi        : {{ {', '.join(f'{k}: {v:.3f}' for k, v in alloc.limited_weights.items())} }}")
    print(f"    Nihai (risk-butceli) : {{ {', '.join(f'{k}: {v:.3f}' for k, v in alloc.final_weights.items())} }}")
    print(f"    Portfoy gunluk vol    = {alloc.portfolio_daily_vol:.4f}")
    print(f"    Risk olcek faktoru    = {alloc.risk_scale:.3f}")
    if alloc.warnings:
        print(f"    Uyarilar              : {alloc.warnings}")

    print("\n" + "=" * 70)
    print("Faz 9 tamamlandi: kalibrasyon + CPCV/DSR + kuyruk riski + HRP portfoy")
    print("insasi uctan uca calisti. FAZ-PLANI.md'deki son faz budur (Faz 0-9).")
    print("=" * 70)


if __name__ == "__main__":
    main()
