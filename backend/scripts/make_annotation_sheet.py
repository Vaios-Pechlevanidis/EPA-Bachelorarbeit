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

``--companies`` begrenzt den Bogen auf eine Teilmenge (Unternehmens-ids).

Blinde Fassung (``--blind``, zweite Person, E5)
-----------------------------------------------
Für eine zweite Person, die weder Unternehmen noch Kalenderdaten sehen soll (sonst
könnte sie Ereignisse aus Weltwissen einbeziehen):

- Reihen heißen „Reihe A“, „Reihe B“ … in zufälliger, durch ``--seed`` fester
  Reihenfolge (ohne ``--seed`` wird ein Seed gezogen und im Schlüssel vermerkt),
- Monate heißen M001, M002 …: fortlaufende Kalendermonate ab dem ersten Monat der
  jeweiligen Reihe; fehlt ein Kalendermonat in der CSV, wird er als leerer Monat
  eingefügt, damit Lücken sichtbar bleiben. Senkrechte Marken alle zwölf Monate ab
  M001 statt der Jahresmarken,
- keine Jahreszahlen, keine Namen, keine Unternehmens-ids, keine Dateinamen und kein
  Erzeugungsdatum im HTML (Prüfung ``blind_leaks`` vor dem Schreiben),
- Protokolltexte bleiben, aber ohne Ereignisanker-Schritt: Regel 7 entfällt
  ausdrücklich, die Regeln 8, 9 und 11 stehen sinngemäß für die zweite Person
  (``BLIND_RULES``); Vorgehen und note-Beispiel sind eigene Fassungen, weil das
  Vorgehen aus annotations.json die Serien-CSVs mit Unternehmensnamen öffnet. Blind gibt
  es nur die Beurteilung „Reihe allein“.

Zusätzlich entsteht eine Schlüsseldatei (Standard
``backend/data/annotationsbogen_blind_schluessel.json``, über ``.gitignore``
ausgeschlossen) mit der Zuordnung Reihe → Unternehmens-id, Name, Quelle und
Mxxx → YYYY-MM. Die Rückübersetzung der blinden Annotationsdatei übernimmt
``scripts/blind_annotations.py``; Ablauf in ``docs/annotation-anleitung.md``. Ohne
``--blind`` bleibt die Ausgabe unverändert (Test).

Verwendung
----------
    cd backend
    uv run python scripts/make_annotation_sheet.py                 # -> data/annotationsbogen.html
    uv run python scripts/make_annotation_sheet.py --source candidates --include-ineligible
    uv run python scripts/make_annotation_sheet.py --out /pfad/bogen.html
    uv run python scripts/make_annotation_sheet.py --blind --companies 19,24,28 --seed 4711
        # -> data/annotationsbogen_blind.html und data/annotationsbogen_blind_schluessel.json
"""

from __future__ import annotations

import argparse
import csv
import glob
import hashlib
import html
import json
import os
import random
import re
import sys
from datetime import date
from typing import Any, Dict, List, Optional, Tuple

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
DEFAULT_OUT_BLIND = os.path.join(BACKEND_DIR, "data", "annotationsbogen_blind.html")
DEFAULT_KEY = os.path.join(BACKEND_DIR, "data", "annotationsbogen_blind_schluessel.json")

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

# Blinde Fassung: Kurzfassung ohne Ereignisanker, Monate als Index.
KURZFASSUNG_BLIND = (
    "Einheit Kalendermonat, im Bogen als fortlaufender Index M001, M002 … ab dem ersten Monat der Reihe; "
    "Zeitraum 1–3, höchstens 6 Monate; Randmonate mit ≥ 5 Bewertungen; Richtwert ≥ 0,5 Sterne "
    "Niveauunterschied gegenüber den bis zu sechs Vormonaten; 0–3 Zeiträume je Reihe; Toleranz beim Abgleich "
    "±1 Monat mit Eins-zu-eins-Zuordnung und F1 als Hauptmaß; Beurteilung allein aus der Reihe, ohne Suche "
    "nach Ereignissen (blinde Fassung); Reihen unter der Mindestdichte aus E4 ohne Einträge."
)

# Regeln aus annotations.json (hinweise.protokoll.regeln), die in der blinden Fassung ersetzt
# werden; Nummern bleiben, damit Verweise wie „Regel 6“ gültig sind. Regel 7 (Ereignisanker)
# entfällt ausdrücklich; 8, 9 und 11 stehen sinngemäß für die zweite Person.
BLIND_RULES: Dict[str, str] = {
    "7": ("Ereignisanker: entfällt in der blinden Fassung. Jeder Zeitraum wird allein aus der Reihe "
          "beurteilt; keine Suche nach Ereignissen, keine Vermutung über Unternehmen oder Kalenderdaten. "
          "Beurteilung immer 'Reihe allein'."),
    "8": ("Unabhängigkeit: Datei vollständig erstellen und abgeben, ohne Einsicht in Erkennungsergebnisse, "
          "in das Dashboard oder in die Einträge des Autors und ohne Absprache zu einzelnen Reihen; "
          "Rückübersetzung, Prüfung und Versionierung übernimmt der Autor."),
    "9": ("Dünn belegte Reihen (< 12 Monate mit >= 5 Bewertungen) erhalten keine Einträge; der Bogen "
          "enthält nur geeignete Reihen oder kennzeichnet die übrigen als nicht geeignet."),
    "11": ("Inhalt der note (deutsch, in dieser Reihenfolge): Vorniveau (Mittel, Monate als Index Mxxx, "
           "n je Monat) - Niveau im Zeitraum (Mittel, n je Monat) - Differenz in Sternen - Richtung - "
           "ggf. Streuungshinweis - Beurteilung: 'Reihe allein'."),
}
BLIND_NOTE_BEISPIEL = "Vorniveau 3,9 (M010 bis M014, n=7-12); Zeitraum 3,1 (n=9, 11); Δ -0,8; fall; Reihe allein."

# Kalendermonat im Text (für die Prüfung der blinden Fassung)
DATE_RE = re.compile(r"\b(?:19|20)\d\d-\d\d\b")

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


def parse_company_ids(values: Optional[List[str]]) -> List[int]:
    """Unternehmens-ids aus ``--companies`` (kommagetrennt und/oder mehrere Angaben)."""
    ids: List[int] = []
    for value in values or []:
        for part in re.split(r"[,\s]+", str(value).strip()):
            if not part:
                continue
            if not part.isdigit():
                raise ValueError(f"Unternehmens-id '{part}' ist keine ganze Zahl.")
            ids.append(int(part))
    return sorted(set(ids))


def select_companies(entries: List[Dict[str, Any]], ids: List[int]) -> List[Dict[str, Any]]:
    """Nur die Reihen der genannten Unternehmens-ids (Teilmenge); unbekannte ids sind ein Fehler."""
    wanted = set(ids)
    missing = sorted(wanted - {e["company_id"] for e in entries})
    if missing:
        raise ValueError(
            f"Unternehmens-id(s) {', '.join(map(str, missing))} nicht im Bogen: keine Serien-CSV der Quelle "
            "oder nicht geeignet nach E4 (dann zusätzlich --include-ineligible)."
        )
    return [e for e in entries if e["company_id"] in wanted]


# ── Blinde Fassung (zweite Person, E5) ──────────────────────────────────────

def month_index(period: str) -> int:
    return int(period[:4]) * 12 + int(period[5:7]) - 1


def month_str(index: int) -> str:
    return f"{index // 12:04d}-{index % 12 + 1:02d}"


def series_label(i: int) -> str:
    """Buchstaben der Reihe: 0 -> A, 25 -> Z, 26 -> AA (Schema der Tabellenspalten)."""
    letters = ""
    i += 1
    while i > 0:
        i, rest = divmod(i - 1, 26)
        letters = chr(ord("A") + rest) + letters
    return letters


def month_labels(n: int) -> List[str]:
    """M001 … für ``n`` Kalendermonate (mindestens drei Ziffern)."""
    width = max(3, len(str(n)))
    return [f"M{k:0{width}d}" for k in range(1, n + 1)]


def fill_calendar_gaps(series: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Fehlende Kalendermonate zwischen erstem und letztem Monat als leere Monate einfügen
    (Anzahl 0, kein Mittel), damit der Index Mxxx fortlaufend den Kalendermonaten folgt."""
    if not series:
        return []
    by_period = {m["period"]: m for m in series}
    indices = [month_index(m["period"]) for m in series]
    return [
        by_period.get(month_str(i)) or {"period": month_str(i), "mean": None, "count": 0, "delta": None}
        for i in range(min(indices), max(indices) + 1)
    ]


def blind_entries(entries: List[Dict[str, Any]], seed: int) -> Tuple[List[Dict[str, Any]], Dict[str, Dict[str, Any]]]:
    """Reihen der blinden Fassung und Schlüssel; reine Funktion.

    Die Reihen erhalten in zufälliger, durch ``seed`` fester Reihenfolge die Bezeichnungen
    „Reihe A“, „Reihe B“ …; die Monate heißen M001 … (Kalendermonate ab dem ersten Monat der
    Reihe, Lücken eingefügt). Die blinden Einträge enthalten weder Namen noch ids noch
    Dateinamen. Liefert (blinde Einträge, ``{Bezeichnung: Zuordnung}``)."""
    order = sorted(entries, key=lambda e: (e["company_id"], e["source"]))
    random.Random(seed).shuffle(order)
    blinded: List[Dict[str, Any]] = []
    key: Dict[str, Dict[str, Any]] = {}
    for i, e in enumerate(order):
        letters = series_label(i)
        label = f"Reihe {letters}"
        filled = fill_calendar_gaps(e["series"])
        labels = month_labels(len(filled))
        blinded.append({
            "label": label, "anchor": f"s-reihe-{letters.lower()}", "source": e["source"], "series": filled,
            "month_labels": labels, "evaluated_months": e["evaluated_months"], "eligible": e["eligible"],
        })
        key[label] = {
            "company_id": e["company_id"], "name": e["name"], "source": e["source"], "dimension": OVERALL_DIMENSION,
            "file": e["file"], "first_month": filled[0]["period"] if filled else None,
            "last_month": filled[-1]["period"] if filled else None, "evaluated_months": e["evaluated_months"],
            "eligible": e["eligible"], "monate": {lab: m["period"] for lab, m in zip(labels, filled)},
        }
    return blinded, key


def mask_dates(text: str) -> str:
    return DATE_RE.sub("JJJJ-MM", text)


def blind_vorgehen(source: str) -> List[str]:
    """Vorgehen der blinden Fassung (ersetzt hinweise.vorgehen, das die Serien-CSVs öffnet)."""
    return [
        "1. Je Reihe den Verlauf (oben Monatsmittel, unten Anzahl der Bewertungen je Monat) und die aufklappbare "
        "Monatstabelle ansehen. Die Monate heißen M001, M002 … und zählen die Kalendermonate ab dem ersten Monat "
        "der jeweiligen Reihe; Monate ohne Bewertung sind mitgezählt. Die Indizes verschiedener Reihen sind nicht "
        "vergleichbar.",
        "2. Zeiträume nach den Regeln markieren und in die Vorlage eintragen: company = Bezeichnung der Reihe wie "
        f"im Bogen (z. B. 'Reihe A'), source = '{source}', dimension = '{OVERALL_DIMENSION}', period_from und "
        "period_to = Index wie in der Monatstabelle (z. B. 'M015'), direction = 'rise' oder 'fall', note nach "
        "Regel 11.",
        "3. Jede Reihe für sich beurteilen, allein aus ihrem eigenen Verlauf. Nicht nach Ereignissen suchen und "
        "nicht versuchen, Unternehmen oder Kalenderdaten zu bestimmen; jede Beurteilung lautet 'Reihe allein'.",
        "4. Die Datei an den Autor zurückgeben. Er übersetzt sie mit dem Schlüssel in das Schema von "
        "annotations.json, prüft sie und meldet Fehler in der Schreibweise dieses Bogens (Reihe, Mxxx) zurück.",
    ]


def blind_protocol(protocol: Dict[str, Any], source: str = "employee") -> Dict[str, Any]:
    """Protokolltexte der blinden Fassung; reine Funktion. Die Regeln aus annotations.json
    bleiben in Reihenfolge und Nummer, ``BLIND_RULES`` ersetzt 7 (Ereignisanker entfällt), 8, 9
    und 11; Vorgehen und note-Beispiel sind eigene Fassungen. Verbleibende Kalendermonate im
    Text werden als „JJJJ-MM“ maskiert."""
    regeln: List[str] = []
    for rule in protocol.get("regeln") or []:
        text = str(rule)
        m = re.match(r"^(\d+)\s", text)
        if m and m.group(1) in BLIND_RULES:
            text = f"{m.group(1)} {BLIND_RULES[m.group(1)]}"
        regeln.append(mask_dates(text))
    return {
        "regeln": regeln,
        "vorgehen": blind_vorgehen(source),
        "note_beispiel": BLIND_NOTE_BEISPIEL,
        "quelle": mask_dates(str(protocol["quelle"])) if protocol.get("quelle") else None,
        "gefunden": bool(protocol.get("gefunden")),
    }


def blind_leaks(page: str, entries: List[Dict[str, Any]]) -> List[str]:
    """Funde, die die blinde Fassung verraten würden: Kalendermonate (19xx-/20xx-MM),
    Unternehmensnamen, Dateinamen und Slugs der Reihen (als ganzes Wort, ohne Beachtung der
    Groß-/Kleinschreibung). ``entries`` sind die Reihen vor dem Verblinden. Leer = nichts gefunden."""
    text = html.unescape(page)
    found: List[str] = []
    m = DATE_RE.search(text)
    if m:
        found.append(f"Kalendermonat '{m.group(0)}'")
    for e in entries:
        for word in sorted({str(e.get("name") or ""), str(e.get("file") or ""), str(e.get("slug") or "")}):
            if word and re.search(r"(?<!\w)" + re.escape(word) + r"(?!\w)", text, re.IGNORECASE):
                found.append(f"Name oder Datei '{word}'")
    return found


# ── Diagramm (SVG, ohne Skript und ohne externe Bibliothek) ─────────────────

CHART_LEFT, CHART_RIGHT = 56, 16
MEAN_HEIGHT, COUNT_HEIGHT, GAP = 170, 90, 28
TOP = 12
STEP_MIN, STEP_MAX = 5.0, 14.0


def _fmt(value: Optional[float], digits: int = 2) -> str:
    return "–" if value is None else f"{value:.{digits}f}".replace(".", ",")


def series_svg(series: List[Dict[str, Any]], min_reviews: int = MIN_REVIEWS_PER_MONTH,
               labels: Optional[List[str]] = None) -> str:
    """SVG mit Monatsmittel (oben) und Anzahl je Monat (unten). ``labels`` (blinde Fassung)
    ersetzt die Kalendermonate in Beschriftung und Tooltips; die Jahresmarken werden dann zu
    Marken alle zwölf Monate ab dem ersten Monat, beschriftet mit dem Index."""
    n = max(len(series), 1)
    names = labels if labels is not None else [m["period"] for m in series]
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
    if labels is None:
        first_january = next((i for i, m in enumerate(series) if m["period"].endswith("-01")), len(series))
        for i, m in enumerate(series):
            if m["period"].endswith("-01") or (i == 0 and first_january * step >= 30):
                x = CHART_LEFT + step * i
                parts.append(f'<line class="jahr" x1="{x:.1f}" y1="{mean_top}" x2="{x:.1f}" y2="{count_bottom}"/>')
                parts.append(f'<text class="achse" x="{x + 2:.1f}" y="{count_bottom + 16}">{m["period"][:4]}</text>')
    else:
        # Blinde Fassung: Marke alle zwölf Monate ab M001, ohne Bezug zum Kalenderjahr.
        for i in range(0, len(series), 12):
            x = CHART_LEFT + step * i
            parts.append(f'<line class="jahr" x1="{x:.1f}" y1="{mean_top}" x2="{x:.1f}" y2="{count_bottom}"/>')
            parts.append(f'<text class="achse" x="{x + 2:.1f}" y="{count_bottom + 16}">{html.escape(names[i])}</text>')
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
        title = f"{names[i]}: Mittel {_fmt(m['mean'])}, {m['count']} Bewertungen"
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
            f'<title>{names[i]}: {m["count"]} Bewertungen</title></rect>'
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
                min_reviews: int = MIN_REVIEWS_PER_MONTH, min_months: int = MIN_EVALUATED_MONTHS,
                blind: bool = False) -> str:
    """Eigenständiger Bogen: Umfang, Protokoll, Übersicht, ein Abschnitt je Reihe.

    ``blind``: ``entries`` stammen aus ``blind_entries`` (Bezeichnung, Monatsindizes) und
    ``protocol`` aus ``blind_protocol``; der Bogen nennt dann weder Erzeugungsdatum noch
    Namen, ids, Dateinamen oder Kalendermonate."""
    generated = generated or date.today()
    src_label = SOURCE_LABELS.get(source, source)
    h: List[str] = []
    h.append("<!DOCTYPE html><html lang=\"de\"><head><meta charset=\"utf-8\">")
    h.append(f"<title>Annotationsbogen Referenzzeiträume – {html.escape(src_label)}</title>")
    h.append(f"<style>{CSS}</style></head><body>")
    if blind:
        h.append("<h1>Annotationsbogen für die Referenzzeiträume (DZ1, E5) – blinde Fassung</h1>")
        h.append(
            "<p class=\"meta\">Erzeugt aus den Monatsreihen (Monatsmittel und Anzahl je Kalendermonat, E3). "
            f"Quelle: {html.escape(src_label)}; Dimension: {html.escape(DIMENSION_LABEL)}; "
            f"{len(entries)} Reihen" + (" (einschließlich nicht geeigneter Reihen)" if include_ineligible else
                                        f", nur nach E4 geeignete Reihen (mindestens {min_months} Monate mit "
                                        f"mindestens {min_reviews} Bewertungen)") + ".</p>"
        )
    else:
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
             f"<p><strong>Kurzfassung des Protokolls (E5):</strong> {html.escape(KURZFASSUNG_BLIND if blind else KURZFASSUNG_E5)}</p>")
    if blind:
        h.append("<p><strong>Blinde Fassung:</strong> Die Reihen heißen „Reihe A“, „Reihe B“ … in zufälliger Reihenfolge, "
                 "die Monate M001, M002 … (fortlaufende Kalendermonate ab dem ersten Monat der jeweiligen Reihe; Monate "
                 "ohne Bewertung sind mitgezählt, Lücken bleiben sichtbar). Unternehmen und Kalenderdaten sind bewusst "
                 "nicht genannt. Die senkrechten Linien im Diagramm stehen alle zwölf Monate ab M001.</p>")
    if protocol.get("regeln"):
        h.append("<p><strong>Regeln</strong>" + (f" ({html.escape(str(protocol.get('quelle')))})" if protocol.get("quelle") else "") + ":</p><ol>")
        for rule in protocol["regeln"]:
            text = re.sub(r"^\d+\s+", "", str(rule))
            h.append(f"<li>{html.escape(text)}</li>")
        h.append("</ol>")
    if protocol.get("note_beispiel"):
        h.append(f"<p><strong>Beispiel für die <code>note</code>:</strong> {html.escape(str(protocol['note_beispiel']))}</p>")
    if protocol.get("vorgehen"):
        h.append("<p><strong>Vorgehen (blinde Fassung):</strong></p><ul>" if blind else
                 "<p><strong>Vorgehen (annotations.json):</strong></p><ul>")
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
        flag = "" if e["eligible"] else " – nicht geeignet (E4)"
        if blind:
            labels = e["month_labels"]
            first = labels[0] if labels else "–"
            last = labels[-1] if labels else "–"
            h.append(f"<li><a href=\"#{e['anchor']}\">{html.escape(e['label'])}</a>: "
                     f"{e['evaluated_months']} bewertete Monate, {html.escape(first)} – {html.escape(last)}{flag}</li>")
            continue
        first = e["series"][0]["period"] if e["series"] else "–"
        last = e["series"][-1]["period"] if e["series"] else "–"
        h.append(f"<li><a href=\"#s-{e['company_id']}-{e['source']}\">{html.escape(e['name'])} ({e['company_id']})</a>: "
                 f"{e['evaluated_months']} bewertete Monate, {html.escape(first)} – {html.escape(last)}{flag}</li>")
    h.append("</ul></nav>")
    # Abschnitte
    for e in entries:
        s = e["series"]
        not_eligible = ("" if e["eligible"] else
                        f"; <strong>nicht geeignet nach E4</strong> (unter {min_months}), keine Einträge (Regel 9)")
        if blind:
            names = e["month_labels"]
            first = names[0] if names else "–"
            last = names[-1] if names else "–"
            h.append(f"<section id=\"{e['anchor']}\"><h2>{html.escape(e['label'])} – "
                     f"{html.escape(src_label)} – {html.escape(DIMENSION_LABEL)}</h2>")
            h.append(f"<p class=\"meta\">{len(s)} Kalendermonate {html.escape(first)} – {html.escape(last)} (fortlaufend ab "
                     f"dem ersten Monat der Reihe); {e['evaluated_months']} bewertete Monate" + not_eligible + ".</p>")
            h.append(series_svg(s, min_reviews, names))
        else:
            names = [m["period"] for m in s]
            first = s[0]["period"] if s else "–"
            last = s[-1]["period"] if s else "–"
            h.append(f"<section id=\"s-{e['company_id']}-{e['source']}\"><h2>{html.escape(e['name'])} ({e['company_id']}) – "
                     f"{html.escape(src_label)} – {html.escape(DIMENSION_LABEL)}</h2>")
            h.append(f"<p class=\"meta\">Datei <code>{html.escape(e['file'])}</code>; {len(s)} Kalendermonate {html.escape(first)} – "
                     f"{html.escape(last)}; {e['evaluated_months']} bewertete Monate" + not_eligible + ".</p>")
            h.append(series_svg(s, min_reviews))
        h.append("<details><summary>Monatstabelle (für die Angaben in der note)</summary><table><thead><tr>"
                 "<th>Monat</th><th>Mittel</th><th>Anzahl</th><th>Δ zum letzten Monat mit Wert</th><th>Status</th></tr></thead><tbody>")
        for i, m in enumerate(s):
            if m["mean"] is None:
                cls, status = "leer", "keine Bewertung"
            elif is_evaluated(m, min_reviews):
                cls, status = "bewertet", "bewertet"
            else:
                cls, status = "duenn", f"unter Mindestdichte ({min_reviews})"
            h.append(f"<tr class=\"{cls}\"><td>{html.escape(names[i])}</td><td>{_fmt(m['mean'], 3)}</td><td>{m['count']}</td>"
                     f"<td>{_fmt(m['delta'], 3)}</td><td>{status}</td></tr>")
        h.append("</tbody></table></details></section>")
    h.append("</body></html>")
    return "\n".join(h)


# ── CLI ──────────────────────────────────────────────────────────────────────

def _write_text(path: str, text: str) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


def build_sheet(series_dir: str = DEFAULT_SERIES_DIR, source: str = "employee", out: Optional[str] = None,
                density_path: str = DEFAULT_DENSITY, annotations_path: str = DEFAULT_ANNOTATIONS,
                include_ineligible: bool = False, companies: Optional[List[int]] = None, blind: bool = False,
                seed: Optional[int] = None, key_path: str = DEFAULT_KEY) -> Dict[str, Any]:
    """Bogen schreiben; liefert Pfad und Zahl der Reihen. ``companies`` begrenzt auf diese
    Unternehmens-ids. Mit ``blind`` entsteht die blinde Fassung (Standard
    ``data/annotationsbogen_blind.html``) und zusätzlich der Schlüssel unter ``key_path``."""
    if source not in VALID_SOURCES:
        raise ValueError(f"source '{source}' ungültig; erlaubt: {', '.join(VALID_SOURCES)}.")
    out = out or (DEFAULT_OUT_BLIND if blind else DEFAULT_OUT)
    entries = collect_series(series_dir, source, company_names(density_path), include_ineligible)
    if companies:
        entries = select_companies(entries, companies)
    protocol = protocol_texts(annotations_path)
    result: Dict[str, Any] = {"out": out, "n_series": len(entries), "companies": [e["name"] for e in entries]}
    if not blind:
        _write_text(out, render_html(entries, source, protocol, include_ineligible=include_ineligible))
        return result

    if os.path.abspath(key_path) == os.path.abspath(out):
        raise ValueError("Schlüssel und blinder Bogen dürfen nicht dieselbe Datei sein.")
    if seed is None:
        seed = random.SystemRandom().randrange(1, 10**9)
    blinded, reihen = blind_entries(entries, seed)
    page = render_html(blinded, source, blind_protocol(protocol, source), include_ineligible=include_ineligible, blind=True)
    leaks = blind_leaks(page, entries)
    if leaks:
        raise RuntimeError("Blinde Fassung nicht geschrieben; sie enthielte: " + "; ".join(leaks))
    key = {
        "zweck": ("Schlüssel zum blinden Annotationsbogen (DZ1, E5): Zuordnung Reihe -> Unternehmen und "
                  "Mxxx -> Kalendermonat. Nur für den Autor; nicht an die annotierende Person weitergeben und "
                  "nicht einchecken (.gitignore). Rückübersetzung: scripts/blind_annotations.py."),
        "erzeugt_am": date.today().isoformat(),
        "bogen": os.path.basename(out),
        "bogen_sha256": hashlib.sha256(page.encode("utf-8")).hexdigest(),
        "seed": seed,
        "source": source,
        "dimension": OVERALL_DIMENSION,
        "auswahl": {"companies": sorted(companies) if companies else None, "include_ineligible": include_ineligible},
        "reihen": reihen,
    }
    _write_text(key_path, json.dumps(key, ensure_ascii=False, indent=2) + "\n")
    _write_text(out, page)
    result.update({"key": key_path, "seed": seed})
    return result


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--series-dir", default=DEFAULT_SERIES_DIR, help="Ordner der Serien-CSVs (Default: data/series)")
    parser.add_argument("--source", default="employee", choices=list(VALID_SOURCES), help="Quelle (Default: employee)")
    parser.add_argument("--out", default=None, help="Zieldatei (Default: data/annotationsbogen.html, mit --blind "
                                                     "data/annotationsbogen_blind.html; nicht eingecheckt)")
    parser.add_argument("--density", default=DEFAULT_DENSITY, help="data_density.json für die Unternehmensnamen")
    parser.add_argument("--annotations", default=DEFAULT_ANNOTATIONS, help="annotations.json für die Protokolltexte (nur lesen)")
    parser.add_argument("--include-ineligible", action="store_true", help="auch Unternehmen unter der Mindestdichte (E4) aufnehmen")
    parser.add_argument("--companies", nargs="+", metavar="ID",
                        help="nur diese Unternehmens-ids (Teilmenge), z. B. --companies 19,24,28")
    parser.add_argument("--blind", action="store_true",
                        help="blinde Fassung für die zweite Person (Reihe A, B …, Monate M001 …; ohne Namen und "
                             "Kalenderdaten) und Schlüsseldatei schreiben")
    parser.add_argument("--seed", type=int, default=None,
                        help="Seed der zufälligen Reihenfolge (nur mit --blind; ohne Angabe gezogen und im Schlüssel vermerkt)")
    parser.add_argument("--key", default=DEFAULT_KEY,
                        help="Schlüsseldatei der blinden Fassung (Default: data/annotationsbogen_blind_schluessel.json, "
                             "nicht eingecheckt)")
    args = parser.parse_args(argv)
    if not os.path.isdir(args.series_dir):
        print(f"FEHLER: Serienordner fehlt: {args.series_dir}\nHinweis: zuerst 'uv run python scripts/make_annotation_basis.py' ausführen.")
        return 1
    if not args.blind and args.seed is not None:
        print("Hinweis: --seed wirkt nur mit --blind.")
    try:
        companies = parse_company_ids(args.companies)
        result = build_sheet(args.series_dir, args.source, args.out, args.density, args.annotations, args.include_ineligible,
                             companies=companies or None, blind=args.blind, seed=args.seed, key_path=args.key)
    except (ValueError, RuntimeError) as exc:
        print(f"FEHLER: {exc}")
        return 1
    if args.blind:
        print(f"Blinder Annotationsbogen geschrieben: {result['out']} ({result['n_series']} Reihen, Quelle {args.source}).")
        print(f"Schlüssel: {result['key']} (Seed {result['seed']}). Den Schlüssel nicht an die annotierende Person weitergeben.")
    else:
        print(f"Annotationsbogen geschrieben: {result['out']} ({result['n_series']} Reihen, Quelle {args.source}).")
    for name in result["companies"]:
        print(f"  - {name}")
    print("Die Datei ist nicht Teil des Repositorys (.gitignore)." if not args.blind else
          "Bogen und Schlüssel sind nicht Teil des Repositorys (.gitignore).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
