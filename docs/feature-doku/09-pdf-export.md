# 09 – PDF-Export des Dashboards

| | |
|---|---|
| Inkrement | 6 (Nachtrag zum Transparenz-Inkrement) |
| Anforderungen | keine eigene Anforderung an den Export; er übernimmt die Elemente aus FA-08 (rollierende Schnitte), FA-25 und FA-26 (Datenbasis, n, Warnung bei kleiner Basis), FA-37 (Datenstand) sowie die Anomalien-Karte aus Inkrement 1 |
| Entscheidungen | keine neue Entscheidung; Schwellen und Texte wie E4 (5 Bewertungen je Monat), E12 (10 Bewertungen je Fenster), E13 (Status) |
| Status | umgesetzt; Layout vorläufig |
| Stand | 2026-10-09 |

## 1. Vorstellung

Der Knopf „PDF Export“ in der linken Leiste des Dashboards erzeugt einen Bericht
(A4, Hochformat) mit allen Elementen, die das Dashboard für die gewählte Firma zeigt,
in der Reihenfolge der Seite. Vor dem 2026-10-09 enthielt der Bericht nur vier
Kennzahl-Kacheln ohne n, die Timeline, die Topic-Bewertungen und die Topic-Tabelle; die
Datenstand-Leiste, die fünfte Kachel (12- vs. 24-Monats-Schnitt), die Kennzeichen der
Datenbasis, die Warnungen bei kleiner Basis, der globale Zeitfilter und die
Anomalien-Karte fehlten.

Der Bericht hat fünf Abschnitte (bei vielen Topics mehr Seiten):

| Seite | Abschnitt | Elemente des Dashboards |
|---|---|---|
| 1 | Cover | Firmenname, Erstellungszeit, Meta-Band mit Zeitfilter (Standard, 1 Jahr, 3 Jahre), Zeitraum der Timeline, Bewertungen im Datensatz (Mitarbeitende, Bewerbende), Zahl der Topics und Erwähnungen; Inhaltsverzeichnis mit Seitenzahlen |
| 2 (seit 2026-10-17) | Kurzbericht | Lage der Bewertung, die jüngsten auffälligen Veränderungen mit ihrer Folge für das Niveau, zwei Spalten „Was gut läuft“ / „Was verbessert werden sollte“ nach festen Regeln; siehe [14](14-kurzbericht-pdf.md). Die folgenden Seiten rücken um eine Seite nach hinten |
| 3 | Kennzahlen (bis 2026-10-17 „Datenstand und Kennzahlen“) | Datenstand-Leiste (FA-37) mit allen Zeilen (Mitarbeitende, Bewerbende, letzter Import, Plattform, Kurs, Belege), der Schwellen-Erklärung und der aufklappbaren Zeitstempel-Tabelle; die fünf Kacheln (Ø Score, Trend, 12- vs. 24-Monats-Schnitt, Most Critical, Negative Topic) mit Wert, Badge, n, Warnung bei kleiner Basis und Kennzeichen der Datenbasis; ein Satz, welche Elemente der Zeitfilter betrifft — seit 2026-10-17 zeigt die Seite nur die fünf Kacheln (n in der Kachel, Zeitfenster-Daten auf der letzten Seite) und den Satz zum Zeitfilter; Datenstand-Leiste, Berechnungshinweis und Kategorienmittel stehen auf der letzten Seite |
| 4 | Timeline und Topics im Detail | beide Diagramm-Karten der Diagrammzeile mit Kopf (Quelle, Metrik, Datenbasis), Diagramm, Legende und den Kennzahlen unter dem Diagramm (je Metrik wie in der Karte) |
| 5 | Anomalien im Verlauf | Diagramm-Karte mit Auswahl (Quelle, Status, Dimension), Zähler, Legende (Monatsmittel, interpolierte Monate, Ring, Raute), Kennzahlen (bewertete Monate, Veränderungen, Einzelmonate, Eignung), Eignungshinweis, Statushinweis (E13) und – neu gegenüber der Karte – die markierten Veränderungen und Einzelmonate als Liste, weil ein Tooltip im Druck fehlt. Seit 2026-10-13 tragen Einzelmonate in Legende, Kachel und Listenkopf den Zusatz „ungeprüft“ (E30); mit `VITE_SHOW_OUTLIER_MONTHS=false` entfallen Kachel und Liste, und außerhalb des geprüften Umfangs stand der Vermerk „Erkennung für diese Auswahl nicht geprüft“ (E27, Nachtrag 2026-10-13; am 2026-10-24 auf Entscheidung des Autors entfernt, E25) — seit 2026-10-17 mit kurzer Legende; Schwellen, Status-Hinweis, voller Prüfumfang-Hinweis, Erklärung „ungeprüft“ und der Verweis auf die Detailseite stehen auf der letzten Seite, auf der Seite bleibt nur „nicht geprüft“ bzw. „ungeprüft“ als Vermerk |
| 6 ff. | Topic-Übersicht | Kopf mit n, Warnbanner „Begrenzte Datenbasis“, Stats-Strip, Sentiment-Verteilung und die Tabelle aller Topics mit Beispielzitat; die Tabelle läuft über mehrere Seiten, nichts wird gekürzt — seit 2026-10-17 ohne Warnbanner und ohne Hinweis auf nicht gelieferte Topics (beides auf der letzten Seite); die Markierung je Zeile bleibt |
| letzte Seite (seit 2026-10-17) | Technische Hinweise | Kennzeichen der Datenbasis; Datenstand-Leiste mit Zeitstempel-Tabelle; Berechnung und Zeitfenster der Kacheln (Berechnungshinweis zum Ø Score, Kategorienmittel, Trend- und Schnitt-Fenster mit n, Zeitfilter, Schwelle der kleinen Basis); Schwellen und Prüfumfang der Erkennung, Status-Hinweis, Erklärung der Einzelmonate; Hinweise zur Topic-Übersicht (Herkunft, begrenzte Datenbasis, nicht gelieferte Topics); Regeln des Kurzberichts |

Der Firmenvergleich (`/compare`) hat einen eigenen Export, der unverändert bleibt.

## 2. Erklärung

**Ablauf.** Der Export wartet, bis alle Karten geladen sind (Kennzahlen, Timeline,
Topics im Detail, Anomalien, Topic-Übersicht). Dann holt er die drei Diagramme aus dem
DOM des Dashboards (IDs `timeline-chart-export`, `topic-rating-chart-export`,
`anomaly-chart-export`), wandelt das SVG von Recharts in ein PNG um (html2canvas als
Rückfall) und setzt den Bericht mit jsPDF zusammen. Fehlt ein Diagramm, weil der
gewählte Zeitraum keine Daten hat, zeigt die Karte im PDF denselben Text wie im
Dashboard („Keine Daten für diesen Zeitraum verfügbar“); der Export bricht nicht mehr ab.

**Daten.** Jede Karte meldet ihren Zustand an die Dashboard-Seite, wie es Timeline und
Topic-Übersicht schon taten (`onFiltersChange`, `onDataChange`): die Anomalien-Karte
liefert Auswahl, Zähler, Eignung, Reihe und Hinweise (neu, `AnomalyCard.onDataChange`),
die Topic-Übersicht zusätzlich n und die Zahl der Topics mit begrenzter Basis. Der
Datenstand kommt aus derselben Antwort wie die Leiste (`GET /companies/{id}/data-status`,
Zwischenspeicher in `hooks/useDataStatus.js`, kein zweiter Abruf). Die rollierenden
Schnitte, n je Kachel und der globale Zeitfilter liegen bereits im Zustand der Seite.

**Texte.** Die Formulierungen des Datenstands stehen seit diesem Nachtrag in
`frontend/src/lib/dataStatusText.js` und werden von Leiste und Export gemeinsam genutzt;
die Kacheltexte nutzen `lib/rollingAverage.js` (Zeitraum, Lage, Warnungen) und
`lib/dataBasis.js` (Vokabular der Datenbasis, Schwelle 10 Bewertungen je Fenster).
So kann der Bericht nicht von der Oberfläche abweichen.

**Parameter (alle Setzungen des Autors, vorläufig).**

| Parameter | Wert | Zweck |
|---|---|---|
| Breite der Diagramm-PNGs | 3000 px | scharfe Linien im Druck |
| Bildkompression | Flate („FAST“ in jsPDF) | Dateigröße; ohne Kompression lagen drei Diagramme bei 42 MB, mit Kompression bei 0,7 MB |
| Kacheln je Zeile | 3 | wie die mittlere Breite des Dashboards (3 + 2); fünf nebeneinander wären zu schmal für die Fußnoten |
| Zeilenhöhe der Kacheln | höchste Kachel der Zeile | mehrzeilige Fußnoten (rollierende Schnitte) bleiben lesbar |
| Tabellenzeile Topic-Übersicht | 10,5 mm mit Beispiel, 7 mm ohne | Beispielzitat wie in der Tabelle der Web-App |
| Seitenumbruch | unterhalb von 278 mm | Fußzeile bleibt frei; Tabellenkopf wird auf Folgeseiten wiederholt |
| Kennzahlen-Streifen unter Diagrammen und Karten | 20 mm je Zelle (bis 2026-10-17: 16 mm) | Bezeichnung, Wert (14 pt) und Unterzeile (7 pt) auf drei getrennten Grundlinien; bei 16 mm überlappte die Unterzeile den Wert (Rückmeldung des Autors am 2026-10-17) |
| Höhe des Diagrammbereichs | höchstens der feste Wert der Karte (58 bzw. 78 mm), sonst Breite × Seitenverhältnis des Bildes + 4 mm, mindestens 24 mm | breite Diagramme (Anomalien-Karte, 220 px hoch im DOM) standen sonst mit Leerraum ober- und unterhalb im Rahmen (seit 2026-10-17) |

## 3. Begründung

**Warum alle Elemente?** Inkrement 6 hat dem Dashboard Transparenz hinzugefügt: n je
Kachel, Kennzeichen der Datenbasis, Warnungen bei kleiner Basis, Datenstand. Ein
Bericht, der diese Angaben weglässt, zeigt dieselben Zahlen ohne ihre Einordnung – das
widerspricht FA-25 bis FA-37. Der Export übernimmt deshalb jedes Element mit genau den
Texten der Oberfläche.

**Warum Listen auf der Anomalien-Seite?** Im Dashboard erklärt ein Tooltip jede
Markierung (Delta, Ø davor und danach, Bewertungen je Abschnitt, Lücken). Im Druck gibt
es keinen Tooltip; ohne Liste wären die Ringe im Diagramm unerklärt. Die Liste enthält
dieselben Angaben wie der Tooltip, mit derselben Wortwahl („auffällige Veränderung“,
keine Ursachen).

**Warum ein Satz zum Zeitfilter?** Der Zeitfilter des Dashboards gilt für Kennzahlen,
Timeline, Topics und Topic-Übersicht, nicht für die rollierenden Schnitte (fester Anker,
FA-08) und nicht für die Anomalien (ganze Reihe). Im Dashboard ist das durch die Lage
der Elemente erkennbar, im Bericht nicht; der Satz unter den Kacheln nennt es.

**Warum Diagramme als Rasterbild?** Recharts zeichnet SVG mit Theme-Variablen; jsPDF
kann SVG nicht verlässlich einbetten. Die Umwandlung in PNG übernimmt die berechneten
Farben und ist seit dem ersten Export das Verfahren. Verworfen: ein serverseitiger Export
(das Backend kennt die Diagramme nicht; das Dashboard ist die einzige Quelle der
Darstellung) und html2canvas über die ganze Seite (bricht an oklch-Farben, wurde schon
im ersten Export nur als Rückfall genutzt).

## 4. Grenzen

- Die Diagramme übernehmen die Farben des aktiven Themes. Im dunklen Theme sind Achsen
  und Beschriftungen hell und auf dem weißen PDF schlecht lesbar; der Export sollte im
  hellen Theme ausgeführt werden.
- Die Größe der Diagramme hängt von der Breite des Browserfensters ab (die Karten sind
  im DOM 220 px hoch); in schmalen Fenstern sind die Bilder schmaler.
- Die Legende unter „Topics im Detail“ nennt wie die Karte höchstens sechs Topics und
  zählt die übrigen („+ n weitere“).
- Die Topic-Tabelle ist nach Erwähnungen sortiert (Standard der Tabelle in der Web-App);
  Sortierung und Sentiment-Filter der Web-App werden nicht übernommen.
- Der Bericht beschreibt; er enthält keine Aussage über Ursachen. Seit dem 2026-10-17
  enthält die Seite „Kurzbericht“ Stärken und Handlungsfelder, die nach festen,
  auf der Seite genannten Regeln aus den Bewertungen abgeleitet sind ([14](14-kurzbericht-pdf.md)).
- Es gibt keine automatischen Tests für das Frontend; die Prüfung ist manuell.

## 5. Prüfung und Belege

- `npm run lint` (ESLint) ohne Fehler und Warnungen; `npm run build` erfolgreich.
- Manuell am 2026-10-09 gegen das laufende Backend (Port 8000), heller Modus:
  - Bechtle (geeignete Reihe, 1 auffällige Veränderung, 23 Topics mit Beispiel): 6 Seiten,
    0,7 MB; alle fünf Kacheln mit n und Kennzeichen, Datenstand mit Zeitstempel-Tabelle,
    Anomalien-Seite mit Liste, Topic-Tabelle über zwei Seiten.
  - Bechtle mit Zeitfilter „1 Jahr“ (keine Bewertungen im Zeitraum) und Status
    „Ex-Angestellt“ in der Anomalien-Karte: Cover nennt „1 Jahr“, Diagramm-Karten zeigen
    den Text der Karte statt eines Diagramms, die Anomalien-Karte die gewählte Gruppe.
- Code: `frontend/src/utils/pdfExport.js` (Export), `frontend/src/pages/Dashboard.jsx`
  (Sammeln der Zustände), `frontend/src/components/dashboard/AnomalyCard.jsx`
  (`onDataChange`, ID `anomaly-chart-export`), `TopicOverviewCard.jsx` (n, begrenzte
  Basis), `DataStatusBar.jsx` und `frontend/src/lib/dataStatusText.js` (gemeinsame Texte).

## 6. Offene Punkte

- Rückmeldung der Interviewpartner (DZ3), ob die Listen auf der Anomalien-Seite im
  Bericht erwünscht sind oder die Karte allein genügt.
- Export im dunklen Theme: entweder die Diagramme für den Export im hellen Theme neu
  zeichnen oder den Export auf das helle Theme beschränken.
- Ob der Bericht die Detailseiten (Anomalien, Aktie) aufnehmen soll; derzeit bewusst nur
  das Dashboard.

## 7. Nachtrag 2026-10-17: Technische Hinweise auf der letzten Seite

**Anlass.** Rückmeldung des Autors am 2026-10-17: Die Inhaltsseiten sollen nur die
Elemente zeigen, die auf den ersten Blick sichtbar sein müssen; die technischen Angaben
(Datengrundlage, Berechnung, Schwellen) sollen gesammelt auf der letzten Seite stehen.

**Was sich ändert.** Der Bericht bekommt als letzten Abschnitt die Seite „Technische
Hinweise“ (im Inhalt 06, in der Zählung der Überschriften 7). Dorthin wandern,
wortgleich wie bisher: die Kennzeichen der Datenbasis (FA-25), die Datenstand-Leiste
mit Zeitstempel-Tabelle (FA-37), der Berechnungshinweis zum Ø Score und das
Kategorienmittel (FA-38), die Zeitfenster von Trend und rollierenden Schnitten mit n
(FA-08, FA-26), der Satz zum Zeitfilter, die Schwelle der kleinen Basis, die Schwellen
der Erkennung (bewertete Monate, Mindestzahl, Abschnittslänge), der Status-Hinweis und
der volle Hinweis zum Prüfumfang (E27), die Erklärung „ungeprüft“ der Einzelmonate (E30),
der Verweis auf die Detailseite, die Hinweise der Topic-Übersicht (Herkunft, begrenzte
Datenbasis, nicht gelieferte Topics) und die Regeln des Kurzberichts ([14](14-kurzbericht-pdf.md)).

**Was auf den Inhaltsseiten bleibt.** Werte, Badges, n und die Warnung bei kleiner
Basis in den Kacheln; Legenden mit einem Satz je Element; die Kennzahlen unter den
Diagrammen; die Tabellen der Veränderungen und Einzelmonate; die Markierung begrenzter
Datenbasis je Topic-Zeile; die kurzen Vermerke „ungeprüft“ (Einzelmonate) und „Keine
automatische Erkennung“ mit Grund (der Vermerk „Erkennung für diese Auswahl nicht geprüft“
ist seit 2026-10-24 entfernt, E25). Jede
Seite, von der etwas verschoben wurde, verweist mit „Technische Hinweise (letzte Seite)“
dorthin. Die Kachel-Fußnoten nennen statt der Fensterdaten nur noch n („n = 88 vs. 76“,
„n = 88 (12 M) · 164 (24 M)“); die Daten der Fenster stehen auf der letzten Seite.

**Begründung.** Die Transparenz-Angaben aus Inkrement 6 bleiben vollständig im Bericht,
nur an einer Stelle statt verteilt; n und Warnungen bleiben neben den Werten, weil sie
die Einordnung einer Zahl sind (FA-26), nicht ihre Erklärung. Die Texte kommen weiter
aus denselben Bibliotheken wie das Dashboard, der Wortlaut bleibt gleich.

**Darstellung.** Die letzte Seite setzt die Blöcke als Zwischenüberschrift mit Absätzen
(7 pt). Ein Block bleibt zusammen, wenn er auf die Seite passt, sonst bricht er zwischen
zwei Absätzen um; bei vielen Veränderungen oder langen Hinweisen umfasst die Seite zwei
Blätter.

**Prüfung (2026-10-17).** `npm run lint` 0/0, `npm run build` erfolgreich; Rendern in
Node gegen das laufende Backend (1&1 AG: 8 Seiten, Telekom, Formycon) mit Sichtung von
Kurzbericht, Kennzahlen, Anomalien und Technische Hinweise; Export-Knopf im Dashboard
(Vite auf Port 5173, Backend auf Port 8000, heller Modus, 1&1 AG): 8 Seiten ohne Fehler,
Konsole meldet „PDF gespeichert“, letzte Seite „Technische Hinweise“ auf einem Blatt.

## 8. Nachtrag 2026-10-17: Überlappende Beschriftungen

Rückmeldung des Autors anhand eines exportierten Berichts: In den Kennzahlen-Streifen
(„Lage der Bewertung“, unter Zeitverlauf, Topics im Detail und Anomalien, Stats-Strip
der Topic-Übersicht) überlappte die Unterzeile („Okt. 2016 – Juli 2025“, „1.486
Bewertungen“) den großen Wert. Ursache: 16 mm Zellhöhe mit Wert-Grundlinie bei 11 mm und
Unterzeile bei 13 mm. Korrektur: Zellhöhe 20 mm, Wert bei 11,5 mm, Unterzeile bei 17 mm
(Tabelle der Parameter oben); die Kartenhöhe folgt automatisch. In den Kacheln rücken
Badge und Kennzeichen um 1 mm nach unten, damit das Komma des Werts die Pille nicht
berührt. Zusätzlich richtet sich die Höhe des Diagrammbereichs nach dem Seitenverhältnis
des Bildes; die Anomalien-Karte stand vorher mit großem Leerraum im 78-mm-Rahmen.
Geprüft am 2026-10-17 mit Node-Render (Streifen) und Export-Knopf im Dashboard
(Diagramme, 1&1 AG, 8 Seiten ohne Fehler).

## 9. Nachtrag 2026-10-17: Prüfung der Berichtsqualität

Mit der Prüfung in [16](16-report-qualitaet.md) änderte sich der Bericht an diesen Stellen:
Mittel durchgängig mit zwei Nachkommastellen; Ø Score und Trend-Differenz mit 95-%-Intervall
(Kachel-Fußnote, Kurzbericht, Technische Hinweise); „Ø Historisch“ heißt „Ø Monatsmittel“;
die Prognose steht mit einer Nachkommastelle und ±Bandbreite (80 %, aus dem Backtest), die
Bildunterschrift nennt die helle Fläche; „Sentiment“ heißt „Einstufung“ (nach Ø Sternen);
„Ø Rating“ der Topic-Übersicht heißt „Ø Topic-Mittel“ (n Topics, ungewichtet), der Kopf
nennt bei „Alle Quellen“ Mitarbeitende und Bewerbende getrennt; die Legende von „Topics im
Detail“ nennt die Kategorien-Sterne; die Tabellen der Veränderungen (Kurzbericht und Seite
„Anomalien“) tragen die Spalte „Stabilität“ (Treffer/Varianten); die Datenstand-Leiste nennt
Duplikate und Zeilen ohne Gesamtnote; der Kurzbericht hat Datenstand, Warnungen und nächste
Analyseschritte; die Technischen Hinweise haben die Blöcke Zeitverlauf (mit Backtest) und
Grenzen. Der Bericht umfasst bei 1&1 AG und Telekom 9 Seiten.
