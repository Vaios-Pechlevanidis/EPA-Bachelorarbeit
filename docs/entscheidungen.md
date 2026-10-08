# Entscheidungen Zyklus 2 – Inkrement 0 „Fundament“, Inkrement 1 „Anomalien im Verlauf“, Inkrement 2 „Drill-down und Vorher-Nachher-Vergleich“ und Inkrement 3 „Aktienkurs und Kennzahlen“

Stand: 2026-10-08 (E1–E8 vom 2026-10-02, E5 aktualisiert und E9 neu am 2026-10-03, E9 aktualisiert und E10–E16 neu am 2026-10-04, E17 neu am 2026-10-05; E5, E13, E15 und E16 aktualisiert am 2026-10-08 nach den Entscheidungen D1–D3 in `docs/offene-punkte-vor-inkrement-4.md`; E7 fortgeschrieben und E18–E20 neu am 2026-10-08 mit Inkrement 4 „Externe Belege im Ereignisfenster“). Jede Entscheidung nennt Kontext, Entscheidung, Begründung und Status.
Status „vorläufig“ heißt: gilt, bis die manuellen Annotationen (DZ1) eine belastbare
Kalibrierung erlauben; dann wird der Eintrag mit Beleg aktualisiert.

## E1 – Kanonisches Repository

- **Kontext:** Neben diesem Repository existierte eine testweise angelegte Kopie
  (`Vaios-Pechlevanidis/Bachelorarbeit`), die in dieselbe gehostete Supabase-Datenbank
  geschrieben hatte (Tabellen `anomalies`, `context_items`, `stock_prices`, `explanations`,
  `financial_kpis`, `analyst_recommendations`, Spalten `companies.ticker/isin`).
- **Entscheidung:** `EPA-Bachelorarbeit` ist das einzige Repository der Arbeit. Zyklus 2 wird
  hier vollständig neu aufgebaut. Die fremden Datenbankobjekte wurden am 2026-10-02 per
  SQL-Editor entfernt; die Datenbank entspricht wieder genau den Migrationen 001–005.
- **Status:** endgültig.

## E2 – Datenbasis und Untersuchungsunternehmen

- **Kontext:** Die Datenbank enthält 26 reale Kununu-Profile (13 aus Zyklus 1, 13 TecDAX-
  Unternehmen, importiert am 2026-10-02) sowie die synthetischen Firmen Demo 1–3.
- **Entscheidung:** Alle 26 realen Unternehmen sind Untersuchungsunternehmen. Demo 1–3
  dienen nur der Entwicklung und gehen in keine Auswertung ein. Beide Quellen, `employee`
  und `candidates`, gehen in die Erkennung ein.
- **Begründung:** Breite Fallbasis für die Experteninterviews (DZ3); die Kandidatenquelle ist
  bei mehreren Unternehmen dünn, liefert aber bei Thyssengas, Carl Zeiss und Thyssenkrupp
  eine zweite Perspektive. Die Dichte je Unternehmen ist in `docs/datenbasis.md` belegt.
- **Status:** endgültig (Autor, 2026-10-02).

## E3 – Erkennungsreihe für die Gesamtbewertung

- **Kontext:** Das Backend kennt zwei Aggregationen: `get_company_timeline`
  (`backend/routes/analytics.py`) mittelt die Spalte `durchschnittsbewertung` je Bewertung
  und Monat; `_compute_avg_overall` (`backend/routes/companies.py`) mittelt die 13
  Kategorienmittelwerte über alle Bewertungen.
- **Entscheidung:** Die Erkennung arbeitet je Unternehmen, Quelle und Kalendermonat auf dem
  arithmetischen Mittel der Spalte `durchschnittsbewertung` aller Bewertungen dieses Monats
  (die Spalte stammt aus dem Kununu-Export und entspricht der dort je Bewertung angezeigten
  Gesamtnote). Einzeldimensionen werden analog aus den jeweiligen `sternebewertung_*`-Spalten
  gemittelt. Bewertungen ohne `datum` werden ignoriert.
- **Begründung:** Diese Reihe ist identisch mit der Zeitleiste im Dashboard, also mit dem,
  was die Nutzer sehen; das Kategorienmittel weicht davon ab, weil Bewertungen mit
  unvollständigen Kategorien anders gewichtet werden, und ist für Kandidaten nicht
  definiert.
- **Umsetzung:** `backend/services/rating_series_service.py` ist die einzige Implementierung
  dieser Reihe (`monthly_series`, `build_monthly_series`, Eignung nach E4 über `is_eligible`).
  Die Anomalieerkennung in Inkrement 1 nutzt diesen Dienst; die Serien-CSVs unter
  `backend/data/series/` werden über denselben Dienst erzeugt.
- **Status:** endgültig für Inkrement 1.

## E4 – Mindestdichte je Monat

- **Kontext:** Viele Monate enthalten nur einzelne Bewertungen; ein Monatsmittel aus einer
  oder zwei Bewertungen ist Rauschen.
- **Entscheidung:** Monate mit weniger als 5 Bewertungen werden in der Erkennungsreihe
  nicht bewertet (sie bleiben als Lücke sichtbar; im Dashboard werden Lücken zwischen zwei
  bewerteten Monaten nur zur Darstellung gestrichelt überbrückt, siehe
  `docs/feature-doku/01-anomalien-im-verlauf.md`). Unternehmen mit weniger als 12 solchen
  Monaten in der Mitarbeiterquelle werden nicht in die automatische Erkennung aufgenommen,
  sondern nur als Fallstudie ohne Zeitreihenanalyse geführt; die Liste steht in
  `docs/datenbasis.md`, Abschnitt „Konsequenzen“. Stand 2026-10-02 erfüllen in der
  Mitarbeiterquelle 15 von 26 Unternehmen das Kriterium, in der Kandidatenquelle 5 von 26.
- **Begründung:** Der Schwellwert 5 entspricht dem Kriterium der Prüfliste für Inkrement 0
  („Monate mit weniger als 5 Bewertungen“). 12 Monate sind das Minimum, damit ein
  Referenzfenster vor und nach einer Veränderung existiert.
- **Status:** vorläufig; nach Vorliegen der Annotationen gegen DZ1 zu prüfen.

## E5 – Referenzzeiträume (Annotationen)

- **Kontext:** DZ1 verlangt den Abgleich der automatisch erkannten Veränderungen mit
  manuell annotierten auffälligen Zeiträumen.
- **Entscheidung:** Die Annotationen stehen in `backend/data/annotations.json` (Schema:
  `company`, `source`, `dimension`, `period_from`, `period_to`, `direction`, `note`). Sie werden
  vom Autor anhand der Serien-CSVs unter `backend/data/series/` eingetragen, bevor
  Erkennungscode entsteht, und mit `backend/scripts/validate_annotations.py` geprüft. Die
  Datei wird in einem eigenen Commit vor dem ersten Erkennungscode versioniert.
- **Annotationsprotokoll (2026-10-03):** Die Regeln für Auswahl, Länge und Abgleich der
  Referenzzeiträume stehen in `docs/referenzzeitraeume-literatur.md`, Abschnitt 3, und sind in
  `backend/data/annotations.json` unter `hinweise.protokoll` wiederholt. Kurzfassung: Einheit
  Kalendermonat; Zeitraum 1–3, höchstens 6 Monate; Randmonate mit ≥ 5 Bewertungen; Richtwert
  ≥ 0,5 Sterne Niveauunterschied gegenüber den bis zu sechs Vormonaten; 0–3 Zeiträume je Reihe;
  Toleranz beim Abgleich ±1 Monat mit Eins-zu-eins-Zuordnung und F1 als Hauptmaß; Ereignisanker
  erst nach der Beurteilung aus der Reihe; Unternehmen unter der Mindestdichte aus E4 ohne
  Einträge. Literaturgrundlage: Green et al. (2019) für Quartalsreaktion und Mindestfallzahl
  (15 je Quartal, SD der Quartalsänderung 0,45), van den Burg & Williams (2020), Truong et al.
  (2020), Lavin & Ahmad (2015) und Tatbul et al. (2018) für Toleranzmarge, Eins-zu-eins-Zuordnung
  und Regionslabels, Restart Career & kununu (2024) für die Größenordnung realer Einbrüche.
  Kein Paper untersucht „optimale Referenzzeiträume“ für Arbeitgeberbewertungen direkt; die
  Zahlenwerte sind Setzungen des Autors innerhalb literaturgezogener Spannen und so gekennzeichnet.
- **Begründung:** Eine aus der Erkennung abgeleitete oder nachträglich erzeugte Referenz
  wäre zirkulär und würde den F1-Wert entwerten; die Git-Historie belegt die Reihenfolge.
- **Status:** Vorlage, Protokoll und Validierung vorhanden; Einträge offen (Handarbeit des Autors).
  Die Referenzzeiträume sind kein Teil des Dashboards; sie dienen nur der Evaluation (DZ1).
- **Aktualisierung 2026-10-03 – Einträge zurückgestellt:** Der Autor hat das Eintragen der
  Referenzzeiträume am 2026-10-03 zurückgestellt; der Erkennungscode von Inkrement 1 (E9) ist
  seitdem entstanden. Die oben vorgesehene Reihenfolge (Annotation vor dem ersten
  Erkennungscode, belegt durch die Git-Historie) gilt damit **nicht mehr**.
- **Ersatzregel:** Die Annotation erfolgt **vor der Evaluation** (DZ1) anhand der Serien-CSVs
  unter `backend/data/series/` und **ohne Einsicht in Erkennungsergebnisse** (keine Karte, keine
  Detailseite, keine API-Antwort, keine Parameterübersicht unter `backend/data/calibration/`
  für die zu annotierenden Reihen). Die Annotationen werden in einem eigenen Commit vor dem
  ersten Abgleich versioniert.
- **Einschränkung für DZ1:** Die Unabhängigkeit der Referenz lässt sich nicht mehr über die
  Git-Historie belegen, sondern nur über die Selbstverpflichtung des Autors. Zudem kennt der
  Autor die Ergebnisse für Demo 3 und die Größenordnung der Treffer aus der Parameterübersicht
  (E9). Beides ist in der Evaluation als Grenze der Validität zu nennen.
- **Aktualisierung 2026-10-08 – Umfang, Werkzeuge und Ablauf (Vorbereitung vor Inkrement 4):**
  - **Umfang der Annotation:** Quelle Mitarbeitende, Dimension Gesamtbewertung, alle nach E4
    geeigneten Unternehmen; Stand 2026-10-08 sind das 15 Reihen (Thyssenkrupp, Open Grid
    Europe, E.ON, RWE, KIT, TU München, SAP SE, NTT DATA SE, 1&1 AG, Bechtle, Cancom, Carl
    Zeiss, Compugroup Medical Deutschland, Telekom, Freenet). Unternehmen unter der
    Mindestdichte erhalten keine Einträge (Protokoll-Regel 9). Die Bewerberquelle (5 geeignete
    Reihen) und Einzeldimensionen gehören nicht zum Umfang; der Bogen lässt sich mit
    `--source candidates` erzeugen, falls der Autor sie später aufnimmt.
  - **Serien-CSVs:** am 2026-10-08 neu erzeugt und mit dem eingecheckten Stand verglichen,
    identisch; sie entsprechen damit der Datenbank.
  - **Annotationsbogen:** `backend/scripts/make_annotation_sheet.py` schreibt eine
    eigenständige HTML-Datei (`backend/data/annotationsbogen.html`, nicht eingecheckt) mit
    einem Diagramm je Reihe (Monatsmittel, Anzahl je Monat, Monate unter der Mindestdichte in
    Grau, Linie der Mindestdichte), einer aufklappbaren Monatstabelle für die Angaben der
    `note` sowie der Kurzfassung des Protokolls und den Regeln aus `annotations.json`. Das
    Skript importiert weder `anomaly_service` noch `changepoint_detector` und zeichnet keine
    Markierung, keine Niveaulinie und keinen Einzelmonat (Test
    `backend/tests/test_make_annotation_sheet.py`).
  - **Abgleich:** `backend/scripts/evaluate_detection.py` berechnet die Erkennung mit den
    Standardparametern (E9, E14) für jede annotierte Reihe und gleicht nach Regel 6 ab, fest im
    Skript: Toleranz ±1 Monat, bei nicht bewertetem Nachbarmonat bis zu 3 Kalendermonate,
    gleiche Richtung, Eins-zu-eins-Zuordnung (Annotationen in zeitlicher Reihenfolge, früheste
    passende Erkennung). Ausgabe je Reihe, je Quelle und gesamt: Precision, Recall und F1,
    getrennt für Niveauwechsel allein und für Niveauwechsel mit Einzelmonaten, dazu Treffer,
    verfehlte Zeiträume und zusätzliche Markierungen; `--json` schreibt das Ergebnis als Datei.
    Reihen unter der Mindestdichte werden übersprungen (Regel 9); bei leerer Annotationsliste
    bricht das Skript mit einem Hinweis ab. Tests mit konstruierten Reihen und Annotationen in
    `backend/tests/test_evaluate_detection.py`.
  - **Ablauf (verbindlich):** (1) `uv run python scripts/make_annotation_sheet.py`;
    (2) annotieren in `backend/data/annotations.json` allein aus dem Bogen, ohne Karte,
    Detailseite, API-Antwort oder Parameterübersicht zu öffnen, Ereignisanker erst danach
    (Regel 7); (3) `uv run python scripts/validate_annotations.py`; (4) die Annotationsdatei in
    einem eigenen Commit versionieren, der sonst nichts ändert; (5) erst dann
    `uv run python scripts/evaluate_detection.py --json data/calibration/dz1_ergebnis.json` und
    das Ergebnis in einem weiteren Commit ablegen; (6) E9 und E14 mit dem Beleg aktualisieren.
    Die Auswertung darf vor Schritt 4 nicht auf echten Reihen laufen, weil ihre Ausgabe alle
    erkannten Veränderungen der Reihe nennt.
- **Status (2026-10-08):** Protokoll, Validierung, Bogen und Abgleich vorhanden; Einträge offen
  (Handarbeit des Autors). Die Referenzzeiträume bleiben außerhalb des Dashboards.

## E6 – Unternehmens-Metadaten

- **Kontext:** Für die Kontextsammlung (Kurse, Ad-hoc-Meldungen) braucht die Erklärung
  Ticker und ISIN; 8 der 26 Unternehmen sind nicht börsennotiert.
- **Entscheidung:** Migration `006_add_company_metadata.sql` ergänzt `companies` um
  `ticker` (Yahoo-Finance-Notation), `isin`, `sector` (Branche) und `peer_group` mit den
  Werten „Börsennotiert DE“, „Börsennotiert Ausland“, „Nicht börsennotiert“, „Demo“. Die
  Werte stehen versioniert in `backend/data/company_metadata.json` und werden mit
  `backend/scripts/seed_company_metadata.py --apply` eingespielt. Nicht börsennotierte
  Unternehmen erhalten keine Finanzmarktquellen; für sie gilt die namensbasierte
  Nachrichtensuche aus E7.
- **Sonderfälle (vorläufig, vom Autor zu bestätigen):** Compugroup Medical wurde 2025 von
  der Börse genommen; yfinance liefert für keinen COP-Ticker Kurse, daher vorerst
  „Nicht börsennotiert“ ohne Ticker, obwohl das Unternehmen im Untersuchungszeitraum
  notiert war. NTT DATA SE ist eine Tochter von NTT DATA Group (9613.T, 2025 von NTT
  übernommen, keine Kursdaten mehr); hinterlegt ist der notierte Mutterkonzern NTT, Inc.
  (9432.T) als „Börsennotiert Ausland“. ISINs konnten über yfinance nicht verifiziert
  werden und bleiben leer, bis sie aus einer belegbaren Quelle nachgetragen sind.
- **Status:** Migration und Daten vorhanden; Einspielen nach Ausführung der Migration.

## E7 – Nachrichtenquelle für historische Meldungen

- **Kontext:** `yfinance.Ticker.get_news` hat keinen Datumsparameter und liefert nur die
  jüngsten Meldungen; Anomalien liegen überwiegend Jahre zurück.
- **Entscheidung (vorläufig, Spike vom 2026-10-02, `docs/quellen-spike.md`):**
  Google-News-RSS ist die primäre Quelle für alle Unternehmen (Monatsfenster, bei 0 Treffern
  ±1 Monat); EQS-News-REST ist sekundäre Quelle für börsennotierte Unternehmen (Ad-hoc,
  Stimmrechte, Finanzberichte; undokumentierte Schnittstelle, companyUUID je Unternehmen
  einmalig ermittelt); GDELT bleibt optional hinter einem Flag (Rate-Limit 429, Cap
  75 Treffer); yfinance wird für Nachrichten nicht genutzt.
- **Begründung:** Im Spike lieferte Google-News-RSS für Thyssenkrupp 04/2023 28 datierte
  deutsche Treffer inklusive des Vorstandswechsels, für Bechtle 10/2020 6, für das nicht
  notierte KIT 8; EQS lieferte 5 bzw. 1 Meldung nur für die notierten Fälle; yfinance 0 im
  Fenster. Für Open Grid Europe fand keine Quelle Treffer im Einzelmonat, erst im
  3-Monats-Fenster.
- **Offen:** Nutzungsbedingungen von Google News RSS und EQS für die Arbeit, Umgang mit
  englischsprachigen Treffern, Fenstergröße 1 oder 3 Monate.
- **Entscheidung 2026-10-08 (Autor):** Die Nutzung von Google News RSS, EQS und Yahoo Finance
  gilt im Rahmen der wissenschaftlichen Arbeit als vertretbar (Fundstellen und offene Fragen in
  `docs/nutzungsbedingungen.md`). Dafür gelten folgende Maßnahmen, umgesetzt in Inkrement 4
  (E18–E20):
  - Google News RSS ist Hauptquelle: eine Abfrage je Unternehmen und Kalendermonat mit den
    Operatoren `after:` und `before:` (Suchbegriff und Ausschlussbegriffe je Unternehmen in
    `backend/data/company_metadata.json`, Felder `news_term`, `news_exclude`,
    `news_term_confirmed`). EQS News ist zweite Quelle für börsennotierte Unternehmen
    (companyUUID je Emittent in der Metadatei, Feld `eqs`). GDELT bleibt hinter dem Schalter
    `CONTEXT_GDELT=1` und ist aus.
  - Gespeichert werden nur Titel, Herausgeber, Link, Datum, Quelle, Typ, Verlässlichkeit und
    Sprache; keine Volltexte, keine Textauszüge. Die Beispieltitel aus dem Spike wurden am
    2026-10-08 aus `backend/data/spike_news_sources.json` entfernt, die Zahlen bleiben.
  - Zwischen zwei Abrufen derselben Quelle liegen mindestens 2 Sekunden; die Kennung nennt
    Forschung und nicht-kommerzielle Nutzung (`USER_AGENT` in `backend/services/news_service.py`).
  - Der Belegspeicher liegt unter `backend/data/context/` und steht in `.gitignore`; keine
    Schlagzeilen in Code, Tests, Dokumentation oder Commits.
  - `CONTEXT_LIVE_FETCH=0` unterbindet jeden Abruf; dann gilt nur der Speicher (Evaluationsinstanz,
    `docs/evaluationsinstanz.md`).
  - Jede Quelle läuft getrennt; fällt eine aus, liefert die andere weiter.
  - Englischsprachige Treffer bleiben enthalten und tragen eine Sprachkennzeichnung (E19);
    das Fenster ist nicht mehr 1 oder 3 Monate je Abfrage, sondern das Ereignisfenster aus E18
    über mehrere Monatsabfragen.
- **Status:** Quellen entschieden (2026-10-08); die Fragen an den Betreuer aus
  `docs/nutzungsbedingungen.md` bleiben zu klären.

## E8 – Reproduzierbarkeit des Docker-Stacks

- **Kontext:** `backend/Dockerfile` kopierte mit `COPY . .` auch `backend/.env` ins Image.
  Weil `database/supabase_client.py` den Service-Key der Datei vor dem Anon-Key aus
  `docker-compose.yml` bevorzugt, sprach der Container gegen das lokale PostgREST mit dem
  Schlüssel des gehosteten Projekts (Fehler PGRST301), und der Schlüssel lag im Image.
- **Entscheidung:** `backend/.dockerignore` schließt `.env`, `.venv`, Caches und trainierte
  Modelle aus. Die Abhängigkeiten `ruptures` und `yfinance` stehen in `pyproject.toml`,
  `uv.lock`, `requirements.txt` und beiden Dockerfiles.
- **Status:** endgültig; Image nach der Änderung neu bauen.

## E9 – Erkennungsverfahren und Parameter

- **Kontext:** Inkrement 1 markiert im Dashboard auffällige Veränderungen im Monatsverlauf
  (FA-01 bis FA-04, Zähler aus FA-26). Gesucht sind anhaltende Niveauwechsel, keine einzelnen
  Ausreißermonate. Eingabe ist die Monatsreihe nach E3, nur bewertete Monate nach E4.
- **Entscheidung:**
  - **Verfahren:** PELT (Killick, Fearnhead & Eckley 2012) aus `ruptures` mit Kostenfunktion
    `model="l2"` (Wechsel des Mittelwerts), `min_size=3` bewertete Monate je Abschnitt und
    Strafterm `penalty=0.5` (fester Wert, gültig bis 2026-10-04; seitdem skalierter
    Strafterm, siehe „Aktualisierung 2026-10-04“ unten). Umsetzung:
    `backend/models/changepoint_detector.py`.
  - **Fallback:** Für Reihen, die für PELT zu kurz sind (unter `2 × min_size` Werten),
    Differenz der Mittel zweier angrenzender Fenster von 3 Monaten mit Schwelle 0,3 Sterne.
    Im Dashboard greift er nicht, weil geeignete Reihen mindestens 12 Monate haben.
  - **Mindestbetrag:** Wechsel mit `|delta| < min_delta = 0,3` Sternen werden nicht angezeigt.
  - **Schweregrad:** `high` („deutlich“) ab 0,5 Sternen (Richtwert des Annotationsprotokolls,
    E5), sonst `medium` („mäßig“).
  - **Austauschbarkeit:** Das Protocol `ChangePointDetector` erlaubt ein zweites Verfahren
    (geplant: Günnemann et al. 2014), ohne Service, API oder Frontend zu ändern.
  - **Kennzahlen je Veränderung:** Monat (erster bewerteter Monat auf dem neuen Niveau),
    Richtung, Delta, Mittel davor und danach, Bewertungen davor und danach
    (`n_reviews_before`, `n_reviews_after`, Summe `n_reviews`), Abschnittsgrenzen
    (`before_from`, `after_to`), Lücke vor dem Monat (`previous_period`, `gap_months`),
    Verfahren und Parameter.
  - **Darstellung (2026-10-03):** Je Veränderung eine Stufe von Ø davor zu Ø danach am
    markierten Monat (Höhe = Ausmaß, Form = Richtung, Strichstärke = Schweregrad), auf der
    Detailseite zusätzlich die Niveaulinie der Abschnitte; Begründung in
    `docs/feature-doku/01-anomalien-im-verlauf.md`, Abschnitt 3.
    Umsetzung: `backend/services/anomaly_service.py`,
    API `GET /api/analytics/company/{id}/anomalies` (auch `dimension=all`).
- **Begründung:** PELT findet die beste Zerlegung exakt in linearer Zeit, ohne die Zahl der
  Wechsel vorzugeben; `l2` passt zur Frage nach Niveauverschiebungen. `min_size=3` dämpft
  Ausreißermonate, schließt sie aber nicht vollständig aus: Ein kurzer, starker Einbruch kann
  als 3-Monats-Abschnitt mit einem unauffälligen Randmonat erscheinen (Telekom 2022-10; 6 Fälle
  in 7 dichten Reihen, Prüfung vom 2026-10-03). Die API kennzeichnet das
  (`month_near_previous_level`). Die Zahlenwerte sind Setzungen des Autors innerhalb der Größenordnungen
  aus `docs/referenzzeitraeume-literatur.md` (u. a. SD der Quartalsänderung ≈ 0,45 Sterne bei
  Green et al. 2019; Richtwert 0,5 Sterne im Annotationsprotokoll).
- **Prüfung bisher:**
  - Synthetische Demo-Reihen (`backend/tests/anomaly/`): Demo 3 liefert den erwarteten Abfall
    um 2023-01 und Anstieg um 2023-12 (±1 Monat); Demo 1 und Demo 2 liefern in der
    Gesamtbewertung keine Veränderung.
  - Parameterübersicht (`backend/scripts/explore_anomaly_params.py`,
    `backend/data/calibration/anomaly_params_employee_durchschnittsbewertung.csv`, Stand
    2026-10-03): Mit den Startwerten 31 Abfälle und 35 Anstiege bei 15 geeigneten Unternehmen
    (Mitarbeitende, Gesamtbewertung). Die Zahl hängt vor allem vom Strafterm ab (penalty 0,25:
    116; 0,5: 66; 1,0: 35; 2,0: 9 bei min_delta 0,3); `min_delta` wirkt ab penalty 0,5 kaum.
    Lange, dichte Reihen (Cancom, 1&1, Telekom) erhalten die meisten Markierungen, weil der
    Strafterm nicht mit der Reihenlänge wächst.
- **Status (2026-10-03):** **vorläufig.** Die Werte sind Setzungen des Autors, geprüft an Demo 3
  und an der Parameterübersicht, **nicht an Referenzzeiträumen**. Die Messung gegen die
  Referenzzeiträume für DZ1 (F1 mit ±1 Monat Toleranz, E5) steht aus; danach wird dieser
  Eintrag mit Beleg aktualisiert.

### E9 – Aktualisierung 2026-10-04: skalierter Strafterm

- **Alte Regel:** fester Strafterm `penalty = 0,5` (quadrierte Sterne) für jede Reihe.
- **Befund:** Der feste Wert berücksichtigt weder die Länge noch die Streuung einer Reihe.
  Mit den Startwerten entstanden 66 Markierungen bei 15 geeigneten Unternehmen (Cancom 16,
  1&1 und Telekom je 9), 55 davon „deutlich“. Reihen mit stark schwankenden Monatsmitteln
  wurden übersegmentiert. Auf synthetischen Reihen ohne Sprung (120 Monate, σ 0,5) meldet
  der feste Wert 0,5 in mindestens 40 von 50 Fällen eine Veränderung über 0,3 Sterne
  (`backend/tests/anomaly/test_changepoint_detector.py`,
  `test_fixed_05_oversegments_noisy_series`).
- **Neue Regel:** Standard ist der skalierte Strafterm
  `penalty = penalty_factor · σ² · ln(n)` mit `penalty_factor = 2,0`, `n` = Zahl der
  bewerteten Monate und `σ = noise_sigma(values) = 1,4826 · MAD(diff(values)) / √2`
  (robuste Streuung der Monatsmittel aus den ersten Differenzen, Untergrenze 0,05 Sterne).
  Die Differenzen machen die Schätzung unempfindlich gegen Niveauwechsel, der Median gegen
  Ausreißer. Der Strafterm wächst damit mit der Streuung (σ²) und langsam mit der Länge
  (ln n). Mit Faktor 2 entspricht die Form dem BIC-Strafterm für einen Mittelwertwechsel bei
  bekannter Varianz; Beleg offen (Autor), vgl. Truong et al. 2020 zu prüfen. Ein ausdrücklich
  übergebener fester `penalty` bleibt möglich und hat Vorrang (fester Modus). `model`,
  `min_size`, `min_delta`, Schweregrad und das Protocol bleiben unverändert. Die API nennt je
  Antwort und je Anomalie `penalty_mode` („scaled“/„fixed“), `penalty_factor`,
  `noise_sigma` und den verwendeten `penalty`; bei `dimension=all` je Dimension.
- **Ergebnis der neuen Parameterübersicht** (`backend/scripts/explore_anomaly_params.py`,
  `backend/data/calibration/anomaly_params_scaled_employee_durchschnittsbewertung.csv`,
  Stand 2026-10-04, Mitarbeitende, Gesamtbewertung, 15 geeignete Unternehmen; die CSV vom
  2026-10-03 bleibt als Beleg): Markierungen gesamt (davon „deutlich“) bei `min_delta` 0,3:
  Faktor 1: 44 (33), **Faktor 2: 19 (15)**, Faktor 3: 13 (9), Faktor 4: 10 (9); zum Vergleich
  fest 0,5: 66 (55). Mit Faktor 2 je Unternehmen: Freenet 5, Telekom 4, NTT DATA 4, je 1 bei
  SAP, 1&1, Bechtle, Compugroup, E.ON und RWE, keine bei Cancom, Thyssenkrupp, Carl Zeiss,
  KIT, TU München und Open Grid Europe. Der verwendete Strafterm reicht von 0,42 (Open Grid
  Europe, σ 0,26, n 22) bis 2,39 (Cancom, σ 0,50, n 115). Synthetisch (je 200 Reihen,
  `min_delta` 0,3): Fehlalarme ohne Sprung bei 120 Monaten und σ 0,5 mit Faktor 2 in 6 %,
  ein Sprung von 1,0 Sternen wird in 77 % genau getroffen (Faktor 3: 3 % / 82 %).
- **Folgen:** Das Beispiel Telekom 2022-10 (Mindestlänge füllt einen kurzen Einbruch auf,
  siehe oben) wird mit dem neuen Standard nicht mehr markiert. Demo 3 liefert weiter Abfall
  um 2023-01 und Anstieg um 2023-12, Demo 1 und 2 keine Veränderung. Bei sehr verrauschten
  Reihen braucht ein Wechsel jetzt einen größeren Sprung (Cancom bei 12/12 Monaten
  0,63 statt 0,29 Sterne); echte, aber kleine Veränderungen können dort unerkannt bleiben.
- **Status:** **vorläufig.** Faktor 2 ist eine Setzung des Autors, geprüft an Demo 1–3, an
  synthetischen Reihen und an der Parameterübersicht, **nicht an Referenzzeiträumen** (DZ1).

## E10 – Themenweg für den Vorher-Nachher-Vergleich

- **Kontext:** Inkrement 2 vergleicht die Bewertungen vor und ab einer auffälligen
  Veränderung und nennt je Thema, wie sich der Anteil der Bewertungen verschiebt, die es
  ansprechen. Im Repository gibt es zwei Themenwege: die Schlüsselwort-Themen der
  Themenübersicht (`topic-overview`, je Quelle 13 bzw. 10 Themen, benannt wie die
  Kununu-Kategorien) und das LDA-Modell aus Zyklus 1 (`backend/models/lda_topic_model.py`,
  Themenzahl über die Kohärenz c_v gewählt, `backend/scripts/sweep_num_topics_db.py`).
- **Entscheidung (Autor, 2026-10-04):** Schlüsselwort-Themen, kein LDA. Die Definitionen je
  Quelle und `analyze_topic` sind aus `backend/routes/analytics.py` nach
  `backend/services/keyword_topic_service.py` umgezogen; die Ausgabe von `topic-overview`
  ist unverändert (geprüft gegen Commit 4ad0a80 für Demo 1–3). Ein Thema gilt in einer
  Bewertung als genannt, wenn eines seiner Schlüsselwörter (regulärer Ausdruck) in einem
  Textfeld vorkommt (`topics_in_review`).
- **Begründung:** Die Themen sind dieselben, die das Dashboard schon zeigt, und tragen die
  Namen der Kununu-Kategorien; damit lässt sich eine Verschiebung im Text direkt neben die
  Sternebewertung derselben Kategorie stellen. Die Zuordnung ist nachvollziehbar (ein
  Schlüsselwort, eine Textstelle) und für jede Bewertung gleich, ohne Training und ohne
  Abhängigkeit von der Themenzahl. Sie ist schnell genug, um je Anfrage live zu laufen.
- **Grenzen:**
  - Es ist **nicht** das per c_v validierte LDA-Modell aus Zyklus 1. Die Schlüsselwortlisten
    sind Setzungen und nicht gegen eine Kohärenz oder eine manuelle Zuordnung geprüft.
  - Die Schlüsselwörter sind deutsch. Englische Texte werden kaum erfasst
    (Test `test_english_text_is_not_matched`); bei Unternehmen mit vielen englischen
    Bewertungen sind die Anteile zu niedrig. Relevant für Inkrement 5 (Erklärungen).
  - Mehrdeutige Wörter zählen mit (z. B. „Klima“ bei Arbeitsatmosphäre und Umwelt,
    „Entwicklung“ bei Karriere auch im Sinn von Softwareentwicklung).
- **Status:** endgültig für Inkrement 2 (Entscheidung des Autors); die Grenzen werden in
  Inkrement 5 neu bewertet.

## E11 – Stimmung im Vorher-Nachher-Vergleich

- **Kontext:** Der Vergleich nennt neben den Themenanteilen die Stimmung der Texte, gesamt
  und je Thema. Im Repository gibt es `SentimentAnalyzer`
  (`backend/models/sentiment_analyzer.py`) mit den Modi `transformer` (German Sentiment
  BERT mit Abgleich gegen das Lexikon) und `lexicon` (Wortlisten), mit eingebautem Rückfall
  auf das Lexikon, wenn das Modell nicht lädt.
- **Entscheidung (Autor, 2026-10-04):** Modus `transformer` mit der Sternebewertung
  (`durchschnittsbewertung`) als Hinweis; lädt das Modell nicht, gilt der Lexikon-Modus. Die
  Antwort nennt den tatsächlich verwendeten Modus (`sentiment_mode`).
  - Ein Analyzer je Prozess, nicht je Anfrage; Ergebnisse je Quelle, Bewertungs-ID und
    Modus im Prozess zwischengespeichert.
  - Text einer Bewertung: die Freitextfelder ohne Titel (Mitarbeitende: gut, schlecht,
    Verbesserungsvorschläge; Bewerbende: Stellenbeschreibung, Verbesserungsvorschläge).
    Bewertungen ohne Freitext gehen nicht in die Stimmung ein.
  - Stichprobe: höchstens 300 Bewertungen mit Freitext je Fenster, bei mehr die jüngsten
    300; die Antwort nennt das (`sentiment_sample`).
  - Kennzahlen: Anteile positiv, neutral, negativ und mittlere Polarität (−1 bis 1).
- **Begründung:** Der Transformer ist im Projekt der Hauptmodus, das Lexikon die Reserve.
  Die Stichprobe begrenzt die Antwortzeit: gemessen 2026-10-04 auf dem Entwicklungsrechner
  rund 23 bis 26 ms je Text im Transformer-Modus (Telekom, 457 Texte: 10,8 s), dazu einmal je
  Prozess rund 4 s für das Laden des Modells; mit Zwischenspeicher 0,2 bis 0,4 s. Die
  jüngsten 300 liegen am nächsten am markierten Monat.
- **Grenzen:** Die Stimmung ist eine Modellschätzung je Bewertung, nicht je Thema; die
  Stimmung „je Thema“ ist die Stimmung der ganzen Bewertungen, die das Thema nennen. Die
  Sternebewertung als Hinweis kann die Stimmung zur Note hin ziehen. Der Lexikon-Modus
  trennt Wörter nur an Leerzeichen; ein Wort mit Satzzeichen („schlecht.“) wird nicht
  erkannt. Die Stichprobe ist nicht zufällig, sondern zeitlich.
- **Status:** vorläufig (Stichprobengröße 300 ist eine Setzung).

## E12 – Vergleichsfenster

- **Kontext:** Für Drill-down und Vergleich braucht jede auffällige Veränderung einen
  Zeitraum davor und danach.
- **Entscheidung:** Für eine Veränderung mit Monat `date`:
  - davor: die `window_months` Kalendermonate vor `date`, nicht früher als `before_from`
    (Beginn des Abschnitts vor dem Wechsel),
  - danach: `date` und die folgenden Monate, zusammen `window_months`, nicht später als
    `after_to` (Ende des Abschnitts nach dem Wechsel),
  - Standard `window_months = 6`. In die Fenster gehen **alle** Bewertungen dieser Monate
    ein, auch aus Monaten mit weniger als 5 Bewertungen (anders als in der
    Erkennungsreihe, E4).
  - Kleine Basis (`low_basis`): ein Fenster mit weniger als 10 Bewertungen, oder je Thema
    weniger als 5 Nennungen in beiden Fenstern zusammen.
  - Umsetzung: `comparison_windows` in `backend/services/explanation_service.py`; dieselbe
    Regel rechnet `comparisonWindows` in `frontend/src/lib/anomalySeries.js` für die
    Bewertungsliste.
- **Begründung:** Sechs Monate geben auch bei mäßig dichten Reihen genug Bewertungen für
  Anteile; die Begrenzung durch die Nachbarabschnitte verhindert, dass ein Fenster über
  einen weiteren erkannten Wechsel reicht.
- **Grenzen:** Die Fenster sind nach Bewertungen gewichtet, die Erkennung nach
  Monatsmitteln. Bei ungleich verteilten Bewertungen kann die mittlere Gesamtnote im
  Vergleich in die andere Richtung zeigen als die erkannte Veränderung (SAP SE, Anstieg
  ab 2024-07: Ø der Monatsmittel 3,07 → 3,74, Ø je Bewertung 3,79 → 3,65, weil der März 2024
  174 der 246 Bewertungen des Fensters davor mit Ø 4,16 enthält).
- **Status:** vorläufig (Fensterlänge und Schwellen der kleinen Basis sind Setzungen).

## E13 – Statusfilter (Bewertendengruppe)

- **Kontext:** Die Bewertungen tragen eine Spalte `status`. Die Werte sind uneinheitlich
  (nur lesend geprüft am 2026-10-04): Mitarbeitende `1.0` (13 815), `0.0` (4 030), leer
  (2 494), `Angestellt` (889) und `Ex-Angestellt` (719, beide nur Demo), `True` (11) und
  `False` (4, beide nur Formycon); Bewerbende `hired` (1 235), leer (799), `Bewerber` (792,
  nur Demo), `offerDeclined` (711), `rejected` (625), `deferred` (514).
- **Entscheidung:** Eine Bewertendengruppe ist Quelle plus Status. Die Rohwerte werden auf
  feste Schlüssel zurückgeführt (`normalize_status` in
  `backend/services/review_service.py`, Vorbild `formatStatus` im Frontend):
  - Mitarbeitende: `angestellt` (1, 1.0, True, Angestellt), `ex-angestellt` (0, 0.0, False,
    Ex-Angestellt), `unbekannt` (leer),
  - Bewerbende: `eingestellt` (hired), `angebot-abgelehnt` (offerDeclined), `abgelehnt`
    (rejected), `zurueckgestellt` (deferred), `unbekannt` (leer und „Bewerber“, das keinen
    Ausgang nennt).
  Mit `status` laufen Monatsreihe, Eignung (E4), Strafterm (E9) und Erkennung nur auf
  dieser Gruppe; jede Kombination aus Quelle, Dimension und Status ist eine eigene Reihe.
  Vergleich und Bewertungsliste nutzen dieselbe Gruppe. Ohne `status` ist alles wie in
  Inkrement 1.
- **Begründung:** Aktuelle und ehemalige Mitarbeitende bzw. eingestellte und abgelehnte
  Bewerbende bewerten aus verschiedenen Lagen; eine Veränderung kann in einer Gruppe
  auftreten und in der Mischung verdeckt sein. Die Zuordnung `True`/`False` folgt der von
  `1.0`/`0.0` (Annahme des Entwicklers, 15 Bewertungen).
- **Ergebnis (2026-10-04, 26 reale Unternehmen, Gesamtbewertung):** geeignete Reihen
  Mitarbeitende alle 15, `angestellt` 15, `ex-angestellt` 6, `unbekannt` 3; Bewerbende
  alle 5, `eingestellt` 1 (Carl Zeiss), `unbekannt` 1 (Thyssengas), übrige 0. Erkannte
  Veränderungen (Mitarbeitende, Gesamtbewertung): alle 19, `angestellt` 11,
  `ex-angestellt` 1.
- **Grenzen:** Die meisten Gruppen der Bewerberquelle sind für die automatische Erkennung
  zu dünn; die Detailseite zeigt dann den Hinweis zur Eignung. Die Bedeutung von
  `deferred` ist aus den Daten nicht eindeutig („zurückgestellt“ ist eine Übersetzung).
- **Aktualisierung 2026-10-08 – Zuordnung bestätigt (Entscheidung D1):** Belege in
  `docs/offene-punkte-vor-inkrement-4.md`, Abschnitt D1 (nur lesend erhoben: Datenbank,
  Rohexporte und Scraper des Autors). Der Autor hat den Vorschlag angenommen:
  - `True`/`False` (nur Formycon, 15 Bewertungen) sind derselbe Kununu-Wert wie `1.0`/`0.0`,
    im Export als Wahrheitswert statt als Zahl; die Zuordnung `True` → `angestellt`, `False`
    → `ex-angestellt` ist damit belegt (mittlere Gesamtnote 4,55 bzw. 2,15 wie 4,31 bzw.
    2,36 bei `1.0`/`0.0`). Formycon ist für die Erkennung nicht geeignet.
  - `deferred` behält den Schlüssel `zurueckgestellt`; die Bezeichnung lautet jetzt
    „Zurückgestellt oder Absage“. Grund: Die 13 Unternehmen aus Zyklus 1 (id 3–20) haben
    keinen Wert `rejected`, weil ihr Scraper-Stand „Absage“ und `rejected` auf `deferred`
    abbildet; 453 der 514 Zeilen mit `deferred` liegen dort, und 20 % ihrer Texte nennen eine
    Absage. Bei den TecDAX-Exporten ist `deferred` der unveränderte Rohwert von Kununu.
  - Leere Werte bleiben `unbekannt` („ohne Angabe“). Bei Mitarbeitenden fehlt das Feld vor
    allem bei alten Bewertungen (bis 2013 bei 93–100 %, ab 2016 bei unter 6 %). `Bewerber`
    (nur Demo) bleibt `unbekannt`.
  - Einschränkung: Für die Unternehmen aus Zyklus 1 liegt keine Unterscheidung
    aktuell/ehemalig vor (kein Wert `0.0`, 3 758 Zeilen `1.0`, 360 leer); `angestellt` heißt
    dort „Bewertung mit Typangabe“ und entspricht bis auf die leeren Zeilen der Gruppe „alle“.
    Das betrifft 8 der 15 geeigneten Mitarbeiter-Reihen (Thyssenkrupp, Open Grid Europe,
    E.ON, RWE, KIT, TU München, SAP SE, NTT DATA SE); die 6 geeigneten Reihen `ex-angestellt`
    sind TecDAX-Unternehmen.
  - Geeignete Reihen je Status (nachgezählt 2026-10-08, Gesamtbewertung) unverändert:
    Mitarbeitende alle 15, `angestellt` 15, `ex-angestellt` 6, `unbekannt` 3; Bewerbende alle
    5, `eingestellt` 1, `unbekannt` 1, übrige 0. `normalize_status` liefert dieselben
    Schlüssel wie zuvor; geändert sind nur Bezeichnung und Dokumentation.
- **Status:** Zuordnung der Rohwerte bestätigt (Autor, 2026-10-08). Die Lesart von `deferred`
  und die fehlende Unterscheidung aktuell/ehemalig bei Zyklus 1 sind in der Arbeit als
  Einschränkung zu nennen.

## E14 – Auffällige Einzelmonate

- **Kontext:** Bei Telekom fällt das Monatsmittel im Dezember 2022 auf 2,60 Sterne (11
  Bewertungen), davor und danach liegt es um 4,0. Die Erkennung nach E9 sucht anhaltende
  Niveauwechsel (mindestens 3 Monate je Abschnitt) und markiert einen solchen einzelnen
  Monat absichtlich nicht; der Autor hielt ihn trotzdem für zeigenswert (2026-10-04).
- **Entscheidung (Autor, 2026-10-04):** Eine zweite, getrennte Markierung „auffälliger
  Einzelmonat“ neben den Niveauwechseln, als Raute dargestellt. Ein bewerteter Monat wird
  gemeldet, wenn er
  - vom Median der bis zu 3 bewerteten Monate davor **und** vom Median der bis zu 3
    bewerteten Monate danach um mindestens `T = max(3 · noise_sigma, 0,5 Sterne)` abweicht,
    beide Male in dieselbe Richtung (je Seite mindestens 2 Monate), und
  - seine direkten bewerteten Nachbarn selbst nicht um `T` oder mehr in dieselbe Richtung
    vom Niveau abweichen.
  `noise_sigma` ist dieselbe robuste Streuung wie im Strafterm (E9). Niveau ist der Median
  der Nachbarmonate beider Seiten. Umsetzung: `detect_outlier_months` in
  `backend/services/anomaly_service.py`, Feld `outlier_months` in
  `GET /api/analytics/company/{id}/anomalies` (auch je Dimension und Statusgruppe).
- **Begründung:** Der Vergleich mit beiden Seiten unterscheidet einen einzelnen Ausreißer
  von einem Niveauwechsel: Am Wechsel liegt eine Seite auf dem Niveau des Monats, dort
  wird nichts gemeldet. Ein erster Entwurf mit dem Niveau des PELT-Abschnitts wurde
  verworfen, weil PELT um einen großen Ausreißer bei ruhiger Reihe einen eigenen
  3-Monats-Abschnitt bildet und dann auch die Nachbarmonate gemeldet wurden. Die Schwelle
  in Vielfachen von σ passt sich der Streuung der Reihe an; 0,5 Sterne entsprechen dem
  Richtwert „deutlich“ (E5, E9).
- **Ergebnis (2026-10-04, Mitarbeitende, Gesamtbewertung, 15 geeignete Unternehmen):**
  Faktor 2,5: 18, **Faktor 3: 9**, Faktor 3,5: 3 Einzelmonate. Mit Faktor 3: Telekom 2022-12
  (−1,41), 2015-05 (−1,12), 2017-05 (−0,96), SAP SE 2024-03 (+1,23, 174 Bewertungen), Carl
  Zeiss 2024-12 (−1,24) und 2016-11 (+1,23), Cancom 2016-05 (−1,70) und 2017-08 (−1,57), RWE
  2024-07 (−1,07). Über alle Dimensionen 121 in 208 geeigneten Reihen.
- **Grenzen:** Viele gemeldete Monate beruhen auf nur 5 bis 11 Bewertungen; ein
  Einzelmonat kann Zufall sein. Er ist ein Hinweis auf einen auffälligen Monat, keine
  Aussage über Ursachen. Am Anfang und Ende einer Reihe (weniger als 2 Nachbarmonate auf
  einer Seite) wird nichts gemeldet. Zwei aufeinanderfolgende auffällige Monate werden
  nicht gemeldet (kein einzelner Monat, aber auch zu kurz für einen Niveauwechsel).
- **Status:** vorläufig (Faktor 3, 0,5 Sterne und 3 Nachbarmonate sind Setzungen; Prüfung
  gegen Referenzzeiträume wie E9 ausstehend).

## E15 – Kurs und Kennzahlen

- **Kontext:** Inkrement 3 stellt den Aktienkurs neben den
  Bewertungsverlauf, dazu wenige Unternehmenskennzahlen. 17 der 26 realen Unternehmen haben
  einen Ticker (E6), 9 nicht. Für die Arbeit soll erkennbar sein, in welchem Marktumfeld
  eine auffällige Veränderung liegt, ohne daraus eine Ursache abzuleiten.
- **Entscheidung (2026-10-04):**
  - **Rolle:** Kurs und Kennzahlen sind eine Einordnung, keine Erklärung. Das Dashboard
    berechnet keine Korrelation und keinen Vergleichswert und behauptet keinen Zusammenhang
    mit den Bewertungen. Fester Hinweis in der Ansicht: „Einordnung, keine Erklärung. Der
    Kurs zeigt das Marktumfeld; ein Zusammenhang mit den Bewertungen wird nicht behauptet.“
  - **Quelle:** Yahoo Finance über `yfinance` (Version im Feld `source`), keine neue
    Abhängigkeit (E8).
  - **Kursreihe:** Monatsschlusskurse über den ganzen verfügbaren Zeitraum
    (`period="max"`, `interval="1mo"`, `auto_adjust=True`), also um Splits und Dividenden
    bereinigt; je Monat `period` und `close`, dazu die Währung. Der Monat des Abrufs fehlt,
    weil er nicht abgeschlossen ist. Gezeichnet wird nur der angezeigte Zeitraum.
  - **Zwischenspeicher außerhalb des Repositorys:** je Ticker eine Datei
    `backend/data/market/<ticker>.json` (in `.gitignore`), gefüllt mit
    `backend/scripts/fetch_market_data.py`. Zur Laufzeit zuerst der Zwischenspeicher; fehlt
    er, ein Live-Abruf mit Speichern, außer bei `MARKET_LIVE_FETCH=0`. Ein Fehlschlag
    ergibt `available: false` mit Begründung, keinen Serverfehler. Die Datenbank wird nur
    gelesen.
  - **Kennzahlen:** aktuelle Marktkapitalisierung (Kurswährung, Stand = Tag des letzten
    Kurses), aktuelle Zahl der Mitarbeitenden (Stand = Abrufdatum) und Umsatz („Total
    Revenue“) je Geschäftsjahr in Berichtswährung, so viele Jahre, wie yfinance liefert.
    Aktuelle Werte tragen in der Ansicht „aktuell, Stand …“. Fehlende Werte bleiben leer.
  - **Ticker:** aus `companies.ticker`; fehlt die Spalte oder der Wert, aus
    `company_metadata.json` über `company_id`, aber nur bei gleichem Namen. Neues Feld
    `ticker_scope` in der Metadatei: „eigene Aktie“ oder „Konzernmutter“, ohne Ticker leer
    (seit 2026-10-08 auch „Konzerngesellschaft“, siehe Sonderfälle).
- **Sonderfälle:**
  - **Konzernmutter:** Für NTT DATA SE wird der Kurs der NTT, Inc. (9432.T, Tokio, JPY)
    gezeigt (E6), `ticker_scope` „Konzernmutter“. Die Ansicht nennt das in Legende und
    Hinweis ausdrücklich; auch die Kennzahlen sind die der Konzernmutter.
  - **Nicht mehr notierte Unternehmen:** Compugroup Medical war im Untersuchungszeitraum
    bis 2025 notiert, yfinance liefert nach dem Delisting aber keine Kurse mehr (E6). Ohne
    Ticker zeigt die Ansicht „Kein Aktienkurs: nicht börsennotiert“, obwohl für frühere Jahre
    ein Kurs existierte. Dasselbe gilt für die frühere NTT DATA Group (9613.T).
  - **Offene Zuordnung:** Carl Zeiss ist dem Ticker der Carl Zeiss Meditec AG (AFX.DE)
    zugeordnet; ob sich das Kununu-Profil auf die Meditec oder die nicht notierte Carl Zeiss
    AG bezieht, ist offen (E6). `ticker_scope` bleibt daher leer; die Ansicht nennt das
    Wertpapier („Carl Zeiss Meditec AG (AFX.DE)“).
    **Entscheidung 2026-10-08 (Autor, D2, Option A):** Die Bewertungen beschreiben den
    Gesamtkonzern (Belege in `docs/offene-punkte-vor-inkrement-4.md`, D2: Nennungen von SMT,
    Oberkochen und Stiftung deutlich häufiger als Meditec; Profilpfad `carl-zeiss`). Der Ticker
    AFX.DE bleibt, `ticker_scope` ist „Konzerngesellschaft“ (dritter erlaubter Wert,
    `TICKER_SCOPES` in `backend/services/context_service.py`). Die Ansicht nennt in Legende,
    Untertitel und Hinweis ausdrücklich „Kurs der börsennotierten Konzerngesellschaft Carl Zeiss
    Meditec AG (AFX.DE), nicht des Gesamtkonzerns Carl Zeiss, den die Bewertungen beschreiben“.
    Nicht gewählt: Ticker entfernen (hätte zusätzlich einen Schreibzugriff auf
    `companies.ticker` verlangt) und „eigene Aktie“ (durch die Bewertungen nicht gedeckt).
- **Begründung:** Der Monatsschluss passt zur Auflösung der Bewertungsreihe (Monatsmittel,
  E3). Bereinigte Kurse vermeiden Sprünge durch Splits, die wie Kursbewegungen aussähen. Der
  Zwischenspeicher macht die Ansicht unabhängig von der Erreichbarkeit von Yahoo Finance,
  hält Kursdaten Dritter aus dem Repository und macht den Stand über `fetched_at`
  nachvollziehbar. Eine Korrelation wurde bewusst nicht berechnet: Die Bewertungsreihen sind
  lückenhaft, der Kurs hängt von vielen gleichzeitigen Einflüssen ab, und ein Zusammenhangsmaß
  würde in der Ansicht leicht als Erklärung gelesen.
- **Grenzen der Kennzahlen:** Marktkapitalisierung und Mitarbeitende sind nur als aktueller
  Wert verfügbar, nicht für frühere Zeiträume; sie dürfen nicht auf den Zeitpunkt einer
  Veränderung bezogen werden. yfinance nennt für die Mitarbeitenden kein Stichtagsdatum. Der
  Umsatz reicht nur etwa vier Geschäftsjahre zurück (Stand 2026-10-04: 2022 bis 2025, bei
  NTT bis 03/2026), der Bewertungszeitraum meist weiter. Bereinigte Kurse ändern sich
  rückwirkend mit jeder Dividende; ein neuer Abruf kann ältere Werte leicht verschieben.
  Ein Konzernkurs bildet ein Tochterunternehmen nur mittelbar ab; umgekehrt bildet der Kurs
  einer Konzerngesellschaft (Carl Zeiss Meditec AG) das Profil des Gesamtkonzerns nur zum Teil ab.
- **Offen:** Nutzungsbedingungen von Yahoo Finance für die Verwendung in der Arbeit (Abbildungen,
  Weitergabe der Daten; Fundstellen und Fragen in `docs/nutzungsbedingungen.md`); ob für
  Compugroup historische Kurse aus einer anderen Quelle nachgetragen werden. Die Zuordnung Carl
  Zeiss ist seit 2026-10-08 entschieden (Sonderfälle).
- **Nachtrag 2026-10-05 (Kurs auf der Anomalien-Seite):** Der Kurs ist auf der
  Anomalien-Detailseite wieder einblendbar, **Standard aus**. Hat das Unternehmen einen Ticker
  (Firmenliste), steht im Kopf des Abschnitts „Monatsverlauf“ das Kästchen „Aktienkurs“; der
  Zustand steht in der Adresse (`?kurs=an`). Erst dann wird `/market` geladen. Der Kurs folgt
  dem gewählten Zeitraum und bleibt beim Wechsel von Quelle, Status und Dimension erhalten;
  Markierungen, Vergleichsfenster, Klick und Ziehen funktionieren wie ohne Kurs. Unter dem
  Diagramm stehen dann der feste Hinweis, bei der Konzernmutter der ausdrückliche Vermerk und
  die Quelle; der Link zum Aktien-Dashboard bleibt. Ohne Ticker gibt es kein Kästchen, nur den
  Link. Die Dashboard-Karte bleibt ohne Kurs. Es gibt weiterhin keine Korrelation und keine
  Aussage über einen Zusammenhang.
  **Begründung:** Das Exposé beschreibt eine integrierte Darstellung aus Bewertungsverlauf mit
  Anomalien, Erklärungsansätzen, Aktienkursverlauf und Kennzahlen (TF4); seit dem Nachtrag in
  E16 vom 2026-10-04 stand der Kurs nur auf `/aktie`. Standard aus, damit die Seite ohne Zutun
  übersichtlich bleibt.
- **Status:** vorläufig.

## E16 – Aktien-Dashboard

- **Kontext:** Der Autor wünschte am 2026-10-04 ein eigenes Dashboard zum Aktienkurs mit
  den Elementen Kursverlauf, Analystenempfehlungen, Umsatz und Gewinn („Revenue vs.
  Earnings“) und Nachrichten, angelehnt an die Kursseite von Yahoo Finance. Die
  Finanzseite der Test-Kopie (E1) hing an Tabellen, die am 2026-10-02 gelöscht wurden; sie
  wurde daher nicht übernommen, sondern auf dem Kursdienst aus E15 neu gebaut.
- **Entscheidung (2026-10-04):**
  - Eigene Seite `/aktie?company=ID` (Link „Aktie“ in der Seitenleiste des Dashboards und
    auf der Anomalien-Detailseite). Firma, Zeitfenster (`range`, `verlauf`), Kurs an oder
    aus (`kurs=aus`) und Jahres- oder Quartalsansicht (`periode=quartal`) stehen in der URL.
  - **Kurs und Bewertungsverlauf (Nachtrag 2026-10-04, Wunsch des Autors):** Das Diagramm
    aus E15 (Monatsverlauf der Gesamtbewertung der Mitarbeitenden mit auffälligen
    Veränderungen, Kurs auf der rechten Achse) steht nur noch hier, nicht mehr auf der
    Anomalien-Detailseite. Diese zeigt unter ihrem Diagramm einen Link zum Aktien-Dashboard
    und bleibt sonst wie vor Inkrement 3. Ein Klick auf eine Markierung öffnet die
    Veränderung auf der Anomalien-Seite. (Seit 2026-10-05 lässt sich der Kurs auf der
    Anomalien-Seite wieder einblenden, Standard aus; siehe Nachtrag in E15.)
  - **Kursverlauf:** die bereinigten Monatsschlusskurse aus E15, Fenster 1, 3, 5 (Standard),
    10 Jahre oder alles; dazu die Kennzahlenzeile, Quelle und der Hinweis aus E15.
  - **Analystenempfehlungen:** `yfinance.Ticker.recommendations`, Zahl der Empfehlungen je
    Stufe (stark kaufen, kaufen, halten, verkaufen, stark verkaufen) für den Monat des
    Abrufs und die drei Monate davor; yfinance nennt die Monate relativ (`0m`, `-1m`), sie
    werden auf den Monat des Abrufs bezogen.
  - **Umsatz und Nettoergebnis:** „Total Revenue“ und „Net Income“ aus
    `income_stmt` bzw. `quarterly_income_stmt` in Berichtswährung. Ein Zeitraum entfällt
    nur, wenn beide Werte fehlen.
  - **Nachrichten:** Google-News-RSS mit dem Unternehmensnamen ohne Rechtsform, deutsch,
    letzte 90 Tage, höchstens 30 Meldungen, neueste zuerst (Quelle nach E7). yfinance liefert
    für keinen der 17 Ticker Nachrichten (geprüft 2026-10-04). Zwischenspeicher
    `backend/data/market/news/<company_id>.json`, nach 12 Stunden neu abgerufen; schlägt
    das fehl, gilt der ältere Stand mit Hinweis.
  - Endpunkte `GET /api/analytics/company/{id}/finance` (Kurs, Kennzahlen, Empfehlungen,
    Umsatz und Gewinn) und `GET /api/analytics/company/{id}/news`; `/market` bleibt
    unverändert. Datenbank nur lesend, keine neuen Abhängigkeiten.
- **Rolle in der Arbeit (Nachtrag 2026-10-05):** Kurs und Kennzahlen decken FA-15 (Kurs und
  zwei bis drei Kennzahlen: Marktkapitalisierung, Mitarbeitende, Umsatz aus E15). Die übrigen
  Karten – Analystenempfehlungen, Umsatz und Nettoergebnis, Aktuelle Meldungen – und ihre
  Kacheln (Nettoergebnis, Analysten) sind ein Zusatz ohne Anforderung aus den Interviews und
  gehören nicht zum evaluierten Artefakt. Für die Evaluationsinstanz lassen sie sich
  ausblenden, indem das Frontend mit `VITE_SHOW_FINANCE_EXTRAS=false` gebaut wird (Standard
  an, also wie bisher). Die Seite zeigt dann Kurs, Kurs mit Bewertungsverlauf, die Kennzahlen aus FA-15
  und den Hinweis aus E15; sie ruft `/market` statt `/finance` und `/news` nicht ab, und die
  Kurskarte nimmt die ganze Fläche ein. Die Einträge oben beschreiben die Seite, wie sie am
  2026-10-04 entstand, und bleiben als Verlauf stehen.
- **Begründung:** Die Seite sammelt die Marktinformationen an einer Stelle, ohne die
  Anomalien-Ansicht zu überladen. Sie bleibt eine Einordnung: Es gibt keine Verknüpfung von
  Empfehlungen, Gewinn oder Meldungen mit den Bewertungen, keine Bewertung der Meldungen und
  keine Zuordnung zu auffälligen Veränderungen. Kurs und Empfehlungen werden nicht
  kommentiert; die Seite gibt keine Anlageempfehlung.
- **Grenzen:** Empfehlungen gibt es nur für die letzten vier Monate, Umsatz und Gewinn nur
  für etwa vier Geschäftsjahre bzw. sechs Quartale (bei NTT und Formycon keine Quartale);
  der Bewertungszeitraum reicht weiter zurück. Die Nachrichten sind aktuell und reichen nicht
  in die Zeiträume der auffälligen Veränderungen zurück. Die Namenssuche liefert bei
  mehrdeutigen Namen fremde Treffer (z. B. „Carl Zeiss“ auch den FC Carl Zeiss Jena) und bei
  sehr kleinen Unternehmen keine (PLEdoc). Für NTT DATA SE stammen Kurs, Empfehlungen und
  Zahlen von der Konzernmutter, die Nachrichten von der Suche nach „NTT DATA“.
- **Offen:** Nutzungsbedingungen von Yahoo Finance und Google News für die Arbeit (wie E7,
  E15); ob die Seite in der Evaluation (DZ3) gezeigt wird. Nachtrag 2026-10-05: Kurs und
  Kennzahlen gehören zum evaluierten Artefakt, die Zusatzkarten nicht (Rolle in der Arbeit);
  Nachtrag 2026-10-08: entschieden, siehe Entscheidung D3.
- **Entscheidung 2026-10-08 (Autor, D3):** Die Evaluationsinstanz für die Interviews (DZ3) wird
  mit `VITE_SHOW_FINANCE_EXTRAS=false` gebaut (Variante B in `docs/evaluationsinstanz.md`). Die
  Befragten sehen auf `/aktie` nur Kurs, Kurs mit Bewertungsverlauf und die Kennzahlen aus
  FA-15 mit dem festen Hinweis; `/finance` und `/news` werden nicht abgerufen. Die Zusatzkarten
  bleiben im Standardbau außerhalb der Evaluation erhalten. Der Hinweistext des Eintrags „Aktie“
  in der Seitenleiste richtet sich seit 2026-10-08 nach dem Schalter. Einstellungen und die
  Prüfliste für den Tag vor einem Interview stehen in `docs/evaluationsinstanz.md`.
- **Status:** vorläufig (Nutzungsbedingungen offen); Evaluationsinstanz entschieden.

## E17 – Freier Drill-down und Vergleich mit dem Zeitraum davor

- **Kontext:** Der Drill-down aus Inkrement 2 setzt eine erkannte Veränderung oder einen
  auffälligen Einzelmonat voraus. Viele Reihen haben keine (Mitarbeitende, Gesamtbewertung:
  Cancom, Thyssenkrupp, Carl Zeiss, KIT, TU München, Open Grid Europe), und nicht geeignete
  Reihen (E4) werden gar nicht erkannt. Der Autor möchte die Bewertungen trotzdem bei
  Bedarf ansehen (2026-10-05).
- **Entscheidung (Autor, 2026-10-05):** Auf der Detailseite lässt sich jeder Zeitraum frei
  wählen: Klick auf einen Monat, Ziehen über mehrere Monate im Diagramm oder Auswahlfeld
  „von / bis“ mit Schnellwahl (letzter Monat, letzte 6 bzw. 12 Monate). Die Auswahl steht
  in der Adresse (`?from=YYYY-MM&to=YYYY-MM`) und bleibt beim Wechsel von Quelle, Status
  und Dimension erhalten. Darunter stehen
  - der **Vergleich mit dem Zeitraum davor**: Auswahl gegen die gleich vielen
    Kalendermonate direkt davor, mindestens 6 (`period_windows` in
    `backend/services/explanation_service.py`, `GET
    /api/analytics/company/{id}/compare?from=&to=&source=&dimension=&status=`). Kennzahlen,
    Themen, Stimmung, kleine Basis und Stichprobe wie beim Vorher-Nachher-Vergleich
    (E10–E12),
  - die **Bewertungen der Auswahl** (umschaltbar auf den Zeitraum davor), mit Markierung
    des Themas der Dimension.
  Ein Klick auf eine Stufe wählt weiter die erkannte Veränderung mit ihren Fenstern (E12),
  ein Klick auf eine Raute den Einzelmonat als Auswahl.
- **Begründung:** Der Drill-down ist ein Werkzeug zum Nachsehen, nicht an die Erkennung
  gebunden. Ein gleich langer Zeitraum davor ist die naheliegende Bezugsgröße; mindestens 6
  Monate, damit ein einzelner Monat gegen eine stabile Basis verglichen wird (wie die
  Fensterlänge in E12).
- **Grenzen:** Der Vergleich einer frei gewählten Auswahl ist keine erkannte Veränderung.
  Wer eine Auswahl wegen eines sichtbaren Einbruchs wählt, vergleicht gezielt; Unterschiede
  sind dann erwartbar und kein Beleg. Die Hinweise zu kleiner Basis und Ursachen gelten
  unverändert.
- **Status:** vorläufig (Mindestlänge 6 Monate ist eine Setzung).


## E18 – Ereignisfenster und Belegspeicher (Inkrement 4)

- **Kontext:** Inkrement 4 „Externe Belege im Ereignisfenster“ stellt zu einer auffälligen
  Veränderung, einem auffälligen Einzelmonat oder einer frei gewählten Auswahl zeitlich nahe
  Meldungen aus externen Quellen (E7). Ein Beleg ist eine Meldung mit Datum, Titel, Herausgeber
  und Link; er ist keine Ursache, die Oberfläche behauptet keinen Zusammenhang und bewertet
  keine Meldung. Die Roadmap sah für Kontext und Erklärungen Datenbanktabellen (Migrationen 007
  und 008) vor.
- **Entscheidung (2026-10-08):**
  - **Ereignisfenster (vorläufig):** Für einen Niveauwechsel reicht das Fenster von
    `window_before` = 3 Monaten vor dem Beginn des Übergangs bis `window_after` = 1 Monat nach
    `date`. Der Beginn des Übergangs ist der Monat nach `previous_period` (dem letzten bewerteten
    Monat vor `date`); ohne Lücke ist das `date` selbst, am Reihenrand ohne Vormonat ebenfalls.
    Für einen Einzelmonat und eine freie Auswahl gelten dieselben Abstände um den Monat bzw. den
    Zeitraum. Beide Größen sind Parameter der Routen (0 bis 24 Monate). Umsetzung:
    `backend/services/evidence_service.py` (`window_for_change`, `window_for_outlier`,
    `window_for_selection`).
  - **Belegspeicher:** Meldungen werden je Unternehmen, Quelle und Kalendermonat als Datei
    abgelegt (`backend/data/context/<company_id>/<quelle>/<YYYY-MM>.json`, in `.gitignore`), nicht
    je Veränderung. Die Belege eines Fensters sind alle gespeicherten Meldungen, deren Datum im
    Fenster liegt. Abgeschlossene Monate werden nicht erneut abgerufen, der laufende Monat
    frühestens nach 12 Stunden; ein geänderter Suchbegriff macht einen gespeicherten Monat
    ungültig. Doppelte Meldungen (gleicher Link oder gleicher normalisierter Titel) zählen einmal.
    Fehlgeschlagene Abrufe werden nicht gespeichert und 15 Minuten lang nicht wiederholt.
  - **Abweichung von der Roadmap:** Dateispeicher je Monat statt der Tabellen 007 und 008, weil
    die Erkennung noch nicht gegen Referenzzeiträume kalibriert ist (E5, E9) und sich Monate,
    Parameter und Markierungen daher noch ändern; ein Speicher je Monat bleibt dabei gültig. Die
    Datenbank wird in Zyklus 2 nur gelesen (E1, keine Migration).
  - **Routen:** `GET /api/analytics/company/{id}/anomalies/{anomaly_id}/context` (auch für die
    Kennung eines Einzelmonats `…:einzelmonat`) und `GET /api/analytics/company/{id}/context?from=&to=`
    mit `window_before`, `window_after`, `limit`, `offset`; Antwort mit Fenster, Belegen (neueste
    zuerst, seitenweise), Anzahl je Typ, Stand und Fehlern je Quelle und `coverage`. Unbekannte
    Veränderung 404; ohne Daten eine leere Liste mit Grund, kein 500.
  - **Ansicht:** Abschnitt „Externe Belege im Ereignisfenster“ auf der Detailseite unter dem
    Vergleich, mit festem Hinweis: „Belege sind zeitlich nahe Meldungen aus externen Quellen. Sie
    sind keine Aussage über Ursachen; interne Auslöser sind von außen nicht sichtbar.“ Keine
    Rangfolge nach Erklärungskraft, keine thematische Zuordnung, keine Stimmung (Inkrement 5).
  - **Vorabruf und Betrieb:** `backend/scripts/fetch_context.py` füllt den Speicher für alle
    Markierungen der geeigneten Unternehmen (gedrosselt, fortsetzbar); `CONTEXT_LIVE_FETCH=0`
    unterbindet jeden Abruf zur Laufzeit.
- **Begründung:** Drei Monate vor dem Übergang decken die Reaktionszeit ab, die die Literatur
  für Arbeitgeberbewertungen nennt (Reaktion innerhalb des Folgequartals, Green et al. 2019 in
  `docs/referenzzeitraeume-literatur.md`), ein Monat danach fängt Meldungen ein, die auf die
  Veränderung folgen; bei einer Lücke beginnt das Fenster vor der Lücke, weil der Übergang
  irgendwo darin liegen kann. Der Speicher je Monat trennt Abruf und Erkennung und hält die
  Zahl der Abrufe klein (eine Abfrage je Unternehmen, Quelle und Monat).
- **Vergleichsfenster (2026-10-08, Nachschärfung A1, vorläufig):** Die Prüfung vom 2026-10-08
  ergab rund 14 Meldungen je Unternehmensmonat; große Unternehmen haben in fast jedem Fenster
  eine Meldung, die Abdeckung allein unterscheidet kaum. Deshalb gehören zu jeder Markierung mit
  Ankermonat m bis zu drei Vergleichsfenster desselben Unternehmens: das Fenster der Markierung
  um −12, +12, −24, +24 Monate verschoben, in dieser Reihenfolge geprüft, gleiche Länge und Lage
  zum Anker. Ein Vergleichsfenster entfällt, wenn es ein Fenster einer Markierung dieses
  Unternehmens überschneidet (auch das eigene) oder nicht vollständig in der bewerteten Reihe
  liegt (`comparison_windows` in `backend/services/evidence_service.py`;
  `scripts/report_context_coverage.py --comparison`; Vorabruf `scripts/fetch_context.py
  --comparison`). ±12 und ±24 Monate halten Jahreszeit und Berichtskalender gleich. Fenster mit
  fehlenden Monaten im Speicher werden ausgewiesen und nicht als „kein Beleg“ gezählt.
- **Befund (2026-10-08, `backend/data/calibration/context_coverage_vergleich_2026-10-08.json`):**
  28 von 28 Markierungsfenstern und 76 von 76 Vergleichsfenstern haben mindestens einen Beleg
  (Meldung oder Ad-hoc-Mitteilung; allgemeine Ereignisse zählen nicht); die Mediane der Belege je
  Fenster liegen in derselben Größenordnung (Markierung 45, Vergleich 47,5), je Unternehmen mal
  über, mal unter dem Vergleich. Die Abdeckung allein ist deshalb kein Gütemaß für die Belege: In
  der Zahl der Meldungen unterscheidet sich ein Markierungsfenster nicht erkennbar von einem um
  ein oder zwei Jahre verschobenen Fenster desselben Unternehmens. Die Unterscheidung liefert
  erst die thematische Korrespondenz in Inkrement 5. Die Zahlen sind beschreibend, ohne
  Signifikanzaussage; ein Unterschied sagt nichts über Ursachen und nichts darüber, ob
  Markierungen Meldungen „auslösen“.
- **Abruf (2026-10-08, Nachschärfung A2):** Die Quellen werden nebeneinander abgerufen, je
  Quelle ein Strang; der Mindestabstand von 2 Sekunden gilt je Quelle (Sperre je Quelle). Erster
  Abruf eines Fensters von fünf Monaten mit zwei Quellen: 16,6 s vorher, 9,8 s nachher. Während
  eines ersten Abrufs nennt der Abschnitt nach zwei Sekunden den Grund der Wartezeit.
  `fetch_context.py --from-month` lädt alle Monate eines Unternehmens ab einem Startmonat; nach
  drei Fehlern in Folge einer Quelle (etwa Status 429 oder 503) bricht der Lauf für diese Quelle
  ab und nennt die Stelle zum Fortsetzen. Vorabruf vom 2026-10-08
  (`context_prefetch_nachschaerfung_2026-10-08.json`): Vergleichsfenster aller elf Unternehmen mit
  Markierungen und alle Monate ab 2019-01 für die acht Unternehmen mit Markierungen ab 2019
  (Autor, D4); 1463 Abrufe in 27 Minuten, ein Zeitüberschreitungsfehler, nachgeholt.
- **Bestätigung (Autor, 2026-10-08, D1 und D2):** Suchbegriffe der elf Unternehmen mit
  Markierungen bestätigt, NTT DATA SE erweitert auf `"NTT DATA" OR "NTT Data Deutschland" OR
  itelligence` (der Niveauwechsel 2017-11 hat damit einen Beleg; die 27 Markierungsmonate liefern
  mit dem neuen Begriff 26 statt 54 Meldungen); EQS-companyUUIDs der elf Emittenten bestätigt.
- **Grenzen:** Die Fenstergrößen und die Versätze der Vergleichsfenster sind Setzungen des Autors
  ohne Kalibrierung. Google News liefert höchstens rund 100 Einträge je Abfrage, für ältere
  Zeiträume und kleine Unternehmen oft wenige oder keine; mehrdeutige Namen bringen fremde
  Treffer. Ein fehlender Beleg heißt nicht, dass nichts geschehen ist; ein Vergleich der Anzahlen
  sagt nichts über den Inhalt der Meldungen.
- **Status:** vorläufig (Fenstergrößen 3 und 1 Monat sowie Versätze ±12/±24 Monate als Setzung);
  Suchbegriffe und UUIDs der Unternehmen mit Markierungen bestätigt (2026-10-08).

## E19 – Quellenarten und Verlässlichkeit der Belege

- **Kontext:** Belege stammen aus Quellen unterschiedlicher Art; die Ansicht soll das sichtbar
  machen, ohne Meldungen zu bewerten oder zu ordnen.
- **Entscheidung (2026-10-08):** Jeder Beleg trägt `source_type` und eine Verlässlichkeitsstufe:
  - `adhoc` (EQS News: Ad-hoc-, Stimmrechts-, Finanzberichts- und weitere Pflicht- oder
    Unternehmensmitteilungen des Emittenten) → `hoch`; der Beleg nennt den Emittenten
    (`issuer`), damit bei Konzernmutter (NTT DATA SE, kein EQS-Emittent) oder
    Konzerngesellschaft (Carl Zeiss → Carl Zeiss Meditec AG) sichtbar bleibt, zu welcher
    Gesellschaft er gehört;
  - `news` (Google News RSS; GDELT hinter dem Schalter) → `mittel`;
  - `global` (bestätigte allgemeine Ereignisse, E20) → `hypothese`;
  - `market` ist reserviert und wird nicht erzeugt.
  Die Sprache je Titel wird mit der Stoppwort-Heuristik aus dem Spike geschätzt
  (`de`, `en` oder unbestimmt; EQS und GDELT melden die Sprache selbst); englische Meldungen
  tragen in der Ansicht die Kennzeichnung „EN“. EQS liefert in der Listenroute die englische
  Fassung einer Meldung; die deutsche Fassung existiert, ihr Abruf bräuchte eine Detailanfrage je
  Meldung und unterbleibt. Innerhalb eines Fensters gibt es keine Rangfolge nach
  Erklärungskraft, keine thematische Zuordnung und keine Stimmung der Meldungen; das folgt in
  Inkrement 5.
- **Begründung:** Pflichtmitteilungen sind datiert, vom Unternehmen selbst verantwortet und
  präzise, Nachrichtenmeldungen sind breiter, aber mit Streutreffern; allgemeine Ereignisse
  betreffen viele Unternehmen zugleich und sind nur eine Hypothese. Die Stufen beschreiben die
  Art der Quelle, nicht den Wahrheitsgehalt einer Meldung.
- **Status:** vorläufig (Stufen sind Setzungen des Autors).

## E20 – Allgemeine Ereignisse

- **Kontext:** Manche Zeiträume betreffen viele Unternehmen zugleich (Pandemie, Energiekrise);
  sie sollen als Hypothese sichtbar sein, ohne als Ursache zu gelten.
- **Entscheidung (2026-10-08):** `backend/data/global_events.json` führt allgemeine Ereignisse mit
  `date_from`, `date_to`, `title`, `scope`, `note`, `url` und `confirmed`. Der Entwickler hat acht
  Vorschläge mit belegender Adresse angelegt (Finanzkrise 2008/09, Atom-Moratorium 2011, zwei
  Corona-Lockdowns, Homeoffice-Pflicht 2021, Überfall auf die Ukraine 2022, Energiepreiskrise und
  Inflationshoch 2022/23, Rezession 2023/24), alle `confirmed: false`; nur vom Autor bestätigte
  Ereignisse werden gezeigt. Bestätigte Ereignisse erscheinen als Belege vom Typ `global`
  (Verlässlichkeit `hypothese`) und als einblendbares Overlay im Diagramm der Detailseite
  (Kästchen „Allgemeine Ereignisse“, `?ereignisse=an`, Standard aus), beschriftet als
  „Allgemeines Ereignis, Hypothese“. Route `GET /api/analytics/global-events`.
- **Begründung:** Ein Overlay macht sichtbar, ob eine Markierung in einen allgemeinen Zeitraum
  fällt, ohne die Ansicht ohne Zutun zu verändern; die Bestätigung durch den Autor hält die
  Auswahl bei ihm.
- **Dauerregel (2026-10-08, Nachschärfung A3, vorläufig):** Ein allgemeines Ereignis dauert
  höchstens 6 Monate (`MAX_GLOBAL_EVENT_MONTHS` in `backend/services/evidence_service.py`); der
  Lader weist längere Einträge mit Warnung zurück, ein Test prüft die Repository-Datei. Grund: Ein
  vorgeschlagenes Ereignis über 24 Monate (Konjunkturschwäche 2023/24) hinge an fast jeder
  Markierung dieser Jahre und wäre als Hypothese wertlos; ein allgemeines Ereignis muss datierbar
  sein. Überarbeitung der Vorschläge: Finanzkrise auf 2008-09 bis 2009-02, zweiter Lockdown auf
  2020-11 bis 2021-03 und Energiepreiskrise auf 2022-08 bis 2023-01 verkürzt (jeweils mit
  belegender Adresse), die Konjunkturschwäche 2023/24 gestrichen. Allgemeine Ereignisse zählen in
  der Abdeckung (`report_context_coverage.py`, Feld `coverage` der Routen) nicht als Beleg; die
  Auswertung weist sie getrennt aus.
- **Bestätigung (Autor, 2026-10-08, D3):** sechs Ereignisse bestätigt (Finanzkrise 2008/09,
  Atom-Moratorium 2011, erster und zweiter Lockdown, Überfall auf die Ukraine 2022,
  Energiepreiskrise 2022/23); die Homeoffice-Pflicht 2021 bleibt unbestätigt, weil sie den
  zweiten Lockdown überschneidet.
- **Grenzen:** Ein zeitliches Zusammentreffen ist keine Erklärung; auch sechs Monate treffen
  mehrere Fenster. Die Liste ist eine Auswahl, keine Vollständigkeit.
- **Status:** vorläufig (Dauergrenze ist eine Setzung); sechs Ereignisse bestätigt (2026-10-08).
