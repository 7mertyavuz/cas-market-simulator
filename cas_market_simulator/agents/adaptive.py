"""Adaptif ajan: tek kural -- zarar edince stratejini mutasyona ugrat.

Kural (04-yeni-agent-onerileri.md, meta ajanlar / FAZ-PLANI.md Faz 8):
"Zarar edince stratejisini mutasyona ugratir (senin metnindeki
'evrim'). Basit GA/parametre perturbasyonu." Bu ajan bir momentum
kuralini (MomentumAgent ile ayni mantik) tasir, ama parametreleri
(threshold_pct, size) SABIT DEGIL: her `evaluation_interval` tick'te
bir, o pencerede kazanip kazanmadigina bakar; kaybettiyse parametreleri
rastgele perturbe eder (kazanan payini buyutmenin basit versiyonu --
tek-ajan evrimi, "kazanan strateji hayatta kalir, kaybeden mutasyona
ugrar").
"""
from __future__ import annotations

from collections import deque
from typing import Optional

from ..environment.base import EnvironmentState, Order
from .base import Agent


class AdaptiveAgent(Agent):
    def __init__(
        self,
        agent_id: str = "adaptive-0",
        *,
        seed: int | None = 60,
        lookback: int = 5,
        threshold_pct: float = 0.003,
        size: float = 1.0,
        evaluation_interval: int = 20,
        mutation_scale: float = 0.3,
        min_threshold_pct: float = 0.0005,
        max_size: float = 5.0,
    ) -> None:
        super().__init__(agent_id)
        import random

        self._rng = random.Random(seed)
        self.lookback = lookback
        self.threshold_pct = threshold_pct
        self.size = size
        self.evaluation_interval = evaluation_interval
        self.mutation_scale = mutation_scale
        self.min_threshold_pct = min_threshold_pct
        self.max_size = max_size

        self._prices: deque[float] = deque(maxlen=lookback + 1)
        self._last_state: Optional[EnvironmentState] = None
        self._ticks_since_eval = 0
        self._pnl_at_last_eval = 0.0
        self.mutation_count = 0
        self.param_history: list[tuple[float, float]] = [(threshold_pct, size)]

    def observe(self, state: EnvironmentState) -> None:
        self._last_state = state
        self._prices.append(state.price)
        self._ticks_since_eval += 1
        if self._ticks_since_eval >= self.evaluation_interval:
            self._evaluate_and_maybe_mutate(state.price)
            self._ticks_since_eval = 0

    def _evaluate_and_maybe_mutate(self, current_price: float) -> None:
        current_pnl = self.total_pnl(current_price)
        window_pnl = current_pnl - self._pnl_at_last_eval
        self._pnl_at_last_eval = current_pnl

        if window_pnl < 0:
            self.threshold_pct = max(
                self.min_threshold_pct,
                self.threshold_pct * self._rng.uniform(1 - self.mutation_scale, 1 + self.mutation_scale),
            )
            self.size = max(
                0.1, min(self.max_size, self.size * self._rng.uniform(1 - self.mutation_scale, 1 + self.mutation_scale))
            )
            self.mutation_count += 1
            self.param_history.append((self.threshold_pct, self.size))
        # kazandiysa parametreler sabit kalir (kazanan strateji hayatta kalir)

    def decide(self) -> Optional[Order]:
        if self._last_state is None or len(self._prices) < self._prices.maxlen:
            return None
        change_pct = (self._prices[-1] - self._prices[0]) / self._prices[0]
        if change_pct > self.threshold_pct:
            return Order(agent_id=self.agent_id, symbol=self._last_state.symbol, side="buy", size=self.size)
        if change_pct < -self.threshold_pct:
            return Order(agent_id=self.agent_id, symbol=self._last_state.symbol, side="sell", size=self.size)
        return None
