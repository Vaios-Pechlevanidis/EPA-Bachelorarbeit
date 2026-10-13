"""
Tests für scripts/compare_annotations.py (DZ1, E5): Übereinstimmung zweier beliebiger
Annotationsdateien mit der Zuordnungsregel aus E5 (Toleranz ±1 Monat, Lücken bis 3 Monate,
gleiche Richtung, Eins-zu-eins). Konstruierte Dateien und Reihen, ohne DB und ohne Netz.

Ergänzt 2026-10-13: Cohens κ auf Monatsebene (bekannte Beispiele: vollständige Übereinstimmung
1, Lehrbuchbeispiel 0,4, unabhängige Zufallsurteile nahe 0), die unveränderte bisherige
Textausgabe (Text des Stands vor der Erweiterung als Vorspann) und ``--series``.

Ausführen:
    cd backend
    uv run python -m pytest tests/test_compare_annotations.py -q -p no:cacheprovider
"""

import json
import os
import random
import sys

import pytest

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

    def test_cli_b_is_required(self, tmp_path, capsys):
        a = tmp_path / "a.json"
        a.write_text(json.dumps(doc()), encoding="utf-8")
        with pytest.raises(SystemExit) as exc:
            ca.main(["--a", str(a), "--series-dir", str(tmp_path / "fehlt"), "--density", str(tmp_path / "fehlt.json")])
        assert exc.value.code == 2 and "--b" in capsys.readouterr().err
        assert not hasattr(ca, "DEFAULT_B")

    def test_cli_wrong_schema(self, tmp_path, capsys):
        a, b = tmp_path / "a.json", tmp_path / "b.json"
        a.write_text(json.dumps([1, 2]), encoding="utf-8")
        b.write_text(json.dumps(doc()), encoding="utf-8")
        assert ca.main(["--a", str(a), "--b", str(b), "--series-dir", str(tmp_path / "fehlt"), "--density", str(tmp_path / "fehlt.json")]) == 1
        assert "Schema" in capsys.readouterr().out


# ── Cohens κ auf Monatsebene ─────────────────────────────────────────────────

class TestKappa:

    def test_perfect_agreement(self):
        pairs = [("rise", "rise")] * 3 + [("fall", "fall")] * 2 + [("keine", "keine")] * 19
        k = ca.cohens_kappa(pairs)
        assert k["kappa"] == 1.0 and k["p_o"] == 1.0 and k["n_months"] == 24
        assert k["matrix"]["rise"]["rise"] == 3 and k["matrix"]["keine"]["keine"] == 19

    def test_textbook_example(self):
        # 50 Urteile: 20 beide ja, 5 nur A, 10 nur B, 15 beide nein -> p_o 0,7, p_e 0,5, κ 0,4
        pairs = [("rise", "rise")] * 20 + [("rise", "keine")] * 5 + [("keine", "rise")] * 10 + [("keine", "keine")] * 15
        k = ca.cohens_kappa(pairs)
        assert (k["p_o"], k["p_e"], k["kappa"]) == (0.7, 0.5, 0.4)

    def test_complete_disagreement_is_negative(self):
        pairs = [("rise", "keine")] * 10 + [("keine", "rise")] * 10
        assert ca.cohens_kappa(pairs)["kappa"] == -1.0

    def test_independent_random_judgements_near_zero(self):
        rng = random.Random(20261013)
        cats, weights = ["rise", "fall", "keine"], [0.1, 0.1, 0.8]
        pairs = [(rng.choices(cats, weights)[0], rng.choices(cats, weights)[0]) for _ in range(20000)]
        k = ca.cohens_kappa(pairs)
        assert abs(k["kappa"]) < 0.03 and k["p_o"] > 0.6, "hohe Rohübereinstimmung, κ trotzdem nahe 0"

    def test_undefined_cases(self):
        k = ca.cohens_kappa([("keine", "keine")] * 12)
        assert k["kappa"] is None and k["p_o"] == 1.0 and k["p_e"] == 1.0 and "nicht definiert" in k["reason"]
        k = ca.cohens_kappa([])
        assert k["kappa"] is None and k["n_months"] == 0 and k["reason"] == "keine bewerteten Monate"

    def test_month_categories(self):
        months_ = sorted(ALL_2020 - {"2020-06"})
        cats = ca.month_categories([ann("2020-05", "2020-07", "fall"), ann("2020-07", "2020-08", "rise"),
                                    ann("2020-xx", "2020-09", "rise"), ann("2020-10", "2020-10", "seitwärts")], months_)
        assert cats["2020-05"] == "fall" and cats["2020-07"] == "fall", "früherer Zeitraum gilt bei Überschneidung"
        assert cats["2020-08"] == "rise" and cats["2020-09"] == "keine" and cats["2020-10"] == "keine"
        assert "2020-06" not in cats, "nicht bewertete Monate zählen nicht"
        assert sum(1 for c in cats.values() if c == "keine") == len(months_) - 3

    def test_compare_kappa_per_series_and_overall(self):
        a = doc(ann("2020-05", "2020-06", "fall"))
        b = doc(ann("2020-06", "2020-07", "fall"), ann("2020-03", "2020-03", "rise", company="Musterbau"))
        r = ca.compare(a, b, SERIES)
        rows = {s["company"]: s for s in r["series"]}
        # Beispielwerk: 24 Monate, A fall {05, 06}, B fall {06, 07}: p_o 22/24, p_e 488/576, κ 40/88
        kb = rows["Beispielwerk"]["kappa"]
        assert kb["n_months"] == 24 and kb["kappa"] == round(40 / 88, 4) and kb["p_o"] == round(22 / 24, 4)
        assert rows["Musterbau"]["kappa"]["kappa"] == 0.0, "nur B sieht einen Monat: keine Übereinstimmung über Zufall"
        assert rows["Leerwerk"]["kappa"]["kappa"] is None
        o = r["kappa"]["overall"]
        assert o["n_months"] == 96 and r["kappa"]["n_series_with_months"] == 4
        assert o["matrix"]["fall"]["fall"] == 1 and o["matrix"]["fall"]["keine"] == 1 and o["matrix"]["keine"]["fall"] == 1
        assert o["matrix"]["keine"]["rise"] == 1 and o["matrix"]["keine"]["keine"] == 92
        assert r["kappa"]["categories"] == ["rise", "fall", "keine"]

    def test_series_without_csv_has_no_months(self):
        r = ca.compare(doc(ann("2020-05", "2020-05", "fall", company="Fremdwerk")), doc(), SERIES)
        rows = {s["company"]: s for s in r["series"]}
        assert rows["Fremdwerk"]["kappa"]["n_months"] == 0 and r["kappa"]["n_series_with_months"] == 4


# ── Bisherige Ausgabe unverändert ────────────────────────────────────────────

# Text von format_report für dieses Beispiel, erzeugt mit compare_annotations.py vor der
# Erweiterung um κ (Stand HEAD 2551300).
OLD_REPORT = (
    "Übereinstimmung zweier Annotationsdateien (DZ1, E5) – A: a.json, B: b.json\n"
    "  Regel 6: Toleranz ±1 Monat, Lücken bis 3 Monate, gleiche Richtung, Eins-zu-eins-Zuordnung.\n"
    "  Zeiträume A: 2, B: 3; übereinstimmend 1, nur bei A 1, nur bei B 2.\n"
    "  Reihen: 5, davon beide ohne Zeitraum: 2 (40 %).\n"
    "\n"
    "  Reihe                                                        A   B   =  nurA  nurB\n"
    "  Beispielwerk / employee / durchschnittsbewertung             1   2   1     0     1\n"
    "  Fremdwerk / employee / durchschnittsbewertung                0   1   0     0     1   (ohne Serien-CSV: reine Toleranz)\n"
    "  Leerwerk / employee / durchschnittsbewertung                 0   0   0     0     0\n"
    "  Musterbau / employee / durchschnittsbewertung                1   0   0     1     0\n"
    "  Stillwerk / employee / durchschnittsbewertung                0   0   0     0     0\n"
    "  Beispielwerk / employee / durchschnittsbewertung:\n"
    "    Übereinstimmung: A 2020-05..2020-06 fall (Fenster 2020-04..2020-07) <-> B 2020-06..2020-07\n"
    "    Nur bei B:       2020-11..2020-11 rise\n"
    "  Fremdwerk / employee / durchschnittsbewertung:\n"
    "    Nur bei B:       2021-02..2021-02 fall\n"
    "  Musterbau / employee / durchschnittsbewertung:\n"
    "    Nur bei A:       2020-03..2020-03 rise (Fenster 2020-02..2020-04)\n"
    "\n"
    "Beschreibende Zahlen. Übereinstimmung nach E5, Regel 6 (Toleranz, Richtung, Eins-zu-eins); keine Aussage, "
    "welche Datei richtig liegt."
)
OLD_KEYS = {
    "report": {"generated_at", "note", "rules", "series", "totals", "versions"},
    "totals": {"matched", "n_a", "n_b", "n_series", "only_a", "only_b", "series_both_none", "share_both_none",
               "share_matched_of_a", "share_matched_of_b"},
    "row": {"both_none", "company", "dimension", "evaluated_known", "matches", "n_a", "n_b", "only_a", "only_b", "series", "source"},
}


class TestOutputUnchanged:

    def _report(self):
        a = doc(ann("2020-05", "2020-06", "fall"), ann("2020-03", "2020-03", "rise", company="Musterbau"))
        b = doc(ann("2020-06", "2020-07", "fall"), ann("2020-11", "2020-11", "rise"), ann("2021-02", "2021-02", "fall", company="Fremdwerk"))
        return ca.compare(a, b, SERIES)

    def test_old_text_is_unchanged_prefix(self):
        text = ca.format_report(self._report(), "a.json", "b.json")
        assert text.startswith(OLD_REPORT + "\n")
        kappa_block = text[len(OLD_REPORT):]
        assert kappa_block.startswith("\n\nCohens κ auf Monatsebene")
        assert "Gesamt: κ " in kappa_block and "in 4 Reihen" in kappa_block
        assert "Fremdwerk / employee / durchschnittsbewertung" in kappa_block and "(ohne Serien-CSV: keine Monate)" in kappa_block
        assert "konstruiert" not in text

    def test_old_json_keys_kept(self):
        r = self._report()
        assert OLD_KEYS["report"] <= set(r) and set(r) - OLD_KEYS["report"] == {"kappa"}
        assert set(r["totals"]) == OLD_KEYS["totals"]
        for row in r["series"]:
            assert set(row) - OLD_KEYS["row"] == {"kappa"}


# ── Teilmenge (--series) ─────────────────────────────────────────────────────

class TestSeriesSelection:

    def test_compare_only(self):
        a = doc(ann("2020-05", "2020-05", "fall"), ann("2020-03", "2020-03", "fall", company="Musterbau"))
        r = ca.compare(a, doc(), SERIES, only={"beispielwerk", "leerwerk"})
        assert [s["company"] for s in r["series"]] == ["Beispielwerk", "Leerwerk"]
        assert r["totals"]["n_a"] == 1 and r["kappa"]["overall"]["n_months"] == 48

    def test_selection_from_key_and_converted_file(self):
        key = {"reihen": {"Reihe A": {"company_id": 2, "name": "Musterbau"}, "Reihe B": {"company_id": 1, "name": "Beispielwerk"}}}
        converted = {"hinweise": {"herkunft": {"reihen": {"Reihe A": {"company_id": 2, "company": "Musterbau"}}}}}
        assert sorted(ca.selection_from_doc(key)) == [(1, "Beispielwerk"), (2, "Musterbau")]
        assert ca.selection_from_doc(converted) == [(2, "Musterbau")]
        assert ca.selection_from_doc(doc()) is None and ca.selection_from_doc([1]) is None

    def test_resolve_ids_and_files(self, tmp_path):
        names = {1: "Beispielwerk", 2: "Musterbau"}
        assert ca.resolve_selection("1, 2", names) == ({"beispielwerk", "musterbau"}, None)
        sel, err = ca.resolve_selection("1,9", names)
        assert sel is None and "9" in err
        sel, err = ca.resolve_selection("abc", names)
        assert sel is None and "weder eine Datei" in err
        key = tmp_path / "key.json"
        key.write_text(json.dumps({"reihen": {"Reihe A": {"company_id": 2, "name": "Musterbau"}}}), encoding="utf-8")
        assert ca.resolve_selection(str(key), names) == ({"musterbau"}, None)
        other = tmp_path / "other.json"
        other.write_text(json.dumps(doc()), encoding="utf-8")
        sel, err = ca.resolve_selection(str(other), names)
        assert sel is None and "herkunft" in err

    def test_cli_series_and_hint(self, tmp_path, capsys):
        series_dir = tmp_path / "series"
        series_dir.mkdir()
        _write_csv(series_dir / "1_beispielwerk_employee.csv", list(months(2020, 1, 24)))
        _write_csv(series_dir / "2_leerwerk_employee.csv", list(months(2020, 1, 24)))
        density = tmp_path / "density.json"
        density.write_text(json.dumps({"companies": [{"id": 1, "name": "Beispielwerk"}, {"id": 2, "name": "Leerwerk"}]}), encoding="utf-8")
        a, b = tmp_path / "a.json", tmp_path / "b.json"
        a.write_text(json.dumps(doc(ann("2020-05", "2020-06", "fall"))), encoding="utf-8")
        b_doc = doc(ann("2020-05", "2020-06", "fall"))
        b_doc["hinweise"] = {"herkunft": {"reihen": {"Reihe A": {"company_id": 1, "company": "Beispielwerk"}}}}
        b.write_text(json.dumps(b_doc), encoding="utf-8")
        base = ["--a", str(a), "--b", str(b), "--series-dir", str(series_dir), "--density", str(density)]
        assert ca.main(base) == 0
        out = capsys.readouterr().out
        assert "Datei B stammt aus der blinden Zweitannotation" in out and "Reihen: 2," in out
        result = tmp_path / "r.json"
        assert ca.main(base + ["--series", str(b), "--json", str(result)]) == 0
        out = capsys.readouterr().out
        assert "Auswahl (--series): 1 Reihen." in out and "Reihen: 1," in out
        data = json.loads(result.read_text(encoding="utf-8"))
        assert data["kappa"]["overall"]["kappa"] == 1.0 and data["series"][0]["kappa"]["n_months"] == 24
        assert ca.main(base + ["--series", "7"]) == 1 and "FEHLER" in capsys.readouterr().out
