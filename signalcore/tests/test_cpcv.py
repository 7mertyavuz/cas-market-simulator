import numpy as np

from signalcore.validation.cpcv import purged_group_splits, run_cpcv


def test_purged_group_splits_basic_shape():
    splits = purged_group_splits(120, n_groups=6, n_test_groups=2, embargo=2)
    from math import comb

    assert len(splits) == comb(6, 2)
    for train_idx, test_idx in splits:
        assert len(set(train_idx) & set(test_idx)) == 0


def test_purged_group_splits_invalid_params_raise():
    import pytest

    with pytest.raises(ValueError):
        purged_group_splits(100, n_groups=1)
    with pytest.raises(ValueError):
        purged_group_splits(100, n_groups=5, n_test_groups=5)


def test_purged_group_splits_embargo_removes_neighbors():
    splits = purged_group_splits(100, n_groups=5, n_test_groups=1, embargo=10)
    # her test grubu ~20 ornek; embargo 10 -> komsu egitim orneklerinin bir kismi budanmali
    for train_idx, test_idx in splits:
        assert len(train_idx) < 100 - len(test_idx)


def test_run_cpcv_random_score_near_zero_mean():
    rng = np.random.default_rng(0)

    def score_fn(train_idx, test_idx):
        return float(rng.normal(0, 1))

    result = run_cpcv(100, score_fn, n_groups=5, n_test_groups=1, embargo=2)
    assert result.n_splits == 5
    assert -1.0 < result.mean_score < 1.0


def test_run_cpcv_always_positive_score_no_overfit_flag():
    def score_fn(train_idx, test_idx):
        return 1.0

    result = run_cpcv(100, score_fn, n_groups=5, n_test_groups=1, embargo=2)
    assert result.negative_score_ratio == 0.0
    assert not result.looks_overfit


def test_run_cpcv_always_negative_score_flags_overfit():
    def score_fn(train_idx, test_idx):
        return -1.0

    result = run_cpcv(100, score_fn, n_groups=5, n_test_groups=1, embargo=2)
    assert result.negative_score_ratio == 1.0
    assert result.looks_overfit
