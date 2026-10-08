"""
Tests für das Ereignisfenster (services/evidence_service.py, Inkrement 4, E18):
Niveauwechsel mit und ohne Lücke, Reihenrand, Jahreswechsel, Einzelmonat,
freie Auswahl, Parameter. Reine Funktionen, ohne DB und Netz.

Ausführen:
    cd backend
    uv run python -m pytest tests/evidence/test_evidence_window.py -q -p no:cacheprovider
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))

import services.evidence_service as ev  # noqa: E402


class TestMonths:

    def test_index_and_shift(self):
        assert ev.month_index("2020-01") == 2020 * 12
        assert ev.period_from_index(ev.month_index("2021-12")) == "2021-12"
        assert ev.shift_month("2020-01", -3) == "2019-10"
        assert ev.shift_month("2020-12", 1) == "2021-01"

    def test_range(self):
        assert ev.month_range("2019-11", "2020-02") == ["2019-11", "2019-12", "2020-01", "2020-02"]
        assert ev.month_range("2020-02", "2020-01") == []

    @pytest.mark.parametrize("bad", ["2020-13", "2020/01", "20-01", "", None, "2020-1"])
    def test_invalid_period(self, bad):
        assert not ev.is_period(bad)
        with pytest.raises(ValueError):
            ev.month_index(bad)


class TestChangeWindow:

    def test_without_gap(self):
        """Ohne Lücke beginnt der Übergang am markierten Monat: 3 Monate davor, 1 danach."""
        w = ev.window_for_change("2021-09", previous_period="2021-08", gap_months=0)
        assert (w["from"], w["to"]) == ("2021-06", "2021-10")
        assert w["transition_from"] == "2021-09" and w["months"] == 5
        assert w["kind"] == "niveauwechsel" and w["anchor"]["gap_months"] == 0

    def test_with_gap_window_starts_before_the_gap(self):
        """Lücke: Der Übergang liegt irgendwo zwischen previous_period und date; das
        Fenster beginnt 3 Monate vor dem Monat nach previous_period."""
        w = ev.window_for_change("2021-09", previous_period="2021-05", gap_months=3)
        assert w["transition_from"] == "2021-06"
        assert (w["from"], w["to"]) == ("2021-03", "2021-10")
        assert w["anchor"] == {"date": "2021-09", "previous_period": "2021-05", "gap_months": 3}

    def test_gap_is_derived_when_missing(self):
        w = ev.window_for_change("2021-09", previous_period="2021-05")
        assert w["anchor"]["gap_months"] == 3

    def test_series_edge_without_previous_period(self):
        """Reihenrand: kein bewerteter Monat davor, der markierte Monat ist der Beginn."""
        w = ev.window_for_change("2015-03", previous_period=None)
        assert w["transition_from"] == "2015-03"
        assert (w["from"], w["to"]) == ("2014-12", "2015-04") and w["anchor"]["gap_months"] == 0

    def test_year_boundary_both_sides(self):
        w = ev.window_for_change("2020-01", previous_period="2019-12", gap_months=0)
        assert (w["from"], w["to"]) == ("2019-10", "2020-02")
        w = ev.window_for_change("2020-12", previous_period="2020-11", gap_months=0)
        assert (w["from"], w["to"]) == ("2020-09", "2021-01")

    def test_custom_sizes_and_zero(self):
        w = ev.window_for_change("2021-09", "2021-08", 0, window_before=6, window_after=2)
        assert (w["from"], w["to"], w["months"]) == ("2021-03", "2021-11", 9)
        w = ev.window_for_change("2021-09", "2021-05", 3, window_before=0, window_after=0)
        assert (w["from"], w["to"]) == ("2021-06", "2021-09")

    def test_from_anomaly_dict(self):
        anomaly = {"id": "employee:durchschnittsbewertung:2021-09", "date": "2021-09", "previous_period": "2021-07", "gap_months": 1}
        w = ev.window_for_anomaly(anomaly)
        assert (w["from"], w["to"], w["transition_from"]) == ("2021-05", "2021-10", "2021-08")

    @pytest.mark.parametrize("before, after", [(-1, 1), (3, -1), (25, 1), (3, 25), (1.5, 1), (True, 1)])
    def test_invalid_sizes(self, before, after):
        with pytest.raises(ValueError):
            ev.window_for_change("2021-09", "2021-08", 0, window_before=before, window_after=after)

    def test_previous_after_date_is_invalid(self):
        with pytest.raises(ValueError):
            ev.window_for_change("2021-09", previous_period="2021-09")


class TestOutlierAndSelection:

    def test_outlier_window(self):
        w = ev.window_for_outlier("2022-12")
        assert (w["from"], w["to"], w["months"]) == ("2022-09", "2023-01", 5)
        assert w["kind"] == "einzelmonat" and w["transition_from"] == "2022-12" and w["anchor"] == {"date": "2022-12"}

    def test_selection_window(self):
        w = ev.window_for_selection("2020-03", "2020-05")
        assert (w["from"], w["to"], w["months"]) == ("2019-12", "2020-06", 7)
        assert w["kind"] == "auswahl" and (w["anchor_from"], w["anchor_to"]) == ("2020-03", "2020-05")

    def test_selection_single_month_equals_outlier_window(self):
        assert ev.window_for_selection("2022-12", "2022-12")["from"] == ev.window_for_outlier("2022-12")["from"]
        assert ev.window_for_selection("2022-12", "2022-12")["to"] == ev.window_for_outlier("2022-12")["to"]

    def test_selection_order_checked(self):
        with pytest.raises(ValueError, match="from liegt nach to"):
            ev.window_for_selection("2020-05", "2020-03")

    def test_window_months_list(self):
        w = ev.window_for_outlier("2019-12", window_before=1, window_after=1)
        assert ev.window_months(w) == ["2019-11", "2019-12", "2020-01"]


class TestComparisonWindows:
    """Vergleichsfenster (Nachschärfung Inkrement 4): das Fenster der Markierung um −12, +12,
    −24, +24 Monate verschoben, höchstens drei, ohne Überschneidung mit einem Fenster einer
    Markierung des Unternehmens und nur innerhalb der bewerteten Reihe."""

    WINDOW = ev.window_for_change("2021-09", previous_period="2021-08", gap_months=0)   # 2021-06 .. 2021-10

    def test_three_windows_in_order_with_same_length_and_position(self):
        found = ev.comparison_windows(self.WINDOW, [self.WINDOW], "2015-01", "2024-12")
        assert [(c["offset_months"], c["from"], c["to"]) for c in found] == [
            (-12, "2020-06", "2020-10"), (12, "2022-06", "2022-10"), (-24, "2019-06", "2019-10")]
        first = found[0]
        assert first["kind"] == "vergleich" and first["months"] == 5 == self.WINDOW["months"]
        assert (first["anchor_from"], first["anchor_to"], first["transition_from"]) == ("2020-09", "2020-09", "2020-09")
        assert (first["window_before"], first["window_after"]) == (3, 1)
        assert first["reference"] == {"kind": "niveauwechsel", "from": "2021-06", "to": "2021-10",
                                      "anchor_from": "2021-09", "anchor_to": "2021-09"}
        assert ev.window_months(first) == ["2020-06", "2020-07", "2020-08", "2020-09", "2020-10"]

    def test_overlap_with_any_marker_window_drops_the_anchor(self):
        other = ev.window_for_outlier("2020-08")          # 2020-05 .. 2020-09 überschneidet −12
        found = ev.comparison_windows(self.WINDOW, [self.WINDOW, other], "2015-01", "2024-12")
        assert [c["offset_months"] for c in found] == [12, -24, 24], "−12 entfällt, +24 rückt nach"
        edge = ev.window_for_outlier("2020-11", 1, 0)     # 2020-10 .. 2020-11: Randmonat 2020-10 gemeinsam
        assert [c["offset_months"] for c in ev.comparison_windows(self.WINDOW, [edge], "2015-01", "2024-12")] == [12, -24, 24]

    def test_long_marker_window_overlaps_itself(self):
        long = ev.window_for_change("2010-01", previous_period="2008-07", gap_months=17)   # 2008-05 .. 2010-02, 22 Monate
        found = ev.comparison_windows(long, [long], "2005-01", "2015-12")
        assert [c["offset_months"] for c in found] == [-24, 24], "±12 überschneiden das eigene Fenster"

    def test_outside_the_series_is_dropped(self):
        found = ev.comparison_windows(self.WINDOW, [self.WINDOW], "2019-07", "2022-09")
        assert [c["offset_months"] for c in found] == [-12], "+12 endet nach der Reihe, −24 beginnt davor, +24 ebenso"
        assert ev.comparison_windows(self.WINDOW, [self.WINDOW], "2021-01", "2021-12") == []
        assert [c["offset_months"] for c in ev.comparison_windows(self.WINDOW, [self.WINDOW])] == [-12, 12, -24], "ohne Grenzen"
        with pytest.raises(ValueError):
            ev.comparison_windows(self.WINDOW, [], "2022-01", "2021-01")

    def test_offsets_and_count_are_parameters(self):
        found = ev.comparison_windows(self.WINDOW, [self.WINDOW], "2015-01", "2024-12", offsets=(6, -6), max_count=1)
        assert [(c["offset_months"], c["from"]) for c in found] == [(6, "2021-12")]
        assert ev.windows_overlap({"from": "2020-01", "to": "2020-03"}, {"from": "2020-03", "to": "2020-05"})
        assert not ev.windows_overlap({"from": "2020-01", "to": "2020-03"}, {"from": "2020-04", "to": "2020-05"})
