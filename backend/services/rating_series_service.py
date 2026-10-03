"""
Monatsreihen der Kununu-Bewertungen je Unternehmen, Quelle und Dimension.

Eingabe für die Anomalieerkennung in Zyklus 2 (Inkrement 1). Die Reihe ist in
``docs/entscheidungen.md`` festgelegt:

- E3: Je Kalendermonat das arithmetische Mittel der Spalte
  ``durchschnittsbewertung`` (Gesamtbewertung) bzw. der jeweiligen
  ``sternebewertung_*``-Spalte (Einzeldimension) über alle Bewertungen des
  Monats. Bewertungen ohne ``datum`` werden ignoriert.
- E4: Ein Monat gilt als bewertet, wenn sein Mittel auf mindestens
  ``MIN_REVIEWS_PER_MONTH`` = 5 Werten beruht. Eine Reihe ist für die
  automatische Erkennung geeignet, wenn sie mindestens
  ``MIN_EVALUATED_MONTHS`` = 12 bewertete Monate hat.

Die Reihe enthält jeden Kalendermonat zwischen der ersten und der letzten
datierten Bewertung, auch Monate ohne Bewertung (``count`` 0, ``mean`` None),
damit Lücken sichtbar bleiben. Je Monat werden geliefert:

- ``period``: Kalendermonat ``YYYY-MM``
- ``mean``: Monatsmittel (3 Nachkommastellen) oder None
- ``count``: Anzahl datierter Bewertungen im Monat
- ``n_values``: Anzahl nicht-leerer Werte der Spalte, auf denen ``mean`` beruht
  (bei Einzeldimensionen kann sie kleiner als ``count`` sein)
- ``evaluated``: ``n_values >= min_reviews``

Die Datenbank wird nur gelesen. Alle Zeilen werden seitenweise über
``_fetch_all_rows`` geladen, weil PostgREST höchstens 1000 Zeilen je Anfrage
liefert.

Verwendung::

    from services.rating_series_service import monthly_series, is_eligible

    result = monthly_series(company_id=3, source="employee")
    if is_eligible(result["series"]):
        ...  # Erkennung nur auf bewerteten Monaten
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from services.topic_average_rating_service import TOPIC_COLUMNS_BY_SOURCE, _fetch_all_rows

OVERALL_DIMENSION = "durchschnittsbewertung"
VALID_SOURCES = ("employee", "candidates")
DIMENSIONS_BY_SOURCE: Dict[str, List[str]] = {
    source: [OVERALL_DIMENSION] + list(TOPIC_COLUMNS_BY_SOURCE[source].keys())
    for source in VALID_SOURCES
}

MIN_REVIEWS_PER_MONTH = 5   # E4: bewerteter Monat
MIN_EVALUATED_MONTHS = 12   # E4: Mindestzahl bewerteter Monate für die Erkennung


# ── Spalten und Monate ──────────────────────────────────────────────────────

def value_column(source: str, dimension: str = OVERALL_DIMENSION) -> str:
    """DB-Spalte zu Quelle und Dimension; ValueError bei ungültiger Angabe."""
    if source not in VALID_SOURCES:
        raise ValueError(f"source '{source}' ungültig; erlaubt: {', '.join(VALID_SOURCES)}.")
    if dimension not in DIMENSIONS_BY_SOURCE[source]:
        raise ValueError(
            f"dimension '{dimension}' ist für source '{source}' unbekannt; "
            f"erlaubt: {', '.join(DIMENSIONS_BY_SOURCE[source])}."
        )
    if dimension == OVERALL_DIMENSION:
        return OVERALL_DIMENSION
    return TOPIC_COLUMNS_BY_SOURCE[source][dimension]


def month_key(datum_raw: Any) -> Optional[str]:
    """Kalendermonat ``YYYY-MM`` eines Datumswerts aus der DB oder None."""
    if not datum_raw:
        return None
    try:
        dt = datetime.fromisoformat(str(datum_raw).replace("Z", "+00:00"))
    except ValueError:
        return None
    return f"{dt.year:04d}-{dt.month:02d}"


def month_range(first: str, last: str) -> List[str]:
    """Alle Kalendermonate von ``first`` bis ``last`` einschließlich."""
    y, m = (int(x) for x in first.split("-"))
    last_y, last_m = (int(x) for x in last.split("-"))
    out: List[str] = []
    while (y, m) <= (last_y, last_m):
        out.append(f"{y:04d}-{m:02d}")
        m += 1
        if m == 13:
            y, m = y + 1, 1
    return out


# ── Reihenbildung ───────────────────────────────────────────────────────────

def build_monthly_series(
    rows: List[Dict[str, Any]],
    column: str = OVERALL_DIMENSION,
    min_reviews: int = MIN_REVIEWS_PER_MONTH,
) -> List[Dict[str, Any]]:
    """Monatsreihe aus Rohzeilen mit ``datum`` und ``column``.

    Reine Funktion ohne DB-Zugriff. Liefert eine leere Liste, wenn keine Zeile
    ein gültiges Datum hat.
    """
    sums: Dict[str, float] = {}
    n_values: Dict[str, int] = {}
    counts: Dict[str, int] = {}
    for row in rows:
        period = month_key(row.get("datum"))
        if period is None:
            continue
        counts[period] = counts.get(period, 0) + 1
        value = row.get(column)
        if value is None:
            continue
        try:
            v = float(value)
        except (TypeError, ValueError):
            continue
        sums[period] = sums.get(period, 0.0) + v
        n_values[period] = n_values.get(period, 0) + 1

    if not counts:
        return []

    series: List[Dict[str, Any]] = []
    for period in month_range(min(counts), max(counts)):
        n = n_values.get(period, 0)
        series.append({
            "period": period,
            "mean": round(sums[period] / n, 3) if n else None,
            "count": counts.get(period, 0),
            "n_values": n,
            "evaluated": n >= min_reviews,
        })
    return series


def fetch_review_rows(source: str, company_id: int, column: str) -> List[Dict[str, Any]]:
    """Alle Zeilen (id, datum, ``column``) eines Unternehmens aus der Tabelle
    ``source``; nur SELECT, vollständig paginiert. ``column`` darf eine
    kommagetrennte Spaltenliste sein (siehe ``monthly_series_by_dimension``)."""
    from database.supabase_client import get_supabase_client  # lazy, damit Tests ohne DB laufen

    query = (
        get_supabase_client()
        .table(source)
        .select(f"id,datum,{column}")
        .eq("company_id", company_id)
        .order("id")  # stabile Reihenfolge für die range()-Paginierung
    )
    return _fetch_all_rows(query, page_size=1000)


def monthly_series(
    company_id: int,
    source: str,
    dimension: str = OVERALL_DIMENSION,
    min_reviews: int = MIN_REVIEWS_PER_MONTH,
) -> Dict[str, Any]:
    """Monatsreihe eines Unternehmens direkt aus der Datenbank.

    Rückgabe: ``{"company_id", "source", "dimension", "column", "min_reviews",
    "evaluated_months", "series": [...]}``. ValueError bei ungültiger
    Quelle oder Dimension.
    """
    column = value_column(source, dimension)
    rows = fetch_review_rows(source, company_id, column)
    series = build_monthly_series(rows, column, min_reviews)
    return {
        "company_id": company_id,
        "source": source,
        "dimension": dimension,
        "column": column,
        "min_reviews": min_reviews,
        "evaluated_months": evaluated_months(series),
        "series": series,
    }


def monthly_series_by_dimension(
    company_id: int,
    source: str,
    min_reviews: int = MIN_REVIEWS_PER_MONTH,
) -> Dict[str, List[Dict[str, Any]]]:
    """Monatsreihen aller Dimensionen einer Quelle aus einer einzigen Abfrage.

    Rückgabe: ``{dimension: series}`` in der Reihenfolge von
    ``DIMENSIONS_BY_SOURCE[source]``. ValueError bei ungültiger Quelle.
    """
    columns = {dimension: value_column(source, dimension) for dimension in DIMENSIONS_BY_SOURCE.get(source, [])}
    if not columns:
        value_column(source)  # wirft ValueError mit der Liste erlaubter Quellen
    rows = fetch_review_rows(source, company_id, ",".join(dict.fromkeys(columns.values())))
    return {dimension: build_monthly_series(rows, column, min_reviews) for dimension, column in columns.items()}


# ── Eignung nach E4 ─────────────────────────────────────────────────────────

def evaluated_months(series: List[Dict[str, Any]]) -> int:
    """Anzahl bewerteter Monate einer Reihe."""
    return sum(1 for month in series if month.get("evaluated"))


def is_eligible(series: List[Dict[str, Any]], min_months: int = MIN_EVALUATED_MONTHS) -> bool:
    """True, wenn die Reihe genug bewertete Monate für die Erkennung hat (E4)."""
    return evaluated_months(series) >= min_months


__all__ = [
    "OVERALL_DIMENSION", "VALID_SOURCES", "DIMENSIONS_BY_SOURCE",
    "MIN_REVIEWS_PER_MONTH", "MIN_EVALUATED_MONTHS",
    "value_column", "month_key", "month_range",
    "build_monthly_series", "fetch_review_rows", "monthly_series", "monthly_series_by_dimension",
    "evaluated_months", "is_eligible",
]
