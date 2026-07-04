import numpy as np

from signalcore.validation.calibration import compute_calibration_report
from signalcore.feeds import synthetic_ohlcv


def test_too_short_series_returns_defaults():
    report = compute_calibration_report([100.0, 101.0])
    assert report.n == 2
    assert not report.is_fat_tailed


def test_normal_returns_no_fat_tails():
    rng = np.random.default_rng(0)
    prices = 100 * np.cumprod(1 + rng.normal(0, 0.001, 2000))
    report = compute_calibration_report(list(prices), fat_tail_threshold=1.0)
    assert abs(report.excess_kurtosis) < 1.0
    assert not report.is_fat_tailed


def test_fat_tailed_returns_detected():
    rng = np.random.default_rng(1)
    # karisik dagilim: cogu kucuk, bazen buyuk siçrama -- kalin kuyruk uretir
    normal_part = rng.normal(0, 0.001, 1900)
    jumps = rng.normal(0, 0.03, 100)
    returns = np.concatenate([normal_part, jumps])
    rng.shuffle(returns)
    prices = 100 * np.cumprod(1 + returns)
    report = compute_calibration_report(list(prices), fat_tail_threshold=1.0)
    assert report.excess_kurtosis > 1.0
    assert report.is_fat_tailed


def test_synthetic_ohlcv_calibration_runs():
    bars = synthetic_ohlcv(1000, seed=5)
    closes = [b.close for b in bars]
    report = compute_calibration_report(closes)
    assert report.n == 1000
    assert isinstance(report.stylized_facts_passed, int)
    assert 0 <= report.stylized_facts_passed <= 3


def test_vol_clustering_detected_in_regime_switching_series():
    # GARCH-benzeri: sakin donem + firtinali donem art arda -> guclu clustering
    rng = np.random.default_rng(2)
    calm = rng.normal(0, 0.001, 500)
    storm = rng.normal(0, 0.02, 500)
    returns = np.concatenate([calm, storm, calm, storm])
    prices = 100 * np.cumprod(1 + returns)
    report = compute_calibration_report(list(prices), clustering_threshold=0.05)
    assert report.vol_clustering_autocorr > 0.05
    assert report.has_vol_clustering
