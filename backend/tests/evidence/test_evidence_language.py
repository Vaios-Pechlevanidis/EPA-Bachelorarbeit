"""
Tests für die Sprachschätzung der Belege (Inkrement 4, Schritt 6): Heuristik aus dem
Spike über Stoppwörter im Titel, Zuordnung beim Anlegen eines Belegs und Ergänzung
beim Lesen älterer Speicherstände. Ohne Netz.
"""

import os
import sys
from datetime import datetime, timezone

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import services.evidence_service as ev  # noqa: E402
import services.evidence_sources as src  # noqa: E402
from _evidence_helpers import FakeRss  # noqa: E402

NOW = datetime(2024, 3, 15, 12, 0, tzinfo=timezone.utc)
INFO = {"company_id": 7, "name": "E.ON", "search_term": "E.ON", "exclude": [], "term_confirmed": False,
        "ticker": None, "ticker_scope": None, "eqs_uuid": None, "eqs_name": None}
FAST = {"sleep": lambda s: None, "clock": lambda: 1000.0}


@pytest.mark.parametrize("title, expected", [
    ("Konzern kündigt Stellenabbau an und streicht Stellen in der Verwaltung", "de"),
    ("Company announces new strategy for the European market", "en"),
    ("Quartalszahlen", None),                       # kein Stoppwort
    ("Die Zahlen the figures", None),               # gleich viele Treffer
    ("", None),
])
def test_guess_language(title, expected):
    assert src.guess_language(title) == expected


def test_make_item_fills_language_from_title():
    item = src.make_item(title="The board approves the plan", url="https://x/1", published_at="2024-01-02",
                         publisher=None, source="gnews", source_type="news")
    assert item["language"] == "en"
    given = src.make_item(title="The board approves the plan", url="https://x/2", published_at="2024-01-02",
                          publisher=None, source="eqs", source_type="adhoc", language="de")
    assert given["language"] == "de", "eine gemeldete Sprache hat Vorrang"


def test_fetched_items_carry_language():
    fetcher = FakeRss({"2024-01": [("Der Vorstand stellt die neue Strategie vor", "https://a/1", "2024-01-10", "P"),
                                   ("Board presents the new strategy to investors", "https://a/2", "2024-01-11", "P")]})
    items, _ = src.fetch_gnews_month("E.ON", "2024-01", fetcher=fetcher)
    assert {i["title"][:5]: i["language"] for i in items} == {"Der V": "de", "Board": "en"}


def test_stored_items_without_language_get_one_when_read(tmp_path):
    item = src.make_item(title="Board presents the new strategy to investors", url="https://a/2", published_at="2024-01-11",
                         publisher=None, source="gnews", source_type="news")
    item["language"] = None   # älterer Speicherstand
    record = ev.build_record(7, "gnews", "2024-01", ev.expected_query(INFO, "gnews", "2024-01"), [item], NOW)
    ev.save_record(record, tmp_path)
    result = ev.evidence_for_window(INFO, ev.window_for_outlier("2024-01", 0, 0), fetchers={"gnews": FakeRss()},
                                    store_dir=tmp_path, now=NOW, **FAST)
    assert result["items"][0]["language"] == "en"
    assert ev.load_record(7, "gnews", "2024-01", tmp_path)["items"][0]["language"] is None, "Speicher bleibt unverändert"
