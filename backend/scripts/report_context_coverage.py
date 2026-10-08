"""
Abdeckung der Markierungen mit externen Belegen (Zyklus 2, Inkrement 4,
Schritt 8, Kontrollpunkt 2).

Je Unternehmen der Anteil der Niveauwechsel und der auffälligen Einzelmonate
(Mitarbeitende, Gesamtbewertung, Standardparameter), deren Ereignisfenster
mindestens einen Beleg enthält, getrennt nach Typ (news, adhoc, global) und
nach Jahr der Markierung (bis 2018, ab 2019). Nur Zahlen, keine Titel. Die
Belege kommen allein aus dem Belegspeicher (kein Abruf); die Datenbank wird
nur gelesen. Bestätigte allgemeine Ereignisse zählen als Typ global.

Verwendung
----------
    cd backend
    uv run python scripts/report_context_coverage.py                 # Tabellen auf der Konsole (Markdown)
    uv run python scripts/report_context_coverage.py --md ../docs/feature-doku/bilder/abdeckung.md
    uv run python scripts/report_context_coverage.py --json data/calibration/context_coverage.json
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND_DIR)
sys.path.insert(0, os.path.join(BACKEND_DIR, "scripts"))

from fetch_context import company_anchors, list_companies  # noqa: E402
from services import evidence_service as ev  # noqa: E402
from services.evidence_sources import TYPE_ADHOC, TYPE_GLOBAL, TYPE_NEWS  # noqa: E402

TYPES = (TYPE_NEWS, TYPE_ADHOC, TYPE_GLOBAL)
YEAR_SPLIT = 2019                 # Markierungen bis 2018 / ab 2019
KINDS = (ev.KIND_CHANGE, ev.KIND_OUTLIER)


def marker_records(window_before: int = ev.DEFAULT_WINDOW_BEFORE, window_after: int = ev.DEFAULT_WINDOW_AFTER,
                   companies: Optional[List[Dict[str, Any]]] = None, verbose: bool = True) -> List[Dict[str, Any]]:
    """Je Markierung: Unternehmen, Art, Monat, Fenster und Anzahl Belege je Typ (nur Speicher)."""
    records: List[Dict[str, Any]] = []
    events = ev.load_global_events()
    for company in companies if companies is not None else list_companies():
        anchors = company_anchors(company["id"])
        if not anchors["eligible"]:
            continue
        info = ev.company_context_info(company["id"])
        if info is None:
            continue
        markers = [(ev.KIND_CHANGE, a["date"], ev.window_for_anomaly(a, window_before, window_after)) for a in anchors["anomalies"]]
        markers += [(ev.KIND_OUTLIER, o["date"], ev.window_for_outlier(o["date"], window_before, window_after)) for o in anchors["outliers"]]
        for kind, date, window in markers:
            result = ev.evidence_for_window(info, window, live=False, events=events)
            records.append({
                "company_id": company["id"], "company": company["name"], "kind": kind, "date": date,
                "window_from": window["from"], "window_to": window["to"],
                "counts": {t: int(result["counts"].get(t, 0)) for t in TYPES}, "total": int(result["total"]),
                "missing_months": sum(s["missing"] for s in result["sources"].values()),
            })
        if verbose:
            n = sum(1 for r in records if r["company_id"] == company["id"])
            covered = sum(1 for r in records if r["company_id"] == company["id"] and r["total"] > 0)
            print(f"  {company['name']:<40} Markierungen {n:>3}  mit Beleg {covered:>3}")
    return records


def _share(k: int, n: int) -> Optional[float]:
    return round(k / n, 4) if n else None


def _cell(k: int, n: int) -> str:
    return "–" if not n else f"{k}/{n} ({100 * k / n:.0f} %)"


def aggregate(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Anteile je Unternehmen und gesamt: je Art (Niveauwechsel, Einzelmonat) mit Beleg
    überhaupt und je Typ; je Jahresgruppe (bis 2018, ab 2019) mit Beleg überhaupt."""
    def bucket(date: str) -> str:
        return "bis 2018" if int(date[:4]) < YEAR_SPLIT else "ab 2019"

    def summarize(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
        out: Dict[str, Any] = {"n": len(rows), "covered": sum(1 for r in rows if r["total"] > 0)}
        out["share"] = _share(out["covered"], out["n"])
        for t in TYPES:
            k = sum(1 for r in rows if r["counts"].get(t, 0) > 0)
            out[t] = {"covered": k, "share": _share(k, out["n"])}
        return out

    def block(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
        return {
            "kinds": {kind: summarize([r for r in rows if r["kind"] == kind]) for kind in KINDS},
            "years": {b: summarize([r for r in rows if bucket(r["date"]) == b]) for b in ("bis 2018", "ab 2019")},
            "all": summarize(rows),
        }

    companies: Dict[int, Dict[str, Any]] = {}
    for r in records:
        companies.setdefault(r["company_id"], {"company_id": r["company_id"], "company": r["company"], "rows": []})["rows"].append(r)
    per_company = []
    for c in sorted(companies.values(), key=lambda c: c["company_id"]):
        per_company.append({"company_id": c["company_id"], "company": c["company"], **block(c["rows"])})
    uncovered = [{"company": r["company"], "kind": r["kind"], "date": r["date"], "missing_months": r["missing_months"]}
                 for r in records if r["total"] == 0]
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "n_markers": len(records),
        "companies": per_company,
        "total": block(records),
        "uncovered": sorted(uncovered, key=lambda u: (u["company"], u["date"])),
    }


def markdown_tables(summary: Dict[str, Any]) -> str:
    """Zwei Markdown-Tabellen: je Art und Typ, je Jahresgruppe; dazu die Markierungen ohne Beleg."""
    lines = []
    lines.append("| Unternehmen | Niveauwechsel mit Beleg | davon news | davon adhoc | davon global | Einzelmonate mit Beleg | davon news | davon adhoc | davon global |")
    lines.append("|---|---|---|---|---|---|---|---|---|")
    rows = summary["companies"] + [{"company": "**Gesamt**", **summary["total"]}]
    for c in rows:
        cells = []
        for kind in KINDS:
            k = c["kinds"][kind]
            cells.append(_cell(k["covered"], k["n"]))
            cells += [_cell(k[t]["covered"], k["n"]) for t in TYPES]
        lines.append(f"| {c['company']} | " + " | ".join(cells) + " |")
    lines.append("")
    lines.append("| Unternehmen | Markierungen bis 2018 mit Beleg | Markierungen ab 2019 mit Beleg | alle Markierungen mit Beleg |")
    lines.append("|---|---|---|---|")
    for c in rows:
        y = c["years"]
        lines.append(f"| {c['company']} | {_cell(y['bis 2018']['covered'], y['bis 2018']['n'])} | "
                     f"{_cell(y['ab 2019']['covered'], y['ab 2019']['n'])} | {_cell(c['all']['covered'], c['all']['n'])} |")
    if summary["uncovered"]:
        lines.append("")
        lines.append("Markierungen ohne Beleg (Unternehmen, Art, Monat; fehlende Monate im Speicher):")
        for u in summary["uncovered"]:
            lines.append(f"- {u['company']}, {u['kind']}, {u['date']}" + (f" ({u['missing_months']} Monate nicht im Speicher)" if u["missing_months"] else ""))
    return "\n".join(lines)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--window-before", type=int, default=ev.DEFAULT_WINDOW_BEFORE)
    parser.add_argument("--window-after", type=int, default=ev.DEFAULT_WINDOW_AFTER)
    parser.add_argument("--md", help="Markdown-Tabellen in diese Datei schreiben")
    parser.add_argument("--json", dest="json_out", help="Zusammenfassung als JSON-Datei")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args(argv)
    records = marker_records(args.window_before, args.window_after, verbose=not args.quiet)
    summary = aggregate(records)
    summary["window_before"], summary["window_after"] = args.window_before, args.window_after
    text = markdown_tables(summary)
    print(text)
    t = summary["total"]["all"]
    print(f"\nMarkierungen: {t['n']}, mit mindestens einem Beleg: {t['covered']}"
          + (f" ({100 * t['share']:.0f} %)" if t["share"] is not None else ""))
    if args.md:
        os.makedirs(os.path.dirname(os.path.abspath(args.md)), exist_ok=True)
        with open(args.md, "w", encoding="utf-8") as fh:
            fh.write(text + "\n")
        print(f"Tabellen gespeichert: {args.md}")
    if args.json_out:
        os.makedirs(os.path.dirname(os.path.abspath(args.json_out)), exist_ok=True)
        with open(args.json_out, "w", encoding="utf-8") as fh:
            json.dump(summary, fh, ensure_ascii=False, indent=2)
            fh.write("\n")
        print(f"Zusammenfassung gespeichert: {args.json_out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
