"""
API-Routen für Aktienkurs und Kennzahlen als Einordnung (Zyklus 2, Inkrement 3,
E15) und für das Aktien-Dashboard (E16: Empfehlungen, Umsatz und Gewinn, Nachrichten).

Kurs und Kennzahlen zeigen das Marktumfeld; ein Zusammenhang mit den
Bewertungen wird weder behauptet noch berechnet. Logik in
``services/context_service.py``; die Datenbank wird nur gelesen.
"""

from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from services.context_service import company_finance, company_market
from services.news_service import company_news

router = APIRouter(prefix="/api/analytics", tags=["Market"])


@router.get("/company/{company_id}/market")
def get_company_market(
    company_id: int,
    start: Optional[str] = Query(None, description="Erster Monat (YYYY-MM, einschließlich)"),
    end: Optional[str] = Query(None, description="Letzter Monat (YYYY-MM, einschließlich)"),
):
    """
    Monatsschlusskurse und Kennzahlen eines Unternehmens::

        {
          "company_id": 19, "ticker": "SAP.DE", "ticker_scope": "eigene Aktie",
          "ticker_name": "SAP SE", "currency": "EUR",
          "available": true, "reason": null,
          "prices": [{"period": "2024-01", "close": 165.3}, ...],
          "metrics": {...},
          "fetched_at": "2026-10-04T15:57:26+00:00",
          "source": "Yahoo Finance über yfinance 1.7.0"
        }

    Kurse sind um Splits und Dividenden bereinigt (Monatsschluss); der Monat
    des Abrufs fehlt. ``ticker_scope`` ist ``"eigene Aktie"`` oder
    ``"Konzernmutter"`` (Kurs des Mutterkonzerns, z. B. NTT DATA SE).

    Ohne Ticker (nicht börsennotiert, Demo) oder ohne abrufbare Kurse:
    ``available: false`` mit Begründung in ``reason``, Status 200. Unbekanntes
    Unternehmen: 404; ``start``/``end`` nicht im Format YYYY-MM oder
    ``start`` nach ``end``: 400, jeweils ``{"detail": ...}``.
    """
    try:
        result = company_market(company_id, start=start, end=end)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading market data: {str(e)}")
    if result is None:
        raise HTTPException(status_code=404, detail=f"Unternehmen {company_id} nicht gefunden.")
    return result


@router.get("/company/{company_id}/finance")
def get_company_finance(company_id: int):
    """
    Daten des Aktien-Dashboards (E16): alle Felder von ``/market`` (ganze
    Kursreihe) und zusätzlich::

        "analysts": {"as_of": "2026-10-04",
                     "months": [{"month": "2026-07", "strong_buy": 3, "buy": 20, "hold": 4,
                                 "sell": 0, "strong_sell": 0, "total": 27}, ...]} | null,
        "earnings": {"currency": "EUR",
                     "annual": [{"period_end": "2025-12-31", "revenue": 3.68e10,
                                 "net_income": 7.16e9}, ...],
                     "quarterly": [...]} | null

    ``null``, wenn yfinance die Angaben nicht liefert oder der Zwischenspeicher
    sie noch nicht enthält. Fehlerfälle wie bei ``/market``.
    """
    try:
        result = company_finance(company_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading finance data: {str(e)}")
    if result is None:
        raise HTTPException(status_code=404, detail=f"Unternehmen {company_id} nicht gefunden.")
    return result


@router.get("/company/{company_id}/news")
def get_company_news(company_id: int):
    """
    Aktuelle Meldungen zum Unternehmen (E16), Quelle Google-News-RSS::

        {"company_id", "query", "available", "reason", "stale",
         "items": [{"title", "source", "url", "published_at"}, ...],   # neueste zuerst
         "fetched_at", "source", "window_days"}

    Die Meldungen werden keiner Veränderung der Bewertungen zugeordnet. Ohne
    Treffer oder ohne Abruf ``available: false`` mit Grund (Status 200);
    ``stale: true``, wenn ein älterer Stand gezeigt wird. Unbekanntes Unternehmen: 404.
    """
    try:
        result = company_news(company_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading news: {str(e)}")
    if result is None:
        raise HTTPException(status_code=404, detail=f"Unternehmen {company_id} nicht gefunden.")
    return result
