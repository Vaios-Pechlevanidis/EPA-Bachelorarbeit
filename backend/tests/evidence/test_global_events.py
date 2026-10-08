"""
Tests für die allgemeinen Ereignisse (Inkrement 4, Schritt 7): Laden mit
Bestätigungsfilter, Überschneidung mit dem Fenster, Belege vom Typ global,
Route /global-events und Einblendung in den Kontext einer Veränderung. Ohne Netz.
"""

import json
import os
import sys
from datetime import datetime, timezone

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

NOW = datetime(2024, 3, 15, 12, 0, tzinfo=timezone.utc)
INFO = {"company_id": 7, "name": "E.ON", "search_term": "E.ON", "exclude": [], "term_confirmed": False,
        "ticker": None, "ticker_scope": None, "eqs_uuid": None, "eqs_name": None}
FAST = {"sleep": lambda s: None, "clock": lambda: 1000.0}


def event(id_, date_from, date_to, confirmed=True, **extra):
    return {"id": id_, "date_from": date_from, "date_to": date_to, "title": f"Ereignis {id_}", "scope": "Deutschland",
            "note": "Vermerk", "url": f"https://example.org/{id_}", "confirmed": confirmed, **extra}


def write_events(path, events):
    path.write_text(json.dumps({"version": 1, "hinweise": {}, "events": events}, ensure_ascii=False), encoding="utf-8")


class TestLoad:

    def test_confirmed_filter_and_validation(self, tmp_path):
        path = tmp_path / "events.json"
        write_events(path, [event("a", "2020-03", "2020-05"), event("b", "2021-01", "2021-02", confirmed=False),
                            {"id": "kaputt", "date_from": "2020-13", "date_to": "2020-14", "title": "x", "scope": "", "note": "", "url": "", "confirmed": True},
                            event("c", "2022-05", "2022-01")])
        assert [e["id"] for e in ev.load_global_events(path)] == ["a"]
        assert [e["id"] for e in ev.load_global_events(path, confirmed_only=False)] == ["a", "b"]
        assert ev.load_global_events(tmp_path / "fehlt.json") == []
        (tmp_path / "bad.json").write_text("{kaputt", encoding="utf-8")
        assert ev.load_global_events(tmp_path / "bad.json") == []

    def test_repository_file_has_only_unconfirmed_proposals(self):
        proposals = ev.load_global_events(confirmed_only=False)
        assert 1 <= len(proposals) <= 10
        assert all(e["url"].startswith("https://") for e in proposals)
        assert ev.load_global_events() == [], "Vorschläge gelten erst nach Bestätigung durch den Autor"


class TestItems:

    def test_overlap_rules(self):
        window = ev.window_for_outlier("2020-04", 1, 1)   # 2020-03 .. 2020-05
        events = [event("vorher", "2019-11", "2020-02"), event("rand", "2020-01", "2020-03"), event("drin", "2020-04", "2020-04"),
                  event("lang", "2019-01", "2021-12"), event("danach", "2020-06", "2020-07")]
        items = ev.global_event_items(events, window)
        assert [i["event"]["id"] for i in items] == ["rand", "drin", "lang"]
        first = items[0]
        assert (first["source"], first["source_type"], first["reliability"], first["language"]) == ("global", "global", "hypothese", "de")
        assert first["id"] == "global:rand" and first["date"] == "2020-01-01" and first["category"] == "Deutschland"
        assert first["event"] == {"id": "rand", "from": "2020-01", "to": "2020-03", "scope": "Deutschland", "note": "Vermerk"}

    def test_window_evidence_includes_confirmed_events(self, tmp_path):
        window = ev.window_for_outlier("2020-04", 1, 1)
        fetcher = FakeRss({"2020-04": [("Zeitung", "https://z/1", "2020-04-03", "P")]})
        result = ev.evidence_for_window(INFO, window, fetchers={"gnews": fetcher}, store_dir=tmp_path, now=NOW,
                                        events=[event("lockdown", "2020-03", "2020-05")], **FAST)
        assert result["counts"] == {"news": 1, "adhoc": 0, "global": 1}
        assert [i["source_type"] for i in result["items"]] == ["news", "global"], "neueste zuerst; Ereignis datiert auf den 1. des Beginnmonats"
        without = ev.evidence_for_window(INFO, window, fetchers={"gnews": fetcher}, store_dir=tmp_path, now=NOW, events=[], **FAST)
        assert without["counts"]["global"] == 0

    def test_default_loads_confirmed_file(self, tmp_path, monkeypatch):
        path = tmp_path / "events.json"
        write_events(path, [event("x", "2020-03", "2020-05")])
        monkeypatch.setattr(ev, "GLOBAL_EVENTS_PATH", path)
        result = ev.evidence_for_window(INFO, ev.window_for_outlier("2020-04", 0, 0), fetchers={"gnews": FakeRss()},
                                        store_dir=tmp_path, now=NOW, **FAST)
        assert result["counts"]["global"] == 1 and result["coverage"] is True


class TestRoute:

    @pytest.fixture(scope="module")
    def client(self, in_memory_db):
        app = FastAPI()
        app.include_router(anomalies_router)
        app.include_router(context_router)
        return TestClient(app)

    def test_global_events_route(self, client, tmp_path, monkeypatch):
        path = tmp_path / "events.json"
        write_events(path, [event("a", "2020-03", "2020-05"), event("b", "2021-01", "2021-02", confirmed=False)])
        monkeypatch.setattr(ev, "GLOBAL_EVENTS_PATH", path)
        body = client.get("/api/analytics/global-events").json()
        assert [e["id"] for e in body["events"]] == ["a"] and body["n_confirmed"] == 1 and body["note"].startswith("Belege sind")
        both = client.get("/api/analytics/global-events", params={"all": "true"}).json()
        assert [e["id"] for e in both["events"]] == ["a", "b"]

    def test_anomaly_context_shows_global_item(self, client, tmp_path, monkeypatch):
        path = tmp_path / "events.json"
        write_events(path, [event("demo", "2022-10", "2023-02")])
        monkeypatch.setattr(ev, "GLOBAL_EVENTS_PATH", path)
        monkeypatch.setattr(ev, "STORE_DIR", tmp_path)
        monkeypatch.setattr(ev, "_failed_fetches", {})
        monkeypatch.setattr(src, "_last_request", {})
        monkeypatch.setattr(src.time, "sleep", lambda s: None)
        monkeypatch.setattr(ev, "company_context_info", lambda cid, metadata=None: {**INFO, "company_id": 3, "name": "Demo 3"} if cid == 3 else None)
        monkeypatch.setattr(news_service, "fetch_rss", FakeRss())
        body = client.get("/api/analytics/company/3/anomalies/employee:durchschnittsbewertung:2023-01/context").json()
        assert body["counts"]["global"] == 1 and body["items"][-1]["source_type"] == "global"
        assert body["items"][-1]["event"]["id"] == "demo"
