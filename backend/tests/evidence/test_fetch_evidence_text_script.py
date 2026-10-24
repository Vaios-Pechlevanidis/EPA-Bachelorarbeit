"""
Tests für scripts/fetch_evidence_text.py (Texte der Belege nachfüllen, E35): Kandidaten
(Unternehmen im Titel, zeitliche Nähe ab 0,5; mit --comparison auch Vergleichsfenster),
EQS-Mitteilungen aus dem Speicher, --dry-run, Abruf mit nachgebildeten Antworten und
temporären Speichern, Fortsetzen, Abrufgrenze, CONTEXT_LIVE_FETCH=0, --retry-failed,
Abbruch nach Fehlern in Folge bei Google News (nicht bei Verlagsseiten), --json. Ohne DB
und ohne Netz; alle Titel und Texte sind konstruiert.

Ausführung:
    cd backend
    uv run python -m pytest tests/evidence/test_fetch_evidence_text_script.py -q -p no:cacheprovider
"""

import json
import os
import sys
import urllib.parse
from datetime import datetime, timezone

import pytest

BACKEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
sys.path.insert(0, BACKEND_DIR)
sys.path.insert(0, os.path.join(BACKEND_DIR, "scripts"))

import fetch_evidence_text as script  # noqa: E402
import services.evidence_service as ev  # noqa: E402
import services.evidence_sources as src  # noqa: E402
import services.evidence_text as et  # noqa: E402

NOW = datetime(2026, 10, 23, 12, 0, tzinfo=timezone.utc)
INFO = {"company_id": 7, "name": "E.ON", "search_term": "E.ON", "exclude": [], "term_confirmed": True, "title_words": [],
        "ticker": None, "ticker_scope": None, "eqs_uuid": "u", "eqs_name": "E.ON SE"}
ANCHORS = {"eligible": True, "series_from": "2019-01", "series_to": "2022-12",
           "anomalies": [{"id": "employee:durchschnittsbewertung:2021-09", "date": "2021-09", "previous_period": "2021-08", "gap_months": 0}],
           "outliers": []}
LONG = " ".join(["Der Konzern baut die Verwaltung um und nennt dafür Gründe aus dem Vorjahr."] * 6)


def gl(key):
    return f"https://news.google.com/rss/articles/{key}"


def page(sg="S", ts="1700000000"):
    return f'<c-wiz data-n-a-sg="{sg}" data-n-a-ts="{ts}"></c-wiz>'


def batch(target):
    return ")]}'\n[[\"wrb.fr\",\"Fbv4je\",\"[\\\"garturlres\\\",\\\"" + target + "\\\",1]\",null,null,null,\"generic\"]]\n"


class FakeHttp:
    def __init__(self):
        self.google_fail = set()      # Kennungen, deren Artikelseite bei Google nicht antwortet
        self.publisher_fail = set()   # Zieladressen, die nicht antworten
        self.calls = []

    def get(self, url):
        self.calls.append(("GET", url))
        if url.startswith("https://news.google.com/rss/articles/"):
            key = url.rsplit("/", 1)[-1]
            if key in self.google_fail:
                raise OSError("429")
            return page().encode()
        if url in self.publisher_fail:
            raise OSError("Verlag antwortet nicht")
        return f"<html><body><article><p>{LONG}</p></article></body></html>".encode()

    def post(self, url, data):
        self.calls.append(("POST", url))
        payload = urllib.parse.unquote(data.decode())
        key = next(k for k in ("a1", "b2", "c3", "e5", "f6", "g7", "h8") if f'\\"{k}\\"' in payload or f'"{k}"' in payload)
        return batch(f"https://verlag.example/{key}").encode()


def news(key, title, day):
    return src.make_item(title=title, url=gl(key), published_at=day, publisher="P", source="gnews", source_type="news")


def adhoc(key, title, day):
    return src.make_item(title=title, url=f"https://www.eqs-news.com/news/x/{key}", published_at=day, publisher="EQS News",
                         source="eqs", source_type="adhoc", issuer="E.ON SE", category="Ad-hoc")


@pytest.fixture
def world(tmp_path, monkeypatch):
    store, texts = tmp_path / "context", tmp_path / "context_text"
    monkeypatch.setattr(ev, "STORE_DIR", store)
    monkeypatch.setattr(et, "TEXT_DIR", texts)
    monkeypatch.setattr(src, "_last_request", {})
    monkeypatch.setattr(src, "_source_locks", {})
    monkeypatch.setattr(script.time, "sleep", lambda s: None)
    monkeypatch.setattr(script, "list_companies", lambda: [{"id": 7, "name": "E.ON"}, {"id": 5, "name": "PLEdoc GmbH"}])
    monkeypatch.setattr(script, "company_anchors", lambda cid: ANCHORS if cid == 7 else {"eligible": False, "anomalies": [], "outliers": []})
    monkeypatch.setattr(ev, "company_context_info", lambda cid, metadata=None: dict(INFO) if cid == 7 else None)
    monkeypatch.delenv(ev.LIVE_FETCH_ENV, raising=False)
    http = FakeHttp()
    monkeypatch.setattr(et, "http_get", http.get)
    monkeypatch.setattr(et, "http_post", http.post)
    by_month = {
        "2021-08": [news("a1", "E.ON baut die Verwaltung um", "2021-08-10"),            # Kandidat (Titel, Nähe 1,0)
                    news("b2", "Energie wird teurer", "2021-08-11"),                    # kein Kandidat: Unternehmen nicht genannt
                    adhoc("d4", "E.ON SE: Ad-hoc", "2021-08-12")],
        "2021-06": [news("c3", "E.ON legt Quartalszahlen vor", "2021-06-01")],          # kein Kandidat: Nähe 0,33 (Rand)
        "2020-08": [news("e5", "E.ON im Sommer", "2020-08-10")],                        # Kandidat nur mit Vergleichsfenster (−12)
    }
    for month, items in by_month.items():
        for source in ("gnews", "eqs"):
            mine = [i for i in items if i["source"] == source]
            ev.save_record(ev.build_record(7, source, month, ev.expected_query(INFO, source, month), mine, NOW))
    for month in ("2021-07", "2021-09", "2021-10", "2020-06", "2020-07", "2020-09", "2020-10",
                  "2022-06", "2022-07", "2022-08", "2022-09", "2022-10", "2019-06", "2019-07", "2019-08", "2019-09", "2019-10"):
        for source in ("gnews", "eqs"):
            ev.save_record(ev.build_record(7, source, month, ev.expected_query(INFO, source, month), [], NOW))
    return {"http": http, "store": store, "texts": texts}


def ways(summary, way):
    return summary["ways_summary"][way]


class TestPlan:
    def test_dry_run_counts_candidates_and_fetches_nothing(self, world):
        s = script.run(["eqs", "news"], dry_run=True, verbose=False)
        assert ways(s, "eqs")["candidates"] == 1 and ways(s, "news")["candidates"] == 1
        assert s["fetches"] == 0 and not world["http"].calls and not world["texts"].exists()
        s = script.run(["news"], dry_run=True, comparison=True, verbose=False)
        assert ways(s, "news")["candidates"] == 2 and ways(s, "news")["skipped"] == 2
        eon = next(c for c in s["companies"] if c["company_id"] == 7)
        assert eon["eligible"] and eon["n_windows"] == 1 + 3 and eon["ways"]["news"]["candidates"] == 2
        assert next(c for c in s["companies"] if c["company_id"] == 5).get("error") == "Unternehmen nicht auflösbar"

    def test_candidate_rule(self):
        window = ev.window_for_change("2021-09", "2021-08", 0, 3, 1)
        words = {"eon", "e.on"}
        assert script.is_candidate(news("a", "E.ON baut um", "2021-08-01"), window, words)
        assert not script.is_candidate(news("a", "Energie wird teurer", "2021-08-01"), window, words)
        assert not script.is_candidate(news("a", "E.ON am Rand", "2021-06-01"), window, words)
        assert script.is_candidate(news("a", "E.ON danach", "2021-10-01"), window, words)       # danach 0,5
        assert not script.is_candidate(adhoc("a", "E.ON SE", "2021-08-01"), window, words)       # EQS gehört zum Weg eqs
        assert script.is_candidate(news("a", "irgendwas", "2021-08-01"), window, set())          # ohne Namenswörter nicht prüfbar


class TestRun:
    def test_fetches_and_stores_then_resumes(self, world):
        s = script.run(["eqs", "news"], comparison=True, verbose=False)
        assert s["live"] and s["fetches"] == 3
        assert ways(s, "eqs") == {**ways(s, "eqs"), "candidates": 1, "fetched_now": 1, "ok": 1, "fehlgeschlagen": 0}
        assert ways(s, "news")["fetched_now"] == 2 and ways(s, "news")["ok"] == 2
        files = sorted(p.name for p in (world["texts"] / "7").glob("*.json"))
        assert len(files) == 3
        rec = et.load_text(7, news("a1", "E.ON baut die Verwaltung um", "2021-08-10")["id"])
        assert rec["status"] == "ok" and rec["target_url"] == "https://verlag.example/a1" and "Verwaltung" in rec["text"]
        calls_before = len(world["http"].calls)
        again = script.run(["eqs", "news"], comparison=True, verbose=False)
        assert again["fetches"] == 0 and ways(again, "news")["stored"] == 2 and ways(again, "eqs")["stored"] == 1
        assert len(world["http"].calls) == calls_before

    def test_fetch_limit_and_live_switch(self, world, monkeypatch):
        s = script.run(["news"], comparison=True, max_fetches=1, verbose=False)
        assert s["fetches"] == 1 and s["fetch_limit_reached"] and ways(s, "news")["skipped"] == 1
        monkeypatch.setenv(ev.LIVE_FETCH_ENV, "0")
        s = script.run(["eqs"], verbose=False)
        assert not s["live"] and s["fetches"] == 0 and ways(s, "eqs")["skipped"] == 1

    def test_retry_failed_only_on_request(self, world):
        world["http"].publisher_fail.add("https://verlag.example/a1")
        s = script.run(["news"], verbose=False)
        assert ways(s, "news")["fehlgeschlagen"] == 1 and ways(s, "news")["errors"][0]["error"].startswith("OSError")
        assert not ways(s, "news").get("aborted"), "ein Verlag, der nicht antwortet, bricht nicht ab"
        world["http"].publisher_fail.clear()
        s = script.run(["news"], verbose=False)
        assert s["fetches"] == 0 and ways(s, "news")["stored"] == 1 and ways(s, "news")["fehlgeschlagen"] == 1
        s = script.run(["news"], retry_failed=True, verbose=False)
        assert s["fetches"] == 1 and ways(s, "news")["ok"] == 1

    def test_aborts_after_consecutive_google_failures(self, world):
        extra = [news(k, f"E.ON Meldung {k}", "2021-08-1" + str(i)) for i, k in enumerate(("f6", "g7", "h8"))]
        rec = ev.load_record(7, "gnews", "2021-08")
        rec["items"] += extra
        ev.save_record(rec)
        world["http"].google_fail.update({"a1", "f6", "g7", "h8"})
        s = script.run(["news"], comparison=True, verbose=False, max_consecutive_errors=3)
        t = ways(s, "news")
        assert t["aborted"] and t["aborted"]["after_errors"] == 3 and t["aborted"]["company_id"] == 7
        assert t["fetched_now"] == 3 and t["fehlgeschlagen"] == 3 and t["skipped"] == 2   # h8 und e5 übersprungen
        text = script.format_summary(s)
        assert "ABGEBROCHEN nach 3 Fehlern in Folge bei E.ON (7)" in text and "--news --company 7" in text

    def test_main_writes_json_and_summary(self, world, tmp_path, capsys):
        out = tmp_path / "sum.json"
        assert script.main(["--eqs", "--news", "--comparison", "--quiet", "--json", str(out)]) == 0
        printed = capsys.readouterr().out
        assert "Texte der Belege nachfüllen (E35)" in printed and "Kandidaten 2" in printed and "Kandidaten 1" in printed
        data = json.loads(out.read_text(encoding="utf-8"))
        assert data["ways"] == ["eqs", "news"] and data["fetches"] == 3 and data["comparison"] is True

    def test_database_outage_skips_the_company_and_continues(self, world, monkeypatch):
        calls = []

        def anchors(cid):
            calls.append(cid)
            if cid == 5:
                raise ConnectionError("nodename nor servname provided")
            return ANCHORS
        monkeypatch.setattr(script, "company_anchors", anchors)
        monkeypatch.setattr(script, "list_companies", lambda: [{"id": 5, "name": "PLEdoc GmbH"}, {"id": 7, "name": "E.ON"}])
        monkeypatch.setattr(ev, "company_context_info", lambda cid, metadata=None: dict(INFO, company_id=cid))
        s = script.run(["news"], verbose=False)
        assert calls == [5, 7] and s["fetches"] == 1
        first = s["companies"][0]
        assert first["error"].startswith("ConnectionError") and first["ways"] == {}
        assert "Übersprungene Unternehmen" in script.format_summary(s) and "PLEdoc GmbH (5)" in script.format_summary(s)

    def test_requires_a_way(self):
        with pytest.raises(SystemExit):
            script.main(["--dry-run"])
