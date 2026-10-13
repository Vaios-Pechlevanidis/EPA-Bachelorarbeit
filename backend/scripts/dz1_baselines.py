"""
Bezugsgrößen und Unsicherheit für den DZ1-Wert (E9, Aktualisierung 2026-10-10;
E5 Regel 6), offline und reproduzierbar.

Zweck
-----
Der DZ1-Lauf (``data/calibration/dz1_ergebnis.json``) liefert im Hauptwert F1 0,43
(8 Treffer, 9 zusätzliche Markierungen, 12 verfehlte Zeiträume). Für sich sagt die
Zahl wenig: Dieses Skript stellt ihr Bezugsgrößen (Zufall, eine naive Regel) und
Intervalle gegenüber. Es **kalibriert nichts**; Erkennung (E9, E14), Referenz (E5)
und Abgleichregel (Regel 6) bleiben unverändert. Die Größen sind nachträglich
gewählt, nicht vorab festgelegt.

Eingaben (nur versionierte Dateien, keine Datenbank, kein erneuter Detektorlauf)
-------------------------------------------------------------------------------
- ``data/calibration/dz1_ergebnis.json``: Treffer, zusätzliche Markierungen und
  verfehlte Zeiträume je annotierter Reihe; daraus die Erkennungen (Monat,
  Richtung) und ihre Zahl je Reihe und Variante.
- ``data/annotations.json``: Referenzzeiträume (Mitarbeitende, Gesamtbewertung).
- ``data/series/<id>_<slug>_employee.csv``: bewertete Monate (``count`` ≥ 5 und
  Monatsmittel vorhanden, E4) und Monatsmittel.
- ``data/calibration/semisynthetisch_2026-10-13.json``: die 15 geeigneten Reihen
  (E4) und für die 7 Reihen ohne Eintrag die Zahl der beobachteten Niveauwechsel
  und Einzelmonate (``series[].observed_level_shifts`` / ``observed_outliers``).

Abgleich ausschließlich mit den reinen Funktionen aus ``evaluate_detection``
(``match_series``, ``match_window`` über ``match_series``, ``metrics``), also
Regel 6 unverändert (Toleranz ±1 Monat, Lückenkappung 3, gleiche Richtung,
Eins-zu-eins).

Kennzahlen
----------
Zwei Bezugsmengen, je Variante ``niveauwechsel`` und ``niveauwechsel+einzelmonate``:

- ``hauptwert``: die 8 annotierten Reihen wie im DZ1-Lauf.
- ``regelkonform``: alle 15 geeigneten Reihen (Regel 6 nennt F1 „über alle
  Reihen“); in den 7 Reihen ohne Eintrag ist jede Markierung zusätzlich (FP).

1. **Beobachtet:** TP, FP, FN, Precision, Recall, F1. Für die annotierten Reihen
   neu abgeglichen und gegen die Zahlen in ``dz1_ergebnis.json`` geprüft.
2. **Zufall:** je Reihe so viele Markierungen wie die Erkennung (Variante),
   gleichverteilt auf die bewerteten Monate ohne Doppelung. Richtung entweder
   50/50 oder aus dem Vorniveau (``rise``, wenn das Monatsmittel mindestens so hoch
   ist wie das Mittel der bis zu 6 vorangehenden bewerteten Monate; im ersten
   bewerteten Monat ohne Vorniveau 50/50). Ausgabe: Mittel, Median, 95.- und
   99.-Perzentil des F1, Anteil der Ziehungen mit F1 ≥ beobachtet, Verteilung der
   Treffer. Weil die Zahl der Markierungen fest ist, gilt je Ziehung
   ``F1 = 2·TP / (Markierungen + Zeiträume)``; der Vergleich ist ein Vergleich der
   Trefferzahl. In der Bezugsmenge ``regelkonform`` zählen die Markierungen der
   7 Reihen ohne Eintrag unabhängig von ihrer Lage als FP.
   Sensitivität ``wie_pelt`` (nur Niveauwechsel): Stellen mit mindestens 3
   bewerteten Monaten davor und ab der Stelle, Abstand zweier Markierungen
   mindestens 3 bewertete Monate (wie ``min_size`` in E9). Das ist die Regel des
   Prüfskripts aus dem Gutachten vom 2026-10-13.
3. **Naive Regel** (Definition des Prüfskripts, unverändert übernommen): je Reihe
   die ``k`` Stellen mit dem größten Betrag ``|Monatsmittel − Mittel der bis zu 6
   vorangehenden bewerteten Monate|`` unter den Stellen mit mindestens 3 bewerteten
   Monaten davor und ab der Stelle; absteigend sortiert nach (Betrag, Index,
   Richtung), gierig ausgewählt mit Abstand ≥ 3 bewertete Monate; ``k`` wie die
   Erkennung; Richtung ``rise``, wenn das Monatsmittel über dem Vorniveau liegt,
   sonst ``fall``. **Grenze:** Das Vorniveau ist dasselbe wie im Größenkriterium der
   Referenzregel (Protokoll-Regel 4); die naive Regel ist der Referenz deshalb
   ähnlich und keine unabhängige Bezugsgröße.
4. **Wilson-Intervalle** (95 %) für Precision und Recall. Sie behandeln
   Markierungen bzw. Zeiträume als unabhängig und unterschätzen die Unsicherheit,
   wenn Treffer innerhalb einer Reihe zusammenhängen.
5. **Cluster-Bootstrap über Reihen:** Reihen mit Zurücklegen ziehen, TP, FP, FN
   summieren, F1 berechnen; 95-%-Perzentilintervall. Ziehungen ohne definierten F1
   (keine Markierung und kein Zeitraum) werden nicht gewertet und gezählt.

Perzentile: Rang ``⌊q·N⌋`` der aufsteigend sortierten Werte (0-basiert, ohne
Interpolation), wie im Prüfskript.

Reproduzierbarkeit
------------------
Jeder Teil zieht aus einem eigenen ``random.Random(f"{seed}/{Bezeichnung}")``
(Seed 20261013, 10 000 Ziehungen für Zufall und Bootstrap). Die JSON-Ausgabe nennt
Commit, uncommittete Änderungen unter ``backend/``, SHA-256 dieses Skripts und von
``evaluate_detection.py``, SHA-256 jeder Eingabedatei, einen SHA-256 über die
Einträge von ``annotations.json`` (ohne ``hinweise``), Seed und Ziehungen. Schlägt
eine Konsistenzprüfung fehl (Neuabgleich ≠ ``dz1_ergebnis.json``, Zahl der
bewerteten Monate, Zahl der Markierungen, Menge der geeigneten Reihen), bricht das
Skript ohne JSON-Ausgabe ab.

Abweichungen zum Prüfskript: anderer Seed (20261013 statt 42 bzw. 7) und 10 000
statt 20 000 Ziehungen (Monte-Carlo-Fehler); Zufall im Hauptteil auf allen
bewerteten Monaten ohne Doppelung statt mit Rand und Abstand 3 (die Regel des
Prüfskripts steht als Sensitivität ``wie_pelt`` daneben); Abgleich mit
``evaluate_detection.match_series`` statt einer eigenen Nachbildung.

Verwendung::

    cd backend
    uv run python scripts/dz1_baselines.py
    uv run python scripts/dz1_baselines.py --json data/calibration/dz1_baselines_YYYY-MM-DD.json
"""

from __future__ import annotations

import argparse
import csv
import glob
import hashlib
import json
import math
import os
import platform
import random
import statistics
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND_DIR)
sys.path.insert(0, os.path.join(BACKEND_DIR, "scripts"))

import evaluate_detection as ed  # noqa: E402
import validate_annotations as va  # noqa: E402
from services.rating_series_service import (  # noqa: E402
    MIN_EVALUATED_MONTHS,
    MIN_REVIEWS_PER_MONTH,
    OVERALL_DIMENSION,
)

SOURCE = "employee"
DIMENSION = OVERALL_DIMENSION
MEAN_COLUMN = f"mean_{OVERALL_DIMENSION}"
SEED = 20261013
DRAWS = 10_000             # Ziehungen der Zufalls-Bezugsgrößen
BOOTSTRAP = 10_000         # Ziehungen des Cluster-Bootstrap
PRIOR_WIDTH = 6            # Vorniveau: bis zu 6 vorangehende bewertete Monate (Protokoll-Regel 4)
PELT_EDGE = 3              # wie min_size (E9): bewertete Monate davor und ab der Stelle
PELT_GAP = 3               # wie min_size (E9): Mindestabstand zweier Markierungen in bewerteten Monaten
MAX_TRIES = 1000           # Versuche je Reihe und Ziehung beim Platzieren der Zufallsmarkierungen
WILSON_Z = 1.959964
VARIANTS = ed.VARIANTS     # ("niveauwechsel", "niveauwechsel+einzelmonate")
SCOPES: Tuple[str, str] = ("hauptwert", "regelkonform")
DIRECTIONS: Tuple[str, str] = ("richtung_50_50", "richtung_vorniveau")
POSITION_RULES: Dict[str, Tuple[int, int]] = {   # Name: (Rand, Mindestabstand) in bewerteten Monaten
    "bewertete_monate": (0, 1),
    "wie_pelt": (PELT_EDGE, PELT_GAP),
}
KIND_RANDOM = "zufall"
KIND_NAIVE = "naiv"

DEFAULT_DZ1 = os.path.join(BACKEND_DIR, "data", "calibration", "dz1_ergebnis.json")
DEFAULT_ANNOTATIONS = os.path.join(BACKEND_DIR, "data", "annotations.json")
DEFAULT_SEMI = os.path.join(BACKEND_DIR, "data", "calibration", "semisynthetisch_2026-10-13.json")
DEFAULT_SERIES_DIR = os.path.join(BACKEND_DIR, "data", "series")

Counts = Tuple[int, int, int]           # (tp, fp, fn)
Evaluated = List[Tuple[str, float]]     # bewertete Monate (Monat, Monatsmittel) in zeitlicher Folge


# ── Reihen aus den Serien-CSVs (rein) ────────────────────────────────────────

def parse_series_csv(lines: Iterable[str], column: str = MEAN_COLUMN) -> List[Tuple[str, Optional[float], int]]:
    """Zeilen einer Serien-CSV (Trennzeichen ';') als ``(Monat, Mittel oder None, count)``."""
    out = []
    for row in csv.DictReader(lines, delimiter=";"):
        raw = (row.get(column) or "").strip()
        out.append((row["period"], float(raw) if raw else None, int(row.get("count") or 0)))
    return out


def evaluated_of(rows: Sequence[Tuple[str, Optional[float], int]],
                 min_reviews: int = MIN_REVIEWS_PER_MONTH) -> Evaluated:
    """Bewertete Monate (E4): Monatsmittel vorhanden und ``count`` ≥ ``min_reviews``."""
    return [(p, m) for p, m, n in sorted(rows, key=lambda r: r[0]) if m is not None and n >= min_reviews]


def prior_level(values: Sequence[float], i: int, width: int = PRIOR_WIDTH) -> Optional[float]:
    """Mittel der bis zu ``width`` vorangehenden Werte; None ohne Vorgänger."""
    pre = values[max(0, i - width):i]
    return sum(pre) / len(pre) if pre else None


def informed_direction(values: Sequence[float], i: int, width: int = PRIOR_WIDTH) -> Optional[str]:
    """``rise``, wenn ``values[i]`` mindestens so hoch ist wie das Vorniveau, sonst ``fall``; None ohne Vorniveau."""
    prior = prior_level(values, i, width)
    if prior is None:
        return None
    return "rise" if values[i] >= prior else "fall"


# ── Markierungen ohne Detektor (rein) ────────────────────────────────────────

def allowed_positions(n: int, edge: int = 0) -> List[int]:
    """Indizes bewerteter Monate, an denen eine Markierung liegen darf. ``edge > 0``:
    mindestens ``edge`` bewertete Monate davor und ``edge`` ab der Stelle (einschließlich)."""
    return list(range(edge, n - edge + 1)) if edge > 0 else list(range(n))


def draw_positions(n: int, k: int, rng: random.Random, edge: int = 0, min_gap: int = 1,
                   max_tries: int = MAX_TRIES) -> List[int]:
    """Bis zu ``k`` Stellen, nacheinander gleichverteilt aus ``allowed_positions`` gezogen
    und verworfen, wenn sie einer gewählten Stelle näher als ``min_gap`` liegen
    (``min_gap = 1``: ohne Doppelung). Höchstens ``max_tries`` Versuche; die Liste
    kann dann kürzer als ``k`` sein. Reihenfolge = Reihenfolge der Ziehung."""
    pos = allowed_positions(n, edge)
    chosen: List[int] = []
    if not pos or k <= 0:
        return chosen
    tries = 0
    while len(chosen) < k and tries < max_tries:
        tries += 1
        i = rng.choice(pos)
        if all(abs(i - j) >= min_gap for j in chosen):
            chosen.append(i)
    return chosen


def random_detections(evaluated: Evaluated, k: int, rng: random.Random, directions: str = DIRECTIONS[0],
                      edge: int = 0, min_gap: int = 1,
                      informed: Optional[Sequence[Optional[str]]] = None) -> List[Dict[str, Any]]:
    """Zufallsmarkierungen einer Reihe im Format von ``match_series``.

    ``directions``: ``richtung_50_50`` (Münzwurf je Markierung) oder
    ``richtung_vorniveau`` (``informed_direction``; ohne Vorniveau Münzwurf).
    ``informed`` (optional) sind die vorab berechneten Richtungen je Index."""
    values = [m for _, m in evaluated]
    out = []
    for i in draw_positions(len(evaluated), k, rng, edge, min_gap):
        direction = None
        if directions == DIRECTIONS[1]:
            direction = informed[i] if informed is not None else informed_direction(values, i)
        elif directions != DIRECTIONS[0]:
            raise ValueError(f"unbekannte Richtungsregel: {directions}")
        if direction is None:
            direction = rng.choice(("rise", "fall"))
        out.append({"kind": KIND_RANDOM, "date": evaluated[i][0], "direction": direction})
    return sorted(out, key=lambda d: d["date"])


def naive_topk(evaluated: Evaluated, k: int, width: int = PRIOR_WIDTH, edge: int = PELT_EDGE,
               min_gap: int = PELT_GAP) -> List[Dict[str, Any]]:
    """Naive Regel des Prüfskripts: die ``k`` Stellen mit dem größten
    ``|Monatsmittel − Vorniveau|`` (Vorniveau = Mittel der bis zu ``width``
    vorangehenden bewerteten Monate), Stellen nach ``allowed_positions(n, edge)``,
    absteigend nach (Betrag, Index, Richtung) sortiert und gierig mit Abstand ≥
    ``min_gap`` gewählt. Richtung ``rise``, wenn das Mittel über dem Vorniveau liegt."""
    values = [m for _, m in evaluated]
    scored = []
    for i in allowed_positions(len(values), edge):
        prior = prior_level(values, i, width)
        if prior is None:
            continue
        scored.append((abs(values[i] - prior), i, "rise" if values[i] > prior else "fall"))
    scored.sort(reverse=True)
    chosen: List[Tuple[int, str, float]] = []
    for score, i, direction in scored:
        if len(chosen) >= k:
            break
        if all(abs(i - j) >= min_gap for j, _, _ in chosen):
            chosen.append((i, direction, score))
    return sorted(({"kind": KIND_NAIVE, "date": evaluated[i][0], "direction": d, "deviation": round(s, 3)}
                   for i, d, s in chosen), key=lambda d: d["date"])


# ── Eingaben zusammenführen (rein) ───────────────────────────────────────────

def detections_from_dz1(variant_result: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Erkennungen einer Variante aus ``dz1_ergebnis.json``: Treffer und zusätzliche Markierungen."""
    dets = [dict(h["detection"]) for h in variant_result.get("hits") or []]
    dets += [dict(e) for e in variant_result.get("extras") or []]
    return sorted(dets, key=lambda d: (d["date"], d.get("kind") or ""))


def _ann_key(ann: Dict[str, Any]) -> Tuple[str, str, str]:
    return (ann["period_from"], ann["period_to"], ann["direction"])


def _check(name: str, problems: List[str], ok_detail: str) -> Dict[str, Any]:
    return {"name": name, "ok": not problems, "detail": "; ".join(problems) if problems else ok_detail}


def build_inputs(dz1: Dict[str, Any], ann_doc: Dict[str, Any], semi: Dict[str, Any],
                 csv_rows: Dict[int, Sequence[Tuple[str, Optional[float], int]]],
                 eval_counts_all: Optional[Dict[int, int]] = None,
                 source: str = SOURCE, dimension: str = DIMENSION) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Reihen (nach ``company_id``) und Konsistenzprüfungen; reine Funktion.

    ``csv_rows``: Zeilen der Serien-CSV je ``company_id`` (mindestens die geeigneten
    Reihen); ``eval_counts_all``: bewertete Monate aller CSVs je ``company_id`` für
    den Abgleich der Menge geeigneter Reihen (E4) mit ``semi``."""
    semi_by_id = {int(s["company_id"]): s for s in semi.get("series") or []}
    dz1_by_id = {int(s["company_id"]): s for s in dz1.get("series") or []
                 if s.get("source") == source and s.get("dimension") == dimension}
    norm_to_id = {va.normalize_company_name(s["company"]): cid for cid, s in semi_by_id.items()}

    grouped: Dict[int, List[Dict[str, Any]]] = {}
    unknown: List[str] = []
    for (norm, src, dim), anns in ed.group_annotations(ann_doc).items():
        if src != source or dim != dimension:
            continue
        cid = norm_to_id.get(norm)
        if cid is None:
            unknown.append(anns[0]["company"])
        else:
            grouped[cid] = anns

    p_series: List[str] = []
    if unknown:
        p_series.append("Einträge zu nicht geeigneten oder unbekannten Reihen: " + ", ".join(sorted(unknown)))
    if set(grouped) != set(dz1_by_id):
        p_series.append(f"annotierte Reihen {sorted(grouped)} ≠ Reihen im DZ1-Ergebnis {sorted(dz1_by_id)}")
    if dz1.get("skipped"):
        p_series.append(f"DZ1-Ergebnis mit übersprungenen Reihen: {len(dz1['skipped'])}")
    p_ann, p_months, p_marks, p_eligible = [], [], [], []
    if eval_counts_all is not None:
        eligible = {cid for cid, n in eval_counts_all.items() if n >= MIN_EVALUATED_MONTHS}
        if eligible != set(semi_by_id):
            p_eligible.append(f"geeignet laut CSV {sorted(eligible)} ≠ Reihen der Simulation {sorted(semi_by_id)}")

    series: List[Dict[str, Any]] = []
    for cid in sorted(semi_by_id):
        s = semi_by_id[cid]
        if cid not in csv_rows:
            raise ValueError(f"Serien-CSV für Unternehmen {cid} ({s['company']}) fehlt.")
        evaluated = evaluated_of(csv_rows[cid])
        if len(evaluated) != int(s["evaluated_months"]):
            p_months.append(f"{s['company']}: CSV {len(evaluated)} ≠ Simulation {s['evaluated_months']}")
        semi_k = {VARIANTS[0]: int(s["observed_level_shifts"]),
                  VARIANTS[1]: int(s["observed_level_shifts"]) + int(s["observed_outliers"])}
        entry: Dict[str, Any] = {"company_id": cid, "company": s["company"], "evaluated": evaluated,
                                 "annotations": grouped.get(cid, []), "annotated": cid in grouped,
                                 "detections": None, "recorded": None, "k": semi_k}
        if cid in grouped and cid in dz1_by_id:
            d = dz1_by_id[cid]
            entry["detections"] = {v: detections_from_dz1(d["variants"][v]) for v in VARIANTS}
            entry["k"] = {v: len(entry["detections"][v]) for v in VARIANTS}
            entry["recorded"] = {v: (d["variants"][v]["tp"], d["variants"][v]["fp"], d["variants"][v]["fn"])
                                 for v in VARIANTS}
            for v in VARIANTS:
                if entry["k"][v] != int(d["variants"][v].get("n_detections", entry["k"][v])):
                    p_marks.append(f"{s['company']} {v}: Treffer+zusätzlich {entry['k'][v]} ≠ n_detections")
                if entry["k"][v] != semi_k[v]:
                    p_marks.append(f"{s['company']} {v}: DZ1 {entry['k'][v]} ≠ Simulation {semi_k[v]}")
            if len(evaluated) != int(d["evaluated_months"]):
                p_months.append(f"{s['company']}: CSV {len(evaluated)} ≠ DZ1 {d['evaluated_months']}")
            in_dz1 = sorted(_ann_key(x["annotation"]) for x in d["variants"][VARIANTS[0]]["hits"]
                            + d["variants"][VARIANTS[0]]["misses"])
            if sorted(_ann_key(a) for a in grouped[cid]) != in_dz1:
                p_ann.append(f"{s['company']}: Einträge in annotations.json ≠ Einträge im DZ1-Ergebnis")
        elif cid in grouped:
            entry["annotated"] = False   # ohne DZ1-Ergebnis nicht auswertbar; Prüfung oben schlägt an
        series.append(entry)

    checks = [
        _check("reihen", p_series, f"{len(grouped)} annotierte von {len(semi_by_id)} geeigneten Reihen, wie im DZ1-Ergebnis"),
        _check("geeignete_reihen", p_eligible,
               "Menge der geeigneten Reihen aus den CSVs gleich der Simulation" if eval_counts_all is not None
               else "nicht geprüft (keine Zählungen aller CSVs)"),
        _check("referenzzeitraeume", p_ann, "Einträge in annotations.json gleich den Einträgen im DZ1-Ergebnis"),
        _check("bewertete_monate", p_months, "Zahl der bewerteten Monate aus den CSVs gleich DZ1-Ergebnis und Simulation"),
        _check("markierungen", p_marks, "Zahl der Markierungen je annotierter Reihe in DZ1-Ergebnis und Simulation gleich"),
    ]
    return series, checks


# ── Abgleich und Kennzahlen (rein) ───────────────────────────────────────────

def _evaluated_set(entry: Dict[str, Any]) -> set:
    return {p for p, _ in entry["evaluated"]}


def observed_counts(series: Sequence[Dict[str, Any]], variant: str) -> List[Dict[str, Any]]:
    """Beobachtete TP/FP/FN je Reihe: annotierte Reihen neu nach Regel 6 abgeglichen
    (``match_series``), Reihen ohne Eintrag mit allen Markierungen als FP."""
    out = []
    for s in series:
        if s["annotated"]:
            m = ed.match_series(s["annotations"], s["detections"][variant], _evaluated_set(s))
            counts = (m["tp"], m["fp"], m["fn"])
            reproduced: Optional[bool] = counts == tuple(s["recorded"][variant])
        else:
            m = ed.metrics(0, s["k"][variant], 0)
            counts, reproduced = (m["tp"], m["fp"], m["fn"]), None
        out.append({"company_id": s["company_id"], "company": s["company"], "annotated": s["annotated"],
                    "tp": counts[0], "fp": counts[1], "fn": counts[2], "reproduced": reproduced})
    return out


def naive_counts(series: Sequence[Dict[str, Any]], variant: str) -> List[Dict[str, Any]]:
    """TP/FP/FN der naiven Regel je Reihe (``k`` wie die Erkennung in der Variante)."""
    out = []
    for s in series:
        dets = naive_topk(s["evaluated"], s["k"][variant])
        m = ed.match_series(s["annotations"], dets, _evaluated_set(s))
        out.append({"company_id": s["company_id"], "company": s["company"], "annotated": s["annotated"],
                    "tp": m["tp"], "fp": m["fp"], "fn": m["fn"], "dates": [d["date"] for d in dets]})
    return out


def sum_counts(rows: Iterable[Dict[str, Any]]) -> Counts:
    rows = list(rows)
    return (sum(r["tp"] for r in rows), sum(r["fp"] for r in rows), sum(r["fn"] for r in rows))


def wilson(k: int, n: int, z: float = WILSON_Z) -> Optional[List[float]]:
    """Wilson-Intervall eines Anteils ``k/n`` (Standard 95 %); None ohne Fälle."""
    if n <= 0:
        return None
    p = k / n
    centre = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return [max(0.0, centre - half), min(1.0, centre + half)]


def quantile(sorted_values: Sequence[float], q: float) -> Optional[float]:
    """Perzentil nach Rang ``⌊q·N⌋`` der aufsteigend sortierten Werte (0-basiert, ohne Interpolation)."""
    if not sorted_values:
        return None
    return sorted_values[min(len(sorted_values) - 1, int(math.floor(q * len(sorted_values))))]


def _r(value: Optional[float], digits: int = 4) -> Optional[float]:
    return None if value is None else round(float(value), digits)


def describe(counts: Counts) -> Dict[str, Any]:
    """Kennzahlen und Wilson-Intervalle für (tp, fp, fn)."""
    tp, fp, fn = counts
    m = ed.metrics(tp, fp, fn)
    return {"tp": tp, "fp": fp, "fn": fn, "precision": _r(m["precision"]), "recall": _r(m["recall"]), "f1": _r(m["f1"]),
            "precision_wilson95": [_r(v) for v in wilson(tp, tp + fp)] if tp + fp else None,
            "recall_wilson95": [_r(v) for v in wilson(tp, tp + fn)] if tp + fn else None}


def summarize_draws(draws: Sequence[Counts], observed_f1: float, extra_fp: int = 0,
                    tol: float = 1e-9) -> Dict[str, Any]:
    """Verteilung des F1 über Zufallsziehungen; ``extra_fp`` wird je Ziehung zu FP addiert
    (Markierungen in Reihen ohne Eintrag). ``share_ge_observed_plus1`` = (Anzahl+1)/(N+1)."""
    f1s, tps = [], []
    for tp, fp, fn in draws:
        f1 = ed.metrics(tp, fp + extra_fp, fn)["f1"]
        f1s.append(0.0 if f1 is None else f1)
        tps.append(tp)
    f1s.sort()
    n = len(f1s)
    n_ge = sum(1 for v in f1s if v >= observed_f1 - tol)
    return {
        "draws": n,
        "f1_mean": _r(statistics.mean(f1s)) if n else None,
        "f1_median": _r(statistics.median(f1s)) if n else None,
        "f1_p95": _r(quantile(f1s, 0.95)),
        "f1_p99": _r(quantile(f1s, 0.99)),
        "f1_max": _r(f1s[-1]) if n else None,
        "tp_mean": _r(statistics.mean(tps)) if n else None,
        "tp_p95": quantile(sorted(tps), 0.95),
        "tp_p99": quantile(sorted(tps), 0.99),
        "tp_distribution": {str(k): v for k, v in sorted(Counter(tps).items())},
        "observed_f1": _r(observed_f1),
        "n_ge_observed": n_ge,
        "share_ge_observed": _r(n_ge / n) if n else None,
        "share_ge_observed_plus1": _r((n_ge + 1) / (n + 1)) if n else None,
    }


def random_baseline(series: Sequence[Dict[str, Any]], variant: str, draws: int, rng: random.Random,
                    directions: str = DIRECTIONS[0], edge: int = 0, min_gap: int = 1) -> Tuple[List[Counts], int]:
    """Zufallsziehungen über die annotierten Reihen (in Reihenfolge der Liste).

    Je Ziehung (tp, fp, fn) summiert über die annotierten Reihen; dazu die Zahl der
    Ziehungen, in denen eine Reihe weniger als ``k`` Markierungen erhielt."""
    prepared = []
    for s in series:
        if not s["annotated"]:
            continue
        values = [m for _, m in s["evaluated"]]
        informed = [informed_direction(values, i) for i in range(len(values))]
        prepared.append((s["annotations"], s["evaluated"], _evaluated_set(s), s["k"][variant], informed))
    out: List[Counts] = []
    short = 0
    for _ in range(draws):
        tp = fp = fn = 0
        is_short = False
        for anns, evaluated, evset, k, informed in prepared:
            dets = random_detections(evaluated, k, rng, directions, edge, min_gap, informed)
            is_short = is_short or len(dets) < k
            m = ed.match_series(anns, dets, evset)
            tp, fp, fn = tp + m["tp"], fp + m["fp"], fn + m["fn"]
        out.append((tp, fp, fn))
        short += int(is_short)
    return out, short


def cluster_bootstrap(per_series: Sequence[Counts], draws: int, rng: random.Random) -> Dict[str, Any]:
    """Reihen mit Zurücklegen ziehen, TP/FP/FN summieren, F1; 95-%-Perzentilintervall."""
    n = len(per_series)
    values: List[float] = []
    undefined = 0
    for _ in range(draws):
        sample = [per_series[rng.randrange(n)] for _ in range(n)]
        f1 = ed.metrics(sum(s[0] for s in sample), sum(s[1] for s in sample), sum(s[2] for s in sample))["f1"]
        if f1 is None:
            undefined += 1
        else:
            values.append(f1)
    values.sort()
    return {"draws": draws, "n_series": n, "undefined": undefined,
            "f1_mean": _r(statistics.mean(values)) if values else None,
            "f1_median": _r(statistics.median(values)) if values else None,
            "f1_interval95": [_r(quantile(values, 0.025)), _r(quantile(values, 0.975))] if values else None}


def make_rng(seed: int, label: str) -> random.Random:
    """Eigener, reproduzierbarer Zufallsstrom je Teil (String-Seed über SHA-512, Python ≥ 3.2)."""
    return random.Random(f"{seed}/{label}")


def compute(series: Sequence[Dict[str, Any]], seed: int = SEED, draws: int = DRAWS,
            boot_draws: int = BOOTSTRAP) -> Dict[str, Any]:
    """Alle Kennzahlen; deterministisch bei gleichem Seed und gleichen Eingaben."""
    results: Dict[str, Dict[str, Any]] = {scope: {} for scope in SCOPES}
    sensitivity: Dict[str, Dict[str, Any]] = {scope: {} for scope in SCOPES}
    per_series: Dict[int, Dict[str, Any]] = {
        s["company_id"]: {"company_id": s["company_id"], "company": s["company"], "annotated": s["annotated"],
                          "evaluated_months": len(s["evaluated"]), "n_annotations": len(s["annotations"]),
                          "markers": dict(s["k"]), "observed": {}, "naive": {}}
        for s in series}
    reproduced: List[bool] = []
    for variant in VARIANTS:
        obs = observed_counts(series, variant)
        naive = naive_counts(series, variant)
        reproduced += [o["reproduced"] for o in obs if o["reproduced"] is not None]
        for o, nv in zip(obs, naive):
            per_series[o["company_id"]]["observed"][variant] = {k: o[k] for k in ("tp", "fp", "fn")}
            per_series[o["company_id"]]["naive"][variant] = {k: nv[k] for k in ("tp", "fp", "fn", "dates")}
        extra_fp = sum(s["k"][variant] for s in series if not s["annotated"])
        rules = ["bewertete_monate"] + (["wie_pelt"] if variant == VARIANTS[0] else [])
        draws_by: Dict[Tuple[str, str], Tuple[List[Counts], int]] = {}
        for rule in rules:
            edge, gap = POSITION_RULES[rule]
            for directions in DIRECTIONS:
                rng = make_rng(seed, f"zufall/{variant}/{directions}/{rule}")
                draws_by[(rule, directions)] = random_baseline(series, variant, draws, rng, directions, edge, gap)
        for scope in SCOPES:
            sel = [i for i, s in enumerate(series) if scope == "regelkonform" or s["annotated"]]
            scope_extra = extra_fp if scope == "regelkonform" else 0
            obs_counts = sum_counts(obs[i] for i in sel)
            observed = describe(obs_counts)
            observed_f1 = ed.metrics(*obs_counts)["f1"] or 0.0
            boot = cluster_bootstrap([(obs[i]["tp"], obs[i]["fp"], obs[i]["fn"]) for i in sel], boot_draws,
                                     make_rng(seed, f"bootstrap/{scope}/{variant}"))
            entry = {
                "n_series": len(sel),
                "n_annotations": sum(len(series[i]["annotations"]) for i in sel),
                "n_markers": sum(series[i]["k"][variant] for i in sel),
                "observed": observed,
                "bootstrap": boot,
                "random": {},
                "naive": describe(sum_counts(naive[i] for i in sel)),
            }
            for rule in rules:
                target = entry["random"] if rule == "bewertete_monate" else sensitivity[scope].setdefault(variant, {})
                for directions in DIRECTIONS:
                    counts, short = draws_by[(rule, directions)]
                    summary = summarize_draws(counts, observed_f1, scope_extra)
                    summary["draws_with_fewer_markers"] = short
                    target[directions] = summary
            results[scope][variant] = entry
    return {"results": results, "sensitivity_wie_pelt": sensitivity,
            "series": [per_series[s["company_id"]] for s in series],
            "reproduced_all": all(reproduced) if reproduced else False}


# ── Bericht ──────────────────────────────────────────────────────────────────

def _f(value: Optional[float], digits: int = 2) -> str:
    return "–" if value is None else f"{value:.{digits}f}".replace(".", ",")


def _iv(iv: Optional[Sequence[Optional[float]]]) -> str:
    return "–" if not iv else f"[{_f(iv[0])}; {_f(iv[1])}]"


def _random_line(label: str, s: Dict[str, Any]) -> str:
    return (f"    {label:<34} F1 Mittel {_f(s['f1_mean'], 3)}, Median {_f(s['f1_median'], 3)}, "
            f"95. P. {_f(s['f1_p95'], 3)}, 99. P. {_f(s['f1_p99'], 3)}, max {_f(s['f1_max'], 3)}; "
            f"TP Mittel {_f(s['tp_mean'])}; F1 ≥ beobachtet {s['n_ge_observed']}/{s['draws']}")


def format_report(report: Dict[str, Any]) -> str:
    p = report["params"]
    lines = [
        "Bezugsgrößen und Unsicherheit für den DZ1-Wert (E9, E5 Regel 6) – offline, nachträglich",
        f"  Seed {p['seed']}, {p['draws']} Ziehungen Zufall, {p['bootstrap_draws']} Ziehungen Bootstrap; "
        "Abgleich mit evaluate_detection.match_series (Regel 6 unverändert).",
    ]
    for c in report["checks"]:
        lines.append(f"  Prüfung {c['name']}: {'in Ordnung' if c['ok'] else 'FEHLER'} – {c['detail']}")
    titles = {"hauptwert": "Hauptwert (annotierte Reihen wie im DZ1-Lauf)",
              "regelkonform": "Regelkonform (alle geeigneten Reihen; Markierungen ohne Eintrag als FP)"}
    for scope in SCOPES:
        for variant in VARIANTS:
            e = report["results"][scope][variant]
            o = e["observed"]
            vt = "Niveauwechsel allein" if variant == VARIANTS[0] else "Niveauwechsel und Einzelmonate"
            lines += ["", f"  {titles[scope]} – {vt}: {e['n_series']} Reihen, {e['n_annotations']} Zeiträume, "
                          f"{e['n_markers']} Markierungen"]
            lines.append(f"    beobachtet: TP {o['tp']}, FP {o['fp']}, FN {o['fn']}; Precision {_f(o['precision'])} "
                         f"{_iv(o['precision_wilson95'])}, Recall {_f(o['recall'])} {_iv(o['recall_wilson95'])} "
                         f"(Wilson 95 %), F1 {_f(o['f1'])}")
            b = e["bootstrap"]
            lines.append(f"    Cluster-Bootstrap über {b['n_series']} Reihen: F1 95 % {_iv(b['f1_interval95'])}, "
                         f"Median {_f(b['f1_median'])}" + (f", {b['undefined']} Ziehungen ohne F1" if b["undefined"] else ""))
            lines.append(_random_line("Zufall, Richtung 50/50:", e["random"][DIRECTIONS[0]]))
            lines.append(_random_line("Zufall, Richtung aus Vorniveau:", e["random"][DIRECTIONS[1]]))
            nv = e["naive"]
            lines.append(f"    Naive Top-k-Regel (|Monat − Vorniveau|): TP {nv['tp']}, FP {nv['fp']}, FN {nv['fn']}; "
                         f"F1 {_f(nv['f1'])}")
    lines += ["", "  Sensitivität: Zufall mit Rand und Abstand 3 bewertete Monate (wie min_size, Regel des Prüfskripts), "
                  "Niveauwechsel allein"]
    for scope in SCOPES:
        sens = report["sensitivity_wie_pelt"][scope][VARIANTS[0]]
        lines.append(f"  {titles[scope]}")
        lines.append(_random_line("Zufall, Richtung 50/50:", sens[DIRECTIONS[0]]))
        lines.append(_random_line("Zufall, Richtung aus Vorniveau:", sens[DIRECTIONS[1]]))
    lines += ["", f"  {'Reihe':<32}{'Mon.':>5}{'Ann':>4}{'k NW':>5}{'k +E':>5}{'beob. NW':>10}{'naiv NW':>10}"]
    for s in report["series"]:
        o, nv = s["observed"][VARIANTS[0]], s["naive"][VARIANTS[0]]
        obs_s = "{tp}/{fp}/{fn}".format(**o)
        naive_s = "{tp}/{fp}/{fn}".format(**nv)
        lines.append(f"  {s['company'][:32]:<32}{s['evaluated_months']:>5}{s['n_annotations']:>4}"
                     f"{s['markers'][VARIANTS[0]]:>5}{s['markers'][VARIANTS[1]]:>5}{obs_s:>10}{naive_s:>10}")
    lines.append("  k NW / k +E: Markierungen der Erkennung (Niveauwechsel / mit Einzelmonaten); beob./naiv: TP/FP/FN.")
    lines.append("  Lesart: Bezugsgrößen nachträglich, nicht vorab festgelegt; die naive Regel nutzt dasselbe Vorniveau "
                 "wie die Referenzregel (Regel 4) und ist keine unabhängige Bezugsgröße.")
    return "\n".join(lines)


# ── Dateien und Herkunft ─────────────────────────────────────────────────────

def file_sha256(path: str) -> str:
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def entries_sha256(ann_doc: Dict[str, Any]) -> str:
    """SHA-256 über die Einträge (ohne ``hinweise``), kanonisch serialisiert."""
    blob = json.dumps(ann_doc.get("annotations") or [], ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def _git(*args: str) -> Optional[str]:
    try:
        return subprocess.run(["git", *args], cwd=BACKEND_DIR, capture_output=True, text=True, check=True).stdout
    except (OSError, subprocess.CalledProcessError):
        return None


def git_state() -> Dict[str, Any]:
    """Commit und uncommittete Änderungen unter backend/."""
    commit = _git("rev-parse", "HEAD")
    status = _git("status", "--porcelain", "--", ".")
    paths = [line[3:] for line in (status or "").splitlines() if line.strip()]
    return {"commit": commit.strip() if commit else None,
            "dirty": bool(paths) if status is not None else None, "dirty_paths": paths[:50]}


def _rel(path: str) -> str:
    return os.path.relpath(os.path.abspath(path), BACKEND_DIR)


def find_series_csvs(series_dir: str, source: str = SOURCE) -> Dict[int, str]:
    """Serien-CSVs je ``company_id`` (Dateiname ``<id>_<slug>_<source>.csv``)."""
    out: Dict[int, str] = {}
    for path in sorted(glob.glob(os.path.join(series_dir, f"*_{source}.csv"))):
        head = os.path.basename(path).split("_", 1)[0]
        if head.isdigit():
            out[int(head)] = path
    return out


def load_inputs(dz1_path: str = DEFAULT_DZ1, ann_path: str = DEFAULT_ANNOTATIONS, semi_path: str = DEFAULT_SEMI,
                series_dir: str = DEFAULT_SERIES_DIR) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
    """Eingabedateien lesen; Reihen, Prüfungen und Herkunft der Eingaben."""
    docs = {}
    for key, path, what in (("dz1", dz1_path, "DZ1-Ergebnis"), ("ann", ann_path, "Annotationsdatei"),
                            ("semi", semi_path, "Ergebnis der Simulation")):
        doc, err = va._load_json(path, what)
        if err:
            raise SystemExit(f"FEHLER: {err}")
        docs[key] = doc
    csv_paths = find_series_csvs(series_dir)
    csv_rows: Dict[int, List[Tuple[str, Optional[float], int]]] = {}
    for cid, path in csv_paths.items():
        with open(path, encoding="utf-8", newline="") as fh:
            csv_rows[cid] = parse_series_csv(fh)
    eval_counts_all = {cid: len(evaluated_of(rows)) for cid, rows in csv_rows.items()}
    series, checks = build_inputs(docs["dz1"], docs["ann"], docs["semi"], csv_rows, eval_counts_all)
    used = {s["company_id"] for s in series}
    inputs = {
        "dz1_ergebnis": {"path": _rel(dz1_path), "sha256": file_sha256(dz1_path),
                         "generated_at": docs["dz1"].get("generated_at"),
                         "annotations_version": docs["dz1"].get("annotations_version")},
        "annotations": {"path": _rel(ann_path), "sha256": file_sha256(ann_path), "version": docs["ann"].get("version"),
                        "n_entries": len(docs["ann"].get("annotations") or []),
                        "entries_sha256": entries_sha256(docs["ann"])},
        "semisynthetisch": {"path": _rel(semi_path), "sha256": file_sha256(semi_path),
                            "generated_at": docs["semi"].get("generated_at"),
                            "git_commit": (docs["semi"].get("git") or {}).get("commit")},
        "series_csv": [{"company_id": cid, "path": _rel(path), "sha256": file_sha256(path), "used": cid in used}
                       for cid, path in sorted(csv_paths.items())],
    }
    return series, checks, inputs


# ── CLI ──────────────────────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument("--draws", type=int, default=DRAWS, help=f"Ziehungen der Zufalls-Bezugsgrößen (Standard {DRAWS})")
    parser.add_argument("--bootstrap", type=int, default=BOOTSTRAP, help=f"Ziehungen des Bootstrap (Standard {BOOTSTRAP})")
    parser.add_argument("--dz1", default=DEFAULT_DZ1, help="DZ1-Ergebnis (dz1_ergebnis.json)")
    parser.add_argument("--annotations", default=DEFAULT_ANNOTATIONS, help="annotations.json")
    parser.add_argument("--semi", default=DEFAULT_SEMI, help="Ergebnis der semi-synthetischen Prüfung (E30)")
    parser.add_argument("--series-dir", default=DEFAULT_SERIES_DIR, help="Serien-CSVs")
    parser.add_argument("--json", dest="json_out", help="Ergebnis zusätzlich als JSON-Datei schreiben")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.draws < 1 or args.bootstrap < 1:
        parser.error("--draws und --bootstrap müssen mindestens 1 sein.")
    if args.seed < 0:
        parser.error("--seed muss ≥ 0 sein.")
    series, checks, inputs = load_inputs(args.dz1, args.annotations, args.semi, args.series_dir)
    computed = compute(series, args.seed, args.draws, args.bootstrap)
    checks.append(_check("abgleich_reproduziert", [] if computed["reproduced_all"] else
                         ["Neuabgleich der annotierten Reihen weicht von dz1_ergebnis.json ab"],
                         "Neuabgleich mit match_series ergibt je Reihe und Variante dieselben TP/FP/FN wie dz1_ergebnis.json"))
    with open(os.path.abspath(__file__), "rb") as fh:
        script_sha = hashlib.sha256(fh.read()).hexdigest()
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "argv": list(argv) if argv is not None else sys.argv[1:],
        "provenance": {
            "git": git_state(),
            "script_sha256": script_sha,
            "evaluate_detection_sha256": file_sha256(os.path.join(BACKEND_DIR, "scripts", "evaluate_detection.py")),
            "python": platform.python_version(),
            "platform": platform.platform(),
            "inputs": inputs,
        },
        "params": {
            "seed": args.seed, "draws": args.draws, "bootstrap_draws": args.bootstrap,
            "rng": "random.Random(f'{seed}/{Bezeichnung}') je Teil (Zufall je Variante, Richtung, Lage; Bootstrap je Bezugsmenge, Variante)",
            "source": SOURCE, "dimension": DIMENSION, "min_reviews_per_month": MIN_REVIEWS_PER_MONTH,
            "rules": {"tolerance_months": ed.TOLERANCE_MONTHS, "max_shift_months": ed.MAX_SHIFT_MONTHS,
                      "same_direction": True, "one_to_one": True, "function": "evaluate_detection.match_series"},
            "scopes": {"hauptwert": "annotierte Reihen wie im DZ1-Lauf",
                       "regelkonform": "alle geeigneten Reihen (E4); Markierungen in Reihen ohne Eintrag zählen als FP"},
            "random": {
                "markers": "je Reihe so viele wie die Erkennung in der Variante",
                "positions": {"bewertete_monate": "gleichverteilt auf die bewerteten Monate ohne Doppelung",
                              "wie_pelt": f"mindestens {PELT_EDGE} bewertete Monate davor und ab der Stelle, "
                                          f"Abstand mindestens {PELT_GAP} (Regel des Prüfskripts; nur Niveauwechsel)"},
                "directions": {DIRECTIONS[0]: "Münzwurf je Markierung",
                               DIRECTIONS[1]: f"rise, wenn Monatsmittel ≥ Mittel der bis zu {PRIOR_WIDTH} vorangehenden "
                                              "bewerteten Monate, sonst fall; ohne Vorniveau Münzwurf"},
                "regelkonform": "Markierungen der Reihen ohne Eintrag als feste Zahl FP addiert",
            },
            "naive": (f"je Reihe die k Stellen mit größtem |Monatsmittel − Mittel der bis zu {PRIOR_WIDTH} vorangehenden "
                      f"bewerteten Monate|, Stellen mit mindestens {PELT_EDGE} bewerteten Monaten davor und ab der Stelle, "
                      f"absteigend nach (Betrag, Index, Richtung), gierig mit Abstand ≥ {PELT_GAP}; k wie die Erkennung; "
                      "Richtung rise, wenn Monatsmittel > Vorniveau"),
            "percentile": "Rang ⌊q·N⌋ der aufsteigend sortierten Werte (0-basiert, ohne Interpolation)",
            "wilson_z": WILSON_Z,
            "bootstrap": "Reihen mit Zurücklegen, TP/FP/FN summiert, F1; Ziehungen ohne definierten F1 nicht gewertet",
            "status": "nachträglich gewählt, nicht vorab festgelegt; kalibriert nichts (E5, E9, E30)",
        },
        "checks": checks,
        **{k: computed[k] for k in ("results", "sensitivity_wie_pelt", "series")},
    }
    print(format_report(report))
    if not all(c["ok"] for c in checks):
        print("\nAbbruch: mindestens eine Konsistenzprüfung ist fehlgeschlagen; keine JSON-Ausgabe.")
        return 1
    if args.json_out:
        os.makedirs(os.path.dirname(os.path.abspath(args.json_out)), exist_ok=True)
        with open(args.json_out, "w", encoding="utf-8") as fh:
            json.dump(report, fh, ensure_ascii=False, indent=2)
            fh.write("\n")
        print(f"\nErgebnis gespeichert: {args.json_out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
