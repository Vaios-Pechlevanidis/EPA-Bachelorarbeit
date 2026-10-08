"""
Quellen der externen Belege (Zyklus 2, Inkrement 4): Abruf je Unternehmen,
Quelle und Kalendermonat.

Ein Beleg ist eine zeitlich nahe Meldung mit Datum, Titel, Herausgeber und
Link; er ist keine Ursache. Gespeichert werden nur Titel, Herausgeber, Link,
Datum, Quelle, Typ, Verlässlichkeit und Sprache: keine Volltexte, keine
Textauszüge (Maßnahmen zu den Nutzungsbedingungen, E7, 2026-10-08).

Quellen und Typen:

- ``gnews`` Google News RSS, Hauptquelle: eine Abfrage je Unternehmen und
  Monat mit den Operatoren ``after:``/``before:`` (wie im Spike,
  ``docs/quellen-spike.md``), Typ ``news``, Verlässlichkeit ``mittel``.
- ``eqs`` EQS News, zweite Quelle für börsennotierte Unternehmen (Schritt 5),
  Typ ``adhoc``, Verlässlichkeit ``hoch``.
- ``gdelt`` GDELT DOC, nur hinter dem Schalter ``CONTEXT_GDELT=1`` (Standard aus).
- ``global`` allgemeine Ereignisse aus ``backend/data/global_events.json``
  (Schritt 7), Typ ``global``, Verlässlichkeit ``hypothese``.

Der Typ ``market`` ist reserviert und wird nicht erzeugt. Zwischen zwei
Abrufen derselben Quelle liegen mindestens ``MIN_FETCH_INTERVAL_S`` Sekunden;
die Kennung (``USER_AGENT`` aus ``news_service``) nennt Forschung und
nicht-kommerzielle Nutzung. Der Netzabruf liegt hinter austauschbaren
Abruffunktionen (``fetcher``), damit Tests ohne Netz laufen.
"""

from __future__ import annotations

import hashlib
import re
import time
from datetime import datetime, timezone
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple

from services import news_service

SOURCE_GNEWS = "gnews"
SOURCE_EQS = "eqs"
SOURCE_GDELT = "gdelt"
SOURCE_GLOBAL = "global"

TYPE_NEWS = "news"
TYPE_ADHOC = "adhoc"
TYPE_GLOBAL = "global"
TYPE_MARKET = "market"          # reserviert, wird nicht erzeugt
SOURCE_TYPES = (TYPE_NEWS, TYPE_ADHOC, TYPE_GLOBAL, TYPE_MARKET)

RELIABILITY = {TYPE_ADHOC: "hoch", TYPE_NEWS: "mittel", TYPE_GLOBAL: "hypothese"}
SOURCE_LABELS = {SOURCE_GNEWS: "Google News RSS", SOURCE_EQS: "EQS News", SOURCE_GDELT: "GDELT DOC",
                 SOURCE_GLOBAL: "Allgemeines Ereignis"}

MIN_FETCH_INTERVAL_S = 2.0
GNEWS_LIMIT = 200               # RSS liefert höchstens rund 100 Einträge; keine Kürzung

Fetcher = Callable[[str], bytes]

# Zeitpunkt des letzten Abrufs je Quelle (monotonic), für die Drosselung.
_last_request: Dict[str, float] = {}


# ── Drosselung ───────────────────────────────────────────────────────────────

def throttle(source: str, sleep: Optional[Callable[[float], None]] = None,
             clock: Optional[Callable[[], float]] = None, interval: float = MIN_FETCH_INTERVAL_S) -> float:
    """Wartet, bis seit dem letzten Abruf derselben Quelle ``interval`` Sekunden
    vergangen sind; liefert die gewartete Zeit. ``sleep`` und ``clock`` werden erst
    beim Aufruf aufgelöst (Tests ersetzen ``time.sleep``)."""
    sleep = sleep or time.sleep
    clock = clock or time.monotonic
    last = _last_request.get(source)
    now = clock()
    waited = 0.0
    if last is not None and now - last < interval:
        waited = interval - (now - last)
        sleep(waited)
        now = clock()
    _last_request[source] = now
    return waited


# ── Einträge ─────────────────────────────────────────────────────────────────

_WS_RE = re.compile(r"\s+")
_PUNCT_RE = re.compile(r"[^\w\s]", re.UNICODE)


def normalize_title(title: str) -> str:
    """Titel für den Duplikatvergleich: klein, ohne Satzzeichen, Leerraum zusammengefasst."""
    return _WS_RE.sub(" ", _PUNCT_RE.sub(" ", (title or "").casefold())).strip()


def item_id(url: str, title: str) -> str:
    key = (url or "").strip() or normalize_title(title)
    return hashlib.sha1(key.encode("utf-8")).hexdigest()[:16]


def make_item(*, title: str, url: str, published_at: Optional[str], publisher: Optional[str], source: str,
              source_type: str, language: Optional[str] = None, issuer: Optional[str] = None,
              category: Optional[str] = None) -> Dict[str, Any]:
    """Einheitlicher Beleg. ``published_at`` ist ein ISO-Zeitstempel oder ``YYYY-MM-DD``;
    ``date`` ist der Kalendertag."""
    if source_type == TYPE_MARKET:
        raise ValueError("source_type 'market' ist reserviert und wird nicht erzeugt.")
    if source_type not in RELIABILITY:
        raise ValueError(f"source_type '{source_type}' unbekannt; erlaubt: {', '.join(RELIABILITY)}.")
    return {
        "id": item_id(url, title),
        "date": published_at[:10] if published_at else None,
        "datetime": published_at,
        "title": " ".join((title or "").split()),
        "publisher": publisher or None,
        "url": url,
        "source": source,
        "source_type": source_type,
        "reliability": RELIABILITY[source_type],
        "language": language,
        "issuer": issuer,
        "category": category,
    }


def dedupe(items: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Doppelte Meldungen (gleicher Link oder gleicher normalisierter Titel) zählen
    einmal; die erste bleibt."""
    seen_urls: set = set()
    seen_titles: set = set()
    out: List[Dict[str, Any]] = []
    for item in items:
        url = (item.get("url") or "").strip()
        title = normalize_title(item.get("title") or "")
        if (url and url in seen_urls) or (title and title in seen_titles):
            continue
        if url:
            seen_urls.add(url)
        if title:
            seen_titles.add(title)
        out.append(item)
    return out


# ── Google News RSS (Hauptquelle) ────────────────────────────────────────────

def _next_month(month: str) -> str:
    year, mon = int(month[:4]), int(month[5:7])
    return f"{year + (mon // 12):04d}-{mon % 12 + 1:02d}"


def _exclusion(term: str) -> str:
    term = " ".join(str(term).split())
    return f'-"{term}"' if " " in term else f"-{term}"


def gnews_month_query(term: str, month: str, exclude: Iterable[str] = ()) -> str:
    """Suchbegriff für einen Kalendermonat: ``term after:YYYY-MM-01 before:<1. des Folgemonats>``
    (``before:`` ist ausschließend), dazu Ausschlussbegriffe als ``-wort`` bzw. ``-"wort folge"``."""
    parts = [term, f"after:{month}-01", f"before:{_next_month(month)}-01"]
    parts += [_exclusion(e) for e in exclude if str(e).strip()]
    return " ".join(parts)


def fetch_gnews_month(term: str, month: str, exclude: Iterable[str] = (),
                      fetcher: Optional[Fetcher] = None) -> Tuple[List[Dict[str, Any]], str]:
    """Meldungen eines Monats aus Google News RSS als Belege vom Typ ``news``.
    ``fetcher(query) -> bytes`` ersetzt den Netzabruf (Standard ``news_service.fetch_rss``).
    Liefert ``(items, query)``; Fehler des Abrufs werden weitergereicht."""
    query = gnews_month_query(term, month, exclude)
    body = (fetcher or news_service.fetch_rss)(query)
    entries = news_service.parse_rss(body, limit=GNEWS_LIMIT)
    items = [
        make_item(title=e["title"], url=e["url"], published_at=e.get("published_at"), publisher=e.get("source"),
                  source=SOURCE_GNEWS, source_type=TYPE_NEWS)
        for e in entries
    ]
    return dedupe(items), query


def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


__all__ = [
    "SOURCE_GNEWS", "SOURCE_EQS", "SOURCE_GDELT", "SOURCE_GLOBAL",
    "TYPE_NEWS", "TYPE_ADHOC", "TYPE_GLOBAL", "TYPE_MARKET", "SOURCE_TYPES", "RELIABILITY", "SOURCE_LABELS",
    "MIN_FETCH_INTERVAL_S", "throttle", "normalize_title", "item_id", "make_item", "dedupe",
    "gnews_month_query", "fetch_gnews_month", "utc_now",
]
