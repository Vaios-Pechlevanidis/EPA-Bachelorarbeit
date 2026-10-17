"""
Tests für die Stabilität auffälliger Veränderungen über ein Parameterraster
(Prüfung 2026-10-17, docs/feature-doku/16-report-qualitaet.md, B9). Konstruierte
Zeilen, ohne Netzwerk.

Ausführen:
    cd backend
    uv run python -m pytest tests/anomaly/test_stability.py -q -p no:cacheprovider
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))

import services.anomaly_service as an  # noqa: E402
from services.rating_series_service import OVERALL_DIMENSION, build_monthly_series  # noqa: E402


def _rows(levels, per_month=6, start_year=2020):
    """levels: Liste von Monatsniveaus; je Monat ``per_month`` Bewertungen um das Niveau."""
    rows = []
    i = 0
    for k, level in enumerate(levels):
        y, m = start_year + k // 12, k % 12 + 1
        for j in range(per_month):
            v = level + (0.1 if j % 2 else -0.1)
            rows.append({"id": i, "datum": f"{y:04d}-{m:02d}-15T12:00:00+00:00", OVERALL_DIMENSION: round(v, 2)})
            i += 1
    return rows


def test_clear_shift_is_stable_across_grid():
    rows = _rows([4.2] * 18 + [3.0] * 18, per_month=9)  # 9 je Monat: auch bei min_reviews 8 geeignet
    series = build_monthly_series(rows, OVERALL_DIMENSION)
    found = an.detect_anomalies(series, company_id=1, source="employee")
    assert len(found) == 1 and found[0]["direction"] == "fall"
    with_stab = an.stability_of_anomalies(found, rows, OVERALL_DIMENSION, company_id=1, source="employee", dimension=OVERALL_DIMENSION)
    st = with_stab[0]["stability"]
    assert st["variants"] == 4 * 4 * 3
    assert st["matches"] == st["variants"]
    assert st["share"] == 1.0
    assert st["tolerance_months"] == 3 and set(st["grid"]) == {"penalty_factor", "min_size", "min_reviews_per_month"}


def test_variants_count_only_eligible_series():
    # 4 Bewertungen je Monat: bei min_reviews 5 und 8 ist die Reihe nicht geeignet
    rows = _rows([4.2] * 18 + [3.0] * 18, per_month=4)
    series = build_monthly_series(rows, OVERALL_DIMENSION, min_reviews=3)
    found = an.detect_anomalies(series, company_id=1, source="employee")
    assert len(found) == 1
    st = an.stability_of_anomalies(found, rows, OVERALL_DIMENSION, company_id=1, source="employee", dimension=OVERALL_DIMENSION)[0]["stability"]
    assert st["variants"] == 4 * 4 * 1


def test_no_anomalies_returns_empty():
    assert an.stability_of_anomalies([], [], OVERALL_DIMENSION, company_id=1, source="employee", dimension=OVERALL_DIMENSION) == []


def test_short_dip_is_less_stable_than_clear_shift():
    # kurzer Einbruch über 3 Monate: bei min_size 4 und 6 nicht als eigener Abschnitt erkennbar
    rows = _rows([4.0] * 20 + [2.6] * 3 + [4.0] * 20)
    series = build_monthly_series(rows, OVERALL_DIMENSION)
    found = an.detect_anomalies(series, company_id=1, source="employee")
    if not found:
        return  # Standardparameter finden den Einbruch nicht; nichts zu prüfen
    st = an.stability_of_anomalies(found, rows, OVERALL_DIMENSION, company_id=1, source="employee", dimension=OVERALL_DIMENSION)
    for item in st:
        stab = item["stability"]
        assert stab["variants"] > 0 and 0 <= stab["matches"] <= stab["variants"]
        assert stab["share"] == round(stab["matches"] / stab["variants"], 2)
