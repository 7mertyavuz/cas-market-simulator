"""Walk-forward degerlendirme: look-ahead yok.

Bir faktor fonksiyonunu, yalnizca o ana kadarki barlarla besleyip
(nedensel/causal), N bar sonraki getiriyle karsilastirir. Boylece
faktorun gercekten "gelecegi tahmin edip etmedigi" olculur.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from ..core.types import FactorVote, OHLCVBar
from ..core.registry import FactorFn


@dataclass
class WalkForwardSample:
    index: int
    vote: float
    forward_return: float


@dataclass
class WalkForwardReport:
    samples: list[WalkForwardSample]
    ic: float              # Information Coefficient (Pearson corr(vote, forward_return))
    hit_rate: float         # dogru yon orani (vote!=0 olan orneklerde)
    n: int

    @property
    def is_significant(self) -> bool:
        """Cok kaba bir anlamlilik esigi: yeterli ornek + pozitif IC."""
        return self.n >= 30 and self.ic > 0.0


def walk_forward_eval(
    factor_fn: FactorFn,
    bars: list[OHLCVBar],
    *,
    min_window: int = 50,
    forward_horizon: int = 5,
    step: int = 1,
) -> WalkForwardReport:
    """Her adimda yalnizca bars[:i+1]'i faktore verir (gelecegi gormez),
    i+forward_horizon barindaki getiriyi 'gercek sonuc' olarak kaydeder.
    """
    samples: list[WalkForwardSample] = []
    n = len(bars)
    last_idx = n - forward_horizon - 1

    for i in range(min_window - 1, max(min_window - 1, last_idx + 1), step):
        if i + forward_horizon >= n:
            break
        causal_bars = bars[: i + 1]   # <-- yalnizca gecmis + su an
        vote_obj = factor_fn(causal_bars)
        vote = vote_obj.vote if isinstance(vote_obj, FactorVote) else float(vote_obj)

        price_now = bars[i].close
        price_future = bars[i + forward_horizon].close
        forward_return = (price_future - price_now) / price_now if price_now else 0.0

        samples.append(WalkForwardSample(index=i, vote=vote, forward_return=forward_return))

    if len(samples) < 2:
        return WalkForwardReport(samples=samples, ic=0.0, hit_rate=0.0, n=len(samples))

    votes = np.array([s.vote for s in samples])
    rets = np.array([s.forward_return for s in samples])

    if np.std(votes) == 0 or np.std(rets) == 0:
        ic = 0.0
    else:
        ic = float(np.corrcoef(votes, rets)[0, 1])

    directional = votes != 0
    if directional.sum() == 0:
        hit_rate = 0.0
    else:
        correct = np.sign(votes[directional]) == np.sign(rets[directional])
        hit_rate = float(np.mean(correct))

    return WalkForwardReport(samples=samples, ic=ic, hit_rate=hit_rate, n=len(samples))
