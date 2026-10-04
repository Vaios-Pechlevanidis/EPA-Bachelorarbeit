"""
Fixtures der Kurs-Tests (Inkrement 3, E15). Ohne Netzwerk und ohne gehostete DB:

- ``fake_db`` ersetzt ``database.supabase_client.get_supabase_client`` durch
  einen kleinen Client mit festen Zeilen der Tabelle ``companies``; mit
  ``missing_columns=True`` meldet er wie PostgREST den Fehler 42703, sobald
  ``ticker`` oder ``peer_group`` abgefragt werden.
- ``market`` lenkt Zwischenspeicher (``tmp_path``) und Abruf (``FakeFetcher``)
  von ``services.context_service`` um und leert die Liste fehlgeschlagener Abrufe.
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import database.supabase_client as supabase_client  # noqa: E402
from services import context_service  # noqa: E402

sys.path.insert(0, os.path.dirname(__file__))
from _market_helpers import COMPANIES, FakeCompaniesClient, FakeFetcher  # noqa: E402


@pytest.fixture
def fake_db(monkeypatch):
    client = FakeCompaniesClient([dict(r) for r in COMPANIES])
    monkeypatch.setattr(supabase_client, "get_supabase_client", lambda: client)
    return client


@pytest.fixture
def market(monkeypatch, tmp_path):
    """Zwischenspeicher in tmp_path, Abruf nachgebildet, Live-Abruf erlaubt."""
    fetcher = FakeFetcher()
    monkeypatch.setattr(context_service, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(context_service, "fetch_raw", fetcher)
    monkeypatch.setattr(context_service, "_failed_fetches", {})
    monkeypatch.delenv(context_service.LIVE_FETCH_ENV, raising=False)
    return type("Market", (), {"fetcher": fetcher, "cache_dir": tmp_path})()
