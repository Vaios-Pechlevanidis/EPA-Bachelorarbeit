# DZ1-Referenz: Herkunft, Regelprüfer und Entscheidungsprotokoll

Dieser Ordner legt offen, wie die 20 Referenzzeiträume in `backend/data/annotations.json`
entstanden sind (DZ1, E5). Regelprüfer, Agentendefinition und Entscheidungsprotokoll lagen bis
2026-10-13 nur außerhalb des Repositorys (im übergeordneten Ordner bzw. in `.claude/agents/`).

**Einordnung vorab.** Die Referenz ist **regelbasiert und agentengestützt** und **kein
Goldstandard**: Ein Agenten-Workflow hat die Zeiträume nach dem Annotationsprotokoll
(`docs/referenzzeitraeume-literatur.md`, Abschnitt 3, Regeln 1–11) und zusätzlichen Setzungen
allein aus den Serien-CSVs vorgeschlagen; der Autor hat sie am 2026-10-09 ohne Änderung
freigegeben. Es gibt einen einzigen Annotator und kein Übereinstimmungsmaß, und die Freigabe war
nicht blind gegenüber der Erkennung (E5, „Grenzen für DZ1“). Ein **erster Annotationslauf des
Agenten mit 26 Einträgen wurde verworfen**, und die **Setzungen 1–6 sind keine Protokollregeln**
(siehe unten).

**Begriffe.** „Annotationslauf 1“ und „Annotationslauf 2“ meinen hier die beiden Läufe des
Agenten, der die Referenz erzeugt hat; Annotationslauf 2 ist der vom 2026-10-09, aus dem die 20
Einträge stammen. Davon zu unterscheiden ist der einmalige DZ1-Abgleich vom 2026-10-10, den E5
und E9 „ersten Lauf“ nennen. Das archivierte Protokoll selbst sagt „erster Lauf“ und „Lauf 2“
für die Annotationsläufe; es ist unverändert bis auf die Bereinigung.

## Dateien

| Datei | Inhalt | Stand |
|---|---|---|
| `dz1_rechner.py` | Regelprüfer des Annotationslaufs 2: reine Rechenarbeit auf einer Serien-CSV, nur Standardbibliothek; prüft Regeln 2–5 und die Setzungen 1–3 (`tabelle`, `pruefe`, `scan`, `satz`) | unveränderte Kopie |
| `agent-dz1-referenzzeitraeume.md` | Agentendefinition mit Unabhängigkeitsregeln, Ablauf Stufe A/B, Setzungen, Eintragsformat; enthält auch die Modi `zweitperson` und `auswerten`, belegt hier ist nur der Modus `annotieren` | unveränderte Kopie, vor dem Ablegen auf Geheimnisse geprüft: keine Zugangsdaten, Schlüssel oder Tokens (nur Pfade, Befehle, Commit-Vorlagen) |
| `entscheidungsprotokoll_2026-10-09.md` | Entscheidungsprotokoll des Annotationslaufs 2: 1 Ergebnis, 2 Ablauf, 3 Setzungen, 4 Vergleich mit Annotationslauf 1, 5 Stufe B je Fall, 6 Stufe A je Reihe | bereinigte Fassung (Titel von Meldungen ersetzt, E7) |
| `pruefe_bereinigung.py` | Prüfskript für die Bereinigung (siehe unten) | neu, 2026-10-13 |

Nachprüfung im Test: `backend/tests/test_dz1_referenz_archiv.py`.

## Entstehung (E5)

- **2026-10-09, Modus `annotieren`:** Stufe A allein aus `backend/data/series/<id>_<slug>_employee.csv`,
  je Reihe ein Annotator-Agent und ein adversarialer Prüfer (30 Agenten); alle Zahlen aus
  `dz1_rechner.py`, Endcheck jedes Eintrags. Stufe B (Ereignisanker, Regel 7) erst nach allen 15
  Reihen: 176 gedrosselte Abrufe bei Google News RSS und EQS News, keiner fehlgeschlagen; je Fall
  ein Agent zur Ankerwahl und ein Prüfer (42 Agenten); die Monate der Einträge blieben unverändert.
  Gesperrt waren Dashboard, API, `backend/data/calibration/`, Belegspeicher, Erkennungs- und
  Auswertungscode (Protokoll, Abschnitt 2).
- **Commit `f50b727`:** 20 Zeiträume in 8 von 15 Reihen, 11 mit Ereignisanker; davon ein
  Zweifelsfall (|Δ| 0,30–0,49), der nur wegen seines Ankers steht.
- **Version 2 (Commit `9703403`):** nur `note`; nahezu wörtliche Schlagzeilen durch eigene
  Kurzbeschreibungen ersetzt.
- **Version 3 (2026-10-13):** nur `hinweise.zweck` und `hinweise.wichtig`; die Selbstbeschreibung
  der Datei entspricht jetzt der Entstehung. Einträge unverändert
  (`backend/tests/test_annotations_file.py`).

## Was ausdrücklich gilt

- **Kein Goldstandard:** regelbasiert, agentengestützt, ein Annotator, Freigabe nicht blind.
- **Annotationslauf 1 verworfen:** Ein erster, abgebrochener Annotationslauf (Setzung zum
  Folgeniveau: 0,25 Sterne im Mittel der Folgemonate) hatte 26 Einträge und wurde nicht committet.
  Der Agent hat die Setzung geschärft (heutige Setzung 1) und neu annotiert. Das Protokoll
  (Abschnitt 4) nennt „12 bestehen, 14 scheitern“. Nachgerechnet mit dem archivierten Regelprüfer
  sind von den 26 Zeiträumen **11 regelkonform und 15 verworfen**; laut Tabelle in Abschnitt 4 sind
  6 unverändert übernommen, 7 überlappen mit einem Eintrag des Annotationslaufs 2, 13 haben kein
  Gegenstück. Die Zahl 12/14 im Fließtext ist damit nicht nachvollziehbar. Annotationslauf 1 wurde
  auf die Sperren geprüft (66 Werkzeugaufrufe, kein Verstoß).
- **Setzungen 1–6 sind keine Protokollregeln.** Sie füllen Lücken des Protokolls und sind vom
  Autor zu prüfen:
  1. *Bleiben auf dem neuen Niveau:* (a) Folgemittel der bis zu drei bewerteten Folgemonate
     mindestens |Δ|/2 in Sprungrichtung vom Vorniveau, (b) erster Folgemonat mindestens 0,25
     Sterne in Sprungrichtung, (c) ohne bewerteten Folgemonat kein Eintrag.
  2. *Vorniveau* aus mindestens drei bewerteten Monaten.
  3. *Stützung dünner Monate:* Jeder Monat mit 5–9 Bewertungen braucht einen weiteren Monat
     (im Zeitraum oder erster Folgemonat) mit mindestens 0,5 Sternen Abweichung in Sprungrichtung.
  4. *Auswahl nach Regel 5* (mehr als drei Kandidaten) nach größtem |Δ|; die `note` nennt dann die
     Schwankung.
  5. *Abgrenzung nach der Definition:* `period_from` erster deutlich abweichender, `period_to`
     erster Monat auf dem neuen Niveau (nicht nach größtem Δ).
  6. *Anker* nur mit Arbeitgeberbezug und für das Unternehmen selbst; keine Produkt-, Zahlen-,
     Kurs-, Formalmeldungen oder Rankings; Ereignisse mit klar entgegengesetzter erwarteter Wirkung
     zählen nicht, richtungsneutrale große Ereignisse (Vorstandswechsel, Übernahmen) zählen;
     beurteilt nur nach Titel, Datum, Herausgeber und Kategorie.

  Die Agentendefinition nennt dazu Arbeitsregeln ohne Nummer (nahe Sprünge zusammenfassen,
  Zahlenformat der `note`, Rechenwerkzeug).

## Prüfsummen (SHA-256)

Herkunft relativ zum Repository-Wurzelverzeichnis. Die Werte der Originale wurden am 2026-10-13
gebildet.

| Datei im Ordner | Herkunft | SHA-256 Original | SHA-256 Datei im Ordner |
|---|---|---|---|
| `dz1_rechner.py` | `../dz1-protokoll/dz1_rechner.py` | `97158e185fd94ac587b82551e2baa58cbe4c3ed7f9463e61ef2987379ac077cd` | `97158e185fd94ac587b82551e2baa58cbe4c3ed7f9463e61ef2987379ac077cd` |
| `agent-dz1-referenzzeitraeume.md` | `../.claude/agents/dz1-referenzzeitraeume.md` | `9da20c5c53bde6e7f51df52f2eb538fdfe550b81363b5037bad7c4a0bec138f6` | `9da20c5c53bde6e7f51df52f2eb538fdfe550b81363b5037bad7c4a0bec138f6` |
| `entscheidungsprotokoll_2026-10-09.md` | `../dz1-protokoll/dz1_entscheidungsprotokoll_annotieren_2026-10-09.md` | `3760407ce9faf2c26ed714398f995f9aaeb4d547efd9d46a15d56317f6713430` | `91d20be1fff2b01254033b3edc2ffab49cb5b253b33a21aa33cfa29a3d755ced` |

Der Regelprüfer ist außerdem byte-gleich mit `scratchpad/lauf2/dz1_rechner.py` der Sitzung vom
2026-10-09, den das Protokoll als verwendetes Werkzeug nennt (am 2026-10-13 lokal verglichen; der
Scratchpad ist temporär und nicht Teil des Repositorys).

## Bereinigung des Entscheidungsprotokolls

Ersetzungen insgesamt: 91

| Stelle | Ersetzungen | geänderte Zeilen |
|---|---|---|
| Abschnitt 1, Spalte „Anker“ der Ergebnistabelle | 11 | 11 |
| Abschnitt 5, Zeilen „**Anker:**“ | 11 | 63 (zusammen) |
| Abschnitt 5, Fließtext von Wahl und Prüfer | 69 | |
| Abschnitte 2–4 und 6 | 0 | 0 |

**Regel.** Durch „[Titel entfernt]“ ersetzt wurde jede Stelle, die (Bereinigungsregeln B1–B3;
nicht zu verwechseln mit den Regeln 1–11 des Annotationsprotokolls)

- **B1** einen Titel vollständig wiedergibt, wörtlich oder mit geringen Abweichungen
  (Schreibung, Satzzeichen, Artikel, Beugung, Wortstellung, Aktiv/Passiv, Nominalisierung) oder
  als wörtliche Übersetzung;
- **B2** ein Stück eines Titels wörtlich wiedergibt, das eine Aussage bildet oder mindestens vier
  Wörter umfasst; oder
- **B3** eine Titelaussage als eigenen Satz mit den Inhaltswörtern des Titels nachformuliert.

B1–B3 gelten ohne Ausnahme, auch für Sätze, die ein Ereignis mit Ereignisart und Namen
beschreiben. Nicht als Wiedergabe gelten:

- Datum, Herausgeber, Quellenart, Link und `idx`-Nummern;
- Namen von Unternehmen, Personen, Organen, Produkten und Funktionen sowie Zahlenangaben, auch
  wenn sie in einem Titel stehen und mehr als drei Wörter umfassen; ein Name in Anführungszeichen
  (bis drei Wörter, ohne Verb) bleibt, solange der Satz zusammen mit ihm den Titel nicht nach B1
  wiedergibt;
- zufällige Übereinstimmungen allgemeiner Wendungen mit einem Titel (z. B. Zeitangaben) und
  Wortfolgen aus Titeln zu anderen Ereignissen.

Eigene Beschreibungen eines Ereignisses bleiben nur, wenn sie keine von B1–B3 erfüllen.

**Sonst unverändert.** Außer den Ersetzungen sind in drei Sätzen Satzzeichen angepasst (einmal
ein Komma durch einen Doppelpunkt ersetzt, einmal ein Doppelpunkt eingefügt, einmal Klammern um
die Marke gesetzt), damit die Ersetzung grammatisch steht. Alle übrigen Zeichen sind wie im
Original; Original und bereinigte Fassung haben ohne Vorspann gleich viele Zeilen. Vorangestellt
ist ein Vorspann mit dem SHA-256 des Originals. Lokale absolute Pfade (5 Stellen) bleiben; sie
enthalten keine Geheimnisse.

**Links.** Die 11 Links der Ankerzeilen bleiben, wie in `annotations.json`. Die 5 EQS-Links
enthalten den Titel als Pfadbestandteil; die 6 Google-News-Links sind kodiert.

**Maschinelle Prüfung** mit `pruefe_bereinigung.py` (Normalisierung: Kleinschreibung, Akzente
und Umlaute auf den Grundbuchstaben, Nicht-Wortzeichen als Leerzeichen; Links ausgenommen):

- Titelquellen: der lokale Belegspeicher `backend/data/context/*/*/*.json` (1 839 Dateien, 17 545
  verschiedene Titel; nicht versioniert, E7) und, weil der Speicher für Google News nur 66 der 92
  Monate der 21 Stufe-B-Fenster enthält, zusätzlich die Abrufe des Annotationslaufs 2 selbst (176
  Abrufe, 891 Meldungen; lokal im Scratchpad der Sitzung vom 2026-10-09, nicht versioniert).
  Zusammen 17 711 Titel.
- Ergebnis für die bereinigte Fassung: **0** Zeilen mit einem vollständigen Titel ab 25 Zeichen,
  **0** Zeilen mit 8 aufeinanderfolgenden Wörtern eines Titels, **0** Zitate in Abschnitt 5 mit
  mindestens 4 Wörtern aus einem Titel. Von den 49 Zitaten in Abschnitt 5 kommen 30 kürzere in
  einem Titel vor (Unternehmens- und Suchbegriffe, Funktions- und Begriffsnamen).
- Gegenprobe am Original: 27 Zeilen mit vollständigem Titel, 14 Zeilen mit 8 Wörtern in Folge,
  23 lange Zitate.
- Prüfung in der Schärfe von B2 (`--n 4`): 22 Zeilen mit 4 Wörtern in Folge aus einem
  Titel. Alle einzeln gesichtet und belassen: Unternehmens- und Organnamen (auch mit Artikel oder
  Präposition), ein Berichtsname, eine Zahlenangabe, eine Ereignisart mit Unternehmensnamen (drei
  Wörter; das Und-Zeichen im Namen zählt die Normalisierung als Worttrenner), allgemeine
  Wendungen (Zeitangaben, Vergleiche) und Wortfolgen aus Titeln zu anderen Ereignissen.
- Strengere Zusatzprüfung (`--n 5 --min-zeichen 15 --zitat-woerter 3`): 7 Zeilen mit einem
  vollständigen kurzen Titel (jeweils nur ein Unternehmensname, der auch allein als Titel
  vorkommt), 6 Zeilen mit 5 Wörtern in Folge (eine Zahlenangabe zweimal, ein Unternehmensname,
  eine Organbezeichnung zweimal, eine Wortfolge aus einem Titel zu einem anderen Ereignis) und 5
  Zitate (ein Unternehmensname zweimal, ein Funktionsname zweimal, ein Begriffsname). Keine
  Schlagzeile.
- **Nachbesserung 2026-10-13:** Bei der Nachprüfung mit 5 Wörtern fiel ein Satz in Abschnitt 5 auf,
  der einen Titel in umgestellter Reihenfolge fast vollständig wiedergab: ein wörtliches Titelstück
  aus 5 Wörtern und ein Funktionsname in Anführungszeichen; im Absatz fehlte nur ein Wort des
  Titels. Dasselbe Titelstück stand im selben Fall ein zweites Mal. Die Prüfung mit 8 Wörtern hatte
  beides nicht erfasst. Beide Stellen sind seitdem ersetzt (89 → 91 Ersetzungen); die Regel oben
  lässt für Ereignisbeschreibungen mit Namen keine Ausnahme mehr zu.

Das Skript gibt nur Zählungen und Zeilennummern aus, nie einen Titel:

```bash
python3 docs/dz1-referenz/pruefe_bereinigung.py docs/dz1-referenz/entscheidungsprotokoll_2026-10-09.md \
  --titel 'backend/data/context/*/*/*.json'
```

## Regelprüfer anwenden

Der Regelprüfer hat keine fest eingetragenen Pfade; er bekommt die Serien-CSV als Argument
(Trennzeichen `;`, Spalten `period`, `mean_durchschnittsbewertung`, `count`). Aufruf aus dem
Repository-Wurzelverzeichnis:

```bash
# Monatstabelle mit Status (bewertet ab 5 Bewertungen) und Mittel der bis zu sechs Vormonate
python3 docs/dz1-referenz/dz1_rechner.py tabelle backend/data/series/19_sap_se_employee.csv
# alle Regeln und Setzungen für einen Zeitraum (JSON mit Ergebnis und Notizgerüst)
python3 docs/dz1-referenz/dz1_rechner.py pruefe backend/data/series/19_sap_se_employee.csv 2024-07 2024-08
# alle regelkonformen Zeiträume und Zweifelsfälle (0,30–0,49) einer Reihe, gruppiert
python3 docs/dz1-referenz/dz1_rechner.py scan backend/data/series/25_cancom_employee.csv
# Regel 5 für eine Auswahl (höchstens drei, mindestens drei bewertete Monate Abstand)
python3 docs/dz1-referenz/dz1_rechner.py satz backend/data/series/25_cancom_employee.csv 2016-08:2016-08 2021-07:2021-07 2023-12:2023-12
```

`pruefe` liefert `regelkonform`, `zweifelsfall_0_3_bis_0_49` oder `verworfen` (mit
`gescheitert_an`). Der Regelprüfer importiert nichts aus `services` oder `models` und kennt keine
Erkennungsergebnisse.

## Nachprüfung (`backend/tests/test_dz1_referenz_archiv.py`)

Mechanisch geprüft, offline aus den versionierten Serien-CSVs:

- Prüfsummen der Kopien wie oben; die Originale, wenn sie lokal vorhanden sind.
- `pruefe` für alle 20 Einträge: 19 regelkonform, einer Zweifelsfall (Compugroup Medical
  Deutschland, 2021-04 bis 2021-05, Δ +0,47), dessen `note` den Ereignisanker als Grund nennt.
- Richtung und die Zahlen am Anfang jeder `note` (Vorniveau, Zeitraum, Δ, Richtung) entsprechen
  dem Notizgerüst des Regelprüfers.
- `satz` (Regel 5) ist in allen 8 Reihen mit Einträgen erfüllt.
- 15 Reihen haben mindestens 12 bewertete Monate (Regel 9). Von den 7 Reihen ohne Eintrag haben 6
  keinen regelkonformen Kandidaten; Carl Zeiss hat genau einen (2023-04), den der Agent in Stufe A
  nach der Definition verworfen hat.
- Annotationslauf 1: 11 regelkonform, 15 verworfen; 6 unverändert übernommen, 7 überlappend, 13 ohne
  Gegenstück.
- Bereinigung: Ankerzeilen und Ankerzellen ersetzt, Zahl der Ersetzungen wie oben; mit lokalem
  Belegspeicher zusätzlich die maschinelle Prüfung (ohne Speicher übersprungen); mit lokalem
  Original zusätzlich, dass sich die Fassung nur in den Ersetzungen und den drei
  Satzzeichen-Anpassungen unterscheidet (11 Zeilen in Abschnitt 1, 63 in Abschnitt 5; ohne
  Original übersprungen).

Nicht mechanisch prüfbar, weil agentische Entscheidungen (im Protokoll je Reihe und Fall
begründet):

- die Abgrenzung nach der Definition (Setzung 5), also welche Variante einer Kandidatengruppe
  eingetragen wird;
- die Auswahl der drei deutlichsten bei mehr als drei Kandidaten (Setzung 4);
- das Trendurteil nach Regel 2 (der Regelprüfer gibt nur einen Hinweis zum Vortrend);
- die Ankerwahl in Stufe B (Setzung 6) und damit die Aufnahme des Zweifelsfalls; die Quellen
  wurden live abgerufen, die Titel sind nicht versioniert.

## Grenzen

- Die maschinelle Prüfung erkennt nur Titel aus den beiden lokalen Quellen und nur in derselben
  Sprache. Übersetzungen und Nachformulierungen sind nach der Regel oben von Hand beurteilt.
- Ohne das Original außerhalb des Repositorys lässt sich die Bereinigung nicht Stelle für Stelle
  nachvollziehen; der SHA-256 des Originals steht oben und im Vorspann.
