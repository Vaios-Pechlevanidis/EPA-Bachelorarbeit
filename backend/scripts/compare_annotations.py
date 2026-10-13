"""
Abgleich zweier beliebiger Annotationsdateien (DZ1, E5): Übereinstimmung der
Referenzzeiträume aus Datei A (Standard ``data/annotations.json``) mit denen aus
Datei B (``--b``, Pflichtangabe). Eine zweite, unabhängige Person stand für DZ1
nicht zur Verfügung (E5, Aktualisierung 2026-10-09); das Skript bleibt für
spätere Vergleiche, etwa zweier Fassungen derselben Datei.

Zuordnungsregel: dieselbe wie beim Abgleich Erkennung ↔ Referenz (E5, Regel 6,
``scripts/evaluate_detection.match_window``), auf zwei Zeiträume übertragen:

- Toleranz ±``TOLERANCE_MONTHS`` (1) Kalendermonat um den Zeitraum aus Datei A; ist
  der Nachbarmonat nicht bewertet, rückt die Grenze auf den nächsten bewerteten
  Monat, höchstens ``MAX_SHIFT_MONTHS`` (3) Monate weit (bewertete Monate aus den
  Serien-CSVs unter ``data/series/``; ohne CSV gilt die reine Toleranz),
- gleiche Richtung (``rise``/``fall``),
- Eins-zu-eins-Zuordnung: Zeiträume aus A in zeitlicher Reihenfolge, je Zeitraum
  der früheste noch nicht zugeordnete Zeitraum aus B, der das Fenster berührt.

Ausgabe je Reihe und gesamt: übereinstimmende Zeiträume, nur bei A, nur bei B,
und der Anteil der Reihen, in denen beide keinen Zeitraum sehen. Die Reihen sind
die nach E4 geeigneten Reihen der Quelle (Standard: Mitarbeitende,
Gesamtbewertung) aus den Serien-CSVs, dazu jede Reihe mit Einträgen in einer der
Dateien. Nur Zahlen; keine Wertung, welche Datei „richtig“ liegt.

Zusätzlich (ergänzt 2026-10-13, blinde Zweitannotation): Cohens κ auf Monatsebene,
gesamt und je Reihe. Einheit sind die bewerteten Monate (E4) der verglichenen Reihen
mit Serien-CSV; jeder Monat erhält je Datei eine Kategorie ``rise``, ``fall`` oder
``keine`` (Monate innerhalb eines Zeitraums tragen dessen Richtung; überschneiden sich
Zeiträume einer Datei, gilt der früheste). κ = (p_o − p_e) / (1 − p_e) mit der
beobachteten Übereinstimmung p_o und der aus den Randverteilungen erwarteten p_e
(Cohen 1960); κ ist nicht definiert, wenn beide Dateien alle Monate derselben Kategorie
zuordnen (p_e = 1). Anders als Regel 6 kennt κ keine Toleranz: Ein um einen Monat
verschobener Zeitraum senkt κ. Die bisherige Textausgabe bleibt Zeichen für Zeichen
erhalten; der κ-Block folgt am Ende, im JSON stehen ``kappa`` gesamt und je Reihe.

``--series`` begrenzt den Vergleich auf eine Teilmenge: Schlüssel des blinden Bogens
(``reihen``), die übersetzte Datei der Zweitannotation (``hinweise.herkunft.reihen``)
oder kommagetrennte Unternehmens-ids.

Die Funktionen ``match_periods``, ``month_categories``, ``cohens_kappa`` und ``compare``
sind rein (Tests: ``backend/tests/test_compare_annotations.py``). Das Skript liest nur
Dateien.

Verwendung
----------
    cd backend
    uv run python scripts/compare_annotations.py --b <andere_datei.json>
    uv run python scripts/compare_annotations.py --a <datei_a.json> --b <datei_b.json> --json <ergebnis.json>
    uv run python scripts/compare_annotations.py --b data/annotations_zweitperson.json --series data/annotations_zweitperson.json
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import re
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set, Tuple

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND_DIR)
sys.path.insert(0, os.path.join(BACKEND_DIR, "scripts"))

import validate_annotations as va  # noqa: E402
from evaluate_detection import MAX_SHIFT_MONTHS, TOLERANCE_MONTHS, match_window  # noqa: E402
from make_annotation_sheet import company_names, is_eligible, is_evaluated, read_series_csv  # noqa: E402
from services.rating_series_service import OVERALL_DIMENSION, VALID_SOURCES  # noqa: E402

DEFAULT_A = os.path.join(BACKEND_DIR, "data", "annotations.json")
DEFAULT_SERIES_DIR = os.path.join(BACKEND_DIR, "data", "series")
DEFAULT_DENSITY = os.path.join(BACKEND_DIR, "data", "data_density.json")

SeriesKey = Tuple[str, str, str]   # (normalisierter Unternehmensname, Quelle, Dimension)
_FILE_RE = re.compile(r"^(\d+)_(.+)_(employee|candidates)\.csv$")


# ── Abgleich einer Reihe ─────────────────────────────────────────────────────

def _view(ann: Dict[str, Any]) -> Dict[str, Any]:
    return {k: ann.get(k) for k in ("company", "period_from", "period_to", "direction")}


def match_periods(a: List[Dict[str, Any]], b: List[Dict[str, Any]], evaluated: Any = (),
                  tolerance: int = TOLERANCE_MONTHS, max_shift: int = MAX_SHIFT_MONTHS) -> Dict[str, Any]:
    """Eins-zu-eins-Abgleich der Zeiträume einer Reihe aus A und B nach Regel 6; reine Funktion.
    Ein Zeitraum aus B trifft einen aus A, wenn er dessen Fenster ``match_window`` berührt und
    dieselbe Richtung hat. Liefert ``matches``, ``only_a``, ``only_b``."""
    used: Set[int] = set()
    matches: List[Dict[str, Any]] = []
    only_a: List[Dict[str, Any]] = []
    for ann in sorted(a, key=lambda x: (x["period_from"], x["period_to"])):
        lo, hi = match_window(ann["period_from"], ann["period_to"], evaluated, tolerance, max_shift)
        candidates = [
            (i, other) for i, other in enumerate(b)
            if i not in used and other["direction"] == ann["direction"]
            and other["period_from"] <= hi and other["period_to"] >= lo
        ]
        if candidates:
            i, other = min(candidates, key=lambda c: (c[1]["period_from"], c[1]["period_to"], c[0]))
            used.add(i)
            matches.append({"a": _view(ann), "b": _view(other), "window_a": [lo, hi]})
        else:
            only_a.append({"a": _view(ann), "window_a": [lo, hi]})
    only_b = [_view(other) for i, other in enumerate(b) if i not in used]
    only_b.sort(key=lambda x: (x["period_from"], x["period_to"]))
    return {"n_a": len(a), "n_b": len(b), "matches": matches, "only_a": only_a, "only_b": only_b}


# ── Cohens κ auf Monatsebene ─────────────────────────────────────────────────

KAPPA_CATEGORIES: Tuple[str, ...] = ("rise", "fall", "keine")


def month_categories(periods: List[Dict[str, Any]], months: Any) -> Dict[str, str]:
    """Kategorie je Monat aus ``months``: Richtung des Zeitraums, der den Monat enthält, sonst
    „keine“; reine Funktion. Überschneiden sich Zeiträume, gilt der früheste (nach period_from,
    period_to). Zeiträume mit ungültigem Monat oder unbekannter Richtung bleiben außen vor."""
    cats = {m: "keine" for m in months}
    for ann in sorted(periods, key=lambda x: (str(x.get("period_from")), str(x.get("period_to")))):
        p_from, p_to, direction = ann.get("period_from"), ann.get("period_to"), ann.get("direction")
        if direction not in ("rise", "fall") or not all(isinstance(p, str) and va.PERIOD_RE.fullmatch(p) for p in (p_from, p_to)):
            continue
        for m in va._month_range(p_from, p_to):
            if cats.get(m) == "keine":
                cats[m] = direction
    return cats


def cohens_kappa(pairs: List[Tuple[str, str]], categories: Tuple[str, ...] = KAPPA_CATEGORIES) -> Dict[str, Any]:
    """Cohens κ für Paare (Kategorie A, Kategorie B); reine Funktion. Liefert κ, p_o, p_e, die
    Zahl der Monate und die Kreuztabelle (Zeilen A, Spalten B). κ ist ``None``, wenn keine Monate
    vorliegen oder p_e = 1 (beide Dateien ordnen alle Monate derselben Kategorie zu)."""
    n = len(pairs)
    matrix = {a: {b: 0 for b in categories} for a in categories}
    for a, b in pairs:
        matrix.setdefault(a, {}).setdefault(b, 0)
        matrix[a][b] += 1
    out: Dict[str, Any] = {"n_months": n, "kappa": None, "p_o": None, "p_e": None, "matrix": matrix, "reason": None}
    if n == 0:
        out["reason"] = "keine bewerteten Monate"
        return out
    cats = list(dict.fromkeys(list(categories) + [c for pair in pairs for c in pair]))
    count_a = {c: sum(1 for a, _ in pairs if a == c) for c in cats}
    count_b = {c: sum(1 for _, b in pairs if b == c) for c in cats}
    agree = sum(1 for a, b in pairs if a == b)
    expected = sum(count_a[c] * count_b[c] for c in cats)      # p_e · n²
    out["p_o"] = round(agree / n, 4)
    out["p_e"] = round(expected / (n * n), 4)
    if expected == n * n:
        out["reason"] = "nicht definiert: beide Dateien ordnen alle Monate derselben Kategorie zu"
        return out
    out["kappa"] = round((agree * n - expected) / (n * n - expected), 4)
    return out


# ── Reihen ───────────────────────────────────────────────────────────────────

def group_by_series(doc: Dict[str, Any]) -> Dict[SeriesKey, List[Dict[str, Any]]]:
    grouped: Dict[SeriesKey, List[Dict[str, Any]]] = {}
    for ann in doc.get("annotations") or []:
        key = (va.normalize_company_name(str(ann.get("company", ""))), str(ann.get("source", "")), str(ann.get("dimension", "")))
        grouped.setdefault(key, []).append(ann)
    return grouped


def series_from_csvs(series_dir: str, source: str, density_path: str,
                     dimension: str = OVERALL_DIMENSION) -> Dict[SeriesKey, Dict[str, Any]]:
    """Geeignete Reihen (E4) der Quelle aus den Serien-CSVs: ``{Schlüssel: {"name", "evaluated"}}``
    mit der Menge der bewerteten Monate. Leer, wenn der Ordner fehlt."""
    names = company_names(density_path)
    out: Dict[SeriesKey, Dict[str, Any]] = {}
    for path in sorted(glob.glob(os.path.join(series_dir, f"*_{source}.csv"))):
        m = _FILE_RE.match(os.path.basename(path))
        if not m:
            continue
        rows = read_series_csv(path)
        if not is_eligible(rows):
            continue
        company_id = int(m.group(1))
        name = names.get(company_id) or m.group(2).replace("_", " ")
        out[(va.normalize_company_name(name), source, dimension)] = {
            "name": name, "company_id": company_id, "evaluated": {r["period"] for r in rows if is_evaluated(r)},
        }
    return out


# ── Gesamtvergleich ──────────────────────────────────────────────────────────

def compare(doc_a: Dict[str, Any], doc_b: Dict[str, Any], series: Optional[Dict[SeriesKey, Dict[str, Any]]] = None,
            source: Optional[str] = None, only: Optional[Set[str]] = None) -> Dict[str, Any]:
    """Abgleich aller Reihen; reine Funktion. ``series`` sind die Reihen aus den CSVs (Name,
    bewertete Monate); dazu kommt jede Reihe mit Einträgen in A oder B. ``source`` begrenzt auf
    eine Quelle, ``only`` auf die normalisierten Unternehmensnamen einer Teilmenge (``--series``).
    Liefert je Reihe Treffer, nur A, nur B und gesamt die Summen sowie den Anteil der Reihen, in
    denen beide keinen Zeitraum sehen; dazu Cohens κ auf Monatsebene je Reihe und gesamt."""
    series = series or {}
    by_a, by_b = group_by_series(doc_a), group_by_series(doc_b)
    keys = set(series) | set(by_a) | set(by_b)
    if source:
        keys = {k for k in keys if k[1] == source}
    if only is not None:
        keys = {k for k in keys if k[0] in only}
    rows: List[Dict[str, Any]] = []
    all_pairs: List[Tuple[str, str]] = []
    for key in sorted(keys):
        a, b = by_a.get(key, []), by_b.get(key, [])
        info = series.get(key)
        name = info["name"] if info else (a or b)[0].get("company")
        evaluated = info["evaluated"] if info else set()
        result = match_periods(a, b, evaluated)
        months = sorted(evaluated)
        cat_a, cat_b = month_categories(a, months), month_categories(b, months)
        pairs = [(cat_a[m], cat_b[m]) for m in months]
        all_pairs.extend(pairs)
        rows.append({
            "series": f"{name} / {key[1]} / {key[2]}", "company": name, "source": key[1], "dimension": key[2],
            "evaluated_known": info is not None, "both_none": not a and not b, **result,
            "kappa": cohens_kappa(pairs),
        })
    n_series = len(rows)
    both_none = sum(1 for r in rows if r["both_none"])
    matched = sum(len(r["matches"]) for r in rows)
    n_a, n_b = sum(r["n_a"] for r in rows), sum(r["n_b"] for r in rows)
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "rules": {"tolerance_months": TOLERANCE_MONTHS, "max_shift_months": MAX_SHIFT_MONTHS, "same_direction": True,
                  "one_to_one": True, "assignment": "Zeiträume aus A in zeitlicher Reihenfolge, frühester passender Zeitraum aus B"},
        "versions": {"a": doc_a.get("version"), "b": doc_b.get("version")},
        "series": rows,
        "totals": {
            "n_series": n_series, "n_a": n_a, "n_b": n_b, "matched": matched,
            "only_a": sum(len(r["only_a"]) for r in rows), "only_b": len([x for r in rows for x in r["only_b"]]),
            "series_both_none": both_none, "share_both_none": round(both_none / n_series, 4) if n_series else None,
            "share_matched_of_a": round(matched / n_a, 4) if n_a else None,
            "share_matched_of_b": round(matched / n_b, 4) if n_b else None,
        },
        "note": ("Beschreibende Zahlen. Übereinstimmung nach E5, Regel 6 (Toleranz, Richtung, Eins-zu-eins); "
                 "keine Aussage, welche Datei richtig liegt."),
        "kappa": {
            "overall": cohens_kappa(all_pairs),
            "categories": list(KAPPA_CATEGORIES),
            "n_series_with_months": sum(1 for r in rows if r["kappa"]["n_months"]),
            "basis": ("Bewertete Monate (E4) der verglichenen Reihen mit Serien-CSV; Monate innerhalb eines Zeitraums "
                      "tragen dessen Richtung, alle übrigen 'keine'; ohne Toleranz; gesamt über alle Monate gepoolt."),
        },
    }


# ── Bericht ──────────────────────────────────────────────────────────────────

def _pct(value: Optional[float]) -> str:
    return "–" if value is None else f"{100 * value:.0f} %"


def format_report(report: Dict[str, Any], path_a: str = "", path_b: str = "") -> str:
    r = report["rules"]
    t = report["totals"]
    lines = [
        "Übereinstimmung zweier Annotationsdateien (DZ1, E5)" + (f" – A: {path_a}, B: {path_b}" if path_a or path_b else ""),
        f"  Regel 6: Toleranz ±{r['tolerance_months']} Monat, Lücken bis {r['max_shift_months']} Monate, gleiche Richtung, Eins-zu-eins-Zuordnung.",
        f"  Zeiträume A: {t['n_a']}, B: {t['n_b']}; übereinstimmend {t['matched']}, nur bei A {t['only_a']}, nur bei B {t['only_b']}.",
        f"  Reihen: {t['n_series']}, davon beide ohne Zeitraum: {t['series_both_none']} ({_pct(t['share_both_none'])}).",
        "",
        f"  {'Reihe':<58}{'A':>4}{'B':>4}{'=':>4}{'nurA':>6}{'nurB':>6}",
    ]
    for s in report["series"]:
        lines.append(f"  {s['series'][:58]:<58}{s['n_a']:>4}{s['n_b']:>4}{len(s['matches']):>4}{len(s['only_a']):>6}{len(s['only_b']):>6}"
                     + ("" if s["evaluated_known"] else "   (ohne Serien-CSV: reine Toleranz)"))
    for s in report["series"]:
        if not (s["matches"] or s["only_a"] or s["only_b"]):
            continue
        lines.append(f"  {s['series']}:")
        for m in s["matches"]:
            lines.append(f"    Übereinstimmung: A {m['a']['period_from']}..{m['a']['period_to']} {m['a']['direction']} "
                         f"(Fenster {m['window_a'][0]}..{m['window_a'][1]}) <-> B {m['b']['period_from']}..{m['b']['period_to']}")
        for o in s["only_a"]:
            lines.append(f"    Nur bei A:       {o['a']['period_from']}..{o['a']['period_to']} {o['a']['direction']} "
                         f"(Fenster {o['window_a'][0]}..{o['window_a'][1]})")
        for o in s["only_b"]:
            lines.append(f"    Nur bei B:       {o['period_from']}..{o['period_to']} {o['direction']}")
    lines.append("")
    lines.append(report["note"])
    if report.get("kappa"):
        lines.extend(format_kappa(report))
    return "\n".join(lines)


def _num(value: Optional[float], digits: int = 2) -> str:
    return "–" if value is None else f"{value:.{digits}f}".replace(".", ",")


def format_kappa(report: Dict[str, Any]) -> List[str]:
    """κ-Block des Berichts (nach der bisherigen Ausgabe)."""
    k = report["kappa"]
    o = k["overall"]
    cats = k["categories"]
    lines = [
        "",
        "Cohens κ auf Monatsebene (Kategorien rise / fall / keine; bewertete Monate der Reihen mit Serien-CSV; ohne Toleranz)",
        f"  Gesamt: κ {_num(o['kappa'])} bei {o['n_months']} Monaten in {k['n_series_with_months']} Reihen; "
        f"beobachtete Übereinstimmung {_pct(o['p_o'])}, aus den Randverteilungen erwartet {_pct(o['p_e'])}."
        + (f" ({o['reason']})" if o["reason"] else ""),
        "  Kreuztabelle (Zeilen A, Spalten B): " + "  ".join(
            f"{a}: " + "/".join(str(o["matrix"].get(a, {}).get(b, 0)) for b in cats) for a in cats
        ) + f"  (Reihenfolge {' / '.join(cats)})",
        "",
        f"  {'Reihe':<58}{'Monate':>7}{'κ':>7}{'p_o':>7}{'p_e':>7}",
    ]
    for s in report["series"]:
        sk = s["kappa"]
        lines.append(f"  {s['series'][:58]:<58}{sk['n_months']:>7}{_num(sk['kappa']):>7}{_pct(sk['p_o']):>7}{_pct(sk['p_e']):>7}"
                     + ("   (ohne Serien-CSV: keine Monate)" if not s["evaluated_known"] else ""))
    lines.append("  κ „–“: nicht definiert (keine Monate, oder beide Dateien ordnen alle Monate derselben Kategorie zu).")
    lines.append("κ ist zufallskorrigiert: 1 = vollständige Übereinstimmung, 0 = so viel wie aus den Randverteilungen "
                 "erwartet. Beschreibend; keine Aussage, welche Datei richtig liegt.")
    return lines


# ── Teilmenge (--series) ─────────────────────────────────────────────────────

def selection_from_doc(doc: Any) -> Optional[List[Tuple[Optional[int], Optional[str]]]]:
    """(Unternehmens-id, Name) der Reihen aus dem Schlüssel des blinden Bogens (``reihen``) oder
    aus einer übersetzten Datei der Zweitannotation (``hinweise.herkunft.reihen``); ``None``,
    wenn das Dokument keine solche Liste enthält."""
    if not isinstance(doc, dict):
        return None
    reihen = doc.get("reihen")
    if not isinstance(reihen, dict):
        herkunft = (doc.get("hinweise") or {}).get("herkunft") if isinstance(doc.get("hinweise"), dict) else None
        reihen = herkunft.get("reihen") if isinstance(herkunft, dict) else None
    if not isinstance(reihen, dict):
        return None
    out: List[Tuple[Optional[int], Optional[str]]] = []
    for info in reihen.values():
        if isinstance(info, dict):
            cid = info.get("company_id")
            out.append((int(cid) if cid is not None else None, info.get("name") or info.get("company")))
    return out


def resolve_selection(spec: str, names: Dict[int, str]) -> Tuple[Optional[Set[str]], Optional[str]]:
    """``--series``: Datei (Schlüssel oder übersetzte Datei) oder kommagetrennte ids ->
    normalisierte Unternehmensnamen. Liefert (Namen, Fehlermeldung)."""
    if os.path.isfile(spec):
        doc, err = va._load_json(spec, "Reihenauswahl (--series)")
        if err:
            return None, err
        pairs = selection_from_doc(doc)
        if pairs is None:
            return None, (f"{spec} enthält weder 'reihen' (Schlüssel des blinden Bogens) noch "
                          "'hinweise.herkunft.reihen' (übersetzte Datei der Zweitannotation).")
    else:
        parts = [p for p in re.split(r"[,\s]+", spec.strip()) if p]
        if not parts or not all(p.isdigit() for p in parts):
            return None, f"--series '{spec}' ist weder eine Datei noch eine Liste von Unternehmens-ids."
        pairs = [(int(p), None) for p in parts]
    selected: Set[str] = set()
    unknown: List[str] = []
    for cid, name in pairs:
        resolved = names.get(cid) if cid is not None else None
        if not resolved and not name:
            unknown.append(str(cid))
            continue
        selected.add(va.normalize_company_name(resolved or name))
    if unknown:
        return None, f"Unternehmens-id(s) {', '.join(unknown)} nicht in data_density.json."
    return selected, None


# ── CLI ──────────────────────────────────────────────────────────────────────

def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--a", default=DEFAULT_A, help="Annotationsdatei A (Default: data/annotations.json)")
    parser.add_argument("--b", required=True, help="Annotationsdatei B (Pflichtangabe)")
    parser.add_argument("--series-dir", default=DEFAULT_SERIES_DIR, help="Serien-CSVs (bewertete Monate, geeignete Reihen)")
    parser.add_argument("--density", default=DEFAULT_DENSITY, help="data_density.json für die Unternehmensnamen")
    parser.add_argument("--source", default="employee", choices=list(VALID_SOURCES), help="Quelle der Reihen (Default: employee)")
    parser.add_argument("--json", dest="json_out", help="Ergebnis zusätzlich als JSON-Datei schreiben")
    parser.add_argument("--series", dest="series_spec",
                        help="nur diese Reihen: Schlüssel des blinden Bogens, übersetzte Datei der Zweitannotation "
                             "(hinweise.herkunft.reihen) oder kommagetrennte Unternehmens-ids")
    args = parser.parse_args(argv)

    docs = []
    for label, path in (("A", args.a), ("B", args.b)):
        doc, err = va._load_json(path, f"Annotationsdatei {label}")
        if err:
            print(f"FEHLER: {err}")
            return 1
        if not isinstance(doc, dict) or not isinstance(doc.get("annotations"), list):
            print(f"FEHLER: Annotationsdatei {label} hat nicht das Schema {{version, hinweise, annotations}}: {path}")
            return 1
        docs.append(doc)
    series = series_from_csvs(args.series_dir, args.source, args.density) if os.path.isdir(args.series_dir) else {}
    if not series:
        print(f"Hinweis: keine Serien-CSVs unter {args.series_dir}; es gilt die reine Toleranz, und die Reihen ohne Einträge fehlen.")
    only: Optional[Set[str]] = None
    if args.series_spec:
        only, err = resolve_selection(args.series_spec, company_names(args.density))
        if err:
            print(f"FEHLER: {err}")
            return 1
        print(f"Auswahl (--series): {len(only)} Reihen.")
    elif selection_from_doc(docs[1]) is not None:
        print(f"Hinweis: Datei B stammt aus der blinden Zweitannotation; mit --series {args.b} "
              "werden nur die Reihen des blinden Bogens verglichen.")
    report = compare(docs[0], docs[1], series, source=args.source, only=only)
    if report["totals"]["n_a"] == 0 and report["totals"]["n_b"] == 0:
        print("Hinweis: beide Dateien enthalten keine Einträge; der Abgleich liefert noch keine Übereinstimmung.")
    print(format_report(report, os.path.relpath(args.a, BACKEND_DIR), os.path.relpath(args.b, BACKEND_DIR)))
    if args.json_out:
        os.makedirs(os.path.dirname(os.path.abspath(args.json_out)), exist_ok=True)
        with open(args.json_out, "w", encoding="utf-8") as fh:
            json.dump(report, fh, ensure_ascii=False, indent=2)
            fh.write("\n")
        print(f"\nErgebnis gespeichert: {args.json_out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
