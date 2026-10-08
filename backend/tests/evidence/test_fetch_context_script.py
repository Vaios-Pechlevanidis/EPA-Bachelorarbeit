"""
Tests für scripts/fetch_context.py (Vorabruf, Inkrement 4): Planung der Monate,
Abruf mit nachgebildeter Quelle und temporärem Speicher, Fortsetzen, --dry-run,
CONTEXT_LIVE_FETCH=0, Abrufgrenze. Ohne DB (Unternehmen und Markierungen
nachgebildet) und ohne Netz.
"""

import os
import sys
from datetime import datetime
from email.utils import format_datetime

import pytest

BACKEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
sys.path.insert(0, BACKEND_DIR)
sys.path.insert(0, os.path.join(BACKEND_DIR, "scripts"))

import fetch_context as script  # noqa: E402
import services.evidence_service as ev  # noqa: E402
import services.evidence_sources as src  # noqa: E402
from services import news_service  # noqa: E402

INFO = {"company_id": 7, "name": "E.ON", "search_term": "E.ON", "exclude": [], "term_confirmed": False,
        "ticker": "EOAN.DE", "ticker_scope": "eigene Aktie", "eqs_uuid": None, "eqs_name": None}
ANCHORS = {
    "eligible": True,
    "anomalies": [{"id": "employee:durchschnittsbewertung:2021-09", "date": "2021-09", "previous_period": "2021-08", "gap_months": 0}],
    "outliers": [{"id": "employee:durchschnittsbewertung:2021-11:einzelmonat", "date": "2021-11"}],
}


def rss(n):
    items = "".join(
        f"<item><title>Meldung {i} - P</title><link>https://x/{i}</link>"
        f"<pubDate>{format_datetime(datetime.fromisoformat('2021-09-10T09:00:00+00:00'))}</pubDate></item>"
        for i in range(n)
    )
    return ("<?xml version=\"1.0\"?><rss version=\"2.0\"><channel><title>t</title>" + items + "</channel></rss>").encode()


class FakeRss:
    def __init__(self):
        self.queries = []

    def __call__(self, query):
        self.queries.append(query)
        return rss(2)


@pytest.fixture
def world(tmp_path, monkeypatch):
    fetcher = FakeRss()
    monkeypatch.setattr(ev, "STORE_DIR", tmp_path)
    monkeypatch.setattr(ev, "_failed_fetches", {})
    monkeypatch.setattr(src, "_last_request", {})
    monkeypatch.setattr(script.time, "sleep", lambda s: None)
    monkeypatch.setattr(script, "list_companies", lambda: [{"id": 7, "name": "E.ON"}, {"id": 5, "name": "PLEdoc GmbH"}])
    monkeypatch.setattr(script, "company_anchors", lambda cid: ANCHORS if cid == 7 else {"eligible": False, "anomalies": [], "outliers": []})
    monkeypatch.setattr(ev, "company_context_info", lambda cid, metadata=None: dict(INFO) if cid == 7 else None)
    monkeypatch.setattr(news_service, "fetch_rss", fetcher)
    monkeypatch.delenv(ev.LIVE_FETCH_ENV, raising=False)
    monkeypatch.delenv(ev.GDELT_ENV, raising=False)
    return fetcher


def test_months_for_anchors_merges_windows():
    plan = script.months_for_anchors(ANCHORS, 3, 1)
    # Niveauwechsel 2021-09 ohne Lücke: 2021-06..2021-10; Einzelmonat 2021-11: 2021-08..2021-12
    assert plan["months"] == ["2021-06", "2021-07", "2021-08", "2021-09", "2021-10", "2021-11", "2021-12"]
    assert [w["kind"] for w in plan["windows"]] == ["niveauwechsel", "einzelmonat"]


def test_run_fetches_then_resumes(world):
    summary = script.run(verbose=False)
    g = summary["sources"]["gnews"]
    assert (g["companies"], g["months"], g["fetched_now"], g["from_store"], g["missing"]) == (1, 7, 7, 0, 0)
    assert g["items"] == 14 and summary["fetches"] == 7 and summary["live"] is True
    assert [c["eligible"] for c in summary["companies"]] == [True, False]
    assert len(world.queries) == 7
    again = script.run(verbose=False)
    assert len(world.queries) == 7 and again["sources"]["gnews"]["from_store"] == 7 and again["fetches"] == 0
    text = script.format_summary(again)
    assert "Google News RSS (gnews): 1 Unternehmen, 7 Monate, gespeichert 7" in text
    assert "Suchbegriffe noch nicht vom Autor bestätigt: E.ON" in text


def test_dry_run_counts_only(world):
    summary = script.run(dry_run=True, verbose=False)
    assert world.queries == [] and summary["sources"]["gnews"]["missing"] == 7 and summary["dry_run"] is True
    assert "nur zählen" in script.format_summary(summary)


def test_live_fetch_disabled(world, monkeypatch):
    monkeypatch.setenv(ev.LIVE_FETCH_ENV, "0")
    summary = script.run(verbose=False)
    assert world.queries == [] and summary["live"] is False and "CONTEXT_LIVE_FETCH=0" in script.format_summary(summary)


def test_max_fetches_limits_a_run(world):
    summary = script.run(max_fetches=3, verbose=False)
    assert len(world.queries) == 3 and summary["fetch_limit_reached"] is True
    assert summary["sources"]["gnews"]["missing"] == 4
    script.run(verbose=False)
    assert len(world.queries) == 7, "Fortsetzung holt nur die fehlenden Monate"


def test_source_and_company_filters(world):
    summary = script.run(sources=["eqs"], verbose=False)
    assert summary["sources"] == {} and world.queries == []
    summary = script.run(company_ids=[5], verbose=False)
    assert [c["company_id"] for c in summary["companies"]] == [5]


def test_cli_writes_json(world, tmp_path, capsys):
    out = tmp_path / "s.json"
    assert script.main(["--quiet", "--json", str(out)]) == 0
    assert out.exists() and "Vorabruf der externen Belege" in capsys.readouterr().out
