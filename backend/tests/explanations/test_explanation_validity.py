"""
Tests für scripts/report_explanation_validity.py (Inkrement 5, A6): Rangfolge je Markierungs-
und Vergleichsfenster aus einem nachgebildeten Speicher ohne Abruf, Unternehmen,
Markierungen und Bewertungen nachgebildet (kein Netz, keine Datenbank); Anteile je Stufe,
Abdeckungsquote nach NFA-05, Markdown ohne Titel.

Ausführung:
    cd backend
    uv run python -m pytest tests/explanations/test_explanation_validity.py -q -p no:cacheprovider
"""

import json
import os
import sys
from datetime import datetime, timezone

import pytest

BACKEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
sys.path.insert(0, BACKEND_DIR)
sys.path.insert(0, os.path.join(BACKEND_DIR, "scripts"))

import report_explanation_validity as script  # noqa: E402
import services.evidence_service as ev  # noqa: E402
import services.evidence_sources as src  # noqa: E402

NOW = datetime(2026, 1, 15, 12, 0, tzinfo=timezone.utc)
INFO = {"company_id": 5, "name": "Beispielwerk", "search_term": "Beispielwerk", "exclude": [], "term_confirmed": True,
        "ticker": None, "ticker_scope": None, "eqs_uuid": None, "eqs_name": None}
# Ein Niveauwechsel 2023-04 (Übergang ab 2023-03) und ein Einzelmonat 2021-06; Reihe 2019-01 bis 2024-12.
ANCHORS = {
    "eligible": True,
    "anomalies": [{"id": "employee:durchschnittsbewertung:2023-04", "date": "2023-04", "direction": "fall", "previous_period": "2023-02",
                   "gap_months": 1, "before_from": "2021-01", "after_to": "2024-12"}],
    "outliers": [{"id": "employee:durchschnittsbewertung:2021-06:einzelmonat", "date": "2021-06", "direction": "fall"}],
    "series_from": "2019-01", "series_to": "2024-12",
}


def _review(i, day, text):
    return {"id": i, "datum": f"{day}T10:00:00+00:00", "durchschnittsbewertung": 3.0, "status": "Angestellt", "titel": "Titel",
            "gut_am_arbeitgeber_finde_ich": "", "schlecht_am_arbeitgeber_finde_ich": text, "verbesserungsvorschlaege": ""}


def _reviews(source, company_id, start, end):
    """Nachgebildete Bewertungen: 12 je Monat, ab 2023-04 mit dem Begriff 'Stellenabbau'."""
    out = []
    i = 0
    month = ev.period_from_index(ev.month_index(start.strftime("%Y-%m")))
    while month <= end.strftime("%Y-%m"):
        for k in range(12):
            i += 1
            text = "Der Stellenabbau drückt die Stimmung" if month >= "2023-04" and k < 8 else "Alles ruhig im Büro"
            out.append(_review(i + ev.month_index(month) * 100, f"{month}-{10 + k:02d}", text))
        month = ev.shift_month(month, 1)
    return out


def _fill(store, by_month):
    for month, entries in by_month.items():
        items = [src.make_item(title=t, url=f"https://x/{month}/{i}", published_at=f"{day}T10:00:00+00:00", publisher=pub,
                               source="gnews", source_type="news") for i, (t, day, pub) in enumerate(entries)]
        ev.save_record(ev.build_record(5, "gnews", month, ev.expected_query(INFO, "gnews", month), items, NOW), store)


@pytest.fixture
def env(tmp_path, monkeypatch):
    monkeypatch.setenv(ev.LIVE_FETCH_ENV, "0")
    monkeypatch.setattr(ev, "STORE_DIR", tmp_path)
    monkeypatch.setattr(ev, "GLOBAL_EVENTS_PATH", tmp_path / "keine.json")
    monkeypatch.setattr(ev, "company_context_info", lambda cid, metadata=None: dict(INFO) if cid == 5 else None)
    monkeypatch.setattr(script, "company_anchors", lambda cid: ANCHORS)
    monkeypatch.setattr(script, "fetch_review_rows_in_range", _reviews)
    # Speicher: alle Monate der Fenster leer, bis auf die Markierung (Stellenabbau im Monat vor dem Übergang)
    # und ein Vergleichsfenster des Einzelmonats (Spielbericht, ohne Arbeitgeberbezug).
    months = {}
    for first, last in (("2022-12", "2023-05"), ("2021-12", "2022-05"), ("2023-12", "2024-05"), ("2020-12", "2021-05"),
                        ("2021-03", "2021-07"), ("2020-03", "2020-07"), ("2022-03", "2022-07"), ("2019-03", "2019-07"), ("2023-03", "2023-07")):
        for m in ev.month_range(first, last):
            months.setdefault(m, [])
    months["2023-02"] = [("Beispielwerk kündigt Stellenabbau an", "2023-02-10", "Blatt A"), ("Beispielwerk kündigt Stellenabbau an: Verwaltung betroffen", "2023-02-11", "Blatt B")]
    months["2020-05"] = [("Beispielwerk gewinnt das Derby", "2020-05-12", "Sport")]
    _fill(tmp_path, months)
    return tmp_path


class TestRecords:

    def test_records_marker_and_comparison_windows(self, env):
        records = script.window_records(companies=[{"id": 5, "name": "Beispielwerk"}], verbose=False)
        markers = [r for r in records if r["group"] == "markierung"]
        comps = [r for r in records if r["group"] == "vergleich"]
        assert [(r["kind"], r["date"]) for r in markers] == [("niveauwechsel", "2023-04"), ("einzelmonat", "2021-06")]
        # Niveauwechsel: −12, +12 (+24 liegt nach dem Reihenende, −24 überschneidet das Fenster des Einzelmonats);
        # Einzelmonat: −12, +12, −24.
        assert len(comps) == 5 and {r["offset_months"] for r in comps} == {-12, 12, -24}
        assert sorted(r["offset_months"] for r in comps if r["kind"] == "niveauwechsel") == [-12, 12]
        change = markers[0]
        assert change["window_from"] == "2022-12" and change["window_to"] == "2023-05"
        assert change["review_before"] == {"from": "2022-10", "to": "2023-03", "n": 72} and change["review_after"]["from"] == "2023-04"
        assert change["state"] == "ansaetze" and change["n_items"] == 2 and change["n_bundles"] == 1 and change["top_stage"] == "hoch"
        assert change["n_terms"] >= 1 and change["missing_months"] == 0 and change["sources"] == ["gnews"]
        outlier = markers[1]
        assert outlier["review_before"]["from"] == "2020-12" and outlier["review_after"] == {"from": "2021-06", "to": "2021-06", "n": 12}
        assert outlier["state"] == "offen" and outlier["n_items"] == 0
        derby = next(r for r in comps if r["kind"] == "einzelmonat" and r["offset_months"] == -12)
        assert derby["n_items"] == 1 and derby["state"] == "offen", "Spielbericht: ohne Arbeitgeberbezug, keine Stufe"
        assert all(r["missing_months"] == 0 for r in records)

    def test_comparison_anchor_like_marked_month(self, env):
        records = script.window_records(companies=[{"id": 5, "name": "Beispielwerk"}], verbose=False)
        comp = next(r for r in records if r["kind"] == "niveauwechsel" and r["offset_months"] == -12)
        assert comp["window_from"] == "2021-12" and comp["review_before"] == {"from": "2021-10", "to": "2022-03", "n": 72}
        assert comp["review_after"] == {"from": "2022-04", "to": "2022-09", "n": 72}

    def test_missing_months_are_counted_not_treated_as_without(self, env, tmp_path):
        (tmp_path / "5" / "gnews" / "2023-01.json").unlink()
        records = script.window_records(companies=[{"id": 5, "name": "Beispielwerk"}], verbose=False)
        change = next(r for r in records if r["group"] == "markierung" and r["kind"] == "niveauwechsel")
        assert change["missing_months"] == 1
        s = script.aggregate(records)
        m = s["total"]["markierung"]
        assert m["n"] == 2 and m["complete"] == 1 and m["incomplete"] == 1
        assert s["total"]["coverage_nfa05"]["n"] == 1

    def test_no_fetch(self, env, monkeypatch):
        from services import news_service

        def boom(query):
            raise AssertionError("kein Abruf erlaubt")
        monkeypatch.setattr(news_service, "fetch_rss", boom)
        monkeypatch.delenv(ev.LIVE_FETCH_ENV, raising=False)
        assert script.window_records(companies=[{"id": 5, "name": "Beispielwerk"}], verbose=False)


class TestAggregate:

    def test_shares_and_coverage(self, env):
        records = script.window_records(companies=[{"id": 5, "name": "Beispielwerk"}], verbose=False)
        s = script.aggregate(records)
        t = s["total"]
        assert t["n_markers"] == 2 and t["n_comparison_windows"] == 5
        m, c = t["markierung"], t["vergleich"]
        assert (m["complete"], m["with_any"], m["share_any"]) == (2, 1, 0.5)
        assert m["by_stage"]["hoch"] == {"windows": 1, "share": 0.5} and m["by_stage"]["niedrig"]["windows"] == 0
        assert m["top_stage"] == {"hoch": 1, "mittel": 0, "niedrig": 0, "offen": 1}
        assert (c["complete"], c["with_any"], c["share_any"]) == (5, 0, 0.0)
        assert c["median_items"] == 0 and m["median_items"] == 1.0 and m["median_bundles"] == 0.5 and m["windows_with_terms"] == 1
        cov = t["coverage_nfa05"]
        assert (cov["covered"], cov["n"], cov["share"]) == (1, 2, 0.5)
        assert cov["by_kind"]["niveauwechsel"] == {"covered": 1, "n": 1, "share": 1.0}
        assert cov["by_kind"]["einzelmonat"] == {"covered": 0, "n": 1, "share": 0.0}
        assert s["companies"][0]["company"] == "Beispielwerk" and s["companies"][0]["coverage_nfa05"]["share"] == 0.5
        assert s["rules"]["max_explanations"] == 5 and len(s["windows"]) == 7

    def test_empty(self):
        s = script.aggregate([])
        assert s["total"]["n_markers"] == 0 and s["total"]["coverage_nfa05"]["share"] is None and s["companies"] == []
        assert "| **Gesamt** | – |" in script.markdown_tables(s)

    def test_markdown_numbers_only(self, env):
        records = script.window_records(companies=[{"id": 5, "name": "Beispielwerk"}], verbose=False)
        text = script.markdown_tables(script.aggregate(records))
        assert "| Beispielwerk | 2 (2) | 1/2 (50 %) | 1/2 (50 %) | 0/2 (0 %) | 0/2 (0 %) | 1 / 0.5 |" in text
        assert "| **Gesamt** | 1/2 (50 %) | 1/1 (100 %) | 0/1 (0 %) | 0/5 (0 %) |" in text
        assert "| Markierungsfenster | 1 | 0 | 0 | 1 |" in text
        for forbidden in ("Stellenabbau", "Derby", "http", "Blatt"):
            assert forbidden not in text
        assert "keine Ursache" in text

    def test_json_roundtrip(self, env, tmp_path):
        records = script.window_records(companies=[{"id": 5, "name": "Beispielwerk"}], verbose=False)
        path = tmp_path / "out" / "validity.json"
        import report_explanation_validity as sc
        sc.window_records = lambda *a, **k: records
        assert sc.main(["--quiet", "--json", str(path)]) == 0
        data = json.loads(path.read_text(encoding="utf-8"))
        assert data["total"]["coverage_nfa05"]["share"] == 0.5 and data["window_before"] == 3
        assert all("title" not in w for w in data["windows"])
