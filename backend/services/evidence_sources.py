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

import calendar
import hashlib
import json
import re
import threading
import time
import unicodedata
import urllib.parse
import urllib.request
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
# Eine Sperre je Quelle: Die Quellen werden nebeneinander abgerufen (je Quelle ein
# Strang), der Mindestabstand gilt je Quelle auch dann, wenn mehrere Anfragen
# dieselbe Quelle zugleich brauchen.
_source_locks: Dict[str, threading.Lock] = {}
_source_locks_guard = threading.Lock()


# ── Drosselung ───────────────────────────────────────────────────────────────

def source_lock(source: str) -> threading.Lock:
    with _source_locks_guard:
        lock = _source_locks.get(source)
        if lock is None:
            lock = _source_locks[source] = threading.Lock()
        return lock


def throttle(source: str, sleep: Optional[Callable[[float], None]] = None,
             clock: Optional[Callable[[], float]] = None, interval: float = MIN_FETCH_INTERVAL_S) -> float:
    """Wartet, bis seit dem letzten Abruf derselben Quelle ``interval`` Sekunden
    vergangen sind; liefert die gewartete Zeit. ``sleep`` und ``clock`` werden erst
    beim Aufruf aufgelöst (Tests ersetzen ``time.sleep``). Die Sperre je Quelle hält
    den Abstand auch zwischen Strängen ein; andere Quellen warten nicht."""
    sleep = sleep or time.sleep
    clock = clock or time.monotonic
    with source_lock(source):
        last = _last_request.get(source)
        now = clock()
        waited = 0.0
        if last is not None and now - last < interval:
            waited = interval - (now - last)
            sleep(waited)
            now = clock()
        _last_request[source] = now
    return waited


# ── Sprache ──────────────────────────────────────────────────────────────────
# Grobe Stoppwort-Heuristik über den Titel (wie im Spike, docs/quellen-spike.md):
# "de", "en" oder None (kein oder gleich viele Treffer). Keine neue Abhängigkeit.

DE_WORDS = frozenset({
    "und", "der", "die", "das", "für", "mit", "von", "im", "am", "bei", "nach", "über", "zum", "zur", "ist",
    "wird", "sich", "nicht", "auf", "den", "dem", "des", "ein", "eine", "einen", "neue", "neuer", "neues",
    "gegen", "bis", "aus", "wie", "noch", "mehr", "als", "auch", "um", "beim", "vom", "ins",
})
EN_WORDS = frozenset({
    "the", "and", "of", "for", "with", "to", "in", "on", "at", "is", "are", "by", "from", "as", "that",
    "this", "its", "new", "will", "has", "after", "says", "over", "into", "than", "more", "about",
})
_WORD_RE = re.compile(r"[a-zäöüß]+")


def guess_language(title: str) -> Optional[str]:
    """Sprache eines Titels nach Stoppwörtern: ``"de"``, ``"en"`` oder None."""
    de = en = 0
    for token in _WORD_RE.findall((title or "").lower()):
        if token in DE_WORDS:
            de += 1
        elif token in EN_WORDS:
            en += 1
    if de > en:
        return "de"
    if en > de:
        return "en"
    return None


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
        "language": language or guess_language(title),
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


# ── HTTP ─────────────────────────────────────────────────────────────────────

TIMEOUT_S = 20


def http_get(url: str) -> bytes:
    """GET mit der Forschungs-Kennung; einzige Stelle mit Netzabruf für EQS und GDELT."""
    req = urllib.request.Request(url, headers={"User-Agent": news_service.USER_AGENT, "Accept": "application/json, */*"})
    with urllib.request.urlopen(req, timeout=TIMEOUT_S) as resp:
        return resp.read()


def _month_bounds(month: str) -> Tuple[str, str]:
    """Erster Tag des Monats und erster Tag des Folgemonats (``YYYY-MM-DD``)."""
    return f"{month}-01", f"{_next_month(month)}-01"


# ── EQS News (zweite Quelle, börsennotierte Unternehmen) ─────────────────────

EQS_URL = "https://www.eqs-news.com/wp-json/eqsnews/v1/news"
EQS_COMPANIES_URL = "https://www.eqs-news.com/wp-json/eqsnews/v1/companies"
EQS_NEWS_PAGE = "https://www.eqs-news.com/news"
EQS_PER_PAGE = 100
EQS_MAX_PAGES = 5
EQS_PUBLISHER = "EQS News"


def slugify(text: str) -> str:
    """Pfadteil wie in den öffentlichen Meldungsseiten von EQS (klein, ASCII, Bindestriche)."""
    text = (text or "").replace("ß", "ss")
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii").lower()
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", text)).strip("-")


def eqs_news_url(record: Dict[str, Any]) -> str:
    """Öffentliche Meldungsseite: ``…/news/<kategorie>/<schlagzeile>/<id>`` (Muster aus
    ``share_url`` der Detailroute; die Listenroute nennt keinen Link)."""
    news_id = re.sub(r"_(de|en)$", "", str(record.get("id") or ""))
    return f"{EQS_NEWS_PAGE}/{slugify(record.get('category') or 'news') or 'news'}/{slugify(record.get('headline') or '') or 'meldung'}/{news_id}"


def _eqs_datetime(record: Dict[str, Any]) -> Optional[str]:
    raw = record.get("dateUtc") or record.get("date")
    if not raw:
        return None
    try:
        return datetime.strptime(str(raw)[:19], "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc).isoformat()
    except ValueError:
        return None


def eqs_month_url(uuid: str, month: str, page: int = 1) -> str:
    start, end = _month_bounds(month)
    params = {"company_name": uuid, "start_date": start, "end_date": end, "per_page": EQS_PER_PAGE, "page": page}
    return f"{EQS_URL}?{urllib.parse.urlencode(params)}"


def _eqs_records(body: bytes) -> Tuple[List[Dict[str, Any]], Optional[str]]:
    data = json.loads(body.decode("utf-8", "replace"))
    if not isinstance(data, dict):
        raise ValueError("EQS: keine JSON-Antwort mit Datensätzen")
    error = data.get("error")
    if isinstance(error, dict) and error.get("message"):
        raise ValueError(f"EQS: {error.get('message')}")
    records = data.get("records") or []
    return (records if isinstance(records, list) else []), None


def fetch_eqs_month(info: Dict[str, Any], month: str, fetcher: Optional[Fetcher] = None) -> Tuple[List[Dict[str, Any]], str]:
    """Pflicht- und Unternehmensmitteilungen eines Monats aus EQS News als Belege vom Typ
    ``adhoc``; ``info['eqs_uuid']`` ist die companyUUID des Emittenten. Der Beleg nennt den
    Emittenten (``issuer``), damit bei Konzernmutter oder Konzerngesellschaft sichtbar
    bleibt, zu welcher Gesellschaft er gehört. ``fetcher(url) -> bytes``."""
    uuid = info.get("eqs_uuid")
    if not uuid:
        raise ValueError("EQS: keine companyUUID in der Metadatei")
    get = fetcher or http_get
    items: List[Dict[str, Any]] = []
    first_url = eqs_month_url(uuid, month, 1)
    for page in range(1, EQS_MAX_PAGES + 1):
        records, _ = _eqs_records(get(eqs_month_url(uuid, month, page)))
        for r in records:
            published = _eqs_datetime(r)
            if not published or not published.startswith(month):
                continue   # end_date ist beim Endpunkt unscharf; nur der Kalendermonat zählt
            items.append(make_item(
                title=r.get("headline") or "", url=eqs_news_url(r), published_at=published, publisher=EQS_PUBLISHER,
                source=SOURCE_EQS, source_type=TYPE_ADHOC, language=(r.get("language") or None),
                issuer=r.get("companyName") or info.get("eqs_name"), category=r.get("category") or None,
            ))
        total = int(records[0].get("totalItem") or 0) if records else 0
        if len(records) < EQS_PER_PAGE or page * EQS_PER_PAGE >= total:
            break
    return dedupe(items), first_url


def eqs_search_companies(name: str, fetcher: Optional[Fetcher] = None) -> List[Dict[str, Any]]:
    """Emittenten zu einem Namen (Route ``companies?search=``), für die einmalige Suche der
    companyUUID: ``[{"company_name", "uuid", "isin", "country"}]``."""
    url = f"{EQS_COMPANIES_URL}?{urllib.parse.urlencode({'search': name, 'per_page': EQS_PER_PAGE})}"
    records, _ = _eqs_records((fetcher or http_get)(url))
    return [{"company_name": r.get("companyName"), "uuid": r.get("companyUUID"), "isin": r.get("isin"),
             "country": r.get("country")} for r in records if r.get("companyUUID")]


# ── GDELT DOC (nur hinter dem Schalter CONTEXT_GDELT=1) ──────────────────────

GDELT_URL = "https://api.gdeltproject.org/api/v2/doc/doc"
GDELT_MAX_RECORDS = 75
_GDELT_LANG = {"german": "de", "english": "en"}


def gdelt_month_url(term: str, month: str) -> str:
    start, end = _month_bounds(month)
    last_day = calendar.monthrange(int(month[:4]), int(month[5:7]))[1]
    params = {"query": term, "mode": "artlist", "format": "json",
              "startdatetime": start.replace("-", "") + "000000",
              "enddatetime": f"{month}-{last_day:02d}".replace("-", "") + "235959",
              "maxrecords": GDELT_MAX_RECORDS, "sort": "datedesc"}
    return f"{GDELT_URL}?{urllib.parse.urlencode(params)}"


def fetch_gdelt_month(info: Dict[str, Any], month: str, fetcher: Optional[Fetcher] = None) -> Tuple[List[Dict[str, Any]], str]:
    """Artikel eines Monats aus GDELT DOC als Belege vom Typ ``news`` (nur mit Schalter)."""
    url = gdelt_month_url(info["search_term"], month)
    body = (fetcher or http_get)(url)
    text = body.decode("utf-8", "replace").strip()
    articles = json.loads(text).get("articles") or [] if text else []
    items = []
    for a in articles:
        published = None
        raw = a.get("seendate")
        if raw:
            try:
                published = datetime.strptime(raw, "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc).isoformat()
            except ValueError:
                published = None
        if not published or not published.startswith(month):
            continue
        items.append(make_item(title=a.get("title") or "", url=a.get("url") or "", published_at=published,
                               publisher=a.get("domain") or None, source=SOURCE_GDELT, source_type=TYPE_NEWS,
                               language=_GDELT_LANG.get(str(a.get("language") or "").lower())))
    return dedupe([i for i in items if i["url"]]), url


__all__ = [
    "SOURCE_GNEWS", "SOURCE_EQS", "SOURCE_GDELT", "SOURCE_GLOBAL",
    "TYPE_NEWS", "TYPE_ADHOC", "TYPE_GLOBAL", "TYPE_MARKET", "SOURCE_TYPES", "RELIABILITY", "SOURCE_LABELS",
    "MIN_FETCH_INTERVAL_S", "throttle", "source_lock", "guess_language", "normalize_title", "item_id", "make_item", "dedupe",
    "gnews_month_query", "fetch_gnews_month", "utc_now", "http_get",
    "EQS_URL", "EQS_COMPANIES_URL", "slugify", "eqs_news_url", "eqs_month_url", "fetch_eqs_month", "eqs_search_companies",
    "GDELT_URL", "gdelt_month_url", "fetch_gdelt_month",
]
