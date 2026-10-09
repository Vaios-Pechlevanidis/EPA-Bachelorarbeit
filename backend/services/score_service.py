"""
Ø Score nach Entscheidung D1 des Autors (2026-10-09, Inkrement 6, FA-38).

„Ø Score“ ist das Mittel der **Gesamtnote** (Spalte ``durchschnittsbewertung``)
aller Bewertungen der Mitarbeitenden im gewählten Zeitraum, ungewichtet. Das ist
dieselbe Basis wie die Erkennungsreihe (E3), der Zeitverlauf und die
rollierenden Schnitte (FA-08). Das bisherige Feld ``avg_overall`` (Mittel der 13
Kategorienmittel) bleibt unverändert in der Antwort und heißt in der Oberfläche
„Kategorienmittel“; beide Werte können voneinander abweichen, weil die
Gesamtnote je Bewertung kein Mittel der Kategorien sein muss und Kategorien
unterschiedlich oft bewertet werden.

Der Trend-Modus ``score_months`` vergleicht die Gesamtnote der letzten
``months`` (Standard 12) vollen Kalendermonate mit den ``months`` davor. Anker
wie bei den rollierenden Schnitten (FA-08): der letzte volle Kalendermonat mit
Bewertungen des Unternehmens, nicht das heutige Datum.

Reine Funktionen ohne Datenbankzugriff (Tests:
``backend/tests/test_score_service.py``).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from services.rating_series_service import OVERALL_DIMENSION
from services.rolling_average_service import (
    ANCHOR_RULE,
    LOW_BASIS_MIN_REVIEWS,
    SIGN_EPS,
    _month_index,
    _period,
    dated_values,
    last_full_month_with_data,
    rolling_window,
)

SCORE_DEFINITION = (
    "Mittel der Gesamtnote (Spalte durchschnittsbewertung) aller Bewertungen von Mitarbeitenden "
    "im gewählten Zeitraum, ungewichtet"
)
CATEGORY_MEAN_DEFINITION = (
    "Kategorienmittel: Mittel der 13 Kategorienmittel (ungewichtet), nur Mitarbeitende; "
    "kann von der Gesamtnote abweichen"
)
TREND_MODE = "score_months"
TREND_DEFINITION = (
    "Gesamtnote der letzten vollen Kalendermonate bis zum Anker im Vergleich mit derselben Zahl "
    "Kalendermonate davor; Mittel aller Bewertungen je Fenster, ungewichtet"
)


def _values(rows: List[Dict[str, Any]], column: str = OVERALL_DIMENSION) -> List[float]:
    out: List[float] = []
    for row in rows:
        v = row.get(column)
        if v is None:
            continue
        try:
            out.append(float(v))
        except (TypeError, ValueError):
            continue
    return out


def score_from_rows(rows: List[Dict[str, Any]], column: str = OVERALL_DIMENSION) -> Dict[str, Any]:
    """``score`` (Mittel der Gesamtnote, zwei Nachkommastellen) und ``score_n``
    (Bewertungen mit Gesamtnote) aus Zeilen der Tabelle ``employee``."""
    values = _values(rows, column)
    return {
        "score": round(sum(values) / len(values), 2) if values else None,
        "score_n": len(values),
    }


def _sign(difference: Optional[float]) -> Optional[str]:
    if difference is None:
        return None
    if difference > SIGN_EPS:
        return "up"
    if difference < -SIGN_EPS:
        return "down"
    return "flat"


def score_trend(
    rows: List[Dict[str, Any]],
    months: int = 12,
    today: Optional[datetime] = None,
    min_reviews: int = LOW_BASIS_MIN_REVIEWS,
    column: str = OVERALL_DIMENSION,
) -> Dict[str, Any]:
    """Gesamtnote der letzten ``months`` vollen Kalendermonate bis zum Anker
    (``current``) gegen die ``months`` Kalendermonate davor (``previous``),
    n je Fenster; reine Funktion.

    ``overall.deltaPoints`` und ``n_reviews`` haben dieselbe Form wie in den
    Modi ``stable_months``/``stable_all``, damit die Kachel beide lesen kann.
    """
    values = dated_values(rows, column)
    anchor = last_full_month_with_data(values, today)
    result: Dict[str, Any] = {
        "mode": TREND_MODE,
        "months": months,
        "requestedMonths": months,
        "column": column,
        "definition": TREND_DEFINITION,
        "anchor": anchor,
        "anchor_rule": ANCHOR_RULE,
        "current": None,
        "previous": None,
        "difference": None,
        "sign": None,
        "low_basis": False,
        "low_basis_rule": {"min_reviews_per_window": min_reviews, "origin": "E12, vorläufig (T5 offen)"},
        "insufficient_history": True,
        "overall": {"deltaPoints": None, "deltaPercent": None},
        "n_reviews": {"current": 0, "previous": 0},
        "current_range": {"from": None, "to": None},
        "previous_range": {"from": None, "to": None},
        "source": "employee",
        "basis": "durchschnittsbewertung",
    }
    if anchor is None:
        return result
    first_month = min(p for p, _ in values)
    previous_anchor = _period(_month_index(anchor) - months)
    current = rolling_window(values, anchor, months, min_reviews, first_month)
    previous = rolling_window(values, previous_anchor, months, min_reviews, first_month)
    cur_vals = [v for p, v in values if current["from"] <= p <= current["to"]]
    prev_vals = [v for p, v in values if previous["from"] <= p <= previous["to"]]
    difference = None
    percent = None
    if cur_vals and prev_vals:
        cur_mean, prev_mean = sum(cur_vals) / len(cur_vals), sum(prev_vals) / len(prev_vals)
        difference = round(cur_mean - prev_mean, 2)
        percent = round((cur_mean - prev_mean) / prev_mean * 100, 1) if abs(prev_mean) > 1e-12 else None
    result.update({
        "current": current,
        "previous": previous,
        "difference": difference,
        "sign": _sign(difference),
        "low_basis": bool(current["low_basis"] or previous["low_basis"]),
        "insufficient_history": not previous["covered"],
        "overall": {"deltaPoints": difference, "deltaPercent": percent},
        "n_reviews": {"current": current["n"], "previous": previous["n"]},
        "current_range": {"from": current["from"], "to": current["to"]},
        "previous_range": {"from": previous["from"], "to": previous["to"]},
    })
    return result


def company_score_trend(company_id: int, months: int = 12, today: Optional[datetime] = None) -> Dict[str, Any]:
    """``score_trend`` aus der Datenbank (Mitarbeitende, nur lesend, seitenweise)."""
    from services.rating_series_service import fetch_review_rows  # lazy, damit Tests ohne DB laufen

    rows = fetch_review_rows("employee", company_id, OVERALL_DIMENSION)
    result = score_trend(rows, months, today)
    result["company_id"] = int(company_id)
    return result


__all__ = [
    "SCORE_DEFINITION", "CATEGORY_MEAN_DEFINITION", "TREND_MODE", "TREND_DEFINITION",
    "score_from_rows", "score_trend", "company_score_trend",
]
