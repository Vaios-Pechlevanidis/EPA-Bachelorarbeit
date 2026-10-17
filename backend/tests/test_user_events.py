"""
Tests für eigene Ereignisse (2026-10-17, E32): Prüfung der Eingabe
(``services/user_events_service.py``), Routen GET/POST/PUT/DELETE
``/api/companies/{id}/events`` gegen den In-Memory-Store (Demo 1 = 1), Fehler
bei fehlender Tabelle (503 mit Hinweis auf Migration 007), Löschen im
In-Memory-Store und die Migrationsdatei. Ohne Netz, ohne Zugangsdaten.

Ausführen:
    cd backend
    uv run python -m pytest tests/test_user_events.py -q -p no:cacheprovider
"""

import os
import sys

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

import services.user_events_service as svc  # noqa: E402
from database import in_memory_store  # noqa: E402
from routes.user_events import router as user_events_router  # noqa: E402

DEMO_1 = 1
DEMO_2 = 2
EVENTS = "/api/companies/{}/events"
EVENT = "/api/companies/{}/events/{}"
MIGRATION = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "migrations", "007_create_user_events.sql")


@pytest.fixture(scope="module")
def client(in_memory_db):
    app = FastAPI()
    app.include_router(user_events_router)
    return TestClient(app)


@pytest.fixture(autouse=True)
def clean_events():
    """Jeder Test beginnt ohne eigene Ereignisse im In-Memory-Store."""
    in_memory_store._TABLES.pop(svc.TABLE, None)
    yield
    in_memory_store._TABLES.pop(svc.TABLE, None)


def payload(**over):
    base = {"title": "Führungswechsel", "date_from": "2023-06", "date_to": "2023-08", "note": "Neue Geschäftsführung"}
    base.update(over)
    return base


class TestNormalize:

    def test_trims_and_defaults(self):
        out = svc.normalize_event({"title": "  Umzug  ", "date_from": " 2022-03 ", "date_to": "", "note": "   "})
        assert out == {"title": "Umzug", "date_from": "2022-03", "date_to": "2022-03", "note": None}

    def test_missing_date_to_equals_date_from(self):
        out = svc.normalize_event({"title": "x", "date_from": "2022-03"})
        assert out["date_to"] == "2022-03"

    @pytest.mark.parametrize("bad, message", [
        ({"title": "", "date_from": "2022-03"}, "Titel"),
        ({"title": None, "date_from": "2022-03"}, "Titel"),
        ({"title": "x" * (svc.TITLE_MAX + 1), "date_from": "2022-03"}, "höchstens"),
        ({"title": "x", "date_from": "2022-13"}, "Startmonat"),
        ({"title": "x", "date_from": "2022-3"}, "Startmonat"),
        ({"title": "x", "date_from": "03.2022"}, "Startmonat"),
        ({"title": "x", "date_from": "2022-03", "date_to": "2022-00"}, "Endmonat"),
        ({"title": "x", "date_from": "2022-03", "date_to": "2022-02"}, "nicht vor dem Startmonat"),
        ({"title": "x", "date_from": "2022-03", "note": "n" * (svc.NOTE_MAX + 1)}, "Vermerk"),
    ])
    def test_rejects_invalid_input_with_german_message(self, bad, message):
        with pytest.raises(ValueError) as err:
            svc.normalize_event(bad)
        assert message in str(err.value)

    def test_month_count(self):
        assert svc.month_count("2023-06", "2023-06") == 1
        assert svc.month_count("2023-06", "2023-08") == 3
        assert svc.month_count("2022-11", "2023-02") == 4


class TestRoutes:

    def test_empty_list_has_note(self, client):
        r = client.get(EVENTS.format(DEMO_1))
        assert r.status_code == 200
        body = r.json()
        assert body["company_id"] == DEMO_1
        assert body["events"] == []
        assert "keine Aussage über Ursachen" in body["note"]

    def test_create_returns_stored_event(self, client):
        r = client.post(EVENTS.format(DEMO_1), json=payload(title="  Führungswechsel ", note=""))
        assert r.status_code == 201, r.text
        ev = r.json()
        assert set(ev) == set(svc.FIELDS) | {"months"}
        assert ev["company_id"] == DEMO_1
        assert ev["title"] == "Führungswechsel"
        assert ev["note"] is None
        assert (ev["date_from"], ev["date_to"], ev["months"]) == ("2023-06", "2023-08", 3)
        assert isinstance(ev["id"], int)
        assert ev["created_at"] == ev["updated_at"]

    def test_date_to_defaults_to_date_from(self, client):
        r = client.post(EVENTS.format(DEMO_1), json={"title": "Standortschließung", "date_from": "2024-01"})
        assert r.status_code == 201
        assert r.json()["date_to"] == "2024-01"
        assert r.json()["months"] == 1

    def test_list_sorted_by_start_and_scoped_to_company(self, client):
        client.post(EVENTS.format(DEMO_1), json=payload(title="später", date_from="2024-02", date_to="2024-02"))
        client.post(EVENTS.format(DEMO_1), json=payload(title="früher", date_from="2022-05", date_to="2022-09"))
        client.post(EVENTS.format(DEMO_2), json=payload(title="andere Firma", date_from="2023-01", date_to="2023-01"))
        titles = [e["title"] for e in client.get(EVENTS.format(DEMO_1)).json()["events"]]
        assert titles == ["früher", "später"]
        assert [e["title"] for e in client.get(EVENTS.format(DEMO_2)).json()["events"]] == ["andere Firma"]

    @pytest.mark.parametrize("bad, message", [
        ({"date_from": "2023-06"}, "Titel"),
        ({"title": "x", "date_from": "2023-6"}, "Startmonat"),
        ({"title": "x", "date_from": "2023-06", "date_to": "2023-05"}, "nicht vor dem Startmonat"),
        ({"title": "x", "date_from": "2023-06", "note": "n" * 1001}, "Vermerk"),
    ])
    def test_invalid_input_is_400_with_message(self, client, bad, message):
        r = client.post(EVENTS.format(DEMO_1), json=bad)
        assert r.status_code == 400
        assert message in r.json()["detail"]
        assert client.get(EVENTS.format(DEMO_1)).json()["events"] == []

    def test_unknown_company_is_404(self, client):
        assert client.get(EVENTS.format(999)).status_code == 404
        assert client.post(EVENTS.format(999), json=payload()).status_code == 404
        assert client.put(EVENT.format(999, 1), json=payload()).status_code == 404
        assert client.delete(EVENT.format(999, 1)).status_code == 404

    def test_update_changes_fields_and_timestamp(self, client, monkeypatch):
        created = client.post(EVENTS.format(DEMO_1), json=payload()).json()
        monkeypatch.setattr(svc, "_now", lambda: "2030-01-01T00:00:00+00:00")
        r = client.put(EVENT.format(DEMO_1, created["id"]), json=payload(title="Umstrukturierung", date_from="2023-07", date_to="2023-07", note=None))
        assert r.status_code == 200, r.text
        ev = r.json()
        assert ev["id"] == created["id"]
        assert ev["title"] == "Umstrukturierung"
        assert (ev["date_from"], ev["date_to"], ev["months"]) == ("2023-07", "2023-07", 1)
        assert ev["note"] is None
        assert ev["created_at"] == created["created_at"]
        assert ev["updated_at"] == "2030-01-01T00:00:00+00:00"
        assert client.get(EVENTS.format(DEMO_1)).json()["events"][0]["title"] == "Umstrukturierung"

    def test_update_validates_and_keeps_old_values_on_error(self, client):
        created = client.post(EVENTS.format(DEMO_1), json=payload()).json()
        r = client.put(EVENT.format(DEMO_1, created["id"]), json=payload(title=""))
        assert r.status_code == 400
        assert client.get(EVENTS.format(DEMO_1)).json()["events"][0]["title"] == "Führungswechsel"

    def test_update_or_delete_of_foreign_or_unknown_event_is_404(self, client):
        created = client.post(EVENTS.format(DEMO_1), json=payload()).json()
        assert client.put(EVENT.format(DEMO_2, created["id"]), json=payload()).status_code == 404
        assert client.delete(EVENT.format(DEMO_2, created["id"])).status_code == 404
        assert client.put(EVENT.format(DEMO_1, created["id"] + 100), json=payload()).status_code == 404
        assert client.get(EVENTS.format(DEMO_1)).json()["events"][0]["id"] == created["id"]

    def test_delete_removes_event(self, client):
        a = client.post(EVENTS.format(DEMO_1), json=payload(title="a")).json()
        b = client.post(EVENTS.format(DEMO_1), json=payload(title="b", date_from="2024-01", date_to="2024-01")).json()
        r = client.delete(EVENT.format(DEMO_1, a["id"]))
        assert r.status_code == 200
        assert r.json() == {"deleted": a["id"], "company_id": DEMO_1}
        assert [e["id"] for e in client.get(EVENTS.format(DEMO_1)).json()["events"]] == [b["id"]]
        assert client.delete(EVENT.format(DEMO_1, a["id"])).status_code == 404

    def test_missing_table_is_503_with_migration_hint(self, client, monkeypatch):
        class PostgrestError(Exception):
            code = "42P01"

        original = in_memory_store.QueryBuilder.execute

        def execute(self):
            if self._table_name == svc.TABLE:
                raise PostgrestError('relation "public.user_events" does not exist')
            return original(self)

        monkeypatch.setattr(in_memory_store.QueryBuilder, "execute", execute)
        r = client.get(EVENTS.format(DEMO_1))
        assert r.status_code == 503
        assert "007_create_user_events.sql" in r.json()["detail"]
        assert client.post(EVENTS.format(DEMO_1), json=payload()).status_code == 503

    def test_missing_table_detection(self):
        class WithCode(Exception):
            code = "PGRST205"

        assert svc.is_missing_table_error(WithCode("x"))
        assert svc.is_missing_table_error(RuntimeError("Could not find the table 'public.user_events' in the schema cache"))
        assert not svc.is_missing_table_error(RuntimeError("timeout"))


class TestInMemoryDelete:

    def test_delete_removes_filtered_rows_and_returns_them(self, in_memory_db):
        tbl = "test_delete_rows"
        in_memory_store._TABLES[tbl] = [{"id": 1, "k": "a"}, {"id": 2, "k": "b"}, {"id": 3, "k": "a"}]
        try:
            result = in_memory_db.table(tbl).delete().eq("k", "a").execute()
            assert sorted(r["id"] for r in result.data) == [1, 3]
            assert [r["id"] for r in in_memory_store._TABLES[tbl]] == [2]
            assert in_memory_db.table("gibt_es_nicht").delete().eq("id", 1).execute().data == []
        finally:
            in_memory_store._TABLES.pop(tbl, None)


class TestMigrationFile:

    def test_migration_creates_table_with_constraints_and_policies(self):
        text = open(MIGRATION, encoding="utf-8").read()
        assert "CREATE TABLE IF NOT EXISTS user_events" in text
        assert "REFERENCES companies(id) ON DELETE CASCADE" in text
        assert "date_to >= date_from" in text
        assert f"BETWEEN 1 AND {svc.TITLE_MAX}" in text
        assert f"char_length(note) <= {svc.NOTE_MAX}" in text
        assert "ENABLE ROW LEVEL SECURITY" in text
        assert "service_role_all_user_events" in text and "public_read_user_events" in text
        assert svc.MIGRATION_FILE.endswith("007_create_user_events.sql")
