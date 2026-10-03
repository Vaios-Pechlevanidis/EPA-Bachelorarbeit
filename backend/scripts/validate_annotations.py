"""
Validator für die manuellen Referenzannotationen (Prüfpunkt 5 des
Fundament-Checks, Inkrement 0).

Zweck
-----
Prüft ``backend/data/annotations.json`` auf

- gültiges JSON und die Grundstruktur {"version": 1, "hinweise": {...}, "annotations": [...]}
- Pflichtfelder je Eintrag: company, source, dimension, period_from, period_to, direction, note
- company: auflösbar über den bereinigten Namen (strip, Whitespace-Kollaps,
  casefold) gegen die Unternehmen der Datenbank (Standard) bzw. gegen die
  Unternehmensliste in ``backend/data/data_density.json`` (``--offline``);
  Demo-Unternehmen sind nicht zulässig
- source in {employee, candidates}; dimension = "durchschnittsbewertung" oder
  ein Themen-Schlüssel der jeweiligen Quelle
- period_from / period_to im Format YYYY-MM, period_from <= period_to, beide
  innerhalb des Datenzeitraums des Unternehmens für diese Quelle (aus
  ``data_density.json``, daher wird diese Datei immer benötigt)
- direction in {rise, fall}; note nicht leer
- keine Duplikate (gleiche company/source/dimension/period_from/period_to);
  Überschneidungen derselben Dimension werden als Warnung gemeldet

Gibt einen deutschen Bericht aus und beendet sich mit Exit-Code 1 bei
Fehlern. Mit ``--require-all-companies`` gilt zusätzlich als Fehler, wenn ein
Nicht-Demo-Unternehmen keinen Eintrag hat.

Die Prüf-Logik ist als reine Funktion ``validate()`` ohne Datenbank- oder
Dateizugriff implementiert, damit sie in Tests mit In-Memory-Fixtures
verwendet werden kann (siehe ``tests/test_annotations_validator.py``).

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
import json
import os
import re
import sys
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND_DIR)

from services.topic_average_rating_service import (  # noqa: E402
    CANDIDATES_TOPIC_COLUMNS,
    EMPLOYEE_TOPIC_COLUMNS,
)

DEFAULT_FILE = os.path.join(BACKEND_DIR, "data", "annotations.json")
DEFAULT_DENSITY = os.path.join(BACKEND_DIR, "data", "data_density.json")

VALID_SOURCES: Tuple[str, ...] = ("employee", "candidates")
VALID_DIRECTIONS: Tuple[str, ...] = ("rise", "fall")
REQUIRED_KEYS: Tuple[str, ...] = (
    "company", "source", "dimension", "period_from", "period_to", "direction", "note",
)
DIMENSIONS_BY_SOURCE: Dict[str, List[str]] = {
    "employee": ["durchschnittsbewertung"] + list(EMPLOYEE_TOPIC_COLUMNS.keys()),
    "candidates": ["durchschnittsbewertung"] + list(CANDIDATES_TOPIC_COLUMNS.keys()),
}
PERIOD_RE = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")
_DEMO_RE = re.compile(r"^demo\s*\d+$")


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
    if isinstance(doc["version"], bool) or doc["version"] != 1:
        result.errors.append(f"version muss 1 sein, ist {doc['version']!r}.")
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
    result = validate(doc, companies, require_all_companies=args.require_all_companies)
    result.warnings = load_warnings + result.warnings
    print(f"Modus: {mode}")
    print(format_report(result, args.file))
    return 0 if result.ok else 1


if __name__ == "__main__":
    sys.exit(main())
