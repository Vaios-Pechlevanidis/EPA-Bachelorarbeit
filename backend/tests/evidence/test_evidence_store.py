"""
Tests für den Belegspeicher und die Hauptquelle (Inkrement 4, Schritt 2):
Monatsabfrage, Normalisierung, Speicher je Unternehmen/Quelle/Monat, erneuter
Abruf (abgeschlossener vs. laufender Monat, geänderter Suchbegriff), Duplikate,
Ausfall einer Quelle, CONTEXT_LIVE_FETCH=0 und Drosselung. Ohne Netz, mit
nachgebildetem Abruf und temporärem Speicher.

Ausführen:
    cd backend
    uv run python -m pytest tests/evidence/test_evidence_store.py -q -p no:cacheprovider
"""

import os
import sys
from datetime import datetime, timedelta, timezone
from email.utils import format_datetime

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))

import services.evidence_service as ev  # noqa: E402
import services.evidence_sources as src  # noqa: E402
from services import context_service  # noqa: E402

NOW = datetime(2024, 3, 15, 12, 0, tzinfo=timezone.utc)
INFO = {"company_id": 7, "name": "E.ON", "search_term": "E.ON", "exclude": [], "term_confirmed": False,
        "ticker": "EOAN.DE", "ticker_scope": "eigene Aktie", "eqs_uuid": None, "eqs_name": None}
FAST = {"sleep": lambda s: None, "clock": lambda: 1000.0}


def rss(entries):
    """RSS-Antwort wie Google News: Titel mit angehängter Quelle, Link, pubDate, source."""
    items = []
    for title, url, day, publisher in entries:
        pub = format_datetime(datetime.fromisoformat(day + "T10:00:00+00:00"))
        items.append(f"<item><title>{title} - {publisher}</title><link>{url}</link><pubDate>{pub}</pubDate>"
                     f"<source url=\"https://{publisher.lower()}.example\">{publisher}</source></item>")
    return ("<?xml version=\"1.0\"?><rss version=\"2.0\"><channel><title>t</title><language>de</language>"
            + "".join(items) + "</channel></rss>").encode("utf-8")


class FakeRss:
    """Abruf je Monat: Einträge aus ``by_month``; Monate in ``fail`` werfen; zählt Abfragen."""

    def __init__(self, by_month=None, fail=()):
        self.by_month = by_month or {}
        self.fail = set(fail)
        self.queries = []

    def __call__(self, query):
        self.queries.append(query)
        month = query.split("after:")[1][:7]
        if month in self.fail:
            raise OSError("Netz weg")
        return rss(self.by_month.get(month, []))


@pytest.fixture(autouse=True)
def clean(monkeypatch):
    monkeypatch.setattr(ev, "_failed_fetches", {})
    monkeypatch.setattr(src, "_last_request", {})
    monkeypatch.delenv(ev.LIVE_FETCH_ENV, raising=False)
    monkeypatch.delenv(ev.GDELT_ENV, raising=False)


# ── Abfrage und Normalisierung ───────────────────────────────────────────────

class TestGnews:

    def test_month_query_format(self):
        q = src.gnews_month_query('"Deutsche Telekom"', "2023-12", ["Baskets", "FC Carl Zeiss"])
        assert q == '"Deutsche Telekom" after:2023-12-01 before:2024-01-01 -Baskets -"FC Carl Zeiss"'
        assert src.gnews_month_query("E.ON", "2024-02") == "E.ON after:2024-02-01 before:2024-03-01"

    def test_fetch_month_normalizes_items(self):
        fetcher = FakeRss({"2023-12": [
            ("Meldung A", "https://a.example/1", "2023-12-03", "Zeitung"),
            ("Meldung B", "https://b.example/2", "2023-12-20", "Portal"),
            ("Meldung A", "https://a.example/1", "2023-12-03", "Zeitung"),   # Duplikat (Link)
        ]})
        items, query = src.fetch_gnews_month("E.ON", "2023-12", fetcher=fetcher)
        assert query == "E.ON after:2023-12-01 before:2024-01-01"
        assert [i["title"] for i in items] == ["Meldung B", "Meldung A"]
        first = items[1]
        assert (first["date"], first["publisher"], first["url"]) == ("2023-12-03", "Zeitung", "https://a.example/1")
        assert (first["source"], first["source_type"], first["reliability"], first["language"]) == ("gnews", "news", "mittel", None)
        assert set(first) == {"id", "date", "datetime", "title", "publisher", "url", "source", "source_type",
                              "reliability", "language", "issuer", "category"}

    def test_dedupe_by_normalized_title(self):
        a = src.make_item(title="Neuer Chef: Wechsel an der Spitze!", url="https://x/1", published_at="2024-01-01",
                          publisher=None, source="gnews", source_type="news")
        b = src.make_item(title="neuer chef  wechsel an der spitze", url="https://y/2", published_at="2024-01-02",
                          publisher=None, source="gnews", source_type="news")
        assert len(src.dedupe([a, b])) == 1

    def test_market_type_is_reserved(self):
        with pytest.raises(ValueError, match="reserviert"):
            src.make_item(title="x", url="https://x", published_at=None, publisher=None, source="gnews", source_type="market")
        assert src.RELIABILITY == {"adhoc": "hoch", "news": "mittel", "global": "hypothese"}


# ── Speicher ─────────────────────────────────────────────────────────────────

class TestStore:

    def test_roundtrip_and_layout(self, tmp_path):
        record = ev.build_record(7, "gnews", "2023-12", "q", [], NOW)
        path = ev.save_record(record, tmp_path)
        assert path == tmp_path / "7" / "gnews" / "2023-12.json"
        assert ev.load_record(7, "gnews", "2023-12", tmp_path) == record
        assert record["complete_month"] is True and record["status"] == "ok"
        assert ev.load_record(8, "gnews", "2023-12", tmp_path) is None
        assert not [p for p in path.parent.iterdir() if p.suffix == ".tmp"]

    def test_record_validity(self):
        complete = ev.build_record(7, "gnews", "2023-12", "q", [], NOW)
        assert ev.record_is_current(complete, "2023-12", NOW + timedelta(days=400), "q")
        assert not ev.record_is_current(complete, "2023-12", NOW, "anderer Suchbegriff")
        current = ev.build_record(7, "gnews", "2024-03", "q", [], NOW)
        assert ev.record_is_current(current, "2024-03", NOW + timedelta(hours=11), "q")
        assert not ev.record_is_current(current, "2024-03", NOW + timedelta(hours=13), "q")
        assert not ev.record_is_current({**complete, "status": "error"}, "2023-12", NOW, "q")
        assert not ev.record_is_current(None, "2023-12", NOW, "q")

    def test_invalid_keys(self, tmp_path):
        with pytest.raises(ValueError):
            ev.record_path(7, "gnews", "2023-13", tmp_path)
        with pytest.raises(ValueError):
            ev.record_path(7, "../x", "2023-12", tmp_path)


# ── Belege eines Fensters ────────────────────────────────────────────────────

WINDOW = ev.window_for_change("2024-02", "2024-01", 0)   # 2023-11 .. 2024-03


class TestWindowEvidence:

    def test_fetches_each_month_once_then_uses_store(self, tmp_path):
        fetcher = FakeRss({"2023-12": [("Alt", "https://a/1", "2023-12-05", "P")],
                           "2024-02": [("Neu", "https://a/2", "2024-02-10", "P")]})
        result = ev.evidence_for_window(INFO, WINDOW, fetchers={"gnews": fetcher}, store_dir=tmp_path, now=NOW, **FAST)
        assert len(fetcher.queries) == 5 and [i["title"] for i in result["items"]] == ["Neu", "Alt"]
        assert result["coverage"] is True and result["counts"] == {"news": 2, "adhoc": 0, "global": 0}
        s = result["sources"]["gnews"]
        assert (s["status"], s["fetched_now"], s["from_store"], s["missing"], s["errors"]) == ("ok", 5, 0, 0, [])
        again = ev.evidence_for_window(INFO, WINDOW, fetchers={"gnews": fetcher}, store_dir=tmp_path, now=NOW, **FAST)
        assert len(fetcher.queries) == 5, "abgeschlossene und frische Monate werden nicht erneut abgerufen"
        assert again["sources"]["gnews"]["from_store"] == 5 and again["items"] == result["items"]
        assert result["note"].startswith("Belege sind zeitlich nahe Meldungen")

    def test_current_month_refetched_after_12_hours(self, tmp_path):
        fetcher = FakeRss()
        ev.evidence_for_window(INFO, WINDOW, fetchers={"gnews": fetcher}, store_dir=tmp_path, now=NOW, **FAST)
        later = NOW + timedelta(hours=13)
        ev.evidence_for_window(INFO, WINDOW, fetchers={"gnews": fetcher}, store_dir=tmp_path, now=later, **FAST)
        assert fetcher.queries[5:] == ["E.ON after:2024-03-01 before:2024-04-01"], "nur der laufende Monat"

    def test_changed_search_term_invalidates_store(self, tmp_path):
        fetcher = FakeRss()
        ev.evidence_for_window(INFO, WINDOW, fetchers={"gnews": fetcher}, store_dir=tmp_path, now=NOW, **FAST)
        other = {**INFO, "search_term": '"E.ON SE"'}
        ev.evidence_for_window(other, WINDOW, fetchers={"gnews": fetcher}, store_dir=tmp_path, now=NOW, **FAST)
        assert len(fetcher.queries) == 10 and fetcher.queries[-1].startswith('"E.ON SE" after:')

    def test_duplicates_and_window_limits(self, tmp_path):
        fetcher = FakeRss({
            "2023-12": [("Grenze", "https://a/9", "2024-01-01", "P"), ("Davor", "https://a/0", "2023-10-30", "P")],
            "2024-01": [("Grenze", "https://a/9", "2024-01-01", "P"), ("Jan", "https://a/3", "2024-01-15", "P")],
        })
        result = ev.evidence_for_window(INFO, WINDOW, fetchers={"gnews": fetcher}, store_dir=tmp_path, now=NOW, **FAST)
        assert [i["title"] for i in result["items"]] == ["Jan", "Grenze"], "Duplikat einmal, Oktober außerhalb"

    def test_source_failure_is_isolated_and_not_retried_within_ttl(self, tmp_path):
        fetcher = FakeRss({"2024-01": [("Jan", "https://a/3", "2024-01-15", "P")]}, fail={"2023-12"})
        result = ev.evidence_for_window(INFO, WINDOW, fetchers={"gnews": fetcher}, store_dir=tmp_path, now=NOW, **FAST)
        s = result["sources"]["gnews"]
        assert [i["title"] for i in result["items"]] == ["Jan"] and result["coverage"] is True
        assert s["status"] == "teilweise" and s["missing"] == 1 and [e["month"] for e in s["errors"]] == ["2023-12"]
        assert "OSError" in s["errors"][0]["error"]
        assert not (tmp_path / "7" / "gnews" / "2023-12.json").exists(), "Fehlschlag wird nicht gespeichert"
        n = len(fetcher.queries)
        again = ev.evidence_for_window(INFO, WINDOW, fetchers={"gnews": fetcher}, store_dir=tmp_path, now=NOW, **FAST)
        assert len(fetcher.queries) == n, "innerhalb der Sperrfrist kein neuer Versuch"
        assert again["sources"]["gnews"]["errors"][0]["month"] == "2023-12"

    def test_all_months_fail(self, tmp_path):
        fetcher = FakeRss(fail={"2023-11", "2023-12", "2024-01", "2024-02", "2024-03"})
        result = ev.evidence_for_window(INFO, WINDOW, fetchers={"gnews": fetcher}, store_dir=tmp_path, now=NOW, **FAST)
        assert result["items"] == [] and result["coverage"] is False
        assert result["sources"]["gnews"]["status"] == "fehlgeschlagen" and "nicht abrufbar" in result["reason"]

    def test_no_hits(self, tmp_path):
        result = ev.evidence_for_window(INFO, WINDOW, fetchers={"gnews": FakeRss()}, store_dir=tmp_path, now=NOW, **FAST)
        assert result["items"] == [] and result["reason"] == "Kein Beleg im Fenster gefunden."

    def test_live_fetch_disabled_uses_store_only(self, tmp_path, monkeypatch):
        fetcher = FakeRss({"2024-01": [("Jan", "https://a/3", "2024-01-15", "P")]})
        ev.evidence_for_window(INFO, ev.window_for_outlier("2024-01", 0, 0), fetchers={"gnews": fetcher},
                               store_dir=tmp_path, now=NOW, **FAST)
        monkeypatch.setenv(ev.LIVE_FETCH_ENV, "0")
        result = ev.evidence_for_window(INFO, WINDOW, fetchers={"gnews": fetcher}, store_dir=tmp_path, now=NOW, **FAST)
        assert len(fetcher.queries) == 1, "kein Abruf bei CONTEXT_LIVE_FETCH=0"
        assert [i["title"] for i in result["items"]] == ["Jan"]
        s = result["sources"]["gnews"]
        assert s["from_store"] == 1 and s["missing"] == 4 and all("CONTEXT_LIVE_FETCH=0" in e["error"] for e in s["errors"])
        empty = ev.evidence_for_window(INFO, ev.window_for_outlier("2020-05"), fetchers={"gnews": fetcher},
                                       store_dir=tmp_path, now=NOW, **FAST)
        assert empty["items"] == [] and "CONTEXT_LIVE_FETCH=0" in empty["reason"]

    def test_live_false_argument_blocks_fetch(self, tmp_path):
        fetcher = FakeRss()
        result = ev.evidence_for_window(INFO, WINDOW, fetchers={"gnews": fetcher}, store_dir=tmp_path, now=NOW,
                                        live=False, **FAST)
        assert fetcher.queries == [] and result["sources"]["gnews"]["missing"] == 5


class TestThrottle:

    def test_two_seconds_between_requests_of_one_source(self):
        clock = {"t": 100.0}
        sleeps = []

        def sleep(s):
            sleeps.append(s)
            clock["t"] += s

        tick = lambda: clock["t"]  # noqa: E731
        assert src.throttle("gnews", sleep=sleep, clock=tick) == 0.0
        clock["t"] += 0.5
        waited = src.throttle("gnews", sleep=sleep, clock=tick)
        assert waited == pytest.approx(1.5) and sleeps == [pytest.approx(1.5)]
        assert src.throttle("eqs", sleep=sleep, clock=tick) == 0.0, "andere Quelle wartet nicht"


# ── Unternehmen ──────────────────────────────────────────────────────────────

class TestCompanyInfo:

    @pytest.fixture
    def ticker_info(self, monkeypatch):
        monkeypatch.setattr(context_service, "company_ticker_info", lambda cid: (
            {"company_id": 26, "name": "Carl Zeiss", "ticker": "AFX.DE", "ticker_scope": "Konzerngesellschaft",
             "peer_group": "Börsennotiert DE", "ticker_source": "db"} if cid == 26 else None))

    def test_metadata_overrides(self, ticker_info):
        meta = {26: {"company_id": 26, "name": "Carl Zeiss", "news_term": '"Carl Zeiss" OR ZEISS',
                     "news_exclude": ["FC Carl Zeiss"], "news_term_confirmed": False,
                     "eqs": {"uuid": "abc", "company_name": "Carl Zeiss Meditec AG"}}}
        info = ev.company_context_info(26, meta)
        assert info["search_term"] == '"Carl Zeiss" OR ZEISS' and info["exclude"] == ["FC Carl Zeiss"]
        assert (info["eqs_uuid"], info["eqs_name"], info["term_confirmed"]) == ("abc", "Carl Zeiss Meditec AG", False)
        assert ev.available_sources(info) == ["gnews", "eqs"]

    def test_default_term_from_name(self, ticker_info, monkeypatch):
        info = ev.company_context_info(26, {26: {"company_id": 26, "name": "Carl Zeiss"}})
        assert info["search_term"] == '"Carl Zeiss"' and info["exclude"] == [] and info["eqs_uuid"] is None
        assert ev.available_sources(info) == ["gnews"]
        monkeypatch.setenv(ev.GDELT_ENV, "1")
        assert ev.available_sources(info) == ["gnews", "gdelt"]

    def test_metadata_ignored_when_name_differs(self, ticker_info):
        info = ev.company_context_info(26, {26: {"company_id": 26, "name": "Andere AG", "news_term": "x"}})
        assert info["search_term"] == '"Carl Zeiss"'

    def test_unknown_company(self, ticker_info):
        assert ev.company_context_info(999, {}) is None

    def test_real_metadata_file_loads(self, ticker_info):
        info = ev.company_context_info(26)
        assert info["search_term"].startswith('"Carl Zeiss"') and "FC Carl Zeiss" in info["exclude"]
