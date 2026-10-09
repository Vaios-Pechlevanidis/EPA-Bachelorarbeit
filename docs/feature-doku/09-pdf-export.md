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
| 2 | Datenstand und Kennzahlen | Datenstand-Leiste (FA-37) mit allen Zeilen (Mitarbeitende, Bewerbende, letzter Import, Plattform, Kurs, Belege), der Schwellen-Erklärung und der aufklappbaren Zeitstempel-Tabelle; die fünf Kacheln (Ø Score, Trend, 12- vs. 24-Monats-Schnitt, Most Critical, Negative Topic) mit Wert, Badge, n, Warnung bei kleiner Basis und Kennzeichen der Datenbasis; ein Satz, welche Elemente der Zeitfilter betrifft |
| 3 | Timeline und Topics im Detail | beide Diagramm-Karten der Diagrammzeile mit Kopf (Quelle, Metrik, Datenbasis), Diagramm, Legende und den Kennzahlen unter dem Diagramm (je Metrik wie in der Karte) |
| 4 | Anomalien im Verlauf | Diagramm-Karte mit Auswahl (Quelle, Status, Dimension), Zähler, Legende (Monatsmittel, interpolierte Monate, Ring, Raute), Kennzahlen (bewertete Monate, Veränderungen, Einzelmonate, Eignung), Eignungshinweis, Statushinweis (E13) und – neu gegenüber der Karte – die markierten Veränderungen und Einzelmonate als Liste, weil ein Tooltip im Druck fehlt |
| 5 ff. | Topic-Übersicht | Kopf mit n, Warnbanner „Begrenzte Datenbasis“, Stats-Strip, Sentiment-Verteilung und die Tabelle aller Topics mit Beispielzitat; die Tabelle läuft über mehrere Seiten, nichts wird gekürzt |

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
- Der Bericht beschreibt; er enthält keine Bewertung und keine Aussage über Ursachen.
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
