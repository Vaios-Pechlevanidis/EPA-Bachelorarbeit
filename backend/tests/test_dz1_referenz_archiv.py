"""
Tests für das DZ1-Archiv unter ``docs/dz1-referenz/`` (Herkunft der Referenzzeiträume, E5).

Das Archiv enthält den Regelprüfer ``dz1_rechner.py`` und die Agentendefinition als
unveränderte Kopien, das Entscheidungsprotokoll vom 2026-10-09 in bereinigter Fassung
(Titel von Meldungen ersetzt, E7) und das Prüfskript ``pruefe_bereinigung.py``.

Geprüft wird:

1. **Unverändert:** Die SHA-256-Werte der Kopien entsprechen den Werten im README; für
   ``dz1_rechner.py`` und die Agentendefinition ist der Wert des Originals derselbe. Die
   Originale liegen außerhalb des Repositorys und werden nur verglichen, wenn sie lokal
   vorhanden sind.
2. **Regelprüfer auf die 20 Einträge** (offline, Serien-CSVs unter ``backend/data/series``):
   Die archivierte Kopie wird per ``importlib`` geladen und nicht verändert; sie hat keine
   fest eingetragenen Pfade, die CSV wird übergeben.
   - ``pruefe``: 19 Einträge „regelkonform“, ein Eintrag (Compugroup 2021-04 bis 2021-05,
     Δ +0,47) „zweifelsfall_0_3_bis_0_49“; dessen ``note`` nennt den Ereignisanker als Grund.
   - Richtung und die Zahlen am Anfang jeder ``note`` (Vorniveau, Zeitraum, Δ, Richtung)
     entsprechen dem Notizgerüst des Regelprüfers.
   - ``satz`` (Regel 5: höchstens drei Zeiträume, mindestens drei bewertete Monate Abstand)
     ist für jede der 8 Reihen mit Einträgen erfüllt.
   - Von den 7 geeigneten Reihen ohne Eintrag haben 6 keinen regelkonformen Kandidaten;
     Carl Zeiss hat genau einen (2023-04), den der Agent in Stufe A nach der Definition
     verworfen hat (Protokoll Abschnitt 6).
   - Annotationslauf 1 (verworfen; Abschnitt 4, 26 Zeiträume): Nach dem archivierten
     Regelprüfer sind 11 regelkonform und 15 verworfen. Der Fließtext des Protokolls nennt
     „bestehen davon 12; 14 scheitern“; diese Zahl lässt sich mit dem Regelprüfer nicht
     nachrechnen. Die Tabelle selbst ergibt 6 unverändert übernommen, 7 überlappend, 13 ohne
     Gegenstück.
   **Nicht mechanisch prüfbar** (agentische Entscheidungen, im Protokoll begründet):
   Abgrenzung nach der Definition (Setzung 5), Auswahl der drei deutlichsten (Setzung 4),
   Trendurteil nach Regel 2 (der Regelprüfer gibt nur einen Hinweis), Ankerwahl in Stufe B
   (Setzung 6; Quellen live abgerufen, Titel nicht versioniert) und damit die Aufnahme des
   Zweifelsfalls.
3. **Bereinigung:** Jede Ankerzeile und jede Ankerzelle trägt „[Titel entfernt]“, die Zahl
   der Ersetzungen entspricht dem README. Ist das Original lokal vorhanden, unterscheidet
   sich die Fassung davon nur in den Ersetzungen (11 Zeilen in Abschnitt 1, 63 in
   Abschnitt 5) und in drei Satzzeichen-Anpassungen. Ist der lokale Belegspeicher
   ``backend/data/context/`` vorhanden, findet ``pruefe_bereinigung.pruefe`` keinen Titel
   (ab 25 Zeichen), keine Folge von 8 Wörtern eines Titels und kein langes Zitat in
   Abschnitt 5. Fehlt Original oder Speicher, wird der jeweilige Teil übersprungen. Die
   schärfere Sichtung mit 4 und 5 Wörtern ist im README beschrieben und hängt von nicht
   versionierten Titeln ab; sie ist deshalb kein Test.

Kein Test wendet ``evaluate_detection``, ``compare_annotations`` oder
``report_explanation_validity`` an; die echte Annotationsdatei wird nur gelesen.

Ausführen:
    cd backend
    uv run python -m pytest tests/test_dz1_referenz_archiv.py -q -p no:cacheprovider
"""

import glob
import hashlib
import importlib.util
import json
import os
import re
import sys
from collections import Counter

import pytest

BACKEND_DIR = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
REPO_DIR = os.path.dirname(BACKEND_DIR)
ARCHIV = os.path.join(REPO_DIR, "docs", "dz1-referenz")
sys.path.insert(0, BACKEND_DIR)
sys.path.insert(0, os.path.join(BACKEND_DIR, "scripts"))

import validate_annotations as va  # noqa: E402  (nur für die Standardpfade)

README = os.path.join(ARCHIV, "README.md")
RECHNER = os.path.join(ARCHIV, "dz1_rechner.py")
AGENT = os.path.join(ARCHIV, "agent-dz1-referenzzeitraeume.md")
PROTOKOLL = os.path.join(ARCHIV, "entscheidungsprotokoll_2026-10-09.md")
PRUEFSKRIPT = os.path.join(ARCHIV, "pruefe_bereinigung.py")
BELEGSPEICHER = os.path.join(BACKEND_DIR, "data", "context", "*", "*", "*.json")
ERSATZ = "[Titel entfernt]"

# Der einzige Eintrag, der nur wegen seines Ereignisankers steht (|Δ| 0,30 bis 0,49).
ZWEIFELSFALL_MIT_ANKER = ("Compugroup Medical Deutschland", "2021-04", "2021-05")
# Geeignete Reihe ohne Eintrag, aber mit regelkonformem Kandidaten (Stufe A, Abschnitt 6).
AGENTISCH_VERWORFEN = {"Carl Zeiss": [("2023-04", "2023-04")]}


def _lade_modul(name, pfad):
    spec = importlib.util.spec_from_file_location(name, pfad)
    modul = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modul)
    return modul


rechner = _lade_modul("dz1_rechner_archiv", RECHNER)
pruefskript = _lade_modul("pruefe_bereinigung_archiv", PRUEFSKRIPT)


def _sha256(pfad):
    with open(pfad, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def _text(pfad):
    with open(pfad, encoding="utf-8") as fh:
        return fh.read()


def _readme_hashes(dateiname):
    """Alle SHA-256-Werte der Tabellenzeile, die mit `dateiname` beginnt, und der Herkunftspfad."""
    for zeile in _text(README).splitlines():
        hashes = re.findall(r"\b[0-9a-f]{64}\b", zeile)
        if zeile.startswith(f"| `{dateiname}` |") and hashes:
            zellen = [z.strip() for z in zeile.strip("|").split("|")]
            herkunft = zellen[1].strip("`")
            return hashes, herkunft
    raise AssertionError(f"{dateiname} fehlt in der Prüfsummentabelle des README")


def _eintraege():
    with open(va.DEFAULT_FILE, encoding="utf-8") as fh:
        return json.load(fh)["annotations"]


def _csv_je_name():
    with open(va.DEFAULT_DENSITY, encoding="utf-8") as fh:
        firmen = json.load(fh)["companies"]
    pfade = {}
    for c in firmen:
        treffer = glob.glob(os.path.join(va.DEFAULT_SERIES_DIR, f"{c['id']}_*_employee.csv"))
        if treffer:
            pfade[c["name"]] = treffer[0]
    return pfade


_ZEILEN_CACHE = {}


def _zeilen(name):
    if name not in _ZEILEN_CACHE:
        _ZEILEN_CACHE[name] = rechner.lese(_csv_je_name()[name])
    return _ZEILEN_CACHE[name]


# ---------------------------------------------------------------------------
# 1. Unveränderte Kopien und Prüfsummen
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("dateiname", ["dz1_rechner.py", "agent-dz1-referenzzeitraeume.md"])
def test_kopie_unveraendert_wie_im_readme(dateiname):
    hashes, _ = _readme_hashes(dateiname)
    assert len(hashes) == 2, hashes
    original, kopie = hashes
    assert original == kopie
    assert _sha256(os.path.join(ARCHIV, dateiname)) == kopie


def test_bereinigte_fassung_wie_im_readme():
    hashes, _ = _readme_hashes("entscheidungsprotokoll_2026-10-09.md")
    assert len(hashes) == 2, hashes
    original, kopie = hashes
    assert original != kopie
    assert _sha256(PROTOKOLL) == kopie
    # Der Vorspann der bereinigten Fassung nennt den Wert des Originals.
    assert original in _text(PROTOKOLL).split("\n# ", 1)[0]


@pytest.mark.parametrize("dateiname", ["dz1_rechner.py", "agent-dz1-referenzzeitraeume.md",
                                       "entscheidungsprotokoll_2026-10-09.md"])
def test_original_unveraendert_falls_lokal_vorhanden(dateiname):
    hashes, herkunft = _readme_hashes(dateiname)
    pfad = os.path.normpath(os.path.join(REPO_DIR, herkunft))
    if not os.path.exists(pfad):
        pytest.skip(f"Original außerhalb des Repositorys nicht vorhanden: {herkunft}")
    assert _sha256(pfad) == hashes[0]


def test_rechner_ohne_feste_pfade_und_ohne_projektimporte():
    quelle = _text(RECHNER)
    assert not re.search(r"^\s*(from|import)\s+(services|models)\b", quelle, re.M)
    assert "/Users/" not in quelle and "backend/data/series/" not in quelle.split('"""', 2)[2]


# ---------------------------------------------------------------------------
# 2. Regelprüfer auf die 20 Einträge (offline)
# ---------------------------------------------------------------------------

def test_jeder_eintrag_regelkonform_bis_auf_einen_zweifelsfall_mit_anker():
    eintraege = _eintraege()
    assert len(eintraege) == 20
    ergebnisse = {}
    for e in eintraege:
        p = rechner.pruefe(_zeilen(e["company"]), e["period_from"], e["period_to"])
        ergebnisse[(e["company"], e["period_from"], e["period_to"])] = (p["ergebnis"], e["note"])
    assert Counter(v[0] for v in ergebnisse.values()) == Counter(
        {"regelkonform": 19, "zweifelsfall_0_3_bis_0_49": 1})
    ergebnis, note = ergebnisse[ZWEIFELSFALL_MIT_ANKER]
    assert ergebnis == "zweifelsfall_0_3_bis_0_49"
    assert "Differenz unter 0,5, Eintrag wegen Ereignisanker (Regel 4)" in note
    assert note.endswith("Reihe + Ereignis.")


def test_richtung_und_zahlen_der_note_aus_dem_regelpruefer():
    for e in _eintraege():
        p = rechner.pruefe(_zeilen(e["company"]), e["period_from"], e["period_to"])
        assert p["richtung"] == e["direction"], e
        # Vorniveau; Zeitraum; Δ; Richtung – die ersten vier Teile des Notizgerüsts (Regel 11)
        geruest = "; ".join(p["note_geruest"].split("; ")[:4]) + ";"
        assert e["note"].startswith(geruest), (e["company"], e["period_from"], geruest)


def test_regel5_satz_je_reihe():
    je_reihe = {}
    for e in _eintraege():
        je_reihe.setdefault(e["company"], []).append((e["period_from"], e["period_to"]))
    assert len(je_reihe) == 8
    for name, paare in je_reihe.items():
        s = rechner.satz(_zeilen(name), paare)
        assert s["ok"], (name, s)
        assert s["anzahl"] <= 3


def test_reihen_ohne_eintrag_ohne_regelkonformen_kandidaten_bis_auf_carl_zeiss():
    csv = _csv_je_name()
    geeignet = [n for n in csv if sum(r["bewertet"] for r in _zeilen(n)) >= 12]  # Regel 9
    assert len(geeignet) == 15
    mit_eintrag = {e["company"] for e in _eintraege()}
    ohne = sorted(set(geeignet) - mit_eintrag)
    assert len(ohne) == 7
    kandidaten = {}
    for name in ohne:
        gut, _zweifel = rechner.scan(_zeilen(name))
        kandidaten[name] = [(p["von"], p["bis"]) for p in gut]
    assert {n: k for n, k in kandidaten.items() if k} == AGENTISCH_VERWORFEN


def _abschnitt(text, nummer):
    return text.split(f"\n## {nummer} ", 1)[1].split("\n## ", 1)[0]


def test_erster_lauf_nach_regelpruefer_11_regelkonform_15_verworfen():
    abschnitt4 = _abschnitt(_text(PROTOKOLL), 4)
    assert "hatte 26 Einträge, nicht committet" in abschnitt4
    zeilen = re.findall(r"^\| (.+?) (\d{4}-\d\d)\.\.(\d{4}-\d\d) (rise|fall) \| (.+?) \|$", abschnitt4, re.M)
    assert len(zeilen) == 26
    art = Counter()
    ergebnis = Counter()
    lauf2 = {(e["company"], e["period_from"], e["period_to"]) for e in _eintraege()}
    for name, von, bis, richtung, vergleich in zeilen:
        p = rechner.pruefe(_zeilen(name), von, bis)
        ergebnis[p["ergebnis"]] += 1
        if vergleich == "identisch übernommen":
            art["identisch"] += 1
            assert (name, von, bis) in lauf2
            assert p["ergebnis"] == "regelkonform" and p["richtung"] == richtung
        elif vergleich.startswith("überlappt mit "):
            art["ueberlappt"] += 1
            a, b = vergleich.removeprefix("überlappt mit ").split("..")
            assert (name, a, b) in lauf2
        else:
            assert vergleich == "kein Eintrag"
            art["kein"] += 1
    assert art == Counter({"identisch": 6, "ueberlappt": 7, "kein": 13})
    assert ergebnis == Counter({"regelkonform": 11, "verworfen": 15})


# ---------------------------------------------------------------------------
# 3. Bereinigung der Titel
# ---------------------------------------------------------------------------

def _readme_zahl_ersetzungen():
    m = re.search(r"Ersetzungen insgesamt: (\d+)", _text(README))
    assert m, "README nennt die Zahl der Ersetzungen nicht"
    return int(m.group(1))


def test_anker_ersetzt_und_zahl_wie_im_readme():
    text = _text(PROTOKOLL)
    koerper = "\n".join(z for z in text.splitlines() if not z.startswith(">"))
    assert koerper.count(ERSATZ) == _readme_zahl_ersetzungen()
    ankerzeilen = re.findall(r"^\*\*Anker:\*\* (.+)$", _abschnitt(text, 5), re.M)
    assert len(ankerzeilen) == 21
    datiert = [z for z in ankerzeilen if re.match(r"\d{4}-\d\d-\d\d, ", z)]
    assert len(datiert) == 11
    assert all(z.rstrip().endswith(ERSATZ) for z in datiert)
    assert all(z.rstrip() == "keiner." for z in ankerzeilen if z not in datiert)
    zellen = re.findall(r"^\| [^|\n]+ \| \d{4}-\d\d bis \d{4}-\d\d \| [^|\n]+ \| [^|\n]+ \| (.+?) \|$",
                        _abschnitt(text, 1), re.M)
    assert len(zellen) == 20
    assert all(z == "keiner" or re.fullmatch(r"\d{4}-\d\d-\d\d: " + re.escape(ERSATZ), z) for z in zellen)


def test_bereinigte_fassung_nur_ersetzungen_gegen_original():
    # Außer den Ersetzungen nur drei Satzzeichen-Anpassungen (README, „Sonst unverändert“).
    _, herkunft = _readme_hashes("entscheidungsprotokoll_2026-10-09.md")
    pfad = os.path.normpath(os.path.join(REPO_DIR, herkunft))
    if not os.path.exists(pfad):
        pytest.skip(f"Original außerhalb des Repositorys nicht vorhanden: {herkunft}")
    text = _text(PROTOKOLL)
    koerper = text[text.index("\n# ") + 1:].split("\n")
    original = _text(pfad).split("\n")
    assert len(koerper) == len(original)
    geaendert, angepasst, abschnitt = Counter(), 0, None
    for neu, alt in zip(koerper, original):
        m = re.match(r"^## (\d+) ", alt)
        if m:
            abschnitt = int(m.group(1))
        if neu == alt:
            continue
        assert ERSATZ in neu and ERSATZ not in alt
        geaendert[abschnitt] += 1
        # Die Teile zwischen den Marken stehen in derselben Reihenfolge im Original.
        pos = 0
        for teil in neu.split(ERSATZ):
            j = alt.find(teil, pos)
            if j < 0:
                angepasst += 1
                break
            pos = j + len(teil)
    assert geaendert == Counter({1: 11, 5: 63})
    assert angepasst == 3


def test_bereinigung_gegen_lokalen_belegspeicher():
    titel, dateien = pruefskript.lade_titel([BELEGSPEICHER])
    if not titel:
        pytest.skip("Belegspeicher backend/data/context/ nicht vorhanden (nicht versioniert, E7)")
    erg = pruefskript.pruefe(_text(PROTOKOLL), titel)
    assert erg["volltitel_zeilen"] == []
    assert erg["folgen_zeilen"] == []
    assert erg["zitate_lang_zeilen"] == []
    assert erg["ok"]


def test_pruefskript_mit_konstruierten_titeln():
    # Erfundene Titel, keine echten Meldungen.
    titel = {"Beispielwerk meldet erfundene Neuigkeit zum Testen der Pruefung heute",
             "Kurzer Testtitel ohne Bedeutung für Prüfzwecke"}
    sauber = "# X\n\n## 5 Stufe B\n\nDie Meldung beschreibt ein erfundenes Ereignis.\n"
    assert pruefskript.pruefe(sauber, titel)["ok"]
    voll = "## 5 Stufe B\n\nText: Kurzer TESTTITEL ohne Bedeutung für Prüfzwecke.\n"
    erg = pruefskript.pruefe(voll, titel)
    assert erg["volltitel_zeilen"] == [3] and not erg["ok"]
    folge = "## 1 A\n\nBeispielwerk meldet erfundene Neuigkeit zum Testen der Pruefung, sagt jemand.\n"
    erg = pruefskript.pruefe(folge, titel)
    assert erg["folgen_zeilen"] == [3] and erg["volltitel_zeilen"] == []
    zitat = '## 5 B\n\nidx 1 ("erfundene Neuigkeit zum Testen") und "Testtitel".\n## 6 C\n\n"erfundene Neuigkeit zum Testen"\n'
    erg = pruefskript.pruefe(zitat, titel)
    assert erg["zitate_lang_zeilen"] == [3]
    assert erg["zitate_kurz_in_titel"] == 1
    assert erg["zitate_abschnitt5"] == 2
    link = "## 5 B\n\nhttps://example.org/beispielwerk-meldet-erfundene-neuigkeit-zum-testen-der-pruefung-heute\n"
    assert pruefskript.pruefe(link, titel)["ok"]
    # Die Ausgabe enthält nur Zählungen und Zeilennummern.
    assert not any(isinstance(v, str) for v in pruefskript.pruefe(voll, titel).values())
