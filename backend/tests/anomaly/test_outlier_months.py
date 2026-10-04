"""
Test Suite für auffällige Einzelmonate (E14): detect_outlier_months mit
konstruierten Reihen und outlier_months in der Route /anomalies.

Ausführung:
    uv run python -m pytest tests/anomaly/test_outlier_months.py -v
"""

import os
import random
import sys

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
import services.anomaly_service as svc  # noqa: E402
from routes.anomalies import router  # noqa: E402


def _series(values, n_values=20, evaluated=None):
    """Monatsreihe ab 2020-01 aus Monatsmitteln; None = nicht bewertet."""
    out = []
    for i, v in enumerate(values):
        y, m = 2020 + i // 12, i % 12 + 1
        ok = v is not None if evaluated is None else evaluated[i]
        out.append({"period": f"{y:04d}-{m:02d}", "mean": v, "count": n_values, "n_values": n_values if ok else 2,
                    "evaluated": ok})
    return out


def _noisy(n, level, sigma=0.1, seed=1):
    rng = random.Random(seed)
    return [round(level + rng.gauss(0, sigma), 3) for _ in range(n)]


def _outliers(series, **kw):
    return svc.detect_outlier_months(series, company_id=1, source="employee", **kw)


class TestDetectOutlierMonths:

    def test_single_dip_is_flagged(self):
        """Test: Ein einzelner Monat weit unter dem Niveau → genau ein Einzelmonat, Abfall."""
        values = _noisy(30, 4.0)
        values[15] = 2.6
        found = _outliers(_series(values))
        assert [o["date"] for o in found] == ["2021-04"]
        o = found[0]
        assert o["direction"] == "fall" and o["deviation"] == pytest.approx(2.6 - o["level"], abs=1e-3)
        assert o["level"] == pytest.approx(4.0, abs=0.1) and o["threshold"] >= 0.5
        assert o["id"] == "employee:durchschnittsbewertung:2021-04:einzelmonat"

    def test_single_peak_is_rise(self):
        values = _noisy(30, 3.0)
        values[10] = 4.4
        assert [o["direction"] for o in _outliers(_series(values))] == ["rise"]

    def test_level_shift_is_not_an_outlier(self):
        """Test: Ein anhaltender Niveauwechsel erzeugt keine Einzelmonate."""
        values = _noisy(20, 4.0) + _noisy(20, 3.0, seed=2)
        assert _outliers(_series(values)) == []

    def test_small_deviation_below_min_delta(self):
        """Test: Bei sehr ruhiger Reihe reicht 3 σ nicht; mindestens 0,5 Sterne nötig."""
        values = [4.0] * 30
        values[12] = 3.6   # 0,4 Sterne < 0,5
        assert _outliers(_series(values)) == []
        values[12] = 3.4   # 0,6 Sterne
        assert [o["date"] for o in _outliers(_series(values))] == ["2021-01"]

    def test_noisy_series_needs_three_sigma(self):
        """Test: Bei großer Streuung reicht 0,5 Sterne nicht, Schwelle 3 · noise_sigma."""
        values = _noisy(40, 3.8, sigma=0.35, seed=5)
        found = _outliers(_series(values))
        assert all(abs(o["deviation"]) >= o["threshold"] > 0.5 for o in found)

    def test_unevaluated_months_ignored(self):
        """Test: Nicht bewertete Monate werden nie gemeldet."""
        values = _noisy(30, 4.0)
        values[15] = 1.5
        evaluated = [True] * 30
        evaluated[15] = False
        found = _outliers(_series(values, evaluated=evaluated))
        assert found == []

    def test_sorted_by_magnitude(self):
        values = _noisy(40, 4.0)
        values[8], values[30] = 3.0, 2.5
        assert [o["date"] for o in _outliers(_series(values))] == ["2022-07", "2020-09"]

    def test_too_short(self):
        assert _outliers(_series([4.0])) == []


@pytest.fixture(scope="module")
def client(in_memory_db):
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


class TestRoute:

    def test_outlier_months_in_response(self, client):
        body = client.get("/api/analytics/company/3/anomalies").json()
        assert isinstance(body["outlier_months"], list)
        assert body["params"]["outlier_sigma_factor"] == 3.0 and body["params"]["outlier_min_delta"] == 0.5
        for o in body["outlier_months"]:
            assert abs(o["deviation"]) >= o["threshold"]

    def test_ineligible_series_has_none(self, client):
        body = client.get("/api/analytics/company/999/anomalies").json()
        assert body["outlier_months"] == []

    def test_dimension_all(self, client):
        body = client.get("/api/analytics/company/3/anomalies", params={"dimension": "all"}).json()
        per_dim = sum(len(d["outlier_months"]) for d in body["dimensions"])
        assert len(body["outlier_months"]) == per_dim
