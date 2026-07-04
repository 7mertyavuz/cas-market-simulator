"""Ajan taban arayuzu: observe -> decide -> act.

Kural (FAZ-PLANI.md, kritik kural #2): ajanlari basit tut. Emergence
basit kurallarin carpismasindan dogar; her ajan ~50 satir, tek kural
hedefler (Faz 5+).
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from ..environment.base import Environment, EnvironmentState, Order


class Agent(ABC):
    def __init__(self, agent_id: str) -> None:
        self.agent_id = agent_id

    @abstractmethod
    def observe(self, state: EnvironmentState) -> None:
        """Cevrenin guncel durumunu (ve ileride ekstra faktorleri) al."""

    @abstractmethod
    def decide(self) -> Optional[Order]:
        """Gozleme dayanarak bir emir uret (veya None -- islem yok)."""

    def act(self, env: Environment) -> None:
        """decide() ciktisini cevreye gonderir. Alt siniflar genelde
        bunu degistirmez; observe/decide'i override eder."""
        order = self.decide()
        if order is not None:
            env.submit(order)
