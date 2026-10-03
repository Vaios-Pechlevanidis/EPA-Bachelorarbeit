"""
Datenbasis-Report (Prüfpunkt 4 des Fundament-Checks, Inkrement 0).

Zweck
-----
Ermittelt für jedes Nicht-Demo-Unternehmen und beide Quellen ("employee",
"candidates") die zeitliche Dichte der Kununu-Bewertungen in der gehosteten
Supabase-Datenbank und schreibt das Ergebnis

- maschinenlesbar nach ``backend/data/data_density.json`` (Grundlage für
  ``validate_annotations.py``) und
- als deutsche Dokumentation nach ``docs/datenbasis.md``.

Kennzahlen je Unternehmen und Quelle
------------------------------------
- rows                      Zeilen insgesamt (inkl. Zeilen ohne Datum)
- rows_without_datum        Zeilen mit ``datum IS NULL``
- first_month / last_month  Kalendermonat (YYYY-MM) der ältesten / jüngsten
                            datierten Bewertung
- months_spanned            Kalendermonate von first_month bis last_month,
                            beide inklusive (Lücken zählen mit)
- reviews_per_month_min     Minimum der Bewertungen je Kalendermonat im Zeitraum
- reviews_per_month_median  Median der Bewertungen je Kalendermonat im Zeitraum
                            (Monate ohne Bewertung gehen mit 0 ein)
- months_eq0 / months_lt5 / months_ge5
                            Kalendermonate im Zeitraum mit 0, weniger als 5
                            bzw. mindestens 5 Bewertungen
- non_null_share            Anteil nicht-leerer Werte je Sternekategorie
                            (durchschnittsbewertung + Themen-Spalten der
                            Quelle); Nenner = rows

Das Skript ist strikt lesend gegenüber der Datenbank (nur SELECT). Es
schreibt ausschließlich die beiden Ausgabedateien.

Verwendung
----------
    cd backend
    uv run python scripts/report_data_density.py
    uv run python scripts/report_data_density.py --json data/x.json --md ../docs/y.md
"""

from __future__ import annotations

import argparse
import json
import os
import re
import statistics
import sys
import unicodedata
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND_DIR)

from database.supabase_client import get_supabase_client  # noqa: E402
from services.topic_average_rating_service import (  # noqa: E402
    CANDIDATES_TOPIC_COLUMNS,
    EMPLOYEE_TOPIC_COLUMNS,
    _fetch_all_rows,
)

SOURCES: Tuple[str, str] = ("employee", "candidates")
TOPIC_COLUMNS_BY_SOURCE: Dict[str, Dict[str, str]] = {
    "employee": EMPLOYEE_TOPIC_COLUMNS,
    "candidates": CANDIDATES_TOPIC_COLUMNS,
}

# Schwellen, auf die sich die Dokumentation bezieht
MIN_REVIEWS_PER_MONTH = 5
MIN_MONTHS_WITH_ENOUGH_REVIEWS = 12

DEFAULT_JSON = os.path.join(BACKEND_DIR, "data", "data_density.json")
DEFAULT_MD = os.path.join(os.path.dirname(BACKEND_DIR), "docs", "datenbasis.md")

_DEMO_RE = re.compile(r"^demo\s*\d+$")


# ── Namens-Helfer ────────────────────────────────────────────────────────────

def clean_company_name(raw: str) -> str:
    """Bereinigt Whitespace-Defekte der DB-Namen (strip, Mehrfach-Leerzeichen,
    Zeilenumbrüche), behält aber Gross-/Kleinschreibung bei."""
    return " ".join(str(raw).split())


def normalize_company_name(raw: str) -> str:
    """Schlüssel für den Namensvergleich: bereinigt + casefold."""
    return clean_company_name(raw).casefold()


def is_demo_company(raw: str) -> bool:
    """Demo 1/2/3 sind synthetisch und werden aus jeder Analyse ausgeschlossen."""
    return _DEMO_RE.match(normalize_company_name(raw)) is not None


def slugify(name: str) -> str:
    """ASCII-Slug für Dateinamen (Umlaute transliteriert, Rest -> '_')."""
    s = clean_company_name(name).casefold()
    for src, dst in (("ä", "ae"), ("ö", "oe"), ("ü", "ue"), ("ß", "ss")):
        s = s.replace(src, dst)
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")
    s = re.sub(r"[^a-z0-9]+", "_", s).strip("_")
    return s or "unbenannt"


# ── Monats-Helfer ────────────────────────────────────────────────────────────

def month_key(datum_raw: Any) -> Optional[str]:
    """YYYY-MM aus einem ISO-Datum/Zeitstempel; None, wenn nicht parsebar."""
    if not datum_raw:
        return None
    try:
        dt = datetime.fromisoformat(str(datum_raw).replace("Z", "+00:00"))
    except ValueError:
        return None
    return f"{dt.year:04d}-{dt.month:02d}"


def month_range(first: str, last: str) -> List[str]:
    """Alle Kalendermonate von first bis last (beide inklusive)."""
    y, m = (int(x) for x in first.split("-"))
    ly, lm = (int(x) for x in last.split("-"))
    out: List[str] = []
    while (y, m) <= (ly, lm):
        out.append(f"{y:04d}-{m:02d}")
        m += 1
        if m == 13:
            y, m = y + 1, 1
    return out


# ── Datenzugriff (nur lesend) ────────────────────────────────────────────────

def fetch_companies(supabase) -> List[Dict[str, Any]]:
    res = supabase.table("companies").select("id,name").order("id").execute()
    return list(res.data or [])


def fetch_rows(supabase, source: str, company_id: int) -> List[Dict[str, Any]]:
    cols = ["id", "datum", "durchschnittsbewertung"] + list(TOPIC_COLUMNS_BY_SOURCE[source].values())
    q = (
        supabase.table(source)
        .select(",".join(cols))
        .eq("company_id", company_id)
        .order("id")  # stabile Reihenfolge für die range()-Paginierung
    )
    return _fetch_all_rows(q, page_size=1000)


def fetch_count(supabase, source: str, company_id: int) -> Optional[int]:
    res = supabase.table(source).select("id", count="exact").eq("company_id", company_id).limit(1).execute()
    return res.count


# ── Kennzahlen ───────────────────────────────────────────────────────────────

def compute_density(rows: List[Dict[str, Any]], source: str) -> Dict[str, Any]:
    """Berechnet alle Dichte-Kennzahlen für die Zeilen einer Quelle/eines Unternehmens."""
    n_rows = len(rows)
    months: List[str] = []
    rows_without_datum = 0
    for r in rows:
        mk = month_key(r.get("datum"))
        if mk is None:
            rows_without_datum += 1
        else:
            months.append(mk)

    star_cols: Dict[str, str] = {"durchschnittsbewertung": "durchschnittsbewertung"}
    star_cols.update(TOPIC_COLUMNS_BY_SOURCE[source])
    non_null_share: Dict[str, Optional[float]] = {}
    for key, col in star_cols.items():
        if n_rows == 0:
            non_null_share[key] = None
        else:
            non_null = sum(1 for r in rows if r.get(col) is not None)
            non_null_share[key] = round(non_null / n_rows, 4)

    result: Dict[str, Any] = {
        "rows": n_rows,
        "rows_without_datum": rows_without_datum,
        "first_month": None,
        "last_month": None,
        "months_spanned": 0,
        "reviews_per_month_min": None,
        "reviews_per_month_median": None,
        "months_eq0": 0,
        "months_lt5": 0,
        "months_ge5": 0,
        "non_null_share": non_null_share,
    }
    if not months:
        return result

    first, last = min(months), max(months)
    calendar = month_range(first, last)
    per_month = {m: 0 for m in calendar}
    for mk in months:
        per_month[mk] += 1
    counts = [per_month[m] for m in calendar]

    result.update(
        {
            "first_month": first,
            "last_month": last,
            "months_spanned": len(calendar),
            "reviews_per_month_min": min(counts),
            "reviews_per_month_median": float(statistics.median(counts)),
            "months_eq0": sum(1 for c in counts if c == 0),
            "months_lt5": sum(1 for c in counts if c < MIN_REVIEWS_PER_MONTH),
            "months_ge5": sum(1 for c in counts if c >= MIN_REVIEWS_PER_MONTH),
        }
    )
    return result


def build_report(supabase, verbose: bool = True) -> Dict[str, Any]:
    companies = fetch_companies(supabase)
    included: List[Dict[str, Any]] = []
    excluded: List[Dict[str, Any]] = []
    warnings: List[str] = []

    for c in companies:
        raw_name = c["name"]
        entry = {"id": int(c["id"]), "name": clean_company_name(raw_name), "name_raw": raw_name}
        if is_demo_company(raw_name):
            excluded.append(entry)
            continue
        entry["name_normalized"] = normalize_company_name(raw_name)
        entry["slug"] = slugify(raw_name)
        entry["sources"] = {}
        for source in SOURCES:
            rows = fetch_rows(supabase, source, entry["id"])
            expected = fetch_count(supabase, source, entry["id"])
            if expected is not None and expected != len(rows):
                warnings.append(
                    f"{entry['name']}/{source}: count={expected}, aber {len(rows)} Zeilen geladen "
                    "(Paginierung prüfen)"
                )
            entry["sources"][source] = compute_density(rows, source)
            if verbose:
                d = entry["sources"][source]
                print(
                    f"  {entry['id']:>3} {entry['name']:<38} {source:<10} rows={d['rows']:>5} "
                    f"ohneDatum={d['rows_without_datum']:>2} {d['first_month'] or '----'}..{d['last_month'] or '----'} "
                    f"Monate={d['months_spanned']:>3} min={d['reviews_per_month_min']} "
                    f"median={d['reviews_per_month_median']} =0:{d['months_eq0']:>3} <5:{d['months_lt5']:>3} >=5:{d['months_ge5']:>3}"
                )
        included.append(entry)

    return {
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "thresholds": {
            "min_reviews_per_month": MIN_REVIEWS_PER_MONTH,
            "min_months_with_enough_reviews": MIN_MONTHS_WITH_ENOUGH_REVIEWS,
        },
        "method": {
            "months_spanned": "Kalendermonate zwischen erster und letzter datierter Bewertung, beide inklusive; Monate ohne Bewertung zählen mit.",
            "reviews_per_month": "Anzahl datierter Bewertungen je Kalendermonat im Zeitraum; Minimum und Median werden über alle Kalendermonate (inkl. 0-Monate) gebildet.",
            "months_lt5": "Kalendermonate im Zeitraum mit weniger als min_reviews_per_month Bewertungen (0-Monate eingeschlossen).",
            "non_null_share": "Anteil der Zeilen mit nicht-leerem Wert je Sternekategorie; Nenner = rows (alle Zeilen, auch ohne Datum).",
            "company_matching": "Unternehmen werden über den bereinigten Namen (strip, Whitespace-Kollaps, casefold) oder die id identifiziert; Demo 1/2/3 sind ausgeschlossen.",
        },
        "dimensions": {
            "employee": ["durchschnittsbewertung"] + list(EMPLOYEE_TOPIC_COLUMNS.keys()),
            "candidates": ["durchschnittsbewertung"] + list(CANDIDATES_TOPIC_COLUMNS.keys()),
        },
        "companies": included,
        "excluded_companies": excluded,
        "warnings": warnings,
    }


# ── Markdown ─────────────────────────────────────────────────────────────────

def _de_num(x: Optional[float], digits: int = 1) -> str:
    if x is None:
        return "–"
    if float(x).is_integer() and digits == 0:
        return str(int(x))
    return f"{x:.{digits}f}".replace(".", ",")


def _de_pct(x: Optional[float]) -> str:
    return "–" if x is None else f"{x * 100:.1f} %".replace(".", ",")


def _md_table(header: List[str], rows: List[List[str]]) -> str:
    lines = ["| " + " | ".join(header) + " |", "|" + "|".join("---" for _ in header) + "|"]
    for r in rows:
        lines.append("| " + " | ".join(r) + " |")
    return "\n".join(lines)


def _source_table(report: Dict[str, Any], source: str) -> str:
    header = [
        "ID", "Unternehmen", "Zeilen", "ohne Datum", "Zeitraum", "Kal.-Monate",
        "Min/Monat", "Median/Monat", "Monate = 0", "Monate < 5", "Monate ≥ 5",
        "Ø-Bew. nicht-null", "Themen nicht-null (min – max)",
    ]
    rows: List[List[str]] = []
    for c in report["companies"]:
        d = c["sources"][source]
        shares = d["non_null_share"]
        topic_shares = [v for k, v in shares.items() if k != "durchschnittsbewertung" and v is not None]
        if d["rows"] == 0 or d["first_month"] is None:  # keine (datierten) Bewertungen
            span = "–"
        else:
            span = f"{d['first_month']} – {d['last_month']}"
        rows.append([
            str(c["id"]), c["name"], str(d["rows"]), str(d["rows_without_datum"]), span,
            str(d["months_spanned"]), _de_num(d["reviews_per_month_min"], 0),
            _de_num(d["reviews_per_month_median"], 1), str(d["months_eq0"]), str(d["months_lt5"]),
            str(d["months_ge5"]), _de_pct(shares.get("durchschnittsbewertung")),
            (f"{_de_pct(min(topic_shares))} – {_de_pct(max(topic_shares))}" if topic_shares else "–"),
        ])
    return _md_table(header, rows)


def _share_detail_table(report: Dict[str, Any], source: str) -> str:
    dims = report["dimensions"][source]
    header = ["ID", "Unternehmen"] + dims
    rows: List[List[str]] = []
    for c in report["companies"]:
        shares = c["sources"][source]["non_null_share"]
        rows.append([str(c["id"]), c["name"]] + [_de_pct(shares.get(dim)) for dim in dims])
    return _md_table(header, rows)


def render_markdown(report: Dict[str, Any]) -> str:
    thr = report["thresholds"]
    k = thr["min_reviews_per_month"]
    n_min = thr["min_months_with_enough_reviews"]
    companies = report["companies"]

    def too_sparse(source: str) -> List[Dict[str, Any]]:
        return [c for c in companies if c["sources"][source]["months_ge5"] < n_min]

    def dense_enough(source: str) -> List[Dict[str, Any]]:
        return [c for c in companies if c["sources"][source]["months_ge5"] >= n_min]

    out: List[str] = []
    out.append("# Datenbasis: Dichte der Kununu-Bewertungen je Unternehmen\n")
    out.append(
        f"Stand: {report['generated_at']} (automatisch erzeugt durch "
        "`backend/scripts/report_data_density.py`, Quelle: gehostete Supabase-Datenbank, "
        "Tabellen `employee` und `candidates`). Diese Datei nicht von Hand bearbeiten; "
        "die Rohwerte liegen in `backend/data/data_density.json`.\n"
    )
    out.append("## Methode\n")
    out.append(
        "- **Unternehmen:** Alle Einträge der Tabelle `companies` außer den synthetischen "
        "Demo-Unternehmen (Demo 1/2/3), die aus jeder Analyse ausgeschlossen sind. "
        "Die Rohnamen enthalten Whitespace-Defekte (z. B. `'E.ON\\n'`, doppelte Leerzeichen); "
        "Unternehmen werden deshalb über den bereinigten Namen (strip, Whitespace-Kollaps, casefold) "
        "oder die `id` identifiziert. Die Tabellen zeigen den bereinigten Namen.\n"
        f"- **Ausgeschlossen:** {', '.join(f'{e['name']} (id {e['id']})' for e in report['excluded_companies']) or '–'}.\n"
        "- **Zeilen:** Anzahl aller Bewertungen des Unternehmens in der jeweiligen Quelle, "
        "einschließlich Zeilen ohne Datum. **Ohne Datum:** Zeilen mit `datum IS NULL`; sie fließen "
        "nicht in die Monatsstatistik ein.\n"
        "- **Zeitraum:** Kalendermonat (`YYYY-MM`) der ältesten und der jüngsten datierten Bewertung.\n"
        "- **Kalendermonate:** Anzahl der Kalendermonate zwischen erster und letzter Bewertung, "
        "beide inklusive. Monate ohne Bewertung werden mitgezählt (Lücken verkürzen den Zeitraum nicht).\n"
        "- **Bewertungen je Monat:** Anzahl datierter Bewertungen je Kalendermonat im Zeitraum; "
        "Minimum und Median werden über alle Kalendermonate gebildet, Monate ohne Bewertung gehen mit 0 ein.\n"
        f"- **Monate = 0 / < {k} / ≥ {k}:** Anzahl Kalendermonate im Zeitraum mit genau 0, weniger als {k} "
        f"bzw. mindestens {k} Bewertungen (die 0-Monate sind in „< {k}“ enthalten).\n"
        "- **Nicht-null-Anteil:** Anteil der Zeilen mit nicht-leerem Wert je Sternekategorie "
        "(`durchschnittsbewertung` sowie alle `sternebewertung_*`-Spalten der Quelle); Nenner sind alle Zeilen "
        "der Quelle. Die Haupttabellen zeigen den Anteil für die Durchschnittsbewertung und die Spannweite "
        "über die Themen; die Aufschlüsselung je Thema steht im Anhang.\n"
        f"- **Schwelle:** Ein Monat gilt als ausreichend belegt, wenn er mindestens {k} Bewertungen enthält. "
        f"Ein Unternehmen gilt für die Monatsanalyse als ausreichend dicht, wenn mindestens {n_min} solcher "
        "Monate vorliegen (siehe Konsequenzen).\n"
    )

    out.append(f"## Mitarbeitende (`employee`), {len(companies)} Unternehmen\n")
    out.append(_source_table(report, "employee") + "\n")
    out.append(f"## Bewerbende (`candidates`), {len(companies)} Unternehmen\n")
    out.append(_source_table(report, "candidates") + "\n")

    out.append("## Konsequenzen\n")
    for source, label in (("employee", "Mitarbeitende"), ("candidates", "Bewerbende")):
        sparse = too_sparse(source)
        dense = dense_enough(source)
        out.append(
            f"**{label} (`{source}`):** {len(dense)} von {len(companies)} Unternehmen haben mindestens "
            f"{n_min} Monate mit ≥ {k} Bewertungen"
            + (": " + ", ".join(f"{c['name']} ({c['sources'][source]['months_ge5']})" for c in dense) if dense else "")
            + ".\n"
        )
        if sparse:
            out.append(
                f"Weniger als {n_min} Monate mit ≥ {k} Bewertungen ({len(sparse)} Unternehmen):\n"
            )
            for c in sparse:
                d = c["sources"][source]
                if d["rows"] == 0:
                    out.append(f"- {c['name']} (id {c['id']}): keine Bewertungen in dieser Quelle")
                else:
                    out.append(
                        f"- {c['name']} (id {c['id']}): Monate ≥ {k}: {d['months_ge5']}; {d['rows']} Zeilen "
                        f"über {d['months_spanned']} Kalendermonate; Median {_de_num(d['reviews_per_month_median'], 1)} Bewertungen/Monat"
                    )
            out.append("")
    nodate = [
        (c, s, c["sources"][s]["rows_without_datum"])
        for c in companies for s in SOURCES if c["sources"][s]["rows_without_datum"] > 0
    ]
    if nodate:
        out.append(
            "**Zeilen ohne Datum** (nicht zeitlich zuordenbar, in Monatsstatistiken ignoriert): "
            + ", ".join(f"{c['name']}/{s}: {n}" for c, s, n in nodate) + ".\n"
        )
    out.append(
        "Für sehr dünn belegte Unternehmen ist eine Monatsauflösung nicht tragfähig; dort kommen nur "
        "gröbere Zeitfenster (Quartal/Jahr) oder ein Ausschluss aus der quantitativen Evaluation in Frage. "
        "Diese Entscheidung wird im Design der Erkennung (nachfolgende Inkremente) getroffen und hier nur "
        "vorbereitet.\n"
    )
    if report["warnings"]:
        out.append("## Warnungen\n")
        out.extend(f"- {w}" for w in report["warnings"])
        out.append("")

    out.append("## Anhang: Nicht-null-Anteil je Sternekategorie\n")
    for source, label in (("employee", "Mitarbeitende"), ("candidates", "Bewerbende")):
        out.append(f"<details>\n<summary>{label} (`{source}`)</summary>\n")
        out.append(_share_detail_table(report, source) + "\n")
        out.append("</details>\n")
    return "\n".join(out)


# ── CLI ──────────────────────────────────────────────────────────────────────

def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--json", default=DEFAULT_JSON, help=f"Zielpfad der JSON-Ausgabe (Default: {DEFAULT_JSON})")
    parser.add_argument("--md", default=DEFAULT_MD, help=f"Zielpfad der Markdown-Dokumentation (Default: {DEFAULT_MD})")
    parser.add_argument("--quiet", action="store_true", help="Keine Zeile je Unternehmen/Quelle auf stdout")
    args = parser.parse_args(argv)

    supabase = get_supabase_client()
    print("Lese Unternehmen und Bewertungen (nur SELECT) ...")
    report = build_report(supabase, verbose=not args.quiet)

    os.makedirs(os.path.dirname(os.path.abspath(args.json)), exist_ok=True)
    with open(args.json, "w", encoding="utf-8") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=2)
    os.makedirs(os.path.dirname(os.path.abspath(args.md)), exist_ok=True)
    with open(args.md, "w", encoding="utf-8") as fh:
        fh.write(render_markdown(report))

    n = len(report["companies"])
    thr = report["thresholds"]
    print(f"\n{n} Unternehmen ausgewertet, {len(report['excluded_companies'])} Demo-Unternehmen ausgeschlossen.")
    for source in SOURCES:
        dense = [c["name"] for c in report["companies"]
                 if c["sources"][source]["months_ge5"] >= thr["min_months_with_enough_reviews"]]
        print(
            f"  {source:<10}: {len(dense)} Unternehmen mit >= {thr['min_months_with_enough_reviews']} Monaten "
            f">= {thr['min_reviews_per_month']} Bewertungen: {', '.join(dense) or '–'}"
        )
    for w in report["warnings"]:
        print(f"  WARNUNG: {w}")
    print(f"JSON: {args.json}\nMarkdown: {args.md}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
