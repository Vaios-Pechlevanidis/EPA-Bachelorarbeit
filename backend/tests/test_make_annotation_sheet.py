"""
Tests für scripts/make_annotation_sheet.py (Annotationsbogen, E5): ohne DB und
ohne Netz, aus konstruierten Serien-CSVs in einem temporären Ordner.

Gesichert wird vor allem die Unabhängigkeit der Referenz: Das Skript importiert
weder den Anomalie-Dienst noch den Changepoint-Detektor, und der Bogen enthält
keine Markierung, keine Niveaulinie und keinen hervorgehobenen Einzelmonat.

Ausführen:
    cd backend
    uv run python -m pytest tests/test_make_annotation_sheet.py -q -p no:cacheprovider
"""

import ast
import json
import os
import re
import sys

import pytest

BACKEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, BACKEND_DIR)
sys.path.insert(0, os.path.join(BACKEND_DIR, "scripts"))

import make_annotation_sheet as mas  # noqa: E402

SCRIPT_PATH = os.path.join(BACKEND_DIR, "scripts", "make_annotation_sheet.py")
FORBIDDEN_MODULES = ("anomaly_service", "changepoint_detector", "explanation_service")


# ── Hilfen ───────────────────────────────────────────────────────────────────

def months(first_year: int, first_month: int, n: int):
    y, m = first_year, first_month
    for _ in range(n):
        yield f"{y:04d}-{m:02d}"
        m += 1
        if m == 13:
            y, m = y + 1, 1


def write_series(path, rows):
    """rows: Liste (period, mean | None, count)."""
    prev = None
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("period;mean_durchschnittsbewertung;count;delta_vs_previous\n")
        for period, mean, count in rows:
            delta = "" if (mean is None or prev is None) else f"{mean - prev:.3f}"
            fh.write(f"{period};{'' if mean is None else f'{mean:.3f}'};{count};{delta}\n")
            if mean is not None:
                prev = mean


@pytest.fixture
def workspace(tmp_path):
    series_dir = tmp_path / "series"
    series_dir.mkdir()
    # Geeignete Reihe (id 7): 14 bewertete Monate mit deutlichem Sprung, eine Lücke und dünne Monate
    periods = list(months(2020, 1, 18))
    rows = []
    for i, p in enumerate(periods):
        if i == 6:
            rows.append((p, None, 0))            # Monat ohne Bewertung
        elif i in (9, 10):
            rows.append((p, 3.9, 2))             # unter der Mindestdichte
        else:
            rows.append((p, 4.2 if i < 12 else 2.6, 8))
    write_series(series_dir / "7_e_on_employee.csv", rows)
    # Nicht geeignete Reihe (id 5): nur 3 bewertete Monate
    rows2 = [(p, 3.5, 6 if i < 3 else 1) for i, p in enumerate(months(2021, 1, 10))]
    write_series(series_dir / "5_pledoc_gmbh_employee.csv", rows2)
    # Bewerberquelle (id 7), geeignet
    rows3 = [(p, 3.0, 5) for p in months(2019, 1, 12)]
    write_series(series_dir / "7_e_on_candidates.csv", rows3)

    density = {"companies": [{"id": 7, "name": "E.ON", "name_raw": "E.ON\n"}, {"id": 5, "name": "PLEdoc GmbH"}]}
    (tmp_path / "data_density.json").write_text(json.dumps(density), encoding="utf-8")
    annotations = {
        "version": 1,
        "hinweise": {
            "vorgehen": ["1. CSV öffnen.", "2. Zeiträume markieren."],
            "protokoll": {
                "quelle": "docs/referenzzeitraeume-literatur.md, Abschnitt 3",
                "regeln": ["1 Einheit: Kalendermonat.", "2 Länge: höchstens 6 Kalendermonate."],
                "note_beispiel": "Vorniveau 3,9; Zeitraum 3,1; Δ -0,8; fall; Anker: keiner; Reihe allein.",
            },
        },
        "annotations": [],
    }
    (tmp_path / "annotations.json").write_text(json.dumps(annotations, ensure_ascii=False), encoding="utf-8")
    return tmp_path


def build(workspace, **kwargs):
    out = workspace / "bogen.html"
    result = mas.build_sheet(
        series_dir=str(workspace / "series"), out=str(out),
        density_path=str(workspace / "data_density.json"), annotations_path=str(workspace / "annotations.json"),
        **kwargs,
    )
    return result, out.read_text(encoding="utf-8")


# ── Unabhängigkeit vom Erkennungscode ───────────────────────────────────────

class TestIndependence:

    def test_script_imports_no_detection_code(self):
        tree = ast.parse(open(SCRIPT_PATH, encoding="utf-8").read())
        imported = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imported.append(node.module or "")
        for name in imported:
            assert not any(f in name for f in FORBIDDEN_MODULES), f"verbotener Import: {name}"
        source = open(SCRIPT_PATH, encoding="utf-8").read()
        assert "__import__" not in source and "importlib" not in source

    def test_sheet_has_no_markers_levels_or_outliers(self, workspace):
        _, page = build(workspace)
        svg = re.search(r"<svg.*?</svg>", page, re.S).group(0)
        series = mas.read_series_csv(str(workspace / "series" / "7_e_on_employee.csv"))
        n_with_mean = sum(1 for m in series if m["mean"] is not None)
        n_with_count = sum(1 for m in series if m["count"] > 0)
        # genau ein Punkt je Monat mit Wert und ein Balken je Monat mit Bewertungen, sonst keine Formen
        assert len(re.findall(r"<circle ", svg)) == n_with_mean
        assert len(re.findall(r"<rect ", svg)) == n_with_count
        assert "<path" not in svg and "<polygon" not in svg
        # Linien: Raster (5), Jahresmarken, Mindestdichte; keine Niveaulinie
        classes = set(re.findall(r'<line class="([a-z]+)"', svg))
        assert classes == {"raster", "jahr", "mindestdichte"}
        # eine Verlaufslinie je zusammenhängendem Block bewerteter Monate (Lücke bei Index 6 und 9/10)
        assert len(re.findall(r"<polyline ", svg)) == 3
        # Die Abschnitte der Reihen (Diagramme und Tabellen) nennen keine Erkennungsbegriffe;
        # der Hinweiskasten oben darf sie nennen, um das Fehlen zu erklären.
        sections = page[page.index("<section"):].lower()
        for word in ("anomal", "niveauwechsel", "einzelmonat", "auffällig", "erkannt", "markierung", "pelt", "strafterm"):
            assert word not in sections, f"Reihenabschnitt nennt '{word}'"


# ── Inhalt ───────────────────────────────────────────────────────────────────

class TestContent:

    def test_only_eligible_series_by_default(self, workspace):
        result, page = build(workspace)
        assert result["n_series"] == 1 and result["companies"] == ["E.ON"]
        assert 'id="s-7-employee"' in page and 'id="s-5-employee"' not in page
        assert "7_e_on_employee.csv" in page and "E.ON (7)" in page

    def test_include_ineligible_marks_them(self, workspace):
        result, page = build(workspace, include_ineligible=True)
        assert result["n_series"] == 2
        assert 'id="s-5-employee"' in page and "nicht geeignet nach E4" in page

    def test_candidates_source(self, workspace):
        result, page = build(workspace, source="candidates")
        assert result["companies"] == ["E.ON"] and "7_e_on_candidates.csv" in page and "Bewerbende" in page

    def test_thin_months_and_min_density_visible(self, workspace):
        _, page = build(workspace)
        assert 'class="punkt duenn"' in page and 'class="balken duenn"' in page
        assert 'class="mindestdichte"' in page
        assert "unter der Mindestdichte" in page
        # Monatstabelle mit Anzahl und Differenz
        assert "<table>" in page and "unter Mindestdichte (5)" in page and "keine Bewertung" in page

    def test_protocol_texts_from_annotations_file(self, workspace):
        _, page = build(workspace)
        assert mas.KURZFASSUNG_E5[:40] in page
        assert "Einheit: Kalendermonat." in page and "höchstens 6 Kalendermonate" in page
        assert "Beispiel für die" in page and "Reihe allein" in page
        assert "Zeiträume markieren" in page

    def test_missing_annotations_file_falls_back(self, workspace):
        out = workspace / "b2.html"
        mas.build_sheet(series_dir=str(workspace / "series"), out=str(out),
                        density_path=str(workspace / "data_density.json"), annotations_path=str(workspace / "fehlt.json"))
        page = out.read_text(encoding="utf-8")
        assert "annotations.json wurde nicht gefunden" in page and mas.KURZFASSUNG_E5[:40] in page

    def test_eligibility_rule(self):
        evaluated = [{"period": p, "mean": 3.0, "count": 5, "delta": None} for p in months(2020, 1, 12)]
        assert mas.is_eligible(evaluated)
        evaluated[0]["count"] = 4
        assert not mas.is_eligible(evaluated)
        no_mean = [{"period": p, "mean": None, "count": 9, "delta": None} for p in months(2020, 1, 12)]
        assert mas.evaluated_months(no_mean) == 0

    def test_invalid_source_raises(self, workspace):
        with pytest.raises(ValueError):
            mas.build_sheet(series_dir=str(workspace / "series"), source="kunden", out=str(workspace / "x.html"))

    def test_cli_writes_file(self, workspace, capsys):
        out = workspace / "cli.html"
        code = mas.main([
            "--series-dir", str(workspace / "series"), "--out", str(out),
            "--density", str(workspace / "data_density.json"), "--annotations", str(workspace / "annotations.json"),
        ])
        assert code == 0 and out.exists()
        text = capsys.readouterr().out
        assert "1 Reihen" in text and "E.ON" in text

    def test_cli_missing_series_dir(self, workspace, capsys):
        assert mas.main(["--series-dir", str(workspace / "gibt_es_nicht"), "--out", str(workspace / "x.html")]) == 1
        assert "make_annotation_basis.py" in capsys.readouterr().out
