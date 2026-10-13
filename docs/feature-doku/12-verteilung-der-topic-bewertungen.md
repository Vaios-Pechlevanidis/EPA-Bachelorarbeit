# 12 – Verteilung der Bewertungen im Topic-Detail

| | |
|---|---|
| Inkrement | Korrektur (2026-10-13) an der Topic-Übersicht aus Zyklus 1 |
| Anforderungen | keine eigene Anforderung; Transparenz der angezeigten Zahlen wie FA-25 und FA-26 (Datenbasis und n, siehe [10](10-transparenz-und-datenstand.md)) |
| Entscheidungen | keine neue; die Schwellen 2,5 und 3,5 Sterne stammen aus Zyklus 1 (eigene Setzung) |
| Status | umgesetzt (2026-10-13), Commit `baad4fa`; Schwellen **vorläufig** |
| Stand | 2026-10-13 |

## 1. Vorstellung

Im Detailfenster eines Topics (Dashboard → Topic-Übersicht → Topic anklicken) zeigt die Karte
**„Verteilung der Bewertungen“** (vorher „Sentiment-Verteilung“, Überschrift „Stimmung“):

- oben den **Durchschnitt** der Sterne des Topics, z. B. „Ø 4,4 · Sterne · Einstufung Positiv“
  (SAP SE, Mitarbeitende, Kollegenzusammenhalt);
- einen **gestapelten Balken**, dessen Abschnitte die gezählten Anteile zeigen;
- drei Kennzeichen mit **Anteil und Anzahl**, z. B. „3 % negativ (3) · 13 % neutral (13) · 84 %
  positiv (87)“; der Tooltip nennt den Sternebereich und „x von n Bewertungen“;
- darunter, woraus gezählt wurde: n, die Schwellen und wie viele Bewertungen ohne
  Teilbewertung mit ihrer Gesamtnote zählen, und den Satz „Keine Textanalyse“.

Die Kachel oben rechts heißt **„Einstufung“** (vorher „Sentiment“) und nennt statt „77 % Stimmung“
die Regel „nach Ø Sternen: ab 3,5 positiv, ab 2,5 neutral“. Der Durchschnitt steht überall mit
einer Nachkommastelle, so genau, wie das Backend ihn liefert (vorher „4,10“).

Nutzen: Man sieht, ob ein mittlerer Durchschnitt aus vielen mittleren oder aus vielen sehr guten
und sehr schlechten Bewertungen entsteht; das kann der Durchschnitt allein nicht zeigen.

## 2. Erklärung

1. **Welche Bewertungen:** alle Bewertungen der gewählten Quelle und des Zeitraums, deren Text
   ein Schlüsselwort des Topics enthält (Schlüsselwort-Themen, `services/keyword_topic_service.py`,
   dieselbe Auswahl wie für „Erwähnungen“).
2. **Ein Wert je Bewertung:** die Sternebewertung zu diesem Topic (z. B.
   `sternebewertung_kollegenzusammenhalt`). Fehlt sie, zählt die Gesamtnote der Bewertung
   (`durchschnittsbewertung`), wie schon beim Durchschnitt. Wie oft das vorkommt, steht als
   `fallback_overall` in der Antwort und im Hinweistext. Bewertungen ohne beides zählen nicht.
3. **Einstufung je Bewertung** mit denselben Schwellen wie das Etikett des Topics
   (`NEUTRAL_FROM = 2.5`, `POSITIVE_FROM = 3.5`, Funktion `rating_class`): unter 2,5 negativ,
   2,5 bis unter 3,5 neutral, ab 3,5 positiv. Bei ganzen Sternen: 1–2 negativ, 3 neutral, 4–5 positiv.
4. **Antwort** von `GET /api/analytics/company/{id}/topic-overview`, je Topic neu:
   `ratingDistribution = {negative, neutral, positive, n, fallback_overall, neutral_from, positive_from}`.
5. **Anzeige:** Balkenbreite = Anzahl / n. Die Prozentzahlen sind ganze Zahlen nach dem Verfahren
   des größten Restes, damit sie zusammen 100 ergeben. Fehlt das Feld (älteres Backend), steht
   „Verteilung nicht verfügbar“ statt einer Schätzung.

„Positiv/Neutral/Negativ“ ist hier eine **Einstufung der Sterne**, keine Stimmungsanalyse der Texte.
Die Textanalyse (German Sentiment BERT) gibt es nur im Vorher-Nachher-Vergleich ([02](02-drilldown-und-vergleich.md)).

## 3. Begründung

**Der Fehler vorher:** Die Karte „Sentiment-Verteilung“ zählte keine Bewertung. Sie rechnete den
Durchschnitt auf 0–100 % um ((Ø − 1) / 4) und leitete daraus feste Anteile ab: ab 65 % (etwa
3,6 Sterne) immer 15 % negativ, 15 % neutral, 70 % positiv; darunter 30/40/30, 15/55/30 usw.
Eine Raute auf dem Balken stand an der umgerechneten Stelle, obwohl der Balken Anteile zeigte,
keine Sterneskala. Zusätzlich ergab 4,1 Sterne durch einen Rundungsfehler im Browser 77 % statt
77,5 %. Die Zahlen sahen gemessen aus, waren es aber nicht. Für die Arbeit und die
Experteninterviews (DZ3) ist das nicht vertretbar.

**Warum gezählt statt entfernt:** Die Verteilung ergänzt den Durchschnitt um eine Aussage, die
er nicht enthält (Streuung, Polarisierung). Sie lässt sich aus den vorhandenen Daten ohne neue
Annahmen zählen.

**Warum dieselben Schwellen wie das Etikett:** Etikett und Verteilung sollen sich nicht
widersprechen können. Die Werte 2,5 und 3,5 teilen die Skala 1–5 in drei gleich breite Bereiche
um die Mitte 3; sie stammen aus Zyklus 1 und sind eine Setzung.

**Warum Raute und Skalenbeschriftung entfallen:** Ein Balken aus Anteilen hat keine Achse von
„negativ“ bis „positiv“; eine Markierung darauf vermischt zwei Maßstäbe.

**Warum „Einstufung“ und „Sternebewertung“ statt „Sentiment“ und „Stimmung“:** Die Werte
kommen aus den Sternen. Die alten Begriffe ließen eine Textanalyse vermuten.

## 4. Grenzen

- „Nennt das Topic“ heißt: ein Schlüsselwort steht im Text. Die Bewertung muss nicht vom Topic
  handeln, und Bewertungen, die das Topic ohne Schlüsselwort meinen, fehlen.
- Fehlt die Teilbewertung, zählt die Gesamtnote; sie sagt über das Topic weniger aus. Bei
  Bewerbenden fehlen manche Teilbewertungen häufig (z. B. Kommunikation bei SAP SE: 108 von 170).
- Bei kleinem n schwanken die Anteile stark. Die Karte nennt n, warnt aber nicht eigens;
  die Topic-Übersicht markiert Topics mit begrenzter Datenbasis.
- Die Schwellen sind Setzungen; andere Grenzen verschieben die Anteile.

## 5. Prüfung und Belege

- Tests: `backend/tests/test_analyze_topic_rating.py`, Klasse `TestRatingDistribution`: Grenzen
  einschließlich (2,5 neutral, 3,5 positiv), Ø 4,1 aus 2 × 1,0 und 8 × 4,9 ergibt 2/0/8 und nicht
  15/15/70, Rückfall auf die Gesamtnote gezählt und ausgewiesen, Bewertungen ohne Nennung oder
  ohne Wert zählen nicht, Etikett mit denselben Schwellen.
- `backend/tests/drilldown/test_keyword_topic_service.py` (Hash der übrigen Antwort): unverändert;
  das neue Feld ist dort ausgenommen (`TOPIC_ADDED_KEYS` in `tests/drilldown/_helpers.py`).
- Gesamte Backend-Suite 2026-10-13: 1216 bestanden.
- Manuelle Prüfung 2026-10-13 im Browser, SAP SE, Topic „Kommunikation“ (alle Quellen):
  Ø 2,7, 55 % negativ (93), 12 % neutral (20), 33 % positiv (57), n = 170, davon 108 mit Gesamtnote.

Vergleich alt und neu für SAP SE, Mitarbeitende, gesamter Zeitraum (Abruf 2026-10-13):

| Topic | Ø | alt neg/neu/pos | gezählt neg/neu/pos | n |
|---|---|---|---|---|
| Kollegenzusammenhalt | 4,4 | 15/15/70 | 3/13/84 | 103 |
| Interessante Aufgaben | 4,2 | 15/15/70 | 3/28/69 | 29 |
| Work-Life Balance | 3,6 | 15/15/70 | 24/10/65 | 49 |
| Gehalt & Sozialleistungen | 3,2 | 30/40/30 | 25/37/38 | 106 |
| Vorgesetztenverhalten | 3,2 | 30/40/30 | 36/20/44 | 50 |
| Kommunikation | 2,7 | 30/40/30 | 53/16/31 | 62 |
| Gleichberechtigung | 3,4 | 15/55/30 | 22/11/67 | 9 |

## 6. Offene Punkte

- Schwellen 2,5 und 3,5 bestätigen oder ändern (Autor); dann als Entscheidung in
  `docs/entscheidungen.md` festhalten.
- Die PDF-Topic-Übersicht nennt die Spalte und die Zählung der Topics noch „Sentiment“. Die
  Werte dort sind gezählte Etiketten je Topic und nicht falsch, der Begriff ist aber derselbe
  wie hier.
- Das Backend auf dem Hugging-Face-Space muss neu gebaut werden; bis dahin zeigt das
  Detailfenster dort „Verteilung nicht verfügbar“.
