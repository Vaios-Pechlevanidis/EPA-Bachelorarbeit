"""
Tests für den Wortbezug im Text der Meldung (E35, 2026-10-23, services/explanation_ranking.py):
Begriffe im gespeicherten Text zählen für ``term_match`` mit Fundort ``in``; Titeltreffer
zuerst; strenge Richtung des Wortanfangs gilt auch im Text; Ereignisart und Arbeitgeberbezug
bleiben beim Titel; Bündel, Einträge, ``item_scores`` und Textbausteine nennen den Fundort;
ohne Text bleibt alles wie bisher; Regeln nennen die Fassung. Alle Texte sind konstruiert.

Ausführung:
    cd backend
    uv run python -m pytest tests/explanations/test_text_match.py -q -p no:cacheprovider
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))

import services.evidence_service as ev  # noqa: E402
import services.evidence_sources as src  # noqa: E402
import services.explanation_ranking as er  # noqa: E402
from services.event_categories import load_event_categories  # noqa: E402

CATS = load_event_categories(use_cache=False)
WINDOW = ev.window_for_change("2023-04", "2023-03", 0, 3, 1)      # Fenster 2023-01 bis 2023-05, Übergang 2023-04
TERM = {"term": "stellenabbau", "before": 1, "after": 3, "n_before": 20, "n_after": 20, "before_share": 0.05, "after_share": 0.15, "ratio": 3.0}
TERM2 = {"term": "homeoffice", "before": 0, "after": 4, "n_before": 20, "n_after": 20, "before_share": 0.0, "after_share": 0.2, "ratio": None}
TERMS = [TERM, TERM2]
TEXT_WITH_TERM = ("Der Konzern teilte am Dienstag mit, dass im Zuge des Sparprogramms ein Stellenabbau von bis zu 300 "
                  "Stellen vorgesehen ist. Die Belegschaft wurde am Vormittag informiert.")
TEXT_WITH_CATEGORY_ONLY = ("Im Rückblick auf das Geschäftsjahr nennt der Bericht Verluste im Auslandsgeschäft und eine "
                           "Klage eines Zulieferers; die Prognose bleibt unverändert.")


def news(title, text=None, date="2023-03-15"):
    item = src.make_item(title=title, url=f"https://x/{abs(hash(title + (text or '')))}", published_at=date, publisher="P",
                         source="gnews", source_type="news")
    if text is not None:
        item["text"] = text
        item["text_status"] = "ok"
    return item


def score(item, strict=True):
    return er.score_item(item, WINDOW, TERMS, {}, CATS, {"beispielkonzern"}, strict_terms=strict)


class TestScoreWithText:
    def test_term_in_text_counts_with_origin(self):
        s = score(news("Beispielkonzern legt Zahlen vor", TEXT_WITH_TERM))
        assert s["term_match"] == er.TERM_MATCH_PER_TERM and s["has_text"] and s["text_status"] == "ok"
        assert s["terms"] == [{**{k: TERM[k] for k in ("term", "before", "after", "n_before", "n_after")}, "word": "stellenabbau",
                               "strong": False, "in": er.TERM_IN_TEXT}]

    def test_title_hit_comes_first_and_is_not_doubled(self):
        s = score(news("Beispielkonzern: Stellenabbau beschlossen", TEXT_WITH_TERM + " Homeoffice bleibt möglich."))
        assert [(t["term"], t["in"]) for t in s["terms"]] == [("stellenabbau", "title"), ("homeoffice", "text")]
        assert s["term_match"] == 1.0   # zwei Begriffe, je 0,5 (homeoffice stark: 1, Summe höchstens 1)

    def test_without_text_everything_as_before(self):
        s = score(news("Beispielkonzern: Stellenabbau beschlossen"))
        assert s["has_text"] is False and s["text_status"] is None
        assert [(t["term"], t["in"]) for t in s["terms"]] == [("stellenabbau", "title")]
        assert score(news("Beispielkonzern legt Zahlen vor"))["term_match"] == 0.0

    def test_compound_direction_applies_to_text(self):
        text = "Die Firmen der Region melden Arbeitsplätze und Stellenabbauprogramme für das kommende Jahr."
        strict = score(news("Beispielkonzern legt Zahlen vor", text), strict=True)
        assert [t["word"] for t in strict["terms"]] == ["stellenabbauprogramme"]
        both = "Beim Stellen-Abbau geht es um Stellen."    # 'stellen' ist ein Wortanfang von 'stellenabbau', nicht umgekehrt
        assert score(news("Beispielkonzern legt Zahlen vor", both), strict=False)["term_match"] == 0.5   # E21: beide Richtungen
        assert score(news("Beispielkonzern legt Zahlen vor", both), strict=True)["term_match"] == 0.0    # E33: nur eine Richtung

    def test_category_and_employer_relation_stay_with_the_title(self):
        s = score(news("Beispielkonzern legt Zahlen vor", TEXT_WITH_CATEGORY_ONLY))
        assert s["category"] is None and s["employer_related"] is None and s["category_match"] == 0.0
        s = score(news("Beispielkonzern kündigt Stellenabbau an", "Die Aktie legte nach der Meldung an der Börse deutlich zu, der DAX stieg."))
        assert s["category"]["id"] == "personalabbau" and s["employer_related"] is True

    def test_empty_or_non_string_text_is_ignored(self):
        assert score({**news("Beispielkonzern legt Zahlen vor"), "text": ""})["has_text"] is False
        assert score({**news("Beispielkonzern legt Zahlen vor"), "text": ["liste"]})["has_text"] is False


class TestRankWithText:
    def test_text_hit_passes_strict_selection_and_is_marked(self):
        items = [news("Beispielkonzern legt Zahlen vor", TEXT_WITH_TERM), news("Beispielkonzern legt Zahlen vor im Detail")]
        ranked = er.rank_evidence(items, WINDOW, terms=TERMS, exclude={"beispielkonzern"}, categories=CATS)
        assert ranked["n_selected"] == 1 and ranked["n_excluded"] == 1
        entry = ranked["explanations"][0]
        assert entry["confidence"] == er.STAGE_MEDIUM and entry["has_text"] is True
        assert entry["terms"][0]["in"] == "text" and entry["items"][0]["has_text"] is True and entry["items"][0]["terms"][0]["in"] == "text"
        assert "'stellenabbau' steht im Text der Meldung und wird in den Bewertungen danach häufiger genannt (3 gegenüber 1 Bewertungen)" in entry["text"]
        scores = ranked["item_scores"]
        with_text = scores[items[0]["id"]]
        assert with_text["has_text"] and with_text["terms_in_text"] == ["stellenabbau"] and with_text["selected"]
        without = scores[items[1]["id"]]
        assert not without["has_text"] and without["terms_in_text"] == [] and without["excluded"] == er.EXCLUDED_TOPIC

    def test_bundle_carries_has_text_and_mixed_phrase(self):
        a = news("Beispielkonzern: Stellenabbau beschlossen", "Homeoffice bleibt für alle Beschäftigten weiter möglich, heißt es.")
        ranked = er.rank_evidence([a], WINDOW, terms=TERMS, exclude={"beispielkonzern"}, categories=CATS)
        entry = ranked["explanations"][0]
        assert entry["has_text"] and [t["in"] for t in entry["terms"]] == ["title", "text"]
        assert "'stellenabbau' und 'homeoffice' (im Text der Meldung) häufiger genannt" in entry["text"]

    def test_all_terms_in_text_phrase(self):
        a = news("Beispielkonzern legt Zahlen vor", TEXT_WITH_TERM + " Homeoffice bleibt für alle Beschäftigten möglich.")
        ranked = er.rank_evidence([a], WINDOW, terms=TERMS, exclude={"beispielkonzern"}, categories=CATS)
        text = ranked["explanations"][0]["text"]
        assert "'stellenabbau' und 'homeoffice' stehen im Text der Meldung und werden in den Bewertungen danach häufiger genannt (stellenabbau: 3 gegenüber 1, homeoffice: 4 gegenüber 0 Bewertungen)" in text
        assert "(im Text der Meldung)" not in text

    def test_rules_name_the_text_version(self):
        rules = er.rules()
        assert rules["text"] == {"version": 1, "version_date": "2026-10-23", "used_for": "term_match",
                                 "title_only": ["category_match", "employer_related", "company_in_title"],
                                 "term_max_share": 0.2, "term_min_hits": 3, "note": er.TEXT_NOTE}
        assert "im Text der Meldung" in er.SELECTION_RULES[2]
        assert rules["version"] == 2 and rules["selection"]["version"] == 1   # Stufenregeln und Auswahl unverändert


class TestFrequentTextTerms:
    """Begriffe, die in zu vielen Texten des Fensters stehen, zählen im Text nicht (E35)."""

    def test_counts_and_threshold(self):
        hit = "Der Stellenabbau trifft die Verwaltung; die Belegschaft wurde am Vormittag informiert."
        items = [news(f"Beispielkonzern Meldung {i}", hit if i < 3 else "Die Sitzung endete ohne weitere Beschlüsse.") for i in range(10)]
        out = er.frequent_text_terms(items, TERMS, strict_terms=True)
        assert out == {"n_texts": 10, "excluded": [{"term": "stellenabbau", "n_texts_with_term": 3, "share": 0.3}]}
        out = er.frequent_text_terms(items[:2] + items[3:], TERMS, strict_terms=True)    # 2 von 9: unter der Mindestzahl
        assert out["excluded"] == [] and out["n_texts"] == 9
        assert er.frequent_text_terms([news("ohne Text")], TERMS) == {"n_texts": 0, "excluded": []}
        assert er.frequent_text_terms([], TERMS) == {"n_texts": 0, "excluded": []}
        many = [news(f"Beispielkonzern {i}", hit) for i in range(3)] + [news(f"Beispielkonzern {i}", "nichts") for i in range(12)]
        assert er.frequent_text_terms(many, TERMS, strict_terms=True)["excluded"] == []   # 3 von 15 = 20 %: nicht über der Grenze

    def test_rank_skips_frequent_term_in_text_but_keeps_it_in_titles(self):
        hit = "Der Stellenabbau trifft die Verwaltung; die Belegschaft wurde am Vormittag informiert."
        items = [news(f"Beispielkonzern Meldung {i}", hit) for i in range(4)]
        items.append(news("Beispielkonzern: Stellenabbau beschlossen", hit))
        ranked = er.rank_evidence(items, WINDOW, terms=TERMS, exclude={"beispielkonzern"}, categories=CATS)
        assert ranked["texts"] == {"n_texts": 5, "n_with_text": 5,
                                   "excluded_terms": [{"term": "stellenabbau", "n_texts_with_term": 5, "share": 1.0}]}
        assert ranked["n_selected"] == 1 and ranked["explanations"][0]["terms"][0]["in"] == "title"
        for item in items[:4]:
            sc = ranked["item_scores"][item["id"]]
            assert sc["terms"] == [] and sc["has_text"] and sc["excluded"] == er.EXCLUDED_TOPIC

    def test_score_item_honours_text_excluded(self):
        s = er.score_item(news("Beispielkonzern legt Zahlen vor", TEXT_WITH_TERM), WINDOW, TERMS, {}, CATS, {"beispielkonzern"},
                          strict_terms=True, text_excluded={"stellenabbau"})
        assert s["terms"] == [] and s["has_text"]

    def test_rules_name_the_guard(self):
        text = er.rules()["text"]
        assert text["term_max_share"] == 0.2 and text["term_min_hits"] == 3 and "20 %" in text["note"]


class TestStopwordsExtended:
    """Funktionswörter, die in Texten in bis zu einem Drittel der Meldungen stehen, sind keine Begriffe mehr (E35)."""

    def test_generic_words_are_stopwords(self):
        from services.review_terms import STOPWORDS
        for word in ("andere", "bisher", "deutlich", "aktuellen", "eigenen", "gerade", "statt", "wohl", "innerhalb", "sogar",
                     "wäre", "hätte", "konnte", "musste", "weder", "laut", "paar", "seit", "pro", "uhr", "gegenüber",
                     "don", "far", "every", "everything", "nothing", "especially", "different", "think", "really"):
            assert word in STOPWORDS, word
        for word in ("stellenabbau", "überstunden", "weiterbildung", "vorgesetzte", "homeoffice", "gehalt", "verantwortung"):
            assert word not in STOPWORDS, word

    def test_generic_words_do_not_become_terms(self):
        from services.review_terms import distinctive_terms
        before = [{"titel": "Alles ruhig", "gut_am_arbeitgeber_finde_ich": "nett"} for _ in range(12)]
        after = [{"titel": "Andere Sicht", "gut_am_arbeitgeber_finde_ich": "bisher deutlich andere Lage, Stellenabbau"} for _ in range(12)]
        terms = {t["term"] for t in distinctive_terms(before, after, source="employee")}
        assert "stellenabbau" in terms and not ({"andere", "bisher", "deutlich"} & terms)
