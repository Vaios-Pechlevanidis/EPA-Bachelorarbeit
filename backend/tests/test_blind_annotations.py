"""
Tests für scripts/blind_annotations.py (blinde Zweitannotation, DZ1, E5): Rückübersetzung
einer blinden Annotationsdatei (Reihe X, Mxxx) mit dem Schlüssel aus
``make_annotation_sheet.py --blind`` in das Schema von annotations.json, Prüfung mit dem
Validator und Rückmeldung in blinder Schreibweise. Konstruierte Reihen, Schlüssel und Dateien
in einem temporären Ordner, ohne DB und ohne Netz.

Gesichert wird: Schlüssel und Rückübersetzung sind invers; Vorlage und Rückmeldung an die
Person nennen weder Unternehmen noch Kalendermonate; data/annotations.json wird nie geschrieben.

Ausführen:
    cd backend
    uv run python -m pytest tests/test_blind_annotations.py -q -p no:cacheprovider
"""

import ast
import json
import os
import re
import sys
from datetime import date

import pytest

BACKEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, BACKEND_DIR)
sys.path.insert(0, os.path.join(BACKEND_DIR, "scripts"))

import blind_annotations as ba  # noqa: E402
import make_annotation_sheet as mas  # noqa: E402

SCRIPT_PATH = os.path.join(BACKEND_DIR, "scripts", "blind_annotations.py")
FORBIDDEN_MODULES = ("anomaly_service", "changepoint_detector", "explanation_service", "evaluate_detection")
DATE_PATTERN = re.compile(r"\b(19|20)\d\d-\d\d\b")
NAMES = ("Beispielwerk GmbH", "Musterbau AG")


def months(first_year, first_month, n):
    y, m = first_year, first_month
    for _ in range(n):
        yield f"{y:04d}-{m:02d}"
        m += 1
        if m == 13:
            y, m = y + 1, 1


def write_series(path, rows):
    """rows: Liste (period, mean | None, count)."""
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("period;mean_durchschnittsbewertung;count;delta_vs_previous\n")
        for period, mean, count in rows:
            fh.write(f"{period};{'' if mean is None else f'{mean:.3f}'};{count};\n")


@pytest.fixture
def workspace(tmp_path):
    """Zwei geeignete Reihen, Dichte-Datei und ein Schlüssel aus make_annotation_sheet --blind."""
    series_dir = tmp_path / "series"
    series_dir.mkdir()
    rows1 = [(p, 4.2 if i < 10 else 3.3, 2 if p == "2020-08" else 8) for i, p in enumerate(months(2020, 1, 24))]
    write_series(series_dir / "1_beispielwerk_gmbh_employee.csv", rows1)
    write_series(series_dir / "2_musterbau_ag_employee.csv", [(p, 3.6, 9) for p in months(2018, 6, 30)])
    density = {"companies": [
        {"id": 1, "name": "Beispielwerk GmbH", "name_raw": "Beispielwerk GmbH",
         "sources": {"employee": {"first_month": "2020-01", "last_month": "2021-12"}}},
        {"id": 2, "name": "Musterbau AG", "name_raw": "Musterbau AG ",
         "sources": {"employee": {"first_month": "2018-06", "last_month": "2020-11"}}},
    ]}
    (tmp_path / "data_density.json").write_text(json.dumps(density), encoding="utf-8")
    mas.build_sheet(series_dir=str(series_dir), out=str(tmp_path / "bogen.html"), density_path=str(tmp_path / "data_density.json"),
                    annotations_path=str(tmp_path / "fehlt.json"), blind=True, seed=11, key_path=str(tmp_path / "key.json"))
    return tmp_path


def load_key(ws):
    return json.loads((ws / "key.json").read_text(encoding="utf-8"))


def label_of(key, company_id):
    return next(label for label, info in key["reihen"].items() if info["company_id"] == company_id)


def blind_ann(label, p_from, p_to, direction="fall", note="Vorniveau 4,2 (M004 bis M009, n=8); Zeitraum 3,3 (n=8, 8); Δ -0,9; fall; Reihe allein."):
    return {"company": label, "source": "employee", "dimension": "durchschnittsbewertung", "period_from": p_from,
            "period_to": p_to, "direction": direction, "note": note}


def blind_doc(*entries, version=1):
    return {"version": version, "hinweise": {}, "annotations": list(entries)}


NAMES_BY_ID = {1: "Beispielwerk GmbH", 2: "Musterbau AG"}


# ── Unabhängigkeit ───────────────────────────────────────────────────────────

def test_script_imports_no_detection_code():
    tree = ast.parse(open(SCRIPT_PATH, encoding="utf-8").read())
    imported = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported.append(node.module or "")
    for name in imported:
        assert not any(f in name for f in FORBIDDEN_MODULES), f"verbotener Import: {name}"


# ── Übersetzung ──────────────────────────────────────────────────────────────

class TestUnblind:

    def test_translates_series_months_and_note(self, workspace):
        key = load_key(workspace)
        a = label_of(key, 1)
        doc, errors, warnings = ba.unblind(blind_doc(blind_ann(a, "M011", "M012")), key, NAMES_BY_ID,
                                           today=date(2026, 10, 13), blind_file="blind.json")
        assert errors == [] and warnings == []
        assert doc["annotations"] == [{
            "company": "Beispielwerk GmbH", "source": "employee", "dimension": "durchschnittsbewertung",
            "period_from": "2020-11", "period_to": "2020-12", "direction": "fall",
            "note": "Vorniveau 4,2 (2020-04 bis 2020-09, n=8); Zeitraum 3,3 (n=8, 8); Δ -0,9; fall; Reihe allein.",
        }]
        herkunft = doc["hinweise"]["herkunft"]
        assert herkunft["uebersetzt_am"] == "2026-10-13" and herkunft["blinddatei"] == "blind.json"
        assert herkunft["bogen_sha256"] == key["bogen_sha256"]
        assert {v["company_id"]: v["company"] for v in herkunft["reihen"].values()} == NAMES_BY_ID
        assert doc["version"] == 1 and list(doc) == ["version", "hinweise", "annotations"]

    def test_lenient_spelling_and_missing_source(self, workspace):
        key = load_key(workspace)
        b = label_of(key, 2)
        entry = {"company": f"  {b.lower()} ", "period_from": "m3", "period_to": " M004", "direction": "rise", "note": "x"}
        doc, errors, _ = ba.unblind(blind_doc(entry), key, NAMES_BY_ID)
        assert errors == []
        e = doc["annotations"][0]
        assert (e["company"], e["source"], e["period_from"], e["period_to"]) == ("Musterbau AG", "employee", "2018-08", "2018-09")

    def test_errors_are_in_blind_spelling(self, workspace):
        key = load_key(workspace)
        a = label_of(key, 1)
        doc, errors, warnings = ba.unblind(blind_doc(
            blind_ann("Reihe Q", "M001", "M002"),
            blind_ann(a, "2020-05", "M002"),
            blind_ann(a, "M020", "M030"),
            {**blind_ann(a, "M001", "M002"), "dimension": "kommunikation"},
            {**blind_ann(a, "M005", "M006"), "kommentar": "zusätzlich"},
            ["kein Objekt"],
        ), key, NAMES_BY_ID)
        assert len(errors) == 5
        assert "Reihe 'Reihe Q' gibt es im Bogen nicht" in errors[0]
        assert "hat nicht die Form Mxxx" in errors[1]
        assert "liegt außerhalb der Reihe (M001 bis M024)" in errors[2]
        assert "dimension 'kommunikation' passt nicht" in errors[3]
        assert "muss ein JSON-Objekt sein" in errors[4]
        assert len(warnings) == 1 and "kommentar" in warnings[0]
        assert len(doc["annotations"]) == 1, "nur der fehlerfreie Eintrag"
        for msg in errors + warnings:
            assert DATE_PATTERN.search(msg.replace("'2020-05'", "")) is None
            assert not any(n in msg for n in NAMES)

    def test_note_index_outside_series_is_kept_with_warning(self, workspace):
        key = load_key(workspace)
        a = label_of(key, 1)
        doc, errors, warnings = ba.unblind(blind_doc(blind_ann(a, "M011", "M012", note="Vorniveau ab M099; Reihe allein.")), key, NAMES_BY_ID)
        assert errors == [] and "M099" in warnings[0] and doc["annotations"][0]["note"] == "Vorniveau ab M099; Reihe allein."

    def test_note_short_index_form_is_translated(self, workspace):
        """Kurzformen (M5, m5) gelten in period_from/period_to; die note liest sie ebenso."""
        key = load_key(workspace)
        a = label_of(key, 1)
        note = "Vorniveau (M1 bis m4, M0004); Zeitraum M5..M6; Reihe allein."
        doc, errors, warnings = ba.unblind(blind_doc(blind_ann(a, "m5", "M6", note=note)), key, NAMES_BY_ID)
        assert errors == [] and warnings == []
        e = doc["annotations"][0]
        assert (e["period_from"], e["period_to"]) == ("2020-05", "2020-06")
        assert e["note"] == "Vorniveau (2020-01 bis 2020-04, 2020-04); Zeitraum 2020-05..2020-06; Reihe allein."
        assert re.search(r"\b[Mm]\d+\b", e["note"]) is None

    def test_note_short_index_outside_series_warns(self, workspace):
        key = load_key(workspace)
        a = label_of(key, 1)
        doc, errors, warnings = ba.unblind(blind_doc(blind_ann(a, "M011", "M012", note="ab M0 und m99; Reihe allein.")), key, NAMES_BY_ID)
        assert errors == [] and len(warnings) == 1 and "M0" in warnings[0] and "m99" in warnings[0]
        assert doc["annotations"][0]["note"] == "ab M0 und m99; Reihe allein."

    def test_name_from_density_preferred(self, workspace):
        key = load_key(workspace)
        doc, _, warnings = ba.unblind(blind_doc(blind_ann(label_of(key, 1), "M011", "M012")), key, {1: "Beispielwerk"})
        assert doc["annotations"][0]["company"] == "Beispielwerk" and warnings == []
        doc, _, warnings = ba.unblind(blind_doc(blind_ann(label_of(key, 1), "M011", "M012")), key, {})
        assert doc["annotations"][0]["company"] == "Beispielwerk GmbH" and "data_density.json" in warnings[0]


class TestInverse:

    def test_key_months_are_bijective(self, workspace):
        key = load_key(workspace)
        for info in key["reihen"].values():
            forward, back = ba.series_maps(info)
            assert len(forward) == len(back) == len(info["monate"])
            assert all(back[forward[i]] == f"M{i:03d}" for i in forward)

    def test_blind_unblind_reblind(self, workspace):
        key = load_key(workspace)
        a, b = label_of(key, 1), label_of(key, 2)
        original = blind_doc(blind_ann(a, "M011", "M012"), blind_ann(b, "M003", "M003", "rise", "Vorniveau M001 bis M002; Reihe allein."),
                             blind_ann(a, "M020", "M022", "rise"))
        doc, errors, _ = ba.unblind(original, key, NAMES_BY_ID)
        back, errors2 = ba.reblind(doc, key, NAMES_BY_ID)
        assert errors == [] and errors2 == []
        assert back["annotations"] == original["annotations"]

    def test_normal_reblind_unblind(self, workspace):
        key = load_key(workspace)
        normal = {"version": 2, "hinweise": {}, "annotations": [
            {"company": "Musterbau AG", "source": "employee", "dimension": "durchschnittsbewertung", "period_from": "2019-01",
             "period_to": "2019-03", "direction": "fall", "note": "Vorniveau 3,6 (2018-07 bis 2018-12); Reihe allein."},
            {"company": "Beispielwerk GmbH", "source": "employee", "dimension": "durchschnittsbewertung", "period_from": "2021-12",
             "period_to": "2021-12", "direction": "rise", "note": "ohne Monatsangabe"},
        ]}
        blinded, errors = ba.reblind(normal, key, NAMES_BY_ID)
        assert errors == []
        assert DATE_PATTERN.search(json.dumps(blinded)) is None and not any(n in json.dumps(blinded) for n in NAMES)
        doc, errors, _ = ba.unblind(blinded, key, NAMES_BY_ID)
        assert errors == [] and doc["annotations"] == normal["annotations"] and doc["version"] == 2


class TestTemplateAndPersonReport:

    def test_template_without_mapping(self, workspace):
        key = load_key(workspace)
        text = json.dumps(ba.template_doc(key), ensure_ascii=False)
        assert DATE_PATTERN.search(text) is None and not any(n in text for n in NAMES)
        assert "company_id" not in text and "seed" not in text and key["bogen_sha256"] not in text
        tpl = ba.template_doc(key)
        assert tpl["annotations"] == [] and tpl["version"] == 1
        assert tpl["hinweise"]["reihen_im_bogen"] == {label_of(key, 1): "M001 bis M024", label_of(key, 2): "M001 bis M030"}
        assert tpl["hinweise"]["beispiel_format"]["note"] == mas.BLIND_NOTE_BEISPIEL
        assert "reihen_im_bogen" not in ba.template_doc(None)["hinweise"]

    def test_person_messages(self, workspace):
        key = load_key(workspace)
        a = label_of(key, 1)
        doc = {"annotations": [{"company": "Beispielwerk GmbH", "period_from": "2020-08", "period_to": "2020-09"}]}
        msgs = ba.person_messages([
            "Eintrag #1 (Beispielwerk GmbH/employee/durchschnittsbewertung): period_from 2020-08 hat nur 2 Bewertungen.",
            "Eintrag #1 (Beispielwerk GmbH/employee/durchschnittsbewertung): Zeitraum 2020-08..2020-09 liegt außerhalb "
            "des Datenzeitraums 2019-01..2021-12.",
            "Unternehmen 'MUSTERBAU AG' ohne Bezug, Monat 2019-02.",
        ], doc, key, NAMES_BY_ID)
        assert msgs[0] == f"Eintrag #1 ({a}/employee/durchschnittsbewertung): period_from M008 hat nur 2 Bewertungen."
        assert "M008..M009" in msgs[1] and "[Monat]..M024" in msgs[1]
        assert msgs[2] == f"Unternehmen '{label_of(key, 2)}' ohne Bezug, Monat [Monat]."
        for msg in msgs:
            assert DATE_PATTERN.search(msg) is None and not any(n.lower() in msg.lower() for n in NAMES)


# ── CLI ──────────────────────────────────────────────────────────────────────

def cli(ws, *extra):
    return ba.main(["--key", str(ws / "key.json"), "--blind-file", str(ws / "blind.json"), "--out", str(ws / "out.json"),
                    "--density", str(ws / "data_density.json"), "--series-dir", str(ws / "series"), *extra])


class TestCli:

    @pytest.fixture(autouse=True)
    def protect(self, workspace, monkeypatch):
        # Schutz der Referenz auf eine Datei im Testordner umbiegen, damit kein Test die echte Datei berührt
        monkeypatch.setattr(ba, "PROTECTED_FILE", str(workspace / "annotations.json"))

    def test_template_then_roundtrip_ok(self, workspace, capsys):
        assert cli(workspace, "--template") == 0
        tpl = json.loads((workspace / "blind.json").read_text(encoding="utf-8"))
        assert tpl["annotations"] == [] and len(tpl["hinweise"]["reihen_im_bogen"]) == 2
        key = load_key(workspace)
        tpl["annotations"] = [blind_ann(label_of(key, 1), "M011", "M012")]
        (workspace / "blind.json").write_text(json.dumps(tpl, ensure_ascii=False), encoding="utf-8")
        assert cli(workspace) == 0
        out = capsys.readouterr().out
        assert "Übersetzt: 1 Einträge" in out and "Ergebnis: OK" in out
        doc = json.loads((workspace / "out.json").read_text(encoding="utf-8"))
        assert doc["annotations"][0]["period_from"] == "2020-11" and doc["annotations"][0]["company"] == "Beispielwerk GmbH"

    def test_template_does_not_overwrite(self, workspace, capsys):
        (workspace / "blind.json").write_text(json.dumps(blind_doc(blind_ann("Reihe A", "M001", "M002"))), encoding="utf-8")
        assert cli(workspace, "--template") == 1 and "--force" in capsys.readouterr().out
        assert json.loads((workspace / "blind.json").read_text(encoding="utf-8"))["annotations"] != []
        assert cli(workspace, "--template", "--force") == 0
        assert json.loads((workspace / "blind.json").read_text(encoding="utf-8"))["annotations"] == []

    def test_validation_error_reported_blind_for_person(self, workspace, capsys):
        key = load_key(workspace)
        a = label_of(key, 1)
        # M008 = 2020-08 hat nur 2 Bewertungen: Regel 3 (Randmonat) -> Fehler des Validators
        (workspace / "blind.json").write_text(json.dumps(blind_doc(blind_ann(a, "M008", "M009"))), encoding="utf-8")
        assert cli(workspace, "--for-person") == 1
        out = capsys.readouterr().out
        assert "Beispielwerk GmbH" in out and "2020-08" in out, "Autorenbericht mit Namen und Monaten"
        person = out[out.index("Prüfbericht in der Schreibweise des Bogens"):]
        assert f"Eintrag #1 ({a}/employee/durchschnittsbewertung): period_from M008 hat nur 2 Bewertungen" in person
        assert DATE_PATTERN.search(person) is None and not any(n in person for n in NAMES)
        assert "Ergebnis: FEHLER (1)." in person

    def test_conversion_error_writes_nothing(self, workspace, capsys):
        (workspace / "blind.json").write_text(json.dumps(blind_doc(blind_ann("Reihe Z", "M001", "M002"))), encoding="utf-8")
        assert cli(workspace) == 1
        assert "nichts geschrieben" in capsys.readouterr().out and not (workspace / "out.json").exists()

    def test_refuses_protected_target(self, workspace, capsys):
        (workspace / "blind.json").write_text(json.dumps(blind_doc()), encoding="utf-8")
        (workspace / "annotations.json").write_text("{}", encoding="utf-8")
        code = ba.main(["--key", str(workspace / "key.json"), "--blind-file", str(workspace / "blind.json"),
                        "--out", str(workspace / "annotations.json"), "--density", str(workspace / "data_density.json")])
        assert code == 1 and "Referenz des Autors" in capsys.readouterr().out
        assert (workspace / "annotations.json").read_text(encoding="utf-8") == "{}"

    def test_missing_key(self, workspace, capsys):
        (workspace / "blind.json").write_text(json.dumps(blind_doc()), encoding="utf-8")
        code = ba.main(["--key", str(workspace / "fehlt.json"), "--blind-file", str(workspace / "blind.json"),
                        "--out", str(workspace / "out.json")])
        assert code == 1 and "nicht gefunden" in capsys.readouterr().out

    def test_wrong_schema(self, workspace, capsys):
        (workspace / "blind.json").write_text(json.dumps([1, 2]), encoding="utf-8")
        assert cli(workspace) == 1 and "Schema" in capsys.readouterr().out


def test_default_protected_file_is_the_reference():
    # nur der Pfad wird geprüft; die Datei selbst liest oder schreibt kein Test (test_annotations_file.py)
    protected = os.path.abspath(ba.PROTECTED_FILE)
    assert os.path.basename(protected) == "annotations.json"
    assert os.path.dirname(protected) == os.path.abspath(os.path.join(BACKEND_DIR, "data"))
