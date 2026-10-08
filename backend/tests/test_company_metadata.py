"""
Tests für die Unternehmens-Metadaten (Prüfpunkt 7 des Fundaments).

Abgedeckt (ohne Netzwerk, ohne gehostete DB):
- Struktur und erlaubte Werte von backend/data/company_metadata.json
- normalize_company_name (Whitespace, Zeilenumbrüche, Großschreibung)
- CompanyCreate-Validierung (ticker/isin, peer_group)
- get_companies / create_company gegen den In-Memory-Client
- Fallback von get_companies auf "id,name" bei fehlenden Spalten (42703)
- select/update der Metadaten-Spalten im In-Memory-Store (Demo-Modus)

Ausführen (aus dem backend-Verzeichnis):
    uv run python -m pytest tests/test_company_metadata.py -q -p no:cacheprovider
"""

import json
import logging
import os
import re
import sys

import pytest
from pydantic import ValidationError

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import routes.companies as companies_module  # noqa: E402
from database import in_memory_store  # noqa: E402
from database.in_memory_store import get_in_memory_client  # noqa: E402
from services.context_service import TICKER_SCOPES  # noqa: E402
from routes.companies import (  # noqa: E402
    COMPANY_META_COLUMNS,
    PEER_GROUPS,
    CompanyCreate,
    create_company,
    get_companies,
    normalize_company_name,
)

BACKEND_DIR = os.path.join(os.path.dirname(__file__), "..")
DATA_PATH = os.path.join(BACKEND_DIR, "data", "company_metadata.json")
MIGRATION_PATH = os.path.join(BACKEND_DIR, "migrations", "006_add_company_metadata.sql")

# IDs aller realen Unternehmen in der gehosteten DB (ohne Demo 1/2/3 = 10, 17, 18)
EXPECTED_IDS = {3, 4, 5, 6, 7, 8, 9, 13, 14, 15, 16, 19, 20, 21, 22, 23, 24, 25,
                26, 27, 28, 29, 30, 31, 32, 33}
REQUIRED_FIELDS = {
    "company_id", "name", "name_normalized", "ticker", "ticker_scope", "isin", "sector",
    "peer_group", "news_term", "news_exclude", "news_term_confirmed", "eqs", "listed", "verification", "note",
}
VERIFICATION_FIELDS = {"ticker_checked_with", "rows", "isin_source", "checked_at"}


@pytest.fixture(scope="module")
def entries() -> list[dict]:
    with open(DATA_PATH, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    assert isinstance(data, list)
    return data


@pytest.fixture
def in_memory(monkeypatch):
    """Lenkt routes.companies auf den In-Memory-Client um."""
    client = get_in_memory_client()
    monkeypatch.setattr(companies_module, "get_supabase_client", lambda: client)
    monkeypatch.setattr(companies_module, "_meta_columns_warning_logged", False)
    return client


# ---------------------------------------------------------------------------
# company_metadata.json
# ---------------------------------------------------------------------------

def test_metadata_json_has_26_real_companies(entries):
    assert len(entries) == 26
    ids = [e["company_id"] for e in entries]
    assert len(set(ids)) == 26, "company_id muss eindeutig sein"
    assert set(ids) == EXPECTED_IDS
    assert not any("demo" in e["name"].casefold() for e in entries), "Demo-Unternehmen sind ausgeschlossen"


def test_metadata_json_structure_and_types(entries):
    for e in entries:
        assert set(e) == REQUIRED_FIELDS, f"Felder passen nicht für {e.get('name')!r}"
        assert isinstance(e["company_id"], int)
        assert isinstance(e["name"], str) and e["name"].strip()
        assert isinstance(e["name_normalized"], str)
        assert isinstance(e["sector"], str) and e["sector"].strip()
        assert isinstance(e["listed"], bool)
        assert isinstance(e["note"], str)
        for key in ("ticker", "isin"):
            assert e[key] is None or (isinstance(e[key], str) and e[key].strip())
        # ticker_scope (Inkrement 3, E15): einer der erlaubten Werte; None nur ohne Ticker
        assert e["ticker_scope"] in TICKER_SCOPES + (None,)
        if e["ticker"] is None:
            assert e["ticker_scope"] is None
        else:
            assert e["ticker_scope"] in TICKER_SCOPES, f"{e['name']}: ticker_scope fehlt"
        assert set(e["verification"]) == VERIFICATION_FIELDS
        v = e["verification"]
        assert v["ticker_checked_with"] in ("yfinance history 2y", None)
        assert isinstance(v["rows"], int) and v["rows"] >= 0
        assert v["isin_source"] in ("yfinance", "unverified", None)
        assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", v["checked_at"])


def test_metadata_json_name_normalization(entries):
    for e in entries:
        assert e["name_normalized"] == " ".join(e["name"].split())
        assert e["name_normalized"] == normalize_company_name(e["name"])
    # Seit scripts/fix_company_names.py --apply (2026-10-03) sind die DB-Namen bereinigt;
    # name und name_normalized müssen daher für alle Einträge übereinstimmen.
    by_id = {e["company_id"]: e for e in entries}
    for entry in by_id.values():
        assert entry["name"] == " ".join(entry["name"].split())
        assert entry["name"] == entry["name_normalized"]
    assert by_id[7]["name"] == "E.ON"
    assert by_id[20]["name"] == "NTT DATA SE"
    assert by_id[9]["name"] == "Thyssengas GmbH"
    assert by_id[13]["name"] == "Universität Duisburg-Essen"


def test_metadata_json_allowed_values_and_consistency(entries):
    for e in entries:
        assert e["peer_group"] in PEER_GROUPS
        assert e["peer_group"] != "Demo"
        v = e["verification"]
        if e["listed"]:
            assert e["ticker"] is not None
            assert e["ticker"] == e["ticker"].strip().upper()
            assert e["peer_group"] in ("Börsennotiert DE", "Börsennotiert Ausland")
            assert v["ticker_checked_with"] == "yfinance history 2y"
            assert v["rows"] > 0, f"{e['name_normalized']}: Ticker {e['ticker']} nicht verifiziert"
            assert v["isin_source"] in ("yfinance", "unverified")
        else:
            assert e["ticker"] is None and e["isin"] is None
            assert e["peer_group"] == "Nicht börsennotiert"
            assert v["rows"] == 0
        if e["isin"] is None:
            assert v["isin_source"] != "yfinance"
        else:
            assert re.fullmatch(r"[A-Z]{2}[A-Z0-9]{9}\d", e["isin"])
            assert v["isin_source"] == "yfinance"


def test_metadata_json_known_assignments(entries):
    by_id = {e["company_id"]: e for e in entries}
    assert by_id[3]["ticker"] == "TKA.DE" and by_id[3]["peer_group"] == "Börsennotiert DE"
    assert by_id[7]["ticker"] == "EOAN.DE"
    assert by_id[8]["ticker"] == "RWE.DE"
    assert by_id[19]["ticker"] == "SAP.DE"
    assert by_id[28]["ticker"] == "DTE.DE"
    assert by_id[20]["peer_group"] == "Börsennotiert Ausland"
    assert by_id[20]["ticker"].endswith(".T")
    assert by_id[26]["ticker"] == "AFX.DE" and "Carl Zeiss" in by_id[26]["note"]
    for cid in (4, 5, 6, 9, 13, 14, 15, 16):
        assert by_id[cid]["listed"] is False
    for cid in (13, 14, 15, 16):
        assert by_id[cid]["sector"] == "Hochschule"
    listed_de = [e for e in entries if e["peer_group"] == "Börsennotiert DE"]
    assert len(listed_de) >= 12


def test_migration_006_defines_columns_and_comments():
    with open(MIGRATION_PATH, "r", encoding="utf-8") as fh:
        sql = fh.read()
    for col in COMPANY_META_COLUMNS:
        assert re.search(rf"ADD COLUMN IF NOT EXISTS {col} TEXT", sql)
        assert f"COMMENT ON COLUMN companies.{col}" in sql
    for value in PEER_GROUPS:
        assert value in sql


# ---------------------------------------------------------------------------
# normalize_company_name
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "raw, expected",
    [
        ("E.ON\n", "E.ON"),
        ("NTT  DATA SE", "NTT DATA SE"),
        ("  Thyssengas  GmbH  ", "Thyssengas GmbH"),
        ("Universität\t Duisburg-Essen", "Universität Duisburg-Essen"),
        ("\n\nRWE\r\n", "RWE"),
        ("demo 1", "Demo 1"),
        ("1 und 1", "1 und 1"),
        ("   ", ""),
        ("", ""),
    ],
)
def test_normalize_company_name(raw, expected):
    assert normalize_company_name(raw) == expected


# ---------------------------------------------------------------------------
# CompanyCreate
# ---------------------------------------------------------------------------

def test_company_create_defaults_to_none():
    c = CompanyCreate(name="Firma")
    assert (c.ticker, c.isin, c.sector, c.peer_group) == (None, None, None, None)


def test_company_create_normalizes_ticker_and_isin():
    c = CompanyCreate(name="Firma", ticker="  tka.de ", isin=" de0007500001 ", sector="  Stahl /  Industrie ")
    assert c.ticker == "TKA.DE"
    assert c.isin == "DE0007500001"
    assert c.sector == "Stahl / Industrie"


def test_company_create_empty_strings_become_none():
    c = CompanyCreate(name="Firma", ticker="   ", isin="", sector=" ", peer_group="")
    assert (c.ticker, c.isin, c.sector, c.peer_group) == (None, None, None, None)


@pytest.mark.parametrize("value", PEER_GROUPS)
def test_company_create_accepts_allowed_peer_groups(value):
    assert CompanyCreate(name="Firma", peer_group=value).peer_group == value


@pytest.mark.parametrize("value", ["DAX", "börsennotiert de", "Boersennotiert DE", "demo"])
def test_company_create_rejects_unknown_peer_group(value):
    with pytest.raises(ValidationError) as excinfo:
        CompanyCreate(name="Firma", peer_group=value)
    assert "peer_group" in str(excinfo.value)


def test_company_create_rejects_non_string_ticker():
    with pytest.raises(ValidationError):
        CompanyCreate(name="Firma", ticker=123)


# ---------------------------------------------------------------------------
# get_companies / create_company gegen In-Memory-Client
# ---------------------------------------------------------------------------

def test_get_companies_returns_metadata_and_review_count(in_memory):
    data = get_companies()
    assert [row["name"] for row in data] == ["Demo 1", "Demo 2", "Demo 3"]
    for row in data:
        assert isinstance(row["id"], str)
        assert row["review_count"] > 0
        for col in COMPANY_META_COLUMNS:
            assert col in row
        assert row["ticker"] is None and row["isin"] is None
        assert row["sector"] == "Demo" and row["peer_group"] == "Demo"


class _FakeAPIError(Exception):
    """Nachbildung eines PostgREST-APIError bei fehlender Spalte."""

    def __init__(self):
        super().__init__("{'message': 'column companies.ticker does not exist', 'code': '42703'}")
        self.code = "42703"


class _MissingColumnTable:
    def __init__(self, inner_qb, table_name):
        self._qb = inner_qb
        self._name = table_name

    def select(self, cols, **kwargs):
        if self._name == "companies" and any(c in cols for c in COMPANY_META_COLUMNS):
            raise _FakeAPIError()
        return self._qb.select(cols, **kwargs)

    def __getattr__(self, item):
        return getattr(self._qb, item)


class _MissingColumnClient:
    """In-Memory-Client, der sich wie eine DB ohne Migration 006 verhält."""

    def __init__(self, inner):
        self._inner = inner
        self.selects: list[str] = []

    def table(self, name):
        qb = self._inner.table(name)
        wrapper = _MissingColumnTable(qb, name)
        original_select = wrapper.select

        def recording_select(cols, **kwargs):
            if name == "companies":
                self.selects.append(cols)
            return original_select(cols, **kwargs)

        wrapper.select = recording_select  # type: ignore[attr-defined]
        return wrapper

    def rpc(self, func, params):
        return self._inner.rpc(func, params)


def test_get_companies_falls_back_without_migration_and_warns_once(monkeypatch, caplog):
    fake = _MissingColumnClient(get_in_memory_client())
    monkeypatch.setattr(companies_module, "get_supabase_client", lambda: fake)
    monkeypatch.setattr(companies_module, "_meta_columns_warning_logged", False)

    with caplog.at_level(logging.WARNING, logger="routes.companies"):
        first = get_companies()
        second = get_companies()

    assert len(first) == 3 and len(second) == 3
    for row in first:
        assert row["review_count"] > 0
        for col in COMPANY_META_COLUMNS:
            assert row[col] is None
    assert fake.selects[:2] == [companies_module.COMPANY_SELECT_FULL, companies_module.COMPANY_SELECT_BASIC]
    warnings = [r for r in caplog.records if "006_add_company_metadata" in r.getMessage()]
    assert len(warnings) == 1, "Warnung muss genau einmal geloggt werden"


def test_create_company_returns_existing_case_insensitive(in_memory):
    result = create_company(CompanyCreate(name="  demo  1 ", ticker="XYZ.DE"))
    assert result["id"] == 1
    assert result["name"] == "Demo 1"


def test_create_company_inserts_only_non_null_metadata(in_memory):
    companies = in_memory_store._TABLES["companies"]
    before = len(companies)
    try:
        created = create_company(CompanyCreate(
            name=" neue   firma\n", ticker=" nfa.de ", peer_group="Börsennotiert DE", isin="", sector=None,
        ))
        assert created["name"] == "Neue firma"
        assert created["ticker"] == "NFA.DE"
        assert created["peer_group"] == "Börsennotiert DE"
        assert created["id"] == 4
        assert "isin" not in created and "sector" not in created
        assert len(companies) == before + 1
        # Metadaten sind anschließend über select abrufbar
        row = in_memory.table("companies").select("id,name,ticker,isin,sector,peer_group").eq("id", 4).execute().data[0]
        assert row == {"id": 4, "name": "Neue firma", "ticker": "NFA.DE", "isin": None,
                       "sector": None, "peer_group": "Börsennotiert DE"}
    finally:
        del companies[before:]


def test_create_company_rejects_empty_name(in_memory):
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as excinfo:
        create_company(CompanyCreate(name="  \n "))
    assert excinfo.value.status_code == 400


# ---------------------------------------------------------------------------
# In-Memory-Store: select/update der Metadaten-Spalten (Demo-Modus)
# ---------------------------------------------------------------------------

def test_in_memory_select_metadata_columns():
    client = get_in_memory_client()
    rows = client.table("companies").select("id,name,ticker,isin,sector,peer_group").order("name").execute().data
    assert len(rows) == 3
    assert rows[0] == {"id": 1, "name": "Demo 1", "ticker": None, "isin": None, "sector": "Demo", "peer_group": "Demo"}


def test_in_memory_update_metadata_columns():
    client = get_in_memory_client()
    try:
        res = client.table("companies").update({"sector": "Test", "ticker": "TST.DE"}).eq("id", 2).execute()
        assert len(res.data) == 1 and res.data[0]["sector"] == "Test"
        row = client.table("companies").select("id,sector,ticker").eq("id", 2).execute().data[0]
        assert row == {"id": 2, "sector": "Test", "ticker": "TST.DE"}
        untouched = client.table("companies").select("sector").eq("id", 1).execute().data[0]
        assert untouched["sector"] == "Demo"
    finally:
        client.table("companies").update({"sector": "Demo", "ticker": None}).eq("id", 2).execute()


def test_ticker_scope_decisions(entries):
    """Sonderfälle der Metadatei: NTT DATA SE zeigt die Konzernmutter (E6/E15), Carl Zeiss die
    börsennotierte Konzerngesellschaft Carl Zeiss Meditec AG (Entscheidung D2, 2026-10-08)."""
    by_id = {e["company_id"]: e for e in entries}
    assert (by_id[20]["ticker"], by_id[20]["ticker_scope"]) == ("9432.T", "Konzernmutter")
    assert (by_id[26]["ticker"], by_id[26]["ticker_scope"]) == ("AFX.DE", "Konzerngesellschaft")
    assert "Gesamtkonzern" in by_id[26]["note"]
    assert sum(1 for e in entries if e["ticker_scope"] == "eigene Aktie") == 15


def test_news_search_fields(entries):
    """Suchbegriff und Ausschlussbegriffe für die Belege (Inkrement 4): optional, Vorschläge
    sind als unbestätigt gekennzeichnet (news_term_confirmed false), bis der Autor sie prüft."""
    for e in entries:
        assert e["news_term"] is None or (isinstance(e["news_term"], str) and e["news_term"].strip())
        assert isinstance(e["news_exclude"], list) and all(isinstance(x, str) and x.strip() for x in e["news_exclude"])
        assert isinstance(e["news_term_confirmed"], bool)
    by_id = {e["company_id"]: e for e in entries}
    assert by_id[26]["news_term"] and by_id[26]["news_exclude"], "Carl Zeiss: mehrdeutiger Name braucht Vorschlag"
    assert by_id[28]["news_term"] == '"Deutsche Telekom"'
    assert all(not e["news_term_confirmed"] for e in entries if e["news_term"] or e["news_exclude"]), \
        "Vorschläge gelten erst nach Bestätigung durch den Autor"


def test_eqs_issuer_fields(entries):
    """EQS-companyUUID je Emittent (Inkrement 4, Schritt 5): für alle Unternehmen mit Ticker
    außer NTT DATA SE (nicht bei EQS) und für Compugroup (ehemals notiert); unbestätigt, bis
    der Autor sie prüft."""
    for e in entries:
        eqs = e["eqs"]
        assert eqs is None or (
            set(eqs) == {"uuid", "company_name", "isin", "found_at", "confirmed", "note"}
            and re.fullmatch(r"[0-9a-f-]{36}", eqs["uuid"]) and eqs["company_name"] and isinstance(eqs["confirmed"], bool)
        )
    by_id = {e["company_id"]: e for e in entries}
    assert by_id[20]["eqs"] is None, "NTT DATA: kein Emittent bei EQS"
    assert by_id[26]["eqs"]["company_name"] == "Carl Zeiss Meditec AG"
    assert by_id[27]["eqs"] and "ehemals" in by_id[27]["eqs"]["note"]
    with_ticker = [e for e in entries if e["ticker"] and e["company_id"] != 20]
    assert all(e["eqs"] for e in with_ticker)
    assert all(not e["eqs"]["confirmed"] for e in entries if e["eqs"]), "UUIDs gelten erst nach Bestätigung"
