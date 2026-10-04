"""
Gemeinsame Fixtures der Tests gegen den In-Memory-Store (Anomalien seit
Inkrement 1, Drill-down und Vergleich seit Inkrement 2).

``in_memory_db`` schaltet ``database.supabase_client`` auf den In-Memory-Store
(Demo 1 bis 3) um, und zwar über denselben Weg wie die Anwendung: Fehlen
``SUPABASE_URL`` oder der Schlüssel beim Import, liefert
``get_supabase_client()`` den In-Memory-Client. ``load_dotenv()`` überschreibt
bereits gesetzte Variablen nicht; leere Werte verhindern also, dass
``backend/.env`` greift. Das Modul wird dafür neu geladen und am Ende mit der
ursprünglichen Umgebung wiederhergestellt, damit andere Tests (etwa
``tests/forecast/test_forecast_databasis.py``) unverändert bleiben.

Damit laufen die Tests ohne Netzwerk und ohne Zugangsdaten. In-Memory-IDs:
Demo 1 = 1, Demo 2 = 2, Demo 3 = 3 (in der gehosteten DB 10, 17, 18).
"""

import importlib
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

_ENV_KEYS = ("SUPABASE_URL", "SUPABASE_KEY", "SUPABASE_SERVICE_KEY")


@pytest.fixture(scope="module")
def in_memory_db():
    import database.supabase_client as supabase_client
    from database.in_memory_store import InMemoryClient

    with pytest.MonkeyPatch.context() as mp:
        for key in _ENV_KEYS:
            mp.setenv(key, "")
        importlib.reload(supabase_client)
        client = supabase_client.get_supabase_client()
        assert isinstance(client, InMemoryClient), "Fallback nicht aktiv; Test würde die echte DB abfragen"
        yield client
    importlib.reload(supabase_client)
