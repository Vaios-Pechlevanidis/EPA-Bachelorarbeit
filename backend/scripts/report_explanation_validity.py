"""
Auswertung der Erklärungsansätze (Zyklus 2, Inkrement 5, A6): Markierungs- gegen
Vergleichsfenster.

Für jedes Markierungsfenster (Niveauwechsel und auffällige Einzelmonate der
geeigneten Unternehmen, Mitarbeitende, Gesamtbewertung, Standardparameter) und
jedes Vergleichsfenster aus E18 (das Fenster um −12, +12, −24, +24 Monate
verschoben, höchstens drei je Markierung, ``evidence_service.comparison_windows``)
wird dieselbe Rangfolge gerechnet wie in der Oberfläche
(``explanation_ranking.rank_evidence``): Belege allein aus dem Belegspeicher (kein
Abruf), kennzeichnende Begriffe und Themenverschiebung aus den Bewertungen der
Vergleichsfenster nach E12 (für einen Einzelmonat und ein Vergleichsfenster eines
Einzelmonats die Fenster nach E17, Auswahl = der Monat). Für ein Vergleichsfenster
gilt der Vergleichsanker wie ein markierter Monat. Die Stimmung der Titel wird
nicht berechnet (ohne Einfluss auf die Stufe).

Ausgabe je Unternehmen und gesamt, getrennt nach Markierung und Vergleich: Anteil
der Fenster mit mindestens einem Ansatz je Stufe (hoch, mittel, niedrig) und mit
mindestens einem Ansatz überhaupt (Stufe mindestens niedrig), Verteilung der
obersten Stufe, Median der Belege und Bündel je Fenster; dazu die
**Abdeckungsquote nach NFA-05**: der Anteil der Markierungsfenster mit mindestens
einem Erklärungsansatz (Stufe mindestens niedrig), auch je Art der Markierung.
Fenster mit fehlenden Monaten im Speicher werden ausgewiesen und nicht als „ohne
Ansatz“ gezählt. Nur Zahlen, keine Titel, beschreibend; es gibt keinen Test und
keine Signifikanzaussage, und ein Unterschied sagt nichts über Ursachen.

**Zusatzauswertung nach Referenzzeiträumen (E5, Iteration 2, festgelegt am
2026-10-08):** dieselbe Tabelle getrennt für Markierungen, die einen
Referenzzeitraum der Annotationsdatei (``--annotations``, Standard
``data/annotations.json``; Quelle Mitarbeitende, Gesamtbewertung) treffen, und
für die übrigen. Treffer nach E5, Regel 6 (``evaluate_detection.match_window``):
Markierungsmonat im Fenster ±1 Monat um den Zeitraum, bei nicht bewertetem
Nachbarmonat bis zu 3 Monate, gleiche Richtung; jede Markierung für sich geprüft.
Solange die Annotationsdatei keine Einträge hat, meldet der Bericht „nicht
verfügbar“; die Festlegung steht, der Lauf kommt nach der Annotation.

Verwendung
----------
    cd backend
    uv run python scripts/report_explanation_validity.py                     # Tabellen (Markdown) auf der Konsole
    uv run python scripts/report_explanation_validity.py --json data/calibration/explanation_validity.json
    uv run python scripts/report_explanation_validity.py --md ../docs/feature-doku/bilder/erklaerungsansaetze.md
    uv run python scripts/report_explanation_validity.py --annotations data/annotations.json
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

import validate_annotations as va  # noqa: E402
from evaluate_detection import match_window  # noqa: E402
from fetch_context import company_anchors, list_companies  # noqa: E402
from services import evidence_service as ev  # noqa: E402
from services import explanation_service as es  # noqa: E402
from services.event_categories import load_event_categories  # noqa: E402
from services.explanation_ranking import STAGE_NONE, STAGES, rank_evidence, rules, topic_shift_table  # noqa: E402
from services.review_service import fetch_review_rows_in_range, parse_day  # noqa: E402
from services.review_terms import company_terms, distinctive_terms  # noqa: E402

SOURCE = "employee"
DIMENSION = "durchschnittsbewertung"
DEFAULT_ANNOTATIONS = os.path.join(BACKEND_DIR, "data", "annotations.json")
REFERENCE_NOT_AVAILABLE = "nicht verfügbar"
REFERENCE_DEFINITION = ("Markierung trifft einen Referenzzeitraum der Annotationsdatei (E5, Regel 6): Markierungsmonat im "
                        "Fenster ±1 Monat um den Zeitraum, bei nicht bewertetem Nachbarmonat bis zu 3 Monate, gleiche "
                        "Richtung; jede Markierung für sich geprüft, Vergleichsfenster außen vor.")
GROUP_MARKER = "markierung"
GROUP_COMPARISON = "vergleich"
GROUPS = (GROUP_MARKER, GROUP_COMPARISON)
KINDS = (ev.KIND_CHANGE, ev.KIND_OUTLIER)
STAGES_WITH_ANY = [s for s in STAGES if s != STAGE_NONE]


# ── Referenzzeiträume (E5) ───────────────────────────────────────────────────

def load_reference(path: Optional[str]) -> Dict[str, Any]:
    """Annotationsdatei für die Zusatzauswertung: ``{"available", "reason", "by_company"}``;
    ``by_company`` ordnet dem normalisierten Namen die Einträge (Quelle Mitarbeitende,
    Gesamtbewertung) zu. Nicht verfügbar ohne Datei oder ohne Einträge."""
    if not path:
        return {"available": False, "reason": "keine Annotationsdatei angegeben", "by_company": {}}
    doc, err = va._load_json(path, "Annotationsdatei")
    if err:
        return {"available": False, "reason": err, "by_company": {}}
    entries = doc.get("annotations") if isinstance(doc, dict) else None
    if not isinstance(entries, list) or not entries:
        return {"available": False, "reason": f"Annotationsdatei ohne Einträge ({os.path.relpath(path, BACKEND_DIR)})", "by_company": {}}
    by_company: Dict[str, List[Dict[str, Any]]] = {}
    for ann in entries:
        if not isinstance(ann, dict) or ann.get("source") != SOURCE or ann.get("dimension") != DIMENSION:
            continue
        by_company.setdefault(va.normalize_company_name(str(ann.get("company", ""))), []).append(ann)
    return {"available": True, "reason": None, "by_company": by_company, "n_annotations": len(entries),
            "version": doc.get("version"), "path": os.path.relpath(path, BACKEND_DIR)}


def reference_hit(company: str, date: str, direction: Optional[str], evaluated: Any, reference: Optional[Dict[str, Any]]) -> Optional[bool]:
    """Trifft die Markierung (Monat ``date``, Richtung) einen Referenzzeitraum des Unternehmens
    nach E5, Regel 6? None, wenn die Referenz nicht verfügbar ist. Reine Funktion."""
    if not reference or not reference.get("available"):
        return None
    for ann in reference["by_company"].get(va.normalize_company_name(company), []):
        if ann.get("direction") != direction:
            continue
        lo, hi = match_window(ann["period_from"], ann["period_to"], evaluated or ())
        if lo <= date[:7] <= hi:
            return True
    return False


# ── Fenster ──────────────────────────────────────────────────────────────────

def review_windows(kind: str, anchor_from: str, anchor_to: str, anomaly: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Vergleichsfenster der Bewertungen: für einen Niveauwechsel nach E12 (mit den Grenzen
    der Nachbarabschnitte), für sein Vergleichsfenster nach E12 um den Vergleichsanker ohne
    Grenzen; für einen Einzelmonat und sein Vergleichsfenster nach E17 (Auswahl = der Monat)."""
    if kind == ev.KIND_CHANGE:
        return es.comparison_windows(anomaly if anomaly is not None else {"date": anchor_from})
    return es.period_windows(anchor_from, anchor_to)


def _window_record(info: Dict[str, Any], window: Dict[str, Any], windows: Dict[str, Any], rows: List[Dict[str, Any]],
                   categories: List[Dict[str, Any]], exclude: set) -> Dict[str, Any]:
    """Rangfolge eines Fensters aus dem Speicher (kein Abruf, keine Stimmung): Zahlen je Stufe."""
    by_window = es.split_rows_by_window(rows, windows)
    evidence = ev.evidence_for_window(info, window, live=False, events=[])
    terms = distinctive_terms(by_window["before"], by_window["after"], source=SOURCE, exclude=exclude)
    topics = topic_shift_table(by_window["before"], by_window["after"], SOURCE)
    ranked = rank_evidence(evidence["items"], window, terms=terms, topics=topics, exclude=exclude, categories=categories,
                           analyzer=None, kind=window["kind"])
    missing = {source: int(s["missing"]) for source, s in evidence["sources"].items()}
    top = ranked["explanations"][0]["confidence"] if ranked["explanations"] else None
    return {
        "window_from": window["from"], "window_to": window["to"], "months": int(window["months"]),
        "review_before": {"from": windows["before"]["from"], "to": windows["before"]["to"], "n": len(by_window["before"])},
        "review_after": {"from": windows["after"]["from"], "to": windows["after"]["to"], "n": len(by_window["after"])},
        "n_items": ranked["n_items"], "n_bundles": ranked["n_bundles"], "n_by_stage": ranked["n_by_stage"],
        "state": ranked["state"], "top_stage": top, "n_terms": len(terms),
        "n_shifted_topics": sum(1 for t in topics if t["share_shift_pp"] is not None and not t["low_basis"]
                                and abs(t["share_shift_pp"]) >= rules()["topic_shift_min_pp"]),
        "sources": sorted(evidence["sources"].keys()), "missing": missing, "missing_months": sum(missing.values()),
    }


def _rows_for(company_id: int, windows: Dict[str, Any]) -> List[Dict[str, Any]]:
    return fetch_review_rows_in_range(SOURCE, company_id, parse_day(windows["before"]["start"], "start"),
                                      parse_day(windows["after"]["end"], "end"))


def window_records(window_before: int = ev.DEFAULT_WINDOW_BEFORE, window_after: int = ev.DEFAULT_WINDOW_AFTER,
                   companies: Optional[List[Dict[str, Any]]] = None, verbose: bool = True,
                   reference: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """Je Markierungsfenster und je Vergleichsfenster ein Datensatz mit den Zahlen der
    Rangfolge (nur lesend: Datenbank und Belegspeicher). ``reference`` (``load_reference``)
    setzt je Markierung ``reference_hit`` (True/False; None ohne Referenz)."""
    records: List[Dict[str, Any]] = []
    categories = load_event_categories()
    for company in companies if companies is not None else list_companies():
        anchors = company_anchors(company["id"])
        if not anchors["eligible"]:
            continue
        info = ev.company_context_info(company["id"])
        if info is None:
            continue
        exclude = company_terms(info.get("name"), info.get("search_term"))
        markers = [(ev.KIND_CHANGE, a, ev.window_for_anomaly(a, window_before, window_after)) for a in anchors["anomalies"]]
        markers += [(ev.KIND_OUTLIER, o, ev.window_for_outlier(o["date"], window_before, window_after)) for o in anchors["outliers"]]
        marker_windows = [w for _, _, w in markers]
        for kind, anchor, window in markers:
            windows = review_windows(kind, window["anchor_from"], window["anchor_to"], anchor if kind == ev.KIND_CHANGE else None)
            records.append({
                "company_id": company["id"], "company": company["name"], "group": GROUP_MARKER, "kind": kind,
                "date": anchor["date"], "direction": anchor.get("direction"), "offset_months": 0,
                "reference_hit": reference_hit(company["name"], anchor["date"], anchor.get("direction"),
                                               anchors.get("evaluated_months"), reference),
                **_window_record(info, window, windows, _rows_for(company["id"], windows), categories, exclude),
            })
            for comp in ev.comparison_windows(window, marker_windows, anchors.get("series_from"), anchors.get("series_to")):
                cw = review_windows(kind, comp["anchor_from"], comp["anchor_to"])
                records.append({
                    "company_id": company["id"], "company": company["name"], "group": GROUP_COMPARISON, "kind": kind,
                    "date": anchor["date"], "direction": anchor.get("direction"), "offset_months": comp["offset_months"],
                    "reference_hit": None,
                    **_window_record(info, comp, cw, _rows_for(company["id"], cw), categories, exclude),
                })
        if verbose:
            mine = [r for r in records if r["company_id"] == company["id"]]
            n_m = sum(1 for r in mine if r["group"] == GROUP_MARKER)
            n_c = len(mine) - n_m
            with_m = sum(1 for r in mine if r["group"] == GROUP_MARKER and r["state"] == "ansaetze")
            with_c = sum(1 for r in mine if r["group"] == GROUP_COMPARISON and r["state"] == "ansaetze")
            print(f"  {company['name']:<40} Markierungen {n_m:>3} mit Ansatz {with_m:>3}  Vergleichsfenster {n_c:>3} mit Ansatz {with_c:>3}")
    return records


# ── Auswertung ───────────────────────────────────────────────────────────────

def _share(k: int, n: int) -> Optional[float]:
    return round(k / n, 4) if n else None


def _is_complete(row: Dict[str, Any]) -> bool:
    return bool(row.get("sources")) and int(row.get("missing_months", 0)) == 0


def _median(values: List[float]) -> Optional[float]:
    return float(statistics.median(values)) if values else None


def group_stats(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Beschreibende Zahlen einer Fenstergruppe: Anzahl, davon vollständig im Speicher,
    je Stufe der Anteil der vollständigen Fenster mit mindestens einem Bündel dieser Stufe,
    Anteil mit mindestens einem Ansatz (Stufe mindestens niedrig), Verteilung der obersten
    Stufe, Median von Belegen, Bündeln und Begriffen je Fenster."""
    complete = [r for r in rows if _is_complete(r)]
    n = len(complete)
    out: Dict[str, Any] = {
        "n": len(rows), "complete": n, "incomplete": len(rows) - n,
        "missing_months": sum(int(r.get("missing_months", 0)) for r in rows),
        "with_any": sum(1 for r in complete if r["state"] == "ansaetze"),
    }
    out["share_any"] = _share(out["with_any"], n)
    out["by_stage"] = {}
    for stage in STAGES_WITH_ANY:
        k = sum(1 for r in complete if int(r["n_by_stage"].get(stage, 0)) > 0)
        out["by_stage"][stage] = {"windows": k, "share": _share(k, n)}
    out["top_stage"] = {stage: sum(1 for r in complete if r["top_stage"] == stage) for stage in STAGES_WITH_ANY}
    out["top_stage"]["offen"] = sum(1 for r in complete if r["top_stage"] is None)
    out["median_items"] = _median([r["n_items"] for r in complete])
    out["median_bundles"] = _median([r["n_bundles"] for r in complete])
    out["median_terms"] = _median([r["n_terms"] for r in complete])
    out["windows_with_terms"] = sum(1 for r in complete if r["n_terms"] > 0)
    return out


def aggregate(records: List[Dict[str, Any]], reference: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Je Unternehmen und gesamt: ``group_stats`` für Markierungs- und Vergleichsfenster, je
    Art der Markierung; Abdeckungsquote nach NFA-05 (Markierungsfenster mit mindestens einem
    Ansatz unter den vollständigen Fenstern), gesamt und je Art. Dazu ``referenz``: dieselben
    Zahlen getrennt für Markierungen mit und ohne Referenzzeitraum (E5), sofern verfügbar."""
    available = bool(reference and reference.get("available")) and any(r.get("reference_hit") is not None for r in records)
    reason = None if available else ((reference or {}).get("reason") or REFERENCE_NOT_AVAILABLE)

    def block(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
        markers = [r for r in rows if r["group"] == GROUP_MARKER]
        comparisons = [r for r in rows if r["group"] == GROUP_COMPARISON]
        m = group_stats(markers)
        if available:
            referenz: Dict[str, Any] = {
                "available": True, "definition": REFERENCE_DEFINITION,
                "treffer": group_stats([r for r in markers if r.get("reference_hit") is True]),
                "uebrige": group_stats([r for r in markers if r.get("reference_hit") is False]),
            }
        else:
            referenz = {"available": False, "status": REFERENCE_NOT_AVAILABLE, "reason": reason, "definition": REFERENCE_DEFINITION}
        return {
            "n_markers": len(markers), "n_comparison_windows": len(comparisons),
            GROUP_MARKER: m, GROUP_COMPARISON: group_stats(comparisons),
            "referenz": referenz,
            "kinds": {kind: {GROUP_MARKER: group_stats([r for r in markers if r["kind"] == kind]),
                             GROUP_COMPARISON: group_stats([r for r in comparisons if r["kind"] == kind])} for kind in KINDS},
            "coverage_nfa05": {
                "definition": "Anteil der Markierungsfenster (vollständig im Speicher) mit mindestens einem Erklärungsansatz der Stufe mindestens niedrig",
                "covered": m["with_any"], "n": m["complete"], "share": m["share_any"],
                "by_kind": {kind: {"covered": group_stats([r for r in markers if r["kind"] == kind])["with_any"],
                                   "n": group_stats([r for r in markers if r["kind"] == kind])["complete"],
                                   "share": group_stats([r for r in markers if r["kind"] == kind])["share_any"]} for kind in KINDS},
            },
        }

    companies: Dict[int, Dict[str, Any]] = {}
    for r in records:
        companies.setdefault(r["company_id"], {"company_id": r["company_id"], "company": r["company"], "rows": []})["rows"].append(r)
    per_company = [{"company_id": c["company_id"], "company": c["company"], **block(c["rows"])}
                   for c in sorted(companies.values(), key=lambda c: c["company_id"])]
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": SOURCE, "offsets": list(ev.COMPARISON_OFFSETS), "max_per_marker": ev.COMPARISON_MAX,
        "rules": rules(),
        "reference": {"available": available, "reason": reason, "definition": REFERENCE_DEFINITION,
                      **({k: reference[k] for k in ("path", "version", "n_annotations") if k in reference} if available and reference else {})},
        "companies": per_company,
        "total": block(records),
        "windows": [{k: r.get(k) for k in ("company", "group", "kind", "date", "offset_months", "window_from", "window_to", "n_items",
                                           "n_bundles", "n_by_stage", "state", "top_stage", "n_terms", "n_shifted_topics", "missing_months",
                                           "review_before", "review_after", "reference_hit")} for r in records],
        "note": ("Beschreibende Zahlen ohne Signifikanzaussage. Ein Erklärungsansatz ist ein möglicher Zusammenhang, keine "
                 "Ursache; die Einstufung beruht auf Titeln und Wortbezügen. Fenster mit fehlenden Monaten im Speicher "
                 "zählen nicht als 'ohne Ansatz'. Die Stimmung der Titel wurde nicht berechnet (ohne Einfluss auf die Stufe)."),
    }


# ── Ausgabe ──────────────────────────────────────────────────────────────────

def _cell(k: int, n: int) -> str:
    return "–" if not n else f"{k}/{n} ({100 * k / n:.0f} %)"


def _med(value: Optional[float]) -> str:
    if value is None:
        return "–"
    return f"{value:.0f}" if float(value).is_integer() else f"{value:.1f}"


def _group_cells(g: Dict[str, Any]) -> List[str]:
    return [f"{g['n']} ({g['complete']})", _cell(g["with_any"], g["complete"])] + [
        _cell(g["by_stage"][s]["windows"], g["complete"]) for s in STAGES_WITH_ANY
    ] + [f"{_med(g['median_items'])} / {_med(g['median_bundles'])}"]


def markdown_tables(summary: Dict[str, Any]) -> str:
    """Markdown-Tabellen: je Unternehmen und gesamt die Markierungs- und Vergleichsfenster
    (Anzahl, vollständig, mit Ansatz, je Stufe, Median Belege/Bündel); Abdeckungsquote nach
    NFA-05; oberste Stufe je Gruppe gesamt. Nur Zahlen."""
    lines = []
    head = "| Unternehmen | Fenster (vollständig) | mit Ansatz | mit hoch | mit mittel | mit niedrig | Belege / Bündel je Fenster (Median) |"
    rows = summary["companies"] + [{"company": "**Gesamt**", **summary["total"]}]
    for group, title in ((GROUP_MARKER, "Markierungsfenster"), (GROUP_COMPARISON, "Vergleichsfenster")):
        lines.append(f"**{title}**")
        lines.append("")
        lines.append(head)
        lines.append("|---|---|---|---|---|---|---|")
        for c in rows:
            lines.append(f"| {c['company']} | " + " | ".join(_group_cells(c[group])) + " |")
        lines.append("")
    lines.append("„mit Ansatz“ = mindestens ein Bündel der Stufe niedrig oder höher; „mit hoch/mittel/niedrig“ = mindestens ein Bündel "
                 "dieser Stufe. Anteile beziehen sich auf die vollständig im Speicher liegenden Fenster (in Klammern).")
    lines.append("")
    lines.append("| Unternehmen | Abdeckungsquote NFA-05 (Markierungen mit Ansatz) | Niveauwechsel | Einzelmonate | Vergleichsfenster mit Ansatz |")
    lines.append("|---|---|---|---|---|")
    for c in rows:
        cov = c["coverage_nfa05"]
        lines.append(f"| {c['company']} | {_cell(cov['covered'], cov['n'])} | "
                     f"{_cell(cov['by_kind'][ev.KIND_CHANGE]['covered'], cov['by_kind'][ev.KIND_CHANGE]['n'])} | "
                     f"{_cell(cov['by_kind'][ev.KIND_OUTLIER]['covered'], cov['by_kind'][ev.KIND_OUTLIER]['n'])} | "
                     f"{_cell(c[GROUP_COMPARISON]['with_any'], c[GROUP_COMPARISON]['complete'])} |")
    lines.append("")
    ref = summary.get("reference") or {}
    lines.append("**Nach Referenzzeiträumen (E5)**")
    lines.append("")
    if ref.get("available"):
        for part, title in (("treffer", "Markierungsfenster mit Referenzzeitraum"), ("uebrige", "Markierungsfenster ohne Referenzzeitraum")):
            lines.append(f"*{title}*")
            lines.append("")
            lines.append(head)
            lines.append("|---|---|---|---|---|---|---|")
            for c in rows:
                lines.append(f"| {c['company']} | " + " | ".join(_group_cells(c["referenz"][part])) + " |")
            lines.append("")
        lines.append(f"{ref.get('definition', REFERENCE_DEFINITION)} Annotationsdatei: {ref.get('path', '–')} (version {ref.get('version', '–')}, "
                     f"{ref.get('n_annotations', 0)} Einträge).")
    else:
        lines.append(f"{REFERENCE_NOT_AVAILABLE}: {ref.get('reason') or 'keine Referenz'}. {ref.get('definition', REFERENCE_DEFINITION)}")
    lines.append("")
    t = summary["total"]
    lines.append("| Oberste Stufe je Fenster (gesamt) | hoch | mittel | niedrig | offen |")
    lines.append("|---|---|---|---|---|")
    for group, title in ((GROUP_MARKER, "Markierungsfenster"), (GROUP_COMPARISON, "Vergleichsfenster")):
        ts = t[group]["top_stage"]
        lines.append(f"| {title} | {ts['hoch']} | {ts['mittel']} | {ts['niedrig']} | {ts['offen']} |")
    lines.append("")
    lines.append(summary["note"])
    incomplete = [w for w in summary["windows"] if w["missing_months"]]
    if incomplete:
        lines.append("")
        lines.append("Fenster mit fehlenden Monaten im Speicher (Unternehmen, Gruppe, Art, Markierung, Versatz; fehlende Monate je Quelle gezählt):")
        for w in incomplete:
            lines.append(f"- {w['company']}, {w['group']}, {w['kind']}, {w['date']}, {w['offset_months']:+d} Monate ({w['missing_months']})")
    return "\n".join(lines)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--window-before", type=int, default=ev.DEFAULT_WINDOW_BEFORE)
    parser.add_argument("--window-after", type=int, default=ev.DEFAULT_WINDOW_AFTER)
    parser.add_argument("--md", help="Markdown-Tabellen in diese Datei schreiben")
    parser.add_argument("--json", dest="json_out", help="Zusammenfassung als JSON-Datei")
    parser.add_argument("--annotations", default=DEFAULT_ANNOTATIONS,
                        help="Annotationsdatei für die Zusatzauswertung nach Referenzzeiträumen (Default: data/annotations.json)")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args(argv)
    reference = load_reference(args.annotations)
    if not reference["available"] and not args.quiet:
        print(f"Zusatzauswertung nach Referenzzeiträumen: {REFERENCE_NOT_AVAILABLE} ({reference['reason']}).")
    records = window_records(args.window_before, args.window_after, verbose=not args.quiet, reference=reference)
    summary = aggregate(records, reference)
    summary["window_before"], summary["window_after"] = args.window_before, args.window_after
    text = markdown_tables(summary)
    print(text)
    t = summary["total"]
    print(f"\nMarkierungsfenster: {t['n_markers']} (vollständig {t[GROUP_MARKER]['complete']}), mit Ansatz: {t[GROUP_MARKER]['with_any']}; "
          f"Vergleichsfenster: {t['n_comparison_windows']} (vollständig {t[GROUP_COMPARISON]['complete']}), mit Ansatz: {t[GROUP_COMPARISON]['with_any']}")
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
