"""
Externe Belege im Ereignisfenster (Zyklus 2, Inkrement 4) – Fenster.

Ein Beleg ist eine zeitlich nahe Meldung mit Datum, Titel, Herausgeber und
Link. Er ist keine Ursache: Das Dashboard behauptet keinen Zusammenhang und
bewertet keine Meldung. Dieses Modul rechnet nur das **Ereignisfenster**, also
den Zeitraum in Kalendermonaten, in dem Meldungen als Belege gelten.

Ereignisfenster (vorläufig, E18):

- **Niveauwechsel** (E9): von ``window_before`` Monaten vor dem Beginn des
  Übergangs bis ``window_after`` Monate nach ``date``. Der Beginn des Übergangs
  ist der Monat nach ``previous_period`` (dem letzten bewerteten Monat vor
  ``date``); ohne Lücke (``gap_months`` 0) ist das ``date`` selbst. Liegt zwischen
  beiden eine Lücke, kann der Übergang irgendwo darin liegen; das Fenster
  beginnt deshalb vor der Lücke. Ohne ``previous_period`` (Reihenrand) gilt
  ``date`` als Beginn.
- **Einzelmonat** (E14): dieselben Abstände um den Monat.
- **Freie Auswahl** (E17): dieselben Abstände um den Zeitraum ``from``..``to``.

Standardwerte: ``DEFAULT_WINDOW_BEFORE`` = 3 Monate, ``DEFAULT_WINDOW_AFTER`` =
1 Monat (Setzung des Autors, vorläufig; Begründung in E18). Alle Funktionen
sind rein (kein Datei-, DB- oder Netzzugriff).
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

DEFAULT_WINDOW_BEFORE = 3   # Monate vor dem Beginn des Übergangs (vorläufig, E18)
DEFAULT_WINDOW_AFTER = 1    # Monate nach dem markierten Monat bzw. dem Ende der Auswahl (vorläufig, E18)
MAX_WINDOW_MONTHS = 24      # Obergrenze je Seite für die API

KIND_CHANGE = "niveauwechsel"
KIND_OUTLIER = "einzelmonat"
KIND_SELECTION = "auswahl"

_PERIOD_RE = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")


# ── Monate ───────────────────────────────────────────────────────────────────

def is_period(value: Any) -> bool:
    return isinstance(value, str) and _PERIOD_RE.fullmatch(value) is not None


def month_index(period: str) -> int:
    """``YYYY-MM`` als fortlaufende Zahl (Jahr · 12 + Monat − 1); ValueError bei falschem Format."""
    if not is_period(period):
        raise ValueError(f"Monat muss das Format YYYY-MM haben, nicht {period!r}.")
    return int(period[:4]) * 12 + int(period[5:7]) - 1


def period_from_index(index: int) -> str:
    return f"{index // 12:04d}-{index % 12 + 1:02d}"


def shift_month(period: str, months: int) -> str:
    """Kalendermonat um ``months`` verschoben, auch über Jahresgrenzen."""
    return period_from_index(month_index(period) + months)


def month_range(first: str, last: str) -> List[str]:
    """Alle Kalendermonate von ``first`` bis ``last`` einschließlich (leer, wenn ``first`` nach ``last``)."""
    a, b = month_index(first), month_index(last)
    return [period_from_index(i) for i in range(a, b + 1)]


def _check_sizes(window_before: int, window_after: int) -> None:
    for name, value in (("window_before", window_before), ("window_after", window_after)):
        if not isinstance(value, int) or isinstance(value, bool) or value < 0 or value > MAX_WINDOW_MONTHS:
            raise ValueError(f"{name} muss eine ganze Zahl zwischen 0 und {MAX_WINDOW_MONTHS} sein, nicht {value!r}.")


# ── Fenster ──────────────────────────────────────────────────────────────────

def _window(kind: str, anchor_from: str, anchor_to: str, transition_from: str,
            window_before: int, window_after: int, anchor: Dict[str, Any]) -> Dict[str, Any]:
    start = shift_month(transition_from, -window_before)
    end = shift_month(anchor_to, window_after)
    return {
        "kind": kind,
        "from": start,
        "to": end,
        "months": month_index(end) - month_index(start) + 1,
        "transition_from": transition_from,
        "anchor_from": anchor_from,
        "anchor_to": anchor_to,
        "window_before": window_before,
        "window_after": window_after,
        "anchor": anchor,
    }


def window_for_change(
    date: str,
    previous_period: Optional[str] = None,
    gap_months: Optional[int] = None,
    window_before: int = DEFAULT_WINDOW_BEFORE,
    window_after: int = DEFAULT_WINDOW_AFTER,
) -> Dict[str, Any]:
    """Ereignisfenster eines Niveauwechsels.

    ``date`` ist der erste bewertete Monat auf dem neuen Niveau, ``previous_period``
    der letzte bewertete Monat davor (None am Reihenrand). Der Übergang beginnt im
    Monat nach ``previous_period``; ohne Lücke ist das ``date``. ``gap_months`` wird
    nur übernommen (Information für die Anzeige), die Rechnung nutzt
    ``previous_period``.
    """
    _check_sizes(window_before, window_after)
    if previous_period is not None and month_index(previous_period) >= month_index(date):
        raise ValueError("previous_period muss vor date liegen.")
    transition_from = shift_month(previous_period, 1) if previous_period else date
    gap = (month_index(date) - month_index(previous_period) - 1) if previous_period else 0
    anchor = {"date": date, "previous_period": previous_period, "gap_months": gap if gap_months is None else gap_months}
    return _window(KIND_CHANGE, date, date, transition_from, window_before, window_after, anchor)


def window_for_anomaly(anomaly: Dict[str, Any], window_before: int = DEFAULT_WINDOW_BEFORE,
                       window_after: int = DEFAULT_WINDOW_AFTER) -> Dict[str, Any]:
    """``window_for_change`` für eine Anomalie aus ``anomaly_service`` (Felder ``date``,
    ``previous_period``, ``gap_months``)."""
    return window_for_change(
        anomaly["date"], anomaly.get("previous_period"), anomaly.get("gap_months"), window_before, window_after,
    )


def window_for_outlier(date: str, window_before: int = DEFAULT_WINDOW_BEFORE,
                       window_after: int = DEFAULT_WINDOW_AFTER) -> Dict[str, Any]:
    """Ereignisfenster eines auffälligen Einzelmonats (E14): die Abstände um den Monat."""
    _check_sizes(window_before, window_after)
    month_index(date)
    return _window(KIND_OUTLIER, date, date, date, window_before, window_after, {"date": date})


def window_for_selection(from_month: str, to_month: str, window_before: int = DEFAULT_WINDOW_BEFORE,
                         window_after: int = DEFAULT_WINDOW_AFTER) -> Dict[str, Any]:
    """Ereignisfenster einer freien Auswahl (E17): die Abstände um ``from``..``to``.
    ValueError, wenn ``from`` nach ``to`` liegt."""
    _check_sizes(window_before, window_after)
    if month_index(from_month) > month_index(to_month):
        raise ValueError("from liegt nach to.")
    return _window(KIND_SELECTION, from_month, to_month, from_month, window_before, window_after,
                   {"from": from_month, "to": to_month})


def window_months(window: Dict[str, Any]) -> List[str]:
    """Die Kalendermonate eines Fensters, erster zuerst."""
    return month_range(window["from"], window["to"])


__all__ = [
    "DEFAULT_WINDOW_BEFORE", "DEFAULT_WINDOW_AFTER", "MAX_WINDOW_MONTHS",
    "KIND_CHANGE", "KIND_OUTLIER", "KIND_SELECTION",
    "is_period", "month_index", "period_from_index", "shift_month", "month_range",
    "window_for_change", "window_for_anomaly", "window_for_outlier", "window_for_selection", "window_months",
]


# ═════════════════════════════════════════════════════════════════════════════
# Belegspeicher und Belege eines Fensters (Inkrement 4, Schritt 2)
# ═════════════════════════════════════════════════════════════════════════════
#
# Meldungen werden je Unternehmen, Quelle und Kalendermonat abgelegt, nicht je
# Veränderung: ``backend/data/context/<company_id>/<source>/<YYYY-MM>.json``
# (in ``.gitignore``). Die Belege eines Fensters sind alle gespeicherten
# Meldungen, deren Datum im Fenster liegt. So bleibt der Speicher gültig, wenn
# sich die Erkennung ändert. Abgeschlossene Monate werden nicht erneut
# abgerufen, der laufende Monat frühestens nach ``CURRENT_MONTH_MAX_AGE``; ein
# anderer Suchbegriff macht einen gespeicherten Monat ungültig.
# ``CONTEXT_LIVE_FETCH=0`` unterbindet jeden Abruf; dann gilt nur der Speicher.
# Jede Quelle läuft getrennt: Fällt eine aus, liefern die anderen weiter.

import json  # noqa: E402
import logging  # noqa: E402
import os  # noqa: E402
import tempfile  # noqa: E402
import time  # noqa: E402
from datetime import datetime, timedelta, timezone  # noqa: E402
from pathlib import Path  # noqa: E402
from typing import Callable, Tuple  # noqa: E402

from services import news_service  # noqa: E402
from services.evidence_sources import (  # noqa: E402
    SOURCE_EQS, SOURCE_GDELT, SOURCE_GNEWS, SOURCE_LABELS, TYPE_ADHOC, TYPE_GLOBAL, TYPE_NEWS,
    dedupe, fetch_gnews_month, gnews_month_query, guess_language, throttle, utc_now,
)

logger = logging.getLogger(__name__)

BACKEND_DIR = Path(__file__).resolve().parent.parent
STORE_DIR = BACKEND_DIR / "data" / "context"
LIVE_FETCH_ENV = "CONTEXT_LIVE_FETCH"
GDELT_ENV = "CONTEXT_GDELT"
CURRENT_MONTH_MAX_AGE = timedelta(hours=12)
FAILED_FETCH_TTL = 15 * 60      # Sekunden ohne neuen Versuch nach einem fehlgeschlagenen Abruf
STORE_VERSION = 1

EVIDENCE_NOTE = ("Belege sind zeitlich nahe Meldungen aus externen Quellen. Sie sind keine Aussage über "
                 "Ursachen; interne Auslöser sind von außen nicht sichtbar.")

# Fehlgeschlagene Abrufe je (Quelle, Unternehmen, Monat): (Zeitpunkt, Begründung).
_failed_fetches: Dict[Tuple[str, int, str], Tuple[float, str]] = {}


def live_fetch_enabled() -> bool:
    return os.getenv(LIVE_FETCH_ENV, "1").strip() != "0"


def gdelt_enabled() -> bool:
    return os.getenv(GDELT_ENV, "0").strip() == "1"


# ── Unternehmen ──────────────────────────────────────────────────────────────

def _normalize_name(raw: Any) -> str:
    return " ".join(str(raw or "").split()).casefold()


def company_context_info(company_id: int, metadata: Optional[Dict[int, Dict[str, Any]]] = None) -> Optional[Dict[str, Any]]:
    """Suchbegriff, Ausschlussbegriffe und Quellenangaben eines Unternehmens oder None,
    wenn es die ID nicht gibt. Name und Ticker kommen aus ``companies`` (nur lesend), der
    Rest aus ``company_metadata.json`` (``news_term``, ``news_exclude``,
    ``news_term_confirmed``, ``eqs``), nur bei gleichem Namen."""
    from services.context_service import company_ticker_info, load_metadata  # lazy: Tests ohne DB

    info = company_ticker_info(company_id)
    if info is None:
        return None
    meta_all = load_metadata() if metadata is None else metadata
    meta = meta_all.get(int(company_id)) or {}
    if meta and _normalize_name(meta.get("name")) != _normalize_name(info.get("name")):
        meta = {}
    name = info.get("name") or ""
    eqs = meta.get("eqs") or {}
    return {
        "company_id": int(company_id),
        "name": name,
        "search_term": (meta.get("news_term") or "").strip() or news_service.search_term(name),
        "exclude": [str(e) for e in (meta.get("news_exclude") or []) if str(e).strip()],
        "term_confirmed": bool(meta.get("news_term_confirmed")),
        "ticker": info.get("ticker"),
        "ticker_scope": info.get("ticker_scope"),
        "eqs_uuid": eqs.get("uuid") or None,
        "eqs_name": eqs.get("company_name") or None,
    }


def available_sources(info: Dict[str, Any]) -> List[str]:
    """Quellen eines Unternehmens: Google News immer, EQS mit companyUUID, GDELT nur mit Schalter."""
    sources = [SOURCE_GNEWS]
    if info.get("eqs_uuid"):
        sources.append(SOURCE_EQS)
    if gdelt_enabled():
        sources.append(SOURCE_GDELT)
    return sources


# ── Speicher ─────────────────────────────────────────────────────────────────

def record_path(company_id: int, source: str, month: str, store_dir: Optional[Path] = None) -> Path:
    if not is_period(month):
        raise ValueError(f"Monat muss das Format YYYY-MM haben, nicht {month!r}.")
    if not re.fullmatch(r"[a-z]+", source):
        raise ValueError(f"Quelle '{source}' ungültig.")
    return Path(store_dir or STORE_DIR) / str(int(company_id)) / source / f"{month}.json"


def load_record(company_id: int, source: str, month: str, store_dir: Optional[Path] = None) -> Optional[Dict[str, Any]]:
    """Gespeicherter Monat oder None (fehlt, unlesbar oder gehört nicht zu diesem Schlüssel)."""
    path = record_path(company_id, source, month, store_dir)
    if not path.exists():
        return None
    try:
        with open(path, "r", encoding="utf-8") as fh:
            record = json.load(fh)
    except (OSError, ValueError) as exc:
        logger.warning("Belegspeicher %s nicht lesbar: %s", path, exc)
        return None
    if not isinstance(record, dict):
        return None
    if (record.get("company_id"), record.get("source"), record.get("month")) != (int(company_id), source, month):
        return None
    return record


def save_record(record: Dict[str, Any], store_dir: Optional[Path] = None) -> Path:
    """Schreibt einen Monat atomar (temporäre Datei, dann umbenennen)."""
    path = record_path(record["company_id"], record["source"], record["month"], store_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=f".{path.stem}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(record, fh, ensure_ascii=False, indent=1)
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise
    return path


def is_month_complete(month: str, now: datetime) -> bool:
    return month < now.strftime("%Y-%m")


def build_record(company_id: int, source: str, month: str, query: Optional[str], items: List[Dict[str, Any]],
                 now: datetime) -> Dict[str, Any]:
    return {
        "version": STORE_VERSION,
        "company_id": int(company_id),
        "source": source,
        "month": month,
        "query": query,
        "fetched_at": now.replace(microsecond=0).isoformat(),
        "complete_month": is_month_complete(month, now),
        "status": "ok",
        "items": list(items),
    }


def record_is_current(record: Optional[Dict[str, Any]], month: str, now: datetime, query: Optional[str] = None) -> bool:
    """Ein gespeicherter Monat gilt, wenn er erfolgreich abgerufen wurde, zum erwarteten
    Suchbegriff passt und entweder abgeschlossen ist oder (laufender Monat) jünger als
    ``CURRENT_MONTH_MAX_AGE``."""
    if not isinstance(record, dict) or record.get("status") != "ok":
        return False
    if query is not None and record.get("query") != query:
        return False
    if is_month_complete(month, now):
        return True
    try:
        fetched = datetime.fromisoformat(str(record.get("fetched_at")))
    except (TypeError, ValueError):
        return False
    if fetched.tzinfo is None:
        fetched = fetched.replace(tzinfo=timezone.utc)
    return now - fetched < CURRENT_MONTH_MAX_AGE


# ── Abruf je Quelle ──────────────────────────────────────────────────────────

Fetcher = Callable[[str], bytes]


def expected_query(info: Dict[str, Any], source: str, month: str) -> Optional[str]:
    """Suchbegriff, mit dem ein gespeicherter Monat übereinstimmen muss; None, wenn die
    Quelle keinen Suchbegriff hat."""
    if source == SOURCE_GNEWS:
        return gnews_month_query(info["search_term"], month, info.get("exclude") or [])
    return None


def fetch_source_month(info: Dict[str, Any], source: str, month: str,
                       fetcher: Optional[Fetcher] = None) -> Tuple[List[Dict[str, Any]], Optional[str]]:
    """Ein Monat einer Quelle (Netz oder ``fetcher``); liefert ``(items, query)``."""
    if source == SOURCE_GNEWS:
        return fetch_gnews_month(info["search_term"], month, info.get("exclude") or [], fetcher)
    if source == SOURCE_EQS:
        from services.evidence_sources import fetch_eqs_month  # Schritt 5
        return fetch_eqs_month(info, month, fetcher)
    if source == SOURCE_GDELT:
        from services.evidence_sources import fetch_gdelt_month  # Schalter CONTEXT_GDELT
        return fetch_gdelt_month(info, month, fetcher)
    raise ValueError(f"Quelle '{source}' unbekannt.")


def month_record(
    info: Dict[str, Any],
    source: str,
    month: str,
    *,
    fetcher: Optional[Fetcher] = None,
    store_dir: Optional[Path] = None,
    now: Optional[datetime] = None,
    live: bool = True,
    sleep: Optional[Callable[[float], None]] = None,
    clock: Optional[Callable[[], float]] = None,
) -> Dict[str, Any]:
    """Gespeicherter Monat, sonst (wenn erlaubt) ein Abruf mit Speichern.

    Rückgabe ``{"record", "fetched_now", "error", "stale"}``: ``record`` ist None,
    wenn weder Speicher noch Abruf etwas liefern; ``stale`` heißt, dass ein
    älterer Stand des laufenden Monats gezeigt wird; ``error`` nennt den Grund,
    wenn ein Abruf nötig war und nicht möglich war. Wirft nicht.
    """
    now = now or utc_now()
    sleep = sleep or time.sleep
    clock = clock or time.monotonic
    company_id = int(info["company_id"])
    query = expected_query(info, source, month)
    record = load_record(company_id, source, month, store_dir)
    if record is not None and record_is_current(record, month, now, query):
        return {"record": record, "fetched_now": False, "error": None, "stale": False}
    stale = record if (record and record.get("status") == "ok" and (query is None or record.get("query") == query)) else None
    if not live or not live_fetch_enabled():
        error = None if stale is not None else (
            f"Kein gespeicherter Beleg für {month}; der Live-Abruf ist abgeschaltet ({LIVE_FETCH_ENV}=0)."
        )
        return {"record": stale, "fetched_now": False, "error": error, "stale": stale is not None}
    key = (source, company_id, month)
    failed = _failed_fetches.get(key)
    if failed and clock() - failed[0] < FAILED_FETCH_TTL:
        return {"record": stale, "fetched_now": False, "error": failed[1], "stale": stale is not None}
    throttle(source, sleep=sleep, clock=clock)
    try:
        items, used_query = fetch_source_month(info, source, month, fetcher)
    except Exception as exc:  # noqa: BLE001 – Netz, XML/JSON, Dateisystem: Quelle fällt aus, Rest läuft weiter
        reason = f"{SOURCE_LABELS.get(source, source)} für {month} nicht abrufbar ({type(exc).__name__}: {exc})."
        logger.warning("Belegabruf %s/%s/%s fehlgeschlagen: %s", source, company_id, month, exc)
        _failed_fetches[key] = (clock(), reason)
        return {"record": stale, "fetched_now": False, "error": reason, "stale": stale is not None}
    new = build_record(company_id, source, month, used_query, items, now)
    save_record(new, store_dir)
    _failed_fetches.pop(key, None)
    return {"record": new, "fetched_now": True, "error": None, "stale": False}


# ── Belege eines Fensters ────────────────────────────────────────────────────

def _in_window(item: Dict[str, Any], window: Dict[str, Any]) -> bool:
    date = item.get("date") or ""
    return bool(date) and window["from"] <= date[:7] <= window["to"]


def with_language(item: Dict[str, Any]) -> Dict[str, Any]:
    """Beleg mit Sprache: gespeicherte Einträge ohne ``language`` (ältere Stände) werden
    beim Lesen über die Titel-Heuristik ergänzt, ohne erneuten Abruf."""
    if item.get("language"):
        return item
    return {**item, "language": guess_language(item.get("title") or "")}


def _sort_key(item: Dict[str, Any]) -> str:
    return str(item.get("datetime") or item.get("date") or "")


def evidence_for_window(
    info: Dict[str, Any],
    window: Dict[str, Any],
    *,
    sources: Optional[List[str]] = None,
    fetchers: Optional[Dict[str, Fetcher]] = None,
    store_dir: Optional[Path] = None,
    now: Optional[datetime] = None,
    live: bool = True,
    sleep: Optional[Callable[[float], None]] = None,
    clock: Optional[Callable[[], float]] = None,
    events: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Alle Belege eines Fensters, neueste zuerst, mit Anzahl je Typ, Stand je Quelle und
    ``coverage`` (mindestens ein Beleg). Monate kommen aus dem Speicher oder werden
    (wenn erlaubt) abgerufen; ``fetchers`` ordnet Quellen Abruffunktionen zu (Tests).
    ``events`` sind bestätigte allgemeine Ereignisse (Schritt 7)."""
    now = now or utc_now()
    months = window_months(window)
    used_sources = list(sources) if sources else available_sources(info)
    items: List[Dict[str, Any]] = []
    summary: Dict[str, Dict[str, Any]] = {}
    for source in used_sources:
        fetcher = (fetchers or {}).get(source)
        s: Dict[str, Any] = {"label": SOURCE_LABELS.get(source, source), "months": len(months), "from_store": 0,
                             "fetched_now": 0, "missing": 0, "stale": 0, "errors": [], "fetched_at": None}
        for month in months:
            result = month_record(info, source, month, fetcher=fetcher, store_dir=store_dir, now=now, live=live,
                                  sleep=sleep, clock=clock)
            record = result["record"]
            if record is None:
                s["missing"] += 1
            else:
                s["fetched_now" if result["fetched_now"] else "from_store"] += 1
                if result["stale"]:
                    s["stale"] += 1
                fetched_at = record.get("fetched_at")
                if fetched_at and (s["fetched_at"] is None or fetched_at > s["fetched_at"]):
                    s["fetched_at"] = fetched_at
                items.extend(with_language(it) for it in record.get("items") or [] if _in_window(it, window))
            if result["error"]:
                s["errors"].append({"month": month, "error": result["error"]})
        if not s["errors"] and s["missing"] == 0:
            s["status"] = "ok"
        elif s["missing"] == len(months):
            s["status"] = "fehlgeschlagen"
        else:
            s["status"] = "teilweise"
        summary[source] = s
    if events:
        from services.evidence_service import global_event_items  # Schritt 7
        items.extend(global_event_items(events, window))
    items = dedupe(items)
    items.sort(key=_sort_key, reverse=True)
    counts = {TYPE_NEWS: 0, TYPE_ADHOC: 0, TYPE_GLOBAL: 0}
    for item in items:
        counts[item["source_type"]] = counts.get(item["source_type"], 0) + 1
    reason = None
    if not items:
        if summary and all(s["missing"] == s["months"] for s in summary.values()):
            errors = [e["error"] for s in summary.values() for e in s["errors"]]
            reason = errors[0] if errors else "Keine gespeicherten Belege für dieses Fenster."
        else:
            reason = "Kein Beleg im Fenster gefunden."
    return {
        "window": window,
        "items": items,
        "total": len(items),
        "counts": counts,
        "sources": summary,
        "coverage": bool(items),
        "reason": reason,
        "note": EVIDENCE_NOTE,
    }


__all__ += [
    "STORE_DIR", "LIVE_FETCH_ENV", "GDELT_ENV", "CURRENT_MONTH_MAX_AGE", "FAILED_FETCH_TTL", "EVIDENCE_NOTE",
    "live_fetch_enabled", "gdelt_enabled", "company_context_info", "available_sources",
    "record_path", "load_record", "save_record", "is_month_complete", "build_record", "record_is_current",
    "expected_query", "fetch_source_month", "month_record", "with_language", "evidence_for_window",
]


# ═════════════════════════════════════════════════════════════════════════════
# Belege zu einer Veränderung, einem Einzelmonat oder einer Auswahl (Schritt 3)
# ═════════════════════════════════════════════════════════════════════════════

OUTLIER_SUFFIX = "einzelmonat"


def resolve_anchor(company_id: int, anomaly_id: str, source: Optional[str] = None, dimension: Optional[str] = None,
                   status: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Veränderung (``"{source}:{dimension}:{YYYY-MM}"``) oder Einzelmonat
    (``"…:{YYYY-MM}:einzelmonat"``) zur Kennung, mit den Standardparametern der Erkennung
    neu berechnet (nur lesend). None, wenn die Kennung nicht unter den erkannten
    Markierungen ist; ValueError bei ungültiger Quelle, Dimension oder ungültigem Status."""
    from services.anomaly_service import company_anomalies  # lazy: Tests ohne DB

    parts = anomaly_id.split(":")
    if len(parts) == 4 and parts[3] == OUTLIER_SUFFIX and all(parts[:3]):
        kind = KIND_OUTLIER
    elif len(parts) == 3 and all(parts):
        kind = KIND_CHANGE
    else:
        return None
    if not is_period(parts[2]):
        return None
    source = source or parts[0]
    dimension = dimension or parts[1]
    detected = company_anomalies(company_id, source=source, dimension=dimension, status=status)
    if kind == KIND_CHANGE:
        anomaly = next((a for a in detected["anomalies"] if a["id"] == anomaly_id), None)
        if anomaly is None:
            return None
        return {"kind": kind, "id": anomaly_id, "source": source, "dimension": dimension, "status": status,
                "date": anomaly["date"], "direction": anomaly["direction"], "previous_period": anomaly.get("previous_period"),
                "gap_months": anomaly.get("gap_months"), "delta": anomaly.get("delta")}
    outlier = next((o for o in detected.get("outlier_months") or [] if o["id"] == anomaly_id), None)
    if outlier is None:
        return None
    return {"kind": kind, "id": anomaly_id, "source": source, "dimension": dimension, "status": status,
            "date": outlier["date"], "direction": outlier["direction"], "previous_period": None, "gap_months": None,
            "deviation": outlier.get("deviation")}


def _context_response(info: Dict[str, Any], anchor: Dict[str, Any], window: Dict[str, Any], evidence: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "company_id": info["company_id"],
        "company": info["name"],
        "search_term": info["search_term"],
        "anchor": anchor,
        **evidence,
    }


def context_for_anchor(
    company_id: int,
    anomaly_id: str,
    *,
    source: Optional[str] = None,
    dimension: Optional[str] = None,
    status: Optional[str] = None,
    window_before: int = DEFAULT_WINDOW_BEFORE,
    window_after: int = DEFAULT_WINDOW_AFTER,
    **evidence_kwargs: Any,
) -> Optional[Dict[str, Any]]:
    """Belege zu einer Veränderung oder einem Einzelmonat. Rückgabe None, wenn es das
    Unternehmen nicht gibt; ``{"anchor": None}``, wenn die Kennung unbekannt ist;
    ValueError bei ungültigen Angaben. ``evidence_kwargs`` gehen an ``evidence_for_window``."""
    info = company_context_info(company_id)
    if info is None:
        return None
    anchor = resolve_anchor(company_id, anomaly_id, source, dimension, status)
    if anchor is None:
        return {"anchor": None}
    if anchor["kind"] == KIND_CHANGE:
        window = window_for_change(anchor["date"], anchor["previous_period"], anchor["gap_months"], window_before, window_after)
    else:
        window = window_for_outlier(anchor["date"], window_before, window_after)
    evidence = evidence_for_window(info, window, **evidence_kwargs)
    return _context_response(info, anchor, window, evidence)


def context_for_selection(
    company_id: int,
    from_month: str,
    to_month: str,
    *,
    window_before: int = DEFAULT_WINDOW_BEFORE,
    window_after: int = DEFAULT_WINDOW_AFTER,
    **evidence_kwargs: Any,
) -> Optional[Dict[str, Any]]:
    """Belege zu einer frei gewählten Auswahl (E17). None bei unbekanntem Unternehmen;
    ValueError bei ungültigen Monaten oder Fenstergrößen."""
    info = company_context_info(company_id)
    if info is None:
        return None
    window = window_for_selection(from_month, to_month, window_before, window_after)
    anchor = {"kind": KIND_SELECTION, "id": None, "from": from_month, "to": to_month}
    evidence = evidence_for_window(info, window, **evidence_kwargs)
    return _context_response(info, anchor, window, evidence)


def paginate(result: Dict[str, Any], offset: int = 0, limit: int = 25) -> Dict[str, Any]:
    """Seite der Belegliste: ``items`` ab ``offset``, höchstens ``limit``; ``total`` bleibt."""
    items = result.get("items") or []
    return {**result, "items": items[offset:offset + limit], "offset": offset, "limit": limit, "total": len(items)}


__all__ += ["OUTLIER_SUFFIX", "resolve_anchor", "context_for_anchor", "context_for_selection", "paginate"]
