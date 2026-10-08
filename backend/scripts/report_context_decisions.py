"""
Entscheidungsvorlagen für die externen Belege (Zyklus 2, Inkrement 4,
Nachschärfung A4). Nur lesend, nur Zahlen: kein Abruf, keine Schlagzeile.

Vier Vorlagen für den Autor:

- D1 Suchbegriffe: je Unternehmen mit Markierungen der Suchbegriff, die
  Ausschlussbegriffe, die gespeicherten Monate und Meldungen je Monat sowie der
  Anteil der Titel, die den Unternehmensnamen nennen (Wortteile des
  Suchbegriffs oder der Name ohne Rechtsform, Groß- und Kleinschreibung egal).
- D2 EQS: je Unternehmen mit companyUUID der Emittentenname aus der Metadatei
  und die Emittentennamen, die in den gespeicherten Mitteilungen stehen.
- D3 Allgemeine Ereignisse: die Liste aus ``global_events.json`` mit Zeitraum,
  Dauer und Adresse (Dauerregel: höchstens 6 Monate).
- D4 Vorabruf: Vorschlag, für welche Unternehmen alle Monate ab einem
  Startmonat geladen werden (Ausgangspunkt: Unternehmen mit Markierungen ab
  2019), mit fehlenden Monaten je Quelle, Zahl der Abrufe und geschätzter
  Dauer; dazu die fehlenden Monate der Vergleichsfenster.

Verwendung
----------
    cd backend
    uv run python scripts/report_context_decisions.py
    uv run python scripts/report_context_decisions.py --from-month 2019-01 --json data/calibration/context_decisions.json
"""

from __future__ import annotations

import argparse
import json
import os
import re
import statistics
import sys
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional, Set

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND_DIR)
sys.path.insert(0, os.path.join(BACKEND_DIR, "scripts"))

from fetch_context import company_anchors, list_companies, months_for_anchors, months_from  # noqa: E402
from services import evidence_service as ev  # noqa: E402
from services.evidence_sources import SOURCE_EQS, SOURCE_GNEWS  # noqa: E402

DEFAULT_FROM_MONTH = "2019-01"
MARKER_YEAR_FROM = 2019           # Ausgangspunkt für D4: Unternehmen mit Markierungen ab diesem Jahr
SECONDS_PER_FETCH = 2.0           # gemessen im Vorabruf vom 2026-10-08: 297 Abrufe in 586 s
_LEGAL_RE = re.compile(r"\b(SE|AG|GmbH|KGaA|Deutschland)\b|&\s*Co\.", re.IGNORECASE)


# ── D1: Suchbegriffe ─────────────────────────────────────────────────────────

def name_tokens(search_term: str, name: str) -> List[str]:
    """Wortteile, die einen Titel als Nennung des Unternehmens zählen lassen: die Glieder
    des Suchbegriffs (``OR``-Alternativen ohne Anführungszeichen) und der Name ohne
    Rechtsform; klein geschrieben, ohne Doppelte."""
    tokens: List[str] = []
    for part in re.split(r"\s+OR\s+", search_term or ""):
        part = part.strip().strip('"').strip()
        if part:
            tokens.append(part.casefold())
    core = " ".join(_LEGAL_RE.sub(" ", name or "").split()).casefold()
    if core:
        tokens.append(core)
    return list(dict.fromkeys(tokens))


def mention_share(titles: Iterable[str], tokens: List[str]) -> Optional[float]:
    """Anteil der Titel, die eines der Wortteile enthalten (None ohne Titel)."""
    titles = list(titles)
    if not titles:
        return None
    hits = sum(1 for t in titles if any(tok in (t or "").casefold() for tok in tokens))
    return round(hits / len(titles), 4)


def stored_months(company_id: int, source: str, store_dir=None) -> Dict[str, Dict[str, Any]]:
    """Gespeicherte Monate einer Quelle: ``{monat: {"n": Anzahl, "titles": [...], "issuers": [...]}}``
    (Titel nur zum Zählen, sie verlassen diese Funktion nicht als Ausgabe)."""
    base = ev.record_path(company_id, source, "2000-01", store_dir).parent
    out: Dict[str, Dict[str, Any]] = {}
    if not base.exists():
        return out
    for path in sorted(base.glob("*.json")):
        record = ev.load_record(company_id, source, path.stem, store_dir)
        if record is None:
            continue
        items = record.get("items") or []
        out[path.stem] = {"n": len(items), "titles": [i.get("title") or "" for i in items],
                          "issuers": [i.get("issuer") for i in items if i.get("issuer")]}
    return out


def search_term_row(info: Dict[str, Any], months: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    counts = [m["n"] for m in months.values()]
    titles = [t for m in months.values() for t in m["titles"]]
    tokens = name_tokens(info["search_term"], info["name"])
    return {
        "company_id": info["company_id"], "company": info["name"], "search_term": info["search_term"],
        "exclude": list(info.get("exclude") or []), "term_confirmed": bool(info.get("term_confirmed")),
        "months": len(months), "items": len(titles),
        "items_per_month_mean": round(statistics.mean(counts), 1) if counts else None,
        "items_per_month_median": float(statistics.median(counts)) if counts else None,
        "months_without_items": sum(1 for c in counts if c == 0),
        "tokens": tokens, "mention_share": mention_share(titles, tokens),
    }


# ── D2: EQS ──────────────────────────────────────────────────────────────────

def eqs_row(info: Dict[str, Any], meta: Dict[str, Any], months: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    issuers: Dict[str, int] = {}
    for m in months.values():
        for issuer in m["issuers"]:
            issuers[issuer] = issuers.get(issuer, 0) + 1
    eqs = meta.get("eqs") or {}
    return {
        "company_id": info["company_id"], "company": info["name"], "uuid": info.get("eqs_uuid"),
        "eqs_name": info.get("eqs_name"), "isin": eqs.get("isin"), "confirmed": bool(eqs.get("confirmed")),
        "note": eqs.get("note"), "months": len(months), "items": sum(m["n"] for m in months.values()),
        "issuers_in_store": dict(sorted(issuers.items(), key=lambda kv: -kv[1])),
    }


# ── D4: Vorabruf ─────────────────────────────────────────────────────────────

def prefetch_plan(company: Dict[str, Any], anchors: Dict[str, Any], sources: List[str], from_month: str,
                  now: datetime, stored: Dict[str, Set[str]], window_before: int, window_after: int) -> Dict[str, Any]:
    """Fehlende Monate je Quelle für (a) alle Monate ab ``from_month`` und (b) die
    Vergleichsfenster der Markierungen; Abrufe und geschätzte Dauer."""
    plan = months_for_anchors(anchors, window_before, window_after)
    all_months = set(months_from(from_month, anchors.get("series_to"), window_after, now))
    marker_windows = [ev.window_for_anomaly(a, window_before, window_after) for a in anchors["anomalies"]]
    marker_windows += [ev.window_for_outlier(o["date"], window_before, window_after) for o in anchors["outliers"]]
    comparison_months: Set[str] = set()
    n_comparison = 0
    for w in marker_windows:
        for c in ev.comparison_windows(w, marker_windows, anchors.get("series_from"), anchors.get("series_to")):
            n_comparison += 1
            comparison_months.update(ev.window_months(c))
    out: Dict[str, Any] = {
        "company_id": company["id"], "company": company["name"], "series_from": anchors.get("series_from"),
        "series_to": anchors.get("series_to"), "n_markers": len(marker_windows),
        "markers_from_year": sum(1 for w in marker_windows if int(w["anchor_from"][:4]) >= MARKER_YEAR_FROM),
        "marker_months": len(plan["months"]), "n_comparison_windows": n_comparison,
        "comparison_months": len(comparison_months), "all_months": len(all_months), "sources": {},
    }
    for source in sources:
        have = stored.get(source, set())
        out["sources"][source] = {
            "stored": len(have),
            "missing_comparison": len(comparison_months - have),
            "missing_all": len(all_months - have),
            "missing_all_from": min(all_months - have) if all_months - have else None,
        }
    out["fetches_comparison"] = sum(s["missing_comparison"] for s in out["sources"].values())
    out["fetches_all"] = sum(s["missing_all"] for s in out["sources"].values())
    return out


def estimate_minutes(fetches: int, seconds_per_fetch: float = SECONDS_PER_FETCH) -> float:
    return round(fetches * seconds_per_fetch / 60, 1)


# ── Lauf ─────────────────────────────────────────────────────────────────────

def collect(from_month: str = DEFAULT_FROM_MONTH, window_before: int = ev.DEFAULT_WINDOW_BEFORE,
            window_after: int = ev.DEFAULT_WINDOW_AFTER, companies: Optional[List[Dict[str, Any]]] = None,
            now: Optional[datetime] = None, store_dir=None) -> Dict[str, Any]:
    from services.context_service import load_metadata  # lazy: Tests ohne DB

    now = now or datetime.now(timezone.utc)
    metadata = load_metadata()
    d1: List[Dict[str, Any]] = []
    d2: List[Dict[str, Any]] = []
    d4: List[Dict[str, Any]] = []
    for company in companies if companies is not None else list_companies():
        anchors = company_anchors(company["id"])
        if not anchors["eligible"]:
            continue
        info = ev.company_context_info(company["id"], metadata)
        if info is None:
            continue
        has_markers = bool(anchors["anomalies"] or anchors["outliers"])
        sources = ev.available_sources(info)
        months_by_source = {s: stored_months(company["id"], s, store_dir) for s in sources}
        if has_markers:
            d1.append(search_term_row(info, months_by_source[SOURCE_GNEWS]))
        if SOURCE_EQS in sources:
            d2.append(eqs_row(info, metadata.get(company["id"]) or {}, months_by_source[SOURCE_EQS]))
        if has_markers:
            d4.append(prefetch_plan(company, anchors, sources, from_month, now,
                                    {s: set(m.keys()) for s, m in months_by_source.items()}, window_before, window_after))
    events = ev.load_global_events(confirmed_only=False)
    d3 = [{**e, "months": ev.event_months(e)} for e in events]
    proposed = [p for p in d4 if p["markers_from_year"] > 0]
    return {
        "generated_at": now.isoformat(timespec="seconds"), "from_month": from_month,
        "window_before": window_before, "window_after": window_after,
        "d1_search_terms": d1, "d2_eqs": d2, "d3_global_events": d3,
        "d4_prefetch": {
            "companies": d4,
            "proposed_company_ids": [p["company_id"] for p in proposed],
            "fetches_comparison_all": sum(p["fetches_comparison"] for p in d4),
            "minutes_comparison_all": estimate_minutes(sum(p["fetches_comparison"] for p in d4)),
            "fetches_all_proposed": sum(p["fetches_all"] for p in proposed),
            "minutes_all_proposed": estimate_minutes(sum(p["fetches_all"] for p in proposed)),
            "seconds_per_fetch": SECONDS_PER_FETCH,
        },
    }


def _pct(value: Optional[float]) -> str:
    return "–" if value is None else f"{100 * value:.0f} %"


def markdown(summary: Dict[str, Any]) -> str:
    lines = ["### D1 Suchbegriffe", "",
             "| Unternehmen | Suchbegriff | Ausschluss | bestätigt | Monate im Speicher | Meldungen | je Monat Ø (Median) | Monate ohne Meldung | Titel mit Unternehmensnennung |",
             "|---|---|---|---|---|---|---|---|---|"]
    for r in summary["d1_search_terms"]:
        med = r["items_per_month_median"]
        lines.append(f"| {r['company']} | `{r['search_term']}` | {', '.join(r['exclude']) or '–'} | {'ja' if r['term_confirmed'] else 'nein'} | "
                     f"{r['months']} | {r['items']} | {r['items_per_month_mean'] if r['items_per_month_mean'] is not None else '–'} "
                     f"({med:.0f}) | {r['months_without_items']} | {_pct(r['mention_share'])} |" if med is not None else
                     f"| {r['company']} | `{r['search_term']}` | {', '.join(r['exclude']) or '–'} | {'ja' if r['term_confirmed'] else 'nein'} | 0 | 0 | – | 0 | – |")
    lines += ["", "### D2 EQS-Zuordnungen", "",
              "| Unternehmen | companyUUID | Emittent laut Metadatei | ISIN | bestätigt | Monate | Mitteilungen | Emittent in den Mitteilungen |",
              "|---|---|---|---|---|---|---|---|"]
    for r in summary["d2_eqs"]:
        issuers = ", ".join(f"{k} ({v})" for k, v in r["issuers_in_store"].items()) or "–"
        lines.append(f"| {r['company']} | `{r['uuid']}` | {r['eqs_name']} | {r['isin'] or '–'} | {'ja' if r['confirmed'] else 'nein'} | "
                     f"{r['months']} | {r['items']} | {issuers} |")
    lines += ["", "### D3 Allgemeine Ereignisse (Dauer höchstens 6 Monate)", "",
              "| Kennung | Zeitraum | Monate | Titel | Adresse | bestätigt |", "|---|---|---|---|---|---|"]
    for e in summary["d3_global_events"]:
        lines.append(f"| {e['id']} | {e['date_from']} – {e['date_to']} | {e['months']} | {e['title']} | {e['url']} | {'ja' if e['confirmed'] else 'nein'} |")
    d4 = summary["d4_prefetch"]
    lines += ["", f"### D4 Vorabruf (alle Monate ab {summary['from_month']})", "",
              "| Unternehmen | Reihe | Markierungen (ab 2019) | Vergleichsfenster | fehlende Monate Vergleich (gnews / eqs) | "
              f"Monate ab {summary['from_month']} | fehlend (gnews / eqs) | Abrufe | Dauer ≈ | Vorschlag |",
              "|---|---|---|---|---|---|---|---|---|---|"]

    def src_cell(p: Dict[str, Any], key: str) -> str:
        return " / ".join(str(p["sources"][s][key]) if s in p["sources"] else "–" for s in (SOURCE_GNEWS, SOURCE_EQS))

    for p in d4["companies"]:
        proposed = p["company_id"] in d4["proposed_company_ids"]
        lines.append(f"| {p['company']} | {p['series_from']} – {p['series_to']} | {p['n_markers']} ({p['markers_from_year']}) | "
                     f"{p['n_comparison_windows']} | {src_cell(p, 'missing_comparison')} | {p['all_months']} | {src_cell(p, 'missing_all')} | "
                     f"{p['fetches_all']} | {estimate_minutes(p['fetches_all'])} min | {'ja' if proposed else 'nein'} |")
    lines.append(f"| **Summe** | | | | {d4['fetches_comparison_all']} Abrufe, ≈ {d4['minutes_comparison_all']} min | | | "
                 f"{d4['fetches_all_proposed']} (Vorschlag) | ≈ {d4['minutes_all_proposed']} min | |")
    lines.append("")
    lines.append(f"Dauer geschätzt mit {d4['seconds_per_fetch']} s je Abruf (Mindestabstand je Quelle; die Quellen laufen im Skript "
                 "nacheinander). Die Monate der Vergleichsfenster sind in den Monaten ab dem Startmonat enthalten, soweit sie "
                 "danach liegen.")
    return "\n".join(lines)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--from-month", default=DEFAULT_FROM_MONTH, metavar="YYYY-MM")
    parser.add_argument("--window-before", type=int, default=ev.DEFAULT_WINDOW_BEFORE)
    parser.add_argument("--window-after", type=int, default=ev.DEFAULT_WINDOW_AFTER)
    parser.add_argument("--json", dest="json_out", help="Zusammenfassung als JSON-Datei (ohne Titel)")
    args = parser.parse_args(argv)
    if not ev.is_period(args.from_month):
        parser.error(f"--from-month muss das Format YYYY-MM haben, nicht {args.from_month!r}")
    summary = collect(args.from_month, args.window_before, args.window_after)
    print(markdown(summary))
    if args.json_out:
        os.makedirs(os.path.dirname(os.path.abspath(args.json_out)), exist_ok=True)
        with open(args.json_out, "w", encoding="utf-8") as fh:
            json.dump(summary, fh, ensure_ascii=False, indent=2)
            fh.write("\n")
        print(f"\nZusammenfassung gespeichert: {args.json_out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
