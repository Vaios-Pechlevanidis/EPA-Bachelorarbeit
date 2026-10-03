"""
API-Route für auffällige Veränderungen im Bewertungsverlauf (Zyklus 2, Inkrement 1).

Live berechnet aus der Monatsreihe (E3/E4), ohne Cache-Tabelle; die Datenbank
wird nur gelesen. Logik in ``services/anomaly_service.py``.
"""

from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from models.changepoint_detector import DEFAULT_PENALTY
from services.anomaly_service import DEFAULT_MIN_DELTA, company_anomalies
from services.rating_series_service import OVERALL_DIMENSION

router = APIRouter(prefix="/api/analytics", tags=["Anomalies"])


@router.get("/company/{company_id}/anomalies")
def get_company_anomalies(
    company_id: int,
    source: str = Query("employee", description="Quelle: employee oder candidates"),
    dimension: str = Query(OVERALL_DIMENSION, description="Dimension aus DIMENSIONS_BY_SOURCE"),
    penalty: Optional[float] = Query(None, gt=0, description=f"PELT-Strafterm (Standard {DEFAULT_PENALTY})"),
    min_delta: Optional[float] = Query(None, ge=0, description=f"Mindestbetrag der Veränderung in Sternen (Standard {DEFAULT_MIN_DELTA})"),
):
    """
    Monatsverlauf und auffällige Veränderungen (Niveauwechsel) einer Dimension.

    Antwort: ``series`` (period, mean, count, evaluated), ``anomalies``
    (fall vor rise, nach Betrag von delta), ``params`` und ``eligibility``.
    Nicht geeignete Reihen (weniger als 12 bewertete Monate) liefern eine
    leere Anomalieliste mit Begründung.
    """
    try:
        return company_anomalies(
            company_id,
            source=source,
            dimension=dimension,
            penalty=DEFAULT_PENALTY if penalty is None else penalty,
            min_delta=DEFAULT_MIN_DELTA if min_delta is None else min_delta,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error detecting anomalies: {str(e)}")
