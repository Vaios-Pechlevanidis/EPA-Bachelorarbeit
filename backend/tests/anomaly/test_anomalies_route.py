"""
Test Suite für die Route GET /api/analytics/company/{company_id}/anomalies.
Die App enthält nur den Anomalie-Router (main.py lädt Sentiment-Modelle und
bräuchte Netzwerk); Daten aus dem In-Memory-Store.

Ausführung:
    uv run python -m pytest tests/anomaly/test_anomalies_route.py -v
"""

import os
import sys

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from routes.anomalies import router  # noqa: E402
from services.rating_series_service import DIMENSIONS_BY_SOURCE  # noqa: E402

URL = "/api/analytics/company/{}/anomalies"


@pytest.fixture(scope="module")
def client(in_memory_db):
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


# ═══════════════════════════════════════════════════════════════════════════════
# 1. Einzelne Dimension
# ═══════════════════════════════════════════════════════════════════════════════

class TestSingleDimension:

    def test_default_response_shape(self, client):
        """Test: Standardabfrage → 200 mit series, anomalies, params, eligibility."""
        res = client.get(URL.format(3))
        assert res.status_code == 200
        body = res.json()
        assert set(body) == {"company_id", "source", "dimension", "series", "anomalies", "params", "eligibility"}
        assert body["dimension"] == "durchschnittsbewertung"
        assert body["params"]["min_reviews_per_month"] == 5

    def test_query_parameters_are_applied(self, client):
        """Test: penalty und min_delta landen in params; großer min_delta filtert alles."""
        body = client.get(URL.format(3), params={"penalty": 1.5, "min_delta": 5}).json()
        assert body["params"]["penalty"] == 1.5 and body["params"]["min_delta"] == 5
        assert body["anomalies"] == []

    def test_unknown_company_is_empty_and_ineligible(self, client):
        """Test: Unbekanntes Unternehmen → 200, leere Reihe, nicht geeignet, Grund gesetzt."""
        res = client.get(URL.format(999))
        assert res.status_code == 200
        body = res.json()
        assert body["series"] == [] and body["anomalies"] == []
        assert body["eligibility"]["eligible"] is False and body["eligibility"]["reason"]


# ═══════════════════════════════════════════════════════════════════════════════
# 2. Fehler
# ═══════════════════════════════════════════════════════════════════════════════

class TestErrors:

    @pytest.mark.parametrize("params", [
        {"source": "bewerber"},
        {"dimension": "gibt_es_nicht"},
        {"source": "candidates", "dimension": "kommunikation"},  # Dimension der anderen Quelle
        {"source": "bewerber", "dimension": "all"},
    ])
    def test_invalid_source_or_dimension_400(self, client, params):
        """Test: Ungültige source oder dimension → 400 mit {"detail": str}."""
        res = client.get(URL.format(3), params=params)
        assert res.status_code == 400
        assert isinstance(res.json()["detail"], str)

    @pytest.mark.parametrize("params", [{"penalty": 0}, {"penalty": -1}, {"min_delta": -0.1}])
    def test_out_of_range_parameters_422(self, client, params):
        """Test: penalty <= 0 oder min_delta < 0 → 422 (FastAPI-Validierung)."""
        res = client.get(URL.format(3), params=params)
        assert res.status_code == 422
        assert "detail" in res.json()


# ═══════════════════════════════════════════════════════════════════════════════
# 3. dimension=all
# ═══════════════════════════════════════════════════════════════════════════════

class TestAllDimensions:

    def test_documented_shape(self, client):
        """Test: dimension=all → dimensions je Dimension, gemeinsame Liste, params; keine series."""
        res = client.get(URL.format(3), params={"dimension": "all"})
        assert res.status_code == 200
        body = res.json()
        assert set(body) == {"company_id", "source", "dimension", "dimensions", "anomalies", "params"}
        assert body["dimension"] == "all"
        assert [d["dimension"] for d in body["dimensions"]] == DIMENSIONS_BY_SOURCE["employee"]
        for entry in body["dimensions"]:
            assert set(entry) == {"dimension", "eligibility", "anomalies"}
        assert len(body["anomalies"]) == sum(len(d["anomalies"]) for d in body["dimensions"])

    def test_candidates_source(self, client):
        """Test: dimension=all für candidates nutzt deren Dimensionen."""
        body = client.get(URL.format(3), params={"source": "candidates", "dimension": "all"}).json()
        assert [d["dimension"] for d in body["dimensions"]] == DIMENSIONS_BY_SOURCE["candidates"]

    def test_unknown_company_all_ineligible(self, client):
        """Test: Unbekanntes Unternehmen mit dimension=all → alle Dimensionen nicht geeignet."""
        body = client.get(URL.format(999), params={"dimension": "all"}).json()
        assert body["anomalies"] == []
        assert all(not d["eligibility"]["eligible"] for d in body["dimensions"])
