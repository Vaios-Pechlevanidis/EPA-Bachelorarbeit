"""
Erklärungsansätze: Rangfolge der Belege (Zyklus 2, Inkrement 5, A3).

Ein **Erklärungsansatz** ist ein möglicher Zusammenhang zwischen einer
auffälligen Veränderung und einem extern belegten Ereignis, begründet durch
zeitliche und thematische Korrespondenz. Er ist nie eine Ursache; jede Stufe
nennt, worauf sie beruht. Befund aus Inkrement 4 (E18): fast jedes Fenster hat
Belege, die zeitliche Nähe allein unterscheidet nicht. Die Aussagekraft muss
aus der thematischen Korrespondenz kommen; es liegen nur Titel vor.

Signale je Beleg (0 bis 1, aus Titel und Bewertungen):

- ``term_match``: kennzeichnende Begriffe der Bewertungen (``review_terms``,
  A1), die im Titel stehen. Jeder Begriff zählt ``TERM_MATCH_PER_TERM``, ein
  starker Begriff (mindestens ``TERM_STRONG_MIN_AFTER`` Bewertungen danach,
  Anteil mindestens ``TERM_STRONG_MIN_RATIO``-fach und mindestens
  ``TERM_STRONG_MIN_SHIFT`` über dem Anteil davor) ``TERM_MATCH_STRONG``;
  Summe höchstens 1.
- ``category_match``: Ereignisart mit Arbeitgeberbezug aus dem Titel
  (``event_categories``, A2). ``CATEGORY_MATCH_WITH_SHIFT`` (1), wenn sich ein
  zugeordnetes Thema im Vorher-Nachher-Vergleich um mindestens
  ``TOPIC_SHIFT_MIN_PP`` Prozentpunkte verschoben hat und keine kleine Basis
  vorliegt; ``CATEGORY_MATCH_ONLY`` (0,5), wenn nur die Ereignisart erkannt
  wird; sonst 0. Die Gruppe ohne Arbeitgeberbezug gibt 0 und stuft zurück.
- ``time_match``: ``TIME_NEAR`` (1) im Monat vor dem Übergang und im Übergang
  bis zum markierten Monat, davor linear abnehmend zum Rand des Fensters
  (``1 − Abstand / window_before``), nach dem markierten Monat
  ``TIME_AFTER_FACTOR`` (0,5) und weiter abnehmend.

``topic_match`` ist das Maximum aus ``term_match`` und ``category_match``.

Stufen (feste Regeln, keine gewichtete Summe):

- **hoch**: ``topic_match ≥ TOPIC_STRONG`` und ``time_match ≥ TIME_NEAR``
- **mittel**: ``topic_match ≥ TOPIC_STRONG`` und ``time_match ≥ TIME_MID``,
  oder ``topic_match ≥ TOPIC_WEAK`` und ``time_match ≥ TIME_NEAR``
- **niedrig**: ``topic_match ≥ TOPIC_WEAK`` und ``time_match ≥ TIME_MIN``
- **keine**: sonst (insbesondere ohne thematische Korrespondenz)
- Gruppe ohne Arbeitgeberbezug (Börsenbericht, Kursziel, Sport, Produkt):
  eine Stufe tiefer.

Bündelung: Meldungen zum selben Ereignis (gleiche Ereignisart, höchstens
``BUNDLE_MAX_DAYS`` Tage Abstand, Titelähnlichkeit mindestens
``BUNDLE_TITLE_SIMILARITY`` nach Jaccard über die Begriffe) werden ein
Eintrag mit Anzahl der Meldungen und Herausgebern. Stellvertreter ist die
Ad-hoc-Mitteilung, sonst die früheste Meldung; für das Bündel gelten die
höchsten Signale seiner Meldungen.

Sortierung: Stufe, dann Quellenart (Ad-hoc vor Meldung; die Quellenart
ordnet nur innerhalb einer Stufe), dann ``topic_match``, ``time_match``,
Anzahl der Meldungen, Datum. Höchstens ``MAX_EXPLANATIONS`` Einträge;
erreicht kein Bündel die Stufe niedrig, ist die Liste leer und der Zustand
``offen``. Zusätzlich, ohne Einfluss auf die Stufe: die Stimmung des Titels
über den ``SentimentAnalyzer`` und ob sie zur Richtung der Veränderung passt.

Alle Schwellen sind Setzungen (vorläufig). Alle Funktionen sind rein; nur
``title_sentiment`` ruft den übergebenen Analyzer.
"""

from __future__ import annotations

import re
from datetime import date as _date
from typing import Any, Dict, Iterable, List, Optional, Tuple

from services.event_categories import classify_title, load_event_categories
from services.evidence_service import KIND_CHANGE, KIND_OUTLIER, KIND_SELECTION, month_index
from services.evidence_sources import TYPE_ADHOC, TYPE_GLOBAL, TYPE_NEWS
from services.keyword_topic_service import topic_definitions_for, topics_in_review
from services.review_terms import COMPANY_PREFIX_MIN_LENGTH, match_terms, term_set

_TITLE_WORD_RE = re.compile(r"[a-zäöüß0-9&]+")

# ── Schwellen und Regeln (Setzungen, vorläufig; nur hier) ────────────────────

TERM_MATCH_PER_TERM = 0.5        # jeder kennzeichnende Begriff im Titel
TERM_MATCH_STRONG = 1.0          # ein starker Begriff zählt voll
TERM_STRONG_MIN_AFTER = 5        # starker Begriff: mindestens so viele Bewertungen danach ...
TERM_STRONG_MIN_RATIO = 3.0      # ... Anteil mindestens so vielfach wie davor (ohne Nennung davor: erfüllt) ...
TERM_STRONG_MIN_SHIFT = 0.05     # ... und Anteil danach mindestens so viel über dem Anteil davor (5 Prozentpunkte)

TOPIC_SHIFT_MIN_PP = 5.0         # merkliche Verschiebung eines Themas (Prozentpunkte, Betrag)
CATEGORY_MATCH_WITH_SHIFT = 1.0  # Ereignisart erkannt und zugeordnetes Thema verschoben
CATEGORY_MATCH_ONLY = 0.5        # nur Ereignisart erkannt

TIME_NEAR = 1.0                  # Monat vor dem Übergang und Übergang bis zum markierten Monat
TIME_AFTER_FACTOR = 0.5          # erster Monat nach dem markierten Monat

TOPIC_STRONG = 1.0               # Stufenregeln: thematische Korrespondenz stark
TOPIC_WEAK = 0.5                 # thematische Korrespondenz vorhanden
TIME_MID = 0.5                   # zeitliche Nähe mittel
TIME_MIN = 0.3                   # zeitliche Nähe mindestens (Rand eines Fensters von 3 Monaten: 0,33)

STAGE_HIGH, STAGE_MEDIUM, STAGE_LOW, STAGE_NONE = "hoch", "mittel", "niedrig", "keine"
STAGES = (STAGE_HIGH, STAGE_MEDIUM, STAGE_LOW, STAGE_NONE)
_STAGE_RANK = {s: i for i, s in enumerate(STAGES)}

BUNDLE_MAX_DAYS = 3              # Meldungen zum selben Ereignis liegen höchstens so viele Tage auseinander
BUNDLE_TITLE_SIMILARITY = 0.5    # Jaccard-Ähnlichkeit der Begriffe zweier Titel

MAX_EXPLANATIONS = 5
SOURCE_TYPE_ORDER = {TYPE_ADHOC: 0, TYPE_NEWS: 1}   # ordnet nur innerhalb einer Stufe
STATE_OPEN, STATE_FOUND = "offen", "ansaetze"

EXPLANATION_NOTE = ("Die Einstufung beruht auf Titeln und Wortbezügen. Sie zeigt mögliche Zusammenhänge, "
                    "keine Ursachen.")
OPEN_NOTE = ("Kein Beleg erreicht die Stufe niedrig: Keine Meldung im Ereignisfenster hat einen Wortbezug "
             "zu den Bewertungen oder eine erkannte Ereignisart mit Arbeitgeberbezug. Interne Auslöser sind "
             "von außen nicht sichtbar; die Veränderung bleibt offen.")



def rules() -> Dict[str, Any]:
    """Alle Schwellen und Stufenregeln, für Antworten und Berichte."""
    return {
        "term_match_per_term": TERM_MATCH_PER_TERM, "term_match_strong": TERM_MATCH_STRONG,
        "term_strong_min_after": TERM_STRONG_MIN_AFTER, "term_strong_min_ratio": TERM_STRONG_MIN_RATIO,
        "term_strong_min_shift": TERM_STRONG_MIN_SHIFT,
        "topic_shift_min_pp": TOPIC_SHIFT_MIN_PP, "category_match_with_shift": CATEGORY_MATCH_WITH_SHIFT,
        "category_match_only": CATEGORY_MATCH_ONLY, "time_near": TIME_NEAR, "time_after_factor": TIME_AFTER_FACTOR,
        "topic_strong": TOPIC_STRONG, "topic_weak": TOPIC_WEAK, "time_mid": TIME_MID, "time_min": TIME_MIN,
        "bundle_max_days": BUNDLE_MAX_DAYS, "bundle_title_similarity": BUNDLE_TITLE_SIMILARITY,
        "max_explanations": MAX_EXPLANATIONS,
        "stages": {
            STAGE_HIGH: f"topic_match >= {TOPIC_STRONG} und time_match >= {TIME_NEAR}",
            STAGE_MEDIUM: f"topic_match >= {TOPIC_STRONG} und time_match >= {TIME_MID}, oder topic_match >= {TOPIC_WEAK} und time_match >= {TIME_NEAR}",
            STAGE_LOW: f"topic_match >= {TOPIC_WEAK} und time_match >= {TIME_MIN}",
            STAGE_NONE: "sonst; Gruppe ohne Arbeitgeberbezug eine Stufe tiefer",
        },
    }


# ── Signale ──────────────────────────────────────────────────────────────────

def time_match(month: Optional[str], window: Dict[str, Any]) -> float:
    """Zeitliche Nähe eines Monats zum Anker des Fensters (``transition_from`` bis
    ``anchor_to``): 1 im Monat vor dem Übergang und im Übergang, davor linear abnehmend
    zum Fensterrand, nach dem markierten Monat ``TIME_AFTER_FACTOR`` und weiter abnehmend;
    0 außerhalb des Fensters oder ohne Monat."""
    if not month:
        return 0.0
    try:
        m = month_index(str(month)[:7])
    except ValueError:
        return 0.0
    start, end = month_index(window["from"]), month_index(window["to"])
    if m < start or m > end:
        return 0.0
    near_from = month_index(window["transition_from"]) - 1
    anchor_to = month_index(window["anchor_to"])
    if near_from <= m <= anchor_to:
        return TIME_NEAR
    if m < near_from:
        before = int(window.get("window_before") or (near_from + 1 - start))
        return round(max(0.0, TIME_NEAR - (near_from - m) / before), 2) if before > 0 else 0.0
    after = int(window.get("window_after") or (end - anchor_to))
    if after <= 0:
        return 0.0
    return round(max(0.0, TIME_AFTER_FACTOR * (1 - (m - anchor_to - 1) / after)), 2)


def is_strong_term(term: Dict[str, Any]) -> bool:
    ratio = term.get("ratio")
    shift = float(term.get("after_share") or 0.0) - float(term.get("before_share") or 0.0)
    return (int(term.get("after") or 0) >= TERM_STRONG_MIN_AFTER and (ratio is None or float(ratio) >= TERM_STRONG_MIN_RATIO)
            and shift >= TERM_STRONG_MIN_SHIFT)


def term_match(matched_terms: List[Dict[str, Any]]) -> float:
    """Summe der Begriffsgewichte (``TERM_MATCH_PER_TERM`` je Begriff, ``TERM_MATCH_STRONG``
    je starkem Begriff), höchstens 1."""
    total = sum(TERM_MATCH_STRONG if is_strong_term(t) else TERM_MATCH_PER_TERM for t in matched_terms)
    return round(min(1.0, total), 2)


def topic_shift_index(topics: Optional[Iterable[Dict[str, Any]]]) -> Dict[str, Dict[str, Any]]:
    """``{Thema: {"share_shift_pp", "low_basis"}}`` aus der Themenliste eines Vergleichs."""
    out: Dict[str, Dict[str, Any]] = {}
    for t in topics or []:
        if isinstance(t, dict) and t.get("topic"):
            out[t["topic"]] = {"share_shift_pp": t.get("share_shift_pp"), "low_basis": bool(t.get("low_basis"))}
    return out


def category_match(primary: Optional[Dict[str, Any]], shifts: Dict[str, Dict[str, Any]]) -> Tuple[float, List[Dict[str, Any]]]:
    """``(category_match, verschobene Themen)``: 1 mit merklicher Verschiebung eines
    zugeordneten Themas ohne kleine Basis, 0,5 nur mit erkannter Ereignisart, 0 ohne
    Ereignisart mit Arbeitgeberbezug."""
    if not primary or not primary.get("employer_related"):
        return 0.0, []
    shifted = []
    for topic in primary.get("topics") or []:
        s = shifts.get(topic)
        if not s or s.get("low_basis") or s.get("share_shift_pp") is None:
            continue
        if abs(float(s["share_shift_pp"])) >= TOPIC_SHIFT_MIN_PP:
            shifted.append({"topic": topic, "share_shift_pp": float(s["share_shift_pp"])})
    shifted.sort(key=lambda s: (-abs(s["share_shift_pp"]), s["topic"]))
    return (CATEGORY_MATCH_WITH_SHIFT, shifted) if shifted else (CATEGORY_MATCH_ONLY, [])


def stage_for(topic: float, time: float, employer_related: Optional[bool] = None) -> str:
    """Stufe aus ``topic_match`` und ``time_match`` nach festen Regeln; ``employer_related``
    False (Gruppe ohne Arbeitgeberbezug) eine Stufe tiefer."""
    if topic >= TOPIC_STRONG and time >= TIME_NEAR:
        stage = STAGE_HIGH
    elif (topic >= TOPIC_STRONG and time >= TIME_MID) or (topic >= TOPIC_WEAK and time >= TIME_NEAR):
        stage = STAGE_MEDIUM
    elif topic >= TOPIC_WEAK and time >= TIME_MIN:
        stage = STAGE_LOW
    else:
        stage = STAGE_NONE
    if employer_related is False and stage != STAGE_NONE:
        stage = STAGES[_STAGE_RANK[stage] + 1]
    return stage


def company_in_title(title: Any, company_words: Iterable[str]) -> Optional[bool]:
    """Nennt der Titel das Unternehmen? Ein Wort des Titels gleicht einem Wortteil des
    Namens oder beginnt mit einem Wortteil ab ``COMPANY_PREFIX_MIN_LENGTH`` Zeichen. None
    ohne Wortteile (dann nicht prüfbar). Nur Information, ohne Einfluss auf die Stufe."""
    words = [w for w in (company_words or ()) if w]
    if not words or not title or not isinstance(title, str):
        return None
    tokens = _TITLE_WORD_RE.findall(title.lower())
    prefixes = tuple(w for w in words if len(w) >= COMPANY_PREFIX_MIN_LENGTH)
    exact = set(words)
    return any(t in exact or (prefixes and t.startswith(prefixes)) for t in tokens)


def score_item(item: Dict[str, Any], window: Dict[str, Any], terms: List[Dict[str, Any]],
               shifts: Dict[str, Dict[str, Any]], categories: Optional[List[Dict[str, Any]]] = None,
               company_words: Iterable[str] = ()) -> Dict[str, Any]:
    """Signale, Begriffe, Ereignisart und Stufe eines Belegs (reine Funktion)."""
    title = item.get("title") or ""
    matched = match_terms(title, terms)
    classification = classify_title(title, categories, eqs_category=item.get("category"))
    primary = classification["primary"]
    cat_match, shifted = category_match(primary, shifts)
    t_match, tm = term_match(matched), time_match(item.get("date"), window)
    topic = max(t_match, cat_match)
    employer = primary["employer_related"] if primary else None
    category = None
    if primary:
        category = {"id": primary["id"], "label": primary["label"], "employer_related": primary["employer_related"],
                    "keywords": primary["keywords"], "topics": primary["topics"], "match": cat_match,
                    "shifted_topics": shifted}
    return {
        "id": item.get("id"), "date": item.get("date"), "title": title, "publisher": item.get("publisher"),
        "url": item.get("url"), "source": item.get("source"), "source_type": item.get("source_type"),
        "reliability": item.get("reliability"), "language": item.get("language"), "issuer": item.get("issuer"),
        "time_match": tm, "term_match": t_match, "category_match": cat_match, "topic_match": topic,
        "terms": [{"term": t["term"], "word": t["word"], "before": t["before"], "after": t["after"],
                   "n_before": t["n_before"], "n_after": t["n_after"], "strong": is_strong_term(t)} for t in matched],
        "category": category,
        "employer_related": employer,
        "company_in_title": company_in_title(title, company_words),
        "stage": stage_for(topic, tm, employer),
    }


# ── Bündelung ────────────────────────────────────────────────────────────────

def title_similarity(a: str, b: str, exclude: Iterable[str] = ()) -> float:
    """Jaccard-Ähnlichkeit der Begriffe zweier Titel (ohne Stoppwörter und ``exclude``)."""
    sa, sb = term_set(a, exclude), term_set(b, exclude)
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


def _day(value: Optional[str]) -> Optional[_date]:
    try:
        return _date.fromisoformat(str(value)[:10]) if value else None
    except ValueError:
        return None


def _days_apart(a: Optional[str], b: Optional[str]) -> Optional[int]:
    da, db = _day(a), _day(b)
    return abs((da - db).days) if da and db else None


def _category_key(scored: Dict[str, Any]) -> Optional[str]:
    return scored["category"]["id"] if scored.get("category") else None


def bundle_items(scored: List[Dict[str, Any]], exclude: Iterable[str] = ()) -> List[Dict[str, Any]]:
    """Meldungen zum selben Ereignis bündeln: gleiche Ereignisart, höchstens
    ``BUNDLE_MAX_DAYS`` Tage Abstand zur frühesten Meldung des Bündels und Titelähnlichkeit
    mindestens ``BUNDLE_TITLE_SIMILARITY`` zu ihr. Stellvertreter ist die Ad-hoc-Mitteilung,
    sonst die früheste Meldung; Signale, Begriffe und Themen des Bündels sind die höchsten
    bzw. vereinigten seiner Meldungen. Reine Funktion."""
    ordered = sorted(scored, key=lambda s: (str(s.get("date") or "9999"), SOURCE_TYPE_ORDER.get(s.get("source_type"), 9), str(s.get("id"))))
    excluded = set(exclude)
    bundles: List[Dict[str, Any]] = []
    for s in ordered:
        home = None
        for b in bundles:
            first = b["items"][0]
            if _category_key(first) != _category_key(s):
                continue
            apart = _days_apart(first.get("date"), s.get("date"))
            if apart is None or apart > BUNDLE_MAX_DAYS:
                continue
            if title_similarity(first["title"], s["title"], excluded) >= BUNDLE_TITLE_SIMILARITY:
                home = b
                break
        if home is None:
            bundles.append({"items": [s]})
        else:
            home["items"].append(s)
    return [_finish_bundle(b["items"]) for b in bundles]


def _finish_bundle(items: List[Dict[str, Any]]) -> Dict[str, Any]:
    representative = next((i for i in items if i.get("source_type") == TYPE_ADHOC), items[0])
    items = [representative] + [i for i in items if i is not representative]   # Stellvertreter zuerst, dann nach Datum
    tm = max(i["time_match"] for i in items)
    t_match = max(i["term_match"] for i in items)
    cat_match = max(i["category_match"] for i in items)
    topic = max(t_match, cat_match)
    # Begriffe aller Meldungen, je Begriff einmal; Reihenfolge: Stellvertreter zuerst.
    terms: Dict[str, Dict[str, Any]] = {}
    for i in items:
        for t in i["terms"]:
            terms.setdefault(t["term"], t)
    category = representative.get("category")
    if category is None:
        category = next((i["category"] for i in items if i.get("category")), None)
    employer = category["employer_related"] if category else None
    if category:
        category = {**category, "match": cat_match}
    publishers = list(dict.fromkeys(i.get("publisher") for i in items if i.get("publisher")))
    return {
        "representative": representative,
        "items": items,
        "n_items": len(items),
        "publishers": publishers,
        "date": representative.get("date"),
        "time_match": tm, "term_match": t_match, "category_match": cat_match, "topic_match": topic,
        "terms": list(terms.values()),
        "category": category,
        "employer_related": employer,
        "stage": stage_for(topic, tm, employer),
        "source_type": representative.get("source_type"),
        "has_adhoc": any(i.get("source_type") == TYPE_ADHOC for i in items),
        "company_in_title": representative.get("company_in_title"),
    }


def sort_key(bundle: Dict[str, Any]) -> Tuple:
    """Stufe, dann Quellenart (nur innerhalb der Stufe), dann Signale, Größe und Datum."""
    return (
        _STAGE_RANK[bundle["stage"]],
        SOURCE_TYPE_ORDER.get(bundle.get("source_type"), 9),
        -bundle["topic_match"], -bundle["time_match"], -bundle["n_items"],
        str(bundle.get("date") or "9999"),
    )


# ── Textbausteine ────────────────────────────────────────────────────────────

_MONTHS_DE = ["Jan.", "Feb.", "März", "Apr.", "Mai", "Juni", "Juli", "Aug.", "Sep.", "Okt.", "Nov.", "Dez."]


def fmt_month(period: str) -> str:
    return f"{_MONTHS_DE[int(period[5:7]) - 1]} {period[:4]}"


def time_phrase(month: Optional[str], window: Dict[str, Any], kind: Optional[str] = None) -> str:
    """Lage eines Monats zum Anker in Worten, je Art des Fensters."""
    kind = kind or window.get("kind") or KIND_CHANGE
    if kind == KIND_SELECTION:
        anchor, before_word, inside = "der Auswahl", "vor der Auswahl", "in der Auswahl"
    elif kind == KIND_OUTLIER:
        anchor, before_word, inside = "dem auffälligen Monat", "vor dem auffälligen Monat", "im auffälligen Monat"
    else:
        anchor, before_word, inside = "dem markierten Monat", "vor dem Übergang", "im Übergang"
    if not month:
        return "ohne Datum im Fenster"
    m = month_index(str(month)[:7])
    near_from = month_index(window["transition_from"]) - 1
    anchor_from, anchor_to = month_index(window["anchor_from"]), month_index(window["anchor_to"])
    if m == near_from:
        return f"im Monat {before_word}"
    if m < near_from:
        d = near_from - m + 1
        return f"{d} Monate {before_word}"
    if m <= anchor_to:
        if kind in (KIND_SELECTION, KIND_OUTLIER):
            return inside
        if m >= anchor_from:
            return "im markierten Monat"
        return f"{inside} ({fmt_month(str(month)[:7])})"
    d = m - anchor_to
    return f"im Monat nach {anchor}" if d == 1 else f"{d} Monate nach {anchor}"


def _count_phrase(bundle: Dict[str, Any]) -> str:
    n, adhoc = bundle["n_items"], bundle.get("has_adhoc")
    if n == 1:
        return "eine Ad-hoc-Mitteilung" if bundle.get("source_type") == TYPE_ADHOC else "eine Meldung"
    return f"{n} Meldungen" + (" (darunter eine Ad-hoc-Mitteilung)" if adhoc else "")


def _term_phrase(terms: List[Dict[str, Any]], kind: str) -> str:
    if not terms:
        return ""
    where = "in den Bewertungen der Auswahl" if kind == KIND_SELECTION else "in den Bewertungen danach"
    if len(terms) == 1:
        t = terms[0]
        return f"; {where} wird '{t['term']}' häufiger genannt ({t['after']} gegenüber {t['before']} Bewertungen)"
    names = ", ".join(f"'{t['term']}'" for t in terms[:-1]) + f" und '{terms[-1]['term']}'"
    counts = ", ".join(f"{t['term']}: {t['after']} gegenüber {t['before']}" for t in terms)
    return f"; {where} werden {names} häufiger genannt ({counts} Bewertungen)"


def _category_phrase(category: Optional[Dict[str, Any]]) -> str:
    if not category or not category.get("employer_related"):
        return ""
    shifted = category.get("shifted_topics") or []
    if shifted:
        parts = ", ".join(f"{s['topic']} um {s['share_shift_pp']:+.1f}".replace(".", ",") for s in shifted)
        word = "verschiebt sich das zugeordnete Thema" if len(shifted) == 1 else "verschieben sich die zugeordneten Themen"
        return f"; im Vergleich {word} {parts} Prozentpunkte"
    return "; die Ereignisart ist aus dem Titel erkannt, ein zugeordnetes Thema verschiebt sich nicht merklich"


def explanation_text(bundle: Dict[str, Any], window: Dict[str, Any], kind: Optional[str] = None) -> str:
    """Begründung in Klartext: Anzahl der Meldungen, Ereignisart, Lage im Fenster, Begriffe
    mit Zählungen, Themenverschiebung; ohne Wörter, die eine Ursache behaupten."""
    kind = kind or window.get("kind") or KIND_CHANGE
    category = bundle.get("category")
    when = time_phrase(bundle.get("date"), window, kind)
    head = f"Möglicher Zusammenhang: {_count_phrase(bundle)}"
    if category and category.get("employer_related"):
        head += f" zu {category['label']}"
    elif category:
        head += " ohne erkennbaren Arbeitgeberbezug (Börsenbericht, Kursziel, Sport oder Produkt)"
    text = head + f" {when}" + _term_phrase(bundle.get("terms") or [], kind) + _category_phrase(category)
    if category and not category.get("employer_related"):
        text += "; eine Stufe zurückgestuft"
    if not bundle.get("terms") and not (category and category.get("employer_related")):
        text += "; kein Wortbezug zu den Bewertungen"
    return text + "."


# ── Stimmung des Titels (ohne Einfluss auf die Stufe) ────────────────────────

def title_sentiment(title: str, analyzer, direction: Optional[str], cache: Optional[Dict[str, Dict[str, Any]]] = None) -> Optional[Dict[str, Any]]:
    """Stimmung eines Titels über ``analyzer.analyze_sentiment`` und ob sie zur Richtung
    passt (``fall`` ↔ negativ, ``rise`` ↔ positiv; neutral oder ohne Richtung: None).
    None ohne Analyzer. Wirft nicht."""
    if analyzer is None or not title:
        return None
    if cache is not None and title in cache:
        raw = cache[title]
    else:
        try:
            result = analyzer.analyze_sentiment(title, None)
            raw = {"label": result.get("sentiment", "neutral"), "polarity": round(float(result.get("polarity", 0.0)), 3)}
        except Exception:  # noqa: BLE001 – die Stimmung ist Beiwerk, ein Fehler darf die Antwort nicht verhindern
            return None
        if cache is not None:
            cache[title] = raw
    fits = None
    if direction in ("fall", "rise") and raw["label"] in ("positive", "negative"):
        fits = (direction == "fall") == (raw["label"] == "negative")
    return {**raw, "fits_direction": fits}


# ── Rangfolge ────────────────────────────────────────────────────────────────

def _entry(bundle: Dict[str, Any], window: Dict[str, Any], kind: str, analyzer, direction: Optional[str],
           cache: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    rep = bundle["representative"]
    item_fields = ("id", "date", "title", "publisher", "url", "source", "source_type", "reliability", "language", "issuer",
                   "time_match", "term_match", "category_match", "topic_match", "stage", "company_in_title")
    return {
        "id": rep.get("id"),
        "confidence": bundle["stage"],
        "event": rep.get("title"),
        "date": rep.get("date"),
        "source": rep.get("publisher"),
        "url": rep.get("url"),
        "source_type": rep.get("source_type"),
        "reliability": rep.get("reliability"),
        "language": rep.get("language"),
        "issuer": rep.get("issuer"),
        "n_items": bundle["n_items"],
        "publishers": bundle["publishers"],
        "time_match": bundle["time_match"],
        "topic_match": bundle["topic_match"],
        "term_match": bundle["term_match"],
        "terms": bundle["terms"],
        "category": bundle["category"],
        "time_phrase": time_phrase(rep.get("date"), window, kind),
        "company_in_title": bundle.get("company_in_title"),
        "sentiment": title_sentiment(rep.get("title") or "", analyzer, direction, cache),
        "text": explanation_text(bundle, window, kind),
        "items": [{k: i.get(k) for k in item_fields} for i in bundle["items"]],
    }


def rank_evidence(
    items: List[Dict[str, Any]],
    window: Dict[str, Any],
    *,
    terms: List[Dict[str, Any]],
    topics: Optional[Iterable[Dict[str, Any]]] = None,
    direction: Optional[str] = None,
    exclude: Iterable[str] = (),
    categories: Optional[List[Dict[str, Any]]] = None,
    analyzer=None,
    kind: Optional[str] = None,
    max_explanations: int = MAX_EXPLANATIONS,
) -> Dict[str, Any]:
    """Rangfolge der Belege eines Fensters als Erklärungsansätze.

    ``items``: Belege aus ``evidence_for_window`` (allgemeine Ereignisse, Typ ``global``,
    bleiben außen vor: Hypothesen nach E20). ``terms``: kennzeichnende Begriffe
    (``review_terms.distinctive_terms``). ``topics``: Themenliste des Vergleichs
    (``share_shift_pp``, ``low_basis``). ``direction``: ``fall`` oder ``rise`` für die
    Stimmung. ``exclude``: Wortteile des Unternehmensnamens (Titelähnlichkeit).
    ``analyzer``: ``SentimentAnalyzer`` oder None (dann keine Stimmung).

    Rückgabe ``{"state", "explanations", "n_items", "n_bundles", "n_by_stage",
    "item_scores", "terms", "note", "rules"}``: höchstens ``max_explanations`` Bündel mit
    Stufe mindestens niedrig; ``state`` ``offen`` ohne solches Bündel. ``item_scores``
    nennt je Beleg Stufe, Signale, Ereignisart und Rang (1 = oberster Beleg) für die
    Sortierung der Belegliste. Reine Funktion bis auf den Analyzer.
    """
    cats = load_event_categories() if categories is None else categories
    kind = kind or window.get("kind") or KIND_CHANGE
    shifts = topic_shift_index(topics)
    scored = [score_item(i, window, terms, shifts, cats, exclude) for i in items if i.get("source_type") != TYPE_GLOBAL]
    bundles = sorted(bundle_items(scored, exclude), key=sort_key)
    n_by_stage = {s: 0 for s in STAGES}
    for b in bundles:
        n_by_stage[b["stage"]] += 1
    cache: Dict[str, Dict[str, Any]] = {}
    top = [b for b in bundles if b["stage"] != STAGE_NONE][:max_explanations]
    explanations = [_entry(b, window, kind, analyzer, direction, cache) for b in top]
    for rank, e in enumerate(explanations, start=1):
        e["rank"] = rank
    item_scores: Dict[str, Dict[str, Any]] = {}
    rank = 0
    for b_index, b in enumerate(bundles):
        for i in b["items"]:
            rank += 1
            item_scores[str(i.get("id"))] = {
                "rank": rank, "stage": b["stage"], "bundle": b_index, "bundle_size": b["n_items"],
                "time_match": i["time_match"], "term_match": i["term_match"], "category_match": i["category_match"],
                "topic_match": i["topic_match"], "item_stage": i["stage"],
                "category": i["category"]["id"] if i.get("category") else None,
                "category_label": i["category"]["label"] if i.get("category") else None,
                "employer_related": i.get("employer_related"),
                "company_in_title": i.get("company_in_title"),
                "terms": [t["term"] for t in i["terms"]],
            }
    state = STATE_FOUND if explanations else STATE_OPEN
    return {
        "state": state,
        "explanations": explanations,
        "n_items": len(scored),
        "n_bundles": len(bundles),
        "n_by_stage": n_by_stage,
        "item_scores": item_scores,
        "terms": terms,
        "note": EXPLANATION_NOTE,
        "open_note": OPEN_NOTE if state == STATE_OPEN else None,
        "rules": rules(),
    }


# ── Themenverschiebung ohne Stimmung (für Auswertung und Tests) ──────────────

def topic_shift_table(before_rows: List[Dict[str, Any]], after_rows: List[Dict[str, Any]], source: str) -> List[Dict[str, Any]]:
    """Themenliste wie in ``compare_windows`` (``topic``, ``before``/``after`` mit ``mentions``
    und ``share``, ``share_shift_pp``, ``low_basis``), aber ohne Stimmung; dieselben
    Regeln für die kleine Basis (E12). Reine Funktion."""
    from services.explanation_service import LOW_BASIS_MIN_MENTIONS, LOW_BASIS_MIN_REVIEWS

    topics = list(topic_definitions_for(source).keys())
    counts = {"before": {t: 0 for t in topics}, "after": {t: 0 for t in topics}}
    sizes = {"before": len(before_rows), "after": len(after_rows)}
    for side, rows in (("before", before_rows), ("after", after_rows)):
        for row in rows:
            for t in topics_in_review(row, source):
                if t in counts[side]:
                    counts[side][t] += 1
    small = any(n < LOW_BASIS_MIN_REVIEWS for n in sizes.values())
    out = []
    for t in topics:
        b, a = counts["before"][t], counts["after"][t]
        b_share = round(b / sizes["before"], 4) if sizes["before"] else None
        a_share = round(a / sizes["after"], 4) if sizes["after"] else None
        shift = None if b_share is None or a_share is None else round((a_share - b_share) * 100, 2)
        out.append({"topic": t, "before": {"mentions": b, "share": b_share}, "after": {"mentions": a, "share": a_share},
                    "share_shift_pp": shift, "low_basis": small or (a + b < LOW_BASIS_MIN_MENTIONS)})
    out.sort(key=lambda e: (-abs(e["share_shift_pp"] or 0.0), e["topic"]))
    return out


__all__ = [
    "TERM_MATCH_PER_TERM", "TERM_MATCH_STRONG", "TERM_STRONG_MIN_AFTER", "TERM_STRONG_MIN_RATIO", "TERM_STRONG_MIN_SHIFT",
    "TOPIC_SHIFT_MIN_PP",
    "CATEGORY_MATCH_WITH_SHIFT", "CATEGORY_MATCH_ONLY", "TIME_NEAR", "TIME_AFTER_FACTOR", "TOPIC_STRONG", "TOPIC_WEAK",
    "TIME_MID", "TIME_MIN", "STAGE_HIGH", "STAGE_MEDIUM", "STAGE_LOW", "STAGE_NONE", "STAGES", "BUNDLE_MAX_DAYS",
    "BUNDLE_TITLE_SIMILARITY", "MAX_EXPLANATIONS", "SOURCE_TYPE_ORDER", "STATE_OPEN", "STATE_FOUND", "EXPLANATION_NOTE",
    "OPEN_NOTE", "rules", "time_match", "is_strong_term", "term_match", "topic_shift_index", "category_match", "stage_for",
    "company_in_title", "score_item", "title_similarity", "bundle_items", "sort_key", "fmt_month", "time_phrase", "explanation_text",
    "title_sentiment", "rank_evidence", "topic_shift_table",
]
