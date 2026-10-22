# Stoffsammlung für Kapitel 5 „Gestaltung des Artefaktes“

Stand: 2026-10-22. Arbeitsdatei für die Thesis, kein Teil des Dashboards. Sie ordnet jedem
Abschnitt 5.1 bis 5.5 den Stoff aus `docs/entscheidungen.md` (E-Nummern), der Feature-Doku
(`docs/feature-doku/NN-…`), `docs/datenbasis.md` und dem Code zu. Zahlen tragen den Stand ihrer
Quelle. Die E-Nummern, FA-Nummern und DZ-Kürzel sind Arbeitskürzel des Repositorys; im
Thesis-Text werden sie ausgeschrieben oder in Fußnoten auf den Anhang verwiesen.

Lesehinweis zur DSRM (Tabelle 1 der Thesis): 5.1 bis 5.4 sind „Design and Development“,
5.5 ist „Demonstration“. Jeder Abschnitt sollte am Ende sagen, welches Design-Prinzip
(DP1 bis DP6, Tabelle 7) er umsetzt; die Nachverfolgungstabelle aus 4.7 (unten, Abschnitt 7)
ist der rote Faden.

---

## 0. Vorab: Textstellen, die vor Kapitel 5 angepasst werden müssen

| Stelle | Problem | Korrektur |
|---|---|---|
| 3.2, letzter Absatz | „Limitationen der NLP-Komponenten, die unverändert übernommen werden, ebenso die Prognosekomponente“ | LDA-Modell und Sentiment-Modell bleiben unverändert; der Vorher-Nachher-Vergleich nutzt einen eigenen Schlüsselwort-Weg (E10). Holt bleibt, bekam aber Bauschalter (E28), Erklärungskarte (Doku 11), Backtest und Bandbreite (Doku 16). |
| 4.6, Tabelle 7, DP4 | „Filter nach Status der Bewertenden“ ohne Einschränkung | Der Filter wirkt auf der Anomalieseite (Erkennung, Vergleich, Bewertungsliste), nicht auf Dashboard-Kacheln und Firmenvergleich (E13). In 5.4 so beschreiben. |
| 4.7 | Nachverfolgungstabelle fehlt im PDF | Entwurf unten, Abschnitt 7. |
| 5.1, Abb. 1 und 2 | Stand vor 2026-10-13 | Ergänzen: `user_events` (Route, Service, Tabelle, Migration 007), `macro_events.py` mit Eurostat als externem Dienst, `forecast_service.py`, `AnomalyDetailCards`/`CardPreview`, `UserEvents.jsx`, `ForecastExplanation`, `lib/reportSummary.js`, `lib/comparisonText.js`; `Compare.jsx` ist Z1+Z2; Ereignisarten 13 (12 mit Arbeitgeberbezug + 1 Gruppe ohne), nicht 12; „Supabase nur gelesen“ streichen. Quelldateien der Diagramme liegen nicht im Repository (`docs/architektur` ist leer). |
| 4.4.1 | „(E-2, 02:23)“ | nach Konvention Anhang B: „(E-2, Zeitmarke fehlt; nach Frage 02:23)“; Tippfehler „Studen“. |

---

## 1. Abschnitt 5.1 Architektur und Datengrundlage

### 1.1 Drei-Schichten-Architektur (Fortführung aus Zyklus 1, Kapitel 3)

- **Frontend:** React 19, Vite, React Router, Recharts, Tailwind. Seiten: `/welcome`,
  `/dashboard`, `/compare`, `/anomalies`, `/aktie`. Komponenten unter
  `frontend/src/components/dashboard/`, Hooks unter `frontend/src/hooks/`, Hilfsmodule unter
  `frontend/src/lib/`, PDF-Export unter `frontend/src/utils/pdfExport.js`.
- **Backend:** FastAPI, Python 3.13, uvicorn. Routen unter `backend/routes/` (companies,
  topics, upload, analytics, anomalies, context, market, user_events), Dienste unter
  `backend/services/`, Modelle unter `backend/models/` (changepoint_detector, lda_topic_model,
  sentiment_analyzer). REST-API mit Präfix `/api`, OpenAPI unter `/docs`.
- **Datenbank:** Supabase (PostgreSQL), Tabellen `companies`, `employee`, `candidates`,
  seit Zyklus 2 `user_events` (Migration 007). Zugriff über `database/supabase_client.py`,
  In-Memory-Store für Tests.
- **Dateispeicher außerhalb der Datenbank** (alle in `.gitignore`, Begründung E18 „Abweichung
  von der Roadmap“): Belegspeicher `backend/data/context/<id>/<quelle>/<YYYY-MM>.json`,
  Kurs-Zwischenspeicher `backend/data/market/<ticker>.json`, Eurostat-Reihen
  `backend/data/macro/eurostat_de.json`.
- **Versionierte Metadaten:** `backend/data/company_metadata.json` (Ticker, ISIN, Branche laut
  Kununu, Vergleichsgruppe, Suchbegriff und Ausschlussbegriffe für Google News, EQS-UUID,
  `title_words`, Plattformwert für den Abgleich), eingespielt mit
  `seed_company_metadata.py` (E6, Nachträge 2026-10-12 und 2026-10-22).
- **Reproduzierbarkeit:** Docker-Stack, `.dockerignore`, Abhängigkeiten `ruptures` und
  `yfinance` (E8). Kanonisches Repository E1.
- **Bauschalter** in `frontend/src/config.js`: `VITE_SHOW_FORECAST` (E28),
  `VITE_SHOW_FINANCE_EXTRAS` (E16, Variante A/B in `docs/evaluationsinstanz.md`),
  `VITE_SHOW_OUTLIER_MONTHS` (Doku 03, Entscheidung 1a offen).

### 1.2 Datengrundlage

- **Unternehmen:** 26 reale Kununu-Profile (13 aus Zyklus 1, 13 TecDAX-Unternehmen, Import
  2026-10-02) plus Demo 1 bis 3, die in keine Auswertung eingehen (E2). Beide Quellen
  (`employee`, `candidates`) gehen in die Erkennung ein.
- **Dichte:** `docs/datenbasis.md` (automatisch erzeugt, Stand 2026-10-03). Ein Monat gilt als
  bewertet ab 5 Bewertungen; ein Unternehmen ist für die Erkennung geeignet ab 12 bewerteten
  Monaten (E4). Stand 2026-10-02: 15 von 26 Unternehmen in der Mitarbeiterquelle, 5 von 26 in
  der Bewerberquelle. Die 15 geeigneten Reihen: Thyssenkrupp, Open Grid Europe, E.ON, RWE, KIT,
  TU München, SAP SE, NTT DATA SE, 1&1 AG, Bechtle, Cancom, Carl Zeiss, Compugroup Medical,
  Telekom, Freenet.
- **Offen:** Am 2026-10-18 wurden 28 exakte Duplikate aus der gehosteten Datenbank entfernt
  (`remove_duplicates.py`, Doku 16). `datenbasis.md` ist älter; vor dem Schreiben
  `backend/scripts/report_data_density.py` erneut laufen lassen und die Zahlen in 5.1 und 5.5
  daraus nehmen. Ein E-Eintrag zur Duplikatentfernung fehlt noch.
- **Börsennotierung:** 17 der 26 Unternehmen mit Ticker, 9 ohne (E15); Sonderfälle Compugroup
  (2025 von der Börse genommen) und NTT DATA SE (Mutterkonzern hinterlegt), vom Autor zu
  bestätigen (E6).
- **Erkennungsreihe:** je Unternehmen, Quelle und Kalendermonat das arithmetische Mittel der
  Spalte `durchschnittsbewertung` (Gesamtnote je Bewertung), Einzeldimensionen analog aus den
  `sternebewertung_*`-Spalten; eine Implementierung in `rating_series_service.py` (E3).
  Begründung: identisch mit der Zeitleiste, die die Nutzenden sehen.
- **Ø Score:** seit 2026-10-09 dasselbe Mittel der Gesamtnote, ungewichtet, mit n; das
  Kategorienmittel aus Zyklus 1 heißt jetzt so und steht darunter (E26, D1). Hinweistext aus
  `frontend/src/lib/scoreText.js` (Kununu gewichtet anders, Wert kann abweichen).
- **Bewertendengruppe:** Quelle plus normalisierter Status (`angestellt`, `ex-angestellt`,
  `unbekannt`; Bewerbende `eingestellt`, `angebot-abgelehnt`, `abgelehnt`, `zurueckgestellt`,
  `unbekannt`); Rohwerte in der Datenbank uneinheitlich (E13).
- **Datenstand:** `GET /api/companies/{id}/data-status` liefert je Quelle Anzahl, erste und
  jüngste Bewertung, bewertete Monate, Eignung, drei Zeitstempel, Stand von Kurs- und
  Belegspeicher und den Plattformabgleich (E25). Der Abgleich ist ein manueller Eintrag des
  Autors in der Metadatei, kein Abruf. Das Abrufdatum bei Kununu ist nicht gespeichert.

Design-Prinzipien in 5.1: DP5 (Datenbasis, Datenstand) und die Grundlage für DP4
(Bewertendengruppe, Branche).

---

## 2. Abschnitt 5.2 Anomalie-Erkennungsansatz

### 2.1 Verfahren (E9, `backend/models/changepoint_detector.py`, `backend/services/anomaly_service.py`)

- **PELT** (Killick, Fearnhead & Eckley 2012) aus `ruptures`, Kostenfunktion `l2`
  (Mittelwertwechsel), Mindestsegmentlänge `min_size = 3` bewertete Monate.
- **Strafterm** seit 2026-10-04 skaliert: `penalty = 2 · σ² · ln n`, `n` = Zahl der bewerteten
  Monate, `σ = 1,4826 · MAD(diff(values)) / √2`, Untergrenze 0,05 Sterne. Begründung: BIC für
  Mittelwertwechsel bei bekannter Varianz (Yao 1988; Fearnhead & Fryzlewicz 2024, Abschn. 3.3,
  3.4, 7, 9; R-Paket `changepoint`); Belege in `docs/referenzzeitraeume-literatur.md`,
  Abschnitt 2.5. Vorher fester Wert 0,5, der verrauschte Reihen übersegmentierte (66
  Markierungen bei 15 Unternehmen, mit Faktor 2 noch 19).
- **Mindestbetrag** `min_delta = 0,3` Sterne; **Schweregrad** „deutlich“ ab 0,5 Sternen (Richtwert
  des Annotationsprotokolls), sonst „mäßig“. `min_size`, `min_delta`, Untergrenze σ: Setzungen.
- **Fallback** für Reihen unter 6 Werten: Differenz zweier 3-Monats-Fenster, Schwelle 0,3;
  greift im Dashboard nicht (geeignete Reihen haben mindestens 12 Monate).
- **Je Veränderung:** Monat (erster bewerteter Monat auf dem neuen Niveau), Richtung, Delta,
  Mittel davor/danach, n davor/danach, Abschnittsgrenzen, Lücke davor (`gap_months`),
  Kennzeichen `month_near_previous_level`, Verfahren und Parameter inklusive `penalty_mode`.
- **Austauschbarkeit:** Protocol `ChangePointDetector`; ein zweites Verfahren (Günnemann et al.
  2014) ist vorgesehen, aber kein Drop-in: Günnemann modelliert kurze Anomalieintervalle um ein
  glatt laufendes Grundverhalten, nicht dauerhafte Niveauwechsel.
- **Bezug zu 2.2:** Die Thesis nennt Truongs Strafterm `σ² log T |𝒯|`; das Artefakt nutzt den
  Faktor 2 je Wechsel. In 5.2 den Faktor mit Yao / Fearnhead & Fryzlewicz begründen, PELT über
  Exaktheit begründen, nicht über Laufzeit (Killick S. 1594: ein log-n-Strafterm liegt außerhalb
  des Linearzeit-Theorems).

### 2.2 Auffällige Einzelmonate (E14, Doku 03)

- Getrennte zweite Markierung (Raute). Ein bewerteter Monat wird gemeldet, wenn er vom Median
  der bis zu 3 bewerteten Monate davor und danach um mindestens `T = max(3σ, 0,5 Sterne)` in
  dieselbe Richtung abweicht und seine Nachbarn das nicht tun. Ergebnis 2026-10-04: 9 Einzelmonate
  in den 15 Reihen (Telekom 2022-12 mit −1,41 bei 11 Bewertungen als Anlass).
- **Befund E30:** ohne eingesetzte Veränderung entstehen 5,4 bis 8,9 Einzelmonate je
  Simulationslauf, auf den echten Reihen 9. Einzelmonate liegen auf Zufallsniveau; seit
  2026-10-13 überall als „ungeprüft“ gekennzeichnet, per `VITE_SHOW_OUTLIER_MONTHS` ausblendbar.
  Entscheidung für die Interviews offen (Evaluationsinstanz 1a; Empfehlung: aus).

### 2.3 Rollierende Schnitte (E24, `rolling_average_service.py`)

- 12- und 24-Monats-Schnitt der Gesamtnote bis zum Anker (letzter voller Kalendermonat mit
  Bewertungen, nicht heute); Differenz 12 minus 24, bis 0,05 gleichauf; kleine Basis unter 10
  Bewertungen je Fenster. Setzt H4.9 um (DP1).

### 2.4 Ergebnisse auf den Daten (für 5.2 oder 5.5)

- Mit den Standardparametern: 19 Niveauwechsel und 9 Einzelmonate in den 15 geeigneten Reihen
  (Mitarbeitende, Gesamtbewertung). Je Unternehmen: Freenet 5, Telekom 4, NTT DATA 4, je 1 bei
  SAP, 1&1, Bechtle, Compugroup, E.ON, RWE; keine bei Cancom, Thyssenkrupp, Carl Zeiss, KIT,
  TU München, Open Grid Europe (E9, Stand 2026-10-04; Parameterübersicht
  `backend/data/calibration/anomaly_params_scaled_*.csv`).
- Strafterm je Reihe von 0,42 (Open Grid Europe) bis 2,39 (Cancom).

### 2.5 Was in 5.2 nur angekündigt, in Kapitel 6 ausgeführt wird

- **DZ1 gegen Referenzzeiträume** (E5, E9 Aktualisierung 2026-10-10): 20 Zeiträume in 8 Reihen,
  F1 0,43 (Precision 0,47, Recall 0,40), regelkonform 0,41; Bootstrap über Reihen [0,27; 0,56];
  Zufall 0,04, naive Regel 0,22 (E9 Nachtrag 2026-10-13). Grenzen: ein Annotator,
  agentengestützt, nicht blind.
- **Semi-synthetische Prüfung** (E30): Recall bei 0,5 Sternen 41 bis 58 %, bei 0,75 Sternen 71
  bis 81 %, bei 1,0 Sternen 87 bis 92 %; 0,25 bis 0,35 Markierungen je Reihe ohne Wechsel.
- **Lesart** (E31, Entscheidung des Autors offen): DZ1 teilweise erreicht, nur für die
  Gesamtbewertung der Mitarbeitenden; Einzelmonate nicht; Einzeldimensionen, Bewerbende und
  Statusgruppen nicht geprüft (Hinweis „ungeprüft“ im Dashboard, E27 Nachtrag).
- **Grenzen des Verfahrens** (E9 Nachtrag 2026-10-11): Autokorrelation der Monatsmittel lässt σ
  zu klein ausfallen; Monatsmittel aus unterschiedlich vielen Bewertungen werden gleich
  gewichtet. Beides gehört in 7.2.

Design-Prinzip in 5.2: DP1.

---

## 3. Abschnitt 5.3 Kontextsammlung und Erklärungsgenerierung

Reihenfolge, die der Verarbeitung folgt: Fenster, Vorher-Nachher-Vergleich, externe Belege,
allgemeine Ereignisse, eigene Ereignisse, Rangfolge zu Erklärungsansätzen, Auswertung.

### 3.1 Vergleichsfenster und Vorher-Nachher-Vergleich (E12, E10, E11, E17, Doku 02, 06)

- **Fenster:** 6 Kalendermonate vor dem Wechsel und 6 ab dem Wechselmonat, begrenzt durch die
  Nachbarabschnitte; alle Bewertungen dieser Monate, auch aus dünnen Monaten (E12). Kleine Basis:
  Fenster unter 10 Bewertungen oder Thema unter 5 Nennungen. Freie Auswahl gegen gleich lange
  Monate davor, mindestens 6 (E17).
- **Themen:** Schlüsselwort-Themen mit den Namen der Kununu-Kategorien (13 Mitarbeitende, 10
  Bewerbende), ein Thema gilt als genannt bei Treffer eines regulären Ausdrucks in einem
  Textfeld, seit 2026-10-13 auch in den Kommentaren zu den 13 Kategorien (E10). **Nicht** das
  LDA-Modell aus Zyklus 1. Begründung aus den Anforderungen: Nachvollziehbarkeit (DP5, H4.10),
  Anschluss an die Sternekategorie (H2.6), stabil zwischen zwei Fenstern. Literatur:
  Wörterbuchverfahren bei Campion und Campion (Kapitel 2.3). Grenzen: nicht validiert, nur
  Deutsch, mehrdeutige Wörter. Für 7.2 vormerken; eine Handstichprobe (etwa 100 Bewertungen)
  würde eine Trefferquote je Thema liefern.
- **Stimmung:** `SentimentAnalyzer` aus Zyklus 1 im Modus `transformer` (German Sentiment BERT
  mit Lexikonabgleich), Rückfall Lexikon; höchstens 300 Bewertungen mit Freitext je Fenster;
  Anteile positiv/neutral/negativ und mittlere Polarität (E11).
- **Bewertungen ohne Freitext:** seit 2026-10-22 je Fenster `n_with_text` und `n_without_text`,
  in Fensterköpfen und Vorschau-Karte sichtbar (Doku 02 Nachtrag). Setzt MR2 „erkennbar machen,
  wo Freitexte fehlen“ um.
- **Grenze E12:** Fenster nach Bewertungen gewichtet, Erkennung nach Monatsmitteln; Beispiel SAP
  SE ab 2024-07 (Ø Monatsmittel 3,07 → 3,74, Ø je Bewertung 3,79 → 3,65 wegen 174 Bewertungen im
  März 2024).
- **Bewertungsliste:** Einzelbewertungen des Fensters mit Themenmarken, Themenfilter und
  Datumssortierung (Doku 17); Zitate ohne Stellenfelder (NFA-07, Doku 10).

### 3.2 Externe Belege (E7, E18, E19, Doku 07)

- **Quellen:** Google News RSS als Hauptquelle (eine Abfrage je Unternehmen und Kalendermonat mit
  `after:`/`before:`, Suchbegriff und Ausschlussbegriffe in der Metadatei), EQS News für
  börsennotierte Unternehmen (companyUUID je Emittent), GDELT hinter `CONTEXT_GDELT=1` und aus;
  yfinance nicht für Nachrichten. Spike vom 2026-10-02 in `docs/quellen-spike.md` (Thyssenkrupp
  04/2023: 28 Treffer inklusive Vorstandswechsel). Nutzungsbedingungen in
  `docs/nutzungsbedingungen.md` (Entscheidung des Autors 2026-10-08: vertretbar im Rahmen der
  Arbeit).
- **Ereignisfenster:** 3 Monate vor dem Beginn des Übergangs bis 1 Monat nach dem markierten
  Monat; bei Lücke beginnt das Fenster vor der Lücke. Begründung: Reaktion innerhalb des
  Folgequartals (Green et al. 2019) und der Ereignisfenster-Gedanke aus Kapitel 2.4 (MacKinlay)
  mit umgekehrter Blickrichtung.
- **Belegspeicher:** je Unternehmen, Quelle und Monat als Datei; nur Titel, Herausgeber, Link,
  Datum, Quelle, Typ, Verlässlichkeit, Sprache; keine Volltexte. Abgeschlossene Monate werden
  nicht erneut abgerufen; Vorabruf `fetch_context.py`; `CONTEXT_LIVE_FETCH=0` für den Betrieb.
- **Quellenarten und Verlässlichkeit:** `adhoc` (EQS) hoch, `news` mittel, `global` Hypothese;
  Sprache je Titel geschätzt, „EN“-Kennzeichen (E19). Stufen beschreiben die Art der Quelle, nicht
  den Wahrheitsgehalt.
- **Fester Hinweis:** „Belege sind zeitlich nahe Meldungen aus externen Quellen. Sie sind keine
  Aussage über Ursachen; interne Auslöser sind von außen nicht sichtbar.“ Das ist H3.7 und H4.5
  aus den Interviews in Programmtext.
- **Abdeckung:** rund 14 Meldungen je Unternehmensmonat; alle 28 Markierungsfenster und alle
  Vergleichsfenster liegen vollständig im Speicher (E23).

### 3.3 Allgemeine Ereignisse (E20 abgelöst durch E29, Doku 07)

- Seit 2026-10-13 automatisch aus zwei Eurostat-Monatsreihen für Deutschland: Konjunktureinbruch
  (ESI mindestens 10 Punkte unter dem Wert drei Monate davor) und Inflationsschub (HVPI
  mindestens 2 Prozentpunkte über dem Wert drei Monate davor und mindestens 5 %). Höchstens 6
  Monate je Ereignis. Ergebnis: fünf Ereignisse (2008/09, 2020, Nov. 2021, Apr./Mai 2022,
  Sept. bis Nov. 2022). Als Overlay im Verlauf, seit 2026-10-17 anklickbar und als Hypothese bei
  den Erklärungsansätzen gelistet; kein Eingang in die Rangfolge. Grenzen: Schwellen Setzungen,
  nur gesamtwirtschaftliche Spur (Atom-Moratorium, Kriegsbeginn fehlen als eigene Ereignisse).
- Vorher (E20): acht von Hand vorgeschlagene Ereignisse, nur bestätigte sichtbar; Datei gelöscht.

### 3.4 Eigene Ereignisse (E32, Doku 15)

- Tabelle `user_events` je Unternehmen (Migration 007), Routen `GET/POST/PUT/DELETE
  /api/companies/{id}/events`; Formular auf der Detailseite, nummerierte violette Marken,
  Reiter „Eigene Ereignisse“, Klick wählt den Zeitraum. Seit 2026-10-22 bei den
  Erklärungsansätzen als Gruppe „Eigenes Ereignis im Ereignisfenster · möglicher Zusammenhang“,
  in Vorschau-Karte, PDF und Kurzbericht. Kein Eingang in Erkennung, Rangfolge oder Belegzählung.
- Setzt MR3 „internes Ereigniswissen der Nutzenden“ um (H2.9, H3.5). Grenzen: keine Anmeldung,
  keine Historie. Migration 007 in der gehosteten Datenbank: Stand prüfen.

### 3.5 Erklärungsansätze: Signale, Stufen, Auswahl (E21, E22, E33, Doku 08, 18)

- **Ereignisarten** (E22): 12 mit Arbeitgeberbezug (Personalabbau, Führungswechsel, Übernahme,
  Tarif/Streik, Standort, Vergütung, Arbeitsmodell, Rechtsstreit/Skandal, Auszeichnung,
  Krise/Geschäftslage, Einstellungen/Ausbildung, Kultur/Diversität) mit Schlüsselwörtern deutsch
  und englisch und zugeordneten Themen aus E10; eine Gruppe ohne Arbeitgeberbezug (Börse, Kursziel,
  Sport, Produkt, EQS-Kapitalmarktkategorien). Datei `backend/data/event_categories.json`.
- **Signale je Beleg** (E21): `term_match` (kennzeichnende Begriffe der Bewertungen im Titel;
  Begriff ab 3 Bewertungen und 3 % im Fenster danach mit mindestens doppeltem Anteil),
  `category_match` (Ereignisart erkannt 0,5; plus Themenverschiebung ab 5 Prozentpunkten 1),
  `time_match` (1 im Monat vor dem Übergang und im Übergang, linear abfallend zum Fensterrand).
- **Stufen, Fassung 2** (E21 Iteration 2): hoch bei `term_match ≥ 0,5` und Ereignisart erkannt
  und `time_match ≥ 1`; mittel und niedrig nach festen Regeln; zeitliche Nähe allein genügt nie.
  Feste Regeln statt gewichteter Summe, damit die Oberfläche die Einstufung begründen kann.
  Regeln eingefroren in `backend/tests/explanations/test_frozen_rules.py`.
- **Strenge Auswahl** (E33, seit 2026-10-18) vor Bündelung und Rangfolge: Unternehmen im Titel
  genannt, Arbeitgeberbezug, thematische Korrespondenz (`term_match ≥ 0,5` oder
  `category_match ≥ 1`), zeitliche Nähe `time_match ≥ 0,5`. Ausgeschlossene bleiben in der
  Belegliste mit der verletzten Regel. Begründung: Meldungen ohne Nennung lassen sich nicht als
  Zusammenhang lesen; Stufe niedrig war in Vergleichsfenstern so häufig wie bei Markierungen.
- **Bündelung:** gleiche Ereignisart, höchstens 3 Tage Abstand, Jaccard der Titelbegriffe ≥ 0,5;
  fasst selten zusammen (362 Belege, 353 Bündel). Höchstens fünf Einträge.
- **Sprache der Begründung:** Textbausteine nennen Anzahl, Ereignisart, Lage im Fenster, Begriffe
  mit Zählungen, Themenverschiebung; ein Test sichert, dass kein Baustein „Ursache“, „Auslöser“,
  „Grund“, „weil“ oder „führte“ enthält. Fester Hinweis: „Die Einstufung beruht auf Titeln und
  Wortbezügen. Sie zeigt mögliche Zusammenhänge, keine Ursachen.“ Das ist DP3 im Programmtext.
- **Grenzen:** nur Titel, deutsche Begriffe treffen englische EQS-Titel kaum, Stimmungsmodell an
  Bewertungen geprüft, nicht an Schlagzeilen (nur Vermerk, ohne Einfluss auf die Stufe).

### 3.6 Kurs und Kennzahlen (E15, E16, Doku 04, 05)

- Rolle: Einordnung, keine Erklärung; keine Korrelation, kein Vergleichswert; fester Hinweis.
  Quelle Yahoo Finance über `yfinance`, bereinigte Monatsschlusskurse, Zwischenspeicher je Ticker;
  Kennzahlen Marktkapitalisierung, Mitarbeitende, Umsatz je Geschäftsjahr. Eigene Seite `/aktie`;
  Kurs auf der Anomalieseite per Kästchen einblendbar, Standard aus. Zusatzkarten
  (Analystenempfehlungen, Nettoergebnis, Meldungen) sind Wunsch des Autors außerhalb der
  Anforderungen und per `VITE_SHOW_FINANCE_EXTRAS=false` ausblendbar (Variante B für die
  Interviews). Setzt H4.6 um.

### 3.7 Was in 5.3 nur angekündigt, in Kapitel 6 ausgeführt wird (DZ2, E23)

- Abdeckungsquote nach NFA-05 (Anteil der Markierungsfenster mit mindestens einem
  Erklärungsansatz): Fassung 2 vom 2026-10-13: 23/28 (82 %) gegen 57/72 Vergleichsfenster
  (79 %); mindestens mittel 15/28 (54 %) gegen 32/72 (44 %). Mit strenger Auswahl 2026-10-18:
  14/28 (50 %) gegen 23/72 (32 %); Niveauwechsel 63 %, Einzelmonate 22 %. Beschreibend, ohne
  Signifikanzaussage; die Quote unterscheidet Markierungs- und Vergleichsfenster nicht
  erkennbar. Zusätzlich eine blinde Passungsbewertung (184 Urteile, kein trennendes Maß;
  `docs/erklaerungsansaetze-passung.md`).

Design-Prinzipien in 5.3: DP2 (Vergleich), DP3 (Belege, eigene Ereignisse, Kausalitätsvorbehalt,
Kurs zur Einordnung).

---

## 4. Abschnitt 5.4 Dashboard

Je Design-Prinzip ein Absatz mit der Komponente, dem sichtbaren Element und dem festen Hinweis.
Regel des Autors: keine Arbeitskürzel (E, FA, DZ, TF) in Oberfläche, PDF oder Backend-Texten.

| DP | Sichtbares Element | Komponente / Datei | Quelle |
|---|---|---|---|
| DP1 Verortete Veränderungserkennung | Stufen im Monatsverlauf (Höhe = Ausmaß, Form = Richtung, Strichstärke = Schweregrad), Rauten für Einzelmonate, Kachel „12- vs. 24-Monats-Schnitt“, Dimensionwahl, Zähler | `AnomalyCard.jsx`, `TimelineCard`, `KPIGrid.jsx` | Doku 01, 03; E9, E14, E24 |
| DP2 Textgestützte Kontextualisierung | Vergleich davor/danach mit Themenanteilen, Stimmung, n mit/ohne Freitext; Bewertungsliste mit Themenmarken; freier Drill-down | `AnomalyComparison.jsx`, `PeriodReviews.jsx`, `DrilldownPicker.jsx`, `lib/comparisonText.js` | Doku 02, 06, 17; E10 bis E12, E17 |
| DP3 Belegte Erklärungsansätze | Karte „Mögliche Zusammenhänge“ mit Stufe, Begründung, Signalmarken, Ausschlussgründen; Belegliste; allgemeine Ereignisse als Overlay und Hypothese; eigene Ereignisse; Kurs als Einordnung | `ExplanationPanel.jsx`, `EvidenceSection.jsx`, `UserEvents.jsx`, `MarketContext.jsx`, `FinanceCards.jsx` | Doku 07, 08, 15, 18, 04; E18 bis E23, E29, E32, E33 |
| DP4 Gruppenbezogene Betrachtung | Statusfilter auf der Anomalieseite; Firmenvergleich mit Branche unter dem Namen und Vorschlag „gleiche Branche“ | `Anomalies.jsx`, `Compare.jsx`, `CompanySearchSelect.jsx`, `lib/companies.js` | Doku 19; E13, E6 |
| DP5 Rechentransparenz | Datenstand-Leiste, Kennzeichen Sternebewertung/Freitextanalyse/Externe Meldungen/Marktdaten, n an jeder Kennzahl, Warnung „kleine Basis“, Berechnungshinweis Ø Score, Hinweis „ungeprüft“, Prognose-Erklärung | `DataStatusBar.jsx`, `DataBasis.jsx`, `lib/dataBasis.js`, `lib/scoreText.js`, `ScopeHint`, `ForecastExplanation.jsx` | Doku 10, 11, 12; E25 bis E28 |
| DP6 Weitergabefähige Aufbereitung | PDF-Export aller Elemente, Seite „Kurzbericht“ (Lage, jüngste Veränderungen mit Folge, „Was gut läuft“ / „Was verbessert werden sollte“ nach festen Regeln), letzte Seite „Technische Hinweise“ | `utils/pdfExport.js`, `lib/reportSummary.js` | Doku 09, 14, 16 |

Weitere Punkte für 5.4:

- **Vorschau-Karten** auf der Anomalieseite: Vergleich, Bewertungen, Erklärungsansätze, Externe
  Berichte als vier Karten mit je einer Kennzahl, Klick öffnet den Dialog (Doku 13).
- **Seitenstruktur:** `/welcome` Auswahl, `/dashboard` Kennzahlen, Verlauf, Themen, PDF,
  `/anomalies` Verlauf, Drill-down, Belege, Ansätze, `/compare`, `/aktie`.
- **Statusfilter:** gilt für Erkennung, Vergleich und Bewertungsliste der Anomalieseite; jede
  Kombination aus Quelle, Dimension und Status ist eine eigene Reihe. Dashboard-Kacheln und
  Firmenvergleich ohne Status. Grenze für H2.3: Bereich und Standort fehlen in den Daten.
- **Prognose:** Holt aus Zyklus 1 bleibt im Zeitverlauf, Evaluationsinstanz blendet sie aus
  (E28); Erklärungskarte mit geglättetem Niveau (Doku 11); Backtest zeigt Holt schlechter als
  naive Baselines, Autor behält Holt (Doku 16). In 5.4 kurz, in 7.2 als Grenze.
- **Kurzbericht:** Formulierung „sollte“ statt „muss“, weil die Daten keinen Bedarf beweisen
  (Doku 14).
- **Kleine Basis:** feste Schwellen 5 je Monat, 10 je Fenster; keine Unsicherheitsangabe (E27).

---

## 5. Abschnitt 5.5 Demonstration am Anwendungsfall

### 5.1 Auswahl des Falls

Kandidaten aus den 15 geeigneten Reihen (Mitarbeitende, Gesamtbewertung):

| Unternehmen | Markierungen | Argumente | Einwände |
|---|---|---|---|
| Telekom | 4 Niveauwechsel, Einzelmonate 2022-12 (−1,41), 2015-05, 2017-05 | längste Reihe (165 bewertete Monate), F1 0,57, Recall in der Simulation 88 %, börsennotiert (EQS und Google News), Einzelmonat als Beispiel für die Abgrenzung | Einzelmonate „ungeprüft“; Begriffe „deutschen“ als Namensvorsilbe waren ein Problem (E21) |
| SAP SE | 1 Anstieg ab 2024-07, Einzelmonat 2024-03 (+1,23, 174 Bewertungen) | F1 1,00, zeigt die Grenze E12 (Fenster nach Bewertungen gewichtet), viele Belege | nur ein Wechsel; vor E33 33 Bündel „hoch“ unter 362 Belegen (Beispiel für die strenge Auswahl) |
| Freenet | 5 Niveauwechsel | meiste Markierungen, F1 0,50 | Referenz hatte die Obergrenze von 3 Zeiträumen erreicht |
| NTT DATA SE | 4 Niveauwechsel | Zweifelsfall 2024-03 (−0,50) zeigt den Richtwert | Konzernmutter als Ticker (E6), Recall in der Simulation nur 23 % |
| Thyssenkrupp | keine Markierung | Spike-Fall 04/2023 Vorstandswechsel mit 28 Treffern | nur als freier Drill-down (E17) zeigbar |

Empfehlung: ein Hauptfall mit Niveauwechsel und Belegen (Telekom oder SAP SE) plus ein kurzer
Gegenfall ohne Markierung über den freien Drill-down (Thyssenkrupp), um zu zeigen, dass das
Werkzeug nicht an die Erkennung gebunden ist.

### 5.2 Ablauf der Demonstration (eine Spur durch alle DPs)

1. `/dashboard`: Datenstand-Leiste, Kacheln Ø Score und 12/24-Monats-Schnitt mit n (DP5, DP1).
2. Anomalien-Karte im Verlauf: Stufe mit Zeitpunkt, Richtung, Ausmaß; Hinweis „ungeprüft“ bei
   Wechsel der Dimension (DP1, DP5).
3. `/anomalies`: Klick auf die Stufe, Vergleich davor/danach mit Themen, Stimmung, n ohne
   Freitext (DP2); Bewertungsliste mit Themenfilter.
4. Karte „Mögliche Zusammenhänge“: Stufe, Begründung, Ausschlüsse; Belegliste mit Quellenart und
   „EN“; allgemeines Ereignis als Hypothese; eigenes Ereignis eintragen und als möglicher
   Zusammenhang sehen (DP3).
5. Statusfilter umstellen, Reihe als „ungeprüft“ gekennzeichnet (DP4, DP5).
6. `/compare`: Vorschlag „gleiche Branche“ (DP4).
7. `/aktie`: Kurs mit Hinweis „Einordnung, keine Erklärung“ (DP3).
8. PDF-Export mit Kurzbericht und Technischen Hinweisen (DP6).

### 5.3 Rahmen

- Evaluationsinstanz: `VITE_SHOW_FORECAST=false`, Variante B (`VITE_SHOW_FINANCE_EXTRAS=false`),
  `VITE_SHOW_OUTLIER_MONTHS` nach Entscheidung 1a; `CONTEXT_LIVE_FETCH=0`, `MARKET_LIVE_FETCH=0`
  mit vorab gefülltem Speicher; Abnahme mit `backend/scripts/check_evaluation_instance.py`
  (`docs/abnahme-inkrement-6.md`).
- Screenshots aus derselben Instanz, helles Theme (PDF-Export dort geprüft).
- Zahlen im Text aus dem Datenstand der Instanz, nicht aus älteren Dokus.

---

## 6. Offene Entscheidungen des Autors, die Kapitel 5 berühren

| Nr. | Entscheidung | Wo |
|---|---|---|
| 1 | Einzelmonate in den Interviews zeigen oder ausblenden | `docs/evaluationsinstanz.md` 1a, Doku 03 |
| 2 | Lesart von DZ1 (teilweise erreicht?) | E31 |
| 3 | Abdeckungsquote NFA-05 mit strenger Auswahl (50 %) als erfüllt werten? | E33, Doku 18 |
| 4 | `title_words` „CGM“ für Compugroup bestätigen | E33 |
| 5 | Sonderfälle Compugroup (delistet) und NTT DATA (Mutterkonzern) bestätigen | E6 |
| 6 | Migration 007 in der gehosteten Datenbank ausgeführt? | E32 |
| 7 | E-Eintrag zur Duplikatentfernung vom 2026-10-18 anlegen, `datenbasis.md` neu erzeugen | Doku 16 |
| 8 | Holt behalten trotz Backtest (bereits entschieden: ja), in 7.2 begründen | Doku 16 |
| 9 | Handstichprobe für Schlüsselwort-Themen (optional) | E10 |

---

## 7. Entwurf der Nachverfolgungstabelle (Abschnitt 4.7)

| MR | DP | Komponente des Artefakts | Prüfkriterium in Kapitel 6 |
|---|---|---|---|
| MR1 Veränderungen erkennen und verorten | DP1 | Erkennung (PELT, E9), Einzelmonate (E14), rollierende Schnitte (E24), Anomalien-Karte | DZ1: F1 gegen Referenzzeiträume, Recall in der Simulation (E30); DZ3: Nachvollziehbarkeit der Markierung |
| MR2 Freitexte gegenüberstellen, fehlende Freitexte ausweisen | DP2 | Vergleichsfenster (E12), Schlüsselwort-Themen (E10), Stimmung (E11), n ohne Freitext, Bewertungsliste | DZ3: Verständlichkeit des Vergleichs; Grenze: keine Validierung der Themen |
| MR3 Ereignisse als möglicher Zusammenhang, extern und intern | DP3 | Belegspeicher und Quellen (E18, E19), Rangfolge und Auswahl (E21, E33), allgemeine Ereignisse (E29), eigene Ereignisse (E32), Kurs als Einordnung (E15) | DZ2: Abdeckungsquote und Vergleichsfenster (E23); DZ3: Plausibilität ohne Kausalanspruch |
| MR4 Bewertendengruppen und Vergleichsorganisationen | DP4 | Statusfilter (E13), Firmenvergleich mit Branche (E6, Doku 19) | DZ3: Nutzen des Filters und des Branchenvorschlags; Datengrenze Bereich/Standort |
| MR5 Berechnung, Datenbasis, Datenstand nachvollziehbar | DP5 | Datenstand (E25), Ø Score mit Hinweis (E26), Kennzeichen und n (E27), „ungeprüft“ (E27 Nachtrag) | DZ3: Vertrauen in die Zahlen; Grenze: Plattformabgleich manuell |
| MR6 Weitergabe an Leitung und Führungskräfte | DP6 | PDF-Export (Doku 09), Kurzbericht (Doku 14), Technische Hinweise | DZ3: Eignung des Exports für die Weitergabe |
