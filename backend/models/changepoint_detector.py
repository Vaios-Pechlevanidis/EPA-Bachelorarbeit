"""
Erkennung von Niveauwechseln in Monatsreihen der Kununu-Bewertungen.

Reine Funktionen ohne Datenbankzugriff (Zyklus 2, Inkrement 1). Eingabe sind
die Mittelwerte der bewerteten Monate (E4) in zeitlicher Reihenfolge, Ausgabe
die Indizes der Niveauwechsel. Ein Index ``i`` bezeichnet den ersten Wert auf
dem neuen Niveau: ``values[:i]`` liegt davor, ``values[i:]`` danach.

Verfahren:

- ``PeltDetector``: PELT (Killick et al. 2012) aus ``ruptures`` mit
  Kostenfunktion ``model`` (Start "l2", Niveauwechsel im Mittel),
  Mindestsegmentlänge ``min_size`` (Start 3 Monate) und Strafterm
  ``penalty`` (Start 0.5, Einheit: quadrierte Sterne). Alle Werte vorläufig,
  siehe E9 in ``docs/entscheidungen.md``.
- ``MovingMeanDetector``: Fallback für Reihen, die für PELT zu kurz sind.
  Differenz der Mittel zweier angrenzender Fenster der Breite ``window``;
  ein Wechsel liegt vor, wo der Betrag der Differenz ``threshold`` erreicht
  und lokal maximal ist.

Weitere Verfahren (geplant: Günnemann et al. 2014) werden über das Protokoll
``ChangePointDetector`` eingehängt.

Verwendung::

    from models.changepoint_detector import detect_changepoints, level_shifts

    result = detect_changepoints([4.1, 4.0, 4.2, 3.1, 3.0, 3.2])
    shifts = level_shifts(values, result.indices)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Protocol, Sequence, runtime_checkable

import numpy as np

DEFAULT_MODEL = "l2"
DEFAULT_MIN_SIZE = 3
DEFAULT_PENALTY = 0.5
DEFAULT_WINDOW = 3
DEFAULT_THRESHOLD = 0.3


# ── Schnittstelle ───────────────────────────────────────────────────────────

@runtime_checkable
class ChangePointDetector(Protocol):
    """Schnittstelle eines Verfahrens zur Erkennung von Niveauwechseln."""

    name: str

    @property
    def min_length(self) -> int:
        """Mindestlänge der Reihe, ab der das Verfahren Wechsel finden kann."""
        ...

    def params(self) -> Dict[str, Any]:
        """Parameter des Verfahrens, für Ausgabe und Nachvollziehbarkeit."""
        ...

    def detect(self, values: Sequence[float]) -> List[int]:
        """Aufsteigende Indizes der ersten Werte auf neuem Niveau."""
        ...


@dataclass(frozen=True)
class DetectionResult:
    indices: List[int]
    method: str
    params: Dict[str, Any] = field(default_factory=dict)


# ── Verfahren ───────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class PeltDetector:
    model: str = DEFAULT_MODEL
    min_size: int = DEFAULT_MIN_SIZE
    penalty: float = DEFAULT_PENALTY
    jump: int = 1
    name: str = "pelt"

    @property
    def min_length(self) -> int:
        return 2 * self.min_size

    def params(self) -> Dict[str, Any]:
        return {"model": self.model, "min_size": self.min_size, "penalty": self.penalty, "jump": self.jump}

    def detect(self, values: Sequence[float]) -> List[int]:
        if len(values) < self.min_length:
            return []
        import ruptures as rpt  # lazy: Modul bleibt ohne ruptures importierbar

        signal = np.asarray(values, dtype=float).reshape(-1, 1)
        algo = rpt.Pelt(model=self.model, min_size=self.min_size, jump=self.jump).fit(signal)
        breakpoints = algo.predict(pen=self.penalty)
        # ruptures liefert Segmentenden; das letzte ist immer len(values).
        return [int(b) for b in breakpoints if 0 < b < len(values)]


@dataclass(frozen=True)
class MovingMeanDetector:
    window: int = DEFAULT_WINDOW
    threshold: float = DEFAULT_THRESHOLD
    name: str = "moving_mean"

    @property
    def min_length(self) -> int:
        return 2 * self.window

    def params(self) -> Dict[str, Any]:
        return {"window": self.window, "threshold": self.threshold}

    def detect(self, values: Sequence[float]) -> List[int]:
        n, w = len(values), self.window
        if w < 1 or n < self.min_length:
            return []
        x = np.asarray(values, dtype=float)
        # diffs[i]: Mittel von values[i:i+w] minus Mittel von values[i-w:i]
        diffs = {i: float(x[i:i + w].mean() - x[i - w:i].mean()) for i in range(w, n - w + 1)}
        candidates = sorted(
            (i for i, d in diffs.items() if abs(d) >= self.threshold),
            key=lambda i: (-abs(diffs[i]), i),
        )
        # Stärkste Kandidaten zuerst; Nachbarn innerhalb eines Fensters entfallen.
        chosen: List[int] = []
        for i in candidates:
            if all(abs(i - j) >= w for j in chosen):
                chosen.append(i)
        return sorted(chosen)


# ── Ablauf ──────────────────────────────────────────────────────────────────

def detect_changepoints(
    values: Sequence[float],
    detector: Optional[ChangePointDetector] = None,
    fallback: Optional[ChangePointDetector] = None,
) -> DetectionResult:
    """Niveauwechsel einer Reihe; nutzt ``fallback``, wenn die Reihe für
    ``detector`` zu kurz ist. Standard: PELT mit Startwerten, Fallback
    gleitende Mittel."""
    detector = detector or PeltDetector()
    fallback = fallback or MovingMeanDetector()
    if any(v is None for v in values):
        raise ValueError("values darf keine Lücken (None) enthalten; nur bewertete Monate übergeben.")
    chosen = detector if len(values) >= detector.min_length else fallback
    return DetectionResult(indices=chosen.detect(values), method=chosen.name, params=chosen.params())


def level_shifts(values: Sequence[float], indices: Sequence[int]) -> List[Dict[str, Any]]:
    """Kennzahlen je Wechsel: Mittel des Segments davor und danach (bis zum
    benachbarten Wechsel) und ``delta`` = danach minus davor."""
    bounds = [0] + list(indices) + [len(values)]
    shifts: List[Dict[str, Any]] = []
    for k, idx in enumerate(indices, start=1):
        before = values[bounds[k - 1]:idx]
        after = values[idx:bounds[k + 1]]
        before_mean = float(np.mean(before))
        after_mean = float(np.mean(after))
        shifts.append({
            "index": int(idx),
            "before_start": bounds[k - 1],
            "after_end": bounds[k + 1],
            "before_mean": before_mean,
            "after_mean": after_mean,
            "delta": after_mean - before_mean,
        })
    return shifts


__all__ = [
    "DEFAULT_MODEL", "DEFAULT_MIN_SIZE", "DEFAULT_PENALTY", "DEFAULT_WINDOW", "DEFAULT_THRESHOLD",
    "ChangePointDetector", "DetectionResult", "PeltDetector", "MovingMeanDetector",
    "detect_changepoints", "level_shifts",
]
