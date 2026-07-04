<div align="center">

# 🧠 cas-market-simulator

**Karmaşık Uyarlanabilir Sistem (CAS) tabanlı piyasa simülatörü**
_İki katman: sinyal beyni (`signalcore`) + çok-ajanlı piyasa ekosistemi — bir dürüstlük katmanıyla mühürlenmiş._

<br/>

![tests](https://img.shields.io/badge/tests-314%20passing-2ea44f?style=flat-square)
![python](https://img.shields.io/badge/python-3.11%2B-3776ab?style=flat-square&logo=python&logoColor=white)
![deps](https://img.shields.io/badge/deps-NumPy%20only-013243?style=flat-square&logo=numpy&logoColor=white)
![no external APIs](https://img.shields.io/badge/offline-first-6f42c1?style=flat-square)
![phases](https://img.shields.io/badge/roadmap-Faz%200→9%20✓-orange?style=flat-square)
![license](https://img.shields.io/badge/license-MIT-black?style=flat-square)

</div>

---

> ⚠️ **Araştırma / PoC — yatırım tavsiyesi değildir.** Simülasyon ≠ kehanet.
> Amaç bir "alfa" iddiası değil; basit kuralların çarpışmasından **ortaya çıkan
> (emergent)** davranışı ölçülebilir ve dürüst biçimde gözlemlemektir.

---

## 🎯 Ne işe yarar?

Piyasalar birbirini gözleyen, birbirine tepki veren binlerce basit aktörün
kolektif sonucudur — yani klasik bir **karmaşık uyarlanabilir sistem**. Bu repo
o sistemi iki katmanda modeller:

| Katman | Rol | Sorduğu soru |
|:--|:--|:--|
| 🧩 **`signalcore`** | Sinyal beyni — indikatör + formasyon + rejim + risk | *"Şu an ne alınmalı/satılmalı?"* |
| 🐜 **CAS Motoru** | Çok-ajanlı ekosistem — momentum, balina, likidasyon, panik… | *"Bu aktörler bir arada neyi doğurur?"* |

Bu iki katman **kapalı bir döngüdür**: ajan popülasyonunun ürettiği kolektif
davranış (`crowd_emergence`) beyne bir faktör olarak geri beslenir — beyin
kalabalığı okur, kalabalık fiyatı hareket ettirir, fiyat beyni besler.

---

## 🌐 Büyük resim — hibrit CAS ekosistemi

Bu simülatör üç bağımsız reponun buluştuğu **merkezdir**. Diğer ikisi birer
"duyu organı"; simülatör bunları yalnızca **veri sözleşmeleri** üzerinden okur
(kod bağımlılığı yok).

```mermaid
flowchart LR
    subgraph MICRO["🔬 microstructure-analyzer"]
        direction TB
        M1["Mempool → decode → aktör etiketi<br/>OFI · VPIN · MEV tespiti"]
    end
    subgraph MACRO["📰 macro-sentiment-agent"]
        direction TB
        S1["Haber · Fed · Sosyal → NLP<br/>panic / euphoria / fed-tone"]
    end
    subgraph SIM["🧠 cas-market-simulator (bu repo)"]
        direction TB
        B["signalcore beyni"]
        E["CAS ajan motoru"]
        B <--> E
    end

    M1 -- "FlowState<br/>(akış/toksisite)" --> SIM
    S1 -- "SentimentState + ShockEvent<br/>(duyarlılık/şok)" --> SIM
    SIM -- "Card<br/>(yön · güven · risk)" --> OUT["📊 Karar Kartı"]

    style SIM fill:#1f2937,stroke:#f59e0b,stroke-width:2px,color:#fff
    style MICRO fill:#0f3d3e,stroke:#2dd4bf,color:#fff
    style MACRO fill:#3b0764,stroke:#c084fc,color:#fff
    style OUT fill:#064e3b,stroke:#34d399,color:#fff
```

| Repo | Üretir | Sözleşme tipi |
|:--|:--|:--|
| 🔬 [`microstructure-analyzer`](../microstructure-analyzer) | DEX akış mikroyapısı, MEV, aktör karışımı | `FlowState` |
| 📰 [`macro-sentiment-agent`](../macro-sentiment-agent) | Haber/Fed/sosyal duyarlılık + dışsal şok | `SentimentState`, `ShockEvent` |
| 🧠 **cas-market-simulator** | Sinyal beyni + ajan ekosistemi + dürüstlük | `FactorVote`, `PatternHit`, `Card` |

> Tüm tipler `cas_market_simulator/adapters/contracts.py` içinde `Protocol`
> olarak sabittir. Her bileşen kendi reposunda gelişir; buluşma noktası yalnızca
> bu sözleşmedir (gevşek bağlılık).

---

## 🏗️ İç mimari — iki katmanlı kapalı döngü

```mermaid
flowchart TD
    FEED["FlowFeed + SentimentFeed<br/>(sim/gerçek)"] --> BRAIN

    subgraph BRAIN["🧩 signalcore beyni — brain.analyze()"]
        direction TB
        F["6 çekirdek faktör<br/>trend·momentum·vol·meanrev·volume·structure"]
        SENS["5 sensör<br/>derivatives·orderbook·onchain·intermarket·cross-exchange"]
        PAT["formasyon dedektörü<br/>mum + grafik formasyonları"]
        RR["rejim yönlendirici<br/>Hurst/ER → trend↔MR ağırlık"]
        F & SENS & PAT --> AGG["aggregator<br/>(vote × weight)"]
        AGG --> RR --> RISK["risk motoru<br/>yarım-Kelly · ATR stop/TP · kuyruk tavanı"]
    end

    RISK --> CARD["📇 Card<br/>yön · güven · oylar · risk"]

    subgraph CAS["🐜 CAS ajan motoru — Engine._tick()"]
        direction TB
        POP["12+ ajan popülasyonu"]
        ENV["Environment<br/>emir → fiyat etkisi → OHLCV"]
        POP -->|emirler| ENV
        ENV -->|fiyat| POP
        ENV --> EMER["emergence metrikleri<br/>kaskad · senkron · otokorelasyon"]
    end

    CARD -.-> POP
    ENV --> BARS["OHLCV bar geçmişi"] --> BRAIN
    EMER -->|"crowd_emergence_score<br/>[-1,+1]"| BRAIN

    style BRAIN fill:#111827,stroke:#60a5fa,color:#fff
    style CAS fill:#111827,stroke:#f472b6,color:#fff
    style CARD fill:#064e3b,stroke:#34d399,color:#fff
    style EMER fill:#7c2d12,stroke:#fb923c,color:#fff
```

**Geri besleme döngüsü (Faz 7):** her tick'te son 60 tick'ten
`crowd_emergence_score` hesaplanır → beyne düşük ağırlıklı bir faktör olarak
girer → beyin kararı ajanları etkiler → ajanlar fiyatı hareket ettirir → döngü
kapanır.

---

## 🐜 Ajan ekosistemi

Her ajan **tek kural, ~50–90 satır**. Zenginlik kuralların basitliğinden değil,
etkileşimlerinden doğar.

| Ajan | Davranışı | Rolü |
|:--|:--|:--|
| `MomentumAgent` | Yükseliyorsa al | Trend / balon büyütücü |
| `MarketMakerAgent` | İki yönlü kotasyon; vol artınca çekil | Likidite / denge |
| `PanicAgent` | Doğrulanmış düşüşte gecikmeli sat | Aşağı kaskad tetikleyici |
| `LiquidationEngineAgent` | Kaldıraçlı havuz; eşik kırılınca zorunlu kapat | 💥 **Kaskadın yıldızı** |
| `WhaleAgent` | Büyük, seyrek, yön belirleyici emirler | Şok kaynağı |
| `ArbitrageAgent` | Referans fiyata yakınsa | Ortalama-döndürücü |
| `MevAgent` | Kısa-vade momentumu büyüt (sandwich analogu) | Mikro-yağmacı |
| `NewsReactorAgent` | `ShockEvent`'e tepki + üssel sönüm | Makro köprüsü |
| `ContrarianAgent` | Aşırı uzamada ters pozisyon | Denge / fitil |
| `AdaptiveAgent` | Zarar edince parametre mutasyonu | 🧬 Tek-ajan evrimi |
| `RegimeSwitcherAgent` | Verimlilik oranıyla trend↔MR geçişi | Uyarlanma |
| `HerdAgent` | En kârlı ajanı taklit et | 🐑 Sürü / balon |

---

## 🛡️ Dürüstlük katmanı (Faz 9)

Bir simülatörün en tehlikeli yanı kendini kandırabilmesidir. Bu katman, üretilen
her sinyali **aşırı-uyum ve şansa karşı** sınar:

```mermaid
flowchart LR
    STRAT["Strateji"] --> CPCV["CPCV<br/>Combinatorial Purged CV"]
    STRAT --> DSR["Deflated Sharpe<br/>çoklu-deneme cezası"]
    STRAT --> TAIL["Kuyruk riski<br/>VaR · CVaR · Hill/EVT"]
    STRAT --> CAL["Kalibrasyon<br/>stylized facts"]
    CPCV & DSR & TAIL & CAL --> V{"Gerçek edge var mı?"}
    V -->|"naif MA-kesişim"| NO["❌ %87 negatif skor · DSR≈0<br/>DOĞRU ŞEKİLDE reddedildi"]
    V -->|"gerçek strateji"| YES["✅ düşük negatif oran · DSR≥0.95"]

    style NO fill:#7f1d1d,stroke:#ef4444,color:#fff
    style YES fill:#064e3b,stroke:#34d399,color:#fff
```

Demo'daki naif strateji bilerek zayıftır — **katmanın çalıştığını kanıtlamak
için**. `portfolio.py` ayrıca scipy'siz sıfırdan **HRP** (Hierarchical Risk
Parity) + korelasyon limiti + günlük risk bütçesi ölçeklendirmesi sağlar.

---

## 🗺️ Yol haritası — Faz 0 → 9

| Faz | Başlık | Öne çıkan | Test |
|:--:|:--|:--|:--:|
| 0️⃣ | İskelet | Uçtan uca boru hattı bağlı | ✅ |
| 1️⃣ | Beyin | 6 faktör + rejim + risk + doğrulama | ✅ |
| 2️⃣ | Formasyoncu | Mum + grafik formasyonları | ✅ |
| 3️⃣ | Omurga | Gerçek `SignalCoreFactorBrain` + paper exec + journal | ✅ |
| 4️⃣ | Sensörler | 5 yeni düşük-ağırlıklı sensör | ✅ |
| 5️⃣ | CAS başlıyor | Momentum / MM / panik ajanları | ✅ |
| 6️⃣ | Kaskad | +6 ajan + şok → **ölçülen −%23 kaskad** | ✅ |
| 7️⃣ | Kapalı döngü | `crowd_emergence` beyne geri besleniyor | ✅ |
| 8️⃣ | Meta ajanlar | Evrim + rejim geçişi + sürü | ✅ |
| 9️⃣ | Dürüstlük | Kalibrasyon · CPCV · DSR · kuyruk · HRP | ✅ **314/314** |

**Faz 6 vaka çalışması:** tick 100'de scriptli panik şoku → 20 tick'te **−%23
kaskad**, 26 pozisyon likide, ajan senkronizasyonu **0.82**, getiri
otokorelasyonu **+0.78**. Neden izlenebilir: şok → panik/likidasyon → fiyat
çöküşü.

---

## 🚀 Çalıştırma

```bash
pip install -r requirements.txt
pytest -q                                   # 314 test, tamamı yeşil

# Demolar (her biri kendi fazını gösterir):
PYTHONPATH=. python3 scripts/run_faz3_demo.py   # beyin + sim feed + forward-test
PYTHONPATH=. python3 scripts/run_faz6_demo.py   # 9 ajan + panik şoku → kaskad
PYTHONPATH=. python3 scripts/run_faz7_demo.py   # crowd_emergence kartta faktör
PYTHONPATH=. python3 scripts/run_faz8_demo.py   # meta ajanlar → popülasyon kayması
PYTHONPATH=. python3 scripts/run_faz9_demo.py   # dürüstlük katmanı + HRP
```

Tüm çekirdek **saf Python + NumPy** — scipy/sklearn/torch yok, harici API/anahtar
gerekmez. Feed'ler varsayılan olarak deterministik **simülasyon modunda** çalışır.

---

## 📁 Proje yapısı

```
cas_market_simulator/
  adapters/     contracts.py (sözleşme + Protocol'ler) · bars · sentiment/flow feed · factor_brain
  environment/  emir → fiyat etkisi → tick (+ dışsal şok enjeksiyonu)
  agents/       12+ ajan (taban sınıf otomatik PnL takibi yapar)
  analysis/     execution (paper) · journal (forward-test) · emergence · portfolio (HRP)
  engine/       senkron tick döngüsü — beyin + ajanlar + şok + geri besleme
signalcore/
  indicators/   6 çekirdek faktör + 5 sensör (her biri saf: bars → FactorVote)
  patterns/     mum + grafik formasyonları + destek/direnç
  combine/      aggregator · regime_router · registry
  risk/         sizing (yarım-Kelly) · levels (ATR) · tail (VaR/CVaR/Hill/EVT)
  validation/   walkforward · leakage · conformal · calibration · cpcv · deflated_sharpe
  brain.py      analyze(symbol, bars, extra_factors, sensor_states) → Card
```

---

## 🔌 Entegrasyon durumu ve sonraki adım

Bu repo ilk kez, diğer iki reponun **gerçek** kodunun yanında bulunuyor.
Şu an `adapters/sentiment_feed.py` ve `flow_feed.py` içindeki `Sim*Feed`
sınıfları deterministik **yer tutuculardır** — aynı `Protocol`'ü uygulayan ama
gerçek repoları sarmayan sentetik süreçler.

**Sıradaki iş:** bu iki sınıfı, üstteki repoların hâlihazırda offline çalışan
gerçek `FlowFeed` / `SentimentFeed` beslemelerine bağlamak. Sözleşme
(`contracts.py`) sabit kalacak şekilde tasarlandığı için çekirdek mantığa
dokunmak gerekmez. Detaylı yön için: [`PLAN.md`](PLAN.md), [`FAZ-PLANI.md`](FAZ-PLANI.md).

---

## ⚖️ Uyarı & Lisans

Yalnızca araştırma ve eğitim amaçlıdır. **Yatırım tavsiyesi değildir.** Kripto
ticareti önemli risk taşır; yazarlar hiçbir kayıptan sorumlu değildir.

MIT — bkz. [LICENSE](LICENSE).
