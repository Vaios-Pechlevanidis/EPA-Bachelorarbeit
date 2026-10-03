"""
Tests für services/rating_series_service.py (Monatsreihe als Eingabe der
Anomalieerkennung, E3/E4). Ohne Datenbank: Rohzeilen werden direkt übergeben
bzw. der Zeilenabruf per monkeypatch ersetzt.

Ausführen:
    cd backend
    uv run python -m pytest tests/test_rating_series_service.py -q -p no:cacheprovider
"""

import os
import sys

import pytest

BACKEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, BACKEND_DIR)
sys.path.insert(0, os.path.join(BACKEND_DIR, "scripts"))

import services.rating_series_service as rs  # noqa: E402


def rows(*spec):
    """spec: (datum, wert) je Bewertung."""
    return [{"id": i, "datum": d, "durchschnittsbewertung": v} for i, (d, v) in enumerate(spec, start=1)]


# ---------------------------------------------------------------------------
# Spalten und Dimensionen
# ---------------------------------------------------------------------------

def test_value_column_overall_and_topic():
    assert rs.value_column("employee") == "durchschnittsbewertung"
    assert rs.value_column("employee", "kommunikation") == "sternebewertung_kommunikation"
    assert rs.value_column("candidates", "schnelle_antwort") == "sternebewertung_schnelle_antwort"


@pytest.mark.parametrize("source,dimension", [
    ("bewerber", "durchschnittsbewertung"),
    ("employee", "schnelle_antwort"),      # Kandidaten-Dimension bei Mitarbeitenden
    ("candidates", "kommunikation"),        # Mitarbeitenden-Dimension bei Kandidaten
    ("employee", "gibt_es_nicht"),
])
def test_value_column_rejects_invalid(source, dimension):
    with pytest.raises(ValueError):
        rs.value_column(source, dimension)


def test_dimensions_cover_both_sources():
    assert rs.DIMENSIONS_BY_SOURCE["employee"][0] == "durchschnittsbewertung"
    assert len(rs.DIMENSIONS_BY_SOURCE["employee"]) == 14
    assert len(rs.DIMENSIONS_BY_SOURCE["candidates"]) == 11


# ---------------------------------------------------------------------------
# Reihenbildung
# ---------------------------------------------------------------------------

def test_series_fills_missing_months_with_zero_count():
    series = rs.build_monthly_series(rows(("2023-01-05T00:00:00+00:00", 4.0), ("2023-03-10T00:00:00+00:00", 2.0)))
    assert [m["period"] for m in series] == ["2023-01", "2023-02", "2023-03"]
    gap = series[1]
    assert gap["count"] == 0 and gap["n_values"] == 0 and gap["mean"] is None and gap["evaluated"] is False


def test_mean_is_rounded_to_three_decimals():
    series = rs.build_monthly_series(rows(("2023-01-01", 3.0), ("2023-01-02", 3.0), ("2023-01-03", 4.0)))
    assert series[0]["mean"] == 3.333


def test_evaluated_requires_min_reviews():
    four = rows(*[(f"2023-01-0{d}", 3.0) for d in range(1, 5)])
    five = rows(*[(f"2023-02-0{d}", 3.0) for d in range(1, 6)])
    series = rs.build_monthly_series(four + five)
    assert [m["evaluated"] for m in series] == [False, True]
    assert rs.build_monthly_series(four, min_reviews=4)[0]["evaluated"] is True


def test_rows_without_valid_date_are_ignored():
    data = rows(("2023-01-05", 4.0), (None, 1.0), ("kein-datum", 1.0), ("", 1.0))
    series = rs.build_monthly_series(data)
    assert len(series) == 1 and series[0]["count"] == 1 and series[0]["mean"] == 4.0


def test_count_includes_reviews_without_value_but_mean_does_not():
    data = [
        {"datum": "2023-01-01", "sternebewertung_kommunikation": 2.0},
        {"datum": "2023-01-02", "sternebewertung_kommunikation": None},
        {"datum": "2023-01-03", "sternebewertung_kommunikation": "x"},
    ]
    month = rs.build_monthly_series(data, "sternebewertung_kommunikation")[0]
    assert month["count"] == 3 and month["n_values"] == 1 and month["mean"] == 2.0


def test_empty_input_gives_empty_series():
    assert rs.build_monthly_series([]) == []
    assert rs.build_monthly_series(rows((None, 3.0))) == []


def test_month_range_crosses_year_boundary():
    assert rs.month_range("2022-11", "2023-02") == ["2022-11", "2022-12", "2023-01", "2023-02"]


# ---------------------------------------------------------------------------
# Eignung nach E4 und Abruf
# ---------------------------------------------------------------------------

def test_is_eligible_needs_twelve_evaluated_months():
    eleven = [{"evaluated": True}] * 11 + [{"evaluated": False}] * 5
    assert rs.evaluated_months(eleven) == 11
    assert rs.is_eligible(eleven) is False
    assert rs.is_eligible(eleven + [{"evaluated": True}]) is True


def test_monthly_series_uses_paginated_fetch(monkeypatch):
    calls = {}

    def fake_fetch(source, company_id, column):
        calls.update(source=source, company_id=company_id, column=column)
        return [{"datum": "2023-01-01", column: 4.0}] * 5

    monkeypatch.setattr(rs, "fetch_review_rows", fake_fetch)
    result = rs.monthly_series(28, "employee", "work_life_balance")
    assert calls == {"source": "employee", "company_id": 28, "column": "sternebewertung_work_life_balance"}
    assert result["column"] == "sternebewertung_work_life_balance"
    assert result["min_reviews"] == 5 and result["evaluated_months"] == 1
    assert result["series"] == [{"period": "2023-01", "mean": 4.0, "count": 5, "n_values": 5, "evaluated": True}]


def test_monthly_series_rejects_invalid_dimension_before_fetch(monkeypatch):
    monkeypatch.setattr(rs, "fetch_review_rows", lambda *a: pytest.fail("darf nicht abgerufen werden"))
    with pytest.raises(ValueError):
        rs.monthly_series(3, "employee", "schnelle_antwort")


# ---------------------------------------------------------------------------
# Konsistenz mit der Annotationsgrundlage (gleiche Reihe für Erkennung und CSVs)
# ---------------------------------------------------------------------------

def test_annotation_basis_uses_the_same_series():
    import make_annotation_basis as mab

    data = rows(("2023-01-01", 4.0), ("2023-01-02", 3.0), ("2023-03-01", 2.0))
    csv_series = mab.build_series(data)
    service_series = rs.build_monthly_series(data)
    assert [(c["period"], c["mean_durchschnittsbewertung"], c["count"]) for c in csv_series] == \
           [(s["period"], s["mean"], s["count"]) for s in service_series]
    assert csv_series[2]["delta_vs_previous"] == -1.5   # Differenz zum letzten Monat mit Wert
