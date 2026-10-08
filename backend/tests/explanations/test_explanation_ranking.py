"""
Tests für services/explanation_ranking.py (Inkrement 5, A3): die drei Signale, Stufenregeln,
Rückstufung ohne Arbeitgeberbezug, Bündelung, Sortierung, Textbausteine (ohne Ursache-
Wörter), Stimmung des Titels ohne Einfluss auf die Stufe, Rangfolge eines Fensters mit
Zustand „offen“. Alle Titel und Bewertungen sind konstruiert (E7).

Ausführung:
    cd backend
    uv run python -m pytest tests/explanations/test_explanation_ranking.py -q -p no:cacheprovider
"""

import os
import re
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))

import services.evidence_service as ev  # noqa: E402
import services.evidence_sources as src  # noqa: E402
import services.explanation_ranking as er  # noqa: E402
from services.event_categories import load_event_categories  # noqa: E402
from services.review_terms import distinctive_terms  # noqa: E402

CATS = load_event_categories(use_cache=False)
# Niveauwechsel 2023-04 mit Lücke: letzter bewerteter Monat davor 2023-02, Übergang ab 2023-03,
# Fenster 2022-12 bis 2023-05 (3 Monate vor dem Übergang, 1 danach).
WINDOW = ev.window_for_change("2023-04", "2023-02", 1, 3, 1)
SELECTION = ev.window_for_selection("2023-03", "2023-04", 3, 1)
OUTLIER = ev.window_for_outlier("2023-04", 3, 1)

TERM_WEAK = {"term": "stellenabbau", "before": 1, "after": 3, "n_before": 20, "n_after": 20, "before_share": 0.05, "after_share": 0.15, "ratio": 3.0}
TERM_STRONG = {"term": "entlassung", "before": 0, "after": 6, "n_before": 20, "n_after": 20, "before_share": 0.0, "after_share": 0.3, "ratio": None}
TERM_MANY_BUT_FLAT = {"term": "streik", "before": 3, "after": 6, "n_before": 20, "n_after": 20, "before_share": 0.15, "after_share": 0.3, "ratio": 2.0}
SHIFTED = [{"topic": "Arbeitsatmosphäre", "share_shift_pp": -8.0, "low_basis": False},
           {"topic": "Kommunikation", "share_shift_pp": 2.0, "low_basis": False},
           {"topic": "Image", "share_shift_pp": -12.0, "low_basis": True}]


def item(title, day, source_type="news", publisher="Blatt", url=None, category=None):
    it = src.make_item(title=title, url=url or f"https://x/{abs(hash((title, day, publisher))) % 10**8}",
                       published_at=day, publisher=publisher, source="eqs" if source_type == "adhoc" else "gnews",
                       source_type=source_type, category=category)
    return it


class StubAnalyzer:
    mode = "lexicon"

    def __init__(self, label="negative", polarity=-0.6):
        self.label, self.polarity, self.calls = label, polarity, []

    def analyze_sentiment(self, text, star_rating=None):
        self.calls.append(text)
        return {"sentiment": self.label, "polarity": self.polarity}


# ═══════════════════════════════════════════════════════════════════════════════
# 1. Signale
# ═══════════════════════════════════════════════════════════════════════════════

class TestTimeMatch:

    @pytest.mark.parametrize("month, expected", [
        ("2022-11", 0.0),    # außerhalb
        ("2022-12", 0.33),   # Rand, 2 Monate vor dem Monat vor dem Übergang
        ("2023-01", 0.67),
        ("2023-02", 1.0),    # Monat vor dem Übergang
        ("2023-03", 1.0),    # Übergang (Lücke)
        ("2023-04", 1.0),    # markierter Monat
        ("2023-05", 0.5),    # Monat danach
        ("2023-06", 0.0),
    ])
    def test_change_window_with_gap(self, month, expected):
        assert er.time_match(f"{month}-15", WINDOW) == expected

    def test_selection_and_outlier(self):
        assert [er.time_match(f"{m}-10", SELECTION) for m in ("2022-12", "2023-01", "2023-02", "2023-03", "2023-04", "2023-05")] == [0.33, 0.67, 1.0, 1.0, 1.0, 0.5]
        assert [er.time_match(f"{m}-10", OUTLIER) for m in ("2023-01", "2023-03", "2023-04", "2023-05")] == [0.33, 1.0, 1.0, 0.5]

    def test_longer_after_window_decreases(self):
        window = ev.window_for_outlier("2023-04", 1, 2)
        assert [er.time_match(f"{m}-01", window) for m in ("2023-03", "2023-04", "2023-05", "2023-06")] == [1.0, 1.0, 0.5, 0.25]

    def test_no_or_bad_date(self):
        assert er.time_match(None, WINDOW) == 0.0 and er.time_match("kein datum", WINDOW) == 0.0


class TestTermMatch:

    def test_weights(self):
        assert er.term_match([]) == 0.0
        assert er.term_match([TERM_WEAK]) == 0.5
        assert er.term_match([TERM_STRONG]) == 1.0, "mindestens 5 danach, ohne Nennung davor: stark"
        assert er.term_match([TERM_WEAK, TERM_MANY_BUT_FLAT]) == 1.0, "zwei Begriffe zählen voll"
        assert er.term_match([TERM_MANY_BUT_FLAT]) == 0.5, "6 danach, aber Verhältnis 2 < 3: nicht stark"
        assert er.is_strong_term(TERM_STRONG) and not er.is_strong_term(TERM_WEAK)


class TestCategoryMatch:

    def test_with_shift_only_and_none(self):
        shifts = er.topic_shift_index(SHIFTED)
        primary = {"id": "personalabbau", "employer_related": True, "topics": ["Arbeitsatmosphäre", "Kommunikation", "Image"]}
        match, shifted = er.category_match(primary, shifts)
        assert match == 1.0 and [s["topic"] for s in shifted] == ["Arbeitsatmosphäre"], "Image hat kleine Basis, Kommunikation unter 5 Pp."
        assert er.category_match({"id": "x", "employer_related": True, "topics": ["Kommunikation"]}, shifts) == (0.5, [])
        assert er.category_match({"id": "x", "employer_related": True, "topics": ["Image"]}, shifts) == (0.5, []), "kleine Basis zählt nicht"
        assert er.category_match({"id": "ohne", "employer_related": False, "topics": []}, shifts) == (0.0, [])
        assert er.category_match(None, shifts) == (0.0, [])


# ═══════════════════════════════════════════════════════════════════════════════
# 2. Stufen
# ═══════════════════════════════════════════════════════════════════════════════

class TestStages:

    @pytest.mark.parametrize("topic, time, expected", [
        (1.0, 1.0, "hoch"),
        (1.0, 0.67, "mittel"),
        (1.0, 0.5, "mittel"),
        (0.5, 1.0, "mittel"),
        (1.0, 0.33, "niedrig"),
        (0.5, 0.67, "niedrig"),
        (0.5, 0.5, "niedrig"),
        (0.5, 0.33, "niedrig"),
        (0.5, 0.17, "keine"),    # Rand eines Fensters von 6 Monaten
        (0.0, 1.0, "keine"),     # zeitliche Nähe allein genügt nie
        (0.0, 0.0, "keine"),
    ])
    def test_rules(self, topic, time, expected):
        assert er.stage_for(topic, time) == expected

    def test_group_without_employer_relation_one_stage_lower(self):
        assert er.stage_for(1.0, 1.0, employer_related=False) == "mittel"
        assert er.stage_for(1.0, 0.5, employer_related=False) == "niedrig"
        assert er.stage_for(0.5, 0.5, employer_related=False) == "keine"
        assert er.stage_for(0.0, 1.0, employer_related=False) == "keine"
        assert er.stage_for(1.0, 1.0, employer_related=True) == "hoch" and er.stage_for(1.0, 1.0, None) == "hoch"

    def test_score_item_combines_signals(self):
        shifts = er.topic_shift_index(SHIFTED)
        scored = er.score_item(item("Konzern kündigt Stellenabbau an", "2023-02-10"), WINDOW, [TERM_WEAK], shifts, CATS)
        assert (scored["term_match"], scored["category_match"], scored["topic_match"], scored["time_match"]) == (0.5, 1.0, 1.0, 1.0)
        assert scored["stage"] == "hoch" and scored["category"]["id"] == "personalabbau"
        assert scored["category"]["shifted_topics"][0]["topic"] == "Arbeitsatmosphäre"
        assert scored["terms"][0]["term"] == "stellenabbau" and scored["terms"][0]["strong"] is False

    def test_score_item_stock_report_is_downgraded(self):
        scored = er.score_item(item("Aktie fällt auf neues Kursziel", "2023-02-10"), WINDOW, [], {}, CATS)
        assert scored["employer_related"] is False and scored["topic_match"] == 0.0 and scored["stage"] == "keine"
        with_term = er.score_item(item("Aktie fällt nach Entlassungen", "2023-02-10"), WINDOW, [TERM_STRONG], {}, CATS)
        assert with_term["category"]["id"] == "personalabbau" and with_term["stage"] == "hoch", "Arbeitgeberbezug hat Vorrang"
        stock_with_term = er.score_item(item("Aktie unter Druck, Analysten senken Kursziel nach Entlassungswelle im Vertrieb", "2023-02-10"),
                                        WINDOW, [{**TERM_STRONG, "term": "vertrieb"}], {}, CATS)
        assert stock_with_term["stage"] in ("hoch", "mittel")

    def test_score_item_only_stock_terms_downgrade(self):
        """Test: Börsenbericht mit Wortbezug, aber ohne Ereignisart mit Arbeitgeberbezug: eine Stufe tiefer."""
        scored = er.score_item(item("Aktie steigt dank Dividende", "2023-02-10"), WINDOW, [{**TERM_STRONG, "term": "dividende"}], {}, CATS)
        assert scored["category"]["id"] == "ohne_arbeitgeberbezug" and scored["topic_match"] == 1.0 and scored["stage"] == "mittel"


# ═══════════════════════════════════════════════════════════════════════════════
# 3. Bündelung und Sortierung
# ═══════════════════════════════════════════════════════════════════════════════

class TestBundling:

    def _scored(self, items, terms=(), shifts=None):
        return [er.score_item(i, WINDOW, list(terms), shifts or {}, CATS) for i in items]

    def test_same_event_bundled_adhoc_is_representative(self):
        items = [
            item("Konzern streicht 500 Stellen in der Verwaltung", "2023-02-10", publisher="Blatt A"),
            item("Konzern streicht 500 Stellen: Verwaltung betroffen", "2023-02-11", publisher="Blatt B"),
            item("Konzern streicht 500 Stellen", "2023-02-12", source_type="adhoc", publisher="EQS News"),
            item("Konzern streicht 500 Stellen in der Verwaltung", "2023-02-20", publisher="Blatt C"),   # zu weit weg
            item("Neuer Chef für die Verwaltung", "2023-02-11", publisher="Blatt A"),                     # andere Ereignisart
        ]
        bundles = er.bundle_items(self._scored(items, [TERM_WEAK]))
        assert sorted(b["n_items"] for b in bundles) == [1, 1, 3]
        big = next(b for b in bundles if b["n_items"] == 3)
        assert big["representative"]["source_type"] == "adhoc" and big["has_adhoc"] is True
        assert big["publishers"] == ["EQS News", "Blatt A", "Blatt B"] and big["date"] == "2023-02-12"   # Stellvertreter zuerst
        assert big["category"]["id"] == "personalabbau"

    def test_bundle_takes_highest_signals(self):
        items = [item("Werk schließt, 200 Stellen fallen weg", "2022-12-30"),
                 item("Werk schließt: 200 Stellen fallen weg", "2023-01-02")]   # 3 Tage später, Monat näher am Übergang
        scored = self._scored(items, [TERM_WEAK])
        assert [s["time_match"] for s in scored] == [0.33, 0.67]
        bundle = er.bundle_items(scored)
        assert len(bundle) == 1 and bundle[0]["time_match"] == 0.67 and bundle[0]["stage"] == "niedrig"

    def test_company_name_does_not_make_titles_similar(self):
        items = [item("Beispielwerk AG eröffnet Standort", "2023-02-10"), item("Beispielwerk AG schließt Standort", "2023-02-10")]
        scored = self._scored(items)
        assert len(er.bundle_items(scored, exclude={"beispielwerk"})) == 2
        assert er.title_similarity("Beispielwerk AG eröffnet Standort", "Beispielwerk AG schließt Standort", {"beispielwerk"}) == pytest.approx(1 / 3)

    def test_without_date(self):
        it = item("Streik im Werk", "2023-02-10")
        it["date"] = None
        bundles = er.bundle_items(self._scored([it, item("Streik im Werk", "2023-02-10")]))
        assert len(bundles) == 2, "ohne Datum kein Bündel"

    def test_sort_key_stage_then_source_type_then_signals(self):
        def bundle(stage, source_type, topic=1.0, time=1.0, n=1, date="2023-02-01"):
            return {"stage": stage, "source_type": source_type, "topic_match": topic, "time_match": time, "n_items": n, "date": date}
        order = sorted([
            bundle("niedrig", "adhoc"), bundle("hoch", "news", 0.5, 1.0), bundle("hoch", "adhoc", 0.5, 0.5),
            bundle("mittel", "news", n=3), bundle("mittel", "news", n=1), bundle("keine", "adhoc"), bundle("hoch", "news", 1.0, 1.0, n=2),
        ], key=er.sort_key)
        assert [(b["stage"], b["source_type"], b["topic_match"], b["n_items"]) for b in order] == [
            ("hoch", "adhoc", 0.5, 1), ("hoch", "news", 1.0, 2), ("hoch", "news", 0.5, 1),
            ("mittel", "news", 1.0, 3), ("mittel", "news", 1.0, 1), ("niedrig", "adhoc", 1.0, 1), ("keine", "adhoc", 1.0, 1)]


# ═══════════════════════════════════════════════════════════════════════════════
# 4. Textbausteine
# ═══════════════════════════════════════════════════════════════════════════════

FORBIDDEN = re.compile(r"\b(ursache|ursachen|ursächlich|auslöser|auslösen|ausgelöst|auslöst|grund|gründe|weil|führte|führt zu|führten|"
                       r"verursacht|verursachte|wegen|deshalb|deswegen|daher|bewirkt|bewirkte|folge von|infolge|aufgrund)\b", re.IGNORECASE)


def _bundle(**kw):
    base = {"n_items": 1, "has_adhoc": False, "source_type": "news", "date": "2023-02-10", "terms": [], "category": None}
    base.update(kw)
    return base


TEXT_CASES = [
    _bundle(),
    _bundle(n_items=4, has_adhoc=True, category={"label": "Personalabbau und Restrukturierung", "employer_related": True, "shifted_topics": []},
            terms=[{"term": "stellenabbau", "after": 12, "before": 1}]),
    _bundle(category={"label": "Personalabbau und Restrukturierung", "employer_related": True,
                      "shifted_topics": [{"topic": "Arbeitsatmosphäre", "share_shift_pp": -8.5}, {"topic": "Kommunikation", "share_shift_pp": 6.0}]},
            terms=[{"term": "stellenabbau", "after": 12, "before": 1}, {"term": "entlassung", "after": 6, "before": 0}]),
    _bundle(source_type="adhoc", date="2023-04-03", category={"label": "Führungswechsel", "employer_related": True, "shifted_topics": []}),
    _bundle(date="2022-12-20", category={"label": "Ohne Arbeitgeberbezug", "employer_related": False, "shifted_topics": []},
            terms=[{"term": "dividende", "after": 5, "before": 0}]),
    _bundle(date="2023-05-02", n_items=2),
    _bundle(date=None),
]


class TestText:

    def test_example_sentence(self):
        text = er.explanation_text(TEXT_CASES[1], WINDOW)
        assert text == ("Möglicher Zusammenhang: 4 Meldungen (darunter eine Ad-hoc-Mitteilung) zu Personalabbau und "
                        "Restrukturierung im Monat vor dem Übergang; in den Bewertungen danach wird 'stellenabbau' häufiger "
                        "genannt (12 gegenüber 1 Bewertungen); die Ereignisart ist aus dem Titel erkannt, ein zugeordnetes "
                        "Thema verschiebt sich nicht merklich.")

    def test_two_terms_and_shifted_topics(self):
        text = er.explanation_text(TEXT_CASES[2], WINDOW)
        assert "werden 'stellenabbau' und 'entlassung' häufiger genannt (stellenabbau: 12 gegenüber 1, entlassung: 6 gegenüber 0 Bewertungen)" in text
        assert "verschieben sich die zugeordneten Themen Arbeitsatmosphäre um -8,5, Kommunikation um +6,0 Prozentpunkte" in text

    def test_adhoc_in_marked_month_and_downgraded_group(self):
        assert er.explanation_text(TEXT_CASES[3], WINDOW).startswith("Möglicher Zusammenhang: eine Ad-hoc-Mitteilung zu Führungswechsel im markierten Monat")
        text = er.explanation_text(TEXT_CASES[4], WINDOW)
        assert "ohne erkennbaren Arbeitgeberbezug" in text and "3 Monate vor dem Übergang" in text and "eine Stufe zurückgestuft" in text
        assert "kein Wortbezug" not in text

    def test_after_and_without_terms(self):
        assert "2 Meldungen im Monat nach dem markierten Monat; kein Wortbezug zu den Bewertungen." in er.explanation_text(TEXT_CASES[5], WINDOW)
        assert "ohne Datum im Fenster" in er.explanation_text(TEXT_CASES[6], WINDOW)

    @pytest.mark.parametrize("month, kind, expected", [
        ("2023-02-10", "niveauwechsel", "im Monat vor dem Übergang"),
        ("2023-03-10", "niveauwechsel", "im Übergang (März 2023)"),
        ("2023-01-10", "niveauwechsel", "2 Monate vor dem Übergang"),
        ("2023-02-10", "auswahl", "im Monat vor der Auswahl"),
        ("2023-03-10", "auswahl", "in der Auswahl"),
        ("2023-05-10", "auswahl", "im Monat nach der Auswahl"),
        ("2023-03-10", "einzelmonat", "im Monat vor dem auffälligen Monat"),
        ("2023-04-10", "einzelmonat", "im auffälligen Monat"),
        ("2023-02-10", "vergleich", "im Monat vor dem Übergang"),
    ])
    def test_time_phrase(self, month, kind, expected):
        window = {"auswahl": SELECTION, "einzelmonat": OUTLIER}.get(kind, WINDOW)
        assert er.time_phrase(month, window, kind) == expected

    @pytest.mark.parametrize("bundle", TEXT_CASES)
    @pytest.mark.parametrize("kind", ["niveauwechsel", "auswahl", "einzelmonat", "vergleich"])
    def test_no_causal_words(self, bundle, kind):
        """Test: kein Baustein enthält Ursache, Auslöser, Grund, weil, führte oder Verwandtes."""
        window = {"auswahl": SELECTION, "einzelmonat": OUTLIER}.get(kind, WINDOW)
        text = er.explanation_text(bundle, window, kind)
        assert not FORBIDDEN.search(text), text
        assert text.startswith("Möglicher Zusammenhang:") and text.endswith(".")

    def test_fixed_notes(self):
        """Test: der feste Hinweis hat den vorgegebenen Wortlaut (er verneint Ursachen, statt sie zu behaupten);
        die Stufenregeln kommen ohne Ursache-Wörter aus."""
        assert er.EXPLANATION_NOTE == "Die Einstufung beruht auf Titeln und Wortbezügen. Sie zeigt mögliche Zusammenhänge, keine Ursachen."
        assert "interne auslöser sind von außen nicht sichtbar" in er.OPEN_NOTE.lower() and "offen" in er.OPEN_NOTE
        for text in er.rules()["stages"].values():
            assert not FORBIDDEN.search(text), text


# ═══════════════════════════════════════════════════════════════════════════════
# 5. Stimmung und Rangfolge
# ═══════════════════════════════════════════════════════════════════════════════

class TestSentiment:

    def test_fits_direction(self):
        neg = StubAnalyzer("negative", -0.6)
        assert er.title_sentiment("Titel", neg, "fall") == {"label": "negative", "polarity": -0.6, "fits_direction": True}
        assert er.title_sentiment("Titel", neg, "rise")["fits_direction"] is False
        assert er.title_sentiment("Titel", neg, None)["fits_direction"] is None
        assert er.title_sentiment("Titel", StubAnalyzer("neutral", 0.0), "fall")["fits_direction"] is None
        assert er.title_sentiment("Titel", None, "fall") is None and er.title_sentiment("", neg, "fall") is None

    def test_cache_and_errors(self):
        cache = {}
        a = StubAnalyzer()
        er.title_sentiment("Titel", a, "fall", cache)
        er.title_sentiment("Titel", a, "fall", cache)
        assert len(a.calls) == 1

        class Broken:
            def analyze_sentiment(self, text, star_rating=None):
                raise RuntimeError("kaputt")
        assert er.title_sentiment("Titel", Broken(), "fall") is None


class TestRankEvidence:

    def _reviews(self, n, text, start):
        return [{"id": start + i, "datum": "2023-04-10", "schlecht_am_arbeitgeber_finde_ich": text} for i in range(n)]

    @pytest.fixture
    def context(self):
        before = self._reviews(20, "Alles ruhig im Büro", 1)
        after = self._reviews(12, "Der Stellenabbau drückt die Stimmung", 100) + self._reviews(8, "Alles ruhig im Büro", 200)
        terms = distinctive_terms(before, after, exclude={"beispielwerk"})
        topics = er.topic_shift_table(before, after, "employee")
        items = [
            item("Beispielwerk kündigt Stellenabbau in der Verwaltung an", "2023-02-10", publisher="A"),
            item("Beispielwerk kündigt Stellenabbau an", "2023-02-11", publisher="B"),
            item("Beispielwerk: Stellenabbau in der Verwaltung angekündigt", "2023-02-12", source_type="adhoc", publisher="EQS News", category="Ad-hoc"),
            item("Aktie von Beispielwerk erreicht Kursziel", "2023-02-15", publisher="C"),
            item("Beispielwerk gewinnt Pokalspiel", "2023-04-02", publisher="D"),
            item("Neuer Chef bei Beispielwerk", "2022-12-05", publisher="E"),
            item("Beispielwerk eröffnet Kantine", "2023-05-20", publisher="F"),
        ]
        items.append(ev.global_event_items([{"id": "g", "date_from": "2023-01", "date_to": "2023-03", "title": "Allgemeines", "scope": "x",
                                             "note": "n", "url": "https://g", "confirmed": True}], WINDOW)[0])
        return {"items": items, "terms": terms, "topics": topics}

    def test_ranking_shape_and_order(self, context):
        result = er.rank_evidence(context["items"], WINDOW, terms=context["terms"], topics=context["topics"], direction="fall",
                                  exclude={"beispielwerk"}, categories=CATS, analyzer=StubAnalyzer())
        assert result["state"] == "ansaetze" and result["n_items"] == 7, "allgemeines Ereignis bleibt außen vor"
        assert set(result) >= {"state", "explanations", "n_items", "n_bundles", "n_by_stage", "item_scores", "terms", "note", "rules"}
        top = result["explanations"][0]
        assert top["confidence"] == "hoch" and top["n_items"] == 3 and top["source_type"] == "adhoc"
        assert top["publishers"] == ["EQS News", "A", "B"] and top["rank"] == 1
        assert [t["term"] for t in top["terms"]] == ["stellenabbau"] and top["terms"][0]["after"] == 12 and top["terms"][0]["before"] == 0
        assert top["category"]["id"] == "personalabbau" and top["category"]["match"] == 1.0
        assert top["category"]["shifted_topics"][0]["topic"] == "Arbeitsatmosphäre"
        assert top["sentiment"] == {"label": "negative", "polarity": -0.6, "fits_direction": True}
        assert top["text"].startswith("Möglicher Zusammenhang: 3 Meldungen (darunter eine Ad-hoc-Mitteilung) zu Personalabbau")
        assert len(top["items"]) == 3 and {"id", "title", "stage", "time_match"} <= set(top["items"][0])
        assert top["items"][0]["source_type"] == "adhoc", "Stellvertreter zuerst"
        stages = [e["confidence"] for e in result["explanations"]]
        assert stages == sorted(stages, key=lambda s: er.STAGES.index(s))
        assert all(e["confidence"] != "keine" for e in result["explanations"]) and len(result["explanations"]) <= 5
        assert result["n_by_stage"]["keine"] >= 2, "Kursziel und Pokalspiel"
        assert len(result["item_scores"]) == 7 and result["item_scores"][top["id"]]["rank"] == 1
        assert result["item_scores"][top["id"]]["category"] == "personalabbau"
        assert result["open_note"] is None

    def test_sentiment_does_not_change_stage(self, context):
        a = er.rank_evidence(context["items"], WINDOW, terms=context["terms"], topics=context["topics"], direction="fall",
                             exclude={"beispielwerk"}, categories=CATS, analyzer=StubAnalyzer("positive", 0.9))
        b = er.rank_evidence(context["items"], WINDOW, terms=context["terms"], topics=context["topics"], direction="fall",
                             exclude={"beispielwerk"}, categories=CATS, analyzer=None)
        assert [e["confidence"] for e in a["explanations"]] == [e["confidence"] for e in b["explanations"]]
        assert a["explanations"][0]["sentiment"]["fits_direction"] is False and b["explanations"][0]["sentiment"] is None

    def test_open_state_without_topic_match(self):
        items = [item("Aktie erreicht Kursziel", "2023-02-10"), item("Pokalsieg im Elfmeterschießen", "2023-03-10"),
                 item("Heute scheint die Sonne", "2023-04-10")]
        result = er.rank_evidence(items, WINDOW, terms=[], topics=[], categories=CATS)
        assert result["state"] == "offen" and result["explanations"] == [] and result["n_bundles"] == 3
        assert result["open_note"] and "offen" in result["open_note"]
        assert all(s["stage"] == "keine" for s in result["item_scores"].values())

    def test_max_explanations(self):
        items = [item(f"Streik Nummer {i} legt Werk lahm", f"2023-01-{1 + 5 * i:02d}") for i in range(0, 6)]   # je 5 Tage Abstand: kein Bündel
        result = er.rank_evidence(items, WINDOW, terms=[], topics=[], categories=CATS, max_explanations=5)
        assert len(result["explanations"]) == 5 and result["n_bundles"] == 6
        assert er.rank_evidence(items, WINDOW, terms=[], topics=[], categories=CATS, max_explanations=2)["n_bundles"] == 6

    def test_topic_shift_table_matches_compare_windows_rules(self):
        before = self._reviews(20, "Das Gehalt ist in Ordnung", 1)
        after = self._reviews(10, "Die Kommunikation fehlt", 100) + self._reviews(10, "Alles gut", 200)
        table = er.topic_shift_table(before, after, "employee")
        komm = next(t for t in table if t["topic"] == "Kommunikation")
        gehalt = next(t for t in table if t["topic"] == "Gehalt & Sozialleistungen")
        assert komm["share_shift_pp"] == 50.0 and komm["low_basis"] is False
        assert gehalt["share_shift_pp"] == -100.0 and gehalt["before"]["mentions"] == 20
        assert table[0]["topic"] == "Gehalt & Sozialleistungen", "sortiert nach Betrag der Verschiebung"
        small = er.topic_shift_table(before[:5], after[:5], "employee")
        assert all(t["low_basis"] for t in small)
