<div align="center">

# 🧠 cas-market-simulator

**Karmaşık Uyarlanabilir Sistem (CAS) tabanlı piyasa simülatörü**
_Sinyal beyni + çok-ajanlı ekosistem — dürüstlük katmanıyla mühürlenmiş._

<br/>

![tests](https://img.shields.io/badge/tests-334%20passing-2ea44f?style=flat-square)
![python](https://img.shields.io/badge/python-3.11%2B-3776ab?style=flat-square&logo=python&logoColor=white)
![react](https://img.shields.io/badge/react-19-61dafb?style=flat-square&logo=react&logoColor=white)
![fastapi](https://img.shields.io/badge/fastapi-0.115-009688?style=flat-square&logo=fastapi&logoColor=white)
![license](https://img.shields.io/badge/license-MIT-black?style=flat-square)

</div>

---

> ⚠️ **Araştırma / PoC — yatırım tavsiyesi değildir.** Simülasyon çıktıları *ortaya çıkan davranışların gözlemlenmesi* içindir; kehanet değildir.

---

## 🎯 Ne işe yarar?

Piyasalar, birbirini gözleyen ve tepki veren çok sayıda basit aktörün kolektif sonucudur. Bu repo bu sistemi iki katmanda modeller:

| Katman | Rol | Sorduğu soru |
|:--|:--|:--|
| 🧩 **`signalcore`** | Sinyal beyni — indikatör + formasyon + rejim + risk | *"Şu an ne algılanıyor?*" |
| 🐜 **CAS Motoru** | Çok-ajanlı ekosistem — momentum, MM, panik, likidasyon... | *"Bu aktörler bir arada neyi doğurur?*" |

Bu iki katman **kapalı bir döngüdür**: ajan popülasyonunun ürettiği kolektif davranış, beyne bir faktör olarak geri beslenir.

---

## 🌐 Büyük Resim

Bu simülatör, üç bağımsız reponun buluştuğu **merkezdir**. Diğer ikisi birer "duyu organı"; simülatör bunları yalnızca veri sözleşmeleri üzerinden okur:

```mermaid
flowchart LR
    subgraph MICRO["🔬 lob-microstructure-agent"]
        M1["Mempool → decode → aktör etiketi<br/>OFI · VPIN · MEV"]
    end
    subgraph MACRO["📰 macro-sentiment-agent"]
        S1["Haber · Fed · Sosyal → NLP<br/>panic / euphoria / fed-tone"]
    end
    subgraph SIM["🧠 cas-market-simulator"]
        direction TB
        B["signalcore beyni"]
        E["CAS ajan motoru"]
        B <--> E
    end

    M1 -->|FlowState + BookState| SIM
    S1 -->|SentimentState + ShockEvent| SIM
    SIM -->|Card| OUT["📊 Karar desteği kartı"]

    style SIM fill:#1f2937,stroke:#f59e0b,stroke-width:2px,color:#fff
    style MICRO fill:#0f3d3e,stroke:#2dd4bf,color:#fff
    style MACRO fill:#3b0764,stroke:#c084fc,color:#fff
    style OUT fill:#064e3b,stroke:#34d399,color:#fff
```

---

## 🏗️ İç Mimari

```mermaid
flowchart TD
    FEED["Gerçek / sim feed'ler"] --> BRAIN

    subgraph BRAIN["🧩 signalcore beyni"]
        F["6 çekirdek faktör + 5 sensör"]
        PAT["Formasyon dedektörü"]
        RR["Rejim yönlendirici"]
        RISK["Risk motoru"]
        F & PAT --> RR --> RISK
    end

    RISK --> CARD["📇 Card"]

    subgraph CAS["🐜 CAS ajan motoru"]
        POP["12+ ajan popülasyonu"]
        ENV["Order-book çevresi"]
        POP -->|emirler| ENV
        ENV -->|fiyat| POP
    end

    CARD -.-> POP
    ENV --> BARS["OHLCV"] --> BRAIN
    CAS -->|crowd_emergence| BRAIN
```

---

## 🛡️ Dürüstlük Katmanı

Bir simülatörün en tehlikeli yanı kendini kandırabilmesidir. Üretilen her sinyal aşırı-uyum ve şansa karşı sınanır:

- **CPCV** — Combinatorial Purged Cross-Validation
- **Deflated Sharpe** — çoklu-deneme cezası
- **Kuyruk riski** — VaR / CVaR / Hill/EVT
- **Kalibrasyon** — stilize gerçekler
- **HRP** — Hierarchical Risk Parity portföy dağıtımı

---

## 🚀 Çalıştırma

### Backend

```bash
pip install -r requirements.txt
pytest -q                                   # 334 test

# Dashboard API
python -m uvicorn cas_market_simulator.api.main:app --host 127.0.0.1 --port 8000

# Demolar
PYTHONPATH=. python scripts/run_faz3_demo.py
PYTHONPATH=. python scripts/run_faz6_demo.py
PYTHONPATH=. python scripts/run_faz7_demo.py
PYTHONPATH=. python scripts/run_faz8_demo.py
PYTHONPATH=. python scripts/run_faz9_demo.py
```

### Frontend

```bash
cd ui
npm install
npm run dev        # http://localhost:5173
npm run test       # UI testleri
npm run build      # production build -> ui/dist
```

Vite geliştirme sunucusu `/v1` isteklerini otomatik olarak `http://127.0.0.1:8000`'e yönlendirir. Gerçek backend verisi için `VITE_USE_MOCK=false npm run dev` çalıştırın.

Tüm çekirdek **saf Python + NumPy**. Feed'ler varsayılan olarak deterministik simülasyon modunda çalışır.

---

## ⚖️ Uyarı & Lisans

Yalnızca araştırma ve eğitim amaçlıdır. **Yatırım tavsiyesi değildir.**

MIT — bkz. [LICENSE](LICENSE).
