"""
API-Routen für eigene Ereignisse (2026-10-17, E32):
GET/POST   /api/companies/{company_id}/events
PUT/DELETE /api/companies/{company_id}/events/{event_id}

Logik in ``services/user_events_service.py``. Eingabefehler → 400 mit deutschem
Text, unbekanntes Unternehmen oder Ereignis → 404, fehlende Tabelle (Migration
007 nicht ausgeführt) → 503 mit Hinweis auf die Migrationsdatei.
"""

from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services import user_events_service as svc

router = APIRouter(prefix="/api/companies", tags=["User events"])


class UserEventIn(BaseModel):
    """Eingabe eines eigenen Ereignisses; die Prüfung übernimmt der Service (deutsche Meldungen)."""

    title: Optional[str] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    note: Optional[str] = None


def _client_or_503():
    # Lazy wie in rating_series_service: Tests schalten database.supabase_client
    # auf den In-Memory-Store um, nachdem dieses Modul importiert wurde.
    from database.supabase_client import get_supabase_client

    return get_supabase_client()


def _require_company(client, company_id: int) -> None:
    if not svc.company_exists(client, company_id):
        raise HTTPException(status_code=404, detail=f"Unternehmen {company_id} nicht gefunden.")


def _handle(fn):
    """Service-Fehler in HTTP-Antworten übersetzen."""
    try:
        return fn()
    except svc.MissingTableError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{company_id}/events")
def list_user_events(company_id: int):
    """
    Eigene Ereignisse eines Unternehmens, sortiert nach Beginn::

        {"company_id", "events": [{"id", "company_id", "date_from", "date_to", "title", "note",
                                   "created_at", "updated_at", "months"}, ...], "note"}
    """
    client = _client_or_503()
    _require_company(client, company_id)
    events = _handle(lambda: svc.list_events(client, company_id))
    return {"company_id": company_id, "events": events, "note": svc.USER_EVENT_NOTE}


@router.post("/{company_id}/events", status_code=201)
def create_user_event(company_id: int, body: UserEventIn):
    """Neues Ereignis; Antwort ist der gespeicherte Eintrag."""
    client = _client_or_503()
    _require_company(client, company_id)
    return _handle(lambda: svc.create_event(client, company_id, body.model_dump()))


@router.put("/{company_id}/events/{event_id}")
def update_user_event(company_id: int, event_id: int, body: UserEventIn):
    """Ereignis ändern (alle Felder); Antwort ist der gespeicherte Eintrag."""
    client = _client_or_503()
    _require_company(client, company_id)
    updated = _handle(lambda: svc.update_event(client, company_id, event_id, body.model_dump()))
    if updated is None:
        raise HTTPException(status_code=404, detail=f"Ereignis {event_id} nicht gefunden.")
    return updated


@router.delete("/{company_id}/events/{event_id}")
def delete_user_event(company_id: int, event_id: int):
    """Ereignis löschen; Antwort ``{"deleted": id}``."""
    client = _client_or_503()
    _require_company(client, company_id)
    if not _handle(lambda: svc.delete_event(client, company_id, event_id)):
        raise HTTPException(status_code=404, detail=f"Ereignis {event_id} nicht gefunden.")
    return {"deleted": event_id, "company_id": company_id}
