"""
Tests für services/forecast_service.py (Prüfung 2026-10-17): Baselines, Backtest mit
rollierendem Ursprung ohne Data Leakage, Fehlermaße und empirische Bandbreite.
Konstruierte Reihen, ohne Netzwerk.

Ausführen:
    cd backend
    uv run python -m pytest tests/forecast/test_forecast_service.py -q -p no:cacheprovider
"""

import math
import os
import random
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))

import services.forecast_service as fs  # noqa: E402


def _series(n=60, seed=1, level=3.5, slope=0.0, noise=0.2):
    rnd = random.Random(seed)
    return [min(5.0, max(1.0, level + slope * i + rnd.gauss(0, noise))) for i in range(n)]


def test_baselines_shapes_and_values():
    v = [3.0, 3.5, 4.0, 4.5]
    assert fs.naive_forecast(v, 3) == [4.5, 4.5, 4.5]
    assert fs.mean_forecast(v, 2) == [3.75, 3.75]
    assert fs.moving_average_forecast(v, 2, window=2) == [4.25, 4.25]
    assert fs.seasonal_naive_forecast(v, 2, season=12) is None
    assert fs.seasonal_naive_forecast(list(range(12)), 3, season=12) == [0.0, 1.0, 2.0]
    assert fs.naive_forecast([], 3) is None and fs.mean_forecast(v, 0) is None


def test_holt_forecast_is_clamped_and_finite():
    out = fs.holt_forecast([4.6, 4.8, 4.9, 5.0, 5.0, 5.0, 5.0, 5.0], 6)
    assert out is not None and len(out) == 6
    assert all(0.0 <= p <= 5.0 for p in out)
    assert fs.holt_forecast([4.0], 3) is None


def test_backtest_needs_min_train_plus_one():
    assert fs.rolling_origin_backtest(_series(n=24), min_train=24) is None
    bt = fs.rolling_origin_backtest(_series(n=25), min_train=24, horizon=3)
    assert bt is not None and bt["origins"] == 1 and bt["first_origin"] == 24


def test_backtest_uses_only_past_values_no_leakage():
    """Eine Reihe, die am Ende abrupt springt: Prognosen vom Ursprung vor dem Sprung
    dürfen den Sprung nicht kennen (naiv = letzter Wert vor dem Sprung)."""
    v = [3.0] * 30 + [5.0] * 6
    bt = fs.rolling_origin_backtest(v, horizon=6, min_train=24, max_origins=1, methods={"naive": fs.naive_forecast})
    assert bt["origins"] == 1 and bt["first_origin"] == 35
    # Ursprung 35: Anpassung auf v[:35] (endet 5,0), nur v[35] prüfbar → Fehler 0
    assert bt["methods"]["naive"]["n"] == 1
    bt2 = fs.rolling_origin_backtest(v, horizon=6, min_train=24, max_origins=6, methods={"naive": fs.naive_forecast})
    # Ursprung 30: Anpassung auf v[:30] (nur 3,0), Prognose 3,0 gegen 5,0 → Fehler +2 in allen Horizonten
    errs = bt2["residuals"]["naive"]
    assert all(2.0 in errs[h] for h in range(1, 7))


def test_backtest_metrics_and_best_method():
    v = _series(n=72, seed=3, slope=0.01, noise=0.1)
    bt = fs.rolling_origin_backtest(v, horizon=6, min_train=24, max_origins=12)
    assert set(bt["methods"]) == set(fs.METHODS)
    for m in bt["methods"].values():
        if m["n"]:
            assert m["mae"] >= 0 and m["rmse"] >= m["mae"] * 0.99
            assert len(m["mae_by_horizon"]) == 6
    assert bt["best_method"] in bt["methods"]
    assert bt["methods"]["naive"]["n"] == bt["methods"]["mean"]["n"]


def test_interval_offsets_from_residual_quantiles():
    bt = {"residuals": {"holt": {1: [-0.3, -0.1, 0.0, 0.1, 0.3, -0.2, 0.2, 0.0, 0.05, -0.05], 2: [0.1] * 3}}}
    off = fs.interval_offsets(bt, level=0.8, min_errors=8)
    assert set(off) == {1}
    assert off[1]["low"] < 0 < off[1]["high"] and off[1]["n"] == 10
    assert fs.interval_offsets(None) == {}


def test_interval_offsets_never_narrow_with_horizon():
    wide = [-0.6, -0.4, -0.2, 0.0, 0.2, 0.4, 0.6, -0.5, 0.5, 0.1]
    narrow = [-0.1, -0.05, 0.0, 0.05, 0.1, -0.08, 0.08, 0.02, -0.02, 0.0]
    bt = {"residuals": {"holt": {1: wide, 2: narrow, 3: wide}}}
    off = fs.interval_offsets(bt, level=0.8, min_errors=8)
    assert off[2]["low"] == off[1]["low"] and off[2]["high"] == off[1]["high"]   # Horizont 2 bleibt so breit wie 1
    assert off[2]["raw_high"] < off[2]["high"]                                   # rohes Quantil war schmaler
    assert off[3]["low"] <= off[2]["low"] and off[3]["high"] >= off[2]["high"]


def test_public_backtest_strips_residuals():
    v = _series(n=40)
    bt = fs.rolling_origin_backtest(v, horizon=3, min_train=24, max_origins=4, methods={"naive": fs.naive_forecast})
    pub = fs.public_backtest(bt)
    assert "residuals" not in pub and pub["origins"] == 4
