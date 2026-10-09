"""
NFA-07 (Inkrement 6, 2026-10-09): Beispielzitate der Topics (``example``,
``typicalStatements``, ``reviewDetails[].preview``; Topic-Tabelle, Topic-Details,
PDF) stammen nie aus ``jobbeschreibung`` oder ``stellenbeschreibung``. Die
Topic-Berechnung (Häufigkeit, Bewertung, Stimmung) bleibt unverändert: Eine
Nennung nur in diesen Feldern zählt weiter mit. Konstruierte Bewertungen.

Ausführen:
    cd backend
    uv run python -m pytest tests/test_topic_quotes_nfa07.py -q -p no:cacheprovider
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from services.keyword_topic_service import QUOTE_EXCLUDED_FIELDS, analyze_topic  # noqa: E402

KEYWORDS = [r"\büberstunden\b"]
RATING_FIELDS = ["sternebewertung_work_life_balance"]


def review(i, **fields):
    row = {"id": i, "datum": "2024-03-15T00:00:00", "durchschnittsbewertung": 3.0,
           "sternebewertung_work_life_balance": 2.0, "gut_am_arbeitgeber_finde_ich": "", "titel": "Konstruiert"}
    row.update(fields)
    return row


JOB_TEXT = "Konstruierte Tätigkeit mit vielen Überstunden in der Abteilung Beispiel"
POSITION_TEXT = "Konstruierte Stelle, Überstunden werden in der Ausschreibung erwähnt"
FREE_TEXT = "Die Überstunden werden bei uns sauber erfasst und ausgeglichen"


def _quotes(result):
    texts = [result["example"]] + list(result["typicalStatements"])
    texts += [d.get("preview") or "" for d in result["reviewDetails"]]
    return texts


def test_excluded_fields_are_the_two_description_fields():
    assert set(QUOTE_EXCLUDED_FIELDS) == {"jobbeschreibung", "stellenbeschreibung"}


def test_quotes_never_from_job_or_position_description():
    rows = [
        review(1, jobbeschreibung=JOB_TEXT),
        review(2, stellenbeschreibung=POSITION_TEXT),
        review(3, schlecht_am_arbeitgeber_finde_ich=FREE_TEXT),
    ]
    result = analyze_topic("Work-Life Balance", KEYWORDS, RATING_FIELDS, rows)
    for text in _quotes(result):
        assert "Tätigkeit" not in text and "Ausschreibung" not in text, text
    assert result["typicalStatements"] == [FREE_TEXT]
    assert result["example"].startswith("Die Überstunden")


def test_topic_calculation_unchanged_mentions_still_count():
    """Nennungen nur in den ausgeschlossenen Feldern zählen für Häufigkeit und Bewertung."""
    rows = [review(1, jobbeschreibung=JOB_TEXT), review(2, stellenbeschreibung=POSITION_TEXT)]
    result = analyze_topic("Work-Life Balance", KEYWORDS, RATING_FIELDS, rows)
    assert result["frequency"] == 2 and result["avgRating"] == 2.0
    assert result["typicalStatements"] == ["Keine spezifischen Aussagen zu Work-Life Balance gefunden"]
    for text in _quotes(result):
        assert "Tätigkeit" not in text and "Ausschreibung" not in text


def test_other_field_of_same_review_still_quoted():
    rows = [review(1, jobbeschreibung=JOB_TEXT, verbesserungsvorschlaege=FREE_TEXT)]
    result = analyze_topic("Work-Life Balance", KEYWORDS, RATING_FIELDS, rows)
    assert result["typicalStatements"] == [FREE_TEXT] and result["frequency"] == 1
