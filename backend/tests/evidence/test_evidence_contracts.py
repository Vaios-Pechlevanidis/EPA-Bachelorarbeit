"""
Zusicherungen der Belege (Inkrement 4, Schritt 9): Auflösen eines Einzelmonats aus einer
konstruierten Erkennung, keine Volltexte in Belegen, reservierter Typ market, Speicher
außerhalb der Versionierung, Konstanten der Fenster. Ohne DB und ohne Netz.
"""

import os
import sys

import pytest

BACKEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
sys.path.insert(0, BACKEND_DIR)

import services.evidence_service as ev  # noqa: E402
import services.evidence_sources as src  # noqa: E402

ITEM_KEYS = {"id", "date", "datetime", "title", "publisher", "url", "source", "source_type", "reliability", "language",
             "issuer", "category"}


class TestResolveAnchor:

    @pytest.fixture
    def detection(self, monkeypatch):
        import services.anomaly_service as anomaly_service

        result = {
            "anomalies": [{"id": "employee:durchschnittsbewertung:2021-09", "date": "2021-09", "direction": "fall",
                           "previous_period": "2021-07", "gap_months": 1, "delta": -0.8}],
            "outlier_months": [{"id": "employee:durchschnittsbewertung:2022-12:einzelmonat", "date": "2022-12",
                                "direction": "fall", "deviation": -1.4}],
            "eligibility": {"eligible": True},
        }
        calls = []

        def fake(company_id, source="employee", dimension="durchschnittsbewertung", status=None, **kw):
            calls.append((company_id, source, dimension, status))
            return result

        monkeypatch.setattr(anomaly_service, "company_anomalies", fake)
        return calls

    def test_change_and_outlier(self, detection):
        change = ev.resolve_anchor(7, "employee:durchschnittsbewertung:2021-09")
        assert change["kind"] == "niveauwechsel" and change["previous_period"] == "2021-07" and change["gap_months"] == 1
        outlier = ev.resolve_anchor(7, "employee:durchschnittsbewertung:2022-12:einzelmonat", status="angestellt")
        assert outlier["kind"] == "einzelmonat" and outlier["date"] == "2022-12" and outlier["deviation"] == -1.4
        assert detection[-1] == (7, "employee", "durchschnittsbewertung", "angestellt"), "Erkennung je Bewertendengruppe"

    @pytest.mark.parametrize("anomaly_id", [
        "employee:durchschnittsbewertung:2020-01", "employee:durchschnittsbewertung:2020-01:einzelmonat",
        "employee:durchschnittsbewertung:2021-09:anderes", "nur-ein-teil", "employee::2021-09", "employee:durchschnittsbewertung:2021-13",
    ])
    def test_unknown_or_malformed(self, detection, anomaly_id):
        assert ev.resolve_anchor(7, anomaly_id) is None


class TestContracts:

    def test_items_carry_no_full_texts(self):
        item = src.make_item(title="Titel", url="https://x/1", published_at="2024-01-01", publisher="P", source="gnews", source_type="news")
        assert set(item) == ITEM_KEYS
        event_item = ev.global_event_items([{"id": "e", "date_from": "2024-01", "date_to": "2024-01", "title": "T", "scope": "DE",
                                              "note": "N", "url": "https://x/e", "confirmed": True}], ev.window_for_outlier("2024-01"))[0]
        assert set(event_item) == ITEM_KEYS | {"event"}
        assert set(event_item["event"]) == {"id", "from", "to", "scope", "note"}

    def test_market_type_is_reserved_and_never_produced(self):
        assert src.TYPE_MARKET == "market" and src.TYPE_MARKET not in src.RELIABILITY
        source = open(os.path.join(BACKEND_DIR, "services", "evidence_sources.py"), encoding="utf-8").read()
        assert source.count("source_type=TYPE_MARKET") == 0

    def test_store_and_events_defaults(self):
        gitignore = open(os.path.join(BACKEND_DIR, "..", ".gitignore"), encoding="utf-8").read()
        assert "backend/data/context/" in gitignore, "Belegspeicher bleibt außerhalb der Versionierung"
        assert ev.STORE_DIR.name == "context" and ev.GLOBAL_EVENTS_PATH.name == "global_events.json"
        assert (ev.DEFAULT_WINDOW_BEFORE, ev.DEFAULT_WINDOW_AFTER) == (3, 1)
        assert src.MIN_FETCH_INTERVAL_S >= 2.0 and "non-commercial" in src.news_service.USER_AGENT
