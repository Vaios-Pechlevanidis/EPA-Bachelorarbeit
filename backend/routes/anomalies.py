"""
API-Route für auffällige Veränderungen im Bewertungsverlauf (Zyklus 2, Inkrement 1).

Live berechnet aus der Monatsreihe (E3/E4), ohne Cache-Tabelle; die Datenbank
wird nur gelesen. Logik in ``services/anomaly_service.py``.
"""

from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from models.changepoint_detector import DEFAULT_PENALTY
from services.anomaly_service import DEFAULT_MIN_DELTA, company_anomalies, company_anomalies_all
from services.rating_series_service import OVERALL_DIMENSION

router = APIRouter(prefix="/api/analytics", tags=["Anomalies"])


@router.get("/company/{company_id}/anomalies")
def get_company_anomalies(
    company_id: int,
    source: str = Query("employee", description="Quelle: employee oder candidates"),
    dimension: str = Query(OVERALL_DIMENSION, description="Dimension aus DIMENSIONS_BY_SOURCE oder 'all'"),
    penalty: Optional[float] = Query(None, gt=0, description=f"PELT-Strafterm (Standard {DEFAULT_PENALTY})"),
    min_delta: Optional[float] = Query(None, ge=0, description=f"Mindestbetrag der Veränderung in Sternen (Standard {DEFAULT_MIN_DELTA})"),
):
    """
    Monatsverlauf und auffällige Veränderungen (Niveauwechsel).

    **Eine Dimension** (Standard ``durchschnittsbewertung``)::

        {
          "company_id": 18, "source": "employee", "dimension": "durchschnittsbewertung",
          "series": [{"period": "2022-01", "mean": 4.235, "count": 13, "n_values": 13,
                      "evaluated": true}, ...],   # evaluated: n_values >= min_reviews_per_month
          "anomalies": [{"id", "company_id", "source", "dimension", "date", "direction",
                         "delta", "before_mean", "after_mean", "n_reviews_before",
                         "n_reviews_after", "n_reviews", "severity", "method", "params"}, ...],
          "params": {"method", "model", "min_size", "penalty", "min_delta", "min_reviews_per_month"},
          "eligibility": {"eligible", "evaluated_months", "min_evaluated_months", "reason"}
        }

    **Alle Dimensionen** (``dimension=all``), ohne Monatsreihen::

        {
          "company_id": 18, "source": "employee", "dimension": "all",
          "dimensions": [{"dimension": "durchschnittsbewertung",
                          "eligibility": {...}, "anomalies": [...]}, ...],
          "anomalies": [...],   # alle Dimensionen zusammen, sortiert
          "params": {...}
        }

    ``dimensions`` folgt der Reihenfolge von ``DIMENSIONS_BY_SOURCE[source]``.
    ``anomalies`` ist sortiert: fall vor rise, dann nach Betrag von delta.
    Nicht geeignete Reihen (weniger als 12 bewertete Monate) liefern eine
    leere Anomalieliste mit Begründung in ``eligibility.reason``.
    Ungültige ``source`` oder ``dimension``: 400 ``{"detail": ...}``.
    """
    penalty = DEFAULT_PENALTY if penalty is None else penalty
    min_delta = DEFAULT_MIN_DELTA if min_delta is None else min_delta
    try:
        if dimension == "all":
            return company_anomalies_all(company_id, source=source, penalty=penalty, min_delta=min_delta)
        return company_anomalies(
            company_id,
            source=source,
            dimension=dimension,
            penalty=penalty,
            min_delta=min_delta,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error detecting anomalies: {str(e)}")
