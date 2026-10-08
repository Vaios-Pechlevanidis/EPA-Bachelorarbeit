"""
Aktienkurs als Einordnung neben dem Bewertungsverlauf (Zyklus 2, Inkrement 3).

Kurs und Kennzahlen zeigen das Marktumfeld eines Unternehmens. Sie sind eine
Einordnung, keine Erklärung: Dieser Dienst berechnet keinen Zusammenhang
zwischen Kurs und Bewertungen und liefert keinen Vergleichswert.

Ablauf je Unternehmen:

1. Ticker aus ``companies.ticker`` (nur lesend). Fehlt die Spalte (Migration
   006 nicht eingespielt) oder der Wert, gilt ``backend/data/company_metadata.json``
   über ``company_id``, aber nur, wenn der Name dort zum Namen in der Datenbank
   passt (Schutz gegen andere IDs, etwa im In-Memory-Store).
2. Kursreihe aus dem Zwischenspeicher ``backend/data/market/<ticker>.json``
   (nicht eingecheckt, gefüllt mit ``scripts/fetch_market_data.py``).
3. Fehlt der Zwischenspeicher und ist ``MARKET_LIVE_FETCH`` nicht ``0``, wird
   einmal live über yfinance abgerufen und gespeichert. Schlägt das fehl, gibt
   es keinen Fehler, sondern ``available: false`` mit Begründung; derselbe
   Ticker wird dann für ``FAILED_FETCH_TTL`` Sekunden nicht erneut versucht.

Kursreihe: Monatsschlusskurse über den ganzen verfügbaren Zeitraum
(``interval="1mo"``, ``auto_adjust=True``, also um Splits und Dividenden
bereinigt), je Monat ``{"period": "YYYY-MM", "close": float}``. Der Monat des
Abrufs fehlt, weil er noch nicht abgeschlossen ist.

Kennzahlen (``metrics``) aus yfinance, ohne Schätzung fehlender Werte:

- ``market_cap``: aktuelle Marktkapitalisierung in Kurswährung, Stand = Datum
  des letzten Kurses (``regularMarketTime``), sonst Abrufdatum,
- ``employees``: aktuelle Zahl der Mitarbeitenden (``fullTimeEmployees``);
  yfinance nennt kein Stichtagsdatum, Stand ist daher das Abrufdatum,
- ``revenue``: Umsatz (``Total Revenue``) je Geschäftsjahr in Berichtswährung,
  so viele Jahre, wie yfinance liefert (meist vier), Stand = Ende des Geschäftsjahrs.

Fehlt ein Wert, bleibt die Kennzahl ``None`` bzw. das Jahr fehlt in ``revenue``.

Für das Aktien-Dashboard (``/aktie``, E16) speichert der Datensatz zusätzlich:

- ``analysts``: Zahl der Analystenempfehlungen je Stufe (stark kaufen bis stark
  verkaufen) für den Monat des Abrufs und die drei Monate davor
  (``Ticker.recommendations``), Stand = Abrufdatum,
- ``earnings``: Umsatz (``Total Revenue``) und Nettoergebnis (``Net Income``) je
  Geschäftsjahr und je Quartal in Berichtswährung, so weit yfinance sie liefert.

Ältere Zwischenspeicher ohne diese Felder bleiben für die Kursreihe gültig; die
Felder sind dann ``None``, bis ``scripts/fetch_market_data.py`` erneut läuft.

Der Netzabruf liegt hinter ``fetch_raw`` (austauschbar über den Parameter
``fetcher``); ``build_record`` formt die Rohdaten ohne Netzwerk um. So laufen
die Tests mit nachgebildeten Rohdaten.
"""

from __future__ import annotations

import json
import logging
import math
import os
import re
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)

BACKEND_DIR = Path(__file__).resolve().parent.parent
METADATA_PATH = BACKEND_DIR / "data" / "company_metadata.json"
CACHE_DIR = BACKEND_DIR / "data" / "market"

SOURCE = "Yahoo Finance über yfinance"
# Erlaubte Werte von ``ticker_scope`` in der Metadatei (E15): eigene Aktie des
# Unternehmens, Kurs der Konzernmutter (NTT DATA SE) oder Kurs einer
# börsennotierten Gesellschaft des Konzerns, den das Profil beschreibt (Carl Zeiss,
# Entscheidung D2 vom 2026-10-08).
TICKER_SCOPES = ("eigene Aktie", "Konzernmutter", "Konzerngesellschaft")
ADJUSTMENT = "Monatsschluss, um Splits und Dividenden bereinigt"
LIVE_FETCH_ENV = "MARKET_LIVE_FETCH"
FAILED_FETCH_TTL = 15 * 60  # Sekunden ohne neuen Live-Versuch nach einem Fehlschlag

_PERIOD_RE = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")

RawFetcher = Callable[[str], Dict[str, Any]]

# Fehlgeschlagene Live-Abrufe je Ticker: (Zeitpunkt, Begründung).
_failed_fetches: Dict[str, tuple[float, str]] = {}


# ---------------------------------------------------------------------------
# Ticker
# ---------------------------------------------------------------------------

def _normalize_name(raw: Optional[str]) -> str:
    """Wie ``scripts/seed_company_metadata.normalize_for_match``."""
    return " ".join(str(raw or "").split()).casefold()


def _is_missing_column_error(exc: Exception) -> bool:
    """True, wenn PostgREST eine fehlende Spalte meldet (SQLSTATE 42703), wie in
    ``routes/companies.py``."""
    return getattr(exc, "code", None) == "42703" or "42703" in str(exc)


def load_metadata(path: Path = METADATA_PATH) -> Dict[int, Dict[str, Any]]:
    """Einträge aus ``company_metadata.json`` nach ``company_id``."""
    with open(path, "r", encoding="utf-8") as fh:
        return {int(e["company_id"]): e for e in json.load(fh)}


def _company_row(company_id: int) -> Optional[Dict[str, Any]]:
    """Zeile aus ``companies`` (nur lesend); ohne Migration 006 nur id und name."""
    from database.supabase_client import get_supabase_client  # lazy, damit Tests ohne DB laufen

    supabase = get_supabase_client()
    try:
        res = supabase.table("companies").select("id,name,ticker,peer_group").eq("id", company_id).execute()
    except Exception as exc:  # noqa: BLE001
        if not _is_missing_column_error(exc):
            raise
        res = supabase.table("companies").select("id,name").eq("id", company_id).execute()
    rows = res.data or []
    return rows[0] if rows else None


def company_ticker_info(company_id: int, metadata: Optional[Dict[int, Dict[str, Any]]] = None) -> Optional[Dict[str, Any]]:
    """Ticker und Einordnung eines Unternehmens oder None, wenn es die ID nicht gibt.

    Rückgabe: ``{"company_id", "name", "ticker", "ticker_scope", "peer_group",
    "ticker_source"}`` mit ``ticker_source`` ``"db"``, ``"metadata"`` oder None.
    ``ticker_scope`` (``"eigene Aktie"``, ``"Konzernmutter"`` oder
    ``"Konzerngesellschaft"``, siehe ``TICKER_SCOPES``) steht nur in der
    Metadatei; ohne passenden Eintrag bleibt er None.
    """
    row = _company_row(company_id)
    if row is None:
        return None
    meta_all = load_metadata() if metadata is None else metadata
    meta = meta_all.get(int(company_id))
    if meta is not None and _normalize_name(meta.get("name")) != _normalize_name(row.get("name")):
        meta = None
    ticker = (row.get("ticker") or "").strip().upper() or None
    ticker_source = "db" if ticker else None
    if ticker is None and meta is not None and meta.get("ticker"):
        ticker = str(meta["ticker"]).strip().upper()
        ticker_source = "metadata"
    peer_group = row.get("peer_group") or (meta or {}).get("peer_group")
    return {
        "company_id": int(company_id),
        "name": row.get("name"),
        "ticker": ticker,
        "ticker_scope": (meta or {}).get("ticker_scope") if ticker else None,
        "peer_group": peer_group,
        "ticker_source": ticker_source,
    }


def ticker_for_company(company_id: int) -> Optional[str]:
    """Ticker in Yahoo-Notation oder None (kein Unternehmen oder kein Ticker)."""
    info = company_ticker_info(company_id)
    return info["ticker"] if info else None


# ---------------------------------------------------------------------------
# Abruf und Umformung
# ---------------------------------------------------------------------------

def fetch_raw(ticker: str) -> Dict[str, Any]:
    """Rohdaten über yfinance (Netzwerk). Einzige Stelle mit Netzabruf.

    Rückgabe: ``{"currency", "name", "history": [{"date": "YYYY-MM-DD",
    "close": float}, ...], "info": {...}, "revenue": [{"period_end":
    "YYYY-MM-DD", "value": float}, ...], "yfinance_version"}``. Fehlen Info oder
    Erfolgsrechnung, bleiben ``info`` bzw. ``revenue`` leer; die Kurse zählen.
    """
    import yfinance as yf  # erst hier: Tests und Start ohne Netz brauchen es nicht

    tk = yf.Ticker(ticker)
    hist = tk.history(period="max", interval="1mo", auto_adjust=True)
    history = [
        {"date": idx.strftime("%Y-%m-%d"), "close": float(close)}
        for idx, close in zip(hist.index, hist["Close"])
    ] if hist is not None and len(hist) else []
    meta = getattr(tk, "history_metadata", None) or {}
    info_keys = ("marketCap", "currency", "regularMarketTime", "fullTimeEmployees", "financialCurrency")
    try:
        full_info = tk.info or {}
        info = {k: full_info.get(k) for k in info_keys}
    except Exception as exc:  # noqa: BLE001 – Kennzahlen sind optional
        logger.info("yfinance info für %s nicht verfügbar: %s", ticker, exc)
        info = {}
    revenue = []
    income_annual = []
    try:
        stmt = tk.income_stmt
        if stmt is not None and "Total Revenue" in stmt.index:
            revenue = [
                {"period_end": col.strftime("%Y-%m-%d"), "value": val}
                for col, val in stmt.loc["Total Revenue"].items()
            ]
        income_annual = _income_rows(stmt)
    except Exception as exc:  # noqa: BLE001
        logger.info("yfinance income_stmt für %s nicht verfügbar: %s", ticker, exc)
    try:
        income_quarterly = _income_rows(tk.quarterly_income_stmt)
    except Exception as exc:  # noqa: BLE001
        logger.info("yfinance quarterly_income_stmt für %s nicht verfügbar: %s", ticker, exc)
        income_quarterly = []
    try:
        rec = tk.recommendations
        recommendations = rec.to_dict("records") if rec is not None and len(rec) else []
    except Exception as exc:  # noqa: BLE001
        logger.info("yfinance recommendations für %s nicht verfügbar: %s", ticker, exc)
        recommendations = []
    return {
        "currency": meta.get("currency"),
        "name": meta.get("longName") or meta.get("shortName"),
        "history": history,
        "info": info,
        "revenue": revenue,
        "income_annual": income_annual,
        "income_quarterly": income_quarterly,
        "recommendations": recommendations,
        "yfinance_version": getattr(yf, "__version__", None),
    }


def _income_rows(stmt: Any) -> List[Dict[str, Any]]:
    """Umsatz und Nettoergebnis je Spalte einer yfinance-Erfolgsrechnung."""
    if stmt is None or not len(stmt.columns):
        return []
    def row(name: str) -> Dict[Any, Any]:
        return stmt.loc[name].to_dict() if name in stmt.index else {}
    revenue, net_income = row("Total Revenue"), row("Net Income")
    return [
        {"period_end": col.strftime("%Y-%m-%d"), "revenue": revenue.get(col), "net_income": net_income.get(col)}
        for col in stmt.columns
    ]


def _finite(value: Any) -> Optional[float]:
    try:
        f = float(value)
    except (TypeError, ValueError):
        return None
    return f if math.isfinite(f) else None


def monthly_closes(history: List[Dict[str, Any]], fetched_at: datetime) -> List[Dict[str, Any]]:
    """Monatsreihe ``[{"period", "close"}]`` aus den Kursbalken.

    Je Kalendermonat zählt der letzte Balken (yfinance hängt teils einen
    zusätzlichen Balken mit Tagesdatum an). Fehlende Kurse entfallen. Der
    Monat des Abrufs und spätere Monate entfallen, weil sie nicht abgeschlossen sind.
    """
    current = fetched_at.strftime("%Y-%m")
    by_period: Dict[str, float] = {}
    for bar in sorted(history, key=lambda b: str(b.get("date"))):
        period = str(bar.get("date", ""))[:7]
        close = _finite(bar.get("close"))
        if not _PERIOD_RE.match(period) or close is None or period >= current:
            continue
        by_period[period] = round(close, 4)
    return [{"period": p, "close": c} for p, c in sorted(by_period.items())]


def build_metrics(raw: Dict[str, Any], fetched_at: datetime) -> Dict[str, Any]:
    """Kennzahlen aus Rohdaten; fehlende Werte bleiben leer, nichts wird geschätzt."""
    info = raw.get("info") or {}
    fetched_day = fetched_at.strftime("%Y-%m-%d")
    market_cap = _finite(info.get("marketCap"))
    price_time = _finite(info.get("regularMarketTime"))
    market_cap_day = (datetime.fromtimestamp(price_time, tz=timezone.utc).strftime("%Y-%m-%d")
                      if price_time else fetched_day)
    employees = _finite(info.get("fullTimeEmployees"))
    revenue_currency = info.get("financialCurrency") or raw.get("currency")
    revenue = sorted(
        (
            {"value": value, "unit": revenue_currency, "fiscal_year_end": str(r.get("period_end"))[:10],
             "basis": "geschaeftsjahr"}
            for r in raw.get("revenue") or []
            if (value := _finite(r.get("value"))) is not None
        ),
        key=lambda r: r["fiscal_year_end"],
    )
    return {
        "market_cap": ({"value": market_cap, "unit": info.get("currency") or raw.get("currency"),
                        "as_of": market_cap_day, "basis": "aktuell"}
                       if market_cap and market_cap > 0 else None),
        "employees": ({"value": int(employees), "unit": "Personen", "as_of": fetched_day, "basis": "aktuell"}
                      if employees and employees > 0 else None),
        "revenue": revenue if revenue_currency else [],
    }


RATINGS = ("strongBuy", "buy", "hold", "sell", "strongSell")
RATING_KEYS = ("strong_buy", "buy", "hold", "sell", "strong_sell")
_REL_MONTH_RE = re.compile(r"^(0|-\d+)m$")


def _shift_month(day: datetime, months: int) -> str:
    index = day.year * 12 + day.month - 1 + months
    return f"{index // 12}-{index % 12 + 1:02d}"


def build_analysts(raw: Dict[str, Any], fetched_at: datetime) -> Optional[Dict[str, Any]]:
    """Analystenempfehlungen je Monat (älteste zuerst) oder None.

    yfinance nennt den Monat relativ (``0m`` = laufender Monat, ``-1m`` = Vormonat);
    er wird auf den Monat des Abrufs bezogen. Monate ohne gültige Zahlen entfallen.
    """
    months = []
    for row in raw.get("recommendations") or []:
        match = _REL_MONTH_RE.match(str(row.get("period", "")))
        counts = [_finite(row.get(k)) for k in RATINGS]
        if not match or any(c is None or c < 0 for c in counts):
            continue
        entry = {"month": _shift_month(fetched_at, int(match.group(1))), **{k: int(c) for k, c in zip(RATING_KEYS, counts)}}
        entry["total"] = sum(entry[k] for k in RATING_KEYS)
        if entry["total"] > 0:
            months.append(entry)
    if not months:
        return None
    return {"as_of": fetched_at.strftime("%Y-%m-%d"), "months": sorted(months, key=lambda m: m["month"])}


def _earnings_rows(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out = []
    for r in rows or []:
        revenue, net_income = _finite(r.get("revenue")), _finite(r.get("net_income"))
        if revenue is None and net_income is None:
            continue
        out.append({"period_end": str(r.get("period_end"))[:10], "revenue": revenue, "net_income": net_income})
    return sorted(out, key=lambda r: r["period_end"])


def build_earnings(raw: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Umsatz und Nettoergebnis je Geschäftsjahr und Quartal oder None.

    Ein Zeitraum entfällt nur, wenn beide Werte fehlen; fehlt einer, bleibt er None.
    """
    annual = _earnings_rows(raw.get("income_annual"))
    quarterly = _earnings_rows(raw.get("income_quarterly"))
    if not annual and not quarterly:
        return None
    info = raw.get("info") or {}
    return {"currency": info.get("financialCurrency") or raw.get("currency"), "annual": annual, "quarterly": quarterly}


def build_record(ticker: str, raw: Dict[str, Any], fetched_at: Optional[datetime] = None) -> Dict[str, Any]:
    """Speicherbarer Datensatz aus Rohdaten (ohne Netzwerk)."""
    fetched_at = fetched_at or datetime.now(timezone.utc)
    version = raw.get("yfinance_version")
    return {
        "ticker": ticker,
        "ticker_name": raw.get("name"),
        "currency": raw.get("currency"),
        "fetched_at": fetched_at.replace(microsecond=0).isoformat(),
        "source": f"{SOURCE} {version}".strip() if version else SOURCE,
        "adjustment": ADJUSTMENT,
        "prices": monthly_closes(raw.get("history") or [], fetched_at),
        "metrics": build_metrics(raw, fetched_at),
        "analysts": build_analysts(raw, fetched_at),
        "earnings": build_earnings(raw),
    }


# ---------------------------------------------------------------------------
# Zwischenspeicher
# ---------------------------------------------------------------------------

def _cache_path(ticker: str, cache_dir: Optional[Path] = None) -> Path:
    safe = re.sub(r"[^A-Za-z0-9._-]", "_", ticker)
    return Path(cache_dir or CACHE_DIR) / f"{safe}.json"


def load_cached(ticker: str, cache_dir: Optional[Path] = None) -> Optional[Dict[str, Any]]:
    """Datensatz aus dem Zwischenspeicher oder None (fehlt oder unlesbar)."""
    path = _cache_path(ticker, cache_dir)
    if not path.exists():
        return None
    try:
        with open(path, "r", encoding="utf-8") as fh:
            record = json.load(fh)
    except (OSError, ValueError) as exc:
        logger.warning("Zwischenspeicher %s nicht lesbar: %s", path.name, exc)
        return None
    return record if isinstance(record, dict) and record.get("ticker") == ticker else None


def save_cached(record: Dict[str, Any], cache_dir: Optional[Path] = None) -> Path:
    """Schreibt den Datensatz atomar (temporäre Datei, dann umbenennen)."""
    path = _cache_path(record["ticker"], cache_dir)
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


def fetch_and_store(ticker: str, fetcher: Optional[RawFetcher] = None, cache_dir: Optional[Path] = None) -> Dict[str, Any]:
    """Ruft ab, formt um und speichert; Fehler des Abrufs werden weitergereicht.

    Liefert der Abruf keinen einzigen Monatskurs, wird nichts gespeichert und
    ein ValueError ausgelöst (etwa bei nicht mehr notierten Titeln).
    """
    raw = (fetcher or fetch_raw)(ticker)
    record = build_record(ticker, raw)
    if not record["prices"]:
        raise ValueError(f"yfinance liefert für {ticker} keine Monatskurse")
    save_cached(record, cache_dir)
    return record


def live_fetch_enabled() -> bool:
    return os.getenv(LIVE_FETCH_ENV, "1").strip() != "0"


def market_record(ticker: str, fetcher: Optional[RawFetcher] = None, cache_dir: Optional[Path] = None) -> tuple[Optional[Dict[str, Any]], Optional[str]]:
    """Datensatz zur Laufzeit: Zwischenspeicher, sonst einmal live.

    Rückgabe ``(record, None)`` oder ``(None, Begründung)``; wirft nicht.
    """
    record = load_cached(ticker, cache_dir)
    if record is not None:
        return record, None
    if not live_fetch_enabled():
        return None, (f"Keine gespeicherten Kursdaten für {ticker}; der Live-Abruf ist abgeschaltet "
                      f"({LIVE_FETCH_ENV}=0).")
    failed = _failed_fetches.get(ticker)
    if failed and time.monotonic() - failed[0] < FAILED_FETCH_TTL:
        return None, failed[1]
    try:
        return fetch_and_store(ticker, fetcher=fetcher, cache_dir=cache_dir), None
    except Exception as exc:  # noqa: BLE001 – Netz, yfinance, Dateisystem
        logger.warning("Kursabruf für %s fehlgeschlagen: %s", ticker, exc)
        reason = f"Kursdaten für {ticker} konnten nicht abgerufen werden ({type(exc).__name__}: {exc})."
        _failed_fetches[ticker] = (time.monotonic(), reason)
        return None, reason


# ---------------------------------------------------------------------------
# Antwort des Endpunkts
# ---------------------------------------------------------------------------

NO_TICKER_REASONS = {
    "Nicht börsennotiert": "Kein Aktienkurs: nicht börsennotiert",
    "Demo": "Kein Aktienkurs: synthetisches Demo-Unternehmen",
}
NO_TICKER_DEFAULT = "Kein Aktienkurs: kein Ticker hinterlegt"


def _check_period(name: str, value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    if not _PERIOD_RE.match(value):
        raise ValueError(f"{name} muss im Format YYYY-MM angegeben werden, nicht {value!r}")
    return value


def company_market(
    company_id: int,
    start: Optional[str] = None,
    end: Optional[str] = None,
    fetcher: Optional[RawFetcher] = None,
    cache_dir: Optional[Path] = None,
) -> Optional[Dict[str, Any]]:
    """Kursreihe eines Unternehmens für ``GET /analytics/company/{id}/market``.

    ``start``/``end`` (``YYYY-MM``, einschließlich) begrenzen ``prices``.
    None, wenn es das Unternehmen nicht gibt; ValueError bei ungültigem
    Zeitraum. Ohne Ticker oder ohne Kursdaten ``available: false`` mit ``reason``.
    """
    found = _market_with_record(company_id, start, end, fetcher, cache_dir)
    return found[0] if found else None


def company_finance(
    company_id: int,
    fetcher: Optional[RawFetcher] = None,
    cache_dir: Optional[Path] = None,
) -> Optional[Dict[str, Any]]:
    """Daten des Aktien-Dashboards (``GET /analytics/company/{id}/finance``, E16).

    Wie ``company_market`` ohne Zeitraum, dazu ``analysts`` und ``earnings``
    (je None, wenn yfinance oder der Zwischenspeicher sie nicht enthält).
    """
    found = _market_with_record(company_id, None, None, fetcher, cache_dir)
    if found is None:
        return None
    result, record = found
    result["analysts"] = (record or {}).get("analysts")
    result["earnings"] = (record or {}).get("earnings")
    return result


def _market_with_record(
    company_id: int,
    start: Optional[str],
    end: Optional[str],
    fetcher: Optional[RawFetcher],
    cache_dir: Optional[Path],
) -> Optional[tuple[Dict[str, Any], Optional[Dict[str, Any]]]]:
    """Antwort von ``company_market`` und der zugrunde liegende Datensatz."""
    start = _check_period("start", start)
    end = _check_period("end", end)
    if start and end and start > end:
        raise ValueError(f"start ({start}) liegt nach end ({end})")
    info = company_ticker_info(company_id)
    if info is None:
        return None
    result: Dict[str, Any] = {
        "company_id": int(company_id),
        "ticker": info["ticker"],
        "ticker_scope": info["ticker_scope"],
        "ticker_name": None,
        "currency": None,
        "available": False,
        "reason": None,
        "prices": [],
        "metrics": {},
        "fetched_at": None,
        "source": None,
    }
    if not info["ticker"]:
        result["reason"] = NO_TICKER_REASONS.get(info["peer_group"], NO_TICKER_DEFAULT)
        return result, None
    record, reason = market_record(info["ticker"], fetcher=fetcher, cache_dir=cache_dir)
    if record is None:
        result["reason"] = reason
        return result, None
    prices = [
        p for p in record.get("prices") or []
        if (start is None or p["period"] >= start) and (end is None or p["period"] <= end)
    ]
    result.update({
        "ticker_name": record.get("ticker_name"),
        "currency": record.get("currency"),
        "available": bool(record.get("prices")),
        "reason": None if record.get("prices") else f"Keine Monatskurse für {info['ticker']} gespeichert.",
        "prices": prices,
        "metrics": record.get("metrics") or {},
        "fetched_at": record.get("fetched_at"),
        "source": record.get("source"),
    })
    return result, record
