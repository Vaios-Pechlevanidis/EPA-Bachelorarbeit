"""
Entscheidungsgrundlage für manuelle Annotationen (Prüfpunkt 5 des
Fundament-Checks, Inkrement 0).

Zweck
-----
1. Schreibt für jedes Nicht-Demo-Unternehmen und jede Quelle ("employee",
   "candidates") eine Monatsserie der Durchschnittsbewertung nach
   ``backend/data/series/<company_id>_<slug>_<source>.csv`` mit den Spalten

       period;mean_durchschnittsbewertung;count;delta_vs_previous

   - period                      Kalendermonat YYYY-MM; es werden ALLE
                                 Kalendermonate zwischen erster und letzter
                                 datierter Bewertung ausgegeben (count 0 erlaubt)
   - mean_durchschnittsbewertung Mittelwert von ``durchschnittsbewertung`` über
                                 die datierten Bewertungen des Monats (3 Nach-
                                 kommastellen, Dezimalpunkt); leer bei count 0
                                 oder wenn kein Wert vorliegt
   - count                       Anzahl datierter Bewertungen im Monat
   - delta_vs_previous           Differenz des Mittelwerts zum letzten
                                 vorhergehenden Monat MIT Wert (nicht zwingend
                                 der direkte Vormonat, da viele Monate leer
                                 sind); leer, wenn kein Vorwert existiert

   Zeilen ohne Datum werden ignoriert. Quellen ohne Bewertungen erhalten eine
   CSV, die nur die Kopfzeile enthält.

   Diese CSVs sind die menschliche Entscheidungsgrundlage für die
   Referenzannotationen; sie enthalten bewusst keine automatische Erkennung.

2. Legt ``backend/data/annotations.json`` an, falls die Datei noch NICHT
   existiert. Eine vorhandene Datei wird nie überschrieben. Die Datei wird
   mit leerer Annotationsliste und deutschen Hinweisen angelegt; sie wird
   niemals vorbefüllt.

Das Skript ist strikt lesend gegenüber der Datenbank (nur SELECT).

Verwendung
----------
    cd backend
    uv run python scripts/make_annotation_basis.py
    uv run python scripts/make_annotation_basis.py --series-dir data/series --annotations data/annotations.json
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
import unicodedata
from typing import Any, Dict, List, Optional, Tuple

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND_DIR)

from database.supabase_client import get_supabase_client  # noqa: E402
from services.rating_series_service import OVERALL_DIMENSION, build_monthly_series  # noqa: E402
from services.topic_average_rating_service import (  # noqa: E402
    CANDIDATES_TOPIC_COLUMNS,
    EMPLOYEE_TOPIC_COLUMNS,
    _fetch_all_rows,
)

SOURCES: Tuple[str, str] = ("employee", "candidates")
DEFAULT_SERIES_DIR = os.path.join(BACKEND_DIR, "data", "series")
DEFAULT_ANNOTATIONS = os.path.join(BACKEND_DIR, "data", "annotations.json")
CSV_HEADER = ["period", "mean_durchschnittsbewertung", "count", "delta_vs_previous"]

_DEMO_RE = re.compile(r"^demo\s*\d+$")


# ── Namens-Helfer (identisch zu report_data_density.py) ──────────────────────

def clean_company_name(raw: str) -> str:
    """Bereinigt Whitespace-Defekte der DB-Namen, behält Gross-/Kleinschreibung."""
    return " ".join(str(raw).split())


def normalize_company_name(raw: str) -> str:
    """Schlüssel für den Namensvergleich: bereinigt + casefold."""
    return clean_company_name(raw).casefold()


def is_demo_company(raw: str) -> bool:
    return _DEMO_RE.match(normalize_company_name(raw)) is not None


def slugify(name: str) -> str:
    """ASCII-Slug für Dateinamen (Umlaute transliteriert, Rest -> '_')."""
    s = clean_company_name(name).casefold()
    for src, dst in (("ä", "ae"), ("ö", "oe"), ("ü", "ue"), ("ß", "ss")):
        s = s.replace(src, dst)
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")
    s = re.sub(r"[^a-z0-9]+", "_", s).strip("_")
    return s or "unbenannt"


# ── Serienbildung ────────────────────────────────────────────────────────────

def build_series(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Monatsserie (alle Kalendermonate im Zeitraum) aus Rohzeilen mit datum und
    durchschnittsbewertung. Mittel und Anzahl kommen aus
    services/rating_series_service.build_monthly_series, also aus derselben
    Reihenbildung, die die Anomalieerkennung verwendet (E3). Ergänzt wird nur die
    Differenz zum letzten Monat mit Wert. Reine Funktion, ohne DB-Zugriff."""
    series: List[Dict[str, Any]] = []
    prev_mean: Optional[float] = None
    for month in build_monthly_series(rows, OVERALL_DIMENSION):
        mean = month["mean"]
        delta = round(mean - prev_mean, 3) if (mean is not None and prev_mean is not None) else None
        series.append({
            "period": month["period"],
            "mean_durchschnittsbewertung": mean,
            "count": month["count"],
            "delta_vs_previous": delta,
        })
        if mean is not None:
            prev_mean = mean
    return series


def write_series_csv(path: str, series: List[Dict[str, Any]]) -> None:
    def fmt(v: Any) -> str:
        return "" if v is None else (f"{v:.3f}" if isinstance(v, float) else str(v))

    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, delimiter=";", lineterminator="\n")
        w.writerow(CSV_HEADER)
        for item in series:
            w.writerow([fmt(item[k]) for k in CSV_HEADER])


# ── annotations.json ─────────────────────────────────────────────────────────

def annotations_template() -> Dict[str, Any]:
    """Leere Annotationsdatei mit deutschen Hinweisen. Wird NIE vorbefüllt."""
    return {
        "version": 1,
        "hinweise": {
            "zweck": (
                "Manuell erstellte Referenzannotationen (Gold-Standard) extremer Veränderungen in "
                "Kununu-Bewertungsverläufen. Sie dienen in Zyklus 2 der Evaluation der automatischen "
                "Erkennung und Erklärung extremer Veränderungen."
            ),
            "wichtig": (
                "Die Einträge werden MANUELL aus den Serien-CSVs in backend/data/series/ erstellt, und "
                "zwar BEVOR Erkennungscode existiert oder ausgeführt wird. Ergebnisse einer automatischen "
                "Erkennung dürfen weder als Vorlage noch zur Korrektur der Annotationen verwendet werden; "
                "sonst würde die spätere Validierung zirkulär (die Erkennung würde gegen sich selbst "
                "geprüft). Dieses Skript befüllt die Liste 'annotations' bewusst nicht."
            ),
            "vorgehen": [
                "1. Je Unternehmen und Quelle die CSV backend/data/series/<id>_<slug>_<source>.csv öffnen "
                "(Trennzeichen ';', Dezimalpunkt '.').",
                "2. Spalten: period (Kalendermonat), mean_durchschnittsbewertung (Monatsmittel), count "
                "(Anzahl Bewertungen), delta_vs_previous (Differenz zum letzten vorhergehenden Monat mit "
                "Wert, nicht zwingend der direkte Vormonat).",
                "3. Zeiträume markieren, in denen die Bewertung nach eigener fachlicher Einschätzung extrem "
                "steigt (rise) oder fällt (fall). Monate mit sehr kleinem count sind mit Vorsicht zu "
                "beurteilen; die Dichte je Unternehmen steht in docs/datenbasis.md.",
                "4. Für Themen-Dimensionen (z. B. 'kommunikation') gibt es keine eigene CSV; sie werden nur "
                "annotiert, wenn eine Begründung unabhängig von Erkennungscode möglich ist.",
                "5. Jeden Eintrag mit einer kurzen deutschen Begründung versehen (Feld 'note').",
                "6. Danach prüfen: cd backend && uv run python scripts/validate_annotations.py "
                "[--offline] [--require-all-companies].",
            ],
            "felder": {
                "company": "Bereinigter Unternehmensname, wie in backend/data/data_density.json unter 'name' "
                           "(z. B. 'E.ON', 'Thyssengas GmbH'). Der Abgleich erfolgt whitespace-normalisiert "
                           "und ohne Beachtung der Gross-/Kleinschreibung. Demo 1/2/3 sind nicht erlaubt.",
                "source": "'employee' (Mitarbeitende) oder 'candidates' (Bewerbende).",
                "dimension": "'durchschnittsbewertung' oder ein Themen-Schlüssel der jeweiligen Quelle "
                             "(siehe 'gueltige_dimensionen').",
                "period_from": "Erster Monat der Veränderung im Format YYYY-MM.",
                "period_to": "Letzter Monat der Veränderung im Format YYYY-MM; period_from <= period_to. "
                             "Beide Monate müssen im Datenzeitraum des Unternehmens für diese Quelle liegen.",
                "direction": "'rise' (Anstieg) oder 'fall' (Abfall).",
                "note": "Nicht-leere deutsche Begründung, unabhängig von jeder automatischen Erkennung "
                        "(z. B. beobachteter Sprung des Monatsmittels, Anzahl Bewertungen, Kontext).",
            },
            "gueltige_dimensionen": {
                "employee": ["durchschnittsbewertung"] + list(EMPLOYEE_TOPIC_COLUMNS.keys()),
                "candidates": ["durchschnittsbewertung"] + list(CANDIDATES_TOPIC_COLUMNS.keys()),
            },
            "regeln": [
                "Jeder Eintrag enthält genau die Felder company, source, dimension, period_from, period_to, "
                "direction, note.",
                "Keine Duplikate (gleiche company, source, dimension, period_from, period_to).",
                "Ein Unternehmen darf mehrere Einträge haben; Einträge dürfen sich nicht überschneiden, wenn "
                "sie dieselbe Dimension derselben Quelle betreffen.",
                "Entfällt eine Veränderung für ein Unternehmen, bleibt es ohne Eintrag; das ist zulässig und "
                "wird vom Validator nur mit --require-all-companies beanstandet.",
            ],
            "beispiel_format": {
                "company": "<Name aus data_density.json>",
                "source": "employee",
                "dimension": "durchschnittsbewertung",
                "period_from": "YYYY-MM",
                "period_to": "YYYY-MM",
                "direction": "rise|fall",
                "note": "<deutsche Begründung>",
            },
        },
        "annotations": [],
    }


# ── Hauptprogramm ────────────────────────────────────────────────────────────

def fetch_companies(supabase) -> List[Dict[str, Any]]:
    res = supabase.table("companies").select("id,name").order("id").execute()
    return list(res.data or [])


def fetch_rows(supabase, source: str, company_id: int) -> List[Dict[str, Any]]:
    q = (
        supabase.table(source)
        .select("id,datum,durchschnittsbewertung")
        .eq("company_id", company_id)
        .order("id")  # stabile Reihenfolge für die range()-Paginierung
    )
    return _fetch_all_rows(q, page_size=1000)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--series-dir", default=DEFAULT_SERIES_DIR, help=f"Zielordner der CSVs (Default: {DEFAULT_SERIES_DIR})")
    parser.add_argument("--annotations", default=DEFAULT_ANNOTATIONS, help=f"Pfad der Annotationsdatei (Default: {DEFAULT_ANNOTATIONS})")
    args = parser.parse_args(argv)

    supabase = get_supabase_client()
    os.makedirs(args.series_dir, exist_ok=True)

    companies = [c for c in fetch_companies(supabase) if not is_demo_company(c["name"])]
    print(f"Schreibe Monatsserien für {len(companies)} Unternehmen nach {args.series_dir} (nur SELECT) ...")
    written = 0
    for c in companies:
        cid = int(c["id"])
        slug = slugify(c["name"])
        for source in SOURCES:
            rows = fetch_rows(supabase, source, cid)
            series = build_series(rows)
            path = os.path.join(args.series_dir, f"{cid}_{slug}_{source}.csv")
            write_series_csv(path, series)
            written += 1
            with_vals = sum(1 for s in series if s["mean_durchschnittsbewertung"] is not None)
            print(f"  {os.path.basename(path):<60} Monate={len(series):>3} davon mit Wert={with_vals:>3}")
    print(f"{written} CSV-Dateien geschrieben.")

    if os.path.exists(args.annotations):
        print(f"annotations.json existiert bereits und wird nicht angetastet: {args.annotations}")
    else:
        os.makedirs(os.path.dirname(os.path.abspath(args.annotations)), exist_ok=True)
        with open(args.annotations, "w", encoding="utf-8") as fh:
            json.dump(annotations_template(), fh, ensure_ascii=False, indent=2)
            fh.write("\n")
        print(f"Leere Annotationsdatei angelegt: {args.annotations}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
