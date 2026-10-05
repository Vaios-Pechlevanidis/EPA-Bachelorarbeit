"""
Tests für das Aktien-Dashboard (Inkrement 3, E16): Analystenempfehlungen,
Umsatz und Nettoergebnis, GET /finance und Nachrichten (news_service, GET /news).
Ohne Netzwerk: yfinance- und RSS-Abruf nachgebildet, Zwischenspeicher in tmp_path.

Ausführen (aus dem backend-Verzeichnis):
    uv run python -m pytest tests/market -q -p no:cacheprovider
"""

import os
import sys
from datetime import datetime, timedelta, timezone

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from _market_helpers import FETCHED_AT, raw_data  # noqa: E402
from routes.market import router  # noqa: E402
from services import context_service as cs  # noqa: E402
from services import news_service as ns  # noqa: E402

RECOMMENDATIONS = [
    {"period": "0m", "strongBuy": 3, "buy": 21, "hold": 4, "sell": 0, "strongSell": 0},
    {"period": "-1m", "strongBuy": 3, "buy": 20, "hold": 4, "sell": 1, "strongSell": 0},
    {"period": "-3m", "strongBuy": 2, "buy": 18, "hold": 5, "sell": 1, "strongSell": 1},
]
INCOME_ANNUAL = [
    {"period_end": "2023-12-31", "revenue": 3.1e10, "net_income": 6.1e9},
    {"period_end": "2022-12-31", "revenue": 2.9e10, "net_income": None},
    {"period_end": "2021-12-31", "revenue": float("nan"), "net_income": None},
]
NOW = datetime(2026, 10, 4, 12, 0, tzinfo=timezone.utc)

RSS = b"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel><title>t</title>
<item><title>Aelter - Quelle A</title><link>https://example.org/a</link>
  <pubDate>Wed, 01 Oct 2026 08:00:00 GMT</pubDate><source url="https://a.example">Quelle A</source></item>
<item><title>Neuer - Quelle B</title><link>https://example.org/b</link>
  <pubDate>Fri, 03 Oct 2026 08:00:00 GMT</pubDate><source url="https://b.example">Quelle B</source></item>
<item><title>Ohne Link</title><link></link><pubDate>Fri, 03 Oct 2026 08:00:00 GMT</pubDate></item>
<item><title>Ohne Datum</title><link>https://example.org/c</link></item>
</channel></rss>"""


def finance_raw():
    raw = raw_data()
    raw.update({"recommendations": RECOMMENDATIONS, "income_annual": INCOME_ANNUAL,
                "income_quarterly": [{"period_end": "2024-03-31", "revenue": 8e9, "net_income": 1.5e9}]})
    return raw


class FakeRss:
    def __init__(self, body=RSS, error=None):
        self.body, self.error, self.calls = body, error, []

    def __call__(self, query):
        self.calls.append(query)
        if self.error is not None:
            raise self.error
        return self.body


@pytest.fixture
def client():
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


@pytest.fixture
def rss(monkeypatch, market):
    fake = FakeRss()
    monkeypatch.setattr(ns, "fetch_rss", fake)
    monkeypatch.setattr(ns, "_failed_fetches", {})
    return fake


# ---------------------------------------------------------------------------
# Analystenempfehlungen, Umsatz und Nettoergebnis
# ---------------------------------------------------------------------------

class TestAnalysts:

    def test_relative_months_become_calendar_months(self):
        analysts = cs.build_analysts(finance_raw(), FETCHED_AT)  # Abruf 2024-03
        assert analysts["as_of"] == "2024-03-15"
        assert [m["month"] for m in analysts["months"]] == ["2023-12", "2024-02", "2024-03"]
        assert analysts["months"][-1] == {"month": "2024-03", "strong_buy": 3, "buy": 21, "hold": 4,
                                          "sell": 0, "strong_sell": 0, "total": 28}

    def test_month_shift_over_year_boundary(self):
        analysts = cs.build_analysts({"recommendations": RECOMMENDATIONS}, datetime(2024, 1, 5, tzinfo=timezone.utc))
        assert [m["month"] for m in analysts["months"]] == ["2023-10", "2023-12", "2024-01"]

    def test_invalid_rows_are_skipped_and_empty_is_none(self):
        rows = [{"period": "x", "strongBuy": 1, "buy": 1, "hold": 1, "sell": 1, "strongSell": 1},
                {"period": "0m", "strongBuy": None, "buy": 1, "hold": 1, "sell": 1, "strongSell": 1},
                {"period": "-1m", "strongBuy": 0, "buy": 0, "hold": 0, "sell": 0, "strongSell": 0}]
        assert cs.build_analysts({"recommendations": rows}, FETCHED_AT) is None
        assert cs.build_analysts({}, FETCHED_AT) is None


class TestEarnings:

    def test_annual_sorted_and_missing_values_kept_empty(self):
        earnings = cs.build_earnings(finance_raw())
        assert earnings["currency"] == "EUR"
        assert earnings["annual"] == [
            {"period_end": "2022-12-31", "revenue": 2.9e10, "net_income": None},
            {"period_end": "2023-12-31", "revenue": 3.1e10, "net_income": 6.1e9},
        ]
        assert earnings["quarterly"] == [{"period_end": "2024-03-31", "revenue": 8e9, "net_income": 1.5e9}]

    def test_no_income_data_is_none(self):
        assert cs.build_earnings(raw_data()) is None

    def test_record_contains_new_fields(self):
        record = cs.build_record("TST.DE", finance_raw(), FETCHED_AT)
        assert record["analysts"]["months"] and record["earnings"]["annual"]


class TestFinanceRoute:

    def test_shape_with_ticker(self, client, fake_db, market):
        market.fetcher.result = finance_raw()
        res = client.get("/api/analytics/company/3/finance")
        assert res.status_code == 200
        body = res.json()
        assert body["available"] is True and body["ticker"] == "TKA.DE"
        assert {"analysts", "earnings", "prices", "metrics"} <= set(body)
        assert body["analysts"]["months"][-1]["total"] == 28
        assert len(body["earnings"]["annual"]) == 2

    def test_old_cache_without_new_fields(self, client, fake_db, market):
        record = cs.build_record("TKA.DE", raw_data(), FETCHED_AT)
        del record["analysts"], record["earnings"]
        cs.save_cached(record)
        body = client.get("/api/analytics/company/3/finance").json()
        assert body["available"] is True and body["analysts"] is None and body["earnings"] is None

    def test_without_ticker(self, client, fake_db, market):
        body = client.get("/api/analytics/company/4/finance").json()
        assert body["available"] is False and body["analysts"] is None and body["earnings"] is None
        assert body["reason"] == "Kein Aktienkurs: nicht börsennotiert"

    def test_unknown_company(self, client, fake_db, market):
        assert client.get("/api/analytics/company/999/finance").status_code == 404

    def test_market_response_unchanged(self, client, fake_db, market):
        market.fetcher.result = finance_raw()
        body = client.get("/api/analytics/company/3/market").json()
        assert "analysts" not in body and "earnings" not in body


# ---------------------------------------------------------------------------
# Nachrichten
# ---------------------------------------------------------------------------

class TestNewsParsing:

    def test_query(self):
        assert ns.news_query("Telekom") == "Telekom when:90d"
        assert ns.news_query("SAP SE") == "SAP when:90d"
        assert ns.news_query("NTT DATA  SE") == '"NTT DATA" when:90d'
        assert ns.news_query("Universität zu Köln") == '"Universität zu Köln" when:90d'

    def test_parse_rss(self):
        items = ns.parse_rss(RSS)
        assert [i["title"] for i in items] == ["Neuer", "Aelter", "Ohne Datum"]
        assert items[0] == {"title": "Neuer", "source": "Quelle B", "url": "https://example.org/b",
                            "published_at": "2026-10-03T08:00:00+00:00"}
        assert items[2]["published_at"] is None and items[2]["source"] is None
        assert len(ns.parse_rss(RSS, limit=1)) == 1


class TestNewsRuntime:

    def test_fetches_once_and_uses_cache(self, fake_db, rss):
        first = ns.company_news(19, now=NOW)
        assert first["available"] is True and first["stale"] is False
        assert first["query"] == "SAP when:90d" and len(first["items"]) == 3
        assert ns.company_news(19, now=NOW + timedelta(hours=1))["items"] == first["items"]
        assert rss.calls == ["SAP when:90d"]

    def test_old_cache_is_refreshed(self, fake_db, rss):
        ns.company_news(19, now=NOW)
        ns.company_news(19, now=NOW + ns.NEWS_MAX_AGE + timedelta(minutes=1))
        assert len(rss.calls) == 2

    def test_failed_refresh_shows_stale_cache(self, fake_db, rss):
        ns.company_news(19, now=NOW)
        rss.error = TimeoutError("zu langsam")
        later = ns.company_news(19, now=NOW + timedelta(days=1))
        assert later["available"] is True and later["stale"] is True and later["reason"] is None

    def test_failed_fetch_without_cache(self, fake_db, rss):
        rss.error = ConnectionError("kein Netz")
        result = ns.company_news(19, now=NOW)
        assert result["available"] is False and "kein Netz" in result["reason"]
        ns.company_news(19, now=NOW)
        assert len(rss.calls) == 1, "kein sofortiger zweiter Versuch"

    def test_live_fetch_disabled(self, fake_db, rss, monkeypatch):
        monkeypatch.setenv(cs.LIVE_FETCH_ENV, "0")
        result = ns.company_news(19, now=NOW)
        assert result["available"] is False and "MARKET_LIVE_FETCH=0" in result["reason"]
        assert rss.calls == []

    def test_no_hits(self, fake_db, rss):
        rss.body = b"<rss><channel></channel></rss>"
        result = ns.company_news(4, now=NOW)
        assert result["available"] is False and "Keine Meldungen" in result["reason"]

    def test_unknown_company(self, fake_db, rss):
        assert ns.company_news(999, now=NOW) is None


class TestNewsRoute:

    def test_shape(self, client, fake_db, rss):
        res = client.get("/api/analytics/company/4/news")
        assert res.status_code == 200
        assert set(res.json()) == {"company_id", "query", "available", "reason", "stale", "items",
                                   "fetched_at", "source", "window_days"}

    def test_fetch_error_is_not_500(self, client, fake_db, rss):
        rss.error = RuntimeError("Google nicht erreichbar")
        res = client.get("/api/analytics/company/4/news")
        assert res.status_code == 200 and res.json()["available"] is False

    def test_unknown_company_is_404(self, client, fake_db, rss):
        res = client.get("/api/analytics/company/999/news")
        assert res.status_code == 404 and "999" in res.json()["detail"]
