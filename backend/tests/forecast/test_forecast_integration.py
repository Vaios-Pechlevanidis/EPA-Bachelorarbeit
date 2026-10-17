"""
Tests für die Ergänzungen von ``forecast_with_details`` (Prüfung 2026-10-17):
Backtest, Bandbreite je Prognosepunkt, Monate seit dem letzten Datenmonat und
Monate unter der Mindestdichte. Synthetische Reihe, ohne Netzwerk.

Ausführen:
    cd backend
    uv run python -m pytest tests/forecast/test_forecast_integration.py -q -p no:cacheprovider
"""

import os
import random
import sys
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))

from routes.analytics import forecast_with_details  # noqa: E402


def _history(n=48, seed=7):
    rnd = random.Random(seed)
    out = []
    for i in range(n):
        y, m = 2021 + i // 12, i % 12 + 1
        out.append({"date": f"{y:04d}-{m:02d}", "date_display": "", "score": round(3.5 + rnd.gauss(0, 0.2), 2),
                    "count": 3 if i % 5 == 0 else 12, "is_forecast": False})
    return out


def test_forecast_points_carry_band_and_info():
    forecast, info = forecast_with_details(_history(), 6, today=datetime(2026, 10, 17))
    assert len(forecast) == 6
    assert info["method"] == "holt"
    assert info["backtest"] is not None and "residuals" not in info["backtest"]
    assert set(info["backtest"]["methods"]) >= {"holt", "naive", "mean", "ma6", "snaive12"}
    assert info["interval"]["level"] == 0.8 and info["interval"]["available"] is True
    for point in forecast:
        assert point["low"] is not None and point["high"] is not None
        assert 0.0 <= point["low"] <= point["score"] <= point["high"] <= 5.0
    # letzter Datenmonat 2024-12 → bis Okt. 2026 sind es 22 Monate
    assert info["last_month"] == "2024-12" and info["months_since_last_data"] == 22
    assert info["months_below_min_reviews"] == 10 and info["min_reviews_per_month"] == 5


def test_short_series_has_no_backtest_but_forecast():
    forecast, info = forecast_with_details(_history(n=12), 6, today=datetime(2026, 10, 17))
    assert len(forecast) == 6
    assert info["backtest"] is None and info["interval"]["available"] is False
    assert all(p["low"] is None and p["high"] is None for p in forecast)
