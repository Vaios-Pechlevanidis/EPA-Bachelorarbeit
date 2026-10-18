"""
Strenge Auswahl der Belege für die Erklärungsansätze (E33, 2026-10-18): vier
Ausschlussregeln je Beleg vor Bündelung und Rangfolge (Unternehmen im Titel, Arbeitgeberbezug,
Wortbezug oder Themenverschiebung, zeitliche Nähe mindestens 0,5); ausgeschlossene Belege
stehen in ``item_scores`` mit der nicht erfüllten Regel hinter allen Bündeln; ``strict=False``
gibt die Fassung bis 2026-10-17. Die Werte sind Setzungen des Autors und hier festgeschrieben.
Alle Titel und Bewertungen sind konstruiert (E7).

Ausführung:
    cd backend
    uv run python -m pytest tests/explanations/test_strict_selection.py -q -p no:cacheprovider
"""

import os
import re
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))

import services.evidence_service as ev  # noqa: E402
import services.evidence_sources as src  # noqa: E402
import services.explanation_ranking as er  # noqa: E402
import services.explanation_service as es  # noqa: E402
from services.event_categories import load_event_categories  # noqa: E402
from services.review_terms import company_terms, distinctive_terms  # noqa: E402

CATS = load_event_categories(use_cache=False)
# Niveauwechsel 2023-04 mit Lücke: Übergang ab 2023-03, Fenster 2022-12 bis 2023-05; zeitliche
# Nähe 1 in 2023-02 bis 2023-04, 0,67 in 2023-01, 0,33 in 2022-12, 0,5 in 2023-05.
WINDOW = ev.window_for_change("2023-04", "2023-02", 1, 3, 1)
CAUSAL = re.compile(r"\b(ursache|ursachen|ursächlich|auslöser|auslösen|ausgelöst|grund|gründe|weil|führte|führt zu|wegen)\b", re.IGNORECASE)


def item(title, day, source_type="news", publisher="Blatt", category=None):
    return src.make_item(title=title, url=f"https://x/{abs(hash((title, day))) % 10**8}", published_at=day, publisher=publisher,
                         source="eqs" if source_type == "adhoc" else "gnews", source_type=source_type, category=category)


def reviews(n, text, start):
    return [{"id": start + i, "datum": "2023-04-10", "schlecht_am_arbeitgeber_finde_ich": text} for i in range(n)]


@pytest.fixture
def context():
    before = reviews(20, "Alles ruhig im Büro", 1)
    after = reviews(12, "Der Stellenabbau drückt die Stimmung", 100) + reviews(8, "Alles ruhig im Büro", 200)
    terms = distinctive_terms(before, after, exclude={"beispielwerk"})
    topics = er.topic_shift_table(before, after, "employee")
    items = {
        "kept": item("Beispielwerk kündigt Stellenabbau an", "2023-02-10", publisher="A"),
        "unnamed": item("Konzern kündigt Stellenabbau an", "2023-02-11", publisher="B"),
        "stock": item("Aktie von Beispielwerk erreicht Kursziel", "2023-02-15", publisher="C"),
        "category_only": item("Neuer Chef bei Beispielwerk", "2023-02-05", publisher="D"),
        "far": item("Beispielwerk: Stellenabbau beschlossen", "2022-12-20", publisher="E"),
        "eqs": item("Restructuring programme announced", "2023-02-12", source_type="adhoc", publisher="EQS News", category="Ad-hoc"),
        "plain": item("Beispielwerk eröffnet Kantine", "2023-05-20", publisher="F"),
    }
    return {"before": before, "after": after, "terms": terms, "topics": topics, "items": items}


# ── Festschreibung ───────────────────────────────────────────────────────────

def test_selection_constants_frozen():
    assert er.STRICT_SELECTION is True and er.SELECTION_VERSION == 1 and er.SELECTION_DATE == "2026-10-18"
    assert er.SELECTION_MIN_TIME == 0.5 and er.COMPANY_TITLE_MAX_SUFFIX == 2
    assert er.EXCLUSION_REASONS == ("Unternehmen im Titel nicht genannt", "ohne Arbeitgeberbezug",
                                    "kein Wortbezug und keine Themenverschiebung", "zeitliche Nähe unter 0,5")
    assert len(er.SELECTION_RULES) == 4
    assert er.RULES_VERSION == 2, "die Stufenregeln bleiben in der zweiten Fassung"
    sel = er.rules()["selection"]
    assert sel == er.selection_rules()
    assert sel["strict"] is True and sel["version"] == 1 and sel["min_stage"] == "mittel" and sel["min_time"] == 0.5
    assert sel["require_company_in_title"] is True and sel["exclude_non_employer"] is True
    assert sel["rules"] == list(er.SELECTION_RULES) and sel["reasons"] == list(er.EXCLUSION_REASONS)


def test_texts_without_causal_words():
    for text in (*er.SELECTION_RULES, *er.EXCLUSION_REASONS, er.SELECTION_NOTE):
        assert not CAUSAL.search(text), text
    # Der feste Hinweis verneint Ursachen ("interne Auslöser ... nicht sichtbar"), wie bisher (test_fixed_notes).
    assert "interne auslöser sind von außen nicht sichtbar" in er.OPEN_NOTE.lower() and "offen" in er.OPEN_NOTE
    assert "strengen auswahlregeln" in er.OPEN_NOTE.lower()
    assert er.OPEN_NOTE_LENIENT.startswith("Kein Beleg erreicht die Stufe niedrig")


# ── Unternehmen im Titel ─────────────────────────────────────────────────────

class TestCompanyInTitle:

    def test_title_words_drop_generic_and_stop_words(self):
        assert er.company_title_words(company_terms("Telekom", '"Deutsche Telekom"')) == {"telekom"}
        words = er.company_title_words(company_terms("Compugroup Medical Deutschland", '"CompuGroup Medical" OR CompuGroup'))
        assert "compugroup" in words and "medical" not in words and "deutschland" not in words
        assert er.company_title_words({"digital", "technology"}) == {"digital", "technology"}, "allgemeine Wörter nur, wenn nichts anderes bleibt"
        assert er.company_title_words({"eon"}, extra=["CGM", "E.ON Energie"]) == {"eon", "cgm", "energie"}
        assert er.company_title_words(()) == set()

    @pytest.mark.parametrize("title, expected", [
        ("Telekom streicht Stellen", True),
        ("Telekoms Chef geht", True),                       # Genitiv: höchstens 2 Zeichen mehr
        ("Telekom-Tochter baut um", True),
        ("Telekommunikation: Branche wächst", False),       # Wortanfang mit längerem Rest zählt nicht
        ("Deutsche Bahn streicht Stellen", False),          # "Deutsche" ist kein kennzeichnendes Wort
        ("Konzern streicht Stellen", False),
    ])
    def test_strict_name_rule(self, title, expected):
        words = er.company_title_words(company_terms("Telekom", '"Deutsche Telekom"'))
        assert er.company_in_title(title, words) is expected

    def test_dots_digits_and_unknown(self):
        assert er.company_in_title("E.ON kündigt Stellenabbau an", er.company_title_words(company_terms("E.ON", "E.ON"))) is True
        assert er.company_in_title("1&1 mit neuem Netz", er.company_title_words(company_terms("1&1 AG", '"1&1"'))) is True
        assert er.company_in_title("CGM streicht Stellen", er.company_title_words(company_terms("Compugroup Medical Deutschland"), ["CGM"])) is True
        assert er.company_in_title("CGM streicht Stellen", er.company_title_words(company_terms("Compugroup Medical Deutschland"))) is False
        assert er.company_in_title("Irgendwas", set()) is None and er.company_in_title("", {"x"}) is None


# ── Wortbezug nur in einer Richtung ──────────────────────────────────────────

class TestCompoundOnlyTerms:
    TERMS = [{"term": "firmenwagen", "before": 0, "after": 4, "n_before": 20, "n_after": 20, "before_share": 0.0, "after_share": 0.2, "ratio": None},
             {"term": "stellenabbau", "before": 0, "after": 4, "n_before": 20, "n_after": 20, "before_share": 0.0, "after_share": 0.2, "ratio": None}]

    def test_match_terms_direction(self):
        from services.review_terms import match_terms
        lenient = [m["term"] for m in match_terms("Firmen bringen Geflüchtete in Arbeit; Stellenabbauprogramm läuft", self.TERMS)]
        strict = [m["term"] for m in match_terms("Firmen bringen Geflüchtete in Arbeit; Stellenabbauprogramm läuft", self.TERMS, compound_only=True)]
        assert lenient == ["firmenwagen", "stellenabbau"], "bisher: 'firmen' trifft 'firmenwagen'"
        assert strict == ["stellenabbau"], "streng: nur der Begriff selbst oder ein Wort, das mit ihm beginnt"
        assert [m["word"] for m in match_terms("Der Firmenwagen bleibt", self.TERMS, compound_only=True)] == ["firmenwagen"]

    def test_rank_evidence_uses_compound_only_when_strict(self):
        it = item("Beispielwerk: Firmen bringen Geflüchtete in Arbeit", "2023-02-10")
        strict = er.rank_evidence([it], WINDOW, terms=self.TERMS, topics=[], exclude={"beispielwerk"}, categories=CATS)
        lenient = er.rank_evidence([it], WINDOW, terms=self.TERMS, topics=[], exclude={"beispielwerk"}, categories=CATS, strict=False)
        assert strict["item_scores"][it["id"]]["term_match"] == 0.0 and strict["item_scores"][it["id"]]["excluded"] == er.EXCLUDED_TOPIC
        assert lenient["item_scores"][it["id"]]["term_match"] == 0.5 and lenient["state"] == "ansaetze"
        assert er.rules()["selection"]["term_match_compound_only"] is True


# ── Ausschlussregeln je Beleg ────────────────────────────────────────────────

class TestExclusionReason:

    def _scored(self, **kw):
        base = {"source_type": "news", "company_in_title": True, "employer_related": True, "term_match": 0.5, "category_match": 0.5, "time_match": 1.0}
        return {**base, **kw}

    def test_order_and_each_rule(self):
        assert er.exclusion_reason(self._scored()) is None
        assert er.exclusion_reason(self._scored(company_in_title=False)) == er.EXCLUDED_COMPANY
        assert er.exclusion_reason(self._scored(company_in_title=None)) is None, "ohne Namenswörter nicht prüfbar"
        assert er.exclusion_reason(self._scored(company_in_title=False, source_type="adhoc")) is None, "EQS-Mitteilung des Emittenten"
        assert er.exclusion_reason(self._scored(employer_related=False, category_match=0.0)) == er.EXCLUDED_NON_EMPLOYER
        assert er.exclusion_reason(self._scored(term_match=0.0, category_match=0.5)) == er.EXCLUDED_TOPIC, "nur Ereignisart genügt nicht"
        assert er.exclusion_reason(self._scored(term_match=0.0, category_match=1.0)) is None, "Themenverschiebung genügt"
        assert er.exclusion_reason(self._scored(term_match=0.0, category_match=0.0, employer_related=None)) == er.EXCLUDED_TOPIC
        assert er.exclusion_reason(self._scored(time_match=0.33)) == er.EXCLUDED_TIME
        assert er.exclusion_reason(self._scored(time_match=0.5)) is None
        # Reihenfolge: das Unternehmen vor dem Arbeitgeberbezug vor dem Thema vor der Zeit
        assert er.exclusion_reason(self._scored(company_in_title=False, employer_related=False, term_match=0.0, time_match=0.0)) == er.EXCLUDED_COMPANY

    def test_select_items_marks_entries(self):
        scored = [self._scored(id=1), self._scored(id=2, time_match=0.33)]
        kept, dropped = er.select_items(scored)
        assert [s["id"] for s in kept] == [1] and [s["id"] for s in dropped] == [2]
        assert kept[0]["selected"] is True and kept[0]["excluded"] is None and dropped[0]["excluded"] == er.EXCLUDED_TIME
        kept, dropped = er.select_items([self._scored(id=3, time_match=0.0)], strict=False)
        assert len(kept) == 1 and dropped == [] and kept[0]["selected"] is True

    def test_every_selected_item_reaches_stage_medium(self):
        """Wer alle vier Regeln erfüllt, erreicht nach den Stufenregeln mindestens mittel."""
        for term in (0.0, 0.5, 1.0):
            for category, employer in ((0.0, None), (0.5, True), (1.0, True), (0.0, False)):
                for time in (0.0, 0.33, 0.5, 0.67, 1.0):
                    s = self._scored(term_match=term, category_match=category, employer_related=employer, time_match=time)
                    if er.exclusion_reason(s) is None:
                        assert er.stage_for(term, category, time, employer) in ("hoch", "mittel"), s


# ── Rangfolge mit strenger Auswahl ───────────────────────────────────────────

class TestRankEvidenceStrict:

    def _rank(self, context, **kw):
        return er.rank_evidence(list(context["items"].values()), WINDOW, terms=context["terms"], topics=context["topics"],
                                exclude={"beispielwerk"}, categories=CATS, analyzer=None, **kw)

    def test_only_selected_items_become_explanations(self, context):
        result = self._rank(context)
        items = context["items"]
        assert result["state"] == "ansaetze" and result["n_items"] == 7 and result["n_selected"] == 2 and result["n_excluded"] == 5
        assert result["n_excluded_by_reason"] == {er.EXCLUDED_COMPANY: 1, er.EXCLUDED_NON_EMPLOYER: 1, er.EXCLUDED_TOPIC: 2, er.EXCLUDED_TIME: 1}
        assert result["n_bundles"] == 2 and result["n_by_stage"] == {"hoch": 1, "mittel": 1, "niedrig": 0, "keine": 0}
        assert len(result["explanations"]) == 1, "eine Gruppe (Personalabbau) mit zwei Bündeln"
        top = result["explanations"][0]
        assert top["id"] == items["kept"]["id"] and top["confidence"] == "hoch" and top["n_items"] == 1, "der ungenannte Konzern wird nicht gebündelt"
        assert top["group"]["n_bundles"] == 2 and top["group"]["others"][0]["id"] == items["eqs"]["id"]
        shown = {top["id"]} | {o["id"] for o in top["group"]["others"]} | {i["id"] for i in top["items"]}
        assert not shown & {items[k]["id"] for k in ("unnamed", "stock", "category_only", "far", "plain")}
        assert result["selection"]["strict"] is True and result["open_note"] is None

    def test_item_scores_name_the_failed_rule_and_rank_after_bundles(self, context):
        scores = self._rank(context)["item_scores"]
        items = context["items"]
        assert len(scores) == 7
        assert scores[items["kept"]["id"]]["rank"] == 1 and scores[items["eqs"]["id"]]["rank"] == 2
        for key in ("kept", "eqs"):
            assert scores[items[key]["id"]]["selected"] is True and scores[items[key]["id"]]["excluded"] is None
        expected = {"unnamed": er.EXCLUDED_COMPANY, "stock": er.EXCLUDED_NON_EMPLOYER, "category_only": er.EXCLUDED_TOPIC,
                    "far": er.EXCLUDED_TIME, "plain": er.EXCLUDED_TOPIC}
        for key, reason in expected.items():
            s = scores[items[key]["id"]]
            assert s["selected"] is False and s["excluded"] == reason and s["rank"] > 2 and s["bundle"] is None and s["bundle_size"] == 1
        assert scores[items["unnamed"]["id"]]["stage"] == "hoch", "die eigene Stufe bleibt sichtbar"
        assert scores[items["unnamed"]["id"]]["rank"] == 3 < scores[items["far"]["id"]]["rank"] < scores[items["category_only"]["id"]]["rank"]
        assert scores[items["stock"]["id"]]["stage"] == "keine" and scores[items["stock"]["id"]]["company_in_title"] is True

    def test_open_when_nothing_passes(self, context):
        items = [context["items"][k] for k in ("unnamed", "stock", "category_only", "far", "plain")]
        result = er.rank_evidence(items, WINDOW, terms=context["terms"], topics=context["topics"], exclude={"beispielwerk"}, categories=CATS)
        assert result["state"] == "offen" and result["explanations"] == [] and result["n_selected"] == 0 and result["n_excluded"] == 5
        assert result["n_bundles"] == 0 and result["open_note"] == er.OPEN_NOTE and sum(result["n_by_stage"].values()) == 0

    def test_lenient_variant_reproduces_the_previous_ranking(self, context):
        lenient = self._rank(context, strict=False)
        assert lenient["n_excluded"] == 0 and lenient["n_selected"] == 7 and lenient["selection"]["strict"] is False
        assert all(s["selected"] and s["excluded"] is None for s in lenient["item_scores"].values())
        assert lenient["n_by_stage"]["niedrig"] >= 1 and lenient["n_by_stage"]["keine"] >= 1
        assert lenient["explanations"][0]["n_items"] == 2, "ohne Auswahl wird der ungenannte Konzern gebündelt"
        assert len(lenient["explanations"]) > 1

    def test_global_events_stay_out(self, context):
        g = ev.global_event_items([{"id": "g", "date_from": "2023-01", "date_to": "2023-03", "title": "Allgemeines", "scope": "x",
                                    "note": "n", "url": "https://g", "confirmed": True}], WINDOW)[0]
        result = er.rank_evidence([context["items"]["kept"], g], WINDOW, terms=context["terms"], topics=context["topics"],
                                  exclude={"beispielwerk"}, categories=CATS)
        assert result["n_items"] == 1 and result["n_selected"] == 1 and len(result["global_events"]) == 1


# ── Kennungen aus der Metadatei (title_words) ────────────────────────────────

class TestTitleWords:

    def test_explanations_for_passes_title_words(self, context):
        info = {"company_id": 27, "name": "Compugroup Medical Deutschland", "search_term": '"CompuGroup Medical" OR CompuGroup'}
        evidence = {"items": [item("CGM streicht 300 Stellen", "2023-02-10")], "sources": {}, "coverage": True, "reason": None}
        comparison = {"topics": context["topics"]}
        with_words = es.explanations_for(27, WINDOW, context["before"], context["after"], comparison, info={**info, "title_words": ["CGM"]},
                                         evidence=evidence, source="employee")
        without = es.explanations_for(27, WINDOW, context["before"], context["after"], comparison, info=info, evidence=evidence, source="employee")
        assert with_words["summary"]["state"] == "ansaetze" and with_words["summary"]["n_selected"] == 1
        assert without["summary"]["state"] == "offen" and without["summary"]["n_excluded_by_reason"][er.EXCLUDED_COMPANY] == 1
        for s in (with_words["summary"], without["summary"]):
            assert s["selection"]["version"] == 1 and set(s["n_excluded_by_reason"]) == set(er.EXCLUSION_REASONS)

    def test_company_context_info_reads_title_words(self, monkeypatch):
        import services.context_service as cs
        monkeypatch.setattr(cs, "company_ticker_info", lambda cid: {"company_id": cid, "name": "Compugroup Medical Deutschland"} if cid == 27 else None)
        meta = {27: {"company_id": 27, "name": "Compugroup Medical Deutschland", "title_words": ["CGM", " ", 7]}}
        assert ev.company_context_info(27, meta)["title_words"] == ["CGM", "7"]
        assert ev.company_context_info(27, {27: {"company_id": 27, "name": "Compugroup Medical Deutschland"}})["title_words"] == []
        assert cs.load_metadata()[27].get("title_words") == ["CGM"], "Vorschlag in company_metadata.json (vom Autor zu bestätigen)"
