"""
Hilfen der Drill-down-Tests (Inkrement 2): App mit dem Analytics-Router gegen
den In-Memory-Store und Hashes der Antworten vor Inkrement 2.

``routes/analytics.py`` bindet beim Import einen Modul-Client ``supabase``. Er
wird hier auf den In-Memory-Client gesetzt, damit auch die unveränderten
Pfade (``/reviews`` ohne neue Parameter, ``topic-overview``) ohne Netzwerk laufen.
"""

import hashlib
import json

from fastapi import FastAPI
from fastapi.testclient import TestClient

# SHA-256 (16 Zeichen) der JSON-Antworten auf Commit 4ad0a80, also vor
# Inkrement 2, erzeugt mit demselben In-Memory-Store (Zufallszahlen mit Seed 42).
# Schlüssel: (Unternehmen, source oder None, start_date bzw. limit oder None).
TOPIC_OVERVIEW_BASE = {
    (1, None, None): "6618518225d27f63",
    (1, None, "2024-01-01"): "1efea88e2aa11f72",
    (1, "employee", None): "e5f8496af1aea407",
    (1, "employee", "2024-01-01"): "1402028b70680c7e",
    (1, "candidates", None): "7cbaf99ff7fadd44",
    (1, "candidates", "2024-01-01"): "0aacda8849acc3de",
    (2, None, None): "5f1e5c1f1826158e",
    (2, None, "2024-01-01"): "95c52b67dcd914a6",
    (2, "employee", None): "c518ad151a4acbbf",
    (2, "employee", "2024-01-01"): "9bd62536cdb36c6c",
    (2, "candidates", None): "3ceac6d472dbf2c9",
    (2, "candidates", "2024-01-01"): "4fe8a709a466a31b",
    (3, None, None): "8b363a29d3f3d25f",
    (3, None, "2024-01-01"): "c51c5c1d9edbcb37",
    (3, "employee", None): "5706f0d8ec50cbf7",
    (3, "employee", "2024-01-01"): "866ef5e2cd8c06f0",
    (3, "candidates", None): "c60722de4e4047d4",
    (3, "candidates", "2024-01-01"): "550f88b47feeca3c",
}

REVIEWS_BASE = {
    (1, None, None): "144b7a5de65d1da9",
    (1, None, 7): "a56c5c5a36302610",
    (1, "employee", None): "827fda41e56f6799",
    (1, "employee", 7): "366e7ef6f11e9885",
    (1, "candidates", None): "ec7594d29c884209",
    (1, "candidates", 7): "ccf3eeb83cfe0015",
    (2, None, None): "2fb8d0f1423e6cf0",
    (2, None, 7): "2423a6fbc6477a90",
    (2, "employee", None): "1e712d550a8bfa06",
    (2, "employee", 7): "17b7bf7e8e981ef8",
    (2, "candidates", None): "b18661c6528595c8",
    (2, "candidates", 7): "0c5b5851f0e0cb09",
    (3, None, None): "8b31d52417e85e1b",
    (3, None, 7): "76782192a7d899a3",
    (3, "employee", None): "fd5bc119b8858ec7",
    (3, "employee", 7): "04469b12ba893522",
    (3, "candidates", None): "b2f3fe912d7c88cb",
    (3, "candidates", 7): "a71abe53185f0a8f",
}


def response_hash(body) -> str:
    """Hash wie bei der Erzeugung der Referenzwerte."""
    return hashlib.sha256(json.dumps(body, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:16]


def analytics_client(monkeypatch, client):
    """TestClient mit dem Analytics-Router; Modul-Client auf ``client`` gesetzt."""
    import routes.analytics as analytics

    monkeypatch.setattr(analytics, "supabase", client)
    app = FastAPI()
    app.include_router(analytics.router)
    return TestClient(app)


def store_rows(table: str, company_id: int):
    """Zeilen eines Unternehmens direkt aus dem In-Memory-Store."""
    from database.in_memory_store import _TABLES

    return [r for r in _TABLES[table] if r["company_id"] == company_id]
