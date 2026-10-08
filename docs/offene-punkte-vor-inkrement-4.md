# Offene Punkte vor Inkrement 4 – Belege und Entscheidungsvorlagen

Stand: 2026-10-08, Branch `feature/offene-punkte-vor-inkrement-4` (von `main`, Commit 8a24d3b).
Alle Zahlen wurden **nur lesend** erhoben: Datenbank nur per SELECT (über
`backend/database/supabase_client.py`, seitenweise mit `_fetch_all_rows`), die Rohexporte und
der Scraper des Autors wurden nur gelesen. Es stehen keine Texte einzelner Bewertungen und keine
personenbezogenen Angaben in diesem Dokument. Die Entscheidungen D1 bis D3 trifft der Autor;
danach werden E13, E15 und E16 in `docs/entscheidungen.md` fortgeschrieben (Phase B).

## D1 – Statuszuordnung (E13)

> **Entscheidung des Autors (2026-10-08): Vorschlag angenommen.** Umgesetzt in Phase B (B1):
> Bezeichnung „Zurückgestellt oder Absage“, Vermerke in E13 und Feature-Doku 02, Tests;
> Schlüssel und Zahl der geeigneten Reihen unverändert.

### 1. Bestand je Quelle und Rohwert

Spalte `status` der Tabellen `employee` und `candidates`, alle Zeilen (26 reale Unternehmen und
Demo 1–3), Stand 2026-10-08. Zeitraum = Kalendermonat der Spalte `datum` (erste bis letzte
Bewertung mit diesem Wert). Die Zahlen stimmen mit der Prüfung vom 2026-10-04 in E13 überein.

**Mitarbeitende (`employee`, 21 962 Zeilen)**

| Rohwert | Anzahl | Unternehmen (Zeilen) | Zeitraum | Zuordnung heute |
|---|---:|---|---|---|
| `1.0` | 13 815 | 25 reale Unternehmen, alle außer Formycon; am meisten Telekom (4 708), Bechtle (1 309), Carl Zeiss (1 283), Cancom (720), Freenet (654) | 2008-06 – 2026-07 | `angestellt` |
| `0.0` | 4 030 | 12 Unternehmen, **nur TecDAX-Importe**: Telekom (1 272), Bechtle (798), Cancom (534), 1&1 AG (410), Compugroup (366), Carl Zeiss (287), Freenet (262), Evotec (34), Atoss (25), Aixtron (23), Eckert Ziegler (11), Elmos (8) | 2012-08 – 2025-08 | `ex-angestellt` |
| leer (NULL) | 2 494 | 25 reale Unternehmen; am meisten Telekom (919), 1&1 AG (337), Bechtle (262), Cancom (220), Carl Zeiss (130), Thyssengas (118) | 2007-06 – 2026-06 | `unbekannt` |
| `Angestellt` | 889 | nur Demo 1–3 | 2022-01 – 2026-05 | `angestellt` |
| `Ex-Angestellt` | 719 | nur Demo 1–3 | 2022-01 – 2026-05 | `ex-angestellt` |
| `True` | 11 | nur Formycon | 2017-08 – 2025-01 | `angestellt` (Annahme) |
| `False` | 4 | nur Formycon | 2016-11 – 2024-01 | `ex-angestellt` (Annahme) |

**Bewerbende (`candidates`, 4 676 Zeilen)**

| Rohwert | Anzahl | Unternehmen (Zeilen) | Zeitraum | Zuordnung heute |
|---|---:|---|---|---|
| `hired` | 1 235 | 24 Unternehmen; am meisten Carl Zeiss (301), Thyssenkrupp (167), E.ON (123), Atoss (101), Bechtle (85) | 2009-11 – 2026-04 | `eingestellt` |
| leer (NULL) | 799 | 22 Unternehmen; am meisten Thyssengas (353), Aixtron (108), Carl Zeiss (62), Thyssenkrupp (45) | 2008-09 – 2026-04 | `unbekannt` |
| `Bewerber` | 792 | nur Demo 1–3 | 2022-01 – 2026-05 | `unbekannt` |
| `offerDeclined` | 711 | 24 Unternehmen; am meisten Carl Zeiss (115), 1&1 AG (74), Thyssenkrupp (72), Bechtle (67), E.ON (63) | 2011-05 – 2026-05 | `angebot-abgelehnt` |
| `rejected` | 625 | 12 Unternehmen, **nur TecDAX-Importe**: Carl Zeiss (211), Bechtle (101), Telekom (81), 1&1 AG (66), Compugroup (46), Atoss (40), Freenet (33), Cancom (29), Evotec (10), Elmos (4), Aixtron (3), Eckert Ziegler (1) | 2009-10 – 2025-07 | `abgelehnt` |
| `deferred` | 514 | 21 Unternehmen; am meisten Thyssenkrupp (140), SAP SE (99), E.ON (97), RWE (68), Open Grid Europe (15), Carl Zeiss (15) | 2010-11 – 2026-03 | `zurueckgestellt` |

### 2. Wie die Werte entstehen (Importcode, Exportspalten, Scraper)

**Importweg.** Kununu-Profil → Scraper des Autors (eigenes Repository `kununu_scraper`,
nicht Teil dieses Repositorys) → Excel-Export mit der Spalte `Status` → Upload über
`backend/services/excel_service.py`. Der Import übernimmt den Zellwert unverändert als Text:
`clean_text(str(row.get("status")))`, sonst `None` (`_import_candidates`, `_import_employees`).
Es gibt im Repository keine Übersetzung der Statuswerte vor der Speicherung; `normalize_status`
in `backend/services/review_service.py` ordnet erst beim Lesen zu.

**Exportspalten (28 xlsx-Dateien des TecDAX-Imports, nur gelesen).** In 13 von 14
Mitarbeiter-Dateien ist `Status` eine **Zahlenspalte** (pandas `float64`) mit den Werten 1,
0 und leer; `str(1.0)` ergibt `"1.0"`. Allein `formyconEmployee.xlsx` (15 Zeilen) hat eine
Spalte vom Typ **Wahrheitswert** (pandas `bool`, TRUE/FALSE, keine leere Zelle); `str(True)`
ergibt `"True"`. In allen Bewerber-Dateien ist `Status` Text mit den Werten `hired`,
`offerDeclined`, `rejected`, `deferred` und leer. Die Kopfzeilen sind sonst identisch.

**Scraper (Stand des Repositorys `kununu_scraper`, Historie ab 2026-03-08).**

- Mitarbeitende: Das Feld `former` der Kununu-Antwort wird in eine Zahl übersetzt: `former`
  wahr (oder Auszubildende mit Status `former`, oder Typbezeichnung mit „Ex“) → `0.0`;
  `former` falsch oder eine Typangabe vorhanden → `1.0`; sonst bleibt die Zelle leer. Auf dem
  HTML-Weg ohne JSON gilt: Typbezeichnung mit „Ex-“ → `0.0`, sonst `1.0`. **`1.0` steht also
  für „aktuell“, `0.0` für „ehemalig“**; das ist die Zuordnung aus E13. Die Zahlencodes stehen
  seit dem ersten Commit des Scrapers (2026-03-08) im Code; eine Version, die Wahrheitswerte
  schreibt, ist in der Historie nicht enthalten. Die Formycon-Datei stammt laut Dateidatum vom
  2025-08-16, also von einem älteren Stand, der nicht rekonstruierbar ist.
- Bewerbende: `status` (bzw. `result`) der Kununu-Antwort wird über eine Tabelle übersetzt:
  `hired` → `hired`, `deferred` → `deferred`, **`rejected` → `deferred`** (seit dem Commit vom
  2026-04-10), HTML-Beschriftungen `Zusage`/`Eingestellt` → `hired`, **`Absage` → `deferred`**,
  `Hat sich beworben` und `Bewerber/in hat sich selbst anders entschieden` → leer. Werte ohne
  Eintrag in der Tabelle (`offerDeclined`) werden unverändert durchgereicht.
- `Angestellt`, `Ex-Angestellt` (Mitarbeitende) und `Bewerber` (Bewerbende) kommen nur aus
  den Seed-Skripten der Demo-Unternehmen (`backend/scripts/seed_demo1.py`, `seed_demo2.py`,
  `seed_demo3.py`, `seed_bulk_reviews.py`); sie gehen in keine Auswertung ein (E2).

**Befund: zwei Importrunden mit unterschiedlichem Scraper-Stand.** Die 13 Unternehmen aus
Zyklus 1 (id 3–20) und die 13 TecDAX-Unternehmen (id 21–33, Exportdateien vom Juli/August
2025, importiert am 2026-10-02) unterscheiden sich systematisch:

| Quelle | Zyklus 1 (id 3–20) | TecDAX (id 21–33) |
|---|---|---|
| Mitarbeitende | `1.0` 3 758, leer 360, **kein einziger Wert `0.0`** | `1.0` 10 057, `0.0` 4 030, leer 2 134, `True` 11, `False` 4 |
| Bewerbende | leer 501, `hired` 475, **`deferred` 453**, `offerDeclined` 255, **kein `rejected`** | `hired` 760, `rejected` 625, `offerDeclined` 456, leer 298, `deferred` 61 |

Folgerungen (Lesart, vom Autor zu bestätigen):

1. Für die Unternehmen aus Zyklus 1 liegt **keine Unterscheidung aktuell/ehemalig** vor:
   kein Unternehmen hat einen Wert `0.0` (Thyssenkrupp, Open Grid Europe, PLEdoc, E.ON Digital
   Technology, E.ON, RWE, Thyssengas, Universität Duisburg-Essen, KIT, TU München, Universität
   zu Köln, SAP SE, NTT DATA SE). Dort bedeutet `angestellt` „Bewertung mit Typangabe“, nicht
   „aktuell angestellt“. Von den 15 nach E4 geeigneten Mitarbeiter-Reihen betrifft das 8
   (Thyssenkrupp, Open Grid Europe, E.ON, RWE, KIT, TU München, SAP SE, NTT DATA SE); die
   Gruppe `angestellt` ist dort bis auf die leeren Zeilen gleich „alle“. Die 6 geeigneten
   Reihen `ex-angestellt` aus E13 sind ausschließlich TecDAX-Unternehmen.
2. Bei den Bewerbenden aus Zyklus 1 fehlt `rejected` vollständig, während `deferred` dort
   453 von 514 Zeilen stellt. Das passt zur Übersetzungstabelle des Scrapers, die `Absage`
   und `rejected` auf `deferred` abbildet: **`deferred` enthält bei den Zyklus-1-Unternehmen
   mit hoher Wahrscheinlichkeit die Absagen.** Ein Textsignal stützt das: Von den
   Bewerbungstexten mit Status `deferred` nennen bei Zyklus 1 20,3 % eine Absage (Wörter
   Absage, abgelehnt, abgesagt, Ablehnung), bei TecDAX-`deferred` 11,5 %, bei
   TecDAX-`rejected` 42,7 %, bei `hired` 0,2 bzw. 1,3 %. Bei den TecDAX-Exporten wurde der
   Rohwert `deferred` dagegen unverändert übernommen; was Kununu damit bezeichnet
   („zurückgestellt“, „Entscheidung offen“), ließ sich nicht prüfen (die Kununu-Seiten sind
   für automatisierte Abrufe gesperrt, Stand 2026-10-08).
3. Die leeren Statuswerte der Mitarbeitenden sind überwiegend ein **Alterseffekt**: Von den
   Bewertungen bis 2013 haben 93–100 % keinen Status, 2014 46 %, 2015 24 %, ab 2016 unter
   6 %. Das Feld fehlt bei alten Bewertungen; „ohne Angabe“ ist die passende Bezeichnung.
4. `True`/`False` (Formycon) sind derselbe Kununu-Wert wie `1.0`/`0.0`, nur anders typisiert.
   Belege für `True` = aktuell: Die mittlere Gesamtnote beträgt bei `True` 4,55 und bei
   `False` 2,15 (TecDAX: `1.0` 4,31, `0.0` 2,36); der Anteil `True` liegt bei 73 % (TecDAX
   `1.0` an `1.0`+`0.0`: 71 %). Formycon hat keinen Monat mit 5 Bewertungen und ist für die
   Erkennung nicht geeignet; die Zuordnung ändert keine geeignete Reihe.

### 3. Vorschläge je unklarem Wert (Entscheidung D1)

| Rohwert | Vorschlag | Begründung | Alternative | Folge für die geeigneten Reihen |
|---|---|---|---|---|
| `True` / `False` (Formycon) | Zuordnung `True` → `angestellt`, `False` → `ex-angestellt` **bestätigen** und in E13 als belegt (nicht mehr als Annahme) führen | gleiches Kununu-Feld wie `1.0`/`0.0`, nur als Wahrheitswert exportiert; Notenprofil und Anteil passen | beide → `unbekannt` | keine (Formycon nicht geeignet) |
| `deferred` | eigener Schlüssel `zurueckgestellt` **bleibt**, aber Bezeichnung und E13 präzisieren: „Zurückgestellt oder Absage (deferred)“ mit Vermerk, dass der Wert bei den Zyklus-1-Unternehmen die Absagen enthält | Rohwerte bleiben unterscheidbar; nichts wird vermischt, was sich später nicht mehr trennen ließe; keine geeignete Reihe betroffen | `deferred` → `abgelehnt` zusammen mit `rejected` (für Zyklus 1 wahrscheinlich richtig, zieht aber die 61 TecDAX-Zeilen mit dem Rohwert `deferred` mit) – oder Neuexport der Bewerberdaten von Zyklus 1 mit korrigierter Scraper-Tabelle (Schreibzugriff auf die Datenbank, nicht in diesem Branch) | keine (keine geeignete Reihe `zurueckgestellt`, E13) |
| leer (Bewerbende) | `unbekannt` („ohne Angabe“) **bestätigen** | kein Ausgang im Export; auf dem HTML-Weg des Scrapers fallen auch „Hat sich beworben“ und „selbst anders entschieden“ auf leer, sind also nicht rekonstruierbar | – | keine (Thyssengas `unbekannt` bleibt die einzige geeignete Reihe dieser Gruppe) |
| leer (Mitarbeitende) | `unbekannt` („ohne Angabe“) **bestätigen**; in Feature-Doku 02 den Alterseffekt nennen | Feld fehlt bei Bewertungen vor 2014 | – | keine |
| `Bewerber` (nur Demo) | `unbekannt` **bestätigen** | nennt keinen Ausgang; nur Demo 1–3 | eigene Bezeichnung „Demo“ | keine |
| `angestellt` bei Zyklus-1-Unternehmen | in E13 und Feature-Doku 02 **vermerken**, dass für id 3–20 keine Unterscheidung aktuell/ehemalig vorliegt; `angestellt` heißt dort „mit Typangabe“ | ohne Vermerk suggeriert der Filter eine Trennung, die die Daten nicht hergeben | Statusauswahl für diese Unternehmen in der Oberfläche ausblenden, oder Neuexport mit dem Feld `former` (Schreibzugriff, nicht jetzt) | keine Änderung der Zahlen; Lesart der 8 Reihen ändert sich |

Was sich mit dem Vorschlag **nicht** ändert: `normalize_status` liefert dieselben Schlüssel wie
heute; die Zahl der geeigneten Reihen je Status (E13: Mitarbeitende alle 15, `angestellt` 15,
`ex-angestellt` 6, `unbekannt` 3; Bewerbende alle 5, `eingestellt` 1, `unbekannt` 1) bleibt
gleich. Entscheidet sich der Autor für die Alternative `deferred` → `abgelehnt`, ändert sich
die Zahl ebenfalls nicht (weder `abgelehnt` noch `zurueckgestellt` hat eine geeignete Reihe);
die Bewertungslisten und der Vergleich der Gruppe `abgelehnt` enthalten dann zusätzlich die
514 Zeilen.

### 4. Prüfung

- Zählungen: Hilfsskripte außerhalb des Repositorys gegen die gehostete Datenbank
  (`employee`: 21 962 Zeilen, `candidates`: 4 676 Zeilen, nur SELECT, seitenweise zu 1 000).
- Exportspalten: `pandas.read_excel` auf die 28 Dateien des TecDAX-Ordners, nur Kopfzeile,
  Spaltentyp und Werteverteilung der Spalte `Status`.
- Scraper: Lesen von `kununu_bewertungen_scraper.py` (Zuordnungstabellen, Statuslogik) und
  der Git-Historie (`git log -S`), ohne Ausführung.
- Textsignale: reguläre Ausdrücke über Titel und Verbesserungsvorschlag je Bewerbungsstatus,
  nur Zählungen.

## D2 – Zuordnung Carl Zeiss (E15)

> **Entscheidung des Autors (2026-10-08): Option A.** Umgesetzt in Phase B (B2): `ticker_scope`
> „Konzerngesellschaft“ in der Metadatei, ausdrücklicher Vermerk in der Ansicht, Tests, E15
> und Feature-Doku 04.

### 1. Ausgangslage

- Datenbank: `companies` id 26, Name „Carl Zeiss“, `ticker` AFX.DE, `sector` „Optik/Medizintechnik“,
  `peer_group` „Börsennotiert DE“ (die Spalten aus Migration 006 sind vorhanden; der Wert steht
  also in der Datenbank, nicht nur in der Metadatei). `backend/data/company_metadata.json`:
  `ticker_scope` leer, Vermerk, dass sich das Kununu-Profil möglicherweise auf die nicht
  börsennotierte Carl Zeiss AG bezieht (E6, E15).
- Bewertungen: 1 700 Mitarbeitende (2007-09 bis 2025-07), 704 Bewerbende (2011-04 bis 2025-07).
  Die Exportdateien heißen `carl-zeissEmployee.xlsx` und `carl-zeissCandidates.xlsx`; der Scraper
  benennt Dateien nach dem Profilpfad, das Profil ist also `kununu.com/de/carl-zeiss`. Welchen
  Firmennamen dieses Profil trägt, konnte am 2026-10-08 nicht automatisiert geprüft werden
  (Kununu antwortet auf Abrufe ohne Browser mit einer Bot-Sperre, HTTP 405 „Human
  Verification“); **der Autor sieht das im Browser auf der Profilseite.**
- Die Ansicht nennt heute das Wertpapier über `ticker_name` aus dem Zwischenspeicher
  („Carl Zeiss Meditec AG · AFX.DE“ im Aktien-Dashboard, Legende und Hinweis auf der
  Anomalien-Seite), ohne Vermerk zur Konzernzugehörigkeit; den gibt es nur für
  `ticker_scope` = „Konzernmutter“ (`frontend/src/components/dashboard/MarketContext.jsx`,
  `pages/Stock.jsx`).

### 2. Hinweise in den Bewertungen (nur Zählungen)

Gezählt wurde je Bewertung, ob ein Begriff in Titel, Positionsangabe oder einem Textfeld vorkommt
(Groß-/Kleinschreibung egal). Mitarbeitende: 1 700 Bewertungen, Bewerbende: 704.

| Begriff (Suchmuster) | Mitarbeitende: Bewertungen mit Nennung | Bewerbende: Bewertungen mit Nennung | Lesart |
|---|---:|---:|---|
| „Meditec“ | 10 | 3 | Carl Zeiss Meditec AG (AFX.DE) |
| „Carl Zeiss AG“ / „ZEISS AG“ | 10 | 3 | Konzernmutter (nicht börsennotiert) |
| „Stiftung“ | 27 | 0 | Carl-Zeiss-Stiftung als Eigentümerin der Carl Zeiss AG |
| „Oberkochen“ | 34 | 9 | Sitz der Carl Zeiss AG und der SMT |
| „Jena“ | 15 | 4 | Sitz der Meditec, aber auch Standort des Konzerns (nicht eindeutig) |
| „SMT“ / „Halbleiter“ / „Semiconductor“ | 45 | 6 | Carl Zeiss SMT GmbH, Konzernsparte, nicht Meditec |
| „Vision“ / „Brillen“ | 10 | 0 | Sparte Vision Care (Aalen), nicht Meditec |
| „Microscopy“ / „Mikroskop“ | 5 | 4 | Sparte Mikroskopie (Jena, Göttingen) |
| „Industrial Quality“ / „Messtechnik“ / „IMT“ | 7 | 3 | Sparte Messtechnik |
| „Medizintechnik“ / „medical“ | 5 | 1 | Sparte Medizintechnik (Meditec) |
| „Aalen“, „Wetzlar“, „Göttingen“ (Standorte) | 7, 3, 3 | 1, 1, 1 | Konzernstandorte außerhalb der Meditec |
| „Konzern“ | 95 | 7 | Rahmen „Konzern“ überwiegt |
| „Sparte“ / „Geschäftsbereich“ / „Business Unit“ | 11 | 2 | Sichtweise auf mehrere Bereiche |
| „Tochter“ | 4 | 1 | – |
| „Zeiss“ überhaupt | 267 | 97 | – |

Beispiele ohne personenbezogene Angaben: Mehrere Bewertungen nennen als Arbeitgeber ausdrücklich
die Carl Zeiss SMT GmbH; einige den Konzernslogan „one ZEISS“; mehrfach werden Oberkochen als
Standort und die Stiftung als Eigentümerin genannt. Nennungen der Meditec sind selten (10 von
1 700). Die Positionsfelder helfen nicht weiter: `jobbeschreibung` enthält nur Typ und Abteilung
(am häufigsten „employee, research“ 250, „employee, operations“ 182, „employee, other“ 113),
`stellenbeschreibung` nur Berufsbezeichnungen (am häufigsten „Entwicklungsingenieur“ 29,
„Projektleiter“ 13, „Wissenschaftlicher Mitarbeiter“ 11).

Lesart (vom Autor zu bestätigen): Die Bewertungen beschreiben den **Gesamtkonzern** mit mehreren
Sparten und Standorten; die börsennotierte Meditec ist darin nur eine Gesellschaft. Eine
Zuordnung „eigene Aktie“ lässt sich aus den Bewertungen nicht begründen.

### 3. Optionen (Entscheidung D2)

| | Option A: Ticker AFX.DE behalten, neuer `ticker_scope` | Option B: Ticker entfernen, „Nicht börsennotiert“ |
|---|---|---|
| Änderung | `company_metadata.json`: `ticker_scope` z. B. „Konzerngesellschaft“ (börsennotierte Gesellschaft des Konzerns, den das Profil beschreibt); erlaubte Werte in `backend/tests/test_company_metadata.py` erweitern; Frontend nennt bei diesem Wert ausdrücklich „Kurs der Konzerngesellschaft Carl Zeiss Meditec AG (AFX.DE), nicht des Gesamtkonzerns“ (wie heute bei der Konzernmutter); E15 und Feature-Doku 04 fortschreiben | `company_metadata.json`: `ticker` null, `listed` false, `peer_group` „Nicht börsennotiert“, Vermerk; E15 und Feature-Doku 04 fortschreiben. **Zusätzlich muss der Wert in der Datenbank geändert werden**, weil `companies.ticker` Vorrang vor der Metadatei hat (`context_service.company_ticker_info`): `uv run python scripts/seed_company_metadata.py --apply` durch den Autor (Schreibzugriff, nicht in diesem Branch) |
| Folge in der Ansicht | Kurs und Kennzahlen der Meditec bleiben als Einordnung sichtbar, mit ausdrücklichem Vermerk; 17 Unternehmen mit Kurs bleiben | Carl Zeiss zeigt „Kein Aktienkurs: nicht börsennotiert“; das Kästchen auf der Anomalien-Seite entfällt; 16 Unternehmen mit Kurs |
| Folge für die Arbeit | FA-15 bleibt für Carl Zeiss erfüllbar; die Grenze „Konzernkurs bildet die bewertete Einheit nur mittelbar ab“ (E15) gilt hier umgekehrt: Teilkonzernkurs für ein Profil des Gesamtkonzerns | Konsistent mit der Lesart der Bewertungen; die Einordnung über den Markt entfällt für eines der dichtesten Profile (99 bewertete Monate) |
| Risiko | Leser könnte den Meditec-Kurs als Kurs „von Zeiss“ lesen; der Vermerk muss daher in jeder Kursansicht stehen | Information geht verloren, obwohl ein Teil der Bewertenden (Medizintechnik, Jena) zur notierten Gesellschaft gehören könnte |
| Tests | `test_company_metadata.py` (erlaubte Werte), `tests/market/` (Vermerk), Frontend-Bau | `test_company_metadata.py`, `tests/market/test_market_summary.py` (Tabelle ohne AFX.DE), Frontend-Bau |

Nicht vorgeschlagen: `ticker_scope` „eigene Aktie“ für AFX.DE, weil die Bewertungen das nicht
stützen. In beiden Optionen nennt die Ansicht das Wertpapier weiterhin ausdrücklich (Option B:
gar kein Wertpapier, dafür der Hinweis „nicht börsennotiert“).

## D3 – Evaluationsinstanz (E16)

> **Entscheidung des Autors (2026-10-08): Variante B**, Bau mit `VITE_SHOW_FINANCE_EXTRAS=false`.
> Varianten, Folgen, Einstellungen und Prüfliste stehen in `docs/evaluationsinstanz.md`;
> umgesetzt in Phase B (B3): E16, Evaluationsdokument, Feature-Doku 05 und der Tooltip „Aktie“
> in der Seitenleiste.

## Stand nach Phase B (2026-10-08)

| Schritt | Commit | Inhalt |
|---|---|---|
| B1 | 1f9578b | Statuszuordnung bestätigt (D1): Bezeichnung „Zurückgestellt oder Absage“, Herkunft in Kommentaren, Vertragstests, E13, Feature-Doku 02 |
| B2 | ba2f804 | Carl Zeiss (D2, Option A): `ticker_scope` „Konzerngesellschaft“, ausdrücklicher Vermerk in der Ansicht, Tests, E15, Feature-Doku 04, README |
| B3 | f83aedc | Evaluationsinstanz (D3, Variante B): Tooltip „Aktie“ nach Schalter, E16, Evaluationsdokument, Feature-Doku 05, README |
| B4 | dieser Commit | E5: Umfang, Werkzeuge und Ablauf der Annotation; README-Tabelle |

Offen bleiben die Nutzungsbedingungen (`docs/nutzungsbedingungen.md`, Fragen an den Betreuer)
und das Eintragen der Referenzzeiträume durch den Autor.
