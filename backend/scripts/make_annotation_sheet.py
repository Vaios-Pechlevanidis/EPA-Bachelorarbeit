"""
Annotationsbogen für die Referenzzeiträume (DZ1, E5): eine eigenständige
HTML-Datei mit einem Diagramm je Reihe, erzeugt allein aus den Serien-CSVs
unter ``backend/data/series/``.

Umfang (Standard, festgehalten am 2026-10-08): Quelle Mitarbeitende
(``employee``), Dimension Gesamtbewertung (``durchschnittsbewertung``), alle
Unternehmen, die nach E4 für die Erkennung geeignet sind (mindestens
``MIN_EVALUATED_MONTHS`` = 12 Monate mit mindestens ``MIN_REVIEWS_PER_MONTH``
= 5 Bewertungen). Ein Monat gilt hier als bewertet, wenn ``count`` in der CSV
die Mindestdichte erreicht und ein Monatsmittel vorliegt. Mit
``--include-ineligible`` erscheinen auch die übrigen Unternehmen, mit
``--source candidates`` die Bewerberquelle.

Je Reihe zeigt der Bogen

- das Monatsmittel der Gesamtbewertung (Linie zwischen bewerteten Monaten;
  Monate unter der Mindestdichte als kleine graue Punkte ohne Linie),
- die Anzahl der Bewertungen je Monat als Balken, Monate unter der
  Mindestdichte grau, mit der Linie der Mindestdichte,
- eine aufklappbare Monatstabelle (Monat, Mittel, Anzahl, Differenz zum
  letzten Monat mit Wert), damit die Pflichtangaben der ``note`` (Regel 11)
  abgelesen werden können,

dazu oben die Kurzfassung des Annotationsprotokolls aus E5 und die Regeln aus
``backend/data/annotations.json`` (``hinweise.protokoll``), nur gelesen.

Der Bogen enthält **keine** Erkennungsergebnisse: Das Skript importiert weder
``services.anomaly_service`` noch ``models.changepoint_detector`` und zeichnet
keine Markierung, keine Niveaulinie und keinen hervorgehobenen Einzelmonat
(Unabhängigkeit der Referenz, E5; Test:
``backend/tests/test_make_annotation_sheet.py``). Die Datenbank wird nicht
angefasst; die erzeugte Datei liegt unter ``backend/data/`` und ist über
``.gitignore`` vom Repository ausgeschlossen.

Verwendung
----------
    cd backend
    uv run python scripts/make_annotation_sheet.py                 # -> data/annotationsbogen.html
    uv run python scripts/make_annotation_sheet.py --source candidates --include-ineligible
    uv run python scripts/make_annotation_sheet.py --out /pfad/bogen.html
"""

from __future__ import annotations

import argparse
import csv
import glob
import html
import json
import os
import re
import sys
from datetime import date
from typing import Any, Dict, List, Optional

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND_DIR)

# Nur Reihen-Konstanten (E4); bewusst kein Import von anomaly_service oder changepoint_detector.
from services.rating_series_service import (  # noqa: E402
    MIN_EVALUATED_MONTHS,
    MIN_REVIEWS_PER_MONTH,
    OVERALL_DIMENSION,
    VALID_SOURCES,
)

DEFAULT_SERIES_DIR = os.path.join(BACKEND_DIR, "data", "series")
DEFAULT_DENSITY = os.path.join(BACKEND_DIR, "data", "data_density.json")
DEFAULT_ANNOTATIONS = os.path.join(BACKEND_DIR, "data", "annotations.json")
DEFAULT_OUT = os.path.join(BACKEND_DIR, "data", "annotationsbogen.html")

SOURCE_LABELS = {"employee": "Mitarbeitende", "candidates": "Bewerbende"}
DIMENSION_LABEL = "Gesamtbewertung (durchschnittsbewertung)"

# Kurzfassung des Annotationsprotokolls, wörtlich aus docs/entscheidungen.md, E5.
KURZFASSUNG_E5 = (
    "Einheit Kalendermonat; Zeitraum 1–3, höchstens 6 Monate; Randmonate mit ≥ 5 Bewertungen; "
    "Richtwert ≥ 0,5 Sterne Niveauunterschied gegenüber den bis zu sechs Vormonaten; 0–3 Zeiträume je "
    "Reihe; Toleranz beim Abgleich ±1 Monat mit Eins-zu-eins-Zuordnung und F1 als Hauptmaß; "
    "Ereignisanker erst nach der Beurteilung aus der Reihe; Unternehmen unter der Mindestdichte aus E4 "
    "ohne Einträge."
)

_FILE_RE = re.compile(r"^(\d+)_(.+)_(employee|candidates)\.csv$")


# ── Daten ────────────────────────────────────────────────────────────────────

def read_series_csv(path: str) -> List[Dict[str, Any]]:
    """Zeilen der Serien-CSV (``period``, ``mean``, ``count``, ``delta``)."""
    rows: List[Dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as fh:
        for row in csv.DictReader(fh, delimiter=";"):
            mean_raw = (row.get("mean_durchschnittsbewertung") or "").strip()
            delta_raw = (row.get("delta_vs_previous") or "").strip()
            rows.append({
                "period": row["period"],
                "mean": float(mean_raw) if mean_raw else None,
                "count": int(row.get("count") or 0),
                "delta": float(delta_raw) if delta_raw else None,
            })
    return rows


def is_evaluated(month: Dict[str, Any], min_reviews: int = MIN_REVIEWS_PER_MONTH) -> bool:
    """Bewerteter Monat nach E4 auf Basis der CSV: Mindestdichte erreicht und Mittel vorhanden."""
    return month["count"] >= min_reviews and month["mean"] is not None


def evaluated_months(series: List[Dict[str, Any]]) -> int:
    return sum(1 for m in series if is_evaluated(m))


def is_eligible(series: List[Dict[str, Any]], min_months: int = MIN_EVALUATED_MONTHS) -> bool:
    return evaluated_months(series) >= min_months


def company_names(density_path: str) -> Dict[int, str]:
    """``id -> bereinigter Name`` aus data_density.json; leer, wenn die Datei fehlt."""
    if not os.path.exists(density_path):
        return {}
    with open(density_path, "r", encoding="utf-8") as fh:
        density = json.load(fh)
    return {
        int(c["id"]): " ".join(str(c.get("name") or c.get("name_raw") or "").split())
        for c in density.get("companies", []) if c.get("id") is not None
    }


def collect_series(series_dir: str, source: str, names: Dict[int, str],
                   include_ineligible: bool = False) -> List[Dict[str, Any]]:
    """Alle Reihen der Quelle aus dem Serienordner, sortiert nach Unternehmens-ID."""
    out: List[Dict[str, Any]] = []
    for path in sorted(glob.glob(os.path.join(series_dir, f"*_{source}.csv"))):
        m = _FILE_RE.match(os.path.basename(path))
        if not m:
            continue
        cid, slug = int(m.group(1)), m.group(2)
        series = read_series_csv(path)
        eligible = is_eligible(series)
        if not eligible and not include_ineligible:
            continue
        out.append({
            "company_id": cid,
            "name": names.get(cid) or slug.replace("_", " "),
            "slug": slug,
            "source": source,
            "file": os.path.basename(path),
            "series": series,
            "evaluated_months": evaluated_months(series),
            "eligible": eligible,
        })
    out.sort(key=lambda s: s["company_id"])
    return out


def protocol_texts(annotations_path: str) -> Dict[str, Any]:
    """Regeln, Vorgehen und note-Beispiel aus annotations.json (nur lesen)."""
    if not os.path.exists(annotations_path):
        return {"regeln": [], "vorgehen": [], "note_beispiel": None, "quelle": None, "gefunden": False}
    with open(annotations_path, "r", encoding="utf-8") as fh:
        doc = json.load(fh)
    hinweise = doc.get("hinweise") or {}
    protokoll = hinweise.get("protokoll") or {}
    return {
        "regeln": list(protokoll.get("regeln") or []),
        "vorgehen": list(hinweise.get("vorgehen") or []),
        "note_beispiel": protokoll.get("note_beispiel"),
        "quelle": protokoll.get("quelle"),
        "gefunden": True,
    }


# ── Diagramm (SVG, ohne Skript und ohne externe Bibliothek) ─────────────────

CHART_LEFT, CHART_RIGHT = 56, 16
MEAN_HEIGHT, COUNT_HEIGHT, GAP = 170, 90, 28
TOP = 12
STEP_MIN, STEP_MAX = 5.0, 14.0


def _fmt(value: Optional[float], digits: int = 2) -> str:
    return "–" if value is None else f"{value:.{digits}f}".replace(".", ",")


def series_svg(series: List[Dict[str, Any]], min_reviews: int = MIN_REVIEWS_PER_MONTH) -> str:
    """SVG mit Monatsmittel (oben) und Anzahl je Monat (unten)."""
    n = max(len(series), 1)
    step = max(STEP_MIN, min(STEP_MAX, 1040 / n))
    width = CHART_LEFT + step * n + CHART_RIGHT
    mean_top = TOP
    mean_bottom = mean_top + MEAN_HEIGHT
    count_top = mean_bottom + GAP
    count_bottom = count_top + COUNT_HEIGHT
    height = count_bottom + 26
    max_count = max([m["count"] for m in series] + [min_reviews * 2])

    def x_of(i: int) -> float:
        return CHART_LEFT + step * (i + 0.5)

    def y_mean(v: float) -> float:
        return mean_bottom - (v - 1.0) / 4.0 * MEAN_HEIGHT

    def y_count(c: int) -> float:
        return count_bottom - c / max_count * COUNT_HEIGHT

    parts: List[str] = [
        f'<svg class="reihe" viewBox="0 0 {width:.0f} {height:.0f}" width="100%" '
        f'preserveAspectRatio="xMinYMin meet" role="img" aria-label="Monatsmittel und Anzahl je Monat">'
    ]
    # Raster und Achsen oben (1–5 Sterne)
    for v in (1, 2, 3, 4, 5):
        y = y_mean(v)
        parts.append(f'<line class="raster" x1="{CHART_LEFT}" y1="{y:.1f}" x2="{width - CHART_RIGHT:.1f}" y2="{y:.1f}"/>')
        parts.append(f'<text class="achse" x="{CHART_LEFT - 6}" y="{y + 4:.1f}" text-anchor="end">{v}</text>')
    parts.append(f'<text class="achsentitel" x="{CHART_LEFT}" y="{mean_top - 2}">Monatsmittel (Sterne)</text>')
    # Jahresmarken: je Januar eine Linie mit Jahreszahl; das Startjahr nur, wenn der erste
    # Januar weit genug entfernt ist (sonst überlappen die Beschriftungen).
    first_january = next((i for i, m in enumerate(series) if m["period"].endswith("-01")), len(series))
    for i, m in enumerate(series):
        if m["period"].endswith("-01") or (i == 0 and first_january * step >= 30):
            x = CHART_LEFT + step * i
            parts.append(f'<line class="jahr" x1="{x:.1f}" y1="{mean_top}" x2="{x:.1f}" y2="{count_bottom}"/>')
            parts.append(f'<text class="achse" x="{x + 2:.1f}" y="{count_bottom + 16}">{m["period"][:4]}</text>')
    # Linie zwischen aufeinanderfolgenden bewerteten Monaten (Lücke = Unterbrechung)
    points: List[str] = []
    segments: List[List[str]] = []
    prev_i: Optional[int] = None
    for i, m in enumerate(series):
        if is_evaluated(m, min_reviews):
            if prev_i is not None and i - prev_i > 1:
                segments.append(points)
                points = []
            points.append(f"{x_of(i):.1f},{y_mean(m['mean']):.1f}")
            prev_i = i
    segments.append(points)
    for seg in segments:
        if len(seg) >= 2:
            parts.append(f'<polyline class="mittel" points="{" ".join(seg)}"/>')
    # Punkte: bewertet (gefüllt) und dünn (grau, klein)
    for i, m in enumerate(series):
        if m["mean"] is None:
            continue
        x, y = x_of(i), y_mean(m["mean"])
        cls = "punkt" if is_evaluated(m, min_reviews) else "punkt duenn"
        r = 2.6 if is_evaluated(m, min_reviews) else 1.8
        title = f"{m['period']}: Mittel {_fmt(m['mean'])}, {m['count']} Bewertungen"
        if not is_evaluated(m, min_reviews):
            title += f" (unter der Mindestdichte {min_reviews})"
        parts.append(f'<circle class="{cls}" cx="{x:.1f}" cy="{y:.1f}" r="{r}"><title>{html.escape(title)}</title></circle>')
    # Balken der Anzahl je Monat
    parts.append(f'<text class="achsentitel" x="{CHART_LEFT}" y="{count_top - 4}">Anzahl Bewertungen je Monat</text>')
    y_min = y_count(min_reviews)
    parts.append(f'<line class="mindestdichte" x1="{CHART_LEFT}" y1="{y_min:.1f}" x2="{width - CHART_RIGHT:.1f}" y2="{y_min:.1f}"/>')
    parts.append(f'<text class="achse" x="{CHART_LEFT - 6}" y="{y_min + 4:.1f}" text-anchor="end">{min_reviews}</text>')
    parts.append(f'<text class="achse" x="{CHART_LEFT - 6}" y="{count_top + 4}" text-anchor="end">{max_count}</text>')
    bar_w = max(1.0, step - 1.0)
    for i, m in enumerate(series):
        if m["count"] <= 0:
            continue
        cls = "balken" if m["count"] >= min_reviews else "balken duenn"
        x = CHART_LEFT + step * i + 0.5
        y = y_count(m["count"])
        parts.append(
            f'<rect class="{cls}" x="{x:.1f}" y="{y:.1f}" width="{bar_w:.1f}" height="{count_bottom - y:.1f}">'
            f'<title>{m["period"]}: {m["count"]} Bewertungen</title></rect>'
        )
    parts.append("</svg>")
    return "".join(parts)


# ── HTML ─────────────────────────────────────────────────────────────────────

CSS = """
body { font-family: -apple-system, "Segoe UI", Helvetica, Arial, sans-serif; margin: 0; padding: 24px; color: #1b1b1b; background: #fff; max-width: 1200px; }
h1 { font-size: 1.5rem; margin: 0 0 4px; } h2 { font-size: 1.15rem; margin: 36px 0 4px; border-top: 1px solid #ddd; padding-top: 16px; }
p, li, td, th { font-size: 0.92rem; line-height: 1.4; }
.meta { color: #555; margin: 0 0 12px; }
.kasten { background: #f6f7f9; border: 1px solid #dde1e6; border-radius: 6px; padding: 12px 16px; margin: 12px 0; }
.kasten ol, .kasten ul { padding-left: 20px; margin: 6px 0; }
nav ul { columns: 3; padding-left: 18px; }
svg.reihe { display: block; max-width: 100%; height: auto; margin: 8px 0; }
.raster { stroke: #e6e6e6; stroke-width: 1; } .jahr { stroke: #eceff3; stroke-width: 1; }
.achse { font-size: 10px; fill: #666; } .achsentitel { font-size: 11px; fill: #333; }
.mittel { fill: none; stroke: #2b5aa6; stroke-width: 1.4; }
.punkt { fill: #2b5aa6; } .punkt.duenn { fill: #b4b8bd; }
.balken { fill: #7aa0d8; } .balken.duenn { fill: #cfd3d8; }
.mindestdichte { stroke: #c0392b; stroke-width: 1; stroke-dasharray: 4 3; }
.legende span { display: inline-block; margin-right: 14px; } .legende i { display: inline-block; width: 10px; height: 10px; margin-right: 4px; vertical-align: middle; border-radius: 50%; }
details { margin: 6px 0 0; } summary { cursor: pointer; font-size: 0.9rem; color: #2b5aa6; }
table { border-collapse: collapse; margin-top: 6px; } th, td { border: 1px solid #ddd; padding: 2px 8px; text-align: right; } th:first-child, td:first-child { text-align: left; }
tr.duenn td { color: #8a8f95; } tr.leer td { color: #b4b8bd; }
@media print { nav, details { display: none; } h2 { page-break-before: always; } }
"""


def render_html(entries: List[Dict[str, Any]], source: str, protocol: Dict[str, Any],
                generated: Optional[date] = None, include_ineligible: bool = False,
                min_reviews: int = MIN_REVIEWS_PER_MONTH, min_months: int = MIN_EVALUATED_MONTHS) -> str:
    """Eigenständiger Bogen: Umfang, Protokoll, Übersicht, ein Abschnitt je Reihe."""
    generated = generated or date.today()
    src_label = SOURCE_LABELS.get(source, source)
    h: List[str] = []
    h.append("<!DOCTYPE html><html lang=\"de\"><head><meta charset=\"utf-8\">")
    h.append(f"<title>Annotationsbogen Referenzzeiträume – {html.escape(src_label)}</title>")
    h.append(f"<style>{CSS}</style></head><body>")
    h.append("<h1>Annotationsbogen für die Referenzzeiträume (DZ1, E5)</h1>")
    h.append(
        f"<p class=\"meta\">Erzeugt am {generated.isoformat()} aus den Serien-CSVs unter "
        f"<code>backend/data/series/</code> (Monatsmittel und Anzahl je Kalendermonat, E3). "
        f"Quelle: {html.escape(src_label)}; Dimension: {html.escape(DIMENSION_LABEL)}; "
        f"{len(entries)} Reihen" + (" (einschließlich nicht geeigneter Unternehmen)" if include_ineligible else
                                    f", nur nach E4 geeignete Unternehmen (mindestens {min_months} Monate mit "
                                    f"mindestens {min_reviews} Bewertungen)") + ".</p>"
    )
    h.append("<div class=\"kasten\"><p><strong>Dieser Bogen zeigt nur die Reihen selbst.</strong> Er enthält keine "
             "Ergebnisse einer automatischen Erkennung, keine Markierungen und keine Niveaulinien; die Beurteilung "
             "erfolgt allein aus dem Verlauf (E5, Ersatzregel: Annotation vor der Evaluation, ohne Einsicht in "
             "Erkennungsergebnisse, Karte und Detailseite des Dashboards nicht öffnen).</p>"
             f"<p><strong>Kurzfassung des Protokolls (E5):</strong> {html.escape(KURZFASSUNG_E5)}</p>")
    if protocol.get("regeln"):
        h.append("<p><strong>Regeln</strong>" + (f" ({html.escape(str(protocol.get('quelle')))})" if protocol.get("quelle") else "") + ":</p><ol>")
        for rule in protocol["regeln"]:
            text = re.sub(r"^\d+\s+", "", str(rule))
            h.append(f"<li>{html.escape(text)}</li>")
        h.append("</ol>")
    if protocol.get("note_beispiel"):
        h.append(f"<p><strong>Beispiel für die <code>note</code>:</strong> {html.escape(str(protocol['note_beispiel']))}</p>")
    if protocol.get("vorgehen"):
        h.append("<p><strong>Vorgehen (annotations.json):</strong></p><ul>")
        for step in protocol["vorgehen"]:
            h.append(f"<li>{html.escape(str(step))}</li>")
        h.append("</ul>")
    if not protocol.get("gefunden"):
        h.append("<p><em>annotations.json wurde nicht gefunden; es gilt die Kurzfassung oben.</em></p>")
    h.append("<p class=\"legende\"><span><i style=\"background:#2b5aa6\"></i>bewerteter Monat (Anzahl ≥ Mindestdichte)</span>"
             "<span><i style=\"background:#b4b8bd\"></i>Monat unter der Mindestdichte (nur zur Orientierung)</span>"
             "<span><i style=\"background:#c0392b;border-radius:0;height:2px\"></i>Mindestdichte je Monat</span></p></div>")
    # Übersicht
    h.append("<nav><p><strong>Reihen im Bogen</strong></p><ul>")
    for e in entries:
        first = e["series"][0]["period"] if e["series"] else "–"
        last = e["series"][-1]["period"] if e["series"] else "–"
        flag = "" if e["eligible"] else " – nicht geeignet (E4)"
        h.append(f"<li><a href=\"#s-{e['company_id']}-{e['source']}\">{html.escape(e['name'])} ({e['company_id']})</a>: "
                 f"{e['evaluated_months']} bewertete Monate, {html.escape(first)} – {html.escape(last)}{flag}</li>")
    h.append("</ul></nav>")
    # Abschnitte
    for e in entries:
        s = e["series"]
        first = s[0]["period"] if s else "–"
        last = s[-1]["period"] if s else "–"
        h.append(f"<section id=\"s-{e['company_id']}-{e['source']}\"><h2>{html.escape(e['name'])} ({e['company_id']}) – "
                 f"{html.escape(src_label)} – {html.escape(DIMENSION_LABEL)}</h2>")
        h.append(f"<p class=\"meta\">Datei <code>{html.escape(e['file'])}</code>; {len(s)} Kalendermonate {html.escape(first)} – "
                 f"{html.escape(last)}; {e['evaluated_months']} bewertete Monate"
                 + ("" if e["eligible"] else f"; <strong>nicht geeignet nach E4</strong> (unter {min_months}), keine Einträge (Regel 9)")
                 + ".</p>")
        h.append(series_svg(s, min_reviews))
        h.append("<details><summary>Monatstabelle (für die Angaben in der note)</summary><table><thead><tr>"
                 "<th>Monat</th><th>Mittel</th><th>Anzahl</th><th>Δ zum letzten Monat mit Wert</th><th>Status</th></tr></thead><tbody>")
        for m in s:
            if m["mean"] is None:
                cls, status = "leer", "keine Bewertung"
            elif is_evaluated(m, min_reviews):
                cls, status = "bewertet", "bewertet"
            else:
                cls, status = "duenn", f"unter Mindestdichte ({min_reviews})"
            h.append(f"<tr class=\"{cls}\"><td>{m['period']}</td><td>{_fmt(m['mean'], 3)}</td><td>{m['count']}</td>"
                     f"<td>{_fmt(m['delta'], 3)}</td><td>{status}</td></tr>")
        h.append("</tbody></table></details></section>")
    h.append("</body></html>")
    return "\n".join(h)


# ── CLI ──────────────────────────────────────────────────────────────────────

def build_sheet(series_dir: str = DEFAULT_SERIES_DIR, source: str = "employee", out: str = DEFAULT_OUT,
                density_path: str = DEFAULT_DENSITY, annotations_path: str = DEFAULT_ANNOTATIONS,
                include_ineligible: bool = False) -> Dict[str, Any]:
    """Bogen schreiben; liefert Pfad und Zahl der Reihen."""
    if source not in VALID_SOURCES:
        raise ValueError(f"source '{source}' ungültig; erlaubt: {', '.join(VALID_SOURCES)}.")
    entries = collect_series(series_dir, source, company_names(density_path), include_ineligible)
    page = render_html(entries, source, protocol_texts(annotations_path), include_ineligible=include_ineligible)
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(page)
    return {"out": out, "n_series": len(entries), "companies": [e["name"] for e in entries]}


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--series-dir", default=DEFAULT_SERIES_DIR, help="Ordner der Serien-CSVs (Default: data/series)")
    parser.add_argument("--source", default="employee", choices=list(VALID_SOURCES), help="Quelle (Default: employee)")
    parser.add_argument("--out", default=DEFAULT_OUT, help="Zieldatei (Default: data/annotationsbogen.html, nicht eingecheckt)")
    parser.add_argument("--density", default=DEFAULT_DENSITY, help="data_density.json für die Unternehmensnamen")
    parser.add_argument("--annotations", default=DEFAULT_ANNOTATIONS, help="annotations.json für die Protokolltexte (nur lesen)")
    parser.add_argument("--include-ineligible", action="store_true", help="auch Unternehmen unter der Mindestdichte (E4) aufnehmen")
    args = parser.parse_args(argv)
    if not os.path.isdir(args.series_dir):
        print(f"FEHLER: Serienordner fehlt: {args.series_dir}\nHinweis: zuerst 'uv run python scripts/make_annotation_basis.py' ausführen.")
        return 1
    result = build_sheet(args.series_dir, args.source, args.out, args.density, args.annotations, args.include_ineligible)
    print(f"Annotationsbogen geschrieben: {result['out']} ({result['n_series']} Reihen, Quelle {args.source}).")
    for name in result["companies"]:
        print(f"  - {name}")
    print("Die Datei ist nicht Teil des Repositorys (.gitignore).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
