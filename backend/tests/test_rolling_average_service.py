"""
Tests für services/rolling_average_service.py (rollierende Schnitte über 12 und 24
Monate, FA-08, Inkrement 6) und den Modus ``rolling`` von
GET /api/companies/{id}/ratings/trend. Konstruierte Reihen, ohne Netzwerk; die
Route läuft gegen den In-Memory-Store (Demo 1 bis 3).

Ausführen:
    cd backend
    uv run python -m pytest tests/test_rolling_average_service.py -q -p no:cacheprovider
"""

import os
import sys
from datetime import datetime, timezone

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

import services.rolling_average_service as ra  # noqa: E402

TODAY = datetime(2026, 10, 9, 12, 0, tzinfo=timezone.utc)


def rows(*spec):
    """spec: (datum, wert) je Bewertung; wert None = ohne Wert."""
    return [{"id": i, "datum": d, "durchschnittsbewertung": v} for i, (d, v) in enumerate(spec, start=1)]


def month_rows(period_values):
    """{Monat: [Werte]} → Zeilen, alle am 15. des Monats."""
    out = []
    for period, values in period_values.items():
        for v in values:
            out.append((f"{period}-15T00:00:00", v))
    return rows(*out)


# ---------------------------------------------------------------------------
# Anker
# ---------------------------------------------------------------------------

def test_anchor_is_last_full_month_with_data_not_today():
    data = month_rows({"2025-06": [3.0], "2025-07": [4.0]})
    result = ra.rolling_averages(data, today=TODAY)
    assert result["anchor"] == "2025-07"
    assert result["today"] == "2026-10"
    assert result["short"]["to"] == "2025-07" and result["short"]["from"] == "2024-08"
    assert result["long"]["to"] == "2025-07" and result["long"]["from"] == "2023-08"


def test_current_month_is_never_the_anchor():
    """Bewertungen im laufenden Monat zählen nicht: der Monat ist nicht abgeschlossen."""
    data = month_rows({"2026-09": [3.0, 3.0], "2026-10": [5.0, 5.0, 5.0]})
    result = ra.rolling_averages(data, today=TODAY)
    assert result["anchor"] == "2026-09"
    assert result["short"]["n"] == 2 and result["short"]["mean"] == 3.0


def test_only_current_month_has_data_gives_no_anchor():
    data = month_rows({"2026-10": [4.0]})
    result = ra.rolling_averages(data, today=TODAY)
    assert result["anchor"] is None and result["short"] is None and result["difference"] is None


# ---------------------------------------------------------------------------
# Monatsgrenzen und Fenster
# ---------------------------------------------------------------------------

def test_month_borders_are_inclusive_by_calendar_month():
    """Erster Tag des ersten Fenstermonats zählt, letzter Tag des Monats davor nicht."""
    data = rows(
        ("2024-07-31T23:59:00", 1.0),   # vor dem 12-Monats-Fenster (Aug. 2024 – Juli 2025)
        ("2024-08-01T00:00:00", 5.0),   # erster Tag des Fensters
        ("2025-07-31T00:00:00", 5.0),   # letzter Tag des Ankermonats
        ("2023-08-01T00:00:00", 1.0),   # erster Tag des 24-Monats-Fensters
        ("2023-07-31T00:00:00", 1.0),   # davor: zählt nirgends
    )
    result = ra.rolling_averages(data, today=TODAY)
    assert result["anchor"] == "2025-07"
    assert result["short"]["n"] == 2 and result["short"]["mean"] == 5.0
    assert result["long"]["n"] == 4 and result["long"]["mean"] == 3.0   # 5, 5, 1 (Juli 2024) und 1 (Aug. 2023)
    assert result["difference"] == 2.0 and result["sign"] == "up"


def test_long_window_contains_the_short_window():
    data = month_rows({"2025-07": [4.0, 4.0], "2024-07": [2.0, 2.0]})
    result = ra.rolling_averages(data, today=TODAY)
    assert result["short"]["n"] == 2 and result["long"]["n"] == 4
    assert result["short"]["mean"] == 4.0 and result["long"]["mean"] == 3.0
    assert result["difference"] == 1.0


def test_difference_uses_unrounded_means_and_sign_eps():
    data = month_rows({"2025-07": [3.004, 3.004, 3.004], "2024-07": [2.996, 2.996, 2.996]})
    result = ra.rolling_averages(data, today=TODAY)
    # 12 Monate: 3,004; 24 Monate: 3,000 → Differenz 0,00 (gerundet), Vorzeichen „flat“
    assert result["difference"] == 0.0 and result["sign"] == "flat"


def test_rows_without_date_or_value_are_ignored():
    data = rows(("2025-07-10T00:00:00", 4.0), (None, 1.0), ("2025-07-11T00:00:00", None), ("kein datum", 1.0))
    result = ra.rolling_averages(data, today=TODAY)
    assert result["n_total"] == 1 and result["short"]["n"] == 1 and result["short"]["mean"] == 4.0


def test_months_with_reviews_counts_distinct_months():
    data = month_rows({"2025-07": [4.0, 4.0], "2025-05": [3.0], "2025-01": [3.0]})
    result = ra.rolling_averages(data, today=TODAY)
    assert result["short"]["months_with_reviews"] == 3
    assert result["long"]["months_with_reviews"] == 3


# ---------------------------------------------------------------------------
# Weniger als 24 Monate Daten, kleine Basis, leere Reihe
# ---------------------------------------------------------------------------

def test_less_than_24_months_of_data_is_flagged():
    data = month_rows({"2025-07": [4.0] * 12, "2025-01": [3.0] * 12})
    result = ra.rolling_averages(data, today=TODAY)
    assert result["history_months"] == 7 and result["insufficient_history"] is True
    assert result["short"]["covered"] is False and result["short"]["covered_from"] == "2025-01"
    assert result["long"]["covered"] is False and result["long"]["covered_from"] == "2025-01"
    assert result["short"]["mean"] == 3.5 and result["long"]["mean"] == 3.5 and result["difference"] == 0.0


def test_exactly_24_months_of_data_is_sufficient():
    data = month_rows({"2025-07": [4.0] * 12, "2023-08": [3.0] * 12})
    result = ra.rolling_averages(data, today=TODAY)
    assert result["history_months"] == 24 and result["insufficient_history"] is False
    assert result["short"]["covered"] is True and result["long"]["covered"] is True
    assert result["long"]["covered_from"] is None


def test_low_basis_per_window_with_default_threshold():
    data = month_rows({"2025-07": [4.0] * 9, "2023-09": [3.0] * 1})
    result = ra.rolling_averages(data, today=TODAY)
    assert result["short"]["n"] == 9 and result["short"]["low_basis"] is True
    assert result["long"]["n"] == 10 and result["long"]["low_basis"] is False
    assert result["low_basis"] is True
    assert result["low_basis_rule"]["min_reviews_per_window"] == ra.LOW_BASIS_MIN_REVIEWS == 10


def test_low_basis_threshold_is_a_parameter():
    data = month_rows({"2025-07": [4.0] * 9})
    assert ra.rolling_averages(data, today=TODAY, min_reviews=5)["low_basis"] is False


def test_empty_series_keeps_all_fields():
    result = ra.rolling_averages([], today=TODAY)
    assert result["anchor"] is None and result["first_month"] is None and result["last_month"] is None
    assert result["short"] is None and result["long"] is None
    assert result["difference"] is None and result["sign"] is None
    assert result["low_basis"] is False and result["insufficient_history"] is True
    assert result["n_total"] == 0 and result["history_months"] == 0


def test_window_lengths_are_parameters():
    data = month_rows({"2025-07": [4.0], "2025-02": [2.0], "2024-10": [2.0]})
    result = ra.rolling_averages(data, today=TODAY, short_months=3, long_months=6)
    assert result["short"]["from"] == "2025-05" and result["short"]["n"] == 1
    assert result["long"]["from"] == "2025-02" and result["long"]["n"] == 2


def test_fixed_texts_describe_without_causes_or_forecasts():
    """Die festen Texte der Antwort beschreiben nur (keine Ursache, keine Prognose)."""
    import re

    result = ra.rolling_averages(month_rows({"2025-07": [4.0]}), today=TODAY)
    texts = " ".join([result["anchor_rule"], result["low_basis_rule"]["origin"]]).lower()
    for word in ("ursache", "auslöser", "grund", "weil", "führt zu", "wird sinken", "prognose"):
        assert re.search(rf"\b{word}\b", texts) is None, word


# ---------------------------------------------------------------------------
# Datenbankzugriff (monkeypatch) und Route
# ---------------------------------------------------------------------------

def test_company_rolling_averages_uses_employee_rows(monkeypatch):
    import services.rating_series_service as rs

    calls = []

    def fake_fetch(source, company_id, column, status=None):
        calls.append((source, company_id, column, status))
        return month_rows({"2025-07": [4.0], "2024-07": [2.0]})

    monkeypatch.setattr(rs, "fetch_review_rows", fake_fetch)
    result = ra.company_rolling_averages(7, today=TODAY)
    assert calls == [("employee", 7, "durchschnittsbewertung", None)]
    assert result["company_id"] == 7 and result["source"] == "employee" and result["status"] is None
    assert result["short"]["mean"] == 4.0 and result["long"]["mean"] == 3.0


def test_company_rolling_averages_rejects_unknown_status():
    with pytest.raises(ValueError):
        ra.company_rolling_averages(7, status="nicht-vorhanden", today=TODAY)


@pytest.fixture
def client(in_memory_db, monkeypatch):
    """Router gegen den In-Memory-Store: ``routes.companies`` bindet
    ``get_supabase_client`` beim Import, daher wie in
    ``test_companies_review_counts.py`` per monkeypatch umlenken."""
    import routes.companies as companies_module

    monkeypatch.setattr(companies_module, "get_supabase_client", lambda: in_memory_db)
    app = FastAPI()
    app.include_router(companies_module.router)
    return TestClient(app)


def test_route_mode_rolling_shape(client):
    res = client.get("/api/companies/3/ratings/trend", params={"mode": "rolling"})
    assert res.status_code == 200
    body = res.json()
    assert body["mode"] == "rolling" and body["source"] == "employee" and body["column"] == "durchschnittsbewertung"
    for key in ("anchor", "short", "long", "difference", "sign", "low_basis", "low_basis_rule",
                "history_months", "insufficient_history", "first_month", "last_month", "n_total"):
        assert key in body
    # Demo 3 im In-Memory-Store hat Bewertungen bis 2025-04; der Anker liegt vor dem laufenden Monat.
    assert body["anchor"] is not None and body["anchor"] < datetime.now().strftime("%Y-%m")
    assert body["short"]["to"] == body["anchor"] and body["long"]["to"] == body["anchor"]
    assert body["short"]["months"] == 12 and body["long"]["months"] == 24
    assert body["long"]["n"] >= body["short"]["n"] > 0


def test_route_other_modes_unchanged(client):
    stable = client.get("/api/companies/3/ratings/trend", params={"mode": "stable_all", "months": 12}).json()
    assert stable["mode"] == "stable_all" and "metrics" in stable and "anchor" not in stable
