"""En basit ajan: hicbir zaman emir vermez.

Faz 0'daki uctan-uca tick dongusunu kanitlamak icin kullanilir --
"tek bos ajan" (bkz. FAZ-PLANI.md Faz 0 'Bitti' kriteri).
"""
from __future__ import annotations

from typing import Optional

from ..environment.base import EnvironmentState, Order

from .base import Agent


class NoopAgent(Agent):
    def __init__(self, agent_id: str = "noop-0") -> None:
        super().__init__(agent_id)
        self.last_seen: EnvironmentState | None = None

    def observe(self, state: EnvironmentState) -> None:
        self.last_seen = state

    def decide(self) -> Optional[Order]:
        return None
