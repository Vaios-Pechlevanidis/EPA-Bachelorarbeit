#!/usr/bin/env python3
"""Prüft, ob eine Textdatei Titel von Meldungen enthält (E7, DZ1-Archiv in docs/dz1-referenz/).

Hilfsskript zur bereinigten Fassung des DZ1-Entscheidungsprotokolls
(``entscheidungsprotokoll_2026-10-09.md``). Es vergleicht den Text mit einer Menge
von Titeln, die aus lokalen JSON-Dateien gelesen werden (Feld ``title`` in jeder
Liste ``items``, beliebig tief verschachtelt), zum Beispiel aus dem nicht
versionierten Belegspeicher ``backend/data/context/*/*/*.json``.

Geprüft wird nach Normalisierung (Kleinschreibung, Akzente und Umlaute auf den
Grundbuchstaben, jedes Nicht-Wortzeichen als Leerzeichen):

1. kein vollständiger Titel ab ``min_zeichen`` (Standard 25) Zeichen im Text;
2. keine Folge von ``n_woerter`` (Standard 8) aufeinanderfolgenden Wörtern eines
   Titels im Text;
3. kein Text in Anführungszeichen in Abschnitt 5 („Stufe B je Fall“), der mit
   mindestens ``zitat_woerter`` (Standard 4) Wörtern in einem Titel vorkommt;
   kürzere Zitate, die in einem Titel vorkommen (Bezeichnungen, Namen), werden
   nur gezählt.

Links (``http…``) sind ausgenommen: Datum, Quelle und Link dürfen stehen bleiben
(wie in ``backend/data/annotations.json``); EQS-Links enthalten den Titel als
Pfadbestandteil.

Das Skript gibt nur Zählungen und Zeilennummern aus, nie einen Titel. Nur
Standardbibliothek; keine Netzabrufe.

Aufruf (aus dem Repository-Wurzelverzeichnis):
  python3 docs/dz1-referenz/pruefe_bereinigung.py DATEI --titel 'backend/data/context/*/*/*.json'
      [--titel WEITERE_JSON ...] [--n 8] [--min-zeichen 25] [--zitat-woerter 4] [--json]
Exit-Code 0 ohne Treffer, 1 mit Treffern, 2 ohne Titel.
"""
import argparse
import glob
import json
import re
import sys
import unicodedata

URL = re.compile(r"https?://\S+")
ZITAT = re.compile(r'"([^"\n]{1,300})"|„([^“"\n]{1,300})[“"]|“([^”\n]{1,300})”')
ABSCHNITT5 = re.compile(r"^## 5 ")
ABSCHNITT_NEU = re.compile(r"^## \d+ ")


def normalisiere(text):
    """Kleinschreibung, ohne Akzente, Nicht-Wortzeichen als Leerzeichen, einfache Abstände."""
    t = unicodedata.normalize("NFKD", text.casefold())
    t = "".join(ch for ch in t if not unicodedata.combining(ch))
    return " ".join(re.sub(r"[^\w]+", " ", t).split())


def _titel_aus(obj, ziel):
    if isinstance(obj, dict):
        items = obj.get("items")
        if isinstance(items, list):
            for it in items:
                if isinstance(it, dict) and isinstance(it.get("title"), str) and it["title"].strip():
                    ziel.add(it["title"])
        for v in obj.values():
            if isinstance(v, (dict, list)):
                _titel_aus(v, ziel)
    elif isinstance(obj, list):
        for v in obj:
            if isinstance(v, (dict, list)):
                _titel_aus(v, ziel)


def lade_titel(muster):
    """Alle Titel aus den JSON-Dateien zu den Glob-Mustern; liefert (Titelmenge, Dateizahl)."""
    titel, dateien = set(), 0
    for m in muster:
        for pfad in sorted(glob.glob(m)):
            try:
                with open(pfad, encoding="utf-8") as fh:
                    _titel_aus(json.load(fh), titel)
                dateien += 1
            except (OSError, ValueError):
                continue
    return titel, dateien


def _folgen(woerter, n):
    return {" ".join(woerter[i:i + n]) for i in range(len(woerter) - n + 1)}


class _Titelindex:
    """Normalisierte Titel mit Index für vollständige Treffer und Wortfolgen beliebiger Länge."""

    def __init__(self, titel, min_zeichen):
        self.woerter = [t.split() for t in {normalisiere(t) for t in titel} if t.strip()]
        self.woerter = [w for w in self.woerter if w]
        self.voll = {}
        for w in self.woerter:
            if len(" ".join(w)) >= min_zeichen:
                self.voll.setdefault(w[0], []).append(w)
        self._folgen = {}

    def folgen(self, n):
        if n not in self._folgen:
            s = set()
            for w in self.woerter:
                s |= _folgen(w, n)
            self._folgen[n] = s
        return self._folgen[n]

    def enthaelt_volltitel(self, woerter):
        for i, wort in enumerate(woerter):
            for t in self.voll.get(wort, ()):
                if woerter[i:i + len(t)] == t:
                    return True
        return False

    def ist_teil_eines_titels(self, woerter):
        return " ".join(woerter) in self.folgen(len(woerter))


def pruefe(text, titel, n_woerter=8, min_zeichen=25, zitat_woerter=4):
    """Reine Prüfung; liefert nur Zählungen und Zeilennummern, keine Titel."""
    idx = _Titelindex(titel, min_zeichen)
    folgen = idx.folgen(n_woerter)
    erg = {"titel": len(idx.woerter), "volltitel_zeilen": [], "folgen_zeilen": [],
           "zitate_abschnitt5": 0, "zitate_lang_zeilen": [], "zitate_kurz_in_titel": 0}
    in5 = False
    for nr, zeile in enumerate(text.splitlines(), 1):
        if ABSCHNITT5.match(zeile):
            in5 = True
        elif ABSCHNITT_NEU.match(zeile):
            in5 = False
        ohne_link = URL.sub(" ", zeile)
        woerter = normalisiere(ohne_link).split()
        if idx.enthaelt_volltitel(woerter):
            erg["volltitel_zeilen"].append(nr)
        if _folgen(woerter, n_woerter) & folgen:
            erg["folgen_zeilen"].append(nr)
        if in5:
            for m in ZITAT.finditer(ohne_link):
                z = normalisiere(next(g for g in m.groups() if g is not None)).split()
                if not z:
                    continue
                erg["zitate_abschnitt5"] += 1
                if not idx.ist_teil_eines_titels(z):
                    continue
                if len(z) >= zitat_woerter:
                    erg["zitate_lang_zeilen"].append(nr)
                else:
                    erg["zitate_kurz_in_titel"] += 1
    erg["ok"] = not (erg["volltitel_zeilen"] or erg["folgen_zeilen"] or erg["zitate_lang_zeilen"])
    return erg


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("datei")
    ap.add_argument("--titel", action="append", required=True, help="Glob-Muster für JSON-Dateien mit items[].title")
    ap.add_argument("--n", type=int, default=8, help="Länge der Wortfolgen (Standard 8)")
    ap.add_argument("--min-zeichen", type=int, default=25, help="Mindestlänge vollständiger Titel (Standard 25)")
    ap.add_argument("--zitat-woerter", type=int, default=4, help="Mindestwortzahl langer Zitate (Standard 4)")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    titel, dateien = lade_titel(a.titel)
    if not titel:
        print("Keine Titel gefunden; Prüfung nicht möglich.")
        return 2
    with open(a.datei, encoding="utf-8") as fh:
        erg = pruefe(fh.read(), titel, a.n, a.min_zeichen, a.zitat_woerter)
    erg["dateien"] = dateien
    if a.json:
        print(json.dumps(erg, ensure_ascii=False))
    else:
        print(f"Titel: {erg['titel']} aus {dateien} Dateien")
        print(f"Zeilen mit vollständigem Titel (ab {a.min_zeichen} Zeichen): {len(erg['volltitel_zeilen'])} {erg['volltitel_zeilen']}")
        print(f"Zeilen mit {a.n} Wörtern in Folge aus einem Titel: {len(erg['folgen_zeilen'])} {erg['folgen_zeilen']}")
        print(f"Zitate in Abschnitt 5: {erg['zitate_abschnitt5']}; davon ab {a.zitat_woerter} Wörtern in einem Titel: "
              f"{len(erg['zitate_lang_zeilen'])} {erg['zitate_lang_zeilen']}; kürzer und in einem Titel: {erg['zitate_kurz_in_titel']}")
        print("Ergebnis: " + ("keine Treffer" if erg["ok"] else "TREFFER"))
    return 0 if erg["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
