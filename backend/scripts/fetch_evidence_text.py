"""
Texte der Belege nachfüllen (Erweiterung der Erklärungsansätze um den Mitteilungs- und
Artikeltext, 2026-10-23, E35).

Füllt den Textspeicher ``backend/data/context_text/`` (``services/evidence_text.py``):

- ``--eqs``: alle gespeicherten EQS-Mitteilungen (Typ ``adhoc``) der Unternehmen aus dem
  Belegspeicher, Text von der öffentlichen Meldungsseite.
- ``--news``: die **Kandidaten** unter den Meldungen (Typ ``news``) in den Ereignisfenstern
  der Markierungen (Niveauwechsel und Einzelmonate, E18) und mit ``--comparison`` auch in
  den Vergleichsfenstern. Kandidat ist eine Meldung, die die beiden titel- und datums-
  abhängigen Regeln der strengen Auswahl (E33) erfüllt: Unternehmen im Titel genannt (oder
  nicht prüfbar) und zeitliche Nähe mindestens 0,5. Nur bei ihnen kann der Text die
  Auswahl ändern (Regeln 2 und 3); alle anderen Meldungen bleiben ausgeschlossen, mit oder
  ohne Text. Der Text wird über die Google-Weiterleitung und die Verlagsseite abgerufen.

Gespeicherte Texte werden übersprungen (fortsetzbar); gespeicherte Fehlschläge nur mit
``--retry-failed`` erneut versucht. Drosselung: Google News und EQS 2 s, Verlage 1 s je
Host. Nach ``MAX_CONSECUTIVE_ERRORS`` Fehlern in Folge je Weg (Google News bzw. EQS) bricht
der Lauf für diesen Weg ab und nennt das Unternehmen zum Fortsetzen. ``CONTEXT_LIVE_FETCH=0``
unterbindet jeden Abruf (dann nur zählen). Die Datenbank wird nur gelesen.

Verwendung
----------
    cd backend
    uv run python scripts/fetch_evidence_text.py --dry-run --eqs --news --comparison   # nur zählen
    uv run python scripts/fetch_evidence_text.py --eqs                                  # alle EQS-Mitteilungen
    uv run python scripts/fetch_evidence_text.py --news --comparison                    # Kandidaten der Fenster
    uv run python scripts/fetch_evidence_text.py --news --company 19 --max-fetches 50
    uv run python scripts/fetch_evidence_text.py --eqs --news --comparison --json data/calibration/evidence_text.json
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND_DIR)

from fetch_context import company_anchors, list_companies  # noqa: E402
from services import evidence_service as ev  # noqa: E402
from services import evidence_text as et  # noqa: E402
from services.evidence_sources import SOURCE_EQS, TYPE_ADHOC, TYPE_NEWS  # noqa: E402
from services.explanation_ranking import SELECTION_MIN_TIME, company_in_title, company_title_words, time_match  # noqa: E402
from services.review_terms import company_terms  # noqa: E402

MAX_CONSECUTIVE_ERRORS = 3
WAY_NEWS = "news"
WAY_EQS = "eqs"
WAY_LABELS = {WAY_NEWS: "Meldungen (Google News, Verlagsseiten)", WAY_EQS: "EQS-Mitteilungen (Meldungsseiten)"}


def marker_and_comparison_windows(anchors: Dict[str, Any], window_before: int, window_after: int,
                                  comparison: bool) -> List[Dict[str, Any]]:
    """Ereignisfenster der Markierungen eines Unternehmens, mit ``comparison`` auch die
    Vergleichsfenster (E18)."""
    markers = [ev.window_for_anomaly(a, window_before, window_after) for a in anchors["anomalies"]]
    markers += [ev.window_for_outlier(o["date"], window_before, window_after) for o in anchors["outliers"]]
    windows = list(markers)
    if comparison:
        for w in markers:
            windows.extend(ev.comparison_windows(w, markers, anchors.get("series_from"), anchors.get("series_to")))
    return windows


def is_candidate(item: Dict[str, Any], window: Dict[str, Any], name_words) -> bool:
    """Meldung, bei der der Text die strenge Auswahl noch ändern kann: Unternehmen im Titel
    genannt (oder nicht prüfbar) und zeitliche Nähe mindestens ``SELECTION_MIN_TIME``."""
    if item.get("source_type") != TYPE_NEWS:
        return False
    if company_in_title(item.get("title"), name_words) is False:
        return False
    return time_match(item.get("date"), window) >= SELECTION_MIN_TIME


def news_candidates(info: Dict[str, Any], windows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Kandidaten (je Kennung einmal) aus dem Belegspeicher aller Fenster; kein Abruf."""
    name_words = company_title_words(company_terms(info.get("name"), info.get("search_term")), info.get("title_words") or ())
    found: Dict[str, Dict[str, Any]] = {}
    for window in windows:
        evidence = ev.evidence_for_window(info, window, live=False, events=[])
        for item in evidence["items"]:
            if item.get("id") and item["id"] not in found and is_candidate(item, window, name_words):
                found[item["id"]] = item
    return list(found.values())


def stored_eqs_items(company_id: int) -> List[Dict[str, Any]]:
    """Alle EQS-Mitteilungen der Monatsdateien eines Unternehmens (je Kennung einmal)."""
    folder = ev.STORE_DIR / str(int(company_id)) / SOURCE_EQS
    found: Dict[str, Dict[str, Any]] = {}
    if not folder.is_dir():
        return []
    for path in sorted(folder.glob("*.json")):
        record = ev.load_record(company_id, SOURCE_EQS, path.stem)
        for item in (record or {}).get("items") or []:
            if item.get("source_type") == TYPE_ADHOC and item.get("id") and item["id"] not in found:
                found[item["id"]] = item
    return list(found.values())


def run(
    ways: List[str],
    company_ids: Optional[List[int]] = None,
    window_before: int = ev.DEFAULT_WINDOW_BEFORE,
    window_after: int = ev.DEFAULT_WINDOW_AFTER,
    comparison: bool = False,
    dry_run: bool = False,
    max_fetches: Optional[int] = None,
    retry_failed: bool = False,
    verbose: bool = True,
    max_consecutive_errors: int = MAX_CONSECUTIVE_ERRORS,
) -> Dict[str, Any]:
    """Nachfüllen; liefert die Zusammenfassung (auch bei ``dry_run``)."""
    started = time.monotonic()
    now = datetime.now(timezone.utc)
    live = ev.live_fetch_enabled() and not dry_run
    companies = [c for c in list_companies() if not company_ids or c["id"] in company_ids]
    summary: Dict[str, Any] = {
        "generated_at": now.isoformat(timespec="seconds"), "ways": list(ways), "comparison": comparison,
        "window_before": window_before, "window_after": window_after, "live": live, "dry_run": dry_run,
        "retry_failed": retry_failed, "companies": [], "fetches": 0, "fetch_limit_reached": False,
        "min_text_chars": et.MIN_TEXT_CHARS, "max_text_chars": et.MAX_TEXT_CHARS,
    }
    totals = {w: {"label": WAY_LABELS[w], "candidates": 0, "stored": 0, "fetched_now": 0, "ok": 0, "kurz": 0,
                  "fehlgeschlagen": 0, "skipped": 0, "errors": []} for w in ways}
    summary["ways_summary"] = totals
    fetches = 0
    consecutive = {w: 0 for w in ways}
    for company in companies:
        entry: Dict[str, Any] = {"company_id": company["id"], "name": company["name"], "ways": {}}
        try:
            info = ev.company_context_info(company["id"])
            anchors = company_anchors(company["id"]) if WAY_NEWS in ways else None
        except Exception as exc:  # noqa: BLE001 – Datenbank oder Netz kurz weg: dieses Unternehmen überspringen, der Lauf geht weiter
            entry["error"] = f"{type(exc).__name__}: {exc}"[:200]
            summary["companies"].append(entry)
            if verbose:
                print(f"  {company['name']:<40} übersprungen: {entry['error']}", flush=True)
            continue
        if info is None:
            entry["error"] = "Unternehmen nicht auflösbar"
            summary["companies"].append(entry)
            continue
        plans: Dict[str, List[Dict[str, Any]]] = {}
        if WAY_NEWS in ways:
            entry["eligible"] = anchors["eligible"]
            if anchors["eligible"]:
                windows = marker_and_comparison_windows(anchors, window_before, window_after, comparison)
                entry["n_windows"] = len(windows)
                plans[WAY_NEWS] = news_candidates(info, windows)
            else:
                plans[WAY_NEWS] = []
        if WAY_EQS in ways:
            plans[WAY_EQS] = stored_eqs_items(company["id"])
        for way, items in plans.items():
            t = totals[way]
            c = {"candidates": len(items), "stored": 0, "fetched_now": 0, "ok": 0, "kurz": 0, "fehlgeschlagen": 0,
                 "skipped": 0, "errors": 0}
            t["candidates"] += len(items)
            for item in items:
                if t.get("aborted"):
                    c["skipped"] += 1
                    t["skipped"] += 1
                    continue
                allow = live and (max_fetches is None or fetches < max_fetches)
                stored_before = et.load_text(company["id"], item["id"])
                if not allow and (stored_before is None or (stored_before.get("status") == et.STATUS_FAILED and retry_failed)):
                    c["skipped"] += 1
                    t["skipped"] += 1
                    if max_fetches is not None and fetches >= max_fetches and live:
                        summary["fetch_limit_reached"] = True
                    continue
                result = et.text_record(company["id"], item, fetch=allow, retry_failed=retry_failed,
                                        sleep=time.sleep, clock=time.monotonic, now=now)
                record = result["record"]
                if result["fetched_now"]:
                    fetches += 1
                    c["fetched_now"] += 1
                    t["fetched_now"] += 1
                else:
                    c["stored"] += 1
                    t["stored"] += 1
                status = (record or {}).get("status")
                if status in ("ok", "kurz", "fehlgeschlagen"):
                    c[status] += 1
                    t[status] += 1
                if result["fetched_now"]:
                    if status == et.STATUS_FAILED:
                        c["errors"] += 1
                        if len(t["errors"]) < 50:
                            t["errors"].append({"company_id": company["id"], "id": item["id"], "error": record.get("error")})
                        # Nur ein Fehler vor der Verlagsseite (keine Zieladresse) zählt als Fehler des Wegs;
                        # eine Verlagsseite, die nicht antwortet, bricht den Lauf nicht ab.
                        if way == WAY_EQS or not record.get("target_url"):
                            consecutive[way] += 1
                            if consecutive[way] >= max_consecutive_errors:
                                t["aborted"] = {"company_id": company["id"], "company": company["name"],
                                                "after_errors": consecutive[way], "last_error": record.get("error")}
                    else:
                        consecutive[way] = 0
            entry["ways"][way] = c
            if verbose:
                print(f"  {company['name']:<40} {way:<5} Kandidaten {c['candidates']:>4}  gespeichert {c['stored']:>4}"
                      f"  neu {c['fetched_now']:>4}  ok {c['ok']:>4}  kurz {c['kurz']:>3}  fehlgeschlagen {c['fehlgeschlagen']:>3}"
                      f"  übersprungen {c['skipped']:>4}", flush=True)
        summary["companies"].append(entry)
    summary["fetches"] = fetches
    summary["duration_s"] = round(time.monotonic() - started, 1)
    return summary


def format_summary(summary: Dict[str, Any]) -> str:
    lines = ["Texte der Belege nachfüllen (E35)"]
    mode = "nur zählen (--dry-run)" if summary["dry_run"] else ("Abruf erlaubt" if summary["live"] else
                                                             f"kein Abruf ({ev.LIVE_FETCH_ENV}=0), nur Speicher")
    lines.append(f"  Modus: {mode}; Fenster {summary['window_before']} Monate davor, {summary['window_after']} danach"
                 + ("; dazu die Vergleichsfenster" if summary.get("comparison") else "")
                 + f"; Dauer {summary['duration_s']} s; Abrufe in diesem Lauf: {summary['fetches']}"
                 + (" (Grenze erreicht)" if summary["fetch_limit_reached"] else ""))
    skipped = [c for c in summary["companies"] if c.get("error") and c["error"] != "Unternehmen nicht auflösbar"]
    if skipped:
        lines.append("  Übersprungene Unternehmen (Datenbank oder Netz nicht erreichbar, erneut laufen lassen): "
                     + ", ".join(f"{c['name']} ({c['company_id']})" for c in skipped))
    for way, t in summary["ways_summary"].items():
        lines.append(f"  {t['label']} ({way}): Kandidaten {t['candidates']}, gespeichert {t['stored']}, neu {t['fetched_now']}, "
                     f"ok {t['ok']}, kurz {t['kurz']}, fehlgeschlagen {t['fehlgeschlagen']}, übersprungen {t['skipped']}")
        for e in t["errors"][:10]:
            lines.append(f"      - Unternehmen {e['company_id']}, Beleg {e['id']}: {e['error']}")
        if len(t["errors"]) > 10:
            lines.append(f"      … {len(t['errors']) - 10} weitere")
        if t.get("aborted"):
            a = t["aborted"]
            lines.append(f"    ABGEBROCHEN nach {a['after_errors']} Fehlern in Folge bei {a['company']} ({a['company_id']}): "
                         f"{a['last_error']}; {t['skipped']} übersprungen. Fortsetzen nach einer Pause: "
                         f"uv run python scripts/fetch_evidence_text.py --{way} --company {a['company_id']} … und die weiteren Unternehmen.")
    return "\n".join(lines)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--eqs", action="store_true", help="alle gespeicherten EQS-Mitteilungen")
    parser.add_argument("--news", action="store_true", help="Kandidaten unter den Meldungen der Markierungsfenster")
    parser.add_argument("--comparison", action="store_true", help="mit --news auch die Vergleichsfenster")
    parser.add_argument("--company", action="append", type=int, help="nur dieses Unternehmen (id), mehrfach möglich")
    parser.add_argument("--window-before", type=int, default=ev.DEFAULT_WINDOW_BEFORE)
    parser.add_argument("--window-after", type=int, default=ev.DEFAULT_WINDOW_AFTER)
    parser.add_argument("--dry-run", action="store_true", help="nichts abrufen, nur zählen")
    parser.add_argument("--max-fetches", type=int, default=None, help="höchstens so viele Abrufe in diesem Lauf")
    parser.add_argument("--retry-failed", action="store_true", help="gespeicherte Fehlschläge erneut versuchen")
    parser.add_argument("--max-consecutive-errors", type=int, default=MAX_CONSECUTIVE_ERRORS)
    parser.add_argument("--json", dest="json_out", help="Zusammenfassung zusätzlich als JSON-Datei")
    parser.add_argument("--quiet", action="store_true", help="keine Zeile je Unternehmen und Weg")
    args = parser.parse_args(argv)
    ways = [w for w, on in ((WAY_EQS, args.eqs), (WAY_NEWS, args.news)) if on]
    if not ways:
        parser.error("mindestens --eqs oder --news angeben")
    summary = run(ways, company_ids=args.company, window_before=args.window_before, window_after=args.window_after,
                  comparison=args.comparison, dry_run=args.dry_run, max_fetches=args.max_fetches,
                  retry_failed=args.retry_failed, verbose=not args.quiet, max_consecutive_errors=args.max_consecutive_errors)
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
