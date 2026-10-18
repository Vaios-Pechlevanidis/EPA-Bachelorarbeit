"""
Entfernt exakte Duplikate aus den Bewertungstabellen ``employee`` und ``candidates``.

Zwei Zeilen gelten als Duplikat, wenn sie zum selben Unternehmen gehören und in
denselben Feldern übereinstimmen wie bei der Duplikatzählung im Datenstand
(``services/data_status_service.py``, ``DUPLICATE_KEY_FIELDS_BY_SOURCE``):
Datum, Titel, Gesamtnote, Status und die Freitexte der Quelle. Zeilen ohne Datum
werden nicht verglichen (wie in der Zählung). Je Gruppe bleibt die Zeile mit der
kleinsten ``id`` (der erste Import), die übrigen werden gelöscht.

Standard ist ein Dry-Run: Es werden nur die Gruppen und die zu löschenden ids
ausgegeben. Erst mit ``--apply`` wird gelöscht. Vor dem Löschen eine Sicherung
der Tabellen anlegen (Supabase: Backups oder CSV-Export).

Verwendung (aus dem backend-Verzeichnis):
    uv run python scripts/remove_duplicates.py                    # Dry-Run, beide Tabellen
    uv run python scripts/remove_duplicates.py --source employee  # nur eine Tabelle
    uv run python scripts/remove_duplicates.py --company 4        # nur ein Unternehmen
    uv run python scripts/remove_duplicates.py --apply            # löscht

Exit-Codes: 0 = ok, 1 = Fehler beim Löschen.
"""

import argparse
import os
import sys
from typing import Any, Dict, List, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import database.supabase_client as db  # noqa: E402
from services.data_status_service import DUPLICATE_KEY_FIELDS_BY_SOURCE, SOURCES  # noqa: E402
from services.topic_average_rating_service import _fetch_all_rows  # noqa: E402


def key_fields(source: str) -> tuple:
    """Vergleichsfelder je Quelle: Unternehmen plus die Felder der Duplikatzählung."""
    return ("company_id", *DUPLICATE_KEY_FIELDS_BY_SOURCE[source])


def find_duplicate_groups(rows: List[Dict[str, Any]], fields: tuple) -> List[Dict[str, Any]]:
    """Gruppen gleicher Zeilen (mindestens zwei). ``keep`` ist die kleinste id,
    ``delete`` die übrigen ids aufsteigend. Zeilen ohne Datum zählen nicht mit."""
    groups: Dict[tuple, List[int]] = {}
    for r in rows:
        if not r.get("datum"):
            continue
        key = tuple(str(r.get(f)) for f in fields)
        groups.setdefault(key, []).append(r["id"])
    out = []
    for key, ids in groups.items():
        if len(ids) < 2:
            continue
        ids = sorted(ids)
        out.append({"key": dict(zip(fields, key)), "keep": ids[0], "delete": ids[1:]})
    return sorted(out, key=lambda g: g["keep"])


def fetch_rows(supabase, source: str, company_id: Optional[int] = None) -> List[Dict[str, Any]]:
    cols = ",".join(["id", *dict.fromkeys(key_fields(source))])
    query = supabase.table(source).select(cols)
    if company_id is not None:
        query = query.eq("company_id", company_id)
    return _fetch_all_rows(query.order("id"))


def delete_ids(supabase, source: str, ids: List[int]) -> int:
    """Löscht Zeile für Zeile über die id; liefert die Zahl gelöschter Zeilen."""
    deleted = 0
    for row_id in ids:
        res = supabase.table(source).delete().eq("id", row_id).execute()
        deleted += len(res.data or [])
    return deleted


def _short(value: Any, n: int = 40) -> str:
    s = "" if value is None else str(value).replace("\n", " ")
    return s if len(s) <= n else s[: n - 1] + "…"


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Entfernt exakte Duplikate aus employee und candidates. Ohne --apply nur Dry-Run."
    )
    parser.add_argument("--apply", action="store_true", help="Duplikate tatsächlich löschen")
    parser.add_argument("--source", choices=SOURCES, action="append", help="nur diese Tabelle (wiederholbar)")
    parser.add_argument("--company", type=int, help="nur dieses Unternehmen (company_id)")
    args = parser.parse_args(argv)

    supabase = db.get_supabase_client()
    total_delete, total_deleted, errors = 0, 0, 0

    for source in args.source or SOURCES:
        rows = fetch_rows(supabase, source, args.company)
        groups = find_duplicate_groups(rows, key_fields(source))
        n_delete = sum(len(g["delete"]) for g in groups)
        total_delete += n_delete
        print(f"\n{source}: {len(rows)} Zeilen, {len(groups)} Gruppen mit Duplikaten, {n_delete} überzählige Zeilen")
        for g in groups:
            k = g["key"]
            print(f"  Unternehmen {k['company_id']} · {_short(k['datum'], 10)} · {_short(k['titel'])!r} · "
                  f"Note {k['durchschnittsbewertung']}: behalte id {g['keep']}, lösche {g['delete']}")

        if args.apply and n_delete:
            ids = [i for g in groups for i in g["delete"]]
            try:
                deleted = delete_ids(supabase, source, ids)
            except Exception as exc:  # Abbruch melden, Rest nicht weiter löschen
                print(f"  FEHLER beim Löschen in {source}: {exc}")
                errors += 1
                continue
            total_deleted += deleted
            print(f"  gelöscht: {deleted} von {len(ids)} Zeilen")

    if not args.apply:
        print(f"\nDry-Run: {total_delete} Zeilen würden gelöscht. Zum Löschen --apply angeben.")
        return 0
    print(f"\nFertig: {total_deleted} Zeilen gelöscht.")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
