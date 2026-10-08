"""
Test Suite für GET /api/analytics/company/{company_id}/anomalies/{anomaly_id}/explanations
(Inkrement 2): Form der Antwort, 404 bei unbekannter anomaly_id, status wirkt.
In-Memory-Store, Stimmung im Lexikon-Modus.

Ausführung:
    uv run python -m pytest tests/drilldown/test_explanations_route.py -v
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from routes.anomalies import router

ANOMALIES = "/api/analytics/company/{}/anomalies"
EXPLAIN = "/api/analytics/company/{}/anomalies/{}/explanations"
DEMO_3 = 3


@pytest.fixture(scope="module")
def client(in_memory_db, lexicon_analyzer):
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


def _first_id(client, **params):
    anomalies = client.get(ANOMALIES.format(DEMO_3), params=params).json()["anomalies"]
    assert anomalies, "Demo 3 sollte Veränderungen haben"
    return anomalies[0]["id"]


class TestShape:

    def test_response_shape(self, client):
        """Test: anomaly, windows, comparison, explanations (leer) und Kopfangaben."""
        anomaly_id = _first_id(client)
        res = client.get(EXPLAIN.format(DEMO_3, anomaly_id))
        assert res.status_code == 200
        body = res.json()
        assert set(body) == {"company_id", "source", "dimension", "status", "dimension_topic", "anomaly", "windows",
                             "comparison", "explanations", "explanation_summary"}
        assert body["dimension_topic"] is None  # Gesamtbewertung
        assert body["explanations"] == [] and body["status"] is None
        assert body["explanation_summary"]["state"] == "offen", "leerer Belegspeicher, kein Abruf"
        assert body["anomaly"]["id"] == anomaly_id
        assert set(body["windows"]) == {"window_months", "before", "after"}
        assert body["windows"]["before"]["to"] < body["anomaly"]["date"] == body["windows"]["after"]["from"]
        cmp = body["comparison"]
        for key in ("before", "after", "rating_shift", "polarity_shift", "topics", "low_basis", "low_basis_rule",
                    "sentiment_mode", "sentiment_sample"):
            assert key in cmp
        assert cmp["sentiment_mode"] == "lexicon"
        assert body["windows"]["before"]["n_reviews"] == cmp["before"]["n_reviews"] > 0
        assert body["windows"]["after"]["n_reviews"] == cmp["after"]["n_reviews"] > 0

    def test_fall_has_lower_mean_after(self, client):
        """Test: Beim Abfall von Demo 3 (2023-01) ist die mittlere Gesamtnote danach niedriger."""
        body = client.get(EXPLAIN.format(DEMO_3, "employee:durchschnittsbewertung:2023-01")).json()
        assert body["anomaly"]["direction"] == "fall"
        assert body["comparison"]["rating_shift"] < 0

    def test_window_months(self, client):
        """Test: window_months verkleinert die Fenster."""
        anomaly_id = _first_id(client)
        w6 = client.get(EXPLAIN.format(DEMO_3, anomaly_id)).json()["windows"]
        w2 = client.get(EXPLAIN.format(DEMO_3, anomaly_id), params={"window_months": 2}).json()["windows"]
        assert w2["window_months"] == 2 and w2["before"]["months"] <= 2
        assert w2["before"]["n_reviews"] < w6["before"]["n_reviews"]

    def test_candidates_source(self, client):
        """Test: Bewerberquelle mit den Bewerberthemen."""
        anomaly_id = _first_id(client, source="candidates")
        body = client.get(EXPLAIN.format(DEMO_3, anomaly_id), params={"source": "candidates"}).json()
        assert body["source"] == "candidates" and len(body["comparison"]["topics"]) == 10


class TestErrors:

    @pytest.mark.parametrize("anomaly_id", [
        "employee:durchschnittsbewertung:1999-01",   # kein solcher Wechsel
        "quatsch",                                    # falscher Aufbau
        "employee:kommunikation:1999-01",            # Einzeldimension ohne diese Veränderung
    ])
    def test_unknown_anomaly_id_gives_404(self, client, anomaly_id):
        res = client.get(EXPLAIN.format(DEMO_3, anomaly_id))
        assert res.status_code == 404 and isinstance(res.json()["detail"], str)

    def test_unknown_company_gives_404(self, client):
        assert client.get(EXPLAIN.format(999, "employee:durchschnittsbewertung:2023-01")).status_code == 404

    def test_mismatching_source_gives_404(self, client):
        """Test: source passt nicht zur ID → die ID ist unter den Veränderungen dieser Quelle nicht vorhanden."""
        anomaly_id = _first_id(client)
        assert client.get(EXPLAIN.format(DEMO_3, anomaly_id), params={"source": "candidates"}).status_code == 404

    @pytest.mark.parametrize("params", [{"source": "foo"}, {"status": "eingestellt"}, {"dimension": "gibtsnicht"}])
    def test_invalid_parameters_give_400(self, client, params):
        res = client.get(EXPLAIN.format(DEMO_3, "employee:durchschnittsbewertung:2023-01"), params=params)
        assert res.status_code == 400 and isinstance(res.json()["detail"], str)

    def test_window_months_out_of_range(self, client):
        res = client.get(EXPLAIN.format(DEMO_3, "employee:durchschnittsbewertung:2023-01"), params={"window_months": 0})
        assert res.status_code == 422


class TestStatus:

    def test_status_restricts_windows(self, client):
        """Test: Mit status nur Bewertungen dieser Gruppe in den Fenstern; status in der Antwort.

        Der Abfall ab 2023-01 wird in Demo 3 für alle Mitarbeitenden und für die
        Angestellten allein erkannt."""
        anomaly_id = "employee:durchschnittsbewertung:2023-01"
        group = client.get(EXPLAIN.format(DEMO_3, anomaly_id), params={"status": "angestellt"}).json()
        everyone = client.get(EXPLAIN.format(DEMO_3, anomaly_id)).json()
        assert group["status"] == "angestellt" and everyone["status"] is None
        for side in ("before", "after"):
            assert 0 < group["windows"][side]["n_reviews"] < everyone["windows"][side]["n_reviews"]

    def test_status_window_counts_match_store(self, client):
        """Test: Fensterzahlen mit status = Bewertungen dieser Gruppe in den Monaten."""
        from database.in_memory_store import _TABLES

        anomaly_id = _first_id(client, status="ex-angestellt")
        body = client.get(EXPLAIN.format(DEMO_3, anomaly_id), params={"status": "ex-angestellt"}).json()
        for side in ("before", "after"):
            w = body["windows"][side]
            expected = sum(
                1 for r in _TABLES["employee"]
                if r["company_id"] == DEMO_3 and r["status"] == "Ex-Angestellt" and w["from"] <= r["datum"][:7] <= w["to"]
            )
            assert w["n_reviews"] == expected

    def test_anomaly_of_other_group_is_404(self, client):
        """Test: Eine Veränderung, die es nur ohne Status gibt, ist mit Status nicht auffindbar."""
        all_ids = {a["id"] for a in client.get(ANOMALIES.format(DEMO_3)).json()["anomalies"]}
        ex_ids = {a["id"] for a in client.get(ANOMALIES.format(DEMO_3), params={"status": "ex-angestellt"}).json()["anomalies"]}
        only_all = sorted(all_ids - ex_ids)
        assert only_all, "Demo 3: Veränderungen unterscheiden sich je Gruppe"
        res = client.get(EXPLAIN.format(DEMO_3, only_all[0]), params={"status": "ex-angestellt"})
        assert res.status_code == 404
