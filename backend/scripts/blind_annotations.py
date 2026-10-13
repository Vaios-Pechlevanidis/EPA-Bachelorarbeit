"""
Rückweg der blinden Zweitannotation (DZ1, E5): übersetzt eine Annotationsdatei aus dem
blinden Annotationsbogen (``scripts/make_annotation_sheet.py --blind``) mit dessen
Schlüssel in das Schema von ``data/annotations.json`` und prüft das Ergebnis mit
``scripts/validate_annotations.py`` (offline).

Blinde Datei: Schema wie annotations.json (``{version, hinweise, annotations}``), aber
``company`` = Bezeichnung der Reihe im Bogen („Reihe A“) und ``period_from`` /
``period_to`` = Monatsindex („M015“). ``source`` und ``dimension`` dürfen fehlen; sonst
müssen sie zur Reihe passen. Bezeichnung und Index werden ohne Beachtung von Leerraum und
Groß-/Kleinschreibung gelesen („reihe a“, „m15“).

Übersetzung (reine Funktion ``unblind``):

- ``company`` -> Name aus ``data_density.json`` über die Unternehmens-id im Schlüssel,
- ``period_from`` / ``period_to`` -> YYYY-MM nach dem Schlüssel,
- Monatsindizes in der ``note`` (Mxxx, wie bei den Feldern auch „M5“ oder „m5“) -> YYYY-MM
  derselben Reihe; Indizes außerhalb der Reihe bleiben mit Warnung stehen; sonst bleibt die note
  wörtlich, ``direction`` unverändert, die Reihenfolge der Einträge ebenso,
- ``source`` und ``dimension`` aus dem Schlüssel,
- ``hinweise.herkunft`` vermerkt blinde Datei, Bogen mit Prüfsumme, Datum und die
  Zuordnung Reihe -> Unternehmen (``compare_annotations.py --series`` liest sie).

``reblind`` ist die Umkehrung (Tests: Schlüssel und Rückübersetzung sind invers).

Prüfung: ``validate_annotations.validate`` gegen die Unternehmen aus ``data_density.json``
mit den Monatszählungen der Serien-CSVs (Regeln 2, 3 und 5). Mit ``--for-person`` folgen
Fehler und Warnungen zusätzlich in der Schreibweise des Bogens (Reihe, Mxxx), damit sie
ohne Namen und Kalenderdaten an die Person zurückgehen können.

``--template`` schreibt eine leere Vorlage für die Person; sie nennt nur die Bezeichnungen
der Reihen und ihre Indexbereiche, keine Zuordnung. Eine vorhandene Datei wird nur mit
``--force`` überschrieben.

Das Skript liest nur Dateien, schreibt nie ``data/annotations.json`` und importiert keinen
Erkennungscode. Tests: ``backend/tests/test_blind_annotations.py``.

Verwendung
----------
    cd backend
    uv run python scripts/blind_annotations.py --template       # -> data/annotations_zweitperson_blind.json
    uv run python scripts/blind_annotations.py                  # -> data/annotations_zweitperson.json, mit Prüfung
    uv run python scripts/blind_annotations.py --for-person     # Prüfbericht zusätzlich in blinder Schreibweise
    uv run python scripts/blind_annotations.py --blind-file <datei> --key <schluessel> --out <ziel>
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import date
from typing import Any, Dict, List, Optional, Tuple

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND_DIR)
sys.path.insert(0, os.path.join(BACKEND_DIR, "scripts"))

import make_annotation_sheet as mas  # noqa: E402
import validate_annotations as va  # noqa: E402

DEFAULT_KEY = mas.DEFAULT_KEY
DEFAULT_BLIND = os.path.join(BACKEND_DIR, "data", "annotations_zweitperson_blind.json")
DEFAULT_OUT = os.path.join(BACKEND_DIR, "data", "annotations_zweitperson.json")
DEFAULT_DENSITY = os.path.join(BACKEND_DIR, "data", "data_density.json")
DEFAULT_SERIES_DIR = os.path.join(BACKEND_DIR, "data", "series")
# Die Referenz des Autors; das Skript schreibt sie nie.
PROTECTED_FILE = os.path.join(BACKEND_DIR, "data", "annotations.json")

_INDEX_RE = re.compile(r"^M(\d+)$")
# Monatsindizes in der note: dieselbe Lesart wie period_from/period_to (_parse_index), also auch
# Kurzformen wie „M5“ oder „m5“; sonst blieben blinde Indizes ohne Hinweis in der übersetzten Datei.
_NOTE_INDEX_RE = re.compile(r"\b[Mm](\d+)\b")
_NOTE_MONTH_RE = re.compile(r"\b\d{4}-(?:0[1-9]|1[0-2])\b")
_ENTRY_RE = re.compile(r"^Eintrag #(\d+)")


# ── Schlüssel ────────────────────────────────────────────────────────────────

def _norm(raw: Any) -> str:
    return " ".join(str(raw).split()).casefold()


def check_key(key: Any) -> List[str]:
    """Grundstruktur des Schlüssels aus ``make_annotation_sheet.py --blind``."""
    if not isinstance(key, dict) or not isinstance(key.get("reihen"), dict) or not key["reihen"]:
        return ["Schlüssel ohne 'reihen' (erwartet: Datei aus make_annotation_sheet.py --blind)."]
    errors: List[str] = []
    for label, info in key["reihen"].items():
        if not isinstance(info, dict) or not isinstance(info.get("monate"), dict) or "company_id" not in info:
            errors.append(f"Schlüssel: Eintrag '{label}' ohne company_id oder monate.")
    return errors


def series_maps(info: Dict[str, Any]) -> Tuple[Dict[int, str], Dict[str, str]]:
    """(Index -> YYYY-MM, YYYY-MM -> Mxxx) einer Reihe aus dem Schlüssel."""
    forward: Dict[int, str] = {}
    back: Dict[str, str] = {}
    for label, period in (info.get("monate") or {}).items():
        m = _INDEX_RE.match(str(label))
        if m:
            forward[int(m.group(1))] = period
            back[period] = label
    return forward, back


def _index_range(info: Dict[str, Any]) -> str:
    labels = list((info.get("monate") or {}).keys())
    return f"{labels[0]} bis {labels[-1]}" if labels else "–"


def _parse_index(raw: Any) -> Optional[int]:
    m = _INDEX_RE.match(" ".join(str(raw or "").split()).upper())
    return int(m.group(1)) if m else None


# ── Übersetzung (rein) ───────────────────────────────────────────────────────

def unblind(blind_doc: Dict[str, Any], key: Dict[str, Any], names: Optional[Dict[int, str]] = None,
            today: Optional[date] = None, blind_file: str = "") -> Tuple[Dict[str, Any], List[str], List[str]]:
    """Blinde Annotationsdatei -> Schema von annotations.json; reine Funktion.
    ``names`` ist ``id -> Name`` aus data_density.json (fehlt eine id, gilt der Name aus dem
    Schlüssel). Liefert (Dokument, Fehler, Warnungen); alle Meldungen in der Schreibweise des
    Bogens. Bei Fehlern fehlen die betroffenen Einträge im Dokument."""
    names = names or {}
    today = today or date.today()
    errors: List[str] = []
    warnings: List[str] = []
    labels = {_norm(label): label for label in key["reihen"]}
    entries: List[Dict[str, Any]] = []
    raw_entries = blind_doc.get("annotations")
    if not isinstance(raw_entries, list):
        return {}, ["annotations muss eine Liste sein."], warnings
    for i, entry in enumerate(raw_entries, start=1):
        if not isinstance(entry, dict):
            errors.append(f"Eintrag #{i}: muss ein JSON-Objekt sein.")
            continue
        label = labels.get(_norm(entry.get("company", "")))
        if label is None:
            errors.append(f"Eintrag #{i}: Reihe '{entry.get('company')}' gibt es im Bogen nicht "
                          f"(gültig: {', '.join(key['reihen'])}).")
            continue
        info = key["reihen"][label]
        forward, _ = series_maps(info)
        n_errors = len(errors)
        periods: Dict[str, str] = {}
        for field in ("period_from", "period_to"):
            index = _parse_index(entry.get(field))
            if index is None:
                errors.append(f"Eintrag #{i} ({label}): {field} '{entry.get(field)}' hat nicht die Form Mxxx (z. B. M015).")
            elif index not in forward:
                errors.append(f"Eintrag #{i} ({label}): {field} '{entry.get(field)}' liegt außerhalb der Reihe "
                              f"({_index_range(info)}).")
            else:
                periods[field] = forward[index]
        for field in ("source", "dimension"):
            if field in entry and entry[field] != info.get(field):
                errors.append(f"Eintrag #{i} ({label}): {field} '{entry[field]}' passt nicht zur Reihe "
                              f"(erwartet '{info.get(field)}').")
        extra = [k for k in entry if k not in va.REQUIRED_KEYS]
        if extra:
            warnings.append(f"Eintrag #{i} ({label}): Felder ohne Entsprechung im Schema werden nicht übernommen: "
                            f"{', '.join(extra)}.")
        if len(periods) < 2 or len(errors) > n_errors:
            continue
        company_id = int(info["company_id"])
        name = names.get(company_id)
        if not name:
            name = str(info.get("name") or "")
            warnings.append(f"Eintrag #{i} ({label}): Unternehmen fehlt in data_density.json; Name aus dem Schlüssel übernommen.")
        out: Dict[str, Any] = {"company": name, "source": info.get("source"), "dimension": info.get("dimension"),
                               **periods}
        if "direction" in entry:
            out["direction"] = entry["direction"]
        if "note" in entry:
            note = entry["note"]
            if isinstance(note, str):
                unknown = sorted({m.group(0) for m in _NOTE_INDEX_RE.finditer(note) if int(m.group(1)) not in forward})
                if unknown:
                    warnings.append(f"Eintrag #{i} ({label}): note nennt {', '.join(unknown)}; diese Indizes liegen "
                                    "außerhalb der Reihe und bleiben unverändert.")
                note = _NOTE_INDEX_RE.sub(lambda m: forward.get(int(m.group(1)), m.group(0)), note)
            out["note"] = note
        entries.append({k: out[k] for k in va.REQUIRED_KEYS if k in out})
    version = blind_doc.get("version", 1)
    doc = {
        "version": version,
        "hinweise": {
            "zweck": ("Referenzzeiträume einer zweiten Person aus der blinden Zweitannotation (DZ1, E5): eingetragen "
                      "ohne Kenntnis von Unternehmen und Kalenderdaten, allein aus dem blinden Annotationsbogen "
                      "(Beurteilung 'Reihe allein'), mit dem Schlüssel mechanisch in das Schema von annotations.json "
                      "übersetzt (company, source, dimension, period_from, period_to und die Monatsindizes der note). "
                      "Vergleich mit dem Autor: scripts/compare_annotations.py."),
            "herkunft": {
                "blinddatei": blind_file,
                "uebersetzt_am": today.isoformat(),
                "bogen": key.get("bogen"),
                "bogen_sha256": key.get("bogen_sha256"),
                "schluessel_erzeugt_am": key.get("erzeugt_am"),
                "source": key.get("source"),
                "dimension": key.get("dimension"),
                "reihen": {
                    label: {"company_id": int(info["company_id"]),
                            "company": names.get(int(info["company_id"])) or info.get("name")}
                    for label, info in key["reihen"].items()
                },
            },
        },
        "annotations": entries,
    }
    return doc, errors, warnings


def reblind(doc: Dict[str, Any], key: Dict[str, Any], names: Optional[Dict[int, str]] = None) -> Tuple[Dict[str, Any], List[str]]:
    """Umkehrung von ``unblind``: Schema von annotations.json -> blinde Schreibweise; reine
    Funktion. Nur Einträge der Reihen im Schlüssel; Kalendermonate der note, die zur Reihe
    gehören, werden zu Mxxx. Liefert (blindes Dokument, Fehler)."""
    names = names or {}
    by_name: Dict[str, str] = {}
    for label, info in key["reihen"].items():
        for alias in (info.get("name"), names.get(int(info["company_id"]))):
            if alias:
                by_name[_norm(alias)] = label
    errors: List[str] = []
    entries: List[Dict[str, Any]] = []
    for i, entry in enumerate(doc.get("annotations") or [], start=1):
        label = by_name.get(_norm(entry.get("company", "")))
        if label is None:
            errors.append(f"Eintrag #{i}: Unternehmen nicht im Schlüssel.")
            continue
        _, back = series_maps(key["reihen"][label])
        if entry.get("period_from") not in back or entry.get("period_to") not in back:
            errors.append(f"Eintrag #{i} ({label}): Monat außerhalb der Reihe.")
            continue
        out = {"company": label, "source": entry.get("source"), "dimension": entry.get("dimension"),
               "period_from": back[entry["period_from"]], "period_to": back[entry["period_to"]],
               "direction": entry.get("direction")}
        note = entry.get("note")
        out["note"] = _NOTE_MONTH_RE.sub(lambda m: back.get(m.group(0), m.group(0)), note) if isinstance(note, str) else note
        entries.append(out)
    return {"version": doc.get("version", 1), "hinweise": {}, "annotations": entries}, errors


def person_messages(messages: List[str], doc: Dict[str, Any], key: Dict[str, Any],
                    names: Optional[Dict[int, str]] = None) -> List[str]:
    """Meldungen des Validators in der Schreibweise des Bogens; reine Funktion. Namen werden
    zu „Reihe X“, Kalendermonate der Reihe des gemeldeten Eintrags zu Mxxx; was danach noch
    wie ein Kalendermonat aussieht, wird zu „[Monat]“."""
    names = names or {}
    aliases: List[Tuple[str, str]] = []
    for label, info in key["reihen"].items():
        for alias in {str(info.get("name") or ""), str(names.get(int(info["company_id"])) or "")}:
            if alias:
                aliases.append((alias, label))
    aliases.sort(key=lambda a: -len(a[0]))      # längere Namen zuerst („E.ON Digital Technology“ vor „E.ON“)
    by_name = {_norm(alias): label for alias, label in aliases}
    entry_label: Dict[int, str] = {}
    for i, entry in enumerate(doc.get("annotations") or [], start=1):
        label = by_name.get(_norm(entry.get("company", "")))
        if label:
            entry_label[i] = label
    out: List[str] = []
    for msg in messages:
        text = msg
        for alias, label in aliases:
            text = re.sub(r"(?<!\w)" + re.escape(alias) + r"(?!\w)", label, text, flags=re.IGNORECASE)
        m = _ENTRY_RE.match(msg)
        label = entry_label.get(int(m.group(1))) if m else None
        if label:
            _, back = series_maps(key["reihen"][label])
            text = _NOTE_MONTH_RE.sub(lambda mm: back.get(mm.group(0), mm.group(0)), text)
        out.append(mas.DATE_RE.sub("[Monat]", text))
    return out


def template_doc(key: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Leere Vorlage für die Person: Felder, Beispiel und (mit Schlüssel) die Reihen des Bogens
    mit ihren Indexbereichen, ohne Zuordnung."""
    source = (key or {}).get("source") or "employee"
    dimension = (key or {}).get("dimension") or "durchschnittsbewertung"
    hinweise: Dict[str, Any] = {
        "zweck": ("Vorlage für die blinde Zweitannotation der Referenzzeiträume (DZ1, E5). Einträge allein aus dem "
                  "blinden Annotationsbogen; Unternehmen und Kalenderdaten sind dort bewusst nicht genannt. "
                  "Anleitung: docs/annotation-anleitung.md."),
        "felder": {
            "company": "Bezeichnung der Reihe wie im Bogen, z. B. 'Reihe A'.",
            "source": f"'{source}' (wie im Bogen).",
            "dimension": f"'{dimension}' (Gesamtbewertung).",
            "period_from": "Erster Monat als Index wie in der Monatstabelle, z. B. 'M015'.",
            "period_to": "Letzter Monat als Index; gleich oder später als period_from.",
            "direction": "'rise' (Anstieg) oder 'fall' (Abfall).",
            "note": "Deutsche Begründung nach Regel 11 der blinden Fassung, Monate als Index; am Ende 'Reihe allein'.",
        },
        "beispiel_format": {
            "company": "Reihe A", "source": source, "dimension": dimension, "period_from": "M015",
            "period_to": "M016", "direction": "fall", "note": mas.BLIND_NOTE_BEISPIEL,
        },
    }
    if key:
        hinweise["reihen_im_bogen"] = {label: _index_range(info) for label, info in key["reihen"].items()}
    return {"version": 1, "hinweise": hinweise, "annotations": []}


# ── Berichte ─────────────────────────────────────────────────────────────────

def format_person_report(result: va.ValidationResult, messages_errors: List[str], messages_warnings: List[str],
                         conversion_warnings: List[str]) -> str:
    lines = ["Prüfbericht in der Schreibweise des Bogens (zur Weitergabe an die annotierende Person)",
             f"  Einträge: {result.n_entries}"]
    warnings = conversion_warnings + messages_warnings
    if warnings:
        lines.append(f"  Warnungen ({len(warnings)}):")
        lines.extend(f"    - {w}" for w in warnings)
    if messages_errors:
        lines.append(f"  Fehler ({len(messages_errors)}):")
        lines.extend(f"    - {e}" for e in messages_errors)
    lines.append("Ergebnis: " + ("OK, keine Fehler." if result.ok else f"FEHLER ({len(result.errors)})."))
    return "\n".join(lines)


def _write_json(path: str, doc: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, ensure_ascii=False, indent=2)
        fh.write("\n")


def _rel(path: str) -> str:
    return os.path.relpath(path, BACKEND_DIR)


# ── CLI ──────────────────────────────────────────────────────────────────────

def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--key", default=DEFAULT_KEY, help="Schlüssel des blinden Bogens (Default: data/annotationsbogen_blind_schluessel.json)")
    parser.add_argument("--blind-file", default=DEFAULT_BLIND,
                        help="blinde Annotationsdatei der Person (Default: data/annotations_zweitperson_blind.json)")
    parser.add_argument("--out", default=DEFAULT_OUT, help="übersetzte Datei (Default: data/annotations_zweitperson.json)")
    parser.add_argument("--density", default=DEFAULT_DENSITY, help="data_density.json für Namen und Datenzeiträume")
    parser.add_argument("--series-dir", default=DEFAULT_SERIES_DIR, help="Serien-CSVs für die Protokollregeln 3 und 5")
    parser.add_argument("--template", action="store_true", help="leere Vorlage nach --blind-file schreiben und beenden")
    parser.add_argument("--force", action="store_true", help="mit --template: vorhandene Datei überschreiben")
    parser.add_argument("--for-person", action="store_true",
                        help="Prüfbericht zusätzlich in der Schreibweise des Bogens (Reihe, Mxxx) ausgeben")
    args = parser.parse_args(argv)

    key, key_err = va._load_json(args.key, "Schlüssel des blinden Bogens")
    key_errors = [key_err] if key_err else check_key(key)

    if args.template:
        if os.path.exists(args.blind_file) and not args.force:
            print(f"FEHLER: {args.blind_file} gibt es schon; sie kann Einträge der Person enthalten. Überschreiben nur mit --force.")
            return 1
        if key_errors:
            print(f"Hinweis: {key_errors[0]} Die Vorlage nennt deshalb keine Reihen.")
        _write_json(args.blind_file, template_doc(None if key_errors else key))
        print(f"Vorlage geschrieben: {args.blind_file}. Sie nennt nur Bezeichnungen der Reihen und Indexbereiche, keine Zuordnung.")
        return 0

    if key_errors:
        print("FEHLER: " + " ".join(key_errors))
        return 1
    if os.path.abspath(args.out) in (os.path.abspath(PROTECTED_FILE), os.path.abspath(args.blind_file), os.path.abspath(args.key)):
        print(f"FEHLER: Ziel {args.out} ist die Referenz des Autors, die blinde Datei oder der Schlüssel; bitte ein anderes --out wählen.")
        return 1
    blind_doc, err = va._load_json(args.blind_file, "Blinde Annotationsdatei")
    if err:
        print(f"FEHLER: {err}\nHinweis: Vorlage mit 'uv run python scripts/blind_annotations.py --template' erzeugen.")
        return 1
    if not isinstance(blind_doc, dict) or not isinstance(blind_doc.get("annotations"), list):
        print(f"FEHLER: {args.blind_file} hat nicht das Schema {{version, hinweise, annotations}}.")
        return 1
    density, err = va._load_json(args.density, "data_density.json")
    if err:
        print(f"FEHLER: {err}")
        return 1

    names = mas.company_names(args.density)
    doc, errors, conversion_warnings = unblind(blind_doc, key, names, blind_file=os.path.basename(args.blind_file))
    if errors:
        print(f"Übersetzung nicht möglich, nichts geschrieben ({len(errors)} Fehler, Schreibweise des Bogens):")
        print("\n".join(f"  - {e}" for e in errors + conversion_warnings))
        return 1
    _write_json(args.out, doc)
    print(f"Übersetzt: {len(doc['annotations'])} Einträge aus {args.blind_file} -> {args.out}")

    companies = va.companies_from_density(density)
    load_warnings: List[str] = []
    if os.path.isdir(args.series_dir):
        va.attach_series_counts(companies, args.series_dir, load_warnings)
    else:
        load_warnings.append(f"Serien-Verzeichnis {args.series_dir} fehlt; Protokoll-Regeln 3 und 5 werden nicht geprüft.")
    result = va.validate(doc, companies)
    person_errors = person_messages(result.errors, doc, key, names)
    person_warnings = person_messages(result.warnings, doc, key, names)
    author_result = va.ValidationResult(
        errors=result.errors, warnings=load_warnings + conversion_warnings + result.warnings, n_entries=result.n_entries,
        companies_total=result.companies_total, companies_annotated=result.companies_annotated,
        companies_missing=result.companies_missing,
    )
    print(va.format_report(author_result, _rel(args.out) if os.path.abspath(args.out).startswith(BACKEND_DIR) else args.out))
    if args.for_person:
        print()
        print(format_person_report(result, person_errors, person_warnings, conversion_warnings))
    return 0 if result.ok else 1


if __name__ == "__main__":
    sys.exit(main())
