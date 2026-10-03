"""
Seed-Skript: Überträgt die Unternehmens-Metadaten (Ticker, ISIN, Branche,
Vergleichsgruppe) aus ``backend/data/company_metadata.json`` in die Tabelle
``companies`` der Supabase-Datenbank (Prüfpunkt 7 des Fundaments, Zyklus 2).

Voraussetzung: Migration ``backend/migrations/006_add_company_metadata.sql``
wurde ausgeführt (Spalten ``ticker``, ``isin``, ``sector``, ``peer_group``).
Fehlen die Spalten, meldet PostgREST den Fehlercode 42703; das Skript gibt dann
einen Hinweis aus und schreibt nichts.

Ablauf:
  1. JSON laden (Liste von Einträgen mit ``company_id``, ``name``,
     ``name_normalized``, ``ticker``, ``isin``, ``sector``, ``peer_group``, ...).
  2. Für jeden Eintrag das Unternehmen per ``company_id`` laden und den
     normalisierten Namen vergleichen (Whitespace reduziert, Groß-/Kleinschreibung
     ignoriert). Bei Abweichung oder fehlender ID wird abgebrochen, bevor
     irgendetwas geschrieben wird (Schutz gegen vertauschte IDs).
  3. Diff-Tabelle ausgeben: aktueller DB-Wert vs. neuer Wert je Spalte.
  4. Nur mit ``--apply`` werden die geänderten Zeilen per UPDATE geschrieben.
     Standard ist ein Dry-Run ohne Schreibzugriffe.

Verwendung (aus dem backend-Verzeichnis):
    uv run python scripts/seed_company_metadata.py                 # Dry-Run
    uv run python scripts/seed_company_metadata.py --apply         # schreibt
    uv run python scripts/seed_company_metadata.py --json other.json

Exit-Codes: 0 = ok, 1 = Validierungsfehler (Namen/IDs), 2 = Spalten fehlen
(nur im --apply-Modus), 3 = JSON nicht lesbar.
"""

import argparse
import json
import os
import sys
from typing import Any, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.supabase_client import get_supabase_client  # noqa: E402

META_COLUMNS: tuple[str, ...] = ("ticker", "isin", "sector", "peer_group")
PEER_GROUPS: tuple[str, ...] = (
    "Börsennotiert DE",
    "Börsennotiert Ausland",
    "Nicht börsennotiert",
    "Demo",
)
DEFAULT_JSON = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "company_metadata.json",
)
MISSING_COLUMNS_HINT = (
    "FEHLER: Die Spalten ticker/isin/sector/peer_group existieren in der Tabelle "
    "companies noch nicht (PostgREST-Fehlercode 42703).\n"
    "Bitte zuerst die Migration backend/migrations/006_add_company_metadata.sql "
    "in Supabase ausführen (SQL-Editor) und das Skript danach erneut starten."
)


def normalize_for_match(raw: Optional[str]) -> str:
    """Normalisiert einen Namen für den Vergleich: Whitespace (inkl. Zeilenumbrüche)
    auf einzelne Leerzeichen reduzieren, trimmen, casefold."""
    if raw is None:
        return ""
    return " ".join(str(raw).split()).casefold()


def is_missing_column_error(exc: Exception) -> bool:
    """True, wenn PostgREST eine fehlende Spalte meldet (SQLSTATE 42703)."""
    if getattr(exc, "code", None) == "42703":
        return True
    return "42703" in str(exc)


def load_entries(path: str) -> list[dict[str, Any]]:
    """Liest und validiert die JSON-Datei grob (Struktur, erlaubte Werte)."""
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, list) or not data:
        raise ValueError("JSON muss eine nicht-leere Liste von Einträgen sein")
    required = {"company_id", "name", "name_normalized", *META_COLUMNS}
    seen_ids: set[int] = set()
    for i, entry in enumerate(data):
        missing = required - set(entry)
        if missing:
            raise ValueError(f"Eintrag {i}: fehlende Felder {sorted(missing)}")
        cid = entry["company_id"]
        if not isinstance(cid, int) or isinstance(cid, bool) or cid in seen_ids:
            raise ValueError(f"Eintrag {i}: company_id {cid!r} ungültig oder doppelt")
        seen_ids.add(cid)
        if entry["peer_group"] not in PEER_GROUPS:
            raise ValueError(
                f"Eintrag {i} ({entry['name_normalized']}): peer_group "
                f"{entry['peer_group']!r} nicht in {PEER_GROUPS}"
            )
        if normalize_for_match(entry["name"]) != normalize_for_match(entry["name_normalized"]):
            raise ValueError(
                f"Eintrag {i}: name und name_normalized passen nicht zusammen "
                f"({entry['name']!r} vs. {entry['name_normalized']!r})"
            )
    return data


def columns_available(supabase) -> bool:
    """Prüft per Probe-Select, ob die Metadaten-Spalten in der DB existieren."""
    try:
        supabase.table("companies").select("id," + ",".join(META_COLUMNS)).limit(1).execute()
        return True
    except Exception as exc:  # noqa: BLE001
        if is_missing_column_error(exc):
            return False
        raise


def load_company(supabase, company_id: int, with_meta: bool) -> Optional[dict[str, Any]]:
    """Lädt eine Firma per ID; mit oder ohne Metadaten-Spalten."""
    cols = "id,name" + ("," + ",".join(META_COLUMNS) if with_meta else "")
    res = supabase.table("companies").select(cols).eq("id", company_id).limit(1).execute()
    rows = res.data or []
    return rows[0] if rows else None


def fmt(value: Any) -> str:
    """Formatiert einen Zellenwert für die Tabelle (NULL sichtbar machen)."""
    if value is None:
        return "NULL"
    return str(value)


def print_table(rows: list[list[str]], header: list[str]) -> None:
    """Gibt eine einfache Tabelle mit festen Spaltenbreiten aus."""
    widths = [len(h) for h in header]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(cell))
    line = "  ".join(h.ljust(widths[i]) for i, h in enumerate(header))
    print(line)
    print("  ".join("-" * w for w in widths))
    for row in rows:
        print("  ".join(cell.ljust(widths[i]) for i, cell in enumerate(row)))


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Setzt ticker/isin/sector/peer_group in companies aus company_metadata.json. "
                    "Ohne --apply nur Dry-Run (Diff-Tabelle, keine Schreibzugriffe)."
    )
    parser.add_argument("--json", default=DEFAULT_JSON, help="Pfad zur Metadaten-JSON (Standard: backend/data/company_metadata.json)")
    parser.add_argument("--apply", action="store_true", help="Änderungen tatsächlich per UPDATE schreiben")
    args = parser.parse_args(argv)

    try:
        entries = load_entries(args.json)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"FEHLER beim Lesen der JSON-Datei {args.json}: {exc}")
        return 3

    supabase = get_supabase_client()
    have_meta = columns_available(supabase)
    if not have_meta:
        print(MISSING_COLUMNS_HINT)
        if args.apply:
            print("Abbruch: --apply ist ohne die Spalten nicht möglich.")
            return 2
        print("Dry-Run wird fortgesetzt; aktuelle Werte werden als '<Spalte fehlt>' angezeigt.\n")

    errors: list[str] = []
    table_rows: list[list[str]] = []
    updates: list[tuple[int, str, dict[str, Any]]] = []

    for entry in entries:
        cid = entry["company_id"]
        row = load_company(supabase, cid, with_meta=have_meta)
        if row is None:
            errors.append(f"id={cid} ({entry['name_normalized']}): Unternehmen nicht in der DB gefunden")
            continue
        if normalize_for_match(row.get("name")) != normalize_for_match(entry["name_normalized"]):
            errors.append(
                f"id={cid}: Name in DB {row.get('name')!r} passt nicht zu JSON "
                f"{entry['name_normalized']!r} – Eintrag prüfen"
            )
            continue

        payload: dict[str, Any] = {}
        for col in META_COLUMNS:
            new_val = entry.get(col)
            if have_meta:
                cur_val = row.get(col)
                current = fmt(cur_val)
                changed = cur_val != new_val
            else:
                current = "<Spalte fehlt>"
                changed = True
            if changed:
                payload[col] = new_val
            table_rows.append([
                str(cid),
                entry["name_normalized"],
                col,
                current,
                fmt(new_val),
                "*" if changed else "",
            ])
        if payload:
            updates.append((cid, entry["name_normalized"], payload))

    print_table(table_rows, ["id", "Unternehmen", "Feld", "aktuell", "neu", "Änd."])
    print()
    print(f"{len(entries)} Einträge geprüft, {len(updates)} Unternehmen mit Änderungen, {len(errors)} Fehler.")

    if errors:
        print("\nABBRUCH – Validierung fehlgeschlagen (es wurde nichts geschrieben):")
        for err in errors:
            print(f"  - {err}")
        return 1

    if not args.apply:
        print("\nDry-Run: keine Änderungen geschrieben. Zum Schreiben --apply angeben.")
        return 0

    written = 0
    for cid, name, payload in updates:
        supabase.table("companies").update(payload).eq("id", cid).execute()
        written += 1
        print(f"  aktualisiert: id={cid} {name}: {payload}")
    print(f"\nFertig: {written} Unternehmen aktualisiert.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
