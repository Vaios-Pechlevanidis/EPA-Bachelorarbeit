"""
API-Routen für externe Belege im Ereignisfenster (Zyklus 2, Inkrement 4).

Ein Beleg ist eine zeitlich nahe Meldung mit Datum, Titel, Herausgeber und
Link. Die Routen behaupten keinen Zusammenhang mit den Bewertungen und bewerten
keine Meldung. Logik in ``services/evidence_service.py``; die Datenbank wird
nur gelesen, Meldungen kommen aus dem Belegspeicher oder (wenn erlaubt) aus
einem Abruf je Unternehmen und Monat.
"""

from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from services.evidence_service import (
    DEFAULT_WINDOW_AFTER,
    DEFAULT_WINDOW_BEFORE,
    EVIDENCE_NOTE,
    MAX_WINDOW_MONTHS,
    context_for_anchor,
    context_for_selection,
    load_global_events,
    paginate,
)

router = APIRouter(prefix="/api/analytics", tags=["Context"])

DEFAULT_LIMIT = 25
MAX_LIMIT = 200


def _window_params(window_before: int, window_after: int) -> dict:
    return {"window_before": window_before, "window_after": window_after}


@router.get("/company/{company_id}/anomalies/{anomaly_id}/context")
def get_anomaly_context(
    company_id: int,
    anomaly_id: str,
    source: Optional[str] = Query(None, description="Quelle; Standard aus anomaly_id"),
    dimension: Optional[str] = Query(None, description="Dimension; Standard aus anomaly_id"),
    status: Optional[str] = Query(None, description="Statusschlüssel der Bewertendengruppe (E13); ohne = alle"),
    dimension_only: bool = Query(False, description="Nur Belege zur Dimension (Schlüsselwort des Themas im Titel oder zugeordnete Ereignisart, 2026-10-23); braucht eine Einzeldimension"),
    window_before: int = Query(DEFAULT_WINDOW_BEFORE, ge=0, le=MAX_WINDOW_MONTHS, description="Monate vor dem Beginn des Übergangs (Standard 3)"),
    window_after: int = Query(DEFAULT_WINDOW_AFTER, ge=0, le=MAX_WINDOW_MONTHS, description="Monate nach dem markierten Monat (Standard 1)"),
    limit: int = Query(DEFAULT_LIMIT, ge=1, le=MAX_LIMIT, description="Belege je Seite"),
    offset: int = Query(0, ge=0, description="Erster Beleg der Seite"),
):
    """
    Externe Belege im Ereignisfenster einer auffälligen Veränderung oder eines
    auffälligen Einzelmonats (Kennung ``…:einzelmonat``)::

        {
          "company_id", "company", "search_term",
          "anchor": {"kind": "niveauwechsel" | "einzelmonat", "id", "source", "dimension", "status",
                     "date", "direction", "previous_period", "gap_months", ...},
          "window": {"kind", "from", "to", "months", "transition_from", "anchor_from", "anchor_to",
                     "window_before", "window_after", "anchor"},
          "items": [{"id", "date", "datetime", "title", "publisher", "url", "source", "source_type",
                     "reliability", "language", "issuer", "category"}, ...],   # neueste zuerst, eine Seite
          "total", "offset", "limit",
          "counts": {"news", "adhoc", "global"},
          "sources": {"gnews": {"label", "status", "months", "from_store", "fetched_now", "missing",
                                "stale", "errors": [{"month", "error"}], "fetched_at"}, ...},
          "coverage": true | false,      # mindestens eine Meldung oder Ad-hoc-Mitteilung (allgemeine Ereignisse zählen nicht)
          "reason": null | "...",         # Grund ohne Beleg
          "note": "Belege sind zeitlich nahe Meldungen ..."
        }

    Das Fenster reicht von ``window_before`` Monaten vor dem Beginn des Übergangs
    (Monat nach ``previous_period``; ohne Lücke der markierte Monat) bis
    ``window_after`` Monate nach dem markierten Monat (E18). Unbekannte Kennung:
    404; keine Daten: leere Liste mit ``reason``, kein 500. Ungültige Quelle,
    Dimension, Status oder Monate: 400, jeweils ``{"detail": ...}``.

    Dimension als globaler Filter (2026-10-23): ``dimension_only=true`` lässt nur Belege
    übrig, die zur Einzeldimension der Veränderung gehören (``services/dimension_scope.py``);
    jeder Beleg trägt dann ``dimension_match`` (``terms``, ``category``), die Antwort
    ``scope`` (``dimension``, ``topic``, ``n_all``, ``n_dimension``, ``note``); ``total``,
    ``counts`` und ``coverage`` zählen nur diese Belege. Mit der Gesamtbewertung: 400.
    """
    try:
        result = context_for_anchor(
            company_id, anomaly_id, source=source, dimension=dimension, status=status,
            dimension_only=dimension_only, **_window_params(window_before, window_after),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Error loading context: {str(e)}")
    if result is None:
        raise HTTPException(status_code=404, detail=f"Unternehmen {company_id} nicht gefunden.")
    if result.get("anchor") is None:
        raise HTTPException(status_code=404, detail=f"Auffällige Veränderung '{anomaly_id}' nicht gefunden.")
    return paginate(result, offset, limit)


@router.get("/company/{company_id}/context")
def get_selection_context(
    company_id: int,
    from_: str = Query(..., alias="from", description="Erster Monat der Auswahl (YYYY-MM)"),
    to: str = Query(..., description="Letzter Monat der Auswahl (YYYY-MM, einschließlich)"),
    source: Optional[str] = Query(None, description="Quelle der Dimension (Standard employee); nur mit dimension"),
    dimension: Optional[str] = Query(None, description="Einzeldimension für dimension_only (2026-10-23)"),
    dimension_only: bool = Query(False, description="Nur Belege zur Dimension (Schlüsselwort des Themas im Titel oder zugeordnete Ereignisart); braucht dimension"),
    window_before: int = Query(DEFAULT_WINDOW_BEFORE, ge=0, le=MAX_WINDOW_MONTHS, description="Monate vor der Auswahl (Standard 3)"),
    window_after: int = Query(DEFAULT_WINDOW_AFTER, ge=0, le=MAX_WINDOW_MONTHS, description="Monate nach der Auswahl (Standard 1)"),
    limit: int = Query(DEFAULT_LIMIT, ge=1, le=MAX_LIMIT, description="Belege je Seite"),
    offset: int = Query(0, ge=0, description="Erster Beleg der Seite"),
):
    """
    Externe Belege im Ereignisfenster einer frei gewählten Auswahl (E17): dieselbe
    Antwort wie bei einer Veränderung, ``anchor`` ist ``{"kind": "auswahl", "from", "to"}``
    und das Fenster reicht von ``window_before`` Monaten vor ``from`` bis ``window_after``
    Monate nach ``to``. Unbekanntes Unternehmen: 404; ungültige Monate: 400.
    ``source``, ``dimension`` und ``dimension_only`` wie bei der Veränderung (2026-10-23):
    nur Belege zur Dimension, mit ``dimension_match`` je Beleg und ``scope``.
    """
    try:
        result = context_for_selection(
            company_id, from_, to, source=source, dimension=dimension, dimension_only=dimension_only,
            **_window_params(window_before, window_after),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Error loading context: {str(e)}")
    if result is None:
        raise HTTPException(status_code=404, detail=f"Unternehmen {company_id} nicht gefunden.")
    return paginate(result, offset, limit)


@router.get("/global-events")
def get_global_events(
    all_events: bool = Query(False, alias="all", description="ohne Wirkung seit E29 (alle Ereignisse gelten als bestätigt)"),
):
    """
    Allgemeine Ereignisse, seit 2026-10-13 automatisch aus amtlichen Wirtschaftsdaten
    (E29, ``services/macro_events.py``: Konjunktureinbruch nach dem ESI, Inflationsschub
    nach der HVPI-Rate, Eurostat)::

        {"events": [{"id", "date_from", "date_to", "title", "scope", "note", "url", "confirmed"}, ...],
         "n_confirmed", "basis": {"fetched_at", "sources"}, "note"}

    Die Ereignisse erscheinen im Ereignisfenster als Belege vom Typ ``global``
    (Verlässlichkeit ``hypothese``) und als einblendbares Overlay im Diagramm der
    Detailseite, beschriftet als „Allgemeines Ereignis, Hypothese“.
    """
    from services import macro_events

    events = load_global_events(confirmed_only=not all_events)
    return {
        "events": events,
        "n_confirmed": sum(1 for e in events if e.get("confirmed") is True),
        "basis": macro_events.status(),
        "note": EVIDENCE_NOTE,
    }
