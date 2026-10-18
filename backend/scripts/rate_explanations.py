"""
Bewertung der Erklärungsansätze je Anomalie (DZ2, Ergänzung zu E23): Passung und Unterschied.

Zwei Fragen an die Erklärungsansätze (Inkrement 5, E21–E23), die der Bericht
``report_explanation_validity.py`` offenlässt:

1. **Passung:** Wie gut passt der einzelne Erklärungsansatz zu der Veränderung, zu der er
   steht? Das beurteilt eine bewertende Instanz (Agent oder Person) **blind**: Sie sieht
   je Fenster das Unternehmen, die Fensterart, die Monate, die Richtung der Veränderung in
   den Bewertungen, die kennzeichnenden Begriffe, die verschobenen Themen und die obersten
   Erklärungsansätze mit Titel, Datum, Herausgeber, Signalen, Stufe und Begründungstext,
   aber nicht, ob das Fenster eine Markierung trägt oder ein verschobenes Vergleichsfenster
   ist (E18). Die Zuordnung steht getrennt im Schlüssel. Bewertet wird auf einer Skala von
   0 bis 3 (``PASSUNG_SCALE``) mit Begründung in eigenen Worten.
2. **Unterschied:** Unterscheiden die Erklärungsansätze Markierungsfenster von
   Vergleichsfenstern, und zwar nicht nur „in derselben Größenordnung“ (E23), sondern mit
   Konfidenzintervall und Test? Gerechnet werden der exakte Test nach Fisher, ein
   Konfidenzintervall nach Newcombe für die Differenz der Anteile und ein
   Permutationstest, der die Abhängigkeit zwischen einer Markierung und ihren bis zu drei
   Vergleichsfenstern berücksichtigt (die Markierung wird innerhalb ihres Clusters
   zufällig neu vergeben). Dazu die kleinste Differenz, die mit diesen Fallzahlen
   überhaupt nachweisbar wäre (Teststärke 80 %). Dasselbe für die blinden
   Passungsurteile, sobald sie vorliegen, und der Zusammenhang zwischen Stufe und
   Passung (Rangkorrelation nach Spearman mit Permutationstest).

Drei Unterbefehle:

    cd backend
    uv run python scripts/rate_explanations.py bogen --out-dir data/bewertungsbogen/2026-10-17
        # Bewertungsbogen (blind) + Schlüssel + Vorlage für die Urteile; braucht Datenbank
        # und Belegspeicher, kein Abruf, keine Stimmung
    uv run python scripts/rate_explanations.py pruefen --bogen <bogen.json> --ratings <bewertungen.json>
        # Vollständigkeit und Wertebereich der Urteile, ohne den Schlüssel zu öffnen
    uv run python scripts/rate_explanations.py auswerten --validity data/calibration/explanation_validity_korrektur_2026-10-13.json \\
        [--bogen <bogen.json> --key <schluessel.json> --ratings <bewertungen.json>] --json <out.json> --md <out.md>
        # Teil A: Tests auf den Stufen des vorhandenen Berichts (ohne Datenbank);
        # Teil B: Entblindung und Tests auf den Passungsurteilen

Der Bogen enthält Titel und Links der Meldungen und bleibt außerhalb des Repositories
(``backend/data/bewertungsbogen/`` in ``.gitignore``); die Auswertung nennt keine Titel.
Das Skript ändert keine Schwelle, keine Stufenregel und keine Datei des Berichts; es
liest nur. Alle Zahlen sind beschreibend oder Tests gegen die Nullhypothese „kein
Unterschied“; ein Unterschied oder dessen Fehlen sagt nichts über Ursachen.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import random
import sys
from datetime import datetime, timezone
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Tuple

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND_DIR)
sys.path.insert(0, os.path.join(BACKEND_DIR, "scripts"))

import report_explanation_validity as rev  # noqa: E402

DEFAULT_VALIDITY = os.path.join(BACKEND_DIR, "data", "calibration", "explanation_validity_korrektur_2026-10-13.json")
DEFAULT_SHEET_DIR = os.path.join(BACKEND_DIR, "data", "bewertungsbogen")
DEFAULT_TOP = 3                 # oberste Erklärungsansätze je Fenster im Bogen
DEFAULT_SEED = 20261017         # Reihenfolge der Fenster im Bogen und Permutationen
DEFAULT_PERMUTATIONS = 20000
MAX_TERMS_IN_SHEET = 10
MAX_TOPICS_IN_SHEET = 5
ALPHA = 0.05
POWER = 0.8
Z_ALPHA = 1.959964              # zweiseitig, 5 %
Z_POWER = 0.841621              # Teststärke 80 %

PASSUNG_SCALE: Dict[int, str] = {
    0: "nicht passend",
    1: "kaum passend",
    2: "teilweise passend",
    3: "passend",
}
PASSUNG_RULES: Dict[int, str] = {
    3: ("Die Meldung betrifft erkennbar dieses Unternehmen als Arbeitgeber (Personalabbau, Führungswechsel, Übernahme, "
        "Tarif und Streik, Standort, Vergütung, Arbeitsmodell, Kultur, Krise mit Belegschaftsbezug), liegt vor oder im "
        "Übergang und passt in ihrer Stoßrichtung zur Richtung der Veränderung, oder ein kennzeichnender Begriff der "
        "Bewertungen benennt dasselbe Ereignis."),
    2: ("Arbeitgeberbezug und richtiges Unternehmen, aber Richtung neutral oder unklar, Meldung erst nach dem markierten "
        "Monat, oder nur allgemeiner Bezug (Konzernumbau ohne Belegschaftsbezug, mehrdeutiger Wortbezug)."),
    1: ("Kein Arbeitgeberbezug (Produkt, Kurs, Sport, Kapitalmarkt), Treffer durch ein mehrdeutiges Schlüsselwort oder "
        "einen mehrdeutigen Begriff, oder das Unternehmen ist nur am Rand erwähnt."),
    0: ("Anderes Unternehmen (fremder Treffer des Suchbegriffs), kein Bezug zur Belegschaft und kein Begriff, oder die "
        "Meldung liegt außerhalb jeder sinnvollen zeitlichen Lage zur Veränderung."),
}
RICHTUNG_VALUES = ("passt", "neutral", "widerspricht", "unklar")
FIT_THRESHOLD = 2               # Passung >= 2 gilt als „passend oder teilweise passend“

STAGE_SCORE = {"hoch": 3, "mittel": 2, "niedrig": 1}
GROUP_MARKER, GROUP_COMPARISON = rev.GROUP_MARKER, rev.GROUP_COMPARISON
DIRECTION_WORDS = {"fall": "Abfall", "rise": "Anstieg", "unklar": "unklar"}
NOTE = ("Beschreibende Zahlen und Tests gegen die Nullhypothese 'kein Unterschied'. Ein Unterschied oder dessen Fehlen "
        "sagt nichts über Ursachen; ein Erklärungsansatz bleibt ein möglicher Zusammenhang. Die Passungsurteile stammen "
        "von einer bewertenden Instanz (Agent oder Person), die den Bogen blind gelesen hat; die Verblindung ist "
        "unvollständig, weil Unternehmen, Monate und Richtung sichtbar sind.")


# ═════════════════════════════════════════════════════════════════════════════
# Statistik (reine Funktionen)
# ═════════════════════════════════════════════════════════════════════════════

def fisher_exact(a: int, b: int, c: int, d: int) -> Optional[float]:
    """Zweiseitiger exakter Test nach Fisher für die Vierfeldertafel ``[[a, b], [c, d]]``
    (Zeilen: Gruppen, Spalten: Merkmal ja/nein). Summe der Wahrscheinlichkeiten aller
    Tafeln mit denselben Randsummen, die höchstens so wahrscheinlich sind wie die
    beobachtete (wie ``scipy.stats.fisher_exact``). None bei leerer Tafel."""
    r1, r2, c1 = a + b, c + d, a + c
    n = r1 + r2
    if n == 0 or r1 == 0 or r2 == 0 or c1 == 0 or c1 == n:
        return None if n == 0 else 1.0
    lo, hi = max(0, c1 - r2), min(r1, c1)
    weights = {k: math.comb(r1, k) * math.comb(r2, c1 - k) for k in range(lo, hi + 1)}
    total = sum(weights.values())
    observed = weights[a]
    return round(sum(w for w in weights.values() if w <= observed) / total, 10)


def wilson_interval(k: int, n: int, z: float = Z_ALPHA) -> Tuple[Optional[float], Optional[float]]:
    """Wilson-Intervall für einen Anteil (Standard 95 %)."""
    if n <= 0:
        return None, None
    p = k / n
    denom = 1 + z * z / n
    centre = p + z * z / (2 * n)
    adj = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (centre - adj) / denom, (centre + adj) / denom


def newcombe_interval(k1: int, n1: int, k2: int, n2: int, z: float = Z_ALPHA) -> Tuple[Optional[float], Optional[float]]:
    """Konfidenzintervall nach Newcombe (Methode 10) für die Differenz ``k1/n1 − k2/n2``."""
    if n1 <= 0 or n2 <= 0:
        return None, None
    p1, p2 = k1 / n1, k2 / n2
    l1, u1 = wilson_interval(k1, n1, z)
    l2, u2 = wilson_interval(k2, n2, z)
    d = p1 - p2
    return (d - math.sqrt((p1 - l1) ** 2 + (u2 - p2) ** 2), d + math.sqrt((u1 - p1) ** 2 + (p2 - l2) ** 2))


def min_detectable_difference(n1: int, n2: int, p2: float, alpha_z: float = Z_ALPHA, power_z: float = Z_POWER) -> Dict[str, Optional[float]]:
    """Kleinster Anteil ``p1`` über und größter unter ``p2``, der mit ``n1`` gegen ``n2`` Fenstern
    bei zweiseitigem Niveau 5 % und Teststärke 80 % noch nachweisbar wäre (Normalnäherung für
    zwei Anteile). Antwort auf die Frage, welche Unterschiede dieser Datenbestand überhaupt
    zeigen könnte."""
    if n1 <= 0 or n2 <= 0 or p2 is None:
        return {"above": None, "below": None}
    above: Optional[float] = None
    below: Optional[float] = None
    needed = alpha_z + power_z
    for step in range(1, 1000):
        p1 = step / 1000
        se = math.sqrt(p1 * (1 - p1) / n1 + p2 * (1 - p2) / n2)
        if se == 0:
            continue
        if abs(p1 - p2) / se >= needed:
            if p1 > p2 and above is None:
                above = p1
            if p1 < p2:
                below = p1
    return {"above": above, "below": below}


def _mean(values: Sequence[float]) -> Optional[float]:
    return round(sum(values) / len(values), 4) if values else None


def cluster_permutation_test(clusters: List[List[float]], n_perm: int = DEFAULT_PERMUTATIONS, seed: int = DEFAULT_SEED) -> Dict[str, Any]:
    """Permutationstest für den Unterschied der Mittelwerte zwischen Markierungen und ihren
    Vergleichsfenstern. ``clusters``: je Markierung eine Liste, erster Wert die Markierung,
    danach ihre Vergleichsfenster. Unter der Nullhypothese ist innerhalb eines Clusters jedes
    Fenster gleich wahrscheinlich das Markierungsfenster; der Test vergibt die Rolle
    ``n_perm`` Mal zufällig neu. Cluster mit nur einem Fenster bleiben fest. Zweiseitiger
    p-Wert mit Korrektur (Treffer + 1) / (Permutationen + 1). Zusätzlich die gepaarte Sicht:
    Markierung minus Mittel ihrer Vergleichsfenster je Cluster."""
    markers = [c[0] for c in clusters if c]
    comparisons = [v for c in clusters for v in c[1:]]
    out: Dict[str, Any] = {"n_clusters": len(markers), "n_markers": len(markers), "n_comparisons": len(comparisons),
                           "mean_markers": _mean(markers), "mean_comparisons": _mean(comparisons),
                           "observed_diff": None, "p_value": None, "n_permutations": 0,
                           "paired": {"n_pairs": 0, "mean_diff": None, "marker_higher": 0, "equal": 0, "marker_lower": 0}}
    if not markers or not comparisons:
        return out
    # Beobachtete Statistik ungerundet: Permutationen, die genau den beobachteten Wert
    # treffen, zählen mit (sonst fiele bei kleinen Clustern die Hälfte der Masse weg).
    observed = sum(markers) / len(markers) - sum(comparisons) / len(comparisons)
    out["observed_diff"] = round(observed, 4)
    pairs = [(c[0], sum(c[1:]) / len(c[1:])) for c in clusters if len(c) > 1]
    diffs = [m - c for m, c in pairs]
    out["paired"] = {"n_pairs": len(pairs), "mean_diff": _mean(diffs),
                     "marker_higher": sum(1 for d in diffs if d > 1e-12), "equal": sum(1 for d in diffs if abs(d) <= 1e-12),
                     "marker_lower": sum(1 for d in diffs if d < -1e-12)}
    movable = [c for c in clusters if len(c) > 1]
    if not movable or n_perm <= 0:
        return out
    fixed_sum = sum(c[0] for c in clusters if len(c) == 1)
    total_sum = sum(v for c in clusters for v in c)
    n_m, n_c = len(markers), len(comparisons)
    rng = random.Random(seed)
    hits = 0
    threshold = abs(observed) - 1e-9
    for _ in range(n_perm):
        marker_sum = fixed_sum
        for c in movable:
            marker_sum += c[rng.randrange(len(c))]
        diff = marker_sum / n_m - (total_sum - marker_sum) / n_c
        if abs(diff) >= threshold:
            hits += 1
    out["p_value"] = round((hits + 1) / (n_perm + 1), 4)
    out["n_permutations"] = n_perm
    return out


def _ranks(values: Sequence[float]) -> List[float]:
    order = sorted(range(len(values)), key=lambda i: values[i])
    ranks = [0.0] * len(values)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and values[order[j + 1]] == values[order[i]]:
            j += 1
        rank = (i + j) / 2 + 1
        for k in range(i, j + 1):
            ranks[order[k]] = rank
        i = j + 1
    return ranks


def _pearson(x: Sequence[float], y: Sequence[float]) -> Optional[float]:
    n = len(x)
    if n < 3:
        return None
    mx, my = sum(x) / n, sum(y) / n
    sxx = sum((a - mx) ** 2 for a in x)
    syy = sum((b - my) ** 2 for b in y)
    if sxx == 0 or syy == 0:
        return None
    return sum((a - mx) * (b - my) for a, b in zip(x, y)) / math.sqrt(sxx * syy)


def spearman(x: Sequence[float], y: Sequence[float], n_perm: int = DEFAULT_PERMUTATIONS, seed: int = DEFAULT_SEED) -> Dict[str, Any]:
    """Rangkorrelation nach Spearman (Bindungen als Mittelrang) mit zweiseitigem
    Permutationstest (``y`` wird gemischt). ``rho`` None bei weniger als drei Paaren oder
    ohne Streuung."""
    if len(x) != len(y):
        raise ValueError("x und y müssen gleich lang sein.")
    rx, ry = _ranks(x), _ranks(y)
    rho = _pearson(rx, ry)
    out: Dict[str, Any] = {"n": len(x), "rho": None if rho is None else round(rho, 4), "p_value": None, "n_permutations": 0}
    if rho is None or n_perm <= 0:
        return out
    rng = random.Random(seed)
    shuffled = list(ry)
    hits = 0
    threshold = abs(rho) - 1e-9
    for _ in range(n_perm):
        rng.shuffle(shuffled)
        r = _pearson(rx, shuffled)
        if r is not None and abs(r) >= threshold:
            hits += 1
    out["p_value"] = round((hits + 1) / (n_perm + 1), 4)
    out["n_permutations"] = n_perm
    return out


def compare_binary(clusters: List[List[int]], n_perm: int = DEFAULT_PERMUTATIONS, seed: int = DEFAULT_SEED) -> Dict[str, Any]:
    """Markierungen gegen Vergleichsfenster für ein Ja/Nein-Merkmal: Anteile, Differenz mit
    Newcombe-Intervall, exakter Test nach Fisher (Fenster als unabhängig behandelt) und
    Permutationstest innerhalb der Cluster (Abhängigkeit berücksichtigt), kleinste
    nachweisbare Differenz."""
    markers = [int(round(c[0])) for c in clusters if c]
    comparisons = [int(round(v)) for c in clusters for v in c[1:]]
    if any(v not in (0, 1) for v in markers + comparisons):
        raise ValueError("compare_binary erwartet Werte 0 oder 1.")
    k1, n1, k2, n2 = sum(markers), len(markers), sum(comparisons), len(comparisons)
    lo, hi = newcombe_interval(k1, n1, k2, n2)
    perm = cluster_permutation_test([[float(v) for v in c] for c in clusters], n_perm, seed)
    p2 = k2 / n2 if n2 else None
    return {
        "markers": {"k": k1, "n": n1, "share": round(k1 / n1, 4) if n1 else None},
        "comparisons": {"k": k2, "n": n2, "share": round(k2 / n2, 4) if n2 else None},
        "diff": round(k1 / n1 - k2 / n2, 4) if n1 and n2 else None,
        "ci95": [None if lo is None else round(lo, 4), None if hi is None else round(hi, 4)],
        "fisher_p": fisher_exact(k1, n1 - k1, k2, n2 - k2) if n1 and n2 else None,
        "permutation": perm,
        "min_detectable": min_detectable_difference(n1, n2, p2) if p2 is not None else {"above": None, "below": None},
    }


def compare_means(clusters: List[List[float]], n_perm: int = DEFAULT_PERMUTATIONS, seed: int = DEFAULT_SEED) -> Dict[str, Any]:
    """Markierungen gegen Vergleichsfenster für ein Merkmal mit Stufen (0 bis 3): Mittelwerte
    und Permutationstest innerhalb der Cluster."""
    perm = cluster_permutation_test(clusters, n_perm, seed)
    markers = [c[0] for c in clusters if c]
    comparisons = [v for c in clusters for v in c[1:]]
    return {
        "markers": {"n": len(markers), "mean": _mean(markers), "distribution": _distribution(markers)},
        "comparisons": {"n": len(comparisons), "mean": _mean(comparisons), "distribution": _distribution(comparisons)},
        "diff": perm["observed_diff"],
        "permutation": perm,
    }


def _distribution(values: Iterable[float]) -> Dict[str, int]:
    out: Dict[str, int] = {}
    for v in values:
        key = str(int(v)) if float(v).is_integer() else str(v)
        out[key] = out.get(key, 0) + 1
    return dict(sorted(out.items(), key=lambda kv: kv[0]))


# ═════════════════════════════════════════════════════════════════════════════
# Teil A: Tests auf den Stufen eines vorhandenen Berichts (ohne Datenbank)
# ═════════════════════════════════════════════════════════════════════════════

def cluster_key(window: Dict[str, Any]) -> Tuple[str, str, str]:
    return (str(window.get("company")), str(window.get("kind")), str(window.get("date")))


def build_clusters(windows: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
    """Fenster nach Markierung gruppieren: je Cluster die Markierung zuerst, dann ihre
    Vergleichsfenster. Cluster ohne Markierung oder mit mehr als einer werden übersprungen
    (Datenfehler; im Bericht genannt)."""
    groups: Dict[Tuple[str, str, str], List[Dict[str, Any]]] = {}
    for w in windows:
        groups.setdefault(cluster_key(w), []).append(w)
    clusters = []
    for members in groups.values():
        markers = [w for w in members if w.get("group") == GROUP_MARKER]
        if len(markers) != 1:
            continue
        clusters.append(markers + [w for w in members if w.get("group") == GROUP_COMPARISON])
    return clusters


def stage_score(top_stage: Optional[str]) -> int:
    return STAGE_SCORE.get(top_stage or "", 0)


STAGE_METRICS: Dict[str, Tuple[str, Callable[[Dict[str, Any]], int]]] = {
    "mit_ansatz": ("mindestens ein Ansatz (Stufe mindestens niedrig)", lambda w: 1 if w.get("state") == "ansaetze" else 0),
    "mindestens_mittel": ("oberste Stufe mindestens mittel", lambda w: 1 if w.get("top_stage") in ("hoch", "mittel") else 0),
    "hoch": ("mindestens ein Bündel der Stufe hoch", lambda w: 1 if w.get("top_stage") == "hoch" else 0),
    "mit_begriffen": ("Fenster mit kennzeichnenden Begriffen", lambda w: 1 if int(w.get("n_terms") or 0) > 0 else 0),
}


def _complete(w: Dict[str, Any]) -> bool:
    return int(w.get("missing_months") or 0) == 0


def stage_tests(windows: List[Dict[str, Any]], n_perm: int = DEFAULT_PERMUTATIONS, seed: int = DEFAULT_SEED) -> Dict[str, Any]:
    """Teil A für eine Fensterliste eines Berichts: je Merkmal der Vergleich Markierung gegen
    Vergleichsfenster, gesamt und je Art der Markierung; oberste Stufe als Rangmerkmal;
    Referenztreffer gegen übrige Markierungen (nur Fisher, kleine Zahlen); Zusammenhang der
    Belegzahl mit der Stufe (Nullmodell des Gutachtens vom 2026-10-13)."""
    complete = [w for w in windows if _complete(w)]
    clusters = build_clusters(complete)
    skipped = len(complete) - sum(len(c) for c in clusters)

    def block(cs: List[List[Dict[str, Any]]]) -> Dict[str, Any]:
        out: Dict[str, Any] = {"n_markers": len(cs), "n_comparisons": sum(len(c) - 1 for c in cs), "binary": {}, "ordinal": None}
        for key, (label, fn) in STAGE_METRICS.items():
            out["binary"][key] = {"label": label, **compare_binary([[fn(w) for w in c] for c in cs], n_perm, seed)}
        out["ordinal"] = {"label": "oberste Stufe (offen 0, niedrig 1, mittel 2, hoch 3)",
                          **compare_means([[float(stage_score(w.get("top_stage"))) for w in c] for c in cs], n_perm, seed)}
        return out

    result: Dict[str, Any] = {
        "n_windows": len(windows), "n_complete": len(complete), "n_skipped_clusters_windows": skipped,
        "total": block(clusters),
        "by_kind": {kind: block([c for c in clusters if c[0].get("kind") == kind]) for kind in rev.KINDS},
    }
    markers = [c[0] for c in clusters]
    hits = [w for w in markers if w.get("reference_hit") is True]
    rest = [w for w in markers if w.get("reference_hit") is False]
    if hits or rest:
        ref: Dict[str, Any] = {"n_treffer": len(hits), "n_uebrige": len(rest), "binary": {}}
        for key, (label, fn) in STAGE_METRICS.items():
            k1, k2 = sum(fn(w) for w in hits), sum(fn(w) for w in rest)
            lo, hi = newcombe_interval(k1, len(hits), k2, len(rest))
            ref["binary"][key] = {"label": label, "treffer": {"k": k1, "n": len(hits)}, "uebrige": {"k": k2, "n": len(rest)},
                                  "diff": round(k1 / len(hits) - k2 / len(rest), 4) if hits and rest else None,
                                  "ci95": [None if lo is None else round(lo, 4), None if hi is None else round(hi, 4)],
                                  "fisher_p": fisher_exact(k1, len(hits) - k1, k2, len(rest) - k2) if hits and rest else None}
        result["reference"] = ref
    else:
        result["reference"] = None
    # Nullmodell: folgt die Stufe der Zahl der Belege? (alle vollständigen Fenster, beide Gruppen)
    n_items = [float(w.get("n_items") or 0) for w in complete]
    result["null_model"] = {
        "label": "Rangkorrelation Belege je Fenster mit oberster Stufe bzw. mit 'mit Ansatz' (alle vollständigen Fenster)",
        "items_vs_top_stage": spearman(n_items, [float(stage_score(w.get("top_stage"))) for w in complete], n_perm, seed),
        "items_vs_any": spearman(n_items, [1.0 if w.get("state") == "ansaetze" else 0.0 for w in complete], n_perm, seed),
        "by_items_tertile": _by_tertile(clusters),
    }
    return result


def _by_tertile(clusters: List[List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    """Anteil 'mit Ansatz' je Drittel der Belegzahl, getrennt nach Gruppe (Schichtung)."""
    windows = [w for c in clusters for w in c]
    if not windows:
        return []
    counts = sorted(int(w.get("n_items") or 0) for w in windows)
    cut1, cut2 = counts[len(counts) // 3], counts[(2 * len(counts)) // 3]
    bins = [("wenige", lambda n: n < cut1), ("mittel", lambda n: cut1 <= n < cut2), ("viele", lambda n: n >= cut2)]
    out = []
    for name, test in bins:
        rows = [w for w in windows if test(int(w.get("n_items") or 0))]
        m = [w for w in rows if w.get("group") == GROUP_MARKER]
        c = [w for w in rows if w.get("group") == GROUP_COMPARISON]
        out.append({"tertile": name, "items_range": [min((int(w.get('n_items') or 0) for w in rows), default=None),
                                                    max((int(w.get('n_items') or 0) for w in rows), default=None)],
                    "markers": {"k": sum(1 for w in m if w.get("state") == "ansaetze"), "n": len(m)},
                    "comparisons": {"k": sum(1 for w in c if w.get("state") == "ansaetze"), "n": len(c)}})
    return out


# ═════════════════════════════════════════════════════════════════════════════
# Bogen (blind) und Schlüssel
# ═════════════════════════════════════════════════════════════════════════════

def _mean_rating(rows: List[Dict[str, Any]]) -> Optional[float]:
    values = []
    for row in rows:
        v = row.get("durchschnittsbewertung")
        try:
            if v is not None:
                values.append(float(v))
        except (TypeError, ValueError):
            continue
    return round(sum(values) / len(values), 3) if values else None


def direction_from_rows(before_rows: List[Dict[str, Any]], after_rows: List[Dict[str, Any]]) -> Tuple[str, Optional[float]]:
    """Richtung der Veränderung in den Bewertungen aus dem Mittel der Gesamtnote beider
    Vergleichsfenster: ``fall``, ``rise`` oder ``unklar`` (kein Mittel oder Differenz 0).
    Für Markierungen und Vergleichsfenster gleich gerechnet, damit der Bogen blind bleibt."""
    before, after = _mean_rating(before_rows), _mean_rating(after_rows)
    if before is None or after is None:
        return "unklar", None
    shift = round(after - before, 3)
    if shift == 0:
        return "unklar", shift
    return ("fall" if shift < 0 else "rise"), shift


def _sheet_explanation(entry: Dict[str, Any]) -> Dict[str, Any]:
    category = entry.get("category") or None
    return {
        "rank": entry.get("rank"),
        "stage": entry.get("confidence"),
        "stage_label": entry.get("stage_label"),
        "signal_label": entry.get("signal_label"),
        "title": entry.get("event"),
        "date": entry.get("date"),
        "publisher": entry.get("source"),
        "source_type": entry.get("source_type"),
        "eqs_category": entry.get("eqs_category"),
        "language": entry.get("language"),
        "n_items": entry.get("n_items"),
        "publishers": entry.get("publishers") or [],
        "time_phrase": entry.get("time_phrase"),
        "time_match": entry.get("time_match"),
        "term_match": entry.get("term_match"),
        "category_match": (category or {}).get("match", 0.0) if category else 0.0,
        "category": None if not category else {"id": category.get("id"), "label": category.get("label"),
                                                "employer_related": category.get("employer_related"),
                                                "shifted_topics": category.get("shifted_topics") or []},
        "terms": [{"term": t.get("term"), "before": t.get("before"), "after": t.get("after"), "strong": bool(t.get("strong"))}
                  for t in entry.get("terms") or []],
        "company_in_title": entry.get("company_in_title"),
        "text": entry.get("text"),
        "url": entry.get("url"),
        "group": None if not entry.get("group") else {"label": entry["group"].get("label"), "n_bundles": entry["group"].get("n_bundles"),
                                                       "n_items": entry["group"].get("n_items")},
    }


def _sheet_window(info: Dict[str, Any], window: Dict[str, Any], kind: str, windows: Dict[str, Any], rows: List[Dict[str, Any]],
                  categories: List[Dict[str, Any]], exclude: set, top: int, strict: bool = True) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Ein Fenster für den Bogen (sichtbar) und seine verdeckten Angaben (Schlüssel). Dieselbe
    Rangfolge wie die Oberfläche und der Bericht: Belege nur aus dem Speicher, ohne Stimmung;
    die Wortwahl der Zeitangaben folgt der Art der Markierung, nicht der des Fensters, damit
    der Text eines Vergleichsfensters nicht verrät, dass es eines ist."""
    from services.explanation_ranking import rank_evidence, rules, topic_shift_table
    from services.review_terms import distinctive_terms

    by_window = rev.es.split_rows_by_window(rows, windows)
    evidence = rev.ev.evidence_for_window(info, window, live=False, events=[])
    terms = distinctive_terms(by_window["before"], by_window["after"], source=rev.SOURCE, exclude=exclude)
    topics = topic_shift_table(by_window["before"], by_window["after"], rev.SOURCE)
    ranked = rank_evidence(evidence["items"], window, terms=terms, topics=topics, exclude=exclude, categories=categories,
                           analyzer=None, kind=kind, max_explanations=max(top, 1), strict=strict,
                           title_words=info.get("title_words") or ())
    direction, shift = direction_from_rows(by_window["before"], by_window["after"])
    min_pp = rules()["topic_shift_min_pp"]
    shifted = [{"topic": t["topic"], "share_shift_pp": t["share_shift_pp"]} for t in topics
               if t["share_shift_pp"] is not None and not t["low_basis"] and abs(t["share_shift_pp"]) >= min_pp]
    missing = sum(int(s["missing"]) for s in evidence["sources"].values())
    visible = {
        "id": None,
        "company": info.get("name"),
        "kind": kind,
        "window": {k: window.get(k) for k in ("from", "to", "months", "transition_from", "anchor_from", "anchor_to")},
        "direction": direction,
        "reviews": {"before": {"from": windows["before"]["from"], "to": windows["before"]["to"], "n": len(by_window["before"])},
                    "after": {"from": windows["after"]["from"], "to": windows["after"]["to"], "n": len(by_window["after"])}},
        "low_basis": any(len(by_window[s]) < rev.es.LOW_BASIS_MIN_REVIEWS for s in ("before", "after")),
        "terms": [{"term": t["term"], "before": t["before"], "after": t["after"]} for t in terms[:MAX_TERMS_IN_SHEET]],
        "n_terms": len(terms),
        "shifted_topics": shifted[:MAX_TOPICS_IN_SHEET],
        "n_items": ranked["n_items"], "n_selected": ranked["n_selected"], "n_excluded": ranked["n_excluded"],
        "n_bundles": ranked["n_bundles"], "n_groups": ranked["n_groups"],
        "n_by_stage": ranked["n_by_stage"], "state": ranked["state"], "missing_months": missing,
        "explanations": [_sheet_explanation(e) for e in ranked["explanations"][:top]],
    }
    hidden = {"rating_shift": shift, "window_from": window["from"], "window_to": window["to"],
              "top_stage": ranked["explanations"][0]["confidence"] if ranked["explanations"] else None,
              "n_explanations": len(visible["explanations"])}
    return visible, hidden


def collect_windows(window_before: int = rev.ev.DEFAULT_WINDOW_BEFORE, window_after: int = rev.ev.DEFAULT_WINDOW_AFTER,
                    companies: Optional[List[Dict[str, Any]]] = None, top: int = DEFAULT_TOP, comparisons: str = "all",
                    reference: Optional[Dict[str, Any]] = None, verbose: bool = True,
                    strict: bool = True) -> List[Tuple[Dict[str, Any], Dict[str, Any]]]:
    """Alle Markierungs- und Vergleichsfenster der geeigneten Unternehmen als Paare
    (sichtbar, verdeckt), in der Reihenfolge der Datenbank (wird vor der Ausgabe gemischt).
    Nur lesend: Datenbank und Belegspeicher, kein Abruf. ``strict``: strenge Auswahl der
    Belege (E33, Standard seit 2026-10-18); False für die Fassung des Bogens vom 2026-10-17."""
    from services.event_categories import load_event_categories
    from services.review_terms import company_terms

    if comparisons not in ("all", "one", "none"):
        raise ValueError("comparisons muss all, one oder none sein.")
    out: List[Tuple[Dict[str, Any], Dict[str, Any]]] = []
    categories = load_event_categories()
    for company in companies if companies is not None else rev.list_companies():
        anchors = rev.company_anchors(company["id"])
        if not anchors["eligible"]:
            continue
        info = rev.ev.company_context_info(company["id"])
        if info is None:
            continue
        exclude = company_terms(info.get("name"), info.get("search_term"))
        markers = [(rev.ev.KIND_CHANGE, a, rev.ev.window_for_anomaly(a, window_before, window_after)) for a in anchors["anomalies"]]
        markers += [(rev.ev.KIND_OUTLIER, o, rev.ev.window_for_outlier(o["date"], window_before, window_after)) for o in anchors["outliers"]]
        marker_windows = [w for _, _, w in markers]
        n_before = len(out)
        for kind, anchor, window in markers:
            windows = rev.review_windows(kind, window["anchor_from"], window["anchor_to"], anchor if kind == rev.ev.KIND_CHANGE else None)
            visible, hidden = _sheet_window(info, window, kind, windows, rev._rows_for(company["id"], windows), categories, exclude, top, strict)
            out.append((visible, {
                "company_id": company["id"], "company": company["name"], "kind": kind, "date": anchor["date"],
                "direction_marker": anchor.get("direction"), "group": GROUP_MARKER, "offset_months": 0,
                "reference_hit": rev.reference_hit(company["name"], anchor["date"], anchor.get("direction"),
                                                   anchors.get("evaluated_months"), reference),
                **hidden,
            }))
            if comparisons == "none":
                continue
            comps = rev.ev.comparison_windows(window, marker_windows, anchors.get("series_from"), anchors.get("series_to"))
            for comp in comps[:1] if comparisons == "one" else comps:
                cw = rev.review_windows(kind, comp["anchor_from"], comp["anchor_to"])
                visible, hidden = _sheet_window(info, comp, kind, cw, rev._rows_for(company["id"], cw), categories, exclude, top, strict)
                out.append((visible, {
                    "company_id": company["id"], "company": company["name"], "kind": kind, "date": anchor["date"],
                    "direction_marker": anchor.get("direction"), "group": GROUP_COMPARISON, "offset_months": comp["offset_months"],
                    "reference_hit": None, **hidden,
                }))
        if verbose:
            mine = out[n_before:]
            n_m = sum(1 for _, h in mine if h["group"] == GROUP_MARKER)
            print(f"  {company['name']:<40} Markierungen {n_m:>3}  Vergleichsfenster {len(mine) - n_m:>3}")
    return out


def blind_sheet(pairs: List[Tuple[Dict[str, Any], Dict[str, Any]]], seed: int = DEFAULT_SEED, top: int = DEFAULT_TOP,
                comparisons: str = "all") -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Fenster mischen, Kennungen ``F-001`` … vergeben und in Bogen (sichtbar) und Schlüssel
    (verdeckt) trennen. Der Bogen enthält weder Gruppe noch Versatz noch Referenztreffer noch
    die Größe der Verschiebung. Reine Funktion."""
    order = list(range(len(pairs)))
    random.Random(seed).shuffle(order)
    width = max(3, len(str(len(pairs))))
    sheet_windows, key_windows = [], []
    for position, index in enumerate(order, start=1):
        visible, hidden = pairs[index]
        blind_id = f"F-{position:0{width}d}"
        sheet_windows.append({**visible, "id": blind_id})
        key_windows.append({"id": blind_id, **hidden})
    for w in sheet_windows:
        for forbidden in ("group", "offset_months", "reference_hit", "rating_shift"):
            assert forbidden not in w, forbidden
    generated = datetime.now(timezone.utc).isoformat(timespec="seconds")
    sheet = {
        "generated_at": generated, "seed": seed, "top": top, "comparisons": comparisons,
        "n_windows": len(sheet_windows),
        "n_explanations": sum(len(w["explanations"]) for w in sheet_windows),
        "scale": {str(k): v for k, v in PASSUNG_SCALE.items()},
        "scale_rules": {str(k): v for k, v in PASSUNG_RULES.items()},
        "direction_values": list(RICHTUNG_VALUES),
        "hint": ("Blind: Dieser Bogen sagt nicht, ob ein Fenster eine Markierung trägt oder ein verschobenes Vergleichsfenster "
                 "ist. Bewertet wird jeder Ansatz einzeln gegen die beschriebene Veränderung; keine Ursache behaupten."),
        "windows": sheet_windows,
    }
    key = {"generated_at": generated, "seed": seed, "n_windows": len(key_windows), "windows": key_windows}
    return sheet, key


def sheet_checksum(sheet: Dict[str, Any]) -> str:
    """Prüfsumme über die Fenster und Ansätze des Bogens (ohne Zeitstempel), damit Urteile,
    Schlüssel und Bogen zusammenpassen."""
    payload = json.dumps([{k: v for k, v in w.items()} for w in sheet["windows"]], ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def rating_template(sheet: Dict[str, Any]) -> Dict[str, Any]:
    """Leere Vorlage für die Urteile: je Fenster und Ansatz eine Zeile."""
    rows = [{"id": w["id"], "rank": e["rank"], "passung": None, "richtung": None, "begruendung": ""}
            for w in sheet["windows"] for e in w["explanations"]]
    return {"bogen_checksum": sheet_checksum(sheet), "scale": {str(k): v for k, v in PASSUNG_SCALE.items()},
            "direction_values": list(RICHTUNG_VALUES), "rater": None, "rated_at": None, "bewertungen": rows}


def _fmt_pp(value: Optional[float]) -> str:
    return "–" if value is None else f"{value:+.1f}".replace(".", ",")


def _fmt_signal(value: Optional[float]) -> str:
    return "–" if value is None else f"{float(value):.2f}".replace(".", ",")


def sheet_markdown(sheet: Dict[str, Any]) -> str:
    """Der Bogen als lesbarer Text: je Fenster die Veränderung und die obersten Ansätze mit
    Titel, Datum, Herausgeber, Signalen, Stufe und Begründungstext des Systems."""
    lines = [f"# Bewertungsbogen Erklärungsansätze (blind) · {sheet['n_windows']} Fenster · {sheet['n_explanations']} Ansätze", ""]
    lines.append(sheet["hint"])
    lines.append("")
    lines.append("Skala der Passung:")
    for k in sorted(PASSUNG_SCALE):
        lines.append(f"- **{k} – {PASSUNG_SCALE[k]}:** {PASSUNG_RULES[k]}")
    lines.append("")
    lines.append(f"Richtung je Ansatz: {', '.join(RICHTUNG_VALUES)} (passt die Stoßrichtung der Meldung zur Richtung der Veränderung?).")
    lines.append("")
    for w in sheet["windows"]:
        win = w["window"]
        kind_word = "Niveauwechsel" if w["kind"] == rev.ev.KIND_CHANGE else "Einzelmonat"
        anchor = (f"Übergang ab {win['transition_from']}, markierter Monat {win['anchor_to']}" if w["kind"] == rev.ev.KIND_CHANGE
                  else f"auffälliger Monat {win['anchor_to']}")
        lines.append(f"## {w['id']} · {w['company']} · {kind_word} · Fenster {win['from']} bis {win['to']} ({anchor})")
        lines.append("")
        r = w["reviews"]
        lines.append(f"Richtung der Veränderung in den Bewertungen: **{DIRECTION_WORDS.get(w['direction'], w['direction'])}**. "
                     f"Bewertungen davor {r['before']['n']} ({r['before']['from']} bis {r['before']['to']}), "
                     f"danach {r['after']['n']} ({r['after']['from']} bis {r['after']['to']})"
                     + (" · kleine Basis" if w["low_basis"] else "") + ".")
        terms = ", ".join(f"{t['term']} ({t['after']} ggü. {t['before']})" for t in w["terms"]) or "keine"
        lines.append(f"Kennzeichnende Begriffe ({w['n_terms']}): {terms}.")
        topics = ", ".join(f"{t['topic']} {_fmt_pp(t['share_shift_pp'])} pp" for t in w["shifted_topics"]) or "keine merkliche"
        lines.append(f"Verschobene Themen: {topics}.")
        s = w["n_by_stage"]
        lines.append(f"Belege im Fenster: {w['n_items']} ({w['n_bundles']} Bündel, {w['n_groups']} Gruppen); Bündel je Stufe: "
                     f"hoch {s.get('hoch', 0)}, mittel {s.get('mittel', 0)}, niedrig {s.get('niedrig', 0)}; Zustand: {w['state']}.")
        lines.append("")
        if not w["explanations"]:
            lines.append("_Kein Erklärungsansatz (offen). Nichts zu bewerten._")
            lines.append("")
            continue
        for e in w["explanations"]:
            cat = e["category"]
            cat_word = "ohne Ereignisart" if not cat else (f"Ereignisart: {cat['label']}" + ("" if cat["employer_related"] else " (ohne Arbeitgeberbezug)"))
            lines.append(f"### Ansatz {e['rank']} · Stufe {e['stage']} ({e['stage_label']}) · {cat_word}")
            src = "EQS-Mitteilung" if e["source_type"] == "adhoc" else "Meldung"
            if e.get("eqs_category"):
                src += f" ({e['eqs_category']})"
            bundle = f" · {e['n_items']} Meldungen ({', '.join(p for p in e['publishers'] if p)})" if (e["n_items"] or 0) > 1 else ""
            cit = {True: "ja", False: "nein", None: "nicht prüfbar"}[e["company_in_title"]]
            lines.append(f"- Datum {e['date']} · {e['publisher'] or '–'} · {src}{bundle} · Sprache {e['language'] or '–'} · Unternehmen im Titel: {cit}")
            lines.append(f"- Titel: {e['title']}")
            matched = ", ".join(f"'{t['term']}' ({t['after']} ggü. {t['before']}{', stark' if t['strong'] else ''})" for t in e["terms"]) or "keiner"
            shifted = ", ".join(f"{t['topic']} {_fmt_pp(t['share_shift_pp'])} pp" for t in (cat or {}).get("shifted_topics") or []) or "keine"
            lines.append(f"- Lage: {e['time_phrase']} (Zeit {_fmt_signal(e['time_match'])}) · Wortbezug {_fmt_signal(e['term_match'])} "
                         f"({matched}) · Ereignisart {_fmt_signal(e['category_match'])} (verschobene Themen: {shifted})")
            lines.append(f"- Begründung des Systems: {e['text']}")
            if e.get("group") and (e["group"].get("n_bundles") or 0) > 1:
                lines.append(f"- Gruppe: {e['group']['label']} · {e['group']['n_bundles']} Bündel, {e['group']['n_items']} Meldungen")
            lines.append(f"- Link: {e['url']}")
            lines.append("")
    return "\n".join(lines)


# ═════════════════════════════════════════════════════════════════════════════
# Teil B: Urteile prüfen, entblinden, auswerten
# ═════════════════════════════════════════════════════════════════════════════

def validate_ratings(ratings: Dict[str, Any], sheet: Dict[str, Any]) -> Dict[str, Any]:
    """Vollständigkeit und Wertebereich der Urteile gegen den Bogen; kein Schlüssel nötig.
    Fehler: unbekannte Kennung oder Rang, Passung nicht 0 bis 3, Richtung unbekannt,
    doppelte Zeile, Prüfsumme passt nicht. Warnungen: leere Begründung. ``missing`` nennt
    die noch nicht bewerteten (Kennung, Rang)."""
    errors: List[str] = []
    warnings: List[str] = []
    expected = {(w["id"], e["rank"]) for w in sheet["windows"] for e in w["explanations"]}
    checksum = sheet_checksum(sheet)
    if ratings.get("bogen_checksum") and ratings["bogen_checksum"] != checksum:
        errors.append(f"Prüfsumme der Urteile ({ratings['bogen_checksum']}) passt nicht zum Bogen ({checksum}).")
    seen = set()
    rated = set()
    for i, r in enumerate(ratings.get("bewertungen") or []):
        where = f"Zeile {i + 1} ({r.get('id')}, Rang {r.get('rank')})"
        pair = (r.get("id"), r.get("rank"))
        if pair not in expected:
            errors.append(f"{where}: Kennung oder Rang nicht im Bogen.")
            continue
        if pair in seen:
            errors.append(f"{where}: doppelt.")
            continue
        seen.add(pair)
        p = r.get("passung")
        if p is None:
            continue   # noch offen
        if not isinstance(p, int) or isinstance(p, bool) or p not in PASSUNG_SCALE:
            errors.append(f"{where}: Passung {p!r} nicht in 0 bis 3.")
            continue
        if r.get("richtung") not in RICHTUNG_VALUES:
            errors.append(f"{where}: Richtung {r.get('richtung')!r} nicht in {RICHTUNG_VALUES}.")
            continue
        if not str(r.get("begruendung") or "").strip():
            warnings.append(f"{where}: keine Begründung.")
        rated.add(pair)
    missing = sorted(expected - rated)
    return {"ok": not errors, "errors": errors, "warnings": warnings, "n_expected": len(expected), "n_rated": len(rated),
            "missing": [{"id": i, "rank": k} for i, k in missing]}


def join_ratings(ratings: Dict[str, Any], sheet: Dict[str, Any], key: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Entblinden: je Urteil die verdeckten Angaben des Schlüssels und die Signale des Ansatzes
    aus dem Bogen; nur Urteile mit Passung."""
    by_id_sheet = {w["id"]: w for w in sheet["windows"]}
    by_id_key = {w["id"]: w for w in key["windows"]}
    if set(by_id_sheet) != set(by_id_key):
        raise ValueError("Bogen und Schlüssel nennen nicht dieselben Kennungen.")
    rows = []
    for r in ratings.get("bewertungen") or []:
        if r.get("passung") is None:
            continue
        w, k = by_id_sheet.get(r["id"]), by_id_key.get(r["id"])
        if w is None or k is None:
            continue
        e = next((x for x in w["explanations"] if x["rank"] == r["rank"]), None)
        if e is None:
            continue
        cat = e.get("category") or {}
        rows.append({
            "id": r["id"], "rank": r["rank"], "company": k["company"], "kind": k["kind"], "date": k["date"],
            "group": k["group"], "offset_months": k["offset_months"], "reference_hit": k.get("reference_hit"),
            "direction": w["direction"], "stage": e["stage"], "stage_label": e["stage_label"], "signal_label": e["signal_label"],
            "category_id": cat.get("id"), "category_label": cat.get("label"), "employer_related": cat.get("employer_related"),
            "term_match": e.get("term_match"), "category_match": e.get("category_match"), "time_match": e.get("time_match"),
            "company_in_title": e.get("company_in_title"), "source_type": e.get("source_type"),
            "passung": int(r["passung"]), "richtung": r.get("richtung"), "begruendung": str(r.get("begruendung") or "").strip(),
        })
    return rows


def window_fit(rows: List[Dict[str, Any]], key: Dict[str, Any], sheet: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Je Fenster des Schlüssels die Passung des obersten bewerteten Ansatzes (``fit_top1``)
    und die beste Passung (``fit_max``); Fenster ohne Ansatz (offen) bekommen None und zählen in
    der Variante „alle Fenster“ als 0."""
    by_window: Dict[str, List[Dict[str, Any]]] = {}
    for r in rows:
        by_window.setdefault(r["id"], []).append(r)
    out = []
    for k in key["windows"]:
        mine = sorted(by_window.get(k["id"], []), key=lambda r: r["rank"])
        out.append({"id": k["id"], "company": k["company"], "kind": k["kind"], "date": k["date"], "group": k["group"],
                    "offset_months": k["offset_months"], "reference_hit": k.get("reference_hit"), "top_stage": k.get("top_stage"),
                    "n_explanations": k.get("n_explanations", 0), "n_rated": len(mine),
                    "fit_top1": mine[0]["passung"] if mine else None,
                    "fit_max": max(r["passung"] for r in mine) if mine else None,
                    "fit_mean": _mean([r["passung"] for r in mine]) if mine else None,
                    "top1_is_best": (mine[0]["passung"] == max(r["passung"] for r in mine)) if len(mine) >= 2 else None})
    return out


def _fit_clusters(windows: List[Dict[str, Any]], value: Callable[[Dict[str, Any]], Optional[float]]) -> List[List[float]]:
    clusters = build_clusters(windows)
    out = []
    for c in clusters:
        vals = [value(w) for w in c]
        if vals[0] is None:
            continue
        out.append([float(vals[0])] + [float(v) for v in vals[1:] if v is not None])
    return out


def fit_tests(rows: List[Dict[str, Any]], windows: List[Dict[str, Any]], n_perm: int = DEFAULT_PERMUTATIONS, seed: int = DEFAULT_SEED) -> Dict[str, Any]:
    """Teil B: Markierung gegen Vergleichsfenster auf den Passungsurteilen (nur Fenster mit
    Ansatz und alle Fenster mit offen = 0), Stufe gegen Passung (Kreuztabelle, Spearman),
    Signale, Ereignisarten, Richtung und Rangfolge."""
    rated = [w for w in windows if w["fit_top1"] is not None]
    result: Dict[str, Any] = {
        "n_ratings": len(rows), "n_windows_rated": len(rated), "n_windows": len(windows),
        "threshold": FIT_THRESHOLD, "threshold_label": f"Passung mindestens {FIT_THRESHOLD} ({PASSUNG_SCALE[FIT_THRESHOLD]})",
        "windows_with_approach": {
            "fit_top1_mean": compare_means(_fit_clusters(rated, lambda w: w["fit_top1"]), n_perm, seed),
            "fit_top1_at_least": compare_binary(_fit_clusters(rated, lambda w: 1 if w["fit_top1"] >= FIT_THRESHOLD else 0), n_perm, seed),
            "fit_max_at_least": compare_binary(_fit_clusters(rated, lambda w: 1 if w["fit_max"] >= FIT_THRESHOLD else 0), n_perm, seed),
        },
        "all_windows_open_as_zero": {
            "fit_top1_mean": compare_means(_fit_clusters(windows, lambda w: 0.0 if w["fit_top1"] is None else w["fit_top1"]), n_perm, seed),
            "fit_max_at_least": compare_binary(_fit_clusters(windows, lambda w: 1 if (w["fit_max"] or 0) >= FIT_THRESHOLD else 0), n_perm, seed),
        },
        "by_kind": {},
    }
    for kind in rev.KINDS:
        mine = [w for w in rated if w["kind"] == kind]
        result["by_kind"][kind] = {
            "fit_top1_mean": compare_means(_fit_clusters(mine, lambda w: w["fit_top1"]), n_perm, seed),
            "fit_max_at_least": compare_binary(_fit_clusters(mine, lambda w: 1 if w["fit_max"] >= FIT_THRESHOLD else 0), n_perm, seed),
        }
    # Stufe gegen Passung (alle Urteile)
    table: Dict[str, Dict[str, int]] = {s: {str(p): 0 for p in PASSUNG_SCALE} for s in STAGE_SCORE}
    for r in rows:
        if r["stage"] in table:
            table[r["stage"]][str(r["passung"])] += 1
    per_stage = {}
    for s in STAGE_SCORE:
        vals = [r["passung"] for r in rows if r["stage"] == s]
        per_stage[s] = {"n": len(vals), "mean": _mean(vals), "at_least": sum(1 for v in vals if v >= FIT_THRESHOLD)}
    result["stage_vs_fit"] = {
        "table": table, "per_stage": per_stage,
        "spearman": spearman([float(STAGE_SCORE[r["stage"]]) for r in rows if r["stage"] in STAGE_SCORE],
                             [float(r["passung"]) for r in rows if r["stage"] in STAGE_SCORE], n_perm, seed),
    }
    # Signale gegen Passung
    def signal_block(name: str, test: Callable[[Dict[str, Any]], Optional[bool]]) -> Dict[str, Any]:
        yes = [r["passung"] for r in rows if test(r) is True]
        no = [r["passung"] for r in rows if test(r) is False]
        return {"label": name, "with": {"n": len(yes), "mean": _mean(yes), "at_least": sum(1 for v in yes if v >= FIT_THRESHOLD)},
                "without": {"n": len(no), "mean": _mean(no), "at_least": sum(1 for v in no if v >= FIT_THRESHOLD)},
                "fisher_p": fisher_exact(sum(1 for v in yes if v >= FIT_THRESHOLD), sum(1 for v in yes if v < FIT_THRESHOLD),
                                         sum(1 for v in no if v >= FIT_THRESHOLD), sum(1 for v in no if v < FIT_THRESHOLD)) if yes and no else None}
    result["signals_vs_fit"] = {
        "wortbezug": signal_block("Wortbezug (term_match ≥ 0,5)", lambda r: float(r.get("term_match") or 0) >= 0.5),
        "ereignisart": signal_block("Ereignisart erkannt (category_match ≥ 0,5)", lambda r: float(r.get("category_match") or 0) >= 0.5),
        "themenverschiebung": signal_block("Themenverschiebung (category_match ≥ 1)", lambda r: float(r.get("category_match") or 0) >= 1.0),
        "arbeitgeberbezug": signal_block("Ereignisart mit Arbeitgeberbezug", lambda r: r.get("employer_related")),
        "unternehmen_im_titel": signal_block("Unternehmen im Titel genannt", lambda r: r.get("company_in_title")),
        "eqs": signal_block("EQS-Mitteilung", lambda r: r.get("source_type") == "adhoc"),
    }
    # Ereignisarten
    cats: Dict[str, List[int]] = {}
    for r in rows:
        cats.setdefault(r.get("category_label") or "ohne Ereignisart", []).append(r["passung"])
    result["categories_vs_fit"] = sorted(
        [{"category": c, "n": len(v), "mean": _mean(v), "at_least": sum(1 for x in v if x >= FIT_THRESHOLD)} for c, v in cats.items()],
        key=lambda d: (-d["n"], d["category"]))
    # Richtung je Gruppe
    result["direction_by_group"] = {
        g: {d: sum(1 for r in rows if r["group"] == g and r["richtung"] == d) for d in RICHTUNG_VALUES} for g in (GROUP_MARKER, GROUP_COMPARISON)
    }
    # Rangfolge: steht der passendste Ansatz oben?
    multi = [w for w in rated if w["top1_is_best"] is not None]
    result["ranking"] = {"n_windows_with_two_or_more": len(multi), "top1_is_best": sum(1 for w in multi if w["top1_is_best"]),
                         "share": _mean([1.0 if w["top1_is_best"] else 0.0 for w in multi])}
    # Referenz (nur Markierungen)
    hits = [w for w in rated if w["group"] == GROUP_MARKER and w["reference_hit"] is True]
    rest = [w for w in rated if w["group"] == GROUP_MARKER and w["reference_hit"] is False]
    result["reference"] = None if not (hits or rest) else {
        "treffer": {"n": len(hits), "fit_top1_mean": _mean([w["fit_top1"] for w in hits]), "at_least": sum(1 for w in hits if w["fit_max"] >= FIT_THRESHOLD)},
        "uebrige": {"n": len(rest), "fit_top1_mean": _mean([w["fit_top1"] for w in rest]), "at_least": sum(1 for w in rest if w["fit_max"] >= FIT_THRESHOLD)},
        "fisher_p": fisher_exact(sum(1 for w in hits if w["fit_max"] >= FIT_THRESHOLD), sum(1 for w in hits if w["fit_max"] < FIT_THRESHOLD),
                                 sum(1 for w in rest if w["fit_max"] >= FIT_THRESHOLD), sum(1 for w in rest if w["fit_max"] < FIT_THRESHOLD)) if hits and rest else None,
    }
    return result


# ═════════════════════════════════════════════════════════════════════════════
# Ausgabe
# ═════════════════════════════════════════════════════════════════════════════

def _pct(k: int, n: int) -> str:
    return "–" if not n else f"{k}/{n} ({100 * k / n:.0f} %)"


def _num(value: Optional[float], digits: int = 2) -> str:
    return "–" if value is None else f"{value:.{digits}f}".replace(".", ",")


def _p(value: Optional[float]) -> str:
    if value is None:
        return "–"
    return "< 0,001" if value < 0.001 else f"{value:.3f}".replace(".", ",")


def _ci(ci: Sequence[Optional[float]]) -> str:
    if not ci or ci[0] is None:
        return "–"
    return f"[{100 * ci[0]:+.0f}; {100 * ci[1]:+.0f}] pp"


def _binary_row(label: str, b: Dict[str, Any]) -> str:
    m, c = b["markers"], b["comparisons"]
    md = b.get("min_detectable") or {}
    mdd = "–"
    if md.get("above") is not None or md.get("below") is not None:
        parts = []
        if md.get("above") is not None:
            parts.append(f"≥ {100 * md['above']:.0f} %")
        if md.get("below") is not None:
            parts.append(f"≤ {100 * md['below']:.0f} %")
        mdd = " oder ".join(parts)
    return (f"| {label} | {_pct(m['k'], m['n'])} | {_pct(c['k'], c['n'])} | {_num(None if b['diff'] is None else 100 * b['diff'], 0)} pp | "
            f"{_ci(b['ci95'])} | {_p(b['fisher_p'])} | {_p(b['permutation']['p_value'])} | {mdd} |")


def _binary_table(block: Dict[str, Any]) -> List[str]:
    lines = ["| Merkmal | Markierungen | Vergleichsfenster | Differenz | 95 %-Intervall (Newcombe) | p Fisher | p Permutation (Cluster) | nachweisbar wäre (Anteil bei Markierungen) |",
             "|---|---|---|---|---|---|---|---|"]
    for key, b in block["binary"].items():
        lines.append(_binary_row(b["label"], b))
    o = block["ordinal"]
    if o and o["markers"]["n"]:
        lines.append(f"| {o['label']} | Mittel {_num(o['markers']['mean'])} | Mittel {_num(o['comparisons']['mean'])} | "
                     f"{_num(o['diff'])} | – | – | {_p(o['permutation']['p_value'])} | – |")
    return lines


def stage_markdown(a: Dict[str, Any], source_path: str) -> List[str]:
    lines = ["## Teil A: Unterscheiden die Stufen Markierungs- von Vergleichsfenstern?", ""]
    lines.append(f"Grundlage: `{source_path}` ({a['n_windows']} Fenster, davon {a['n_complete']} vollständig im Speicher; "
                 f"{a['total']['n_markers']} Markierungen in Clustern mit {a['total']['n_comparisons']} Vergleichsfenstern"
                 + (f"; {a['n_skipped_clusters_windows']} Fenster ohne eindeutige Markierung übersprungen" if a["n_skipped_clusters_windows"] else "") + ").")
    lines.append("")
    lines.append("Lesart der Spalten: Fisher behandelt die Fenster als unabhängig; der Permutationstest vergibt die Rolle "
                 "„Markierung“ innerhalb jedes Clusters (Markierung und ihre verschobenen Fenster desselben Unternehmens) "
                 "zufällig neu und ist deshalb der angemessene Test. „Nachweisbar wäre“ nennt den Anteil bei Markierungen, "
                 "ab dem ein Unterschied zum Vergleichsanteil mit diesen Fallzahlen überhaupt mit 80 % Teststärke gefunden würde.")
    lines.append("")
    lines.append("**Gesamt**")
    lines.append("")
    lines += _binary_table(a["total"])
    lines.append("")
    pr = a["total"]["ordinal"]["permutation"]["paired"]
    lines.append(f"Gepaart je Cluster (oberste Stufe der Markierung minus Mittel ihrer Vergleichsfenster, {pr['n_pairs']} Paare): "
                 f"Markierung höher {pr['marker_higher']}, gleich {pr['equal']}, niedriger {pr['marker_lower']}; mittlere Differenz {_num(pr['mean_diff'])}.")
    lines.append("")
    for kind, title in ((rev.ev.KIND_CHANGE, "Niveauwechsel"), (rev.ev.KIND_OUTLIER, "Einzelmonate")):
        blk = a["by_kind"][kind]
        lines.append(f"**{title}** ({blk['n_markers']} Markierungen, {blk['n_comparisons']} Vergleichsfenster)")
        lines.append("")
        lines += _binary_table(blk)
        lines.append("")
    ref = a.get("reference")
    lines.append("**Markierungen mit gegen ohne Referenzzeitraum (E5)**")
    lines.append("")
    if ref:
        lines.append("| Merkmal | mit Referenzzeitraum | ohne | Differenz | 95 %-Intervall | p Fisher |")
        lines.append("|---|---|---|---|---|---|")
        for key, b in ref["binary"].items():
            lines.append(f"| {b['label']} | {_pct(b['treffer']['k'], b['treffer']['n'])} | {_pct(b['uebrige']['k'], b['uebrige']['n'])} | "
                         f"{_num(None if b['diff'] is None else 100 * b['diff'], 0)} pp | {_ci(b['ci95'])} | {_p(b['fisher_p'])} |")
    else:
        lines.append("nicht verfügbar (keine Referenztreffer im Bericht).")
    lines.append("")
    nm = a["null_model"]
    lines.append("**Nullmodell: folgt die Stufe der Zahl der Belege?**")
    lines.append("")
    lines.append(f"Spearman ρ Belege ↔ oberste Stufe: {_num(nm['items_vs_top_stage']['rho'])} (p {_p(nm['items_vs_top_stage']['p_value'])}, "
                 f"n {nm['items_vs_top_stage']['n']}); Belege ↔ mit Ansatz: {_num(nm['items_vs_any']['rho'])} (p {_p(nm['items_vs_any']['p_value'])}).")
    lines.append("")
    lines.append("| Belege je Fenster (Drittel) | Spanne | Markierungen mit Ansatz | Vergleichsfenster mit Ansatz |")
    lines.append("|---|---|---|---|")
    for t in nm["by_items_tertile"]:
        rng = t["items_range"]
        lines.append(f"| {t['tertile']} | {rng[0]}–{rng[1]} | {_pct(t['markers']['k'], t['markers']['n'])} | {_pct(t['comparisons']['k'], t['comparisons']['n'])} |")
    lines.append("")
    return lines


def fit_markdown(b: Dict[str, Any]) -> List[str]:
    lines = ["## Teil B: Passung der Erklärungsansätze (blinde Urteile)", ""]
    lines.append(f"{b['n_ratings']} Urteile zu {b['n_windows_rated']} von {b['n_windows']} Fenstern (die übrigen sind offen, ohne Ansatz). "
                 f"Schwelle „passend“: {b['threshold_label']}.")
    lines.append("")
    lines.append("**Markierungen gegen Vergleichsfenster (nur Fenster mit Ansatz)**")
    lines.append("")
    w = b["windows_with_approach"]
    lines.append("| Merkmal | Markierungen | Vergleichsfenster | Differenz | 95 %-Intervall | p Fisher | p Permutation (Cluster) | nachweisbar wäre |")
    lines.append("|---|---|---|---|---|---|---|---|")
    lines.append(_binary_row("oberster Ansatz passend (≥ 2)", w["fit_top1_at_least"]))
    lines.append(_binary_row("bester Ansatz passend (≥ 2)", w["fit_max_at_least"]))
    m = w["fit_top1_mean"]
    lines.append(f"| Passung des obersten Ansatzes (Mittel 0–3) | {_num(m['markers']['mean'])} (n {m['markers']['n']}) | "
                 f"{_num(m['comparisons']['mean'])} (n {m['comparisons']['n']}) | {_num(m['diff'])} | – | – | {_p(m['permutation']['p_value'])} | – |")
    lines.append("")
    lines.append(f"Verteilung der Passung des obersten Ansatzes: Markierungen {m['markers']['distribution']}, Vergleichsfenster {m['comparisons']['distribution']}.")
    lines.append("")
    z = b["all_windows_open_as_zero"]
    lines.append("**Alle Fenster (offen zählt als Passung 0)**")
    lines.append("")
    lines.append("| Merkmal | Markierungen | Vergleichsfenster | Differenz | 95 %-Intervall | p Fisher | p Permutation (Cluster) | nachweisbar wäre |")
    lines.append("|---|---|---|---|---|---|---|---|")
    lines.append(_binary_row("bester Ansatz passend (≥ 2)", z["fit_max_at_least"]))
    m = z["fit_top1_mean"]
    lines.append(f"| Passung des obersten Ansatzes (Mittel 0–3) | {_num(m['markers']['mean'])} (n {m['markers']['n']}) | "
                 f"{_num(m['comparisons']['mean'])} (n {m['comparisons']['n']}) | {_num(m['diff'])} | – | – | {_p(m['permutation']['p_value'])} | – |")
    lines.append("")
    lines.append("**Je Art der Markierung (nur Fenster mit Ansatz)**")
    lines.append("")
    lines.append("| Art | Markierungen: bester Ansatz passend | Vergleichsfenster | p Permutation | Passung oben (Mittel) Markierung / Vergleich | p Permutation |")
    lines.append("|---|---|---|---|---|---|")
    for kind, title in ((rev.ev.KIND_CHANGE, "Niveauwechsel"), (rev.ev.KIND_OUTLIER, "Einzelmonate")):
        k = b["by_kind"][kind]
        fb, fm = k["fit_max_at_least"], k["fit_top1_mean"]
        lines.append(f"| {title} | {_pct(fb['markers']['k'], fb['markers']['n'])} | {_pct(fb['comparisons']['k'], fb['comparisons']['n'])} | "
                     f"{_p(fb['permutation']['p_value'])} | {_num(fm['markers']['mean'])} / {_num(fm['comparisons']['mean'])} | {_p(fm['permutation']['p_value'])} |")
    lines.append("")
    s = b["stage_vs_fit"]
    lines.append("**Stufe des Systems gegen Passung (alle Urteile)**")
    lines.append("")
    lines.append("| Stufe | n | Passung 0 | 1 | 2 | 3 | Mittel | passend (≥ 2) |")
    lines.append("|---|---|---|---|---|---|---|---|")
    for stage in ("hoch", "mittel", "niedrig"):
        t, p = s["table"][stage], s["per_stage"][stage]
        lines.append(f"| {stage} | {p['n']} | {t['0']} | {t['1']} | {t['2']} | {t['3']} | {_num(p['mean'])} | {_pct(p['at_least'], p['n'])} |")
    sp = s["spearman"]
    lines.append("")
    lines.append(f"Spearman ρ Stufe ↔ Passung: {_num(sp['rho'])} (p {_p(sp['p_value'])}, n {sp['n']}).")
    lines.append("")
    lines.append("**Signale gegen Passung**")
    lines.append("")
    lines.append("| Signal | mit: n / Mittel / passend | ohne: n / Mittel / passend | p Fisher (passend) |")
    lines.append("|---|---|---|---|")
    for key, sig in b["signals_vs_fit"].items():
        w_, o_ = sig["with"], sig["without"]
        lines.append(f"| {sig['label']} | {w_['n']} / {_num(w_['mean'])} / {_pct(w_['at_least'], w_['n'])} | "
                     f"{o_['n']} / {_num(o_['mean'])} / {_pct(o_['at_least'], o_['n'])} | {_p(sig['fisher_p'])} |")
    lines.append("")
    lines.append("**Ereignisarten gegen Passung**")
    lines.append("")
    lines.append("| Ereignisart | n | Mittel | passend (≥ 2) |")
    lines.append("|---|---|---|---|")
    for c in b["categories_vs_fit"]:
        lines.append(f"| {c['category']} | {c['n']} | {_num(c['mean'])} | {_pct(c['at_least'], c['n'])} |")
    lines.append("")
    d = b["direction_by_group"]
    lines.append("**Richtung der Meldung zur Richtung der Veränderung (Urteil)**")
    lines.append("")
    lines.append("| Gruppe | " + " | ".join(RICHTUNG_VALUES) + " |")
    lines.append("|---|" + "---|" * len(RICHTUNG_VALUES))
    for g, title in ((GROUP_MARKER, "Markierungen"), (GROUP_COMPARISON, "Vergleichsfenster")):
        lines.append(f"| {title} | " + " | ".join(str(d[g][v]) for v in RICHTUNG_VALUES) + " |")
    lines.append("")
    r = b["ranking"]
    lines.append(f"Rangfolge: In {_pct(r['top1_is_best'], r['n_windows_with_two_or_more'])} der Fenster mit mindestens zwei bewerteten "
                 f"Ansätzen steht der passendste (oder ein gleich passender) Ansatz oben.")
    lines.append("")
    ref = b.get("reference")
    if ref:
        lines.append(f"Referenz (E5, nur Markierungen mit Ansatz): mit Referenzzeitraum bester Ansatz passend {_pct(ref['treffer']['at_least'], ref['treffer']['n'])}, "
                     f"Mittel oben {_num(ref['treffer']['fit_top1_mean'])}; ohne {_pct(ref['uebrige']['at_least'], ref['uebrige']['n'])}, "
                     f"Mittel {_num(ref['uebrige']['fit_top1_mean'])}; p Fisher {_p(ref['fisher_p'])}.")
        lines.append("")
    return lines


def ratings_appendix(rows: List[Dict[str, Any]]) -> List[str]:
    """Anhang: jedes Urteil mit Gruppe, Stufe, Passung, Richtung und Begründung (ohne Titel)."""
    lines = ["## Anhang: alle Urteile (entblindet, ohne Titel)", "",
             "| Kennung | Unternehmen | Art | Markierung | Gruppe | Versatz | Rang | Stufe | Ereignisart | Passung | Richtung | Begründung |",
             "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in sorted(rows, key=lambda r: (r["company"], r["date"], r["offset_months"], r["rank"])):
        lines.append(f"| {r['id']} | {r['company']} | {r['kind']} | {r['date']} | {r['group']} | {r['offset_months']:+d} | {r['rank']} | {r['stage']} | "
                     f"{r.get('category_label') or '–'} | {r['passung']} | {r['richtung']} | {r['begruendung'].replace('|', '/')} |")
    lines.append("")
    return lines


def report_markdown(summary: Dict[str, Any]) -> str:
    lines = ["# Bewertung der Erklärungsansätze: Passung und Unterschied", ""]
    lines.append(f"Stand {summary['generated_at']}; Permutationen {summary['n_permutations']}, Startwert {summary['seed']}.")
    lines.append("")
    if summary.get("stage_tests"):
        lines += stage_markdown(summary["stage_tests"], summary["validity_path"])
    if summary.get("fit_tests"):
        lines += fit_markdown(summary["fit_tests"])
    if summary.get("ratings_check"):
        chk = summary["ratings_check"]
        lines.append(f"Prüfung der Urteile: {chk['n_rated']} von {chk['n_expected']} bewertet"
                     + (f", {len(chk['missing'])} offen" if chk["missing"] else "") + (f", {len(chk['errors'])} Fehler" if chk["errors"] else "")
                     + (f", {len(chk['warnings'])} Warnungen" if chk["warnings"] else "") + ".")
        lines.append("")
    lines.append(NOTE)
    lines.append("")
    if summary.get("ratings_rows"):
        lines += ratings_appendix(summary["ratings_rows"])
    return "\n".join(lines)


# ═════════════════════════════════════════════════════════════════════════════
# Befehle
# ═════════════════════════════════════════════════════════════════════════════

def _write_json(path: str, data: Any) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)
        fh.write("\n")


def _write_text(path: str, text: str) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text + "\n")


def _read_json(path: str) -> Any:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def cmd_bogen(args: argparse.Namespace) -> int:
    out_dir = args.out_dir or os.path.join(DEFAULT_SHEET_DIR, datetime.now().strftime("%Y-%m-%d"))
    paths = {name: os.path.join(out_dir, f"{name}.json") for name in ("bogen", "schluessel", "bewertungen_vorlage")}
    paths["bogen_md"] = os.path.join(out_dir, "bogen.md")
    if not args.force and any(os.path.exists(p) for p in paths.values()):
        print(f"Im Ordner {out_dir} liegt bereits ein Bogen; mit --force überschreiben oder anderen --out-dir wählen.")
        return 2
    reference = rev.load_reference(args.annotations)
    pairs = collect_windows(args.window_before, args.window_after, top=args.top, comparisons=args.comparisons,
                            reference=reference, verbose=not args.quiet, strict=not args.no_strict)
    sheet, key = blind_sheet(pairs, seed=args.seed, top=args.top, comparisons=args.comparisons)
    key["bogen_checksum"] = sheet_checksum(sheet)
    key["git"] = rev.git_state()
    _write_json(paths["bogen"], sheet)
    _write_text(paths["bogen_md"], sheet_markdown(sheet))
    _write_json(paths["schluessel"], key)
    _write_json(paths["bewertungen_vorlage"], rating_template(sheet))
    n_m = sum(1 for w in key["windows"] if w["group"] == GROUP_MARKER)
    print(f"Bogen: {sheet['n_windows']} Fenster ({n_m} Markierungen, {sheet['n_windows'] - n_m} Vergleichsfenster), "
          f"{sheet['n_explanations']} Ansätze zu bewerten.")
    for name, path in paths.items():
        print(f"  {name:<20} {path}")
    print("Den Schlüssel erst nach den Urteilen öffnen.")
    return 0


def cmd_pruefen(args: argparse.Namespace) -> int:
    check = validate_ratings(_read_json(args.ratings), _read_json(args.bogen))
    print(f"Urteile: {check['n_rated']} von {check['n_expected']} bewertet.")
    for e in check["errors"]:
        print(f"Fehler: {e}")
    for w in check["warnings"]:
        print(f"Warnung: {w}")
    if check["missing"]:
        print("Offen: " + ", ".join(f"{m['id']}/{m['rank']}" for m in check["missing"][:40]) + (" …" if len(check["missing"]) > 40 else ""))
    return 0 if check["ok"] and not check["missing"] else 1


def cmd_auswerten(args: argparse.Namespace) -> int:
    summary: Dict[str, Any] = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "seed": args.seed,
        "n_permutations": args.permutations, "git": rev.git_state(), "note": NOTE,
        "validity_path": None, "stage_tests": None, "fit_tests": None, "ratings_check": None, "ratings_rows": None, "windows": None,
    }
    if args.validity:
        validity = _read_json(args.validity)
        summary["validity_path"] = os.path.relpath(args.validity, BACKEND_DIR)
        summary["validity_generated_at"] = validity.get("generated_at")
        summary["validity_git"] = validity.get("git")
        summary["stage_tests"] = stage_tests(validity.get("windows") or [], args.permutations, args.seed)
    if args.ratings:
        if not (args.bogen and args.key):
            print("Für --ratings sind --bogen und --key nötig.")
            return 2
        sheet, key, ratings = _read_json(args.bogen), _read_json(args.key), _read_json(args.ratings)
        if key.get("bogen_checksum") and key["bogen_checksum"] != sheet_checksum(sheet):
            print("Schlüssel passt nicht zum Bogen (Prüfsumme).")
            return 2
        check = validate_ratings(ratings, sheet)
        summary["ratings_check"] = check
        if check["errors"]:
            for e in check["errors"]:
                print(f"Fehler: {e}")
            if args.strict:
                return 1
        rows = join_ratings(ratings, sheet, key)
        windows = window_fit(rows, key, sheet)
        summary["fit_tests"] = fit_tests(rows, windows, args.permutations, args.seed)
        summary["ratings_rows"] = rows
        summary["windows"] = windows
        summary["ratings_meta"] = {k: ratings.get(k) for k in ("rater", "rated_at", "bogen_checksum")}
    if not summary["stage_tests"] and not summary["fit_tests"]:
        print("Nichts zu tun: --validity und/oder --ratings angeben.")
        return 2
    text = report_markdown(summary)
    print(text)
    if args.md:
        _write_text(args.md, text)
        print(f"Bericht gespeichert: {args.md}")
    if args.json_out:
        _write_json(args.json_out, summary)
        print(f"Zusammenfassung gespeichert: {args.json_out}")
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    b = sub.add_parser("bogen", help="blinden Bewertungsbogen, Schlüssel und Vorlage erzeugen (Datenbank und Speicher)")
    b.add_argument("--out-dir", help=f"Zielordner (Standard: {os.path.relpath(DEFAULT_SHEET_DIR, BACKEND_DIR)}/<Datum>)")
    b.add_argument("--top", type=int, default=DEFAULT_TOP, help=f"oberste Ansätze je Fenster (Standard {DEFAULT_TOP})")
    b.add_argument("--comparisons", choices=("all", "one", "none"), default="all", help="alle, nur das erste oder kein Vergleichsfenster je Markierung")
    b.add_argument("--seed", type=int, default=DEFAULT_SEED)
    b.add_argument("--window-before", type=int, default=rev.ev.DEFAULT_WINDOW_BEFORE)
    b.add_argument("--window-after", type=int, default=rev.ev.DEFAULT_WINDOW_AFTER)
    b.add_argument("--annotations", default=rev.DEFAULT_ANNOTATIONS, help="Annotationsdatei für den Referenztreffer im Schlüssel (E5)")
    b.add_argument("--no-strict", action="store_true", help="Rangfolge ohne die strenge Auswahl der Belege (Fassung bis 2026-10-17)")
    b.add_argument("--force", action="store_true", help="vorhandenen Bogen im Zielordner überschreiben")
    b.add_argument("--quiet", action="store_true")
    b.set_defaults(func=cmd_bogen)

    p = sub.add_parser("pruefen", help="Urteile gegen den Bogen prüfen (ohne Schlüssel)")
    p.add_argument("--bogen", required=True)
    p.add_argument("--ratings", required=True)
    p.set_defaults(func=cmd_pruefen)

    a = sub.add_parser("auswerten", help="Tests auf Stufen (Teil A) und Passungsurteilen (Teil B)")
    a.add_argument("--validity", default=DEFAULT_VALIDITY, help="Bericht von report_explanation_validity.py (JSON); '' lässt Teil A aus")
    a.add_argument("--bogen")
    a.add_argument("--key")
    a.add_argument("--ratings")
    a.add_argument("--permutations", type=int, default=DEFAULT_PERMUTATIONS)
    a.add_argument("--seed", type=int, default=DEFAULT_SEED)
    a.add_argument("--strict", action="store_true", help="bei Fehlern in den Urteilen abbrechen")
    a.add_argument("--md", help="Bericht als Markdown-Datei")
    a.add_argument("--json", dest="json_out", help="Zusammenfassung als JSON-Datei")
    a.set_defaults(func=cmd_auswerten)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
