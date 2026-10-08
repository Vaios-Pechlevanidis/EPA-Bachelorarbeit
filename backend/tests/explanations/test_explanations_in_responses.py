"""
Tests für die Erklärungsansätze in den bestehenden Antworten (Inkrement 5, A4):
GET …/anomalies/{id}/explanations und GET …/compare füllen ``explanations`` und
``explanation_summary`` aus dem Belegspeicher (tmp_path, kein Abruf), In-Memory-Store
(Demo 3), Stimmung im Lexikon-Modus; Zustand „offen“ ohne Belege; kein Fehler der Route,
wenn die Belege nicht lesbar sind; Sperre je Monat gegen doppelten Abruf. Titel sind
konstruiert (E7).

Ausführung:
    cd backend
    uv run python -m pytest tests/explanations/test_explanations_in_responses.py -q -p no:cacheprovider
"""

import os
import sys
import threading
import time
from datetime import datetime, timezone

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "evidence"))

import services.evidence_service as ev  # noqa: E402
import services.evidence_sources as src  # noqa: E402
import services.explanation_service as es  # noqa: E402
from routes.anomalies import router  # noqa: E402

DEMO_3 = 3
ANOMALIES = "/api/analytics/company/{}/anomalies"
EXPLAIN = "/api/analytics/company/{}/anomalies/{}/explanations"
COMPARE = "/api/analytics/company/{}/compare"
FALL_ID = "employee:durchschnittsbewertung:2023-01"
NOW = datetime(2026, 1, 15, 12, 0, tzinfo=timezone.utc)
ENTRY_FIELDS = {"id", "rank", "confidence", "stage_label", "event", "date", "source", "url", "source_type", "reliability", "language",
                "issuer", "n_items", "publishers", "time_match", "topic_match", "term_match", "terms", "category",
                "time_phrase", "sentiment", "text", "items", "group"}
SUMMARY_FIELDS = {"state", "kind", "window", "n_items", "n_bundles", "n_groups", "n_by_stage", "terms", "item_scores", "sources",
                  "coverage", "reason", "error", "note", "open_note", "rules"}


@pytest.fixture(scope="module")
def client(in_memory_db):
    from models.sentiment_analyzer import SentimentAnalyzer

    es.set_sentiment_analyzer(SentimentAnalyzer(mode="lexicon"))
    app = FastAPI()
    app.include_router(router)
    yield TestClient(app)
    es.set_sentiment_analyzer(None)


@pytest.fixture
def store(tmp_path, monkeypatch):
    """Leerer Speicher in tmp_path, kein Abruf, keine allgemeinen Ereignisse."""
    monkeypatch.setenv(ev.LIVE_FETCH_ENV, "0")
    monkeypatch.setattr(ev, "STORE_DIR", tmp_path)
    monkeypatch.setattr(ev, "GLOBAL_EVENTS_PATH", tmp_path / "keine.json")
    return tmp_path


def _fill(store, info, by_month):
    """Monate mit konstruierten Meldungen ablegen: ``{monat: [(titel, tag, herausgeber), ...]}``."""
    for month, entries in by_month.items():
        items = [src.make_item(title=t, url=f"https://x/{month}/{i}", published_at=f"{day}T10:00:00+00:00", publisher=pub,
                               source="gnews", source_type="news") for i, (t, day, pub) in enumerate(entries)]
        ev.save_record(ev.build_record(info["company_id"], "gnews", month, ev.expected_query(info, "gnews", month), items, NOW), store)


def _fall(client):
    return next(a for a in client.get(ANOMALIES.format(DEMO_3)).json()["anomalies"] if a["id"] == FALL_ID)


class TestAnomalyExplanations:

    def test_open_state_with_empty_store(self, client, store):
        body = client.get(EXPLAIN.format(DEMO_3, FALL_ID)).json()
        s = body["explanation_summary"]
        assert body["explanations"] == [] and s["state"] == "offen" and s["error"] is None
        assert SUMMARY_FIELDS <= set(s) and s["kind"] == "niveauwechsel"
        assert s["coverage"] is False and "Live-Abruf" in (s["reason"] or "") and s["open_note"]
        assert s["window"]["from"] == ev.shift_month(s["window"]["transition_from"], -3)
        assert s["rules"]["stages"]["hoch"].startswith("term_match") and s["rules"]["version"] == 2

    def test_entries_from_store(self, client, store):
        anomaly = _fall(client)
        info = ev.company_context_info(DEMO_3)
        window = ev.window_for_anomaly(anomaly)
        near = ev.shift_month(window["transition_from"], -1)   # Monat vor dem Übergang: time_match 1
        _fill(store, info, {
            near: [("Konzern kündigt Stellenabbau in der Verwaltung an", f"{near}-10", "Blatt A"),
                   ("Konzern kündigt Stellenabbau an", f"{near}-11", "Blatt B"),
                   ("Aktie erreicht neues Kursziel", f"{near}-12", "Blatt C")],
            window["from"]: [("Neuer Chef für den Konzern", f"{window['from']}-05", "Blatt D")],
        })
        body = client.get(EXPLAIN.format(DEMO_3, FALL_ID)).json()
        s = body["explanation_summary"]
        assert s["state"] == "ansaetze" and s["n_items"] == 4 and s["n_bundles"] == 3 and s["coverage"] is True
        assert s["sources"]["gnews"]["from_store"] >= 2
        entries = body["explanations"]
        assert entries and all(ENTRY_FIELDS <= set(e) for e in entries)
        top = entries[0]
        assert top["confidence"] in ("hoch", "mittel") and top["n_items"] == 2 and top["category"]["id"] == "personalabbau"
        assert top["publishers"] == ["Blatt A", "Blatt B"] and top["time_match"] == 1.0 and top["rank"] == 1
        assert top["text"].startswith("Möglicher Zusammenhang: 2 Meldungen zu Personalabbau und Restrukturierung im Monat vor dem Übergang")
        assert top["sentiment"] is not None and set(top["sentiment"]) == {"label", "polarity", "fits_direction"}
        assert [e["confidence"] for e in entries] == sorted((e["confidence"] for e in entries), key=lambda c: ["hoch", "mittel", "niedrig"].index(c))
        assert all(e["confidence"] != "keine" for e in entries)
        scores = s["item_scores"]
        assert len(scores) == 4 and scores[top["id"]]["rank"] == 1
        stock = next(v for v in scores.values() if v["category"] == "ohne_arbeitgeberbezug")
        assert stock["stage"] == "keine" and stock["employer_related"] is False
        assert body["comparison"]["topics"], "der Vergleich bleibt unverändert enthalten"

    def test_terms_from_reviews_reach_the_title(self, client, store):
        """Test: ein kennzeichnender Begriff der Bewertungen im Titel ergibt term_match > 0."""
        first = client.get(EXPLAIN.format(DEMO_3, FALL_ID)).json()["explanation_summary"]
        if not first["terms"]:
            pytest.skip("Demo 3 hat in diesem Vergleich keinen kennzeichnenden Begriff")
        term = first["terms"][0]
        anomaly = _fall(client)
        info = ev.company_context_info(DEMO_3)
        near = ev.shift_month(ev.window_for_anomaly(anomaly)["transition_from"], -1)
        _fill(store, info, {near: [(f"Meldung über {term['term']} im Werk", f"{near}-10", "Blatt")]})
        body = client.get(EXPLAIN.format(DEMO_3, FALL_ID)).json()
        entry = body["explanations"][0]
        assert entry["term_match"] >= 0.5 and entry["terms"][0]["term"] == term["term"]
        assert entry["terms"][0]["after"] == term["after"] and entry["terms"][0]["before"] == term["before"]
        assert f"'{term['term']}' häufiger genannt ({term['after']} gegenüber {term['before']} Bewertungen)" in entry["text"]

    def test_evidence_failure_does_not_break_route(self, client, store, monkeypatch):
        def boom(*args, **kwargs):
            raise OSError("Speicher nicht lesbar")
        monkeypatch.setattr(ev, "evidence_for_window", boom)
        res = client.get(EXPLAIN.format(DEMO_3, FALL_ID))
        assert res.status_code == 200
        s = res.json()["explanation_summary"]
        assert s["state"] == "offen" and s["error"].startswith("OSError") and res.json()["explanations"] == []

    def test_unknown_anomaly_still_404(self, client, store):
        assert client.get(EXPLAIN.format(DEMO_3, "employee:durchschnittsbewertung:1999-01")).status_code == 404


class TestSelectionExplanations:

    def test_selection_and_single_month(self, client, store):
        info = ev.company_context_info(DEMO_3)
        _fill(store, info, {"2024-02": [("Streik im Werk angekündigt", "2024-02-20", "Blatt")]})
        body = client.get(COMPARE.format(DEMO_3), params={"from": "2024-03", "to": "2024-04"}).json()
        s = body["explanation_summary"]
        assert s["kind"] == "auswahl" and s["window"]["anchor_from"] == "2024-03" and s["window"]["to"] == "2024-05"
        assert s["state"] == "ansaetze" and body["explanations"][0]["time_phrase"] == "im Monat vor der Auswahl"
        assert body["explanations"][0]["category"]["id"] == "tarif_streik"
        single = client.get(COMPARE.format(DEMO_3), params={"from": "2024-03", "to": "2024-03"}).json()
        assert single["explanation_summary"]["window"]["from"] == "2023-12" and single["explanation_summary"]["state"] == "ansaetze"

    def test_direction_from_rating_shift(self, client, store):
        body = client.get(COMPARE.format(DEMO_3), params={"from": "2024-03", "to": "2024-04"}).json()
        shift = body["comparison"]["rating_shift"]
        expected = None if not shift else ("fall" if shift < 0 else "rise")
        assert body["explanation_summary"]["direction"] == expected
        assert es._direction_from_shift(-0.3) == "fall" and es._direction_from_shift(0.2) == "rise"
        assert es._direction_from_shift(0.0) is None and es._direction_from_shift(None) is None


class TestMonthLock:

    def test_concurrent_requests_fetch_a_month_once(self, tmp_path, monkeypatch):
        """Test: zwei Anfragen zum selben Monat lösen einen Abruf aus; die zweite liest den Speicher."""
        from _evidence_helpers import rss

        monkeypatch.delenv(ev.LIVE_FETCH_ENV, raising=False)
        monkeypatch.setattr(ev, "_failed_fetches", {})
        monkeypatch.setattr(src, "_last_request", {})
        monkeypatch.setattr(ev, "_month_locks", {})
        calls = []

        def fetcher(query):
            calls.append(query)
            time.sleep(0.05)
            return rss([("Meldung", "https://x/1", "2024-01-10", "P")])

        info = {"company_id": 7, "name": "E.ON", "search_term": "E.ON", "exclude": [], "term_confirmed": False,
                "ticker": None, "ticker_scope": None, "eqs_uuid": None, "eqs_name": None}
        results = []

        def run():
            results.append(ev.month_record(info, "gnews", "2024-01", fetcher=fetcher, store_dir=tmp_path, now=NOW,
                                           sleep=lambda s: None, clock=time.monotonic))
        threads = [threading.Thread(target=run) for _ in range(2)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert len(calls) == 1
        assert sorted(r["fetched_now"] for r in results) == [False, True]
        assert all(r["record"] and len(r["record"]["items"]) == 1 for r in results)
