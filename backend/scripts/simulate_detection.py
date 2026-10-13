"""
Semi-synthetische Prüfung der Erkennung (DZ1, E30): Niveauwechsel bekannter
Größe in echte Reihen ohne zeitliche Struktur einsetzen und messen, wie oft die
Erkennung sie findet und wie oft sie ohne Wechsel anschlägt.

Zweck
-----
Die Referenzzeiträume (E5) sind regelbasiert und agentengestützt; ihr F1-Wert
misst die Übereinstimmung zweier Regeln. Diese Simulation ergänzt DZ1 um eine
Messung mit bekannter Wahrheit. Sie **kalibriert nichts**: Erkennung (E9, E14)
und Referenz bleiben unverändert, und ihre Ergebnisse sind kein Anlass, Parameter
mit denselben Reihen nachzustellen (E5, E30).

Rauschbedingungen (Klammer, beide werden berichtet)
---------------------------------------------------
- ``bewertungen``: Die Gesamtnoten aller datierten Bewertungen des Unternehmens
  werden zufällig auf dieselben Bewertungen verteilt. Jeder Monat behält seine
  Zahl an Bewertungen, jede Note bleibt im Bestand. Das Rauschen ist danach
  unabhängig je Bewertung: Streuung zwischen Monaten über das Stichprobenrauschen
  hinaus (Häufungen, Monatseffekte), Trends und Autokorrelation fehlen. Die
  Trefferquote ist hier eher **optimistisch**.
- ``monate``: Die bewerteten Monate der echten Reihe tauschen als Ganzes ihre
  Plätze (Monatsmittel samt Zahl der Bewertungen); welche Kalendermonate bewertet
  sind, bleibt gleich. Monatseffekte und ungleiche Belegung bleiben, echte
  Niveauunterschiede werden zu zusätzlichem Rauschen. Die Trefferquote ist hier
  eher **pessimistisch**.

Ablauf je geeigneter Reihe (Mitarbeitende, Gesamtbewertung, E4) und Wiederholung
---------------------------------------------------------------------------------
1. Rauschreihe je Bedingung bilden (oben).
2. **Wechselstelle** ``k`` (ein bewerteter Monat) und Richtung (Anstieg/Abfall,
   je Wiederholung mit Wahrscheinlichkeit 1/2) ziehen:
   - ``mitte``: ``k`` gleichverteilt mit mindestens ``MARGIN`` bewerteten Monaten
     davor und ab ``k``;
   - ``ende`` (nur Bedingung ``bewertungen``): jüngster Wechsel, ab ``k`` liegen
     nur ``END_AFTER`` (3 bis 5) bewertete Monate.
3. **Einsetzen:** Für jede Größe ``delta`` in ``DELTAS`` wird ``±delta`` auf jedes
   Monatsmittel ab ``k`` addiert, ohne Kappung an 1 bzw. 5 Sternen. Nahe der
   Obergrenze sind große Anstiege deshalb nur nominal; der Bericht nennt den
   Anteil der Wiederholungen mit einem Monatsmittel außerhalb von [1, 5] und die
   Trefferquote getrennt nach Richtung. ``delta = 0`` ist die Nullbedingung:
   dieselbe Reihe ohne Wechsel. Alle Größen einer Wiederholung nutzen dieselbe
   Rauschreihe, Stelle und Richtung (gepaarter Vergleich).
4. **Erkennung:** ``anomaly_service.detect_anomalies`` und
   ``detect_outlier_months`` mit den Standardparametern, also genau wie Dashboard
   und DZ1-Lauf.
5. **Abgleich nach Regel 6** mit ``evaluate_detection.match_series`` (Toleranz
   ±1 Monat, Kappung bei Lücken bis 3 Monate, gleiche Richtung, Eins-zu-eins);
   der eingesetzte Wechsel ist ein Referenzzeitraum ``[k, k]``. Gewertet werden
   die Niveauwechsel (Hauptwert in E5); Einzelmonate werden getrennt gezählt.

Kennzahlen je Bedingung, Lage und Größe
---------------------------------------
- ``recall``: Anteil der Wiederholungen, in denen der Wechsel getroffen wird,
  mit Bootstrap-Intervall über die Reihen (jede Reihe zählt gleich, unabhängig
  von ihrer Länge), Spanne der Werte je Reihe und Wilson-Intervall (nur
  Monte-Carlo-Fehler). Bei ``delta = 0`` ist das die Zufallstrefferquote.
- ``recall_tol3`` / ``recall_tol6``: Anteil mit einer gleichgerichteten Markierung
  höchstens 3 bzw. 6 Kalendermonate vom Wechsel entfernt (Verortungsprofil).
- ``detections_mean`` / ``p_any_detection``: Markierungen je Wiederholung und
  Anteil der Wiederholungen mit mindestens einer. Bei ``delta = 0`` sind alle
  Markierungen Fehlalarme bei zeitlich austauschbarem Rauschen; nach E9
  (Nachtrag 2026-10-11) liegt die Rate in echten Reihen vermutlich höher.
- ``extras_mean``, ``extras_near_mean``: zusätzliche Markierungen je Wiederholung,
  davon gleichgerichtet höchstens 6 Monate vom Wechsel (meist der falsch
  verortete Wechsel selbst).
- ``delta_bias_median`` (Quartile): gemeldetes minus eingesetztes Delta bei
  Treffern. Bedingt auf Treffer und wegen ``min_delta`` nahe 0,3 nach oben
  verzerrt; kein Maß für eine Überschätzung durch die Erkennung.
- ``share_high``: Anteil der Treffer mit Schweregrad ``high`` (ab 0,5 Sternen);
  bei ``delta`` unter 0,5 eine Fehleinstufungsquote.
- ``outliers_mean``: auffällige Einzelmonate (E14) je Wiederholung.
- ``precision`` / ``f1`` stehen nur in der JSON-Datei: Mit genau einem Wechsel je
  Reihe hängen sie vom Entwurf ab und sind mit DZ1 nicht vergleichbar.
- Schichten (Größe > 0): Richtung, Bewertungen im Wechselmonat (< / ≥ ``THIN_N``),
  Bewertungen der 3 bewerteten Monate vor und ab ``k`` (kleinere Summe < / ≥
  ``3 · THIN_N``), Lücke vor ``k``, Verhältnis ``delta / sigma`` (``sigma`` =
  ``noise_sigma`` der simulierten Reihe).

Je Reihe zum Vergleich: beobachtete Markierungen auf der echten Reihe,
``noise_sigma`` echt und simuliert, Fehlalarme je 100 bewertete Monate.

Reproduzierbarkeit
------------------
Jede Wiederholung zieht ihren Zufall aus ``SeedSequence([seed, company_id, rep])``
in fester Reihenfolge; das Ergebnis hängt nicht von der Reihenfolge der Aufgaben,
der Zahl der Prozesse oder der Reihenfolge der gelesenen Zeilen ab (sie werden
nach id geordnet). Die Datei nennt Commit, ob der Arbeitsbaum unter ``backend/``
uncommittete Änderungen hat, einen SHA-256 des Skripts, Aufruf, Laufzeit,
Versionen von Python, NumPy und ruptures sowie je Reihe einen SHA-256 über die
gelesenen Bewertungen (id, Datum, Note). Mit ``--json`` bricht das Skript bei
uncommitteten Änderungen ab, außer mit ``--allow-dirty``. ``--records`` schreibt
die Datensätze je Wiederholung (ohne Noten, ohne ids). Die Datenbank wird nur
gelesen (``rating_series_service.fetch_review_rows``); die Serien-CSVs reichen
nicht, weil die Permutation die einzelnen Noten braucht. Demo 1–3 sind
ausgeschlossen (E2).

Verwendung::

    cd backend
    uv run python scripts/simulate_detection.py --reps 20 --workers 4          # Probelauf
    uv run python scripts/simulate_detection.py --workers 6 \\
        --json data/calibration/semisynthetisch_YYYY-MM-DD.json \\
        --records data/calibration/semisynthetisch_YYYY-MM-DD_records.json.gz
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
import os
import platform
import subprocess
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime, timezone
from statistics import median, pstdev
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

import numpy as np

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND_DIR)
sys.path.insert(0, os.path.join(BACKEND_DIR, "scripts"))

import evaluate_detection as ed  # noqa: E402
import validate_annotations as va  # noqa: E402
from models.changepoint_detector import DEFAULT_MIN_SIZE, PeltDetector, noise_sigma  # noqa: E402
from services.anomaly_service import (  # noqa: E402
    SEVERITY_HIGH,
    detect_anomalies,
    detect_outlier_months,
    detection_params,
)
from services.rating_series_service import (  # noqa: E402
    OVERALL_DIMENSION,
    build_monthly_series,
    is_eligible,
    month_key,
)

SOURCE = "employee"
DIMENSION = OVERALL_DIMENSION
COLUMN = OVERALL_DIMENSION
DELTAS: Tuple[float, ...] = (0.0, 0.3, 0.5, 0.75, 1.0)   # Sterne; 0 = ohne Wechsel (Nullbedingung)
REPS = 200                 # Wiederholungen je Reihe
SEED = 20261013
MARGIN = 6                 # Lage "mitte": bewertete Monate vor und ab dem Wechsel (2 · min_size)
END_AFTER = (3, 5)         # Lage "ende": bewertete Monate ab dem Wechsel (min_size bis 5)
NEAR_MONTHS = 6            # "nah": gleichgerichtete Markierung höchstens so weit vom Wechsel
NEIGHBOURS = 3             # bewertete Monate je Seite für die Belegung um den Wechsel
THIN_N = 10                # Wechselmonat "dünn", wenn weniger Bewertungen (Schwelle aus E12)
SNR_EDGES = (1.0, 1.5, 2.0)  # Klassen von delta / sigma
BOOTSTRAP = 2000           # Ziehungen des Bootstrap über die Reihen
CONDITIONS = ("bewertungen", "monate")
DESIGN: Tuple[Tuple[str, str], ...] = (("bewertungen", "mitte"), ("bewertungen", "ende"), ("monate", "mitte"))
DEFAULT_DENSITY = os.path.join(BACKEND_DIR, "data", "data_density.json")

Row = Dict[str, Any]


# ── Bausteine (rein) ─────────────────────────────────────────────────────────

def _numeric(value: Any) -> Optional[float]:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _row_key(row: Row) -> Tuple[Any, ...]:
    """Feste Ordnung der Zeilen: ganzzahlige ids aufsteigend, sonst als Text, dann Datum."""
    rid = row.get("id")
    id_key = (0, rid, "") if isinstance(rid, int) and not isinstance(rid, bool) else (1, 0, str(rid))
    return id_key + (str(row.get("datum")),)


def permute_values(rows: Sequence[Row], column: str, rng: np.random.Generator) -> List[Row]:
    """Kopie der Zeilen, in der die Werte von ``column`` zufällig auf alle Zeilen mit
    Monat und Zahlenwert verteilt sind. Zeilen ohne Datum oder Wert bleiben
    unverändert; damit bleiben ``count`` und ``n_values`` je Monat exakt erhalten.
    Die Zuordnung folgt der festen Ordnung ``_row_key``, nicht der Eingabereihenfolge."""
    out = [dict(r) for r in rows]
    idx = [i for i, r in enumerate(out) if month_key(r.get("datum")) and _numeric(r.get(column)) is not None]
    idx.sort(key=lambda i: _row_key(out[i]))
    values = [out[i][column] for i in idx]
    order = rng.permutation(len(values))
    for target, src in zip(idx, order):
        out[target][column] = values[src]
    return out


def evaluated_of(series: Sequence[Row]) -> List[Row]:
    return [m for m in series if m.get("evaluated") and m.get("mean") is not None]


def permute_months(series: Sequence[Row], rng: np.random.Generator) -> List[Row]:
    """Kopie der Reihe, in der die bewerteten Monate (Mittel, Anzahl) zufällig ihre
    Plätze tauschen; welche Kalendermonate bewertet sind, bleibt gleich."""
    out = [dict(m) for m in series]
    slots = [i for i, m in enumerate(out) if m.get("evaluated") and m.get("mean") is not None]
    payload = [(out[i]["mean"], out[i].get("count"), out[i].get("n_values")) for i in slots]
    order = rng.permutation(len(slots))
    for target, src in zip(slots, order):
        out[target]["mean"], out[target]["count"], out[target]["n_values"] = payload[src]
    return out


def choose_change_index(n_evaluated: int, margin: int, rng: np.random.Generator) -> int:
    """Lage "mitte": Index eines bewerteten Monats mit ``margin`` bewerteten Monaten davor und ab ihm."""
    lo, hi = margin, n_evaluated - margin
    if margin < 1 or hi < lo:
        raise ValueError(f"Reihe zu kurz oder Rand ungültig: {n_evaluated} bewertete Monate, Rand {margin}.")
    return int(rng.integers(lo, hi + 1))


def choose_end_index(n_evaluated: int, margin: int, rng: np.random.Generator,
                     after: Tuple[int, int] = END_AFTER) -> int:
    """Lage "ende": ab dem Wechsel liegen nur ``after[0]`` bis ``after[1]`` bewertete
    Monate, davor mindestens ``margin``."""
    lo, hi = max(margin, n_evaluated - after[1]), n_evaluated - after[0]
    if after[0] < 1 or hi < lo:
        raise ValueError(f"Reihe zu kurz für die Lage 'ende': {n_evaluated} bewertete Monate.")
    return int(rng.integers(lo, hi + 1))


def inject_shift(series: Sequence[Row], change_period: str, delta: float) -> List[Row]:
    """Kopie der Reihe, in der jedes Monatsmittel ab ``change_period`` um ``delta`` verschoben ist."""
    out = []
    for m in series:
        m2 = dict(m)
        if delta and m2.get("mean") is not None and m2["period"] >= change_period:
            m2["mean"] = round(float(m2["mean"]) + delta, 3)
        out.append(m2)
    return out


def months_between(a: str, b: str) -> int:
    """Kalendermonate von ``a`` nach ``b`` (positiv, wenn ``b`` später liegt)."""
    return (int(b[:4]) * 12 + int(b[5:7])) - (int(a[:4]) * 12 + int(a[5:7]))


def neighbour_reviews(evaluated: Sequence[Row], k: int, width: int = NEIGHBOURS) -> int:
    """Kleinere der beiden Summen von ``n_values`` über ``width`` bewertete Monate vor bzw. ab ``k``."""
    before = sum(int(m.get("n_values", 0)) for m in evaluated[max(0, k - width):k])
    after = sum(int(m.get("n_values", 0)) for m in evaluated[k:k + width])
    return min(before, after)


def detect(series: Sequence[Row], company_id: int) -> Dict[str, Any]:
    """Erkennung mit Standardparametern wie im Dashboard."""
    found = detect_anomalies(list(series), company_id=company_id, source=SOURCE, dimension=DIMENSION)
    outliers = detect_outlier_months(list(series), company_id=company_id, source=SOURCE, dimension=DIMENSION)
    evaluated = evaluated_of(series)
    return {
        "found": found,
        "n_outliers": len(outliers),
        "evaluated": {m["period"] for m in evaluated},
        "sigma": noise_sigma([float(m["mean"]) for m in evaluated]),
    }


def match_change(detection: Dict[str, Any], change_period: str, direction: str) -> Dict[str, Any]:
    """Abgleich nach Regel 6 für einen eingesetzten Wechsel [k, k], dazu Verortung."""
    found = detection["found"]
    dets = ed.detections_from_result({"anomalies": found}, with_outliers=False)
    truth = {"company": "simulation", "source": SOURCE, "dimension": DIMENSION,
             "period_from": change_period, "period_to": change_period, "direction": direction}
    match = ed.match_series([truth], dets, detection["evaluated"])
    hit = match["tp"] == 1
    det = match["hits"][0]["detection"] if hit else None
    same = [abs(months_between(change_period, a["date"])) for a in found if a["direction"] == direction]
    near = [e for e in match["extras"]
            if e["direction"] == direction and abs(months_between(change_period, e["date"])) <= NEAR_MONTHS]
    return {
        "hit": hit,
        "extras": match["fp"],
        "extras_near": len(near),
        "n_detections": len(found),
        "nearest_same_dir": min(same) if same else None,
        "loc_error": months_between(change_period, det["date"]) if det else None,
        "detected_delta": float(det["delta"]) if det else None,
        "detected_high": (det.get("severity") == "high") if det else None,
    }


def run_company_rep(rows: Sequence[Row], company_id: int, rep: int, deltas: Sequence[float],
                    seed: int = SEED, margin: int = MARGIN) -> List[Dict[str, Any]]:
    """Eine Wiederholung einer Reihe: beide Rauschbedingungen, alle Lagen und Größen.

    Reihenfolge der Ziehungen (fest): Permutation der Noten, Stelle und Richtung
    "mitte", Stelle und Richtung "ende", Permutation der Monate, Stelle und Richtung
    "mitte" der Monatsbedingung."""
    rng = np.random.default_rng(np.random.SeedSequence([int(seed), int(company_id), int(rep)]))
    noisy: Dict[str, List[Row]] = {}
    noisy["bewertungen"] = build_monthly_series(permute_values(rows, COLUMN, rng), COLUMN)
    n_b = len(evaluated_of(noisy["bewertungen"]))
    draws = {("bewertungen", "mitte"): (choose_change_index(n_b, margin, rng), 1 if rng.random() < 0.5 else -1)}
    draws[("bewertungen", "ende")] = (choose_end_index(n_b, margin, rng), 1 if rng.random() < 0.5 else -1)
    noisy["monate"] = permute_months(build_monthly_series(list(rows), COLUMN), rng)
    n_m = len(evaluated_of(noisy["monate"]))
    draws[("monate", "mitte")] = (choose_change_index(n_m, margin, rng), 1 if rng.random() < 0.5 else -1)

    null_detection = {c: detect(noisy[c], company_id) for c in CONDITIONS}
    out: List[Dict[str, Any]] = []
    for condition, placement in DESIGN:
        series = noisy[condition]
        evaluated = evaluated_of(series)
        k, sign = draws[(condition, placement)]
        change_period = evaluated[k]["period"]
        direction = "rise" if sign > 0 else "fall"
        base = {
            "company_id": int(company_id), "rep": int(rep), "condition": condition, "placement": placement,
            "change_period": change_period, "direction": direction,
            "n_at_change": int(evaluated[k].get("n_values", evaluated[k].get("count", 0))),
            "n_neighbours": neighbour_reviews(evaluated, k),
            "gap_before": months_between(evaluated[k - 1]["period"], change_period) - 1,
        }
        for delta in deltas:
            if delta:
                shifted = inject_shift(series, change_period, sign * float(delta))
                detection = detect(shifted, company_id)
            else:
                shifted, detection = series, null_detection[condition]
            rec = {**base, "delta": float(delta), **match_change(detection, change_period, direction),
                   "n_outliers": detection["n_outliers"], "sigma_sim": round(detection["sigma"], 4),
                   "out_of_range": any(not 1.0 <= float(m["mean"]) <= 5.0 for m in evaluated_of(shifted))}
            out.append(rec)
    return out


# ── Auswertung (rein) ────────────────────────────────────────────────────────

def _mean(values: Sequence[float]) -> Optional[float]:
    return round(float(np.mean(values)), 4) if len(values) else None


def wilson(hits: int, n: int, z: float = 1.959964) -> Optional[List[float]]:
    """Wilson-Intervall eines Anteils (95 %); None ohne Fälle."""
    if n <= 0:
        return None
    p = hits / n
    centre = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return [round(max(0.0, centre - half), 4), round(min(1.0, centre + half), 4)]


def bootstrap_series(values: Dict[int, float], seed: int = SEED, draws: int = BOOTSTRAP) -> Optional[List[float]]:
    """95-%-Perzentilintervall des Mittels über Reihen, Reihen mit Zurücklegen gezogen."""
    if not values:
        return None
    vals = np.array([values[c] for c in sorted(values)], dtype=float)
    rng = np.random.default_rng(np.random.SeedSequence([int(seed), 7]))
    means = vals[rng.integers(0, len(vals), size=(draws, len(vals)))].mean(axis=1)
    return [round(float(np.percentile(means, 2.5)), 4), round(float(np.percentile(means, 97.5)), 4)]


def summarize(records: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    """Kennzahlen einer Menge von Wiederholungen derselben Bedingung, Lage und Größe."""
    n = len(records)
    hits = [r for r in records if r["hit"]]
    tp, fp = len(hits), sum(r["extras"] for r in records)
    m = ed.metrics(tp, fp, n - tp)
    bias = [abs(r["detected_delta"]) - r["delta"] for r in hits if r["delta"] > 0]
    within = lambda limit: [1.0 if r["nearest_same_dir"] is not None and r["nearest_same_dir"] <= limit else 0.0  # noqa: E731
                            for r in records]
    return {
        "reps": n,
        "hits": tp,
        "recall": round(tp / n, 4) if n else None,
        "recall_wilson": wilson(tp, n),
        "recall_tol3": _mean(within(3)),
        "recall_tol6": _mean(within(6)),
        "detections_mean": _mean([r["n_detections"] for r in records]),
        "p_any_detection": _mean([1.0 if r["n_detections"] else 0.0 for r in records]),
        "extras_mean": _mean([r["extras"] for r in records]),
        "extras_near_mean": _mean([r["extras_near"] for r in records]),
        "p_any_extra": _mean([1.0 if r["extras"] else 0.0 for r in records]),
        "precision": None if m["precision"] is None else round(m["precision"], 4),
        "f1": None if m["f1"] is None else round(m["f1"], 4),
        "loc_error_mean_abs": _mean([abs(r["loc_error"]) for r in hits]),
        "delta_bias_median": round(float(np.median(bias)), 4) if bias else None,
        "delta_bias_quartiles": [round(float(q), 4) for q in np.percentile(bias, [25, 75])] if bias else None,
        "share_high": _mean([1.0 if r["detected_high"] else 0.0 for r in hits]),
        "outliers_mean": _mean([r["n_outliers"] for r in records]),
        "share_out_of_range": _mean([1.0 if r["out_of_range"] else 0.0 for r in records]),
        "sigma_sim_median": round(float(np.median([r["sigma_sim"] for r in records])), 4) if n else None,
    }


def _snr_label(delta: float, sigma: float) -> str:
    ratio = delta / sigma if sigma > 0 else float("inf")
    for edge in SNR_EDGES:
        if ratio < edge:
            return f"<{edge:g}"
    return f">={SNR_EDGES[-1]:g}"


STRATA: Tuple[Tuple[str, Callable[[Dict[str, Any]], str]], ...] = (
    ("richtung", lambda r: "anstieg" if r["direction"] == "rise" else "abfall"),
    ("wechselmonat", lambda r: f"n<{THIN_N}" if r["n_at_change"] < THIN_N else f"n>={THIN_N}"),
    ("umgebung", lambda r: f"n<{NEIGHBOURS * THIN_N}" if r["n_neighbours"] < NEIGHBOURS * THIN_N else f"n>={NEIGHBOURS * THIN_N}"),
    ("luecke_davor", lambda r: "ja" if r["gap_before"] > 0 else "nein"),
    ("delta_durch_sigma", lambda r: _snr_label(r["delta"], r["sigma_sim"])),
)


def aggregate(records: Sequence[Dict[str, Any]], deltas: Sequence[float],
              evaluated_months: Optional[Dict[int, int]] = None, seed: int = SEED) -> Dict[str, Any]:
    """Je Bedingung, Lage und Größe: gesamt (mit Intervallen), je Reihe, nach Schichten."""
    groups: Dict[Tuple[str, str, float], List[Dict[str, Any]]] = {}
    for r in records:
        groups.setdefault((r["condition"], r["placement"], r["delta"]), []).append(r)
    total, per_series, strata = [], [], []
    for condition, placement in DESIGN:
        for d in deltas:
            rs = groups.get((condition, placement, float(d)), [])
            if not rs:
                continue
            key = {"condition": condition, "placement": placement, "delta": float(d)}
            by_company: Dict[int, List[Dict[str, Any]]] = {}
            for r in rs:
                by_company.setdefault(r["company_id"], []).append(r)
            series_rows = []
            for cid in sorted(by_company):
                s = {"company_id": cid, **key, **summarize(by_company[cid])}
                if evaluated_months and evaluated_months.get(cid):
                    s["detections_per_100_months"] = round(100 * s["detections_mean"] / evaluated_months[cid], 4)
                series_rows.append(s)
            per_series.extend(series_rows)
            recalls = {s["company_id"]: s["recall"] for s in series_rows}
            dets = {s["company_id"]: s["detections_mean"] for s in series_rows}
            row = {**key, **summarize(rs),
                   "recall_bootstrap": bootstrap_series(recalls, seed),
                   "recall_series_median": round(float(median(recalls.values())), 4),
                   "recall_series_range": [min(recalls.values()), max(recalls.values())],
                   "detections_bootstrap": bootstrap_series(dets, seed),
                   "detections_series_median": round(float(median(dets.values())), 4)}
            per100 = [s["detections_per_100_months"] for s in series_rows if "detections_per_100_months" in s]
            if per100:
                row["detections_per_100_months_median"] = round(float(median(per100)), 4)
            total.append(row)
            if d:
                for name, label_of in STRATA:
                    labelled: Dict[str, List[Dict[str, Any]]] = {}
                    for r in rs:
                        labelled.setdefault(label_of(r), []).append(r)
                    for label in sorted(labelled):
                        sub = labelled[label]
                        strata.append({**key, "stratum": name, "label": label, "reps": len(sub),
                                       "recall": round(sum(r["hit"] for r in sub) / len(sub), 4),
                                       "recall_wilson": wilson(sum(r["hit"] for r in sub), len(sub))})
    return {"total": total, "per_series": per_series, "strata": strata}


def fingerprint(rows: Sequence[Row], column: str = COLUMN) -> str:
    """SHA-256 über (id, Datum, Wert) aller Zeilen, unabhängig von der Reihenfolge."""
    lines = sorted(f"{r.get('id')}|{r.get('datum')}|{r.get(column)}" for r in rows)
    return hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()


def describe_series(rows: Sequence[Row], company_id: int) -> Dict[str, Any]:
    """Kennzahlen der echten Reihe zum Vergleich: Streuung, Dichte, beobachtete Markierungen."""
    series = build_monthly_series(list(rows), COLUMN)
    evaluated = evaluated_of(series)
    values = [v for v in (_numeric(r.get(COLUMN)) for r in rows if month_key(r.get("datum"))) if v is not None]
    observed = detect_anomalies(series, company_id=company_id, source=SOURCE, dimension=DIMENSION)
    observed_outliers = detect_outlier_months(series, company_id=company_id, source=SOURCE, dimension=DIMENSION)
    return {
        "n_reviews": len(values),
        "evaluated_months": len(evaluated),
        "eligible": is_eligible(series),
        "sd_review": round(pstdev(values), 4) if len(values) > 1 else None,
        "median_n": median(m["n_values"] for m in evaluated) if evaluated else None,
        "noise_sigma": round(noise_sigma([m["mean"] for m in evaluated]), 4) if evaluated else None,
        "observed_level_shifts": len(observed),
        "observed_outliers": len(observed_outliers),
        "fingerprint_sha256": fingerprint(rows),
    }


# ── Ausführung ───────────────────────────────────────────────────────────────

_WORKER_DATA: Dict[int, List[Row]] = {}


def _init_worker(data: Dict[int, List[Row]]) -> None:
    global _WORKER_DATA
    _WORKER_DATA = data


def _task(args: Tuple[int, int, Tuple[float, ...], int, int]) -> List[Dict[str, Any]]:
    company_id, rep, deltas, seed, margin = args
    return run_company_rep(_WORKER_DATA[company_id], company_id, rep, deltas, seed, margin)


def simulate(data: Dict[int, List[Row]], reps: int, deltas: Sequence[float], seed: int = SEED,
             margin: int = MARGIN, workers: int = 1) -> List[Dict[str, Any]]:
    """Alle Wiederholungen aller Reihen; Ergebnis nach (Reihe, Wiederholung, Bedingung, Lage, Größe) sortiert."""
    tasks = [(cid, rep, tuple(deltas), seed, margin) for cid in sorted(data) for rep in range(reps)]
    if workers <= 1:
        _init_worker(data)
        chunks = [_task(t) for t in tasks]
    else:
        with ProcessPoolExecutor(max_workers=workers, initializer=_init_worker, initargs=(data,)) as pool:
            chunks = list(pool.map(_task, tasks, chunksize=max(1, len(tasks) // (workers * 8))))
    records = [r for chunk in chunks for r in chunk]
    order = {d: i for i, d in enumerate(DESIGN)}
    return sorted(records, key=lambda r: (r["company_id"], r["rep"], order[(r["condition"], r["placement"])], r["delta"]))


def _git(*args: str) -> Optional[str]:
    try:
        return subprocess.run(["git", *args], cwd=BACKEND_DIR, capture_output=True, text=True, check=True).stdout
    except (OSError, subprocess.CalledProcessError):
        return None


def git_state() -> Dict[str, Any]:
    """Commit, uncommittete Änderungen unter backend/ und SHA-256 dieses Skripts."""
    commit = _git("rev-parse", "HEAD")
    status = _git("status", "--porcelain", "--", ".")
    with open(os.path.abspath(__file__), "rb") as fh:
        script_sha = hashlib.sha256(fh.read()).hexdigest()
    paths = [line[3:] for line in (status or "").splitlines() if line.strip()]
    return {"commit": commit.strip() if commit else None, "dirty": bool(paths) if status is not None else None,
            "dirty_paths": paths[:50], "script_sha256": script_sha}


def _versions() -> Dict[str, Optional[str]]:
    try:
        import ruptures
        rpt_version = getattr(ruptures, "__version__", None)
    except ImportError:
        rpt_version = None
    return {"python": platform.python_version(), "numpy": np.__version__, "ruptures": rpt_version,
            "platform": platform.platform()}


def load_companies(density_path: str, only: Optional[Sequence[int]] = None) -> List[Tuple[int, str]]:
    """Nicht-Demo-Unternehmen mit id aus data_density.json (Liste), optional gefiltert."""
    density, err = va._load_json(density_path, "data_density.json")
    if err:
        raise SystemExit(f"FEHLER: {err}")
    infos = va.companies_from_density(density).values()
    out = sorted((int(i.id), i.name) for i in infos if i.id is not None)
    return [c for c in out if not only or c[0] in set(only)]


def fetch_rows(company_id: int) -> List[Row]:
    from services.rating_series_service import fetch_review_rows  # lazy: Tests ohne DB
    return fetch_review_rows(SOURCE, company_id, COLUMN)


def _fmt(value: Optional[float], pct: bool = False) -> str:
    if value is None:
        return "–"
    return (f"{100 * value:.1f} %" if pct else f"{value:.2f}").replace(".", ",")


def _interval(iv: Optional[List[float]], pct: bool = True) -> str:
    return "–" if not iv else f"[{_fmt(iv[0], pct)}; {_fmt(iv[1], pct)}]"


def format_report(report: Dict[str, Any]) -> str:
    p = report["params"]
    lines = [
        "Semi-synthetische Prüfung der Erkennung (DZ1, E30)",
        f"  {len(report['series'])} Reihen ({SOURCE}/{DIMENSION}), {p['reps']} Wiederholungen je Reihe, "
        f"Seed {p['seed']}; Erkennung mit Standardparametern, Abgleich nach Regel 6.",
        "  Jede Reihe zählt gleich. Intervalle: Bootstrap über die Reihen (95 %).",
    ]
    titles = {("bewertungen", "mitte"): "Rauschen je Bewertung (eher optimistisch), Wechsel im Inneren",
              ("bewertungen", "ende"): "Rauschen je Bewertung, jüngster Wechsel (3–5 bewertete Monate danach)",
              ("monate", "mitte"): "Monate getauscht (eher pessimistisch), Wechsel im Inneren"}
    for condition, placement in DESIGN:
        rows = [t for t in report["results"]["total"] if t["condition"] == condition and t["placement"] == placement]
        if not rows:
            continue
        lines += ["", f"  {titles[(condition, placement)]}",
                  f"  {'Delta':>6} {'Recall':>8} {'Intervall':>18} {'Spanne Reihen':>17} {'±3 Mon.':>8} "
                  f"{'Mark./Wdh.':>11} {'P(≥1)':>7} {'nah':>5} {'Bias Δ':>7} {'deutl.':>7} {'E14':>5} {'>5/<1':>6}"]
        for t in rows:
            rng_ = t["recall_series_range"]
            lines.append(
                f"  {t['delta']:>6.2f} {_fmt(t['recall'], True):>8} {_interval(t['recall_bootstrap']):>18} "
                f"{_interval(rng_):>17} {_fmt(t['recall_tol3'], True):>8} {_fmt(t['detections_mean']):>11} "
                f"{_fmt(t['p_any_detection'], True):>7} {_fmt(t['extras_near_mean']):>5} "
                f"{_fmt(t['delta_bias_median']):>7} {_fmt(t['share_high'], True):>7} {_fmt(t['outliers_mean']):>5} "
                f"{_fmt(t['share_out_of_range'], True):>6}"
            )
        null = next((t for t in rows if t["delta"] == 0), None)
        if null:
            lines.append(f"  Delta 0: Recall = Zufallstreffer; Mark./Wdh. = Fehlalarme bei zeitlich austauschbarem Rauschen "
                         f"(Intervall {_interval(null['detections_bootstrap'], False)}, "
                         f"Median je 100 bewertete Monate {_fmt(null.get('detections_per_100_months_median'))}).")
    lines += ["", "  Recall nach Schichten (Rauschen je Bewertung, Wechsel im Inneren):"]
    for s in report["results"]["strata"]:
        if s["condition"] == "bewertungen" and s["placement"] == "mitte":
            lines.append(f"    Delta {s['delta']:.2f} {s['stratum']:<18} {s['label']:<8} "
                         f"{_fmt(s['recall'], True):>8} {_interval(s['recall_wilson']):>18} ({s['reps']})")
    names = {s["company_id"]: s["company"] for s in report["series"]}
    per = {(r["company_id"], r["condition"], r["placement"], r["delta"]): r for r in report["results"]["per_series"]}
    deltas = [d for d in p["deltas"] if d]
    lines += ["", f"  {'Reihe':<30}{'Mon.':>5}{'med n':>6}{'σ echt':>7}{'σ sim':>7}"
              + "".join(f"{'R@' + format(d, 'g'):>8}" for d in deltas) + f"{'FP@0':>6}{'FP@0 M':>7}{'beob.':>6}{'E14@0':>6}{'beob.':>6}"]
    for s in report["series"]:
        cid = s["company_id"]
        null_b, null_m = per.get((cid, "bewertungen", "mitte", 0.0)), per.get((cid, "monate", "mitte", 0.0))
        cells = "".join(f"{_fmt(per[(cid, 'bewertungen', 'mitte', d)]['recall'], True):>8}"
                        if (cid, "bewertungen", "mitte", d) in per else f"{'–':>8}" for d in deltas)
        lines.append(
            f"  {names[cid][:30]:<30}{s['evaluated_months']:>5}{_fmt(s['median_n']):>6}{_fmt(s['noise_sigma']):>7}"
            f"{_fmt(null_b['sigma_sim_median'] if null_b else None):>7}" + cells
            + f"{_fmt(null_b['detections_mean'] if null_b else None):>6}{_fmt(null_m['detections_mean'] if null_m else None):>7}"
            + f"{s['observed_level_shifts']:>6}{_fmt(null_b['outliers_mean'] if null_b else None):>6}{s['observed_outliers']:>6}"
        )
    lines.append("  R@d: Recall (je Bewertung, Inneres); FP@0 / FP@0 M: Markierungen je Wiederholung ohne Wechsel "
                 "(je Bewertung / Monate getauscht); beob.: auf der echten Reihe; E14@0: Einzelmonate ohne Wechsel.")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--reps", type=int, default=REPS, help=f"Wiederholungen je Reihe (Standard {REPS})")
    parser.add_argument("--deltas", type=float, nargs="+", default=list(DELTAS), help="Größen in Sternen; 0 = ohne Wechsel")
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument("--margin", type=int, default=MARGIN, help="bewertete Monate vor und ab dem Wechsel (Lage mitte)")
    parser.add_argument("--workers", type=int, default=1, help="Prozesse (Ergebnis unabhängig davon)")
    parser.add_argument("--company", type=int, action="append", help="nur diese Unternehmens-id(s)")
    parser.add_argument("--density", default=DEFAULT_DENSITY, help="data_density.json (Unternehmensliste)")
    parser.add_argument("--json", dest="json_out", help="Ergebnis zusätzlich als JSON-Datei schreiben")
    parser.add_argument("--records", dest="records_out", help="Datensätze je Wiederholung (.json oder .json.gz, ohne Noten)")
    parser.add_argument("--allow-dirty", action="store_true", help="--json/--records trotz uncommitteter Änderungen unter backend/")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    deltas = tuple(sorted(dict.fromkeys(float(d) for d in args.deltas)))
    if any(not math.isfinite(d) or d < 0 for d in deltas):
        parser.error("--deltas: nur endliche Beträge ≥ 0 (die Richtung wird je Wiederholung gezogen).")
    if args.reps < 1:
        parser.error("--reps muss mindestens 1 sein.")
    if args.margin < DEFAULT_MIN_SIZE:
        parser.error(f"--margin muss mindestens min_size ({DEFAULT_MIN_SIZE}) sein.")
    if args.seed < 0:
        parser.error("--seed muss ≥ 0 sein.")
    state = git_state()
    if (args.json_out or args.records_out) and state["dirty"] and not args.allow_dirty:
        parser.error("uncommittete Änderungen unter backend/ (" + ", ".join(state["dirty_paths"][:5])
                     + "): erst committen oder --allow-dirty setzen.")

    started = time.time()
    data: Dict[int, List[Row]] = {}
    series_info: List[Dict[str, Any]] = []
    skipped: List[Dict[str, Any]] = []
    print("Lese Bewertungen (nur SELECT) …", file=sys.stderr)
    for cid, name in load_companies(args.density, args.company):
        rows = fetch_rows(cid)
        info = describe_series(rows, cid)
        if not info["eligible"] or info["evaluated_months"] < 2 * args.margin:
            skipped.append({"company_id": cid, "company": name, "evaluated_months": info["evaluated_months"]})
            continue
        data[cid] = rows
        series_info.append({"company_id": cid, "company": name, **info})
    if not data:
        print("Keine geeignete Reihe.", file=sys.stderr)
        return 1

    print(f"Simuliere {len(data)} Reihen × {args.reps} Wiederholungen …", file=sys.stderr)
    records = simulate(data, args.reps, deltas, args.seed, args.margin, args.workers)
    any_rows = next(iter(data.values()))
    detection = {k: v for k, v in detection_params(build_monthly_series(any_rows, COLUMN)).items()
                 if k not in ("noise_sigma", "penalty", "n_evaluated")}
    detection.update({"severity_high": SEVERITY_HIGH, "jump": PeltDetector().jump})
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "started_at": datetime.fromtimestamp(started, timezone.utc).isoformat(timespec="seconds"),
        "duration_s": round(time.time() - started, 1),
        "argv": list(argv) if argv is not None else sys.argv[1:],
        "git": state,
        "versions": _versions(),
        "params": {
            "source": SOURCE, "dimension": DIMENSION, "deltas": list(deltas), "reps": args.reps, "seed": args.seed,
            "margin": args.margin, "end_after": list(END_AFTER), "near_months": NEAR_MONTHS, "neighbours": NEIGHBOURS,
            "thin_n": THIN_N, "snr_edges": list(SNR_EDGES), "bootstrap": BOOTSTRAP,
            "design": [list(d) for d in DESIGN], "company_filter": args.company,
            "detection": detection,
            "rules": {"tolerance_months": ed.TOLERANCE_MONTHS, "max_shift_months": ed.MAX_SHIFT_MONTHS,
                      "same_direction": True, "one_to_one": True, "variant": "niveauwechsel"},
            "conditions": {
                "bewertungen": "Permutation der Gesamtnoten über die datierten Bewertungen; Belegung je Monat unverändert",
                "monate": "Permutation der bewerteten Monate (Mittel und Anzahl) über die bewerteten Kalendermonate",
            },
            "injection": "±delta auf jedes Monatsmittel ab dem Wechselmonat, ohne Kappung",
            "weighting": "jede Reihe gleich (gleich viele Wiederholungen je Reihe)",
        },
        "series": series_info,
        "skipped": skipped,
        "results": aggregate(records, deltas, {s["company_id"]: s["evaluated_months"] for s in series_info}, args.seed),
    }
    print(format_report(report))
    if args.json_out:
        os.makedirs(os.path.dirname(os.path.abspath(args.json_out)), exist_ok=True)
        with open(args.json_out, "w", encoding="utf-8") as fh:
            json.dump(report, fh, ensure_ascii=False, indent=2)
            fh.write("\n")
        print(f"\nErgebnis gespeichert: {args.json_out}")
    if args.records_out:
        os.makedirs(os.path.dirname(os.path.abspath(args.records_out)), exist_ok=True)
        opener = gzip.open if args.records_out.endswith(".gz") else open
        with opener(args.records_out, "wt", encoding="utf-8") as fh:
            json.dump({"git": state, "params": report["params"], "records": records}, fh, ensure_ascii=False)
        print(f"Datensätze gespeichert: {args.records_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
