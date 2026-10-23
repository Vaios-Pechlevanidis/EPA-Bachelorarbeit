# 13 – Vorschau-Karten auf der Anomalien-Seite

| | |
|---|---|
| Inkrement | Korrektur der Darstellung (2026-10-16), keine neue Funktion |
| Anforderungen | keine eigene Anforderung; Rückmeldung des Autors: Die Detailseite „Anomalien im Verlauf“ zeigte zu viel Text auf einmal, die Listen hatten zu wenig Platz, und man sollte auf einen Blick sehen, wo die stärksten Unterschiede liegen |
| Entscheidungen | keine neue Entscheidung; die Inhalte aus [02](02-drilldown-und-vergleich.md), [06](06-freier-drilldown.md), [07](07-externe-belege.md) und [08](08-erklaerungsansaetze.md) bleiben unverändert |
| Status | umgesetzt (2026-10-16, zwei Durchgänge), noch nicht committet; Zahl der gezeigten Themen und Ansätze **vorläufig** |
| Stand | 2026-10-16 |

## 1. Vorstellung

Auf der Detailseite **„Anomalien im Verlauf“** (`/anomalies`) stehen nach der Auswahl einer
auffälligen Veränderung, eines Einzelmonats oder eines freien Zeitraums unter der
Drill-down-Leiste nicht mehr vier große Abschnitte untereinander, sondern **vier Karten
in einer Reihe**, wie die Kennzahlen-Kacheln und Diagramm-Karten des Haupt-Dashboards:

1. **Vorher-Nachher-Vergleich** (bei freier Auswahl: „Vergleich mit dem Zeitraum davor“)
2. **Bewertungen des Zeitraums** (bei freier Auswahl: „Bewertungen der Auswahl“)
3. **Mögliche Zusammenhänge**
4. **Externe Berichte im Ereignisfenster**

Jede Karte beginnt mit **einer großen Kennzahl** und zeigt darunter höchstens ein kleines
Diagramm oder eine Zahlenreihe – kaum Fließtext. So sieht man beim Überfliegen, wo die
stärksten Unterschiede liegen. Die Fußzeile sagt „Karte anklicken öffnet Detailansicht“;
ein **Klick auf die Karte** öffnet die bisherige vollständige Ansicht in einem Dialog mit
90 % der Fensterbreite und 85 % der Fensterhöhe – dieselbe Mechanik wie beim Zeitverlauf
oder den Topics im Haupt-Dashboard. Die Schalter stehen nur im Dialog: „davor / ab dem
markierten Monat“ und der Themenfilter bei den Bewertungen, Sortierung (Datum, Relevanz)
und Filter nach Ereignisart bei den Berichten. Aus der Bewertungsliste im Dialog öffnet
ein Klick wie bisher die Einzelbewertung in ihrem eigenen Fenster.

Vorschau je Karte (Beispiel 1&1 AG, Veränderung ab Okt. 2016):

- *Vergleich:* Kennzahl **−0,74 Sterne** in Rot mit dem Chip „Abfall“ (bei Anstieg Grün,
  „Anstieg“); darunter „Ø 3,84 → 3,10 · 56 → 31 Bewertungen“. Dann **„Stärkste
  Verschiebungen je Thema“**: die drei größten Verschiebungen als Balken auf einer hellen
  Spur (Länge = Betrag, die größte füllt die Spur), daneben der Wert mit Vorzeichen, z. B.
  Kollegenzusammenhalt **+29,4 Pp.**, Kommunikation **+18,7 Pp.**, Vorgesetztenverhalten
  **+17,6 Pp.** Bei kleiner Basis eine Warnzeile in Bernstein; beim Einzelmonat zuerst die
  Warnzeile zur Abweichung mit dem Zusatz „ungeprüft (E30)“.
- *Bewertungen:* Kennzahl **31 Bewertungen** mit dem Chip „Ø 3,10“ (Farbe wie bei der
  Kachel „Ø Score“: ab 3,5 grün, ab 2,5 gelb, sonst rot); darunter Fenster und Zeitraum,
  bei gewählter Dimension „12 nennen Image“. Dann **„Stimmung der Freitexte“** als zwei
  gestapelte Balken positiv / neutral / negativ für „davor“ und „danach“ (bzw. „Auswahl“)
  mit den Anteilen als Zahl, z. B. „21 % pos. · 39 % neg.“ gegenüber „4 % pos. · 57 % neg.“.
- *Mögliche Zusammenhänge:* Kennzahl **1 Ansatz** (oder **Offen**) mit „aus 25 Belegen ·
  25 Bündel“; darunter bis zu zwei Ansätze mit Ereignisart, Kennzeichen der Signale und
  Datum, ohne Titel der Meldung.
- *Externe Berichte:* Kennzahl **25 Belege** mit Ereignisfenster „Juli 2016 – Nov. 2016 ·
  5 Monate“; darunter **„Nach Quelle“** als kleine Zahlen: 19 Meldungen, 6 EQS (allgemeine
  Ereignisse nur, wenn vorhanden). Ohne Beleg: „0 Belege“ und der Hinweis, dass ein
  fehlender Beleg nicht heißt, dass nichts geschehen ist.

Der Monatsverlauf, die Liste der Markierungen und die Drill-down-Leiste sind unverändert.

## 2. Erklärung

Die Karten verwenden die vorhandene Komponente `ExpandableCard`
(`frontend/src/components/dashboard/ExpandableCard.jsx`), mit der schon das
Aktien-Dashboard arbeitet: Kopf mit Symbol, Kennung, Titel, Untertitel und Datenbasis,
Inhalt, Fußzeile; der Dialog zeigt denselben Kopf und rendert den Inhalt mit `modal = true`.
Neu ist nur, dass der Untertitel kurz (Karte: die Bewertendengruppe) oder vollständig
(Dialog) sein kann und die Fußzeile einen eigenen Text bekommt.

Die vier Karten stehen in `AnomalyDetailCards.jsx`; die Bausteine der Vorschau in
`CardPreview.jsx`: `Headline` (große Kennzahl mit Einheit, Chip und einer Zeile Kontext),
`ShiftBars` (Balken für den Betrag, Vorzeichen in der Zahl), `SentimentRows` (gestapelte Balken mit 2 px
Abstand zwischen den Segmenten), `FigureRow` (kleine Zahlen nebeneinander), `Warn`,
`PreviewStatus`. Die Seite `Anomalies.jsx` baut je nach Auswahl ein Objekt `detail`
(Bezeichnungen, Fenster, Datenquelle) und rendert damit eine Kartenreihe – dieselben
Bausteine für eine Veränderung, die freie Auswahl und den Einzelmonat.

Die Daten sind dieselben wie bisher; es gibt keine neue Berechnung:

- *Vergleich*, *Bewertungen* (Note und Stimmung je Fenster) und *Mögliche Zusammenhänge*
  lesen die Antwort des Vergleichs (`GET …/anomalies/{id}/explanations` bzw.
  `GET …/compare`, [02](02-drilldown-und-vergleich.md), [08](08-erklaerungsansaetze.md)).
  Die „stärksten Verschiebungen je Thema“ sind die ersten drei Einträge der dort schon
  nach Größe sortierten Themenliste; die Balkenlänge ist relativ zur größten der drei.
- *Bewertungen* nimmt die Anzahl aus der ersten Seite der Bewertungsliste
  (`useReviewPages`, `total`), die mittlere Note und die Stimmung je Fenster aus der
  Antwort des Vergleichs (dort je Fenster gezählt). Mit Themenfilter entfällt die Note,
  weil der Vergleich nicht gefiltert ist; die Stimmungsbalken gelten immer für alle
  Bewertungen des Fensters.
- *Externe Berichte* nimmt Zählung je Quelle und Ereignisfenster aus der Antwort der
  Belegliste (`useEvidence`, [07](07-externe-belege.md)). Sortierung nach Relevanz und
  Filter laden wie bisher alle Belege nach (`useEvidenceList` in `hooks/useEvidence.js`).

Farben: Rot / Grün für Abfall / Anstieg wie im Monatsverlauf und bei der Trend-Kachel;
Smaragd / Grau / Rosé für positiv / neutral / negativ wie in der Stimmungsleiste des
Vergleichs; Blau für die Themenbalken (Werte aus den Bewertungen). Text trägt nie die
Datenfarbe; Richtung und Bedeutung stehen immer auch als Zahl oder Wort daneben
(Chip „Abfall“, Vorzeichen, „% pos. · % neg.“).

Parameter (alle **vorläufig**, reine Darstellung): drei Themen beim Vergleich, zwei Ansätze
bei den Zusammenhängen, vier Spalten ab 1280 px Breite, zwei Spalten ab 768 px, darunter
eine Spalte.

## 3. Begründung

- **Rückmeldung des Autors (2026-10-16, zwei Durchgänge):** Die Ansicht war
  unübersichtlich – zu viele Texte gleichzeitig, und die Listen (Bewertungen, Belege)
  hatten in ihren festen Scrollbereichen zu wenig Platz. Ein erster Durchgang mit
  Stichpunkten je Karte war dem Autor immer noch zu textlastig; das Ziel ist, beim
  Draufschauen zu sehen, wo die stärksten Unterschiede liegen. Daher der zweite
  Durchgang: Kennzahl zuerst, dann ein kleines Diagramm, Text nur als Beschriftung.
- **Form nach Aufgabe der Daten:** Eine einzelne Kennzahl mit Richtung ist eine
  Stat-Kachel, kein Diagramm; die Frage „wo ist die Verschiebung am größten?“ ist eine
  Frage nach dem Betrag, also ein Balken je Thema vom linken Rand aus (ein erster
  Versuch mit Balken um eine Mittelachse war in der Kartenbreite nicht lesbar: die Achse
  verschwand, die Balken wirkten wie Stummel) – die Richtung trägt das Vorzeichen der
  Zahl daneben; Anteile positiv / neutral / negativ sind ein gestapelter Balken; die
  Belege je Quelle sind drei Zahlen. Das folgt dem Grundsatz, die Darstellungsform aus der
  Aufgabe der Daten abzuleiten (Magnitude, Polarität, Anteil), nicht aus dem Geschmack.
- **Konsistenz mit dem Haupt-Dashboard:** Dort gilt seit Inkrement 6 „Karte anklicken
  öffnet Detailansicht“ für Kennzahlen und Diagramme (Shneidermans Regel „Strive for
  consistency“, *Designing the User Interface*). Die Anomalien-Seite folgt demselben
  Muster mit derselben Komponente, derselben Schriftgröße der Kennzahl und denselben
  Farbstufen für die Note; wer das Dashboard kennt, muss nichts Neues lernen.
- **Übersicht zuerst, Details auf Abruf:** Die Reihenfolge Überblick → Auswahl → Details
  entspricht dem Visual-Information-Seeking-Mantra („overview first, zoom and filter,
  then details-on-demand“, Shneiderman 1996). Monatsverlauf und Markierungen sind der
  Überblick, die Drill-down-Leiste die Auswahl, die Karten die Vorschau der Details, der
  Dialog die Details selbst.
- **Keine Änderung an Inhalt und Wortwahl:** Alle Texte im Dialog, die Hinweise („keine
  Aussage über Ursachen“), die Kennzeichen der Datenbasis (FA-25) und die Warnungen bei
  kleiner Basis (FA-26) bleiben; die Vorschau nimmt nur eine Teilmenge der Zahlen. So
  bleibt die Bewertung aus DZ1/DZ2 unberührt.
- **Alternative, nicht gewählt:** Die Abschnitte einklappbar machen (Akkordeon). Das hätte
  die Seite kürzer, aber nicht übersichtlicher gemacht; die Listen wären weiterhin in
  kleinen Bereichen gescrollt, und das Muster wäre neu gegenüber dem Haupt-Dashboard.

## 4. Grenzen

- Die Vorschau zeigt **keine einzelne Bewertung und keinen einzelnen Beleg**; welche
  Belege zählen, entscheidet weiterhin nur die Lesende oder der Lesende im Dialog.
- Die Themenbalken zeigen nur den **Betrag**, relativ zur größten der drei gezeigten
  Verschiebungen, nicht absolut; ob ein Thema häufiger oder seltener genannt wird, steht
  allein im Vorzeichen der Zahl, und zwei Auswahlen lassen sich über die Balkenlänge
  nicht vergleichen, nur über die Zahl daneben.
- Die Stimmungsbalken gelten für alle Bewertungen des Fensters, auch wenn im Dialog der
  Themenfilter aktiv ist; die Anzahl in der Kennzahl ist dann gefiltert, die Stimmung
  nicht (beschriftet als „nur Bewertungen, die … nennen“ bzw. „Stimmung der Freitexte“).
  Seit 2026-10-18 ist der Themenfilter ein Auswahlfeld für jedes Thema (Doku 17).
- Anzahl und mittlere Note in der Bewertungskarte stammen aus zwei Quellen
  (Bewertungsliste, Vergleich); sie passen, weil beide dasselbe Fenster und dieselbe
  Gruppe verwenden, sind aber keine gemeinsame Berechnung.
- Rot / Grün für Abfall / Anstieg ist für Rot-Grün-Schwäche allein nicht unterscheidbar;
  deshalb stehen Vorzeichen, Pfeil und Wort („Abfall“) daneben, wie im Monatsverlauf.
- Der PDF-Export betrifft nur das Haupt-Dashboard ([09](09-pdf-export.md)); die
  Detailseite wird weiterhin nicht exportiert.

## 5. Prüfung und Belege

- Dateien: `frontend/src/components/dashboard/AnomalyDetailCards.jsx` (neu),
  `CardPreview.jsx` (neu), `ExpandableCard.jsx` (Untertitel je Ansicht, Fußzeile),
  `ExplanationPanel.jsx` und `EvidenceSection.jsx` (Vorschau und Dialoginhalt statt
  Abschnitt), `frontend/src/lib/explanationText.js` und `evidenceText.js` (Texte, aus den
  Komponentendateien herausgelöst), `frontend/src/hooks/useEvidence.js` (`useEvidenceList`),
  `frontend/src/pages/Anomalies.jsx`.
- `npm run lint`: 0 Fehler, 0 Warnungen; `npm run build`: erfolgreich (2026-10-16).
- Manuell im Browser (1&1 AG, Veränderung ab Okt. 2016 und freie Auswahl Jan.–Juni 2019):
  Kartenreihe in dunklem und hellem Theme, bei 1440 px (vier Spalten) und 1100 px (zwei
  Spalten); Dialoge aller vier Karten; aus dem Bewertungsdialog die Einzelbewertung; im
  Berichtedialog Sortierung nach Relevanz. Keine Fehler in der Konsole nach dem Laden.
- Noch nicht committet (Stand 2026-10-16).

## 6. Offene Punkte

- Vier Karten nebeneinander: vom Autor nach Sichtung bestätigt (2026-10-16); eine
  Anordnung in zwei Reihen à zwei Karten ist damit nicht vorgesehen.
- Sollen die Themenbalken absolut skaliert werden (z. B. 50 Pp. = volle Breite), damit
  Auswahlen untereinander vergleichbar sind?
- Rückmeldung der Interviewpartner (DZ3) zur Lesbarkeit der Kennzahlen und Balken.

## Nachtrag 2026-10-23: Kopf der Dialoge

Im Dialog einer Karte (`ExpandableCard`) nehmen Titel und Untertitel die Restbreite und brechen
um; die Schalter rechts bleiben in einer Reihe und rücken nur bei schmalem Fenster als Ganzes
unter den Titel. Vorher brachen die Schalter einzeln um, sobald der Untertitel länger wurde (etwa
beim Wechsel davor / ab dem markierten Monat in „Bewertungen des Zeitraums“), und der Kopf sprang
(Rückmeldung des Autors). Geprüft bei 1800 px (eine Reihe in beiden Fenstern, Kopf 91 px hoch) und
bei 577 px (Schalter unter dem Titel, kein Überlauf).
