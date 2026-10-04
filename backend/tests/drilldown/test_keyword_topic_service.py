"""
Test Suite für services/keyword_topic_service.py (Inkrement 2): Ausgabe von
topic-overview vor und nach dem Umzug identisch, end_date wirkt,
topics_in_review folgt derselben Regel wie analyze_topic.

Ausführung:
    uv run python -m pytest tests/drilldown/test_keyword_topic_service.py -v
"""

import pathlib
from collections import Counter

import pytest

from _helpers import TOPIC_OVERVIEW_BASE, response_hash, store_rows
from services.keyword_topic_service import (
    CANDIDATE_TOPIC_DEFINITIONS,
    EMPLOYEE_TOPIC_DEFINITIONS,
    topic_definitions_for,
    topics_in_review,
)

URL = "/api/analytics/company/{}/topic-overview"
BACKEND = pathlib.Path(__file__).resolve().parents[2]


def _get(api, company_id, **params):
    res = api.get(URL.format(company_id), params={k: v for k, v in params.items() if v is not None})
    assert res.status_code == 200, res.text
    return res.json()


# ═══════════════════════════════════════════════════════════════════════════════
# 1. Umzug ohne Änderung der Ausgabe
# ═══════════════════════════════════════════════════════════════════════════════

class TestTopicOverviewUnchanged:

    @pytest.mark.parametrize("key", sorted(TOPIC_OVERVIEW_BASE, key=str))
    def test_identical_to_base_commit(self, api, key):
        """Test: topic-overview für Demo 1–3 gleicht der Ausgabe vor dem Umzug (Hash)."""
        company_id, source, start_date = key
        assert response_hash(_get(api, company_id, source=source, start_date=start_date)) == TOPIC_OVERVIEW_BASE[key]

    def test_route_uses_service(self):
        """Test: Die Route nutzt analyze_topic aus dem Dienst (kein zweites Exemplar)."""
        import routes.analytics as analytics
        import services.keyword_topic_service as kts

        assert analytics.analyze_topic is kts.analyze_topic

    def test_no_service_imports_a_route(self):
        """Test: Kein Modul unter services/ importiert aus routes/."""
        offenders = [
            p.name for p in (BACKEND / "services").glob("*.py")
            if "from routes" in p.read_text(encoding="utf-8") or "import routes" in p.read_text(encoding="utf-8")
        ]
        assert offenders == []


# ═══════════════════════════════════════════════════════════════════════════════
# 2. end_date
# ═══════════════════════════════════════════════════════════════════════════════

class TestEndDate:

    @pytest.mark.parametrize("source", ["employee", "candidates"])
    def test_end_date_limits_reviews_inclusive(self, api, source):
        """Test: total_reviews = Bewertungen bis einschließlich end_date."""
        rows = store_rows(source, 3)
        end = sorted(str(r["datum"]) for r in rows)[len(rows) // 2]
        body = _get(api, 3, source=source, end_date=end)
        assert body["total_reviews"] == sum(1 for r in rows if str(r["datum"]) <= end)
        assert body["total_reviews"] < len(rows)

    def test_start_and_end_date_together(self, api):
        """Test: start_date und end_date zusammen ergeben den Zeitraum."""
        rows = store_rows("employee", 3)
        body = _get(api, 3, source="employee", start_date="2023-01-01", end_date="2023-06-30")
        assert body["total_reviews"] == sum(1 for r in rows if "2023-01-01" <= str(r["datum"]) <= "2023-06-30")

    def test_timeline_ends_at_end_date(self, api):
        """Test: Kein Monat der Zeitleisten liegt nach end_date."""
        body = _get(api, 3, source="employee", end_date="2023-06-30")
        for topic in body["topics"]:
            assert all((p["year"], p["monthNum"]) <= (2023, 6) for p in topic["timelineData"])

    def test_invalid_end_date_gives_400(self, api):
        """Test: end_date in falschem Format → 400 {"detail": ...}."""
        res = api.get(URL.format(3), params={"end_date": "30.06.2023"})
        assert res.status_code == 400 and "end_date" in res.json()["detail"]


# ═══════════════════════════════════════════════════════════════════════════════
# 3. topics_in_review
# ═══════════════════════════════════════════════════════════════════════════════

class TestTopicsInReview:

    @pytest.mark.parametrize("company_id", [1, 2, 3])
    @pytest.mark.parametrize("source", ["employee", "candidates"])
    def test_counts_match_topic_overview(self, api, company_id, source):
        """Test: Nennungen je Thema wie frequency in topic-overview (gleiche Regel)."""
        body = _get(api, company_id, source=source)
        expected = {t["topic"]: t["frequency"] for t in body["topics"]}
        counted = Counter(t for r in store_rows(source, company_id) for t in topics_in_review(r, source))
        assert dict(counted) == expected

    def test_definitions_per_source(self):
        """Test: Definitionen je Quelle; ohne Quelle beide zusammen."""
        assert topic_definitions_for("employee") is EMPLOYEE_TOPIC_DEFINITIONS
        assert topic_definitions_for("candidates") is CANDIDATE_TOPIC_DEFINITIONS
        assert len(EMPLOYEE_TOPIC_DEFINITIONS) == 13 and len(CANDIDATE_TOPIC_DEFINITIONS) == 10
        assert set(topic_definitions_for(None)) == set(EMPLOYEE_TOPIC_DEFINITIONS) | set(CANDIDATE_TOPIC_DEFINITIONS)

    def test_pure_function_examples(self):
        """Test: Schlüsselwort in einem Textfeld, Groß-/Kleinschreibung egal, Reihenfolge der Definitionen."""
        row = {"gut_am_arbeitgeber_finde_ich": "Das GEHALT ist fair.", "schlecht_am_arbeitgeber_finde_ich": "Zu viele Überstunden."}
        assert topics_in_review(row, "employee") == ["Work-Life Balance", "Gehalt & Sozialleistungen"]

    def test_no_text_no_topic(self):
        """Test: Ohne Text keine Themen; Nicht-Text-Werte werden ignoriert."""
        assert topics_in_review({"titel": None, "gut_am_arbeitgeber_finde_ich": 5}, "employee") == []

    def test_english_text_is_not_matched(self):
        """Test (Grenze E10): Englische Texte werden von den deutschen Schlüsselwörtern kaum erfasst."""
        row = {"gut_am_arbeitgeber_finde_ich": "Great salary, flexible working hours and a supportive manager."}
        assert topics_in_review(row, "employee") == []
