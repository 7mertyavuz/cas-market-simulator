"""Faktor kayit + agirlik tablosu.

Tasarim ilkesi (03-PROMPT Bolum 3): faktor eklemek burada bir satir
olmali; cekirdek (aggregator/brain) degismemeli. Her faktor saf
fonksiyon: (ohlcv, **kwargs) -> FactorVote.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from .types import FactorVote

FactorFn = Callable[..., FactorVote]


@dataclass
class FactorSpec:
    name: str
    fn: FactorFn
    initial_weight: float = 1.0
    axis: str = "unknown"   # "trend" | "momentum" | "meanrev" | "volatility" | "volume" | "structure" | "external"
    enabled: bool = True


class FactorRegistry:
    """Global-benzeri ama test edilebilir faktor kayit defteri."""

    def __init__(self) -> None:
        self._specs: dict[str, FactorSpec] = {}

    def register(
        self,
        name: str,
        fn: FactorFn,
        *,
        initial_weight: float = 1.0,
        axis: str = "unknown",
        enabled: bool = True,
    ) -> None:
        if name in self._specs:
            raise ValueError(f"faktor zaten kayitli: {name}")
        self._specs[name] = FactorSpec(
            name=name, fn=fn, initial_weight=initial_weight, axis=axis, enabled=enabled
        )

    def unregister(self, name: str) -> None:
        self._specs.pop(name, None)

    def get(self, name: str) -> FactorSpec:
        return self._specs[name]

    def all(self, *, enabled_only: bool = True) -> list[FactorSpec]:
        specs = list(self._specs.values())
        if enabled_only:
            specs = [s for s in specs if s.enabled]
        return specs

    def set_weight(self, name: str, weight: float) -> None:
        if weight < 0:
            raise ValueError("weight negatif olamaz")
        self._specs[name].initial_weight = weight

    def __len__(self) -> int:
        return len(self._specs)

    def __contains__(self, name: str) -> bool:
        return name in self._specs


# Modul-seviyesi paylasilan kayit defteri (brain.py ve testler kullanir).
default_registry = FactorRegistry()
