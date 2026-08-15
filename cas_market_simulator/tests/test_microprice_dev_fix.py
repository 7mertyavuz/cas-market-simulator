"""microprice_dev olu yolu -- regresyon kilidi.

`to_signalcore_orderbook_state()` uzun sure sunu yapiyordu:

    mid = book.microprice / (1.0 + getattr(book, "microprice_dev", 0.0))
    dev = (book.microprice / mid - 1.0) if mid > 0 else 0.0

`BookState`'te `microprice_dev` diye bir alan HICBIR ZAMAN olmadi. getattr her
seferinde 0.0 donuyordu, o zaman mid = microprice/1.0 = microprice ve
dev = microprice/microprice - 1 = TAM 0.0 oluyordu. Her zaman.
`orderbook_factor` bu bilesenden hicbir katki almiyordu ve hicbir test bunu
yakalamiyordu -- getattr varsayilani cokmeyi onledi ama sessiz bir olu yol
uretti.

Asil eksik `mid` alaniydi. Bu testler hem sapmanin gercekten hesaplandigini
hem de eski desenin geri gelmedigini dogrular.
"""
from __future__ import annotations

import pytest

from cas_market_simulator.adapters.book_feed import (
    SimBookFeed,
    microprice_dev,
    to_signalcore_orderbook_state,
)
from cas_market_simulator.adapters.contracts import BookState


def _book(**kw) -> BookState:
    base = dict(symbol="BTCUSDT", spread_bps=5.0, microprice=30_010.0, mid=30_000.0,
                depth_imbalance=0.5, ofi=1.0, queue_imbalance=0.2,
                book_slope=1.0, kyle_lambda=1e-6)
    base.update(kw)
    return BookState(**base)


def test_deviation_is_actually_computed():
    """Eski kodda bu deger her zaman tam 0.0 idi."""
    dev = microprice_dev(_book(microprice=30_010.0, mid=30_000.0))
    assert dev == pytest.approx(30_010.0 / 30_000.0 - 1.0)
    assert dev != 0.0


def test_deviation_sign_follows_buy_pressure():
    """Mikro-fiyat mid'in USTUNDEyse yukari baski var demektir."""
    assert microprice_dev(_book(microprice=30_010.0, mid=30_000.0)) > 0
    assert microprice_dev(_book(microprice=29_990.0, mid=30_000.0)) < 0


def test_deviation_is_zero_only_when_prices_truly_agree():
    assert microprice_dev(_book(microprice=30_000.0, mid=30_000.0)) == 0.0


def test_missing_mid_degrades_to_zero_without_crashing():
    """Eski bir micro surumu `mid` gondermeyebilir; cokmemeli ama 0 dondurmeli."""
    assert microprice_dev(_book(mid=0.0)) == 0.0


def test_signalcore_state_carries_the_real_deviation():
    """Ucu uca: sapma signalcore'a gercekten ULASMALI."""
    st = to_signalcore_orderbook_state(_book(microprice=30_030.0, mid=30_000.0))
    assert st.microprice_dev == pytest.approx(0.001)
    assert st.microprice_dev != 0.0


def test_sim_feed_produces_varying_nonzero_deviations():
    """Sabit bir mid kullanmak sapmayi yine 0'a kilitlerdi."""
    feed = SimBookFeed(seed=7)
    devs = [microprice_dev(feed.latest("BTCUSDT")) for _ in range(30)]
    assert any(d != 0.0 for d in devs), "sim akisi hep sifir sapma uretiyor"
    assert len(set(devs)) > 5, "sapma degismiyor"


def test_sim_feed_deviation_tracks_depth_imbalance():
    """Stoikov: derinlik alis tarafinda agirsa mikro-fiyat mid'in ustunde oturur."""
    feed = SimBookFeed(seed=3)
    pairs = []
    for _ in range(60):
        b = feed.latest("BTCUSDT")
        pairs.append((b.depth_imbalance, microprice_dev(b)))
    same_sign = sum(1 for di, dv in pairs if di * dv > 0)
    assert same_sign > 0.9 * len([p for p in pairs if p[0] != 0]), (
        "sapmanin isareti derinlik dengesizligini izlemeli")


def test_deviation_is_not_derived_from_itself():
    """Sapma, KENDISINDEN turetilmemeli — eski hatanin ozu buydu.

    Kaynak metni taramak kirilgan (docstring'ler hatanin kaydini tutuyor), o
    yuzden DERLENMIS koda bakiyoruz: `microprice_dev` sabiti artik bu iki
    fonksiyonun hicbirinde bir oznitelik adi olarak gecmemeli.
    """
    for fn in (microprice_dev, to_signalcore_orderbook_state):
        consts = [c for c in fn.__code__.co_consts if isinstance(c, str)]
        assert "microprice_dev" not in consts, (
            f"{fn.__name__} sapmayi yine kendisinden turetiyor")
