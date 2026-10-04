"""
Regressionstest: parallele Requests dürfen sich keinen Supabase-Client teilen.

Hintergrund: Der gehostete Client (postgrest über httpx mit HTTP/2) ist nicht
threadsicher. Ein einziger Client auf Modulebene, den FastAPI aus mehreren
Threadpool-Threads gleichzeitig nutzt, führte zu httpx.ReadError ([Errno 35])
und damit zu 500ern bei parallelen Aufrufen von /api/companies.

Der Test bildet das ohne Netzwerk nach: create_client wird durch eine Fabrik
ersetzt, deren Clients nur in dem Thread benutzt werden dürfen, in dem sie
erzeugt wurden (sonst Exception). Die Daten kommen aus dem In-Memory-Store.

Ausführen (aus dem backend-Verzeichnis):
    uv run python -m pytest tests/test_supabase_client_concurrency.py -q
"""

import importlib
import os
import sys
import threading
from concurrent.futures import ThreadPoolExecutor

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import supabase as supabase_pkg  # noqa: E402

import database.supabase_client as supabase_client_module  # noqa: E402
import routes.companies as companies_module  # noqa: E402
from database.in_memory_store import get_in_memory_client  # noqa: E402

N_THREADS = 8


class _ThreadAffineClient:
    """Fake-Client, der wie die HTTP/2-Session nur von einem Thread benutzt
    werden darf; Zugriffe aus anderen Threads schlagen fehl."""

    def __init__(self, inner):
        self._inner = inner
        self.owner = threading.get_ident()

    def _check_thread(self):
        if threading.get_ident() != self.owner:
            raise RuntimeError("Client wird von einem fremden Thread benutzt")

    def table(self, name):
        self._check_thread()
        return self._inner.table(name)

    def rpc(self, func, params):
        self._check_thread()
        return self._inner.rpc(func, params)


@pytest.fixture
def hosted_client_module(monkeypatch):
    """Lädt database.supabase_client im 'gehosteten' Zweig (URL und Key gesetzt),
    mit einem Fake statt create_client. Danach wird der Ursprungszustand
    wiederhergestellt."""
    created = []

    def fake_create_client(url, key):
        client = _ThreadAffineClient(get_in_memory_client())
        created.append(client)
        return client

    monkeypatch.setenv("SUPABASE_URL", "http://fake.invalid")
    monkeypatch.setenv("SUPABASE_KEY", "fake-key")
    monkeypatch.setenv("SUPABASE_SERVICE_KEY", "fake-key")
    monkeypatch.setattr(supabase_pkg, "create_client", fake_create_client)
    module = importlib.reload(supabase_client_module)
    monkeypatch.setattr(companies_module, "get_supabase_client", module.get_supabase_client)
    yield module, created
    monkeypatch.undo()
    importlib.reload(supabase_client_module)


def _run_concurrently(fn, n=N_THREADS):
    barrier = threading.Barrier(n)

    def call():
        barrier.wait()  # alle Threads starten gleichzeitig
        return fn()

    with ThreadPoolExecutor(max_workers=n) as pool:
        futures = [pool.submit(call) for _ in range(n)]
        return [f.result() for f in futures]


def test_get_supabase_client_returns_one_client_per_thread(hosted_client_module):
    module, created = hosted_client_module

    clients = _run_concurrently(module.get_supabase_client)

    assert len(created) == N_THREADS
    assert len({id(c) for c in clients}) == N_THREADS
    # Im selben Thread wird der Client wiederverwendet.
    assert module.get_supabase_client() is module.get_supabase_client()


def test_get_companies_runs_concurrently_without_errors(hosted_client_module):
    module, _ = hosted_client_module
    expected = companies_module.get_companies()

    results = _run_concurrently(companies_module.get_companies)

    assert all(r == expected for r in results)
    assert expected  # In-Memory-Store enthält Demo-Unternehmen


def test_shared_client_reproduces_the_original_failure(monkeypatch):
    """Gegenprobe: Mit einem gemeinsamen Client (alter Zustand) schlagen
    parallele Aufrufe fehl. Zeigt, dass der Fake das Problem erkennt."""
    shared = _ThreadAffineClient(get_in_memory_client())
    monkeypatch.setattr(companies_module, "get_supabase_client", lambda: shared)

    with pytest.raises(RuntimeError, match="fremden Thread"):
        _run_concurrently(companies_module.get_companies)
