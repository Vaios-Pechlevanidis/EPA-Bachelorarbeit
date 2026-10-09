"""
Tests für den Ø Score nach D1 (2026-10-09, FA-38): ``score`` = Mittel der
Gesamtnote (Spalte ``durchschnittsbewertung``) der Mitarbeitenden, ungewichtet;
``avg_overall`` bleibt das Mittel der Kategorienmittel. Dazu der Trend-Modus
``score_months`` (letzte 12 volle Kalendermonate gegen die 12 davor, Anker wie
FA-08). Konstruierte Zeilen, ohne Netzwerk; die Routen laufen gegen einen
nachgebildeten Client bzw. den In-Memory-Store.

Ausführen:
    cd backend
    uv run python -m pytest tests/test_score_service.py -q -p no:cacheprovider
"""

import os
import sys
from datetime import datetime, timezone

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

import routes.companies as companies_module  # noqa: E402
import services.score_service as sc  # noqa: E402
from routes.companies import CATEGORY_COLUMN_MAP, avg_overall_from_rows  # noqa: E402
from tests.test_ratings_pagination import CappedClient  # noqa: E402

TODAY = datetime(2026, 10, 9, 12, 0, tzinfo=timezone.utc)
CATEGORY_COLUMNS = list(CATEGORY_COLUMN_MAP.values())


def review(datum, overall, category_value=None, company_id=28, i=0):
    row = {"id": i, "company_id": company_id, "datum": datum, "durchschnittsbewertung": overall}
    for col in CATEGORY_COLUMNS:
        row[col] = category_value
    return row


def month_rows(spec, company_id=28):
    """{Monat: [Gesamtnoten]} → Zeilen am 15. des Monats."""
    out = []
    for period, values in spec.items():
        for v in values:
            out.append(review(f"{period}-15T00:00:00", v, 3.0, company_id, len(out) + 1))
    return out


# ── score_from_rows ──────────────────────────────────────────────────────────

def test_score_is_unweighted_mean_of_overall_rating():
    rows = [review("2024-01-15", 5.0), review("2024-02-15", 2.0), review("2024-03-15", 2.0), review("2024-03-20", None)]
    assert sc.score_from_rows(rows) == {"score": 3.0, "score_n": 3}


def test_score_empty():
    assert sc.score_from_rows([]) == {"score": None, "score_n": 0}
    assert sc.score_from_rows([{"durchschnittsbewertung": "x"}]) == {"score": None, "score_n": 0}


def test_overall_and_category_mean_can_differ_strongly():
    """Gesamtnote hoch, Kategorien niedrig (und eine Kategorie nur einmal bewertet):
    score und avg_overall liegen weit auseinander; beide bleiben in der Antwort."""
    rows = []
    for i in range(10):
        row = review(f"2024-0{1 + i % 9}-15", 4.8, None, i=i)
        for col in CATEGORY_COLUMNS[:12]:
            row[col] = 2.0
        rows.append(row)
    rows[0][CATEGORY_COLUMNS[12]] = 5.0          # 13. Kategorie nur einmal, Wert 5
    score = sc.score_from_rows(rows)
    cats = avg_overall_from_rows(rows)
    assert score == {"score": 4.8, "score_n": 10}
    # 12 Kategorien mit 2,0 und eine mit 5,0 → (12 × 2 + 5) / 13 = 2,23
    assert cats["avg_overall"] == pytest.approx(2.23)
    assert score["score"] - cats["avg_overall"] > 2.5


def test_definitions_name_the_basis():
    assert "Gesamtnote" in sc.SCORE_DEFINITION and "ungewichtet" in sc.SCORE_DEFINITION
    assert "Mitarbeitenden" in sc.SCORE_DEFINITION
    assert sc.CATEGORY_MEAN_DEFINITION.startswith("Kategorienmittel")


# ── score_trend (Modus score_months) ─────────────────────────────────────────

def test_trend_windows_twelve_full_months_before_anchor():
    spec = {"2023-08": [2.0, 2.0], "2024-07": [3.0], "2024-08": [4.0, 4.0], "2025-07": [5.0], "2026-10": [1.0]}
    r = sc.score_trend(month_rows(spec), today=TODAY)
    assert r["mode"] == "score_months" and r["anchor"] == "2025-07"
    assert (r["current"]["from"], r["current"]["to"]) == ("2024-08", "2025-07")
    assert (r["previous"]["from"], r["previous"]["to"]) == ("2023-08", "2024-07")
    assert r["n_reviews"] == {"current": 3, "previous": 3}
    # aktuell (4 + 4 + 5) / 3 = 4,333; davor (2 + 2 + 3) / 3 = 2,333
    assert r["current"]["mean"] == pytest.approx(4.33) and r["previous"]["mean"] == pytest.approx(2.33)
    assert r["difference"] == pytest.approx(2.0) and r["sign"] == "up"
    assert r["overall"]["deltaPoints"] == pytest.approx(2.0)
    assert r["current_range"] == {"from": "2024-08", "to": "2025-07"}
    assert r["insufficient_history"] is False


def test_trend_current_month_never_counts():
    r = sc.score_trend(month_rows({"2026-09": [3.0], "2026-10": [5.0]}), today=TODAY)
    assert r["anchor"] == "2026-09" and r["current"]["n"] == 1


def test_trend_low_basis_and_short_history():
    r = sc.score_trend(month_rows({"2025-06": [3.0] * 4, "2025-07": [3.0] * 3}), today=TODAY)
    assert r["low_basis"] is True and r["previous"]["n"] == 0 and r["difference"] is None and r["sign"] is None
    assert r["insufficient_history"] is True


def test_trend_months_is_a_parameter_and_flat_sign():
    spec = {"2025-01": [3.0] * 10, "2025-02": [3.02] * 10}
    r = sc.score_trend(month_rows(spec), months=1, today=TODAY)
    assert (r["current"]["from"], r["previous"]["from"]) == ("2025-02", "2025-01")
    assert r["sign"] == "flat" and r["months"] == 1


def test_trend_empty_keeps_fields():
    r = sc.score_trend([], today=TODAY)
    assert r["anchor"] is None and r["current"] is None and r["overall"]["deltaPoints"] is None
    assert r["n_reviews"] == {"current": 0, "previous": 0}


def test_trend_uses_overall_rating_not_categories():
    rows = month_rows({"2024-06": [2.0] * 10, "2025-06": [4.0] * 10})
    for r in rows:
        for col in CATEGORY_COLUMNS:
            r[col] = 1.0
    assert sc.score_trend(rows, today=TODAY)["difference"] == pytest.approx(2.0)


# ── Routen ───────────────────────────────────────────────────────────────────

@pytest.fixture
def capped(monkeypatch):
    rows = [review(f"2024-{1 + i % 12:02d}-15T00:00:00", 5.0 if i % 2 else 3.0, 2.0, i=i + 1) for i in range(2400)]
    client = CappedClient({"employee": rows, "candidates": []})
    monkeypatch.setattr(companies_module, "get_supabase_client", lambda: client)
    return client


def test_ratings_with_start_date_adds_score_and_keeps_avg_overall(capped):
    body = companies_module.get_company_ratings_overall(28, start_date="2024-01-01")
    assert body["score"] == 4.0 and body["score_n"] == 2400
    assert body["avg_overall"] == 2.0, "avg_overall bleibt das Kategorienmittel"
    assert body["score_definition"] == sc.SCORE_DEFINITION
    assert body["category_mean_definition"] == sc.CATEGORY_MEAN_DEFINITION
    assert body["definition"] == companies_module.AVG_OVERALL_DEFINITION


def test_compute_score_reads_all_pages(capped):
    assert companies_module._compute_score(28) == {"score": 4.0, "score_n": 2400}


def test_ratings_without_start_date_in_memory(in_memory_db, monkeypatch):
    monkeypatch.setattr(companies_module, "get_supabase_client", lambda: in_memory_db)
    body = companies_module.get_company_ratings_overall(3, start_date=None)
    assert body["avg_overall"] is not None and body["score"] is not None
    assert 1.0 <= body["score"] <= 5.0 and body["score_n"] > 0
    assert set(body) >= {"avg_overall", "n_reviews", "n_rated", "n_categories", "source", "basis", "definition",
                         "score", "score_n", "score_definition", "category_mean_definition"}


def test_trend_route_mode_score_months(in_memory_db, monkeypatch):
    body = companies_module.get_company_ratings_trend(3, days=30, mode="score_months", months=12)
    assert body["mode"] == "score_months" and body["months"] == 12 and body["anchor"] is not None
    assert set(body["n_reviews"]) == {"current", "previous"} and body["n_reviews"]["current"] > 0
    assert body["basis"] == "durchschnittsbewertung"


def test_trend_route_other_modes_unchanged(in_memory_db, monkeypatch):
    monkeypatch.setattr(companies_module, "get_supabase_client", lambda: in_memory_db)
    body = companies_module.get_company_ratings_trend(3, days=30, mode="stable_all", months=12)
    assert body["mode"] == "stable_all" and "metrics" in body and "current" not in body
