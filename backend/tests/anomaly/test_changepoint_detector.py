"""
Test Suite für die Erkennung von Niveauwechseln (Zyklus 2, Inkrement 1).
Überprüft PELT mit Startwerten (model="l2", min_size=3, penalty=0.5), den
Fallback über gleitende Mittel und die Kennzahlen je Wechsel.

Ausführung:
    uv run python -m pytest tests/anomaly/test_changepoint_detector.py -v
"""

import os
import sys

import numpy as np
import pytest

# Add backend root to path so we can import from models
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from models.changepoint_detector import (  # noqa: E402
    ChangePointDetector,
    MovingMeanDetector,
    PeltDetector,
    detect_changepoints,
    level_shifts,
)


# ─── Fixtures ────────────────────────────────────────────────────────────────

def _series(levels: list[tuple[float, int]], noise: float = 0.08, seed: int = 0) -> list[float]:
    """Helper: Stückweise konstante Reihe aus (Niveau, Länge) plus Rauschen."""
    rng = np.random.default_rng(seed)
    values = np.concatenate([np.full(length, level) for level, length in levels])
    return list(np.round(values + rng.normal(0, noise, len(values)), 3))


# ═══════════════════════════════════════════════════════════════════════════════
# 1. PELT — Kernfälle
# ═══════════════════════════════════════════════════════════════════════════════

class TestPeltDetection:
    """Tests für Niveauwechsel mit PELT und Startwerten."""

    def test_single_fall_detected(self):
        """Test: Abfall von 4,0 auf 3,2 nach 12 Monaten → ein Wechsel bei Index 12."""
        values = _series([(4.0, 12), (3.2, 12)])
        result = detect_changepoints(values)
        assert result.method == "pelt"
        assert result.indices == [12]
        shift = level_shifts(values, result.indices)[0]
        assert shift["delta"] == pytest.approx(-0.8, abs=0.1)
        print(f"\n✓ Abfall erkannt bei Index {result.indices[0]}, Delta {shift['delta']:.2f}")

    def test_single_rise_detected(self):
        """Test: Anstieg von 3,0 auf 3,8 → ein Wechsel mit positivem Delta."""
        values = _series([(3.0, 10), (3.8, 14)], seed=1)
        result = detect_changepoints(values)
        assert result.indices == [10]
        shift = level_shifts(values, result.indices)[0]
        assert shift["delta"] > 0.6
        assert shift["before_mean"] == pytest.approx(3.0, abs=0.1)
        assert shift["after_mean"] == pytest.approx(3.8, abs=0.1)
        print(f"\n✓ Anstieg erkannt bei Index {result.indices[0]}")

    def test_fall_then_rise_detected(self):
        """Test: V-Form → zwei Wechsel; Kennzahlen beziehen sich auf die Nachbarsegmente."""
        values = _series([(4.0, 12), (3.0, 12), (3.9, 12)], seed=2)
        result = detect_changepoints(values)
        assert result.indices == [12, 24]
        fall, rise = level_shifts(values, result.indices)
        assert fall["delta"] < 0 < rise["delta"]
        assert (fall["before_start"], fall["after_end"]) == (0, 24)
        assert (rise["before_start"], rise["after_end"]) == (12, 36)
        print("\n✓ V-Form: Abfall und Anstieg erkannt")

    def test_constant_series_no_change(self):
        """Test: Konstante Reihe ohne Veränderung → kein Wechsel."""
        result = detect_changepoints([3.7] * 24)
        assert result.indices == []
        print("\n✓ Konstante Reihe → kein Wechsel")

    @pytest.mark.parametrize("seed", range(10))
    def test_noise_only_no_change(self, seed):
        """Test: Nur Rauschen (SD 0,15 Sterne) → kein Wechsel."""
        values = _series([(3.6, 36)], noise=0.15, seed=seed)
        result = detect_changepoints(values)
        assert result.indices == []

    def test_penalty_is_configurable(self):
        """Test: Höherer Strafterm unterdrückt einen kleinen Wechsel."""
        values = _series([(3.8, 12), (3.4, 12)], noise=0.05, seed=3)
        assert detect_changepoints(values, PeltDetector(penalty=0.5)).indices == [12]
        assert detect_changepoints(values, PeltDetector(penalty=2.0)).indices == []
        print("\n✓ Strafterm steuert die Empfindlichkeit")

    def test_min_size_respected(self):
        """Test: Kurzer Ausreißer (2 Monate) ist kein Segment bei min_size=3."""
        values = [3.8] * 10 + [2.5, 2.5] + [3.8] * 10
        result = detect_changepoints(values, PeltDetector(min_size=3))
        for a, b in zip([0] + result.indices, result.indices + [len(values)]):
            assert b - a >= 3

    def test_params_reported(self):
        """Test: Parameter werden für die Ausgabe mitgeliefert."""
        result = detect_changepoints(_series([(4.0, 12)]), PeltDetector(penalty=1.0))
        assert result.params == {"model": "l2", "min_size": 3, "penalty": 1.0, "jump": 1}


# ═══════════════════════════════════════════════════════════════════════════════
# 2. Kurze Reihen und Fallback
# ═══════════════════════════════════════════════════════════════════════════════

class TestShortSeriesFallback:
    """Tests für zu kurze Reihen und den Fallback über gleitende Mittel."""

    def test_empty_series(self):
        """Test: Leere Reihe → kein Wechsel, kein Fehler."""
        assert detect_changepoints([]).indices == []

    def test_too_short_uses_fallback_without_result(self):
        """Test: 5 Werte < 2·min_size → Fallback, der ebenfalls nichts findet."""
        result = detect_changepoints([4.0, 4.0, 3.0, 3.0, 3.0])
        assert result.method == "moving_mean"
        assert result.indices == []

    def test_fallback_detects_step(self):
        """Test: Fallback findet einen Sprung bei Index 3 (Fenster 3, Schwelle 0,3)."""
        result = detect_changepoints([4.0, 4.1, 4.0, 3.2, 3.1, 3.2], PeltDetector(min_size=4))
        assert result.method == "moving_mean"
        assert result.indices == [3]
        print("\n✓ Fallback erkennt Sprung in kurzer Reihe")

    def test_fallback_ignores_small_differences(self):
        """Test: Differenz unter der Schwelle → kein Wechsel."""
        assert MovingMeanDetector(threshold=0.3).detect([3.9, 4.0, 3.9, 3.8, 3.8, 3.7]) == []

    def test_fallback_keeps_strongest_per_window(self):
        """Test: Benachbarte Kandidaten innerhalb eines Fensters werden zusammengefasst."""
        values = [4.0] * 6 + [3.0] * 6
        assert MovingMeanDetector(window=3).detect(values) == [6]


# ═══════════════════════════════════════════════════════════════════════════════
# 3. Reihen mit Lücken
# ═══════════════════════════════════════════════════════════════════════════════

class TestGaps:
    """Lücken (nicht bewertete Monate) werden vor der Erkennung entfernt."""

    def test_none_values_rejected(self):
        """Test: None in der Eingabe → ValueError, damit Lücken nicht still verschwinden."""
        with pytest.raises(ValueError):
            detect_changepoints([4.0, None, 3.0, 3.0, 3.0, 3.0])

    def test_change_found_on_evaluated_months_only(self):
        """Test: Reihe mit Lücken; nach Entfernen der Lücken liegt der Wechsel
        auf dem ersten bewerteten Monat des neuen Niveaus."""
        months = [f"2022-{m:02d}" for m in range(1, 13)] + [f"2023-{m:02d}" for m in range(1, 13)]
        raw = _series([(4.0, 12), (3.1, 12)], seed=4)
        gaps = {3, 7, 12, 13, 20}  # u. a. die ersten beiden Monate nach dem Wechsel fehlen
        evaluated = [(p, v) for i, (p, v) in enumerate(zip(months, raw)) if i not in gaps]
        values = [v for _, v in evaluated]
        result = detect_changepoints(values)
        assert len(result.indices) == 1
        assert evaluated[result.indices[0]][0] == "2023-03"
        print("\n✓ Wechsel über eine Lücke hinweg auf 2023-03 gelegt")


# ═══════════════════════════════════════════════════════════════════════════════
# 4. Schnittstelle
# ═══════════════════════════════════════════════════════════════════════════════

def test_detectors_satisfy_protocol():
    """Test: Beide Verfahren erfüllen das Protokoll für weitere Verfahren."""
    assert isinstance(PeltDetector(), ChangePointDetector)
    assert isinstance(MovingMeanDetector(), ChangePointDetector)


def test_custom_detector_can_be_plugged_in():
    """Test: Ein eigenes Verfahren wird ohne Änderung am Ablauf genutzt."""

    class Fixed:
        name = "fixed"
        min_length = 1

        def params(self):
            return {}

        def detect(self, values):
            return [len(values) // 2]

    result = detect_changepoints([1.0, 2.0, 3.0, 4.0], Fixed())
    assert (result.method, result.indices) == ("fixed", [2])
