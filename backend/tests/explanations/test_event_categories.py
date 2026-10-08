"""
Tests für services/event_categories.py und backend/data/event_categories.json (Inkrement 5,
A2): Aufbau der Datei (Kennungen, Themen aus E10, Schlüsselwörter), Zuordnung
konstruierter Titel zu Ereignisarten (Wortanfang, Platzhalter, Vorrang des
Arbeitgeberbezugs, EQS-Kategorien), Laden fehlerhafter Dateien. Keine echten
Schlagzeilen (E7).

Ausführung:
    cd backend
    uv run python -m pytest tests/explanations/test_event_categories.py -q -p no:cacheprovider
"""

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))

import services.event_categories as ec  # noqa: E402


@pytest.fixture(scope="module")
def categories():
    return ec.load_event_categories(use_cache=False)


@pytest.fixture(scope="module")
def raw():
    with open(ec.EVENT_CATEGORIES_PATH, "r", encoding="utf-8") as fh:
        return json.load(fh)


class TestRepositoryFile:

    def test_twelve_employer_categories_and_one_group_without(self, categories):
        """Test: acht bis zwölf Ereignisarten mit Arbeitgeberbezug, genau eine Gruppe ohne."""
        employer = [c for c in categories if c["employer_related"]]
        other = [c for c in categories if not c["employer_related"]]
        assert 8 <= len(employer) <= 12 and len(employer) == 12
        assert [c["id"] for c in other] == [ec.NON_EMPLOYER_ID]
        assert len({c["id"] for c in categories}) == len(categories)

    def test_all_unconfirmed_before_phase_b(self, categories):
        """Test: Vorschläge des Entwicklers, alle unbestätigt (Bestätigung folgt in B1)."""
        assert all(c["confirmed"] is False for c in categories)

    def test_topics_are_e10_topics(self, raw, categories):
        """Test: jedes zugeordnete Thema ist ein Schlüsselwort-Thema aus E10; nichts geht beim Laden verloren."""
        known = ec.known_topics()
        for entry in raw["categories"]:
            assert all(t in known for t in entry["topics"]), entry["id"]
        loaded = {c["id"]: c["topics"] for c in categories}
        assert all(loaded[e["id"]] == e["topics"] for e in raw["categories"])
        assert all(c["topics"] for c in categories if c["employer_related"])
        assert next(c for c in categories if not c["employer_related"])["topics"] == []

    def test_keywords_lowercase_unique_both_languages(self, raw):
        """Test: Schlüsselwörter klein, nicht leer, ohne Doppelte, deutsch und englisch vorhanden."""
        for entry in raw["categories"]:
            for key in ("keywords_de", "keywords_en"):
                kws = entry[key]
                assert kws and all(k == k.lower() and k.strip() == k and k for k in kws), (entry["id"], key)
                assert len(set(kws)) == len(kws), (entry["id"], key)

    def test_group_without_employer_relation_has_eqs_categories(self, categories):
        other = next(c for c in categories if not c["employer_related"])
        assert "Directors' Dealings" in other["eqs_categories"] and "Voting rights" in other["eqs_categories"]
        assert all(c["eqs_categories"] == [] for c in categories if c["employer_related"])

    def test_hints_and_version(self, raw):
        assert raw["version"] == 1 and "regeln" in raw["hinweise"] and "felder" in raw["hinweise"]


class TestClassifyTitle:

    @pytest.mark.parametrize("title, expected, keyword", [
        ("Konzern streicht 500 Stellen in der Verwaltung", "personalabbau", "streicht 500 stellen"),
        ("Company announces layoffs at its main plant", "personalabbau", "layoff"),
        ("Neuer Chef für den Konzern berufen", "fuehrungswechsel", "neuer chef"),
        ("Streikwelle legt die Werke lahm", "tarif_streik", "streik"),
        ("Home-Office-Regelung wird geändert", "arbeitsmodell", "home office"),
        ("Konzern will 2000 Stellen abbauen", "personalabbau", "stellen abbauen"),
        ("Aktie steigt nach Anhebung des Kursziels", ec.NON_EMPLOYER_ID, "aktie"),
        ("Neue Tarife für Mobilfunkkunden vorgestellt", ec.NON_EMPLOYER_ID, "tarife"),
    ])
    def test_single_category(self, categories, title, expected, keyword):
        result = ec.classify_title(title, categories)
        assert result["primary"]["id"] == expected
        assert keyword in result["primary"]["keywords"]

    def test_employer_category_beats_group_without(self, categories):
        """Test: Börsenbericht über Stellenabbau zählt als Personalabbau; beide Treffer bleiben sichtbar."""
        result = ec.classify_title("Aktie fällt nach Ankündigung von Stellenabbau", categories)
        assert result["primary"]["id"] == "personalabbau" and result["primary"]["employer_related"] is True
        assert {m["id"] for m in result["matches"]} == {"personalabbau", ec.NON_EMPLOYER_ID}

    def test_most_hits_wins_tie_by_file_order(self, categories):
        """Test: die Ereignisart mit den meisten Schlüsselwörtern gilt; bei Gleichstand die erste."""
        two = ec.classify_title("Nach dem Streik folgt die Schlichtung im Tarifkonflikt, neuer Chef kommt", categories)
        assert two["primary"]["id"] == "tarif_streik" and len(two["primary"]["keywords"]) == 3
        tie = ec.classify_title("Streik und neuer Chef", categories)
        assert tie["primary"]["id"] == "fuehrungswechsel"   # steht vor tarif_streik in der Datei

    def test_no_match(self, categories):
        result = ec.classify_title("Heute scheint die Sonne über dem Werk", categories)
        assert result == {"primary": None, "matches": []}
        assert ec.classify_title("", categories)["primary"] is None and ec.classify_title(None, categories)["primary"] is None

    def test_eqs_category_without_employer_relation(self, categories):
        """Test: Stimmrechtsmitteilungen gehören ohne Blick auf den Titel zur Gruppe ohne Arbeitgeberbezug."""
        result = ec.classify_title("Mitteilung nach Paragraph 40 WpHG", categories, eqs_category="Voting rights")
        assert result["primary"]["id"] == ec.NON_EMPLOYER_ID
        assert result["primary"]["keywords"] == ["EQS: Voting rights"]

    def test_eqs_adhoc_with_employer_title_keeps_employer_category(self, categories):
        result = ec.classify_title("Vorstand beschließt Restrukturierung", categories, eqs_category="Ad-hoc")
        assert result["primary"]["id"] == "personalabbau"

    def test_wildcard_limited_to_three_words(self):
        pattern = ec.compile_keywords(["streicht * stellen"])
        assert pattern.search("firma streicht a b c stellen") is not None
        assert pattern.search("firma streicht a b c d stellen") is None
        assert pattern.search("firma streicht stellen") is not None

    def test_word_start_not_inside_word(self):
        pattern = ec.compile_keywords(["streik"])
        assert pattern.search("warnstreik") is None and pattern.search("der streik") is not None

    def test_category_by_id(self, categories):
        assert ec.category_by_id("verguetung", categories)["label"].startswith("Vergütung")
        assert ec.category_by_id("gibt_es_nicht", categories) is None


class TestLoading:

    def _write(self, tmp_path, categories):
        path = tmp_path / "ereignisarten.json"
        path.write_text(json.dumps({"version": 1, "categories": categories}), encoding="utf-8")
        return path

    def test_unknown_topic_dropped_duplicate_id_skipped_invalid_entries_ignored(self, tmp_path):
        base = {"label": "X", "employer_related": True, "keywords_de": ["streik"], "keywords_en": ["Strike", "strike"],
                "topics": ["Image", "Gibt es nicht"], "confirmed": False}
        path = self._write(tmp_path, [{"id": "a", **base}, {"id": "a", **base}, {"id": "b"}, "kein dict"])
        cats = ec.load_event_categories(path, use_cache=False)
        assert [c["id"] for c in cats] == ["a"]
        assert cats[0]["topics"] == ["Image"] and cats[0]["keywords_en"] == ["strike"], "nur klein geschriebene Schlüsselwörter"

    def test_missing_or_broken_file(self, tmp_path):
        assert ec.load_event_categories(tmp_path / "fehlt.json", use_cache=False) == []
        broken = tmp_path / "kaputt.json"
        broken.write_text("{", encoding="utf-8")
        assert ec.load_event_categories(broken, use_cache=False) == []

    def test_cache_per_path(self, tmp_path):
        path = self._write(tmp_path, [{"id": "a", "label": "A", "employer_related": True, "keywords_de": ["x"],
                                       "keywords_en": [], "topics": [], "confirmed": False}])
        first = ec.load_event_categories(path)
        assert ec.load_event_categories(path) is first
        ec.clear_cache()
        assert ec.load_event_categories(path) is not first
