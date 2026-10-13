"""
Tests für scripts/dz1_baselines.py (Bezugsgrößen und Unsicherheit für den
DZ1-Wert, E9/E5 Regel 6): konstruierte Reihen, Annotationen und Ergebnisse, ohne
DB, ohne Netz und ohne Detektor. Geprüft werden Einlesen der Serien-CSVs,
Vorniveau, Zufallsmarkierungen (Lage, Doppelung, Abstand, Richtung,
Determinismus), die naive Regel (gegen eine Nachbildung des Prüfskripts),
Konsistenzprüfungen, Abgleich, Wilson, Perzentile, Bootstrap und die CLI.
Ein Test liest die versionierten Dateien und prüft den beobachteten Hauptwert
8/9/12 aus ``dz1_ergebnis.json``.

Ausführen:
    cd backend
    uv run python -m pytest tests/test_dz1_baselines.py -q -p no:cacheprovider
"""

import io
import json
import math
import os
import random
import sys
from collections import Counter

import pytest

BACKEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, BACKEND_DIR)
sys.path.insert(0, os.path.join(BACKEND_DIR, "scripts"))

import dz1_baselines as b  # noqa: E402
import evaluate_detection as ed  # noqa: E402

LS, LSE = b.VARIANTS
HEADER = "period;mean_durchschnittsbewertung;count;delta_vs_previous"


# ── Hilfen ───────────────────────────────────────────────────────────────────

def month_list(first_year: int, first_month: int, n: int):
    y, m = first_year, first_month
    out = []
    for _ in range(n):
        out.append(f"{y:04d}-{m:02d}")
        m += 1
        if m == 13:
            y, m = y + 1, 1
    return out


def evaluated_series(values, first=(2020, 1)):
    return list(zip(month_list(first[0], first[1], len(values)), [float(v) for v in values]))


def ann(company, period_from, period_to, direction):
    return {"company": company, "source": "employee", "dimension": "durchschnittsbewertung",
            "period_from": period_from, "period_to": period_to, "direction": direction, "note": "konstruiert"}


def det(date, direction, kind=ed.KIND_LEVEL):
    return {"kind": kind, "date": date, "direction": direction}


def csv_rows(values, counts=None, first=(2020, 1)):
    counts = counts or [8] * len(values)
    return [(p, v, n) for p, v, n in zip(month_list(first[0], first[1], len(values)), values, counts)]


def dz1_variant(annotations, detections, evaluated):
    """Variante im Format von dz1_ergebnis.json, erzeugt mit match_series."""
    m = ed.match_series(annotations, detections, evaluated)
    m["n_detections"] = len(detections)
    return m


def make_dataset():
    """Zwei geeignete Reihen (Alpha mit Eintrag, Beta ohne) und eine nicht geeignete (Gamma).

    Alpha: 20 bewertete Monate ab 2020-01 plus zwei dünne Monate; Anstieg 2020-11.
    Beta: 14 bewertete Monate. Gamma: 6 bewertete Monate."""
    alpha_vals = [3.0] * 10 + [4.0] * 10 + [3.5, 3.5]
    alpha_counts = [8] * 20 + [2, 2]
    rows = {1: csv_rows(alpha_vals, alpha_counts), 2: csv_rows([3.2] * 14), 3: csv_rows([3.0] * 6)}
    ev_alpha = {p for p, _ in b.evaluated_of(rows[1])}
    anns = [ann("Alpha AG", "2020-11", "2020-11", "rise")]
    ls = [det("2020-11", "rise"), det("2021-05", "fall")]
    lse = ls + [det("2020-04", "fall", ed.KIND_OUTLIER)]
    dz1 = {"series": [{
        "series": "Alpha AG / employee / durchschnittsbewertung", "company": "Alpha AG", "company_id": 1,
        "source": "employee", "dimension": "durchschnittsbewertung", "evaluated_months": 20,
        "variants": {LS: dz1_variant(anns, ls, ev_alpha), LSE: dz1_variant(anns, lse, ev_alpha)},
    }], "skipped": []}
    ann_doc = {"version": 3, "hinweise": {"zweck": "konstruiert"}, "annotations": anns}
    semi = {"git": {"commit": "abc"}, "series": [
        {"company_id": 1, "company": "Alpha AG", "evaluated_months": 20, "observed_level_shifts": 2, "observed_outliers": 1},
        {"company_id": 2, "company": "Beta GmbH", "evaluated_months": 14, "observed_level_shifts": 1, "observed_outliers": 1},
    ]}
    return dz1, ann_doc, semi, rows


def eval_counts(rows):
    return {cid: len(b.evaluated_of(r)) for cid, r in rows.items()}


def write_dataset(tmp_path, dz1, ann_doc, semi, rows):
    series_dir = tmp_path / "series"
    series_dir.mkdir()
    names = {1: "alpha_ag", 2: "beta_gmbh", 3: "gamma"}
    for cid, rs in rows.items():
        lines = [HEADER] + [f"{p};{'' if v is None else f'{v:.3f}'};{n};" for p, v, n in rs]
        (series_dir / f"{cid}_{names[cid]}_employee.csv").write_text("\n".join(lines) + "\n", encoding="utf-8")
    paths = {}
    for key, doc in (("dz1", dz1), ("annotations", ann_doc), ("semi", semi)):
        paths[key] = tmp_path / f"{key}.json"
        paths[key].write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")
    return paths, series_dir


# ── Nachbildung des Prüfskripts (Referenz für die exakte Übernahme) ──────────

def reference_naive(ev, k):
    """Naive Regel wie im Prüfskript des Gutachtens (ev: Liste (Monat, Mittel))."""
    sc = []
    for i in range(3, len(ev) - 2):
        pre = [m for _, m in ev[max(0, i - 6): i]]
        sc.append((abs(ev[i][1] - sum(pre) / len(pre)), i, "rise" if ev[i][1] > sum(pre) / len(pre) else "fall"))
    sc.sort(reverse=True)
    chosen = []
    for d, i, dr in sc:
        if len(chosen) >= k:
            break
        if all(abs(i - j) >= 3 for j, _ in chosen):
            chosen.append((i, dr))
    return sorted((ev[i][0], dr) for i, dr in chosen)


def reference_rand(ev, k, rng, informed=False):
    """Zufallsmarkierungen wie im Prüfskript des Gutachtens."""
    n = len(ev)
    pos = list(range(3, n - 2))
    chosen, tries = [], 0
    while len(chosen) < k and tries < 1000:
        tries += 1
        i = rng.choice(pos)
        if all(abs(i - j) >= 3 for j in chosen):
            chosen.append(i)
    out = []
    for i in chosen:
        if informed:
            pre = [m for _, m in ev[max(0, i - 6): i]]
            d = "rise" if ev[i][1] >= sum(pre) / len(pre) else "fall"
        else:
            d = rng.choice(["rise", "fall"])
        out.append((ev[i][0], d))
    return sorted(out)


# ── Serien-CSV und Vorniveau ─────────────────────────────────────────────────

class TestSeriesCsv:

    def test_parse_and_filter_evaluated_months(self):
        text = "\n".join([HEADER, "2020-03;3.500;5;", "2020-01;4.000;7;", "2020-02;;0;", "2020-04;2.000;4;",
                          "2020-05;3.100;12;0.1"]) + "\n"
        rows = b.parse_series_csv(io.StringIO(text))
        assert rows[0] == ("2020-03", 3.5, 5)
        assert ("2020-02", None, 0) in rows
        # sortiert, ohne leeres Mittel, ohne count < 5
        assert b.evaluated_of(rows) == [("2020-01", 4.0), ("2020-03", 3.5), ("2020-05", 3.1)]

    def test_min_reviews_parameter(self):
        rows = [("2020-01", 3.0, 4), ("2020-02", 3.0, 5)]
        assert b.evaluated_of(rows, min_reviews=4) == [("2020-01", 3.0), ("2020-02", 3.0)]


class TestPriorLevel:

    def test_prior_level(self):
        vals = [1, 2, 3, 4, 5, 6, 7, 8]
        assert b.prior_level(vals, 0) is None
        assert b.prior_level(vals, 3) == pytest.approx(2.0)
        assert b.prior_level(vals, 7) == pytest.approx(sum(vals[1:7]) / 6)   # höchstens 6 Vorgänger
        assert b.prior_level(vals, 7, width=2) == pytest.approx(6.5)

    def test_informed_direction_tie_is_rise(self):
        assert b.informed_direction([3.0, 3.0], 1) == "rise"
        assert b.informed_direction([3.0, 2.9], 1) == "fall"
        assert b.informed_direction([3.0, 3.1], 1) == "rise"
        assert b.informed_direction([3.0], 0) is None


# ── Zufallsmarkierungen ──────────────────────────────────────────────────────

class TestPositions:

    def test_allowed_positions(self):
        assert b.allowed_positions(10) == list(range(10))
        assert b.allowed_positions(10, edge=3) == [3, 4, 5, 6, 7]   # 3 davor, 3 ab der Stelle
        assert b.allowed_positions(5, edge=3) == []
        assert b.allowed_positions(0) == []

    def test_no_duplicates_and_all_positions_reachable(self):
        rng = random.Random(1)
        for _ in range(200):
            pos = b.draw_positions(6, 4, rng)
            assert len(pos) == 4 and len(set(pos)) == 4
        assert sorted(b.draw_positions(6, 6, random.Random(2))) == list(range(6))

    def test_uniform_without_edge(self):
        rng = random.Random(3)
        counts = Counter(b.draw_positions(4, 1, rng)[0] for _ in range(4000))
        assert set(counts) == {0, 1, 2, 3}
        assert all(800 < c < 1200 for c in counts.values())

    def test_edge_and_gap(self):
        rng = random.Random(4)
        for _ in range(200):
            pos = b.draw_positions(20, 3, rng, edge=3, min_gap=3)
            assert all(3 <= i <= 17 for i in pos)
            assert all(abs(i - j) >= 3 for i in pos for j in pos if i != j)

    def test_impossible_k_returns_fewer(self):
        assert b.draw_positions(6, 3, random.Random(5), edge=3, min_gap=3) == [3]   # nur Stelle 3 erlaubt
        pos = b.draw_positions(7, 3, random.Random(5), edge=3, min_gap=3)           # Stellen 3 und 4, Abstand 3
        assert len(pos) == 1 and pos[0] in (3, 4)
        assert b.draw_positions(7, 0, random.Random(5)) == []

    def test_deterministic(self):
        a = [b.draw_positions(30, 4, random.Random(9)) for _ in range(3)]
        assert a[0] == a[1] == a[2]


class TestRandomDetections:

    def test_format_and_sorted(self):
        ev = evaluated_series([3.0] * 12)
        dets = b.random_detections(ev, 3, random.Random(1))
        assert [d["date"] for d in dets] == sorted(d["date"] for d in dets)
        assert all(d["kind"] == b.KIND_RANDOM and d["direction"] in ("rise", "fall") for d in dets)

    def test_informed_follows_prior_level(self):
        rising = evaluated_series([1.0 + 0.1 * i for i in range(15)])
        falling = evaluated_series([4.0 - 0.1 * i for i in range(15)])
        rng = random.Random(2)
        for _ in range(50):
            assert {d["direction"] for d in b.random_detections(rising, 3, rng, b.DIRECTIONS[1], edge=1)} == {"rise"}
            assert {d["direction"] for d in b.random_detections(falling, 3, rng, b.DIRECTIONS[1], edge=1)} == {"fall"}

    def test_informed_without_prior_level_is_coin(self):
        ev = evaluated_series([3.0])
        seen = {b.random_detections(ev, 1, random.Random(s), b.DIRECTIONS[1])[0]["direction"] for s in range(40)}
        assert seen == {"rise", "fall"}

    def test_coin_roughly_balanced(self):
        ev = evaluated_series([3.0] * 30)
        rng = random.Random(6)
        dirs = Counter(d["direction"] for _ in range(500) for d in b.random_detections(ev, 2, rng))
        assert 400 < dirs["rise"] < 600

    def test_unknown_direction_rule(self):
        with pytest.raises(ValueError):
            b.random_detections(evaluated_series([3.0] * 5), 1, random.Random(0), "unbekannt")

    @pytest.mark.parametrize("informed", [False, True])
    def test_matches_review_script_with_same_rng(self, informed):
        rng_data = random.Random(11)
        for seed in range(20):
            ev = evaluated_series([round(rng_data.uniform(2.5, 4.5), 3) for _ in range(40)])
            mine = b.random_detections(ev, 4, random.Random(seed), b.DIRECTIONS[int(informed)],
                                       edge=b.PELT_EDGE, min_gap=b.PELT_GAP)
            ref = reference_rand(ev, 4, random.Random(seed), informed)
            assert [(d["date"], d["direction"]) for d in mine] == ref


# ── Naive Regel ──────────────────────────────────────────────────────────────

class TestNaive:

    def test_picks_largest_deviations(self):
        vals = [3.0] * 30
        vals[10] = 4.0     # +1,0 gegen Vorniveau 3,0
        vals[20] = 2.4     # −0,6
        dets = b.naive_topk(evaluated_series(vals), 2)
        assert [(d["date"], d["direction"]) for d in dets] == [("2020-11", "rise"), ("2021-09", "fall")]
        assert dets[0]["kind"] == b.KIND_NAIVE and dets[0]["deviation"] == pytest.approx(1.0)

    def test_gap_and_edge(self):
        vals = [3.0] * 30
        vals[1] = 5.0      # vor dem Rand (Index < 3): nie gewählt
        vals[10], vals[11] = 4.5, 4.4   # benachbart: nur einer
        vals[20] = 2.0     # −1,0; größer als die Abweichung bei Index 3 (Vorniveau mit dem Wert 5,0)
        dets = b.naive_topk(evaluated_series(vals), 2)
        assert [(d["date"], d["direction"]) for d in dets] == [("2020-11", "rise"), ("2021-09", "fall")]

    def test_tie_prefers_larger_index(self):
        vals = [3.0] * 20
        vals[6] = 3.8
        vals[14] = 3.8
        assert [d["date"] for d in b.naive_topk(evaluated_series(vals), 1)] == ["2021-03"]

    def test_k_zero_and_short_series(self):
        assert b.naive_topk(evaluated_series([3.0] * 20), 0) == []
        assert b.naive_topk(evaluated_series([3.0] * 5), 2) == []

    def test_matches_review_script(self):
        rng = random.Random(7)
        for _ in range(30):
            n = rng.randint(8, 60)
            ev = evaluated_series([round(rng.uniform(2.0, 4.8), 3) for _ in range(n)])
            k = rng.randint(0, 6)
            assert [(d["date"], d["direction"]) for d in b.naive_topk(ev, k)] == reference_naive(ev, k)


# ── Eingaben und Konsistenzprüfungen ─────────────────────────────────────────

class TestBuildInputs:

    def test_consistent_dataset(self):
        dz1, ann_doc, semi, rows = make_dataset()
        series, checks = b.build_inputs(dz1, ann_doc, semi, rows, eval_counts(rows))
        assert all(c["ok"] for c in checks), checks
        assert [s["company_id"] for s in series] == [1, 2]
        alpha, beta = series
        assert alpha["annotated"] and not beta["annotated"]
        assert len(alpha["evaluated"]) == 20 and len(beta["evaluated"]) == 14
        assert alpha["k"] == {LS: 2, LSE: 3} and beta["k"] == {LS: 1, LSE: 2}
        assert [d["date"] for d in alpha["detections"][LSE]] == ["2020-04", "2020-11", "2021-05"]

    def test_detections_from_dz1(self):
        v = {"hits": [{"detection": det("2020-05", "rise")}], "extras": [det("2020-02", "fall", ed.KIND_OUTLIER)]}
        assert [d["date"] for d in b.detections_from_dz1(v)] == ["2020-02", "2020-05"]

    def test_marker_mismatch_with_simulation(self):
        dz1, ann_doc, semi, rows = make_dataset()
        semi["series"][0]["observed_level_shifts"] = 3
        _, checks = b.build_inputs(dz1, ann_doc, semi, rows, eval_counts(rows))
        assert not {c["name"]: c for c in checks}["markierungen"]["ok"]

    def test_evaluated_month_mismatch(self):
        dz1, ann_doc, semi, rows = make_dataset()
        semi["series"][1]["evaluated_months"] = 15
        _, checks = b.build_inputs(dz1, ann_doc, semi, rows, eval_counts(rows))
        assert not {c["name"]: c for c in checks}["bewertete_monate"]["ok"]

    def test_annotation_mismatch(self):
        dz1, ann_doc, semi, rows = make_dataset()
        ann_doc["annotations"][0]["direction"] = "fall"
        _, checks = b.build_inputs(dz1, ann_doc, semi, rows, eval_counts(rows))
        assert not {c["name"]: c for c in checks}["referenzzeitraeume"]["ok"]

    def test_eligible_set_mismatch(self):
        dz1, ann_doc, semi, rows = make_dataset()
        rows[3] = csv_rows([3.0] * 12)    # Gamma wäre jetzt geeignet, fehlt aber in der Simulation
        _, checks = b.build_inputs(dz1, ann_doc, semi, rows, eval_counts(rows))
        assert not {c["name"]: c for c in checks}["geeignete_reihen"]["ok"]

    def test_annotation_for_unknown_series(self):
        dz1, ann_doc, semi, rows = make_dataset()
        ann_doc["annotations"].append(ann("Gamma", "2020-03", "2020-03", "rise"))
        _, checks = b.build_inputs(dz1, ann_doc, semi, rows, eval_counts(rows))
        assert not {c["name"]: c for c in checks}["reihen"]["ok"]

    def test_missing_csv_raises(self):
        dz1, ann_doc, semi, rows = make_dataset()
        del rows[2]
        with pytest.raises(ValueError):
            b.build_inputs(dz1, ann_doc, semi, rows)

    def test_entries_hash_ignores_hinweise(self):
        _, ann_doc, _, _ = make_dataset()
        h = b.entries_sha256(ann_doc)
        assert b.entries_sha256({**ann_doc, "hinweise": {"zweck": "anders"}, "version": 4}) == h
        changed = json.loads(json.dumps(ann_doc))
        changed["annotations"][0]["period_to"] = "2020-12"
        assert b.entries_sha256(changed) != h


# ── Abgleich und Kennzahlen ──────────────────────────────────────────────────

class TestObservedAndNaive:

    def test_observed_counts(self):
        dz1, ann_doc, semi, rows = make_dataset()
        series, _ = b.build_inputs(dz1, ann_doc, semi, rows)
        obs = {o["company_id"]: o for o in b.observed_counts(series, LS)}
        assert (obs[1]["tp"], obs[1]["fp"], obs[1]["fn"], obs[1]["reproduced"]) == (1, 1, 0, True)
        assert (obs[2]["tp"], obs[2]["fp"], obs[2]["fn"], obs[2]["reproduced"]) == (0, 1, 0, None)
        obs2 = {o["company_id"]: o for o in b.observed_counts(series, LSE)}
        assert (obs2[1]["fp"], obs2[2]["fp"]) == (2, 2)

    def test_reproduced_false_on_mismatch(self):
        dz1, ann_doc, semi, rows = make_dataset()
        dz1["series"][0]["variants"][LS]["fp"] = 5
        series, _ = b.build_inputs(dz1, ann_doc, semi, rows)
        assert b.observed_counts(series, LS)[0]["reproduced"] is False

    def test_naive_counts(self):
        dz1, ann_doc, semi, rows = make_dataset()
        series, _ = b.build_inputs(dz1, ann_doc, semi, rows)
        nv = {n["company_id"]: n for n in b.naive_counts(series, LS)}
        # Alpha: Sprung bei 2020-11 (Index 10) ist die größte Abweichung -> Treffer
        assert nv[1]["tp"] == 1 and "2020-11" in nv[1]["dates"]
        assert nv[2]["tp"] == 0 and nv[2]["fp"] == len(nv[2]["dates"]) == 1


class TestStatistics:

    def test_wilson(self):
        lo, hi = b.wilson(8, 17)
        assert (round(lo, 2), round(hi, 2)) == (0.26, 0.69)
        lo, hi = b.wilson(8, 20)
        assert (round(lo, 2), round(hi, 2)) == (0.22, 0.61)
        assert b.wilson(0, 10)[0] == 0.0
        assert b.wilson(3, 0) is None
        a, c = b.wilson(3, 10), b.wilson(7, 10)
        assert a[0] == pytest.approx(1 - c[1]) and a[1] == pytest.approx(1 - c[0])

    def test_quantile_rank_rule(self):
        vals = list(range(100))
        assert b.quantile(vals, 0.95) == 95
        assert b.quantile(vals, 0.99) == 99
        assert b.quantile(vals, 1.0) == 99
        assert b.quantile(list(range(10)), 0.025) == 0
        assert b.quantile([], 0.5) is None

    def test_summarize_draws(self):
        draws = [(0, 17, 20)] * 6 + [(1, 16, 19)] * 2 + [(8, 9, 12)] * 2
        observed = ed.metrics(8, 9, 12)["f1"]
        s = b.summarize_draws(draws, observed)
        assert s["draws"] == 10 and s["n_ge_observed"] == 2 and s["share_ge_observed"] == 0.2
        assert s["share_ge_observed_plus1"] == round(3 / 11, 4)
        assert s["tp_distribution"] == {"0": 6, "1": 2, "8": 2}
        assert s["f1_median"] == 0.0 and s["f1_max"] == round(observed, 4)
        assert s["tp_mean"] == pytest.approx(1.8)
        # zusätzliche FP aus Reihen ohne Eintrag senken F1 je Ziehung
        s2 = b.summarize_draws(draws, ed.metrics(8, 11, 12)["f1"], extra_fp=2)
        assert s2["n_ge_observed"] == 2 and s2["f1_max"] == round(ed.metrics(8, 11, 12)["f1"], 4)

    def test_f1_is_linear_in_tp_with_fixed_markers(self):
        for tp in range(0, 9):
            assert ed.metrics(tp, 17 - tp, 20 - tp)["f1"] == pytest.approx(2 * tp / 37)

    def test_bootstrap_degenerate_and_deterministic(self):
        same = [(2, 1, 1)] * 5
        r = b.cluster_bootstrap(same, 200, random.Random(1))
        f1 = ed.metrics(2, 1, 1)["f1"]
        assert r["f1_interval95"] == [round(f1, 4), round(f1, 4)] and r["undefined"] == 0
        mixed = [(2, 1, 1), (0, 3, 2), (1, 0, 0), (0, 0, 3)]
        assert b.cluster_bootstrap(mixed, 300, random.Random(5)) == b.cluster_bootstrap(mixed, 300, random.Random(5))
        lo, hi = b.cluster_bootstrap(mixed, 300, random.Random(5))["f1_interval95"]
        assert 0.0 <= lo <= hi <= 1.0

    def test_bootstrap_counts_undefined(self):
        r = b.cluster_bootstrap([(0, 0, 0)] * 3, 50, random.Random(0))
        assert r["undefined"] == 50 and r["f1_interval95"] is None


class TestRandomBaseline:

    def _series(self, values, anns, k):
        ev = evaluated_series(values)
        return [{"company_id": 1, "company": "Alpha AG", "evaluated": ev, "annotations": anns, "annotated": True,
                 "k": {LS: k, LSE: k}}]

    def test_window_over_whole_series_always_hit_when_informed(self):
        vals = [1.0 + 0.05 * i for i in range(20)]
        months = month_list(2020, 1, 20)
        series = self._series(vals, [ann("Alpha AG", months[0], months[-1], "rise")], 1)
        draws, short = b.random_baseline(series, LS, 100, random.Random(1), b.DIRECTIONS[1], edge=3, min_gap=3)
        assert short == 0 and set(draws) == {(1, 0, 0)}

    def test_counts_bounds_and_determinism(self):
        vals = [3.0, 3.4, 2.8, 3.9, 3.1] * 6
        months = month_list(2020, 1, 30)
        anns = [ann("Alpha AG", months[5], months[6], "rise"), ann("Alpha AG", months[20], months[20], "fall")]
        series = self._series(vals, anns, 3)
        draws, short = b.random_baseline(series, LS, 300, random.Random(2))
        assert short == 0
        assert all(tp + fp == 3 and tp + fn == 2 and 0 <= tp <= 2 for tp, fp, fn in draws)
        assert b.random_baseline(series, LS, 300, random.Random(2)) == (draws, short)

    def test_unannotated_series_not_drawn(self):
        series = self._series([3.0] * 12, [], 2)
        series[0]["annotated"] = False
        draws, _ = b.random_baseline(series, LS, 10, random.Random(0))
        assert set(draws) == {(0, 0, 0)}


class TestCompute:

    def test_structure_scopes_and_determinism(self):
        dz1, ann_doc, semi, rows = make_dataset()
        series, _ = b.build_inputs(dz1, ann_doc, semi, rows)
        out = b.compute(series, seed=1, draws=50, boot_draws=50)
        assert out["reproduced_all"] is True
        main, rk = out["results"]["hauptwert"][LS], out["results"]["regelkonform"][LS]
        assert (main["observed"]["tp"], main["observed"]["fp"], main["observed"]["fn"]) == (1, 1, 0)
        assert (rk["observed"]["tp"], rk["observed"]["fp"], rk["observed"]["fn"]) == (1, 2, 0)
        assert main["n_series"] == 1 and rk["n_series"] == 2 and rk["n_markers"] == 3
        assert set(main["random"]) == set(b.DIRECTIONS)
        assert set(out["sensitivity_wie_pelt"]["hauptwert"]) == {LS}
        assert out["results"]["hauptwert"][LSE]["observed"]["fp"] == 2
        assert b.compute(series, seed=1, draws=50, boot_draws=50) == out

    def test_report_contains_sections(self):
        dz1, ann_doc, semi, rows = make_dataset()
        series, checks = b.build_inputs(dz1, ann_doc, semi, rows, eval_counts(rows))
        out = b.compute(series, seed=1, draws=20, boot_draws=20)
        text = b.format_report({"params": {"seed": 1, "draws": 20, "bootstrap_draws": 20}, "checks": checks, **out})
        assert "Hauptwert" in text and "Regelkonform" in text and "Naive Top-k-Regel" in text
        assert "konstruiert" not in text     # keine Begründungstexte der Einträge im Bericht


# ── CLI ──────────────────────────────────────────────────────────────────────

class TestCli:

    def _args(self, paths, series_dir, out=None):
        args = ["--draws", "30", "--bootstrap", "30", "--dz1", str(paths["dz1"]), "--annotations",
                str(paths["annotations"]), "--semi", str(paths["semi"]), "--series-dir", str(series_dir)]
        return args + (["--json", str(out)] if out else [])

    def test_writes_json_with_provenance(self, tmp_path, capsys):
        paths, series_dir = write_dataset(tmp_path, *make_dataset())
        out = tmp_path / "out" / "baselines.json"
        assert b.main(self._args(paths, series_dir, out)) == 0
        rep = json.loads(out.read_text(encoding="utf-8"))
        prov = rep["provenance"]
        assert len(prov["script_sha256"]) == 64 and len(prov["evaluate_detection_sha256"]) == 64
        assert prov["inputs"]["annotations"]["version"] == 3
        assert prov["inputs"]["semisynthetisch"]["git_commit"] == "abc"
        assert [c["company_id"] for c in prov["inputs"]["series_csv"]] == [1, 2, 3]
        assert [c["used"] for c in prov["inputs"]["series_csv"]] == [True, True, False]
        assert rep["params"]["seed"] == b.SEED and rep["params"]["draws"] == 30
        assert all(c["ok"] for c in rep["checks"])
        assert "konstruiert" not in out.read_text(encoding="utf-8")
        assert "Ergebnis gespeichert" in capsys.readouterr().out

    def test_aborts_without_json_on_failed_check(self, tmp_path, capsys):
        dz1, ann_doc, semi, rows = make_dataset()
        dz1["series"][0]["variants"][LS]["tp"] = 0          # Neuabgleich weicht ab
        paths, series_dir = write_dataset(tmp_path, dz1, ann_doc, semi, rows)
        out = tmp_path / "baselines.json"
        assert b.main(self._args(paths, series_dir, out)) == 1
        assert not out.exists()
        assert "Abbruch" in capsys.readouterr().out

    def test_rejects_invalid_draws(self):
        with pytest.raises(SystemExit):
            b.main(["--draws", "0"])


# ── Versionierte Dateien ─────────────────────────────────────────────────────

class TestVersionedFiles:

    def test_observed_main_value_from_dz1_ergebnis(self):
        """Neuabgleich aus dz1_ergebnis.json, annotations.json und den Serien-CSVs: 8/9/12."""
        series, checks, _ = b.load_inputs()
        assert all(c["ok"] for c in checks), checks
        annotated = [s for s in series if s["annotated"]]
        assert len(annotated) == 8 and len(series) == 15
        obs = b.observed_counts(series, LS)
        assert all(o["reproduced"] for o in obs if o["annotated"])
        assert b.sum_counts(o for o in obs if o["annotated"]) == (8, 9, 12)
        assert b.sum_counts(obs) == (8, 11, 12)
        obs_e = b.observed_counts(series, LSE)
        assert b.sum_counts(o for o in obs_e if o["annotated"]) == (8, 15, 12)
        assert b.sum_counts(obs_e) == (8, 20, 12)
        assert math.isclose(ed.metrics(8, 9, 12)["f1"], 16 / 37)
