"""Tests für scripts/remove_duplicates.py gegen den In-Memory-Store (ohne Netz)."""
import os
import sys

BACKEND = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(BACKEND, "scripts"))

import remove_duplicates as rd  # noqa: E402

FIELDS = rd.key_fields("employee")
BASE = {"company_id": 1, "datum": "2024-01-15T00:00:00+00:00", "titel": "Gut", "durchschnittsbewertung": 4.0,
        "status": "Angestellt", "gut_am_arbeitgeber_finde_ich": "x", "schlecht_am_arbeitgeber_finde_ich": None}


def test_keeps_lowest_id_and_deletes_the_rest():
    rows = [dict(BASE, id=7), dict(BASE, id=3), dict(BASE, id=5), dict(BASE, id=9, titel="Anders")]
    groups = rd.find_duplicate_groups(rows, FIELDS)
    assert len(groups) == 1
    assert groups[0]["keep"] == 3 and groups[0]["delete"] == [5, 7]


def test_other_company_or_other_text_is_no_duplicate():
    rows = [dict(BASE, id=1), dict(BASE, id=2, company_id=2), dict(BASE, id=3, gut_am_arbeitgeber_finde_ich="y")]
    assert rd.find_duplicate_groups(rows, FIELDS) == []


def test_rows_without_date_are_not_compared():
    rows = [dict(BASE, id=1, datum=None), dict(BASE, id=2, datum=None)]
    assert rd.find_duplicate_groups(rows, FIELDS) == []


def test_same_count_as_data_status():
    from services.data_status_service import count_duplicates, DUPLICATE_KEY_FIELDS_BY_SOURCE
    rows = [dict(BASE, id=1), dict(BASE, id=2), dict(BASE, id=3), dict(BASE, id=4, titel="B"), dict(BASE, id=5, titel="B")]
    groups = rd.find_duplicate_groups(rows, FIELDS)
    assert sum(len(g["delete"]) for g in groups) == count_duplicates(rows, DUPLICATE_KEY_FIELDS_BY_SOURCE["employee"])


def test_dry_run_deletes_nothing_and_apply_deletes_duplicates(in_memory_db):
    table = in_memory_db.table("employee").select("*").execute().data
    src = dict(table[0])
    src.pop("id")
    inserted = in_memory_db.table("employee").insert([dict(src), dict(src)]).execute().data
    new_ids = [r["id"] for r in inserted]
    company = src["company_id"]

    def count():
        return len(in_memory_db.table("employee").select("id").eq("company_id", company).execute().data)

    before = count()
    assert rd.main(["--source", "employee", "--company", str(company)]) == 0
    assert count() == before

    assert rd.main(["--source", "employee", "--company", str(company), "--apply"]) == 0
    assert count() == before - 2
    remaining = {r["id"] for r in in_memory_db.table("employee").select("id").execute().data}
    assert table[0]["id"] in remaining and not (set(new_ids) & remaining)
