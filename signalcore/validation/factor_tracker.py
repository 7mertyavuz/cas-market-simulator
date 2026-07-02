"""factor_tracker: her faktorun forward sonuclardaki gercek katkisini olcer.

KURAL (FAZ-PLANI.md, kritik kural #1): Bir faktor, burada pozitif katki
gostermeden agirligi ARTIRILAMAZ. Sezgiyle degil defterle karar verilir.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class FactorRecord:
    vote: float
    forward_return: float


class FactorTracker:
    """Faktor basina (vote, forward_return) defteri tutar; IC/hit-rate
    hesaplar ve agirlik artisina izin verilip verilmeyecegine karar verir.
    """

    def __init__(self, *, min_samples: int = 30, min_ic: float = 0.0) -> None:
        self.min_samples = min_samples
        self.min_ic = min_ic
        self._records: dict[str, list[FactorRecord]] = {}

    def record(self, factor_name: str, vote: float, forward_return: float) -> None:
        self._records.setdefault(factor_name, []).append(
            FactorRecord(vote=vote, forward_return=forward_return)
        )

    def record_many(self, factor_name: str, samples: list[tuple[float, float]]) -> None:
        for vote, ret in samples:
            self.record(factor_name, vote, ret)

    def stats(self, factor_name: str) -> dict:
        import numpy as np

        records = self._records.get(factor_name, [])
        n = len(records)
        if n < 2:
            return {"n": n, "ic": 0.0, "hit_rate": 0.0}

        votes = np.array([r.vote for r in records])
        rets = np.array([r.forward_return for r in records])

        ic = 0.0
        if np.std(votes) > 0 and np.std(rets) > 0:
            ic = float(np.corrcoef(votes, rets)[0, 1])

        directional = votes != 0
        hit_rate = 0.0
        if directional.sum() > 0:
            correct = np.sign(votes[directional]) == np.sign(rets[directional])
            hit_rate = float(np.mean(correct))

        return {"n": n, "ic": ic, "hit_rate": hit_rate}

    def allows_weight_increase(self, factor_name: str) -> bool:
        """Kural: yeterli ornek (min_samples) VE pozitif IC (min_ic'i
        gecmis) olmadan agirlik artisi ONERILMEZ."""
        s = self.stats(factor_name)
        return s["n"] >= self.min_samples and s["ic"] > self.min_ic

    def suggest_weight(self, factor_name: str, current_weight: float, *, step: float = 0.1) -> float:
        """Basit, seffaf kural: izin varsa hafifce artir, katki negatifse
        hafifce azalt, aradaysa sabit tut. Agirlik hicbir zaman negatif
        olamaz."""
        s = self.stats(factor_name)
        if s["n"] < self.min_samples:
            return current_weight  # yeterli veri yok, dokunma
        if s["ic"] > self.min_ic:
            return current_weight * (1.0 + step)
        if s["ic"] < 0:
            return max(0.0, current_weight * (1.0 - step))
        return current_weight

    def known_factors(self) -> list[str]:
        return list(self._records.keys())
