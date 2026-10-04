"""
Test Suite für die Erkennung von Niveauwechseln (Zyklus 2, Inkrement 1).
Überprüft PELT im festen Modus (model="l2", min_size=3, penalty=0.5, der
Standard bis 2026-10-04), den skalierten Strafterm (Standard seit 2026-10-04,
penalty = Faktor · sigma² · ln(n)), noise_sigma, den Fallback über gleitende
Mittel und die Kennzahlen je Wechsel.

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
    DEFAULT_PENALTY_FACTOR,
    MIN_NOISE_SIGMA,
    detect_changepoints,
    level_shifts,
    noise_sigma,
    scaled_penalty,
)

FIXED = PeltDetector(penalty=0.5)  # bisheriger Standard, fester Modus


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
    """Tests für Niveauwechsel mit PELT im festen Modus (penalty 0.5, bisheriger Standard)."""

    def test_single_fall_detected(self):
        """Test: Abfall von 4,0 auf 3,2 nach 12 Monaten → ein Wechsel bei Index 12."""
        values = _series([(4.0, 12), (3.2, 12)])
        result = detect_changepoints(values, FIXED)
        assert result.method == "pelt"
        assert result.indices == [12]
        shift = level_shifts(values, result.indices)[0]
        assert shift["delta"] == pytest.approx(-0.8, abs=0.1)
        print(f"\n✓ Abfall erkannt bei Index {result.indices[0]}, Delta {shift['delta']:.2f}")

    def test_single_rise_detected(self):
        """Test: Anstieg von 3,0 auf 3,8 → ein Wechsel mit positivem Delta."""
        values = _series([(3.0, 10), (3.8, 14)], seed=1)
        result = detect_changepoints(values, FIXED)
        assert result.indices == [10]
        shift = level_shifts(values, result.indices)[0]
        assert shift["delta"] > 0.6
        assert shift["before_mean"] == pytest.approx(3.0, abs=0.1)
        assert shift["after_mean"] == pytest.approx(3.8, abs=0.1)
        print(f"\n✓ Anstieg erkannt bei Index {result.indices[0]}")

    def test_fall_then_rise_detected(self):
        """Test: V-Form → zwei Wechsel; Kennzahlen beziehen sich auf die Nachbarsegmente."""
        values = _series([(4.0, 12), (3.0, 12), (3.9, 12)], seed=2)
        result = detect_changepoints(values, FIXED)
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
        result = detect_changepoints(values, FIXED)
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
        assert result.params == {
            "model": "l2", "min_size": 3, "penalty": 1.0, "penalty_mode": "fixed",
            "penalty_factor": None, "noise_sigma": result.params["noise_sigma"], "jump": 1,
        }
        assert result.params["noise_sigma"] >= MIN_NOISE_SIGMA


# ═══════════════════════════════════════════════════════════════════════════════
# 1b. Skalierter Strafterm (Standard seit 2026-10-04)
# ═══════════════════════════════════════════════════════════════════════════════

def _noisy(n: int, sigma: float, seed: int, jump: float = 0.0) -> list[float]:
    """Helper: Reihe um 3,6 Sterne mit Normalrauschen, optional Sprung in der Mitte."""
    rng = np.random.default_rng(seed)
    x = 3.6 + rng.normal(0, sigma, n)
    x[n // 2:] += jump
    return list(x)


def _shifts_over(values, detector, min_delta=0.3):
    result = detect_changepoints(values, detector)
    return [s for s in level_shifts(values, result.indices) if abs(s["delta"]) >= min_delta]


class TestNoiseSigma:
    """noise_sigma: robuste Streuung aus den ersten Differenzen."""

    def test_constant_series_gives_floor(self):
        """Test: Konstante Reihe → Untergrenze, kein Fehler, keine Division durch null."""
        assert noise_sigma([3.7] * 24) == MIN_NOISE_SIGMA

    @pytest.mark.parametrize("values", [[], [4.0], [4.0, 4.0]])
    def test_short_series_gives_floor(self, values):
        assert noise_sigma(values) == MIN_NOISE_SIGMA

    def test_estimates_true_sigma(self):
        """Test: Normalrauschen sigma 0,5 über 1000 Werte → Schätzung nahe 0,5."""
        assert noise_sigma(_noisy(1000, 0.5, seed=3)) == pytest.approx(0.5, rel=0.1)

    def test_robust_to_single_level_shift(self):
        """Test: Ein Sprung von 1 Stern ändert die Schätzung kaum (nur eine große Differenz)."""
        plain = noise_sigma(_noisy(120, 0.3, seed=4))
        shifted = noise_sigma(_noisy(120, 0.3, seed=4, jump=1.0))
        assert shifted == pytest.approx(plain, rel=0.1)


class TestScaledPenalty:
    """Strafterm = Faktor · sigma² · ln(n); fester Wert hat Vorrang."""

    def test_default_is_scaled_with_factor_2(self):
        result = detect_changepoints(_noisy(60, 0.3, seed=5))
        assert result.params["penalty_mode"] == "scaled"
        assert result.params["penalty_factor"] == DEFAULT_PENALTY_FACTOR == 2.0
        expected = scaled_penalty(_noisy(60, 0.3, seed=5), 2.0)
        assert result.params["penalty"] == pytest.approx(expected["penalty"], rel=1e-6)
        assert result.params["noise_sigma"] == pytest.approx(expected["noise_sigma"], rel=1e-6)

    def test_penalty_grows_with_n(self):
        """Test: Gleiche Streuung, mehr Monate → größerer Strafterm (ln n)."""
        base = [3.6 + (0.2 if i % 2 else -0.2) for i in range(200)]
        p_short = scaled_penalty(base[:24])["penalty"]
        p_long = scaled_penalty(base[:200])["penalty"]
        assert p_long > p_short
        assert p_long / p_short == pytest.approx(np.log(200) / np.log(24), rel=1e-6)

    def test_penalty_grows_with_sigma(self):
        """Test: Gleiche Länge, größere Streuung → größerer Strafterm (sigma²)."""
        assert scaled_penalty(_noisy(60, 0.5, seed=6))["penalty"] > scaled_penalty(_noisy(60, 0.2, seed=6))["penalty"]

    def test_fixed_penalty_has_priority(self):
        """Test: Übergebener fester Wert wird verwendet, Faktor ignoriert."""
        result = detect_changepoints(_noisy(60, 0.3, seed=7), PeltDetector(penalty=0.5, penalty_factor=4.0))
        assert result.params["penalty_mode"] == "fixed"
        assert result.params["penalty"] == 0.5
        assert result.params["penalty_factor"] is None

    def test_fixed_mode_matches_previous_behaviour(self):
        """Test: Fester Modus 0.5 liefert dieselben Indizes wie ruptures direkt mit pen=0.5."""
        import ruptures as rpt
        values = _series([(4.0, 12), (3.0, 12), (3.9, 12)], seed=2)
        direct = rpt.Pelt(model="l2", min_size=3, jump=1).fit(np.asarray(values).reshape(-1, 1)).predict(pen=0.5)
        assert detect_changepoints(values, FIXED).indices == [b for b in direct if b < len(values)]

    def test_long_noisy_series_without_jump(self):
        """Test: 120 Monate, sigma 0,5, kein Sprung (fester Startwert) → keine Veränderung."""
        assert _shifts_over(_noisy(120, 0.5, seed=11), PeltDetector()) == []

    def test_long_noisy_series_with_jump(self):
        """Test: Dieselbe Reihe mit Sprung von 1,0 Sternen → genau dieser Wechsel."""
        shifts = _shifts_over(_noisy(120, 0.5, seed=11, jump=1.0), PeltDetector())
        assert len(shifts) == 1
        assert abs(shifts[0]["index"] - 60) <= 1
        assert shifts[0]["delta"] == pytest.approx(1.0, abs=0.25)

    def test_false_alarm_rate_on_noise(self):
        """Test: Über 50 Startwerte (120 Monate, sigma 0,5) höchstens 10 % Fehlalarme
        mit Faktor 2 und min_delta 0,3 (gemessen 2026-10-04: 6 % über 200 Startwerte)."""
        alarms = sum(bool(_shifts_over(_noisy(120, 0.5, seed=s), PeltDetector())) for s in range(50))
        assert alarms <= 5

    def test_fixed_05_oversegments_noisy_series(self):
        """Test: Der alte feste Wert 0,5 übersegmentiert verrauschte Reihen (Befund für E9)."""
        alarms = sum(bool(_shifts_over(_noisy(120, 0.5, seed=s), FIXED)) for s in range(50))
        assert alarms >= 40


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
