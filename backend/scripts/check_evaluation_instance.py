"""
Abnahme der Evaluationsinstanz (DZ3, Inkrement 6), nur lesend.

Geprüft werden

1. **Umgebung:** ``MARKET_LIVE_FETCH=0`` und ``CONTEXT_LIVE_FETCH=0`` (Umgebung des
   Prozesses oder ``backend/.env``), ``VITE_SHOW_FINANCE_EXTRAS=false`` und
   ``VITE_SHOW_FORECAST=false`` (Umgebung oder ``frontend/.env.local``). Aus den
   Dateien werden nur diese vier Schlüssel gelesen; andere Zeilen (Zugangsdaten)
   werden weder ausgewertet noch ausgegeben.
2. **Kurs-Zwischenspeicher** (``backend/data/market/``): Für jede Markierung
   (Niveauwechsel und Einzelmonate, Mitarbeitende, Gesamtbewertung,
   Standardparameter) der geeigneten Unternehmen liegen die Monate des
   Ereignisfensters im gespeicherten Kursverlauf. Monate vor dem ersten
   gespeicherten Kurs (vor Börsengang oder Datenbeginn) sind ein Hinweis, keine
   Lücke; fehlende Monate innerhalb des Verlaufs oder nach seinem Ende sind Lücken.
   Unternehmen ohne Ticker: Hinweis.
3. **Belegspeicher** (``backend/data/context/``): Für jedes Markierungsfenster liegt
   jeder Monat je Quelle im Speicher (``evidence_for_window`` ohne Abruf).
4. **Stimmungsmodus:** ``SentimentAnalyzer(mode="transformer")`` mit
   ``HF_HUB_OFFLINE=1`` (kein Netz); ``lexicon`` ist eine Warnung, keine Lücke
   (``docs/evaluationsinstanz.md``, 2.3).
5. **Antwortzeiten** der Endpunkte des laufenden Backends (``--api``) je Unternehmen;
   über ``SLOW_SECONDS`` = 3 s eine Warnung (Setzung des Autors), kein Antwortcode
   200 oder keine Verbindung ein Fehler.

Ausgabe als Tabelle (Markdown); Exit-Code 1 bei einer Lücke oder einem Fehler, sonst 0.
Die Datenbank wird nur gelesen (Unternehmen, Markierungen), es gibt keinen Abruf
bei Yahoo Finance, Google News oder EQS und keinen Schreibzugriff.

Verwendung
----------
    cd backend
    uv run python scripts/check_evaluation_instance.py                       # Backend unter http://localhost:8000
    uv run python scripts/check_evaluation_instance.py --api http://localhost:8002 --json ../abnahme.json
    uv run python scripts/check_evaluation_instance.py --skip-api --skip-sentiment
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO_DIR = os.path.dirname(BACKEND_DIR)
sys.path.insert(0, BACKEND_DIR)
sys.path.insert(0, os.path.join(BACKEND_DIR, "scripts"))

BACKEND_ENV_FILE = os.path.join(BACKEND_DIR, ".env")
FRONTEND_ENV_FILE = os.path.join(REPO_DIR, "frontend", ".env.local")

# Erwartete Werte der Evaluationsinstanz (docs/evaluationsinstanz.md, D2, D3)
BACKEND_EXPECTED = {"MARKET_LIVE_FETCH": "0", "CONTEXT_LIVE_FETCH": "0"}
FRONTEND_EXPECTED = {"VITE_SHOW_FINANCE_EXTRAS": "false", "VITE_SHOW_FORECAST": "false"}
FALSE_VALUES = {"false", "0"}

SLOW_SECONDS = 3.0             # Antwortzeit ab der eine Warnung erscheint (Setzung)
REQUEST_TIMEOUT = 120.0

OK, HINT, WARN, GAP, ERROR = "ok", "Hinweis", "Warnung", "Lücke", "Fehler"
FAILING = {GAP, ERROR}

# Endpunkte je Unternehmen in der Reihenfolge der Ansichten (Dashboard, Anomalien, Aktie)
ENDPOINTS: Tuple[Tuple[str, str], ...] = (
    ("Ø Score", "/api/companies/{id}/ratings"),
    ("Trend", "/api/companies/{id}/ratings/trend?mode=score_months&months=12"),
    ("12/24 Monate", "/api/companies/{id}/ratings/trend?mode=rolling"),
    ("Datenstand", "/api/companies/{id}/data-status"),
    ("Zeitverlauf", "/api/analytics/company/{id}/timeline?days=3650&forecast_months=0&source=employee"),
    ("Topic-Übersicht", "/api/analytics/company/{id}/topic-overview"),
    ("Anomalien", "/api/analytics/company/{id}/anomalies"),
    ("Kurs", "/api/analytics/company/{id}/market"),
)


# ── Umgebung ─────────────────────────────────────────────────────────────────

def read_env_keys(path: str, keys: Iterable[str]) -> Dict[str, str]:
    """Nur die genannten Schlüssel aus einer ``.env``-Datei (``KEY=value``); andere Zeilen
    werden übersprungen und nie zurückgegeben."""
    wanted = set(keys)
    found: Dict[str, str] = {}
    if not os.path.exists(path):
        return found
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip().removeprefix("export ").strip()
            if key in wanted:
                found[key] = value.strip().strip('"').strip("'")
    return found


def env_checks(environ: Dict[str, str], backend_file: Dict[str, str], frontend_file: Dict[str, str]) -> List[Dict[str, Any]]:
    """Zeilen der Umgebungsprüfung; reine Funktion. Die Umgebung hat Vorrang vor den Dateien."""
    rows = []
    for key, expected in BACKEND_EXPECTED.items():
        value, origin = (environ[key], "Umgebung") if key in environ else (backend_file.get(key), "backend/.env")
        ok = value is not None and value.strip() == expected
        rows.append({"area": "Umgebung", "check": key, "result": f"{value if value is not None else 'nicht gesetzt'} ({origin})",
                     "status": OK if ok else ERROR})
    for key in FRONTEND_EXPECTED:
        value, origin = (environ[key], "Umgebung") if key in environ else (frontend_file.get(key), "frontend/.env.local")
        ok = value is not None and value.strip().lower() in FALSE_VALUES
        rows.append({"area": "Umgebung", "check": key, "result": f"{value if value is not None else 'nicht gesetzt'} ({origin})",
                     "status": OK if ok else ERROR})
    return rows


# ── Kurs-Zwischenspeicher ────────────────────────────────────────────────────

def market_window_check(price_months: Iterable[str], windows: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Abdeckung der Fenstermonate durch den Kursverlauf; reine Funktion.

    ``before_start``: Monate vor dem ersten Kurs (Hinweis); ``missing``: Monate innerhalb
    des Verlaufs ohne Kurs oder nach dem letzten Kurs (Lücke)."""
    from services.evidence_service import window_months

    months = sorted(set(price_months))
    have = set(months)
    first, last = (months[0], months[-1]) if months else (None, None)
    before_start: set = set()
    missing: set = set()
    for w in windows:
        for m in window_months(w):
            if m in have:
                continue
            if first is not None and m < first:
                before_start.add(m)
            else:
                missing.add(m)
    return {"first": first, "last": last, "windows": len(windows),
            "before_start": sorted(before_start), "missing": sorted(missing)}


def market_row(company: str, ticker: Optional[str], record: Optional[Dict[str, Any]], windows: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not ticker:
        return {"area": "Kurs", "check": company, "result": "kein Ticker", "status": HINT}
    if record is None:
        return {"area": "Kurs", "check": company, "result": f"{ticker}: kein Zwischenspeicher", "status": GAP}
    res = market_window_check([p["period"] for p in record.get("prices") or [] if p.get("period")], windows)
    parts = [f"{ticker}: {res['first'] or '–'} bis {res['last'] or '–'}, {res['windows']} Fenster"]
    if res["missing"]:
        parts.append(f"{len(res['missing'])} Monate fehlen ({res['missing'][0]} … {res['missing'][-1]})")
    if res["before_start"]:
        parts.append(f"{len(res['before_start'])} Monate vor dem ersten Kurs")
    status = GAP if res["missing"] else HINT if res["before_start"] else OK
    return {"area": "Kurs", "check": company, "result": "; ".join(parts), "status": status}


# ── Belegspeicher ────────────────────────────────────────────────────────────

def evidence_row(company: str, window_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """``window_results``: je Fenster ``{"sources": {quelle: {"missing": n, "months": m}}}`` aus
    ``evidence_for_window(live=False)``; reine Funktion."""
    per_source: Dict[str, List[int]] = {}
    for r in window_results:
        for source, s in (r.get("sources") or {}).items():
            agg = per_source.setdefault(source, [0, 0])
            agg[0] += int(s.get("months") or 0)
            agg[1] += int(s.get("missing") or 0)
    if not window_results:
        return {"area": "Belege", "check": company, "result": "keine Markierung", "status": OK}
    missing = sum(v[1] for v in per_source.values())
    detail = ", ".join(f"{src} {v[0] - v[1]}/{v[0]} Monate" for src, v in sorted(per_source.items()))
    return {"area": "Belege", "check": company, "result": f"{len(window_results)} Fenster; {detail}",
            "status": GAP if missing else OK}


# ── Antwortzeiten ────────────────────────────────────────────────────────────

def http_get(url: str, timeout: float = REQUEST_TIMEOUT) -> Tuple[Optional[int], float, Optional[str]]:
    """(Status, Sekunden, Fehler); nur GET."""
    start = time.perf_counter()
    try:
        with urllib.request.urlopen(urllib.request.Request(url, method="GET"), timeout=timeout) as resp:
            resp.read()
            return resp.status, time.perf_counter() - start, None
    except urllib.error.HTTPError as exc:
        return exc.code, time.perf_counter() - start, f"HTTP {exc.code}"
    except Exception as exc:  # noqa: BLE001 – Verbindung, Zeitüberschreitung
        return None, time.perf_counter() - start, f"{type(exc).__name__}"


def timing_rows(api: str, companies: List[Dict[str, Any]], getter: Callable[[str], Tuple[Optional[int], float, Optional[str]]] = http_get,
                slow: float = SLOW_SECONDS) -> List[Dict[str, Any]]:
    """Je Endpunkt: höchste Antwortzeit über die Unternehmen, Fehlerzahl; reine Funktion bis auf ``getter``."""
    rows = []
    for label, path in ENDPOINTS:
        times: List[Tuple[float, str]] = []
        errors: List[str] = []
        for c in companies:
            status, seconds, err = getter(api.rstrip("/") + path.format(id=c["id"]))
            times.append((seconds, c["name"]))
            if status != 200:
                errors.append(f"{c['name']}: {err or status}")
        worst = max(times) if times else (0.0, "–")
        median = sorted(t for t, _ in times)[len(times) // 2] if times else 0.0
        result = (f"Median {median:.2f} s, Maximum {worst[0]:.2f} s ({worst[1]}), {len(companies)} Unternehmen"
                  + (f"; {len(errors)} Fehler: {'; '.join(errors[:3])}" if errors else ""))
        status = ERROR if errors else WARN if worst[0] > slow else OK
        rows.append({"area": "Antwortzeit", "check": label, "result": result, "status": status})
    return rows


# ── Stimmungsmodus ───────────────────────────────────────────────────────────

def sentiment_row() -> Dict[str, Any]:
    os.environ.setdefault("HF_HUB_OFFLINE", "1")   # kein Netz zu Hugging Face
    start = time.perf_counter()
    try:
        from models.sentiment_analyzer import SentimentAnalyzer

        mode = SentimentAnalyzer(mode="transformer").mode
    except Exception as exc:  # noqa: BLE001
        return {"area": "Stimmung", "check": "Modus", "result": f"nicht prüfbar ({type(exc).__name__})", "status": WARN}
    seconds = time.perf_counter() - start
    return {"area": "Stimmung", "check": "Modus", "result": f"{mode} (Laden {seconds:.1f} s, ohne Netz)",
            "status": OK if mode == "transformer" else WARN}


# ── Ablauf ───────────────────────────────────────────────────────────────────

def eligible_companies() -> List[Dict[str, Any]]:
    """Geeignete Unternehmen mit Markierungsfenstern (Datenbank nur lesend)."""
    from fetch_context import company_anchors, list_companies
    from services import evidence_service as ev

    out = []
    for company in list_companies():
        anchors = company_anchors(company["id"])
        if not anchors["eligible"]:
            continue
        windows = [ev.window_for_anomaly(a) for a in anchors["anomalies"]]
        windows += [ev.window_for_outlier(o["date"]) for o in anchors["outliers"]]
        out.append({**company, "windows": windows, "n_anomalies": len(anchors["anomalies"]),
                    "n_outliers": len(anchors["outliers"])})
    return out


def store_rows(companies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    from services import context_service as cs
    from services import evidence_service as ev

    rows = []
    metadata = cs.load_metadata()
    for c in companies:
        info = cs.company_ticker_info(c["id"], metadata=metadata)
        ticker = (info or {}).get("ticker")
        rows.append(market_row(c["name"], ticker, cs.load_cached(ticker) if ticker else None, c["windows"]))
    for c in companies:
        info = ev.company_context_info(c["id"])
        results = [ev.evidence_for_window(info, w, live=False, events=[]) for w in c["windows"]] if info else []
        rows.append(evidence_row(c["name"], results))
    return rows


def format_table(rows: List[Dict[str, Any]]) -> str:
    lines = ["| Bereich | Prüfung | Ergebnis | Status |", "|---|---|---|---|"]
    lines += [f"| {r['area']} | {r['check']} | {r['result']} | {r['status']} |" for r in rows]
    return "\n".join(lines)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--api", default="http://localhost:8000", help="laufendes Backend (Default: http://localhost:8000)")
    parser.add_argument("--skip-api", action="store_true", help="Antwortzeiten nicht messen")
    parser.add_argument("--skip-sentiment", action="store_true", help="Stimmungsmodell nicht laden")
    parser.add_argument("--json", dest="json_out", help="Zeilen zusätzlich als JSON-Datei schreiben")
    args = parser.parse_args(argv)

    rows = env_checks(dict(os.environ), read_env_keys(BACKEND_ENV_FILE, BACKEND_EXPECTED),
                      read_env_keys(FRONTEND_ENV_FILE, FRONTEND_EXPECTED))
    companies = eligible_companies()
    rows.append({"area": "Unternehmen", "check": "geeignet (E4)",
                 "result": f"{len(companies)}: " + ", ".join(f"{c['name']} ({c['n_anomalies']}+{c['n_outliers']})" for c in companies),
                 "status": OK if len(companies) == 15 else WARN})
    rows += store_rows(companies)
    if not args.skip_sentiment:
        rows.append(sentiment_row())
    if not args.skip_api:
        rows += timing_rows(args.api, companies)
    print(format_table(rows))
    failing = [r for r in rows if r["status"] in FAILING]
    print(f"\nErgebnis: {len(failing)} Lücken oder Fehler" if failing else "\nErgebnis: keine Lücke, kein Fehler")
    if args.json_out:
        with open(args.json_out, "w", encoding="utf-8") as fh:
            json.dump(rows, fh, ensure_ascii=False, indent=2)
            fh.write("\n")
    return 1 if failing else 0


if __name__ == "__main__":
    sys.exit(main())
