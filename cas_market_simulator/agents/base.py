"""Ajan taban arayuzu: observe -> decide -> act.

Kural (FAZ-PLANI.md, kritik kural #2): ajanlari basit tut. Emergence
basit kurallarin carpismasindan dogar; her ajan ~50 satir, tek kural
hedefler (Faz 5+).

Faz 5: PnL takibi taban sinifa eklendi -- her ajan otomatik olarak
pozisyon/gerceklesen-kar/anlik-kar takip eder (agirlikli ortalama
maliyet yontemi). Boylece "ajan PnL dagilimi" (Faz 5 'Bitti' kriteri)
her yeni ajan icin bedavaya gelir; alt siniflarin tek isi observe()/
decide()'i doldurmak.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from ..environment.base import Environment, EnvironmentState, Order


class Agent(ABC):
    def __init__(self, agent_id: str) -> None:
        self.agent_id = agent_id
        self.position: float = 0.0
        self.avg_entry_price: float | None = None
        self.realized_pnl: float = 0.0

    @abstractmethod
    def observe(self, state: EnvironmentState) -> None:
        """Cevrenin guncel durumunu (ve ileride ekstra faktorleri) al."""

    @abstractmethod
    def decide(self) -> Optional[Order]:
        """Gozleme dayanarak bir emir uret (veya None -- islem yok)."""

    def act(self, env: Environment) -> None:
        """decide() ciktisini cevreye gonderir. Alt siniflar genelde
        bunu degistirmez; observe/decide'i override eder. Dogrudan
        act() kullanimi PnL takibi YAPMAZ (fiyat callback'i yok) --
        PnL takibi icin Engine, decide()+submit()+on_fill() akisini
        kullanir (bkz. engine/loop.py)."""
        order = self.decide()
        if order is not None:
            env.submit(order)

    def on_fill(self, order: Order, fill_price: float) -> None:
        """Bir emir gerceklestiginde pozisyon/PnL'i gunceller
        (agirlikli ortalama maliyet + gerceklesen kar/zarar).
        Yon degistirme (flip) destekler: once kapatir, kalan miktar
        yeni pozisyon olarak acilir."""
        signed = order.size if order.side == "buy" else -order.size

        if self.position == 0 or self.avg_entry_price is None:
            self.position = signed
            self.avg_entry_price = fill_price
            return

        same_direction = (self.position > 0) == (signed > 0)
        if same_direction:
            new_position = self.position + signed
            self.avg_entry_price = (
                self.avg_entry_price * abs(self.position) + fill_price * abs(signed)
            ) / abs(new_position)
            self.position = new_position
            return

        direction = 1.0 if self.position > 0 else -1.0
        closing_size = min(abs(signed), abs(self.position))
        self.realized_pnl += closing_size * direction * (fill_price - self.avg_entry_price)

        remainder = abs(signed) - closing_size
        self.position += signed
        if self.position == 0:
            self.avg_entry_price = None
        elif remainder > 0:
            # pozisyon yon degistirdi (flip); yeni pozisyonun maliyeti bu fiyat
            self.avg_entry_price = fill_price

    def unrealized_pnl(self, current_price: float) -> float:
        if self.position == 0 or self.avg_entry_price is None:
            return 0.0
        direction = 1.0 if self.position > 0 else -1.0
        return abs(self.position) * direction * (current_price - self.avg_entry_price)

    def total_pnl(self, current_price: float) -> float:
        return self.realized_pnl + self.unrealized_pnl(current_price)
