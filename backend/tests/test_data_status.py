"""
Tests für services/data_status_service.py und GET /api/companies/{id}/data-status
(Datenstand, FA-37, Inkrement 6). Konstruierte Zeilen für die reinen Funktionen;
Zwischenspeicher und Belegspeicher in tmp_path; die Route gegen den In-Memory-Store
(Demo 1 bis 3). Ohne Netzwerk, ohne Abruf.

Ausführen:
    cd backend
    uv run python -m pytest tests/test_data_status.py -q -p no:cacheprovider
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

import services.data_status_service as ds  # noqa: E402
import services.evidence_service as ev  # noqa: E402
import services.context_service as cs  # noqa: E402

NOW = datetime(2026, 10, 9, 12, 0, tzinfo=timezone.utc)


def row(i, datum, status="1.0", value=4.0, update=None, created="2026-10-02T18:50:16.123456+00:00"):
    return {"id": i, "datum": datum, "update_datum": update, "created_at": created, "status": status,
            "durchschnittsbewertung": value}


# ---------------------------------------------------------------------------
# Je Quelle
# ---------------------------------------------------------------------------

def test_source_status_counts_dates_and_timestamps():
    rows = [
        row(1, "2024-01-10T00:00:00", "1.0", 4.0, update="2024-02-01T00:00:00"),
        row(2, "2024-03-05T00:00:00", "0.0", 2.0),
        row(3, None, "", 3.0),                      # ohne Datum
        row(4, "2024-03-20T00:00:00", "True", 5.0, created="2026-10-03T08:00:00+00:00"),
    ]
    s = ds.source_status(rows, "employee")
    assert s["label"] == "Mitarbeitende"
    assert s["n_reviews"] == 4 and s["n_dated"] == 3 and s["n_undated"] == 1
    assert s["first_review"] == "2024-01-10" and s["last_review"] == "2024-03-20"
    assert s["first_month"] == "2024-01" and s["last_month"] == "2024-03" and s["months_in_span"] == 3
    assert s["evaluated_months"] == 0 and s["eligible"] is False
    assert s["timestamps"]["datum"] == {"min": "2024-01-10T00:00:00", "max": "2024-03-20T00:00:00", "n": 3}
    assert s["timestamps"]["update_datum"] == {"min": "2024-02-01T00:00:00", "max": "2024-02-01T00:00:00", "n": 1}
    assert s["timestamps"]["created_at"]["max"] == "2026-10-03T08:00:00" and s["timestamps"]["created_at"]["n"] == 4
    assert s["last_import"] == "2026-10-03T08:00:00"
    assert s["status_counts"] == {"angestellt": 2, "ex-angestellt": 1, "unbekannt": 1}
    assert s["status_distinction"] is True


def test_source_status_without_former_employees_has_no_distinction():
    rows = [row(i, f"2024-0{1 + i % 3}-10T00:00:00", "1.0") for i in range(6)]
    s = ds.source_status(rows, "employee")
    assert s["status_counts"]["ex-angestellt"] == 0 and s["status_distinction"] is False


def test_source_status_candidates_keys_and_no_distinction_field():
    rows = [row(1, "2024-01-10T00:00:00", "hired"), row(2, "2024-01-11T00:00:00", "deferred")]
    s = ds.source_status(rows, "candidates")
    assert s["label"] == "Bewerbende"
    assert s["status_counts"]["eingestellt"] == 1 and s["status_counts"]["zurueckgestellt"] == 1
    assert "status_distinction" not in s


def test_source_status_eligibility_follows_e4():
    rows = []
    i = 0
    for m in range(1, 13):          # 12 Monate mit je 5 Bewertungen → geeignet
        for _ in range(5):
            i += 1
            rows.append(row(i, f"2024-{m:02d}-10T00:00:00"))
    s = ds.source_status(rows, "employee")
    assert s["evaluated_months"] == 12 and s["eligible"] is True


def test_source_status_empty():
    s = ds.source_status([], "employee")
    assert s["n_reviews"] == 0 and s["first_review"] is None and s["last_month"] is None
    assert s["eligible"] is False and s["last_import"] is None and s["status_distinction"] is False


# ---------------------------------------------------------------------------
# Plattform
# ---------------------------------------------------------------------------

def test_platform_comparison_not_provided():
    p = ds.platform_comparison({"platform_review_count": None, "platform_count_date": None}, 120)
    assert p["available"] is False and p["note"] == ds.PLATFORM_NOT_PROVIDED and p["dataset_count"] == 120
    assert ds.platform_comparison(None, 3)["available"] is False
    assert ds.platform_comparison({"platform_review_count": "x"}, 3)["available"] is False


def test_platform_comparison_with_author_values():
    p = ds.platform_comparison({"platform_review_count": 200, "platform_count_date": "2026-10-09"}, 150)
    assert p == {"available": True, "review_count": 200, "count_date": "2026-10-09", "dataset_count": 150,
                 "coverage_share": 0.75, "note": None}


# ---------------------------------------------------------------------------
# Zwischenspeicher (nur lesen)
# ---------------------------------------------------------------------------

def test_market_cache_status_reads_cache_without_fetch(monkeypatch, tmp_path):
    monkeypatch.setattr(cs, "company_ticker_info", lambda cid: {"company_id": cid, "name": "Test AG", "ticker": "TST.DE",
                                                                 "ticker_scope": "eigene Aktie", "peer_group": None})
    monkeypatch.setattr(cs, "fetch_raw", lambda ticker: pytest.fail("kein Abruf erlaubt"))
    assert ds.market_cache_status(19, cache_dir=tmp_path)["available"] is False
    cs.save_cached({"ticker": "TST.DE", "fetched_at": "2026-10-04T15:57:26+00:00", "source": "Yahoo Finance über yfinance 1.0",
                    "prices": [{"period": "2024-01", "close": 1.0}, {"period": "2024-02", "close": 2.0}]}, tmp_path)
    m = ds.market_cache_status(19, cache_dir=tmp_path)
    assert m["available"] is True and m["fetched_at"] == "2026-10-04T15:57:26" and m["months"] == 2
    assert m["first_month"] == "2024-01" and m["last_month"] == "2024-02" and m["ticker_scope"] == "eigene Aktie"


def test_market_cache_status_none_without_ticker(monkeypatch):
    monkeypatch.setattr(cs, "company_ticker_info", lambda cid: {"company_id": cid, "name": "Uni", "ticker": None,
                                                                 "ticker_scope": None, "peer_group": "Nicht börsennotiert"})
    assert ds.market_cache_status(14) is None


def test_evidence_store_status_counts_months_per_source(monkeypatch, tmp_path):
    info = {"company_id": 19, "name": "Test AG", "search_term": '"Test AG"', "exclude": [], "term_confirmed": True,
            "ticker": None, "ticker_scope": None, "eqs_uuid": "u", "eqs_name": "Test AG"}
    monkeypatch.setattr(ev, "company_context_info", lambda cid, metadata=None: info)
    monkeypatch.delenv(ev.GDELT_ENV, raising=False)
    now = NOW
    for month, stamp in (("2024-01", "2026-10-08T17:23:37+00:00"), ("2024-02", "2026-10-08T18:00:00+00:00")):
        ev.save_record(ev.build_record(19, "gnews", month, "q", [{"id": f"g{month}"}], now) | {"fetched_at": stamp}, tmp_path)
    ev.save_record(ev.build_record(19, "eqs", "2024-02", None, [], now), tmp_path)
    # ein fehlgeschlagener Monat zählt nicht
    ev.save_record(ev.build_record(19, "eqs", "2024-03", None, [], now) | {"status": "error"}, tmp_path)
    s = ds.evidence_store_status(19, store_dir=tmp_path)
    assert s["search_term"] == '"Test AG"' and s["term_confirmed"] is True
    assert set(s["sources"]) == {"gnews", "eqs"}
    assert s["sources"]["gnews"] == {"label": "Google News RSS", "months": 2, "first_month": "2024-01", "last_month": "2024-02",
                                     "n_items": 2, "fetched_at": "2026-10-08T18:00:00"}
    assert s["sources"]["eqs"]["months"] == 1 and s["sources"]["eqs"]["n_items"] == 0
    assert s["months"] == 2 and s["first_month"] == "2024-01" and s["last_month"] == "2024-02"
    assert s["sources"]["eqs"]["fetched_at"] == "2026-10-09T12:00:00"   # build_record mit now
    assert s["fetched_at"] == "2026-10-09T12:00:00"                     # jüngster Stand über alle Quellen


def test_evidence_store_status_empty_store(monkeypatch, tmp_path):
    info = {"company_id": 4, "name": "Open Grid", "search_term": "x", "exclude": [], "term_confirmed": False,
            "ticker": None, "ticker_scope": None, "eqs_uuid": None, "eqs_name": None}
    monkeypatch.setattr(ev, "company_context_info", lambda cid, metadata=None: info)
    monkeypatch.delenv(ev.GDELT_ENV, raising=False)
    s = ds.evidence_store_status(4, store_dir=tmp_path)
    assert s["months"] == 0 and s["fetched_at"] is None and s["sources"]["gnews"]["months"] == 0


# ---------------------------------------------------------------------------
# Zusammenführung und Route
# ---------------------------------------------------------------------------

def test_assemble_status_shape_and_last_import():
    rows = {"employee": [row(1, "2024-01-10T00:00:00", created="2026-04-15T07:59:02+00:00")],
            "candidates": [row(2, "2024-02-10T00:00:00", "hired", created="2026-04-15T07:59:00+00:00")]}
    body = ds.assemble_status(3, "Thyssenkrupp", rows, None, None, None, NOW)
    assert body["company_id"] == 3 and body["name"] == "Thyssenkrupp" and body["generated_at"] == "2026-10-09T12:00:00+00:00"
    assert body["n_reviews_total"] == 2
    assert body["last_import"] == {"value": "2026-04-15T07:59:02", "field": "created_at", "meaning": ds.TIMESTAMP_MEANING["created_at"]}
    assert body["thresholds"] == {"min_reviews_per_month": 5, "min_evaluated_months": 12}
    assert body["market_cache"] is None and body["evidence_store"] is None
    assert body["platform"]["available"] is False and body["platform"]["note"] == ds.PLATFORM_NOT_PROVIDED
    assert set(body["timestamp_fields"]) == {"datum", "update_datum", "created_at"}


def test_fixed_texts_describe_only():
    import re

    texts = " ".join([ds.DATA_STATUS_NOTE, ds.PLATFORM_NOT_PROVIDED, *ds.TIMESTAMP_MEANING.values()]).lower()
    for word in ("ursache", "auslöser", "weil", "führt zu", "wird sinken", "prognose"):
        assert re.search(rf"\b{word}\b", texts) is None, word


@pytest.fixture
def client(in_memory_db, monkeypatch, tmp_path):
    import routes.companies as companies_module

    monkeypatch.setattr(companies_module, "get_supabase_client", lambda: in_memory_db)
    # Zwischenspeicher und Belegspeicher leer (tmp_path), kein Abruf
    monkeypatch.setattr(cs, "CACHE_DIR", tmp_path / "market")
    monkeypatch.setattr(ev, "STORE_DIR", tmp_path / "context")
    monkeypatch.setenv(cs.LIVE_FETCH_ENV, "0")
    monkeypatch.setenv(ev.LIVE_FETCH_ENV, "0")
    app = FastAPI()
    app.include_router(companies_module.router)
    return TestClient(app)


def test_route_data_status_demo(client):
    res = client.get("/api/companies/3/data-status")
    assert res.status_code == 200
    body = res.json()
    assert body["company_id"] == 3 and body["name"] == "Demo 3"
    emp, cand = body["sources"]["employee"], body["sources"]["candidates"]
    assert emp["n_reviews"] > 0 and cand["n_reviews"] > 0
    assert body["n_reviews_total"] == emp["n_reviews"] + cand["n_reviews"]
    assert emp["eligible"] is True and emp["evaluated_months"] >= 12
    assert emp["first_month"] <= emp["last_month"]
    assert body["last_import"]["field"] == "created_at"
    assert body["platform"]["note"] == ds.PLATFORM_NOT_PROVIDED
    assert body["market_cache"] is None          # Demo ohne Ticker
    assert body["evidence_store"] is not None and body["evidence_store"]["months"] == 0
    assert body["note"] == ds.DATA_STATUS_NOTE


def test_route_data_status_unknown_company(client):
    assert client.get("/api/companies/999/data-status").status_code == 404


def test_metadata_file_lists_platform_fields_for_every_company():
    path = Path(__file__).resolve().parent.parent / "data" / "company_metadata.json"
    with open(path, "r", encoding="utf-8") as fh:
        entries = json.load(fh)
    assert all(set(ds.PLATFORM_FIELDS) <= set(e) for e in entries)
