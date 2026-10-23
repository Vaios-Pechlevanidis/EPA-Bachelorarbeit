"""
Tests für die Dimension als globalen Filter der Detailseite (2026-10-23, E34):
services/dimension_scope.py (reine Regeln für Bewertungen und Belege) und
/reviews mit dimension_only.

Ausführung:
    uv run python -m pytest tests/drilldown/test_dimension_scope.py -v
"""

import pytest

from services.dimension_scope import (
    NO_EVIDENCE_IN_DIMENSION,
    evidence_dimension_match,
    mean_rating,
    review_dimension_info,
    scope_evidence,
    single_dimension_topic,
    topic_title_terms,
)

URL = "/api/analytics/company/{}/reviews"
WINDOW = {"source": "employee", "start": "2023-01-01", "end": "2023-12-31"}
GEHALT = "Gehalt & Sozialleistungen"


def _employee(**fields):
    row = {"id": 1, "titel": "Solide", "gut_am_arbeitgeber_finde_ich": "Nettes Team.",
           "schlecht_am_arbeitgeber_finde_ich": "", "verbesserungsvorschlaege": "",
           "sternebewertung_gehalt_sozialleistungen": 2.0, "gehalt_sozialleistungen": "-"}
    row.update(fields)
    return row


class TestSingleDimensionTopic:

    def test_topic_of_single_dimension(self):
        assert single_dimension_topic("employee", "gehalt_sozialleistungen") == GEHALT

    @pytest.mark.parametrize("dimension", [None, "durchschnittsbewertung", "gibtsnicht", "schnelle_antwort"])
    def test_rejects_missing_overall_or_invalid(self, dimension):
        with pytest.raises(ValueError):
            single_dimension_topic("employee", dimension)


class TestReviewDimensionInfo:

    def test_comment_counts(self):
        info = review_dimension_info(_employee(gehalt_sozialleistungen="Zu wenig <br/>für die Branche."), "employee", "gehalt_sozialleistungen")
        assert info == {"key": "gehalt_sozialleistungen", "rating": 2.0, "comment": "Zu wenig \nfür die Branche.",
                        "mentions_topic": False, "in_dimension": True}

    def test_topic_in_free_text_counts(self):
        info = review_dimension_info(_employee(schlecht_am_arbeitgeber_finde_ich="Das Gehalt ist mies."), "employee", "gehalt_sozialleistungen")
        assert info["comment"] is None and info["mentions_topic"] and info["in_dimension"]

    def test_stars_alone_do_not_count(self):
        """Test: Sterne ohne Kommentar und ohne Thema gehören nicht zur Dimension; Platzhalter "-" ist kein Kommentar."""
        info = review_dimension_info(_employee(), "employee", "gehalt_sozialleistungen")
        assert info["rating"] == 2.0 and info["comment"] is None and not info["in_dimension"]

    def test_candidates_have_no_category_comment(self):
        row = {"id": 2, "titel": "Bewerbung", "stellenbeschreibung": "Schnelle Antwort nach zwei Tagen.",
               "verbesserungsvorschlaege": "", "sternebewertung_schnelle_antwort": 4.0, "schnelle_antwort": "Text"}
        info = review_dimension_info(row, "candidates", "schnelle_antwort")
        assert info["comment"] is None and info["mentions_topic"] and info["rating"] == 4.0

    def test_mean_rating(self):
        assert mean_rating([{"rating": 2}, {"rating": "3.5"}, {"rating": None}, {"rating": "x"}]) == 2.75
        assert mean_rating([{"rating": None}]) is None


class TestEvidenceDimensionMatch:

    def test_plain_terms_from_patterns(self):
        terms = topic_title_terms(GEHALT, "employee")
        assert "gehalt" in terms and "lohn" in terms and all(t.islower() for t in terms)

    def test_compound_title_word(self):
        """Test: Wortanfang ab sechs Zeichen (Regel der strengen Auswahl): Gehaltserhöhung passt zu gehalt."""
        match = evidence_dimension_match({"title": "Gehaltserhöhung bei Demo 3 beschlossen", "source_type": "news"}, GEHALT, "employee")
        assert match["terms"] == ["gehaltserhöhung"] and match["category"] == "Vergütung und Sozialleistungen"

    def test_short_keyword_only_as_whole_word(self):
        assert evidence_dimension_match({"title": "Es lohnt sich bei Demo 3", "source_type": "news"}, GEHALT, "employee") is None
        assert evidence_dimension_match({"title": "Lohn steigt bei Demo 3", "source_type": "news"}, GEHALT, "employee")["terms"] == ["lohn"]

    def test_category_without_keyword(self):
        match = evidence_dimension_match({"title": "Warnstreik bei Demo 3", "source_type": "news"}, GEHALT, "employee")
        assert match == {"terms": [], "category": "Tarifverhandlung und Streik"}

    def test_no_relation(self):
        assert evidence_dimension_match({"title": "Demo 3 gewinnt das Spiel", "source_type": "news"}, GEHALT, "employee") is None
        assert evidence_dimension_match({"title": "", "source_type": "news"}, GEHALT, "employee") is None
        assert evidence_dimension_match({"title": "Gehalt", "source_type": "news"}, None, "employee") is None

    def test_non_employer_category_does_not_count(self):
        """Test: Ereignisart ohne Arbeitgeberbezug (Börse) zählt nicht, auch wenn das Thema ihr zugeordnet wäre."""
        assert evidence_dimension_match({"title": "Demo 3 Aktie mit Kursziel", "source_type": "news"}, GEHALT, "employee") is None

    def test_global_events_excluded(self):
        assert evidence_dimension_match({"title": "Gehalt und Inflation", "source_type": "global"}, GEHALT, "employee") is None

    def test_scope_evidence(self):
        evidence = {"items": [
            {"id": "a", "title": "Gehaltserhöhung bei Demo 3", "source_type": "news"},
            {"id": "b", "title": "Demo 3 gewinnt das Spiel", "source_type": "news"},
            {"id": "c", "title": "Inflationsschub", "source_type": "global"},
        ], "total": 3, "counts": {"news": 2, "adhoc": 0, "global": 1}, "coverage": True, "reason": None}
        scoped = scope_evidence(evidence, "employee", "gehalt_sozialleistungen")
        assert [i["id"] for i in scoped["items"]] == ["a"] and scoped["items"][0]["dimension_match"]["terms"] == ["gehaltserhöhung"]
        assert scoped["total"] == 1 and scoped["counts"] == {"news": 1, "adhoc": 0, "global": 0} and scoped["coverage"] is True
        assert scoped["scope"]["n_all"] == 3 and scoped["scope"]["n_dimension"] == 1 and scoped["scope"]["topic"] == GEHALT
        assert "dimension_match" not in evidence["items"][0], "Eingabe bleibt unverändert"

    def test_scope_evidence_empty_gets_reason(self):
        evidence = {"items": [{"id": "b", "title": "Demo 3 gewinnt das Spiel", "source_type": "news"}], "total": 1,
                    "counts": {"news": 1, "adhoc": 0, "global": 0}, "coverage": True, "reason": None}
        scoped = scope_evidence(evidence, "employee", "gehalt_sozialleistungen")
        assert scoped["items"] == [] and scoped["coverage"] is False and scoped["reason"] == NO_EVIDENCE_IN_DIMENSION

    def test_scope_evidence_rejects_overall(self):
        with pytest.raises(ValueError):
            scope_evidence({"items": []}, "employee", "durchschnittsbewertung")


class TestReviewsRoute:

    def test_dimension_block_per_review(self, api):
        body = api.get(URL.format(3), params={**WINDOW, "dimension": "gehalt_sozialleistungen", "format": "full", "limit": 50}).json()
        assert "dimension_only" not in body["highlight"], "ohne dimension_only unverändert"
        for r in body["reviews"]:
            d = r["dimension"]
            assert set(d) == {"key", "rating", "comment", "mentions_topic", "in_dimension"} and d["key"] == "gehalt_sozialleistungen"
            assert d["rating"] == r["fullReview"]["ratings"]["gehalt_sozialleistungen"]
            assert d["in_dimension"] == (d["comment"] is not None or d["mentions_topic"])
            for s, e in r.get("highlights", {}).get("comment", []):
                assert 0 <= s < e <= len(d["comment"])

    def test_dimension_only_filters_and_counts(self, api):
        all_ = api.get(URL.format(3), params={**WINDOW, "dimension": "gehalt_sozialleistungen", "limit": 1}).json()
        only = api.get(URL.format(3), params={**WINDOW, "dimension": "gehalt_sozialleistungen", "dimension_only": True,
                                              "format": "full", "limit": 1000}).json()
        h = only["highlight"]
        assert h["dimension_only"] is True and h["n_all"] == all_["total"] and h["n_dimension"] == only["total"] == len(only["reviews"])
        assert 0 < h["n_dimension"] <= h["n_all"] and h["note"]
        assert all(r["dimension"]["in_dimension"] for r in only["reviews"])
        ratings = [float(r["dimension"]["rating"]) for r in only["reviews"] if r["dimension"]["rating"] is not None]
        assert h["dimension_mean"] == round(sum(ratings) / len(ratings), 2)
        assert sum(c["n"] for c in only["topic_summary"]["counts"]) <= sum(len(r["topics"]) for r in only["reviews"])

    def test_candidates_only_by_topic(self, api):
        """Test: Bewerbende haben keine Kategorie-Kommentare; zur Dimension gehört nur, wer das Thema nennt."""
        params = {"source": "candidates", "start": "2023-01-01", "end": "2024-12-31", "dimension": "schnelle_antwort"}
        all_ = api.get(URL.format(3), params=params).json()
        only = api.get(URL.format(3), params={**params, "dimension_only": True, "limit": 1000}).json()
        assert only["total"] == all_["highlight"]["mentions"] and all(r["mentions_topic"] for r in only["reviews"])

    def test_without_single_dimension_no_block(self, api):
        body = api.get(URL.format(3), params={**WINDOW, "dimension": "durchschnittsbewertung", "format": "full", "limit": 2}).json()
        assert all("dimension" not in r for r in body["reviews"])

    @pytest.mark.parametrize("params", [
        {"source": "employee", "dimension_only": True},                                        # ohne dimension
        {"source": "employee", "dimension": "durchschnittsbewertung", "dimension_only": True},  # Gesamtbewertung
    ])
    def test_invalid_gives_400(self, api, params):
        res = api.get(URL.format(3), params={**params, "start": "2023-01-01"})
        assert res.status_code == 400 and isinstance(res.json()["detail"], str)
