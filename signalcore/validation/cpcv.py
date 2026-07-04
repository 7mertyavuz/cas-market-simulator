"""CPCV (Combinatorial Purged Cross-Validation) -- basitlestirilmis.

Kural (FAZ-PLANI.md Faz 9): "faktor seti buyuyunce ezber/sans testi."
Standart walk-forward tek bir gelecek penceresi kullanir; CPCV, zaman
serisini N gruba bolup COKLU test-grubu kombinasyonlari uzerinden
degerlendirir (Lopez de Prado, "Advances in Financial ML"). Test
gruplarina komsu egitim barlarini "purge/embargo" ile temizler ki
sizinti (leakage) olmasin.

DURUSTLUK NOTU: Bu, tam PBO (Probability of Backtest Overfitting)
metodolojisinin (cok sayida strateji varyanti gerektirir) BASITLESTIRILMIS
bir versiyonudur -- TEK bir faktor/strateji icin out-of-sample skor
DAGILIMI ve negatif-skor orani rapor edilir. Gercek PBO icin coklu
aday strateji seti gerekir (bkz. Faz 9 notlari).
"""
from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from typing import Callable

import numpy as np


@dataclass
class CPCVResult:
    n_splits: int
    test_scores: list[float]
    mean_score: float
    std_score: float
    negative_score_ratio: float  # basitlestirilmis asiri-uyum (overfit) gostergesi

    @property
    def looks_overfit(self) -> bool:
        """Kaba esik: skorlarin yarisindan fazlasi negatifse (yani
        strateji cogu kombinasyonda para kaybediyorsa), pozitif tam
        -orneklem sonucu buyuk ihtimalle sans/ezberdir."""
        return self.negative_score_ratio > 0.5


def purged_group_splits(
    n: int,
    *,
    n_groups: int = 6,
    n_test_groups: int = 2,
    embargo: int = 5,
) -> list[tuple[np.ndarray, np.ndarray]]:
    """n ornegi n_groups esit parcaya boler; n_test_groups'luk her
    kombinasyonu bir test seti yapar, komsu egitim orneklerini
    (embargo kadar) budar. (egitim_indeksleri, test_indeksleri) listesi doner."""
    if n_groups < 2 or n_test_groups < 1 or n_test_groups >= n_groups:
        raise ValueError("gecersiz n_groups/n_test_groups")

    bounds = np.linspace(0, n, n_groups + 1, dtype=int)
    groups = [np.arange(bounds[i], bounds[i + 1]) for i in range(n_groups)]

    splits: list[tuple[np.ndarray, np.ndarray]] = []
    for test_group_idx in combinations(range(n_groups), n_test_groups):
        test_idx = np.concatenate([groups[i] for i in test_group_idx])
        test_idx.sort()

        train_mask = np.ones(n, dtype=bool)
        train_mask[test_idx] = False

        # embargo: test bloklarinin hemen komsulugundaki egitim orneklerini de budar
        for i in test_group_idx:
            lo, hi = bounds[i], bounds[i + 1]
            embargo_lo = max(0, lo - embargo)
            embargo_hi = min(n, hi + embargo)
            train_mask[embargo_lo:embargo_hi] = False

        train_idx = np.where(train_mask)[0]
        if len(train_idx) == 0:
            continue
        splits.append((train_idx, test_idx))

    return splits


def run_cpcv(
    n: int,
    score_fn: Callable[[np.ndarray, np.ndarray], float],
    *,
    n_groups: int = 6,
    n_test_groups: int = 2,
    embargo: int = 5,
) -> CPCVResult:
    """score_fn(train_idx, test_idx) -> float (orn. test kesitinde
    Sharpe-benzeri bir skor). Her kombinasyon icin cagrilir."""
    splits = purged_group_splits(n, n_groups=n_groups, n_test_groups=n_test_groups, embargo=embargo)
    scores = [score_fn(train_idx, test_idx) for train_idx, test_idx in splits]

    if not scores:
        return CPCVResult(n_splits=0, test_scores=[], mean_score=0.0, std_score=0.0, negative_score_ratio=0.0)

    arr = np.array(scores)
    return CPCVResult(
        n_splits=len(scores),
        test_scores=scores,
        mean_score=float(np.mean(arr)),
        std_score=float(np.std(arr)),
        negative_score_ratio=float(np.mean(arr < 0)),
    )
