"""
API-Route für auffällige Veränderungen im Bewertungsverlauf (Zyklus 2, Inkrement 1).

Live berechnet aus der Monatsreihe (E3/E4), ohne Cache-Tabelle; die Datenbank
wird nur gelesen. Logik in ``services/anomaly_service.py``; der
Vorher-Nachher-Vergleich (Inkrement 2) in ``services/explanation_service.py``.
"""

from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from models.changepoint_detector import DEFAULT_PENALTY_FACTOR
from services.anomaly_service import DEFAULT_MIN_DELTA, company_anomalies, company_anomalies_all
from services.explanation_service import DEFAULT_WINDOW_MONTHS, explain_anomaly
from services.rating_series_service import OVERALL_DIMENSION

router = APIRouter(prefix="/api/analytics", tags=["Anomalies"])


@router.get("/company/{company_id}/anomalies")
def get_company_anomalies(
    company_id: int,
    source: str = Query("employee", description="Quelle: employee oder candidates"),
    dimension: str = Query(OVERALL_DIMENSION, description="Dimension aus DIMENSIONS_BY_SOURCE oder 'all'"),
    penalty: Optional[float] = Query(None, gt=0, description="Fester PELT-Strafterm in quadrierten Sternen; schaltet auf den festen Modus"),
    penalty_factor: Optional[float] = Query(None, gt=0, description=f"Faktor des skalierten Strafterms Faktor · sigma² · ln(n) (Standard {DEFAULT_PENALTY_FACTOR})"),
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
                         "n_reviews_after", "n_reviews", "severity", "before_from", "after_to",
                         "previous_period", "gap_months", "month_mean",
                         "month_near_previous_level", "method", "params"}, ...],
          "params": {"method", "model", "min_size", "penalty", "penalty_mode", "penalty_factor",
                     "noise_sigma", "n_evaluated", "min_delta", "min_reviews_per_month"},
          "eligibility": {"eligible", "evaluated_months", "min_evaluated_months", "reason"}
        }

    **Alle Dimensionen** (``dimension=all``), ohne Monatsreihen::

        {
          "company_id": 18, "source": "employee", "dimension": "all",
          "dimensions": [{"dimension": "durchschnittsbewertung",
                          "eligibility": {...}, "anomalies": [...],
                          "params": {...}},   # je Dimension eigenes noise_sigma, n, penalty
                         ...],
          "anomalies": [...],   # alle Dimensionen zusammen, sortiert
          "params": {...}
        }

    **Strafterm:** Standard ist der skalierte Modus ``penalty = penalty_factor ·
    sigma² · ln(n)`` je Reihe (``sigma`` = robuste Streuung der bewerteten
    Monatsmittel aus den ersten Differenzen, ``n`` = bewertete Monate, Faktor 2,0).
    Wird ``penalty`` übergeben, gilt der feste Modus mit diesem Wert (Vorrang vor
    ``penalty_factor``). ``params`` nennt ``penalty_mode``, ``penalty_factor``,
    ``noise_sigma`` und den tatsächlich verwendeten ``penalty``.

    ``dimensions`` folgt der Reihenfolge von ``DIMENSIONS_BY_SOURCE[source]``.
    ``anomalies`` ist sortiert: fall vor rise, dann nach Betrag von delta.
    Nicht geeignete Reihen (weniger als 12 bewertete Monate) liefern eine
    leere Anomalieliste mit Begründung in ``eligibility.reason``.
    Ungültige ``source`` oder ``dimension``: 400 ``{"detail": ...}``.
    """
    penalty_factor = DEFAULT_PENALTY_FACTOR if penalty_factor is None else penalty_factor
    min_delta = DEFAULT_MIN_DELTA if min_delta is None else min_delta
    try:
        if dimension == "all":
            return company_anomalies_all(
                company_id, source=source, penalty=penalty, min_delta=min_delta, penalty_factor=penalty_factor,
            )
        return company_anomalies(
            company_id,
            source=source,
            dimension=dimension,
            penalty=penalty,
            min_delta=min_delta,
            penalty_factor=penalty_factor,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error detecting anomalies: {str(e)}")


@router.get("/company/{company_id}/anomalies/{anomaly_id}/explanations")
def get_anomaly_explanations(
    company_id: int,
    anomaly_id: str,
    source: Optional[str] = Query(None, description="Quelle; Standard aus anomaly_id"),
    dimension: Optional[str] = Query(None, description="Dimension; Standard aus anomaly_id"),
    window_months: int = Query(DEFAULT_WINDOW_MONTHS, ge=1, le=36, description=f"Monate je Vergleichsfenster (Standard {DEFAULT_WINDOW_MONTHS}, E12)"),
):
    """
    Vorher-Nachher-Vergleich einer auffälligen Veränderung (Inkrement 2).

    Die Veränderungen werden mit den Standardparametern neu berechnet und
    ``anomaly_id`` (``"{source}:{dimension}:{YYYY-MM}"``) darunter gesucht::

        {
          "company_id", "source", "dimension",
          "anomaly": {...},                       # wie in /anomalies
          "windows": {"window_months": 6,
                      "before": {"from", "to", "start", "end", "months", "n_reviews"},
                      "after": {...}},
          "comparison": {"before": {"n_reviews", "mean_rating", "n_rated", "sentiment"},
                         "after": {...}, "rating_shift", "polarity_shift",
                         "topics": [{"topic", "before": {"mentions", "share", "sentiment"},
                                     "after": {...}, "share_shift_pp", "polarity_shift",
                                     "low_basis"}, ...],
                         "low_basis", "low_basis_rule", "sentiment_mode", "sentiment_sample"},
          "explanations": []                      # folgt in Inkrement 5
        }

    Der Vergleich beschreibt Veränderungen in den Bewertungen, keine Ursachen.
    Unbekannte ``anomaly_id``: 404; ungültige Quelle oder Dimension: 400.
    """
    try:
        result = explain_anomaly(company_id, anomaly_id, source=source, dimension=dimension, window_months=window_months)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error comparing periods: {str(e)}")
    if result is None:
        raise HTTPException(status_code=404, detail=f"Auffällige Veränderung '{anomaly_id}' nicht gefunden.")
    return result
