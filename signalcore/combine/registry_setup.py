"""Varsayilan faktorleri core.registry.default_registry'ye kaydeder.

Ayri dosyada tutulur ki brain.py import edildiginde yan etkili
kayit calissin ama core/registry.py saf/bagimsiz kalsin.
"""
from __future__ import annotations

from ..core.registry import FactorRegistry, default_registry
from ..indicators.meanrev import meanrev_factor
from ..indicators.momentum import momentum_factor
from ..indicators.structure import structure_factor
from ..indicators.trend import trend_factor
from ..indicators.volatility import volatility_factor
from ..indicators.volume import volume_factor


def register_defaults(registry: FactorRegistry | None = None) -> FactorRegistry:
    reg = registry if registry is not None else default_registry
    defaults = [
        ("trend", trend_factor, 1.0, "trend"),
        ("momentum", momentum_factor, 1.0, "momentum"),
        ("volatility", volatility_factor, 0.5, "volatility"),
        ("meanrev", meanrev_factor, 0.8, "meanrev"),
        ("volume", volume_factor, 0.6, "volume"),
        ("structure", structure_factor, 0.5, "structure"),
    ]
    for name, fn, w, axis in defaults:
        if name not in reg:
            reg.register(name, fn, initial_weight=w, axis=axis)
    return reg
