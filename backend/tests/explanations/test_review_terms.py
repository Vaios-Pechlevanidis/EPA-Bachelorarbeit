"""
Tests für services/review_terms.py (Inkrement 5, A1): Normalisierung, Ausschluss von
Stoppwörtern, Bewertungswörtern und Unternehmensnamen, kennzeichnende Begriffe zweier
Fenster mit Mindestanzahl und Anteilsverhältnis, Treffer im Titel. Alle Bewertungen und
Titel sind konstruiert (keine echten Texte, E7).

Ausführung:
    cd backend
    uv run python -m pytest tests/explanations/test_review_terms.py -q -p no:cacheprovider
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))

import services.review_terms as rt  # noqa: E402


def _rows(n, text, start_id=1, field="schlecht_am_arbeitgeber_finde_ich"):
    return [{"id": start_id + i, "datum": "2023-01-15", field: text} for i in range(n)]


class TestTokens:

    def test_lowercase_umlauts_and_short_words(self):
        """Test: klein, Umlaute bleiben, Zahlen und Satzzeichen entfallen, kurze Wörter nicht."""
        assert rt.tokens("Kündigungen 2024: Büro zu, AG weg.") == ["kündigungen", "büro"]

    def test_stopwords_and_review_words_removed(self):
        """Test: Stoppwörter (de, en) und allgemeine Bewertungswörter zählen nicht."""
        assert rt.tokens("Der Arbeitgeber ist sehr gut und the team is nice") == ["nice"]

    def test_empty_and_non_string(self):
        assert rt.tokens("") == [] and rt.tokens(None) == [] and rt.tokens(42) == []

    def test_review_terms_over_topic_fields_with_html(self):
        """Test: Freitexte und Titel über die Themenfelder, HTML bereinigt, je Begriff einmal."""
        row = {"titel": "Stellenabbau angekündigt", "gut_am_arbeitgeber_finde_ich": "Homeoffice<br/>Homeoffice",
               "schlecht_am_arbeitgeber_finde_ich": None, "status": "Angestellt"}
        assert rt.review_terms(row) == {"stellenabbau", "angekündigt", "homeoffice"}
        assert rt.review_terms(row, exclude={"homeoffice"}) == {"stellenabbau", "angekündigt"}


class TestCompanyTerms:

    def test_name_search_term_and_joined_forms(self):
        """Test: Glieder des Suchbegriffs, Name ohne Rechtsform, zusammengezogene Form."""
        assert rt.company_terms("E.ON SE", '"E.ON" OR Eon') == {"eon"}
        terms = rt.company_terms("Universität Duisburg-Essen", '"Universität Duisburg-Essen" OR "Uni Duisburg-Essen"')
        assert terms == {"universität", "duisburg", "essen", "duisburgessen", "uni"}

    def test_empty(self):
        assert rt.company_terms(None) == set() and rt.company_terms("", "") == set()


class TestDistinctiveTerms:

    def test_term_only_after(self):
        """Test: Begriff in 4 Bewertungen danach, 0 davor → kennzeichnend, ratio None."""
        before = _rows(10, "Alles ruhig im Büro")
        after = _rows(4, "Der Stellenabbau macht Angst", start_id=100) + _rows(6, "Alles ruhig im Büro", start_id=200)
        terms = rt.distinctive_terms(before, after)
        assert [t["term"] for t in terms] == ["angst", "stellenabbau"]   # gleiche Verschiebung: alphabetisch
        top = terms[1]
        assert (top["before"], top["after"], top["n_before"], top["n_after"]) == (0, 4, 10, 10)
        assert top["after_share"] == 0.4 and top["before_share"] == 0.0 and top["ratio"] is None

    def test_minimum_reviews_after(self):
        """Test: weniger als 3 Bewertungen danach zählen nicht."""
        after = _rows(2, "Stellenabbau droht", start_id=100) + _rows(8, "Alles ruhig", start_id=200)
        assert rt.distinctive_terms(_rows(10, "Alles ruhig"), after) == []

    def test_share_ratio_with_different_window_sizes(self):
        """Test: Anteile, nicht Anzahlen: 2 von 20 davor (10 %) gegen 3 von 10 danach (30 %) → ratio 3."""
        before = _rows(2, "Die Umstrukturierung läuft") + _rows(18, "Alles ruhig", start_id=50)
        after = _rows(3, "Die Umstrukturierung läuft", start_id=100) + _rows(7, "Alles ruhig", start_id=200)
        terms = rt.distinctive_terms(before, after)
        assert [t["term"] for t in terms] == ["läuft", "umstrukturierung"]
        assert all(t["ratio"] == 3.0 and t["before"] == 2 and t["after"] == 3 for t in terms)

    def test_equal_shares_not_distinctive(self):
        """Test: gleicher Anteil davor und danach ist keine Verschiebung."""
        before = _rows(5, "Streik im Werk") + _rows(5, "Alles ruhig", start_id=50)
        after = _rows(5, "Streik im Werk", start_id=100) + _rows(5, "Alles ruhig", start_id=200)
        assert rt.distinctive_terms(before, after) == []

    def test_sorted_by_share_shift_and_capped(self):
        """Test: Sortierung nach Anteilsverschiebung, dann Anzahl, dann Begriff; Obergrenze."""
        after = (_rows(6, "Kündigung", start_id=100) + _rows(4, "Streik", start_id=200)
                 + _rows(4, "Abfindung", start_id=300) + _rows(3, "Umzug", start_id=400))
        terms = rt.distinctive_terms(_rows(10, "Alles ruhig"), after)
        assert [t["term"] for t in terms] == ["kündigung", "abfindung", "streik", "umzug"]
        assert [t["term"] for t in rt.distinctive_terms(_rows(10, "Alles ruhig"), after, max_terms=2)] == ["kündigung", "abfindung"]

    def test_company_name_and_stopwords_excluded(self):
        """Test: Unternehmensname und Stoppwörter werden nie kennzeichnend."""
        after = _rows(5, "Bei Beispielwerk ist der Chef neu", start_id=100)
        terms = rt.distinctive_terms(_rows(5, "Alles ruhig"), after, exclude=rt.company_terms("Beispielwerk GmbH"))
        assert [t["term"] for t in terms] == ["chef", "neu"]

    def test_empty_windows(self):
        assert rt.distinctive_terms([], []) == []
        assert rt.distinctive_terms([], _rows(3, "Streik im Werk")) and rt.distinctive_terms(_rows(3, "Streik"), []) == []

    def test_each_review_counts_once(self):
        """Test: eine Bewertung zählt je Begriff einmal, auch bei mehrfacher Nennung."""
        after = _rows(3, "Streik Streik Streik", start_id=100) + _rows(7, "Alles ruhig", start_id=200)
        assert rt.distinctive_terms(_rows(10, "Alles ruhig"), after)[0]["after"] == 3


class TestMatchTerms:

    TERMS = [{"term": "stellenabbau", "after": 5}, {"term": "entlassung", "after": 4}, {"term": "neu", "after": 3},
             {"term": "büro", "after": 3}]

    def test_exact_and_prefix_matches(self):
        """Test: gleiches Wort, Flexion und Kompositum ab 6 Zeichen; kurze Begriffe nur exakt."""
        matched = rt.match_terms("Konzern plant Stellenabbauprogramm und Entlassungen, Büro neuer", self.TERMS)
        assert [(m["term"], m["word"]) for m in matched] == [
            ("stellenabbau", "stellenabbauprogramm"), ("entlassung", "entlassungen"), ("büro", "büro")]

    def test_short_term_does_not_match_prefix(self):
        assert rt.match_terms("Neuer Standort", [{"term": "neu"}]) == []
        assert [m["term"] for m in rt.match_terms("Alles neu", [{"term": "neu"}])] == ["neu"]

    def test_title_word_as_prefix_of_term(self):
        """Test: auch ein kürzeres Wort des Titels trifft einen längeren Begriff (ab 6 Zeichen)."""
        assert [m["term"] for m in rt.match_terms("Kündigung angekündigt", [{"term": "kündigungen"}])] == ["kündigungen"]

    @pytest.mark.parametrize("title", ["", None, "   ", "AG SE"])
    def test_empty_title(self, title):
        assert rt.match_terms(title, self.TERMS) == []

    def test_no_terms(self):
        assert rt.match_terms("Stellenabbau", []) == []
