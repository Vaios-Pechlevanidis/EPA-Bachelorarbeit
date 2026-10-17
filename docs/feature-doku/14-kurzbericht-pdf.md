# 14 – Kurzbericht im PDF-Export

| | |
|---|---|
| Inkrement | Nachtrag zum PDF-Export ([09](09-pdf-export.md)), 2026-10-17; keine neue Funktion im Dashboard |
| Anforderungen | keine eigene Anforderung; Wunsch des Autors (2026-10-17): „ein kleiner Bericht, der die aktuellsten Anomalien und deren Folgen auf die Bewertung beschreibt, was verbessert werden muss und was gut läuft“ |
| Entscheidungen | keine neue Entscheidung in `docs/entscheidungen.md`; die Schwellen sind die bestehenden Farbschwellen der Kacheln (3,5 / 2,5, siehe [12](12-verteilung-der-topic-bewertungen.md)) und die Schwelle der kleinen Basis (10 Bewertungen je Fenster, E12) |
| Status | umgesetzt (2026-10-17), nicht committet; alle Regeln und Zahlen **vorläufig** |
| Stand | 2026-10-17 |

## 1. Vorstellung

Der Bericht aus „PDF Export“ hat seit dem 2026-10-17 direkt nach dem Cover eine neue
Seite **„Kurzbericht“** (Abschnitt 01; die bisherigen Abschnitte rücken auf 02 bis 05
im Inhalt bzw. 2 bis 7 in der Zählung der Überschriften). Sie fasst die folgenden
Seiten in vier Blöcken zusammen:

1. **Lage der Bewertung** – drei Zellen wie der Kennzahlen-Streifen der Karten:
   Ø Score (mit n), Trend über 12 bzw. 36 Monate (steigend / sinkend / stabil) und der
   12- gegenüber dem 24-Monats-Schnitt. Darunter ein Satz zur Reihe der Erkennung
   (Gruppe, Dimension, bewertete Monate, Zeitraum).
2. **Jüngste auffällige Veränderungen und ihre Folge** – die bis zu drei jüngsten
   Niveauwechsel der Anomalien-Karte, jüngste zuerst, als Tabelle (ab Monat, Richtung,
   Veränderung in Sternen, Niveau von Ø … auf Ø …, Bewertungen davor / danach, Ausmaß,
   Stand „aktuelles Niveau“ oder „abgelöst“). Unter jeder Zeile steht die **Folge** als
   Satz, z. B. bei 1&1 AG: „Seit Okt. 2016 liegt das Monatsmittel bei Ø 3,21 und damit
   0,39 Sterne unter dem Abschnitt davor (Ø 3,60, Dez. 2010 – Sept. 2016); das gilt bis
   zum letzten bewerteten Monat (Juni 2025).“ Bei mehreren Wechseln folgt eine Zeile
   „Über alle n Wechsel: von Ø … auf Ø …, netto ± … Sterne“, bei Einzelmonaten ein Satz
   mit Anzahl und jüngstem Monat samt dem Zusatz „ungeprüft“ aus [03](03-auffaellige-einzelmonate.md).
   Ohne Veränderung, ohne Erkennung (zu wenige bewertete Monate) oder bei Ladefehler
   steht an dieser Stelle der entsprechende Satz.
3. **Zwei Spalten** nebeneinander, gleich hoch: links grün **„Was gut läuft – Stärken
   laut Bewertungen“**, rechts rot **„Was verbessert werden sollte – Handlungsfelder laut
   Bewertungen“**. Jeder Eintrag hat einen fetten Titel, das Kennzeichen der Datenbasis
   (Sternebewertung / Freitextanalyse, FA-25), eine Zeile mit den Zahlen (Ø, n,
   Erwähnungen, Zeitraum) und bei Bedarf die Warnung „kleine Basis“ bzw. „begrenzte
   Datenbasis (n = …)“ in Bernstein (FA-26). Trifft keine Regel, steht ein Hinweis
   („Kein Handlungsfeld nach den Regeln dieses Berichts.“) oder zur Einordnung das
   höchste bzw. niedrigste Topic.
4. **Regeln des Berichts**: welche Schwellen gelten, woher die Kennzahlen kommen, und
   der Satz „Der Bericht nennt, wo die Bewertungen auffallen, nicht warum: keine Aussage
   über Ursachen.“ Seit dem Umbau am selben Tag ([09](09-pdf-export.md), Nachtrag 7)
   stehen die Regeln auf der letzten Seite „Technische Hinweise“; die Seite „Kurzbericht“
   zeigt oben nur die Zeile „Nach festen Regeln aus den Bewertungen · keine Aussage über
   Ursachen · Regeln und Datengrundlage: Technische Hinweise (letzte Seite)“.

Beispiel 1&1 AG (Stand der Datenbank am 2026-10-17): Lage Ø 3,4 (n = 1.291), Trend
+0,26 steigend, 12 Monate 0,12 über dem 24-Monats-Schnitt (3,63 / 3,51); eine Veränderung
(Abfall um 0,39 Sterne ab Okt. 2016, aktuelles Niveau); Stärken: Gesamtnote steigt,
12-Monats-Schnitt über dem 24-Monats-Schnitt, Kollegenzusammenhalt (Ø 4,1, 257 Erwähnungen),
Arbeitsatmosphäre, Interessante Aufgaben; Handlungsfelder: jüngste Veränderung ist ein
Abfall, Kritischste Kategorie Gehalt/Sozialleistungen (Ø 3,1, n = 1.245),
Vorgesetztenverhalten (Ø 2,2, 158 Erwähnungen, negativ), Image und Gleichberechtigung
(beide mit begrenzter Datenbasis).

## 2. Erklärung

**Keine neuen Daten.** Der Kurzbericht nutzt ausschließlich, was die Dashboard-Seite
schon für den Export sammelt (siehe [09](09-pdf-export.md), Abschnitt „Daten“): die
fünf Kacheln (Ø Score mit n, Trend, rollierende Schnitte, Kritischste Kategorie,
Negativstes Topic), den Zustand der Anomalien-Karte (`AnomalyCard.onDataChange`:
Auswahl, Veränderungen, Einzelmonate, Eignung, bewerteter Zeitraum) und die Topics der
Topic-Übersicht (Name, Ø Rating, Erwähnungen, Stimmung, `statistical_meta`). Es gibt
keinen zusätzlichen Abruf und keine Textgenerierung durch ein Sprachmodell.

**Ableitung.** Die Regeln stehen in `frontend/src/lib/reportSummary.js` als reine
Funktionen (ohne Browser-Abhängigkeit, daher auch in Node prüfbar):

| Funktion | Ergebnis |
|---|---|
| `situationCells` | die drei Zellen der Lage; Farbe wie die Kacheln (Ø ab 3,5 grün, ab 2,5 gelb, sonst rot; Trend und Schnitte nach Vorzeichen) |
| `seriesSentence` | Satz zur Reihe der Erkennung |
| `summarizeChanges` | Veränderungen nach Monat absteigend, höchstens `maxChanges`; je Wechsel der Folge-Satz; Netto über alle Wechsel = Ø des letzten Abschnitts minus Ø des ersten Abschnitts; Zustände `ok`, `none`, `ineligible`, `error`, `missing` |
| `outlierSentence` | Satz zu Einzelmonaten (nur mit `VITE_SHOW_OUTLIER_MONTHS`) |
| `summarizeColumns` | Einträge der beiden Spalten in fester Reihenfolge (unten) |
| `rulesText` | Fußnote mit den Regeln |
| `buildReportSummary` | alles zusammen für `utils/pdfExport.js` |

**Folge-Satz je Wechsel.** Für den jüngsten Wechsel: Seit `date` liegt das Monatsmittel
bei `after_mean`, Differenz zum Abschnitt davor (`before_mean`, `before_from` bis
`previous_period`); endet der Abschnitt danach (`after_to`) im letzten bewerteten Monat
der Reihe, heißt es „das gilt bis zum letzten bewerteten Monat“, sonst wird das Ende des
Abschnitts genannt. Für ältere Wechsel: Ø danach für `date` bis `after_to`, dann „ab
… folgte ein weiterer Wechsel (Anstieg / Abfall)“. Liegt vor dem Wechsel eine Lücke
nicht bewerteter Monate (`gap_months`), wird sie wie in der Liste der Anomalien-Seite
genannt. Alle Felder kommen unverändert aus `GET /analytics/company/{id}/anomalies`
(siehe [01](01-anomalien-im-verlauf.md)).

**Reihenfolge und Regeln der Spalten** (`REPORT_RULES`, alle Werte Setzungen des
Autors, vorläufig):

| Nr. | Eintrag | Spalte | Regel |
|---|---|---|---|
| 1 | Jüngste auffällige Veränderung | Stärke bei Anstieg, Handlungsfeld bei Abfall | jüngster Wechsel der Anomalien-Karte |
| 2 | Gesamtnote steigt / sinkt | nach `sign` der Trend-Kachel | nur bei steigend oder sinkend; Warnung bei weniger als 10 Bewertungen in einem Fenster |
| 3 | 12-Monats-Schnitt über / unter dem 24-Monats-Schnitt | nach `sign` der Kachel | nur bei Unterschied über 0,05 (Regel der Kachel, `lib/rollingAverage.js`); Warnungen der Kachel |
| 4 | Niedrigste Kategorie | Handlungsfeld bei Ø unter 3,5, sonst Stärke „Alle Kategorien ab Ø …“ | Kritischste Kategorie der Kachel (niedrigstes Kategorienmittel) |
| 5 | Topics der Topic-Übersicht | Stärke: Ø ab 3,5 und Stimmung nicht negativ (positive zuerst); Handlungsfeld: Stimmung negativ oder Ø unter 2,5 | mindestens 5 Erwähnungen, nach Erwähnungen sortiert, höchstens 3 je Spalte; „begrenzte Datenbasis (n = …)“ aus `statistical_meta.sample_size` |
| 6 | Negativstes Topic | Handlungsfeld | Topic der Kachel, falls nicht schon unter 5 genannt |
| 7 | Rückfall | leere Spalte | zur Einordnung das Topic mit dem höchsten bzw. niedrigsten Ø, als solches beschriftet |

Doppelte Titel werden je Spalte nur einmal aufgenommen. Die Texte verwenden nur Zeichen
der Standardschriften des PDF (kein Pfeil, kein typografisches Minus), wie der übrige
Export.

**Darstellung.** `utils/pdfExport.js` zeichnet die Seite mit den vorhandenen Helfern
(Abschnittstitel, Kennzahlen-Streifen, kleine Tabelle mit Notizzeile, Kennzeichen der
Datenbasis, Warnzeile) und zwei neuen Helfern für die Spalten (`reportColumnHeight`,
`drawReportColumn`): Titel bis zu zwei Zeilen neben dem Kennzeichen, Zahlenzeile
umbrechend, beide Spalten so hoch wie die höhere. Reicht der Platz nicht, beginnt der
Block auf einer neuen Seite; die Tabelle der Veränderungen bricht wie die Listen der
Anomalien-Seite um.

## 3. Begründung

**Warum feste Regeln statt eines frei formulierten Textes?** Der Export übernimmt bisher
jedes Element des Dashboards wortgleich ([09](09-pdf-export.md)); ein Fazit, das ein
Sprachmodell formuliert, wäre nicht reproduzierbar und hätte keine Entsprechung in der
Oberfläche. Mit Regeln lässt sich jede Aussage auf die Seite zurückführen, aus der ihre
Zahlen stammen, und die Regeln stehen auf derselben Seite. Das passt zur Arbeit: Das
Dashboard zeigt auffällige Veränderungen und beschreibt, es erklärt keine Ursachen.

**Warum „sollte“ statt „muss“?** Die Bitte des Autors lautete „was verbessert werden
muss“. Die Bewertungen zeigen, wo Noten niedrig und Stimmungen negativ sind; ob daraus
eine Maßnahme folgen muss, können die Daten nicht sagen. Die Spalte heißt deshalb
„Was verbessert werden sollte“ mit dem Zusatz „Handlungsfelder laut Bewertungen“, und
die Fußnote nennt die Grenze ausdrücklich. Die Formulierung ist eine Setzung und kann
vom Autor geändert werden (offener Punkt).

**Warum die Schwellen der Kacheln?** 3,5 und 2,5 sind seit [12](12-verteilung-der-topic-bewertungen.md)
die Farbschwellen für Ø-Werte im Dashboard, 10 Bewertungen je Fenster die Schwelle der
kleinen Basis (E12, [10](10-transparenz-und-datenstand.md)). Neue Schwellen nur für den
Kurzbericht würden eine dritte Einteilung einführen, die nirgends sonst sichtbar ist.

**Warum zuerst?** Ein Kurzbericht, der die folgenden Seiten zusammenfasst, gehört vor
sie, wie eine Zusammenfassung in einem Bericht; wer nur eine Seite liest, bekommt Lage,
jüngste Veränderungen und beide Spalten. Die Abschnitte dahinter bleiben in ihrer
bisherigen Reihenfolge.

**Warum die Rückfall-Einträge?** Bei Telekom trifft keine Handlungsfeld-Regel (niedrigste
Kategorie Ø 3,7, kein negatives Topic, Trend stabil). Eine leere Spalte ist korrekt, lässt
die Leserin aber ohne Anhaltspunkt; der Eintrag „Zur Einordnung: niedrigstes Topic“ nennt
das schwächste Topic und sagt dazu, dass es kein Handlungsfeld nach den Regeln ist.

**Verworfen:** ein Text aus einem Sprachmodell (nicht reproduzierbar, keine Quelle in
der App); der Kurzbericht am Ende des Berichts (Zusammenfassung gehört nach vorn); nur
die Veränderungen ohne Stärken und Handlungsfelder (entspricht nicht der Bitte); eigene
Schwellen für den Bericht (siehe oben).

## 4. Grenzen

- Der Kurzbericht bewertet nach Regeln aus den Bewertungen; er trifft keine Aussage über
  Ursachen und ersetzt keine Analyse. „Handlungsfeld“ heißt: niedriges Ø oder negative
  Stimmung in den Bewertungen, nicht: nachgewiesener Bedarf.
- Stimmung und Ø der Topics stammen aus der Topic-Übersicht (Freitextanalyse,
  Schlüsselwort-Themen); begrenzte Datenbasis wird angezeigt, aber nicht ausgeschlossen.
- Die Veränderungen folgen der aktuellen Auswahl der Anomalien-Karte (Quelle, Status,
  Dimension); Ø Score und Trend sind immer Gesamtnote der Mitarbeitenden. Der Satz zur
  Reihe und die Einleitung nennen das.
- Der Zeitfilter des Dashboards gilt für Ø Score und Trend, nicht für Schnitte und
  Veränderungen (wie auf der Seite Kennzahlen).
- Höchstens drei Veränderungen und drei Topics je Spalte; der Rückfall-Eintrag dient nur
  der Einordnung.
- Export im dunklen Theme wie in [09](09-pdf-export.md) nicht empfohlen; der Kurzbericht
  selbst enthält kein Diagramm und ist davon nicht betroffen.
- Es gibt keine automatischen Tests für das Frontend; die Regeln wurden mit einem
  Probelauf in Node geprüft (unten), nicht mit einer Testsuite.

## 5. Prüfung und Belege

- `npm run lint` (ESLint) ohne Fehler und Warnungen; `npm run build` erfolgreich
  (2026-10-17).
- Probelauf der Regeln in Node mit Beispieldaten und Randfällen (keine Veränderung, keine
  Erkennung, Karte nicht geladen, leere Topics): alle Zustände liefern einen Satz, keine
  verbotenen Zeichen.
- Rendern des vollständigen Berichts in Node (Export-Modul mit esbuild gebündelt,
  Diagramme leer, jsPDF-Node-Build) gegen das laufende Backend (Port 8000), Seite 2
  gesichtet: 1&1 AG (1 Wechsel, 5 Stärken, 5 Handlungsfelder), Telekom (4 Wechsel, 3 davon
  gezeigt, Netto-Zeile, 3 Einzelmonate, Handlungsfelder nur Rückfall), Formycon (keine
  Erkennung, 0 bewertete Monate, kleine Basis in allen Einträgen), Bechtle. Berichte 6 bis
  7 Seiten.
- Export-Knopf im Dashboard (Vite-Entwicklungsserver auf Port 5173, Backend auf Port 8000,
  heller Modus, 1&1 AG, 2026-10-17): Export ohne Fehler, Konsole meldet „PDF gespeichert …
  (7 Seiten)“; die Werte der Kacheln (Ø 3,4, Trend +0,26, 3,63 / 3,51, Kritischste Kategorie
  Gehalt/Sozialleistungen) stimmen mit der in Node gerenderten Seite 2 überein.
- Nach dem Umbau mit der Seite „Technische Hinweise“ (gleicher Tag): siehe Nachtrag 7 in
  [09](09-pdf-export.md); der Kurzbericht selbst ist unverändert bis auf die Verweiszeile
  und den Satz zu Einzelmonaten, der „(ungeprüft)“ nun selbst trägt.
- Code: `frontend/src/lib/reportSummary.js` (Regeln), `frontend/src/utils/pdfExport.js`
  (Seite „Kurzbericht“, `drawReportColumn`, Abschnittsnummern 2 bis 7). Keine Änderung an
  `Dashboard.jsx` oder an den Karten.
- Nebenbei behoben: Das n-Kennzeichen bei begrenzter Datenbasis in der Topic-Tabelle des
  PDFs las `statistical_meta.review_count`; die API liefert `sample_size`, das Kennzeichen
  blieb deshalb leer.

## 6. Offene Punkte

- Schwellen, Anzahl der Einträge und die Bezeichnung „Was verbessert werden sollte“ mit
  dem Autor und den Interviewpartnern (DZ3) prüfen; „muss“ nur, wenn der Autor es so
  vertreten will.
- Ob derselbe Kurzbericht auch im Dashboard erscheinen soll (z. B. als Karte oder im
  Detailfenster); derzeit nur im PDF.
- Ob der Kurzbericht die Bewerbenden-Reihe berücksichtigen soll, wenn die Anomalien-Karte
  darauf steht (Ø Score und Trend bleiben Mitarbeitende).

## 7. Nachtrag 2026-10-17: Erweiterung durch die Prüfung der Berichtsqualität

Mit [16](16-report-qualitaet.md) kamen hinzu (alles in `lib/reportSummary.js`, mit Tests in
`src/lib/__tests__/reportSummary.test.js`): die Zeilen zum **Datenstand** (letzter
Bewertungsmonat je Quelle, Abstand zum Berichtsdatum, Import, Beginn der Prognose) unter der
Lage; die **Stabilität** je Veränderung (Spalte „Stabilität“ als Treffer/Varianten und ein Satz
in der Folge; unter 0,5 „hängt deutlich von den Schwellen ab“); **Intervalle** in den Zellen
(Ø Score, Trend-Differenz); die Einträge der Spalten nennen „Einstufung“ statt „Stimmung“ und
tragen Warnungen, wenn die Trend-Differenz 0 einschließt oder eine Veränderung instabil ist; der
Block **Warnungen** (Datenqualität und Aussagekraft) und der Block **Nächste Analyseschritte**
(höchstens drei Untersuchungsfragen je Art des Handlungsfelds, als Vorschläge gekennzeichnet);
die Regeln nennen die Reihenfolge der Einträge ausdrücklich (kein Punktescore). Die Grenzen
(selektive Quelle, keine Ursachen, Unabhängigkeit, Schlüsselwörter) stehen auf der Seite
„Technische Hinweise“.
