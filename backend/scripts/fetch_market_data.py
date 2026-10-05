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

Mit ``--news`` werden außerdem die Nachrichten aller Unternehmen der Metadatei
(bzw. des mit ``--company`` gewählten) aus Google-News-RSS in
``backend/data/market/news/`` gespeichert.

Exit-Codes: 0 = alle abgerufen, 1 = mindestens ein Abruf fehlgeschlagen,
2 = Unternehmen ohne Ticker oder unbekannt.
"""

import argparse
import os
import sys
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services import news_service  # noqa: E402
from services.context_service import (  # noqa: E402
    CACHE_DIR,
    company_ticker_info,
    fetch_and_store,
    load_metadata,
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


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--ticker", help="nur diesen Ticker (Yahoo-Notation, z. B. SAP.DE)")
    group.add_argument("--company", type=int, help="nur dieses Unternehmen (company_id)")
    parser.add_argument("--news", action="store_true", help="zusätzlich Nachrichten speichern (Google News RSS)")
    args = parser.parse_args(argv)

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
