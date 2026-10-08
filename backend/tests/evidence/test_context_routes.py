"""
Tests für die Belege-Routen (Inkrement 4, Schritt 3):
GET /api/analytics/company/{id}/anomalies/{anomaly_id}/context und
GET /api/analytics/company/{id}/context?from=&to=. Erkennung aus dem
In-Memory-Store (Demo 3), Abruf nachgebildet, Speicher in tmp_path.

Ausführen:
    cd backend
    uv run python -m pytest tests/evidence/test_context_routes.py -q -p no:cacheprovider
"""

import os
import sys
from datetime import datetime, timezone
from email.utils import format_datetime

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))

import services.evidence_service as ev  # noqa: E402
import services.evidence_sources as src  # noqa: E402
from services import news_service  # noqa: E402
from routes.anomalies import router as anomalies_router  # noqa: E402
from routes.context import router as context_router  # noqa: E402

DEMO_3 = 3
ANOMALIES = "/api/analytics/company/{}/anomalies"
CONTEXT = "/api/analytics/company/{}/anomalies/{}/context"
SELECTION = "/api/analytics/company/{}/context"
FALL_ID = "employee:durchschnittsbewertung:2023-01"
INFO = {"company_id": DEMO_3, "name": "Demo 3", "search_term": '"Demo 3"', "exclude": [], "term_confirmed": False,
        "ticker": None, "ticker_scope": None, "eqs_uuid": None, "eqs_name": None}
FIELDS = {"company_id", "company", "search_term", "anchor", "window", "items", "total", "offset", "limit", "counts",
          "sources", "coverage", "reason", "note"}


def rss(entries):
    items = []
    for title, url, day in entries:
        pub = format_datetime(datetime.fromisoformat(day + "T09:00:00+00:00"))
        items.append(f"<item><title>{title} - Blatt</title><link>{url}</link><pubDate>{pub}</pubDate>"
                     f"<source url=\"https://blatt.example\">Blatt</source></item>")
    return ("<?xml version=\"1.0\"?><rss version=\"2.0\"><channel><title>t</title>" + "".join(items) + "</channel></rss>").encode()


class FakeRss:
    def __init__(self, per_month=None, fail=()):
        self.per_month = per_month or {}
        self.fail = set(fail)
        self.queries = []

    def __call__(self, query):
        self.queries.append(query)
        month = query.split("after:")[1][:7]
        if month in self.fail:
            raise OSError("Netz weg")
        return rss(self.per_month.get(month, []))


@pytest.fixture(scope="module")
def client(in_memory_db):
    app = FastAPI()
    app.include_router(anomalies_router)
    app.include_router(context_router)
    return TestClient(app)


@pytest.fixture
def store(tmp_path, monkeypatch):
    """Speicher in tmp_path, Unternehmen ohne DB-Zugriff, Abruf nachgebildet, keine Wartezeit."""
    fetcher = FakeRss()
    monkeypatch.setattr(ev, "STORE_DIR", tmp_path)
    monkeypatch.setattr(ev, "_failed_fetches", {})
    monkeypatch.setattr(src, "_last_request", {})
    monkeypatch.setattr(src.time, "sleep", lambda s: None)
    monkeypatch.setattr(ev, "company_context_info", lambda cid, metadata=None: dict(INFO) if cid == DEMO_3 else None)
    monkeypatch.setattr(news_service, "fetch_rss", fetcher)
    monkeypatch.delenv(ev.LIVE_FETCH_ENV, raising=False)
    fetcher.dir = tmp_path
    return fetcher


def _anchor(client, kind):
    body = client.get(ANOMALIES.format(DEMO_3)).json()
    if kind == "change":
        return next(a for a in body["anomalies"] if a["id"] == FALL_ID)
    outliers = body["outlier_months"]
    return outliers[0] if outliers else None


class TestAnomalyContext:

    def test_shape_and_window(self, client, store):
        anomaly = _anchor(client, "change")
        store.per_month["2022-12"] = [("Meldung im Fenster", "https://x/1", "2022-12-20")]
        res = client.get(CONTEXT.format(DEMO_3, FALL_ID))
        assert res.status_code == 200
        body = res.json()
        assert set(body) == FIELDS
        assert body["anchor"]["kind"] == "niveauwechsel" and body["anchor"]["id"] == FALL_ID
        assert body["anchor"]["date"] == anomaly["date"] and body["anchor"]["direction"] == "fall"
        w = body["window"]
        expected_start = ev.shift_month(anomaly["previous_period"], 1) if anomaly["previous_period"] else anomaly["date"]
        assert w["transition_from"] == expected_start
        assert w["from"] == ev.shift_month(expected_start, -3) and w["to"] == ev.shift_month(anomaly["date"], 1)
        assert body["total"] == 1 and body["items"][0]["title"] == "Meldung im Fenster"
        assert body["items"][0]["source_type"] == "news" and body["items"][0]["reliability"] == "mittel"
        assert body["counts"] == {"news": 1, "adhoc": 0, "global": 0} and body["coverage"] is True
        assert body["sources"]["gnews"]["status"] == "ok" and body["note"].startswith("Belege sind")
        assert len(store.queries) == w["months"]

    def test_outlier_id_accepted(self, client, store):
        outlier = _anchor(client, "outlier")
        if outlier is None:
            pytest.skip("Demo 3 hat keinen auffälligen Einzelmonat")
        body = client.get(CONTEXT.format(DEMO_3, outlier["id"])).json()
        assert body["anchor"]["kind"] == "einzelmonat" and body["anchor"]["date"] == outlier["date"]
        assert body["window"]["from"] == ev.shift_month(outlier["date"], -3)

    def test_window_parameters(self, client, store):
        body = client.get(CONTEXT.format(DEMO_3, FALL_ID), params={"window_before": 1, "window_after": 0}).json()
        w = body["window"]
        assert w["window_before"] == 1 and w["window_after"] == 0 and w["to"] == w["anchor_to"]
        assert client.get(CONTEXT.format(DEMO_3, FALL_ID), params={"window_before": 99}).status_code == 422

    def test_unknown_anomaly_is_404(self, client, store):
        res = client.get(CONTEXT.format(DEMO_3, "employee:durchschnittsbewertung:1999-01"))
        assert res.status_code == 404 and "nicht gefunden" in res.json()["detail"]
        assert client.get(CONTEXT.format(DEMO_3, "kaputt")).status_code == 404
        assert client.get(CONTEXT.format(DEMO_3, "employee:durchschnittsbewertung:2023-13")).status_code == 404

    def test_unknown_company_is_404(self, client, store):
        assert client.get(CONTEXT.format(999, FALL_ID)).status_code == 404

    def test_invalid_group_is_400(self, client, store):
        res = client.get(CONTEXT.format(DEMO_3, FALL_ID), params={"status": "kunden"})
        assert res.status_code == 400 and "detail" in res.json()

    def test_no_data_is_empty_list_not_500(self, client, store, monkeypatch):
        monkeypatch.setenv(ev.LIVE_FETCH_ENV, "0")
        res = client.get(CONTEXT.format(DEMO_3, FALL_ID))
        assert res.status_code == 200
        body = res.json()
        assert body["items"] == [] and body["coverage"] is False and "CONTEXT_LIVE_FETCH=0" in body["reason"]
        assert store.queries == []

    def test_source_failure_is_not_500(self, client, store):
        store.fail = {ev.shift_month("2023-01", -1)}
        store.per_month["2023-01"] = [("Januar", "https://x/2", "2023-01-05")]
        res = client.get(CONTEXT.format(DEMO_3, FALL_ID))
        assert res.status_code == 200
        body = res.json()
        assert [i["title"] for i in body["items"]] == ["Januar"]
        assert body["sources"]["gnews"]["status"] == "teilweise" and len(body["sources"]["gnews"]["errors"]) == 1

    def test_pagination_newest_first(self, client, store):
        store.per_month["2023-01"] = [(f"Meldung {i:02d}", f"https://x/{i}", f"2023-01-{i:02d}") for i in range(1, 31)]
        first = client.get(CONTEXT.format(DEMO_3, FALL_ID), params={"limit": 10}).json()
        assert first["total"] == 30 and len(first["items"]) == 10 and first["items"][0]["title"] == "Meldung 30"
        second = client.get(CONTEXT.format(DEMO_3, FALL_ID), params={"limit": 10, "offset": 10}).json()
        assert second["items"][0]["title"] == "Meldung 20" and second["offset"] == 10
        assert len(store.queries) == first["window"]["months"], "zweite Seite kommt aus dem Speicher"


class TestSelectionContext:

    def test_shape(self, client, store):
        store.per_month["2022-05"] = [("Mai", "https://x/5", "2022-05-15")]
        res = client.get(SELECTION.format(DEMO_3), params={"from": "2022-05", "to": "2022-06"})
        assert res.status_code == 200
        body = res.json()
        assert set(body) == FIELDS
        assert body["anchor"] == {"kind": "auswahl", "id": None, "from": "2022-05", "to": "2022-06"}
        assert (body["window"]["from"], body["window"]["to"]) == ("2022-02", "2022-07")
        assert body["total"] == 1 and body["items"][0]["title"] == "Mai"

    def test_invalid_months_are_400(self, client, store):
        assert client.get(SELECTION.format(DEMO_3), params={"from": "2022-06", "to": "2022-05"}).status_code == 400
        assert client.get(SELECTION.format(DEMO_3), params={"from": "2022-6", "to": "2022-07"}).status_code == 400
        assert client.get(SELECTION.format(DEMO_3), params={"from": "2022-06"}).status_code == 422

    def test_unknown_company_is_404(self, client, store):
        assert client.get(SELECTION.format(999), params={"from": "2022-05", "to": "2022-06"}).status_code == 404

    def test_existing_routes_unchanged(self, client, store):
        body = client.get(ANOMALIES.format(DEMO_3)).json()
        assert set(body) == {"company_id", "source", "dimension", "series", "anomalies", "outlier_months", "params", "eligibility"}
