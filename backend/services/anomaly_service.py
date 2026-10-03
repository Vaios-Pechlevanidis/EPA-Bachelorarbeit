"""
Auffällige Veränderungen (Anomalien) in den Monatsreihen der Kununu-Bewertungen.

Zyklus 2, Inkrement 1 (FA-01 bis FA-04). Ablauf je Unternehmen, Quelle und
Dimension:

1. Reihe über ``rating_series_service.monthly_series`` (E3), nur lesend.
2. Eignung nach E4 (``is_eligible``: mindestens 12 bewertete Monate). Nicht
   geeignete Reihen liefern keine Anomalien, sondern Grund und Anzahl
   bewerteter Monate.
3. Erkennung nur auf den bewerteten Monaten (``changepoint_detector``); nicht
   bewertete Monate werden übersprungen, nicht aufgefüllt.
4. Je Wechsel eine Anomalie; Wechsel mit ``|delta| < min_delta`` entfallen.

Felder je Anomalie:

- ``id``: ``"{source}:{dimension}:{YYYY-MM}"``
- ``date``: erster bewerteter Monat auf dem neuen Niveau
- ``direction``: ``"fall"`` oder ``"rise"``
- ``delta``: ``after_mean - before_mean`` in Sternen
- ``before_mean`` / ``after_mean``: Mittel der Monatsmittel im Segment vor bzw.
  nach dem Wechsel (bis zum benachbarten Wechsel)
- ``n_reviews_before`` / ``n_reviews_after``: Anzahl der Werte im Segment vor
  bzw. nach dem Wechsel
- ``n_reviews``: Summe beider Segmente
- ``severity``: ``"high"`` ab ``SEVERITY_HIGH`` (0,5 Sterne, Richtwert des
  Annotationsprotokolls), sonst ``"medium"`` ab ``min_delta``
- ``method`` / ``params``: Verfahren und Parameter der Erkennung

Die Ergebnisse sind Hinweise auf auffällige Veränderungen, keine Aussagen über
Ursachen. Sortierung: ``fall`` vor ``rise``, innerhalb nach ``|delta|`` absteigend.
"""

from __future__ import annotations

from typing import Any, Dict, List

from models.changepoint_detector import (
    DEFAULT_MIN_SIZE,
    DEFAULT_MODEL,
    DEFAULT_PENALTY,
    PeltDetector,
    detect_changepoints,
    level_shifts,
)
from services.rating_series_service import (
    MIN_EVALUATED_MONTHS,
    MIN_REVIEWS_PER_MONTH,
    OVERALL_DIMENSION,
    evaluated_months,
    is_eligible,
    monthly_series,
    monthly_series_by_dimension,
)

DEFAULT_MIN_DELTA = 0.3   # Sterne; vorläufig, siehe E9
SEVERITY_HIGH = 0.5       # Sterne; Richtwert aus dem Annotationsprotokoll (E5)

_DIRECTION_ORDER = {"fall": 0, "rise": 1}


def _severity(delta: float) -> str:
    return "high" if abs(delta) >= SEVERITY_HIGH else "medium"


def _n_values(months: List[Dict[str, Any]]) -> int:
    """Anzahl der Werte, auf denen die Monatsmittel eines Segments beruhen."""
    return sum(int(m.get("n_values", m.get("count", 0))) for m in months)


def eligibility(series: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Eignung der Reihe nach E4 mit Begründung für nicht geeignete Reihen."""
    n = evaluated_months(series)
    eligible = is_eligible(series)
    reason = None
    if not eligible:
        reason = (
            f"Nur {n} bewertete Monate (mindestens {MIN_EVALUATED_MONTHS} nötig, "
            f"je Monat mindestens {MIN_REVIEWS_PER_MONTH} Bewertungen)."
            if series else "Keine datierten Bewertungen in dieser Quelle."
        )
    return {
        "eligible": eligible,
        "evaluated_months": n,
        "min_evaluated_months": MIN_EVALUATED_MONTHS,
        "reason": reason,
    }


def sort_anomalies(anomalies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """``fall`` vor ``rise``, dann nach Betrag von ``delta`` absteigend."""
    return sorted(anomalies, key=lambda a: (_DIRECTION_ORDER[a["direction"]], -abs(a["delta"]), a["date"]))


def detect_anomalies(
    series: List[Dict[str, Any]],
    *,
    company_id: int,
    source: str,
    dimension: str = OVERALL_DIMENSION,
    penalty: float = DEFAULT_PENALTY,
    min_delta: float = DEFAULT_MIN_DELTA,
    model: str = DEFAULT_MODEL,
    min_size: int = DEFAULT_MIN_SIZE,
) -> List[Dict[str, Any]]:
    """Anomalien einer fertigen Monatsreihe; reine Funktion ohne DB-Zugriff.

    Prüft die Eignung nicht; das übernimmt ``company_anomalies``.
    """
    evaluated = [m for m in series if m.get("evaluated") and m.get("mean") is not None]
    values = [float(m["mean"]) for m in evaluated]
    result = detect_changepoints(values, PeltDetector(model=model, min_size=min_size, penalty=penalty))
    params = {**result.params, "min_delta": min_delta}

    anomalies: List[Dict[str, Any]] = []
    for shift in level_shifts(values, result.indices):
        delta = shift["delta"]
        if abs(delta) < min_delta:
            continue
        period = evaluated[shift["index"]]["period"]
        n_before = _n_values(evaluated[shift["before_start"]:shift["index"]])
        n_after = _n_values(evaluated[shift["index"]:shift["after_end"]])
        anomalies.append({
            "id": f"{source}:{dimension}:{period}",
            "company_id": company_id,
            "source": source,
            "dimension": dimension,
            "date": period,
            "direction": "fall" if delta < 0 else "rise",
            "delta": round(delta, 3),
            "before_mean": round(shift["before_mean"], 3),
            "after_mean": round(shift["after_mean"], 3),
            "n_reviews_before": n_before,
            "n_reviews_after": n_after,
            "n_reviews": n_before + n_after,
            "severity": _severity(delta),
            "method": result.method,
            "params": params,
        })
    return sort_anomalies(anomalies)


def company_anomalies(
    company_id: int,
    source: str = "employee",
    dimension: str = OVERALL_DIMENSION,
    penalty: float = DEFAULT_PENALTY,
    min_delta: float = DEFAULT_MIN_DELTA,
) -> Dict[str, Any]:
    """Reihe, Eignung und Anomalien eines Unternehmens aus der Datenbank.

    ValueError bei ungültiger Quelle oder Dimension (aus ``monthly_series``).
    """
    data = monthly_series(company_id, source, dimension)
    series = data["series"]
    elig = eligibility(series)
    anomalies = (
        detect_anomalies(
            series, company_id=company_id, source=source, dimension=dimension,
            penalty=penalty, min_delta=min_delta,
        )
        if elig["eligible"] else []
    )
    return {
        "company_id": company_id,
        "source": source,
        "dimension": dimension,
        "series": [
            {"period": m["period"], "mean": m["mean"], "count": m["count"], "evaluated": m["evaluated"]}
            for m in series
        ],
        "anomalies": anomalies,
        "params": {
            "method": "pelt",
            "model": DEFAULT_MODEL,
            "min_size": DEFAULT_MIN_SIZE,
            "penalty": penalty,
            "min_delta": min_delta,
            "min_reviews_per_month": data["min_reviews"],
        },
        "eligibility": elig,
    }


def company_anomalies_all(
    company_id: int,
    source: str = "employee",
    penalty: float = DEFAULT_PENALTY,
    min_delta: float = DEFAULT_MIN_DELTA,
) -> Dict[str, Any]:
    """Eignung und Anomalien aller Dimensionen einer Quelle (``dimension=all``).

    Ohne Monatsreihen, um die Antwort klein zu halten; die Reihe einer
    Dimension liefert ``company_anomalies``. ``anomalies`` ist die über alle
    Dimensionen zusammengeführte und nach ``sort_anomalies`` sortierte Liste.
    ValueError bei ungültiger Quelle.
    """
    series_by_dimension = monthly_series_by_dimension(company_id, source)
    dimensions: List[Dict[str, Any]] = []
    combined: List[Dict[str, Any]] = []
    for dimension, series in series_by_dimension.items():
        elig = eligibility(series)
        found = (
            detect_anomalies(
                series, company_id=company_id, source=source, dimension=dimension,
                penalty=penalty, min_delta=min_delta,
            )
            if elig["eligible"] else []
        )
        dimensions.append({"dimension": dimension, "eligibility": elig, "anomalies": found})
        combined.extend(found)
    return {
        "company_id": company_id,
        "source": source,
        "dimension": "all",
        "dimensions": dimensions,
        "anomalies": sort_anomalies(combined),
        "params": {
            "method": "pelt",
            "model": DEFAULT_MODEL,
            "min_size": DEFAULT_MIN_SIZE,
            "penalty": penalty,
            "min_delta": min_delta,
            "min_reviews_per_month": MIN_REVIEWS_PER_MONTH,
        },
    }


__all__ = [
    "DEFAULT_MIN_DELTA", "SEVERITY_HIGH",
    "eligibility", "sort_anomalies", "detect_anomalies", "company_anomalies", "company_anomalies_all",
]
