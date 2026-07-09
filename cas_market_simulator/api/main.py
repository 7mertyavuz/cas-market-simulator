"""CAS Market Simulator — merkezi dashboard API cephesi (Faz FE).

REST uclari:
  GET /v1/card/{symbol}
  GET /v1/flow/{token}
  GET /v1/book/{symbol}
  GET /v1/sentiment/{entity}
  GET /v1/shocks
  GET /v1/sim/history

WebSocket:
  /v1/stream

Static:
  /  -> ui/dist/index.html
  /assets/* -> ui/dist/assets/*
"""
from __future__ import annotations

import asyncio
import json
import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, WebSocket
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from cas_market_simulator.adapters import (
    MicrostructureFlowFeed,
    MicrostructureBookFeed,
    MacroSentimentFeed,
    SignalCoreFactorBrain,
)
from cas_market_simulator.adapters.bars import ohlcv_from_history
from cas_market_simulator.environment.base import Environment


# ------------------------------------------------------------------
# Global servisler (basit omur; production'da dependency injection)
# ------------------------------------------------------------------
_flow_feed: MicrostructureFlowFeed | None = None
_book_feed: MicrostructureBookFeed | None = None
_sentiment_feed: MacroSentimentFeed | None = None
_brain: SignalCoreFactorBrain | None = None


def _get_flow_feed() -> MicrostructureFlowFeed:
    global _flow_feed
    if _flow_feed is None:
        _flow_feed = MicrostructureFlowFeed(mode="simulation", seed=42)
    return _flow_feed


def _get_book_feed() -> MicrostructureBookFeed:
    global _book_feed
    if _book_feed is None:
        _book_feed = MicrostructureBookFeed(mode="simulation", seed=42, base_price=30_000.0)
    return _book_feed


def _get_sentiment_feed() -> MacroSentimentFeed:
    global _sentiment_feed
    if _sentiment_feed is None:
        _sentiment_feed = MacroSentimentFeed(mode="offline")
    return _sentiment_feed


def _get_brain() -> SignalCoreFactorBrain:
    global _brain
    if _brain is None:
        _brain = SignalCoreFactorBrain()
    return _brain


# ------------------------------------------------------------------
# Simulasyon gecmisi (mock / cache)
# ------------------------------------------------------------------
_sim_env: Environment | None = None
_sim_history: list[dict] = []


def _ensure_sim_history(n_ticks: int = 60) -> list[dict]:
    global _sim_env, _sim_history
    if _sim_env is None:
        _sim_env = Environment("BTC", 67_000.0)
        for _ in range(n_ticks):
            state = _sim_env.step()
            _sim_history.append({
                "tick": state.tick,
                "price": state.price,
                "card_direction": "NEUTRAL",
                "card_confidence": 0.0,
                "active_shock_magnitude": 0.0,
                "crowd_emergence_score": 0.0,
            })
    return _sim_history


# ------------------------------------------------------------------
# FastAPI
# ------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    _ensure_sim_history()
    yield


app = FastAPI(
    title="CAS Market Dashboard API",
    version="0.1.0",
    lifespan=lifespan,
)


def _serialize(obj):
    """Dataclass / list / dict -> JSON-serializable tree."""
    from dataclasses import asdict, is_dataclass
    if is_dataclass(obj):
        return _serialize(asdict(obj))
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, list):
        return [_serialize(x) for x in obj]
    if isinstance(obj, dict):
        return {k: _serialize(v) for k, v in obj.items()}
    return obj


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/v1/card/{symbol}")
def card(symbol: str):
    brain = _get_brain()
    env = _sim_env or Environment(symbol, 67_000.0)
    bars = ohlcv_from_history(env.history)
    extra = {
        "flow": _get_flow_feed().latest("UniswapV2"),
        "sentiment": _get_sentiment_feed().latest(symbol),
        "crowd_emergence": 0.0,
    }
    c = brain.analyze(symbol, bars, extra)
    return JSONResponse(content=_serialize(c))


@app.get("/v1/flow/{token}")
def flow(token: str):
    state = _get_flow_feed().latest(token)
    return JSONResponse(content=_serialize(state))


@app.get("/v1/book/{symbol}")
def book(symbol: str):
    state = _get_book_feed().latest(symbol)
    return JSONResponse(content=_serialize(state))


@app.get("/v1/sentiment/{entity}")
def sentiment(entity: str):
    state = _get_sentiment_feed().latest(entity)
    return JSONResponse(content=_serialize(state))


@app.get("/v1/shocks")
def shocks():
    since = datetime.now(timezone.utc)
    events = _get_sentiment_feed().shocks(since)
    return JSONResponse(content=[_serialize(e) for e in events])


@app.get("/v1/sim/history")
def sim_history():
    return JSONResponse(content=_ensure_sim_history())


@app.websocket("/v1/stream")
async def stream(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            payload = {
                "ts": datetime.now(timezone.utc).isoformat(),
                "card": _serialize(_get_brain().analyze(
                    "BTC", ohlcv_from_history((_sim_env or Environment("BTC", 67_000.0)).history),
                    {
                        "flow": _get_flow_feed().latest("UniswapV2"),
                        "sentiment": _get_sentiment_feed().latest("BTC"),
                        "crowd_emergence": 0.0,
                    }
                )),
                "flow": _serialize(_get_flow_feed().latest("UniswapV2")),
                "book": _serialize(_get_book_feed().latest("BTCUSDT")),
                "sentiment": _serialize(_get_sentiment_feed().latest("BTC")),
            }
            await websocket.send_text(json.dumps(payload))
            await asyncio.sleep(2.0)
    except Exception:
        pass


# ------------------------------------------------------------------
# Static UI
# ------------------------------------------------------------------
_UI_DIST = Path(__file__).resolve().parents[3] / "ui" / "dist"


if _UI_DIST.exists():
    app.mount("/assets", StaticFiles(directory=str(_UI_DIST / "assets")), name="assets")

    @app.get("/")
    def index():
        return FileResponse(str(_UI_DIST / "index.html"))

    @app.get("/{path:path}")
    def spa_catch_all(path: str):
        if path.startswith("v1/") or path == "health":
            return JSONResponse({"detail": "not found"}, status_code=404)
        return FileResponse(str(_UI_DIST / "index.html"))
