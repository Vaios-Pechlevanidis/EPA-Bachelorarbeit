"""
Tests für fetch_all_rows_parallel (Leistung von topic-overview, 2026-10-05):
Die Seiten nach der ersten werden parallel geholt; das Ergebnis muss dasselbe
sein wie beim seitenweisen Lesen mit _fetch_all_rows, in derselben Reihenfolge.

Ohne Netzwerk, gegen den In-Memory-Store und einen nachgebildeten Builder.

Ausführen (aus dem backend-Verzeichnis):
    uv run python -m pytest tests/test_fetch_all_rows_parallel.py -q -p no:cacheprovider
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from database.in_memory_store import get_in_memory_client  # noqa: E402
from services.topic_average_rating_service import _fetch_all_rows, fetch_all_rows_parallel  # noqa: E402


def _employee_query(company_id):
    def build(count=None):
        return get_in_memory_client().table("employee").select("*", count=count).eq("company_id", company_id).order("id")
    return build


@pytest.mark.parametrize("page_size", [7, 50, 149, 150, 151, 1000])
def test_same_rows_as_sequential(page_size):
    build = _employee_query(1)
    sequential = _fetch_all_rows(build(), page_size=page_size)
    parallel = fetch_all_rows_parallel(build, page_size=page_size)
    assert [r["id"] for r in parallel] == [r["id"] for r in sequential]
    assert parallel == sequential


def test_empty_result():
    assert fetch_all_rows_parallel(_employee_query(999), page_size=10) == []


class _Result:
    def __init__(self, data, count):
        self.data = data
        self.count = count


class _Builder:
    """Liefert Seiten aus ``rows``; ``count`` wie die Datenbank (oder None)."""

    def __init__(self, rows, count_value, calls):
        self._rows, self._count_value, self._calls = rows, count_value, calls
        self._start = self._end = None

    def range(self, start, end):
        self._start, self._end = start, end
        return self

    def execute(self):
        self._calls.append(self._start)
        return _Result(self._rows[self._start:self._end + 1], self._count_value)


def _fake(rows, count_value):
    calls = []
    return (lambda count=None: _Builder(rows, count_value if count else None, calls)), calls


def test_without_total_falls_back_to_paging():
    rows = [{"id": i} for i in range(25)]
    make_query, calls = _fake(rows, count_value=None)
    assert fetch_all_rows_parallel(make_query, page_size=10) == rows
    assert sorted(calls) == [0, 10, 20]


def test_rows_added_after_count_are_read():
    """Zählt die Datenbank weniger Zeilen als später da sind, wird weitergelesen."""
    rows = [{"id": i} for i in range(35)]
    make_query, calls = _fake(rows, count_value=20)
    assert fetch_all_rows_parallel(make_query, page_size=10) == rows
    assert sorted(calls) == [0, 10, 20, 30]
