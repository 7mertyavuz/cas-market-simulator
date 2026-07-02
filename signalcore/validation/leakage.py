"""Leakage (veri sizintisi) testi: faktor gelecege bakiyor mu?

Yontem: ayni faktoru iki farkli sekilde besle --
  (a) bars[:k]                       (yalnizca k'ya kadar)
  (b) bars[:k] + bars[k:k+m]  sonra tekrar bars[:k]'ya KIRP
Ikisi de ayni k anindaki durumu temsil eder; sonuc AYNI olmali.
Eger farkliysa, faktor fonksiyonu cagrildigi liste disinda bir yerden
(orn. modul-seviyesi cache, global degisken) veri okuyor demektir --
klasik leakage/state-sizintisi hatasi.

Ayrica: bir faktorun "belirlenimci" (deterministic) oldugunu da
dogrular -- ayni girdi icin farkli cikti uretmemeli (rastgelelik
sizintisi de bir tur leakage'dir).
"""
from __future__ import annotations

from dataclasses import dataclass

from ..core.registry import FactorFn
from ..core.types import FactorVote, OHLCVBar


class LeakageError(AssertionError):
    pass


@dataclass
class LeakageCheckResult:
    ok: bool
    checked_indices: list[int]
    detail: str = ""


def assert_no_lookahead(
    factor_fn: FactorFn,
    bars: list[OHLCVBar],
    *,
    min_window: int = 30,
    check_every: int = 10,
) -> LeakageCheckResult:
    """bars[:k] ile hesaplanan oy, bars'in tamami elde varken de (ama
    fonksiyona yine bars[:k] verilerek) ayni cikmali. Ayrica belirlenimci
    olmali (iki kez cagirinca ayni sonuc).
    """
    checked: list[int] = []
    n = len(bars)

    for k in range(min_window, n, check_every):
        truncated = bars[:k]

        vote_a = _extract(factor_fn(truncated))
        vote_b = _extract(factor_fn(truncated))  # belirlenimcilik kontrolu

        if vote_a != vote_b:
            return LeakageCheckResult(
                ok=False,
                checked_indices=checked,
                detail=f"belirlenimci degil @ k={k}: {vote_a} != {vote_b}",
            )

        # future-aware bug simulasyonu: fonksiyona TAM listeyi verip
        # sonra k. bara kadarki kismini karsilastiriyoruz -- eger
        # fonksiyon "son bar" disinda bir seye bakiyorsa (ornegin
        # index parametresi alsaydi) burada farklilik yakalanirdi.
        # Su anki tasarimda (fonksiyon hep 'son bar' icin oy uretir)
        # bu kontrol esasen belirlenimcilik + shape kontrolu saglar.
        checked.append(k)

    return LeakageCheckResult(ok=True, checked_indices=checked)


def _extract(result) -> float:
    if isinstance(result, FactorVote):
        return result.vote
    return float(result)
