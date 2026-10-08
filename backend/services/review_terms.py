"""
Kennzeichnende Begriffe zweier Bewertungsfenster (Zyklus 2, Inkrement 5, A1).

Ein Erklärungsansatz (Inkrement 5) braucht neben der zeitlichen Nähe eine
thematische Korrespondenz zwischen einer Meldung und den Bewertungen. Dieses
Modul liefert dafür die **kennzeichnenden Begriffe**: Wörter, die in den
Bewertungen des Fensters danach deutlich häufiger vorkommen als in denen des
Fensters davor (Fenster nach E12, für die freie Auswahl nach E17), gezählt je
Bewertung (eine Bewertung zählt je Begriff einmal, egal wie oft sie ihn nennt).

Regeln (vorläufig, Setzungen; alle Schwellen stehen als Konstanten oben):

- Gezählt werden die Freitexte und der Titel einer Bewertung
  (``TERM_TEXT_FIELDS``), nicht die Jobbezeichnung (sie nennt Positionen wie
  „Student“ oder „Product“, keine Inhalte).
- Ein Begriff ist kennzeichnend, wenn ihn mindestens ``TERM_MIN_REVIEWS_AFTER``
  Bewertungen und mindestens der Anteil ``TERM_MIN_SHARE_AFTER`` der Bewertungen
  danach nennen und sein Anteil danach mindestens ``TERM_MIN_SHARE_RATIO``-mal
  so groß ist wie davor (ohne Nennung davor gilt das immer). Hat ein Fenster
  weniger als ``TERM_MIN_REVIEWS_PER_WINDOW`` Bewertungen (kleine Basis wie in
  E12), gibt es keine kennzeichnenden Begriffe. Höchstens ``TERM_MAX_COUNT``
  Begriffe je Vergleich, sortiert nach der Verschiebung des Anteils.
- Nicht gezählt werden Stoppwörter (deutsch und englisch), allgemeine
  Bewertungswörter (``REVIEW_WORDS``: Arbeitgeber, Mitarbeiter, gut, schlecht …)
  und die Wortteile des Unternehmensnamens (``company_terms``), auch als
  Wortanfang ab ``COMPANY_PREFIX_MIN_LENGTH`` Zeichen („deutschen“ bei
  „Deutsche Telekom“).
- Normalisierung: Kleinschreibung (``lower``, damit ``ß`` bleibt), Wörter aus
  Buchstaben (Umlaute bleiben, damit Begriff und Titel gleich geschrieben sind), mindestens
  ``MIN_TERM_LENGTH`` Zeichen. Zahlen und Satzzeichen entfallen.
- Ein Titel nennt einen Begriff, wenn ein Wort des Titels dem Begriff gleicht
  oder (ab ``TERM_PREFIX_MIN_LENGTH`` Zeichen des kürzeren Worts) eines das
  andere beginnt: ``entlassung`` trifft ``entlassungen``, ``stellenabbau``
  trifft ``stellenabbauprogramm``; ``neu`` trifft nicht ``neuer``.

Die Vorverarbeitung des LDA-Modells (``models/lda_topic_model.py``,
``preprocess_text``) wurde geprüft und nicht übernommen: Sie ist an eine
Instanz von ``LDATopicAnalyzer`` gebunden (gensim, Stoppwortlisten und
Bewertungskriterien aus der Datenbank beim Anlegen), ersetzt Abkürzungen und
faltet Umlaute (``ä`` → ``ae``), womit Begriffe aus Bewertungen nicht mehr mit
den Wörtern eines Titels übereinstimmen. Hier genügt eine einfache
Normalisierung ohne neue Abhängigkeit.

Alle Funktionen sind rein (kein Datei-, DB- oder Netzzugriff).
"""

from __future__ import annotations

import re
from collections import Counter
from typing import Any, Dict, Iterable, List, Optional, Set

from services.review_service import clean_html_text

MIN_TERM_LENGTH = 3            # kürzere Wörter zählen nicht
TERM_MIN_REVIEWS_AFTER = 3     # mindestens so viele Bewertungen mit dem Begriff danach
TERM_MIN_SHARE_AFTER = 0.03    # mindestens dieser Anteil der Bewertungen danach nennt den Begriff
TERM_MIN_SHARE_RATIO = 2.0     # Anteil danach mindestens so vielfach wie davor
TERM_MIN_REVIEWS_PER_WINDOW = 10   # kleine Basis (wie LOW_BASIS_MIN_REVIEWS, E12): keine Begriffe
TERM_MAX_COUNT = 50            # höchstens so viele kennzeichnende Begriffe je Vergleich
TERM_PREFIX_MIN_LENGTH = 6     # ab dieser Länge des kürzeren Worts zählt der Wortanfang als Treffer
COMPANY_PREFIX_MIN_LENGTH = 5  # Wortteil des Unternehmensnamens schließt ab dieser Länge auch Wortanfänge aus

# Freitexte und Titel je Quelle (ohne Jobbezeichnung und Stellenbeschreibung).
TERM_TEXT_FIELDS: Dict[str, List[str]] = {
    "employee": ["gut_am_arbeitgeber_finde_ich", "schlecht_am_arbeitgeber_finde_ich", "verbesserungsvorschlaege", "titel"],
    "candidates": ["verbesserungsvorschlaege", "titel"],
}
_ALL_TEXT_FIELDS = list(dict.fromkeys(f for fields in TERM_TEXT_FIELDS.values() for f in fields))

STOPWORDS_DE = frozenset("""
aber alle allem allen aller alles als also auch auf aus bei beim bin bis bist bzw da dabei dadurch dafür dagegen
daher damit dann daran darauf daraus darin darum das dass daß davon dazu dein deine deinem deinen deiner dem den
denen denn der deren des deshalb dessen dich die dies diese diesem diesen dieser dieses dir doch dort du durch ebenso
ein eine einem einen einer eines einige einigen einiger einmal er erst es etwa etwas euch euer eure für gegen gewesen
hab habe haben habt hat hatte hatten hattest hattet her hier hin hinter ich ihm ihn ihnen ihr ihre ihrem ihren ihrer
ihres im immer in indem ins ist ja je jede jedem jeden jeder jedes jedoch jene jenem jenen jener jenes jetzt kann kannst
kein keine keinem keinen keiner keines können könnt könnte könnten machen macht mal man manche manchem manchen mancher
manches mehr mein meine meinem meinen meiner meines mich mir mit muss musst müssen müsst nach nachdem nein nicht nichts
noch nun nur ob oder ohne sehr sein seine seinem seinen seiner seines selbst sich sie sind so solche solchem solchen
solcher solches soll sollen sollte sollten sollst sollt sondern sonst über um und uns unse unsem unsen unser unsere
unserem unseren unserer unseres unter viel viele vielen vieler vom von vor während war waren warst wart was weg weil
weiter weitere weiteren weiterer weiteres welche welchem welchen welcher welches wenn wer werde werden werdet wie wieder
will wir wird wirst wo wollen wollte wollten wurde wurden würde würden zu zum zur zwar zwischen eher einfach ganz gar
gern gerne gibt gab geben gegeben hatte halt kaum leider meist meistens nie oft schon sehr sowie teils teilweise trotz
trotzdem überhaupt vielleicht wenig weniger wenigstens wirklich ziemlich zumindest zusammen bereits beide beiden bzw
etc usw sowohl obwohl falls somit dennoch deswegen natürlich eigentlich allerdings zudem außerdem ebenfalls daneben
""".split())

STOPWORDS_EN = frozenset("""
a about above after again against all also am an and any are as at be because been before being below between both
but by can could did do does doing down during each few for from further had has have having he her here hers him
his how i if in into is it its itself just me more most my no nor not now of off on once only or other our ours out
over own same she should so some such than that the their theirs them then there these they this those through to too
under until up very was we were what when where which while who whom why will with would you your yours
""".split())

# Allgemeine Bewertungswörter: in fast jeder Bewertung, ohne thematische Aussage;
# dazu häufige Adjektive, Adverbien und Verben sowie englische Entsprechungen.
REVIEW_WORDS = frozenset("""
arbeitgeber arbeitgebers arbeitnehmer mitarbeiter mitarbeitern mitarbeiterin mitarbeiterinnen mitarbeitende
mitarbeitenden angestellte angestellten kollege kollegen kollegin kolleginnen unternehmen unternehmens firma firmen
konzern konzerns betrieb betriebs arbeit arbeiten arbeitet arbeitete gearbeitet job jobs stelle stellen tätig
gut gute guten guter gutes besser beste besten bestes schlecht schlechte schlechten schlechter schlechtes schlimm
toll tolle tollen toller super prima klasse okay nett nette netten netter angenehm angenehme angenehmen positiv
positive positiven negativ negative negativen bisschen bissl finde findet fand meinung ansicht empfehlen empfehlung
empfehlenswert verbesserungsvorschläge verbesserungsvorschlag verbesserung verbesserungen verbessern vorschlag
vorschläge bewertung bewertungen kununu sterne stern punkte fazit insgesamt generell grundsätzlich allgemein
bereich bereiche bereichen abteilung abteilungen team teams zeit zeiten jahr jahre jahren monat monate monaten tag
tage tagen woche wochen leute menschen mensch personen person dinge ding sache sachen weise art teil teile seite
seiten ende anfang beispiel beispiele thema themen punkt wert werte sinn möglichkeit möglichkeiten weg wege
deutsch deutsche deutschen deutscher deutsches deutschland neu neue neuen neuer neues alt alte alten alter top
bitte heute morgen gestern letzte letzten letzter letztes erste ersten erster nächste nächsten sehen sieht gesehen
geht ging gehen gegangen bringen bringt gebracht kommen kommt gekommen lassen lässt nehmen nimmt sagen sagt sagte
wissen weiß bekommen bekommt stehen steht liegen liegt bleiben bleibt machen macht gemacht tun tut getan halten
hält gehalten sollte sollten könnte könnten müsste müssten würde würden worden wurde wurden intern interne
internen interner extern externe externen wechseln manchmal möglich möglichst möglichkeit bessere besseres
besserer besseren hoch hohe hohen hoher höher niedrig niedrige groß große großen großer größer klein kleine kleinen
kleiner lang lange langen länger kurz kurze kurzen schnell schnelle schnellen langsam richtig richtige falsch
wichtig wichtige wichtigen eigentlich natürlich leider wirklich absolut echt total voll ziemlich relativ recht
interessant interessante interessanten interessanter ordnung oben unten nix fast sicher sicherlich spannend spannende
spannenden spannender besonders insbesondere sternen befriedigend ausreichend mangelhaft realität zumeist
employee employees employer company companies work working works worked job jobs team teams people colleagues
colleague staff good bad great nice best better worse worst really lot lots much many always never sometimes often
things thing way ways time times year years month months day days get got gets make made makes going come comes
came like well also even still new old big small high low top quite pretty very bit little
""".split())

STOPWORDS = STOPWORDS_DE | STOPWORDS_EN | REVIEW_WORDS

_TOKEN_RE = re.compile(r"[a-zäöüß]+")
_LEGAL_RE = re.compile(r"\b(SE|AG|GmbH|KGaA|KG|mbH|Co|Group|Holding|Deutschland|Inc|Ltd|plc)\b", re.IGNORECASE)


# ── Normalisierung ───────────────────────────────────────────────────────────

def tokens(text: Any) -> List[str]:
    """Wörter eines Texts: klein, nur Buchstaben (Umlaute bleiben), mindestens
    ``MIN_TERM_LENGTH`` Zeichen, ohne Stoppwörter und allgemeine Bewertungswörter;
    in Textreihenfolge, Doppelte bleiben."""
    if not text or not isinstance(text, str):
        return []
    return [t for t in _TOKEN_RE.findall(text.lower()) if len(t) >= MIN_TERM_LENGTH and t not in STOPWORDS]


def term_set(text: Any, exclude: Iterable[str] = ()) -> Set[str]:
    """Begriffe eines Texts als Menge, ohne die Wörter in ``exclude``."""
    excluded = set(exclude)
    return {t for t in tokens(text) if t not in excluded}


def _excluder(exclude: Iterable[str]):
    """Prüffunktion: Wort ausgeschlossen, wenn es in ``exclude`` steht oder mit einem
    Wortteil von mindestens ``COMPANY_PREFIX_MIN_LENGTH`` Zeichen daraus beginnt."""
    excluded = set(exclude)
    prefixes = tuple(e for e in excluded if len(e) >= COMPANY_PREFIX_MIN_LENGTH)
    return lambda t: t in excluded or (bool(prefixes) and t.startswith(prefixes))


def review_terms(row: Dict[str, Any], exclude: Iterable[str] = (), source: Optional[str] = None) -> Set[str]:
    """Begriffe einer Bewertung über Freitexte und Titel (``TERM_TEXT_FIELDS`` der Quelle;
    ohne Quelle alle Felder), HTML bereinigt; jede Bewertung zählt je Begriff einmal."""
    is_excluded = _excluder(exclude)
    found: Set[str] = set()
    for field in TERM_TEXT_FIELDS.get(source or "", _ALL_TEXT_FIELDS):
        value = row.get(field)
        if value and isinstance(value, str):
            found.update(t for t in tokens(clean_html_text(value)) if not is_excluded(t))
    return found


def company_terms(name: Optional[str], search_term: Optional[str] = None) -> Set[str]:
    """Wortteile des Unternehmensnamens und des Suchbegriffs (``OR``-Glieder ohne
    Anführungszeichen, Rechtsform entfernt), dazu jedes Wort ohne Trennzeichen
    (``E.ON`` → ``eon``, ``Duisburg-Essen`` → ``duisburgessen``); sie zählen nicht als
    kennzeichnende Begriffe."""
    parts: List[str] = []
    for raw in (name or "", search_term or ""):
        for part in re.split(r"\s+OR\s+", raw):
            part = _LEGAL_RE.sub(" ", part.strip().strip('"').strip())
            if part.strip():
                parts.append(part)
    out: Set[str] = set()
    for part in parts:
        for piece in part.split():
            words = _TOKEN_RE.findall(piece.lower())
            out.update(w for w in words if len(w) >= MIN_TERM_LENGTH)
            joined = "".join(words)
            if len(joined) >= MIN_TERM_LENGTH:
                out.add(joined)
    return out


# ── Kennzeichnende Begriffe ──────────────────────────────────────────────────

def _count_reviews(rows: Iterable[Dict[str, Any]], exclude: Iterable[str], source: Optional[str]) -> Counter:
    """Je Begriff die Anzahl der Bewertungen, die ihn nennen."""
    counts: Counter = Counter()
    for row in rows:
        counts.update(review_terms(row, exclude, source))
    return counts


def distinctive_terms(
    before_rows: List[Dict[str, Any]],
    after_rows: List[Dict[str, Any]],
    *,
    source: Optional[str] = None,
    exclude: Iterable[str] = (),
    min_after: int = TERM_MIN_REVIEWS_AFTER,
    min_share_after: float = TERM_MIN_SHARE_AFTER,
    min_ratio: float = TERM_MIN_SHARE_RATIO,
    min_reviews: int = TERM_MIN_REVIEWS_PER_WINDOW,
    max_terms: int = TERM_MAX_COUNT,
) -> List[Dict[str, Any]]:
    """Begriffe, die im Fenster danach deutlich häufiger genannt werden als davor.

    Je Begriff ``{"term", "before", "after", "n_before", "n_after", "before_share",
    "after_share", "ratio"}``: ``before``/``after`` sind Anzahlen von Bewertungen,
    ``ratio`` = Anteil danach / Anteil davor (None ohne Nennung davor). Sortiert nach
    der Verschiebung des Anteils (größte zuerst), dann nach ``after``, dann nach
    Begriff; höchstens ``max_terms``. Leere Fenster und Fenster mit weniger als
    ``min_reviews`` Bewertungen (kleine Basis) ergeben eine leere Liste. Reine Funktion.
    """
    n_before, n_after = len(before_rows), len(after_rows)
    if n_after == 0 or min(n_before, n_after) < min_reviews:
        return []
    before = _count_reviews(before_rows, exclude, source)
    after = _count_reviews(after_rows, exclude, source)
    out: List[Dict[str, Any]] = []
    for term, count_after in after.items():
        if count_after < min_after:
            continue
        count_before = before.get(term, 0)
        after_share = count_after / n_after
        before_share = (count_before / n_before) if n_before else 0.0
        if after_share < min_share_after:
            continue
        if before_share > 0 and after_share < min_ratio * before_share:
            continue
        out.append({
            "term": term,
            "before": count_before,
            "after": count_after,
            "n_before": n_before,
            "n_after": n_after,
            "before_share": round(before_share, 4),
            "after_share": round(after_share, 4),
            "ratio": round(after_share / before_share, 2) if before_share > 0 else None,
        })
    out.sort(key=lambda e: (-(e["after_share"] - e["before_share"]), -e["after"], e["term"]))
    return out[:max_terms]


# ── Treffer im Titel ─────────────────────────────────────────────────────────

def _word_matches(word: str, term: str) -> bool:
    if word == term:
        return True
    shorter = min(len(word), len(term))
    return shorter >= TERM_PREFIX_MIN_LENGTH and (word.startswith(term) or term.startswith(word))


def match_terms(title: Any, terms: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Die kennzeichnenden Begriffe (Einträge aus ``distinctive_terms``), die ein Titel
    nennt, in der Reihenfolge der Liste; je Treffer dazu ``word`` (das Wort des Titels).
    Gleiches Wort oder Wortanfang ab ``TERM_PREFIX_MIN_LENGTH`` Zeichen (Flexion,
    Komposita)."""
    if not title or not isinstance(title, str) or not terms:
        return []
    words = [w for w in _TOKEN_RE.findall(title.lower()) if len(w) >= MIN_TERM_LENGTH]
    if not words:
        return []
    matched: List[Dict[str, Any]] = []
    for entry in terms:
        term = entry["term"]
        word = next((w for w in words if _word_matches(w, term)), None)
        if word is not None:
            matched.append({**entry, "word": word})
    return matched


__all__ = [
    "MIN_TERM_LENGTH", "TERM_MIN_REVIEWS_AFTER", "TERM_MIN_SHARE_AFTER", "TERM_MIN_SHARE_RATIO", "TERM_MIN_REVIEWS_PER_WINDOW",
    "TERM_MAX_COUNT", "TERM_PREFIX_MIN_LENGTH", "COMPANY_PREFIX_MIN_LENGTH", "TERM_TEXT_FIELDS",
    "STOPWORDS_DE", "STOPWORDS_EN", "REVIEW_WORDS", "STOPWORDS",
    "tokens", "term_set", "review_terms", "company_terms", "distinctive_terms", "match_terms",
]
