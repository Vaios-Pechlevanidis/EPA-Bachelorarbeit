# 16 – Qualität des Analytics Reports: Befund und Korrekturen

| | |
|---|---|
| Inkrement | Prüfung und Korrektur des PDF-Berichts und der zugrunde liegenden Kennzahlen (2026-10-17) |
| Anforderungen | Prüfauftrag des Autors (2026-10-17): Kennzahlen mathematisch korrekt, konsistent und nachvollziehbar; Zeitreihe, Prognose, Topics und Stimmung methodisch sauber; Unsicherheit und Datenqualität sichtbar; Zusammenfassung mit Datenstand, Stärken, Handlungsfeldern, Warnungen, Grenzen und nächsten Schritten |
| Entscheidungen | keine neue Entscheidung in `docs/entscheidungen.md` (die Datei wird parallel in einer anderen Sitzung bearbeitet); Setzungen dieses Dokuments sind unten als „vorläufig“ markiert und können vom Autor als E33 ff. übernommen werden |
| Status | Befund (Abschnitt 1) und Korrekturen (Abschnitte 2 bis 5) umgesetzt am 2026-10-17, nicht committet; offene Entscheidungen des Autors in Abschnitt 6 |
| Stand | 2026-10-17 |

## 1. Befund

Grundlage: Code in `backend/services/` und `backend/routes/`, die Tabellen `employee` und
`candidates` (Schema `supabase/init/02-migrations.sql`), der PDF-Export
(`frontend/src/utils/pdfExport.js`), die Dashboard-Karten und ein lesender Abgleich gegen
die laufende Datenbank (1&1 AG, Stand 2026-10-17). Testbasis vor Änderungen: 1430 Tests
grün (`uv run pytest`).

### 1.1 Was bereits trägt

- **Eine Definition für die Gesamtbewertung.** Ø Score, Trend, rollierende Schnitte,
  Zeitverlauf (Monatsmittel) und Erkennung nutzen dieselbe Spalte
  (`durchschnittsbewertung`, nur Mitarbeitende), leere Werte werden überall übersprungen
  (`score_service.py`, `rolling_average_service.py`, `rating_series_service.py`; E26).
- **n und kleine Basis** stehen an jeder Kachel (E27); die Erkennung ist gegen
  Referenzzeiträume und gegen Zufall geprüft, mit Intervallen (E9 Nachtrag 2026-10-13,
  E30); Einzelmonate sind als „ungeprüft“ gekennzeichnet.
- **Keine Kausalaussagen**: jede Seite trägt den Satz „keine Aussage über Ursachen“.

### 1.2 Konkrete Probleme (mit Beleg)

| Nr. | Problem | Beleg | Priorität |
|---|---|---|---|
| B1 | **„Sentiment“ der Topics ist keine Textanalyse, sondern eine Sterneklasse.** Die Einstufung Positiv / Neutral / Negativ entsteht aus dem Ø der Sternebewertung der Bewertungen, die das Thema nennen (Schwellen 3,5 / 2,5). Tabelle, Stats-Strip, Kurzbericht („Stimmung“) und PDF nennen sie „Sentiment“ bzw. „Stimmung“. | `keyword_topic_service.py`, `rating_class`, Kommentar „keine Textanalyse“; PDF Topic-Tabelle Spalte SENTIMENT | hoch |
| B2 | **Einstufung auf dem gerundeten Mittel.** `avgRating` wird auf eine Nachkommastelle gerundet und erst dann eingestuft; 3,45 wird so zu 3,5 = „Positiv“. Zudem verdeckt die Klasse des Mittels die Verteilung: Gehalt & Sozialleistungen (1&1) ist „Neutral“ (Ø 2,6) bei 101 negativen, 40 neutralen und 56 positiven Bewertungen. | `analyze_topic`: `avg_rating = round(…, 1)` vor `rating_class(avg_rating)`; API-Abgleich 2026-10-17 | hoch |
| B3 | **Gehalt: Kategorie 3,08 gegen Topic 2,6.** Unterschiedliche Nenner: die Kategorie mittelt den Stern „Gehalt/Sozialleistungen“ über alle 1.245 Bewertungen mit diesem Wert; das Topic mittelt denselben Stern nur über die 197 Bewertungen, deren Freitext ein Gehalts-Schlüsselwort enthält (3 davon ohne Kategoriewert, dann Gesamtnote). Wer über Gehalt schreibt, bewertet es schlechter. Der Bericht erklärt das nirgends. | `routes/companies.py` (`get_company_ratings_avg`), `analyze_topic` (`rating_fields`, Fallback `durchschnittsbewertung`); Werte aus `GET /ratings/avg` und `GET /topic-overview` | hoch |
| B4 | **Drei „Durchschnitte“ ohne Erklärung.** Ø Score 3,37 (Mittel aller Bewertungen), „Ø Historisch“ 3,16 (ungewichtetes Mittel der 106 Monatsmittel, 10-Jahres-Fenster; gewichtet wären es 3,28), „Ø Rating“ 2,99 der Topic-Übersicht (ungewichtetes Mittel der 23 Topic-Mittel, beschriftet mit „1.486 Bewertungen“). | `TimelineCard.jsx` (`avgHistorical`), `TopicOverviewCard.jsx` (`stats.avg`), PDF Stats-Strips | hoch |
| B5 | **Monate mit sehr wenigen Bewertungen zählen im Zeitverlauf und in der Prognose voll.** Bei 1&1 haben 33 der 106 Monate weniger als 5 Bewertungen (Minimum 1); die Monatsmittel gehen ungewichtet in „Ø Historisch“ und in Holt ein. Die Erkennung dagegen lässt solche Monate aus (E4). | `routes/analytics.py` (`get_company_timeline`), API-Abgleich | mittel |
| B6 | **Prognose ohne Validierung und ohne Unsicherheit.** Holt (statsmodels, α und β geschätzt) auf den Monatsmitteln, Horizont 6 Monate, Werte mit zwei Nachkommastellen, kein Intervall, kein Backtest auf echten Reihen (die vorhandenen Tests nutzen synthetische Reihen), keine Baseline. Monate ohne Bewertungen werden übersprungen; Holt setzt gleiche Abstände voraus. Die Prognose endet Jan. 2026, der Bericht trägt das Datum 17.10.2026: die Daten enden im Juli 2025, der Bericht sagt das nicht. | `forecast_with_details`, `tests/forecast/test_forecast_backtest.py` (synthetisch), `ForecastExplanation.jsx` | hoch |
| B7 | **Unsicherheit der Kennzahlen fehlt.** Ø Score, Trend-Differenz und Vergleichsfenster haben n, aber kein Intervall; `statistical_meta.ci_width_estimate` ist eine Faustformel mit angenommener Streuung 1,0, nicht aus den Daten gerechnet. | `statistical_validator.py` (`assumed_std=1.0`), `score_service.py` | mittel |
| B8 | **Duplikate und fehlende Werte sind nicht dokumentiert.** Lesender Abgleich 2026-10-17: 26 exakt doppelte Mitarbeiter-Zeilen (Telekom 20, 1&1 3, Cancom 2, Elmos 1), 2 doppelte Bewerber-Zeilen; 3 Mitarbeiter-Zeilen ohne Datum und 3 ohne Gesamtnote; 7 bzw. 7 bei Bewerbenden. Der Datenstand nennt nur „ohne Datum“. Duplikate fließen in alle Mittel ein. | Skript (Scratch) über `database.supabase_client`, nur SELECT | mittel |
| B9 | **Robustheit der Veränderung ab Okt. 2016 (1&1, −0,39) ist nicht ausgewiesen.** Die Erkennung ist über 15 Reihen gegen Referenzzeiträume geprüft (F1 0,43 [0,27; 0,56]), aber je Markierung gibt es keine Angabe, ob sie bei anderen Schwellen (Strafterm, Mindestlänge, Mindestdichte) bestehen bleibt. | `anomaly_service.py` (feste Parameter), `scripts/explore_anomaly_params.py` (nur Zählungen je Unternehmen) | mittel |
| B10 | **Topic-Übersicht „Alle Quellen“ mischt Mitarbeitende und Bewerbende** (1.291 + 195 Bewertungen) mit der Vereinigung beider Themenlisten; der Kopf nennt nur die Summe. | `get_topic_overview` (`reviews_to_analyze = all_reviews`), PDF Kopf „n = 1.486 Bewertungen“ | mittel |
| B11 | **Uneinheitliche Nachkommastellen.** Ø Score 3,4 (Kachel, eine Stelle) gegen 3,37 in der API und zwei Stellen bei Schnitten, Trend und Zeitverlauf; Topic-Mittel eine Stelle. | `KPIGrid.jsx` (`fmt(avgScore)` mit d = 1), `pdfExport.js` (`fmtNum(scoreNum, 1)`) | niedrig |
| B12 | **„Kleine Basis“ der Topics zählt Nennungen nach Literatur-Heuristiken (30/64/100)**, die Konfidenzbreite ist nicht aus den Daten gerechnet; die Stufen „Solide/Akzeptabel/Eingeschränkt/Begrenzt“ wirken präziser, als sie sind. | `statistical_enrichment.py`, `statistical_validator.py` | niedrig |
| B13 | **Kurzbericht ohne Datenstand, Warnungen, Grenzen und nächste Schritte.** Seite 2 nennt weder den letzten Datenmonat noch Duplikate, kleine Basis als Zusammenfassung, die selektive Quelle (freiwillige Plattformbewertungen) oder konkrete Untersuchungsfragen. | `lib/reportSummary.js`, `pdfExport.js` | hoch |
| B15 | **„Topics im Detail“ ist beschriftet mit „Themen aus Freitexten, Bewertung aus Sternen“, rechnet aber die Sterne je Kategorie über alle Bewertungen** (keine Schlüsselwort-Zuordnung); die Linien heißen wie die Topics der Übersicht, haben aber einen anderen Nenner. | `topic_average_rating_service.get_topic_rating_timeseries` (Kategorie-Spalten), PDF-Legende Abb. 2 | mittel |
| B14 | Toter Code: `monthly_ratings` in `analyze_topic` verwendet `avg_rating` vor der Zuweisung; der Fehler wird von `except: pass` verschluckt, das Ergebnis ist ungenutzt. | `keyword_topic_service.py`, Schleife über `review` | niedrig |

Nicht als Problem gewertet: die Kachel „Negativstes Topic“ kommt aus einem anderen
Verfahren (LDA-Themen mit Transformer-Stimmung, `routes/topics.py`), fällt aber auf die
Schlüsselwort-Themen zurück, wenn kein Modell geladen ist; die Fußnote nennt „höchste
Negativrate (Freitexte)“. Das wird in den Technischen Hinweisen benannt, nicht geändert.

### 1.3 Priorisierter Plan

1. **Korrektheit der Kennzahlen (B1–B4, B10, B11, B14):** Einstufung auf dem ungerundeten
   Mittel, Umbenennung „Sentiment/Stimmung“ in „Einstufung nach Ø Sternen“, Nenner je
   Kennzahl sichtbar (Topic-Mittel mit n und Basis, Quellenaufteilung, „Ø der
   Monatsmittel“), Erklärung der Gehalt-Abweichung, zwei Nachkommastellen für Mittel.
2. **Datenqualität (B8):** Duplikate und fehlende Werte je Quelle im Datenstand zählen
   und im Bericht nennen; Entscheidung über das Entfernen bleibt beim Autor.
3. **Unsicherheit (B7, B9):** 95-%-Intervall für Ø Score und Trend-Differenz aus den
   Daten; Stabilität jeder auffälligen Veränderung über ein Raster von Schwellen.
4. **Prognose (B5, B6):** Backtest mit rollierendem Ursprung auf echten Reihen gegen
   naive Baselines (MAE, RMSE), empirische Bandbreite aus den Backtest-Fehlern, Hinweis
   auf den letzten Datenmonat; Verfahren bleibt Holt (keine stillschweigende Änderung).
5. **Kurzbericht (B13):** Datenstand, Warnungen, Grenzen, nächste Analyseschritte mit
   dokumentierter Reihenfolge der Handlungsfelder.
6. **Tests** für jede neue Berechnung; Lint, Build, Export.

Nicht umgesetzt (begründet in Abschnitt 5): Mehrfachbewertungen derselben Person sind in
den Daten nicht identifizierbar (kein Personenschlüssel); Repräsentativität ist nicht
belegbar und wird als Grenze genannt; die Stufen aus der Literatur-Heuristik (B12) bleiben,
werden aber als Heuristik beschriftet.

## 2. Umsetzung (2026-10-17)

Alle Änderungen sind additiv oder korrigieren Beschriftungen; kein Verfahren wurde
stillschweigend ersetzt. Die Standardparameter der Erkennung (E9), die Definition des
Ø Score (E26) und das Prognoseverfahren (E28) sind unverändert.

### 2.1 Backend

| Modul | Änderung | Befund | Tests |
|---|---|---|---|
| `services/score_service.py` | `score_sd`, `score_ci95` (halbe Breite des 95-%-Intervalls des Mittels, t-Verteilung), `difference_ci95` der Trend-Differenz (Welch); reine Funktionen `sample_sd`, `mean_ci95`, `difference_ci95` | B7 | `tests/test_score_uncertainty.py` (8), `test_score_service.py` angepasst (nur Mittel und n geprüft) |
| `services/keyword_topic_service.py` | Einstufung auf dem ungerundeten Mittel; `avgRating` mit zwei Nachkommastellen; je Topic `n_rated` und `rating_basis` (Felder, Zahl mit Kategoriewert, Zahl mit Gesamtnote als Ersatz, Text der Einstufung); toter Code entfernt | B1, B2, B3, B14 | `tests/test_analyze_topic_rating.py` (+2); Regressionstest `tests/drilldown` neu verankert, nachdem der Abgleich alt/neu auf den Demo-Daten nur 13 Rundungsfälle (x,x5) und sonst keine Abweichung ergab |
| `routes/analytics.py` (`topic-overview`) | `total_by_source` (Mitarbeitende / Bewerbende) | B10 | Regressionstest |
| `services/data_status_service.py` | je Quelle `n_duplicates` (Datum, Titel, Gesamtnote, Status und die Freitexte der Quelle gleich) und `n_without_value`; Duplikate werden gezählt, nicht entfernt | B8 | `tests/test_data_status.py` (+3) |
| `services/anomaly_service.py` | `stability_of_anomalies`: je Veränderung Anteil der Parametervarianten (Strafterm-Faktor 1/2/3/4 × Mindestlänge 2/3/4/6 × Mindestdichte 3/5/8 = 48), in denen dieselbe Richtung innerhalb von 3 Monaten erkannt wird; `company_anomalies` liest die Zeilen einmal und ergänzt `stability` (nur im Standardmodus, nicht für `dimension=all`) | B9 | `tests/anomaly/test_stability.py` (4), `test_anomaly_service.py` angepasst |
| `services/forecast_service.py` (neu) | Baselines (letzter Wert, Mittel, Mittel der letzten 6 Monate, Wert 12 Monate zuvor), Backtest mit rollierendem Ursprung (24 Monate Mindestlänge, bis zu 36 Ursprünge, 6 Monate Horizont, nur Daten vor dem Ursprung), MAE und RMSE je Verfahren und Horizont, empirische Bandbreite (80 %) aus den Fehlerquantilen | B6 | `tests/forecast/test_forecast_service.py` (7, darunter ein Leakage-Test) |
| `routes/analytics.py` (`forecast_with_details`) | `backtest`, `interval`, `months_since_last_data`, `months_below_min_reviews`; je Prognosepunkt `low`/`high` | B5, B6 | `tests/forecast/test_forecast_integration.py` (2) |
| `scripts/backtest_forecast.py`, `scripts/report_stability.py` (neu) | Läufe auf echten Reihen, nur lesend; Ergebnisse in `backend/data/calibration/forecast_backtest_2026-10-17.json` und `anomaly_stability_2026-10-17.json` | B6, B9 | – |

### 2.2 Frontend und PDF

| Stelle | Änderung | Befund |
|---|---|---|
| `KPIGrid.jsx`, `pdfExport.js` | Ø Score und Kritischste Kategorie mit zwei Nachkommastellen (wie Trend, Schnitte, Zeitverlauf) | B11 |
| `SorceModal.jsx`, `TrendModal.jsx`, `lib/scoreText.js` | 95-%-Intervall des Ø Score mit Streuung; Intervall der Trend-Differenz mit dem Hinweis, wenn 0 im Intervall liegt; Einordnungssatz (`UNCERTAINTY_NOTE`) | B7 |
| `TopicTableModal.jsx`, `TopicDetailModal.jsx`, `TopicOverviewCard.jsx`, `pdfExport.js` | „Sentiment“ heißt „Einstufung“ (Tooltip: nach Ø Sternen, keine Textanalyse); Topic-Mittel mit zwei Nachkommastellen; „Ø Rating · 1.486 Bew.“ heißt „Ø Topic-Mittel · 23 Topics · ungewichtet“; Kopf nennt bei „Alle Quellen“ beide Anteile | B1, B4, B10, B11 |
| `TimelineCard.jsx`, `ForecastExplanation.jsx`, `pdfExport.js` | „Ø Historisch“ heißt „Ø Monatsmittel“ (n Monate, ungewichtet); Prognose mit einer Nachkommastelle und ±Bandbreite; helle Fläche (80 %) im Diagramm; Erklärung mit Datenstand, Backtest je Verfahren, Bandbreite, Grenzen; Legende von „Topics im Detail“ nennt die Kategorien-Sterne | B4, B5, B6, B15 |
| `lib/dataStatusText.js`, Datenstand-Leiste, PDF | Duplikate und Zeilen ohne Gesamtnote je Quelle | B8 |
| `lib/reportSummary.js`, `pdfExport.js` (Kurzbericht) | Datenstand (letzter Bewertungsmonat je Quelle, Abstand zum Berichtsdatum, Import, Beginn der Prognose); Stabilität je Veränderung (Spalte und Satz); Intervalle in den Zellen; Block „Warnungen“ (Duplikate, begrenzte Basis, Monate unter der Mindestdichte, Prognose schlechter als Baseline, Trend nicht von 0 unterscheidbar, instabile Veränderungen, ungeprüfter Umfang); Block „Nächste Analyseschritte“ (höchstens drei Untersuchungsfragen, als Vorschläge gekennzeichnet); Regeln mit expliziter Reihenfolge, ohne Punktescore | B13 |
| `pdfExport.js` (Technische Hinweise) | Unsicherheit, Zeitverlauf und Prognose (Verfahren, Gewichte, Backtest, Bandbreite), Stabilitätsraster, Herkunft und Nenner der Topics gegen Kategorienmittel, Heuristik der Datenqualitätsstufen, Block „Grenzen“ (selektive Quelle, keine Ursachen, Unabhängigkeit, Schlüsselwörter) | B3, B12, B13 |
| `frontend/package.json` | `vitest` als Entwicklungsabhängigkeit, Skript `npm test`; `src/lib/__tests__/reportSummary.test.js` (11 Tests) | – |

Der Dashboard-Teil der Anomalien (`AnomalyCard.jsx`, `Anomalies.jsx`, `AnomalyDetailCards.jsx`)
wurde nicht angefasst, weil diese Dateien am selben Tag in einer anderen Sitzung
(eigene Ereignisse, [15](15-eigene-ereignisse.md)) bearbeitet wurden; die Stabilität steht
deshalb im PDF und in der API, noch nicht in der Karte und auf der Detailseite (offener Punkt).

### 2.3 Ergebnisse der Läufe (2026-10-17, Datenbankstand 02.10.2026)

**Backtest der Prognose** (`forecast_backtest_2026-10-17.json`; 23 Unternehmen mit mindestens
25 Monaten, 4.071 Prognosen je Verfahren, Horizont 1 bis 6 Monate):

| Verfahren | MAE | RMSE |
|---|---|---|
| Holt (die Prognose des Dashboards) | 0,734 | 1,023 |
| letzter Wert | 0,671 | 0,928 |
| Mittel aller Monate | 0,562 | 0,724 |
| Mittel der letzten 6 Monate | **0,521** | **0,718** |
| Wert 12 Monate zuvor | 0,693 | 0,957 |

Holt ist auf keiner der 23 Reihen das genaueste Verfahren; bei 1&1 AG MAE 0,639 gegen 0,483
(Mittel der letzten 6 Monate). Die Bandbreite (80 %) liegt bei 1&1 im ersten Monat bei
etwa ±0,9 Sternen. Lesart: Die Monatsmittel sind zu verrauscht, als dass ein Trendmodell
etwas gegenüber einer einfachen Fortschreibung gewinnt.

**Stabilität der Veränderungen** (`anomaly_stability_2026-10-17.json`; Mitarbeitende,
Gesamtbewertung, 19 Veränderungen in 11 Unternehmen): mittlerer Anteil 0,53; 4 Veränderungen
ab 0,75 (z. B. Compugroup Aug. 2022: 48 von 48, Freenet Apr. 2016: 44 von 48), 9 unter 0,50.
1&1 AG, Okt. 2016 (−0,39): 20 von 48 Varianten. Die Veränderung ist also nicht robust gegen
die Schwellen; mit größerem Strafterm oder längerer Mindestlänge verschwindet sie, mit
kleinerer Mindestdichte verschiebt sie sich. Das steht jetzt im Bericht neben der Markierung.

**Datenqualität** (Datenstand-API): exakte Duplikate Telekom 20 (Mitarbeitende) und 1
(Bewerbende), 1&1 AG 3, Cancom 2, Elmos 1; Zeilen ohne Gesamtnote je Unternehmen 0 bis 3.

## 3. Begründung

- **Verfahren bleiben, Einordnung kommt dazu.** Der Prüfauftrag verlangt, keine
  Berechnungslogik stillschweigend zu ändern. Prognose und Erkennung sind Setzungen des
  Autors (E9, E28); der Bericht zeigt jetzt, wie gut sie in der Vergangenheit waren
  (Backtest) und wie stark eine Markierung an den Schwellen hängt (Stabilität). Ob Holt
  durch das Mittel der letzten 6 Monate ersetzt oder die Prognose in der Arbeit gestrichen
  wird, ist eine Entscheidung des Autors (Abschnitt 6).
- **Intervalle aus den Daten statt Faustformeln.** Die Streuung der Gesamtnote je
  Unternehmen ist bekannt; ein t-Intervall ist bei n in den Hunderten unproblematisch. Die
  Heuristik-Stufen der Topics (30/64/100) bleiben, werden aber als Heuristik beschriftet,
  weil sie in Tabelle und Detailfenster eingebaut sind.
- **„Einstufung“ statt „Sentiment“.** Das Wort „Sentiment“ behauptet eine Textanalyse, die
  nicht stattfindet; „Einstufung nach Ø Sternen“ sagt, was gerechnet wird. Die Schwellen
  bleiben die der Kacheln.
- **Duplikate zählen, nicht löschen.** Ob zwei gleiche Zeilen ein Importfehler oder zwei
  gleichlautende Bewertungen sind, lässt sich ohne Plattformabgleich nicht sagen; Löschen
  wäre ein Eingriff in die Daten der Arbeit.
- **Bandbreite empirisch.** Holt-Intervalle unter Normalverteilungsannahme wären bei
  übersprungenen Monaten und Deckeneffekten (5 Sterne) nicht gerechtfertigt; Quantile der
  eigenen Backtest-Fehler beschreiben ehrlich, wie weit die Prognose danebenlag.

## 4. Grenzen und nicht Umgesetztes

- Mehrfachbewertungen derselben Person sind nicht identifizierbar (kein Personenschlüssel);
  die Intervalle unterstellen Unabhängigkeit und werden mit diesem Satz ausgewiesen.
- Repräsentativität ist nicht belegbar; der Bericht nennt die Quelle als freiwillig und
  selektiv.
- Holt rechnet weiter auf übersprungenen Monaten (ungleiche Abstände) und auf Monaten mit
  sehr wenigen Bewertungen; beides wird genannt und geht in den Backtest ein, wird aber
  nicht korrigiert.
- Der Backtest bewertet die Prognose nur über 6 Monate und auf den letzten 36 Ursprüngen.
- Die Stabilität misst nur das Raster aus drei Parametern; andere Verfahren
  (z. B. andere Kostenfunktion) sind nicht enthalten.
- Die Kachel „Negativstes Topic“ beruht, wenn ein Modell geladen ist, auf LDA-Themen mit
  Transformer-Stimmung, sonst auf den Schlüsselwort-Themen; das ist in den Technischen
  Hinweisen nicht weiter aufgelöst.
- Stabilität und Intervalle sind in der Anomalien-Karte und auf der Detailseite noch nicht
  sichtbar (parallele Bearbeitung, siehe 2.2).

## 5. Prüfung und Belege

- Backend: `uv run pytest` grün (1430 vor den Änderungen, 1485 nach den Backend-Änderungen;
  Stand nach der Duplikat-Änderung siehe Nachtrag unten); neue Tests in
  `tests/test_score_uncertainty.py`, `tests/anomaly/test_stability.py`,
  `tests/forecast/test_forecast_service.py`, `tests/forecast/test_forecast_integration.py`,
  Ergänzungen in `tests/test_analyze_topic_rating.py` und `tests/test_data_status.py`.
- Frontend: `npm run lint` 0/0, `npm run build` erfolgreich, `npm test` (vitest) 11 Tests grün.
- Abgleich alt/neu der Topic-Berechnung auf den Demo-Daten (Skript im Scratch-Verzeichnis):
  nur Rundungsunterschiede.
- PDF in Node gegen das laufende Backend gerendert (1&1 AG, Telekom; 9 Seiten) und
  gesichtet: Kurzbericht mit Datenstand, Stabilität, Warnungen und nächsten Schritten auf
  einer Seite; Technische Hinweise mit Prognose-Backtest, Stabilitätsraster, Nennern der
  Topics und Grenzen.
- Backend-Testlauf nach allen Änderungen: 1486 Tests grün (`uv run pytest`, 2026-10-17).
- Export-Knopf im Dashboard mit dem Endstand (2026-10-18, Vite auf Port 5173, Backend auf Port 8000, heller Modus, 1&1 AG): ohne Fehler, Konsole meldet „PDF gespeichert … (9 Seiten)“. Die Datei landete nicht im Downloads-Ordner der Vorschau; die Seiten wurden mit dem Node-Render desselben Stands gesichtet (Kurzbericht, Zeitverlauf mit Bandbreite, Anomalien mit Stabilitätsspalte, Technische Hinweise).

## 6. Offene Punkte (Entscheidungen des Autors)

1. **Prognose: entschieden (Autor, 2026-10-18): Holt bleibt.** Die Prognose wird mit
   Backtest-Hinweis und Bandbreite gezeigt; ein Wechsel auf das Mittel der letzten 6 Monate
   (im Backtest das genaueste Verfahren) findet nicht statt. Vorschlag für
   `docs/entscheidungen.md` (E33: Verfahren, Backtest-Ergebnis, Entscheidung), dort noch
   nicht eingetragen, weil die Datei parallel bearbeitet wurde.
2. **Duplikate: entschieden (Autor, 2026-10-18): entfernt.** Das Skript
   `backend/scripts/remove_duplicates.py` (gleicher Schlüssel wie die Zählung, plus
   Unternehmen; je Gruppe bleibt die kleinste id) hat am 2026-10-18 in der gehosteten
   Datenbank 26 Mitarbeiter-Zeilen und 2 Bewerber-Zeilen gelöscht (21.962 → 21.936 bzw.
   4.676 → 4.674); ein Dry-Run danach findet 0 Duplikate. Alle Mittel und Läufe vor diesem
   Datum enthalten die Duplikate noch. Tests: `backend/tests/test_remove_duplicates.py`.
3. **Schwelle der Stabilität:** unter 0,5 gilt eine Veränderung im Bericht als „hängt
   deutlich von den Schwellen ab“ (Setzung); ob instabile Markierungen anders dargestellt
   werden sollen, ist offen.
4. **Dashboard:** Stabilität und Intervalle in Anomalien-Karte und Detailseite anzeigen,
   sobald die parallele Bearbeitung abgeschlossen ist.
5. **Topic-Übersicht „Alle Quellen“:** Standard auf „Mitarbeiter“ stellen oder die Mischung
   mit der jetzt sichtbaren Aufteilung beibehalten.
6. **Bezeichnung** „Was verbessert werden sollte“ gegen „muss“ (siehe [14](14-kurzbericht-pdf.md)).

## 7. Nachtrag 2026-10-18: Bandbreite der Prognose im Dashboard

Rückfrage des Autors zur orangenen Fläche im Detailfenster des Zeitverlaufs. Sie ist die
Bandbreite (80 %) aus Abschnitt 2 (Quantile der Backtest-Fehler je Horizont). Drei
Korrekturen: (1) Die Legende hat den Eintrag „Bandbreite (80 %)“ mit Erklärung im Tooltip;
(2) die Fläche setzt am letzten Monatswert an (Brückenpunkt) statt mit einer senkrechten
Kante; (3) die Bandbreite wird mit dem Horizont nie schmaler: ``interval_offsets`` nimmt
je Horizont das Minimum bzw. Maximum über alle kürzeren Horizonte (Setzung; die rohen
Quantile stehen weiter unter ``raw_low``/``raw_high``). Begründung: Die rohen Quantile
schwanken, weil sie aus höchstens 36 Fehlern je Horizont geschätzt sind, und eine mit dem
Horizont schrumpfende Unsicherheit wäre nicht zu begründen. Die Kachel „Ø Prognose“ im
Detailfenster zeigt den Wert mit einer Nachkommastelle und ± der mittleren halben
Bandbreite, wie die Karte und das PDF. Test: ``test_interval_offsets_never_narrow_with_horizon``.
