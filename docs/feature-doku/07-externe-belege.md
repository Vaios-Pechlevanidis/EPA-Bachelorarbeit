# 07 – Externe Belege im Ereignisfenster

| | |
|---|---|
| Inkrement | 4 (Zyklus 2) |
| Anforderungen | Erklärungsansätze neben dem Bewertungsverlauf laut Exposé (TF4); Kontext zu den auffälligen Veränderungen aus [01](01-anomalien-im-verlauf.md) und [03](03-auffaellige-einzelmonate.md); Anforderungstexte liegen nicht im Repository |
| Entscheidungen | E7 (Quellen, Maßnahmen vom 2026-10-08), E18 (Ereignisfenster, Belegspeicher), E19 (Quellenarten, Verlässlichkeit), E20 (allgemeine Ereignisse) in `docs/entscheidungen.md` |
| Status | umgesetzt; **vorläufig** (Fenstergrößen und Verlässlichkeitsstufen sind Setzungen; Suchbegriffe, EQS-UUIDs und allgemeine Ereignisse vom Autor zu bestätigen) |
| Stand | 2026-10-08 |

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
Fensters vorliegen, den Stand des Speichers und nicht abrufbare Monate. Der Abschnitt endet mit
dem festen Hinweis:

> Belege sind zeitlich nahe Meldungen aus externen Quellen. Sie sind keine Aussage über
> Ursachen; interne Auslöser sind von außen nicht sichtbar.

Im Kopf des Monatsverlaufs gibt es das Kästchen **„Allgemeine Ereignisse“** (`?ereignisse=an`,
Standard aus). Es blendet vom Autor bestätigte allgemeine Ereignisse (Pandemie, Energiekrise)
als gestrichelte Flächen in das Diagramm ein, beschriftet als „Allgemeines Ereignis, Hypothese“;
dieselben Ereignisse erscheinen im Abschnitt als Belege vom Typ „Allgemeines Ereignis“.

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
   nicht-kommerzielle Nutzung. Fällt eine Quelle aus, liefert die andere weiter; der Fehler steht
   in der Quellenzeile.
4. **Typ und Verlässlichkeit (E19).** `adhoc` (EQS) hoch, `news` (Google News, GDELT) mittel,
   `global` (allgemeine Ereignisse) Hypothese; `market` ist reserviert. Die Sprache je Titel
   schätzt die Stoppwort-Heuristik aus dem Spike (`docs/quellen-spike.md`); EQS und GDELT
   melden sie selbst. EQS liefert in der Listenroute die englische Fassung einer Meldung.
5. **Routen.** `GET /api/analytics/company/{id}/anomalies/{anomaly_id}/context` (auch für die
   Kennung eines Einzelmonats) und `GET /api/analytics/company/{id}/context?from=&to=` liefern
   Fenster, Belege (seitenweise), Anzahl je Typ, Stand je Quelle und `coverage`;
   `GET /api/analytics/global-events` die bestätigten allgemeinen Ereignisse. Unbekannte
   Veränderung: 404; ohne Daten eine leere Liste mit Grund, kein 500.
6. **Betrieb.** `uv run python scripts/fetch_context.py` füllt den Speicher für alle Markierungen
   der geeigneten Unternehmen (gedrosselt, fortsetzbar, `--dry-run` zählt nur);
   `CONTEXT_LIVE_FETCH=0` unterbindet Abrufe zur Laufzeit (Evaluationsinstanz,
   `docs/evaluationsinstanz.md`). `uv run python scripts/report_context_coverage.py` zählt je
   Unternehmen, wie viele Markierungen mindestens einen Beleg haben (Abschnitt 5).

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
- **Allgemeine Ereignisse als Hypothese, Standard aus:** Ein zeitliches Zusammentreffen mit
  einem allgemeinen Zeitraum ist keine Erklärung; deshalb nur bestätigte Ereignisse, nur auf
  Wunsch eingeblendet und ausdrücklich als Hypothese beschriftet.
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
- **Fenstergrößen** und Verlässlichkeitsstufen sind vorläufige Setzungen.

## 5. Prüfung und Belege

| Was | Beleg |
|---|---|
| Ereignisfenster | `backend/tests/evidence/test_evidence_window.py`: ohne und mit Lücke, Reihenrand, Jahreswechsel, Parameter |
| Speicher und Hauptquelle | `test_evidence_store.py`: Monatsabfrage, Normalisierung, Speicher, erneuter Abruf, geänderter Suchbegriff, Duplikate, Ausfall, `CONTEXT_LIVE_FETCH=0`, Drosselung |
| EQS und GDELT | `test_evidence_eqs.py`: Umformung, Link, Seiten, Fehler des Endpunkts, Suche der UUID, Ausfall einer Quelle neben der anderen, Schalter |
| Sprache | `test_evidence_language.py` |
| Routen | `test_context_routes.py` (In-Memory-Store, Demo 3): Form, Einzelmonat, Parameter, 404, 400, leere Liste statt 500, Seiten; `test_global_events.py` |
| Skripte | `test_fetch_context_script.py` (Vorabruf, Fortsetzen, Grenze, Schalter), `test_context_coverage.py` (Abdeckung) |
| Zusicherungen | `test_evidence_contracts.py`: Einzelmonat aus konstruierter Erkennung, keine Volltexte, reservierter Typ, Speicher in `.gitignore` |
| Browser (2026-10-08) | SAP SE, Anstieg ab 2024-07: Abschnitt mit Fenster Apr.–Aug. 2024, Belege seitenweise, Typ- und EN-Badges; Telekom mit Overlay zweier vorübergehend bestätigter Ereignisse und Legende „Allgemeines Ereignis, Hypothese“ (danach zurückgesetzt); dunkles Farbschema |
| Lint | eslint für die berührten Frontend-Dateien, ruff (nur Pyflakes-Regeln) für die Backend-Dateien, jeweils ohne Befund |

### Abdeckung für Kontrollpunkt 2 (Stand 2026-10-08, Speicher nach dem Vorabruf)

Vorabruf am 2026-10-08 mit `scripts/fetch_context.py` (Zusammenfassung in `backend/data/calibration/context_prefetch_2026-10-08.json`): 15 geeignete Unternehmen, 19 Niveauwechsel und 9 Einzelmonate, 170 Monate je Unternehmen zusammengefasst; Google News RSS 170 Monate (160 in diesem Lauf abgerufen, 2375 gespeicherte Belege, 0 Fehler), EQS News 143 Monate bei 11 Emittenten (137 abgerufen, 252 Belege, 0 Fehler); 297 Abrufe in 9.8 Minuten bei 2 s Abstand je Quelle. Allgemeine Ereignisse: keine bestätigt, daher 0 Belege vom Typ global. Tabellen aus `scripts/report_context_coverage.py` (`backend/data/calibration/context_coverage_2026-10-08.json`); Unternehmen ohne Markierung (Thyssenkrupp, Open Grid Europe, KIT, TU München) fehlen in den Tabellen.

| Unternehmen | Niveauwechsel mit Beleg | davon news | davon adhoc | davon global | Einzelmonate mit Beleg | davon news | davon adhoc | davon global |
|---|---|---|---|---|---|---|---|---|
| E.ON | 1/1 (100 %) | 1/1 (100 %) | 1/1 (100 %) | 0/1 (0 %) | – | – | – | – |
| RWE | 1/1 (100 %) | 1/1 (100 %) | 1/1 (100 %) | 0/1 (0 %) | 1/1 (100 %) | 1/1 (100 %) | 1/1 (100 %) | 0/1 (0 %) |
| SAP SE | 1/1 (100 %) | 1/1 (100 %) | 1/1 (100 %) | 0/1 (0 %) | 1/1 (100 %) | 1/1 (100 %) | 1/1 (100 %) | 0/1 (0 %) |
| NTT DATA SE | 3/4 (75 %) | 3/4 (75 %) | 0/4 (0 %) | 0/4 (0 %) | – | – | – | – |
| 1&1 AG | 1/1 (100 %) | 1/1 (100 %) | 1/1 (100 %) | 0/1 (0 %) | – | – | – | – |
| Bechtle | 1/1 (100 %) | 1/1 (100 %) | 1/1 (100 %) | 0/1 (0 %) | – | – | – | – |
| Cancom | – | – | – | – | 2/2 (100 %) | 2/2 (100 %) | 2/2 (100 %) | 0/2 (0 %) |
| Carl Zeiss | – | – | – | – | 2/2 (100 %) | 2/2 (100 %) | 1/2 (50 %) | 0/2 (0 %) |
| Compugroup Medical Deutschland | 1/1 (100 %) | 1/1 (100 %) | 1/1 (100 %) | 0/1 (0 %) | – | – | – | – |
| Telekom | 4/4 (100 %) | 4/4 (100 %) | 3/4 (75 %) | 0/4 (0 %) | 3/3 (100 %) | 3/3 (100 %) | 3/3 (100 %) | 0/3 (0 %) |
| Freenet | 5/5 (100 %) | 5/5 (100 %) | 5/5 (100 %) | 0/5 (0 %) | – | – | – | – |
| **Gesamt** | 18/19 (95 %) | 18/19 (95 %) | 14/19 (74 %) | 0/19 (0 %) | 9/9 (100 %) | 9/9 (100 %) | 8/9 (89 %) | 0/9 (0 %) |

| Unternehmen | Markierungen bis 2018 mit Beleg | Markierungen ab 2019 mit Beleg | alle Markierungen mit Beleg |
|---|---|---|---|
| E.ON | – | 1/1 (100 %) | 1/1 (100 %) |
| RWE | – | 2/2 (100 %) | 2/2 (100 %) |
| SAP SE | – | 2/2 (100 %) | 2/2 (100 %) |
| NTT DATA SE | 0/1 (0 %) | 3/3 (100 %) | 3/4 (75 %) |
| 1&1 AG | 1/1 (100 %) | – | 1/1 (100 %) |
| Bechtle | 1/1 (100 %) | – | 1/1 (100 %) |
| Cancom | 2/2 (100 %) | – | 2/2 (100 %) |
| Carl Zeiss | 1/1 (100 %) | 1/1 (100 %) | 2/2 (100 %) |
| Compugroup Medical Deutschland | – | 1/1 (100 %) | 1/1 (100 %) |
| Telekom | 5/5 (100 %) | 2/2 (100 %) | 7/7 (100 %) |
| Freenet | 2/2 (100 %) | 3/3 (100 %) | 5/5 (100 %) |
| **Gesamt** | 12/13 (92 %) | 15/15 (100 %) | 27/28 (96 %) |

Markierungen ohne Beleg (Unternehmen, Art, Monat; fehlende Monate im Speicher):
- NTT DATA SE, niveauwechsel, 2017-11

Ergebnis: 27 von 28 Markierungen haben mindestens einen Beleg; ohne Beleg bleibt der Niveauwechsel von NTT DATA SE im November 2017 (Fenster Aug. 2017 – Dez. 2017), für den Google News keine Meldung zum Suchbegriff „NTT DATA“ liefert und EQS keinen Emittenten kennt. Helfen könnten ein größeres Fenster, ein abweichender Suchbegriff (etwa mit „NTT Data Deutschland“ oder „itelligence“, vom Autor zu prüfen) oder GDELT hinter dem Schalter.

## 6. Offene Punkte

- Vom Autor zu bestätigen: Suchbegriffe und Ausschlussbegriffe (`news_term_confirmed`), die
  EQS-UUIDs (`eqs.confirmed`) und die acht allgemeinen Ereignisse (`confirmed`).
- Fenstergrößen 3 und 1 Monat gegen die Referenzzeiträume prüfen, sobald DZ1 vorliegt.
- Deutsche Fassungen der EQS-Mitteilungen (Detailroute je Meldung) und GDELT bleiben aus.
- Die Fragen zu den Nutzungsbedingungen aus `docs/nutzungsbedingungen.md` bleiben beim Betreuer.
- Rangfolge, thematische Zuordnung und Stimmung der Belege folgen in Inkrement 5.
