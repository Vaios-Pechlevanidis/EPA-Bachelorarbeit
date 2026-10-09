"""
Validator für die manuellen Referenzannotationen in ``backend/data/annotations.json``
(Prüfpunkt 5 des Fundaments, Protokoll in ``docs/referenzzeitraeume-literatur.md``,
Abschnitt 3). Die Referenzzeiträume dienen der Evaluation der Anomalieerkennung
(DZ1) und sind nicht Teil des Dashboards.

Geprüft werden

- gültige Grundstruktur {"version": n, "hinweise": {...}, "annotations": [...]}
  mit ganzzahliger version >= 1 (Regel 8: spätere Änderungen erhöhen version)
- Pflichtfelder je Eintrag: company, source, dimension, period_from, period_to, direction, note
- company: auflösbar über den bereinigten Namen (strip, Whitespace-Kollaps,
  casefold) gegen die Unternehmen der Datenbank bzw. gegen die Unternehmensliste
  in ``data_density.json``; Demo-Unternehmen sind nicht zulässig
- source in {employee, candidates}; dimension = "durchschnittsbewertung" oder
  ein Themen-Schlüssel der jeweiligen Quelle
- period_from / period_to im Format YYYY-MM, period_from <= period_to, beide
  innerhalb des Datenzeitraums des Unternehmens für diese Quelle
- direction in {rise, fall}; note nicht leer
- keine Duplikate (gleiche company/source/dimension/period_from/period_to);
  Überschneidungen derselben Dimension werden als Warnung gemeldet
- Protokollregeln 2 (Länge, Warnung), 3 (Mindestfallzahl an den Rändern:
  Fehler; dünne Monate innerhalb: Warnung) und 5 (Mindestabstand: Warnung),
  sofern Monatszählungen aus ``data/series/`` vorliegen

Mit ``--require-all-companies`` gilt zusätzlich als Fehler, wenn ein
Nicht-Demo-Unternehmen keinen Eintrag hat. ``validate()`` ist eine reine
Funktion ohne Datei-, DB- oder Netzwerkzugriff; Exit-Code 1 bei Fehlern.

Verwendung
----------
    cd backend
    uv run python scripts/validate_annotations.py                      # Unternehmen aus der DB (nur SELECT)
    uv run python scripts/validate_annotations.py --offline            # Unternehmen aus data_density.json
    uv run python scripts/validate_annotations.py --require-all-companies
    uv run python scripts/validate_annotations.py --file data/annotations.json --density data/data_density.json
"""

from __future__ import annotations

import argparse
import csv
import glob
import json
import os
import re
import sys
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND_DIR)

# Quellen, Dimensionen und die Schwelle für bewertete Monate (E4) kommen aus
# demselben Dienst, der die Reihe für die Anomalieerkennung bildet.
from services.rating_series_service import (  # noqa: E402
    DIMENSIONS_BY_SOURCE,
    MIN_REVIEWS_PER_MONTH,
    VALID_SOURCES,
)

DEFAULT_FILE = os.path.join(BACKEND_DIR, "data", "annotations.json")
DEFAULT_DENSITY = os.path.join(BACKEND_DIR, "data", "data_density.json")
DEFAULT_SERIES_DIR = os.path.join(BACKEND_DIR, "data", "series")

VALID_DIRECTIONS: Tuple[str, ...] = ("rise", "fall")
REQUIRED_KEYS: Tuple[str, ...] = (
    "company", "source", "dimension", "period_from", "period_to", "direction", "note",
)
PERIOD_RE = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")
_DEMO_RE = re.compile(r"^demo\s*\d+$")

# Protokollregeln aus docs/referenzzeitraeume-literatur.md, Abschnitt 3
# (Regel 3 nutzt MIN_REVIEWS_PER_MONTH aus dem Reihendienst)
MAX_PERIOD_MONTHS = 6          # Regel 2: Obergrenze eines Referenzzeitraums in Kalendermonaten
MAX_THIN_MONTHS_INSIDE = 1     # Regel 3: höchstens ein nicht bewerteter Monat innerhalb des Zeitraums
MIN_GAP_MONTHS = 3             # Regel 5: Mindestabstand zweier Zeiträume derselben Reihe (Kalendermonate)


def _month_index(period: str) -> int:
    return int(period[:4]) * 12 + int(period[5:7]) - 1


def _month_range(p_from: str, p_to: str) -> List[str]:
    out: List[str] = []
    i = _month_index(p_from)
    while i <= _month_index(p_to):
        out.append(f"{i // 12:04d}-{i % 12 + 1:02d}")
        i += 1
    return out


# ── Datenstrukturen ──────────────────────────────────────────────────────────

@dataclass
class CompanyInfo:
    """Ein auflösbares Nicht-Demo-Unternehmen mit Datenzeitraum je Quelle.

    ranges[source] = (first_month, last_month) oder None, wenn die Quelle keine
    datierten Bewertungen enthält; fehlt der Schlüssel, ist der Zeitraum unbekannt.
    """
    id: Optional[int]
    name: str
    name_normalized: str
    ranges: Dict[str, Optional[Tuple[str, str]]] = field(default_factory=dict)
    # counts[source][period] = Anzahl Bewertungen im Monat (aus data/series/*.csv);
    # fehlt der Schlüssel, werden die Regeln 3 und 5 nicht geprüft.
    counts: Dict[str, Dict[str, int]] = field(default_factory=dict)


@dataclass
class ValidationResult:
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    n_entries: int = 0
    companies_total: int = 0
    companies_annotated: List[str] = field(default_factory=list)
    companies_missing: List[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


# ── Namens-Helfer ────────────────────────────────────────────────────────────

def clean_company_name(raw: Any) -> str:
    """Bereinigt Whitespace-Defekte (strip, Mehrfach-Leerzeichen, Zeilenumbrüche)."""
    return " ".join(str(raw).split())


def normalize_company_name(raw: Any) -> str:
    """Schlüssel für den Namensvergleich: bereinigt + casefold."""
    return clean_company_name(raw).casefold()


def is_demo_company(raw: Any) -> bool:
    return _DEMO_RE.fullmatch(normalize_company_name(raw)) is not None


# ── Unternehmenslisten ───────────────────────────────────────────────────────

def _ranges_from_density_company(c: Dict[str, Any]) -> Dict[str, Optional[Tuple[str, str]]]:
    ranges: Dict[str, Optional[Tuple[str, str]]] = {}
    for source, d in (c.get("sources") or {}).items():
        first, last = d.get("first_month"), d.get("last_month")
        ranges[source] = (first, last) if (first and last) else None
    return ranges


def companies_from_density(density: Dict[str, Any]) -> Dict[str, CompanyInfo]:
    """Unternehmensliste (ohne Demo) aus data_density.json, Schlüssel = normalisierter Name."""
    out: Dict[str, CompanyInfo] = {}
    for c in density.get("companies", []):
        raw = c.get("name_raw", c.get("name", ""))
        if is_demo_company(raw):
            continue
        norm = normalize_company_name(raw)
        out[norm] = CompanyInfo(
            id=c.get("id"),
            name=clean_company_name(raw),
            name_normalized=norm,
            ranges=_ranges_from_density_company(c),
        )
    return out


def companies_from_db(density: Dict[str, Any], warnings: Optional[List[str]] = None) -> Dict[str, CompanyInfo]:
    """Unternehmensliste (ohne Demo) aus der Tabelle companies (nur SELECT);
    die Datenzeiträume stammen weiterhin aus data_density.json."""
    from database.supabase_client import get_supabase_client  # lazy, damit Tests ohne DB laufen

    res = get_supabase_client().table("companies").select("id,name").order("id").execute()
    by_density = companies_from_density(density)
    out: Dict[str, CompanyInfo] = {}
    for c in res.data or []:
        raw = c["name"]
        if is_demo_company(raw):
            continue
        norm = normalize_company_name(raw)
        info = CompanyInfo(id=c.get("id"), name=clean_company_name(raw), name_normalized=norm)
        if norm in by_density:
            info.ranges = by_density[norm].ranges
        elif warnings is not None:
            warnings.append(
                f"Unternehmen '{info.name}' (id {info.id}) steht in der DB, aber nicht in data_density.json; "
                "report_data_density.py erneut ausführen (Zeitraumprüfung für dieses Unternehmen nicht möglich)."
            )
        out[norm] = info
    return out


def attach_series_counts(companies: Dict[str, CompanyInfo], series_dir: str,
                         warnings: Optional[List[str]] = None) -> int:
    """Liest die Monatszählungen aus data/series/<id>_<slug>_<source>.csv in CompanyInfo.counts.
    Liefert die Zahl der gelesenen Dateien; fehlende Dateien werden als Warnung gemeldet."""
    loaded = 0
    for info in companies.values():
        if info.id is None:
            continue
        for source in VALID_SOURCES:
            matches = glob.glob(os.path.join(series_dir, f"{info.id}_*_{source}.csv"))
            if not matches:
                if warnings is not None:
                    warnings.append(
                        f"Keine Serien-CSV für '{info.name}'/{source} in {series_dir}; "
                        "Protokoll-Regeln 3 und 5 werden für diese Reihe nicht geprüft "
                        "(make_annotation_basis.py ausführen)."
                    )
                continue
            counts: Dict[str, int] = {}
            with open(matches[0], "r", encoding="utf-8") as fh:
                for row in csv.DictReader(fh, delimiter=";"):
                    try:
                        counts[row["period"]] = int(row.get("count") or 0)
                    except (TypeError, ValueError):
                        continue
            info.counts[source] = counts
            loaded += 1
    return loaded


# ── Prüfung ──────────────────────────────────────────────────────────────────

def _label(i: int, entry: Any) -> str:
    if isinstance(entry, dict):
        parts = [str(entry.get(k, "?")) for k in ("company", "source", "dimension")]
        return f"Eintrag #{i} ({clean_company_name(parts[0])}/{parts[1]}/{parts[2]})"
    return f"Eintrag #{i}"


def _check_entry(
    i: int,
    entry: Any,
    companies: Dict[str, CompanyInfo],
) -> Tuple[List[str], List[str], Optional[Tuple[str, str, str, str, str]]]:
    """Prüft einen Eintrag. Liefert (Fehler, Warnungen, Duplikat-Schlüssel oder None)."""
    errors: List[str] = []
    warnings: List[str] = []
    lab = _label(i, entry)

    if not isinstance(entry, dict):
        return [f"{lab}: muss ein JSON-Objekt sein, ist {type(entry).__name__}."], warnings, None

    missing = [k for k in REQUIRED_KEYS if k not in entry]
    if missing:
        errors.append(f"{lab}: Pflichtfeld(er) fehlen: {', '.join(missing)}.")
    extra = [k for k in entry if k not in REQUIRED_KEYS]
    if extra:
        warnings.append(f"{lab}: unbekannte Felder werden ignoriert: {', '.join(extra)}.")
    for k in REQUIRED_KEYS:
        if k in entry and not isinstance(entry[k], str):
            errors.append(f"{lab}: Feld '{k}' muss eine Zeichenkette sein, ist {type(entry[k]).__name__}.")
    if errors:
        return errors, warnings, None

    # company
    company_raw = entry["company"]
    norm = normalize_company_name(company_raw)
    info: Optional[CompanyInfo] = None
    if is_demo_company(company_raw):
        errors.append(f"{lab}: Demo-Unternehmen '{clean_company_name(company_raw)}' sind nicht zulässig.")
    elif norm not in companies:
        errors.append(
            f"{lab}: Unternehmen '{company_raw}' nicht auflösbar (bereinigt: '{norm}'); "
            "gültig sind die Namen aus data_density.json."
        )
    else:
        info = companies[norm]

    # source
    source = entry["source"]
    source_ok = source in VALID_SOURCES
    if not source_ok:
        errors.append(f"{lab}: source '{source}' ungültig; erlaubt: {', '.join(VALID_SOURCES)}.")

    # dimension
    dimension = entry["dimension"]
    if source_ok and dimension not in DIMENSIONS_BY_SOURCE[source]:
        errors.append(
            f"{lab}: dimension '{dimension}' ist für source '{source}' unbekannt; "
            f"erlaubt: {', '.join(DIMENSIONS_BY_SOURCE[source])}."
        )

    # periods
    p_from, p_to = entry["period_from"], entry["period_to"]
    periods_ok = True
    for key, val in (("period_from", p_from), ("period_to", p_to)):
        if not PERIOD_RE.fullmatch(val):  # fullmatch: "$" würde "2020-03\n" akzeptieren
            errors.append(f"{lab}: {key} '{val}' hat nicht das Format YYYY-MM (Monat 01-12).")
            periods_ok = False
    if periods_ok and p_from > p_to:
        errors.append(f"{lab}: period_from '{p_from}' liegt nach period_to '{p_to}'.")
        periods_ok = False
    if periods_ok and info is not None and source_ok:
        if source not in info.ranges:
            errors.append(
                f"{lab}: Datenzeitraum für '{info.name}'/{source} unbekannt (nicht in data_density.json); "
                "report_data_density.py erneut ausführen."
            )
        elif info.ranges[source] is None:
            errors.append(f"{lab}: '{info.name}' hat in Quelle '{source}' keine datierten Bewertungen.")
        else:
            first, last = info.ranges[source]
            if p_from < first or p_to > last:
                errors.append(
                    f"{lab}: Zeitraum {p_from}..{p_to} liegt außerhalb des Datenzeitraums "
                    f"{first}..{last} von '{info.name}'/{source}."
                )
        # Regel 2: Obergrenze der Länge
        length = _month_index(p_to) - _month_index(p_from) + 1
        if length > MAX_PERIOD_MONTHS:
            warnings.append(
                f"{lab}: Zeitraum {p_from}..{p_to} umfasst {length} Kalendermonate, Protokoll-Regel 2 "
                f"erlaubt höchstens {MAX_PERIOD_MONTHS}; längere monotone Verläufe sind Trends."
            )
        # Regel 3: Randmonate bewertet, höchstens ein dünner Monat innerhalb
        counts = info.counts.get(source) if info is not None else None
        if counts is not None:
            for key, val in (("period_from", p_from), ("period_to", p_to)):
                n = counts.get(val, 0)
                if n < MIN_REVIEWS_PER_MONTH:
                    errors.append(
                        f"{lab}: {key} {val} hat nur {n} Bewertungen; Protokoll-Regel 3 verlangt "
                        f"mindestens {MIN_REVIEWS_PER_MONTH} an beiden Rändern."
                    )
            inside = _month_range(p_from, p_to)[1:-1]
            thin = [m for m in inside if counts.get(m, 0) < MIN_REVIEWS_PER_MONTH]
            if len(thin) > MAX_THIN_MONTHS_INSIDE:
                warnings.append(
                    f"{lab}: {len(thin)} Monate innerhalb des Zeitraums haben weniger als "
                    f"{MIN_REVIEWS_PER_MONTH} Bewertungen ({', '.join(thin)}); Protokoll-Regel 3 erlaubt einen."
                )

    # direction
    direction = entry["direction"]
    if direction not in VALID_DIRECTIONS:
        errors.append(f"{lab}: direction '{direction}' ungültig; erlaubt: {', '.join(VALID_DIRECTIONS)}.")

    # note
    if not entry["note"].strip():
        errors.append(f"{lab}: note ist leer; eine deutsche Begründung ist Pflicht.")

    key = (norm, source, dimension, p_from, p_to) if (info is not None and source_ok and periods_ok) else None
    return errors, warnings, key


def validate(
    doc: Any,
    companies: Dict[str, CompanyInfo],
    require_all_companies: bool = False,
) -> ValidationResult:
    """Prüft ein geladenes annotations.json-Dokument gegen eine Unternehmensliste.
    Reine Funktion: kein Datei-, DB- oder Netzwerkzugriff."""
    result = ValidationResult(companies_total=len(companies))

    if not isinstance(doc, dict):
        result.errors.append(f"Die Datei muss ein JSON-Objekt sein, ist {type(doc).__name__}.")
        return result
    for key in ("version", "hinweise", "annotations"):
        if key not in doc:
            result.errors.append(f"Schlüssel '{key}' fehlt auf oberster Ebene.")
    if result.errors:
        return result
    if isinstance(doc["version"], bool) or not isinstance(doc["version"], int) or doc["version"] < 1:
        result.errors.append(f"version muss eine ganze Zahl ab 1 sein, ist {doc['version']!r}.")
    if not isinstance(doc["hinweise"], dict):
        result.errors.append("hinweise muss ein JSON-Objekt sein.")
    annotations = doc["annotations"]
    if not isinstance(annotations, list):
        result.errors.append(f"annotations muss eine Liste sein, ist {type(annotations).__name__}.")
        return result
    result.n_entries = len(annotations)

    seen: Dict[Tuple[str, str, str, str, str], int] = {}
    spans: Dict[Tuple[str, str, str], List[Tuple[str, str, int]]] = {}
    annotated: Dict[str, str] = {}
    for i, entry in enumerate(annotations, start=1):
        errs, warns, key = _check_entry(i, entry, companies)
        result.errors.extend(errs)
        result.warnings.extend(warns)
        if key is None:
            continue
        norm, source, dimension, p_from, p_to = key
        annotated[norm] = companies[norm].name
        if key in seen:
            result.errors.append(
                f"{_label(i, entry)}: Duplikat von Eintrag #{seen[key]} "
                f"(gleiche company/source/dimension/period_from/period_to)."
            )
            continue
        seen[key] = i
        for o_from, o_to, o_i in spans.get((norm, source, dimension), []):
            if p_from <= o_to and o_from <= p_to:
                result.warnings.append(
                    f"{_label(i, entry)}: Zeitraum {p_from}..{p_to} überschneidet sich mit Eintrag #{o_i} "
                    f"({o_from}..{o_to}) derselben Dimension."
                )
            else:
                gap = (_month_index(p_from) - _month_index(o_to) - 1 if p_from > o_to
                       else _month_index(o_from) - _month_index(p_to) - 1)
                if gap < MIN_GAP_MONTHS:
                    result.warnings.append(
                        f"{_label(i, entry)}: nur {gap} Monat(e) Abstand zu Eintrag #{o_i} ({o_from}..{o_to}); "
                        f"Protokoll-Regel 5 verlangt mindestens {MIN_GAP_MONTHS} bewertete Monate."
                    )
        spans.setdefault((norm, source, dimension), []).append((p_from, p_to, i))

    result.companies_annotated = sorted(annotated.values(), key=str.casefold)
    result.companies_missing = sorted(
        (c.name for n, c in companies.items() if n not in annotated), key=str.casefold
    )
    if require_all_companies and result.companies_missing:
        result.errors.append(
            f"{len(result.companies_missing)} von {result.companies_total} Unternehmen ohne Annotation "
            f"(--require-all-companies): {', '.join(result.companies_missing)}."
        )
    return result


def format_report(result: ValidationResult, path: str = "") -> str:
    lines: List[str] = []
    lines.append(f"Validierung der Annotationen{(' in ' + path) if path else ''}")
    lines.append(f"  Einträge: {result.n_entries}")
    lines.append(
        f"  Annotierte Unternehmen: {len(result.companies_annotated)} von {result.companies_total}"
        + (f" ({', '.join(result.companies_annotated)})" if result.companies_annotated else "")
    )
    if result.companies_missing:
        lines.append(f"  Ohne Annotation: {', '.join(result.companies_missing)}")
    if result.warnings:
        lines.append(f"  Warnungen ({len(result.warnings)}):")
        lines.extend(f"    - {w}" for w in result.warnings)
    if result.errors:
        lines.append(f"  Fehler ({len(result.errors)}):")
        lines.extend(f"    - {e}" for e in result.errors)
    lines.append("Ergebnis: " + ("OK, keine Fehler." if result.ok else f"FEHLER ({len(result.errors)})."))
    return "\n".join(lines)


# ── CLI ──────────────────────────────────────────────────────────────────────

def _load_json(path: str, what: str) -> Tuple[Optional[Any], Optional[str]]:
    if not os.path.exists(path):
        return None, f"{what} nicht gefunden: {path}"
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh), None
    except json.JSONDecodeError as exc:
        return None, f"{what} ist kein gültiges JSON ({path}): {exc.msg} in Zeile {exc.lineno}, Spalte {exc.colno}"


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--file", default=DEFAULT_FILE, help=f"Annotationsdatei (Default: {DEFAULT_FILE})")
    parser.add_argument("--density", default=DEFAULT_DENSITY, help=f"data_density.json (Default: {DEFAULT_DENSITY})")
    parser.add_argument("--offline", action="store_true", help="Unternehmensliste aus data_density.json statt aus der DB")
    parser.add_argument("--require-all-companies", action="store_true",
                        help="Fehler, wenn ein Nicht-Demo-Unternehmen keinen Eintrag hat")
    parser.add_argument("--series-dir", default=DEFAULT_SERIES_DIR,
                        help=f"Serien-CSVs für die Protokollregeln 3 und 5 (Default: {DEFAULT_SERIES_DIR})")
    parser.add_argument("--no-series", action="store_true",
                        help="Serien-CSVs nicht laden (Regeln 3 und 5 werden dann nicht geprüft)")
    args = parser.parse_args(argv)

    density, err = _load_json(args.density, "data_density.json")
    if err:
        print(f"FEHLER: {err}\nHinweis: zuerst 'uv run python scripts/report_data_density.py' ausführen.")
        return 1
    doc, err = _load_json(args.file, "Annotationsdatei")
    if err:
        print(f"FEHLER: {err}")
        return 1

    load_warnings: List[str] = []
    if args.offline:
        companies = companies_from_density(density)
        mode = "offline (Unternehmen aus data_density.json)"
    else:
        companies = companies_from_db(density, load_warnings)
        mode = "online (Unternehmen aus der Datenbank, nur SELECT)"

    if not companies:
        print(
            f"FEHLER: keine Nicht-Demo-Unternehmen gefunden (Modus: {mode}).\n"
            "Hinweis: data_density.json prüfen bzw. 'uv run python scripts/report_data_density.py' ausführen."
        )
        return 1
    if not args.no_series and os.path.isdir(args.series_dir):
        attach_series_counts(companies, args.series_dir, load_warnings)
    elif not args.no_series:
        load_warnings.append(
            f"Serien-Verzeichnis {args.series_dir} fehlt; Protokoll-Regeln 3 und 5 werden nicht geprüft."
        )
    result = validate(doc, companies, require_all_companies=args.require_all_companies)
    result.warnings = load_warnings + result.warnings
    print(f"Modus: {mode}")
    print(format_report(result, args.file))
    return 0 if result.ok else 1


if __name__ == "__main__":
    sys.exit(main())
