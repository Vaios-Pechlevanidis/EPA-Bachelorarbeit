"""
Füllt den Zwischenspeicher der Kursdaten (Zyklus 2, Inkrement 3, E15).

Ruft für alle Unternehmen mit Ticker oder für einen einzelnen Ticker die
Monatsschlusskurse über yfinance ab und schreibt je Ticker eine Datei
``backend/data/market/<ticker>.json``. Das Verzeichnis ist in ``.gitignore``;
die Kursdaten werden nicht eingecheckt. Die Datenbank wird nur gelesen
(``companies``), Ticker ohne Datenbankspalte kommen aus
``backend/data/company_metadata.json``.

Verwendung (aus dem backend-Verzeichnis):
    uv run python scripts/fetch_market_data.py                   # alle Ticker
    uv run python scripts/fetch_market_data.py --ticker SAP.DE   # ein Ticker
    uv run python scripts/fetch_market_data.py --company 19      # ein Unternehmen
    uv run python scripts/fetch_market_data.py --news            # zusätzlich Nachrichten (E16)
    uv run python scripts/fetch_market_data.py --summary         # Bestand, nur lesend

Mit ``--news`` werden außerdem die Nachrichten aller Unternehmen der Metadatei
(bzw. des mit ``--company`` gewählten) aus Google-News-RSS in
``backend/data/market/news/`` gespeichert.

``--summary`` ruft nichts ab und schreibt nichts (auch keine Datenbank): Es
gibt aus dem Zwischenspeicher eine Markdown-Tabelle aus, je Ticker erster und
letzter Monat der Kursreihe, Zahl der Monate, Währung, ``ticker_scope`` und
welche Kennzahlen mit welchem Stand vorliegen, dazu das Abrufdatum. Ticker,
Unternehmen und ``ticker_scope`` kommen aus der Metadatei; Dateien im
Zwischenspeicher ohne Eintrag dort stehen am Ende. Kurs- und Kennzahlwerte
erscheinen nicht. Beleg für die Abnahme von Inkrement 3 (Feature-Doku 04).

Exit-Codes: 0 = alle abgerufen, 1 = mindestens ein Abruf fehlgeschlagen,
2 = Unternehmen ohne Ticker oder unbekannt. Mit ``--summary``: 0 = für jeden
Ticker der Metadatei liegt eine Kursreihe vor, 1 = mindestens einer fehlt.
"""

import argparse
import json
import os
import sys
from datetime import date
from pathlib import Path
from typing import Any, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services import news_service  # noqa: E402
from services.context_service import (  # noqa: E402
    CACHE_DIR,
    company_ticker_info,
    fetch_and_store,
    load_cached,
    load_metadata,
)

SUMMARY_COLUMNS = (
    "Unternehmen (id)", "Ticker", "ticker_scope", "Erster Monat", "Letzter Monat", "Monate",
    "Währung", "Marktkapitalisierung", "Mitarbeitende", "Umsatz je Geschäftsjahr", "Abruf",
)


def tickers_from_metadata() -> list[tuple[int, str]]:
    """(company_id, ticker) aller Unternehmen mit Ticker; Datenbank vor Metadatei."""
    found = []
    metadata = load_metadata()
    for company_id in sorted(metadata):
        info = company_ticker_info(company_id, metadata=metadata)
        if info and info["ticker"]:
            found.append((company_id, info["ticker"]))
    return found


def _metric_state(metric: Optional[dict[str, Any]]) -> str:
    """Kennzahl als Verfügbarkeit mit Stand, ohne den Wert."""
    return f"Stand {metric['as_of']}" if metric and metric.get("as_of") else "fehlt"


def _revenue_state(revenue: Optional[list[dict[str, Any]]]) -> str:
    """Umsatz als Zahl der Geschäftsjahre mit erstem und letztem Ende, ohne Werte."""
    ends = sorted(str(r.get("fiscal_year_end", ""))[:7] for r in revenue or [] if r.get("fiscal_year_end"))
    if not ends:
        return "fehlt"
    return f"{len(ends)} GJ, Ende {ends[0]} bis {ends[-1]}"


def summary_rows(
    metadata: Optional[dict[int, dict[str, Any]]] = None,
    cache_dir: Optional[Path] = None,
) -> list[dict[str, Any]]:
    """Zeilen der Bestandstabelle (``--summary``); liest nur Metadatei und Zwischenspeicher.

    Je Ticker der Metadatei eine Zeile, danach Dateien im Zwischenspeicher ohne
    Eintrag in der Metadatei. ``in_metadata`` und ``has_prices`` dienen dem
    Exit-Code; die übrigen Felder sind die Spalten aus ``SUMMARY_COLUMNS``.
    """
    metadata = load_metadata() if metadata is None else metadata
    cache = Path(cache_dir or CACHE_DIR)
    companies: dict[str, list[dict[str, Any]]] = {}
    for company_id in sorted(metadata):
        ticker = str(metadata[company_id].get("ticker") or "").strip().upper()
        if ticker:
            companies.setdefault(ticker, []).append(metadata[company_id])
    cached: list[str] = []
    for path in sorted(cache.glob("*.json")) if cache.is_dir() else []:
        try:
            with open(path, "r", encoding="utf-8") as fh:
                ticker = json.load(fh).get("ticker")
        except (OSError, ValueError, AttributeError):
            continue
        if isinstance(ticker, str) and ticker not in companies:
            cached.append(ticker)

    rows = []
    for ticker in [*companies, *cached]:
        metas = companies.get(ticker, [])
        record = load_cached(ticker, cache)
        prices = (record or {}).get("prices") or []
        metrics = (record or {}).get("metrics") or {}
        scopes = sorted({m.get("ticker_scope") or "–" for m in metas})
        missing = "kein Zwischenspeicher" if record is None else "–"
        rows.append({
            "in_metadata": bool(metas),
            "has_prices": bool(prices),
            "Unternehmen (id)": ", ".join(f"{m.get('name')} ({m.get('company_id')})" for m in metas) or "nicht in der Metadatei",
            "Ticker": ticker,
            "ticker_scope": ", ".join(scopes) if scopes else "–",
            "Erster Monat": prices[0]["period"] if prices else missing,
            "Letzter Monat": prices[-1]["period"] if prices else missing,
            "Monate": str(len(prices)),
            "Währung": (record or {}).get("currency") or "–",
            "Marktkapitalisierung": _metric_state(metrics.get("market_cap")) if record else "–",
            "Mitarbeitende": _metric_state(metrics.get("employees")) if record else "–",
            "Umsatz je Geschäftsjahr": _revenue_state(metrics.get("revenue")) if record else "–",
            "Abruf": str((record or {}).get("fetched_at") or "–")[:10],
        })
    return rows


def format_summary(rows: list[dict[str, Any]]) -> str:
    """Markdown-Tabelle der Bestandszeilen."""
    lines = [
        "| " + " | ".join(SUMMARY_COLUMNS) + " |",
        "|" + "---|" * len(SUMMARY_COLUMNS),
    ]
    lines += ["| " + " | ".join(str(row[c]) for c in SUMMARY_COLUMNS) + " |" for row in rows]
    return "\n".join(lines)


def print_summary() -> int:
    """Gibt die Bestandstabelle aus (nur lesend); Exit-Code wie im Modulkopf."""
    rows = summary_rows()
    print(f"Zwischenspeicher {os.path.relpath(CACHE_DIR)}, ausgegeben am {date.today().isoformat()} "
          f"(nur lesend, ohne Abruf)\n")
    print(format_summary(rows))
    return 0 if all(r["has_prices"] for r in rows if r["in_metadata"]) else 1


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--ticker", help="nur diesen Ticker (Yahoo-Notation, z. B. SAP.DE)")
    group.add_argument("--company", type=int, help="nur dieses Unternehmen (company_id)")
    group.add_argument("--summary", action="store_true",
                       help="nur lesend: Bestand des Zwischenspeichers als Tabelle ausgeben, nichts abrufen")
    parser.add_argument("--news", action="store_true", help="zusätzlich Nachrichten speichern (Google News RSS)")
    args = parser.parse_args(argv)

    if args.summary:
        if args.news:
            parser.error("--summary ruft nichts ab und lässt sich nicht mit --news verbinden")
        return print_summary()

    if args.ticker:
        targets = [(None, args.ticker.strip().upper())]
    elif args.company is not None:
        info = company_ticker_info(args.company)
        if not info or (not info["ticker"] and not args.news):
            print(f"Unternehmen {args.company}: kein Ticker ({(info or {}).get('peer_group') or 'unbekannt'})")
            return 2
        targets = [(args.company, info["ticker"])] if info["ticker"] else []
    else:
        targets = tickers_from_metadata()

    print(f"Zwischenspeicher: {os.path.relpath(CACHE_DIR)}")
    failures = 0
    for company_id, ticker in targets:
        label = f"{ticker} (id {company_id})" if company_id is not None else ticker
        try:
            record = fetch_and_store(ticker)
        except Exception as exc:  # noqa: BLE001
            failures += 1
            print(f"  FEHLER  {label}: {type(exc).__name__}: {exc}")
            continue
        prices = record["prices"]
        print(f"  ok      {label}: {prices[0]['period']} bis {prices[-1]['period']}, "
              f"{len(prices)} Monate, {record['currency']}")
    if args.news and not args.ticker:
        failures += fetch_news([args.company] if args.company is not None else sorted(load_metadata()))
    return 1 if failures else 0


def fetch_news(company_ids: list[int]) -> int:
    """Speichert die Nachrichten je Unternehmen; Rückgabe: Zahl der Fehlschläge."""
    print("Nachrichten:")
    failures = 0
    for company_id in company_ids:
        info = company_ticker_info(company_id)
        if not info:
            continue
        try:
            record = news_service.fetch_and_store(company_id, info["name"] or "")
        except Exception as exc:  # noqa: BLE001
            failures += 1
            print(f"  FEHLER  id {company_id}: {type(exc).__name__}: {exc}")
            continue
        print(f"  ok      id {company_id} ({record['query']}): {len(record['items'])} Meldungen")
    return failures


if __name__ == "__main__":
    sys.exit(main())
