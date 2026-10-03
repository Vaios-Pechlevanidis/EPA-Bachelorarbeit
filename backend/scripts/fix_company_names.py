"""
Bereinigt Whitespace-Defekte in Unternehmensnamen der Tabelle ``companies``.

Gefunden werden Namen mit führenden/abschließenden Leerzeichen, Zeilenumbrüchen
oder mehrfachen Leerzeichen (z. B. ``'E.ON\\n'`` -> ``'E.ON'``,
``'NTT  DATA SE'`` -> ``'NTT DATA SE'``). Groß-/Kleinschreibung wird nicht
verändert.

Standard ist ein Dry-Run: Es wird nur eine Tabelle mit den betroffenen
Unternehmen (id, roher Name, normalisierter Name) ausgegeben. Erst mit
``--apply`` werden die Namen per UPDATE geschrieben. Würde die Bereinigung mit
dem Namen eines anderen Unternehmens kollidieren (UNIQUE-Constraint auf
``companies.name``), wird die Zeile als Konflikt markiert und übersprungen.

Verwendung (aus dem backend-Verzeichnis):
    uv run python scripts/fix_company_names.py           # Dry-Run
    uv run python scripts/fix_company_names.py --apply   # schreibt

Exit-Codes: 0 = ok, 1 = mindestens ein Konflikt (im --apply-Modus).
"""

import argparse
import os
import sys
from typing import Any, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.supabase_client import get_supabase_client  # noqa: E402
from services.topic_average_rating_service import _fetch_all_rows  # noqa: E402


def normalize_name(raw: Optional[str]) -> str:
    """Trimmt und reduziert jeglichen Whitespace (inkl. Zeilenumbrüche) auf
    einzelne Leerzeichen; Groß-/Kleinschreibung bleibt erhalten."""
    if raw is None:
        return ""
    return " ".join(str(raw).split())


def find_defects(companies: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Liefert die Unternehmen, deren Name von der normalisierten Form abweicht,
    inklusive Konfliktprüfung gegen alle anderen Namen (casefold)."""
    by_norm_cf: dict[str, list[int]] = {}
    for c in companies:
        by_norm_cf.setdefault(normalize_name(c.get("name")).casefold(), []).append(c["id"])

    defects: list[dict[str, Any]] = []
    for c in companies:
        raw = c.get("name")
        norm = normalize_name(raw)
        if raw == norm:
            continue
        others = [cid for cid in by_norm_cf.get(norm.casefold(), []) if cid != c["id"]]
        defects.append({
            "id": c["id"],
            "raw": raw,
            "normalized": norm,
            "conflict_with": others,
        })
    return defects


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Bereinigt Whitespace-Defekte in companies.name. Ohne --apply nur Dry-Run."
    )
    parser.add_argument("--apply", action="store_true", help="Bereinigte Namen tatsächlich per UPDATE schreiben")
    args = parser.parse_args(argv)

    supabase = get_supabase_client()
    companies = _fetch_all_rows(supabase.table("companies").select("id,name").order("id"))
    defects = find_defects(companies)

    print(f"{len(companies)} Unternehmen geladen, {len(defects)} mit Whitespace-Defekten.\n")
    if not defects:
        print("Nichts zu tun.")
        return 0

    header = ["id", "Name (roh, repr)", "Name (normalisiert, repr)", "Status"]
    rows = []
    for d in defects:
        status = "KONFLIKT mit id " + ",".join(map(str, d["conflict_with"])) if d["conflict_with"] else "ok"
        rows.append([str(d["id"]), repr(d["raw"]), repr(d["normalized"]), status])
    widths = [max(len(h), *(len(r[i]) for r in rows)) for i, h in enumerate(header)]
    print("  ".join(h.ljust(widths[i]) for i, h in enumerate(header)))
    print("  ".join("-" * w for w in widths))
    for r in rows:
        print("  ".join(cell.ljust(widths[i]) for i, cell in enumerate(r)))

    conflicts = [d for d in defects if d["conflict_with"]]
    if not args.apply:
        print("\nDry-Run: keine Änderungen geschrieben. Zum Schreiben --apply angeben.")
        return 0

    written = 0
    for d in defects:
        if d["conflict_with"]:
            print(f"  übersprungen (Konflikt): id={d['id']} {d['raw']!r}")
            continue
        supabase.table("companies").update({"name": d["normalized"]}).eq("id", d["id"]).execute()
        written += 1
        print(f"  aktualisiert: id={d['id']} {d['raw']!r} -> {d['normalized']!r}")
    print(f"\nFertig: {written} Namen bereinigt, {len(conflicts)} Konflikte übersprungen.")
    return 1 if conflicts else 0


if __name__ == "__main__":
    sys.exit(main())
