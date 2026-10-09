# 10 – Transparenz und Datenstand

| | |
|---|---|
| Inkrement | 6 „Transparenz und Demo“ (Phase A und Abschluss) |
| Anforderungen | FA-08, FA-25, FA-26, FA-37, FA-38, NFA-07 (Anforderungstexte nicht im Repository) |
| Entscheidungen | E24 (rollierende Schnitte), E25 (Datenstand), E26 (Score-Definition D1, Hinweistext), E27 (Datenbasis und n), E28 (Prognose-Schalter D2), E21 Nachtrag (Bezeichnung nach Signalen) in `docs/entscheidungen.md` |
| Status | umgesetzt; Schwelle der kleinen Basis vorläufig (T5 offen); Anzeige der Beschreibungsfelder in der Einzelbewertung offen (Entscheidung des Autors) |
| Stand | 2026-10-09 |

## 1. Vorstellung

Inkrement 6 macht sichtbar, worauf jede Zahl des Dashboards beruht und wie aktuell sie ist:

- Eine **Datenstand-Leiste** über Dashboard, Anomalien-Seite und Aktien-Dashboard nennt je Quelle
  die Zahl der Bewertungen, den Zeitraum, die bewerteten Monate, den letzten Import und den Stand
  von Kurs- und Belegspeicher (E25).
- Jede Kachel, Karte und Liste trägt ein **Kennzeichen der Datenbasis** (Sternebewertung,
  Freitextanalyse, Externe Meldungen, Marktdaten) und **n**; bei kleiner Basis erscheint eine
  Warnung (E27).
- Die Kachel **„Ø Score“** zeigt das Mittel der **Gesamtnote** der Mitarbeitenden mit n und einem
  Berechnungshinweis; das Detailfenster zeigt darunter die **Kategorienmittel** (E26). Die
  Trend-Kachel vergleicht die Gesamtnote der letzten 12 vollen Monate mit den 12 davor.
- Die Kachel **„12- vs. 24-Monats-Schnitt“** zeigt rollierende Schnitte (E24).
- Die Kacheln heißen **„Kritischste Kategorie“** und **„Negativstes Topic“**, die Zeitreihe
  **„Zeitverlauf“**.
- In der **Evaluationsinstanz** ist die Prognose des Zeitverlaufs ausgeblendet (E28).
- Die **Erklärungsansätze** nennen im Badge die vorhandenen Signale (E21, Nachtrag).
- **Beispielzitate** der Topics stammen nie aus den Beschreibungsfeldern zu Tätigkeit oder Stelle
  (NFA-07).

Der PDF-Export übernimmt alle diese Elemente (Feature-Doku 09).

## 2. Erklärung

**Ø Score (D1).** `GET /api/companies/{id}/ratings` liefert neben dem unveränderten `avg_overall`
(Mittel der 13 Kategorienmittel, jetzt „Kategorienmittel“) die Felder `score` (Mittel der Spalte
`durchschnittsbewertung` aller Bewertungen der Mitarbeitenden ab `start_date`, ungewichtet),
`score_n`, `score_definition` und `category_mean_definition`
(`backend/services/score_service.py`). Der Berechnungshinweis steht in
`frontend/src/lib/scoreText.js` und erscheint wortgleich unter den Kacheln, im Detailfenster und
im PDF:

> Ø Score: Mittel der Gesamtnote aller Bewertungen von Mitarbeitenden im gewählten Zeitraum,
> ungewichtet. Kununu berechnet seinen Score anders (laut Experteninterviews ohne Bewerbende und
> mit geringerem Gewicht für ältere Bewertungen); der Wert kann deshalb von der Anzeige auf Kununu
> abweichen.

**Trend der Gesamtnote.** Modus `score_months` von `GET …/ratings/trend`: Mittel der Gesamtnote
der letzten 12 (bei „3 Jahre“ 36) vollen Kalendermonate bis zum Anker gegen dieselbe Zahl Monate
davor, n je Fenster. Anker ist wie bei den rollierenden Schnitten der letzte volle Monat mit
Bewertungen; der laufende Monat zählt nie.

**Rollierende Schnitte (FA-08).** Modus `rolling`: Gesamtnote über 12 und 24 volle Monate bis zum
Anker, Differenz, n je Fenster, Kennzeichen kleine Basis (unter 10 Bewertungen, E12) und
unvollständige Fenster (E24).

**Datenstand (FA-37).** `GET /api/companies/{id}/data-status`; Texte gemeinsam für Leiste und PDF
in `frontend/src/lib/dataStatusText.js` (E25).

**Datenbasis und n (FA-25, FA-26).** Vokabular und Schwellen in `frontend/src/lib/dataBasis.js`:
5 Bewertungen je Monat (E4), 10 je Fenster (E12) (E27).

**Prognose (D2).** `VITE_SHOW_FORECAST=false` beim Bauen: Der Zeitverlauf ruft
`forecast_months=0` ab, zeigt keine Prognoseelemente, und das PDF-Deckblatt nennt nur den
Zeitraum der Daten (E28).

**Beispielzitate (NFA-07).** `analyze_topic` (`backend/services/keyword_topic_service.py`)
übernimmt aus `jobbeschreibung` und `stellenbeschreibung` keinen Satz als Zitat
(`QUOTE_EXCLUDED_FIELDS`); für Häufigkeit, Bewertung und Stimmung eines Topics zählen die Felder
weiter mit.

### Felder einer einzelnen Bewertung je Ansicht, Antwort und PDF (NFA-07)

Stand 2026-10-09, geprüft am Code. „Beschreibungen“ = `jobbeschreibung` (Mitarbeitende) und
`stellenbeschreibung` (Bewerbende).

| Ort | Felder einer einzelnen Bewertung | Beschreibungen |
|---|---|---|
| Topic-Tabelle (Karte und Fenster „Topic-Übersicht“) | ein Beispielsatz (`example`) | nie (seit NFA-07) |
| Topic-Details: Typische Aussagen, Beispiel-Review | Sätze (`typicalStatements`) | nie (seit NFA-07) |
| Einzelbewertung (`ReviewDetailModal`, aus Topic-Details und der Bewertungsliste der Anomalien-Seite) | Datum, Quelle, Status, Gesamtnote, Titel, Gut, Schlecht, Verbesserungsvorschläge, 13 Sternebewertungen | **ja, beide werden angezeigt** (unverändert, Entscheidung des Autors offen) |
| Bewertungsliste der Anomalien-Seite (`PeriodReviews`) | Datum, Gesamtnote, Titel, Status, Textauszug (Mitarbeitende: Gut, Schlecht, Verbesserung; Bewerbende: `stellenbeschreibung` und Verbesserung, `review_service.TEXT_FIELDS_BY_SOURCE`) | Bewerbende: ja, im Textauszug |
| Detailfenster „Negativstes Topic“ | Kritikpunkte (kurze Wortfolgen aus Schlecht und Verbesserung), sonst Sätze aus der Topic-Übersicht | nein |
| Erklärungsansätze | kennzeichnende Einzelwörter mit Zählungen, keine Sätze | nein |
| Kacheln, Zeitverlauf, Anomalien-Karte, Aktie | nur Zahlen | nein |
| PDF-Export | Beispielsatz je Topic in der Topic-Tabelle; sonst nur Zahlen | nie (seit NFA-07) |
| API `GET …/topic-overview` | `example`, `typicalStatements`, `reviewDetails[].preview` (ohne Beschreibungen), `reviewDetails[].fullReview` (alle Felder) | in `fullReview`: ja |
| API `GET …/reviews` (Liste) | Datum, Gesamtnote, Titel, Gut, Schlecht, Verbesserung, `job_description`, `description` | ja |
| API `GET …/reviews?format=full` | `preview` (Textauszug wie oben), `fullReview` (alle Felder), Markierungen | ja |
| API `GET /api/topics/company/{id}/negative-topics`, `GET …/negative-kritikpunkte` | Wortfolgen aus Schlecht und Verbesserung | nein |

## 3. Begründung

Die Interviews (DZ3) prüfen, ob Fachleute die Zahlen verstehen und ihnen zuordnen können, woher
sie stammen. Dafür braucht jede Zahl ihre Definition, ihre Basis und ihren Stand. Eine
Definition für alle Werte zur Gesamtbewertung (D1) verhindert, dass Kachel und Zeitverlauf
verschiedene Zahlen unter demselben Namen zeigen. Die deutschen Beschriftungen folgen der
Sprache der Oberfläche. Die Prognose bleibt im Artefakt, steht aber nicht zur Evaluation (D2).
Beispielzitate sollen Aussagen zu einem Thema zeigen, nicht die Beschreibung einer Stelle, die
eine Person erkennbar machen kann (NFA-07). Alle Begriffe, Fensterlängen und Schwellen sind
Setzungen des Autors, soweit sie nicht aus E4 und E12 stammen.

### Anforderung, wo erfüllt, Grenze

| Anforderung | Wo erfüllt | Grenze |
|---|---|---|
| FA-08 rollierende Schnitte | Modus `rolling` (`rolling_average_service.py`), Kachel „12- vs. 24-Monats-Schnitt“ mit Detailfenster, PDF (E24) | Anker ist der letzte Monat mit Daten, nicht heute; Schwelle der kleinen Basis vorläufig (T5); beschreibend, keine Prognose |
| FA-25 Kennzeichnung der Datenbasis | `lib/dataBasis.js`; Kennzeichen an Kacheln, Karten, Listen und im PDF (E27) | festes Vokabular aus vier Begriffen; Mischformen tragen teils beide Kennzeichen (Vergleich auf der Anomalien-Seite), teils nur das Hauptkennzeichen („Topics im Detail“: Sternebewertung, obwohl die Themen aus Texten erkannt werden) |
| FA-26 n und kleine Basis | n an jeder Kennzahl, Warnung unter 5 je Monat bzw. 10 je Fenster (E27); Ø Score mit `score_n` (E26) | feste Schwellen, keine Unsicherheitsangabe; „Negativstes Topic“ nennt Nennungen statt Bewertungen; „Kritischste Kategorie“ nennt n nur ohne Zeitfilter |
| FA-37 Datenstand | `GET …/data-status`, Datenstand-Leiste auf drei Seiten und im PDF (E25) | Abrufdatum bei Kununu nicht gespeichert; Plattformvergleich nur mit Eintrag des Autors |
| FA-38 Berechnung des Score erklären | `score` nach D1, Hinweistext aus `lib/scoreText.js` an Kachel, Detailfenster und PDF, Kategorienmittel getrennt beschriftet (E26) | Kununus Gewichtung ist nicht nachgebildet; der Hinweis beruht auf den Experteninterviews |
| NFA-07 Schutz einzelner Personen | keine Beispielzitate aus `jobbeschreibung`/`stellenbeschreibung` (Topic-Tabelle, Topic-Details, PDF) | Einzelbewertung und API-Antworten enthalten beide Felder weiter; Textauszug der Bewerbenden enthält `stellenbeschreibung`; offen für den Autor |

## 4. Grenzen

- Der Ø Score ist nicht der Score auf Kununu; Gesamtnote und Kategorienmittel können voneinander
  abweichen.
- Das Trend-Detailfenster zeigt die Kategorien weiter mit den bestehenden Modi (Monatsmittel je
  Kategorie); „1Y“ und „3Y“ rechnen dort ab heute und bleiben bei Reihen, die 2025 enden, leer.
- In „Topics im Detail“ heißt der Mittelwert über die sichtbaren Topics ebenfalls „Ø Score“; er
  ist ein Mittel der Topic-Bewertungen, nicht der Ø Score nach D1.
- Der Prognose-Schalter wirkt nur beim Bauen.
- Die Anforderungstexte FA-08, FA-25, FA-26, FA-37, FA-38 und NFA-07 liegen nicht im Repository;
  die Zuordnung folgt den Bezeichnungen aus Inkrement 6.

## 5. Prüfung und Belege

- Tests: `backend/tests/test_score_service.py` (Score und `score_months`, darunter Gesamtnote 4,8
  gegen Kategorienmittel 2,23), `backend/tests/test_rolling_average_service.py`,
  `backend/tests/test_data_status.py`, `backend/tests/test_topic_quotes_nfa07.py` und der
  Hash-Vergleich ohne Zitatfelder in `backend/tests/drilldown/test_keyword_topic_service.py`,
  `backend/tests/explanations/test_signal_labels.py`,
  `backend/tests/test_check_evaluation_instance.py`.
- Commits auf `feature/inkrement-6-abschluss`: `0b2737f`, `f1013a9` (Score), `ef05ca6`
  (Prognose-Schalter), `6018f10` (NFA-07), `9870875` (Beschriftungen), `fc73068`
  (Signale), `e006751` (Prüfskript).
- Abnahme der Evaluationsinstanz: `backend/scripts/check_evaluation_instance.py` und
  `docs/abnahme-inkrement-6.md` (15 Unternehmen, helles Schema, PDF-Export).

## 6. Offene Punkte

- Anzeige von `jobbeschreibung` und `stellenbeschreibung` in der Einzelbewertung und im
  Textauszug der Bewerbenden (Entscheidung des Autors im Abschlussbericht).
- Schwelle der kleinen Basis je Fenster (T5).
- Bezeichnung „Ø Score“ in „Topics im Detail“.
- Verständlichkeit der Signalbezeichnungen und des Hinweistexts in den Interviews (DZ3).
