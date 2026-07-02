"""Conformal belirsizlik: tahmine ne kadar guvenmeli.

Basit split-conformal yaklasimi: bir kalibrasyon setindeki
nonconformity skorlarindan (|gercek - tahmin|) istenen kapsama (orn.
%90) icin bir esik (q) cikarilir. Yeni tahmin icin [tahmin-q, tahmin+q]
araligi, o kapsama oraninda gercek degeri icerir (dagilim varsayimi
yok -- yalnizca degisebilirlik/exchangeability varsayimi var).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class ConformalCalibration:
    quantile: float          # kalibre edilmis esik (q)
    coverage: float           # hedef kapsama, orn 0.9
    n_calibration: int


def calibrate(
    predictions: np.ndarray | list[float],
    actuals: np.ndarray | list[float],
    *,
    coverage: float = 0.9,
) -> ConformalCalibration:
    """Kalibrasyon setinden nonconformity esigini cikarir."""
    preds = np.asarray(predictions, dtype=float)
    acts = np.asarray(actuals, dtype=float)
    if len(preds) != len(acts):
        raise ValueError("predictions ve actuals ayni uzunlukta olmali")
    if len(preds) == 0:
        return ConformalCalibration(quantile=float("inf"), coverage=coverage, n_calibration=0)

    scores = np.abs(preds - acts)
    n = len(scores)
    # split-conformal duzeltmesi: ceil((n+1)*coverage)/n kuantili
    level = min(1.0, np.ceil((n + 1) * coverage) / n)
    q = float(np.quantile(scores, level))
    return ConformalCalibration(quantile=q, coverage=coverage, n_calibration=n)


def prediction_interval(point_estimate: float, calibration: ConformalCalibration) -> tuple[float, float]:
    return (point_estimate - calibration.quantile, point_estimate + calibration.quantile)


def confidence_from_interval_width(calibration: ConformalCalibration, *, scale: float = 1.0) -> float:
    """Genis aralik = dusuk guven. [0,1]'e sikistirilmis basit bir donusum;
    Card.confidence'i kalibre etmek icin carpan olarak kullanilabilir."""
    if calibration.n_calibration == 0 or not np.isfinite(calibration.quantile):
        return 0.0
    width = 2 * calibration.quantile
    return float(max(0.0, min(1.0, 1.0 / (1.0 + width / max(scale, 1e-9)))))
