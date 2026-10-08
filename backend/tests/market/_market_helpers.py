"""
Hilfen der Kurs-Tests (Inkrement 3): feste Zeilen der Tabelle ``companies``,
ein nachgebildeter Supabase-Client und nachgebildete yfinance-Rohdaten.
"""

from datetime import datetime, timezone


# Zeilen wie in der gehosteten DB (Auszug) plus ein Unternehmen, dessen
# Ticker nur in der Metadatei steht (SAP SE ohne DB-Wert).
COMPANIES = [
    {"id": 3, "name": "Thyssenkrupp", "ticker": "TKA.DE", "peer_group": "Börsennotiert DE"},
    {"id": 4, "name": "Open Grid Europe", "ticker": None, "peer_group": "Nicht börsennotiert"},
    {"id": 10, "name": "Demo 1", "ticker": None, "peer_group": "Demo"},
    {"id": 19, "name": "SAP SE", "ticker": None, "peer_group": None},
    {"id": 20, "name": "NTT DATA SE", "ticker": "9432.T", "peer_group": "Börsennotiert Ausland"},
    {"id": 26, "name": "Carl Zeiss", "ticker": "AFX.DE", "peer_group": "Börsennotiert DE"},
]


class MissingColumnError(Exception):
    code = "42703"


class _Query:
    def __init__(self, rows, columns, missing_columns):
        self._rows = rows
        self._columns = [c.strip() for c in columns.split(",")]
        self._missing = missing_columns
        self._filters = []

    def eq(self, column, value):
        self._filters.append((column, value))
        return self

    def execute(self):
        if self._missing and {"ticker", "peer_group"} & set(self._columns):
            raise MissingColumnError("column companies.ticker does not exist (42703)")
        rows = [r for r in self._rows if all(r.get(c) == v for c, v in self._filters)]
        return type("Result", (), {"data": [{c: r.get(c) for c in self._columns} for r in rows]})()


class FakeCompaniesClient:
    def __init__(self, rows, missing_columns=False):
        self.rows = rows
        self.missing_columns = missing_columns
        self.queries = []

    def table(self, name):
        assert name == "companies", "Der Kursdienst liest nur companies"
        client = self

        class _Table:
            def select(self, columns):
                client.queries.append(columns)
                return _Query(client.rows, columns, client.missing_columns)

            def __getattr__(self, attr):  # insert/update/delete gibt es hier nicht
                raise AssertionError(f"Schreibzugriff {attr} auf companies")

        return _Table()


def raw_data(history=None, info=None, revenue=None, currency="EUR", name="Test AG"):
    """Nachgebildete Rohdaten wie aus ``context_service.fetch_raw``."""
    return {
        "currency": currency,
        "name": name,
        "history": history if history is not None else [
            {"date": "2023-12-01", "close": 100.0},
            {"date": "2024-01-01", "close": 101.234567},
            {"date": "2024-02-01", "close": 99.5},
            {"date": "2024-03-01", "close": 103.0},
        ],
        "info": info if info is not None else {
            "marketCap": 2.5e9, "currency": currency, "regularMarketTime": 1727740800,
            "fullTimeEmployees": 1234, "financialCurrency": currency,
        },
        "revenue": revenue if revenue is not None else [
            {"period_end": "2023-12-31", "value": 5.0e8},
            {"period_end": "2022-12-31", "value": 4.0e8},
        ],
        "yfinance_version": "0.0-test",
    }


class FakeFetcher:
    """Zählt Aufrufe; liefert Rohdaten oder löst die übergebene Ausnahme aus."""

    def __init__(self, result=None, error=None):
        self.result = result if result is not None else raw_data()
        self.error = error
        self.calls = []

    def __call__(self, ticker):
        self.calls.append(ticker)
        if self.error is not None:
            raise self.error
        return self.result


FETCHED_AT = datetime(2024, 3, 15, 12, 0, tzinfo=timezone.utc)
