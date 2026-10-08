"""
Test Suite für den freien Drill-down (E17): period_windows und
GET /api/analytics/company/{company_id}/compare, auch ohne erkannte Veränderung.
In-Memory-Store, Stimmung im Lexikon-Modus.

Ausführung:
    uv run python -m pytest tests/drilldown/test_period_comparison.py -v
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import services.explanation_service as es
from _helpers import store_rows
from routes.anomalies import router

URL = "/api/analytics/company/{}/compare"


class TestPeriodWindows:

    def test_single_month_uses_six_months_before(self):
        w = es.period_windows("2024-03", "2024-03")
        assert (w["after"]["from"], w["after"]["to"], w["after"]["end"]) == ("2024-03", "2024-03", "2024-03-31")
        assert (w["before"]["from"], w["before"]["to"], w["before"]["months"]) == ("2023-09", "2024-02", 6)
        assert w["window_months"] == 6

    def test_long_selection_uses_same_length(self):
        w = es.period_windows("2022-01", "2023-12")
        assert w["after"]["months"] == 24 and w["before"]["months"] == 24
        assert (w["before"]["from"], w["before"]["to"]) == ("2020-01", "2021-12")

    def test_year_boundary(self):
        w = es.period_windows("2024-01", "2024-02")
        assert (w["before"]["from"], w["before"]["to"]) == ("2023-07", "2023-12")

    @pytest.mark.parametrize("f, t", [("2024-13", "2024-12"), ("2024-1", "2024-02"), ("abc", "2024-01"), ("2024-05", "2024-03")])
    def test_invalid(self, f, t):
        with pytest.raises(ValueError):
            es.period_windows(f, t)


@pytest.fixture(scope="module")
def client(in_memory_db, lexicon_analyzer):
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


class TestCompareRoute:

    def test_shape_and_counts(self, client):
        body = client.get(URL.format(1), params={"from": "2024-03", "to": "2024-08"}).json()
        assert set(body) == {"company_id", "source", "dimension", "status", "dimension_topic", "selection", "windows",
                             "comparison", "explanations", "explanation_summary"}
        assert body["selection"] == {"from": "2024-03", "to": "2024-08"} and body["explanations"] == []
        assert body["explanation_summary"]["state"] == "offen"
        rows = store_rows("employee", 1)
        for side in ("before", "after"):
            w = body["windows"][side]
            assert w["n_reviews"] == sum(1 for r in rows if w["from"] <= r["datum"][:7] <= w["to"])
            assert body["comparison"][side]["n_reviews"] == w["n_reviews"]
        assert body["comparison"]["sentiment_mode"] == "lexicon"

    def test_works_without_detected_change(self, client):
        """Test: Demo 1 hat in der Gesamtbewertung keine Veränderung; der Vergleich geht trotzdem."""
        assert client.get("/api/analytics/company/1/anomalies").json()["anomalies"] == []
        assert client.get(URL.format(1), params={"from": "2023-01", "to": "2023-01"}).status_code == 200

    def test_dimension_status_and_topic(self, client):
        body = client.get(URL.format(3), params={"from": "2023-01", "to": "2023-06", "dimension": "image",
                                                 "status": "angestellt"}).json()
        assert body["dimension_topic"] == "Image" and body["status"] == "angestellt"
        assert "value_shift" in body["comparison"]
        everyone = client.get(URL.format(3), params={"from": "2023-01", "to": "2023-06"}).json()
        assert body["windows"]["after"]["n_reviews"] < everyone["windows"]["after"]["n_reviews"]

    def test_empty_period(self, client):
        """Test: Zeitraum ohne Bewertungen → 200, kleine Basis."""
        body = client.get(URL.format(1), params={"from": "2030-01", "to": "2030-02"}).json()
        assert body["windows"]["after"]["n_reviews"] == 0 and body["comparison"]["low_basis"] is True

    @pytest.mark.parametrize("params", [
        {"from": "2024-13", "to": "2024-12"},
        {"from": "2024-05", "to": "2024-03"},
        {"from": "2024-01", "to": "2024-02", "source": "foo"},
        {"from": "2024-01", "to": "2024-02", "status": "eingestellt"},
        {"from": "2024-01", "to": "2024-02", "dimension": "schnelle_antwort"},
    ])
    def test_invalid_gives_400(self, client, params):
        res = client.get(URL.format(1), params=params)
        assert res.status_code == 400 and isinstance(res.json()["detail"], str)

    def test_missing_parameters_give_422(self, client):
        assert client.get(URL.format(1), params={"from": "2024-01"}).status_code == 422
