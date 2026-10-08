"""
Vorabruf der externen Belege (Zyklus 2, Inkrement 4, Schritt 4).

Füllt den Belegspeicher ``backend/data/context/`` für alle Niveauwechsel und
auffälligen Einzelmonate der nach E4 geeigneten Unternehmen (Mitarbeitende,
Gesamtbewertung, Standardparameter der Erkennung): je Markierung das
Ereignisfenster (E18), daraus die Kalendermonate je Unternehmen, und je Quelle
und Monat ein Abruf, gedrosselt (mindestens 2 s je Quelle). Gespeicherte
Monate werden übersprungen; ein abgebrochener Lauf lässt sich damit
fortsetzen. Die Datenbank wird nur gelesen (Reihen und Erkennung), geschrieben
wird nur in den Belegspeicher.

Quellen: Google News RSS immer, EQS für Unternehmen mit companyUUID in der
Metadatei (Schritt 5), GDELT nur mit ``CONTEXT_GDELT=1``. Mit
``CONTEXT_LIVE_FETCH=0`` ruft das Skript nichts ab und zählt nur.

Verwendung
----------
    cd backend
    uv run python scripts/fetch_context.py                   # alle Quellen, alle geeigneten Unternehmen
    uv run python scripts/fetch_context.py --dry-run         # nur zählen: Markierungen, Monate, fehlende Monate
    uv run python scripts/fetch_context.py --source gnews --company 19 --company 28
    uv run python scripts/fetch_context.py --max-fetches 50  # Teil-Lauf, später fortsetzen
    uv run python scripts/fetch_context.py --json data/calibration/context_prefetch.json
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND_DIR)

from services import evidence_service as ev  # noqa: E402
from services.anomaly_service import company_anomalies  # noqa: E402
from services.evidence_sources import MIN_FETCH_INTERVAL_S, SOURCE_LABELS  # noqa: E402
from services.rating_series_service import OVERALL_DIMENSION  # noqa: E402

SOURCE = "employee"
DIMENSION = OVERALL_DIMENSION
_DEMO_RE = re.compile(r"^demo\s*\d+$")


def is_demo_company(name: str) -> bool:
    return _DEMO_RE.match(" ".join(str(name).split()).casefold()) is not None


def list_companies() -> List[Dict[str, Any]]:
    """Alle realen Unternehmen (id, Name) aus der Datenbank, nur SELECT."""
    from database.supabase_client import get_supabase_client

    rows = get_supabase_client().table("companies").select("id,name").order("id").execute().data or []
    return [{"id": int(r["id"]), "name": " ".join(str(r["name"]).split())} for r in rows if not is_demo_company(r["name"])]


def company_anchors(company_id: int) -> Dict[str, Any]:
    """Niveauwechsel und Einzelmonate eines Unternehmens (Standardparameter) oder
    ``eligible: False``; nur lesend."""
    result = company_anomalies(company_id, source=SOURCE, dimension=DIMENSION)
    return {
        "eligible": bool(result["eligibility"]["eligible"]),
        "anomalies": result["anomalies"],
        "outliers": result.get("outlier_months") or [],
    }


def months_for_anchors(anchors: Dict[str, Any], window_before: int, window_after: int) -> Dict[str, Any]:
    """Kalendermonate aller Fenster eines Unternehmens, dazu die Fenster je Markierung."""
    windows = []
    months: Set[str] = set()
    for anomaly in anchors["anomalies"]:
        w = ev.window_for_anomaly(anomaly, window_before, window_after)
        windows.append({"id": anomaly["id"], "kind": w["kind"], "from": w["from"], "to": w["to"]})
        months.update(ev.window_months(w))
    for outlier in anchors["outliers"]:
        w = ev.window_for_outlier(outlier["date"], window_before, window_after)
        windows.append({"id": outlier["id"], "kind": w["kind"], "from": w["from"], "to": w["to"]})
        months.update(ev.window_months(w))
    return {"windows": windows, "months": sorted(months)}


def run(
    sources: Optional[List[str]] = None,
    company_ids: Optional[List[int]] = None,
    window_before: int = ev.DEFAULT_WINDOW_BEFORE,
    window_after: int = ev.DEFAULT_WINDOW_AFTER,
    dry_run: bool = False,
    max_fetches: Optional[int] = None,
    interval: float = MIN_FETCH_INTERVAL_S,
    verbose: bool = True,
) -> Dict[str, Any]:
    """Vorabruf; liefert die Zusammenfassung (auch bei ``dry_run``)."""
    started = time.monotonic()
    now = datetime.now(timezone.utc)
    live = ev.live_fetch_enabled() and not dry_run
    companies = [c for c in list_companies() if not company_ids or c["id"] in company_ids]
    summary: Dict[str, Any] = {
        "generated_at": now.isoformat(timespec="seconds"),
        "window_before": window_before, "window_after": window_after,
        "live": live, "dry_run": dry_run, "live_fetch_env": ev.live_fetch_enabled(),
        "companies": [], "sources": {}, "fetch_limit_reached": False,
    }
    fetches = 0
    stopped = False
    for company in companies:
        anchors = company_anchors(company["id"])
        entry: Dict[str, Any] = {"company_id": company["id"], "name": company["name"], "eligible": anchors["eligible"],
                                 "n_changes": len(anchors["anomalies"]), "n_outliers": len(anchors["outliers"]),
                                 "months": 0, "sources": {}}
        if not anchors["eligible"]:
            summary["companies"].append(entry)
            continue
        plan = months_for_anchors(anchors, window_before, window_after)
        entry["months"] = len(plan["months"])
        entry["windows"] = plan["windows"]
        info = ev.company_context_info(company["id"])
        if info is None:
            entry["error"] = "Unternehmen nicht auflösbar"
            summary["companies"].append(entry)
            continue
        entry["search_term"] = info["search_term"]
        entry["term_confirmed"] = info["term_confirmed"]
        used_sources = [s for s in ev.available_sources(info) if not sources or s in sources]
        for source in used_sources:
            s_sum = summary["sources"].setdefault(source, {"label": SOURCE_LABELS.get(source, source), "companies": 0,
                                                            "months": 0, "from_store": 0, "fetched_now": 0,
                                                            "missing": 0, "errors": [], "items": 0})
            s_sum["companies"] += 1
            c_src = {"months": len(plan["months"]), "from_store": 0, "fetched_now": 0, "missing": 0, "errors": 0, "items": 0}
            for month in plan["months"]:
                if stopped:
                    c_src["missing"] += 1
                    s_sum["missing"] += 1
                    continue
                allow = live and (max_fetches is None or fetches < max_fetches)
                result = ev.month_record(info, source, month, now=now, live=allow,
                                         sleep=time.sleep, clock=time.monotonic)
                s_sum["months"] += 1
                if result["fetched_now"]:
                    fetches += 1
                    c_src["fetched_now"] += 1
                    s_sum["fetched_now"] += 1
                elif result["record"] is not None:
                    c_src["from_store"] += 1
                    s_sum["from_store"] += 1
                else:
                    c_src["missing"] += 1
                    s_sum["missing"] += 1
                if result["record"] is not None:
                    n = len(result["record"].get("items") or [])
                    c_src["items"] += n
                    s_sum["items"] += n
                if result["error"] and live:
                    c_src["errors"] += 1
                    s_sum["errors"].append({"company_id": company["id"], "month": month, "error": result["error"]})
                if max_fetches is not None and fetches >= max_fetches and live:
                    summary["fetch_limit_reached"] = True
            entry["sources"][source] = c_src
            if verbose:
                print(f"  {company['name']:<40} {source:<6} Monate {c_src['months']:>3}  gespeichert {c_src['from_store']:>3}"
                      f"  neu {c_src['fetched_now']:>3}  fehlend {c_src['missing']:>3}  Fehler {c_src['errors']:>2}  Belege {c_src['items']:>5}")
        summary["companies"].append(entry)
    summary["fetches"] = fetches
    summary["duration_s"] = round(time.monotonic() - started, 1)
    return summary


def format_summary(summary: Dict[str, Any]) -> str:
    lines = ["Vorabruf der externen Belege (Inkrement 4)"]
    mode = "nur zählen (--dry-run)" if summary["dry_run"] else ("Abruf erlaubt" if summary["live"] else
                                                             f"kein Abruf ({ev.LIVE_FETCH_ENV}=0), nur Speicher")
    lines.append(f"  Modus: {mode}; Fenster {summary['window_before']} Monate davor, {summary['window_after']} danach; "
                 f"Dauer {summary['duration_s']} s; Abrufe in diesem Lauf: {summary['fetches']}"
                 + (" (Grenze erreicht)" if summary["fetch_limit_reached"] else ""))
    eligible = [c for c in summary["companies"] if c["eligible"]]
    lines.append(f"  Unternehmen: {len(summary['companies'])}, geeignet {len(eligible)}; Markierungen: "
                 f"{sum(c['n_changes'] for c in eligible)} Niveauwechsel, {sum(c['n_outliers'] for c in eligible)} Einzelmonate; "
                 f"Monate (je Unternehmen zusammengefasst): {sum(c['months'] for c in eligible)}")
    for source, s in summary["sources"].items():
        lines.append(f"  {s['label']} ({source}): {s['companies']} Unternehmen, {s['months']} Monate, gespeichert {s['from_store']}, "
                     f"neu {s['fetched_now']}, fehlend {s['missing']}, Fehler {len(s['errors'])}, Belege {s['items']}")
        for e in s["errors"][:10]:
            lines.append(f"      - Unternehmen {e['company_id']}, {e['month']}: {e['error']}")
        if len(s["errors"]) > 10:
            lines.append(f"      … {len(s['errors']) - 10} weitere")
    unconfirmed = [c["name"] for c in eligible if not c.get("term_confirmed", True)]
    if unconfirmed:
        lines.append(f"  Suchbegriffe noch nicht vom Autor bestätigt: {', '.join(unconfirmed)}")
    return "\n".join(lines)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--source", action="append", choices=["gnews", "eqs", "gdelt"], help="nur diese Quelle(n)")
    parser.add_argument("--company", action="append", type=int, help="nur dieses Unternehmen (id), mehrfach möglich")
    parser.add_argument("--window-before", type=int, default=ev.DEFAULT_WINDOW_BEFORE)
    parser.add_argument("--window-after", type=int, default=ev.DEFAULT_WINDOW_AFTER)
    parser.add_argument("--dry-run", action="store_true", help="nichts abrufen, nur zählen")
    parser.add_argument("--max-fetches", type=int, default=None, help="höchstens so viele Abrufe in diesem Lauf")
    parser.add_argument("--json", dest="json_out", help="Zusammenfassung zusätzlich als JSON-Datei")
    parser.add_argument("--quiet", action="store_true", help="keine Zeile je Unternehmen und Quelle")
    args = parser.parse_args(argv)
    summary = run(sources=args.source, company_ids=args.company, window_before=args.window_before,
                  window_after=args.window_after, dry_run=args.dry_run, max_fetches=args.max_fetches,
                  verbose=not args.quiet)
    print(format_summary(summary))
    if args.json_out:
        os.makedirs(os.path.dirname(os.path.abspath(args.json_out)), exist_ok=True)
        with open(args.json_out, "w", encoding="utf-8") as fh:
            json.dump(summary, fh, ensure_ascii=False, indent=2)
            fh.write("\n")
        print(f"Zusammenfassung gespeichert: {args.json_out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
