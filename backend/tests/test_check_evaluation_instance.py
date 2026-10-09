"""
Tests für scripts/check_evaluation_instance.py (Abnahme der Evaluationsinstanz,
Inkrement 6): reine Prüffunktionen mit konstruierten Werten, ohne DB und ohne Netz.

Ausführen:
    cd backend
    uv run python -m pytest tests/test_check_evaluation_instance.py -q -p no:cacheprovider
"""

import os
import sys

BACKEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, BACKEND_DIR)
sys.path.insert(0, os.path.join(BACKEND_DIR, "scripts"))

import check_evaluation_instance as ce  # noqa: E402
from services import evidence_service as ev  # noqa: E402


def test_read_env_keys_returns_only_wanted_keys(tmp_path):
    path = tmp_path / ".env"
    path.write_text("SUPABASE_KEY=geheim\n# Kommentar\nexport MARKET_LIVE_FETCH=0\nCONTEXT_LIVE_FETCH = '1'\n", encoding="utf-8")
    found = ce.read_env_keys(str(path), ce.BACKEND_EXPECTED)
    assert found == {"MARKET_LIVE_FETCH": "0", "CONTEXT_LIVE_FETCH": "1"}
    assert ce.read_env_keys(str(tmp_path / "fehlt"), ce.BACKEND_EXPECTED) == {}


def test_env_checks_environment_before_files():
    rows = ce.env_checks({"MARKET_LIVE_FETCH": "0", "VITE_SHOW_FORECAST": "0"},
                         {"MARKET_LIVE_FETCH": "1", "CONTEXT_LIVE_FETCH": "0"},
                         {"VITE_SHOW_FINANCE_EXTRAS": "false", "VITE_SHOW_FORECAST": "true"})
    status = {r["check"]: r["status"] for r in rows}
    assert status == {"MARKET_LIVE_FETCH": "ok", "CONTEXT_LIVE_FETCH": "ok", "VITE_SHOW_FINANCE_EXTRAS": "ok", "VITE_SHOW_FORECAST": "ok"}
    rows = ce.env_checks({}, {}, {"VITE_SHOW_FORECAST": "true"})
    assert all(r["status"] == ce.ERROR for r in rows)
    assert "nicht gesetzt" in rows[0]["result"]


def test_market_window_check_separates_before_start_and_gaps():
    windows = [ev.window_for_outlier("2020-03"), ev.window_for_outlier("2021-06")]
    prices = [m for m in ev.month_range("2020-01", "2021-05") if m != "2020-02"]
    res = ce.market_window_check(prices, windows)
    # Fenster 2019-12..2020-04 und 2021-03..2021-07; Kurse 2020-01..2021-05 ohne 2020-02
    assert res["missing"] == ["2020-02", "2021-06", "2021-07"]
    assert res["before_start"] == ["2019-12"]
    res = ce.market_window_check(ev.month_range("2020-02", "2022-12"), windows)
    assert res["before_start"] == ["2019-12", "2020-01"] and res["missing"] == []


def test_market_row_states():
    windows = [ev.window_for_outlier("2020-03")]
    assert ce.market_row("A", None, None, windows)["status"] == ce.HINT
    assert ce.market_row("A", "AAA", None, windows)["status"] == ce.GAP
    full = {"prices": [{"period": m} for m in ev.month_range("2019-01", "2021-01")]}
    assert ce.market_row("A", "AAA", full, windows)["status"] == ce.OK
    late = {"prices": [{"period": m} for m in ev.month_range("2020-02", "2021-01")]}
    assert ce.market_row("A", "AAA", late, windows)["status"] == ce.HINT


def test_evidence_row():
    complete = {"sources": {"gnews": {"months": 5, "missing": 0}, "eqs": {"months": 5, "missing": 0}}}
    gap = {"sources": {"gnews": {"months": 5, "missing": 2}}}
    assert ce.evidence_row("A", [complete])["status"] == ce.OK
    row = ce.evidence_row("A", [complete, gap])
    assert row["status"] == ce.GAP and "gnews 8/10 Monate" in row["result"]
    assert ce.evidence_row("A", [])["status"] == ce.OK


def test_timing_rows_with_fake_getter():
    calls = []

    def getter(url):
        calls.append(url)
        if url.endswith("/market") and "/7/" in url:
            return 500, 0.1, "HTTP 500"
        return 200, 4.0 if "topic-overview" in url else 0.2, None

    rows = ce.timing_rows("http://x/", [{"id": 7, "name": "A"}, {"id": 8, "name": "B"}], getter=getter)
    status = {r["check"]: r["status"] for r in rows}
    assert status["Kurs"] == ce.ERROR and status["Topic-Übersicht"] == ce.WARN and status["Ø Score"] == ce.OK
    assert len(calls) == 2 * len(ce.ENDPOINTS) and calls[0].startswith("http://x/api/")
    assert all(path.count("{id}") == 1 for _, path in ce.ENDPOINTS)


def test_format_table_and_failing_states():
    rows = [{"area": "Umgebung", "check": "X", "result": "0", "status": ce.OK}]
    assert ce.format_table(rows).splitlines()[2] == "| Umgebung | X | 0 | ok |"
    assert ce.FAILING == {ce.GAP, ce.ERROR}
