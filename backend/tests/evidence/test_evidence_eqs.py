"""
Tests für EQS News als zweite Quelle und GDELT hinter dem Schalter (Inkrement 4,
Schritt 5): Umformung der Datensätze, Linkbildung, Monatsfilter, Seiten,
Emittent im Beleg, Suche der companyUUID, Ausfall einer Quelle neben der
anderen. Ohne Netz.
"""

import json
import os
import sys
from datetime import datetime, timezone
from urllib.parse import parse_qs, urlparse

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import services.evidence_service as ev  # noqa: E402
import services.evidence_sources as src  # noqa: E402
from _evidence_helpers import FakeRss  # noqa: E402

NOW = datetime(2024, 3, 15, 12, 0, tzinfo=timezone.utc)
INFO = {"company_id": 26, "name": "Carl Zeiss", "search_term": '"Carl Zeiss"', "exclude": [], "term_confirmed": False,
        "ticker": "AFX.DE", "ticker_scope": "Konzerngesellschaft", "eqs_uuid": "5b6d0000-ea7c-11e8-902f-2c44fd856d8c",
        "eqs_name": "Carl Zeiss Meditec AG"}
FAST = {"sleep": lambda s: None, "clock": lambda: 1000.0}


def record(i, date, headline="Quartalszahlen veröffentlicht: Umsatz & Ergebnis", category="Ad-hoc", language="de",
           company="Carl Zeiss Meditec AG", total=1):
    return {"id": f"aaaa{i:04d}-0000-0000-0000-000000000000_{language}", "dtcreated": date, "date": date, "dateUtc": date,
            "apiType": "news", "locale": "['en', 'de']", "category": category, "categoryCode": "ADH", "category_id": "ADH",
            "companyName": company, "companyUUID": INFO["eqs_uuid"], "isin": "DE0005313704", "timezone": "Europe/Berlin",
            "headline": headline, "language": language, "totalItem": str(total)}


def body(records):
    return json.dumps({"status": 200, "records": records, "error": [], "module": "news"}).encode()


class FakeEqs:
    def __init__(self, pages=None, error=None):
        self.pages = pages or {}
        self.error = error
        self.urls = []

    def __call__(self, url):
        self.urls.append(url)
        if self.error:
            raise self.error
        page = int((parse_qs(urlparse(url).query).get("page") or ["1"])[0])
        return body(self.pages.get(page, []))


@pytest.fixture(autouse=True)
def clean(monkeypatch):
    monkeypatch.setattr(ev, "_failed_fetches", {})
    monkeypatch.setattr(src, "_last_request", {})
    monkeypatch.delenv(ev.LIVE_FETCH_ENV, raising=False)
    monkeypatch.delenv(ev.GDELT_ENV, raising=False)


class TestEqsTransform:

    def test_url_pattern_and_slug(self):
        r = record(1, "2023-12-05 10:00:00", headline="Sebastian  Weiss", category="Voting rights")
        assert src.eqs_news_url(r) == "https://www.eqs-news.com/news/voting-rights/sebastian-weiss/aaaa0001-0000-0000-0000-000000000000"
        assert src.slugify("Übernahme-Angebot: Große Chance für Aktionäre!") == "ubernahme-angebot-grosse-chance-fur-aktionare"

    def test_month_fetch_items(self):
        fetcher = FakeEqs({1: [
            record(1, "2023-12-05 10:00:00"),
            record(2, "2024-01-01 00:30:00", headline="Außerhalb"),            # Folgemonat: end_date ist unscharf
            record(3, "2023-12-20 08:00:00", headline="Voting", category="Voting rights", language="en"),
        ]})
        items, query = src.fetch_eqs_month(INFO, "2023-12", fetcher)
        assert "company_name=5b6d0000" in query and "start_date=2023-12-01" in query and "end_date=2024-01-01" in query
        assert [i["title"] for i in items] == ["Quartalszahlen veröffentlicht: Umsatz & Ergebnis", "Voting"]
        first = items[0]
        assert (first["source"], first["source_type"], first["reliability"], first["publisher"]) == ("eqs", "adhoc", "hoch", "EQS News")
        assert first["issuer"] == "Carl Zeiss Meditec AG" and first["category"] == "Ad-hoc" and first["language"] == "de"
        assert first["date"] == "2023-12-05" and first["datetime"] == "2023-12-05T10:00:00+00:00"
        assert items[1]["language"] == "en"

    def test_pagination(self):
        page1 = [record(i, f"2023-12-{(i % 28) + 1:02d} 09:00:00", headline=f"M {i}", total=150) for i in range(100)]
        page2 = [record(i, f"2023-12-{(i % 28) + 1:02d} 09:00:00", headline=f"M {i}", total=150) for i in range(100, 150)]
        fetcher = FakeEqs({1: page1, 2: page2})
        items, _ = src.fetch_eqs_month(INFO, "2023-12", fetcher)
        assert len(fetcher.urls) == 2 and len(items) == 150

    def test_backend_error_raises(self):
        fetcher = lambda url: json.dumps({"error": {"status": 500, "message": "API Unavailable"}}).encode()  # noqa: E731
        with pytest.raises(ValueError, match="API Unavailable"):
            src.fetch_eqs_month(INFO, "2023-12", fetcher)

    def test_without_uuid(self):
        with pytest.raises(ValueError, match="companyUUID"):
            src.fetch_eqs_month({**INFO, "eqs_uuid": None}, "2023-12", FakeEqs())

    def test_search_companies(self):
        fetcher = FakeEqs({1: [{"companyName": "Bechtle AG", "companyUUID": "5b745f9b-ea7c-11e8-902f-2c44fd856d8c",
                                "isin": "DE0005158703", "country": "Deutschland", "total": "2"}]})
        hits = src.eqs_search_companies("Bechtle", fetcher)
        assert hits == [{"company_name": "Bechtle AG", "uuid": "5b745f9b-ea7c-11e8-902f-2c44fd856d8c",
                         "isin": "DE0005158703", "country": "Deutschland"}]
        assert "search=Bechtle" in fetcher.urls[0]


class TestTwoSources:

    def test_eqs_failure_does_not_block_gnews(self, tmp_path):
        gnews = FakeRss({"2023-12": [("Zeitung", "https://z/1", "2023-12-03", "P")]})
        eqs = FakeEqs(error=OSError("EQS weg"))
        window = ev.window_for_outlier("2023-12", 0, 0)
        result = ev.evidence_for_window(INFO, window, fetchers={"gnews": gnews, "eqs": eqs}, store_dir=tmp_path, now=NOW, **FAST)
        assert [i["title"] for i in result["items"]] == ["Zeitung"]
        assert result["sources"]["gnews"]["status"] == "ok" and result["sources"]["eqs"]["status"] == "fehlgeschlagen"
        assert result["counts"] == {"news": 1, "adhoc": 0, "global": 0} and result["coverage"] is True

    def test_both_sources_counted(self, tmp_path):
        gnews = FakeRss({"2023-12": [("Zeitung", "https://z/1", "2023-12-03", "P")]})
        eqs = FakeEqs({1: [record(1, "2023-12-05 10:00:00")]})
        window = ev.window_for_outlier("2023-12", 0, 0)
        result = ev.evidence_for_window(INFO, window, fetchers={"gnews": gnews, "eqs": eqs}, store_dir=tmp_path, now=NOW, **FAST)
        assert result["counts"] == {"news": 1, "adhoc": 1, "global": 0}
        assert (tmp_path / "26" / "eqs" / "2023-12.json").exists()
        assert ev.available_sources(INFO) == ["gnews", "eqs"]


class TestGdelt:

    def test_disabled_by_default_and_enabled_by_switch(self, monkeypatch):
        assert "gdelt" not in ev.available_sources(INFO)
        monkeypatch.setenv(ev.GDELT_ENV, "1")
        assert ev.available_sources(INFO)[-1] == "gdelt"

    def test_month_fetch(self):
        payload = {"articles": [
            {"title": "Zeiss expands", "url": "https://g/1", "seendate": "20231205T100000Z", "domain": "g.example", "language": "English"},
            {"title": "Zu spät", "url": "https://g/2", "seendate": "20240101T100000Z", "domain": "g.example", "language": "German"},
        ]}
        fetcher = lambda url: json.dumps(payload).encode()  # noqa: E731
        items, url = src.fetch_gdelt_month(INFO, "2023-12", fetcher)
        assert "startdatetime=20231201000000" in url and "enddatetime=20231231235959" in url
        assert [i["title"] for i in items] == ["Zeiss expands"]
        assert (items[0]["source"], items[0]["source_type"], items[0]["language"], items[0]["publisher"]) == ("gdelt", "news", "en", "g.example")
        assert src.fetch_gdelt_month(INFO, "2023-12", lambda url: b"")[0] == []


class TestParallelSources:
    """Nachschärfung A2: die Quellen laufen nebeneinander (je Quelle ein Strang), der
    Mindestabstand gilt je Quelle auch über Stränge hinweg."""

    def test_sources_run_side_by_side(self, tmp_path):
        import threading

        from _evidence_helpers import rss

        barrier = threading.Barrier(2, timeout=3)   # beide Abrufe müssen gleichzeitig laufen, sonst BrokenBarrierError

        def gnews(query):
            barrier.wait()
            return rss([("Zeitung", "https://z/1", "2023-12-03", "P")])

        def eqs(url):
            barrier.wait()
            return body([record(1, "2023-12-05 10:00:00")])

        window = ev.window_for_outlier("2023-12", 0, 0)
        result = ev.evidence_for_window(INFO, window, fetchers={"gnews": gnews, "eqs": eqs}, store_dir=tmp_path, now=NOW, **FAST)
        assert (result["sources"]["gnews"]["status"], result["sources"]["eqs"]["status"]) == ("ok", "ok")
        assert result["counts"] == {"news": 1, "adhoc": 1, "global": 0}
        assert list(result["sources"]) == ["gnews", "eqs"], "Reihenfolge der Quellen bleibt"

    def test_source_failure_in_one_thread_leaves_the_other(self, tmp_path):
        gnews = FakeRss({"2023-12": [("Zeitung", "https://z/1", "2023-12-03", "P")]})
        eqs = FakeEqs(error=ValueError("EQS: 503"))
        result = ev.evidence_for_window(INFO, ev.window_for_outlier("2023-12", 1, 0), fetchers={"gnews": gnews, "eqs": eqs},
                                        store_dir=tmp_path, now=NOW, **FAST)
        assert result["sources"]["eqs"]["status"] == "fehlgeschlagen" and result["sources"]["gnews"]["status"] == "ok"
        assert result["coverage"] is True and "503" in result["sources"]["eqs"]["errors"][0]["error"]

    def test_throttle_lock_keeps_the_interval_between_threads(self):
        import threading
        import time

        starts = []

        def worker():
            src.throttle("probe", interval=0.15)
            starts.append(time.monotonic())

        threads = [threading.Thread(target=worker) for _ in range(2)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert len(starts) == 2 and abs(starts[1] - starts[0]) >= 0.14, "zweiter Abruf derselben Quelle wartet"
        assert src.throttle("other", interval=0.15) == 0.0, "andere Quelle wartet nicht"
