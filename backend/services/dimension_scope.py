"""
Dimension als globaler Filter der Detailseite „Anomalien im Verlauf“ (2026-10-23, E34).

Die im Kopf der Seite gewählte Dimension (z. B. Gehalt/Sozialleistungen) gilt seit dem
2026-10-23 für alle Karten der Seite: für Monatsverlauf, Erkennung und Vergleich wie
bisher, neu auch für die Liste „Bewertungen des Zeitraums“ und die Belegliste
„Externe Berichte im Ereignisfenster“. Dieses Modul entscheidet, welche Bewertungen
und welche Belege zur Dimension gehören. Alle Funktionen sind rein (kein Datei-,
DB- oder Netzzugriff).

Bewertung (``review_dimension_info``): Eine Bewertung gehört zur Dimension, wenn sie

- einen **Kommentar zur Kategorie** der Dimension hat (Spalte mit dem Namen der
  Dimension, nur Mitarbeitende, ``CATEGORY_TEXT_FIELDS``; Platzhalter wie „-“ zählen
  nicht, ``has_text_content``) oder
- das **Schlüsselwort-Thema** der Dimension nennt (``topic_for_dimension``, E10) – in
  Titel, Freitexten und Kategorie-Kommentaren (``EXPLANATION_TOPIC_TEXT_FIELDS``, E23),
  dieselbe Regel wie Themen-Marken und Themenfilter der Liste (Doku 17).

Die Sternewertung der Dimension allein genügt nicht: Fast jede Bewertung bewertet jede
Kategorie (nur lesende Prüfung am 2026-10-23, Unternehmen 3: 445 von 446 Bewertungen
mit Sternen für Arbeitsatmosphäre, 219 mit Kommentar, 70 mit Thema), sie würde nichts
unterscheiden. Die Sterne der Dimension werden je Bewertung mitgeliefert.

Beleg (``evidence_dimension_match``): Eine Meldung gehört zur Dimension, wenn

- ihr **Titel ein Schlüsselwort** des Themas nennt – als ganzes Wort wie in den
  Bewertungen (``topic_spans``) oder als Wortanfang ab ``TERM_PREFIX_MIN_LENGTH``
  Zeichen nach der Regel der strengen Auswahl (E33, ``match_terms(compound_only=True)``:
  „Gehaltserhöhung“ zu „gehalt“; „lohn“ nur als ganzes Wort) – oder
- ihre **Ereignisart** (``classify_title``, E22, nur mit Arbeitgeberbezug) dem Thema
  zugeordnet ist (``event_categories.json``, Feld ``topics``: „Tarifverhandlung und
  Streik“ → Gehalt & Sozialleistungen).

Allgemeine Ereignisse (Konjunktur, Inflation; E29) haben keinen Bezug zu einer
Dimension und entfallen mit dem Filter. Keine Aussage über Ursachen.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from services.event_categories import classify_title
from services.evidence_sources import TYPE_ADHOC, TYPE_GLOBAL, TYPE_NEWS
from services.keyword_topic_service import (
    EXPLANATION_TOPIC_TEXT_FIELDS,
    topic_definitions_for,
    topic_for_dimension,
    topic_spans,
    topics_in_review,
)
from services.rating_series_service import OVERALL_DIMENSION, value_column
from services.review_service import CATEGORY_TEXT_FIELDS, clean_html_text, has_text_content
from services.review_terms import match_terms

SCOPE_VERSION = 1
SCOPE_DATE = "2026-10-23"

# Hinweistexte der Antworten (ohne Kürzel, sie stehen im Dashboard).
REVIEW_SCOPE_NOTE = (
    "Zur Dimension gehört eine Bewertung, wenn sie einen Kommentar zu dieser Kategorie hat "
    "oder ein Schlüsselwort ihres Themas nennt; die Sterne allein genügen nicht."
)
EVIDENCE_SCOPE_NOTE = (
    "Zur Dimension gehört eine Meldung, wenn ihr Titel ein Schlüsselwort des Themas nennt "
    "oder ihre Ereignisart dem Thema zugeordnet ist. Allgemeine Ereignisse entfallen."
)
NO_EVIDENCE_IN_DIMENSION = "Kein Beleg im Fenster gehört zur gewählten Dimension."

# Schlüsselwort-Muster der Form \bwort\b (nur Buchstaben): daraus wird der Begriff für den
# Wortanfang im Titel. Zusammengesetzte Muster (work[\s-]*life …) deckt topic_spans ab.
_PLAIN_KEYWORD_RE = re.compile(r"^\\b([a-zäöüß]+)\\b$")


def single_dimension_topic(source: str, dimension: Optional[str]) -> Optional[str]:
    """Thema einer Einzeldimension. ValueError ohne Dimension, für die Gesamtbewertung
    (sie hat kein Thema und filtert nichts) und bei ungültiger Quelle oder Dimension."""
    if dimension is None:
        raise ValueError("dimension_only braucht dimension.")
    if dimension == OVERALL_DIMENSION:
        raise ValueError("dimension_only braucht eine Einzeldimension, nicht die Gesamtbewertung.")
    return topic_for_dimension(source, dimension)


# ── Bewertungen ──────────────────────────────────────────────────────────────

def dimension_comment(row: Dict[str, Any], source: str, dimension: str) -> Optional[str]:
    """Bereinigter Kommentar zur Kategorie der Dimension (nur Mitarbeitende); None ohne Text."""
    if source != "employee" or dimension not in CATEGORY_TEXT_FIELDS:
        return None
    raw = row.get(dimension)
    if not has_text_content(raw):
        return None
    text = clean_html_text(raw)
    return text.strip() if has_text_content(text) else None


def review_dimension_info(
    row: Dict[str, Any], source: str, dimension: str, topic: Optional[str] = None, topics: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Bezug einer Bewertung zur Dimension: ``rating`` (Sterne der Dimension),
    ``comment`` (Kategorie-Kommentar oder None), ``mentions_topic`` und ``in_dimension``
    (Kommentar oder Thema). ``topic`` und ``topics`` können übergeben werden, wenn sie
    schon berechnet sind (Bewertungsliste). ValueError bei ungültiger Angabe."""
    column = value_column(source, dimension)
    if topic is None:
        topic = topic_for_dimension(source, dimension)
    if topics is None:
        topics = topics_in_review(row, source, EXPLANATION_TOPIC_TEXT_FIELDS)
    comment = dimension_comment(row, source, dimension)
    mentions = topic is not None and topic in topics
    return {
        "key": dimension,
        "rating": row.get(column),
        "comment": comment,
        "mentions_topic": mentions,
        "in_dimension": comment is not None or mentions,
    }


def mean_rating(infos: List[Dict[str, Any]]) -> Optional[float]:
    """Mittel der Sterne der Dimension über die Bewertungen (zwei Nachkommastellen); None ohne Werte."""
    values = []
    for info in infos:
        try:
            values.append(float(info["rating"]))
        except (TypeError, ValueError):
            continue
    return round(sum(values) / len(values), 2) if values else None


# ── Belege ───────────────────────────────────────────────────────────────────

def topic_title_terms(topic: str, source: Optional[str]) -> List[str]:
    """Einfache Schlüsselwörter des Themas (Muster ``\\bwort\\b``) als Begriffe für den
    Wortanfang im Titel; ohne Thema oder Muster leer."""
    definition = topic_definitions_for(source).get(topic) or {}
    terms: List[str] = []
    for pattern in definition.get("keywords", []):
        match = _PLAIN_KEYWORD_RE.match(pattern)
        if match and match.group(1) not in terms:
            terms.append(match.group(1))
    return terms


def evidence_dimension_match(
    item: Dict[str, Any], topic: Optional[str], source: Optional[str], categories: Optional[List[Dict[str, Any]]] = None,
) -> Optional[Dict[str, Any]]:
    """Bezug eines Belegs zur Dimension oder None: ``terms`` (getroffene Wörter des
    Titels, klein) und ``category`` (Bezeichnung der zugeordneten Ereignisart oder None).
    Allgemeine Ereignisse haben keinen Bezug."""
    title = item.get("title")
    if not topic or not title or not isinstance(title, str) or item.get("source_type") == TYPE_GLOBAL:
        return None
    words: List[str] = []
    for start, end in topic_spans(title, topic, source):
        word = title[start:end].lower()
        if word not in words:
            words.append(word)
    terms = [{"term": t} for t in topic_title_terms(topic, source)]
    for hit in match_terms(title, terms, compound_only=True):
        if hit["word"] not in words:
            words.append(hit["word"])
    primary = classify_title(title, categories, eqs_category=item.get("category"))["primary"]
    category = primary["label"] if primary and primary["employer_related"] and topic in primary["topics"] else None
    if not words and category is None:
        return None
    return {"terms": words, "category": category}


def scope_evidence(evidence: Dict[str, Any], source: str, dimension: Optional[str]) -> Dict[str, Any]:
    """Belegliste auf die Dimension eingeschränkt: ``items`` nur mit Bezug (je Beleg
    ``dimension_match``), ``total``, ``counts``, ``coverage`` und ``reason`` neu gerechnet,
    dazu ``scope`` mit Dimension, Thema und Zählung vor und nach dem Filter.
    ValueError wie ``single_dimension_topic``."""
    topic = single_dimension_topic(source, dimension)
    items = evidence.get("items") or []
    kept: List[Dict[str, Any]] = []
    for item in items:
        match = evidence_dimension_match(item, topic, source)
        if match is not None:
            kept.append({**item, "dimension_match": match})
    counts = {TYPE_NEWS: 0, TYPE_ADHOC: 0, TYPE_GLOBAL: 0}
    for item in kept:
        counts[item["source_type"]] = counts.get(item["source_type"], 0) + 1
    reason = evidence.get("reason")
    if items and not kept:
        reason = NO_EVIDENCE_IN_DIMENSION
    return {
        **evidence,
        "items": kept,
        "total": len(kept),
        "counts": counts,
        "coverage": counts[TYPE_NEWS] + counts[TYPE_ADHOC] > 0,
        "reason": reason,
        "scope": {
            "dimension": dimension,
            "topic": topic,
            "n_all": len(items),
            "n_dimension": len(kept),
            "note": EVIDENCE_SCOPE_NOTE,
        },
    }


__all__ = [
    "SCOPE_VERSION", "SCOPE_DATE", "REVIEW_SCOPE_NOTE", "EVIDENCE_SCOPE_NOTE", "NO_EVIDENCE_IN_DIMENSION",
    "single_dimension_topic", "dimension_comment", "review_dimension_info", "mean_rating",
    "topic_title_terms", "evidence_dimension_match", "scope_evidence",
]
