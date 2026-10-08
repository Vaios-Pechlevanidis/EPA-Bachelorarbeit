"""
Tests für scripts/compare_annotations.py (DZ1, E5, Iteration 2): Übereinstimmung zweier
Annotationsdateien mit der Zuordnungsregel aus E5 (Toleranz ±1 Monat, Lücken bis 3 Monate,
gleiche Richtung, Eins-zu-eins). Konstruierte Dateien und Reihen, ohne DB und ohne Netz.

Ausführen:
    cd backend
    uv run python -m pytest tests/test_compare_annotations.py -q -p no:cacheprovider
"""

import json
import os
import sys

BACKEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, BACKEND_DIR)
sys.path.insert(0, os.path.join(BACKEND_DIR, "scripts"))

import compare_annotations as ca  # noqa: E402


def months(first_year, first_month, n):
    y, m = first_year, first_month
    for _ in range(n):
        yield f"{y:04d}-{m:02d}"
        m += 1
        if m == 13:
            y, m = y + 1, 1


ALL_2020 = set(months(2020, 1, 24))


def ann(period_from, period_to, direction, company="Beispielwerk", source="employee", dimension="durchschnittsbewertung"):
    return {"company": company, "source": source, "dimension": dimension, "period_from": period_from,
            "period_to": period_to, "direction": direction, "note": "konstruiert"}


def doc(*entries, version=1):
    return {"version": version, "hinweise": {}, "annotations": list(entries)}


# ── match_periods (Regel 6 auf zwei Zeiträume) ───────────────────────────────

class TestMatchPeriods:

    def test_identical(self):
        r = ca.match_periods([ann("2020-05", "2020-06", "fall")], [ann("2020-05", "2020-06", "fall")], ALL_2020)
        assert len(r["matches"]) == 1 and r["only_a"] == [] and r["only_b"] == []
        assert r["matches"][0]["window_a"] == ["2020-04", "2020-07"]

    def test_within_tolerance(self):
        # B beginnt einen Monat nach dem Ende von A: berührt das Fenster ±1
        r = ca.match_periods([ann("2020-05", "2020-06", "fall")], [ann("2020-07", "2020-08", "fall")], ALL_2020)
        assert len(r["matches"]) == 1
        # zwei Monate Abstand: außerhalb
        r = ca.match_periods([ann("2020-05", "2020-06", "fall")], [ann("2020-08", "2020-09", "fall")], ALL_2020)
        assert r["matches"] == [] and len(r["only_a"]) == 1 and len(r["only_b"]) == 1

    def test_direction_must_match(self):
        r = ca.match_periods([ann("2020-05", "2020-06", "fall")], [ann("2020-05", "2020-06", "rise")], ALL_2020)
        assert r["matches"] == [] and len(r["only_a"]) == 1 and len(r["only_b"]) == 1

    def test_one_to_one_earliest_b(self):
        a = [ann("2020-05", "2020-05", "fall")]
        b = [ann("2020-06", "2020-06", "fall"), ann("2020-04", "2020-04", "fall")]
        r = ca.match_periods(a, b, ALL_2020)
        assert len(r["matches"]) == 1 and r["matches"][0]["b"]["period_from"] == "2020-04", "frühester passender aus B"
        assert [o["period_from"] for o in r["only_b"]] == ["2020-06"]
        # zwei A, ein B: nur eines trifft
        r = ca.match_periods([ann("2020-04", "2020-04", "fall"), ann("2020-06", "2020-06", "fall")], [ann("2020-05", "2020-05", "fall")], ALL_2020)
        assert len(r["matches"]) == 1 and r["matches"][0]["a"]["period_from"] == "2020-04" and len(r["only_a"]) == 1

    def test_gap_shifts_window(self):
        evaluated = ALL_2020 - {"2020-07", "2020-08"}
        # Nachbarmonat 2020-07 nicht bewertet: Fenster rückt bis 2020-09 (2 Monate nach period_to, innerhalb von 3)
        r = ca.match_periods([ann("2020-05", "2020-06", "rise")], [ann("2020-09", "2020-09", "rise")], evaluated)
        assert len(r["matches"]) == 1 and r["matches"][0]["window_a"] == ["2020-04", "2020-09"]
        assert ca.match_periods([ann("2020-05", "2020-06", "rise")], [ann("2020-09", "2020-09", "rise")], ALL_2020)["matches"] == []

    def test_without_evaluated_months_plain_tolerance(self):
        r = ca.match_periods([ann("2020-05", "2020-06", "rise")], [ann("2020-07", "2020-07", "rise")], set())
        assert len(r["matches"]) == 1 and r["matches"][0]["window_a"] == ["2020-04", "2020-07"]

    def test_empty(self):
        r = ca.match_periods([], [], ALL_2020)
        assert r == {"n_a": 0, "n_b": 0, "matches": [], "only_a": [], "only_b": []}


# ── compare (alle Reihen) ────────────────────────────────────────────────────

SERIES = {
    ("beispielwerk", "employee", "durchschnittsbewertung"): {"name": "Beispielwerk", "company_id": 1, "evaluated": ALL_2020},
    ("musterbau", "employee", "durchschnittsbewertung"): {"name": "Musterbau", "company_id": 2, "evaluated": ALL_2020},
    ("leerwerk", "employee", "durchschnittsbewertung"): {"name": "Leerwerk", "company_id": 3, "evaluated": ALL_2020},
    ("stillwerk", "employee", "durchschnittsbewertung"): {"name": "Stillwerk", "company_id": 4, "evaluated": ALL_2020},
}


class TestCompare:

    def test_totals_and_share_both_none(self):
        a = doc(ann("2020-05", "2020-06", "fall"), ann("2021-02", "2021-02", "rise"), ann("2020-03", "2020-03", "fall", company="Musterbau"))
        b = doc(ann("2020-06", "2020-07", "fall"), ann("2020-10", "2020-10", "rise", company="Musterbau"))
        r = ca.compare(a, b, SERIES)
        t = r["totals"]
        assert (t["n_series"], t["n_a"], t["n_b"], t["matched"], t["only_a"], t["only_b"]) == (4, 3, 2, 1, 2, 1)
        assert t["series_both_none"] == 2 and t["share_both_none"] == 0.5, "Leerwerk und Stillwerk ohne Zeitraum in beiden Dateien"
        assert t["share_matched_of_a"] == round(1 / 3, 4) and t["share_matched_of_b"] == 0.5
        rows = {s["company"]: s for s in r["series"]}
        assert rows["Beispielwerk"]["both_none"] is False and rows["Leerwerk"]["both_none"] is True
        assert len(rows["Musterbau"]["only_a"]) == 1 and len(rows["Musterbau"]["only_b"]) == 1
        assert r["rules"]["tolerance_months"] == 1 and r["rules"]["one_to_one"] is True

    def test_series_only_in_annotations_are_included(self):
        # Reihe ohne CSV: wird aufgenommen, reine Toleranz
        a = doc(ann("2020-05", "2020-05", "fall", company="Fremdwerk"))
        r = ca.compare(a, doc(), SERIES)
        rows = {s["company"]: s for s in r["series"]}
        assert "Fremdwerk" in rows and rows["Fremdwerk"]["evaluated_known"] is False and r["totals"]["n_series"] == 5

    def test_company_names_are_normalized(self):
        a = doc(ann("2020-05", "2020-05", "fall", company="  beispielwerk "))
        b = doc(ann("2020-05", "2020-05", "fall", company="BEISPIELWERK"))
        r = ca.compare(a, b, SERIES)
        assert r["totals"]["matched"] == 1 and r["totals"]["n_series"] == 4

    def test_source_filter(self):
        a = doc(ann("2020-05", "2020-05", "fall", source="candidates"))
        r = ca.compare(a, doc(), SERIES, source="employee")
        assert r["totals"]["n_a"] == 0 and r["totals"]["n_series"] == 4

    def test_both_empty(self):
        r = ca.compare(doc(), doc(), SERIES)
        assert r["totals"]["matched"] == 0 and r["totals"]["share_both_none"] == 1.0 and r["totals"]["share_matched_of_a"] is None

    def test_report_text(self):
        a = doc(ann("2020-05", "2020-06", "fall"))
        b = doc(ann("2020-06", "2020-07", "fall"), ann("2020-11", "2020-11", "rise"))
        text = ca.format_report(ca.compare(a, b, SERIES), "a.json", "b.json")
        assert "übereinstimmend 1, nur bei A 0, nur bei B 1" in text
        assert "beide ohne Zeitraum: 3 (75 %)" in text
        assert "Übereinstimmung: A 2020-05..2020-06 fall (Fenster 2020-04..2020-07) <-> B 2020-06..2020-07" in text
        assert "Nur bei B:       2020-11..2020-11 rise" in text
        assert "konstruiert" not in text, "keine note-Texte im Bericht"


# ── Reihen aus CSVs und CLI ──────────────────────────────────────────────────

def _write_csv(path, periods, count=8):
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("period;mean_durchschnittsbewertung;count;delta_vs_previous\n")
        for p in periods:
            fh.write(f"{p};3.5;{count};\n")


class TestSeriesAndCli:

    def test_series_from_csvs_only_eligible(self, tmp_path):
        series_dir = tmp_path / "series"
        series_dir.mkdir()
        _write_csv(series_dir / "1_beispielwerk_employee.csv", list(months(2020, 1, 24)))
        _write_csv(series_dir / "2_duennwerk_employee.csv", list(months(2020, 1, 6)))          # unter 12 bewerteten Monaten
        _write_csv(series_dir / "1_beispielwerk_candidates.csv", list(months(2020, 1, 24)))
        density = tmp_path / "density.json"
        density.write_text(json.dumps({"companies": [{"id": 1, "name": "Beispielwerk GmbH"}, {"id": 2, "name": "Dünnwerk"}]}), encoding="utf-8")
        series = ca.series_from_csvs(str(series_dir), "employee", str(density))
        assert list(series) == [("beispielwerk gmbh", "employee", "durchschnittsbewertung")]
        info = series[("beispielwerk gmbh", "employee", "durchschnittsbewertung")]
        assert info["name"] == "Beispielwerk GmbH" and info["company_id"] == 1 and len(info["evaluated"]) == 24

    def test_cli_json(self, tmp_path, capsys):
        series_dir = tmp_path / "series"
        series_dir.mkdir()
        _write_csv(series_dir / "1_beispielwerk_employee.csv", list(months(2020, 1, 24)))
        _write_csv(series_dir / "2_leerwerk_employee.csv", list(months(2020, 1, 24)))
        density = tmp_path / "density.json"
        density.write_text(json.dumps({"companies": [{"id": 1, "name": "Beispielwerk"}, {"id": 2, "name": "Leerwerk"}]}), encoding="utf-8")
        a, b = tmp_path / "a.json", tmp_path / "b.json"
        a.write_text(json.dumps(doc(ann("2020-05", "2020-06", "fall"))), encoding="utf-8")
        b.write_text(json.dumps(doc(ann("2020-07", "2020-07", "fall"))), encoding="utf-8")
        out = tmp_path / "out" / "result.json"
        code = ca.main(["--a", str(a), "--b", str(b), "--series-dir", str(series_dir), "--density", str(density), "--json", str(out)])
        assert code == 0
        data = json.loads(out.read_text(encoding="utf-8"))
        assert data["totals"]["matched"] == 1 and data["totals"]["n_series"] == 2 and data["totals"]["series_both_none"] == 1
        assert "übereinstimmend 1" in capsys.readouterr().out

    def test_cli_both_empty_hint(self, tmp_path, capsys):
        a, b = tmp_path / "a.json", tmp_path / "b.json"
        a.write_text(json.dumps(doc()), encoding="utf-8")
        b.write_text(json.dumps(doc()), encoding="utf-8")
        assert ca.main(["--a", str(a), "--b", str(b), "--series-dir", str(tmp_path / "fehlt"), "--density", str(tmp_path / "fehlt.json")]) == 0
        out = capsys.readouterr().out
        assert "beide Dateien enthalten keine Einträge" in out

    def test_cli_wrong_schema(self, tmp_path, capsys):
        a, b = tmp_path / "a.json", tmp_path / "b.json"
        a.write_text(json.dumps([1, 2]), encoding="utf-8")
        b.write_text(json.dumps(doc()), encoding="utf-8")
        assert ca.main(["--a", str(a), "--b", str(b), "--series-dir", str(tmp_path / "fehlt"), "--density", str(tmp_path / "fehlt.json")]) == 1
        assert "Schema" in capsys.readouterr().out
