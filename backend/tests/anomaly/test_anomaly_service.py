"""
Test Suite für den Anomalie-Service (Zyklus 2, Inkrement 1).
Prüft company_anomalies und company_anomalies_all gegen den In-Memory-Store
(Demo 1 bis 3) sowie Eignung und n_reviews-Aufteilung.

Ausführung:
    uv run python -m pytest tests/anomaly/test_anomaly_service.py -v
"""

import math
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
import services.anomaly_service as svc  # noqa: E402
import services.rating_series_service as rs  # noqa: E402

DEMO_1, DEMO_2, DEMO_3 = 1, 2, 3
UNKNOWN_COMPANY = 999


# ─── Fixtures ────────────────────────────────────────────────────────────────

def _months_apart(a: str, b: str) -> int:
    """Helper: Abstand zweier Monate YYYY-MM in Monaten."""
    ya, ma = (int(x) for x in a.split("-"))
    yb, mb = (int(x) for x in b.split("-"))
    return abs((ya * 12 + ma) - (yb * 12 + mb))


def _find(anomalies, direction, month, tolerance=1):
    return [a for a in anomalies if a["direction"] == direction and _months_apart(a["date"], month) <= tolerance]


# ═══════════════════════════════════════════════════════════════════════════════
# 1. Demo-Unternehmen mit Startwerten
# ═══════════════════════════════════════════════════════════════════════════════

class TestDemoCompanies:
    """Erwartete Ergebnisse auf den synthetischen Demo-Reihen."""

    def test_demo3_fall_and_rise(self, in_memory_db):
        """Test: Demo 3 (V-Form) → fall um 2023-01 und rise um 2023-12, je ±1 Monat."""
        result = svc.company_anomalies(DEMO_3, "employee")
        anomalies = result["anomalies"]
        assert result["eligibility"]["eligible"] is True
        assert len(_find(anomalies, "fall", "2023-01")) == 1
        assert len(_find(anomalies, "rise", "2023-12")) == 1
        print(f"\n✓ Demo 3: {[(a['date'], a['direction'], a['delta']) for a in anomalies]}")

    @pytest.mark.parametrize("company_id", [DEMO_1, DEMO_2])
    def test_demo1_and_demo2_without_anomaly(self, in_memory_db, company_id):
        """Test: Demo 1 (steigend) und Demo 2 (sinkend) → keine auffällige Veränderung."""
        result = svc.company_anomalies(company_id, "employee")
        assert result["eligibility"]["eligible"] is True
        assert result["anomalies"] == []

    def test_sorted_fall_before_rise(self, in_memory_db):
        """Test: Sortierung fall vor rise."""
        directions = [a["direction"] for a in svc.company_anomalies(DEMO_3, "employee")["anomalies"]]
        assert directions == sorted(directions, key={"fall": 0, "rise": 1}.get)

    def test_anomaly_fields(self, in_memory_db):
        """Test: Felder und id-Format je Anomalie."""
        a = svc.company_anomalies(DEMO_3, "employee")["anomalies"][0]
        assert a["id"] == f"employee:durchschnittsbewertung:{a['date']}"
        assert a["company_id"] == DEMO_3
        assert a["severity"] in ("high", "medium")
        assert a["method"] == "pelt"
        assert a["params"]["penalty_mode"] == "scaled" and a["params"]["penalty_factor"] == 2.0
        assert a["params"]["penalty"] > 0 and a["params"]["noise_sigma"] >= 0.05
        assert a["params"]["min_delta"] == 0.3
        assert round(a["after_mean"] - a["before_mean"], 2) == round(a["delta"], 2)

    def test_n_reviews_is_sum_of_before_and_after(self, in_memory_db):
        """Test: n_reviews_before + n_reviews_after == n_reviews, beide > 0."""
        for a in svc.company_anomalies(DEMO_3, "employee")["anomalies"]:
            assert a["n_reviews_before"] > 0 and a["n_reviews_after"] > 0
            assert a["n_reviews_before"] + a["n_reviews_after"] == a["n_reviews"]

    def test_segment_bounds_and_gap_fields(self, in_memory_db):
        """Test: Abschnittsgrenzen, Vormonat und Lücke sind konsistent mit der Reihe."""
        result = svc.company_anomalies(DEMO_3, "employee")
        evaluated = [m["period"] for m in result["series"] if m["evaluated"]]
        for a in result["anomalies"]:
            i = evaluated.index(a["date"])
            assert a["previous_period"] == evaluated[i - 1]
            assert a["gap_months"] == svc._months_between(a["previous_period"], a["date"]) - 1 >= 0
            assert a["before_from"] <= a["previous_period"] < a["date"] <= a["after_to"]
            assert a["before_from"] in evaluated and a["after_to"] in evaluated
            month = next(m for m in result["series"] if m["period"] == a["date"])
            assert a["month_mean"] == month["mean"]
            near = abs(a["month_mean"] - a["before_mean"]) < abs(a["month_mean"] - a["after_mean"])
            assert a["month_near_previous_level"] is near

    def test_adjacent_segments_share_bounds(self, in_memory_db):
        """Test: Nach-Abschnitt einer Veränderung endet direkt vor der nächsten."""
        anomalies = sorted(svc.company_anomalies(DEMO_3, "employee")["anomalies"], key=lambda a: a["date"])
        for a, b in zip(anomalies, anomalies[1:]):
            assert a["after_to"] == b["previous_period"]
            assert a["after_mean"] == b["before_mean"]

    def test_months_between(self):
        assert svc._months_between("2023-01", "2023-03") == 2
        assert svc._months_between("2022-12", "2023-01") == 1

    def test_series_covers_all_months(self, in_memory_db):
        """Test: Reihe enthält alle Monate mit period, mean, count, n_values, evaluated."""
        series = svc.company_anomalies(DEMO_3, "employee")["series"]
        assert set(series[0]) == {"period", "mean", "count", "n_values", "evaluated"}
        assert all(m["evaluated"] == (m["n_values"] >= 5) for m in series)
        assert [m["period"] for m in series] == rs.month_range(series[0]["period"], series[-1]["period"])


class TestPenaltyModes:
    """Skalierter Strafterm (Standard) und fester Modus im Service."""

    def test_response_params_scaled(self, in_memory_db):
        """Test: Antwort nennt Modus, Faktor, noise_sigma, verwendeten Strafterm und n."""
        params = svc.company_anomalies(DEMO_3, "employee")["params"]
        assert params["penalty_mode"] == "scaled"
        assert params["penalty_factor"] == 2.0
        assert params["n_evaluated"] == 40
        expected = 2.0 * params["noise_sigma"] ** 2 * math.log(params["n_evaluated"])
        assert params["penalty"] == pytest.approx(expected, rel=1e-4)

    def test_anomaly_params_equal_response_params(self, in_memory_db):
        """Test: params je Anomalie enthalten denselben verwendeten Strafterm wie die Antwort."""
        result = svc.company_anomalies(DEMO_3, "employee")
        for a in result["anomalies"]:
            assert a["params"]["penalty"] == result["params"]["penalty"]
            assert a["params"]["noise_sigma"] == result["params"]["noise_sigma"]

    def test_fixed_mode_reproduces_previous_results(self, in_memory_db):
        """Test: penalty=0.5 (fester Modus) liefert die bisherigen Ergebnisse für Demo 1–3."""
        demo3 = svc.company_anomalies(DEMO_3, "employee", penalty=0.5)
        assert demo3["params"]["penalty_mode"] == "fixed" and demo3["params"]["penalty"] == 0.5
        assert demo3["params"]["penalty_factor"] is None
        assert len(_find(demo3["anomalies"], "fall", "2023-01")) == 1
        assert len(_find(demo3["anomalies"], "rise", "2023-12")) == 1
        for company_id in (DEMO_1, DEMO_2):
            assert svc.company_anomalies(company_id, "employee", penalty=0.5)["anomalies"] == []

    def test_higher_factor_never_adds_changes(self, in_memory_db):
        """Test: Größerer Faktor → nicht mehr Veränderungen (Demo 3, alle Dimensionen)."""
        counts = [len(svc.company_anomalies_all(DEMO_3, "employee", penalty_factor=f)["anomalies"]) for f in (1, 2, 4)]
        assert counts[0] >= counts[1] >= counts[2]

    def test_all_dimensions_have_own_sigma(self, in_memory_db):
        """Test: dimension=all berechnet sigma, n und Strafterm je Dimension."""
        result = svc.company_anomalies_all(DEMO_3, "employee")
        assert result["params"]["penalty_mode"] == "scaled" and result["params"]["penalty"] is None
        sigmas = {d["params"]["noise_sigma"] for d in result["dimensions"]}
        assert len(sigmas) > 1
        for d in result["dimensions"]:
            single = svc.company_anomalies(DEMO_3, "employee", d["dimension"])["params"]
            assert d["params"]["penalty"] == single["penalty"]

    def test_ineligible_series_reports_params(self, in_memory_db):
        """Test: Auch ohne Erkennung stehen Modus und Faktor in params."""
        params = svc.company_anomalies(UNKNOWN_COMPANY, "employee")["params"]
        assert params["penalty_mode"] == "scaled" and params["n_evaluated"] == 0


# ═══════════════════════════════════════════════════════════════════════════════
# 2. Nicht geeignete Reihen
# ═══════════════════════════════════════════════════════════════════════════════

class TestIneligible:
    """Nicht geeignete Reihen liefern keine Anomalien, aber einen Grund."""

    def test_unknown_company(self, in_memory_db):
        """Test: Unternehmen ohne Bewertungen → eligible false, reason gesetzt, leer."""
        result = svc.company_anomalies(UNKNOWN_COMPANY, "employee")
        assert result["series"] == []
        assert result["anomalies"] == []
        assert result["eligibility"]["eligible"] is False
        assert result["eligibility"]["evaluated_months"] == 0
        assert result["eligibility"]["reason"]

    def test_too_few_evaluated_months(self, monkeypatch):
        """Test: 11 bewertete Monate (< 12) → eligible false mit Anzahl im Grund."""
        rows = [
            {"id": i, "datum": f"2023-{month:02d}-15", "durchschnittsbewertung": 4.0 if month < 7 else 2.0}
            for month in range(1, 12) for i in range(5)
        ]
        monkeypatch.setattr(rs, "fetch_review_rows", lambda *args, **kwargs: rows)
        result = svc.company_anomalies(42, "employee")
        assert result["eligibility"] == {
            "eligible": False, "evaluated_months": 11, "min_evaluated_months": 12,
            "reason": result["eligibility"]["reason"],
        }
        assert "11" in result["eligibility"]["reason"]
        assert result["anomalies"] == []  # trotz deutlichem Sprung keine Erkennung

    def test_invalid_dimension_raises(self, in_memory_db):
        """Test: Unbekannte Dimension → ValueError (Route macht daraus 400)."""
        with pytest.raises(ValueError):
            svc.company_anomalies(DEMO_3, "employee", "gibt_es_nicht")


# ═══════════════════════════════════════════════════════════════════════════════
# 3. Alle Dimensionen
# ═══════════════════════════════════════════════════════════════════════════════

class TestAllDimensions:
    """company_anomalies_all fasst alle Dimensionen einer Quelle zusammen."""

    def test_shape_and_order(self, in_memory_db):
        """Test: je Dimension aus DIMENSIONS_BY_SOURCE ein Eintrag, gleiche Reihenfolge."""
        result = svc.company_anomalies_all(DEMO_3, "employee")
        assert result["dimension"] == "all"
        assert [d["dimension"] for d in result["dimensions"]] == rs.DIMENSIONS_BY_SOURCE["employee"]
        for entry in result["dimensions"]:
            assert set(entry) == {"dimension", "eligibility", "anomalies", "outlier_months", "params"}

    def test_combined_list_is_union_and_sorted(self, in_memory_db):
        """Test: Gesamtliste = alle Anomalien der Dimensionen, sortiert."""
        result = svc.company_anomalies_all(DEMO_3, "employee")
        per_dimension = [a for d in result["dimensions"] for a in d["anomalies"]]
        assert sorted(a["id"] for a in result["anomalies"]) == sorted(a["id"] for a in per_dimension)
        assert result["anomalies"] == svc.sort_anomalies(per_dimension)

    def test_matches_single_dimension(self, in_memory_db):
        """Test: Ergebnis je Dimension stimmt mit der Einzelabfrage überein."""
        result = svc.company_anomalies_all(DEMO_3, "employee")
        for entry in result["dimensions"][:3]:
            single = svc.company_anomalies(DEMO_3, "employee", entry["dimension"])
            assert entry["anomalies"] == single["anomalies"]
            assert entry["eligibility"] == single["eligibility"]

    def test_invalid_source_raises(self, in_memory_db):
        """Test: Ungültige Quelle → ValueError."""
        with pytest.raises(ValueError):
            svc.company_anomalies_all(DEMO_3, "bewerber")
