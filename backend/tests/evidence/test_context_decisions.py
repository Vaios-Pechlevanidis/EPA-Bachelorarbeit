"""
Tests für scripts/report_context_decisions.py (Nachschärfung A4): Wortteile und
Nennungsanteil der Suchbegriffe, Vorabrufplan mit fehlenden Monaten je Quelle,
Markdown nur mit Zahlen. Ohne DB (Markierungen nachgebildet) und ohne Netz.
"""

import os
import sys
from datetime import datetime, timezone

import pytest

BACKEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
sys.path.insert(0, BACKEND_DIR)
sys.path.insert(0, os.path.join(BACKEND_DIR, "scripts"))

import report_context_decisions as script  # noqa: E402
import services.evidence_service as ev  # noqa: E402
import services.evidence_sources as src  # noqa: E402

NOW = datetime(2026, 10, 8, 12, 0, tzinfo=timezone.utc)
INFO = {"company_id": 28, "name": "Telekom", "search_term": '"Deutsche Telekom"', "exclude": ["Baskets"], "term_confirmed": False,
        "ticker": "DTE.DE", "ticker_scope": "eigene Aktie", "eqs_uuid": "5b70cbe7-0000-0000-0000-000000000000", "eqs_name": "Deutsche Telekom AG"}


class TestSearchTerms:

    def test_name_tokens_from_term_and_name(self):
        assert script.name_tokens('"Carl Zeiss" OR ZEISS', "Carl Zeiss") == ["carl zeiss", "zeiss"]
        assert script.name_tokens('"CompuGroup Medical" OR CompuGroup', "Compugroup Medical Deutschland") == ["compugroup medical", "compugroup"]
        assert script.name_tokens("E.ON", "E.ON SE") == ["e.on"]
        assert script.name_tokens('"1&1"', "1&1 AG") == ["1&1"]

    def test_mention_share(self):
        tokens = script.name_tokens('"Deutsche Telekom"', "Telekom")
        titles = ["Deutsche Telekom legt Zahlen vor", "Die Telekom baut aus", "Netzausbau in Bonn", ""]
        assert script.mention_share(titles, tokens) == 0.5
        assert script.mention_share([], tokens) is None

    def test_row_from_store(self, tmp_path):
        def save(month, n):
            items = [src.make_item(title=f"Telekom {month} Nr. {i}" if i % 2 == 0 else f"Netz {month} Nr. {i}", url=f"https://x/{month}/{i}",
                                   published_at=f"{month}-10", publisher="P", source="gnews", source_type="news") for i in range(n)]
            ev.save_record(ev.build_record(28, "gnews", month, ev.expected_query(INFO, "gnews", month), items, NOW), tmp_path)

        save("2021-01", 4)
        save("2021-02", 0)
        save("2021-03", 2)
        months = script.stored_months(28, "gnews", tmp_path)
        assert [(m, v["n"]) for m, v in months.items()] == [("2021-01", 4), ("2021-02", 0), ("2021-03", 2)]
        row = script.search_term_row(INFO, months)
        assert (row["months"], row["items"], row["items_per_month_mean"], row["items_per_month_median"], row["months_without_items"]) == (3, 6, 2.0, 2.0, 1)
        assert row["mention_share"] == 0.5 and row["tokens"] == ["deutsche telekom", "telekom"]
        assert script.stored_months(99, "gnews", tmp_path) == {}


class TestPrefetchPlan:

    ANCHORS = {
        "eligible": True, "series_from": "2015-01", "series_to": "2021-12",
        "anomalies": [{"id": "x", "date": "2021-09", "previous_period": "2021-08", "gap_months": 0}],
        "outliers": [{"id": "y", "date": "2018-04"}],
    }

    def test_missing_months_per_source_and_estimate(self):
        stored = {"gnews": set(ev.month_range("2021-06", "2021-10")) | {"2020-08"}, "eqs": set()}
        plan = script.prefetch_plan({"id": 28, "name": "Telekom"}, self.ANCHORS, ["gnews", "eqs"], "2019-01", NOW, stored, 3, 1)
        assert (plan["n_markers"], plan["markers_from_year"], plan["marker_months"]) == (2, 1, 10)
        # Vergleichsfenster: 2021-09 → −12 (2020-06..10), +12 (außerhalb der Reihe), −24 (2019-06..10), +24 (außerhalb);
        # 2018-04 → −12 (2017-01..05), +12 (2019-01..05), −24 (2016-01..05): 5 Fenster, 25 Monate
        assert (plan["n_comparison_windows"], plan["comparison_months"]) == (5, 25)
        assert plan["all_months"] == 37, "2019-01 bis 2022-01 (letzter bewerteter Monat plus 1)"
        assert plan["sources"]["gnews"] == {"stored": 6, "missing_comparison": 24, "missing_all": 31, "missing_all_from": "2019-01"}
        assert plan["sources"]["eqs"] == {"stored": 0, "missing_comparison": 25, "missing_all": 37, "missing_all_from": "2019-01"}
        assert (plan["fetches_comparison"], plan["fetches_all"]) == (49, 68)
        assert script.estimate_minutes(68) == 2.3

    def test_markdown_has_numbers_and_no_titles(self):
        summary = {
            "from_month": "2019-01",
            "d1_search_terms": [{"company": "Telekom", "search_term": '"Deutsche Telekom"', "exclude": ["Baskets"], "term_confirmed": False,
                                 "months": 3, "items": 6, "items_per_month_mean": 2.0, "items_per_month_median": 2.0,
                                 "months_without_items": 1, "tokens": ["deutsche telekom"], "mention_share": 0.5},
                                {"company": "Leer", "search_term": "Leer", "exclude": [], "term_confirmed": True, "months": 0, "items": 0,
                                 "items_per_month_mean": None, "items_per_month_median": None, "months_without_items": 0, "tokens": [], "mention_share": None}],
            "d2_eqs": [{"company": "Telekom", "uuid": "u", "eqs_name": "Deutsche Telekom AG", "isin": "DE0005557508", "confirmed": False,
                        "months": 2, "items": 3, "issuers_in_store": {"Deutsche Telekom AG": 3}}],
            "d3_global_events": [{"id": "e", "date_from": "2020-03", "date_to": "2020-05", "months": 3, "title": "Erster Lockdown",
                                  "url": "https://example.org/e", "confirmed": False}],
            "d4_prefetch": {"companies": [{"company_id": 28, "company": "Telekom", "series_from": "2015-01", "series_to": "2021-12",
                                           "n_markers": 2, "markers_from_year": 1, "n_comparison_windows": 5,
                                           "sources": {"gnews": {"missing_comparison": 24, "missing_all": 31}, "eqs": {"missing_comparison": 25, "missing_all": 37}},
                                           "all_months": 37, "fetches_comparison": 49, "fetches_all": 68}],
                            "proposed_company_ids": [28], "fetches_comparison_all": 49, "minutes_comparison_all": 1.6,
                            "fetches_all_proposed": 68, "minutes_all_proposed": 2.3, "seconds_per_fetch": 2.0},
        }
        text = script.markdown(summary)
        assert "| Telekom | `\"Deutsche Telekom\"` | Baskets | nein | 3 | 6 | 2.0 (2) | 1 | 50 % |" in text
        assert "| Leer | `Leer` | – | ja | 0 | 0 | – | 0 | – |" in text
        assert "| Telekom | `u` | Deutsche Telekom AG | DE0005557508 | nein | 2 | 3 | Deutsche Telekom AG (3) |" in text
        assert "| e | 2020-03 – 2020-05 | 3 | Erster Lockdown | https://example.org/e | nein |" in text
        assert "| Telekom | 2015-01 – 2021-12 | 2 (1) | 5 | 24 / 25 | 37 | 31 / 37 | 68 | 2.3 min | ja |" in text
        assert "49 Abrufe, ≈ 1.6 min" in text and "68 (Vorschlag) | ≈ 2.3 min" in text


class TestCollect:

    def test_collect_without_db(self, tmp_path, monkeypatch):
        monkeypatch.setattr(ev, "STORE_DIR", tmp_path)
        monkeypatch.setattr(ev, "GLOBAL_EVENTS_PATH", tmp_path / "keine.json")
        monkeypatch.setattr(ev, "company_context_info", lambda cid, metadata=None: dict(INFO) if cid == 28 else None)
        monkeypatch.setattr(script, "company_anchors", lambda cid: TestPrefetchPlan.ANCHORS if cid == 28 else {"eligible": False, "anomalies": [], "outliers": []})
        import services.context_service as cs
        monkeypatch.setattr(cs, "load_metadata", lambda: {28: {"eqs": {"isin": "DE0005557508", "confirmed": False, "note": "n"}}})
        monkeypatch.setattr(src, "throttle", lambda *a, **k: pytest.fail("kein Abruf"))
        summary = script.collect("2019-01", companies=[{"id": 28, "name": "Telekom"}, {"id": 5, "name": "PLEdoc GmbH"}], now=NOW)
        assert [r["company"] for r in summary["d1_search_terms"]] == ["Telekom"] and summary["d1_search_terms"][0]["months"] == 0
        assert summary["d2_eqs"][0]["isin"] == "DE0005557508" and summary["d3_global_events"] == []
        d4 = summary["d4_prefetch"]
        assert d4["proposed_company_ids"] == [28] and d4["fetches_all_proposed"] == 74 and d4["fetches_comparison_all"] == 50
