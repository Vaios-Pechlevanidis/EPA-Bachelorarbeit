"""
Tests für scripts/make_annotation_sheet.py (Annotationsbogen, E5): ohne DB und
ohne Netz, aus konstruierten Serien-CSVs in einem temporären Ordner.

Gesichert wird vor allem die Unabhängigkeit der Referenz: Das Skript importiert
weder den Anomalie-Dienst noch den Changepoint-Detektor, und der Bogen enthält
keine Markierung, keine Niveaulinie und keinen hervorgehobenen Einzelmonat.

Blinde Fassung (``--blind``, 2026-10-13): kein Unternehmensname, kein Kalendermonat
(Muster ``\\b(19|20)\\d\\d-\\d\\d\\b``), keine ids und Dateinamen im HTML; Schlüssel und
Monatsindizes sind invers; ohne ``--blind`` bleibt die Ausgabe Byte für Byte wie vor der
Erweiterung (Prüfsummen, erzeugt mit dem Stand vor der Änderung).

Ausführen:
    cd backend
    uv run python -m pytest tests/test_make_annotation_sheet.py -q -p no:cacheprovider
"""

import ast
import hashlib
import html
import json
import os
import re
import sys
from datetime import date

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


# ── Ohne --blind unverändert ─────────────────────────────────────────────────

# sha256 der Ausgabe von render_html für den Fixture-Ordner mit generated = 2026-10-13, erzeugt
# mit make_annotation_sheet.py vor der Erweiterung um --blind/--companies (Stand HEAD 2551300).
GOLDEN_SHA256 = {
    ("employee", False): "f038093e4d185bd269e67635a86912d1c6c9f7f89d00615eda8272e49e165b56",
    ("employee", True): "910ccc4293fd0d1efdf7b2a83befcf7f53d8101f51d5f910dd02609c65e6df74",
    ("candidates", False): "4d3c780bffb80aa072af9432e588047965834d8d0204e4d401e88c764e48621e",
}


class TestUnchangedWithoutBlind:

    @pytest.mark.parametrize("source,include_ineligible", list(GOLDEN_SHA256))
    def test_output_identical_to_before(self, workspace, source, include_ineligible):
        names = mas.company_names(str(workspace / "data_density.json"))
        entries = mas.collect_series(str(workspace / "series"), source, names, include_ineligible)
        page = mas.render_html(entries, source, mas.protocol_texts(str(workspace / "annotations.json")),
                               generated=date(2026, 10, 13), include_ineligible=include_ineligible)
        assert hashlib.sha256(page.encode("utf-8")).hexdigest() == GOLDEN_SHA256[(source, include_ineligible)]

    def test_default_out_and_no_key_without_blind(self, workspace, monkeypatch):
        monkeypatch.setattr(mas, "DEFAULT_OUT", str(workspace / "standard.html"))
        monkeypatch.setattr(mas, "DEFAULT_KEY", str(workspace / "schluessel.json"))
        result = mas.build_sheet(series_dir=str(workspace / "series"), out=None,
                                 density_path=str(workspace / "data_density.json"),
                                 annotations_path=str(workspace / "annotations.json"))
        assert result["out"] == str(workspace / "standard.html") and "key" not in result
        assert not (workspace / "schluessel.json").exists()


# ── Teilmenge (--companies) ──────────────────────────────────────────────────

class TestCompanies:

    def test_parse_ids(self):
        assert mas.parse_company_ids(["19,24", "7", " 24 "]) == [7, 19, 24]
        assert mas.parse_company_ids(None) == []
        with pytest.raises(ValueError):
            mas.parse_company_ids(["19,abc"])

    def test_subset(self, workspace):
        result, page = build(workspace, include_ineligible=True, companies=[5])
        assert result["companies"] == ["PLEdoc GmbH"] and 'id="s-5-employee"' in page and 'id="s-7-employee"' not in page

    def test_unknown_or_ineligible_id_is_an_error(self, workspace):
        with pytest.raises(ValueError, match="99"):
            build(workspace, companies=[99])
        with pytest.raises(ValueError, match="include-ineligible"):
            build(workspace, companies=[5])           # nicht geeignet ohne --include-ineligible

    def test_cli_unknown_id(self, workspace, capsys):
        code = mas.main(["--series-dir", str(workspace / "series"), "--out", str(workspace / "x.html"),
                         "--density", str(workspace / "data_density.json"), "--companies", "99"])
        assert code == 1 and "FEHLER" in capsys.readouterr().out and not (workspace / "x.html").exists()


# ── Blinde Fassung ───────────────────────────────────────────────────────────

DATE_PATTERN = re.compile(r"\b(19|20)\d\d-\d\d\b")

FULL_PROTOCOL = {
    "version": 3,
    "hinweise": {
        "vorgehen": ["1. CSV backend/data/series/<id>_<slug>_<source>.csv öffnen.", "3b. Danach nach Ereignissen suchen."],
        "protokoll": {
            "quelle": "docs/referenzzeitraeume-literatur.md, Abschnitt 3",
            "regeln": [f"{i} Regel {i} des Protokolls." for i in range(1, 7)] + [
                "7 Ereignisanker zweistufig: erst die Reihe, dann Ereignissuche mit Datum, Quelle und URL.",
                "8 Unabhängigkeit: vor dem Erkennungscode versionieren.",
                "9 Dünn belegte Unternehmen (Liste in docs/datenbasis.md) erhalten keine Einträge.",
                "10 Dimensionen: primär durchschnittsbewertung.",
                "11 Inhalt der note: ... Ereignisanker: Datum, Quelle, URL oder 'keiner' - 'Reihe allein' oder 'Reihe + Ereignis'.",
            ],
            "note_beispiel": "Vorniveau 3,9 (2022-10 bis 2023-02, n=7-12); Zeitraum 3,1; Anker: 2023-04 (EQS); Reihe + Ereignis.",
        },
    },
    "annotations": [],
}


def build_blind(workspace, seed=7, **kwargs):
    out, key = workspace / "blind.html", workspace / "schluessel.json"
    result = mas.build_sheet(
        series_dir=str(workspace / "series"), out=str(out), density_path=str(workspace / "data_density.json"),
        annotations_path=str(workspace / "annotations.json"), blind=True, seed=seed, key_path=str(key), **kwargs,
    )
    return result, out.read_text(encoding="utf-8"), json.loads(key.read_text(encoding="utf-8"))


def fake_entry(company_id, n=14, first=(2020, 1)):
    series = [{"period": p, "mean": 3.5, "count": 6, "delta": None} for p in months(first[0], first[1], n)]
    return {"company_id": company_id, "name": f"Werk {company_id}", "slug": f"werk_{company_id}", "source": "employee",
            "file": f"{company_id}_werk_{company_id}_employee.csv", "series": series, "evaluated_months": n, "eligible": True}


class TestBlind:

    def test_no_names_dates_ids_or_files(self, workspace):
        result, page, _ = build_blind(workspace, include_ineligible=True)
        text = html.unescape(page)
        assert result["n_series"] == 2
        assert DATE_PATTERN.search(text) is None, "kein Kalendermonat im blinden Bogen"
        for word in ("E.ON", "PLEdoc", "e_on", "pledoc", "employee.csv", "s-7-", "s-5-", "Erzeugt am"):
            assert word.lower() not in text.lower(), f"blinder Bogen nennt '{word}'"
        assert "Reihe A" in text and "Reihe B" in text and "blinde Fassung" in text
        assert mas.blind_leaks(page, mas.collect_series(str(workspace / "series"), "employee",
                                                        mas.company_names(str(workspace / "data_density.json")), True)) == []

    def test_month_labels_in_svg_table_and_nav(self, workspace):
        _, page, key = build_blind(workspace)
        assert list(key["reihen"]) == ["Reihe A"]
        svg = re.search(r"<svg.*?</svg>", page, re.S).group(0)
        # Marken alle zwölf Monate ab M001, beschriftet mit dem Index, keine Jahreszahl
        assert re.findall(r'<text class="achse" x="[\d.]+" y="[\d.]+">(M\d+)</text>', svg) == ["M001", "M013"]
        assert len(re.findall(r'<line class="jahr"', svg)) == 2
        assert "<td>M001</td>" in page and "<td>M018</td>" in page and "<td>M019</td>" not in page
        assert "M001 – M018" in page and 'href="#s-reihe-a"' in page and 'id="s-reihe-a"' in page
        assert "<title>M007: 0 Bewertungen" not in page and "M010: Mittel 3,90, 2 Bewertungen" in page

    def test_key_and_month_indices_are_inverse(self, workspace):
        result, page, key = build_blind(workspace, include_ineligible=True)
        assert key["seed"] == 7 and key["source"] == "employee" and key["dimension"] == "durchschnittsbewertung"
        assert key["bogen_sha256"] == hashlib.sha256(page.encode("utf-8")).hexdigest()
        assert key["bogen"] == "blind.html" and result["key"].endswith("schluessel.json")
        assert {info["company_id"] for info in key["reihen"].values()} == {5, 7}
        for label, info in key["reihen"].items():
            csv_rows = mas.read_series_csv(str(workspace / "series" / info["file"]))
            periods = [r["period"] for r in csv_rows]
            monate = info["monate"]
            assert list(monate.values()) == periods and len(set(monate.values())) == len(monate)
            assert list(monate) == mas.month_labels(len(periods))
            inverse = {v: k for k, v in monate.items()}
            assert all(monate[inverse[p]] == p for p in periods)
            assert (info["first_month"], info["last_month"]) == (periods[0], periods[-1])
            # Abschnitt des Bogens nennt dieselbe Zahl Monate wie der Schlüssel
            assert f"{len(periods)} Kalendermonate M001 – {list(monate)[-1]}" in page

    def test_calendar_gaps_are_filled(self, workspace):
        series_dir = workspace / "series"
        rows = [(p, 4.0, 6) for p in months(2021, 1, 15) if p != "2021-05"]       # 2021-05 fehlt in der CSV
        write_series(series_dir / "9_luecke_ag_employee.csv", rows)
        _, page, key = build_blind(workspace, companies=[9])
        info = key["reihen"]["Reihe A"]
        assert info["monate"]["M005"] == "2021-05" and info["monate"]["M015"] == "2022-03" and len(info["monate"]) == 15
        assert "<tr class=\"leer\"><td>M005</td>" in page

    def test_seed_fixes_order(self):
        entries = [fake_entry(i) for i in (3, 8, 11, 19, 24)]
        order = lambda seed: [info["company_id"] for info in mas.blind_entries(entries, seed)[1].values()]  # noqa: E731
        assert order(42) == order(42)
        assert len({tuple(order(s)) for s in range(1, 21)}) > 1, "verschiedene Seeds ergeben verschiedene Reihenfolgen"
        assert sorted(order(42)) == [3, 8, 11, 19, 24]
        blinded, _ = mas.blind_entries(entries, 42)
        for e in blinded:
            assert set(e) == {"label", "anchor", "source", "series", "month_labels", "evaluated_months", "eligible"}

    def test_series_labels(self):
        assert [mas.series_label(i) for i in (0, 1, 25, 26, 27, 701, 702)] == ["A", "B", "Z", "AA", "AB", "ZZ", "AAA"]
        assert mas.month_labels(3) == ["M001", "M002", "M003"] and mas.month_labels(1000)[-1] == "M1000"

    def test_protocol_without_event_anchor(self, workspace):
        (workspace / "annotations.json").write_text(json.dumps(FULL_PROTOCOL, ensure_ascii=False), encoding="utf-8")
        _, page, _ = build_blind(workspace)
        text = html.unescape(page)
        assert "Ereignisanker zweistufig" not in text and "Reihe + Ereignis" not in text
        assert "Ereignissuche" not in text and "nach Ereignissen suchen." not in text
        assert mas.BLIND_RULES["7"] in text and mas.BLIND_RULES["11"] in text and mas.BLIND_NOTE_BEISPIEL in text
        assert "CSV backend/data/series" not in text and "Vorgehen (blinde Fassung)" in text
        # Nummern bleiben: elf Regeln, Regel 7 an siebter Stelle
        rules = re.findall(r"<li>(.*?)</li>", page[page.index("<ol>"):page.index("</ol>")])
        assert len(rules) == 11 and rules[6].startswith("Ereignisanker: entfällt") and rules[5] == "Regel 6 des Protokolls."
        # die normale Fassung zeigt das Protokoll unverändert
        _, normal = build(workspace)
        assert "Ereignisanker zweistufig" in normal and "Reihe + Ereignis" in normal

    def test_leak_check(self):
        entries = [fake_entry(7)]
        leaks = mas.blind_leaks("<p>Werk 7 im Monat 2020-05; werk_7</p>", entries)
        assert len(leaks) == 3 and any("2020-05" in x for x in leaks)
        assert mas.blind_leaks("<p>Werkstatt 17, Reihe A, M005</p>", entries) == []

    def test_leak_stops_writing(self, workspace, monkeypatch):
        monkeypatch.setattr(mas, "BLIND_NOTE_BEISPIEL", "Vorniveau wie bei E.ON")
        with pytest.raises(RuntimeError, match="E.ON"):
            build_blind(workspace)
        assert not (workspace / "blind.html").exists() and not (workspace / "schluessel.json").exists()

    def test_key_and_out_must_differ(self, workspace):
        with pytest.raises(ValueError):
            mas.build_sheet(series_dir=str(workspace / "series"), out=str(workspace / "a.json"), blind=True, seed=1,
                            key_path=str(workspace / "a.json"), density_path=str(workspace / "data_density.json"))

    def test_cli_blind(self, workspace, capsys):
        out, key = workspace / "b.html", workspace / "k.json"
        code = mas.main(["--series-dir", str(workspace / "series"), "--density", str(workspace / "data_density.json"),
                         "--annotations", str(workspace / "annotations.json"), "--blind", "--seed", "3",
                         "--out", str(out), "--key", str(key), "--include-ineligible", "--companies", "5,7"])
        assert code == 0 and out.exists() and key.exists()
        text = capsys.readouterr().out
        assert "Blinder Annotationsbogen geschrieben" in text and "Seed 3" in text and "nicht an die annotierende Person" in text
        data = json.loads(key.read_text(encoding="utf-8"))
        assert data["auswahl"] == {"companies": [5, 7], "include_ineligible": True}

    def test_random_seed_when_missing(self, workspace):
        _, _, key = build_blind(workspace, seed=None)
        assert isinstance(key["seed"], int) and key["seed"] > 0

    def test_gitignore_excludes_sheet_and_key(self):
        gitignore = os.path.join(BACKEND_DIR, "..", ".gitignore")
        lines = [ln.strip() for ln in open(gitignore, encoding="utf-8")]
        assert "backend/data/annotationsbogen*.html" in lines
        assert "backend/data/annotationsbogen_blind_schluessel*.json" in lines
