"""
Tests für scripts/report_context_coverage.py (Kontrollpunkt 2): Anteile je Art, Typ und
Jahresgruppe, Markierungen ohne Beleg, Markdown-Tabellen, Lauf gegen einen temporären
Speicher ohne Abruf. Ohne DB (Unternehmen und Markierungen nachgebildet) und ohne Netz.
"""

import os
import sys
from datetime import datetime, timezone

import pytest

BACKEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
sys.path.insert(0, BACKEND_DIR)
sys.path.insert(0, os.path.join(BACKEND_DIR, "scripts"))

import report_context_coverage as script  # noqa: E402
import services.evidence_service as ev  # noqa: E402
import services.evidence_sources as src  # noqa: E402

NOW = datetime(2024, 3, 15, 12, 0, tzinfo=timezone.utc)


def rec(company, kind, date, news=0, adhoc=0, glob=0, missing=0):
    return {"company_id": 1 if company == "A" else 2, "company": company, "kind": kind, "date": date,
            "window_from": date, "window_to": date, "counts": {"news": news, "adhoc": adhoc, "global": glob},
            "total": news + adhoc + glob, "missing_months": missing}


RECORDS = [
    rec("A", "niveauwechsel", "2017-05", news=2),
    rec("A", "niveauwechsel", "2021-09", news=1, adhoc=1),
    rec("A", "einzelmonat", "2022-12"),
    rec("B", "niveauwechsel", "2015-10", missing=5),
    rec("B", "einzelmonat", "2020-04", glob=1),
]


class TestAggregate:

    def test_shares_by_kind_type_and_year(self):
        s = script.aggregate(RECORDS)
        a = next(c for c in s["companies"] if c["company"] == "A")
        assert a["kinds"]["niveauwechsel"] == {"n": 2, "covered": 2, "share": 1.0,
                                               "news": {"covered": 2, "share": 1.0}, "adhoc": {"covered": 1, "share": 0.5},
                                               "global": {"covered": 0, "share": 0.0}}
        assert a["kinds"]["einzelmonat"]["covered"] == 0 and a["years"]["bis 2018"]["n"] == 1 and a["years"]["ab 2019"]["n"] == 2
        t = s["total"]
        assert (t["all"]["n"], t["all"]["covered"]) == (5, 3)
        assert (t["years"]["bis 2018"]["covered"], t["years"]["bis 2018"]["n"]) == (1, 2)
        assert (t["years"]["ab 2019"]["covered"], t["years"]["ab 2019"]["n"]) == (2, 3)
        assert t["kinds"]["einzelmonat"]["global"]["covered"] == 1
        assert s["uncovered"] == [{"company": "A", "kind": "einzelmonat", "date": "2022-12", "missing_months": 0},
                                  {"company": "B", "kind": "niveauwechsel", "date": "2015-10", "missing_months": 5}]

    def test_empty(self):
        s = script.aggregate([])
        assert s["n_markers"] == 0 and s["total"]["all"]["share"] is None and s["companies"] == []

    def test_markdown_has_numbers_only(self):
        text = script.markdown_tables(script.aggregate(RECORDS))
        assert "| A | 2/2 (100 %) | 2/2 (100 %) | 1/2 (50 %) | 0/2 (0 %) | 0/1 (0 %) |" in text
        assert "| **Gesamt** | 1/2 (50 %) | 2/3 (67 %) | 3/5 (60 %) |" in text
        assert "- B, niveauwechsel, 2015-10 (5 Monate nicht im Speicher)" in text
        assert "Meldung" not in text and "http" not in text


class TestRun:

    def test_records_from_store_without_fetch(self, tmp_path, monkeypatch):
        info = {"company_id": 7, "name": "E.ON", "search_term": "E.ON", "exclude": [], "term_confirmed": False,
                "ticker": None, "ticker_scope": None, "eqs_uuid": None, "eqs_name": None}
        item = src.make_item(title="Der Konzern und die Zahlen", url="https://x/1", published_at="2021-08-05",
                             publisher="P", source="gnews", source_type="news")
        ev.save_record(ev.build_record(7, "gnews", "2021-08", ev.expected_query(info, "gnews", "2021-08"), [item], NOW), tmp_path)
        monkeypatch.setattr(ev, "STORE_DIR", tmp_path)
        monkeypatch.setattr(ev, "GLOBAL_EVENTS_PATH", tmp_path / "keine.json")
        monkeypatch.setattr(ev, "company_context_info", lambda cid, metadata=None: info if cid == 7 else None)
        monkeypatch.setattr(script, "company_anchors", lambda cid: {
            "eligible": True,
            "anomalies": [{"id": "x", "date": "2021-09", "previous_period": "2021-08", "gap_months": 0}],
            "outliers": [{"id": "y", "date": "2015-03"}],
        })
        monkeypatch.setattr(src, "throttle", lambda *a, **k: pytest.fail("kein Abruf im Abdeckungsbericht"))
        records = script.marker_records(companies=[{"id": 7, "name": "E.ON"}], verbose=False)
        assert [(r["kind"], r["total"]) for r in records] == [("niveauwechsel", 1), ("einzelmonat", 0)]
        assert records[0]["counts"]["news"] == 1 and records[1]["missing_months"] == 5
        summary = script.aggregate(records)
        assert summary["total"]["years"]["bis 2018"]["covered"] == 0 and summary["total"]["years"]["ab 2019"]["covered"] == 1
