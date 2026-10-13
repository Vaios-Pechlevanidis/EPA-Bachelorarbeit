"""
Tests für die Kenngrößen der Prognose (forecast_with_details, 2026-10-13).
Sie erklären im Detailfenster des Zeitverlaufs, wie die Prognose entsteht:
Verfahren, Glättungsgewichte, geglättetes Niveau und Steigung.

Ausführung:
    uv run python -m pytest tests/forecast/test_forecast_details.py -v
"""

import os
import sys
from datetime import datetime
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from routes.analytics import calculate_forecast, forecast_with_details


def _make_historical(scores: list[float], start_year: int = 2024, start_month: int = 1) -> list[dict]:
    data = []
    for i, score in enumerate(scores):
        month_offset = start_month + i
        year = start_year + (month_offset - 1) // 12
        month = ((month_offset - 1) % 12) + 1
        date_obj = datetime(year, month, 1)
        data.append({
            "date": date_obj.strftime("%Y-%m"),
            "date_display": date_obj.strftime("%b %Y"),
            "score": round(score, 2),
            "count": 10,
            "is_forecast": False,
        })
    return data


SCORES = [3.0, 3.4, 2.8, 3.6, 3.1, 3.5, 3.2, 3.9, 3.3, 3.7, 3.4, 4.0, 3.6, 3.8]


def test_without_forecast_no_info():
    assert forecast_with_details([], 6) == ([], None)
    assert forecast_with_details(_make_historical([3.0]), 6) == ([], None)
    assert forecast_with_details(_make_historical(SCORES), 0) == ([], None)


def test_same_forecast_as_calculate_forecast():
    data = _make_historical(SCORES)
    forecast, _ = forecast_with_details(data, 6)
    assert forecast == calculate_forecast(data, 6)


def test_holt_info_fields():
    data = _make_historical(SCORES)
    _, info = forecast_with_details(data, 6)
    assert info["method"] == "holt"
    assert info["n_months"] == len(SCORES)
    assert info["first_month"] == "2024-01"
    assert info["last_month"] == "2025-02"
    assert abs(info["historical_mean"] - sum(SCORES) / len(SCORES)) < 1e-3
    assert 0.0 <= info["alpha"] <= 1.0
    assert 0.0 <= info["beta"] <= 1.0
    assert len(info["smoothed"]) == len(SCORES)
    assert info["smoothed"][-1]["date"] == "2025-02"
    assert info["smoothed"][-1]["value"] == info["level"]
    assert info["clamped"] is False


def test_forecast_is_level_plus_h_times_trend():
    """Holt: Prognose für Monat h = Niveau am Ende + h * Steigung (ohne Begrenzung)."""
    data = _make_historical(SCORES)
    forecast, info = forecast_with_details(data, 6)
    for h, point in enumerate(forecast, start=1):
        expected = info["level"] + h * info["trend"]
        assert abs(point["score"] - expected) < 0.01


def test_clamped_flag():
    data = _make_historical([3.0, 3.4, 3.8, 4.2, 4.6, 4.9, 5.0, 5.0])
    forecast, info = forecast_with_details(data, 12)
    assert all(0.0 <= p["score"] <= 5.0 for p in forecast)
    assert isinstance(info["clamped"], bool)


def test_fallback_reports_mean():
    data = _make_historical(SCORES)
    with patch("statsmodels.tsa.holtwinters.Holt", side_effect=ValueError("boom")):
        forecast, info = forecast_with_details(data, 3)
    assert info["method"] == "mean"
    assert "alpha" not in info
    assert all(abs(p["score"] - round(sum(SCORES) / len(SCORES), 2)) < 1e-9 for p in forecast)
