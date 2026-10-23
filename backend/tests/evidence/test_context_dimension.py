"""
Tests für die Belege-Routen mit der Dimension als globalem Filter (2026-10-23, E34):
dimension_only auf GET /api/analytics/company/{id}/context?from=&to= und auf der
Route der Veränderung. Abruf nachgebildet, Speicher in tmp_path.

Ausführen:
    cd backend
    uv run python -m pytest tests/evidence/test_context_dimension.py -q -p no:cacheprovider
"""

import os
import sys

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import services.evidence_service as ev  # noqa: E402
import services.evidence_sources as src  # noqa: E402
from services import news_service  # noqa: E402
from routes.anomalies import router as anomalies_router  # noqa: E402
from routes.context import router as context_router  # noqa: E402
from _evidence_helpers import FakeRss  # noqa: E402

DEMO_3 = 3
CONTEXT = "/api/analytics/company/{}/anomalies/{}/context"
SELECTION = "/api/analytics/company/{}/context"
FALL_ID = "employee:durchschnittsbewertung:2023-01"
INFO = {"company_id": DEMO_3, "name": "Demo 3", "search_term": '"Demo 3"', "exclude": [], "term_confirmed": False,
        "ticker": None, "ticker_scope": None, "eqs_uuid": None, "eqs_name": None}
SCOPE = {"from": "2022-05", "to": "2022-06", "source": "employee", "dimension": "gehalt_sozialleistungen"}
TITLES = [("Gehaltserhöhung bei Demo 3", "https://x/1", "2022-05-10", "Blatt"),
          ("Warnstreik bei Demo 3", "https://x/2", "2022-05-12", "Blatt"),
          ("Demo 3 gewinnt das Spiel", "https://x/3", "2022-05-15", "Blatt")]


@pytest.fixture(autouse=True)
def no_repository_events(tmp_path, monkeypatch):
    monkeypatch.setattr(ev, "GLOBAL_EVENTS_PATH", tmp_path / "keine_ereignisse.json")


@pytest.fixture(scope="module")
def client(in_memory_db):
    app = FastAPI()
    app.include_router(anomalies_router)
    app.include_router(context_router)
    return TestClient(app)


@pytest.fixture
def store(tmp_path, monkeypatch):
    fetcher = FakeRss()
    monkeypatch.setattr(ev, "STORE_DIR", tmp_path)
    monkeypatch.setattr(ev, "_failed_fetches", {})
    monkeypatch.setattr(src, "_last_request", {})
    monkeypatch.setattr(src.time, "sleep", lambda s: None)
    monkeypatch.setattr(ev, "company_context_info", lambda cid, metadata=None: dict(INFO) if cid == DEMO_3 else None)
    monkeypatch.setattr(news_service, "fetch_rss", fetcher)
    monkeypatch.delenv(ev.LIVE_FETCH_ENV, raising=False)
    fetcher.dir = tmp_path
    fetcher.by_month["2022-05"] = list(TITLES)
    return fetcher


class TestSelectionScope:

    def test_only_evidence_of_the_dimension(self, client, store):
        body = client.get(SELECTION.format(DEMO_3), params={**SCOPE, "dimension_only": True}).json()
        assert [i["title"] for i in body["items"]] == ["Warnstreik bei Demo 3", "Gehaltserhöhung bei Demo 3"]
        assert body["items"][0]["dimension_match"] == {"terms": [], "category": "Tarifverhandlung und Streik"}
        assert body["items"][1]["dimension_match"]["terms"] == ["gehaltserhöhung"]
        assert body["total"] == 2 and body["counts"] == {"news": 2, "adhoc": 0, "global": 0} and body["coverage"] is True
        assert body["scope"]["n_all"] == 3 and body["scope"]["n_dimension"] == 2 and body["scope"]["topic"] == "Gehalt & Sozialleistungen"
        assert body["anchor"] == {"kind": "auswahl", "id": None, "from": "2022-05", "to": "2022-06"}

    def test_without_filter_unchanged(self, client, store):
        body = client.get(SELECTION.format(DEMO_3), params=SCOPE).json()
        assert body["total"] == 3 and "scope" not in body and all("dimension_match" not in i for i in body["items"])

    def test_pagination_after_filter(self, client, store):
        body = client.get(SELECTION.format(DEMO_3), params={**SCOPE, "dimension_only": True, "limit": 1}).json()
        assert body["total"] == 2 and len(body["items"]) == 1

    def test_empty_with_reason(self, client, store):
        store.by_month["2022-05"] = [TITLES[2]]
        body = client.get(SELECTION.format(DEMO_3), params={**SCOPE, "dimension_only": True}).json()
        assert body["items"] == [] and body["coverage"] is False and body["scope"]["n_all"] == 1
        assert body["reason"] == ev.NO_EVIDENCE_IN_DIMENSION if hasattr(ev, "NO_EVIDENCE_IN_DIMENSION") else "Dimension" in body["reason"]

    @pytest.mark.parametrize("params", [
        {"dimension_only": True},                                                           # ohne dimension
        {"source": "employee", "dimension": "durchschnittsbewertung", "dimension_only": True},  # Gesamtbewertung
        {"source": "employee", "dimension": "schnelle_antwort"},                            # Dimension der anderen Quelle
        {"source": "kunden", "dimension": "image"},                                         # Quelle ungültig
    ])
    def test_invalid_is_400(self, client, store, params):
        res = client.get(SELECTION.format(DEMO_3), params={"from": "2022-05", "to": "2022-06", **params})
        assert res.status_code == 400 and isinstance(res.json()["detail"], str)


class TestAnchorScope:

    def test_overall_change_is_400(self, client, store):
        res = client.get(CONTEXT.format(DEMO_3, FALL_ID), params={"dimension_only": True})
        assert res.status_code == 400 and "Einzeldimension" in res.json()["detail"]

    def test_single_dimension_change(self, client, store):
        """Test: Veränderung einer Einzeldimension (falls Demo 3 eine hat): Belege nur zur Dimension."""
        body = client.get("/api/analytics/company/{}/anomalies".format(DEMO_3), params={"dimension": "gehalt_sozialleistungen"}).json()
        if not body["anomalies"]:
            pytest.skip("Demo 3 hat keine Veränderung in Gehalt/Sozialleistungen")
        anomaly = body["anomalies"][0]
        month = anomaly["date"]
        store.by_month[month] = [("Gehaltserhöhung bei Demo 3", "https://x/9", f"{month}-05", "Blatt"),
                                 ("Demo 3 gewinnt das Spiel", "https://x/8", f"{month}-06", "Blatt")]
        res = client.get(CONTEXT.format(DEMO_3, anomaly["id"]), params={"dimension_only": True})
        assert res.status_code == 200
        out = res.json()
        assert [i["title"] for i in out["items"]] == ["Gehaltserhöhung bei Demo 3"] and out["scope"]["dimension"] == "gehalt_sozialleistungen"
