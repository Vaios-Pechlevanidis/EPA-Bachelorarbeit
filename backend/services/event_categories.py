"""
Ereignisarten mit Arbeitgeberbezug (Zyklus 2, Inkrement 5, A2).

Eine Meldung wird über Schlüsselwörter in ihrem Titel einer **Ereignisart**
zugeordnet (Personalabbau, Führungswechsel, Übernahme, Tarif und Streik,
Standort, …). Jede Ereignisart ist Themen aus E10 zugeordnet (Schlüsselwort-
Themen der Bewertungen, ``keyword_topic_service``); daraus entsteht in
Inkrement 5 das Signal ``category_match``. Eine eigene Gruppe **ohne
Arbeitgeberbezug** (Börsenbericht, Kursziel, Sport, Produkt) stuft Belege
zurück. Die Zuordnung ist ein Signal für die thematische Korrespondenz, keine
Aussage über Ursachen.

Datei: ``backend/data/event_categories.json`` (Kennung, Bezeichnung,
Schlüsselwörter deutsch und englisch, Themen, ``confirmed``). Regeln:

- Schlüsselwörter sind klein geschrieben und werden als **Wortanfang**
  gesucht (``streik`` trifft ``Streikwelle``); mehrere Wörter mit Leerzeichen,
  ``*`` steht für bis zu ``WILDCARD_MAX_WORDS`` beliebige Wörter dazwischen
  (``streicht * stellen`` trifft ``streicht 500 Stellen``). Bindestriche und
  Schrägstriche im Titel gelten als Leerzeichen.
- Trifft mindestens eine Ereignisart mit Arbeitgeberbezug, gilt die mit den
  meisten getroffenen Schlüsselwörtern (bei Gleichstand die erste in der
  Datei). Die Gruppe ohne Arbeitgeberbezug gilt nur, wenn keine Ereignisart
  mit Arbeitgeberbezug trifft; EQS-Mitteilungen ihrer ``eqs_categories``
  (Directors' Dealings, Stimmrechte, …) gehören ohne Blick auf den Titel dazu.
- Deutsche Wörter greifen bei englischen Titeln nicht und umgekehrt; deshalb
  beide Listen. Die Schlüsselwörter sind Setzungen (vorläufig, bis der Autor
  sie bestätigt).

Alle Funktionen außer dem Laden sind rein; das Laden liest nur die Datei.
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from services.keyword_topic_service import topic_definitions_for

logger = logging.getLogger(__name__)

BACKEND_DIR = Path(__file__).resolve().parent.parent
EVENT_CATEGORIES_PATH = BACKEND_DIR / "data" / "event_categories.json"
NON_EMPLOYER_ID = "ohne_arbeitgeberbezug"
WILDCARD_MAX_WORDS = 3

_FIELDS = ("id", "label", "employer_related", "keywords_de", "keywords_en", "topics", "confirmed")
_WORD_CHARS = "a-zäöüß0-9"
_SEPARATORS_RE = re.compile(r"[-–—/]+")
_SPACES_RE = re.compile(r"\s+")

_cache: Dict[str, List[Dict[str, Any]]] = {}


# ── Laden ────────────────────────────────────────────────────────────────────

def known_topics() -> set:
    """Alle Themen aus E10 (beide Quellen)."""
    return set(topic_definitions_for(None).keys())


def _valid_keywords(raw: Any) -> List[str]:
    if not isinstance(raw, list):
        return []
    out: List[str] = []
    for kw in raw:
        if isinstance(kw, str) and kw.strip() and kw == kw.lower():
            out.append(" ".join(kw.split()))
    return list(dict.fromkeys(out))


def load_event_categories(path: Optional[Path] = None, use_cache: bool = True) -> List[Dict[str, Any]]:
    """Ereignisarten aus ``event_categories.json`` in Dateireihenfolge, geprüft: alle Felder
    vorhanden, Kennung eindeutig, Schlüsselwörter klein geschrieben, Themen aus E10
    (unbekannte Themen werden mit Warnung weggelassen). Fehlende oder unlesbare Datei ergibt
    eine leere Liste. Je Eintrag zusätzlich ``pattern`` (kompiliert) und ``eqs_categories``."""
    path = Path(path or EVENT_CATEGORIES_PATH)
    key = str(path)
    if use_cache and key in _cache:
        return _cache[key]
    categories: List[Dict[str, Any]] = []
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as fh:
                doc = json.load(fh)
        except (OSError, ValueError) as exc:
            logger.warning("event_categories.json nicht lesbar: %s", exc)
            doc = {}
        topics_known = known_topics()
        seen: set = set()
        for raw in (doc.get("categories") if isinstance(doc, dict) else []) or []:
            if not isinstance(raw, dict) or any(k not in raw for k in _FIELDS) or not isinstance(raw["id"], str):
                continue
            if raw["id"] in seen:
                logger.warning("Ereignisart %r doppelt; zweiter Eintrag übergangen.", raw["id"])
                continue
            seen.add(raw["id"])
            topics = [t for t in (raw.get("topics") or []) if t in topics_known]
            unknown = [t for t in (raw.get("topics") or []) if t not in topics_known]
            if unknown:
                logger.warning("Ereignisart %r: unbekannte Themen %s weggelassen.", raw["id"], unknown)
            keywords_de, keywords_en = _valid_keywords(raw.get("keywords_de")), _valid_keywords(raw.get("keywords_en"))
            entry = {
                "id": raw["id"],
                "label": str(raw.get("label") or raw["id"]),
                "employer_related": raw.get("employer_related") is True,
                "keywords_de": keywords_de,
                "keywords_en": keywords_en,
                "topics": topics,
                "eqs_categories": [str(c) for c in (raw.get("eqs_categories") or []) if str(c).strip()],
                "confirmed": raw.get("confirmed") is True,
            }
            entry["pattern"] = compile_keywords(keywords_de + keywords_en)
            categories.append(entry)
    if use_cache:
        _cache[key] = categories
    return categories


def clear_cache() -> None:
    _cache.clear()


# ── Zuordnung ────────────────────────────────────────────────────────────────

def normalize_title(title: Any) -> str:
    """Titel für die Suche: klein (``lower``, damit ``ß`` bleibt), Bindestriche und
    Schrägstriche als Leerzeichen, Leerraum zusammengefasst, Umlaute bleiben."""
    if not title or not isinstance(title, str):
        return ""
    return _SPACES_RE.sub(" ", _SEPARATORS_RE.sub(" ", title.lower())).strip()


def _keyword_regex(keyword: str) -> str:
    parts = []
    for word in keyword.split():
        if word == "*":
            parts.append(rf"(?:[^\s]+\s+){{0,{WILDCARD_MAX_WORDS}}}")
        else:
            parts.append(re.escape(word) + r"\s+")
    body = "".join(parts)
    body = body[:-len(r"\s+")] if body.endswith(r"\s+") else body
    return body


def compile_keywords(keywords: List[str]) -> Optional[re.Pattern]:
    """Ein Muster für alle Schlüsselwörter einer Ereignisart: jedes als Wortanfang
    (``(?<![a-zäöüß0-9])``), ``*`` als bis zu ``WILDCARD_MAX_WORDS`` Wörter dazwischen. None
    ohne Schlüsselwörter. Die Gruppe ``kw`` liefert den getroffenen Text."""
    if not keywords:
        return None
    alternatives = "|".join(_keyword_regex(k) for k in sorted(keywords, key=len, reverse=True))
    return re.compile(rf"(?<![{_WORD_CHARS}])(?P<kw>{alternatives})")


def _hits(pattern: Optional[re.Pattern], text: str) -> List[str]:
    if pattern is None or not text:
        return []
    found = [m.group("kw") for m in pattern.finditer(text)]
    return list(dict.fromkeys(found))


def classify_title(title: Any, categories: Optional[List[Dict[str, Any]]] = None,
                   eqs_category: Optional[str] = None) -> Dict[str, Any]:
    """Ereignisart(en) eines Titels.

    Rückgabe ``{"primary": {...} | None, "matches": [...]}``; je Treffer ``id``, ``label``,
    ``employer_related``, ``topics`` und ``keywords`` (getroffene Wortfolgen des Titels, bei
    einer EQS-Kategorie ``"EQS: <Kategorie>"``). ``primary`` ist die Ereignisart mit
    Arbeitgeberbezug mit den meisten Treffern (Gleichstand: Dateireihenfolge); ohne solche
    die Gruppe ohne Arbeitgeberbezug, wenn sie trifft oder ``eqs_category`` zu ihr gehört;
    sonst None. Reine Funktion."""
    cats = load_event_categories() if categories is None else categories
    text = normalize_title(title)
    matches: List[Dict[str, Any]] = []
    for c in cats:
        hits = _hits(c.get("pattern"), text)
        if not c["employer_related"] and eqs_category and eqs_category in c.get("eqs_categories", []):
            hits = [f"EQS: {eqs_category}"] + hits
        if hits:
            matches.append({"id": c["id"], "label": c["label"], "employer_related": c["employer_related"],
                            "topics": list(c["topics"]), "keywords": hits})
    employer = [m for m in matches if m["employer_related"]]
    if employer:
        primary = max(employer, key=lambda m: len(m["keywords"]))   # max liefert bei Gleichstand den ersten
    else:
        primary = next((m for m in matches if not m["employer_related"]), None)
    return {"primary": primary, "matches": matches}


def category_by_id(category_id: Optional[str], categories: Optional[List[Dict[str, Any]]] = None) -> Optional[Dict[str, Any]]:
    cats = load_event_categories() if categories is None else categories
    return next((c for c in cats if c["id"] == category_id), None)


__all__ = [
    "EVENT_CATEGORIES_PATH", "NON_EMPLOYER_ID", "WILDCARD_MAX_WORDS",
    "known_topics", "load_event_categories", "clear_cache", "normalize_title", "compile_keywords", "classify_title",
    "category_by_id",
]
