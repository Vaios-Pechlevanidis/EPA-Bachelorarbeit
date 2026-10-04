"""
Einzelbewertungen eines Unternehmens für den Drill-down (Zyklus 2, Inkrement 2).

- ``build_full_review(row)``: das Format ``fullReview``, das ``ReviewDetailModal``
  im Frontend anzeigt. Es war bis Inkrement 1 in ``analyze_topic`` eingebettet;
  jetzt bauen Themenübersicht und Bewertungsliste es hier.
- Bewertendengruppe: Quelle (``employee``, ``candidates``) und Status. Die
  Statuswerte in der Datenbank sind uneinheitlich (Stand 2026-10-04, nur lesend
  geprüft): Mitarbeitende ``1.0``, ``0.0``, ``True``, ``False``, ``Angestellt``,
  ``Ex-Angestellt`` und leer; Bewerbende ``hired``, ``offerDeclined``,
  ``rejected``, ``deferred``, ``Bewerber`` (nur Demo) und leer.
  ``normalize_status`` führt sie auf feste Schlüssel zurück (Vorbild:
  ``formatStatus`` in ``ReviewDetailModal.jsx``).
- ``fetch_reviews``: Bewertungen eines Zeitraums, vollständig paginiert,
  gefiltert nach Status, sortiert nach Datum absteigend.

Die Datenbank wird nur gelesen.
"""

from __future__ import annotations

import html
import re
from datetime import date, timedelta
from typing import Any, Dict, List, Optional

from services.topic_average_rating_service import _fetch_all_rows

# ── Text ────────────────────────────────────────────────────────────────────


def clean_html_text(text: str) -> str:
    """
    Clean HTML entities and tags from text.
    Removes <br/>, <br>, and other HTML tags, and decodes HTML entities.
    """
    if not text or not isinstance(text, str):
        return text

    # Decode HTML entities (&lt; &gt; &amp; etc.)
    text = html.unescape(text)

    # Replace <br/>- or <br>- patterns (bullet points with br tags)
    text = re.sub(r'<br\s*/?\s*>\s*-\s*', '\n• ', text, flags=re.IGNORECASE)

    # Replace remaining <br/>, <br>, <br /> with newlines
    text = re.sub(r'<br\s*/?\s*>', '\n', text, flags=re.IGNORECASE)

    # Remove any other HTML tags
    text = re.sub(r'<[^>]+>', '', text)

    # Clean up patterns like "- text -" at line boundaries (incomplete bullet points)
    text = re.sub(r'^-\s*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'^-\s+', '• ', text, flags=re.MULTILINE)

    # Clean up multiple newlines (max 2 consecutive newlines)
    text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)

    # Remove trailing dashes and whitespace from lines
    text = re.sub(r'\s+-\s*$', '', text, flags=re.MULTILINE)

    # Trim whitespace
    text = text.strip()

    return text


def build_full_review(row: Dict[str, Any]) -> Dict[str, Any]:
    """Format ``fullReview`` einer Bewertungszeile (unverändert aus ``analyze_topic``).

    ``sourceType`` ergibt sich wie bisher aus der Spalte
    ``gut_am_arbeitgeber_finde_ich``: vorhanden = Mitarbeiter, sonst Bewerber.
    """
    source_type = "Mitarbeiter" if 'gut_am_arbeitgeber_finde_ich' in row else "Bewerber"
    employer_status = row.get("status", "Unbekannt")
    return {
        "titel": clean_html_text(row.get("titel", "Keine Titel")),
        "datum": row.get("datum"),
        "durchschnittsbewertung": row.get("durchschnittsbewertung"),
        "status": employer_status,
        "sourceType": source_type,
        "gut_am_arbeitgeber": clean_html_text(row.get("gut_am_arbeitgeber_finde_ich", "")),
        "schlecht_am_arbeitgeber": clean_html_text(row.get("schlecht_am_arbeitgeber_finde_ich", "")),
        "verbesserungsvorschlaege": clean_html_text(row.get("verbesserungsvorschlaege", "")),
        "stellenbeschreibung": clean_html_text(row.get("stellenbeschreibung", "")),
        "jobbeschreibung": clean_html_text(row.get("jobbeschreibung", "")),
        # Include all star ratings
        "ratings": {
            "arbeitsatmosphaere": row.get("sternebewertung_arbeitsatmosphaere"),
            "image": row.get("sternebewertung_image"),
            "work_life_balance": row.get("sternebewertung_work_life_balance"),
            "karriere_weiterbildung": row.get("sternebewertung_karriere_weiterbildung"),
            "gehalt_sozialleistungen": row.get("sternebewertung_gehalt_sozialleistungen"),
            "kollegenzusammenhalt": row.get("sternebewertung_kollegenzusammenhalt"),
            "umwelt_sozialbewusstsein": row.get("sternebewertung_umwelt_sozialbewusstsein"),
            "vorgesetztenverhalten": row.get("sternebewertung_vorgesetztenverhalten"),
            "kommunikation": row.get("sternebewertung_kommunikation"),
            "interessante_aufgaben": row.get("sternebewertung_interessante_aufgaben"),
            "umgang_mit_aelteren_kollegen": row.get("sternebewertung_umgang_mit_aelteren_kollegen"),
            "arbeitsbedingungen": row.get("sternebewertung_arbeitsbedingungen"),
            "gleichberechtigung": row.get("sternebewertung_gleichberechtigung")
        }
    }


# Freitextfelder je Quelle in Anzeigereihenfolge (Textauszug, Stimmung).
TEXT_FIELDS_BY_SOURCE: Dict[str, List[str]] = {
    "employee": ["gut_am_arbeitgeber_finde_ich", "schlecht_am_arbeitgeber_finde_ich", "verbesserungsvorschlaege"],
    "candidates": ["stellenbeschreibung", "verbesserungsvorschlaege"],
}

PREVIEW_MAX_CHARS = 240


def review_text(row: Dict[str, Any], source: str) -> str:
    """Bereinigte Freitexte einer Bewertung, durch Leerzeile getrennt (ohne Titel)."""
    parts = [clean_html_text(row.get(f)) for f in TEXT_FIELDS_BY_SOURCE.get(source, [])]
    return "\n\n".join(p for p in parts if isinstance(p, str) and p.strip())


def review_preview(row: Dict[str, Any], source: str, max_chars: int = PREVIEW_MAX_CHARS) -> str:
    """Textauszug: Freitexte in einer Zeile, nach ``max_chars`` Zeichen gekürzt."""
    text = re.sub(r"\s+", " ", review_text(row, source)).strip()
    if len(text) > max_chars:
        text = text[: max_chars - 1].rstrip() + "…"
    return text


# ── Bewertendengruppe: Status ───────────────────────────────────────────────

UNKNOWN_STATUS = "unbekannt"

# Schlüssel → Anzeigename je Quelle, in Anzeigereihenfolge.
STATUS_LABELS: Dict[str, Dict[str, str]] = {
    "employee": {
        "angestellt": "Angestellt",
        "ex-angestellt": "Ex-Angestellt",
        UNKNOWN_STATUS: "ohne Angabe",
    },
    "candidates": {
        "eingestellt": "Eingestellt",
        "angebot-abgelehnt": "Angebot abgelehnt",
        "abgelehnt": "Abgelehnt",
        "zurueckgestellt": "Zurückgestellt",
        UNKNOWN_STATUS: "ohne Angabe",
    },
}

# Rohwert (klein, ohne Leerraum) → Schlüssel. "1.0"/"0.0" wie formatStatus im
# Frontend; "true"/"false" (nur Formycon) analog zu 1/0. "Bewerber" (nur
# Demo-Daten) sagt nichts über den Ausgang und zählt als "ohne Angabe".
_RAW_STATUS: Dict[str, Dict[str, str]] = {
    "employee": {
        "1": "angestellt", "1.0": "angestellt", "true": "angestellt", "angestellt": "angestellt",
        "0": "ex-angestellt", "0.0": "ex-angestellt", "false": "ex-angestellt",
    },
    "candidates": {
        "hired": "eingestellt",
        "offerdeclined": "angebot-abgelehnt",
        "rejected": "abgelehnt",
        "deferred": "zurueckgestellt",
    },
}


def normalize_status(source: str, raw: Any) -> str:
    """Statusschlüssel einer Bewertung; unbekannte oder leere Werte → ``unbekannt``."""
    if raw is None:
        return UNKNOWN_STATUS
    s = str(raw).strip().lower()
    if not s:
        return UNKNOWN_STATUS
    if source == "employee" and re.match(r"^ex[-\s]?angestell", s):
        return "ex-angestellt"
    return _RAW_STATUS.get(source, {}).get(s, UNKNOWN_STATUS)


def validate_status(source: str, status: Optional[str]) -> Optional[str]:
    """Prüft einen Statusschlüssel für die Quelle; None bleibt None (alle).

    ValueError bei unbekanntem Schlüssel.
    """
    if status is None:
        return None
    allowed = STATUS_LABELS.get(source)
    if allowed is None:
        raise ValueError(f"source '{source}' ungültig; erlaubt: {', '.join(STATUS_LABELS)}.")
    if status not in allowed:
        raise ValueError(f"status '{status}' ist für source '{source}' unbekannt; erlaubt: {', '.join(allowed)}.")
    return status


def filter_by_status(rows: List[Dict[str, Any]], source: str, status: Optional[str]) -> List[Dict[str, Any]]:
    """Zeilen der Bewertendengruppe ``status``; None lässt alle Zeilen durch."""
    if status is None:
        return rows
    return [r for r in rows if normalize_status(source, r.get("status")) == status]


# ── Zeitraum ────────────────────────────────────────────────────────────────


def parse_day(value: Optional[str], name: str) -> Optional[date]:
    """``YYYY-MM-DD`` als Datum; ValueError mit Parameternamen bei falschem Format."""
    if value is None:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise ValueError(f"{name} '{value}' ist kein Datum im Format YYYY-MM-DD.") from None


def fetch_review_rows_in_range(
    source: str,
    company_id: int,
    start: Optional[date] = None,
    end: Optional[date] = None,
    columns: str = "*",
) -> List[Dict[str, Any]]:
    """Alle Zeilen eines Unternehmens mit ``start <= datum <= end`` (beide
    einschließlich, Tagesgenauigkeit), vollständig paginiert, nur SELECT.

    ``end`` wird als ``datum < end + 1 Tag`` abgefragt, damit auch Zeitstempel im
    Laufe des letzten Tages erfasst sind (``datum`` ist in der Datenbank ein
    Zeitstempel). Ohne Grenzen sind auch Zeilen ohne ``datum`` enthalten.
    """
    from database.supabase_client import get_supabase_client  # lazy, damit Tests ohne DB laufen

    query = get_supabase_client().table(source).select(columns).eq("company_id", company_id)
    if start is not None:
        query = query.gte("datum", start.isoformat())
    if end is not None:
        query = query.lt("datum", (end + timedelta(days=1)).isoformat())
    return _fetch_all_rows(query.order("id"), page_size=1000)  # id: stabile Reihenfolge für range()


def sort_newest_first(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Nach ``datum`` absteigend, bei gleichem Datum nach ``id`` absteigend;
    Zeilen ohne Datum zuletzt."""
    with_date = sorted(
        (r for r in rows if r.get("datum")),
        key=lambda r: (str(r["datum"]), r.get("id") or 0),
        reverse=True,
    )
    return with_date + [r for r in rows if not r.get("datum")]


def full_review_item(row: Dict[str, Any], source: str) -> Dict[str, Any]:
    """Listeneintrag im Format der Themenübersicht: ``id``, ``preview``, ``fullReview``."""
    return {"id": row.get("id"), "preview": review_preview(row, source), "fullReview": build_full_review(row)}


__all__ = [
    "clean_html_text", "build_full_review", "TEXT_FIELDS_BY_SOURCE", "review_text", "review_preview",
    "UNKNOWN_STATUS", "STATUS_LABELS", "normalize_status", "validate_status", "filter_by_status",
    "parse_day", "fetch_review_rows_in_range", "sort_newest_first", "full_review_item",
]
