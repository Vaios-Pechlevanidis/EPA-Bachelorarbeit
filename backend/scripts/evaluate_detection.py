"""
Abgleich der automatischen Erkennung mit den manuell annotierten
Referenzzeiträumen (DZ1, E5, Protokoll-Regel 6 in
``docs/referenzzeitraeume-literatur.md``).

Ablauf
------
1. ``backend/data/annotations.json`` lesen. Ohne Einträge bricht das Skript mit
   einem Hinweis ab (Exit-Code 1): erst annotieren (Bogen aus
   ``scripts/make_annotation_sheet.py``), validieren, in einem eigenen Commit
   versionieren, dann auswerten.
2. Einträge mit ``scripts/validate_annotations.validate`` prüfen; Fehler brechen ab.
3. Je annotierter Reihe (Unternehmen, Quelle, Dimension) die Erkennung mit den
   **Standardparametern** berechnen (``services.anomaly_service.company_anomalies``:
   PELT, skalierter Strafterm, ``min_delta`` 0,3; Einzelmonate nach E14). Die
   Datenbank wird nur gelesen. Nicht geeignete Reihen (E4) werden übersprungen
   und gehen nicht in den F1-Wert ein (Regel 9).
4. Abgleich nach Regel 6 (fixiert): Eine Erkennung im Monat ``m`` trifft einen
   Referenzzeitraum, wenn ``period_from − 1 ≤ m ≤ period_to + 1`` (Kalendermonate).
   Ist der Nachbarmonat nicht bewertet, rückt die Grenze auf den nächsten
   bewerteten Monat, höchstens ``MAX_SHIFT_MONTHS`` = 3 Kalendermonate weit.
   Zusätzlich muss die Richtung übereinstimmen (``rise``/``fall``). Jede Annotation
   zählt höchstens einmal (früheste passende Erkennung im Fenster), jede Erkennung
   höchstens für eine Annotation (Eins-zu-eins-Zuordnung, Annotationen in
   zeitlicher Reihenfolge). Erkennungen ohne Annotation sind zusätzliche
   Markierungen (FP), Annotationen ohne Erkennung verfehlte Zeiträume (FN).
5. Ausgabe je Reihe, je Quelle und gesamt: Precision, Recall, F1 (Mikro-Mittel
   über die Summen von TP, FP, FN), getrennt für zwei Varianten:

   - ``niveauwechsel``: nur die Niveauwechsel (``anomalies``),
   - ``niveauwechsel+einzelmonate``: Niveauwechsel und auffällige Einzelmonate
     (``outlier_months``, E14) zusammen.

   Dazu die Listen der Treffer, der verfehlten Zeiträume und der zusätzlichen
   Markierungen; mit ``--json`` auch als Datei.

Teilauswertungen (``--subset``, vor dem ersten Lauf festgelegt, E5 Aktualisierung
2026-10-09): Jede Teilmenge der Referenzzeiträume wird für beide Varianten
berichtet. Ohne ``--subset`` werden alle vier berichtet.

- ``alle``: alle Einträge,
- ``ohne_duenne``: kein Monat im Zeitraum mit weniger als ``THIN_MONTH_REVIEWS`` = 10
  Bewertungen (Zählungen aus den Serien-CSVs in ``data/series/``),
- ``mehrmonatig``: Zeitraum mindestens 2 Kalendermonate,
- ``mit_anker``: ``note`` endet mit "Reihe + Ereignis".

Der Abgleich selbst bleibt der der Gesamtmenge (Regel 6, Eins-zu-eins über alle
Einträge der Reihe). Danach zählen nur Einträge der Teilmenge als Treffer (TP)
oder verfehlt (FN); eine Erkennung, die einem Eintrag außerhalb der Teilmenge
zugeordnet ist, zählt weder als Treffer noch als zusätzliche Markierung
(``neutral``); nicht zugeordnete Erkennungen bleiben zusätzliche Markierungen (FP).
Eine Reihe geht nur in die Teilauswertung ein, wenn sie mindestens einen Eintrag
der Teilmenge hat.

Die Abgleichregeln (``TOLERANCE_MONTHS``, ``MAX_SHIFT_MONTHS``, gleiche Richtung,
Eins-zu-eins) sind mit Regel 6 fixiert und werden nach dem ersten Lauf nicht
geändert. ``match_window``, ``match_series`` und ``evaluate`` sind reine
Funktionen (Tests: ``backend/tests/test_evaluate_detection.py``).

Verwendung
----------
    cd backend
    uv run python scripts/evaluate_detection.py                       # Unternehmen aus der DB (nur SELECT)
    uv run python scripts/evaluate_detection.py --offline             # Unternehmensliste aus data_density.json
    uv run python scripts/evaluate_detection.py --source employee --json data/calibration/dz1_ergebnis.json
    uv run python scripts/evaluate_detection.py --subset alle --subset mit_anker
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, Tuple

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND_DIR)
sys.path.insert(0, os.path.join(BACKEND_DIR, "scripts"))

import validate_annotations as va  # noqa: E402
from services.rating_series_service import OVERALL_DIMENSION, VALID_SOURCES  # noqa: E402

DEFAULT_FILE = os.path.join(BACKEND_DIR, "data", "annotations.json")
DEFAULT_DENSITY = os.path.join(BACKEND_DIR, "data", "data_density.json")
DEFAULT_SERIES_DIR = os.path.join(BACKEND_DIR, "data", "series")

# Regel 6 (fixiert): Toleranz um den Referenzzeitraum und Kappung bei Lücken.
TOLERANCE_MONTHS = 1
MAX_SHIFT_MONTHS = 3
VARIANTS: Tuple[str, str] = ("niveauwechsel", "niveauwechsel+einzelmonate")
KIND_LEVEL = "niveauwechsel"
KIND_OUTLIER = "einzelmonat"

# Teilauswertungen (vor dem ersten Lauf festgelegt, E5 Aktualisierung 2026-10-09)
SUBSETS: Tuple[str, ...] = ("alle", "ohne_duenne", "mehrmonatig", "mit_anker")
THIN_MONTH_REVIEWS = 10
ANCHOR_SUFFIX = "Reihe + Ereignis"
SUBSET_DEFINITIONS: Dict[str, str] = {
    "alle": "alle Einträge",
    "ohne_duenne": f"kein Monat im Zeitraum mit weniger als {THIN_MONTH_REVIEWS} Bewertungen (Serien-CSVs)",
    "mehrmonatig": "Zeitraum mindestens 2 Kalendermonate",
    "mit_anker": f"note endet mit \"{ANCHOR_SUFFIX}\"",
}

Fetcher = Callable[[int, str, str], Dict[str, Any]]


# ── Monate ───────────────────────────────────────────────────────────────────

def _month_index(period: str) -> int:
    return int(period[:4]) * 12 + int(period[5:7]) - 1


def _month_str(index: int) -> str:
    return f"{index // 12:04d}-{index % 12 + 1:02d}"


def match_window(period_from: str, period_to: str, evaluated: Any,
                 tolerance: int = TOLERANCE_MONTHS, max_shift: int = MAX_SHIFT_MONTHS) -> Tuple[str, str]:
    """Fenster ``[lo, hi]`` nach Regel 6: ``period_from − tolerance`` bis
    ``period_to + tolerance``; ist der Randmonat nicht bewertet, rückt die Grenze
    auf den nächsten bewerteten Monat, höchstens ``max_shift`` Kalendermonate vom
    Zeitraum entfernt. ``evaluated`` ist die Menge der bewerteten Monate."""
    evaluated = set(evaluated)
    i_from, i_to = _month_index(period_from), _month_index(period_to)
    lo = i_from - tolerance
    if _month_str(lo) not in evaluated:
        earlier = [i for i in range(i_from - max_shift, lo) if _month_str(i) in evaluated]
        if earlier:
            lo = max(earlier)
    hi = i_to + tolerance
    if _month_str(hi) not in evaluated:
        later = [i for i in range(hi + 1, i_to + max_shift + 1) if _month_str(i) in evaluated]
        if later:
            hi = min(later)
    return _month_str(lo), _month_str(hi)


# ── Abgleich einer Reihe ─────────────────────────────────────────────────────

def metrics(tp: int, fp: int, fn: int) -> Dict[str, Any]:
    """Precision, Recall, F1; ``None``, wenn der Nenner 0 ist (F1 dann 0, wenn TP 0)."""
    precision = tp / (tp + fp) if (tp + fp) else None
    recall = tp / (tp + fn) if (tp + fn) else None
    if precision and recall:
        f1: Optional[float] = 2 * precision * recall / (precision + recall)
    elif tp == 0 and (fp or fn):
        f1 = 0.0
    else:
        f1 = None
    return {"tp": tp, "fp": fp, "fn": fn, "precision": precision, "recall": recall, "f1": f1}


def _annotation_view(ann: Dict[str, Any]) -> Dict[str, Any]:
    return {k: ann.get(k) for k in ("company", "source", "dimension", "period_from", "period_to", "direction")}


def _detection_view(det: Dict[str, Any]) -> Dict[str, Any]:
    keys = ("kind", "date", "direction", "delta", "deviation", "severity", "before_mean", "after_mean", "month_mean", "level")
    return {k: det.get(k) for k in keys if k in det}


def match_series(annotations: List[Dict[str, Any]], detections: List[Dict[str, Any]], evaluated: Any,
                 tolerance: int = TOLERANCE_MONTHS, max_shift: int = MAX_SHIFT_MONTHS) -> Dict[str, Any]:
    """Eins-zu-eins-Abgleich einer Reihe; reine Funktion.

    ``detections``: ``{"kind", "date", "direction", ...}``; ``annotations``: Einträge
    aus annotations.json. Liefert Treffer, verfehlte Zeiträume, zusätzliche
    Markierungen und die Kennzahlen.
    """
    used: set = set()
    hits: List[Dict[str, Any]] = []
    misses: List[Dict[str, Any]] = []
    for ann in sorted(annotations, key=lambda a: (a["period_from"], a["period_to"])):
        lo, hi = match_window(ann["period_from"], ann["period_to"], evaluated, tolerance, max_shift)
        candidates = [
            (i, d) for i, d in enumerate(detections)
            if i not in used and d["direction"] == ann["direction"] and lo <= d["date"] <= hi
        ]
        if candidates:
            i, det = min(candidates, key=lambda c: (c[1]["date"], c[0]))
            used.add(i)
            hits.append({"annotation": _annotation_view(ann), "window": [lo, hi], "detection": _detection_view(det)})
        else:
            misses.append({"annotation": _annotation_view(ann), "window": [lo, hi]})
    extras = [_detection_view(d) for i, d in enumerate(detections) if i not in used]
    extras.sort(key=lambda d: d["date"])
    result = metrics(len(hits), len(extras), len(misses))
    result.update({"n_annotations": len(annotations), "n_detections": len(detections),
                   "hits": hits, "misses": misses, "extras": extras})
    return result


def detections_from_result(result: Dict[str, Any], with_outliers: bool) -> List[Dict[str, Any]]:
    """Erkennungen einer Antwort von ``company_anomalies`` als einheitliche Liste."""
    out = [{**a, "kind": KIND_LEVEL} for a in result.get("anomalies") or []]
    if with_outliers:
        out.extend({**o, "kind": KIND_OUTLIER} for o in result.get("outlier_months") or [])
    return sorted(out, key=lambda d: (d["date"], d["kind"]))


# ── Gesamtauswertung ─────────────────────────────────────────────────────────

def group_annotations(doc: Dict[str, Any]) -> Dict[Tuple[str, str, str], List[Dict[str, Any]]]:
    """Einträge nach (normalisierter Name, Quelle, Dimension)."""
    grouped: Dict[Tuple[str, str, str], List[Dict[str, Any]]] = {}
    for ann in doc.get("annotations") or []:
        key = (va.normalize_company_name(ann["company"]), ann["source"], ann["dimension"])
        grouped.setdefault(key, []).append(ann)
    return grouped


def _sum_metrics(items: List[Dict[str, Any]]) -> Dict[str, Any]:
    tp = sum(i["tp"] for i in items)
    fp = sum(i["fp"] for i in items)
    fn = sum(i["fn"] for i in items)
    out = metrics(tp, fp, fn)
    out["n_series"] = len(items)
    out["n_annotations"] = sum(i["n_annotations"] for i in items)
    return out


def evaluate(doc: Dict[str, Any], companies: Dict[str, va.CompanyInfo], fetch: Fetcher,
             sources: Optional[List[str]] = None) -> Dict[str, Any]:
    """Abgleich aller annotierten Reihen; ``fetch(company_id, source, dimension)``
    liefert die Antwort von ``company_anomalies`` (Standardparameter). Reine
    Funktion bis auf den Aufruf von ``fetch``."""
    series_results: List[Dict[str, Any]] = []
    skipped: List[Dict[str, Any]] = []
    for (norm, source, dimension), anns in sorted(group_annotations(doc).items()):
        label = f"{companies[norm].name if norm in companies else anns[0]['company']} / {source} / {dimension}"
        if sources and source not in sources:
            continue
        info = companies.get(norm)
        if info is None or info.id is None:
            skipped.append({"series": label, "n_annotations": len(anns), "reason": "Unternehmen nicht auflösbar oder ohne id."})
            continue
        result = fetch(info.id, source, dimension)
        elig = result.get("eligibility") or {}
        if not elig.get("eligible", False):
            skipped.append({"series": label, "n_annotations": len(anns),
                            "reason": f"Reihe nicht geeignet (E4): {elig.get('reason') or 'unbekannt'} Einträge gehen nicht in den F1-Wert ein (Regel 9)."})
            continue
        evaluated = {m["period"] for m in result.get("series") or [] if m.get("evaluated")}
        entry: Dict[str, Any] = {
            "series": label, "company": info.name, "company_id": info.id, "source": source, "dimension": dimension,
            "evaluated_months": len(evaluated), "params": result.get("params"), "variants": {},
        }
        for variant in VARIANTS:
            dets = detections_from_result(result, with_outliers=(variant == VARIANTS[1]))
            entry["variants"][variant] = match_series(anns, dets, evaluated)
        series_results.append(entry)

    totals: Dict[str, Any] = {}
    for variant in VARIANTS:
        per_source = {}
        for source in VALID_SOURCES:
            items = [s["variants"][variant] for s in series_results if s["source"] == source]
            if items:
                per_source[source] = _sum_metrics(items)
        totals[variant] = {"gesamt": _sum_metrics([s["variants"][variant] for s in series_results]), "je_quelle": per_source}
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "rules": {"tolerance_months": TOLERANCE_MONTHS, "max_shift_months": MAX_SHIFT_MONTHS,
                  "same_direction": True, "one_to_one": True, "assignment": "Annotationen in zeitlicher Reihenfolge, früheste passende Erkennung"},
        "annotations_version": doc.get("version"),
        "n_annotations": len(doc.get("annotations") or []),
        "series": series_results,
        "totals": totals,
        "skipped": skipped,
    }


# ── Teilauswertungen ─────────────────────────────────────────────────────────

def _annotation_key(ann: Dict[str, Any]) -> Tuple[str, ...]:
    return (va.normalize_company_name(ann["company"]),) + tuple(
        ann[k] for k in ("source", "dimension", "period_from", "period_to", "direction"))


def subset_member(name: str, ann: Dict[str, Any], counts: Optional[Dict[str, int]] = None) -> Optional[bool]:
    """Gehört ein Eintrag zur Teilmenge ``name``? Reine Funktion.

    ``counts``: Bewertungen je Monat der Reihe (Serien-CSV). Für ``ohne_duenne``
    ohne Zählungen ist die Zugehörigkeit nicht bestimmbar (``None``); ein Monat
    ohne Zeile zählt als 0 Bewertungen.
    """
    if name == "alle":
        return True
    if name == "mehrmonatig":
        return _month_index(ann["period_to"]) - _month_index(ann["period_from"]) + 1 >= 2
    if name == "mit_anker":
        return str(ann.get("note") or "").strip().rstrip(".").rstrip().endswith(ANCHOR_SUFFIX)
    if name == "ohne_duenne":
        if counts is None:
            return None
        months = range(_month_index(ann["period_from"]), _month_index(ann["period_to"]) + 1)
        return all(counts.get(_month_str(i), 0) >= THIN_MONTH_REVIEWS for i in months)
    raise ValueError(f"unbekannte Teilmenge: {name}")


def _restrict(variant_result: Dict[str, Any], keep: set) -> Dict[str, Any]:
    """Kennzahlen einer Reihe, eingeschränkt auf die Einträge in ``keep``
    (Schlüssel aus ``_annotation_key``). Zuordnung wie in der Gesamtmenge;
    Treffer außerhalb der Teilmenge sind neutral."""
    hits = [h for h in variant_result["hits"] if _annotation_key(h["annotation"]) in keep]
    misses = [m for m in variant_result["misses"] if _annotation_key(m["annotation"]) in keep]
    neutral = [h for h in variant_result["hits"] if _annotation_key(h["annotation"]) not in keep]
    out = metrics(len(hits), len(variant_result["extras"]), len(misses))
    out.update({"n_annotations": len(hits) + len(misses), "neutral": len(neutral),
                "hits": hits, "misses": misses, "extras": variant_result["extras"]})
    return out


def evaluate_subsets(doc: Dict[str, Any], companies: Dict[str, va.CompanyInfo], report: Dict[str, Any],
                     subsets: Tuple[str, ...] = SUBSETS) -> Dict[str, Any]:
    """Teilauswertungen auf Grundlage eines Berichts von ``evaluate``; reine Funktion.
    Zählungen für ``ohne_duenne`` aus ``CompanyInfo.counts`` (``attach_series_counts``)."""
    out: Dict[str, Any] = {}
    for name in subsets:
        keep: set = set()
        undetermined = 0
        for ann in doc.get("annotations") or []:
            info = companies.get(va.normalize_company_name(ann["company"]))
            counts = info.counts.get(ann["source"]) if info is not None else None
            member = subset_member(name, ann, counts)
            if member is None:
                undetermined += 1
            elif member:
                keep.add(_annotation_key(ann))
        series: List[Dict[str, Any]] = []
        for s in report["series"]:
            variants = {v: _restrict(s["variants"][v], keep) for v in VARIANTS}
            if variants[VARIANTS[0]]["n_annotations"]:
                series.append({"series": s["series"], "source": s["source"], "variants": variants})
        totals: Dict[str, Any] = {}
        for variant in VARIANTS:
            per_source = {}
            for source in VALID_SOURCES:
                items = [s["variants"][variant] for s in series if s["source"] == source]
                if items:
                    per_source[source] = _sum_metrics(items)
            totals[variant] = {"gesamt": _sum_metrics([s["variants"][variant] for s in series]), "je_quelle": per_source}
        out[name] = {"definition": SUBSET_DEFINITIONS[name], "n_annotations": len(keep),
                     "n_undetermined": undetermined, "series": series, "totals": totals}
    return out


# ── Bericht ──────────────────────────────────────────────────────────────────

def _pct(value: Optional[float]) -> str:
    return "–" if value is None else f"{value:.2f}".replace(".", ",")


def _fmt_detection(det: Dict[str, Any]) -> str:
    kind = "Einzelmonat" if det.get("kind") == KIND_OUTLIER else "Niveauwechsel"
    size = det.get("delta") if det.get("delta") is not None else det.get("deviation")
    size_s = "" if size is None else f", {size:+.2f}".replace(".", ",")
    return f"{det['date']} {det['direction']} ({kind}{size_s})"


def format_report(report: Dict[str, Any], path: str = "") -> str:
    lines: List[str] = []
    r = report["rules"]
    lines.append("Abgleich der Erkennung mit den Referenzzeiträumen (DZ1, E5)" + (f" – {path}" if path else ""))
    lines.append(f"  Annotationen: {report['n_annotations']} (version {report['annotations_version']}), "
                 f"Regel 6: Toleranz ±{r['tolerance_months']} Monat, Lücken bis {r['max_shift_months']} Monate, "
                 "gleiche Richtung, Eins-zu-eins-Zuordnung; Erkennung mit Standardparametern.")
    for s in report["skipped"]:
        lines.append(f"  Übersprungen: {s['series']} ({s['n_annotations']} Einträge): {s['reason']}")
    for variant in VARIANTS:
        title = "Niveauwechsel allein" if variant == VARIANTS[0] else "Niveauwechsel und Einzelmonate"
        lines.append("")
        lines.append(f"Variante {title}")
        lines.append(f"  {'Reihe':<58}{'Ann':>4}{'TP':>4}{'FP':>4}{'FN':>4}{'Prec':>7}{'Rec':>7}{'F1':>7}")
        for s in report["series"]:
            v = s["variants"][variant]
            lines.append(f"  {s['series'][:58]:<58}{v['n_annotations']:>4}{v['tp']:>4}{v['fp']:>4}{v['fn']:>4}"
                         f"{_pct(v['precision']):>7}{_pct(v['recall']):>7}{_pct(v['f1']):>7}")
        tot = report["totals"][variant]
        for source, m in tot["je_quelle"].items():
            lines.append(f"  {'Gesamt ' + source:<58}{m['n_annotations']:>4}{m['tp']:>4}{m['fp']:>4}{m['fn']:>4}"
                         f"{_pct(m['precision']):>7}{_pct(m['recall']):>7}{_pct(m['f1']):>7}")
        g = tot["gesamt"]
        lines.append(f"  {'Gesamt':<58}{g['n_annotations']:>4}{g['tp']:>4}{g['fp']:>4}{g['fn']:>4}"
                     f"{_pct(g['precision']):>7}{_pct(g['recall']):>7}{_pct(g['f1']):>7}")
        for s in report["series"]:
            v = s["variants"][variant]
            lines.append(f"  {s['series']}:")
            for h in v["hits"]:
                a = h["annotation"]
                lines.append(f"    Treffer:    {a['period_from']}..{a['period_to']} {a['direction']} "
                             f"(Fenster {h['window'][0]}..{h['window'][1]}) <- {_fmt_detection(h['detection'])}")
            for m in v["misses"]:
                a = m["annotation"]
                lines.append(f"    Verfehlt:   {a['period_from']}..{a['period_to']} {a['direction']} "
                             f"(Fenster {m['window'][0]}..{m['window'][1]})")
            for e in v["extras"]:
                lines.append(f"    Zusätzlich: {_fmt_detection(e)}")
    if report.get("subsets"):
        lines.append("")
        lines.append("Teilauswertungen (vor dem ersten Lauf festgelegt, E5); Erkennungen zu Einträgen außerhalb der Teilmenge neutral")
        for name, sub in report["subsets"].items():
            extra = f", nicht bestimmbar {sub['n_undetermined']}" if sub["n_undetermined"] else ""
            lines.append(f"  Teilmenge {name}: {sub['definition']} ({sub['n_annotations']} Einträge{extra})")
            for variant in VARIANTS:
                title = "Niveauwechsel allein" if variant == VARIANTS[0] else "Niveauwechsel und Einzelmonate"
                lines.append(f"    Variante {title}")
                lines.append(f"    {'Reihe':<56}{'Ann':>4}{'TP':>4}{'FP':>4}{'FN':>4}{'Neu':>4}{'Prec':>7}{'Rec':>7}{'F1':>7}")
                for s in sub["series"]:
                    v = s["variants"][variant]
                    lines.append(f"    {s['series'][:56]:<56}{v['n_annotations']:>4}{v['tp']:>4}{v['fp']:>4}{v['fn']:>4}{v['neutral']:>4}"
                                 f"{_pct(v['precision']):>7}{_pct(v['recall']):>7}{_pct(v['f1']):>7}")
                tot = sub["totals"][variant]
                rows = [("Gesamt " + src, m) for src, m in tot["je_quelle"].items()] + [("Gesamt", tot["gesamt"])]
                for label, m in rows:
                    lines.append(f"    {label:<56}{m['n_annotations']:>4}{m['tp']:>4}{m['fp']:>4}{m['fn']:>4}{'':>4}"
                                 f"{_pct(m['precision']):>7}{_pct(m['recall']):>7}{_pct(m['f1']):>7}")
    return "\n".join(lines)


# ── CLI ──────────────────────────────────────────────────────────────────────

EMPTY_HINT = (
    "Keine Annotationen in {path}: 'annotations' ist leer.\n"
    "Hinweis: erst annotieren (Bogen: uv run python scripts/make_annotation_sheet.py), dann\n"
    "validieren (uv run python scripts/validate_annotations.py), die Datei in einem eigenen Commit\n"
    "versionieren und erst danach auswerten (E5)."
)


def _db_fetch(company_id: int, source: str, dimension: str) -> Dict[str, Any]:
    from services.anomaly_service import company_anomalies  # lazy: Tests ohne Erkennungscode und DB
    return company_anomalies(company_id, source, dimension)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--file", default=DEFAULT_FILE, help=f"Annotationsdatei (Default: {os.path.relpath(DEFAULT_FILE, BACKEND_DIR)})")
    parser.add_argument("--density", default=DEFAULT_DENSITY, help="data_density.json (Unternehmensliste, Zeiträume)")
    parser.add_argument("--offline", action="store_true", help="Unternehmensliste aus data_density.json statt aus der DB (die Erkennung liest weiterhin die DB)")
    parser.add_argument("--source", choices=list(VALID_SOURCES), action="append", help="nur diese Quelle(n) auswerten")
    parser.add_argument("--json", dest="json_out", help="Ergebnis zusätzlich als JSON-Datei schreiben")
    parser.add_argument("--subset", choices=list(SUBSETS), action="append",
                        help="Teilauswertung(en); ohne Angabe alle vier (alle, ohne_duenne, mehrmonatig, mit_anker)")
    parser.add_argument("--series-dir", default=DEFAULT_SERIES_DIR, help="Serien-CSVs für die Teilmenge ohne_duenne")
    args = parser.parse_args(argv)

    doc, err = va._load_json(args.file, "Annotationsdatei")
    if err:
        print(f"FEHLER: {err}")
        return 1
    if not isinstance(doc, dict) or not doc.get("annotations"):
        print(EMPTY_HINT.format(path=args.file))
        return 1
    density, err = va._load_json(args.density, "data_density.json")
    if err:
        print(f"FEHLER: {err}\nHinweis: zuerst 'uv run python scripts/report_data_density.py' ausführen.")
        return 1
    load_warnings: List[str] = []
    companies = va.companies_from_density(density) if args.offline else va.companies_from_db(density, load_warnings)
    validation = va.validate(doc, companies)
    for w in load_warnings + validation.warnings:
        print(f"Warnung: {w}")
    if not validation.ok:
        print(va.format_report(validation, args.file))
        print("Abbruch: Annotationen zuerst korrigieren (validate_annotations.py).")
        return 1

    subsets = tuple(dict.fromkeys(args.subset)) if args.subset else SUBSETS
    if "ohne_duenne" in subsets:
        series_warnings: List[str] = []
        if os.path.isdir(args.series_dir):
            va.attach_series_counts(companies, args.series_dir, series_warnings)
        else:
            series_warnings.append(f"Serien-Verzeichnis {args.series_dir} fehlt; Teilmenge ohne_duenne nicht bestimmbar.")
        for w in series_warnings:
            print(f"Warnung: {w}")

    report = evaluate(doc, companies, _db_fetch, sources=args.source)
    report["subsets"] = evaluate_subsets(doc, companies, report, subsets)
    print(format_report(report, args.file))
    if args.json_out:
        os.makedirs(os.path.dirname(os.path.abspath(args.json_out)), exist_ok=True)
        with open(args.json_out, "w", encoding="utf-8") as fh:
            json.dump(report, fh, ensure_ascii=False, indent=2)
            fh.write("\n")
        print(f"\nErgebnis gespeichert: {args.json_out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
