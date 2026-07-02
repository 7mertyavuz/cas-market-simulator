# Sıfırdan Prompt — Yeni İndikatör + Formasyon Motoru (KatanaFlow'un yerine)

> Bu prompt'u **yeni, boş bir repo**'da çalışan AI kodlama asistanına ver. Amaç: hibrit CAS sisteminin "beyin/faktör kütüphanesi"ni sıfırdan, temiz kurmak. Kod adı placeholder: **`signalcore`** (istediğin gibi değiştir).

---

## 0. Bu motorun hibrit sistemdeki rolü
İki işi var:
1. **Analist çekirdeği (Katman 1) — FactorBrain:** OHLCV + dış faktörlerden (flow, sentiment, crowd-emergence) tek bir **analiz kartı** (`Card`) üretir: yön + güven + faktör oyları + formasyonlar + risk.
2. **Simülasyon (Katman 2) — ajan kural kütüphanesi:** Tek tek faktör fonksiyonları, simülatördeki sentetik ajanların basit karar kuralları olarak yeniden kullanılır.

Sözleşmeler: bkz. `00-ORTAK-SOZLESME.md` (`FactorVote`, `PatternHit`, `Card`, `FactorBrain`).

---

## 1. ÖNCE OKU — neden sıfırdan ve neyi kaybediyorsun
KatanaFlow'u indikatör/formasyon için bırakıyorsun. Onun **asıl değeri indikatörler değildi** — herkeste var. Asıl değeri **güvenilirlik disiplini**ydi: CPCV+PBO (ezber mi?), Deflated Sharpe (şans mı?), conformal belirsizlik, leakage testi, factor_tracker, drift monitor, walk-forward. Sıfırdan yazarsan bunları da kaybedersin ve **overfit bir oyuncak** elde etme riskin yüksek.

**Zorunlu kural:** İndikatör/formasyon yığınını yazarken, en baştan minimum bir doğrulama iskeleti de kur (bkz. Bölüm 6). "Önce 50 indikatör yazarım, doğrulamayı sonra eklerim" = klasik tuzak. Doğrulama olmadan üretilen "yön oyu" gürültüdür.

---

## 2. Mimari ve modül yapısı
```
signalcore/
  core/
    types.py          # FactorVote, PatternHit, Card (ortak sözleşme)
    ohlcv.py          # veri tipi + doğrulama (eksik/çakışık bar tespiti)
    registry.py       # faktör kayıt + ağırlık tablosu
  indicators/         # her dosya = bir faktör, saf fonksiyon: (ohlcv, ...) -> FactorVote
    trend.py          # EMA/Supertrend/ADX/Ichimoku trend durumu
    momentum.py       # RSI/ROC/Connors-RSI/MACD
    meanrev.py        # Bollinger %B, z-score, OU-spread
    volatility.py     # ATR, squeeze (BB-Keltner), realized vol rejimi
    volume.py         # CMF, OBV, hacim-profili POC/VAH/VAL, VWAP sapması
    structure.py      # Hurst/Efficiency-Ratio (trend mi MR mi), fracdiff
  patterns/           # "formasyoncu"
    candles.py        # engulfing, hammer, doji, star (mum formasyonları)
    chart.py          # double top/bottom, triangle, H&S, flag, wedge
    levels.py         # destek/direnç, pivot, likidite seviyeleri
    detector.py       # hepsini tarayıp list[PatternHit] döndürür
  combine/
    aggregator.py     # FactorVote'ları ağırlıklı birleştir -> yön + güven
    regime_router.py  # rejim (trend/MR/random) ağırlıkları yönlendirir
  risk/
    sizing.py         # edge/yarım-Kelly pozisyon boyutu
    levels.py         # ATR-stop, TP, geçersizlik
    tail.py           # CVaR/EVT kuyruk tavanı
  validation/         # GÜVENİLİRLİK (Bölüm 6 — atlanamaz)
    walkforward.py
    cpcv.py
    deflated_sharpe.py
    conformal.py
    leakage.py
    factor_tracker.py
  brain.py            # FactorBrain: analyze(symbol, ohlcv, extra_factors) -> Card
  feeds.py            # OHLCV çekme (ccxt/yfinance) + simülasyon/sentetik üreteç
  cli.py              # ince CLI sarmalayıcı
  tests/
```

**Tasarım ilkeleri:** Her faktör saf fonksiyon (yan etkisiz, OHLCV girer, `FactorVote` çıkar) → hem combine'da hem ajan kuralı olarak çağrılabilir. Ağ erişimi yalnızca `feeds.py`'de. Sentetik/simülasyon modu birinci sınıf (OHLCV üretebilen bir GBM/rejim-anahtarlamalı üreteç).

---

## 3. İndikatör/faktör seti (MVP — az ama doğrulanmış)
KatanaFlow'un 33 faktörünü kopyalama hatasına düşme. **8–12 bağımsız, düşük-korelasyonlu faktörle başla**, her birini doğrula, işe yarayanı tut:

| Faktör | Eksen | Not |
|---|---|---|
| Trend (EMA+Supertrend) | trend | Yön omurgası |
| ADX/efficiency | trend gücü | Yön vermez, güven çarpanı |
| RSI/Connors-RSI | momentum/MR | Rejim-kapılı (trendle savaşma) |
| MACD | momentum | |
| Bollinger %B + Squeeze | MR/volatilite | Sıkışma→kırılım |
| ATR rejimi | volatilite | Boyut/güven çarpanı |
| CMF/OBV | hacim | İmzalı birikim/dağıtım |
| Hacim profili (POC) | yapı | Değer alanı |
| Hurst/ER | rejim | trend↔MR yönlendirici |
| (dış) Flow | akış | microstructure `FlowState` |
| (dış) Sentiment | anlatı | macro `SentimentState` |
| (dış) Crowd-emergence | CAS | simülasyondan geri besleme |

> Faktör eklemek `registry.py`'de bir satır olmalı; çekirdek değişmemeli (KatanaFlow'un en doğru tasarım kararı buydu).

## 4. Formasyon (pattern) motoru
- **Mum formasyonları:** engulfing, hammer/shooting-star, doji, morning/evening star.
- **Grafik formasyonları:** çift dip/tepe, üçgen (simetrik/yükselen/alçalan), omuz-baş-omuz, bayrak/flama, kama.
- Her tespit `PatternHit(name, direction, strength, invalidation)` döndürür; `invalidation` formasyonun bozulduğu fiyat (görünür stop seviyesi).
- Formasyonlar combine'a ayrı bir oy ekler **ve** kartta görsel olarak listelenir.
- Dikkat: grafik formasyon tespiti subjektiftir; kurallı + parametrik yaz, "gözle gördüm" sezgisini kodlama. Her formasyon için bir testte sentetik örnekle doğrula.

## 5. Combine (birleştirme) ve kart
- `aggregator`: `vote × weight` ağırlıklı toplam → `[-1,+1]` → LONG/SHORT/NEUTRAL + güven.
- `regime_router`: Hurst/ER ile trend vs MR faktör ağırlıklarını yönlendir; RANDOM rejimde güveni kıs.
- `brain.analyze(symbol, ohlcv, extra_factors)` → `Card`: yön, güven, `votes`, `patterns`, `risk`.
- `extra_factors` üç dış sinyali (flow/sentiment/crowd_emergence) düşük başlangıç ağırlığıyla faktör olarak ekler.

## 6. GÜVENİLİRLİK — atlanamaz (KatanaFlow'dan taşınması gereken asıl değer)
En azından bunları MVP'de kur (sıfırdan yaz ya da KatanaFlow'un ilgili saf-numpy modüllerini lisansına uygun şekilde ödünç al):
- **walk-forward** değerlendirme (look-ahead yok).
- **leakage testi** (özellik geleceğe bakıyor mu?).
- **factor_tracker:** her faktörün forward sonuçlardaki gerçek katkısını ölç → ağırlıkları sezgiyle değil **defterle** ayarla.
- **conformal** belirsizlik bandı (tahmine ne kadar güvenmeli).
- İleri: CPCV+PBO, Deflated Sharpe (faktör seti büyüyünce).

> Kural: Bir faktör, `factor_tracker`'da pozitif katkı göstermeden ağırlığı artırılmaz. Yeni faktör düşük ağırlıkla girer, defter konuşur.

## 7. Kısıtlar
- Bağımlılık minimal: numpy/pandas zorunlu; ccxt/yfinance yalnız `feeds.py`. ML opsiyonel ve ayrı (MVP'de şart değil).
- Simülasyon modu API gerektirmez.
- Konum: "karar destek / araştırma — yatırım tavsiyesi değildir."
- Her faktör + her formasyon için en az bir test (sentetik veriyle beklenen oy).

## 8. Tanım: bitti sayılır (MVP)
- [ ] 8–12 faktör + `registry` + `aggregator` + `regime_router` çalışıyor.
- [ ] `patterns/detector` mum + en az 3 grafik formasyonu tespit ediyor (testli).
- [ ] `brain.analyze()` ortak sözleşmeye uygun `Card` döndürüyor; `extra_factors` bağlı.
- [ ] `validation/` içinde walk-forward + leakage + factor_tracker + conformal çalışıyor.
- [ ] Simülasyon modu sentetik OHLCV üretip uçtan uca kart çıkarıyor.
- [ ] Testler yeşil; README + "cas-market-simulator entegrasyonu" yazıldı.

## 9. İlk iki gün için sıra
1. `core/types.py` + `ohlcv.py` + `registry.py` + sentetik OHLCV üreteci.
2. 3 faktör (trend, momentum, volatilite) + `aggregator` + `brain` → ilk uçtan-uca kart.
3. `validation/walkforward` + `leakage` + `factor_tracker` iskeleti (faktör eklemeden ÖNCE).
4. Sonra kalan faktörler + formasyonlar, her biri testli ve factor_tracker'a kayıtlı.
