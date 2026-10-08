"""
Tests für scripts/report_context_coverage.py (Kontrollpunkt 2): Anteile je Art, Typ und
Jahresgruppe, Markierungen ohne Beleg, Markdown-Tabellen, Lauf gegen einen temporären
Speicher ohne Abruf. Ohne DB (Unternehmen und Markierungen nachgebildet) und ohne Netz.
"""

import json
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
            "total": news + adhoc, "missing_months": missing}   # allgemeine Ereignisse zählen nicht (E20)


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
        assert (t["all"]["n"], t["all"]["covered"]) == (5, 2), "B 2020-04 hat nur ein allgemeines Ereignis: kein Beleg"
        assert (t["years"]["bis 2018"]["covered"], t["years"]["bis 2018"]["n"]) == (1, 2)
        assert (t["years"]["ab 2019"]["covered"], t["years"]["ab 2019"]["n"]) == (1, 3)
        assert t["kinds"]["einzelmonat"]["global"]["covered"] == 1, "getrennt ausgewiesen"
        assert s["uncovered"] == [{"company": "A", "kind": "einzelmonat", "date": "2022-12", "missing_months": 0},
                                  {"company": "B", "kind": "niveauwechsel", "date": "2015-10", "missing_months": 5},
                                  {"company": "B", "kind": "einzelmonat", "date": "2020-04", "missing_months": 0}]

    def test_empty(self):
        s = script.aggregate([])
        assert s["n_markers"] == 0 and s["total"]["all"]["share"] is None and s["companies"] == []

    def test_markdown_has_numbers_only(self):
        text = script.markdown_tables(script.aggregate(RECORDS))
        assert "| A | 2/2 (100 %) | 2/2 (100 %) | 1/2 (50 %) | 0/2 (0 %) | 0/1 (0 %) |" in text
        assert "| **Gesamt** | 1/2 (50 %) | 1/3 (33 %) | 2/5 (40 %) |" in text
        assert "mit allgemeinem Ereignis (zählt nicht)" in text and "| 0/1 (0 %) | 0/1 (0 %) | 0/1 (0 %) | 1/1 (100 %) |" in text
        assert "- B, niveauwechsel, 2015-10 (5 Monate nicht im Speicher)" in text and "- B, einzelmonat, 2020-04" in text
        assert "Meldung" not in text.replace("Meldung (news)", "") and "http" not in text


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


# ── Vergleichsfenster (Nachschärfung Inkrement 4) ───────────────────────────

def win(news=0, adhoc=0, glob=0, missing=None, sources=("gnews", "eqs"), offset=None, date="2021-09"):
    missing = dict(missing or {})
    row = {"window_from": date, "window_to": date, "months": 5, "counts": {"news": news, "adhoc": adhoc, "global": glob},
           "total": news + adhoc, "sources": sorted(sources), "missing": {s: missing.get(s, 0) for s in sources},
           "missing_months": sum(missing.get(s, 0) for s in sources)}
    if offset is not None:
        row["offset_months"] = offset
    return row


def marker(company, kind, date, comparison, **kw):
    return {"company_id": 1 if company == "A" else 2, "company": company, "kind": kind, "date": date,
            **win(date=date, **kw), "comparison": comparison}


COMPARISON_RECORDS = [
    marker("A", "niveauwechsel", "2021-09", news=4, adhoc=1, comparison=[
        win(news=2, offset=-12), win(news=0, adhoc=1, offset=12), win(news=0, offset=-24, missing={"gnews": 2})]),
    marker("A", "einzelmonat", "2022-12", news=0, glob=1, comparison=[win(news=3, adhoc=0, offset=-12, glob=1)]),
    marker("B", "niveauwechsel", "2017-11", news=1, sources=("gnews",), comparison=[]),
]


class TestComparisonAggregate:

    def test_window_stats_counts_only_complete_windows(self):
        rows = [c for r in COMPARISON_RECORDS for c in r["comparison"]]
        s = script.window_stats(rows)
        assert (s["n"], s["complete"], s["incomplete"], s["missing_months"]) == (4, 3, 1, 2)
        assert (s["covered"], s["share"]) == (3, 1.0), "das unvollständige Fenster zählt nicht als 'kein Beleg'"
        assert (s["median"], s["min"], s["max"]) == (2.0, 1, 3), "news + adhoc je vollständigem Fenster: 2, 1, 3"
        assert s["news"] == {"n": 4, "complete": 3, "covered": 2, "share": 0.6667, "median": 2.0, "min": 0, "max": 3}
        assert s["adhoc"] == {"n": 4, "complete": 4, "covered": 1, "share": 0.25, "median": 0.0, "min": 0, "max": 1}
        assert s["global"] == {"n": 4, "with_event": 1}

    def test_global_events_are_not_evidence(self):
        s = script.window_stats([COMPARISON_RECORDS[1]])
        assert s["covered"] == 0 and s["global"]["with_event"] == 1 and s["median"] == 0.0

    def test_type_without_source_is_not_applicable(self):
        s = script.window_stats([COMPARISON_RECORDS[2]])
        assert s["adhoc"] == {"n": 0, "complete": 0, "covered": 0, "share": None, "median": None, "min": None, "max": None}
        assert s["news"]["covered"] == 1 and s["share"] == 1.0

    def test_aggregate_per_company_and_total(self):
        s = script.aggregate_comparison(COMPARISON_RECORDS)
        assert (s["offsets"], s["max_per_marker"], s["n_markers"], s["n_comparison_windows"]) == ([-12, 12, -24, 24], 3, 3, 4)
        a, b = s["companies"]
        assert (a["n_markers"], a["n_comparison_windows"], a["markers_without_comparison"]) == (2, 4, 0)
        assert (b["n_markers"], b["n_comparison_windows"], b["markers_without_comparison"]) == (1, 0, 1)
        assert a["markierung"]["covered"] == 1 and a["markierung"]["median"] == 2.5
        assert [w["offset_months"] for w in a["windows"]] == [-12, 12, -24, -12]
        assert a["windows"][2]["missing"] == {"gnews": 2, "eqs": 0} and a["windows"][2]["marker_date"] == "2021-09"
        assert s["total"]["markierung"]["n"] == 3 and s["total"]["vergleich"]["complete"] == 3
        assert "Ursache" in s["note"] and "Signifikanz" in s["note"]

    def test_markdown_numbers_only(self):
        text = script.markdown_comparison(script.aggregate_comparison(COMPARISON_RECORDS))
        assert "| A | 2 (2) | 1/2 (50 %) | 1/2 (50 %) | 1/2 (50 %) | 2.5 (0–5) | 4 (3) | 3/3 (100 %) | 2/3 (67 %) | 1/4 (25 %) | 2 (1–3) |" in text
        assert "| B | 1 (1) | 1/1 (100 %) | 1/1 (100 %) | – | 1 (1–1) | 0 (0) | – | – | – | – |" in text
        assert "| **Gesamt** | 3 (3) | 2/3 (67 %)" in text
        assert "| A | 2 | 0 | 4 | 3 | 2 | 1 / 1 |" in text
        assert "- A, niveauwechsel 2021-09, -24 Monate, 2021-09 – 2021-09 (gnews 2)" in text
        assert "Meldung" not in text.replace("Meldung (news)", "") and "http" not in text


class TestComparisonRun:

    def test_comparison_windows_from_store_without_fetch(self, tmp_path, monkeypatch):
        info = {"company_id": 7, "name": "E.ON", "search_term": "E.ON", "exclude": [], "term_confirmed": False,
                "ticker": None, "ticker_scope": None, "eqs_uuid": None, "eqs_name": None}

        def store(month, n):
            items = [src.make_item(title=f"Titel {month} {i} und Zahl", url=f"https://x/{month}/{i}", published_at=f"{month}-05",
                                   publisher="P", source="gnews", source_type="news") for i in range(n)]
            ev.save_record(ev.build_record(7, "gnews", month, ev.expected_query(info, "gnews", month), items, NOW), tmp_path)

        # Markierung 2021-09 (Fenster 2021-06..2021-10) vollständig; −12 (2020-06..2020-10) vollständig mit 1 Beleg;
        # +12 (2022-06..2022-10) fehlt bis auf einen Monat; −24 (2019-06..2019-10) liegt vor der Reihe
        for m in ["2021-06", "2021-07", "2021-08", "2021-09", "2021-10"]:
            store(m, 2)
        for m in ["2020-06", "2020-07", "2020-08", "2020-09", "2020-10"]:
            store(m, 1 if m == "2020-08" else 0)
        store("2022-06", 0)
        monkeypatch.setattr(ev, "STORE_DIR", tmp_path)
        monkeypatch.setattr(ev, "GLOBAL_EVENTS_PATH", tmp_path / "keine.json")
        monkeypatch.setattr(ev, "company_context_info", lambda cid, metadata=None: info if cid == 7 else None)
        monkeypatch.setattr(script, "company_anchors", lambda cid: {
            "eligible": True, "series_from": "2019-08", "series_to": "2023-12",
            "anomalies": [{"id": "x", "date": "2021-09", "previous_period": "2021-08", "gap_months": 0}],
            "outliers": [],
        })
        monkeypatch.setattr(src, "throttle", lambda *a, **k: pytest.fail("kein Abruf im Abdeckungsbericht"))
        records = script.marker_records(companies=[{"id": 7, "name": "E.ON"}], verbose=False, comparison=True)
        assert len(records) == 1 and records[0]["counts"]["news"] == 10 and records[0]["missing"] == {"gnews": 0}
        comps = records[0]["comparison"]
        assert [(c["offset_months"], c["window_from"], c["window_to"]) for c in comps] == [
            (-12, "2020-06", "2020-10"), (12, "2022-06", "2022-10"), (24, "2023-06", "2023-10")]
        assert [(c["counts"]["news"], c["missing_months"]) for c in comps] == [(1, 0), (0, 4), (0, 5)]
        s = script.aggregate_comparison(records)["total"]
        assert (s["vergleich"]["n"], s["vergleich"]["complete"], s["vergleich"]["covered"], s["vergleich"]["share"]) == (3, 1, 1, 1.0)
        assert (s["markierung"]["covered"], s["markierung"]["median"]) == (1, 10.0)
        plain = script.marker_records(companies=[{"id": 7, "name": "E.ON"}], verbose=False)
        assert "comparison" not in plain[0]

    def test_cli_flag(self, tmp_path, monkeypatch, capsys):
        monkeypatch.setattr(script, "marker_records", lambda *a, **k: [dict(r) for r in COMPARISON_RECORDS])
        out = tmp_path / "s.json"
        assert script.main(["--quiet", "--comparison", "--json", str(out)]) == 0
        text = capsys.readouterr().out
        assert "Markierungs- gegen Vergleichsfenster" in text and "Vergleichsfenster: 4 zu 3 Markierungen" in text
        summary = json.loads(out.read_text(encoding="utf-8"))
        assert summary["comparison"]["total"]["vergleich"]["complete"] == 3
