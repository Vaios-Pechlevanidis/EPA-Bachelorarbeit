"""
Allgemeine Ereignisse automatisch aus amtlichen Wirtschaftsdaten (2026-10-13, E29).

Ersetzt die von Hand gepflegte Datei ``backend/data/global_events.json`` (E20).
Ein allgemeines Ereignis ist ein Zeitraum, in dem sich die gesamtwirtschaftliche
Lage in Deutschland schnell verschlechtert. Grundlage sind zwei Monatsreihen von
Eurostat (frei, ohne Schlüssel):

- **ESI** (Economic Sentiment Indicator, Indikator der wirtschaftlichen
  Einschätzung) der Europäischen Kommission, Deutschland, saisonbereinigt
  (``ei_bssi_m_r2``, ``BS-ESI-I``). Die Kommission normiert ihn auf einen
  langjährigen Mittelwert von 100 und eine Standardabweichung von 10.
- **HVPI**-Inflationsrate, Deutschland, Veränderung gegenüber dem
  Vorjahresmonat in % (``prc_hicp_manr``, ``CP00``).

Regeln (Setzungen, E29):

1. **Konjunktureinbruch:** Der ESI liegt mindestens ``ESI_DROP`` Punkte (eine
   Standardabweichung der Normierung) unter seinem Wert drei Monate davor.
2. **Inflationsschub:** Die Inflationsrate liegt mindestens ``HICP_RISE``
   Prozentpunkte über ihrem Wert drei Monate davor und beträgt mindestens
   ``HICP_MIN`` %. Die Untergrenze hält Basiseffekte bei niedriger Inflation
   fern (etwa die Rückkehr zum vollen Mehrwertsteuersatz im Januar 2021).

Monate einer Regel mit höchstens ``MERGE_GAP`` Monat Abstand bilden einen
Zeitraum; Zeiträume beider Regeln, die sich überschneiden oder aneinander
grenzen, werden zu einem Ereignis zusammengefasst. Die Dauerregel aus E20 gilt
weiter: Ein Ereignis umfasst höchstens ``max_months`` Monate (sonst die ersten
``max_months``). Betrachtet werden die Monate ab ``START_MONTH``.

Zwischenspeicher ``backend/data/macro/eurostat_de.json`` (nicht eingecheckt).
Ist er älter als ``MAX_AGE`` und ``CONTEXT_LIVE_FETCH`` nicht ``0``, wird neu
abgerufen; schlägt das fehl, gilt der alte Stand (nach einem Fehlschlag frühestens
nach ``FAILED_FETCH_TTL`` ein neuer Versuch). Ohne Zwischenspeicher und ohne
Abruf gibt es keine allgemeinen Ereignisse. Eurostat überarbeitet die Reihen
gelegentlich; die Ereignisse folgen dem jeweils abgerufenen Stand.
"""

from __future__ import annotations

import json
import logging
import os
import tempfile
import time
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

BACKEND_DIR = Path(__file__).resolve().parent.parent
CACHE_PATH = BACKEND_DIR / "data" / "macro" / "eurostat_de.json"
LIVE_FETCH_ENV = "CONTEXT_LIVE_FETCH"
MAX_AGE = timedelta(days=7)
FAILED_FETCH_TTL = 15 * 60       # Sekunden ohne neuen Versuch nach einem fehlgeschlagenen Abruf
CACHE_VERSION = 1
USER_AGENT = "EPA-Bachelorarbeit/0.1 (Forschungsprototyp)"

EUROSTAT_API = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/"
SERIES: Dict[str, Dict[str, Any]] = {
    "esi": {
        "dataset": "ei_bssi_m_r2",
        "params": {"geo": "DE", "indic": "BS-ESI-I", "s_adj": "SA"},
        "label": "Indikator der wirtschaftlichen Einschätzung (ESI), Deutschland, saisonbereinigt",
        "url": "https://ec.europa.eu/eurostat/databrowser/view/ei_bssi_m_r2/default/table?lang=de",
    },
    "hicp": {
        "dataset": "prc_hicp_manr",
        "params": {"geo": "DE", "coicop": "CP00", "unit": "RCH_A"},
        "label": "HVPI-Inflationsrate, Deutschland, Veränderung gegenüber dem Vorjahresmonat in %",
        "url": "https://ec.europa.eu/eurostat/databrowser/view/prc_hicp_manr/default/table?lang=de",
    },
}

START_MONTH = "2007-01"   # Beginn der Bewertungsreihen (früheste Bewertungen 2007)
LOOKBACK = 3              # Monate, über die die Veränderung gemessen wird
ESI_DROP = 10.0           # Punkte; eine Standardabweichung der ESI-Normierung
HICP_RISE = 2.0           # Prozentpunkte
HICP_MIN = 5.0            # % Mindestrate
MERGE_GAP = 1             # Monate Lücke innerhalb eines Zeitraums
SCOPE = "Deutschland; gesamte Wirtschaft"

RULE_ESI = "konjunktureinbruch"
RULE_HICP = "inflationsschub"

MONTHS_DE = ["Jan.", "Feb.", "März", "Apr.", "Mai", "Juni", "Juli", "Aug.", "Sept.", "Okt.", "Nov.", "Dez."]

Fetcher = Callable[[str], Dict[str, Any]]
_failed_fetch: Dict[str, Any] = {}


# ─── Monate und Zahlen ───────────────────────────────────────────────────────

def month_index(period: str) -> int:
    year, month = str(period)[:7].split("-")
    return int(year) * 12 + int(month) - 1


def month_key(index: int) -> str:
    return f"{index // 12:04d}-{index % 12 + 1:02d}"


def fmt_month(period: str) -> str:
    i = month_index(period)
    return f"{MONTHS_DE[i % 12]} {i // 12}"


def fmt_num(value: float, digits: int = 1) -> str:
    return f"{value:.{digits}f}".replace(".", ",")


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


# ─── Abruf und Zwischenspeicher ──────────────────────────────────────────────

def series_url(name: str) -> str:
    spec = SERIES[name]
    query = urllib.parse.urlencode({**spec["params"], "format": "JSON", "lang": "EN"})
    return f"{EUROSTAT_API}{spec['dataset']}?{query}"


def fetch_json(url: str) -> Dict[str, Any]:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    with urllib.request.urlopen(request, timeout=60) as response:  # noqa: S310 – feste Eurostat-Adresse
        return json.load(response)


def parse_eurostat(doc: Dict[str, Any]) -> Dict[str, float]:
    """JSON-stat-Antwort mit einer Reihe → {"YYYY-MM": Wert}, aufsteigend."""
    index = doc["dimension"]["time"]["category"]["index"]
    by_position = {int(pos): period for period, pos in index.items()}
    values = {}
    for pos, value in (doc.get("value") or {}).items():
        period = by_position.get(int(pos))
        if period and value is not None and len(period) == 7 and period[4] == "-":
            values[period] = float(value)
    return dict(sorted(values.items()))


def fetch_record(fetcher: Optional[Fetcher] = None, now: Optional[datetime] = None) -> Dict[str, Any]:
    """Beide Reihen frisch von Eurostat; wirft bei Netz- oder Formatfehlern."""
    fetcher = fetcher or fetch_json
    series = {}
    for name in SERIES:
        values = parse_eurostat(fetcher(series_url(name)))
        if not values:
            raise ValueError(f"Eurostat-Reihe {name} ist leer.")
        series[name] = values
    return {
        "version": CACHE_VERSION,
        "fetched_at": (now or utc_now()).isoformat(timespec="seconds"),
        "sources": {name: {"dataset": s["dataset"], "params": s["params"], "label": s["label"], "url": s["url"]}
                    for name, s in SERIES.items()},
        "series": series,
    }


def load_cached(path: Optional[Path] = None) -> Optional[Dict[str, Any]]:
    path = Path(path or CACHE_PATH)
    if not path.exists():
        return None
    try:
        with open(path, "r", encoding="utf-8") as fh:
            record = json.load(fh)
    except (OSError, ValueError) as exc:
        logger.warning("Zwischenspeicher der Wirtschaftsdaten nicht lesbar: %s", exc)
        return None
    if not isinstance(record, dict) or not all(isinstance(record.get("series", {}).get(n), dict) for n in SERIES):
        return None
    return record


def save_cached(record: Dict[str, Any], path: Optional[Path] = None) -> Path:
    path = Path(path or CACHE_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        json.dump(record, fh, ensure_ascii=False, indent=1)
    os.replace(tmp, path)
    return path


def live_fetch_enabled() -> bool:
    return os.getenv(LIVE_FETCH_ENV, "1").strip() != "0"


def _age(record: Dict[str, Any], now: datetime) -> timedelta:
    try:
        fetched = datetime.fromisoformat(str(record.get("fetched_at")))
    except ValueError:
        return MAX_AGE * 2
    if fetched.tzinfo is None:
        fetched = fetched.replace(tzinfo=timezone.utc)
    return now - fetched


def macro_record(fetcher: Optional[Fetcher] = None, path: Optional[Path] = None, now: Optional[datetime] = None,
                 live: Optional[bool] = None, clock: Callable[[], float] = time.monotonic) -> Dict[str, Any]:
    """Aktueller Stand der Reihen: ``{"record", "stale", "error"}``. Ruft neu ab, wenn der
    Zwischenspeicher fehlt oder älter als ``MAX_AGE`` ist und ein Abruf erlaubt ist."""
    now = now or utc_now()
    live = live_fetch_enabled() if live is None else live
    cached = load_cached(path)
    if cached is not None and _age(cached, now) <= MAX_AGE:
        return {"record": cached, "stale": False, "error": None}
    if not live:
        reason = None if cached else f"Kein Zwischenspeicher der Wirtschaftsdaten und kein Abruf ({LIVE_FETCH_ENV}=0)."
        return {"record": cached, "stale": cached is not None, "error": reason}
    failed_at = _failed_fetch.get("at")
    if failed_at is not None and clock() - failed_at < FAILED_FETCH_TTL:
        return {"record": cached, "stale": cached is not None, "error": _failed_fetch.get("reason")}
    try:
        record = fetch_record(fetcher, now)
    except Exception as exc:  # noqa: BLE001 – Netz, JSON, Format: alter Stand gilt weiter
        reason = f"Eurostat nicht abrufbar ({type(exc).__name__}: {exc})."
        logger.warning("Abruf der Wirtschaftsdaten fehlgeschlagen: %s", exc)
        _failed_fetch.update({"at": clock(), "reason": reason})
        return {"record": cached, "stale": cached is not None, "error": reason}
    _failed_fetch.clear()
    try:
        save_cached(record, path)
    except OSError as exc:
        logger.warning("Zwischenspeicher der Wirtschaftsdaten nicht schreibbar: %s", exc)
    return {"record": record, "stale": False, "error": None}


# ─── Regeln und Ereignisse ───────────────────────────────────────────────────

def rule_hits(series: Dict[str, Dict[str, float]], start: str = START_MONTH) -> Dict[str, List[Dict[str, Any]]]:
    """Je Regel die Monate, die sie erfüllen, mit Wert, Vergleichswert und Veränderung."""
    hits: Dict[str, List[Dict[str, Any]]] = {RULE_ESI: [], RULE_HICP: []}
    checks = (
        (RULE_ESI, series.get("esi") or {}, lambda value, change: change <= -ESI_DROP),
        (RULE_HICP, series.get("hicp") or {}, lambda value, change: change >= HICP_RISE and value >= HICP_MIN),
    )
    for rule, values, test in checks:
        for period, value in values.items():
            if period < start:
                continue
            before = values.get(month_key(month_index(period) - LOOKBACK))
            if before is None:
                continue
            change = value - before
            if test(value, change):
                hits[rule].append({"month": period, "value": value, "before": before, "change": round(change, 4)})
    return hits


def _runs(months: List[str], gap: int = MERGE_GAP) -> List[Tuple[str, str]]:
    runs: List[Tuple[str, str]] = []
    for period in sorted(months):
        if runs and month_index(period) - month_index(runs[-1][1]) <= gap + 1:
            runs[-1] = (runs[-1][0], period)
        else:
            runs.append((period, period))
    return runs


def _rule_part(rule: str, hits: List[Dict[str, Any]]) -> Dict[str, str]:
    """Titelteil und Vermerk einer Regel für die Treffermonate eines Ereignisses."""
    first = hits[0]
    if rule == RULE_ESI:
        low = min(hits, key=lambda h: h["value"])
        strongest = min(hits, key=lambda h: h["change"])
        return {
            "title": f"Konjunktureinbruch (Wirtschaftsstimmung fällt von {fmt_num(first['before'])} auf {fmt_num(low['value'])} Punkte)",
            "note": (f"ESI mindestens {fmt_num(ESI_DROP, 0)} Punkte unter dem Wert drei Monate davor; stärkster Rückgang um "
                     f"{fmt_num(abs(strongest['change']))} Punkte bis {fmt_month(strongest['month'])}."),
        }
    peak = max(hits, key=lambda h: h["value"])
    return {
        "title": f"Inflationsschub (Inflationsrate steigt auf {fmt_num(peak['value'])} %)",
        "note": (f"HVPI-Inflationsrate mindestens {fmt_num(HICP_RISE, 0)} Prozentpunkte über dem Wert drei Monate davor "
                 f"und mindestens {fmt_num(HICP_MIN, 0)} %; Höchstwert {fmt_num(peak['value'])} % im {fmt_month(peak['month'])}."),
    }


def derive_events(record: Optional[Dict[str, Any]], max_months: int = 6,
                  start: str = START_MONTH) -> List[Dict[str, Any]]:
    """Allgemeine Ereignisse aus einem Stand der Reihen (reine Rechnung, testbar). Felder wie
    bisher in ``global_events.json``; ``confirmed`` ist immer true (keine Freigabe mehr, E29)."""
    if not record:
        return []
    hits = rule_hits(record.get("series") or {}, start)
    spans = []   # (von, bis, Regel)
    for rule, rule_hits_ in hits.items():
        for a, b in _runs([h["month"] for h in rule_hits_]):
            spans.append((a, b, rule))
    spans.sort()
    merged: List[Dict[str, Any]] = []
    for a, b, rule in spans:
        if merged and month_index(a) - month_index(merged[-1]["to"]) <= MERGE_GAP + 1:
            merged[-1]["to"] = max(merged[-1]["to"], b)
            merged[-1]["rules"].add(rule)
        else:
            merged.append({"from": a, "to": b, "rules": {rule}})

    fetched = str(record.get("fetched_at") or "")[:10]
    sources = record.get("sources") or {}
    events = []
    for span in merged:
        date_from, date_to = span["from"], span["to"]
        shortened = month_index(date_to) - month_index(date_from) + 1 > max_months
        if shortened:
            date_to = month_key(month_index(date_from) + max_months - 1)
        parts = []
        used = []
        for rule in (RULE_ESI, RULE_HICP):
            if rule not in span["rules"]:
                continue
            in_span = [h for h in hits[rule] if date_from <= h["month"] <= date_to]
            if in_span:
                parts.append(_rule_part(rule, in_span))
                used.append("esi" if rule == RULE_ESI else "hicp")
        if not parts:
            continue
        source_text = "; ".join(
            f"Eurostat {sources.get(n, SERIES[n]).get('dataset', SERIES[n]['dataset'])}" for n in used
        )
        note = " ".join(p["note"] for p in parts)
        if shortened:
            note += f" Auf die ersten {max_months} Monate gekürzt (Dauerregel E20)."
        note += f" Automatisch ermittelt (E29); Quelle: {source_text}, abgerufen {fetched}."
        events.append({
            "id": f"auto-{date_from}",
            "date_from": date_from,
            "date_to": date_to,
            "title": " und ".join(p["title"] for p in parts),
            "scope": SCOPE,
            "note": note,
            "url": SERIES[used[0]]["url"],
            "confirmed": True,
        })
    return events


def global_events(max_months: int = 6, fetcher: Optional[Fetcher] = None, path: Optional[Path] = None,
                  now: Optional[datetime] = None, live: Optional[bool] = None) -> List[Dict[str, Any]]:
    """Allgemeine Ereignisse aus dem aktuellen Stand der Wirtschaftsdaten (siehe Modulbeschreibung)."""
    state = macro_record(fetcher=fetcher, path=path, now=now, live=live)
    if state["error"]:
        logger.info("Allgemeine Ereignisse: %s", state["error"])
    return derive_events(state["record"], max_months=max_months)


def status(path: Optional[Path] = None) -> Dict[str, Any]:
    """Stand des Zwischenspeichers für die Route (ohne Abruf)."""
    cached = load_cached(path)
    return {
        "fetched_at": cached.get("fetched_at") if cached else None,
        "sources": cached.get("sources") if cached else {n: {k: s[k] for k in ("dataset", "label", "url")} for n, s in SERIES.items()},
    }


__all__ = [
    "CACHE_PATH", "ESI_DROP", "HICP_MIN", "HICP_RISE", "LOOKBACK", "MAX_AGE", "MERGE_GAP", "SERIES", "START_MONTH",
    "derive_events", "fetch_record", "global_events", "load_cached", "macro_record", "parse_eurostat", "rule_hits",
    "save_cached", "status",
]
