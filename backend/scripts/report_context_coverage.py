"""
Abdeckung der Markierungen mit externen Belegen (Zyklus 2, Inkrement 4,
Schritt 8, Kontrollpunkt 2; Vergleichsfenster seit der Nachschärfung).

Je Unternehmen der Anteil der Niveauwechsel und der auffälligen Einzelmonate
(Mitarbeitende, Gesamtbewertung, Standardparameter), deren Ereignisfenster
mindestens einen Beleg enthält, getrennt nach Typ (news, adhoc, global) und
nach Jahr der Markierung (bis 2018, ab 2019). Nur Zahlen, keine Titel. Die
Belege kommen allein aus dem Belegspeicher (kein Abruf); die Datenbank wird
nur gelesen. Bestätigte allgemeine Ereignisse zählen als Typ global.

Mit ``--comparison`` bekommt jede Markierung bis zu drei Vergleichsfenster
desselben Unternehmens (das Fenster um −12, +12, −24, +24 Monate verschoben,
ohne Überschneidung mit einem Markierungsfenster, nur innerhalb der bewerteten
Reihe; ``evidence_service.comparison_windows``). Je Unternehmen und gesamt
stehen dann für Markierungs- und Vergleichsfenster der Anteil mit mindestens
einem Beleg (news oder adhoc, dazu je Typ) sowie Median und Spannweite der
Anzahl Belege je Fenster. Fenster mit fehlenden Monaten im Speicher werden
ausgewiesen und nicht als "kein Beleg" gezählt. Die Zahlen sind beschreibend;
es gibt keine Signifikanzaussage und keinen Test, und ein Unterschied sagt
nichts über Ursachen.

Verwendung
----------
    cd backend
    uv run python scripts/report_context_coverage.py                 # Tabellen auf der Konsole (Markdown)
    uv run python scripts/report_context_coverage.py --comparison    # dazu die Vergleichsfenster
    uv run python scripts/report_context_coverage.py --md ../docs/feature-doku/bilder/abdeckung.md
    uv run python scripts/report_context_coverage.py --json data/calibration/context_coverage.json
"""

from __future__ import annotations

import argparse
import json
import os
import statistics
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND_DIR)
sys.path.insert(0, os.path.join(BACKEND_DIR, "scripts"))

from fetch_context import company_anchors, list_companies  # noqa: E402
from services import evidence_service as ev  # noqa: E402
from services.evidence_sources import SOURCE_EQS, SOURCE_GDELT, SOURCE_GNEWS, TYPE_ADHOC, TYPE_GLOBAL, TYPE_NEWS  # noqa: E402

TYPES = (TYPE_NEWS, TYPE_ADHOC, TYPE_GLOBAL)
EVIDENCE_TYPES = (TYPE_NEWS, TYPE_ADHOC)          # zählen im Vergleich als Beleg; global wird getrennt ausgewiesen
TYPE_SOURCES = {TYPE_NEWS: (SOURCE_GNEWS, SOURCE_GDELT), TYPE_ADHOC: (SOURCE_EQS,)}
YEAR_SPLIT = 2019                 # Markierungen bis 2018 / ab 2019
KINDS = (ev.KIND_CHANGE, ev.KIND_OUTLIER)
GROUP_MARKER = "markierung"
GROUP_COMPARISON = "vergleich"


def _window_record(info: Dict[str, Any], window: Dict[str, Any], events: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Belege eines Fensters aus dem Speicher (kein Abruf): Anzahl je Typ, Summe, fehlende
    Monate je Quelle."""
    result = ev.evidence_for_window(info, window, live=False, events=events)
    missing = {source: int(s["missing"]) for source, s in result["sources"].items()}
    return {
        "window_from": window["from"], "window_to": window["to"], "months": int(window["months"]),
        "counts": {t: int(result["counts"].get(t, 0)) for t in TYPES}, "total": int(result["total"]),
        "sources": sorted(result["sources"].keys()), "missing": missing, "missing_months": sum(missing.values()),
    }


def marker_records(window_before: int = ev.DEFAULT_WINDOW_BEFORE, window_after: int = ev.DEFAULT_WINDOW_AFTER,
                   companies: Optional[List[Dict[str, Any]]] = None, verbose: bool = True,
                   comparison: bool = False) -> List[Dict[str, Any]]:
    """Je Markierung: Unternehmen, Art, Monat, Fenster und Anzahl Belege je Typ (nur Speicher).
    Mit ``comparison`` trägt jede Markierung ihre Vergleichsfenster (``comparison``, je mit
    ``offset_months``) und dieselben Zahlen dafür."""
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
        marker_windows = [w for _, _, w in markers]
        for kind, date, window in markers:
            record = {"company_id": company["id"], "company": company["name"], "kind": kind, "date": date,
                      **_window_record(info, window, events)}
            if comparison:
                record["comparison"] = [
                    {"offset_months": c["offset_months"], **_window_record(info, c, events)}
                    for c in ev.comparison_windows(window, marker_windows, anchors.get("series_from"), anchors.get("series_to"))
                ]
            records.append(record)
        if verbose:
            mine = [r for r in records if r["company_id"] == company["id"]]
            covered = sum(1 for r in mine if r["total"] > 0)
            line = f"  {company['name']:<40} Markierungen {len(mine):>3}  mit Beleg {covered:>3}"
            if comparison:
                windows = [c for r in mine for c in r["comparison"]]
                line += f"  Vergleichsfenster {len(windows):>3}  fehlende Monate {sum(c['missing_months'] for c in windows):>3}"
            print(line)
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


# ── Vergleichsfenster ────────────────────────────────────────────────────────

def evidence_count(row: Dict[str, Any]) -> int:
    """Belege eines Fensters im Sinn des Vergleichs: news und adhoc, ohne global."""
    return sum(int(row["counts"].get(t, 0)) for t in EVIDENCE_TYPES)


def _is_complete(row: Dict[str, Any], sources: Optional[tuple] = None) -> bool:
    used = [s for s in row["sources"] if sources is None or s in sources]
    return bool(used) and all(int(row["missing"].get(s, 0)) == 0 for s in used)


def _spread(values: List[int]) -> Dict[str, Optional[float]]:
    if not values:
        return {"median": None, "min": None, "max": None}
    return {"median": float(statistics.median(values)), "min": min(values), "max": max(values)}


def window_stats(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Beschreibende Zahlen einer Fenstergruppe: Anzahl, davon vollständig im Speicher
    (keine fehlenden Monate), Anteil mit mindestens einem Beleg (news oder adhoc) unter den
    vollständigen, Median und Spannweite der Belege je vollständigem Fenster; je Typ dasselbe
    über die Fenster, die eine Quelle dieses Typs haben; allgemeine Ereignisse getrennt."""
    complete = [r for r in rows if _is_complete(r)]
    covered = sum(1 for r in complete if evidence_count(r) > 0)
    out: Dict[str, Any] = {
        "n": len(rows), "complete": len(complete), "incomplete": len(rows) - len(complete),
        "missing_months": sum(int(r["missing_months"]) for r in rows),
        "covered": covered, "share": _share(covered, len(complete)),
        **_spread([evidence_count(r) for r in complete]),
    }
    for t in EVIDENCE_TYPES:
        applicable = [r for r in rows if any(s in r["sources"] for s in TYPE_SOURCES[t])]
        complete_t = [r for r in applicable if _is_complete(r, TYPE_SOURCES[t])]
        covered_t = sum(1 for r in complete_t if int(r["counts"].get(t, 0)) > 0)
        out[t] = {"n": len(applicable), "complete": len(complete_t), "covered": covered_t,
                  "share": _share(covered_t, len(complete_t)), **_spread([int(r["counts"].get(t, 0)) for r in complete_t])}
    out[TYPE_GLOBAL] = {"n": len(rows), "with_event": sum(1 for r in rows if int(r["counts"].get(TYPE_GLOBAL, 0)) > 0)}
    return out


def aggregate_comparison(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Markierungs- gegen Vergleichsfenster, je Unternehmen und gesamt (``window_stats``);
    dazu je Unternehmen die Liste der Vergleichsfenster mit fehlenden Monaten je Quelle."""
    companies: Dict[int, Dict[str, Any]] = {}
    for r in records:
        c = companies.setdefault(r["company_id"], {"company_id": r["company_id"], "company": r["company"],
                                                   "markers": [], "windows": []})
        c["markers"].append(r)
        for comp in r.get("comparison") or []:
            c["windows"].append({"marker_kind": r["kind"], "marker_date": r["date"], "offset_months": comp["offset_months"],
                                 "from": comp["window_from"], "to": comp["window_to"], "months": comp["months"],
                                 "missing": comp["missing"], "missing_months": comp["missing_months"]})
    per_company = []
    all_markers: List[Dict[str, Any]] = []
    all_comparisons: List[Dict[str, Any]] = []
    for c in sorted(companies.values(), key=lambda c: c["company_id"]):
        comparisons = [comp for r in c["markers"] for comp in (r.get("comparison") or [])]
        per_company.append({
            "company_id": c["company_id"], "company": c["company"],
            "n_markers": len(c["markers"]), "n_comparison_windows": len(comparisons),
            "markers_without_comparison": sum(1 for r in c["markers"] if not r.get("comparison")),
            GROUP_MARKER: window_stats(c["markers"]), GROUP_COMPARISON: window_stats(comparisons),
            "windows": c["windows"],
        })
        all_markers += c["markers"]
        all_comparisons += comparisons
    return {
        "offsets": list(ev.COMPARISON_OFFSETS), "max_per_marker": ev.COMPARISON_MAX,
        "n_markers": len(all_markers), "n_comparison_windows": len(all_comparisons),
        "companies": per_company,
        "total": {GROUP_MARKER: window_stats(all_markers), GROUP_COMPARISON: window_stats(all_comparisons)},
        "note": ("Beschreibende Zahlen ohne Signifikanzaussage; ein Beleg ist eine zeitlich nahe Meldung, "
                 "keine Ursache. Allgemeine Ereignisse zählen nicht als Beleg und stehen getrennt."),
    }


def _spread_cell(stats: Dict[str, Any]) -> str:
    if stats["median"] is None:
        return "–"
    med = stats["median"]
    med_text = f"{med:.0f}" if float(med).is_integer() else f"{med:.1f}"
    return f"{med_text} ({stats['min']}–{stats['max']})"


def _group_cells(stats: Dict[str, Any]) -> List[str]:
    return [
        f"{stats['n']} ({stats['complete']})",
        _cell(stats["covered"], stats["complete"]),
        _cell(stats[TYPE_NEWS]["covered"], stats[TYPE_NEWS]["complete"]),
        _cell(stats[TYPE_ADHOC]["covered"], stats[TYPE_ADHOC]["complete"]),
        _spread_cell(stats),
    ]


def markdown_comparison(summary: Dict[str, Any]) -> str:
    """Markdown-Tabellen des Vergleichs: je Unternehmen und gesamt die Markierungs- und
    Vergleichsfenster (Anzahl, davon vollständig im Speicher, Anteil mit Beleg, je Typ, Median
    und Spannweite); dazu die Fenster je Unternehmen und die Fenster mit fehlenden Monaten."""
    lines = []
    lines.append("| Unternehmen | Markierungsfenster (vollständig) | mit Beleg | davon news | davon adhoc | Belege je Fenster: Median (Spannweite) "
                 "| Vergleichsfenster (vollständig) | mit Beleg | davon news | davon adhoc | Belege je Fenster: Median (Spannweite) |")
    lines.append("|---|---|---|---|---|---|---|---|---|---|---|")
    rows = summary["companies"] + [{"company": "**Gesamt**", **summary["total"]}]
    for c in rows:
        lines.append(f"| {c['company']} | " + " | ".join(_group_cells(c[GROUP_MARKER]) + _group_cells(c[GROUP_COMPARISON])) + " |")
    lines.append("")
    lines.append("Anteile beziehen sich auf die vollständig im Speicher liegenden Fenster (in Klammern); ein Beleg ist eine "
                 "Meldung (news) oder eine Ad-hoc-Mitteilung (adhoc), allgemeine Ereignisse zählen nicht. Die Zahlen sind "
                 "beschreibend, ohne Signifikanzaussage und ohne Aussage über Ursachen.")
    lines.append("")
    lines.append("| Unternehmen | Markierungen | ohne Vergleichsfenster | Vergleichsfenster | davon vollständig im Speicher | fehlende Monate (je Quelle gezählt) | Fenster mit allgemeinem Ereignis (Markierung / Vergleich) |")
    lines.append("|---|---|---|---|---|---|---|")
    for c in rows:
        comp = c[GROUP_COMPARISON]
        lines.append(f"| {c['company']} | {c.get('n_markers', summary['n_markers'])} | {c.get('markers_without_comparison', '')} | {comp['n']} | "
                     f"{comp['complete']} | {comp['missing_months']} | {c[GROUP_MARKER][TYPE_GLOBAL]['with_event']} / {comp[TYPE_GLOBAL]['with_event']} |")
    incomplete = [(c["company"], w) for c in summary["companies"] for w in c["windows"] if w["missing_months"]]
    if incomplete:
        lines.append("")
        lines.append("Vergleichsfenster mit fehlenden Monaten im Speicher (Unternehmen, Markierung, Versatz, Fenster; fehlende Monate je Quelle):")
        for company, w in incomplete:
            missing = ", ".join(f"{s} {n}" for s, n in sorted(w["missing"].items()) if n)
            lines.append(f"- {company}, {w['marker_kind']} {w['marker_date']}, {w['offset_months']:+d} Monate, {w['from']} – {w['to']} ({missing})")
    return "\n".join(lines)


# ── Ausgabe ──────────────────────────────────────────────────────────────────

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
    parser.add_argument("--comparison", action="store_true",
                        help="Vergleichsfenster je Markierung (−12, +12, −24, +24 Monate, höchstens drei) mit auswerten")
    parser.add_argument("--md", help="Markdown-Tabellen in diese Datei schreiben")
    parser.add_argument("--json", dest="json_out", help="Zusammenfassung als JSON-Datei")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args(argv)
    records = marker_records(args.window_before, args.window_after, verbose=not args.quiet, comparison=args.comparison)
    summary = aggregate(records)
    summary["window_before"], summary["window_after"] = args.window_before, args.window_after
    text = markdown_tables(summary)
    if args.comparison:
        summary["comparison"] = aggregate_comparison(records)
        text += "\n\n### Markierungs- gegen Vergleichsfenster\n\n" + markdown_comparison(summary["comparison"])
    print(text)
    t = summary["total"]["all"]
    print(f"\nMarkierungen: {t['n']}, mit mindestens einem Beleg: {t['covered']}"
          + (f" ({100 * t['share']:.0f} %)" if t["share"] is not None else ""))
    if args.comparison:
        comp = summary["comparison"]["total"]
        print(f"Vergleichsfenster: {summary['comparison']['n_comparison_windows']} zu {summary['comparison']['n_markers']} Markierungen; "
              f"vollständig im Speicher: {comp[GROUP_COMPARISON]['complete']}, fehlende Monate: {comp[GROUP_COMPARISON]['missing_months']}")
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
