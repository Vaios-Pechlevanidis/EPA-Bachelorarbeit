"""
Tests für die Unsicherheit des Ø Score und der Trend-Differenz (Prüfung 2026-10-17,
docs/feature-doku/16-report-qualitaet.md): Stichproben-Standardabweichung, halbe Breite
des 95-%-Intervalls des Mittels (t-Verteilung) und der Differenz zweier Fenster (Welch).
Konstruierte Werte, ohne Netzwerk.

Ausführen:
    cd backend
    uv run python -m pytest tests/test_score_uncertainty.py -q -p no:cacheprovider
"""

import math
import os
import sys
from datetime import datetime, timezone

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

import services.score_service as sc  # noqa: E402


def test_sample_sd_matches_textbook():
    assert sc.sample_sd([2.0, 4.0, 4.0, 4.0, 5.0, 5.0, 7.0, 9.0]) == pytest.approx(2.138, abs=1e-3)
    assert sc.sample_sd([3.0]) is None
    assert sc.sample_sd([]) is None


def test_mean_ci95_uses_t_distribution():
    values = [3.0, 4.0, 5.0, 4.0, 3.0]  # n = 5, sd = 0.8367, t(4) = 2.776
    ci = sc.mean_ci95(values)
    assert ci == pytest.approx(2.776 * 0.8367 / math.sqrt(5), abs=1e-3)


def test_mean_ci95_none_for_single_value():
    assert sc.mean_ci95([4.0]) is None


def test_ci_shrinks_with_n():
    small = sc.mean_ci95([1.0, 5.0] * 5)
    large = sc.mean_ci95([1.0, 5.0] * 500)
    assert small > large > 0


def test_difference_ci95_welch():
    a = [4.0, 4.5, 5.0, 4.5, 4.0, 4.5]
    b = [3.0, 3.5, 2.5, 3.0, 3.5, 3.0]
    ci = sc.difference_ci95(a, b)
    se = math.sqrt(sc.sample_sd(a) ** 2 / 6 + sc.sample_sd(b) ** 2 / 6)
    assert ci == pytest.approx(2.228 * se, rel=0.02)  # Freiheitsgrade nach Welch ≈ 10 → t ≈ 2,228
    assert sc.difference_ci95(a, [3.0]) is None


def test_score_from_rows_reports_sd_and_ci():
    rows = [{"durchschnittsbewertung": v} for v in (3.0, 4.0, 5.0, 4.0, 3.0)] + [{"durchschnittsbewertung": None}]
    out = sc.score_from_rows(rows)
    assert out["score"] == 3.8 and out["score_n"] == 5
    assert out["score_sd"] == pytest.approx(0.837, abs=1e-3)
    assert out["score_ci95"] == pytest.approx(1.039, abs=1e-3)


def test_score_from_rows_without_values():
    out = sc.score_from_rows([{"durchschnittsbewertung": None}])
    assert out == {"score": None, "score_n": 0, "score_sd": None, "score_ci95": None}


def test_score_trend_carries_difference_ci():
    today = datetime(2026, 10, 17, tzinfo=timezone.utc)
    rows = []
    i = 0
    for month in range(1, 13):  # 2025-01 .. 2025-12: aktuelles Fenster um 4,0
        for v in (3.5, 4.0, 4.5):
            rows.append({"id": i, "datum": f"2025-{month:02d}-15T12:00:00+00:00", "durchschnittsbewertung": v}); i += 1
    for month in range(1, 13):  # 2024-01 .. 2024-12: Vorfenster um 3,0
        for v in (2.5, 3.0, 3.5):
            rows.append({"id": i, "datum": f"2024-{month:02d}-15T12:00:00+00:00", "durchschnittsbewertung": v}); i += 1
    out = sc.score_trend(rows, 12, today)
    assert out["difference"] == 1.0
    assert out["difference_ci95"] is not None and 0 < out["difference_ci95"] < 0.5
    assert out["n_reviews"] == {"current": 36, "previous": 36}
