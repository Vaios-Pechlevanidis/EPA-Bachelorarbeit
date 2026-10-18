"""
Test Suite für Themen, Themenfilter und Sortierung der Liste „Bewertungen des
Zeitraums“ (Nachtrag 2026-10-18): GET /reviews mit ``topics`` je Bewertung,
``topic_summary``, ``topic=<Thema>`` und ``order=asc|desc``; ``sort_by_date``.

Ausführung:
    uv run python -m pytest tests/drilldown/test_review_topics.py -v
"""

from collections import Counter

import pytest

from _helpers import store_rows
from services.keyword_topic_service import EXPLANATION_TOPIC_TEXT_FIELDS, EMPLOYEE_TOPIC_DEFINITIONS, topics_in_review
from services.review_service import sort_by_date, sort_newest_first

URL = "/api/analytics/company/{}/reviews"
DEMO_3 = 3
WINDOW = {"source": "employee", "start": "2023-01-01", "end": "2023-12-31"}


def _get(api, **params):
    res = api.get(URL.format(DEMO_3), params=params)
    assert res.status_code == 200, res.text
    return res.json()


def _window_rows():
    return [r for r in store_rows("employee", DEMO_3) if "2023-01-01" <= str(r.get("datum"))[:10] <= "2023-12-31"]


def _expected_topics(row):
    return topics_in_review(row, "employee", EXPLANATION_TOPIC_TEXT_FIELDS)


# ═══════════════════════════════════════════════════════════════════════════════
# 1. Themen je Bewertung und Zählung
# ═══════════════════════════════════════════════════════════════════════════════

class TestTopicsPerReview:

    def test_topics_follow_topic_rule(self, api):
        """Test: topics je Bewertung = topics_in_review mit den Feldern des Vergleichs."""
        body = _get(api, **WINDOW, format="full", limit=1000)
        by_id = {r["id"]: r for r in store_rows("employee", DEMO_3)}
        assert body["reviews"]
        for item in body["reviews"]:
            assert item["topics"] == _expected_topics(by_id[item["id"]])

    def test_topics_also_in_short_format(self, api):
        body = _get(api, **WINDOW, limit=3)
        assert all(isinstance(r["topics"], list) for r in body["reviews"])

    def test_summary_counts_all_reviews_of_window(self, api):
        """Test: counts zählt jedes Thema über alle Bewertungen des Zeitraums, in der
        Reihenfolge der Definitionen, nur Themen mit n > 0; without_topic den Rest."""
        rows = _window_rows()
        expected = Counter(t for r in rows for t in _expected_topics(r))
        summary = _get(api, **WINDOW, limit=1)["topic_summary"]
        assert summary["counts"] == [{"topic": t, "n": expected[t]} for t in EMPLOYEE_TOPIC_DEFINITIONS if expected[t]]
        assert summary["without_topic"] == sum(1 for r in rows if not _expected_topics(r))
        assert summary["filter"] is None and summary["marked"] is None

    def test_summary_independent_of_page(self, api):
        a = _get(api, **WINDOW, limit=2)["topic_summary"]
        b = _get(api, **WINDOW, limit=2, offset=10)["topic_summary"]
        assert a == b


# ═══════════════════════════════════════════════════════════════════════════════
# 2. Themenfilter
# ═══════════════════════════════════════════════════════════════════════════════

class TestTopicFilter:

    @pytest.fixture(scope="class")
    def topic(self, api):
        counts = _get(api, **WINDOW, limit=1)["topic_summary"]["counts"]
        return max(counts, key=lambda c: c["n"])

    def test_only_reviews_with_topic(self, api, topic):
        body = _get(api, **WINDOW, topic=topic["topic"], format="full", limit=1000)
        assert body["total"] == topic["n"] == len(body["reviews"])
        assert all(topic["topic"] in r["topics"] for r in body["reviews"])

    def test_summary_before_filter(self, api, topic):
        """Test: Die Zählung bleibt mit Filter gleich; filter und marked nennen das Thema."""
        unfiltered = _get(api, **WINDOW, limit=1)["topic_summary"]
        summary = _get(api, **WINDOW, topic=topic["topic"], limit=1)["topic_summary"]
        assert summary["counts"] == unfiltered["counts"]
        assert summary["filter"] == summary["marked"] == topic["topic"]

    def test_filtered_topic_is_marked(self, api, topic):
        """Test: Ohne Dimension markiert der Filter die Fundstellen seines Themas."""
        body = _get(api, **WINDOW, topic=topic["topic"], format="full", limit=50)
        assert all("highlights" in r for r in body["reviews"])
        assert any(r["highlights"] for r in body["reviews"])

    def test_filter_with_dimension_marks_filter_topic(self, api):
        """Test: Mit Dimension Kommunikation und Filter Image: markiert wird Image,
        mentions_topic und highlight.mentions bleiben beim Thema der Dimension."""
        plain = _get(api, **WINDOW, dimension="kommunikation", limit=1)
        body = _get(api, **WINDOW, dimension="kommunikation", topic="Image", format="full", limit=1000)
        assert body["topic_summary"]["marked"] == "Image"
        assert body["highlight"]["mentions"] == plain["highlight"]["mentions"]
        assert all(r["mentions_topic"] == ("Kommunikation" in r["topics"]) for r in body["reviews"])
        marked = {r["preview"][s:e].lower() for r in body["reviews"] for s, e in r["highlights"].get("preview", [])}
        assert "kommunikation" not in marked

    def test_topic_only_reports_dimension_topic_as_filter(self, api):
        summary = _get(api, **WINDOW, dimension="kommunikation", topic_only=True, limit=1)["topic_summary"]
        assert summary["filter"] == summary["marked"] == "Kommunikation"

    def test_topic_alone_switches_to_range_mode(self, api):
        """Test: topic ohne start/end liefert die neue Antwort (alle Bewertungen mit dem Thema)."""
        body = _get(api, source="employee", topic="Image", limit=5)
        assert "topic_summary" in body and all("Image" in r["topics"] for r in body["reviews"])

    @pytest.mark.parametrize("params", [
        {"source": "employee", "topic": "Gibt es nicht"},
        {"source": "employee", "topic": "Schnelle Antwort"},                                  # Thema der Bewerbenden
        {"source": "employee", "dimension": "kommunikation", "topic_only": True, "topic": "Image"},
    ])
    def test_invalid_gives_400(self, api, params):
        res = api.get(URL.format(DEMO_3), params={**params, "start": "2023-01-01"})
        assert res.status_code == 400 and isinstance(res.json()["detail"], str)


# ═══════════════════════════════════════════════════════════════════════════════
# 3. Sortierung nach Datum
# ═══════════════════════════════════════════════════════════════════════════════

class TestOrder:

    def test_default_is_newest_first(self, api):
        body = _get(api, **WINDOW, limit=1000)
        days = [r["date"] for r in body["reviews"]]
        assert body["order"] == "desc" and days == sorted(days, reverse=True)

    def test_asc_is_oldest_first(self, api):
        body = _get(api, **WINDOW, order="asc", limit=1000)
        days = [r["date"] for r in body["reviews"]]
        assert body["order"] == "asc" and days == sorted(days)

    def test_asc_reverses_desc(self, api):
        """Test: Datum und id als Schlüssel; aufsteigend ist genau die Umkehrung."""
        desc = [r["id"] for r in _get(api, **WINDOW, limit=1000)["reviews"]]
        asc = [r["id"] for r in _get(api, **WINDOW, order="asc", limit=1000)["reviews"]]
        assert asc == desc[::-1]

    def test_pages_in_asc_order(self, api):
        full = [r["id"] for r in _get(api, **WINDOW, order="asc", limit=1000)["reviews"]]
        pages = [r["id"] for off in range(0, 30, 10) for r in _get(api, **WINDOW, order="asc", limit=10, offset=off)["reviews"]]
        assert pages == full[:30]

    def test_order_with_topic_filter(self, api):
        body = _get(api, **WINDOW, topic="Image", order="asc", limit=1000)
        days = [r["date"] for r in body["reviews"]]
        assert days == sorted(days) and all("Image" in r["topics"] for r in body["reviews"])

    def test_invalid_order_rejected(self, api):
        res = api.get(URL.format(DEMO_3), params={**WINDOW, "order": "alt"})
        assert res.status_code == 422


class TestCombinedPatterns:

    @pytest.mark.parametrize("source", ["employee", "candidates"])
    def test_same_topics_as_single_patterns(self, in_memory_db, source):
        """Test: Die zusammengefassten Muster je Thema finden genau die Themen der
        Einzelmuster (Regel vor 2026-10-18), für alle Bewertungen des Demo-Stores."""
        from services.keyword_topic_service import _compiled_topics

        def single(row):
            texts = [row[f].lower() for f in EXPLANATION_TOPIC_TEXT_FIELDS if isinstance(row.get(f), str) and row[f]]
            return [name for name, ps in _compiled_topics(source) if any(p.search(t) for t in texts for p in ps)]

        rows = [r for company in (1, 2, 3) for r in store_rows(source, company)]
        assert rows
        assert all(topics_in_review(r, source, EXPLANATION_TOPIC_TEXT_FIELDS) == single(r) for r in rows)


class TestSortByDate:

    ROWS = [
        {"id": 1, "datum": "2023-02-01"},
        {"id": 2, "datum": None},
        {"id": 3, "datum": "2023-01-01"},
        {"id": 4, "datum": "2023-02-01"},
    ]

    def test_desc(self):
        assert [r["id"] for r in sort_by_date(self.ROWS)] == [4, 1, 3, 2]
        assert sort_by_date(self.ROWS) == sort_newest_first(self.ROWS)

    def test_asc_rows_without_date_last(self):
        assert [r["id"] for r in sort_by_date(self.ROWS, newest_first=False)] == [3, 1, 4, 2]
