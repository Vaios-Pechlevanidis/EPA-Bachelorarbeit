"""
Tests der Korrekturen vom 2026-10-13 an den Erklärungsansätzen (E23, Nachtrag
2026-10-13): Schwellen und Stufenregeln bleiben unverändert, geändert sind
Schlüsselwort ``verdi`` (ganzes Wort), Kategorie-Kommentare als Text, Grenzen der
Vergleichsfenster, Erkennung des Unternehmens im Titel und die Bezeichnung der
EQS-Mitteilungen. Konstruierte Daten, ohne DB und ohne Netz.

Ausführen:
    cd backend
    uv run python -m pytest tests/explanations/test_corrections_2026_10_13.py -q -p no:cacheprovider
"""

import os
import sys

import pytest

BACKEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
sys.path.insert(0, BACKEND_DIR)
sys.path.insert(0, os.path.join(BACKEND_DIR, "scripts"))

import fetch_context  # noqa: E402
import services.event_categories as ec  # noqa: E402
import services.explanation_ranking as er  # noqa: E402
import services.review_terms as rt  # noqa: E402
from services.keyword_topic_service import EXPLANATION_TOPIC_TEXT_FIELDS, TOPIC_TEXT_FIELDS, topics_in_review  # noqa: E402
from services.review_service import CATEGORY_TEXT_FIELDS, has_text_content, review_preview, review_text  # noqa: E402


# ── Schlüsselwort "verdi" als ganzes Wort (E22) ─────────────────────────────

@pytest.fixture(scope="module")
def categories():
    return ec.load_event_categories(use_cache=False)


@pytest.mark.parametrize("title", ["Musterfirma verdient mehr als erwartet", "So viel verdienen Beschäftigte",
                                   "Verdichtung des Netzes geplant"])
def test_verdi_no_longer_matches_other_words(categories, title):
    primary = ec.classify_title(title, categories)["primary"]
    assert primary is None or primary["id"] != "tarif_streik"


@pytest.mark.parametrize("title", ["Verdi ruft zum Warnstreik auf", "Verdi-Streik bei Musterfirma", "Gespräche mit ver.di gescheitert"])
def test_union_still_matches(categories, title):
    assert ec.classify_title(title, categories)["primary"]["id"] == "tarif_streik"


def test_whole_word_marker_in_pattern():
    pattern = ec.compile_keywords(["abc$", "streik"])
    assert pattern.search("abc") and pattern.search("die abc kommt") and not pattern.search("abcde")
    assert pattern.search("streikwelle")          # ohne $ weiter als Wortanfang


def test_repository_file_uses_whole_word_verdi(categories):
    tarif = next(c for c in categories if c["id"] == "tarif_streik")
    assert "verdi$" in tarif["keywords_de"] and "verdi" not in tarif["keywords_de"]


# ── Kategorie-Kommentare als Text (E10, E11, E21) ───────────────────────────

ROW = {
    "gut_am_arbeitgeber_finde_ich": None, "schlecht_am_arbeitgeber_finde_ich": "-", "verbesserungsvorschlaege": "",
    "kommunikation": "Die Kommunikation der Geschäftsführung ist schlecht.", "image": "-", "titel": "Solide",
}


def test_placeholders_are_not_text():
    assert not has_text_content("-") and not has_text_content(" . ") and not has_text_content("4")
    assert has_text_content("ok") and has_text_content("Gut")


def test_review_text_includes_category_comments_and_skips_placeholders():
    text = review_text(ROW, "employee")
    assert text == "Die Kommunikation der Geschäftsführung ist schlecht."
    assert review_preview(ROW, "employee").startswith("Die Kommunikation")
    assert review_text({k: v for k, v in ROW.items() if k not in CATEGORY_TEXT_FIELDS}, "employee") == ""


def test_terms_read_category_comments():
    assert "geschäftsführung" in rt.review_terms(ROW, source="employee")


def test_explanation_topics_read_category_comments_overview_unchanged():
    assert "Kommunikation" in topics_in_review(ROW, "employee", EXPLANATION_TOPIC_TEXT_FIELDS)
    assert "Kommunikation" not in topics_in_review(ROW, "employee")      # Themenübersicht aus Zyklus 1 unverändert
    assert EXPLANATION_TOPIC_TEXT_FIELDS == TOPIC_TEXT_FIELDS + CATEGORY_TEXT_FIELDS


# ── Grenzen der Vergleichsfenster (E18) ─────────────────────────────────────

def test_company_anchors_bounded_by_evaluated_months(monkeypatch):
    series = [{"period": "2019-01", "evaluated": False}, {"period": "2019-02", "evaluated": True},
              {"period": "2019-03", "evaluated": False}, {"period": "2019-04", "evaluated": True},
              {"period": "2019-05", "evaluated": False}]
    monkeypatch.setattr(fetch_context, "company_anomalies", lambda cid, source, dimension: {
        "eligibility": {"eligible": True}, "anomalies": [], "outlier_months": [], "series": series})
    anchors = fetch_context.company_anchors(7)
    assert (anchors["series_from"], anchors["series_to"]) == ("2019-02", "2019-04")
    assert anchors["evaluated_months"] == ["2019-02", "2019-04"]


# ── Unternehmen im Titel (ohne Einfluss auf die Stufe) ──────────────────────

@pytest.mark.parametrize("name, term, title, expected", [
    ("E.ON SE", "E.ON", "E.ON kündigt Stellenabbau an", True),
    ("E.ON SE", "E.ON", "Eon baut ab", True),
    ("E.ON SE", "E.ON", "RWE baut ab", False),
    ("1&1 AG", "1&1", "1&1 mit neuem Netz", True),
    ("1&1 AG", "1&1", "Drillisch übernimmt", False),
])
def test_company_in_title(name, term, title, expected):
    assert er.company_in_title(title, rt.company_terms(name, term)) is expected


# ── Vermerk der Korrekturen in den Regeln ───────────────────────────────────

def test_rules_name_the_corrections_and_keep_version():
    rules = er.rules()
    assert rules["version"] == 2
    # fünf Korrekturen vom 2026-10-13, dazu die Stoppwörter vom 2026-10-23 (E35)
    assert len(rules["corrections"]) == 6 and all(c.startswith(("2026-10-13", "2026-10-23")) for c in rules["corrections"])
