"""
Bestandstabelle von ``scripts/fetch_market_data.py --summary`` (Beleg für die
Abnahme von Inkrement 3): nur lesend, ohne Abruf und ohne Datenbank, nur
Zeiträume und Verfügbarkeit, keine Kurs- oder Kennzahlwerte.
"""

import hashlib
import os
import sys

import pytest

BACKEND = os.path.join(os.path.dirname(__file__), "..", "..")
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, BACKEND)
sys.path.insert(0, os.path.join(BACKEND, "scripts"))

import database.supabase_client as supabase_client  # noqa: E402
import fetch_market_data as script  # noqa: E402
from services import context_service  # noqa: E402
from _market_helpers import FETCHED_AT, raw_data  # noqa: E402

METADATA = {
    19: {"company_id": 19, "name": "SAP SE", "ticker": "SAP.DE", "ticker_scope": "eigene Aktie"},
    20: {"company_id": 20, "name": "NTT DATA SE", "ticker": "9432.T", "ticker_scope": "Konzernmutter"},
    26: {"company_id": 26, "name": "Carl Zeiss", "ticker": "AFX.DE", "ticker_scope": "Konzerngesellschaft"},
    4: {"company_id": 4, "name": "Open Grid Europe", "ticker": None, "ticker_scope": None},
}


def _digest(directory):
    return {p: hashlib.sha256(open(os.path.join(directory, p), "rb").read()).hexdigest()
            for p in sorted(os.listdir(directory))}


@pytest.fixture
def cache(tmp_path, monkeypatch):
    """Zwischenspeicher mit SAP.DE, 9432.T (ohne Kennzahlen) und einer Datei ohne Metadatei-Eintrag."""
    context_service.save_cached(context_service.build_record("SAP.DE", raw_data(), FETCHED_AT), tmp_path)
    context_service.save_cached(context_service.build_record(
        "9432.T", raw_data(currency="JPY", info={}, revenue=[]), FETCHED_AT), tmp_path)
    context_service.save_cached(context_service.build_record("OLD.DE", raw_data(), FETCHED_AT), tmp_path)

    def forbidden(*_args, **_kwargs):
        raise AssertionError("--summary darf weder abrufen noch die Datenbank lesen")

    monkeypatch.setattr(context_service, "fetch_raw", forbidden)
    monkeypatch.setattr(supabase_client, "get_supabase_client", forbidden)
    monkeypatch.setattr(script, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(script, "load_metadata", lambda: METADATA)
    return tmp_path


def test_rows_periods_currency_scope_and_metric_states(cache):
    rows = {r["Ticker"]: r for r in script.summary_rows()}
    sap = rows["SAP.DE"]
    assert (sap["Unternehmen (id)"], sap["ticker_scope"]) == ("SAP SE (19)", "eigene Aktie")
    # raw_data: Kurse 2023-12 bis 2024-03, der Monat des Abrufs (2024-03) fehlt.
    assert (sap["Erster Monat"], sap["Letzter Monat"], sap["Monate"], sap["Währung"]) == ("2023-12", "2024-02", "3", "EUR")
    assert sap["Marktkapitalisierung"] == "Stand 2024-10-01"
    assert sap["Mitarbeitende"] == "Stand 2024-03-15"
    assert sap["Umsatz je Geschäftsjahr"] == "2 GJ, Ende 2022-12 bis 2023-12"
    assert sap["Abruf"] == "2024-03-15"

    ntt = rows["9432.T"]
    assert (ntt["ticker_scope"], ntt["Währung"]) == ("Konzernmutter", "JPY")
    assert (ntt["Marktkapitalisierung"], ntt["Mitarbeitende"], ntt["Umsatz je Geschäftsjahr"]) == ("fehlt", "fehlt", "fehlt")


def test_missing_cache_and_file_without_metadata(cache):
    rows = script.summary_rows()
    assert [r["Ticker"] for r in rows] == ["SAP.DE", "9432.T", "AFX.DE", "OLD.DE"]
    zeiss = rows[2]
    assert (zeiss["ticker_scope"], zeiss["Erster Monat"], zeiss["Monate"]) == ("Konzerngesellschaft", "kein Zwischenspeicher", "0")
    assert zeiss["has_prices"] is False
    assert (rows[3]["Unternehmen (id)"], rows[3]["in_metadata"]) == ("nicht in der Metadatei", False)


def test_table_without_values_and_cache_unchanged(cache):
    before = _digest(cache)
    table = script.format_summary(script.summary_rows())
    assert _digest(cache) == before
    assert table.splitlines()[0] == "| " + " | ".join(script.SUMMARY_COLUMNS) + " |"
    for value in ("100.0", "101.2", "99.5", "2500000000", "2.5e", "1234", "500000000", "5.0e"):
        assert value not in table


def test_main_exit_codes(cache, capsys):
    assert script.main(["--summary"]) == 1  # AFX.DE ohne Zwischenspeicher
    assert "| SAP SE (19) | SAP.DE |" in capsys.readouterr().out
    context_service.save_cached(context_service.build_record("AFX.DE", raw_data(), FETCHED_AT), cache)
    assert script.main(["--summary"]) == 0
    with pytest.raises(SystemExit):
        script.main(["--summary", "--news"])
