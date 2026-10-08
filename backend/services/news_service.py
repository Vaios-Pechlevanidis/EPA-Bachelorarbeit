"""
Aktuelle Nachrichten zu einem Unternehmen für das Aktien-Dashboard (Zyklus 2,
Inkrement 3, E16).

Quelle ist Google-News-RSS (Suche nach dem Unternehmensnamen, deutsch), wie in
E7 als primäre Nachrichtenquelle festgelegt; yfinance liefert für die 17 Ticker
keine Nachrichten (geprüft 2026-10-04). Die Meldungen sind eine Einordnung des
aktuellen Umfelds. Sie werden keiner auffälligen Veränderung zugeordnet und
nicht als Ursache dargestellt.

Ablauf:

1. Suchbegriff = Name aus ``companies`` (nur lesend) ohne Rechtsform am Ende,
   in Anführungszeichen, wenn er Leerzeichen enthält, plus ``when:{NEWS_DAYS}d``.
2. Zwischenspeicher ``backend/data/market/news/<company_id>.json`` (nicht
   eingecheckt). Ist er älter als ``NEWS_MAX_AGE`` und ``MARKET_LIVE_FETCH`` nicht
   ``0``, wird neu abgerufen; schlägt das fehl, gilt der alte Stand (``stale``).
3. Ohne Zwischenspeicher und ohne Abruf: ``available: false`` mit Begründung.

Der Netzabruf liegt hinter ``fetch_rss`` (austauschbar über ``fetcher``).
"""

from __future__ import annotations

import json
import logging
import re
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from services import context_service

logger = logging.getLogger(__name__)

GNEWS_URL = "https://news.google.com/rss/search"
USER_AGENT = "Mozilla/5.0 (compatible; EPA-Bachelorarbeit/0.1; research, non-commercial)"
TIMEOUT_S = 20
NEWS_DAYS = 90             # Suchfenster in Tagen
NEWS_LIMIT = 30            # angezeigte Meldungen, neueste zuerst
NEWS_MAX_AGE = timedelta(hours=12)
SOURCE = "Google News RSS (Suche nach dem Unternehmensnamen, deutsch)"

RssFetcher = Callable[[str], bytes]

# Fehlgeschlagene Abrufe je Unternehmen: (Zeitpunkt, Begründung).
_failed_fetches: Dict[int, tuple[float, str]] = {}


_LEGAL_FORM_RE = re.compile(r"\s+(SE|AG|GmbH|KGaA|SE & Co\. KGaA|Inc\.?)$", re.IGNORECASE)


def search_term(name: str) -> str:
    """Suchbegriff aus dem Firmennamen: ohne Rechtsform am Ende (in Meldungen
    selten mitgeschrieben), mit Leerzeichen in Anführungszeichen. Auch die
    Monatsabfragen der Belege (Inkrement 4, ``services/evidence_sources.py``)
    gehen von diesem Begriff aus."""
    clean = _LEGAL_FORM_RE.sub("", " ".join(str(name).split()))
    return f'"{clean}"' if " " in clean else clean


def news_query(name: str) -> str:
    """Suchbegriff für die aktuellen Meldungen: ``search_term`` plus ``when:{NEWS_DAYS}d``."""
    return f"{search_term(name)} when:{NEWS_DAYS}d"


def fetch_rss(query: str) -> bytes:
    """RSS-Antwort von Google News (Netzwerk). Einzige Stelle mit Netzabruf."""
    params = {"q": query, "hl": "de", "gl": "DE", "ceid": "DE:de"}
    req = urllib.request.Request(f"{GNEWS_URL}?{urllib.parse.urlencode(params)}",
                                 headers={"User-Agent": USER_AGENT, "Accept": "application/rss+xml, */*"})
    with urllib.request.urlopen(req, timeout=TIMEOUT_S) as resp:
        return resp.read()


def parse_rss(body: bytes, limit: int = NEWS_LIMIT) -> List[Dict[str, Any]]:
    """Meldungen ``[{"title", "source", "url", "published_at"}]``, neueste zuerst.

    Google hängt die Quelle an den Titel an (``"… - heise online"``); sie wird
    abgeschnitten und als ``source`` geführt. Meldungen ohne Titel oder Link entfallen.
    """
    root = ET.fromstring(body)
    items = []
    for it in root.findall("./channel/item"):
        title = (it.findtext("title") or "").strip()
        url = (it.findtext("link") or "").strip()
        if not title or not url.startswith("http"):
            continue
        src = it.find("source")
        source = (src.text or "").strip() if src is not None else ""
        if source and title.endswith(f" - {source}"):
            title = title[: -len(source) - 3].rstrip()
        published = None
        raw_date = it.findtext("pubDate")
        if raw_date:
            try:
                published = parsedate_to_datetime(raw_date).astimezone(timezone.utc).replace(microsecond=0).isoformat()
            except (TypeError, ValueError):
                published = None
        items.append({"title": title, "source": source or None, "url": url, "published_at": published})
    items.sort(key=lambda i: i["published_at"] or "", reverse=True)
    return items[:limit]


def _cache_path(company_id: int, cache_dir: Optional[Path] = None) -> Path:
    return Path(cache_dir or context_service.CACHE_DIR) / "news" / f"{int(company_id)}.json"


def load_cached(company_id: int, cache_dir: Optional[Path] = None) -> Optional[Dict[str, Any]]:
    path = _cache_path(company_id, cache_dir)
    if not path.exists():
        return None
    try:
        with open(path, "r", encoding="utf-8") as fh:
            record = json.load(fh)
    except (OSError, ValueError) as exc:
        logger.warning("Nachrichten-Zwischenspeicher %s nicht lesbar: %s", path.name, exc)
        return None
    return record if isinstance(record, dict) and record.get("company_id") == int(company_id) else None


def save_cached(record: Dict[str, Any], cache_dir: Optional[Path] = None) -> Path:
    path = _cache_path(record["company_id"], cache_dir)
    tmp = path.with_suffix(".tmp")
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp.write_text(json.dumps(record, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(path)
    return path


def fetch_and_store(company_id: int, name: str, fetcher: Optional[RssFetcher] = None,
                    cache_dir: Optional[Path] = None, now: Optional[datetime] = None) -> Dict[str, Any]:
    """Ruft ab, wertet aus und speichert; Fehler werden weitergereicht."""
    query = news_query(name)
    items = parse_rss((fetcher or fetch_rss)(query))
    record = {
        "company_id": int(company_id),
        "query": query,
        "fetched_at": (now or datetime.now(timezone.utc)).replace(microsecond=0).isoformat(),
        "source": SOURCE,
        "items": items,
    }
    save_cached(record, cache_dir)
    return record


def _is_fresh(record: Dict[str, Any], now: datetime) -> bool:
    try:
        fetched = datetime.fromisoformat(record["fetched_at"])
    except (KeyError, TypeError, ValueError):
        return False
    return now - fetched < NEWS_MAX_AGE


def _try_fetch(company_id: int, name: str, fetcher: Optional[RssFetcher], cache_dir: Optional[Path],
               now: datetime) -> tuple[Optional[Dict[str, Any]], Optional[str]]:
    """Live-Abruf mit Speichern: ``(record, None)`` oder ``(None, Begründung)``."""
    if not context_service.live_fetch_enabled():
        return None, (f"Keine gespeicherten Nachrichten; der Live-Abruf ist abgeschaltet "
                      f"({context_service.LIVE_FETCH_ENV}=0).")
    failed = _failed_fetches.get(int(company_id))
    if failed and time.monotonic() - failed[0] < context_service.FAILED_FETCH_TTL:
        return None, failed[1]
    try:
        return fetch_and_store(company_id, name, fetcher=fetcher, cache_dir=cache_dir, now=now), None
    except Exception as exc:  # noqa: BLE001 – Netz, XML, Dateisystem
        logger.warning("Nachrichtenabruf für %s fehlgeschlagen: %s", company_id, exc)
        reason = f"Nachrichten konnten nicht abgerufen werden ({type(exc).__name__}: {exc})."
        _failed_fetches[int(company_id)] = (time.monotonic(), reason)
        return None, reason


def company_news(company_id: int, fetcher: Optional[RssFetcher] = None,
                 cache_dir: Optional[Path] = None, now: Optional[datetime] = None) -> Optional[Dict[str, Any]]:
    """Antwort für ``GET /analytics/company/{id}/news``; None bei unbekanntem Unternehmen.

    Wirft bei fehlenden Daten nicht, sondern liefert ``available: false`` mit
    Grund. Ein veralteter Zwischenspeicher wird gezeigt, wenn der neue Abruf
    nicht möglich ist (``stale: true``).
    """
    info = context_service.company_ticker_info(company_id)
    if info is None:
        return None
    now = now or datetime.now(timezone.utc)
    name = info["name"] or ""
    record = load_cached(company_id, cache_dir)
    reason = None
    if record is None or not _is_fresh(record, now):
        fetched, reason = _try_fetch(company_id, name, fetcher, cache_dir, now)
        record = fetched or record
    items = (record or {}).get("items") or []
    if record is None:
        shown_reason = reason
    elif not items:
        shown_reason = f"Keine Meldungen in den letzten {NEWS_DAYS} Tagen gefunden."
    else:
        shown_reason = None
    return {
        "company_id": int(company_id),
        "query": (record or {}).get("query") or news_query(name),
        "available": bool(items),
        "reason": shown_reason,
        "stale": record is not None and not _is_fresh(record, now),
        "items": items,
        "fetched_at": (record or {}).get("fetched_at"),
        "source": SOURCE,
        "window_days": NEWS_DAYS,
    }
