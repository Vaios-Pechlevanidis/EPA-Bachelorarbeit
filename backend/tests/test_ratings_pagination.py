"""
Seitenweise Abfragen in GET /companies/{id}/ratings, …/ratings/avg,
…/ratings/category-counts und GET /analytics/company/{id}/timeline
(Korrektur 2026-10-09, Inkrement 6): PostgREST liefert höchstens 1000 Zeilen je
Abfrage. Ein nachgebildeter Client begrenzt jede Seite auf 1000 Zeilen und
liefert ohne ``range()`` nur die erste Seite, wie die gehostete Datenbank.
Dazu die zusätzlichen Felder ``n_reviews``, ``source``, ``basis`` und
``definition`` (FA-26, FA-38). Ohne Netzwerk, konstruierte Zeilen.

Ausführen:
    cd backend
    uv run python -m pytest tests/test_ratings_pagination.py -q -p no:cacheprovider
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

import routes.analytics as analytics_module  # noqa: E402
import routes.companies as companies_module  # noqa: E402
from routes.companies import CATEGORY_COLUMN_MAP, avg_overall_from_rows  # noqa: E402

MAX_ROWS = 1000  # PostgREST-Grenze je Abfrage


class _Result:
    def __init__(self, data, count=None):
        self.data = data
        self.count = count


class _Query:
    def __init__(self, rows):
        self._rows = list(rows)
        self._range = None
        self._count = None
        self._limit = None

    def select(self, cols, count=None):
        self._count = count
        return self

    def eq(self, col, val):
        self._rows = [r for r in self._rows if r.get(col) == val]
        return self

    def gte(self, col, val):
        self._rows = [r for r in self._rows if r.get(col) is not None and str(r[col]) >= str(val)]
        return self

    def lt(self, col, val):
        self._rows = [r for r in self._rows if r.get(col) is not None and str(r[col]) < str(val)]
        return self

    def order(self, col, desc=False):
        self._rows = sorted(self._rows, key=lambda r: (r.get(col) is None, r.get(col) or ""), reverse=desc)
        return self

    def limit(self, n):
        self._limit = n
        return self

    def range(self, start, end):
        self._range = (start, end)
        return self

    def execute(self):
        rows = self._rows
        if self._range is not None:
            rows = rows[self._range[0]: self._range[1] + 1]
        if self._limit is not None:
            rows = rows[: self._limit]
        return _Result(rows[:MAX_ROWS], count=len(self._rows) if self._count else None)


class CappedClient:
    """Liefert je Abfrage höchstens ``MAX_ROWS`` Zeilen, wie PostgREST."""

    def __init__(self, tables):
        self.tables = tables

    def table(self, name):
        rows = self.tables.get(name, [])
        client = self

        class _Table:
            def select(self, cols, count=None):
                return _Query(rows).select(cols, count=count)

            def __getattr__(self, attr):
                raise AssertionError(f"Schreibzugriff {attr} auf {name} ({client})")

        return _Table()

    def rpc(self, func, params):
        raise AssertionError("kein RPC in diesen Tests")


def employee_rows(n, company_id=28, start_month=1):
    """n Zeilen mit allen 13 Kategorien = 4.0, datiert ab 2020 (innerhalb der
    10 Jahre des Zeitverlaufs), je 100 Zeilen ein Monat weiter."""
    rows = []
    for i in range(n):
        month_index = start_month + i // 100
        year, month = 2020 + (month_index - 1) // 12, (month_index - 1) % 12 + 1
        row = {"id": i + 1, "company_id": company_id, "datum": f"{year:04d}-{month:02d}-15T00:00:00",
               "durchschnittsbewertung": 4.0}
        for col in CATEGORY_COLUMN_MAP.values():
            row[col] = 4.0
        rows.append(row)
    return rows


@pytest.fixture
def capped(monkeypatch):
    rows = employee_rows(2500)
    client = CappedClient({"employee": rows, "candidates": []})
    monkeypatch.setattr(companies_module, "get_supabase_client", lambda: client)
    monkeypatch.setattr(analytics_module, "get_supabase_client", lambda: client)
    return client


def test_capped_client_returns_only_first_page_without_range(capped):
    assert len(capped.table("employee").select("id").eq("company_id", 28).execute().data) == MAX_ROWS


def test_compute_avg_overall_reads_all_pages(capped):
    result = companies_module._compute_avg_overall(28)
    assert result["n_reviews"] == 2500 and result["n_rated"] == 2500 and result["n_categories"] == 13
    assert result["avg_overall"] == 4.0


def test_ratings_with_start_date_counts_all_rows(capped):
    body = companies_module.get_company_ratings_overall(28, start_date="2020-01-01")
    assert body["n_reviews"] == 2500 and body["avg_overall"] == 4.0
    assert body["source"] == "employee" and body["basis"] == "sternebewertung"
    assert body["definition"] == companies_module.AVG_OVERALL_DEFINITION


def test_category_counts_read_all_pages(capped):
    counts = companies_module.get_company_category_counts(28)
    assert set(counts) == set(CATEGORY_COLUMN_MAP)
    assert all(n == 2500 for n in counts.values())


def test_ratings_avg_with_start_date_reads_all_pages(monkeypatch):
    rows = employee_rows(1500)
    for r in rows[1000:]:
        r["sternebewertung_image"] = 1.0   # nur auf der zweiten Seite
    client = CappedClient({"employee": rows})
    monkeypatch.setattr(companies_module, "get_supabase_client", lambda: client)
    body = companies_module.get_company_ratings_avg(28, start_date="2020-01-01")
    assert body["avg_image"] == pytest.approx((1000 * 4.0 + 500 * 1.0) / 1500, abs=1e-4)


def test_timeline_reads_all_pages_and_reaches_last_month(capped):
    body = analytics_module.get_company_timeline(28, days=3650, forecast_months=0, source="employee")
    assert sum(m["count"] for m in body["timeline"]) == 2500
    assert body["timeline"][-1]["date"] == "2022-01"   # 25 Monate ab 2020-01


def test_avg_overall_from_rows_is_mean_of_category_means():
    rows = [
        {"sternebewertung_image": 1.0, "sternebewertung_kommunikation": 3.0},
        {"sternebewertung_image": 3.0},
        {"titel": "ohne Werte"},
    ]
    result = avg_overall_from_rows(rows)
    # Image 2,0; Kommunikation 3,0 → Mittel der Kategorienmittel 2,5 (ungewichtet)
    assert result == {"avg_overall": 2.5, "n_reviews": 3, "n_rated": 2, "n_categories": 2}


def test_avg_overall_from_rows_empty():
    assert avg_overall_from_rows([]) == {"avg_overall": None, "n_reviews": 0, "n_rated": 0, "n_categories": 0}


def test_ratings_without_start_date_adds_n_reviews_in_memory(in_memory_db, monkeypatch):
    monkeypatch.setattr(companies_module, "get_supabase_client", lambda: in_memory_db)
    # Direkter Aufruf: start_date ausdrücklich None (sonst steht dort das Query-Objekt von FastAPI).
    body = companies_module.get_company_ratings_overall(3, start_date=None)
    assert body["avg_overall"] is not None and body["n_reviews"] > 0 and body["n_categories"] == 13
    assert body["definition"] == companies_module.AVG_OVERALL_DEFINITION


def test_trend_stable_modes_add_n_reviews_per_window(in_memory_db, monkeypatch):
    monkeypatch.setattr(companies_module, "get_supabase_client", lambda: in_memory_db)
    body = companies_module.get_company_ratings_trend(3, mode="stable_all", months=12)
    assert body["mode"] == "stable_all" and "metrics" in body
    assert set(body["n_reviews"]) == {"current", "previous"} and body["n_reviews"]["current"] > 0
    assert body["source"] == "employee" and body["basis"] == "sternebewertung"
