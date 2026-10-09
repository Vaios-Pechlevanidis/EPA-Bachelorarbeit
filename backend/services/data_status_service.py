"""
Datenstand eines Unternehmens (FA-37, Zyklus 2, Inkrement 6 „Transparenz und Demo“).

Antwort von ``GET /api/companies/{id}/data-status``: je Quelle (Mitarbeitende,
Bewerbende) Anzahl der Bewertungen, erste und jüngste Bewertung, die drei
Zeitstempel der Tabellen, bewertete Monate und Eignung nach E4; dazu der Stand
des Kurs-Zwischenspeichers (E15) und des Belegspeichers (E18), falls vorhanden,
und der Vergleich mit der Plattform aus ``company_metadata.json``.

Bedeutung der Zeitstempel (Schema ``migrations/001`` und ``002``, Importcode
``services/excel_service.py``, geprüft am 2026-10-09):

- ``datum``: Datum der Bewertung auf Kununu, aus dem Export (``to_iso_dt``).
- ``update_datum``: letzte Änderung der Bewertung auf Kununu, aus dem Export;
  die Exporte der Unternehmen aus Zyklus 1 (id 3–20) enthalten die Spalte
  nicht, dort ist das Feld leer (der Spaltenstandard ``CURRENT_TIMESTAMP``
  greift nur, wenn der Import die Spalte weglässt; der Importcode schickt
  ``None``).
- ``created_at``: Zeitpunkt des Imports in die Datenbank, von der Datenbank
  gesetzt (``DEFAULT CURRENT_TIMESTAMP``); je Unternehmen ein Zeitpunkt.

Das Abrufdatum bei Kununu wird nicht gespeichert. Dem „letzten Abruf“ am
nächsten kommt ``created_at`` (Import; der Abruf lag davor), die jüngste
Bewertung (``datum``) nennt, bis wann der Datensatz reicht. Beides steht in
der Antwort; die Ansicht nennt beides.

Die Datenbank wird nur gelesen; Zwischenspeicher und Belegspeicher werden nur
gelesen, kein Abruf. Reine Funktionen für Tests ohne Datenbank.
"""

from __future__ import annotations

import json
import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from services.rating_series_service import (
    MIN_EVALUATED_MONTHS, MIN_REVIEWS_PER_MONTH, OVERALL_DIMENSION, build_monthly_series, evaluated_months,
    is_eligible, month_key,
)
from services.review_service import STATUS_LABELS, normalize_status
from services.topic_average_rating_service import _fetch_all_rows

logger = logging.getLogger(__name__)

SOURCES = ("employee", "candidates")
SOURCE_LABELS = {"employee": "Mitarbeitende", "candidates": "Bewerbende"}
ROW_COLUMNS = f"id,datum,update_datum,created_at,status,{OVERALL_DIMENSION}"

TIMESTAMP_FIELDS = ("datum", "update_datum", "created_at")
TIMESTAMP_MEANING = {
    "datum": "Datum der Bewertung auf Kununu (aus dem Export)",
    "update_datum": "letzte Änderung der Bewertung auf Kununu (aus dem Export; bei den Unternehmen aus Zyklus 1 nicht exportiert)",
    "created_at": "Import in die Datenbank (von der Datenbank gesetzt); dem letzten Abruf am nächsten, der Abruf lag davor",
}
LAST_FETCH_FIELD = "created_at"
PLATFORM_NOT_PROVIDED = "Vergleich mit der Plattform nicht hinterlegt"
PLATFORM_FIELDS = ("platform_review_count", "platform_count_date")
DATA_STATUS_NOTE = ("Datenstand: Kununu-Export, importiert in die Datenbank; die Zahl auf der Plattform kann "
                    "seitdem gestiegen sein. Das Abrufdatum bei Kununu ist nicht gespeichert.")


# ── Hilfen ──────────────────────────────────────────────────────────────────

def _iso_short(value: Any) -> Optional[str]:
    """Zeitstempel auf Sekunden gekürzt (``YYYY-MM-DDTHH:MM:SS``) oder None."""
    if not value:
        return None
    s = str(value)
    return s[:19] if len(s) >= 19 else s


def _day(value: Any) -> Optional[str]:
    s = _iso_short(value)
    return s[:10] if s else None


def timestamp_span(rows: List[Dict[str, Any]], field: str) -> Dict[str, Any]:
    """``{"min", "max", "n"}`` eines Zeitstempelfelds über die Zeilen."""
    values = [str(r[field]) for r in rows if r.get(field)]
    return {"min": _iso_short(min(values)) if values else None, "max": _iso_short(max(values)) if values else None, "n": len(values)}


def _months_between(first: Optional[str], last: Optional[str]) -> int:
    if not first or not last:
        return 0
    fy, fm = (int(x) for x in first.split("-"))
    ly, lm = (int(x) for x in last.split("-"))
    return (ly - fy) * 12 + (lm - fm) + 1


# ── Je Quelle ───────────────────────────────────────────────────────────────

def source_status(rows: List[Dict[str, Any]], source: str) -> Dict[str, Any]:
    """Datenstand einer Quelle aus ihren Zeilen (reine Funktion)."""
    series = build_monthly_series(rows, OVERALL_DIMENSION)
    dated = [r for r in rows if month_key(r.get("datum"))]
    datum = timestamp_span(rows, "datum")
    counts: Dict[str, int] = {key: 0 for key in STATUS_LABELS.get(source, {})}
    for r in rows:
        key = normalize_status(source, r.get("status"))
        counts[key] = counts.get(key, 0) + 1
    evaluated = evaluated_months(series)
    out: Dict[str, Any] = {
        "label": SOURCE_LABELS.get(source, source),
        "n_reviews": len(rows),
        "n_dated": len(dated),
        "n_undated": len(rows) - len(dated),
        "first_review": _day(datum["min"]),
        "last_review": _day(datum["max"]),
        "first_month": series[0]["period"] if series else None,
        "last_month": series[-1]["period"] if series else None,
        "months_in_span": len(series),
        "evaluated_months": evaluated,
        "eligible": is_eligible(series),
        "timestamps": {field: timestamp_span(rows, field) for field in TIMESTAMP_FIELDS},
        "last_import": _iso_short(timestamp_span(rows, LAST_FETCH_FIELD)["max"]),
        "status_counts": counts,
    }
    if source == "employee":
        # E13: Bei den Unternehmen aus Zyklus 1 gibt es keinen Wert für ehemalige
        # Mitarbeitende; „Angestellt“ heißt dort nur „mit Typangabe“.
        out["status_distinction"] = counts.get("ex-angestellt", 0) > 0
    return out


# ── Plattform (Metadatei, nur vom Autor gefüllt) ─────────────────────────────

def platform_comparison(meta: Optional[Dict[str, Any]], n_dataset: int) -> Dict[str, Any]:
    """Vergleich mit der Zahl auf der Plattform aus ``company_metadata.json``
    (``platform_review_count``, ``platform_count_date``); ohne Angabe der feste
    Hinweis. Kein Abruf bei Kununu."""
    meta = meta or {}
    count = meta.get("platform_review_count")
    try:
        count = int(count) if count is not None else None
    except (TypeError, ValueError):
        count = None
    if count is None or count <= 0:
        return {"available": False, "review_count": None, "count_date": None, "dataset_count": n_dataset,
                "coverage_share": None, "note": PLATFORM_NOT_PROVIDED}
    return {
        "available": True,
        "review_count": count,
        "count_date": meta.get("platform_count_date") or None,
        "dataset_count": n_dataset,
        "coverage_share": round(n_dataset / count, 4),
        "note": None,
    }


# ── Zwischenspeicher (nur lesen) ─────────────────────────────────────────────

def market_cache_status(company_id: int, cache_dir: Optional[Path] = None) -> Optional[Dict[str, Any]]:
    """Stand des Kurs-Zwischenspeichers (E15) ohne Abruf; None ohne Ticker."""
    from services.context_service import company_ticker_info, load_cached  # lazy: Tests ohne DB

    info = company_ticker_info(company_id)
    if info is None or not info.get("ticker"):
        return None
    record = load_cached(info["ticker"], cache_dir)
    prices = (record or {}).get("prices") or []
    return {
        "ticker": info["ticker"],
        "ticker_scope": info.get("ticker_scope"),
        "available": bool(prices),
        "fetched_at": _iso_short((record or {}).get("fetched_at")),
        "first_month": prices[0]["period"] if prices else None,
        "last_month": prices[-1]["period"] if prices else None,
        "months": len(prices),
        "source": (record or {}).get("source"),
    }


def _read_month_record(path: Path) -> Optional[Dict[str, Any]]:
    try:
        with open(path, "r", encoding="utf-8") as fh:
            record = json.load(fh)
    except (OSError, ValueError):
        return None
    return record if isinstance(record, dict) else None


def evidence_store_status(company_id: int, store_dir: Optional[Path] = None) -> Optional[Dict[str, Any]]:
    """Stand des Belegspeichers (E18) je Quelle ohne Abruf; None, wenn es das
    Unternehmen nicht gibt. Quellen ohne gespeicherten Monat erscheinen mit 0."""
    from services import evidence_service as ev  # lazy: Tests ohne DB
    from services.evidence_sources import SOURCE_LABELS as EVIDENCE_LABELS

    info = ev.company_context_info(company_id)
    if info is None:
        return None
    base = Path(store_dir or ev.STORE_DIR) / str(int(company_id))
    sources: Dict[str, Dict[str, Any]] = {}
    all_months: set = set()
    latest: Optional[str] = None
    for source in ev.available_sources(info):
        months: List[str] = []
        fetched: Optional[str] = None
        n_items = 0
        for path in sorted((base / source).glob("*.json")) if (base / source).is_dir() else []:
            record = _read_month_record(path)
            if not record or record.get("status") != "ok" or not ev.is_period(str(record.get("month"))):
                continue
            months.append(str(record["month"]))
            n_items += len(record.get("items") or [])
            stamp = _iso_short(record.get("fetched_at"))
            if stamp and (fetched is None or stamp > fetched):
                fetched = stamp
        all_months.update(months)
        if fetched and (latest is None or fetched > latest):
            latest = fetched
        sources[source] = {
            "label": EVIDENCE_LABELS.get(source, source),
            "months": len(months),
            "first_month": months[0] if months else None,
            "last_month": months[-1] if months else None,
            "n_items": n_items,
            "fetched_at": fetched,
        }
    return {
        "search_term": info.get("search_term"),
        "term_confirmed": info.get("term_confirmed"),
        "sources": sources,
        "months": len(all_months),
        "first_month": min(all_months) if all_months else None,
        "last_month": max(all_months) if all_months else None,
        "fetched_at": latest,
    }


# ── Zusammenführung ─────────────────────────────────────────────────────────

def assemble_status(
    company_id: int,
    name: Optional[str],
    rows_by_source: Dict[str, List[Dict[str, Any]]],
    meta: Optional[Dict[str, Any]] = None,
    market: Optional[Dict[str, Any]] = None,
    evidence: Optional[Dict[str, Any]] = None,
    now: Optional[datetime] = None,
) -> Dict[str, Any]:
    """Antwort aus den Teilen (reine Funktion)."""
    sources = {source: source_status(rows_by_source.get(source, []), source) for source in SOURCES}
    imports = [s["last_import"] for s in sources.values() if s["last_import"]]
    n_total = sum(s["n_reviews"] for s in sources.values())
    return {
        "company_id": int(company_id),
        "name": name,
        "generated_at": (now or datetime.now(timezone.utc)).replace(microsecond=0).isoformat(),
        "sources": sources,
        "n_reviews_total": n_total,
        "last_import": {"value": max(imports) if imports else None, "field": LAST_FETCH_FIELD,
                        "meaning": TIMESTAMP_MEANING[LAST_FETCH_FIELD]},
        "timestamp_fields": dict(TIMESTAMP_MEANING),
        "thresholds": {"min_reviews_per_month": MIN_REVIEWS_PER_MONTH, "min_evaluated_months": MIN_EVALUATED_MONTHS},
        "market_cache": market,
        "evidence_store": evidence,
        "platform": platform_comparison(meta, n_total),
        "note": DATA_STATUS_NOTE,
    }


def _fetch_rows(source: str, company_id: int) -> List[Dict[str, Any]]:
    from database.supabase_client import get_supabase_client  # lazy, je Thread eigener Client

    query = get_supabase_client().table(source).select(ROW_COLUMNS).eq("company_id", company_id).order("id")
    return _fetch_all_rows(query, page_size=1000)


def _company_name(company_id: int) -> Optional[str]:
    from database.supabase_client import get_supabase_client

    res = get_supabase_client().table("companies").select("id,name").eq("id", company_id).execute()
    rows = res.data or []
    return " ".join(str(rows[0].get("name") or "").split()) if rows else None


def company_data_status(company_id: int, now: Optional[datetime] = None) -> Optional[Dict[str, Any]]:
    """Datenstand aus Datenbank (nur lesend), Metadatei und Zwischenspeichern;
    None, wenn es das Unternehmen nicht gibt. Beide Quellen werden nebeneinander
    gelesen (je Thread ein eigener Supabase-Client)."""
    from services.context_service import load_metadata

    name = _company_name(company_id)
    if name is None:
        return None
    with ThreadPoolExecutor(max_workers=len(SOURCES), thread_name_prefix="data-status") as pool:
        rows_by_source = dict(zip(SOURCES, pool.map(lambda s: _fetch_rows(s, company_id), SOURCES)))
    try:
        meta = load_metadata().get(int(company_id))
    except (OSError, ValueError) as exc:  # Metadatei fehlt oder ist unlesbar: Vergleich nicht hinterlegt
        logger.warning("Metadatei nicht lesbar: %s", exc)
        meta = None
    if meta is not None and " ".join(str(meta.get("name") or "").split()).casefold() != name.casefold():
        meta = None
    market = None
    evidence = None
    try:
        market = market_cache_status(company_id)
    except Exception as exc:  # noqa: BLE001 – Zwischenspeicher ist Beiwerk, nie ein Fehler der Route
        logger.warning("Kurs-Zwischenspeicher für %s nicht lesbar: %s", company_id, exc)
    try:
        evidence = evidence_store_status(company_id)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Belegspeicher für %s nicht lesbar: %s", company_id, exc)
    return assemble_status(company_id, name, rows_by_source, meta, market, evidence, now)


__all__ = [
    "SOURCES", "SOURCE_LABELS", "TIMESTAMP_FIELDS", "TIMESTAMP_MEANING", "LAST_FETCH_FIELD", "PLATFORM_NOT_PROVIDED",
    "PLATFORM_FIELDS", "DATA_STATUS_NOTE", "timestamp_span", "source_status", "platform_comparison",
    "market_cache_status", "evidence_store_status", "assemble_status", "company_data_status",
]
