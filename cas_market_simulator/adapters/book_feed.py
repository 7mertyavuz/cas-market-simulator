"""BookFeed adaptoru.

microstructure-analyzer'daki `BookFeed`'i sarar ve simulatorun
`BookState` sozlesmesine cevirir. Sim modu birinci siniftir -- harici
baglanti/anahtar olmadan deterministik L2 defter uretir.
"""
from __future__ import annotations

from datetime import datetime, timezone

from .contracts import BookState


def microprice_dev(book: BookState) -> float:
    """Stoikov mikro-fiyatin orta noktadan sapmasi: (microprice - mid)/mid.

    Yonlu bir sinyaldir: pozitif sapma, derinligin alis tarafinda yogunlastigini
    yani yukari baskiyi gosterir.

    BU FONKSIYON BIR HATANIN DUZELTMESIDIR. Onceki hali soyleydi:

        mid = book.microprice / (1.0 + getattr(book, "microprice_dev", 0.0))
        dev = (book.microprice / mid - 1.0) if mid > 0 else 0.0

    `BookState`'te `microprice_dev` diye bir alan hicbir zaman OLMADI, dolayisiyla
    getattr her seferinde 0.0 donuyordu; o zaman mid = microprice / 1.0 = microprice
    ve dev = microprice/microprice - 1 = TAM OLARAK 0.0 oluyordu. Her zaman.
    `orderbook_factor` bu bilesenden hicbir katki almiyordu ve hicbir test bunu
    yakalamiyordu -- getattr varsayilani cokmeyi onledi ama sessiz bir olu yol
    uretti.

    Asil eksik `mid` alaniydi; artik hem microstructure-analyzer hem de bu repo
    onu sozlesmede tasiyor.
    """
    mid = float(getattr(book, "mid", 0.0) or 0.0)
    if mid <= 0.0 or book.microprice <= 0.0:
        return 0.0
    return book.microprice / mid - 1.0


def to_signalcore_orderbook_state(book: BookState):
    """cas-market-simulator BookState -> signalcore OrderbookState."""
    from signalcore.indicators.orderbook import OrderbookState as SCOrderbookState

    dev = microprice_dev(book)
    return SCOrderbookState(
        spread_bps=book.spread_bps,
        depth_imbalance=book.depth_imbalance,
        liquidation_map_skew=book.liq_map_skew,
        microprice_dev=dev,
        ofi=book.ofi,
        spoof_score=book.spoof_score,
        absorption=book.absorption,
        iceberg_score=book.iceberg_score,
    )


def _convert_micro_book(src) -> BookState:
    """microstructure-analyzer `src.book.state.BookState` -> simulator
    `BookState`. Alan adlari birebir eslestigi icin bu yalnizca siniflar
    arasi gevsek baglama katidir.
    """
    return BookState(
        symbol=src.symbol,
        spread_bps=src.spread_bps,
        microprice=src.microprice,
        # Sozlesmenin yeni alani; eski bir micro surumu icin getattr ile tolere
        # edilir ama o durumda sapma yine 0 kalir (ve bu artik bilinen bir sey).
        mid=float(getattr(src, "mid", 0.0) or 0.0),
        depth_imbalance=src.depth_imbalance,
        ofi=src.ofi,
        queue_imbalance=src.queue_imbalance,
        book_slope=src.book_slope,
        kyle_lambda=src.kyle_lambda,
        iceberg_score=src.iceberg_score,
        spoof_score=src.spoof_score,
        absorption=src.absorption,
        liq_map_skew=src.liq_map_skew,
        ts=src.ts if isinstance(src.ts, datetime) else datetime.now(timezone.utc),
    )


class StubBookFeed:
    """BookFeed Protocol'unu implemente eden sabit yer tutucu."""

    def latest(self, symbol: str) -> BookState:
        return BookState(
            symbol=symbol,
            spread_bps=5.0,
            microprice=30_000.0,
            mid=30_000.0,
            depth_imbalance=0.0,
            ofi=0.0,
            queue_imbalance=0.0,
            book_slope=1.0,
            kyle_lambda=1e-6,
            iceberg_score=0.0,
            spoof_score=0.0,
            absorption=0.0,
            liq_map_skew=0.0,
            ts=datetime.now(timezone.utc),
        )


class SimBookFeed:
    """Basit mean-reverting BookState uretici (test/demo)."""

    def __init__(self, seed: int | None = 13) -> None:
        import numpy as np

        self._rng = np.random.default_rng(seed)
        self._depth_imbalance = 0.0
        self._spread_bps = 5.0

    def latest(self, symbol: str) -> BookState:
        self._depth_imbalance = max(
            -1.0, min(1.0, self._depth_imbalance + self._rng.normal(0, 0.1))
        )
        self._spread_bps = max(1.0, self._spread_bps + self._rng.normal(0, 0.5))
        mid = 30_000.0 + self._rng.normal(0, 10.0)
        # Mikro-fiyat mid'den derinlik dengesizligi yonunde sapar (Stoikov):
        # alis tarafi agirsa mikro-fiyat mid'in ustunde oturur. Sabit bir mid
        # kullanmak sapmayi yine 0'a kilitlerdi.
        half_spread = mid * self._spread_bps / 1e4 / 2.0
        return BookState(
            symbol=symbol,
            spread_bps=self._spread_bps,
            microprice=mid + half_spread * self._depth_imbalance,
            mid=mid,
            depth_imbalance=self._depth_imbalance,
            ofi=self._rng.normal(0, 5.0),
            queue_imbalance=self._depth_imbalance * 0.8,
            book_slope=max(0.1, 1.0 + self._rng.normal(0, 0.2)),
            kyle_lambda=max(1e-7, 1e-6 + self._rng.normal(0, 1e-7)),
            iceberg_score=max(0.0, min(1.0, self._rng.normal(0.2, 0.1))),
            spoof_score=max(0.0, min(1.0, self._rng.normal(0.1, 0.05))),
            absorption=max(-1.0, min(1.0, self._rng.normal(0, 0.2))),
            liq_map_skew=max(-1.0, min(1.0, self._rng.normal(0, 0.3))),
            ts=datetime.now(timezone.utc),
        )


class MicrostructureBookFeed:
    """Gercek microstructure-analyzer BookFeed sarici."""

    def __init__(self, **kwargs) -> None:
        # Paket adi `src` -> `lob_microstructure` olarak degisti (genel bir ad
        # olan `src` baska projelerle cakisiyordu).
        from lob_microstructure.book.feed import BookFeed as _BookFeed

        self._feed = _BookFeed(**kwargs)

    def latest(self, symbol: str) -> BookState:
        return _convert_micro_book(self._feed.latest(symbol))
