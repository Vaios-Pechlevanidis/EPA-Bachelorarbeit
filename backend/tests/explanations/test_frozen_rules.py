"""
Vertragstest (Inkrement 5, B1): Die vom Autor am 2026-10-08 bestätigten Schwellen,
Stufenregeln und Ereignisarten (D1, D2) sind für die Auswertung festgeschrieben. Ändert
sich ein Wert, schlägt dieser Test an; die Änderung und ihr Grund gehören dann in
docs/entscheidungen.md.

Ausführung:
    cd backend
    uv run python -m pytest tests/explanations/test_frozen_rules.py -q -p no:cacheprovider
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))

import services.explanation_ranking as er  # noqa: E402
import services.review_terms as rt  # noqa: E402
from services.event_categories import NON_EMPLOYER_ID, load_event_categories  # noqa: E402

FROZEN_TERMS = {
    "MIN_TERM_LENGTH": 3, "TERM_MIN_REVIEWS_AFTER": 3, "TERM_MIN_SHARE_AFTER": 0.03, "TERM_MIN_SHARE_RATIO": 2.0,
    "TERM_MIN_REVIEWS_PER_WINDOW": 10, "TERM_MAX_COUNT": 50, "TERM_PREFIX_MIN_LENGTH": 6, "COMPANY_PREFIX_MIN_LENGTH": 5,
}
FROZEN_RANKING = {
    "TERM_MATCH_PER_TERM": 0.5, "TERM_MATCH_STRONG": 1.0, "TERM_STRONG_MIN_AFTER": 5, "TERM_STRONG_MIN_RATIO": 3.0,
    "TERM_STRONG_MIN_SHIFT": 0.05, "TOPIC_SHIFT_MIN_PP": 5.0, "CATEGORY_MATCH_WITH_SHIFT": 1.0, "CATEGORY_MATCH_ONLY": 0.5,
    "TIME_NEAR": 1.0, "TIME_AFTER_FACTOR": 0.5, "TOPIC_STRONG": 1.0, "TOPIC_WEAK": 0.5, "TIME_MID": 0.5, "TIME_MIN": 0.3,
    "BUNDLE_MAX_DAYS": 3, "BUNDLE_TITLE_SIMILARITY": 0.5, "MAX_EXPLANATIONS": 5,
}
FROZEN_CATEGORIES = [
    "personalabbau", "fuehrungswechsel", "uebernahme_verkauf", "tarif_streik", "standort", "verguetung", "arbeitsmodell",
    "rechtsstreit_compliance", "arbeitgeberauszeichnung", "krise_geschaeftslage", "einstellung_wachstum", "unternehmenskultur",
    NON_EMPLOYER_ID,
]
FROZEN_TOPICS = {
    "personalabbau": ["Arbeitsatmosphäre", "Kommunikation", "Karriere & Weiterbildung", "Image"],
    "fuehrungswechsel": ["Vorgesetztenverhalten", "Kommunikation"],
    "uebernahme_verkauf": ["Image", "Kommunikation", "Arbeitsatmosphäre"],
    "tarif_streik": ["Gehalt & Sozialleistungen", "Arbeitsbedingungen", "Kommunikation"],
    "standort": ["Arbeitsbedingungen", "Arbeitsatmosphäre"],
    "verguetung": ["Gehalt & Sozialleistungen"],
    "arbeitsmodell": ["Work-Life Balance", "Arbeitsbedingungen"],
    "rechtsstreit_compliance": ["Image", "Umwelt- & Sozialbewusstsein", "Vorgesetztenverhalten", "Gleichberechtigung"],
    "arbeitgeberauszeichnung": ["Image"],
    "krise_geschaeftslage": ["Arbeitsatmosphäre", "Image", "Karriere & Weiterbildung", "Kommunikation"],
    "einstellung_wachstum": ["Karriere & Weiterbildung", "Image", "Interessante Aufgaben", "Erwartbarkeit des Prozesses", "Schnelle Antwort"],
    "unternehmenskultur": ["Gleichberechtigung", "Arbeitsatmosphäre", "Vorgesetztenverhalten", "Work-Life Balance", "Wertschätzende Behandlung"],
    NON_EMPLOYER_ID: [],
}


def test_term_thresholds_frozen():
    assert {name: getattr(rt, name) for name in FROZEN_TERMS} == FROZEN_TERMS


def test_ranking_thresholds_frozen():
    assert {name: getattr(er, name) for name in FROZEN_RANKING} == FROZEN_RANKING
    assert er.STAGES == ("hoch", "mittel", "niedrig", "keine")
    assert er.SOURCE_TYPE_ORDER == {"adhoc": 0, "news": 1}


def test_stage_rules_frozen():
    cases = [(1.0, 1.0, "hoch"), (1.0, 0.5, "mittel"), (0.5, 1.0, "mittel"), (1.0, 0.33, "niedrig"), (0.5, 0.33, "niedrig"),
             (0.5, 0.17, "keine"), (0.0, 1.0, "keine")]
    assert [er.stage_for(t, z) for t, z, _ in cases] == [s for _, _, s in cases]
    assert er.stage_for(1.0, 1.0, employer_related=False) == "mittel"


def test_event_categories_frozen():
    cats = load_event_categories(use_cache=False)
    assert [c["id"] for c in cats] == FROZEN_CATEGORIES
    assert all(c["confirmed"] is True for c in cats)
    assert {c["id"]: c["topics"] for c in cats} == FROZEN_TOPICS
    assert [c["id"] for c in cats if not c["employer_related"]] == [NON_EMPLOYER_ID]
