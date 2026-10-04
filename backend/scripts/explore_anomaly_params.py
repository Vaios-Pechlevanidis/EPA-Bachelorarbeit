"""
Parameterübersicht der Anomalieerkennung (Zyklus 2, Inkrement 1, Kontrollpunkt 1).

Zählt für jedes geeignete Unternehmen (E4) die erkannten auffälligen
Veränderungen der Mitarbeiterquelle, Gesamtbewertung, über ein Raster aus
Strafterm und ``min_delta``:

- skalierter Strafterm (Standard seit 2026-10-04, E9):
  ``penalty = penalty_factor · sigma² · ln(n)`` mit ``penalty_factor`` in
  {1, 2, 3, 4}; ``sigma`` = ``noise_sigma`` der bewerteten Monatsmittel, ``n`` =
  Zahl der bewerteten Monate,
- als Vergleichszeile der bisherige feste Strafterm 0,5,
- jeweils mit ``min_delta`` in {0,2; 0,3; 0,5}.

Die Startwerte (Faktor 2, min_delta 0,3) sind markiert. Zweck: Beleg, wie stark
die Zahl der markierten Veränderungen von den Parametern abhängt. Das Skript ist
**keine Kalibrierung** gegen Referenzzeiträume (DZ1); dafür fehlen die manuellen
Annotationen (E5).

Die Datenbank wird nur gelesen (SELECT über ``rating_series_service``).
Demo 1/2/3 sind ausgeschlossen (E2).

Ausgabe:
- CSV ``backend/data/calibration/anomaly_params_scaled_employee_durchschnittsbewertung.csv``
  mit je Unternehmen und Parameterpaar: Modus, Faktor, noise_sigma, verwendeter
  Strafterm, Anzahl fall, rise, davon deutlich, und die Monate. Die ältere CSV
  ``anomaly_params_employee_durchschnittsbewertung.csv`` (fester Strafterm,
  Stand 2026-10-03) bleibt als Beleg unverändert.
- kurze Tabelle auf der Konsole

Ausführen::

    cd backend
    uv run python scripts/explore_anomaly_params.py
    uv run python scripts/explore_anomaly_params.py --no-csv   # nur Konsole
"""

from __future__ import annotations

import argparse
import csv
import os
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND_DIR)
sys.path.insert(0, os.path.join(BACKEND_DIR, "scripts"))

from database.supabase_client import get_supabase_client  # noqa: E402
from models.changepoint_detector import DEFAULT_PENALTY, DEFAULT_PENALTY_FACTOR  # noqa: E402
from report_data_density import clean_company_name, is_demo_company  # noqa: E402
from services.anomaly_service import DEFAULT_MIN_DELTA, detect_anomalies, detection_params  # noqa: E402
from services.rating_series_service import (  # noqa: E402
    OVERALL_DIMENSION,
    evaluated_months,
    is_eligible,
    monthly_series,
)

SOURCE = "employee"
DIMENSION = OVERALL_DIMENSION
PENALTY_FACTORS = (1.0, 2.0, 3.0, 4.0)
FIXED_PENALTY = DEFAULT_PENALTY  # 0,5: bisheriger Standard, Vergleichszeile
MIN_DELTAS = (0.2, 0.3, 0.5)
# Einstellung: ("scaled", Faktor) oder ("fixed", Strafterm)
SETTINGS: Tuple[Tuple[str, float], ...] = tuple(("scaled", f) for f in PENALTY_FACTORS) + (("fixed", FIXED_PENALTY),)
DEFAULT_OUT = os.path.join(BACKEND_DIR, "data", "calibration", f"anomaly_params_scaled_{SOURCE}_{DIMENSION}.csv")
CSV_HEADER = [
    "company_id", "company", "evaluated_months", "penalty_mode", "penalty_factor", "noise_sigma",
    "penalty", "min_delta", "is_default", "n_fall", "n_rise", "n_high", "fall_months", "rise_months",
]


def is_default(mode: str, value: float, min_delta: float) -> bool:
    return mode == "scaled" and value == DEFAULT_PENALTY_FACTOR and min_delta == DEFAULT_MIN_DELTA


def _kwargs(mode: str, value: float) -> Dict[str, Any]:
    return {"penalty": value} if mode == "fixed" else {"penalty": None, "penalty_factor": value}


def fetch_companies() -> List[Dict[str, Any]]:
    res = get_supabase_client().table("companies").select("id,name").order("id").execute()
    return list(res.data or [])


def explore(verbose: bool = True) -> Dict[str, Any]:
    """Raster für alle geeigneten Nicht-Demo-Unternehmen; liefert Zeilen und Übersprungene."""
    rows: List[Dict[str, Any]] = []
    skipped: List[Dict[str, Any]] = []
    for company in fetch_companies():
        if is_demo_company(company["name"]):
            continue
        cid = int(company["id"])
        name = clean_company_name(company["name"])
        series = monthly_series(cid, SOURCE, DIMENSION)["series"]
        n_eval = evaluated_months(series)
        if not is_eligible(series):
            skipped.append({"company_id": cid, "company": name, "evaluated_months": n_eval})
            continue
        if verbose:
            print(f"  {name} ({n_eval} bewertete Monate)", file=sys.stderr)
        for mode, value in SETTINGS:
            for min_delta in MIN_DELTAS:
                kw = _kwargs(mode, value)
                params = detection_params(series, min_delta=min_delta, **kw)
                found = detect_anomalies(
                    series, company_id=cid, source=SOURCE, dimension=DIMENSION, min_delta=min_delta, **kw,
                )
                falls = sorted(a["date"] for a in found if a["direction"] == "fall")
                rises = sorted(a["date"] for a in found if a["direction"] == "rise")
                rows.append({
                    "company_id": cid,
                    "company": name,
                    "evaluated_months": n_eval,
                    "penalty_mode": mode,
                    "penalty_factor": value if mode == "scaled" else "",
                    "noise_sigma": round(params["noise_sigma"], 4),
                    "penalty": round(params["penalty"], 4),
                    "min_delta": min_delta,
                    "is_default": is_default(mode, value, min_delta),
                    "n_fall": len(falls),
                    "n_rise": len(rises),
                    "n_high": sum(1 for a in found if a["severity"] == "high"),
                    "fall_months": ";".join(falls),
                    "rise_months": ";".join(rises),
                    "_setting": (mode, value),
                })
    return {"rows": rows, "skipped": skipped}


def write_csv(rows: List[Dict[str, Any]], path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=CSV_HEADER, lineterminator="\n", extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({**row, "is_default": "ja" if row["is_default"] else ""})


def _label(mode: str, value: float, min_delta: float) -> str:
    mark = "*" if is_default(mode, value, min_delta) else ""
    head = f"f={value:g}" if mode == "scaled" else f"p={value:g}"
    return f"{head}/d={min_delta:g}{mark}"


def print_summary(rows: List[Dict[str, Any]], skipped: List[Dict[str, Any]]) -> None:
    grid = [(m, v, d) for m, v in SETTINGS for d in MIN_DELTAS]
    companies = sorted({(r["company"], r["evaluated_months"]) for r in rows}, key=lambda c: c[0].casefold())
    by_key = {(r["company"], *r["_setting"], r["min_delta"]): r for r in rows}

    print(f"\nParameterübersicht {SOURCE}/{DIMENSION}, Stand {datetime.now().isoformat(timespec='seconds')}")
    print("Zellen: Anzahl fall/rise; f = Faktor des skalierten Strafterms, p = fester Strafterm;")
    print("* = Startwerte (Faktor 2, min_delta 0,3)\n")
    name_w = max([len("Unternehmen")] + [len(c[0]) for c in companies])
    first = by_key
    header = f"{'Unternehmen':<{name_w}}  Mon.  sigma  pen(f=2) " + " ".join(f"{_label(m, v, d):>12}" for m, v, d in grid)
    print(header)
    print("-" * len(header))
    for name, n_eval in companies:
        ref = first[(name, "scaled", DEFAULT_PENALTY_FACTOR, DEFAULT_MIN_DELTA)]
        cells = [f"{by_key[(name, m, v, d)]['n_fall']}/{by_key[(name, m, v, d)]['n_rise']}".rjust(12) for m, v, d in grid]
        print(f"{name:<{name_w}}  {n_eval:>4}  {ref['noise_sigma']:.3f}  {ref['penalty']:>8.3f} " + " ".join(cells))
    totals = []
    for m, v, d in grid:
        f = sum(by_key[(n, m, v, d)]["n_fall"] for n, _ in companies)
        r = sum(by_key[(n, m, v, d)]["n_rise"] for n, _ in companies)
        totals.append(f"{f}/{r}".rjust(12))
    print("-" * len(header))
    print(f"{'Summe':<{name_w}}                        " + " ".join(totals))
    if skipped:
        print("\nNicht geeignet (< 12 bewertete Monate), ohne Erkennung: "
              + ", ".join(f"{s['company']} ({s['evaluated_months']})" for s in skipped))


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out", default=DEFAULT_OUT, help="Pfad der CSV (Standard: data/calibration/…)")
    parser.add_argument("--no-csv", action="store_true", help="nur Konsolentabelle, keine CSV schreiben")
    args = parser.parse_args(argv)

    print("Lese Monatsreihen (nur SELECT) …", file=sys.stderr)
    result = explore()
    print_summary(result["rows"], result["skipped"])
    if not args.no_csv:
        write_csv(result["rows"], args.out)
        print(f"\nCSV: {os.path.relpath(args.out, os.path.dirname(BACKEND_DIR))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
