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

Exit-Codes: 0 = alle abgerufen, 1 = mindestens ein Abruf fehlgeschlagen,
2 = Unternehmen ohne Ticker oder unbekannt.
"""

import argparse
import os
import sys
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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
    args = parser.parse_args(argv)

    if args.ticker:
        targets = [(None, args.ticker.strip().upper())]
    elif args.company is not None:
        info = company_ticker_info(args.company)
        if not info or not info["ticker"]:
            print(f"Unternehmen {args.company}: kein Ticker ({(info or {}).get('peer_group') or 'unbekannt'})")
            return 2
        targets = [(args.company, info["ticker"])]
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
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
