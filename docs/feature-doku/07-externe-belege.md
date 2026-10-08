# 07 – Externe Belege im Ereignisfenster

| | |
|---|---|
| Inkrement | 4 (Zyklus 2) |
| Anforderungen | Erklärungsansätze neben dem Bewertungsverlauf laut Exposé (TF4); Kontext zu den auffälligen Veränderungen aus [01](01-anomalien-im-verlauf.md) und [03](03-auffaellige-einzelmonate.md); Anforderungstexte liegen nicht im Repository |
| Entscheidungen | E7 (Quellen, Maßnahmen vom 2026-10-08), E18 (Ereignisfenster, Belegspeicher, Vergleichsfenster), E19 (Quellenarten, Verlässlichkeit), E20 (allgemeine Ereignisse, Dauerregel) in `docs/entscheidungen.md` |
| Status | umgesetzt und nachgeschärft (2026-10-08); **vorläufig** (Fenstergrößen, Verlässlichkeitsstufen und Dauergrenze sind Setzungen); Suchbegriffe der Unternehmen mit Markierungen, EQS-UUIDs und sechs allgemeine Ereignisse vom Autor bestätigt (D1–D3, 2026-10-08) |
| Stand | 2026-10-08 (Nachschärfung: Vergleichsfenster, paralleler Abruf, Dauerregel) |

## 1. Vorstellung

Auf der Detailseite **„Anomalien im Verlauf“** (`/anomalies`) steht unter dem Vorher-Nachher-Vergleich
ein neuer Abschnitt **„Externe Belege im Ereignisfenster“**, sobald eine auffällige Veränderung,
ein auffälliger Einzelmonat oder ein frei gewählter Zeitraum ausgewählt ist. Ein **Beleg** ist eine
zeitlich nahe Meldung aus einer externen Quelle mit Datum, Titel, Herausgeber und Link. Er ist
keine Ursache: Die Ansicht behauptet keinen Zusammenhang mit den Bewertungen und bewertet
keine Meldung.

Der Kopf des Abschnitts nennt das **Ereignisfenster** (zum Beispiel „Apr. 2024 – Aug. 2024, 5
Monate: 3 davor, 1 danach, um den Übergang“) und die **Anzahl je Typ** („362 Belege: 350
Meldungen, 12 Ad-hoc“). Je Beleg stehen Datum, Titel als Link in einem neuen Tab, Herausgeber,
der Typ als Badge (**Meldung**, **Ad-hoc**, **Allgemeines Ereignis, Hypothese**) und bei
englischsprachigen Meldungen die Badge **EN**; bei Mitteilungen von EQS steht dazu, von welcher
Gesellschaft sie stammen (bei Carl Zeiss: Carl Zeiss Meditec AG). Die neuesten Belege stehen
oben; lange Listen werden in Schritten von 25 nachgeladen. Gibt es keinen Beleg, steht dort
„Kein Beleg im Fenster gefunden“ mit den bekannten Grenzen (ältere Zeiträume, kleine
Unternehmen, mehrdeutige Namen). Darunter nennt eine Zeile je Quelle, wie viele Monate des
Fensters vorliegen, wie viele davon gerade abgerufen wurden, den Stand des Speichers und nicht
abrufbare Monate. Liegt ein Zeitraum noch nicht im Speicher, dauert die erste Antwort einige
Sekunden; nach zwei Sekunden sagt der Abschnitt, dass die Belege für diesen Zeitraum zum ersten
Mal von den Quellen geladen werden und beim nächsten Aufruf aus dem Speicher kommen. Der
Abschnitt endet mit dem festen Hinweis:

> Belege sind zeitlich nahe Meldungen aus externen Quellen. Sie sind keine Aussage über
> Ursachen; interne Auslöser sind von außen nicht sichtbar.

Im Kopf des Monatsverlaufs gibt es das Kästchen **„Allgemeine Ereignisse“** (`?ereignisse=an`,
Standard aus). Es blendet die vom Autor bestätigten allgemeinen Ereignisse (seit dem 2026-10-08
sechs: Finanzkrise 2008/09, Atom-Moratorium 2011, erster und zweiter Lockdown, Überfall auf die
Ukraine 2022, Energiepreiskrise 2022/23; jedes höchstens sechs Monate lang) als gestrichelte
Flächen in das Diagramm ein, beschriftet als „Allgemeines Ereignis, Hypothese“; dieselben
Ereignisse erscheinen im Abschnitt als Belege vom Typ „Allgemeines Ereignis“.

Nutzen: Wer eine auffällige Veränderung betrachtet, sieht ohne eigene Suche, was in diesen
Monaten über das Unternehmen gemeldet wurde, und kann es bei der Einordnung im Kopf behalten,
ohne dass das Dashboard daraus eine Ursache macht.

## 2. Erklärung

1. **Ereignisfenster (E18).** Für einen Niveauwechsel reicht das Fenster von 3 Monaten vor
   dem Beginn des Übergangs bis 1 Monat nach dem markierten Monat. Der Übergang beginnt im
   Monat nach dem letzten bewerteten Monat davor (`previous_period`); ohne Lücke ist das der
   markierte Monat selbst, bei einer Lücke beginnt das Fenster vor der Lücke, weil der Übergang
   irgendwo darin liegen kann. Für einen Einzelmonat und eine freie Auswahl gelten dieselben
   Abstände um den Monat bzw. den Zeitraum. Beide Größen sind Parameter der Routen.
2. **Quellen (E7, E19).** Google News RSS ist die Hauptquelle: je Unternehmen und Kalendermonat
   eine Abfrage mit den Operatoren `after:` und `before:` und dem Suchbegriff aus
   `backend/data/company_metadata.json` (`news_term`, sonst der Name ohne Rechtsform;
   Ausschlussbegriffe in `news_exclude`, zum Beispiel „FC Carl Zeiss“ und „Fußball“ bei Carl
   Zeiss). EQS News ist die zweite Quelle für börsennotierte Unternehmen: die Mitteilungen des
   Emittenten je Monat über seine companyUUID (Feld `eqs` in der Metadatei). GDELT ist nur hinter
   dem Schalter `CONTEXT_GDELT=1` angebunden und aus. Gespeichert werden nur Titel, Herausgeber,
   Link, Datum, Quelle, Typ, Verlässlichkeit und Sprache; keine Volltexte.
3. **Belegspeicher (E18).** Je Unternehmen, Quelle und Monat eine Datei unter
   `backend/data/context/` (nicht im Repository). Die Belege eines Fensters sind alle gespeicherten
   Meldungen, deren Datum im Fenster liegt; so bleibt der Speicher gültig, wenn sich die
   Erkennung ändert. Abgeschlossene Monate werden nicht erneut abgerufen, der laufende Monat
   frühestens nach 12 Stunden; ein geänderter Suchbegriff macht einen Monat ungültig. Doppelte
   Meldungen (gleicher Link oder gleicher normalisierter Titel) zählen einmal. Zwischen zwei
   Abrufen derselben Quelle liegen mindestens 2 Sekunden; die Kennung nennt Forschung und
   nicht-kommerzielle Nutzung. Die Quellen werden nebeneinander abgerufen, je Quelle ein Strang
   (eine Sperre je Quelle hält den Abstand auch zwischen Strängen ein); ein nicht gespeichertes
   Fenster von fünf Monaten mit zwei Quellen braucht so rund 10 statt 17 Sekunden. Fällt eine
   Quelle aus, liefert die andere weiter; der Fehler steht in der Quellenzeile.
4. **Typ und Verlässlichkeit (E19).** `adhoc` (EQS) hoch, `news` (Google News, GDELT) mittel,
   `global` (allgemeine Ereignisse) Hypothese; `market` ist reserviert. Die Sprache je Titel
   schätzt die Stoppwort-Heuristik aus dem Spike (`docs/quellen-spike.md`); EQS und GDELT
   melden sie selbst. EQS liefert in der Listenroute die englische Fassung einer Meldung.
5. **Routen.** `GET /api/analytics/company/{id}/anomalies/{anomaly_id}/context` (auch für die
   Kennung eines Einzelmonats) und `GET /api/analytics/company/{id}/context?from=&to=` liefern
   Fenster, Belege (seitenweise), Anzahl je Typ, Stand je Quelle und `coverage`;
   `GET /api/analytics/global-events` die bestätigten allgemeinen Ereignisse. Unbekannte
   Veränderung: 404; ohne Daten eine leere Liste mit Grund, kein 500.
6. **Vergleichsfenster (E18, Nachschärfung).** Die Abdeckung der Markierungen allein sagt
   wenig, wenn ein Unternehmen in fast jedem Monat Meldungen hat. Deshalb bekommt jede Markierung
   bis zu drei Vergleichsfenster desselben Unternehmens: das Fenster der Markierung um −12, +12,
   −24 oder +24 Monate verschoben (in dieser Reihenfolge geprüft, gleiche Länge und Lage zum
   Anker). Ein verschobenes Fenster entfällt, wenn es ein Fenster einer Markierung dieses
   Unternehmens überschneidet oder nicht vollständig in der bewerteten Reihe liegt
   (`comparison_windows` in `evidence_service.py`). Der Abdeckungsbericht stellt mit
   `--comparison` Markierungs- und Vergleichsfenster gegenüber: Anteil mit mindestens einem Beleg
   (news oder adhoc, je Typ), Median und Spannweite der Belege je Fenster; Fenster mit fehlenden
   Monaten im Speicher werden ausgewiesen und nicht als „kein Beleg“ gezählt. Die Zahlen sind
   beschreibend, ohne Signifikanzaussage; ein Unterschied sagt nichts über Ursachen und nichts
   darüber, ob Markierungen Meldungen „auslösen“.
7. **Allgemeine Ereignisse, Dauerregel (E20).** Ein allgemeines Ereignis dauert höchstens 6
   Monate (vorläufig); der Lader weist längere Einträge zurück. In der Abdeckung zählt ein
   allgemeines Ereignis nicht als Beleg, die Auswertung weist es getrennt aus.
8. **Betrieb.** `uv run python scripts/fetch_context.py --comparison` füllt den Speicher für alle
   Markierungen der geeigneten Unternehmen und ihre Vergleichsfenster (gedrosselt, fortsetzbar,
   `--dry-run` zählt nur); `--from-month 2019-01 --company <id>` lädt alle Monate eines
   Unternehmens ab dem Startmonat, damit jede Dimension und jede freie Auswahl sofort antwortet.
   Nach drei Fehlern in Folge einer Quelle (zum Beispiel Status 429 oder 503) bricht der Lauf für
   diese Quelle ab und nennt Unternehmen und Monat zum Fortsetzen. `CONTEXT_LIVE_FETCH=0`
   unterbindet Abrufe zur Laufzeit (Evaluationsinstanz, `docs/evaluationsinstanz.md`).
   `uv run python scripts/report_context_coverage.py --comparison` zählt je Unternehmen, wie
   viele Markierungs- und Vergleichsfenster mindestens einen Beleg haben (Abschnitt 5);
   `uv run python scripts/report_context_decisions.py` erzeugt die Entscheidungsvorlagen
   (Suchbegriffe, EQS, Ereignisse, Vorabruf), beides nur lesend und ohne Titel.

## 3. Begründung

- **Fenster statt Einzelmonat:** Die Literatur zu Arbeitgeberbewertungen nennt Reaktionen
  innerhalb des Folgequartals (`docs/referenzzeitraeume-literatur.md`); drei Monate vor dem
  Übergang decken das ab, ein Monat danach fängt Folgemeldungen ein. Die Größen sind
  Setzungen und als Parameter änderbar.
- **Speicher je Monat statt je Veränderung:** Die Erkennung ist noch nicht gegen
  Referenzzeiträume kalibriert (E5, E9); ändern sich Parameter oder Markierungen, bleiben die
  gespeicherten Monate gültig. Ein Dateispeicher statt der in der Roadmap vorgesehenen Tabellen
  007 und 008, weil die Datenbank in Zyklus 2 nur gelesen wird (E18).
- **Keine Rangfolge, keine Stimmung, kein Thema:** Der Abschnitt zeigt, was gemeldet wurde, in
  zeitlicher Folge. Eine Ordnung nach Erklärungskraft oder eine Bewertung der Meldungen folgt in
  Inkrement 5; hier würde sie als Erklärung gelesen.
- **Typ als Badge:** Pflichtmitteilungen, Nachrichten und allgemeine Ereignisse sind
  verschieden verlässlich; die Badge macht die Art der Quelle sichtbar, ohne eine Meldung zu
  bewerten.
- **Allgemeine Ereignisse als Hypothese, Standard aus, höchstens sechs Monate:** Ein zeitliches
  Zusammentreffen mit einem allgemeinen Zeitraum ist keine Erklärung; deshalb nur bestätigte
  Ereignisse, nur auf Wunsch eingeblendet und ausdrücklich als Hypothese beschriftet. Ein
  Zeitraum über Jahre hinge an fast jeder Markierung dieser Jahre; die Dauergrenze hält die
  Ereignisse datierbar.
- **Vergleichsfenster statt bloßer Abdeckung:** Die Prüfung vom 2026-10-08 ergab rund 14
  Meldungen je Unternehmensmonat; große Unternehmen haben in fast jedem Fenster eine Meldung, die
  Abdeckung allein unterscheidet kaum. Die Vergleichsfenster desselben Unternehmens zeigen, ob
  ein Markierungsfenster überhaupt anders aussieht als ein beliebiges Fenster; ±12 und ±24
  Monate halten Jahreszeit und Berichtskalender gleich. Erst die thematische Korrespondenz in
  Inkrement 5 kann Meldungen von Markierungen unterscheiden.
- **Quellen nebeneinander:** Der Mindestabstand gilt je Quelle; zwei Quellen müssen nicht
  aufeinander warten. Der erste Abruf eines Fensters wird so etwa halb so lang, ohne mehr Last
  je Quelle.
- **Nutzungsbedingungen:** Die Maßnahmen aus E7 (Drosselung, Kennung, nur Titel und Link,
  Speicher außerhalb des Repositorys, Abschaltung) folgen den Fundstellen in
  `docs/nutzungsbedingungen.md`.

## 4. Grenzen

- **Keine Ursachen.** Ein Beleg ist eine zeitlich nahe Meldung, mehr nicht; interne Auslöser
  (Umstrukturierungen, Führungswechsel ohne Meldung) sind von außen nicht sichtbar.
- **Abdeckung.** Google News liefert höchstens rund 100 Einträge je Abfrage, für Zeiträume vor
  etwa 2015 und für kleine Unternehmen wenige oder keine Meldungen; die Namenssuche bringt
  bei mehrdeutigen Namen fremde Treffer (Carl Zeiss, Telekom), die Ausschlussbegriffe mildern das
  nur. EQS deckt nur Emittenten und nur Pflicht- und Unternehmensmitteilungen ab; NTT DATA SE
  hat keinen EQS-Emittenten, bei Carl Zeiss gehören die Mitteilungen der Carl Zeiss Meditec AG.
- **Große Unternehmen** erzeugen hunderte Meldungen je Fenster, darunter viele ohne Bezug zum
  Arbeitgeber (Börsenberichte, Sportstätten, Produkte). Die Liste ordnet sie nicht.
- **Sprache.** Die Heuristik schätzt nur Deutsch und Englisch grob; EQS-Mitteilungen liegen
  meist auf Englisch vor.
- **Fenstergrößen**, Verlässlichkeitsstufen und die Dauergrenze der allgemeinen Ereignisse sind
  vorläufige Setzungen; die Versätze der Vergleichsfenster (±12, ±24 Monate, höchstens drei)
  ebenso.
- **Vergleichsfenster** vergleichen nur Anzahlen. Zwei Fenster mit gleich vielen Meldungen können
  ganz verschiedene Meldungen enthalten; ob eine Meldung zur Markierung passt, bleibt offen.

## 5. Prüfung und Belege

| Was | Beleg |
|---|---|
| Ereignisfenster | `backend/tests/evidence/test_evidence_window.py`: ohne und mit Lücke, Reihenrand, Jahreswechsel, Parameter |
| Speicher und Hauptquelle | `test_evidence_store.py`: Monatsabfrage, Normalisierung, Speicher, erneuter Abruf, geänderter Suchbegriff, Duplikate, Ausfall, `CONTEXT_LIVE_FETCH=0`, Drosselung |
| EQS und GDELT | `test_evidence_eqs.py`: Umformung, Link, Seiten, Fehler des Endpunkts, Suche der UUID, Ausfall einer Quelle neben der anderen, Schalter |
| Sprache | `test_evidence_language.py` |
| Routen | `test_context_routes.py` (In-Memory-Store, Demo 3): Form, Einzelmonat, Parameter, 404, 400, leere Liste statt 500, Seiten; `test_global_events.py` |
| Skripte | `test_fetch_context_script.py` (Vorabruf, Fortsetzen, Grenze, Schalter, `--from-month`, `--comparison`, Abbruch nach Fehlern in Folge), `test_context_coverage.py` (Abdeckung, Vergleichsfenster), `test_context_decisions.py` (Entscheidungsvorlagen) |
| Vergleichsfenster | `test_evidence_window.py`: Reihenfolge der Versätze, gleiche Länge, Überschneidung mit Markierungsfenstern (auch dem eigenen), Grenzen der Reihe, Parameter |
| Paralleler Abruf | `test_evidence_eqs.py`: beide Quellen gleichzeitig (Barriere), Ausfall einer Quelle im eigenen Strang, Sperre je Quelle über Stränge hinweg |
| Dauerregel | `test_global_events.py`: 6 Monate erlaubt, 7 und 24 zurückgewiesen, Grenze als Parameter, Repository-Datei innerhalb der Regel, Bestätigungen D3 |
| Zusicherungen | `test_evidence_contracts.py`: Einzelmonat aus konstruierter Erkennung, keine Volltexte, reservierter Typ, Speicher in `.gitignore` |
| Browser (2026-10-08) | SAP SE, Anstieg ab 2024-07: Abschnitt mit Fenster Apr.–Aug. 2024, Belege seitenweise, Typ- und EN-Badges; Telekom mit Overlay zweier vorübergehend bestätigter Ereignisse und Legende „Allgemeines Ereignis, Hypothese“ (danach zurückgesetzt); dunkles Farbschema. Nachschärfung: Freenet, freie Auswahl Okt. 2018 (nicht im Speicher): Hinweis „zum ersten Mal geladen“ nach zwei Sekunden, danach 29 Belege und Quellenzeile „5 gerade abgerufen“, keine Konsolenfehler |
| Dauer des ersten Abrufs | Freenet, Fenster Juli–Nov. 2018, zwei Quellen, temporärer Speicher: 16,6 s nacheinander, 9,8 s nebeneinander, 0,004 s aus dem Speicher |
| Lint | eslint für die berührten Frontend-Dateien, ruff (nur Pyflakes-Regeln) für die Backend-Dateien, jeweils ohne Befund |

### Abdeckung für Kontrollpunkt 2 (Stand 2026-10-08, Speicher nach dem Vorabruf der Nachschärfung)

Vorabruf: erster Lauf am 2026-10-08 (`backend/data/calibration/context_prefetch_2026-10-08.json`:
15 geeignete Unternehmen, 19 Niveauwechsel und 9 Einzelmonate, 297 Abrufe in 9,8 Minuten) und
Nachschärfung B2 (`context_prefetch_nachschaerfung_2026-10-08.json`) in der Reihenfolge geänderter
Suchbegriff NTT DATA (27 Abrufe), Vergleichsfenster aller elf Unternehmen mit Markierungen (Google
News 385, EQS 328 Abrufe), alle Monate ab 2019-01 für die acht Unternehmen mit Markierungen ab
2019 (Google News 378, EQS 345); je Quelle ein Prozess, beide nebeneinander, 2 s Abstand je
Quelle. Google News RSS 790 Abrufe in 26,4 Minuten ohne Fehler, EQS News 673 Abrufe in 22,8
Minuten mit einem Zeitüberschreitungsfehler (Carl Zeiss, 2017-10, im dritten Schritt nachgeholt);
danach 1778 Monatsdateien im Speicher, kein Monat eines Markierungs- oder Vergleichsfensters
fehlt. Allgemeine Ereignisse: sechs bestätigt (E20), sie zählen nicht als Beleg und stehen
getrennt. Tabellen aus `scripts/report_context_coverage.py --comparison`
(`backend/data/calibration/context_coverage_vergleich_2026-10-08.json`); Unternehmen ohne
Markierung (Thyssenkrupp, Open Grid Europe, KIT, TU München) fehlen in den Tabellen.

| Unternehmen | Niveauwechsel mit Beleg | davon news | davon adhoc | mit allgemeinem Ereignis (zählt nicht) | Einzelmonate mit Beleg | davon news | davon adhoc | mit allgemeinem Ereignis (zählt nicht) |
|---|---|---|---|---|---|---|---|---|
| E.ON | 1/1 (100 %) | 1/1 (100 %) | 1/1 (100 %) | 0/1 (0 %) | – | – | – | – |
| RWE | 1/1 (100 %) | 1/1 (100 %) | 1/1 (100 %) | 1/1 (100 %) | 1/1 (100 %) | 1/1 (100 %) | 1/1 (100 %) | 0/1 (0 %) |
| SAP SE | 1/1 (100 %) | 1/1 (100 %) | 1/1 (100 %) | 0/1 (0 %) | 1/1 (100 %) | 1/1 (100 %) | 1/1 (100 %) | 0/1 (0 %) |
| NTT DATA SE | 4/4 (100 %) | 4/4 (100 %) | 0/4 (0 %) | 1/4 (25 %) | – | – | – | – |
| 1&1 AG | 1/1 (100 %) | 1/1 (100 %) | 1/1 (100 %) | 0/1 (0 %) | – | – | – | – |
| Bechtle | 1/1 (100 %) | 1/1 (100 %) | 1/1 (100 %) | 0/1 (0 %) | – | – | – | – |
| Cancom | – | – | – | – | 2/2 (100 %) | 2/2 (100 %) | 2/2 (100 %) | 0/2 (0 %) |
| Carl Zeiss | – | – | – | – | 2/2 (100 %) | 2/2 (100 %) | 1/2 (50 %) | 0/2 (0 %) |
| Compugroup Medical Deutschland | 1/1 (100 %) | 1/1 (100 %) | 1/1 (100 %) | 1/1 (100 %) | – | – | – | – |
| Telekom | 4/4 (100 %) | 4/4 (100 %) | 3/4 (75 %) | 1/4 (25 %) | 3/3 (100 %) | 3/3 (100 %) | 3/3 (100 %) | 1/3 (33 %) |
| Freenet | 5/5 (100 %) | 5/5 (100 %) | 5/5 (100 %) | 1/5 (20 %) | – | – | – | – |
| **Gesamt** | 19/19 (100 %) | 19/19 (100 %) | 14/19 (74 %) | 5/19 (26 %) | 9/9 (100 %) | 9/9 (100 %) | 8/9 (89 %) | 1/9 (11 %) |

| Unternehmen | Markierungen bis 2018 mit Beleg | Markierungen ab 2019 mit Beleg | alle Markierungen mit Beleg |
|---|---|---|---|
| E.ON | – | 1/1 (100 %) | 1/1 (100 %) |
| RWE | – | 2/2 (100 %) | 2/2 (100 %) |
| SAP SE | – | 2/2 (100 %) | 2/2 (100 %) |
| NTT DATA SE | 1/1 (100 %) | 3/3 (100 %) | 4/4 (100 %) |
| 1&1 AG | 1/1 (100 %) | – | 1/1 (100 %) |
| Bechtle | 1/1 (100 %) | – | 1/1 (100 %) |
| Cancom | 2/2 (100 %) | – | 2/2 (100 %) |
| Carl Zeiss | 1/1 (100 %) | 1/1 (100 %) | 2/2 (100 %) |
| Compugroup Medical Deutschland | – | 1/1 (100 %) | 1/1 (100 %) |
| Telekom | 5/5 (100 %) | 2/2 (100 %) | 7/7 (100 %) |
| Freenet | 2/2 (100 %) | 3/3 (100 %) | 5/5 (100 %) |
| **Gesamt** | 13/13 (100 %) | 15/15 (100 %) | 28/28 (100 %) |

Ein Beleg ist eine Meldung (news) oder eine Ad-hoc-Mitteilung (adhoc); bestätigte allgemeine Ereignisse zählen nicht als Beleg und stehen getrennt (E20).

#### Markierungs- gegen Vergleichsfenster

| Unternehmen | Markierungsfenster (vollständig) | mit Beleg | davon news | davon adhoc | Belege je Fenster: Median (Spannweite) | Vergleichsfenster (vollständig) | mit Beleg | davon news | davon adhoc | Belege je Fenster: Median (Spannweite) |
|---|---|---|---|---|---|---|---|---|---|---|
| E.ON | 1 (1) | 1/1 (100 %) | 1/1 (100 %) | 1/1 (100 %) | 373 (373–373) | 3 (3) | 3/3 (100 %) | 3/3 (100 %) | 3/3 (100 %) | 335 (302–438) |
| RWE | 2 (2) | 2/2 (100 %) | 2/2 (100 %) | 2/2 (100 %) | 304.5 (301–308) | 6 (6) | 6/6 (100 %) | 6/6 (100 %) | 6/6 (100 %) | 171 (110–459) |
| SAP SE | 2 (2) | 2/2 (100 %) | 2/2 (100 %) | 2/2 (100 %) | 345.5 (329–362) | 6 (6) | 6/6 (100 %) | 6/6 (100 %) | 6/6 (100 %) | 195.5 (163–460) |
| NTT DATA SE | 4 (4) | 4/4 (100 %) | 4/4 (100 %) | – | 2 (1–21) | 10 (10) | 10/10 (100 %) | 10/10 (100 %) | – | 5 (1–28) |
| 1&1 AG | 1 (1) | 1/1 (100 %) | 1/1 (100 %) | 1/1 (100 %) | 25 (25–25) | 3 (3) | 3/3 (100 %) | 3/3 (100 %) | 3/3 (100 %) | 30 (27–37) |
| Bechtle | 1 (1) | 1/1 (100 %) | 1/1 (100 %) | 1/1 (100 %) | 6 (6–6) | 3 (3) | 3/3 (100 %) | 3/3 (100 %) | 2/3 (67 %) | 7 (4–7) |
| Cancom | 2 (2) | 2/2 (100 %) | 2/2 (100 %) | 2/2 (100 %) | 7 (5–9) | 6 (6) | 6/6 (100 %) | 5/6 (83 %) | 4/6 (67 %) | 4 (2–5) |
| Carl Zeiss | 2 (2) | 2/2 (100 %) | 2/2 (100 %) | 1/2 (50 %) | 59.5 (30–89) | 5 (5) | 5/5 (100 %) | 5/5 (100 %) | 4/5 (80 %) | 34 (16–69) |
| Compugroup Medical Deutschland | 1 (1) | 1/1 (100 %) | 1/1 (100 %) | 1/1 (100 %) | 38 (38–38) | 3 (3) | 3/3 (100 %) | 3/3 (100 %) | 3/3 (100 %) | 25 (19–32) |
| Telekom | 7 (7) | 7/7 (100 %) | 7/7 (100 %) | 6/7 (86 %) | 61 (51–129) | 16 (16) | 16/16 (100 %) | 16/16 (100 %) | 15/16 (94 %) | 60 (47–168) |
| Freenet | 5 (5) | 5/5 (100 %) | 5/5 (100 %) | 5/5 (100 %) | 31 (18–57) | 15 (15) | 15/15 (100 %) | 15/15 (100 %) | 15/15 (100 %) | 41 (7–98) |
| **Gesamt** | 28 (28) | 28/28 (100 %) | 28/28 (100 %) | 22/24 (92 %) | 45 (1–373) | 76 (76) | 76/76 (100 %) | 75/76 (99 %) | 61/66 (92 %) | 47.5 (1–460) |

Anteile beziehen sich auf die vollständig im Speicher liegenden Fenster (in Klammern); ein Beleg ist eine Meldung (news) oder eine Ad-hoc-Mitteilung (adhoc), allgemeine Ereignisse zählen nicht. Die Zahlen sind beschreibend, ohne Signifikanzaussage und ohne Aussage über Ursachen.

| Unternehmen | Markierungen | ohne Vergleichsfenster | Vergleichsfenster | davon vollständig im Speicher | fehlende Monate (je Quelle gezählt) | Fenster mit allgemeinem Ereignis (Markierung / Vergleich) |
|---|---|---|---|---|---|---|
| E.ON | 1 | 0 | 3 | 3 | 0 | 0 / 2 |
| RWE | 2 | 0 | 6 | 6 | 0 | 1 / 3 |
| SAP SE | 2 | 0 | 6 | 6 | 0 | 0 / 3 |
| NTT DATA SE | 4 | 0 | 10 | 10 | 0 | 1 / 5 |
| 1&1 AG | 1 | 0 | 3 | 3 | 0 | 0 / 0 |
| Bechtle | 1 | 0 | 3 | 3 | 0 | 0 / 0 |
| Cancom | 2 | 0 | 6 | 6 | 0 | 0 / 0 |
| Carl Zeiss | 2 | 0 | 5 | 5 | 0 | 0 / 1 |
| Compugroup Medical Deutschland | 1 | 0 | 3 | 3 | 0 | 1 / 1 |
| Telekom | 7 | 1 | 16 | 16 | 0 | 2 / 4 |
| Freenet | 5 | 0 | 15 | 15 | 0 | 1 / 5 |
| **Gesamt** | 28 |  | 76 | 76 | 0 | 6 / 24 |

Ergebnis: Alle 28 Markierungen haben mindestens einen Beleg (Stand vor der Nachschärfung 27 von
28; der Niveauwechsel von NTT DATA SE im November 2017 hat mit dem erweiterten Suchbegriff einen
Beleg, zugleich liefern die 27 Markierungsmonate von NTT DATA mit dem neuen Begriff 26 statt 54
Meldungen). Die 76 Vergleichsfenster sind ebenso zu 100 % abgedeckt, und die Mediane der Belege
je Fenster liegen in derselben Größenordnung (Markierung 45, Vergleich 47,5); je Unternehmen
liegt das Markierungsfenster mal über dem Vergleich (RWE 305 gegen 171, SAP 346 gegen 196, Carl
Zeiss 60 gegen 34), mal darunter (Freenet 31 gegen 41, NTT DATA 2 gegen 5) oder gleichauf
(Telekom 61 gegen 60). Die Abdeckung allein ist damit kein Gütemaß: Ein Markierungsfenster
unterscheidet sich in der Zahl der Meldungen nicht erkennbar von einem um ein oder zwei Jahre
verschobenen Fenster desselben Unternehmens. Die Unterscheidung muss aus dem Inhalt kommen
(thematische Korrespondenz, Inkrement 5). Die Zahlen sind beschreibend, ohne Test und ohne
Aussage über Ursachen.

## 6. Offene Punkte

- Bestätigt am 2026-10-08: Suchbegriffe der elf Unternehmen mit Markierungen (NTT DATA mit
  erweitertem Begriff), die elf EQS-UUIDs, sechs allgemeine Ereignisse. Offen bleiben die
  Suchbegriffe der Unternehmen ohne Markierung, die EQS-UUIDs der Emittenten ohne Markierung und
  die Homeoffice-Pflicht 2021.
- Fenstergrößen 3 und 1 Monat sowie die Versätze der Vergleichsfenster gegen die
  Referenzzeiträume prüfen, sobald DZ1 vorliegt.
- Die Vergleichsfenster zeigen nur, ob Markierungsfenster mehr oder weniger Meldungen haben als
  andere Fenster; die Unterscheidung nach Inhalt liefert erst die thematische Korrespondenz in
  Inkrement 5.
- Deutsche Fassungen der EQS-Mitteilungen (Detailroute je Meldung) und GDELT bleiben aus.
- Die Fragen zu den Nutzungsbedingungen aus `docs/nutzungsbedingungen.md` bleiben beim Betreuer.
- Rangfolge, thematische Zuordnung und Stimmung der Belege folgen in Inkrement 5.
