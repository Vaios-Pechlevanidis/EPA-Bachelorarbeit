"""
Tests für scripts/simulate_detection.py (semi-synthetische Prüfung der Erkennung,
E30): konstruierte Bewertungszeilen, ohne DB und ohne Netz. Geprüft werden beide
Rauschbedingungen (Belegung bleibt erhalten, es wird tatsächlich gemischt),
Wechselstellen, Einsetzen des Wechsels, Abgleich mit dem echten Detektor,
Determinismus über Seed, Prozesse und Zeilenreihenfolge, die Kennzahlen und der
Bericht (nur Aggregate, keine Einzelwerte).

Ausführen:
    cd backend
    uv run python -m pytest tests/anomaly/test_simulate_detection.py -q -p no:cacheprovider
"""

import gzip
import json
import math
import os
import sys
from collections import Counter

import numpy as np
import pytest

BACKEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
sys.path.insert(0, BACKEND_DIR)
sys.path.insert(0, os.path.join(BACKEND_DIR, "scripts"))

import simulate_detection as sd  # noqa: E402
from services.rating_series_service import build_monthly_series, month_key  # noqa: E402

COL = sd.COLUMN


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


def make_rows(counts, values=(3.0, 4.0), first=(2018, 1), seed=0):
    """Zeilen mit ``counts[i]`` Bewertungen im i-ten Monat; Werte zufällig aus ``values``."""
    rng = np.random.default_rng(seed)
    rows, rid = [], 0
    for month, n in zip(month_list(*first, len(counts)), counts):
        for _ in range(n):
            rid += 1
            rows.append({"id": rid, "datum": f"{month}-15T10:00:00+00:00", COL: float(rng.choice(values))})
    return rows


def per_month(rows):
    counts, values = Counter(), Counter()
    for r in rows:
        mk = month_key(r.get("datum"))
        if mk:
            counts[mk] += 1
            if r.get(COL) is not None:
                values[mk] += 1
    return counts, values


def series_of(means, n=8, first=(2018, 1)):
    return [{"period": p, "mean": mu, "count": n, "n_values": n, "evaluated": mu is not None}
            for p, mu in zip(month_list(*first, len(means)), means)]


DENSE = make_rows([20] * 48, values=(3.0, 4.0), seed=5)   # SD 0,5, n = 20: Standardfehler etwa 0,11
N_DESIGN = len(sd.DESIGN)


# ── Rauschbedingung "bewertungen" ────────────────────────────────────────────

class TestPermuteValues:

    def test_keeps_counts_and_values_per_month_and_the_multiset(self):
        rows = make_rows([5, 7, 12, 6, 9, 5] * 3)
        rows.append({"id": 999, "datum": None, COL: 1.0})          # ohne Datum
        rows.append({"id": 1000, "datum": "2018-02-01", COL: None})  # ohne Wert
        out = sd.permute_values(rows, COL, np.random.default_rng(1))
        assert per_month(out) == per_month(rows)
        dated = lambda rs: sorted(r[COL] for r in rs if month_key(r.get("datum")) and r[COL] is not None)  # noqa: E731
        assert dated(out) == dated(rows)
        assert out[-2] == rows[-2] and out[-1] == rows[-1]

    def test_actually_mixes_values_across_time(self):
        rows = [{"id": i, "datum": f"{p}-10", COL: 1.0 if i < 120 else 5.0}
                for i, p in enumerate(m for m in month_list(2018, 1, 24) for _ in range(10))]
        out = sd.permute_values(rows, COL, np.random.default_rng(0))
        first_half = [r[COL] for r in out[:120]]
        assert 2.0 < float(np.mean(first_half)) < 4.0
        assert any(a[COL] != b[COL] for a, b in zip(out, rows))

    def test_series_belegung_is_unchanged(self):
        rows = make_rows([5, 3, 8, 12, 6, 0, 5, 9] * 2)
        before = build_monthly_series(rows, COL)
        after = build_monthly_series(sd.permute_values(rows, COL, np.random.default_rng(7)), COL)
        assert [(m["period"], m["count"], m["n_values"], m["evaluated"]) for m in after] == \
               [(m["period"], m["count"], m["n_values"], m["evaluated"]) for m in before]

    def test_does_not_mutate_input_and_is_deterministic(self):
        rows = make_rows([6] * 12)
        snapshot = [dict(r) for r in rows]
        a = sd.permute_values(rows, COL, np.random.default_rng(3))
        b = sd.permute_values(rows, COL, np.random.default_rng(3))
        assert rows == snapshot
        assert a == b

    def test_input_order_does_not_matter(self):
        rows = make_rows([6, 9, 5, 7] * 4)
        a = {r["id"]: r[COL] for r in sd.permute_values(rows, COL, np.random.default_rng(4))}
        b = {r["id"]: r[COL] for r in sd.permute_values(list(reversed(rows)), COL, np.random.default_rng(4))}
        assert a == b


# ── Rauschbedingung "monate" ─────────────────────────────────────────────────

class TestPermuteMonths:

    def test_keeps_calendar_slots_and_the_set_of_months(self):
        series = series_of([3.0, None, 3.4, 3.8, None, 4.2, 2.9], n=7)
        for i, m in enumerate(series):
            m["count"] = m["n_values"] = 5 + i
        out = sd.permute_months(series, np.random.default_rng(2))
        assert [m["period"] for m in out] == [m["period"] for m in series]
        assert [m["evaluated"] for m in out] == [m["evaluated"] for m in series]
        assert [m["mean"] for m in out if not m["evaluated"]] == [None, None]
        payload = lambda s: sorted((m["mean"], m["count"], m["n_values"]) for m in s if m["evaluated"])  # noqa: E731
        assert payload(out) == payload(series)

    def test_moves_months_and_keeps_mean_with_its_count(self):
        series = series_of([1.0 + i / 10 for i in range(30)])
        for i, m in enumerate(series):
            m["count"] = m["n_values"] = 100 + i
        out = sd.permute_months(series, np.random.default_rng(0))
        assert [m["mean"] for m in out] != [m["mean"] for m in series]
        assert all(round((m["mean"] - 1.0) * 10) == m["count"] - 100 for m in out)


# ── Wechselstelle und Einsetzen ──────────────────────────────────────────────

class TestChangeAndInjection:

    def test_change_index_respects_margin(self):
        rng = np.random.default_rng(0)
        drawn = {sd.choose_change_index(20, 6, rng) for _ in range(500)}
        assert min(drawn) == 6 and max(drawn) == 14

    def test_minimum_length_has_exactly_one_position(self):
        assert sd.choose_change_index(12, 6, np.random.default_rng(0)) == 6

    @pytest.mark.parametrize("n, margin", [(11, 6), (13, 0)])
    def test_invalid_raises(self, n, margin):
        with pytest.raises(ValueError):
            sd.choose_change_index(n, margin, np.random.default_rng(0))

    def test_end_index_leaves_three_to_five_months_after(self):
        rng = np.random.default_rng(0)
        drawn = {sd.choose_end_index(40, 6, rng) for _ in range(500)}
        assert {40 - k for k in drawn} == {3, 4, 5}
        assert sd.choose_end_index(12, 6, np.random.default_rng(1)) in {7, 8, 9}

    def test_inject_shifts_from_change_month_on(self):
        series = series_of([3.0, None, 3.2, 3.4, 3.6])
        out = sd.inject_shift(series, "2018-03", -0.5)
        assert [m["mean"] for m in out] == [3.0, None, 2.7, 2.9, 3.1]
        assert [m["mean"] for m in series] == [3.0, None, 3.2, 3.4, 3.6]  # Eingabe unverändert

    def test_delta_zero_leaves_series_unchanged(self):
        series = series_of([3.1, 3.2, 3.3])
        assert sd.inject_shift(series, "2018-02", 0.0) == series

    def test_months_between_and_neighbours(self):
        assert sd.months_between("2019-11", "2020-02") == 3
        assert sd.months_between("2020-02", "2019-11") == -3
        evaluated = [{"n_values": n} for n in (5, 6, 7, 20, 30, 40, 9)]
        assert sd.neighbour_reviews(evaluated, 3) == min(5 + 6 + 7, 20 + 30 + 40)


# ── Eine Wiederholung mit dem echten Detektor ────────────────────────────────

class TestReplicate:

    def test_record_layout(self):
        recs = sd.run_company_rep(DENSE, company_id=1, rep=0, deltas=(0.0, 0.5, 1.0))
        assert len(recs) == N_DESIGN * 3
        assert {(r["condition"], r["placement"]) for r in recs} == set(sd.DESIGN)
        for key in sd.DESIGN:
            group = [r for r in recs if (r["condition"], r["placement"]) == key]
            assert [r["delta"] for r in group] == [0.0, 0.5, 1.0]
            assert len({(r["change_period"], r["direction"], r["n_at_change"]) for r in group}) == 1

    def test_large_shift_is_hit_in_the_right_direction(self):
        for rep in range(4):
            for r in sd.run_company_rep(DENSE, company_id=1, rep=rep, deltas=(1.0,)):
                assert r["hit"], r
                assert abs(r["loc_error"]) <= 1
                assert (r["detected_delta"] > 0) == (r["direction"] == "rise")
                assert abs(r["detected_delta"]) == pytest.approx(1.0, abs=0.3)

    def test_both_directions_occur(self):
        dirs = {r["direction"] for rep in range(12)
                for r in sd.run_company_rep(DENSE, company_id=1, rep=rep, deltas=(0.0,))}
        assert dirs == {"rise", "fall"}

    def test_null_condition_injects_nothing(self, monkeypatch):
        seen = []
        real = sd.inject_shift

        def spy(series, change_period, delta):
            seen.append(delta)
            return real(series, change_period, delta)

        monkeypatch.setattr(sd, "inject_shift", spy)
        sd.run_company_rep(DENSE, company_id=1, rep=0, deltas=(0.0, 0.5))
        assert seen and all(abs(d) == 0.5 for d in seen)

    def test_null_record_equals_detector_on_the_noise_series(self):
        rec = [r for r in sd.run_company_rep(DENSE, company_id=1, rep=2, deltas=(0.0,))
               if r["condition"] == "bewertungen" and r["placement"] == "mitte"][0]
        rng = np.random.default_rng(np.random.SeedSequence([sd.SEED, 1, 2]))
        series = build_monthly_series(sd.permute_values(DENSE, COL, rng), COL)
        found = sd.detect_anomalies(series, company_id=1, source=sd.SOURCE, dimension=sd.DIMENSION)
        assert rec["n_detections"] == len(found)

    def test_n_at_change_is_the_change_month(self):
        counts = [5 + (i % 17) for i in range(40)]
        rows = make_rows(counts, seed=3)
        n_by_month = dict(zip(month_list(2018, 1, 40), counts))
        for r in sd.run_company_rep(rows, company_id=1, rep=1, deltas=(0.0,)):
            if r["condition"] == "bewertungen":
                assert r["n_at_change"] == n_by_month[r["change_period"]]

    def test_outlier_months_are_counted_separately(self, monkeypatch):
        base = sd.run_company_rep(DENSE, company_id=1, rep=0, deltas=(0.5,))
        monkeypatch.setattr(sd, "detect_outlier_months", lambda *a, **k: [{"date": "2018-05"}] * 4)
        patched = sd.run_company_rep(DENSE, company_id=1, rep=0, deltas=(0.5,))
        assert [r["extras"] for r in patched] == [r["extras"] for r in base]
        assert all(r["n_outliers"] == 4 for r in patched)

    def test_same_seed_same_result_other_rep_other_draw(self):
        a = sd.run_company_rep(DENSE, company_id=1, rep=0, deltas=(0.5,))
        b = sd.run_company_rep(DENSE, company_id=1, rep=0, deltas=(0.5,))
        assert a == b
        draws = {sd.run_company_rep(DENSE, company_id=1, rep=r, deltas=(0.0,))[0]["change_period"] for r in range(10)}
        assert len(draws) > 1

    def test_seed_and_company_enter_the_draw(self):
        def draw(**kw):
            r = sd.run_company_rep(DENSE, rep=0, deltas=(0.0,), **kw)[0]
            return r["change_period"], r["direction"]
        base = draw(company_id=1, seed=1)
        assert any(draw(company_id=1, seed=s) != base for s in range(2, 8))
        assert any(draw(company_id=c, seed=1) != base for c in range(2, 8))

    def test_row_order_does_not_change_the_result(self):
        a = sd.run_company_rep(DENSE, company_id=1, rep=1, deltas=(0.0, 0.5))
        b = sd.run_company_rep(list(reversed(DENSE)), company_id=1, rep=1, deltas=(0.0, 0.5))
        assert a == b


class TestSimulate:

    def test_result_does_not_depend_on_workers(self):
        data = {1: DENSE, 2: make_rows([6] * 30, seed=9)}
        one = sd.simulate(data, reps=2, deltas=(0.0, 0.75), workers=1)
        two = sd.simulate(data, reps=2, deltas=(0.0, 0.75), workers=2)
        assert one == two
        assert len(one) == 2 * 2 * N_DESIGN * 2

    def test_fewer_reps_are_a_prefix(self):
        data = {1: DENSE}
        three = sd.simulate(data, reps=3, deltas=(0.5,))
        two = sd.simulate(data, reps=2, deltas=(0.5,))
        assert two == [r for r in three if r["rep"] < 2]


# ── Kennzahlen ───────────────────────────────────────────────────────────────

def rec(hit, extras, delta=0.5, company_id=1, n_at_change=8, loc=0, det_delta=0.5, high=True, outliers=0,
        near=0, nearest=None, direction="rise", condition="bewertungen", placement="mitte", sigma=0.4,
        n_neighbours=40, gap=0, out_of_range=False):
    return {"hit": hit, "extras": extras, "extras_near": near, "delta": delta, "company_id": company_id,
            "n_at_change": n_at_change, "loc_error": loc if hit else None,
            "detected_delta": det_delta if hit else None, "detected_high": high if hit else None,
            "n_outliers": outliers, "n_detections": int(hit) + extras,
            "nearest_same_dir": (abs(loc) if hit else nearest), "direction": direction, "condition": condition,
            "placement": placement, "sigma_sim": sigma, "n_neighbours": n_neighbours, "gap_before": gap,
            "out_of_range": out_of_range}


class TestSummary:

    def test_metrics(self):
        records = [rec(True, 0, loc=1, det_delta=0.6), rec(True, 1, loc=-1, det_delta=-0.4, high=False, near=1),
                   rec(False, 2, outliers=1, nearest=5), rec(False, 0, outliers=1, out_of_range=True)]
        s = sd.summarize(records)
        assert s["reps"] == 4 and s["hits"] == 2
        assert s["recall"] == 0.5
        assert s["recall_tol3"] == 0.5 and s["recall_tol6"] == 0.75
        assert s["detections_mean"] == 1.25 and s["p_any_detection"] == 0.75
        assert s["extras_mean"] == 0.75 and s["extras_near_mean"] == 0.25 and s["p_any_extra"] == 0.5
        assert s["precision"] == pytest.approx(2 / 5, abs=1e-4)
        assert s["f1"] == pytest.approx(2 * 0.4 * 0.5 / 0.9, abs=1e-4)
        assert s["loc_error_mean_abs"] == 1.0
        assert s["delta_bias_median"] == pytest.approx(0.0, abs=1e-9)   # |0,6| − 0,5 und |−0,4| − 0,5
        assert s["share_high"] == 0.5 and s["outliers_mean"] == 0.5 and s["share_out_of_range"] == 0.25
        assert s["recall_wilson"][0] < 0.5 < s["recall_wilson"][1]

    def test_empty_set(self):
        s = sd.summarize([])
        assert s["reps"] == 0 and s["recall"] is None and s["recall_wilson"] is None

    def test_wilson_and_bootstrap(self):
        lo, hi = sd.wilson(50, 100)
        assert lo == pytest.approx(0.4038, abs=1e-3) and hi == pytest.approx(0.5962, abs=1e-3)
        values = {1: 0.2, 2: 0.4, 3: 0.6, 4: 0.8}
        iv = sd.bootstrap_series(values)
        assert iv == sd.bootstrap_series(values)            # fester Seed
        assert iv[0] < 0.5 < iv[1] and 0.2 <= iv[0] and iv[1] <= 0.8
        assert sd.bootstrap_series({}) is None

    def test_aggregate_splits_by_design_delta_series_and_strata(self):
        records = [rec(True, 0, delta=0.5, company_id=1, n_at_change=5, direction="fall"),
                   rec(False, 1, delta=0.5, company_id=2, n_at_change=12),
                   rec(False, 0, delta=0.0, company_id=1, n_at_change=5),
                   rec(False, 2, delta=0.0, company_id=2, n_at_change=12),
                   rec(True, 0, delta=0.5, company_id=1, condition="monate")]
        agg = sd.aggregate(records, (0.0, 0.5), evaluated_months={1: 50, 2: 100})
        total = {(t["condition"], t["placement"], t["delta"]): t for t in agg["total"]}
        assert total[("bewertungen", "mitte", 0.5)]["recall"] == 0.5
        assert total[("bewertungen", "mitte", 0.5)]["recall_series_range"] == [0.0, 1.0]
        assert total[("monate", "mitte", 0.5)]["recall"] == 1.0
        null = total[("bewertungen", "mitte", 0.0)]
        assert null["detections_mean"] == 1.0
        assert null["detections_per_100_months_median"] == pytest.approx(1.0)   # 0/50 und 2/100 je 100 Monate
        per = {(p["company_id"], p["condition"], p["delta"]): p for p in agg["per_series"]}
        assert per[(1, "bewertungen", 0.5)]["recall"] == 1.0 and per[(2, "bewertungen", 0.5)]["recall"] == 0.0
        strata = {(s["condition"], s["delta"], s["stratum"], s["label"]): s for s in agg["strata"]}
        assert strata[("bewertungen", 0.5, "richtung", "abfall")]["recall"] == 1.0
        assert strata[("bewertungen", 0.5, "wechselmonat", "n<10")]["recall"] == 1.0
        assert not any(s["delta"] == 0.0 for s in agg["strata"])


# ── Bericht und Aufruf ───────────────────────────────────────────────────────

class TestReport:

    def test_fingerprint_is_order_independent_and_value_sensitive(self):
        rows = make_rows([5] * 3)
        assert sd.fingerprint(rows) == sd.fingerprint(list(reversed(rows)))
        changed = [dict(r) for r in rows]
        changed[0][COL] = 1.0 if changed[0][COL] != 1.0 else 2.0
        assert sd.fingerprint(changed) != sd.fingerprint(rows)

    def test_describe_series(self):
        info = sd.describe_series(DENSE, company_id=1)
        assert info["eligible"] and info["evaluated_months"] == 48 and info["median_n"] == 20
        assert info["sd_review"] == pytest.approx(0.5, abs=0.05)
        assert len(info["fingerprint_sha256"]) == 64

    def test_main_writes_only_aggregates(self, monkeypatch, tmp_path, capsys):
        data = {1: DENSE, 2: make_rows([7] * 24, seed=11)}
        monkeypatch.setattr(sd, "load_companies", lambda path, only=None: [(1, "Firma A"), (2, "Firma B")])
        monkeypatch.setattr(sd, "fetch_rows", lambda cid: data[cid])
        out, recs = tmp_path / "r.json", tmp_path / "r_records.json.gz"
        assert sd.main(["--reps", "2", "--json", str(out), "--records", str(recs), "--allow-dirty"]) == 0
        report = json.loads(out.read_text(encoding="utf-8"))
        for key in ("generated_at", "duration_s", "argv", "git", "versions", "params", "series", "skipped", "results"):
            assert key in report
        assert {"commit", "dirty", "script_sha256"} <= set(report["git"])
        assert report["params"]["detection"]["severity_high"] == 0.5 and report["params"]["detection"]["jump"] == 1
        text = out.read_text(encoding="utf-8")
        assert "T10:00:00" not in text and '"id"' not in text
        with gzip.open(recs, "rt", encoding="utf-8") as fh:
            stored = json.load(fh)
        assert len(stored["records"]) == 2 * 2 * N_DESIGN * len(sd.DELTAS)
        assert all("datum" not in r and "id" not in r for r in stored["records"])
        assert "Firma A" in capsys.readouterr().out

    @pytest.mark.parametrize("argv", [["--reps", "0"], ["--margin", "2"], ["--deltas", "nan"],
                                      ["--deltas", "-0.5"], ["--seed", "-1"]])
    def test_invalid_arguments_are_rejected(self, argv):
        with pytest.raises(SystemExit):
            sd.main(argv)

    def test_dirty_tree_blocks_result_files(self, monkeypatch, tmp_path):
        monkeypatch.setattr(sd, "git_state", lambda: {"commit": "x", "dirty": True, "dirty_paths": ["a.py"],
                                                      "script_sha256": "y"})
        with pytest.raises(SystemExit):
            sd.main(["--reps", "1", "--json", str(tmp_path / "x.json")])

    def test_format_report_handles_all_parts(self):
        records = sd.simulate({1: DENSE}, reps=2, deltas=(0.0, 1.0))
        report = {
            "params": {"reps": 2, "seed": sd.SEED, "deltas": [0.0, 1.0]},
            "series": [{"company_id": 1, "company": "Konstruiert", **sd.describe_series(DENSE, 1)}],
            "results": sd.aggregate(records, (0.0, 1.0), {1: 48}),
        }
        text = sd.format_report(report)
        assert "Konstruiert" in text and "jüngster Wechsel" in text and "Monate getauscht" in text
        assert not math.isnan(len(text))
