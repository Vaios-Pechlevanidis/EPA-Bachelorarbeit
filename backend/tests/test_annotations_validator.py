"""
Tests für scripts/validate_annotations.py (reine Prüf-Logik, ohne DB und Netz).

Die Unternehmensliste wird aus einem kleinen In-Memory-Abbild von
data_density.json aufgebaut; es werden nur die Funktionen
companies_from_density(), validate() und format_report() verwendet.

Ausführen:
    cd backend
    uv run python -m pytest tests/test_annotations_validator.py -q -p no:cacheprovider
"""

import os
import sys

import pytest

BACKEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, BACKEND_DIR)
sys.path.insert(0, os.path.join(BACKEND_DIR, "scripts"))

import validate_annotations as va  # noqa: E402


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

DENSITY = {
    "companies": [
        {
            "id": 7, "name": "E.ON", "name_raw": "E.ON\n", "name_normalized": "e.on",
            "sources": {
                "employee": {"first_month": "2018-01", "last_month": "2026-04"},
                "candidates": {"first_month": "2008-10", "last_month": "2026-03"},
            },
        },
        {
            "id": 20, "name": "NTT DATA SE", "name_raw": "NTT  DATA SE", "name_normalized": "ntt data se",
            "sources": {
                "employee": {"first_month": "2015-07", "last_month": "2026-07"},
                "candidates": {"first_month": None, "last_month": None},
            },
        },
        {
            "id": 10, "name": "Demo 1", "name_raw": "Demo 1", "name_normalized": "demo 1",
            "sources": {
                "employee": {"first_month": "2022-01", "last_month": "2026-05"},
                "candidates": {"first_month": "2022-01", "last_month": "2026-05"},
            },
        },
    ]
}


def make_doc(*entries):
    return {"version": 1, "hinweise": {}, "annotations": list(entries)}


def valid_entry(**overrides):
    entry = {
        "company": "E.ON",
        "source": "employee",
        "dimension": "durchschnittsbewertung",
        "period_from": "2020-03",
        "period_to": "2020-05",
        "direction": "fall",
        "note": "Monatsmittel sinkt von 3,8 auf 2,4 bei je mehr als 5 Bewertungen.",
    }
    entry.update(overrides)
    return entry


@pytest.fixture
def companies():
    return va.companies_from_density(DENSITY)


def errors_containing(result, *fragments):
    return [e for e in result.errors if all(f in e for f in fragments)]


# ---------------------------------------------------------------------------
# Unternehmensliste und Namensnormalisierung
# ---------------------------------------------------------------------------

def test_companies_from_density_excludes_demo_and_normalizes(companies):
    assert set(companies) == {"e.on", "ntt data se"}
    assert companies["e.on"].name == "E.ON"
    assert companies["e.on"].ranges["employee"] == ("2018-01", "2026-04")
    assert companies["ntt data se"].ranges["candidates"] is None


@pytest.mark.parametrize("raw,expected", [
    ("E.ON\n", "e.on"),
    ("  e.on ", "e.on"),
    ("NTT  DATA SE", "ntt data se"),
    ("ntt\tdata\nse", "ntt data se"),
    ("Thyssengas  GmbH", "thyssengas gmbh"),
])
def test_normalize_company_name(raw, expected):
    assert va.normalize_company_name(raw) == expected


@pytest.mark.parametrize("raw,expected", [("Demo 1", True), ("demo2", True), ("Demo 3 ", True), ("Demos AG", False), ("E.ON", False)])
def test_is_demo_company(raw, expected):
    assert va.is_demo_company(raw) is expected


# ---------------------------------------------------------------------------
# Gültiger Eintrag
# ---------------------------------------------------------------------------

def test_valid_entry_passes(companies):
    result = va.validate(make_doc(valid_entry()), companies)
    assert result.ok, result.errors
    assert result.warnings == []
    assert result.n_entries == 1
    assert result.companies_annotated == ["E.ON"]
    assert result.companies_missing == ["NTT DATA SE"]
    assert result.companies_total == 2


def test_company_resolves_with_whitespace_and_case_differences(companies):
    doc = make_doc(
        valid_entry(company="  e.on\n"),
        valid_entry(company="ntt   DATA se", period_from="2016-01", period_to="2016-02", direction="rise"),
    )
    result = va.validate(doc, companies)
    assert result.ok, result.errors
    assert result.companies_annotated == ["E.ON", "NTT DATA SE"]


def test_topic_dimension_of_matching_source_is_valid(companies):
    doc = make_doc(
        valid_entry(dimension="kommunikation"),
        valid_entry(source="candidates", dimension="schnelle_antwort", period_from="2015-01", period_to="2015-03"),
    )
    assert va.validate(doc, companies).ok


def test_empty_annotation_list_is_structurally_valid(companies):
    result = va.validate(make_doc(), companies)
    assert result.ok
    assert result.n_entries == 0
    assert result.companies_annotated == []
    assert "0 von 2" in va.format_report(result)


# ---------------------------------------------------------------------------
# Fehlerfälle: jeder liefert eine klare deutsche Meldung
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("bad", ["2024-13", "2024/01", "24-01", "2024-1", "2024-00", "März 2024", "2024-03\n", " 2024-03"])
def test_bad_period_format_fails(companies, bad):
    result = va.validate(make_doc(valid_entry(period_from=bad, period_to="2024-12")), companies)
    assert not result.ok
    assert errors_containing(result, "period_from", bad, "YYYY-MM")


def test_bad_period_to_is_reported_separately(companies):
    result = va.validate(make_doc(valid_entry(period_to="2020-5")), companies)
    assert errors_containing(result, "period_to", "2020-5", "YYYY-MM")
    assert not errors_containing(result, "period_from")


def test_unknown_dimension_fails(companies):
    result = va.validate(make_doc(valid_entry(dimension="stimmung")), companies)
    assert not result.ok
    assert errors_containing(result, "dimension 'stimmung'", "unbekannt")


def test_dimension_of_other_source_fails(companies):
    # "kommunikation" ist ein employee-Thema, nicht candidates
    result = va.validate(
        make_doc(valid_entry(source="candidates", dimension="kommunikation", period_from="2015-01", period_to="2015-02")),
        companies,
    )
    assert errors_containing(result, "dimension 'kommunikation'", "source 'candidates'")


def test_unknown_company_fails(companies):
    result = va.validate(make_doc(valid_entry(company="Siemens")), companies)
    assert not result.ok
    assert errors_containing(result, "Unternehmen 'Siemens'", "nicht auflösbar")


def test_demo_company_is_rejected(companies):
    result = va.validate(make_doc(valid_entry(company="Demo 1", period_from="2023-01", period_to="2023-02")), companies)
    assert errors_containing(result, "Demo-Unternehmen", "nicht zulässig")


def test_period_to_before_period_from_fails(companies):
    result = va.validate(make_doc(valid_entry(period_from="2020-06", period_to="2020-02")), companies)
    assert not result.ok
    assert errors_containing(result, "period_from '2020-06'", "nach period_to '2020-02'")


@pytest.mark.parametrize("note", ["", "   ", "\n\t"])
def test_empty_note_fails(companies, note):
    result = va.validate(make_doc(valid_entry(note=note)), companies)
    assert not result.ok
    assert errors_containing(result, "note ist leer")


def test_period_outside_data_range_fails(companies):
    result = va.validate(make_doc(valid_entry(period_from="2017-11", period_to="2018-02")), companies)
    assert errors_containing(result, "außerhalb des Datenzeitraums", "2018-01..2026-04")
    result = va.validate(make_doc(valid_entry(period_from="2026-04", period_to="2026-05")), companies)
    assert errors_containing(result, "außerhalb des Datenzeitraums")


def test_period_on_range_boundaries_passes(companies):
    result = va.validate(make_doc(valid_entry(period_from="2018-01", period_to="2026-04")), companies)
    assert result.ok, result.errors


def test_source_without_data_fails(companies):
    result = va.validate(
        make_doc(valid_entry(company="NTT DATA SE", source="candidates", period_from="2020-01", period_to="2020-02")),
        companies,
    )
    assert errors_containing(result, "keine datierten Bewertungen", "candidates")


def test_unknown_range_fails():
    companies = va.companies_from_density(DENSITY)
    companies["e.on"].ranges = {}
    result = va.validate(make_doc(valid_entry()), companies)
    assert errors_containing(result, "Datenzeitraum", "unbekannt")


@pytest.mark.parametrize("field,value,fragment", [
    ("source", "kunden", "source 'kunden' ungültig"),
    ("direction", "up", "direction 'up' ungültig"),
])
def test_invalid_enum_values_fail(companies, field, value, fragment):
    result = va.validate(make_doc(valid_entry(**{field: value})), companies)
    assert errors_containing(result, fragment)


def test_missing_required_keys_fail(companies):
    entry = valid_entry()
    del entry["direction"]
    del entry["note"]
    result = va.validate(make_doc(entry), companies)
    assert errors_containing(result, "Pflichtfeld", "direction", "note")


def test_non_string_field_fails(companies):
    result = va.validate(make_doc(valid_entry(period_from=2020)), companies)
    assert errors_containing(result, "'period_from'", "Zeichenkette")


def test_unknown_extra_field_is_only_a_warning(companies):
    result = va.validate(make_doc(valid_entry(detected_by="algorithmus")), companies)
    assert result.ok
    assert any("detected_by" in w for w in result.warnings)


def test_non_object_entry_fails(companies):
    result = va.validate(make_doc("E.ON 2020-03 fall"), companies)
    assert errors_containing(result, "Eintrag #1", "JSON-Objekt")


def test_duplicate_entries_fail(companies):
    result = va.validate(make_doc(valid_entry(), valid_entry(note="andere Begründung")), companies)
    assert errors_containing(result, "Eintrag #2", "Duplikat von Eintrag #1")


def test_overlapping_entries_warn_but_pass(companies):
    doc = make_doc(valid_entry(), valid_entry(period_from="2020-05", period_to="2020-08", direction="rise"))
    result = va.validate(doc, companies)
    assert result.ok
    assert any("überschneidet" in w and "Eintrag #1" in w for w in result.warnings)


def test_same_period_other_dimension_is_no_duplicate(companies):
    doc = make_doc(valid_entry(), valid_entry(dimension="kommunikation"))
    result = va.validate(doc, companies)
    assert result.ok and result.warnings == []


def test_multiple_errors_in_one_entry_are_all_reported(companies):
    result = va.validate(
        make_doc(valid_entry(company="Siemens", dimension="x", period_to="2019-01", direction="down", note="")),
        companies,
    )
    assert errors_containing(result, "nicht auflösbar")
    assert errors_containing(result, "dimension 'x'")
    assert errors_containing(result, "period_from '2020-03'", "nach period_to")
    assert errors_containing(result, "direction 'down'")
    assert errors_containing(result, "note ist leer")


# ---------------------------------------------------------------------------
# Strukturfehler und --require-all-companies
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("doc,fragment", [
    ([], "JSON-Objekt"),
    ({"version": 1, "annotations": []}, "'hinweise' fehlt"),
    ({"version": 2, "hinweise": {}, "annotations": []}, "version muss 1 sein"),
    ({"version": True, "hinweise": {}, "annotations": []}, "version muss 1 sein"),
    ({"version": "1", "hinweise": {}, "annotations": []}, "version muss 1 sein"),
    ({"version": 1, "hinweise": {}, "annotations": {}}, "annotations muss eine Liste sein"),
    ({"version": 1, "hinweise": "text", "annotations": []}, "hinweise muss ein JSON-Objekt sein"),
])
def test_structure_errors(companies, doc, fragment):
    result = va.validate(doc, companies)
    assert not result.ok
    assert any(fragment in e for e in result.errors), result.errors


def test_require_all_companies(companies):
    result = va.validate(make_doc(valid_entry()), companies, require_all_companies=True)
    assert not result.ok
    assert errors_containing(result, "1 von 2 Unternehmen ohne Annotation", "NTT DATA SE")

    doc = make_doc(valid_entry(), valid_entry(company="NTT DATA SE", period_from="2019-01", period_to="2019-02"))
    assert va.validate(doc, companies, require_all_companies=True).ok


def test_format_report_lists_errors_and_result(companies):
    result = va.validate(make_doc(valid_entry(note="")), companies)
    report = va.format_report(result, "annotations.json")
    assert "annotations.json" in report
    assert "Einträge: 1" in report
    assert "Fehler (1)" in report
    assert "note ist leer" in report
    assert report.strip().endswith("FEHLER (1).")
    assert "OK, keine Fehler." in va.format_report(va.validate(make_doc(), companies))
