"""
Tests für scripts/evaluate_detection.py (Abgleich Erkennung ↔ Referenzzeiträume,
E5 Regel 6): konstruierte Annotationen, Reihen und Erkennungen, ohne DB und ohne
Netz. Ein Test lässt den echten Detektor auf einer konstruierten Reihe laufen.

Ausführen:
    cd backend
    uv run python -m pytest tests/test_evaluate_detection.py -q -p no:cacheprovider
"""

import json
import os
import sys

import pytest

BACKEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, BACKEND_DIR)
sys.path.insert(0, os.path.join(BACKEND_DIR, "scripts"))

import evaluate_detection as ed  # noqa: E402
import validate_annotations as va  # noqa: E402


# ── Hilfen ───────────────────────────────────────────────────────────────────

def months(first_year: int, first_month: int, n: int):
    y, m = first_year, first_month
    for _ in range(n):
        yield f"{y:04d}-{m:02d}"
        m += 1
        if m == 13:
            y, m = y + 1, 1


def det(date, direction, kind=ed.KIND_LEVEL, **extra):
    return {"kind": kind, "date": date, "direction": direction, **extra}


def ann(period_from, period_to, direction, company="E.ON", source="employee", dimension="durchschnittsbewertung"):
    return {"company": company, "source": source, "dimension": dimension, "period_from": period_from,
            "period_to": period_to, "direction": direction, "note": "konstruiert"}


ALL_2020 = set(months(2020, 1, 24))


# ── Fenster (Regel 6) ────────────────────────────────────────────────────────

class TestWindow:

    def test_plain_tolerance(self):
        assert ed.match_window("2020-05", "2020-06", ALL_2020) == ("2020-04", "2020-07")

    def test_year_boundary(self):
        assert ed.match_window("2021-01", "2021-01", ALL_2020) == ("2020-12", "2021-02")

    def test_gap_shifts_boundary_to_next_evaluated_month(self):
        evaluated = ALL_2020 - {"2020-04", "2020-07", "2020-08"}
        # davor: 2020-04 nicht bewertet -> 2020-03 (2 Monate vor period_from, innerhalb von 3)
        # danach: 2020-07 und 2020-08 nicht bewertet -> 2020-09 (3 Monate nach period_to)
        assert ed.match_window("2020-05", "2020-06", evaluated) == ("2020-03", "2020-09")

    def test_gap_capped_at_three_months(self):
        evaluated = ALL_2020 - {"2020-02", "2020-03", "2020-04", "2020-08", "2020-09", "2020-10"}
        # keine bewerteten Monate innerhalb der Kappung -> Grenze bleibt beim Toleranzmonat
        assert ed.match_window("2020-05", "2020-07", evaluated) == ("2020-04", "2020-08")

    def test_rules_are_fixed_constants(self):
        assert ed.TOLERANCE_MONTHS == 1 and ed.MAX_SHIFT_MONTHS == 3


# ── Abgleich einer Reihe ─────────────────────────────────────────────────────

class TestMatchSeries:

    def test_hit_within_tolerance(self):
        r = ed.match_series([ann("2020-05", "2020-06", "fall")], [det("2020-07", "fall")], ALL_2020)
        assert (r["tp"], r["fp"], r["fn"]) == (1, 0, 0) and r["f1"] == 1.0
        assert r["hits"][0]["window"] == ["2020-04", "2020-07"] and r["hits"][0]["detection"]["date"] == "2020-07"

    def test_direction_must_match(self):
        r = ed.match_series([ann("2020-05", "2020-06", "fall")], [det("2020-05", "rise")], ALL_2020)
        assert (r["tp"], r["fp"], r["fn"]) == (0, 1, 1) and r["f1"] == 0.0
        assert r["misses"][0]["annotation"]["period_from"] == "2020-05" and r["extras"][0]["date"] == "2020-05"

    def test_outside_window_is_miss_and_extra(self):
        r = ed.match_series([ann("2020-05", "2020-05", "rise")], [det("2020-08", "rise")], ALL_2020)
        assert (r["tp"], r["fp"], r["fn"]) == (0, 1, 1)

    def test_one_annotation_counts_once_earliest_detection(self):
        r = ed.match_series([ann("2020-05", "2020-06", "fall")],
                            [det("2020-06", "fall", delta=-0.9), det("2020-04", "fall", delta=-0.4)], ALL_2020)
        assert (r["tp"], r["fp"], r["fn"]) == (1, 1, 0)
        assert r["hits"][0]["detection"]["date"] == "2020-04" and r["extras"][0]["date"] == "2020-06"

    def test_one_detection_serves_one_annotation(self):
        r = ed.match_series([ann("2020-05", "2020-05", "fall"), ann("2020-09", "2020-09", "fall")],
                            [det("2020-06", "fall")], ALL_2020)
        assert (r["tp"], r["fp"], r["fn"]) == (1, 0, 1)
        assert r["misses"][0]["annotation"]["period_from"] == "2020-09"

    def test_annotations_processed_in_time_order(self):
        # zweite Annotation (später) steht zuerst in der Liste; das Fenster der ersten greift zuerst
        r = ed.match_series([ann("2020-09", "2020-09", "rise"), ann("2020-05", "2020-06", "rise")],
                            [det("2020-07", "rise"), det("2020-10", "rise")], ALL_2020)
        assert (r["tp"], r["fp"], r["fn"]) == (2, 0, 0)
        assert [h["annotation"]["period_from"] for h in r["hits"]] == ["2020-05", "2020-09"]

    def test_no_detections_no_annotations_metrics_undefined(self):
        r = ed.match_series([], [], ALL_2020)
        assert (r["tp"], r["fp"], r["fn"]) == (0, 0, 0)
        assert r["precision"] is None and r["recall"] is None and r["f1"] is None

    def test_metrics_values(self):
        m = ed.metrics(2, 1, 2)
        assert m["precision"] == pytest.approx(2 / 3) and m["recall"] == pytest.approx(0.5)
        assert m["f1"] == pytest.approx(2 * (2 / 3) * 0.5 / ((2 / 3) + 0.5))
        assert ed.metrics(0, 3, 0)["f1"] == 0.0 and ed.metrics(0, 3, 0)["recall"] is None


# ── Varianten und Gesamtauswertung ───────────────────────────────────────────

def make_result(evaluated, anomalies=(), outliers=(), eligible=True):
    return {
        "series": [{"period": p, "mean": 3.5, "count": 8, "n_values": 8, "evaluated": p in evaluated} for p in sorted(ALL_2020)],
        "anomalies": list(anomalies),
        "outlier_months": list(outliers),
        "eligibility": {"eligible": eligible, "evaluated_months": len(evaluated), "reason": None if eligible else "zu wenige Monate"},
        "params": {"method": "pelt", "penalty_mode": "scaled", "penalty_factor": 2.0, "min_delta": 0.3},
    }


DENSITY = {"companies": [
    {"id": 7, "name": "E.ON", "name_raw": "E.ON", "sources": {"employee": {"first_month": "2020-01", "last_month": "2021-12"},
                                                                  "candidates": {"first_month": "2020-01", "last_month": "2021-12"}}},
    {"id": 28, "name": "Telekom", "name_raw": "Telekom", "sources": {"employee": {"first_month": "2020-01", "last_month": "2021-12"}}},
]}


def doc(*entries):
    return {"version": 1, "hinweise": {}, "annotations": list(entries)}


class TestEvaluate:

    def test_variants_differ_by_outliers(self):
        fetch_calls = []

        def fetch(company_id, source, dimension):
            fetch_calls.append((company_id, source, dimension))
            return make_result(ALL_2020,
                               anomalies=[{"date": "2020-11", "direction": "rise", "delta": 0.7}],
                               outliers=[{"date": "2020-05", "direction": "fall", "deviation": -1.2}])

        companies = va.companies_from_density(DENSITY)
        report = ed.evaluate(doc(ann("2020-05", "2020-05", "fall"), ann("2020-10", "2020-11", "rise")), companies, fetch)
        assert fetch_calls == [(7, "employee", "durchschnittsbewertung")], "eine Erkennung je Reihe, Standardparameter"
        s = report["series"][0]["variants"]
        level, both = s["niveauwechsel"], s["niveauwechsel+einzelmonate"]
        assert (level["tp"], level["fp"], level["fn"]) == (1, 0, 1)
        assert (both["tp"], both["fp"], both["fn"]) == (2, 0, 0)
        assert both["hits"][0]["detection"]["kind"] == "einzelmonat"
        assert report["totals"]["niveauwechsel"]["gesamt"]["f1"] == pytest.approx(2 / 3)
        assert report["totals"]["niveauwechsel+einzelmonate"]["gesamt"]["f1"] == 1.0
        assert report["totals"]["niveauwechsel"]["je_quelle"]["employee"]["n_annotations"] == 2

    def test_totals_are_micro_sums_over_series_and_sources(self):
        def fetch(company_id, source, dimension):
            if company_id == 7 and source == "candidates":
                return make_result(ALL_2020, anomalies=[{"date": "2021-03", "direction": "fall", "delta": -0.5}])
            return make_result(ALL_2020, anomalies=[{"date": "2020-02", "direction": "rise", "delta": 0.5},
                                                     {"date": "2020-09", "direction": "rise", "delta": 0.4}])

        companies = va.companies_from_density(DENSITY)
        d = doc(ann("2020-02", "2020-03", "rise"), ann("2020-06", "2020-06", "fall"),
                ann("2020-02", "2020-02", "rise", company="Telekom"), ann("2021-03", "2021-03", "fall", source="candidates"))
        report = ed.evaluate(d, companies, fetch)
        assert [s["series"] for s in report["series"]] == [
            "E.ON / candidates / durchschnittsbewertung", "E.ON / employee / durchschnittsbewertung",
            "Telekom / employee / durchschnittsbewertung",
        ]
        tot = report["totals"]["niveauwechsel"]
        # E.ON employee: TP 1, FP 1, FN 1; Telekom: TP 1, FP 1; E.ON candidates: TP 1
        assert (tot["gesamt"]["tp"], tot["gesamt"]["fp"], tot["gesamt"]["fn"]) == (3, 2, 1)
        assert (tot["je_quelle"]["employee"]["tp"], tot["je_quelle"]["employee"]["fp"]) == (2, 2)
        assert tot["je_quelle"]["candidates"]["f1"] == 1.0
        assert tot["gesamt"]["n_series"] == 3 and tot["gesamt"]["n_annotations"] == 4

    def test_source_filter(self):
        fetch = lambda cid, src, dim: make_result(ALL_2020)  # noqa: E731
        companies = va.companies_from_density(DENSITY)
        report = ed.evaluate(doc(ann("2020-05", "2020-05", "fall"), ann("2020-05", "2020-05", "fall", source="candidates")),
                             companies, fetch, sources=["candidates"])
        assert [s["source"] for s in report["series"]] == ["candidates"]

    def test_ineligible_series_skipped_not_counted(self):
        fetch = lambda cid, src, dim: make_result(set(list(sorted(ALL_2020))[:5]), eligible=False)  # noqa: E731
        companies = va.companies_from_density(DENSITY)
        report = ed.evaluate(doc(ann("2020-02", "2020-02", "fall")), companies, fetch)
        assert report["series"] == [] and len(report["skipped"]) == 1
        assert "nicht geeignet" in report["skipped"][0]["reason"] and "Regel 9" in report["skipped"][0]["reason"]
        assert report["totals"]["niveauwechsel"]["gesamt"]["tp"] == 0

    def test_unresolvable_company_skipped(self):
        companies = va.companies_from_density(DENSITY)
        report = ed.evaluate(doc(ann("2020-02", "2020-02", "fall", company="Unbekannt AG")), companies,
                             lambda *a: pytest.fail("darf nicht abgerufen werden"))
        assert report["series"] == [] and "nicht auflösbar" in report["skipped"][0]["reason"]

    def test_window_uses_evaluated_months_of_series(self):
        evaluated = ALL_2020 - {"2020-04"}
        fetch = lambda cid, src, dim: make_result(evaluated, anomalies=[{"date": "2020-03", "direction": "fall", "delta": -0.6}])  # noqa: E731
        companies = va.companies_from_density(DENSITY)
        report = ed.evaluate(doc(ann("2020-05", "2020-05", "fall")), companies, fetch)
        v = report["series"][0]["variants"]["niveauwechsel"]
        assert v["tp"] == 1 and v["hits"][0]["window"] == ["2020-03", "2020-06"]

    def test_report_text_lists_hits_misses_extras(self):
        fetch = lambda cid, src, dim: make_result(ALL_2020, anomalies=[  # noqa: E731
            {"date": "2020-05", "direction": "fall", "delta": -0.8}, {"date": "2021-01", "direction": "rise", "delta": 0.5}])
        companies = va.companies_from_density(DENSITY)
        report = ed.evaluate(doc(ann("2020-05", "2020-05", "fall"), ann("2020-09", "2020-09", "fall")), companies, fetch)
        text = ed.format_report(report, "annotations.json")
        assert "Variante Niveauwechsel allein" in text and "Variante Niveauwechsel und Einzelmonate" in text
        assert "Treffer:    2020-05..2020-05 fall" in text
        assert "Verfehlt:   2020-09..2020-09 fall" in text
        assert "Zusätzlich: 2021-01 rise (Niveauwechsel, +0,50)" in text
        assert "Gesamt employee" in text and "Gesamt " in text
        json.dumps(report)  # serialisierbar für --json


# ── Echte Erkennung auf konstruierter Reihe ──────────────────────────────────

class TestWithRealDetector:

    def test_constructed_step_is_hit_with_default_parameters(self):
        from services.anomaly_service import detect_anomalies, detect_outlier_months, eligibility

        periods = list(months(2019, 1, 36))
        values = [4.2 + (0.05 if i % 2 else -0.05) for i in range(18)] + [2.9 + (0.05 if i % 2 else -0.05) for i in range(18)]
        series = [{"period": p, "mean": v, "count": 9, "n_values": 9, "evaluated": True} for p, v in zip(periods, values)]
        result = {
            "series": series,
            "anomalies": detect_anomalies(series, company_id=7, source="employee"),
            "outlier_months": detect_outlier_months(series, company_id=7, source="employee"),
            "eligibility": eligibility(series),
            "params": {},
        }
        assert len(result["anomalies"]) == 1 and result["anomalies"][0]["date"] == "2020-07"
        companies = va.companies_from_density({"companies": [
            {"id": 7, "name": "E.ON", "sources": {"employee": {"first_month": "2019-01", "last_month": "2021-12"}}}]})
        report = ed.evaluate(doc(ann("2020-07", "2020-08", "fall")), companies, lambda *a: result)
        for variant in ed.VARIANTS:
            v = report["series"][0]["variants"][variant]
            assert (v["tp"], v["fp"], v["fn"]) == (1, 0, 0), variant


# ── CLI ──────────────────────────────────────────────────────────────────────

class TestCli:

    def test_empty_annotations_abort_with_hint(self, tmp_path, capsys):
        path = tmp_path / "annotations.json"
        path.write_text(json.dumps({"version": 1, "hinweise": {}, "annotations": []}), encoding="utf-8")
        assert ed.main(["--file", str(path), "--offline", "--density", str(tmp_path / "fehlt.json")]) == 1
        out = capsys.readouterr().out
        assert "Keine Annotationen" in out and "make_annotation_sheet.py" in out and "eigenen Commit" in out

    def test_invalid_entries_abort_before_detection(self, tmp_path, capsys, monkeypatch):
        path = tmp_path / "annotations.json"
        path.write_text(json.dumps(doc(ann("2020-05", "2020-05", "fall", company="Demo 1"))), encoding="utf-8")
        density = tmp_path / "density.json"
        density.write_text(json.dumps(DENSITY), encoding="utf-8")
        monkeypatch.setattr(ed, "_db_fetch", lambda *a: pytest.fail("Erkennung darf bei Fehlern nicht laufen"))
        assert ed.main(["--file", str(path), "--offline", "--density", str(density)]) == 1
        assert "Abbruch" in capsys.readouterr().out

    def test_cli_runs_offline_with_fake_detection_and_writes_json(self, tmp_path, capsys, monkeypatch):
        path = tmp_path / "annotations.json"
        path.write_text(json.dumps(doc(ann("2020-05", "2020-06", "fall"))), encoding="utf-8")
        density = tmp_path / "density.json"
        density.write_text(json.dumps(DENSITY), encoding="utf-8")
        monkeypatch.setattr(ed, "_db_fetch", lambda cid, src, dim: make_result(
            ALL_2020, anomalies=[{"date": "2020-06", "direction": "fall", "delta": -0.7}]))
        out = tmp_path / "ergebnis.json"
        assert ed.main(["--file", str(path), "--offline", "--density", str(density), "--json", str(out)]) == 0
        text = capsys.readouterr().out
        assert "Treffer:    2020-05..2020-06 fall" in text
        saved = json.loads(out.read_text(encoding="utf-8"))
        assert saved["totals"]["niveauwechsel"]["gesamt"]["f1"] == 1.0 and saved["rules"]["tolerance_months"] == 1


# ── Teilauswertungen (--subset, vor dem ersten Lauf festgelegt) ──────────────

def ann_note(period_from, period_to, direction, note, company="E.ON"):
    a = ann(period_from, period_to, direction, company=company)
    a["note"] = note
    return a


class TestSubsets:

    def test_definitions_fixed(self):
        assert ed.SUBSETS == ("alle", "ohne_duenne", "mehrmonatig", "mit_anker")
        assert ed.THIN_MONTH_REVIEWS == 10 and ed.ANCHOR_SUFFIX == "Reihe + Ereignis"

    def test_member_mehrmonatig(self):
        assert ed.subset_member("mehrmonatig", ann("2020-05", "2020-05", "fall")) is False
        assert ed.subset_member("mehrmonatig", ann("2020-12", "2021-01", "fall")) is True

    def test_member_mit_anker(self):
        assert ed.subset_member("mit_anker", ann_note("2020-05", "2020-05", "fall", "x; Anker: y; Reihe + Ereignis.")) is True
        assert ed.subset_member("mit_anker", ann_note("2020-05", "2020-05", "fall", "x; Reihe + Ereignis")) is True
        assert ed.subset_member("mit_anker", ann_note("2020-05", "2020-05", "fall", "Reihe + Ereignis; Reihe allein.")) is False

    def test_member_ohne_duenne(self):
        counts = {"2020-05": 10, "2020-06": 9, "2020-07": 12}
        assert ed.subset_member("ohne_duenne", ann("2020-05", "2020-05", "fall"), counts) is True
        assert ed.subset_member("ohne_duenne", ann("2020-05", "2020-06", "fall"), counts) is False
        assert ed.subset_member("ohne_duenne", ann("2020-07", "2020-08", "fall"), counts) is False, "Monat ohne Zeile = 0"
        assert ed.subset_member("ohne_duenne", ann("2020-05", "2020-05", "fall"), None) is None
        assert ed.subset_member("alle", ann("2020-05", "2020-05", "fall")) is True

    def _setup(self, tmp_path=None):
        companies = va.companies_from_density(DENSITY)
        counts = {p: 20 for p in ALL_2020}
        counts["2020-06"] = 7
        companies["e.on"].counts["employee"] = counts
        d = doc(ann_note("2020-05", "2020-06", "fall", "dünn; Anker: keiner; Reihe allein."),
                ann_note("2020-10", "2020-10", "rise", "Anker: Kurzbeschreibung; Reihe + Ereignis."),
                ann_note("2021-03", "2021-04", "fall", "Anker: Kurzbeschreibung; Reihe + Ereignis."))

        def fetch(cid, src, dim):
            return make_result(ALL_2020,
                               anomalies=[{"date": "2020-06", "direction": "fall", "delta": -0.7},
                                          {"date": "2021-08", "direction": "rise", "delta": 0.5}],
                               outliers=[{"date": "2020-10", "direction": "rise", "deviation": 1.1}])
        return d, companies, fetch

    def test_subsets_restrict_counts_neutral_matches(self):
        d, companies, fetch = self._setup()
        report = ed.evaluate(d, companies, fetch)
        subs = ed.evaluate_subsets(d, companies, report)
        assert list(subs) == list(ed.SUBSETS)
        # alle entspricht der Gesamtauswertung
        for variant in ed.VARIANTS:
            a, g = subs["alle"]["totals"][variant]["gesamt"], report["totals"][variant]["gesamt"]
            assert (a["tp"], a["fp"], a["fn"], a["f1"]) == (g["tp"], g["fp"], g["fn"], g["f1"])
        assert subs["ohne_duenne"]["n_annotations"] == 2 and subs["mehrmonatig"]["n_annotations"] == 2
        assert subs["mit_anker"]["n_annotations"] == 2
        # ohne_duenne: 2020-05..06 fällt heraus; die Erkennung 2020-06 ist neutral, nicht FP
        lvl = subs["ohne_duenne"]["series"][0]["variants"]["niveauwechsel"]
        assert (lvl["tp"], lvl["fp"], lvl["fn"], lvl["neutral"]) == (0, 1, 2, 1)
        both = subs["ohne_duenne"]["series"][0]["variants"]["niveauwechsel+einzelmonate"]
        assert (both["tp"], both["fp"], both["fn"], both["neutral"]) == (1, 1, 1, 1)
        # mehrmonatig: 2020-05..06 (Treffer) und 2021-03..04 (verfehlt); 2020-10 ist außerhalb
        m = subs["mehrmonatig"]["totals"]["niveauwechsel+einzelmonate"]["gesamt"]
        assert (m["tp"], m["fp"], m["fn"]) == (1, 1, 1)
        both_m = subs["mehrmonatig"]["series"][0]["variants"]["niveauwechsel+einzelmonate"]
        assert both_m["neutral"] == 1
        # mit_anker: Niveauwechsel allein trifft keinen der beiden Einträge
        k = subs["mit_anker"]["totals"]["niveauwechsel"]["gesamt"]
        assert (k["tp"], k["fp"], k["fn"], k["f1"]) == (0, 1, 2, 0.0)

    def test_series_without_subset_entries_left_out(self):
        companies = va.companies_from_density(DENSITY)
        d = doc(ann("2020-05", "2020-05", "fall"), ann("2020-05", "2020-06", "fall", company="Telekom"))
        fetch = lambda cid, src, dim: make_result(ALL_2020, anomalies=[{"date": "2020-09", "direction": "rise", "delta": 0.5}])  # noqa: E731
        report = ed.evaluate(d, companies, fetch)
        sub = ed.evaluate_subsets(d, companies, report, ("mehrmonatig",))["mehrmonatig"]
        assert [s["series"] for s in sub["series"]] == ["Telekom / employee / durchschnittsbewertung"]
        assert sub["totals"]["niveauwechsel"]["gesamt"]["fp"] == 1, "nur die FP der Telekom-Reihe"

    def test_without_counts_undetermined(self):
        companies = va.companies_from_density(DENSITY)
        d = doc(ann("2020-05", "2020-05", "fall"))
        report = ed.evaluate(d, companies, lambda *a: make_result(ALL_2020))
        sub = ed.evaluate_subsets(d, companies, report, ("ohne_duenne",))["ohne_duenne"]
        assert sub["n_undetermined"] == 1 and sub["n_annotations"] == 0 and sub["series"] == []

    def test_report_text_lists_subsets_for_both_variants(self):
        d, companies, fetch = self._setup()
        report = ed.evaluate(d, companies, fetch)
        report["subsets"] = ed.evaluate_subsets(d, companies, report)
        text = ed.format_report(report, "annotations.json")
        assert "Teilauswertungen (vor dem ersten Lauf festgelegt, E5)" in text
        for name in ed.SUBSETS:
            assert f"Teilmenge {name}: " in text
        assert text.count("    Variante Niveauwechsel allein") == 4
        assert text.count("    Variante Niveauwechsel und Einzelmonate") == 4
        json.dumps(report)

    def test_cli_subset_option_with_constructed_files(self, tmp_path, capsys, monkeypatch):
        d, _, fetch = self._setup()
        path = tmp_path / "annotations.json"
        path.write_text(json.dumps(d), encoding="utf-8")
        density = tmp_path / "density.json"
        density.write_text(json.dumps(DENSITY), encoding="utf-8")
        series_dir = tmp_path / "series"
        series_dir.mkdir()
        rows = ["period;mean_durchschnittsbewertung;count;delta_vs_previous"]
        rows += [f"{p};3.500;{7 if p == '2020-06' else 20};" for p in sorted(ALL_2020)]
        (series_dir / "7_eon_employee.csv").write_text("\n".join(rows) + "\n", encoding="utf-8")
        monkeypatch.setattr(ed, "_db_fetch", fetch)
        out = tmp_path / "ergebnis.json"
        assert ed.main(["--file", str(path), "--offline", "--density", str(density), "--series-dir", str(series_dir),
                        "--subset", "ohne_duenne", "--subset", "mit_anker", "--json", str(out)]) == 0
        saved = json.loads(out.read_text(encoding="utf-8"))
        assert list(saved["subsets"]) == ["ohne_duenne", "mit_anker"]
        assert saved["subsets"]["ohne_duenne"]["n_annotations"] == 2
        assert "Teilmenge mit_anker" in capsys.readouterr().out
        # ohne --subset: alle vier
        assert ed.main(["--file", str(path), "--offline", "--density", str(density), "--series-dir", str(series_dir),
                        "--json", str(out)]) == 0
        assert list(json.loads(out.read_text(encoding="utf-8"))["subsets"]) == list(ed.SUBSETS)
