"""
Hilfen der Drill-down-Tests (Inkrement 2): App mit dem Analytics-Router gegen
den In-Memory-Store und Hashes der Antworten vor Inkrement 2.

``routes/analytics.py`` importiert ``get_supabase_client`` beim Laden; nach dem
Neuladen von ``database.supabase_client`` durch ``in_memory_db`` zeigt dieser Name
noch auf die alte Funktion. Er wird hier auf den In-Memory-Client gesetzt, damit
auch die unveränderten Pfade (``/reviews`` ohne neue Parameter,
``topic-overview``) ohne Netzwerk laufen.
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

# NFA-07 (Inkrement 6, 2026-10-09): Die Beispielzitate (``example``,
# ``typicalStatements``, ``reviewDetails``) stammen seitdem nie aus
# jobbeschreibung oder stellenbeschreibung und weichen deshalb von
# TOPIC_OVERVIEW_BASE ab. Die Topic-Berechnung bleibt gleich: Hash der Antwort
# ohne diese drei Felder, erzeugt auf Commit ef05ca6 (vor der Änderung, dort
# stimmte die volle Antwort mit TOPIC_OVERVIEW_BASE überein).
TOPIC_QUOTE_KEYS = ("example", "typicalStatements", "reviewDetails")
# Stand 2026-10-17 (avgRating mit zwei Nachkommastellen, Einstufung auf dem ungerundeten
# Mittel; siehe without_quotes). Die Werte davor stehen in der Git-Historie.
TOPIC_OVERVIEW_CALC_BASE = {
    (1, 'candidates', '2024-01-01'): "e9e6d4eeba2a3633",
    (1, 'candidates', None): "f821b7497674eab1",
    (1, 'employee', '2024-01-01'): "8a3e57f8db514f6e",
    (1, 'employee', None): "4502ff860ad5732d",
    (1, None, '2024-01-01'): "4ec04dcb25365432",
    (1, None, None): "2adab7b47f9bdd1a",
    (2, 'candidates', '2024-01-01'): "8631ff6da74d48bd",
    (2, 'candidates', None): "48ae3ae040a97be6",
    (2, 'employee', '2024-01-01'): "78093933967e32dd",
    (2, 'employee', None): "f16e4656cdffb44b",
    (2, None, '2024-01-01'): "2ab3429b1b22df45",
    (2, None, None): "1c2bb41b80dc24c9",
    (3, 'candidates', '2024-01-01'): "55729028750354b2",
    (3, 'candidates', None): "5cb2328d70faafbe",
    (3, 'employee', '2024-01-01'): "849fa977ffc2cf61",
    (3, 'employee', None): "24836ee9a73df368",
    (3, None, '2024-01-01'): "1ae63c6991ee5b48",
    (3, None, None): "09ed9626b7f5770d",
}


# Felder, die nach dem Stand der Hashes hinzukamen; ihre Werte prüfen eigene Tests
# (ratingDistribution seit 2026-10-13, n_rated und rating_basis seit 2026-10-17:
# tests/test_analyze_topic_rating.py; total_by_source seit 2026-10-17).
TOPIC_ADDED_KEYS = ("ratingDistribution", "n_rated", "rating_basis")
BODY_ADDED_KEYS = ("total_by_source",)


def without_quotes(body):
    """Antwort von topic-overview ohne die Zitatfelder (NFA-07) und ohne die später
    hinzugekommenen Felder; die übrige Berechnung muss unverändert bleiben.

    Stand der Hashes (``TOPIC_OVERVIEW_CALC_BASE``) seit 2026-10-17: ``avgRating`` mit
    zwei Nachkommastellen und Einstufung auf dem ungerundeten Mittel
    (docs/feature-doku/16-report-qualitaet.md, B2). Der Abgleich alt gegen neu auf den
    Demo-Daten ergab am 2026-10-17 ausschließlich Rundungsunterschiede (13 Topics mit
    einem Mittel auf x,x5), keine andere Abweichung."""
    import copy

    body = copy.deepcopy(body)
    for key in BODY_ADDED_KEYS:
        body.pop(key, None)
    for topic in body.get("topics", []):
        for key in (*TOPIC_QUOTE_KEYS, *TOPIC_ADDED_KEYS):
            topic.pop(key, None)
    return body


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

    monkeypatch.setattr(analytics, "get_supabase_client", lambda: client)
    app = FastAPI()
    app.include_router(analytics.router)
    return TestClient(app)


def store_rows(table: str, company_id: int):
    """Zeilen eines Unternehmens direkt aus dem In-Memory-Store."""
    from database.in_memory_store import _TABLES

    return [r for r in _TABLES[table] if r["company_id"] == company_id]
