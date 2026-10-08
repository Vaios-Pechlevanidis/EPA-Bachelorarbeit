"""
Einmalige Suche der EQS-companyUUID zu einem Firmennamen (Inkrement 4, Schritt 5).

EQS News (``www.eqs-news.com``) löst in der Meldungsroute nur die companyUUID eines
Emittenten auf, nicht den Klarnamen. Die Route ``companies?search=`` nennt zu einem
Suchwort die passenden Emittenten mit UUID und ISIN. Das Ergebnis wird nur
ausgegeben; der Autor trägt die bestätigte UUID in ``backend/data/company_metadata.json``
unter ``eqs`` ein (``uuid``, ``company_name``, ``isin``, ``found_at``, ``confirmed``).
Eine Anfrage je Suchwort, 2 s Abstand, Forschungs-Kennung; kein Schreibzugriff.

Verwendung
----------
    cd backend
    uv run python scripts/eqs_lookup.py "Deutsche Telekom" "Carl Zeiss"
"""

from __future__ import annotations

import argparse
import os
import sys
from typing import List, Optional

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND_DIR)

from services.evidence_sources import SOURCE_EQS, eqs_search_companies, throttle  # noqa: E402


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("names", nargs="+", help="Suchwörter, z. B. Firmenname ohne Rechtsform")
    args = parser.parse_args(argv)
    for name in args.names:
        throttle(SOURCE_EQS)
        try:
            hits = eqs_search_companies(name)
        except Exception as exc:  # noqa: BLE001
            print(f"{name}: Suche fehlgeschlagen ({type(exc).__name__}: {exc})")
            continue
        print(f"{name}: {len(hits)} Treffer")
        for h in hits:
            print(f"  {h['company_name']}  uuid={h['uuid']}  isin={h['isin']}  land={h['country']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
