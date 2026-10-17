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

Unsicherheit (Prüfung 2026-10-17, docs/feature-doku/16-report-qualitaet.md): ``score_sd``
(Stichproben-Standardabweichung) und ``score_ci95`` (halbe Breite des 95-%-Intervalls des
Mittels, t-Verteilung) kommen aus den Daten; der Trend liefert ``difference_ci95`` (Welch,
zwei unabhängige Fenster). Die Intervalle setzen unabhängige Bewertungen voraus; dieselbe
Person kann mehrfach bewertet haben, das ist in den Daten nicht erkennbar. Unter 2 Werten
gibt es kein Intervall (None).

Reine Funktionen ohne Datenbankzugriff (Tests:
``backend/tests/test_score_service.py``, ``backend/tests/test_score_uncertainty.py``).
"""

from __future__ import annotations

import math
from datetime import datetime
from typing import Any, Dict, List, Optional, Sequence

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


def _t_critical(df: int, alpha: float = 0.05) -> float:
    """Kritischer t-Wert (zweiseitig); scipy, sonst Normalnäherung 1,96."""
    try:
        from scipy.stats import t as t_dist  # type: ignore[import-untyped]

        return float(t_dist.ppf(1 - alpha / 2, df))
    except Exception:  # pragma: no cover - scipy fehlt
        return 1.96


def sample_sd(values: Sequence[float]) -> Optional[float]:
    """Stichproben-Standardabweichung (n − 1); None unter 2 Werten."""
    n = len(values)
    if n < 2:
        return None
    mean = sum(values) / n
    return math.sqrt(sum((v - mean) ** 2 for v in values) / (n - 1))


def mean_ci95(values: Sequence[float]) -> Optional[float]:
    """Halbe Breite des 95-%-Intervalls des Mittels (t-Verteilung, n − 1 Freiheitsgrade);
    None unter 2 Werten. Setzt unabhängige Werte voraus."""
    n = len(values)
    sd = sample_sd(values)
    if sd is None:
        return None
    return _t_critical(n - 1) * sd / math.sqrt(n)


def difference_ci95(a: Sequence[float], b: Sequence[float]) -> Optional[float]:
    """Halbe Breite des 95-%-Intervalls der Differenz zweier Mittel (Welch: ungleiche
    Varianzen, Freiheitsgrade nach Welch–Satterthwaite); None, wenn ein Fenster unter 2
    Werte hat."""
    sd_a, sd_b = sample_sd(a), sample_sd(b)
    if sd_a is None or sd_b is None:
        return None
    na, nb = len(a), len(b)
    va, vb = sd_a ** 2 / na, sd_b ** 2 / nb
    se = math.sqrt(va + vb)
    if se == 0:
        return 0.0
    df = (va + vb) ** 2 / ((va ** 2) / (na - 1) + (vb ** 2) / (nb - 1))
    return _t_critical(max(1, int(df))) * se


def score_from_rows(rows: List[Dict[str, Any]], column: str = OVERALL_DIMENSION) -> Dict[str, Any]:
    """``score`` (Mittel der Gesamtnote, zwei Nachkommastellen), ``score_n``
    (Bewertungen mit Gesamtnote), ``score_sd`` und ``score_ci95`` (halbe Breite des
    95-%-Intervalls des Mittels; None unter 2 Werten) aus Zeilen der Tabelle ``employee``."""
    values = _values(rows, column)
    sd = sample_sd(values)
    ci = mean_ci95(values)
    return {
        "score": round(sum(values) / len(values), 2) if values else None,
        "score_n": len(values),
        "score_sd": round(sd, 3) if sd is not None else None,
        "score_ci95": round(ci, 3) if ci is not None else None,
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
        "difference_ci95": None,
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
    diff_ci = None
    if cur_vals and prev_vals:
        cur_mean, prev_mean = sum(cur_vals) / len(cur_vals), sum(prev_vals) / len(prev_vals)
        difference = round(cur_mean - prev_mean, 2)
        percent = round((cur_mean - prev_mean) / prev_mean * 100, 1) if abs(prev_mean) > 1e-12 else None
        ci = difference_ci95(cur_vals, prev_vals)
        diff_ci = round(ci, 3) if ci is not None else None
    result.update({
        "current": current,
        "previous": previous,
        "difference": difference,
        "difference_ci95": diff_ci,
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
    "sample_sd", "mean_ci95", "difference_ci95",
    "score_from_rows", "score_trend", "company_score_trend",
]
