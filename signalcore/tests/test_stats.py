import math

from signalcore.validation._stats import inv_norm_cdf, norm_cdf


def test_norm_cdf_at_zero():
    assert abs(norm_cdf(0.0) - 0.5) < 1e-9


def test_norm_cdf_known_value():
    assert abs(norm_cdf(1.959964) - 0.975) < 1e-4


def test_inv_norm_cdf_roundtrip():
    for p in [0.01, 0.1, 0.5, 0.9, 0.99]:
        x = inv_norm_cdf(p)
        assert abs(norm_cdf(x) - p) < 1e-6


def test_inv_norm_cdf_median_is_zero():
    assert abs(inv_norm_cdf(0.5)) < 1e-9


def test_inv_norm_cdf_extremes():
    assert inv_norm_cdf(0.0) == float("-inf")
    assert inv_norm_cdf(1.0) == float("inf")
