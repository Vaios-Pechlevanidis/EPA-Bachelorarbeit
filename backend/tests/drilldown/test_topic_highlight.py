"""
Test Suite für die Hervorhebung des Themas der gewählten Dimension (Inkrement 2,
Nachtrag): topic_for_dimension, topic_spans, /reviews mit dimension und
topic_only, dimension_topic im Vergleich.

Ausführung:
    uv run python -m pytest tests/drilldown/test_topic_highlight.py -v
"""

import pytest

from _helpers import store_rows
from services.keyword_topic_service import topic_for_dimension, topic_spans, topics_in_review

URL = "/api/analytics/company/{}/reviews"
WINDOW = {"source": "employee", "start": "2023-01-01", "end": "2023-12-31"}


class TestTopicForDimension:

    @pytest.mark.parametrize("source, dimension, topic", [
        ("employee", "image", "Image"),
        ("employee", "kommunikation", "Kommunikation"),
        ("employee", "work_life_balance", "Work-Life Balance"),
        ("candidates", "schnelle_antwort", "Schnelle Antwort"),
        ("employee", "durchschnittsbewertung", None),
    ])
    def test_mapping(self, source, dimension, topic):
        assert topic_for_dimension(source, dimension) == topic

    def test_every_dimension_has_a_topic(self):
        from services.rating_series_service import DIMENSIONS_BY_SOURCE, OVERALL_DIMENSION

        for source, dims in DIMENSIONS_BY_SOURCE.items():
            for dim in dims:
                if dim != OVERALL_DIMENSION:
                    assert topic_for_dimension(source, dim), (source, dim)

    def test_invalid_dimension_raises(self):
        with pytest.raises(ValueError):
            topic_for_dimension("employee", "schnelle_antwort")


class TestTopicSpans:

    def test_spans_point_at_keywords(self):
        text = "Der Ruf ist gut, das Image auch. RUF!"
        spans = topic_spans(text, "Image", "employee")
        assert [text[s:e] for s, e in spans] == ["Ruf", "Image", "RUF"]

    def test_word_boundaries(self):
        """Test: Schlüsselwort nur als ganzes Wort (\\b wie in topics_in_review)."""
        assert topic_spans("Anruf und Rufbereitschaft", "Image", "employee") == []

    def test_overlapping_matches_merged(self):
        text = "Gute Work-Life-Balance"
        spans = topic_spans(text, "Work-Life Balance", "employee")
        assert len(spans) == 1 and text[spans[0][0]:spans[0][1]].lower() == "work-life-balance"

    def test_empty(self):
        assert topic_spans(None, "Image", "employee") == [] and topic_spans("", "Image", "employee") == []

    def test_spans_iff_topic_in_review(self, in_memory_db):
        """Test: Eine Bewertung hat genau dann Fundstellen, wenn topics_in_review das Thema nennt."""
        fields = ["titel", "jobbeschreibung", "gut_am_arbeitgeber_finde_ich", "schlecht_am_arbeitgeber_finde_ich",
                  "verbesserungsvorschlaege"]
        for row in store_rows("employee", 3):
            has_spans = any(topic_spans(row.get(f), "Kommunikation", "employee") for f in fields)
            assert has_spans == ("Kommunikation" in topics_in_review(row, "employee"))


class TestReviewsRoute:

    def test_highlight_block_and_flags(self, api):
        body = api.get(URL.format(3), params={**WINDOW, "dimension": "kommunikation", "format": "full", "limit": 1000}).json()
        h = body["highlight"]
        assert h["topic"] == "Kommunikation" and h["topic_only"] is False
        assert h["mentions"] == sum(r["mentions_topic"] for r in body["reviews"]) > 0
        for r in body["reviews"]:
            for field, spans in r.get("highlights", {}).items():
                text = r["preview"] if field == "preview" else r["fullReview"][field]
                assert all(0 <= s < e <= len(text) for s, e in spans)
            if not r["mentions_topic"]:
                assert "highlights" in r and r["highlights"] == {}

    def test_marked_text_is_a_keyword(self, api):
        body = api.get(URL.format(3), params={**WINDOW, "dimension": "kommunikation", "format": "full", "limit": 200}).json()
        marked = {r["preview"][s:e].lower() for r in body["reviews"] for s, e in r["highlights"].get("preview", [])}
        assert marked and marked <= {"kommunikation", "information", "transparenz", "feedback", "gespräch", "austausch", "rückmeldung"}

    def test_topic_only(self, api):
        """Test: topic_only liefert nur Bewertungen mit dem Thema; total = mentions."""
        all_ = api.get(URL.format(3), params={**WINDOW, "dimension": "kommunikation"}).json()
        only = api.get(URL.format(3), params={**WINDOW, "dimension": "kommunikation", "topic_only": True, "limit": 1000}).json()
        assert only["total"] == all_["highlight"]["mentions"] == len(only["reviews"]) < all_["total"]
        assert all(r["mentions_topic"] for r in only["reviews"])

    def test_overall_dimension_has_no_topic(self, api):
        body = api.get(URL.format(3), params={**WINDOW, "dimension": "durchschnittsbewertung", "format": "full", "limit": 3}).json()
        assert body["highlight"] == {"dimension": "durchschnittsbewertung", "topic": None, "mentions": None, "topic_only": False}
        assert all("highlights" not in r for r in body["reviews"])

    @pytest.mark.parametrize("params", [
        {"dimension": "image"},                                     # ohne source
        {"source": "employee", "dimension": "schnelle_antwort"},   # Dimension der anderen Quelle
        {"source": "employee", "topic_only": True},                # topic_only ohne dimension
    ])
    def test_invalid_gives_400(self, api, params):
        res = api.get(URL.format(3), params={**params, "start": "2023-01-01"})
        assert res.status_code == 400 and isinstance(res.json()["detail"], str)

    def test_without_dimension_unchanged(self, api):
        body = api.get(URL.format(3), params={**WINDOW, "format": "full", "limit": 2}).json()
        assert "highlight" not in body and all(set(r) == {"id", "preview", "fullReview"} for r in body["reviews"])
