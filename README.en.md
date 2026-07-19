<div align="center">

# 🧠 cas-market-simulator

**A market simulator built on Complex Adaptive Systems (CAS)**
_Signal brain + multi-agent ecosystem — sealed with an honesty layer._

🌐 [Türkçe](README.md) · **English**

<br/>

![tests](https://img.shields.io/badge/tests-334%20passing-2ea44f?style=flat-square)
![python](https://img.shields.io/badge/python-3.11%2B-3776ab?style=flat-square&logo=python&logoColor=white)
![react](https://img.shields.io/badge/react-19-61dafb?style=flat-square&logo=react&logoColor=white)
![fastapi](https://img.shields.io/badge/fastapi-0.115-009688?style=flat-square&logo=fastapi&logoColor=white)
![license](https://img.shields.io/badge/license-MIT-black?style=flat-square)

</div>

---

> ⚠️ **Research / PoC — not investment advice.** Simulation outputs are for *observing emergent behavior*; they are not predictions.

---

## 🎯 What does it do?

Markets are the collective result of many simple actors that watch and react to one another. This repo models that system in two layers:

| Layer | Role | Question it asks |
|:--|:--|:--|
| 🧩 **`signalcore`** | Signal brain — indicators + patterns + regime + risk | *"What is being detected right now?*" |
| 🐜 **CAS Engine** | Multi-agent ecosystem — momentum, MM, panic, liquidation... | *"What do these actors give rise to together?*" |

These two layers form a **closed loop**: the collective behavior produced by the agent population is fed back into the brain as a factor.

---

## 🌐 The Big Picture

This simulator is the **hub** where three independent repos meet. The other two are "sensory organs"; the simulator reads them only through data contracts:

```mermaid
flowchart LR
    subgraph MICRO["🔬 lob-microstructure-agent"]
        M1["Mempool → decode → actor label<br/>OFI · VPIN · MEV"]
    end
    subgraph MACRO["📰 macro-sentiment-agent"]
        S1["News · Fed · Social → NLP<br/>panic / euphoria / fed-tone"]
    end
    subgraph SIM["🧠 cas-market-simulator"]
        direction TB
        B["signalcore brain"]
        E["CAS agent engine"]
        B <--> E
    end

    M1 -->|FlowState + BookState| SIM
    S1 -->|SentimentState + ShockEvent| SIM
    SIM -->|Card| OUT["📊 Decision-support card"]

    style SIM fill:#1f2937,stroke:#f59e0b,stroke-width:2px,color:#fff
    style MICRO fill:#0f3d3e,stroke:#2dd4bf,color:#fff
    style MACRO fill:#3b0764,stroke:#c084fc,color:#fff
    style OUT fill:#064e3b,stroke:#34d399,color:#fff
```

---

## 🏗️ Internal Architecture

```mermaid
flowchart TD
    FEED["Real / sim feeds"] --> BRAIN

    subgraph BRAIN["🧩 signalcore brain"]
        F["6 core factors + 5 sensors"]
        PAT["Pattern detector"]
        RR["Regime router"]
        RISK["Risk engine"]
        F & PAT --> RR --> RISK
    end

    RISK --> CARD["📇 Card"]

    subgraph CAS["🐜 CAS agent engine"]
        POP["12+ agent population"]
        ENV["Order-book environment"]
        POP -->|orders| ENV
        ENV -->|price| POP
    end

    CARD -.-> POP
    ENV --> BARS["OHLCV"] --> BRAIN
    CAS -->|crowd_emergence| BRAIN
```

---

## 🛡️ Honesty Layer

The most dangerous thing about a simulator is that it can fool itself. Every signal produced is tested against overfitting and luck:

- **CPCV** — Combinatorial Purged Cross-Validation
- **Deflated Sharpe** — multiple-testing penalty
- **Tail risk** — VaR / CVaR / Hill/EVT
- **Calibration** — stylized facts
- **HRP** — Hierarchical Risk Parity portfolio allocation

---

## 🚀 Running

### Backend

```bash
pip install -r requirements.txt
pytest -q                                   # 334 tests

# Dashboard API
python -m uvicorn cas_market_simulator.api.main:app --host 127.0.0.1 --port 8000

# Demos
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
npm run test       # UI tests
npm run build      # production build -> ui/dist
```

The Vite dev server automatically proxies `/v1` requests to `http://127.0.0.1:8000`. For real backend data, run `VITE_USE_MOCK=false npm run dev`.

The entire core is **pure Python + NumPy**. Feeds run in deterministic simulation mode by default.

---

## ⚖️ Disclaimer & License

For research and educational purposes only. **Not investment advice.**

MIT — see [LICENSE](LICENSE).
