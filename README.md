# cas-market-simulator

Entegrasyon + CAS (Karmaşık Uyarlanabilir Sistem) simülasyon katmanı.
Mimari ve gerekçe için [`PLAN.md`](PLAN.md), faz haritası için
[`FAZ-PLANI.md`](FAZ-PLANI.md), ortak sözleşmeler için
[`prompts/00-ORTAK-SOZLESME.md`](prompts/00-ORTAK-SOZLESME.md).

## Durum: Faz 0 + Faz 1 + Faz 2 + Faz 3 + Faz 4 tamamlandı

Faz 0: boru hattı uçtan uca bağlı. Faz 1: signalcore artık gerçek bir
"beyin" — 6 bağımsız faktör + rejim yönlendirme + risk motoru + tam
doğrulama iskeleti. Faz 2: formasyoncu — mum + grafik formasyonları
tespit ediliyor. Faz 3: üç bileşen tek karta akıyor + forward-test
omurgası (paper execution + journal) kuruldu. Faz 4: 5 yeni sensör
(derivatives, orderbook, onchain, intermarket, cross_exchange) düşük
ağırlıkla karta oy veriyor (182/182 test yeşil).

**Önemli kısıt:** Bu oturumda yalnızca `cas-market-simulator` klasörüne
erişim vardı — `macro-sentiment-agent` ve `microstructure-analyzer`
repolarına erişilemedi. Bu yüzden Faz 3'teki `SimSentimentFeed`/
`SimFlowFeed`, o repoların GERÇEK kodunu sarmıyor; aynı `SentimentFeed`/
`FlowFeed` Protocol'üne uyan, deterministik mean-reverting sentetik
süreçlerle üretilmiş yer tutuculardır. Gerçek repolara erişim
sağlandığında bu iki dosyadaki sınıflar, Protocol imzası korunarak,
gerçek simülasyon modlarına bağlanacak şekilde değiştirilmelidir.

```
cas_market_simulator/
  adapters/       contracts.py (SentimentState, ShockEvent, FlowState,
                   FactorVote, PatternHit, Card + Protocol'ler)
                   bars.py (Environment tick geçmişi -> signalcore OHLCVBar)
                   sentiment_feed.py / flow_feed.py: Stub* (Faz 0, sabit) +
                     Sim* (Faz 3, deterministik mean-reverting süreç —
                     gerçek repo yerine geçici yer tutucu, yukarıdaki kısıtı oku)
                   factor_brain.py: StubFactorBrain (Faz 0) +
                     SignalCoreFactorBrain (Faz 3 — gerçek signalcore.brain'i
                     sarar, extra_factors'u düşük ağırlıkla çevirir)
  environment/     minimal Environment: emir -> fiyat etkisi -> tick
  agents/          Agent taban sınıfı (observe/decide/act) + NoopAgent
  engine/          senkron tick döngüsü (Engine, SimulationConfig) —
                   artık her tick'te gerçek OHLCV bar üretip brain'e veriyor,
                   Journal + PaperExecutor'u tetikliyor
  analysis/        execution.py (PaperExecutor: slipaj+komisyon modeli),
                   journal.py (forward-test defteri: sinyal -> N tick sonra
                   sonuç, win_rate/avg_pnl_pct)
  tests/           55 test (contracts, environment, agents, feed'ler,
                   bars/factor_brain adaptörleri, execution, journal, e2e)

signalcore/        yeni indikatör+formasyon motoru
  core/
    types.py        FactorVote, PatternHit, Card, OHLCVBar
    ohlcv.py         bar doğrulama + to_arrays yardımcısı
    registry.py      faktör kayıt + ağırlık tablosu
  feeds.py           rejim-anahtarlamalı GBM sentetik OHLCV üreteci
  indicators/        _math.py (paylaşılan saf-numpy formüller) +
                      trend, momentum, volatility, meanrev, volume, structure
                      (her biri saf fonksiyon: bars -> FactorVote)
  combine/           aggregator.py (vote×weight → yön+güven),
                      regime_router.py (Hurst/ER → trend↔MR ağırlık yönlendirme,
                      RANDOM rejimde güven kısma), registry_setup.py
  risk/              sizing.py (yarım-Kelly boyutlandırma),
                      levels.py (ATR-stop/TP/geçersizlik)
  validation/        walkforward.py (nedensel/causal değerlendirme),
                      leakage.py (gelecek-veri sızıntısı + belirlenimcilik testi),
                      factor_tracker.py (IC/hit-rate defteri — ağırlık artışı
                      buradan pozitif katkı olmadan verilmez),
                      conformal.py (split-conformal belirsizlik bandı)
  patterns/          candles.py (engulfing, hammer/shooting-star, doji,
                      morning/evening star), chart.py (double top/bottom,
                      triangle, omuz-baş-omuz, bayrak/kama — swing-point
                      geometrisine dayalı, parametrik), levels.py
                      (destek/direnç, pivot, likidite seviyeleri),
                      detector.py (hepsini tarar -> list[PatternHit] +
                      tek bir "patterns" oyu)
  indicators/derivatives.py, orderbook.py, onchain.py, intermarket.py,
                      cross_exchange.py: her biri kendi State tipi +
                      Sim*Feed (deterministik sentetik üreteç, gerçek
                      API/RPC yok) + saf factor fonksiyonu.
                      sensors.py: compute_sensor_votes() hepsini tek bir
                      listeye indirger, sabit düşük ağırlık (0.2) ile.
  brain.py           analyze(symbol, bars, extra_factors, sensor_states)
                      -> Card (registry + regime_router + risk +
                      patterns + sensor oyları hepsi burada birleşir)
  tests/             127 test (indicators, aggregator, regime_router,
                      risk, validation, patterns, sensörler, brain uçtan uca)
```

**Not:** `signalcore` uzun vadede ayrı bir repo olarak planlanmıştı
(bkz. `prompts/03-...md`), ama bu oturumda yalnızca `cas-market-simulator`
klasörüne erişim vardı; bu yüzden şimdilik bu repo içinde bağımsız bir
alt-paket olarak duruyor. `cas_market_simulator` içindeki hiçbir modül
`signalcore`'un iç modüllerine doğrudan bağlı değil — yalnızca
`adapters/contracts.py`'deki ortak sözleşme üzerinden konuşacaklar
(Faz 3'te `adapters/factor_brain.py` gerçek `signalcore.brain`'i
saracak). İstenirse `signalcore/` ayrı bir repoya taşınabilir; kod
zaten bağımsız, tek değişiklik import kökünün taşınması olur.

## Çalıştırma

```bash
pip install -r requirements.txt

# testler (182 test, tamamı yeşil)
pytest -q

# Faz 0 demo: stub feed -> ajan -> environment -> log basan tick döngüsü
PYTHONPATH=. python3 scripts/run_faz0_demo.py

# signalcore demo: sentetik OHLCV üret + doğrula
PYTHONPATH=. python3 scripts/run_signalcore_demo.py

# Faz 1/2 demo: brain.analyze() -> Card (faktörler+formasyonlar) + her faktör için walk-forward IC/hit-rate
PYTHONPATH=. python3 scripts/run_signalcore_brain_demo.py

# Faz 3 demo: gerçek SignalCoreFactorBrain + sim sentiment/flow + paper execution + forward-test defteri
PYTHONPATH=. python3 scripts/run_faz3_demo.py
```

## "Bitti" kriteri (FAZ-PLANI.md)

**Faz 0**
- [x] `cas-market-simulator` paket yapısı kuruldu.
- [x] `adapters/contracts.py` ortak sözleşmedeki tüm tipleri + Protocol'leri içeriyor.
- [x] `signalcore/core/types.py`, `ohlcv.py`, `registry.py` + rejim-anahtarlamalı sentetik OHLCV üreteci çalışıyor.
- [x] Stub `SentimentFeed`/`FlowFeed`/`FactorBrain` sahte veri döndürüyor.
- [x] Stub feed → tek boş ajan (`NoopAgent`) → boş `Environment` → log basan tick döngüsü çalışıyor.

**Faz 1**
- [x] 6 düşük-korelasyonlu faktör (trend, momentum, volatility, meanrev, volume, structure) + `aggregator` + `regime_router` + `risk` çalışıyor.
- [x] `validation/` içinde walk-forward + leakage + factor_tracker + conformal çalışıyor ve testli.
- [x] `brain.analyze()` sentetik OHLCV ile uçtan uca `Card` üretiyor (yön, güven, oylar, risk seviyeleri).
- [x] `run_signalcore_brain_demo.py` her faktör için IC/hit-rate/leakage raporu basıyor — kural gereği (factor_tracker'da pozitif katkı olmadan ağırlık artmaz) uygulanıyor: örnek koşuda `volatility` ve `meanrev` negatif IC gösterdiği için ağırlık artışına izin verilmiyor, bu beklenen ve istenen davranış.

**Faz 2**
- [x] `patterns/detector.py` mum formasyonları (engulfing, hammer/shooting-star, doji, morning/evening star) + en az 3 grafik formasyonu (double top/bottom, head&shoulders, triangle, flag/wedge) tespit ediyor.
- [x] Her formasyon parametrik + kurallı, hazırlanmış sentetik zigzag barlarla testli (sezgi kodlanmadı).
- [x] Formasyonlar `Card.patterns`'te görsel liste olarak listeleniyor **ve** `patterns_to_vote()` ile aggregator'a tek bir ek oy olarak giriyor (demo'da görüldüğü gibi bir `inverse_head_and_shoulders` tespiti kartın yönünü SHORT'tan NEUTRAL'a çekti).
- [x] Testler yeşil (135/135 → şimdi Faz 3 ile birlikte 166/166).

**Faz 3**
- [x] `adapters/factor_brain.py::SignalCoreFactorBrain` gerçek `signalcore.brain.analyze()`'i sarıyor; `adapters/bars.py` `Environment` tick geçmişini OHLCV bar'a çeviriyor.
- [x] `adapters/sentiment_feed.py::SimSentimentFeed` + `adapters/flow_feed.py::SimFlowFeed` simülasyon modunda bağlı (deterministik mean-reverting süreçler — gerçek repo erişimi olmadığı için yer tutucu, yukarıdaki kısıtı oku).
- [x] `extra_factors`: flow + sentiment düşük ağırlıkla (0.15) `FactorVote`'a çevrilip signalcore'a giriyor.
- [x] `analysis/execution.py::PaperExecutor` (slipaj+komisyon modeli) + `analysis/journal.py::Journal` (forward-test defteri: sinyal → N tick sonra sonuç, win_rate/avg_pnl_pct) kuruldu ve `Engine`'e bağlandı.
- [x] `run_faz3_demo.py`: 200 tick'lik simülasyonda 53 sinyal çözüldü, defter dürüstçe zarar gösterdi (win_rate=0.26) — bu **beklenen**: rastgele-yürüyüş ajanı + henüz kalibre edilmemiş bir ortamda gerçek bir "edge" iddia edilmiyor, yalnızca borunun uçtan uca ölçüm yaptığı kanıtlanıyor (bkz. FAZ-PLANI.md kural #5: "Simülasyon ≠ kehanet").
- [x] Testler yeşil (166/166 → Faz 4 ile birlikte 182/182).

**Faz 4**
- [x] `signalcore/indicators/derivatives.py` (funding/OI/basis/IV/put-call), `orderbook.py` (spread/derinlik dengesizliği/likidasyon haritası), `onchain.py` (netflow/stablecoin arzı/NVT/ETF akışı), `intermarket.py` (DXY/altın/10Y/S&P/risk-on-off), `cross_exchange.py` (coinbase premium/lead-lag/fiyat farkı) — her biri kendi `State` tipi + gerçek API/RPC gerektirmeyen deterministik `Sim*Feed` + saf factor fonksiyonu.
- [x] `indicators/sensors.py::compute_sensor_votes()` beşini tek listeye indirgeyip sabit düşük ağırlıkla (0.2) `brain.analyze(..., sensor_states=...)`'e bağlıyor.
- [x] `run_signalcore_brain_demo.py` sensörleri de factor_tracker'a kaydediyor: örnek koşuda yalnızca `onchain` ve `cross_exchange` pozitif IC gösterdi, diğer üçü (derivatives/orderbook/intermarket) negatif IC'de kaldığı için ağırlık artışına izin verilmiyor — kural (factor_tracker'da pozitif katkı olmadan ağırlık artmaz) burada da tutarlı uygulanıyor.
- [x] Testler yeşil (182/182).

**Not:** Bu 5 sensör de (Faz 3'teki sentiment/flow gibi) gerçek borsa/zincir/makro veri sağlayıcılarına bu oturumda erişimim olmadığı için deterministik sentetik süreçlerle çalışıyor — gerçek veri kaynakları bağlandığında yalnızca `Sim*Feed` sınıfları değişecek, `*_factor()` fonksiyonları ve `State` sözleşmeleri sabit kalacak şekilde tasarlandı.

## Sıradaki adım: Faz 5

Minimum CAS motoru (Katman 2, 04-B ilk çekirdek) — `agents/momentum.py`,
`agents/market_maker.py`, `agents/panic.py` (her biri ~50 satır, tek
kural; karar kuralları signalcore faktörlerinden ödünç alınacak).
`environment/`'ın microstructure-analyzer'ın simülasyon modunu "çevre"
olarak kullanması gerekiyordu ama o repo bu oturumda erişilebilir
değildi — mevcut basit `Environment` (net emir dengesizliği → fiyat)
bu fazda geçici çevre olarak kullanılmaya devam edecek. Senkron tick
döngüsü zaten hazır (`Engine`); hedef ilk emergence gözlemi — fiyat
serisi + ajan PnL dağılımı (bkz. FAZ-PLANI.md Faz 5).
