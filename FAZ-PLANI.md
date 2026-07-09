# CAS Market Simulator — Ana Faz Planı

**Tarih:** 2026-07-01
**Kapsam:** `03-yeni-indikator-formasyon-motoru` (signalcore) + `04-yeni-agent-onerileri` dosyalarındaki **tüm kalemler** buradaki fazlara dağıtıldı. Referanslar: [`PLAN.md`](PLAN.md), [`prompts/`](prompts/).

## Repo haritası (4 repo — yeni repo yok)
1. `macro-sentiment-agent` — sentiment sensörü + dış şok (var)
2. `microstructure-analyzer` — akış sensörü + MEV/whale/retail şablonu (var)
3. `signalcore` — yeni indikatör+formasyon motoru + sensör modülleri (yeni)
4. `cas-market-simulator` — entegrasyon + simülasyon ajanları (yeni, buradasın)

## Fazların mantığı
Her faz **tek başına değer üretir** ve bir sonrakini besler. Kural: bir fazı bitirmeden diğerine geçme; "önce devasa sistemi kurayım" tuzağına düşme. Sıralama bağımlılığa göre:

```
Faz 0  iskelet + sözleşmeler
Faz 1  signalcore MVP (beyin)            ← 03: indikatörler, combine, validation
Faz 2  formasyoncu (patterns)            ← 03: patterns/
Faz 3  analist çekirdeği + forward-test  ← 04: execution/journal (öncelik #1)
Faz 4  sensör ajanları                   ← 04(A): derivatives, orderbook, onchain, intermarket
Faz 5  minimum CAS motoru                ← 04(B): ilk 3 sim ajanı
Faz 6  emergence + likidasyon kaskadı    ← 04(B): liquidation, whale, mev, arb + shock
Faz 7  geri besleme (iki katman birleşir)
Faz 8  adaptasyon / evrim                ← 04: meta ajanlar
Faz 9  doğrulama & kalibrasyon           ← 04(A): portfolio/risk; 03: CPCV/DSR
```

---

## FAZ 0 — İskelet ve sözleşmeler  *(1–2 gün)*
**Amaç:** boru hatları boş ama uçtan uca bağlı.

- `cas-market-simulator/` paket yapısı: `adapters/`, `environment/`, `agents/`, `engine/`, `analysis/`, `tests/`.
- `adapters/contracts.py` — `00-ORTAK-SOZLESME.md`'deki tipleri koda dök (`SentimentState`, `ShockEvent`, `FlowState`, `FactorVote`, `PatternHit`, `Card`) + Protocol'ler.
- `signalcore/` boş repo: `core/types.py`, `core/ohlcv.py` (bar doğrulama), `core/registry.py`, `feeds.py` içinde **sentetik OHLCV üreteci** (rejim-anahtarlamalı GBM).
- Stub feed'ler: `SentimentFeed`/`FlowFeed`/`FactorBrain` sahte veri döndürür.

**Bitti:** stub feed → tek boş ajan → boş environment → log basan bir tick döngüsü çalışıyor.

---

## FAZ 1 — signalcore MVP: beyin  *(03'ün çekirdeği)*
**Amaç:** signalcore tek başına OHLCV → `Card` üretiyor, doğrulama ayakta.
Sıra kritik — **doğrulama, faktör çoğaltmadan ÖNCE gelir.**

### 1a — İlk uçtan-uca kart
- `indicators/trend.py` (EMA+Supertrend+ADX), `indicators/momentum.py` (RSI/MACD/Connors-RSI), `indicators/volatility.py` (ATR + squeeze).
- `combine/aggregator.py` (vote×weight → yön+güven), `brain.py` (`analyze` → `Card`).

### 1b — Güvenilirlik iskeleti (ATLANAMAZ)
- `validation/walkforward.py`, `validation/leakage.py`, `validation/factor_tracker.py`, `validation/conformal.py`.
- Kural: faktör `factor_tracker`'da pozitif katkı göstermeden ağırlığı artırılmaz.

### 1c — Kalan çekirdek faktörler (her biri testli)
- `indicators/meanrev.py` (Bollinger %B, z-score, OU-spread), `indicators/volume.py` (CMF/OBV/VWAP/hacim-profili POC), `indicators/structure.py` (Hurst/Efficiency-Ratio, fracdiff).

### 1d — Rejim yönlendirici
- `combine/regime_router.py` — Hurst/ER ile trend↔MR ağırlık yönlendirmesi; RANDOM rejimde güveni kıs.

### 1e — Risk motoru
- `risk/sizing.py` (edge/yarım-Kelly), `risk/levels.py` (ATR-stop/TP/geçersizlik). *(kuyruk riski `tail.py` → Faz 9.)*

**Bitti:** 8–12 düşük-korelasyonlu faktör + combine + regime_router + risk çalışıyor; walk-forward/leakage/factor_tracker/conformal yeşil; sentetik OHLCV ile uçtan-uca kart.

---

## FAZ 2 — Formasyoncu (pattern motoru)  *(03'ün patterns/'i)*
**Amaç:** kart formasyon oyu ve görünür geçersizlik seviyesi içeriyor.

- `patterns/candles.py` — engulfing, hammer/shooting-star, doji, morning/evening star.
- `patterns/chart.py` — çift dip/tepe, üçgen (simetrik/yükselen/alçalan), omuz-baş-omuz, bayrak/flama, kama.
- `patterns/levels.py` — destek/direnç, pivot, likidite seviyeleri.
- `patterns/detector.py` — hepsini tarayıp `list[PatternHit]`; combine'a ayrı oy + kartta görsel liste.
- Her formasyon **parametrik + kurallı** (sezgi kodlama yok) ve sentetik örnekle testli.

**Bitti:** mum + en az 3 grafik formasyonu tespit ediliyor, kartta listeleniyor, testli.

---

## FAZ 3 — Analist çekirdeği entegrasyonu + forward-test  *(Katman 1)*
**Amaç:** üç repo tek karta akıyor; forward-test omurgası kuruldu (04'ün #1 önceliği).

- `adapters/factor_brain.py` — signalcore `analyze()` sarmalanır.
- `adapters/sentiment_feed.py` + `adapters/flow_feed.py` — macro & microstructure sim modda bağlanır.
- `extra_factors`: `flow` (microstructure) + `sentiment` (macro) **düşük ağırlıkla** faktör olarak eklenir; çift-sayım riski `factor_tracker` ile ölçülür.
- **execution/journal agent** (04-A #1): `analysis/journal.py` + paper `execution.py` — sinyali paper emre çevir, slipaj/maliyet modeli, forward-test defteri. *Bu olmadan sonraki sensörler gürültüdür.*

**Bitti:** tek sembol için zenginleştirilmiş kart + forward-test defteri işliyor. **Burada durursan bile kullanışlı bir analist var.**

---

## FAZ 4 — Sensör ajanları  *(04-A, signalcore/indicators genişleme)*
**Amaç:** faktör genişliği; her sensör bir `FactorVote`, hepsi `factor_tracker`'a kayıtlı. Öncelik sırasıyla:

1. `indicators/derivatives.py` — funding, OI, basis/contango, opsiyon IV (DVOL), put/call. *(en güçlü erken sinyal)*
2. `indicators/orderbook.py` — CEX derinlik, spread, likidasyon haritası, kitap dengesizliği. *(microstructure DEX tarafını tamamlar)*
3. `indicators/onchain.py` — borsa netflow, stablecoin arzı, aktif adres, NVT, ETF akışı.
4. `indicators/intermarket.py` — DXY, altın, 10Y, S&P, risk-on/off. *(güven çarpanı)*
5. `indicators/cross_exchange.py` — borsalar arası fark, coinbase premium, lead-lag. *(simülasyondaki arbitraj ajanının gerçek-veri karşılığı)*

**Bitti:** 5 yeni sensör kartta oy veriyor, hepsi düşük ağırlıkla girip factor_tracker ile ölçülüyor.

---

## FAZ 5 — Minimum CAS motoru  *(Katman 2, 04-B ilk çekirdek)*
**Amaç:** ilk emergence gözlemi.

- `environment/` — microstructure'ın simülasyon modunu **çevre** olarak kullan (sıfırdan order book yazma); dışarıdan ajan emri kabul eden geri-bildirim döngüsü.
- `agents/base.py` — ortak arayüz: `observe → decide → act`.
- İlk üç ajan (04-B): `agents/momentum.py`, `agents/market_maker.py`, `agents/panic.py`. Her biri ~50 satır, **tek kural** (karar kuralları signalcore faktörlerinden ödünç).
- Senkron tick döngüsü; ajan emirleri çevreyi günceller.

**Bitti:** fiyat serisi + ajan PnL dağılımı üretiliyor; ilk kolektif davranış görülüyor.

---

## FAZ 6 — Emergence zenginleştirme + likidasyon kaskadı  *(04-B geri kalanı + dış şok)*
**Amaç:** flash crash / ralli üretiliyor ve **ölçülüyor**.

- `agents/liquidation_engine.py` — kaldıraç eşiği kırılınca zorunlu sat. **(yıldız ajan — flash crash'i en net üretir, erken ekle.)**
- `agents/whale.py`, `agents/arbitrage.py`, `agents/mev.py` (microstructure `sandwich/jit/arbitrage` mantığı), `agents/news_reactor.py`, `agents/contrarian.py`.
- Dış şok: macro `ShockEvent` akışı çevreye enjekte edilir (magnitude + decay); deterministik senaryo replay ile.
- `analysis/emergence.py` — metrikler: kaskad büyüklüğü, ajan senkronizasyonu, getiri otokorelasyonu, ani-çöküş frekansı.

**Bitti:** scriptli bir şok, ölçülebilir bir kaskad/ralli belirtiyor; emergence metrikleri raporlanıyor.

---

## FAZ 7 — Geri besleme: iki katman birleşir
**Amaç:** simülasyon, analisti besliyor.

- `analysis/emergence.py` çıktısından **crowd-emergence skoru** üret.
- Bu skoru signalcore'a `extra_factors["crowd_emergence"]` olarak yeni faktör (#N) ekle — düşük ağırlık, factor_tracker ölçer.

**Bitti:** "kalabalık çökmeye mi gidiyor?" okuması karttaki bir faktör hâline geldi; iki katman kapalı döngü.

---

## FAZ 8 — Adaptasyon / evrim  *(04 meta ajanlar)*
**Amaç:** senin metnindeki "evrim" mekanizması.

- `agents/adaptive.py` — zarar edince stratejiyi mutasyona uğrat (parametre perturbasyonu / basit GA); kazanan payı artar.
- `agents/regime_switcher.py` — vol rejimine göre momentum↔MR geçişi.
- `agents/herd.py` — en kârlı ajanı taklit (sürü davranışı → balon büyütme).
- Online öğrenme: microstructure `online.py` + drift monitor'u ajan adaptasyonu için ödünç al.

**Bitti:** popülasyon kompozisyonu rejim değişince kayıyor; adaptasyon ölçülüyor.

---

## FAZ 9 — Doğrulama, kalibrasyon, portföy  *(dürüstlük katmanı)*
**Amaç:** simülatör oyuncak değil, güvenilir bir laboratuvar.

- **Kalibrasyon:** üretilen sentetik piyasa stilize gerçeklerle uyumlu mu? (fat tails, vol clustering, leverage effect). Uymuyorsa emergence yanıltıcıdır.
- `signalcore/validation/cpcv.py` + `deflated_sharpe.py` — faktör seti büyüyünce ezber/şans testi.
- `signalcore/risk/tail.py` — CVaR/EVT kuyruk tavanı.
- **risk/portfolio-agent** (04-A): `analysis/portfolio.py` — HRP dağıtım, korelasyon limiti, günlük risk bütçesi (tek sembolden portföye).
- Kural: simülasyondan çıkan hiçbir "alfa" gerçek veride doğrulanmadan kullanılmaz.

**Bitti:** simülasyon kalibre; CPCV/DSR geçen sinyaller; portföy bütçesi işliyor.

---

## FAZ FE — Ortak Frontend & Entegrasyon Dashboard *(yeni)*
**Amaç:** üç reponun ürettiği tüm sinyalleri tek, gerçek zamanlı, etkileşimli ekranda birleştirmek. Sistem "karar destek" konumlandırmasını güçlendirir; yatırım tavsiyesi değildir.

### FE-1 — Merkezi API cephesi
- `cas-market-simulator/api/` altında tek bir FastAPI uygulaması:
  - `GET /v1/card/{symbol}` → signalcore `Card` (yön · güven · risk · oylar · formasyonlar)
  - `GET /v1/flow/{token}` → microstructure-analyzer `FlowState` + `BookState`
  - `GET /v1/sentiment/{entity}` → macro-sentiment-agent `SentimentState`
  - `GET /v1/shocks` → aktif `ShockEvent` listesi
  - `GET /v1/sim/state` → CAS motoru: fiyat, ajan PnL'leri, crowd_emergence_score, kaskad metrikleri
  - `WebSocket /v1/stream` → yukarıdaki tüm durumların anlık güncellemeleri
- Diğer iki repo ile bağlantı önce simülasyon modunda, sonra canlı adapter'larla.

### FE-2 — Ana dashboard ekranları
| Ekran | İçerik | Veri kaynağı |
|---|---|---|
| **Analist Kartı** | Yön, güven, risk, oylar, formasyonlar, stop/TP | signalcore `Card` |
| **Mikroyapı Paneli** | flow_imbalance, VPIN, actor_mix, regime, lead-lag, defter derinliği/heatmap | microstructure-analyzer `FlowState` + `BookState` |
| **Sentiment & Şoklar** | Panik/euphoria/FED tonu, şok olayları, sönüm durumları | macro-sentiment-agent `SentimentState` + `ShockEvent` |
| **CAS Laboratuvarı** | Fiyat serisi, ajan PnL dağılımı, crowd_emergence_score, kaskad replay | `cas-market-simulator` Engine |
| **HITL Kuyruğu** | Yüksek-etki sinyalleri onayla/ret, geri besleme etiketi | macro-sentiment-agent review API |

### FE-3 — Simülasyon kontrol paneli
- Parametre slayderları: ajan sayısı, başlangıç likiditesi, şok magnitude/süresi
- Butonlar: "panik şoku enjekte et", "balina emri gönder", "kaskad replay"
- Senaryo kaydet/yükle: deterministik replay için JSONL import/export
- Ajan ekle/çıkar/duraklat

### FE-4 — Teknoloji ve konumlandırma
- **Frontend:** React + Vite + TypeScript + Recharts/Tremor (modern, tip güvenli)
- **Backend:** `cas-market-simulator` FastAPI (merkez), diğer iki repo zaten FastAPI/WebSocket destekliyor
- **Dağıtım:** tek repo (`cas-market-simulator/ui/`) veya ayrı `cas-market-ui` repo; karar: başlangıçta `cas-market-simulator/ui/` içinde gelişir, gerektiğinde ayrılır
- **İlkeler:** offline-first, simülasyon modu birinci sınıf, yatırım tavsiyesi değildir ibaresi her ekranda

**Bitti:** tek ekranda üç reponun sinyalleri canlı akar; simülasyon kontrol edilebilir; HITL onayları yapılabilir.

---

## Her kalem hangi fazda (03 + 04 izlenebilirlik)

| Kaynak | Kalem | Faz |
|---|---|---|
| 03 | core/types, ohlcv, registry, feeds (sentetik) | 0 |
| 03 | indicators: trend, momentum, volatility | 1a |
| 03 | validation: walkforward, leakage, factor_tracker, conformal | 1b |
| 03 | indicators: meanrev, volume, structure | 1c |
| 03 | combine: aggregator, regime_router | 1a/1d |
| 03 | risk: sizing, levels | 1e |
| 03 | patterns: candles, chart, levels, detector | 2 |
| 03 | brain.py FactorBrain + extra_factors bağlama | 1a/3 |
| 03 | validation: cpcv, deflated_sharpe / risk: tail | 9 |
| 04-A | execution/journal agent | 3 |
| 04-A | derivatives, orderbook, onchain, intermarket, cross-exchange | 4 |
| 04-A | risk/portfolio agent | 9 |
| 04-B | momentum, market-maker, panic | 5 |
| 04-B | liquidation-engine, whale, mev, arbitrage, news-reactor, contrarian | 6 |
| 04 meta | adaptive, regime-switcher, herd + online öğrenme | 8 |
| — | ShockEvent enjeksiyonu + emergence metrikleri | 6 |
| — | crowd-emergence geri besleme | 7 |
| FE | Merkezi API cephesi (`/v1/card`, `/v1/flow`, `/v1/sentiment`, `/v1/stream`) | FE-1 |
| FE | Dashboard ekranları (kart, mikroyapı, sentiment, CAS lab, HITL) | FE-2 |
| FE | Simülasyon kontrol paneli + senaryo replay | FE-3 |
| FE | React + Vite UI iskeleti | FE-4 |

---

## Kritik kurallar (her fazda geçerli)
1. **Doğrulama faktörden önce.** factor_tracker pozitif demeden ağırlık artmaz.
2. **Ajanları basit tut.** Emergence basit kuralların çarpışmasından doğar.
3. **Çift sayım.** Dış sinyaller düşük ağırlıkla girer, defter konuşur.
4. **Her faz tek başına değer.** Faz 3'te durabilirsen bile elde kullanışlı analist var.
5. **Simülasyon ≠ kehanet.** Kalibre etmeden ondan ticari karar üretme.
6. **Simülasyon modu birinci sınıf.** Geliştirmeyi API/RPC olmadan yap.

## Sonraki adım
Faz 0–9 temel olarak tamamlandı; sıradaki büyük hamle **Faz FE — Ortak Frontend**. Onayınla `cas-market-simulator/ui/` altında React + Vite + TypeScript iskeletini kurar, ardından `api/main.py` üzerinden `/v1/card`, `/v1/flow`, `/v1/sentiment`, `/v1/shocks` ve `/v1/stream` WebSocket uçlarını açarım. İlk ekran "Analist Kartı" olur; simülasyon kontrol paneli ve HITL kuyruğu peşine eklenir.
