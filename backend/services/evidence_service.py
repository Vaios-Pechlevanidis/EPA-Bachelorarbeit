"""
Externe Belege im Ereignisfenster (Zyklus 2, Inkrement 4) – Fenster.

Ein Beleg ist eine zeitlich nahe Meldung mit Datum, Titel, Herausgeber und
Link. Er ist keine Ursache: Das Dashboard behauptet keinen Zusammenhang und
bewertet keine Meldung. Dieses Modul rechnet nur das **Ereignisfenster**, also
den Zeitraum in Kalendermonaten, in dem Meldungen als Belege gelten.

Ereignisfenster (vorläufig, E18):

- **Niveauwechsel** (E9): von ``window_before`` Monaten vor dem Beginn des
  Übergangs bis ``window_after`` Monate nach ``date``. Der Beginn des Übergangs
  ist der Monat nach ``previous_period`` (dem letzten bewerteten Monat vor
  ``date``); ohne Lücke (``gap_months`` 0) ist das ``date`` selbst. Liegt zwischen
  beiden eine Lücke, kann der Übergang irgendwo darin liegen; das Fenster
  beginnt deshalb vor der Lücke. Ohne ``previous_period`` (Reihenrand) gilt
  ``date`` als Beginn.
- **Einzelmonat** (E14): dieselben Abstände um den Monat.
- **Freie Auswahl** (E17): dieselben Abstände um den Zeitraum ``from``..``to``.

Standardwerte: ``DEFAULT_WINDOW_BEFORE`` = 3 Monate, ``DEFAULT_WINDOW_AFTER`` =
1 Monat (Setzung des Autors, vorläufig; Begründung in E18). Alle Funktionen
sind rein (kein Datei-, DB- oder Netzzugriff).
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

DEFAULT_WINDOW_BEFORE = 3   # Monate vor dem Beginn des Übergangs (vorläufig, E18)
DEFAULT_WINDOW_AFTER = 1    # Monate nach dem markierten Monat bzw. dem Ende der Auswahl (vorläufig, E18)
MAX_WINDOW_MONTHS = 24      # Obergrenze je Seite für die API

KIND_CHANGE = "niveauwechsel"
KIND_OUTLIER = "einzelmonat"
KIND_SELECTION = "auswahl"

_PERIOD_RE = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")


# ── Monate ───────────────────────────────────────────────────────────────────

def is_period(value: Any) -> bool:
    return isinstance(value, str) and _PERIOD_RE.fullmatch(value) is not None


def month_index(period: str) -> int:
    """``YYYY-MM`` als fortlaufende Zahl (Jahr · 12 + Monat − 1); ValueError bei falschem Format."""
    if not is_period(period):
        raise ValueError(f"Monat muss das Format YYYY-MM haben, nicht {period!r}.")
    return int(period[:4]) * 12 + int(period[5:7]) - 1


def period_from_index(index: int) -> str:
    return f"{index // 12:04d}-{index % 12 + 1:02d}"


def shift_month(period: str, months: int) -> str:
    """Kalendermonat um ``months`` verschoben, auch über Jahresgrenzen."""
    return period_from_index(month_index(period) + months)


def month_range(first: str, last: str) -> List[str]:
    """Alle Kalendermonate von ``first`` bis ``last`` einschließlich (leer, wenn ``first`` nach ``last``)."""
    a, b = month_index(first), month_index(last)
    return [period_from_index(i) for i in range(a, b + 1)]


def _check_sizes(window_before: int, window_after: int) -> None:
    for name, value in (("window_before", window_before), ("window_after", window_after)):
        if not isinstance(value, int) or isinstance(value, bool) or value < 0 or value > MAX_WINDOW_MONTHS:
            raise ValueError(f"{name} muss eine ganze Zahl zwischen 0 und {MAX_WINDOW_MONTHS} sein, nicht {value!r}.")


# ── Fenster ──────────────────────────────────────────────────────────────────

def _window(kind: str, anchor_from: str, anchor_to: str, transition_from: str,
            window_before: int, window_after: int, anchor: Dict[str, Any]) -> Dict[str, Any]:
    start = shift_month(transition_from, -window_before)
    end = shift_month(anchor_to, window_after)
    return {
        "kind": kind,
        "from": start,
        "to": end,
        "months": month_index(end) - month_index(start) + 1,
        "transition_from": transition_from,
        "anchor_from": anchor_from,
        "anchor_to": anchor_to,
        "window_before": window_before,
        "window_after": window_after,
        "anchor": anchor,
    }


def window_for_change(
    date: str,
    previous_period: Optional[str] = None,
    gap_months: Optional[int] = None,
    window_before: int = DEFAULT_WINDOW_BEFORE,
    window_after: int = DEFAULT_WINDOW_AFTER,
) -> Dict[str, Any]:
    """Ereignisfenster eines Niveauwechsels.

    ``date`` ist der erste bewertete Monat auf dem neuen Niveau, ``previous_period``
    der letzte bewertete Monat davor (None am Reihenrand). Der Übergang beginnt im
    Monat nach ``previous_period``; ohne Lücke ist das ``date``. ``gap_months`` wird
    nur übernommen (Information für die Anzeige), die Rechnung nutzt
    ``previous_period``.
    """
    _check_sizes(window_before, window_after)
    if previous_period is not None and month_index(previous_period) >= month_index(date):
        raise ValueError("previous_period muss vor date liegen.")
    transition_from = shift_month(previous_period, 1) if previous_period else date
    gap = (month_index(date) - month_index(previous_period) - 1) if previous_period else 0
    anchor = {"date": date, "previous_period": previous_period, "gap_months": gap if gap_months is None else gap_months}
    return _window(KIND_CHANGE, date, date, transition_from, window_before, window_after, anchor)


def window_for_anomaly(anomaly: Dict[str, Any], window_before: int = DEFAULT_WINDOW_BEFORE,
                       window_after: int = DEFAULT_WINDOW_AFTER) -> Dict[str, Any]:
    """``window_for_change`` für eine Anomalie aus ``anomaly_service`` (Felder ``date``,
    ``previous_period``, ``gap_months``)."""
    return window_for_change(
        anomaly["date"], anomaly.get("previous_period"), anomaly.get("gap_months"), window_before, window_after,
    )


def window_for_outlier(date: str, window_before: int = DEFAULT_WINDOW_BEFORE,
                       window_after: int = DEFAULT_WINDOW_AFTER) -> Dict[str, Any]:
    """Ereignisfenster eines auffälligen Einzelmonats (E14): die Abstände um den Monat."""
    _check_sizes(window_before, window_after)
    month_index(date)
    return _window(KIND_OUTLIER, date, date, date, window_before, window_after, {"date": date})


def window_for_selection(from_month: str, to_month: str, window_before: int = DEFAULT_WINDOW_BEFORE,
                         window_after: int = DEFAULT_WINDOW_AFTER) -> Dict[str, Any]:
    """Ereignisfenster einer freien Auswahl (E17): die Abstände um ``from``..``to``.
    ValueError, wenn ``from`` nach ``to`` liegt."""
    _check_sizes(window_before, window_after)
    if month_index(from_month) > month_index(to_month):
        raise ValueError("from liegt nach to.")
    return _window(KIND_SELECTION, from_month, to_month, from_month, window_before, window_after,
                   {"from": from_month, "to": to_month})


def window_months(window: Dict[str, Any]) -> List[str]:
    """Die Kalendermonate eines Fensters, erster zuerst."""
    return month_range(window["from"], window["to"])


__all__ = [
    "DEFAULT_WINDOW_BEFORE", "DEFAULT_WINDOW_AFTER", "MAX_WINDOW_MONTHS",
    "KIND_CHANGE", "KIND_OUTLIER", "KIND_SELECTION",
    "is_period", "month_index", "period_from_index", "shift_month", "month_range",
    "window_for_change", "window_for_anomaly", "window_for_outlier", "window_for_selection", "window_months",
]
