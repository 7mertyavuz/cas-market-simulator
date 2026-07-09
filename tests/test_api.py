"""FastAPI dashboard API testleri."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from cas_market_simulator.api.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_card(client):
    r = client.get("/v1/card/BTC")
    assert r.status_code == 200
    data = r.json()
    assert data["symbol"] == "BTC"
    assert "direction" in data
    assert "confidence" in data
    assert "votes" in data


def test_flow(client):
    r = client.get("/v1/flow/UniswapV2")
    assert r.status_code == 200
    data = r.json()
    assert "flow_imbalance" in data
    assert "actor_mix" in data


def test_book(client):
    r = client.get("/v1/book/BTCUSDT")
    assert r.status_code == 200
    data = r.json()
    assert "spread_bps" in data
    assert "microprice" in data


def test_sentiment(client):
    r = client.get("/v1/sentiment/BTC")
    assert r.status_code == 200
    data = r.json()
    assert "entity" in data
    assert "polarity" in data


def test_shocks(client):
    r = client.get("/v1/shocks")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_sim_history(client):
    r = client.get("/v1/sim/history")
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 60
    assert "price" in data[0]
