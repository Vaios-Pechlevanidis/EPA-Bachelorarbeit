"""
Tests für die automatischen allgemeinen Ereignisse aus Wirtschaftsdaten (E29,
services/macro_events.py): Einlesen der Eurostat-Antwort, Regeln, Zusammenfassen,
Dauerregel, Zwischenspeicher und Abruf. Konstruierte Reihen, ohne Netz.

Ausführen:
    cd backend
    uv run python -m pytest tests/evidence/test_macro_events.py -q -p no:cacheprovider
"""

import os
import sys
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))

from services import macro_events as me  # noqa: E402

NOW = datetime(2026, 10, 13, 8, 0, tzinfo=timezone.utc)


def months(first, last):
    a, b = me.month_index(first), me.month_index(last)
    return [me.month_key(i) for i in range(a, b + 1)]


def flat(value, first="2006-01", last="2025-12"):
    return {m: value for m in months(first, last)}


def record(esi=None, hicp=None, fetched_at=NOW):
    return {"fetched_at": fetched_at.isoformat(), "series": {"esi": esi or flat(100.0), "hicp": hicp or flat(2.0)}}


def eurostat_doc(values):
    periods = list(values)
    return {"dimension": {"time": {"category": {"index": {p: i for i, p in enumerate(periods)}}}},
            "value": {str(i): v for i, v in enumerate(values.values())}}


class TestParse:

    def test_parse_eurostat_json_stat(self):
        doc = eurostat_doc({"2020-02": 100.1, "2020-01": 99.5})
        doc["value"]["7"] = 1.0   # Position ohne Zeitangabe wird übergangen
        assert me.parse_eurostat(doc) == {"2020-01": 99.5, "2020-02": 100.1}

    def test_series_urls_name_the_datasets(self):
        assert "ei_bssi_m_r2" in me.series_url("esi") and "BS-ESI-I" in me.series_url("esi") and "geo=DE" in me.series_url("esi")
        assert "prc_hicp_manr" in me.series_url("hicp") and "CP00" in me.series_url("hicp")


class TestRules:

    def test_no_events_in_calm_times(self):
        assert me.derive_events(record()) == []
        assert me.derive_events(None) == []

    def test_esi_drop_of_ten_points_in_three_months(self):
        esi = flat(100.0)
        esi.update({"2020-03": 91.0, "2020-04": 70.0, "2020-05": 72.0, "2020-06": 85.0})
        (event,) = me.derive_events(record(esi=esi))
        # März: 91 − 100 = −9 (knapp nicht); April und Mai mindestens 10 unter drei Monaten davor;
        # Juni: 85 − 91 (März) = −6, nicht mehr
        assert (event["date_from"], event["date_to"]) == ("2020-04", "2020-05")
        assert event["title"] == "Konjunktureinbruch (Wirtschaftsstimmung fällt von 100,0 auf 70,0 Punkte)"
        assert event["confirmed"] is True and event["id"] == "auto-2020-04"
        assert event["scope"] == me.SCOPE and "ei_bssi_m_r2" in event["url"]
        assert "abgerufen 2026-10-13" in event["note"] and "E29" in event["note"]

    def test_hicp_rise_needs_minimum_rate(self):
        hicp = flat(1.0)
        hicp.update({"2021-01": 3.5})              # +2,5 Punkte, aber unter 5 %: kein Ereignis
        hicp.update({m: 4.0 for m in months("2021-02", "2022-02")})
        hicp.update({"2022-03": 7.0})              # +3 Punkte und mindestens 5 %
        (event,) = me.derive_events(record(hicp=hicp))
        assert (event["date_from"], event["date_to"]) == ("2022-03", "2022-03")
        assert event["title"] == "Inflationsschub (Inflationsrate steigt auf 7,0 %)"
        assert "prc_hicp_manr" in event["url"]

    def test_overlapping_rules_merge_into_one_event(self):
        esi = flat(100.0)
        esi.update({"2022-09": 88.0})
        hicp = flat(5.0)
        hicp.update({"2022-09": 8.0, "2022-10": 9.0, "2022-11": 9.5})
        (event,) = me.derive_events(record(esi=esi, hicp=hicp))
        assert (event["date_from"], event["date_to"]) == ("2022-09", "2022-11")
        assert event["title"].startswith("Konjunktureinbruch") and " und Inflationsschub" in event["title"]

    def test_months_one_apart_merge_and_further_apart_split(self):
        esi = flat(100.0)
        esi.update({"2008-11": 85.0, "2009-01": 84.0})        # Lücke von einem Monat: ein Ereignis
        esi.update({"2012-01": 85.0})                         # weit entfernt: eigenes Ereignis
        events = me.derive_events(record(esi=esi))
        assert [(e["date_from"], e["date_to"]) for e in events] == [("2008-11", "2009-01"), ("2012-01", "2012-01")]

    def test_duration_rule_shortens_long_spans(self):
        esi = flat(100.0)
        for i, m in enumerate(months("2009-01", "2009-08")):
            esi[m] = 100.0 - 11.0 * (i + 1)   # acht Monate in Folge stark fallend
        (event,) = me.derive_events(record(esi=esi), max_months=6)
        assert (event["date_from"], event["date_to"]) == ("2009-01", "2009-06")
        assert "Auf die ersten 6 Monate gekürzt" in event["note"]

    def test_start_month_limits_the_search(self):
        esi = flat(100.0)
        esi.update({"2006-06": 80.0})
        assert me.derive_events(record(esi=esi)) == []


class TestCache:

    def fetcher(self, calls):
        def fetch(url):
            calls.append(url)
            values = flat(100.0) if "ei_bssi_m_r2" in url else flat(2.0)
            if "ei_bssi_m_r2" in url:
                values["2020-04"] = 70.0
            return eurostat_doc(values)
        return fetch

    def test_fetches_and_stores_when_missing(self, tmp_path):
        calls = []
        path = tmp_path / "eurostat_de.json"
        state = me.macro_record(fetcher=self.fetcher(calls), path=path, now=NOW, live=True)
        assert state["error"] is None and not state["stale"] and len(calls) == 2
        assert path.exists() and me.load_cached(path)["fetched_at"].startswith("2026-10-13")
        assert [e["date_from"] for e in me.global_events(path=path, now=NOW, live=False)] == ["2020-04"]

    def test_fresh_cache_is_used_without_fetch(self, tmp_path):
        path = tmp_path / "eurostat_de.json"
        me.save_cached(record(fetched_at=NOW - timedelta(days=2)), path)
        calls = []
        state = me.macro_record(fetcher=self.fetcher(calls), path=path, now=NOW, live=True)
        assert calls == [] and state["record"] is not None

    def test_old_cache_is_refreshed_and_kept_on_failure(self, tmp_path):
        path = tmp_path / "eurostat_de.json"
        me.save_cached(record(fetched_at=NOW - timedelta(days=30)), path)

        def broken(url):
            raise OSError("offline")
        state = me.macro_record(fetcher=broken, path=path, now=NOW, live=True, clock=lambda: 100.0)
        assert state["stale"] and state["record"] is not None and "Eurostat nicht abrufbar" in state["error"]
        # innerhalb der Wartezeit kein neuer Versuch
        calls = []
        me.macro_record(fetcher=self.fetcher(calls), path=path, now=NOW, live=True, clock=lambda: 200.0)
        assert calls == []
        # danach wieder
        me.macro_record(fetcher=self.fetcher(calls), path=path, now=NOW, live=True, clock=lambda: 100.0 + me.FAILED_FETCH_TTL + 1)
        assert len(calls) == 2
        me._failed_fetch.clear()

    def test_no_fetch_when_disabled(self, tmp_path, monkeypatch):
        monkeypatch.setenv(me.LIVE_FETCH_ENV, "0")
        calls = []
        state = me.macro_record(fetcher=self.fetcher(calls), path=tmp_path / "fehlt.json", now=NOW)
        assert calls == [] and state["record"] is None and "CONTEXT_LIVE_FETCH=0" in state["error"]
        assert me.global_events(path=tmp_path / "fehlt.json", now=NOW) == []
