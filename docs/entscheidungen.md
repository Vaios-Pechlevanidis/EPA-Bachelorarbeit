# Entscheidungen Zyklus 2 – Inkrement 0 „Fundament“, Inkrement 1 „Anomalien im Verlauf“ und Inkrement 2 „Drill-down und Vorher-Nachher-Vergleich“

Stand: 2026-10-04 (E1–E8 vom 2026-10-02, E5 aktualisiert und E9 neu am 2026-10-03, E9 aktualisiert und E10–E13 neu am 2026-10-04). Jede Entscheidung nennt Kontext, Entscheidung, Begründung und Status.
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
- **Status:** vorläufig.

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
- **Status:** vorläufig (Zuordnung der Rohwerte vom Autor zu bestätigen).
