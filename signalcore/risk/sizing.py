"""Pozisyon boyutu: edge / yarim-Kelly.

Kural: kart guveni dogrudan "bahis boyutu" degildir -- Kelly kesri
uzerinden gecirilir ve guvenlik icin YARIM Kelly kullanilir (tam
Kelly, tahmin hatasina asiri duyarlidir).
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class SizingResult:
    size_pct: float          # portfoyun/sermayenin yuzdesi olarak onerilen boyut
    kelly_fraction: float     # ham (tam) Kelly kesri
    edge: float                # win_rate*avg_win - loss_rate*avg_loss (beklenen deger, birim getiri)


def edge_from_confidence(confidence: float, *, win_loss_ratio: float = 1.5) -> float:
    """Card.confidence'i kaba bir kazanma olasiligina esler (0.5 + confidence*0.4,
    yani en fazla %90 win-rate varsayimi) ve Kelly-uyumlu 'edge' hesaplar.

    Bu bir tahmin degil, KONSERVATIF bir yer tutucudur -- gercek win-rate
    factor_tracker'daki forward-test defterinden (Faz 3) gelmelidir.
    """
    confidence = max(0.0, min(1.0, confidence))
    win_rate = 0.5 + confidence * 0.4
    loss_rate = 1.0 - win_rate
    edge = win_rate * win_loss_ratio - loss_rate
    return edge


def kelly_fraction(win_rate: float, win_loss_ratio: float) -> float:
    """f* = p - q/b  (p=kazanma olasiligi, q=1-p, b=win/loss orani)."""
    if win_loss_ratio <= 0:
        return 0.0
    p = max(0.0, min(1.0, win_rate))
    q = 1.0 - p
    f = p - q / win_loss_ratio
    return max(0.0, f)


def half_kelly_size(
    confidence: float,
    *,
    win_loss_ratio: float = 1.5,
    max_size_pct: float = 0.1,
) -> SizingResult:
    """Card.confidence -> onerilen pozisyon boyutu (sermaye yuzdesi).

    Yarim Kelly + ust sinir (max_size_pct) uygulanir; asla negatif
    boyut donmez (confidence dusukse 0).
    """
    win_rate = 0.5 + max(0.0, min(1.0, confidence)) * 0.4
    f_full = kelly_fraction(win_rate, win_loss_ratio)
    f_half = f_full * 0.5
    size_pct = float(max(0.0, min(max_size_pct, f_half)))
    edge = float(edge_from_confidence(confidence, win_loss_ratio=win_loss_ratio))
    return SizingResult(size_pct=size_pct, kelly_fraction=float(f_full), edge=edge)
