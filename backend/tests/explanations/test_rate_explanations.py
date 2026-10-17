"""
Tests für scripts/rate_explanations.py (DZ2, Ergänzung zu E23): Statistik (exakter Test nach
Fisher gegen die Hypergeometrie von Hand, Wilson und Newcombe, Permutationstest in Clustern
gegen die vollständige Aufzählung, Spearman, nachweisbare Differenz), Cluster aus einem
Bericht und Teil A, Bogen und Schlüssel aus einem nachgebildeten Speicher (Verblindung,
Wortwahl der Zeitangaben, Richtung aus den Bewertungen), Urteile prüfen, entblinden und
auswerten (Teil B), Markdown ohne Titel, Befehle.

Ausführung:
    cd backend
    uv run python -m pytest tests/explanations/test_rate_explanations.py -q -p no:cacheprovider
"""

import itertools
import json
import math
import os
import sys
from datetime import datetime, timezone

import pytest

BACKEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
sys.path.insert(0, BACKEND_DIR)
sys.path.insert(0, os.path.join(BACKEND_DIR, "scripts"))

import rate_explanations as rx  # noqa: E402
import report_explanation_validity as rev  # noqa: E402
import services.evidence_service as ev  # noqa: E402
import services.evidence_sources as src  # noqa: E402


# ── Statistik ────────────────────────────────────────────────────────────────

def _hypergeom_two_sided(a, b, c, d):
    """Unabhängige Rechnung: Summe der Tafelwahrscheinlichkeiten höchstens so groß wie die beobachtete."""
    r1, r2, c1 = a + b, c + d, a + c
    n = r1 + r2
    probs = {k: math.comb(r1, k) * math.comb(r2, c1 - k) / math.comb(n, c1) for k in range(max(0, c1 - r2), min(r1, c1) + 1)}
    return sum(p for p in probs.values() if p <= probs[a] + 1e-12)


class TestFisher:

    def test_known_values(self):
        assert rx.fisher_exact(3, 1, 1, 3) == pytest.approx(0.485714, abs=1e-5)
        assert rx.fisher_exact(10, 0, 0, 10) == pytest.approx(2 / math.comb(20, 10), abs=1e-7)
        assert rx.fisher_exact(23, 5, 57, 15) == 1.0

    def test_matches_hand_calculation_and_symmetry(self):
        for table in ((5, 2, 3, 6), (1, 9, 8, 2), (7, 7, 7, 7), (0, 4, 3, 1), (12, 3, 2, 9)):
            a, b, c, d = table
            assert rx.fisher_exact(a, b, c, d) == pytest.approx(_hypergeom_two_sided(a, b, c, d), abs=1e-6)
            assert rx.fisher_exact(a, b, c, d) == rx.fisher_exact(c, d, a, b)

    def test_edge_cases(self):
        assert rx.fisher_exact(0, 0, 0, 0) is None
        assert rx.fisher_exact(0, 0, 3, 2) == 1.0, "leere Zeile: nichts zu testen"
        assert rx.fisher_exact(4, 0, 5, 0) == 1.0, "Merkmal überall: nichts zu testen"


class TestIntervals:

    def test_wilson(self):
        lo, hi = rx.wilson_interval(0, 10)
        assert lo == pytest.approx(0.0, abs=1e-9) and 0.2 < hi < 0.4
        lo, hi = rx.wilson_interval(10, 10)
        assert hi == pytest.approx(1.0, abs=1e-9) and 0.6 < lo < 0.8
        lo, hi = rx.wilson_interval(5, 10)
        assert lo + hi == pytest.approx(1.0, abs=1e-9)
        assert rx.wilson_interval(0, 0) == (None, None)

    def test_newcombe_contains_difference_and_zero_for_equal_shares(self):
        lo, hi = rx.newcombe_interval(23, 28, 57, 72)
        d = 23 / 28 - 57 / 72
        assert lo < d < hi and lo < 0 < hi
        lo, hi = rx.newcombe_interval(10, 20, 20, 40)
        assert lo < 0 < hi and lo == pytest.approx(-hi, abs=1e-9)
        assert rx.newcombe_interval(1, 0, 1, 2) == (None, None)

    def test_min_detectable_difference(self):
        md = rx.min_detectable_difference(28, 72, 57 / 72)
        assert md["above"] == pytest.approx(0.961, abs=0.002) and md["below"] == pytest.approx(0.494, abs=0.002)
        bigger = rx.min_detectable_difference(280, 720, 57 / 72)
        assert bigger["above"] < md["above"] and bigger["below"] > md["below"], "mehr Fenster: kleinere Differenz nachweisbar"
        assert rx.min_detectable_difference(0, 10, 0.5) == {"above": None, "below": None}


class TestClusterPermutation:

    @staticmethod
    def _exact_p(clusters):
        n_m, n_c = len(clusters), sum(len(c) - 1 for c in clusters)
        total = sum(sum(c) for c in clusters)
        observed_sum = sum(c[0] for c in clusters)
        obs = observed_sum / n_m - (total - observed_sum) / n_c
        hits = n = 0
        for choice in itertools.product(*[range(len(c)) for c in clusters]):
            ms = sum(c[j] for c, j in zip(clusters, choice))
            n += 1
            if abs(ms / n_m - (total - ms) / n_c) >= abs(obs) - 1e-9:
                hits += 1
        return hits / n, obs

    def test_matches_exact_enumeration_including_ties(self):
        # Die neun Einzelmonat-Cluster des Berichts vom 2026-10-13 (oberste Stufe mindestens mittel):
        # exakt 20/36; eine gerundete beobachtete Statistik hätte die Treffer mit genau diesem Wert verloren.
        clusters = [[0, 0, 0, 0], [1, 1, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0], [0, 0, 0, 0], [1, 1, 1, 1], [0, 1, 1, 1], [0, 1, 1]]
        exact, obs = self._exact_p([[float(v) for v in c] for c in clusters])
        assert exact == pytest.approx(20 / 36, abs=1e-9)
        result = rx.cluster_permutation_test([[float(v) for v in c] for c in clusters], n_perm=20000, seed=7)
        assert result["observed_diff"] == pytest.approx(round(obs, 4), abs=1e-9)
        assert result["p_value"] == pytest.approx(exact, abs=0.02)
        assert result["n_markers"] == 9 and result["n_comparisons"] == 24

    def test_matches_exact_enumeration_random_clusters(self):
        import random
        rng = random.Random(3)
        for _ in range(5):
            clusters = [[float(rng.randrange(0, 4)) for _ in range(rng.randrange(1, 5))] for _ in range(6)]
            if not any(len(c) > 1 for c in clusters):
                continue
            exact, _ = self._exact_p(clusters)
            result = rx.cluster_permutation_test(clusters, n_perm=15000, seed=11)
            assert result["p_value"] == pytest.approx(exact, abs=0.025)

    def test_identical_values_and_fixed_clusters(self):
        same = rx.cluster_permutation_test([[1.0, 1.0, 1.0], [1.0, 1.0]], n_perm=500)
        assert same["observed_diff"] == 0.0 and same["p_value"] == 1.0
        fixed = rx.cluster_permutation_test([[1.0], [0.0]], n_perm=500)
        assert fixed["p_value"] is None and fixed["n_comparisons"] == 0
        assert rx.cluster_permutation_test([], n_perm=10)["p_value"] is None

    def test_paired_view(self):
        result = rx.cluster_permutation_test([[3.0, 1.0, 1.0], [2.0, 2.0], [0.0, 1.0, 2.0], [1.0]], n_perm=0)
        paired = result["paired"]
        assert paired["n_pairs"] == 3 and paired["marker_higher"] == 1 and paired["equal"] == 1 and paired["marker_lower"] == 1
        assert paired["mean_diff"] == pytest.approx((2.0 + 0.0 - 1.5) / 3, abs=1e-4)
        assert result["p_value"] is None and result["n_permutations"] == 0

    def test_separated_groups_give_small_p(self):
        clusters = [[1.0, 0.0, 0.0, 0.0] for _ in range(12)]
        result = rx.cluster_permutation_test(clusters, n_perm=4000, seed=1)
        assert result["observed_diff"] == 1.0 and result["p_value"] < 0.01


class TestSpearman:

    def test_perfect_and_ties(self):
        assert rx.spearman([1, 2, 3, 4, 5], [1, 2, 3, 4, 5], n_perm=0)["rho"] == 1.0
        assert rx.spearman([1, 2, 3, 4, 5], [5, 4, 3, 2, 1], n_perm=0)["rho"] == -1.0
        assert rx._ranks([10, 20, 20, 30]) == [1.0, 2.5, 2.5, 4.0]
        assert rx.spearman([1, 1, 1], [1, 2, 3], n_perm=0)["rho"] is None, "ohne Streuung"
        assert rx.spearman([1, 2], [1, 2], n_perm=0)["rho"] is None, "zu wenige Paare"

    def test_permutation_p(self):
        strong = rx.spearman(list(range(12)), list(range(12)), n_perm=2000, seed=2)
        assert strong["p_value"] < 0.01 and strong["n_permutations"] == 2000
        weak = rx.spearman([1, 2, 3, 4, 5, 6], [2, 1, 4, 3, 6, 5], n_perm=2000, seed=2)
        assert weak["rho"] == pytest.approx(0.8286, abs=1e-3) and 0.0 < weak["p_value"] < 0.2
        with pytest.raises(ValueError):
            rx.spearman([1, 2, 3], [1, 2])


class TestCompare:

    def test_compare_binary(self):
        clusters = [[1, 0, 0], [1, 1, 0], [0, 0], [1, 1, 1, 1]]
        b = rx.compare_binary(clusters, n_perm=500, seed=1)
        assert b["markers"] == {"k": 3, "n": 4, "share": 0.75}
        assert b["comparisons"] == {"k": 4, "n": 8, "share": 0.5}
        assert b["diff"] == 0.25 and b["ci95"][0] < 0.25 < b["ci95"][1]
        assert b["fisher_p"] == pytest.approx(_hypergeom_two_sided(3, 1, 4, 4), abs=1e-6)
        assert 0 < b["permutation"]["p_value"] <= 1 and b["min_detectable"]["above"] is not None

    def test_compare_means_distribution(self):
        m = rx.compare_means([[3.0, 1.0, 2.0], [2.0, 2.0]], n_perm=100, seed=1)
        assert m["markers"]["distribution"] == {"2": 1, "3": 1} and m["comparisons"]["distribution"] == {"1": 1, "2": 2}
        assert m["diff"] == pytest.approx(2.5 - 5 / 3, abs=1e-4)


# ── Teil A aus einem Bericht ─────────────────────────────────────────────────

def _w(company, group, kind, date, offset, state, top, n_terms=1, n_items=10, missing=0, ref=None):
    return {"company": company, "group": group, "kind": kind, "date": date, "offset_months": offset, "state": state,
            "top_stage": top, "n_terms": n_terms, "n_items": n_items, "missing_months": missing, "reference_hit": ref,
            "n_by_stage": {"hoch": 1 if top == "hoch" else 0, "mittel": 1 if top in ("hoch", "mittel") else 0, "niedrig": 1 if top else 0, "keine": 0}}


WINDOWS = [
    _w("A", "markierung", "niveauwechsel", "2023-04", 0, "ansaetze", "hoch", n_items=50, ref=True),
    _w("A", "vergleich", "niveauwechsel", "2023-04", -12, "ansaetze", "niedrig", n_items=40),
    _w("A", "vergleich", "niveauwechsel", "2023-04", 12, "offen", None, n_terms=0, n_items=3),
    _w("A", "markierung", "einzelmonat", "2021-06", 0, "offen", None, n_terms=0, n_items=1, ref=False),
    _w("A", "vergleich", "einzelmonat", "2021-06", -12, "ansaetze", "mittel", n_items=20),
    _w("B", "markierung", "niveauwechsel", "2019-02", 0, "ansaetze", "mittel", n_items=30, ref=False),
    _w("B", "vergleich", "niveauwechsel", "2019-02", 12, "ansaetze", "mittel", n_items=30, missing=1),   # unvollständig
    _w("C", "vergleich", "niveauwechsel", "2020-01", -12, "ansaetze", "hoch"),                           # ohne Markierung: übersprungen
]


class TestStageTests:

    def test_build_clusters(self):
        clusters = rx.build_clusters(WINDOWS)
        assert [len(c) for c in clusters] == [3, 2, 2]
        assert all(c[0]["group"] == "markierung" for c in clusters)
        assert rx.cluster_key(WINDOWS[0]) == ("A", "niveauwechsel", "2023-04")
        assert rx.stage_score("hoch") == 3 and rx.stage_score(None) == 0 and rx.stage_score("niedrig") == 1

    def test_stage_tests_counts(self):
        a = rx.stage_tests(WINDOWS, n_perm=300, seed=1)
        assert a["n_windows"] == 8 and a["n_complete"] == 7 and a["n_skipped_clusters_windows"] == 1
        t = a["total"]
        assert t["n_markers"] == 3 and t["n_comparisons"] == 3
        any_ = t["binary"]["mit_ansatz"]
        assert any_["markers"] == {"k": 2, "n": 3, "share": 0.6667} and any_["comparisons"] == {"k": 2, "n": 3, "share": 0.6667}
        assert any_["fisher_p"] == 1.0 and any_["permutation"]["p_value"] is not None
        assert t["binary"]["hoch"]["markers"]["k"] == 1 and t["binary"]["mindestens_mittel"]["markers"]["k"] == 2
        assert t["ordinal"]["markers"]["mean"] == pytest.approx((3 + 0 + 2) / 3, abs=1e-4)
        assert a["by_kind"]["niveauwechsel"]["n_markers"] == 2 and a["by_kind"]["einzelmonat"]["n_markers"] == 1
        ref = a["reference"]
        assert ref["n_treffer"] == 1 and ref["n_uebrige"] == 2 and ref["binary"]["hoch"]["treffer"] == {"k": 1, "n": 1}
        nm = a["null_model"]
        assert nm["items_vs_any"]["n"] == 7 and len(nm["by_items_tertile"]) == 3
        assert sum(t["markers"]["n"] + t["comparisons"]["n"] for t in nm["by_items_tertile"]) == 6

    def test_reference_none_without_hits(self):
        rows = [dict(w, reference_hit=None) for w in WINDOWS]
        assert rx.stage_tests(rows, n_perm=10)["reference"] is None

    def test_markdown_part_a(self):
        summary = {"generated_at": "jetzt", "n_permutations": 10, "seed": 1, "validity_path": "x.json",
                   "stage_tests": rx.stage_tests(WINDOWS, n_perm=10), "fit_tests": None, "ratings_check": None, "ratings_rows": None}
        text = rx.report_markdown(summary)
        assert "## Teil A" in text and "| mindestens ein Ansatz (Stufe mindestens niedrig) | 2/3 (67 %) | 2/3 (67 %) |" in text
        assert "Nullmodell" in text and "nichts über Ursachen" in text
        assert "## Teil B" not in text


# ── Bogen aus nachgebildetem Speicher ───────────────────────────────────────

NOW = datetime(2026, 1, 15, 12, 0, tzinfo=timezone.utc)
INFO = {"company_id": 5, "name": "Beispielwerk", "search_term": "Beispielwerk", "exclude": [], "term_confirmed": True,
        "ticker": None, "ticker_scope": None, "eqs_uuid": None, "eqs_name": None}
ANCHORS = {
    "eligible": True,
    "anomalies": [{"id": "employee:durchschnittsbewertung:2023-04", "date": "2023-04", "direction": "fall", "previous_period": "2023-02",
                   "gap_months": 1, "before_from": "2021-01", "after_to": "2024-12"}],
    "outliers": [{"id": "employee:durchschnittsbewertung:2021-06:einzelmonat", "date": "2021-06", "direction": "fall"}],
    "series_from": "2019-01", "series_to": "2024-12", "evaluated_months": [],
}


def _review(i, day, text, rating):
    return {"id": i, "datum": f"{day}T10:00:00+00:00", "durchschnittsbewertung": rating, "status": "Angestellt", "titel": "Titel",
            "gut_am_arbeitgeber_finde_ich": "", "schlecht_am_arbeitgeber_finde_ich": text, "verbesserungsvorschlaege": ""}


def _reviews(source, company_id, start, end):
    """12 Bewertungen je Monat; ab 2023-04 Note 3 statt 4 und der Begriff 'Stellenabbau'."""
    out, i = [], 0
    month = ev.period_from_index(ev.month_index(start.strftime("%Y-%m")))
    while month <= end.strftime("%Y-%m"):
        for k in range(12):
            i += 1
            after = month >= "2023-04"
            text = "Der Stellenabbau drückt die Stimmung" if after and k < 8 else "Alles ruhig im Büro"
            out.append(_review(i + ev.month_index(month) * 100, f"{month}-{10 + k:02d}", text, 3.0 if after else 4.0))
        month = ev.shift_month(month, 1)
    return out


def _fill(store, by_month):
    for month, entries in by_month.items():
        items = [src.make_item(title=t, url=f"https://x/{month}/{i}", published_at=f"{day}T10:00:00+00:00", publisher=pub,
                               source="gnews", source_type="news") for i, (t, day, pub) in enumerate(entries)]
        ev.save_record(ev.build_record(5, "gnews", month, ev.expected_query(INFO, "gnews", month), items, NOW), store)


@pytest.fixture
def env(tmp_path, monkeypatch):
    monkeypatch.setenv(ev.LIVE_FETCH_ENV, "0")
    monkeypatch.setattr(ev, "STORE_DIR", tmp_path / "store")
    monkeypatch.setattr(ev, "GLOBAL_EVENTS_PATH", tmp_path / "keine.json")
    monkeypatch.setattr(ev, "company_context_info", lambda cid, metadata=None: dict(INFO) if cid == 5 else None)
    monkeypatch.setattr(rev, "company_anchors", lambda cid: ANCHORS)
    monkeypatch.setattr(rev, "fetch_review_rows_in_range", _reviews)
    monkeypatch.setattr(rev, "list_companies", lambda: [{"id": 5, "name": "Beispielwerk"}])
    months = {}
    for first, last in (("2022-12", "2023-05"), ("2021-12", "2022-05"), ("2023-12", "2024-05"),
                        ("2021-03", "2021-07"), ("2020-03", "2020-07"), ("2022-03", "2022-07"), ("2019-03", "2019-07")):
        for m in ev.month_range(first, last):
            months.setdefault(m, [])
    months["2023-02"] = [("Beispielwerk kündigt Stellenabbau an", "2023-02-10", "Blatt A"),
                         ("Beispielwerk kündigt Stellenabbau an: Verwaltung betroffen", "2023-02-11", "Blatt B")]
    months["2022-05"] = [("Beispielwerk kündigt Stellenabbau in der Verwaltung an", "2022-05-12", "Blatt C")]   # Vergleichsfenster des Einzelmonats (+12)
    months["2020-05"] = [("Beispielwerk gewinnt das Derby", "2020-05-12", "Sport")]
    _fill(tmp_path / "store", months)
    return tmp_path


class TestSheet:

    def test_collect_windows_visible_and_hidden(self, env):
        pairs = rx.collect_windows(companies=[{"id": 5, "name": "Beispielwerk"}], verbose=False)
        assert len(pairs) == 7
        groups = [h["group"] for _, h in pairs]
        assert groups.count("markierung") == 2 and groups.count("vergleich") == 5
        for visible, hidden in pairs:
            for forbidden in ("group", "offset_months", "reference_hit", "rating_shift", "reference"):
                assert forbidden not in visible
            assert set(visible["window"]) == {"from", "to", "months", "transition_from", "anchor_from", "anchor_to"}
            assert visible["kind"] in ("niveauwechsel", "einzelmonat")
        marker = next(v for v, h in pairs if h["group"] == "markierung" and h["kind"] == "niveauwechsel")
        assert marker["direction"] == "fall" and marker["state"] == "ansaetze" and len(marker["explanations"]) == 1
        e = marker["explanations"][0]
        assert e["stage"] == "hoch" and e["title"].startswith("Beispielwerk") and e["n_items"] == 2 and e["rank"] == 1
        assert e["terms"][0]["term"] == "stellenabbau" and e["category"]["label"] and "Übergang" in e["time_phrase"]
        assert "stellenabbau" in [t["term"] for t in marker["terms"]] and marker["reviews"]["before"]["n"] == 72
        hidden = next(h for v, h in pairs if h["group"] == "markierung" and h["kind"] == "niveauwechsel")
        assert hidden["rating_shift"] == -1.0 and hidden["direction_marker"] == "fall" and hidden["top_stage"] == "hoch"
        comp = next(v for v, h in pairs if h["group"] == "vergleich" and h["kind"] == "niveauwechsel" and h["offset_months"] == -12)
        assert comp["direction"] == "unklar" and comp["state"] == "ansaetze" and len(comp["explanations"]) == 1
        # Die Meldung vom 2022-05 liegt auch in diesem Fenster (Monat nach dem Vergleichsanker): Wortwahl wie bei einem Niveauwechsel.
        c = comp["explanations"][0]
        assert c["stage"] == "niedrig" and c["time_phrase"] == "im Monat nach dem markierten Monat" and "auffälligen" not in c["text"]
        plus12 = next(v for v, h in pairs if h["group"] == "vergleich" and h["kind"] == "niveauwechsel" and h["offset_months"] == 12)
        assert plus12["direction"] == "unklar" and plus12["state"] == "offen" and plus12["explanations"] == []

    def test_comparison_window_uses_marker_kind_wording(self, env):
        """Der Text eines Vergleichsfensters eines Einzelmonats sagt 'auffälliger Monat', nicht 'Übergang':
        sonst verriete die Wortwahl die Gruppe."""
        pairs = rx.collect_windows(companies=[{"id": 5, "name": "Beispielwerk"}], verbose=False)
        comp = next(v for v, h in pairs if h["group"] == "vergleich" and h["kind"] == "einzelmonat" and h["offset_months"] == 12)
        assert comp["state"] == "ansaetze" and len(comp["explanations"]) == 1
        e = comp["explanations"][0]
        assert e["stage"] == "niedrig" and "auffälligen Monat" in e["time_phrase"] and "Übergang" not in e["time_phrase"]
        assert "auffälligen Monat" in e["text"] and "Übergang" not in e["text"] and "markierten" not in e["text"]
        derby = next(v for v, h in pairs if h["group"] == "vergleich" and h["kind"] == "einzelmonat" and h["offset_months"] == -12)
        assert derby["n_items"] == 1 and derby["explanations"] == [], "Spielbericht: keine Stufe"

    def test_comparisons_one_and_none(self, env):
        one = rx.collect_windows(companies=[{"id": 5, "name": "Beispielwerk"}], comparisons="one", verbose=False)
        assert [h["group"] for _, h in one].count("vergleich") == 2
        none = rx.collect_windows(companies=[{"id": 5, "name": "Beispielwerk"}], comparisons="none", verbose=False)
        assert len(none) == 2
        with pytest.raises(ValueError):
            rx.collect_windows(companies=[], comparisons="alle")

    def test_direction_from_rows(self):
        assert rx.direction_from_rows([{"durchschnittsbewertung": 4}], [{"durchschnittsbewertung": 3}]) == ("fall", -1.0)
        assert rx.direction_from_rows([{"durchschnittsbewertung": 3}], [{"durchschnittsbewertung": 3.5}]) == ("rise", 0.5)
        assert rx.direction_from_rows([{"durchschnittsbewertung": 3}], [{"durchschnittsbewertung": 3}]) == ("unklar", 0.0)
        assert rx.direction_from_rows([], [{"durchschnittsbewertung": 3}]) == ("unklar", None)
        assert rx.direction_from_rows([{"durchschnittsbewertung": "x"}], [{"durchschnittsbewertung": 3}]) == ("unklar", None)

    def test_blind_sheet_and_key(self, env):
        pairs = rx.collect_windows(companies=[{"id": 5, "name": "Beispielwerk"}], verbose=False)
        sheet, key = rx.blind_sheet(pairs, seed=5)
        sheet2, _ = rx.blind_sheet(pairs, seed=5)
        assert [w["id"] for w in sheet["windows"]] == [f"F-{i:03d}" for i in range(1, 8)]
        assert [w["company"] for w in sheet["windows"]] == [w["company"] for w in sheet2["windows"]], "gleicher Startwert, gleiche Reihenfolge"
        assert [w["id"] for w in key["windows"]] == [w["id"] for w in sheet["windows"]]
        assert any(w["group"] == "markierung" for w in key["windows"]) and all("title" not in w for w in key["windows"])
        for w in sheet["windows"]:
            assert "group" not in w and "offset_months" not in w and "reference_hit" not in w and "rating_shift" not in w
        assert sheet["n_windows"] == 7 and sheet["n_explanations"] == 3 and sheet["scale"]["3"] == "passend"
        assert rx.sheet_checksum(sheet) == rx.sheet_checksum(sheet2) and len(rx.sheet_checksum(sheet)) == 16
        template = rx.rating_template(sheet)
        assert len(template["bewertungen"]) == 3 and template["bogen_checksum"] == rx.sheet_checksum(sheet)
        assert all(r["passung"] is None and r["richtung"] is None for r in template["bewertungen"])
        assert {k["group"] for k in key["windows"]} == {"markierung", "vergleich"}

    def test_sheet_markdown(self, env):
        pairs = rx.collect_windows(companies=[{"id": 5, "name": "Beispielwerk"}], verbose=False)
        sheet, key = rx.blind_sheet(pairs, seed=5)
        text = rx.sheet_markdown(sheet)
        assert "# Bewertungsbogen Erklärungsansätze (blind) · 7 Fenster · 3 Ansätze" in text
        assert "Beispielwerk kündigt Stellenabbau an" in text and "https://x/2023-02/0" in text, "der Bogen zeigt Titel und Link"
        assert "**3 – passend:**" in text and "Richtung der Veränderung in den Bewertungen: **Abfall**" in text
        assert "_Kein Erklärungsansatz (offen). Nichts zu bewerten._" in text
        body = text[text.index("## F-"):].lower()   # der Kopf erklärt die Verblindung; die Fenster selbst verraten nichts
        for forbidden in ("markierungsfenster", "vergleichsfenster", "versatz", "offset", "referenz"):
            assert forbidden not in body, forbidden

    def test_bogen_command_writes_files_and_refuses_overwrite(self, env, tmp_path):
        out = tmp_path / "bogen"
        assert rx.main(["bogen", "--out-dir", str(out), "--quiet", "--annotations", str(tmp_path / "fehlt.json")]) == 0
        for name in ("bogen.json", "bogen.md", "schluessel.json", "bewertungen_vorlage.json"):
            assert (out / name).exists()
        sheet = json.loads((out / "bogen.json").read_text(encoding="utf-8"))
        key = json.loads((out / "schluessel.json").read_text(encoding="utf-8"))
        assert sheet["n_windows"] == 7 and key["bogen_checksum"] == rx.sheet_checksum(sheet) and "git" in key
        assert all(k["reference_hit"] is None for k in key["windows"]), "ohne Annotationsdatei kein Referenztreffer"
        assert rx.main(["bogen", "--out-dir", str(out), "--quiet"]) == 2, "ohne --force nicht überschreiben"
        assert rx.main(["bogen", "--out-dir", str(out), "--quiet", "--force", "--annotations", str(tmp_path / "fehlt.json")]) == 0


# ── Urteile: prüfen, entblinden, auswerten ───────────────────────────────────

def _sheet_and_key():
    """Konstruierter Bogen mit drei Fenstern (eine Markierung mit zwei Ansätzen, zwei Vergleichsfenster, eines offen)."""
    def expl(rank, stage, term, cat, label, employer=True, cit=True, source_type="news"):
        return {"rank": rank, "stage": stage, "stage_label": "x", "signal_label": "y", "title": f"Titel {rank}", "date": "2023-02-10",
                "publisher": "Blatt", "source_type": source_type, "eqs_category": None, "language": "de", "n_items": 1, "publishers": ["Blatt"],
                "time_phrase": "im Monat vor dem Übergang", "time_match": 1.0, "term_match": term, "category_match": cat,
                "category": None if label is None else {"id": label, "label": label, "employer_related": employer, "shifted_topics": []},
                "terms": [], "company_in_title": cit, "text": "Möglicher Zusammenhang …", "url": f"https://x/{rank}", "group": None}

    def window(i, company, kind, explanations):
        return {"id": i, "company": company, "kind": kind, "window": {}, "direction": "fall", "reviews": {}, "low_basis": False, "terms": [],
                "n_terms": 1, "shifted_topics": [], "n_items": 5, "n_bundles": 5, "n_groups": 2, "n_by_stage": {}, "state": "ansaetze" if explanations else "offen",
                "missing_months": 0, "explanations": explanations}

    sheet = {"windows": [
        window("F-001", "A", "niveauwechsel", [expl(1, "hoch", 1.0, 0.5, "Personalabbau"), expl(2, "niedrig", 0.0, 0.5, "Sport", employer=False, cit=False)]),
        window("F-002", "A", "niveauwechsel", [expl(1, "mittel", 0.5, 0.0, None)]),
        window("F-003", "A", "niveauwechsel", []),
    ]}
    key = {"windows": [
        {"id": "F-001", "company": "A", "kind": "niveauwechsel", "date": "2023-04", "group": "markierung", "offset_months": 0, "reference_hit": True, "top_stage": "hoch", "n_explanations": 2},
        {"id": "F-002", "company": "A", "kind": "niveauwechsel", "date": "2023-04", "group": "vergleich", "offset_months": -12, "reference_hit": None, "top_stage": "mittel", "n_explanations": 1},
        {"id": "F-003", "company": "A", "kind": "niveauwechsel", "date": "2023-04", "group": "vergleich", "offset_months": 12, "reference_hit": None, "top_stage": None, "n_explanations": 0},
    ]}
    key["bogen_checksum"] = rx.sheet_checksum(sheet)
    return sheet, key


def _ratings(sheet, rows):
    return {"bogen_checksum": rx.sheet_checksum(sheet), "rater": "Test", "bewertungen": rows}


class TestRatings:

    def test_validate_ratings(self):
        sheet, _ = _sheet_and_key()
        good = _ratings(sheet, [{"id": "F-001", "rank": 1, "passung": 3, "richtung": "passt", "begruendung": "Personalabbau vor dem Übergang."},
                                {"id": "F-001", "rank": 2, "passung": 0, "richtung": "unklar", "begruendung": "Spielbericht, anderes Thema."},
                                {"id": "F-002", "rank": 1, "passung": 2, "richtung": "neutral", "begruendung": ""}])
        check = rx.validate_ratings(good, sheet)
        assert check["ok"] and check["n_expected"] == 3 and check["n_rated"] == 3 and check["missing"] == []
        assert len(check["warnings"]) == 1 and "keine Begründung" in check["warnings"][0]
        bad = _ratings(sheet, [{"id": "F-009", "rank": 1, "passung": 3, "richtung": "passt", "begruendung": "x"},
                               {"id": "F-001", "rank": 1, "passung": 5, "richtung": "passt", "begruendung": "x"},
                               {"id": "F-001", "rank": 2, "passung": True, "richtung": "passt", "begruendung": "x"},
                               {"id": "F-002", "rank": 1, "passung": 2, "richtung": "egal", "begruendung": "x"},
                               {"id": "F-002", "rank": 1, "passung": 2, "richtung": "passt", "begruendung": "x"}])
        check = rx.validate_ratings(bad, sheet)
        assert not check["ok"] and len(check["errors"]) == 5 and check["n_rated"] == 0 and len(check["missing"]) == 3
        assert any("doppelt" in e for e in check["errors"]) and any("nicht in 0 bis 3" in e for e in check["errors"])
        partial = _ratings(sheet, [{"id": "F-001", "rank": 1, "passung": None, "richtung": None, "begruendung": ""}])
        check = rx.validate_ratings(partial, sheet)
        assert check["ok"] and check["n_rated"] == 0 and len(check["missing"]) == 3, "offene Zeilen sind kein Fehler"
        mismatch = dict(good, bogen_checksum="deadbeef")
        assert any("Prüfsumme" in e for e in rx.validate_ratings(mismatch, sheet)["errors"])

    def test_join_window_fit_and_tests(self):
        sheet, key = _sheet_and_key()
        ratings = _ratings(sheet, [{"id": "F-001", "rank": 1, "passung": 3, "richtung": "passt", "begruendung": "Personalabbau | passt."},
                                   {"id": "F-001", "rank": 2, "passung": 0, "richtung": "unklar", "begruendung": "Spielbericht."},
                                   {"id": "F-002", "rank": 1, "passung": 1, "richtung": "neutral", "begruendung": "Mehrdeutiger Begriff."}])
        rows = rx.join_ratings(ratings, sheet, key)
        assert [(r["id"], r["rank"], r["group"], r["stage"], r["passung"]) for r in rows] == [
            ("F-001", 1, "markierung", "hoch", 3), ("F-001", 2, "markierung", "niedrig", 0), ("F-002", 1, "vergleich", "mittel", 1)]
        assert rows[1]["employer_related"] is False and rows[1]["company_in_title"] is False and rows[0]["reference_hit"] is True
        windows = rx.window_fit(rows, key, sheet)
        by_id = {w["id"]: w for w in windows}
        assert (by_id["F-001"]["fit_top1"], by_id["F-001"]["fit_max"], by_id["F-001"]["top1_is_best"]) == (3, 3, True)
        assert (by_id["F-002"]["fit_top1"], by_id["F-002"]["top1_is_best"]) == (1, None)
        assert by_id["F-003"]["fit_top1"] is None and by_id["F-003"]["n_rated"] == 0
        b = rx.fit_tests(rows, windows, n_perm=200, seed=1)
        assert b["n_ratings"] == 3 and b["n_windows_rated"] == 2 and b["n_windows"] == 3
        w = b["windows_with_approach"]["fit_top1_at_least"]
        assert w["markers"] == {"k": 1, "n": 1, "share": 1.0} and w["comparisons"] == {"k": 0, "n": 1, "share": 0.0}
        z = b["all_windows_open_as_zero"]["fit_max_at_least"]
        assert z["comparisons"]["n"] == 2 and z["comparisons"]["k"] == 0
        s = b["stage_vs_fit"]
        assert s["table"]["hoch"]["3"] == 1 and s["table"]["niedrig"]["0"] == 1 and s["table"]["mittel"]["1"] == 1
        assert s["per_stage"]["hoch"] == {"n": 1, "mean": 3.0, "at_least": 1} and s["spearman"]["rho"] == 1.0
        sig = b["signals_vs_fit"]
        assert sig["arbeitgeberbezug"]["with"]["n"] == 1 and sig["arbeitgeberbezug"]["without"]["n"] == 1
        assert sig["unternehmen_im_titel"]["with"]["mean"] == 2.0 and sig["wortbezug"]["with"]["n"] == 2
        assert [c["category"] for c in b["categories_vs_fit"]] == ["Personalabbau", "Sport", "ohne Ereignisart"]
        assert b["direction_by_group"]["markierung"] == {"passt": 1, "neutral": 0, "widerspricht": 0, "unklar": 1}
        assert b["ranking"] == {"n_windows_with_two_or_more": 1, "top1_is_best": 1, "share": 1.0}
        assert b["reference"]["treffer"]["n"] == 1 and b["reference"]["fisher_p"] is None
        text = rx.report_markdown({"generated_at": "jetzt", "n_permutations": 200, "seed": 1, "validity_path": None, "stage_tests": None,
                                   "fit_tests": b, "ratings_check": rx.validate_ratings(ratings, sheet), "ratings_rows": rows})
        assert "## Teil B" in text and "| hoch | 1 | 0 | 0 | 0 | 1 | 3,00 | 1/1 (100 %) |" in text
        assert "Titel 1" not in text and "https://x/" not in text, "die Auswertung nennt keine Titel und Links"
        assert "Personalabbau / passt." in text, "senkrechter Strich in der Begründung wird ersetzt"
        assert "3 von 3 bewertet" in text

    def test_join_rejects_foreign_key(self):
        sheet, key = _sheet_and_key()
        other = {"windows": [dict(k, id="X-" + k["id"]) for k in key["windows"]]}
        with pytest.raises(ValueError):
            rx.join_ratings(_ratings(sheet, []), sheet, other)

    def test_commands(self, tmp_path, capsys):
        sheet, key = _sheet_and_key()
        (tmp_path / "bogen.json").write_text(json.dumps(sheet), encoding="utf-8")
        (tmp_path / "schluessel.json").write_text(json.dumps(key), encoding="utf-8")
        partial = _ratings(sheet, [{"id": "F-001", "rank": 1, "passung": 3, "richtung": "passt", "begruendung": "x"}])
        (tmp_path / "teil.json").write_text(json.dumps(partial), encoding="utf-8")
        assert rx.main(["pruefen", "--bogen", str(tmp_path / "bogen.json"), "--ratings", str(tmp_path / "teil.json")]) == 1
        assert "1 von 3 bewertet" in capsys.readouterr().out
        full = _ratings(sheet, [{"id": "F-001", "rank": 1, "passung": 3, "richtung": "passt", "begruendung": "x"},
                                {"id": "F-001", "rank": 2, "passung": 0, "richtung": "unklar", "begruendung": "y"},
                                {"id": "F-002", "rank": 1, "passung": 2, "richtung": "neutral", "begruendung": "z"}])
        (tmp_path / "voll.json").write_text(json.dumps(full), encoding="utf-8")
        assert rx.main(["pruefen", "--bogen", str(tmp_path / "bogen.json"), "--ratings", str(tmp_path / "voll.json")]) == 0
        validity = {"windows": WINDOWS}
        (tmp_path / "validity.json").write_text(json.dumps(validity), encoding="utf-8")
        out_json, out_md = tmp_path / "out" / "a.json", tmp_path / "out" / "a.md"
        rc = rx.main(["auswerten", "--validity", str(tmp_path / "validity.json"), "--bogen", str(tmp_path / "bogen.json"),
                      "--key", str(tmp_path / "schluessel.json"), "--ratings", str(tmp_path / "voll.json"), "--permutations", "100",
                      "--json", str(out_json), "--md", str(out_md)])
        assert rc == 0
        data = json.loads(out_json.read_text(encoding="utf-8"))
        assert data["stage_tests"]["total"]["n_markers"] == 3 and data["fit_tests"]["n_ratings"] == 3
        assert data["validity_path"].endswith("validity.json") and len(data["ratings_rows"]) == 3 and len(data["windows"]) == 3
        text = out_md.read_text(encoding="utf-8")
        assert "## Teil A" in text and "## Teil B" in text and "## Anhang" in text and "Titel 1" not in text
        # nur Teil A, ohne Urteile
        assert rx.main(["auswerten", "--validity", str(tmp_path / "validity.json"), "--permutations", "50"]) == 0
        # Urteile ohne Bogen oder Schlüssel
        assert rx.main(["auswerten", "--validity", "", "--ratings", str(tmp_path / "voll.json")]) == 2
        # Schlüssel passt nicht zum Bogen
        wrong = dict(key, bogen_checksum="0000")
        (tmp_path / "falsch.json").write_text(json.dumps(wrong), encoding="utf-8")
        assert rx.main(["auswerten", "--validity", "", "--bogen", str(tmp_path / "bogen.json"), "--key", str(tmp_path / "falsch.json"),
                        "--ratings", str(tmp_path / "voll.json")]) == 2
        # Fehler in den Urteilen mit --strict
        (tmp_path / "kaputt.json").write_text(json.dumps(_ratings(sheet, [{"id": "F-001", "rank": 1, "passung": 9, "richtung": "passt", "begruendung": "x"}])), encoding="utf-8")
        assert rx.main(["auswerten", "--validity", "", "--bogen", str(tmp_path / "bogen.json"), "--key", str(tmp_path / "schluessel.json"),
                        "--ratings", str(tmp_path / "kaputt.json"), "--strict"]) == 1
