"""
Tests für services/context_service.py (Inkrement 3, E15): Monatsreihe,
Kennzahlen, Zwischenspeicher, Ticker mit Rückfall auf die Metadatei und
Verhalten zur Laufzeit. Ohne Netzwerk: Abruf nachgebildet, Speicher in tmp_path.

Ausführen (aus dem backend-Verzeichnis):
    uv run python -m pytest tests/market -q -p no:cacheprovider
"""

import json
import os
import sys
from datetime import datetime, timezone

import pytest

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from _market_helpers import FETCHED_AT, FakeFetcher, raw_data  # noqa: E402
from services import context_service as cs  # noqa: E402


# ---------------------------------------------------------------------------
# Monatsreihe
# ---------------------------------------------------------------------------

class TestMonthlyCloses:

    def test_one_close_per_month_sorted_and_rounded(self):
        history = [
            {"date": "2024-02-01", "close": 99.5},
            {"date": "2024-01-01", "close": 101.234567},
            {"date": "2023-12-01", "close": 100.0},
        ]
        assert cs.monthly_closes(history, FETCHED_AT) == [
            {"period": "2023-12", "close": 100.0},
            {"period": "2024-01", "close": 101.2346},
            {"period": "2024-02", "close": 99.5},
        ]

    def test_last_bar_of_a_month_wins(self):
        """yfinance hängt teils einen Balken mit Tagesdatum an; es zählt der letzte."""
        history = [{"date": "2024-01-01", "close": 10.0}, {"date": "2024-01-31", "close": 12.0}]
        assert cs.monthly_closes(history, FETCHED_AT) == [{"period": "2024-01", "close": 12.0}]

    def test_running_month_and_later_are_dropped(self):
        history = [{"date": "2024-02-01", "close": 1.0}, {"date": "2024-03-01", "close": 2.0},
                   {"date": "2024-04-01", "close": 3.0}]
        assert [p["period"] for p in cs.monthly_closes(history, FETCHED_AT)] == ["2024-02"]

    def test_missing_and_invalid_values_are_skipped(self):
        history = [{"date": "2024-01-01", "close": float("nan")}, {"date": "2024-02-01", "close": None},
                   {"date": "kaputt", "close": 5.0}, {"date": "2023-11-01", "close": "7.5"}]
        assert cs.monthly_closes(history, FETCHED_AT) == [{"period": "2023-11", "close": 7.5}]


# ---------------------------------------------------------------------------
# Datensatz und Kennzahlen
# ---------------------------------------------------------------------------

class TestBuildRecord:

    def test_record_fields(self):
        record = cs.build_record("TST.DE", raw_data(), FETCHED_AT)
        assert set(record) == {"ticker", "ticker_name", "currency", "fetched_at", "source", "adjustment",
                               "prices", "metrics", "analysts", "earnings"}
        assert record["ticker"] == "TST.DE" and record["currency"] == "EUR"
        assert record["fetched_at"] == "2024-03-15T12:00:00+00:00"
        assert record["source"] == "Yahoo Finance über yfinance 0.0-test"
        assert [p["period"] for p in record["prices"]] == ["2023-12", "2024-01", "2024-02"]

    def test_metrics_values_units_and_dates(self):
        metrics = cs.build_record("TST.DE", raw_data(), FETCHED_AT)["metrics"]
        assert metrics["market_cap"] == {"value": 2.5e9, "unit": "EUR", "as_of": "2024-10-01", "basis": "aktuell"}
        assert metrics["employees"] == {"value": 1234, "unit": "Personen", "as_of": "2024-03-15", "basis": "aktuell"}
        assert metrics["revenue"] == [
            {"value": 4.0e8, "unit": "EUR", "fiscal_year_end": "2022-12-31", "basis": "geschaeftsjahr"},
            {"value": 5.0e8, "unit": "EUR", "fiscal_year_end": "2023-12-31", "basis": "geschaeftsjahr"},
        ]

    def test_missing_metrics_stay_empty(self):
        """Fehlende Werte werden nicht geschätzt: None bzw. Jahr fehlt."""
        raw = raw_data(info={"currency": "EUR"}, revenue=[
            {"period_end": "2021-12-31", "value": float("nan")},
            {"period_end": "2022-12-31", "value": None},
            {"period_end": "2023-12-31", "value": 7.0e8},
        ])
        metrics = cs.build_record("TST.DE", raw, FETCHED_AT)["metrics"]
        assert metrics["market_cap"] is None and metrics["employees"] is None
        assert [r["fiscal_year_end"] for r in metrics["revenue"]] == ["2023-12-31"]

    def test_market_cap_without_quote_time_uses_fetch_date(self):
        raw = raw_data(info={"marketCap": 1e9, "currency": "JPY"}, currency="JPY")
        assert cs.build_record("1.T", raw, FETCHED_AT)["metrics"]["market_cap"]["as_of"] == "2024-03-15"

    def test_revenue_in_reporting_currency(self):
        info = {"marketCap": 1e9, "currency": "USD", "financialCurrency": "EUR"}
        metrics = cs.build_record("X", raw_data(info=info, currency="USD"), FETCHED_AT)["metrics"]
        assert metrics["market_cap"]["unit"] == "USD"
        assert {r["unit"] for r in metrics["revenue"]} == {"EUR"}


# ---------------------------------------------------------------------------
# Zwischenspeicher
# ---------------------------------------------------------------------------

class TestCache:

    def test_save_and_load_roundtrip(self, tmp_path):
        record = cs.build_record("9432.T", raw_data(currency="JPY"), FETCHED_AT)
        path = cs.save_cached(record, tmp_path)
        assert path == tmp_path / "9432.T.json"
        assert cs.load_cached("9432.T", tmp_path) == record
        assert not [p for p in tmp_path.iterdir() if p.name.endswith(".tmp")], "keine Reste der atomaren Schreibweise"

    def test_missing_corrupt_or_foreign_file_reads_as_none(self, tmp_path):
        assert cs.load_cached("NONE.DE", tmp_path) is None
        (tmp_path / "BAD.DE.json").write_text("{kaputt", encoding="utf-8")
        assert cs.load_cached("BAD.DE", tmp_path) is None
        (tmp_path / "OTHER.DE.json").write_text(json.dumps({"ticker": "SAP.DE"}), encoding="utf-8")
        assert cs.load_cached("OTHER.DE", tmp_path) is None

    def test_fetch_and_store_writes_file(self, tmp_path):
        fetcher = FakeFetcher()
        record = cs.fetch_and_store("TST.DE", fetcher=fetcher, cache_dir=tmp_path)
        assert fetcher.calls == ["TST.DE"]
        assert json.loads((tmp_path / "TST.DE.json").read_text(encoding="utf-8")) == record

    def test_fetch_without_prices_is_not_stored(self, tmp_path):
        with pytest.raises(ValueError, match="keine Monatskurse"):
            cs.fetch_and_store("GONE.DE", fetcher=FakeFetcher(raw_data(history=[])), cache_dir=tmp_path)
        assert not (tmp_path / "GONE.DE.json").exists()


# ---------------------------------------------------------------------------
# Ticker
# ---------------------------------------------------------------------------

class TestTicker:

    def test_ticker_from_database(self, fake_db):
        info = cs.company_ticker_info(3)
        assert info["ticker"] == "TKA.DE" and info["ticker_source"] == "db"
        assert info["ticker_scope"] == "eigene Aktie"
        assert cs.ticker_for_company(3) == "TKA.DE"

    def test_fallback_to_metadata_when_value_missing(self, fake_db):
        info = cs.company_ticker_info(19)
        assert info["ticker"] == "SAP.DE" and info["ticker_source"] == "metadata"
        assert info["peer_group"] == "Börsennotiert DE", "peer_group aus der Metadatei, wenn die DB keinen Wert hat"

    def test_fallback_to_metadata_when_columns_missing(self, fake_db):
        fake_db.missing_columns = True
        info = cs.company_ticker_info(3)
        assert info["ticker"] == "TKA.DE" and info["ticker_source"] == "metadata"
        assert fake_db.queries == ["id,name,ticker,peer_group", "id,name"]

    def test_no_fallback_when_names_differ(self, fake_db):
        """Andere Zeile unter derselben ID (z. B. Demo 3 im In-Memory-Store): kein Ticker."""
        fake_db.rows.append({"id": 8, "name": "Nicht RWE", "ticker": None, "peer_group": None})
        info = cs.company_ticker_info(8)
        assert info["ticker"] is None and info["ticker_scope"] is None

    def test_parent_company_scope(self, fake_db):
        assert cs.company_ticker_info(20)["ticker_scope"] == "Konzernmutter"

    def test_group_company_scope(self, fake_db):
        """Carl Zeiss: Ticker der börsennotierten Konzerngesellschaft (Entscheidung D2, 2026-10-08)."""
        info = cs.company_ticker_info(26)
        assert (info["ticker"], info["ticker_scope"], info["ticker_source"]) == ("AFX.DE", "Konzerngesellschaft", "db")
        assert set(cs.TICKER_SCOPES) == {"eigene Aktie", "Konzernmutter", "Konzerngesellschaft"}

    def test_unknown_company(self, fake_db):
        assert cs.company_ticker_info(999) is None
        assert cs.ticker_for_company(999) is None

    def test_no_ticker(self, fake_db):
        info = cs.company_ticker_info(4)
        assert info["ticker"] is None and info["peer_group"] == "Nicht börsennotiert"


# ---------------------------------------------------------------------------
# Laufzeit: Zwischenspeicher, Live-Abruf, Fehlschlag, MARKET_LIVE_FETCH
# ---------------------------------------------------------------------------

class TestRuntime:

    def test_cache_hit_does_not_fetch(self, market):
        cs.save_cached(cs.build_record("TST.DE", raw_data(), FETCHED_AT))
        record, reason = cs.market_record("TST.DE")
        assert reason is None and record["ticker"] == "TST.DE"
        assert market.fetcher.calls == []

    def test_cache_miss_fetches_once_and_stores(self, market):
        record, reason = cs.market_record("TST.DE")
        assert reason is None and record["prices"]
        assert (market.cache_dir / "TST.DE.json").exists()
        cs.market_record("TST.DE")
        assert market.fetcher.calls == ["TST.DE"], "zweiter Aufruf aus dem Zwischenspeicher"

    def test_failed_fetch_gives_reason_and_is_not_retried_at_once(self, market):
        market.fetcher.error = ConnectionError("kein Netz")
        record, reason = cs.market_record("TST.DE")
        assert record is None and "konnten nicht abgerufen werden" in reason and "kein Netz" in reason
        assert not (market.cache_dir / "TST.DE.json").exists()
        assert cs.market_record("TST.DE") == (None, reason)
        assert market.fetcher.calls == ["TST.DE"]

    def test_live_fetch_disabled(self, market, monkeypatch):
        monkeypatch.setenv(cs.LIVE_FETCH_ENV, "0")
        record, reason = cs.market_record("TST.DE")
        assert record is None and "MARKET_LIVE_FETCH=0" in reason
        assert market.fetcher.calls == []

    def test_live_fetch_disabled_still_reads_cache(self, market, monkeypatch):
        monkeypatch.setenv(cs.LIVE_FETCH_ENV, "0")
        cs.save_cached(cs.build_record("TST.DE", raw_data(), FETCHED_AT))
        record, reason = cs.market_record("TST.DE")
        assert reason is None and record is not None

    def test_company_market_filters_period(self, market, fake_db):
        cs.save_cached(cs.build_record("TKA.DE", raw_data(), datetime(2024, 5, 1, tzinfo=timezone.utc)))
        result = cs.company_market(3, start="2024-01", end="2024-02")
        assert result["available"] is True
        assert [p["period"] for p in result["prices"]] == ["2024-01", "2024-02"]

    def test_company_market_invalid_period(self, market, fake_db):
        with pytest.raises(ValueError):
            cs.company_market(3, start="2024-13")
        with pytest.raises(ValueError):
            cs.company_market(3, start="2024-05", end="2024-01")
