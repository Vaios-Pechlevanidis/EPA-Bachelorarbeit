"""
Tests für GET /api/analytics/company/{company_id}/market (Inkrement 3, E15).
Die App enthält nur den Kurs-Router (main.py lädt Sentiment-Modelle); Abruf
nachgebildet, Zwischenspeicher in tmp_path, Unternehmen aus einem
nachgebildeten Client bzw. dem In-Memory-Store.

Ausführen (aus dem backend-Verzeichnis):
    uv run python -m pytest tests/market -q -p no:cacheprovider
"""

import os
import sys
from datetime import datetime, timezone

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from _market_helpers import raw_data  # noqa: E402
from routes.market import router  # noqa: E402
from services import context_service as cs  # noqa: E402

URL = "/api/analytics/company/{}/market"
FIELDS = {"company_id", "ticker", "ticker_scope", "ticker_name", "currency", "available", "reason",
          "prices", "metrics", "fetched_at", "source"}


@pytest.fixture
def client():
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


@pytest.fixture
def cached(market):
    """Zwischenspeicher mit Kursen 2023-12 bis 2024-03 für TKA.DE."""
    cs.save_cached(cs.build_record("TKA.DE", raw_data(history=[
        {"date": "2023-12-01", "close": 10.0},
        {"date": "2024-01-01", "close": 11.0},
        {"date": "2024-02-01", "close": 12.0},
        {"date": "2024-03-01", "close": 13.0},
    ]), datetime(2024, 4, 2, tzinfo=timezone.utc)))
    return market


class TestShape:

    def test_with_ticker(self, client, fake_db, cached):
        res = client.get(URL.format(3))
        assert res.status_code == 200
        body = res.json()
        assert set(body) == FIELDS
        assert body["available"] is True and body["reason"] is None
        assert body["ticker"] == "TKA.DE" and body["ticker_scope"] == "eigene Aktie"
        assert body["currency"] == "EUR" and body["source"].startswith("Yahoo Finance")
        assert [p["period"] for p in body["prices"]] == ["2023-12", "2024-01", "2024-02", "2024-03"]
        assert set(body["metrics"]) == {"market_cap", "employees", "revenue"}
        assert cached.fetcher.calls == []

    def test_without_ticker(self, client, fake_db, market):
        body = client.get(URL.format(4)).json()
        assert set(body) == FIELDS
        assert body["available"] is False and body["ticker"] is None
        assert body["reason"] == "Kein Aktienkurs: nicht börsennotiert"
        assert body["prices"] == [] and body["metrics"] == {}
        assert market.fetcher.calls == []

    def test_demo_company(self, client, fake_db, market):
        body = client.get(URL.format(10)).json()
        assert body["available"] is False and "Demo" in body["reason"]

    def test_parent_company_scope(self, client, fake_db, market):
        body = client.get(URL.format(20)).json()
        assert body["ticker"] == "9432.T" and body["ticker_scope"] == "Konzernmutter"

    def test_group_company_scope(self, client, fake_db, market):
        body = client.get(URL.format(26)).json()
        assert body["ticker"] == "AFX.DE" and body["ticker_scope"] == "Konzerngesellschaft"


class TestPeriod:

    def test_start_and_end(self, client, fake_db, cached):
        body = client.get(URL.format(3), params={"start": "2024-01", "end": "2024-02"}).json()
        assert [p["period"] for p in body["prices"]] == ["2024-01", "2024-02"]

    def test_only_start(self, client, fake_db, cached):
        body = client.get(URL.format(3), params={"start": "2024-03"}).json()
        assert [p["period"] for p in body["prices"]] == ["2024-03"]

    def test_window_without_prices_stays_available(self, client, fake_db, cached):
        body = client.get(URL.format(3), params={"start": "2030-01"}).json()
        assert body["available"] is True and body["prices"] == []

    @pytest.mark.parametrize("params", [{"start": "2024-1"}, {"end": "24-01"}, {"start": "2024-05", "end": "2024-01"}])
    def test_invalid_period_is_400(self, client, fake_db, cached, params):
        res = client.get(URL.format(3), params=params)
        assert res.status_code == 400 and isinstance(res.json()["detail"], str)


class TestNoServerError:

    def test_fetch_fails(self, client, fake_db, market):
        market.fetcher.error = RuntimeError("Yahoo nicht erreichbar")
        res = client.get(URL.format(3))
        assert res.status_code == 200
        body = res.json()
        assert body["available"] is False and "Yahoo nicht erreichbar" in body["reason"]

    def test_live_fetch_disabled(self, client, fake_db, market, monkeypatch):
        monkeypatch.setenv(cs.LIVE_FETCH_ENV, "0")
        res = client.get(URL.format(3))
        assert res.status_code == 200 and res.json()["available"] is False
        assert market.fetcher.calls == []

    def test_no_prices_from_source(self, client, fake_db, market):
        market.fetcher.result = raw_data(history=[])
        body = client.get(URL.format(3)).json()
        assert body["available"] is False and "keine Monatskurse" in body["reason"]

    def test_unknown_company_is_404(self, client, fake_db, market):
        res = client.get(URL.format(999))
        assert res.status_code == 404 and "999" in res.json()["detail"]

    def test_metadata_columns_missing(self, client, fake_db, cached):
        fake_db.missing_columns = True
        body = client.get(URL.format(3)).json()
        assert body["available"] is True and body["ticker"] == "TKA.DE"


class TestInMemoryStore:
    """Demo 3 hat im In-Memory-Store die ID 3 (in der gehosteten DB Thyssenkrupp);
    der Namensabgleich verhindert, dass Demo 3 den Ticker TKA.DE erhält."""

    def test_demo_does_not_inherit_ticker_by_id(self, client, in_memory_db, market):
        body = client.get(URL.format(3)).json()
        assert body["ticker"] is None and body["available"] is False
        assert body["reason"] == "Kein Aktienkurs: synthetisches Demo-Unternehmen"
        assert market.fetcher.calls == []
