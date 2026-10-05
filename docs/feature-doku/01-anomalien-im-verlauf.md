# 01 – Anomalien im Verlauf

| | |
|---|---|
| Inkrement | 1 (Zyklus 2) |
| Anforderungen | FA-01 bis FA-04, Zähler aus FA-26 |
| Entscheidungen | E3 (Erkennungsreihe), E4 (Mindestdichte), E5 (Referenzzeiträume, aktualisiert), E9 (Verfahren und Parameter) |
| Status | Inkrement 1 abgeschlossen: Karte und Detailseite mit Dimensionsauswahl (Quelle Mitarbeitende), gestrichelt überbrückten Lücken, Eignungshinweis und Zeitfilter auf der Detailseite. Parameter **vorläufig** (E9) |
| Stand | 2026-10-03 |

## 1. Vorstellung

**Aufbau der Detailseite seit 2026-10-05** (angelehnt an das Aktien-Dashboard, Doku 05):

1. **Kennzahlenleiste** mit sechs Kacheln für die gewählte Gruppe und Dimension: letzter
   bewerteter Monat, Ø der letzten 12 Monate je Bewertung mit Vorjahr und Differenz,
   Zahl der Bewertungen und bewerteten Monate, Zahl der auffälligen Veränderungen (Abfälle,
   Anstiege), letzte Veränderung, Zahl der auffälligen Einzelmonate (E14). Differenzen ab
   0,1 Sternen sind rot bzw. grün gefärbt. Die Kacheln gelten für die ganze Reihe,
   unabhängig vom Zeitfilter (`frontend/src/components/dashboard/AnomalyKpis.jsx`).
2. **Raster:** links der Monatsverlauf (zwei Drittel der Breite), rechts die Karte
   **„Markierungen“** mit Umschalter „Veränderungen“ / „Einzelmonate“ (`?liste=einzelmonate`)
   als kompakte, zweizeilige Liste mit eigenem Scrollbereich in Höhe des Verlaufs.
3. **Drill-down-Leiste** in einer Zeile: aktuelle Auswahl, „von / bis“, Schnellwahl,
   „Auswahl aufheben“ (Doku 06).
4. **Auswahl:** Vergleich (links, drei Fünftel) und Bewertungen (rechts, zwei Fünftel, eigener
   Scrollbereich) nebeneinander, für eine erkannte Veränderung wie für eine freie Auswahl.

Unter 1280 px Breite stehen die Bereiche untereinander; die Kopfzeile bricht bei schmalen
Fenstern um, statt seitlich zu überlaufen.

Im Dashboard steht unter der Diagrammzeile (Timeline, Topics im Detail) die Karte
**„Anomalien im Verlauf“**. Sie zeigt:

- den **Monatsverlauf** der gewählten Dimension, also den Durchschnitt der Sterne je
  Kalendermonat. Standard ist die Gesamtbewertung; über das Auswahlfeld „Dimension“ lassen
  sich die 13 Einzelkategorien wählen (Arbeitsatmosphäre, Kommunikation, …),
- **Lücken:** Monate mit weniger als 5 Bewertungen mit Wert in der gewählten Dimension
  („nicht bewertet“) unterbrechen die
  durchgezogene Linie. Liegt eine solche Lücke zwischen zwei bewerteten Monaten, wird sie
  mit einer dünnen, grau **gestrichelten** Linie überbrückt (lineare Interpolation, nur
  Darstellung). Ein bewerteter Monat
  zwischen zwei Lücken erhält einen kleinen Punkt,
- **Anzeigebereich:** Das Diagramm beginnt beim ersten und endet beim letzten bewerteten
  Monat. Leere Ränder davor und danach (dort gibt es keinen Monat mit genug Bewertungen und
  nichts zu überbrücken) werden ausgeblendet und in einer Zeile unter dem Diagramm genannt,
  z. B. bei E.ON „Jan. 2018 – Feb. 2019 (14 Monate), Apr. 2026 (1 Monat)“ und bei Open Grid
  Europe „Feb. 2013 – Dez. 2016 (47 Monate), März 2026 (1 Monat)“. Mit Zeitfilter bleibt der
  hintere Rand genannt, weil das Fenster am letzten bewerteten Monat endet (Universität
  Duisburg-Essen, „12 Monate“: „Dez. 2024 – Apr. 2026 (17 Monate)“),
- auf der **Detailseite** eine dezente **Stufe** an jedem Monat, ab dem das Bewertungsniveau auffällig anders
  liegt: ein kurzer Strich auf dem Ø davor, ein senkrechter Strich bis zum Ø danach und
  ein kurzer Strich auf dem neuen Niveau. Die **Höhe** der Stufe ist das Ausmaß im Maßstab
  der Y-Achse, die **Form** zeigt die Richtung (nach unten = Abfall, nach oben = Anstieg)
  und ist auch ohne Farbe lesbar; zusätzlich rot bzw. grün. Ein **kräftiger** Strich heißt
  „deutlich“ (ab 0,5 Sternen), ein dünner „mäßig“. Eine Legende unter dem Diagramm erklärt
  die Zeichen,
- auf der Detailseite zusätzlich eine dünne graue **Niveaulinie**: das Mittel jedes
  Abschnitts zwischen zwei erkannten Wechseln, also genau die Werte, die die Erkennung
  verglichen hat,
- auf der **Dashboard-Karte** die Darstellung der ersten Version: kräftige Monatslinie und
  je Veränderung ein dezenter **Ring** auf dem Monatswert des markierten Monats (rot =
  Abfall, grün = Anstieg, etwas größer bei „deutlich“); darunter nur Interpolation und
  Datenbasis. Stufen, Niveaulinie, ausführliche Legende und ausgeblendete Ränder stehen nur
  auf der Detailseite,
- einen **Tooltip** je Monat mit dem Monatsmittel und der Zahl der Bewertungen (bei
  Einzeldimensionen zusätzlich „davon mit Wert“, wenn nicht jede Bewertung diese Kategorie
  bewertet hat), bei nicht
  bewerteten Monaten mit dem Vermerk „nicht bewertet“ und, wenn die Linie dort überbrückt
  ist, „Linie interpoliert, nur Darstellung“; ein interpolierter Zahlenwert wird nie
  angezeigt. Auf einem markierten Monat zeigt er
  zusätzlich Delta, Mittel davor und danach und die Bewertungen davor / danach,
- unter dem Diagramm den **Hinweis zur Datenbasis**: „Sternebewertung, Monatsmittel, Monate
  mit mindestens 5 Bewertungen mit Wert“, bei überbrückten Lücken zusätzlich die Legende
  „interpoliert (Monat mit weniger als 5 Bewertungen mit Wert, nicht in der Erkennung)“,
- auf der Detailseite eine **Liste** der Veränderungen unter dem Diagramm, Abfälle zuerst,
  innerhalb nach Größe. Auf der Dashboard-Karte steht keine Liste (seit 2026-10-03), damit
  das Dashboard übersichtlich bleibt; der Zähler im Untertitel und der Hinweis „Karte
  anklicken öffnet die Detailseite mit der Liste“ führen dorthin,
- die **Anzahl** der auffälligen Veränderungen im Untertitel der Karte (Zähler aus FA-26),
- bei Unternehmen mit zu wenig Daten statt einer leeren Liste den Hinweis **„Keine
  automatische Erkennung“** mit Grund, zum Beispiel „Nur 5 bewertete Monate (mindestens 12
  nötig, je Monat mindestens 5 Bewertungen)“. „Keine auffälligen Veränderungen erkannt“
  erscheint nur, wenn die Reihe geeignet ist und nichts gefunden wurde.

**Detailseite:** Ein Klick auf die Karte oder auf „Anomalien“ in der linken Navigation
öffnet die eigene Seite `/anomalies?company=ID&dimension=KEY`, ähnlich wie der
Firmenvergleich; die auf der Karte gewählte Dimension wird übernommen. Dort stehen ein
größeres Diagramm und die Liste. Oben rechts lassen sich Dimension und Firma wechseln.
Über dem Diagramm steht ein **Zeitfilter** mit „Gesamt“, „5 Jahre“, „3 Jahre“ und
„12 Monate“. Er wählt den sichtbaren Ausschnitt, gezählt vom letzten bewerteten Monat
zurück; die Y-Achse passt sich dem Ausschnitt an. Der Untertitel nennt den Zeitraum und
wie viele der auffälligen Veränderungen darin liegen („2 von 9 … im Zeitraum“). Die Liste
zeigt nur die Veränderungen im Zeitraum und nennt darunter, wie viele außerhalb liegen,
mit dem Link „Gesamten Zeitraum zeigen“. Der Zeitfilter ändert **nicht** die Erkennung.
„Zurück“ führt mit derselben Firma zum Dashboard. Weil Firma, Dimension und Zeitraum in
der Adresse stehen (`&range=5y|3y|1y`), lässt sich die Seite neu laden, als Lesezeichen
speichern oder weitergeben. Die Karte im Dashboard zeigt immer die ganze Reihe.

Nutzen: Statt einen langen Verlauf selbst nach Brüchen abzusuchen, sieht man sofort,
*wann* sich die Stimmung der Mitarbeitenden spürbar verschoben hat und *wie stark*.
Diese Zeitpunkte sind der Ausgangspunkt für die spätere Kontextsuche (Nachrichten, Kurse),
die in einem folgenden Inkrement entsteht.

## 2. Erklärung

### 2.1 Von den Bewertungen zur Monatsreihe

1. Alle Bewertungen eines Unternehmens aus der gewählten Quelle (im Dashboard fest
   `employee`, also Mitarbeitende; die Quellenauswahl folgt in Inkrement 2) werden gelesen.
   Die Datenbank wird nur gelesen.
2. Je Kalendermonat wird der Mittelwert der Spalte `durchschnittsbewertung` gebildet.
   Das ist die Gesamtnote, die Kununu je Bewertung anzeigt (Entscheidung **E3**). Für eine
   Einzelkategorie wird analog die jeweilige `sternebewertung_*`-Spalte gemittelt.
3. Ein Monat gilt als **bewertet**, wenn mindestens **5 Bewertungen** mit Wert in der
   gewählten Spalte vorliegen (`n_values`). Bei der Gesamtbewertung ist das praktisch die
   Zahl der Bewertungen; bei Einzeldimensionen kann sie kleiner sein, weil nicht jede
   Bewertung jede Kategorie bewertet (Beispiel Open Grid Europe, 2018-08, „Umgang mit
   älteren Kollegen“: 5 Bewertungen, davon 3 mit Wert, also nicht bewertet). Monate mit
   weniger Werten bleiben Lücken und gehen nicht in die Erkennung ein (**E4**). Die API
   liefert je Monat `count` und `n_values`, damit die Anzeige den Grund richtig nennt.
4. Eine Reihe ist **geeignet**, wenn sie mindestens **12 bewertete Monate** hat (**E4**).
   Für nicht geeignete Reihen wird nichts erkannt; die Antwort nennt den Grund und die
   Zahl der bewerteten Monate.

Umsetzung: `backend/services/rating_series_service.py`. Das ist die einzige Stelle, an der
diese Reihe gebildet wird. Auch die Serien-CSVs für die Annotation nutzen sie.

### 2.2 Erkennung der Niveauwechsel

**Niveauwechsel (Change Point):** Ein Zeitpunkt, ab dem eine Reihe dauerhaft um ein
anderes Mittel schwankt als vorher. Gesucht sind also keine einzelnen Ausreißermonate,
sondern Verschiebungen, die über mehrere Monate anhalten. Der Begriff stammt aus der
Statistik der Strukturbruch- bzw. Change-Point-Analyse. Für die Arbeit ist er zentral, weil
die Interviewfrage (DZ3) lautet, ob solche Verschiebungen für Personalverantwortliche
nachvollziehbar und nützlich sind.

Verfahren: **PELT** („Pruned Exact Linear Time“, Killick, Fearnhead & Eckley 2012) in der
Python-Bibliothek `ruptures` (Truong, Oudre & Vayatis 2020). PELT zerlegt die Reihe so in
Abschnitte, dass die Werte innerhalb jedes Abschnitts möglichst nah an dessen Mittel
liegen. Jeder zusätzliche Abschnitt kostet einen Strafterm. Ein Wechsel wird also nur
gesetzt, wenn er die Reihe deutlich besser erklärt, als er „kostet“.

| Parameter | Startwert | Bedeutung |
|---|---|---|
| `model` | `"l2"` | Kostenfunktion: quadrierte Abweichung vom Abschnittsmittel. Reagiert auf Verschiebungen des Mittelwerts |
| `min_size` | 3 | Ein Abschnitt umfasst mindestens 3 bewertete Monate. Ein einzelner Ausreißermonat ist damit kein neues Niveau |
| Strafterm | `penalty_factor` 2,0 (skaliert) | Strafterm je zusätzlichem Wechsel, je Reihe berechnet: `penalty = penalty_factor · σ² · ln(n)` (Einheit: quadrierte Sterne). `σ` ist die robuste Streuung der bewerteten Monatsmittel (`noise_sigma`), `n` die Zahl der bewerteten Monate. Größer heißt weniger, aber robustere Wechsel. Bis 2026-10-04 galt der feste Wert `penalty` 0,5, er ist weiter als fester Modus wählbar (E9) |
| `min_delta` | 0,3 Sterne | Erkannte Wechsel mit kleinerem Betrag werden nicht angezeigt |

Die Erkennung läuft **nur auf den bewerteten Monaten**; Lücken werden übersprungen, nicht
aufgefüllt. Der gemeldete Monat ist der **erste bewertete Monat auf dem neuen Niveau**.

Für Reihen, die für PELT zu kurz sind (weniger als `2 × min_size` Werte), gibt es einen
Fallback. Er vergleicht die Mittel zweier benachbarter Fenster von je 3 Monaten; ab einer
Differenz von 0,3 Sternen gilt das als Wechsel. Im Dashboard greift er praktisch nie, weil
geeignete Reihen mindestens 12 Monate haben. Er sichert das Modul für andere Aufrufer ab.

Umsetzung: `backend/models/changepoint_detector.py`. Das Modul enthält reine Funktionen ohne
Datenbankzugriff. Eine kleine Schnittstelle (`ChangePointDetector`) erlaubt es, später ein
zweites Verfahren einzuhängen (geplant: Günnemann et al. 2014).

### 2.3 Wann wird eine Anomalie gekennzeichnet?

**Was eine Anomalie hier ausmacht:** Eine Anomalie ist in diesem Dashboard eine
**anhaltende Verschiebung des Bewertungsniveaus**. Ab einem bestimmten Monat liegen die
Monatsmittel über mehrere Monate spürbar höher oder tiefer als in den Monaten davor. Ein
einzelner schlechter Monat ist keine Anomalie, ebenso wenig ein kleines Auf und Ab.
Entscheidend ist, dass das neue Niveau hält und der Unterschied groß genug ist.

Ein Monat wird nur markiert, wenn **alle vier Bedingungen** erfüllt sind:

| Nr. | Bedingung | Prüfwert (Start, vorläufig) | Wozu |
|---|---|---|---|
| 1 | Die Reihe ist **geeignet**. | mind. 12 bewertete Monate mit je mind. 5 Bewertungen (E4) | Ohne genug Monate gibt es kein verlässliches „davor“ und „danach“. |
| 2 | **Beide Abschnitte** um den Wechsel sind lang genug. | mind. 3 bewertete Monate davor und danach (`min_size`) | Das neue Niveau muss halten; ein Ausreißermonat reicht nicht. |
| 3 | Der Wechsel **erklärt die Reihe deutlich besser**, als er kostet. | Gewinn > Strafterm `2 · σ² · ln(n)` der Reihe, siehe unten | Zufällige Schwankungen sollen keine Wechsel erzeugen; je stärker eine Reihe schwankt, desto mehr muss ein Wechsel erklären. |
| 4 | Der Unterschied ist **groß genug**. | \|Delta\| ≥ 0,3 Sterne (`min_delta`) | Statistisch erkennbare, aber praktisch belanglose Verschiebungen fallen weg. |

**Bedingung 3 in Zahlen:** Teilt man einen Abschnitt in zwei Teile mit *n₁* und *n₂*
Monaten und den Mitteln *m₁* und *m₂*, sinkt die Summe der quadrierten Abweichungen um

> Gewinn = n₁ · n₂ / (n₁ + n₂) · (m₂ − m₁)²

PELT setzt den Wechsel nur, wenn dieser Gewinn den Strafterm der Reihe übersteigt. Daraus
folgen zwei Faustregeln: **Je kürzer die Abschnitte, desto größer muss der Sprung sein**, und
**je stärker eine Reihe schwankt, desto größer muss der Sprung sein.** Nötiger Sprung allein
durch den Strafterm, für drei reale Reihen (Faktor 2) und den früheren festen Wert:

| Monate davor / danach | fest 0,5 (bis 2026-10-04) | Telekom (σ 0,28, n 165, Strafterm 0,82) | E.ON (σ 0,42, n 38, 1,27) | Cancom (σ 0,50, n 115, 2,39) |
|---|---|---|---|---|
| 3 / 3 | 0,58 | 0,74 | 0,92 | 1,26 |
| 3 / 12 | 0,46 | 0,58 | 0,73 | 1,00 |
| 6 / 6 | 0,41 | 0,52 | 0,65 | 0,89 |
| 12 / 12 | 0,29 | 0,37 | 0,46 | 0,63 |
| 24 / 24 | 0,20 | 0,26 | 0,32 | 0,45 |

Angezeigt wird zusätzlich nur, was `min_delta` 0,3 erreicht. Bei ruhigen Reihen entscheidet
daher bei langen Abschnitten der Mindestbetrag, bei verrauschten Reihen fast immer der
Strafterm. Die Faustregel gilt für einen einzelnen Wechsel; bei mehreren Wechseln wägt
PELT alle Zerlegungen gemeinsam ab.

**Einordnung nach Richtung und Stärke:**

- **Richtung:** Abfall (`fall`), wenn das Niveau danach niedriger ist, sonst Anstieg (`rise`).
- **Stärke:** „deutlich“ (`high`) ab 0,5 Sternen, sonst „mäßig“ (`medium`). 0,5 Sterne ist
  der Richtwert des Annotationsprotokolls (E5); festgehalten in E9, Status vorläufig.
  „Deutlich“ markierte Stufen haben im Diagramm einen kräftigen Strich (2,25 px statt 1,25 px).

**Beispiel (gehostete Demo 3, synthetisch, ruhige Reihe: σ 0,11, n 50, Strafterm 0,10):**

| Monat | davor / danach (bewertete Monate) | Delta | Gewinn | Ergebnis |
|---|---|---|---|---|
| 2023-01 | 12 / 12 | −1,38 | 11,3 | Abfall, deutlich |
| 2024-01 | 12 / 11 | +1,19 | 8,1 | Anstieg, deutlich |
| 2025-01 | 11 / 15 | +0,36 | 0,8 | Anstieg, mäßig (knapp über `min_delta`; Gewinn deutlich über dem Strafterm) |

**Was nicht markiert wird:**

- ein einzelner Ausreißermonat oder ein Ausreißer über zwei Monate **als eigener Abschnitt**
  (Bedingung 2). Ein kurzer, starker Einbruch kann aber trotzdem markiert werden: PELT füllt
  ihn dann mit einem unauffälligen Nachbarmonat auf die Mindestlänge von 3 Monaten auf.
  Beispiel Telekom: 2022-10 (3,98), 2022-11 (3,63), 2022-12 (2,60). Markiert wird 2022-10,
  obwohl dieser Monat noch nahe am alten Niveau 4,07 liegt; der Abschnitt Okt.–Dez. 2022
  hat das Mittel 3,40. Die API kennzeichnet solche Fälle (`month_near_previous_level`), und
  der Tooltip weist darauf hin,
- Monate mit weniger als 5 Bewertungen; sie gehen gar nicht in die Erkennung ein (Bedingung 1),
- Verschiebungen unter 0,3 Sternen (Bedingung 4),
- ein Bruch in den letzten 1–2 bewerteten Monaten, weil das neue Niveau noch keine 3 Monate hat (Bedingung 2),
- langsame, gleichmäßige Trends: Das Verfahren sucht Stufen. Ein schleichender Trend wird
  entweder gar nicht oder als eine bzw. mehrere Stufen erkannt, sobald sich genug Abstand
  aufgebaut hat.

**Was eine Markierung nicht bedeutet:** Sie sagt, *dass* und *wann* sich das Niveau
verschoben hat, nicht *warum*. Die Einordnung, etwa über Nachrichten aus dem Zeitraum,
ist ein eigener, späterer Schritt und bleibt eine Plausibilisierung.

### 2.4 Kennzahlen je Veränderung

| Feld | Bedeutung |
|---|---|
| `date` | erster bewerteter Monat auf dem neuen Niveau |
| `direction` | `fall` (Abfall) oder `rise` (Anstieg) |
| `before_mean` / `after_mean` | Mittel der Monatsmittel im Abschnitt vor bzw. nach dem Wechsel, jeweils bis zum benachbarten Wechsel |
| `delta` | `after_mean − before_mean` in Sternen |
| `n_reviews_before` / `n_reviews_after` | Zahl der Bewertungen mit Wert in der gewählten Dimension im Abschnitt vor bzw. nach dem Wechsel (bei der Gesamtbewertung gleich der Zahl der Bewertungen); im Dashboard „Bewertungen davor / danach“ |
| `n_reviews` | Summe aus beiden |
| `severity` | `high` („deutlich“) ab 0,5 Sternen, sonst `medium` („mäßig“) (E9) |
| `before_from` / `after_to` | erster bzw. letzter bewerteter Monat der beiden Abschnitte; Grundlage für die Zeiträume im Tooltip und die Niveaulinie |
| `previous_period` / `gap_months` | letzter bewerteter Monat vor `date` und Zahl der nicht bewerteten Monate dazwischen |
| `month_mean` / `month_near_previous_level` | Monatsmittel des markierten Monats und ob es näher am alten als am neuen Niveau liegt (Hinweis im Tooltip) |
| `method`, `params` | verwendetes Verfahren und seine Parameter, damit jedes Ergebnis nachvollziehbar bleibt |

Umsetzung: `backend/services/anomaly_service.py`. Die API dazu ist
`GET /api/analytics/company/{id}/anomalies` (`backend/routes/anomalies.py`). Sie rechnet
bei jedem Aufruf live und legt nichts in der Datenbank ab. Mit `dimension=all` liefert sie
für jede Dimension der Quelle Eignung und Anomalien sowie eine gemeinsame, sortierte Liste
(ohne Monatsreihen); die Form steht im Docstring der Route und unter `/docs`.

### 2.5 Darstellung im Frontend

| Teil | Datei | Aufgabe |
|---|---|---|
| Datenabruf | `frontend/src/hooks/useAnomalies.js` | ruft den Endpoint ab; Lade- und Fehlerzustand; bricht veraltete Anfragen beim Firmenwechsel ab |
| Diagramm, Liste, Auswahl | `frontend/src/components/dashboard/AnomalyCard.jsx` (`AnomalyChart`, `AnomalyList`, `DimensionPicker`, `TimeRangeFilter`, `StepGlyph`) | Verlauf mit gestrichelt überbrückten Lücken, Stufen-Markierungen (`ReferenceLine` mit `segment` und eigener `shape`), Niveaulinie (`showLevels`), Kartenvariante (`compact`: Ringe auf dem Monatswert wie in der ersten Version, ohne Niveaulinie und Markierungslegende), Legende und Tooltip, optionaler Ausschnitt (`range`), Liste oder Eignungshinweis (Liste nur auf der Detailseite), Dimensionsauswahl, Zeitfilter; von Karte und Detailseite gemeinsam genutzt |
| Darstellungshilfen | `frontend/src/lib/anomalySeries.js` | reine Funktionen: Anzeigebereich vom ersten bis zum letzten bewerteten Monat (`trimToEvaluated`), Zeitfenster relativ zum letzten angezeigten Monat (`timeWindow`, `inWindow`), lineare Interpolation über Lücken nur zur Anzeige (`interpolateGaps`), Monatsformat |
| Dimensionsnamen | `frontend/src/lib/ratingCategories.js` | einzige Zuordnung Schlüssel → Anzeigename; vorher lokal in `ReviewDetailModal.jsx`, dorthin unverändert verschoben |
| Karte | `AnomalyCard` in derselben Datei, eingebunden in `frontend/src/pages/Dashboard.jsx` | kompakte Ansicht unter der Diagrammzeile; Klick öffnet die Detailseite |
| Icon | `Anomaly` in `frontend/src/icons.jsx` | kleines Liniendiagramm mit Niveausprung, der Ring markiert den ersten Monat auf dem neuen Niveau; im Stil der übrigen App-Icons (nur Konturen, Strichstärke 1,8), genutzt in Kartenkopf, Detailseite und Seitenleiste. Ersetzt das Lucide-Icon `Activity`, das mit fester Größe von 24 px aus dem 14-px-Feld des Kartenkopfs ragte |
| Detailseite | `frontend/src/pages/Anomalies.jsx`, Route `/anomalies` in `frontend/src/App.jsx` | großes Diagramm, Liste, Firmenwechsel, Zurück zum Dashboard mit derselben Firma |
| Navigation | Eintrag „Anomalien“ in der linken Leiste von `Dashboard.jsx` | zweiter Weg zur Detailseite; deaktiviert, solange keine Firma gewählt ist |

Die Farben kommen aus den Theme-Variablen der App (`--rose-500`, `--emerald-500`,
`--color-grid`, `--color-axis`). Die Karte funktioniert deshalb im hellen und im dunklen Theme.
Die Detailseite wendet das gespeicherte Theme auch an, wenn sie direkt über die URL
geöffnet wird. Die Karte gehört nicht zum PDF-Export; der Export nutzt nur die
Diagramm-IDs von Timeline und Topics.

## 3. Begründung

**Warum Niveauwechsel statt Ausreißer?** Einzelne Monate mit 5–15 Bewertungen schwanken
stark. Ein Ausreißermonat ist meist Zufall. Für Personalverantwortliche zählt, ob sich
die Wahrnehmung *anhaltend* verschoben hat. Deshalb sucht das Verfahren Abschnitte mit
anderem Mittel und verlangt mindestens 3 Monate je Abschnitt.

**Warum PELT?** PELT findet die beste Zerlegung exakt, nicht nur näherungsweise, und
rechnet dabei in linearer Zeit. Die Zahl der Wechsel muss nicht vorab bekannt sein, sie
ergibt sich aus dem Strafterm. Das Verfahren ist etabliert und in einer gepflegten
Bibliothek verfügbar. Damit ist es eine nachvollziehbare Basis, gegen die ein zweites
Verfahren verglichen werden kann.

**Warum nur bewertete Monate?** Ein Mittel aus ein oder zwei Bewertungen ist Rauschen. Es
würde Scheinwechsel erzeugen (E4). Lücken für die Erkennung aufzufüllen, etwa durch
Interpolation, hieße, Daten zu erfinden. Die gestrichelte Überbrückung im Diagramm ist
deshalb reine Darstellung: Sie geht nicht in die Erkennung ein, ist als „interpoliert“
beschriftet, und der Tooltip zeigt dort keinen Zahlenwert.

**Warum die Gesamtnote aus `durchschnittsbewertung`?** Das ist dieselbe Reihe, die die
Timeline-Karte zeigt. Nutzerinnen und Nutzer sehen also keinen zweiten, abweichenden
Verlauf (E3).

**Warum diese Startwerte?** Sie sind Setzungen des Autors (E9). Sie passen zu den
Größenordnungen aus der Literaturnotiz (`docs/referenzzeitraeume-literatur.md`), unter
anderem zur Standardabweichung der Quartalsänderung von etwa 0,45 Sternen bei Green et al.
(2019) und zum Richtwert von 0,5 Sternen im Annotationsprotokoll. Die Parameterübersicht
(`backend/scripts/explore_anomaly_params.py`) zeigt, wie stark die Zahl der Markierungen von
ihnen abhängt (Abschnitt 5). Gegen Referenzzeiträume (DZ1) sind sie noch nicht gemessen.

**Warum ein skalierter Strafterm?** Der feste Wert 0,5 behandelte eine ruhige Reihe mit 30
Monaten wie eine stark schwankende mit 160 Monaten. Verrauschte Reihen wurden dadurch
übersegmentiert: 66 Markierungen bei 15 Unternehmen, davon 16 bei Cancom, und auf
synthetischen Rauschreihen ohne jeden Sprung meldete der feste Wert fast immer eine
Veränderung. Der skalierte Strafterm `2 · σ² · ln(n)` misst die Kosten eines Wechsels in
Einheiten der Streuung der jeweiligen Reihe: Ein Wechsel muss sich gegen das übliche
Auf und Ab dieser Reihe abheben. Die Streuung wird aus den Monat-zu-Monat-Differenzen
geschätzt und ist dadurch unempfindlich gegen die Niveauwechsel, die gesucht werden. Mit
Faktor 2 bleiben 19 Markierungen (15 deutlich). Faktor 2 entspricht der Form des
BIC-Strafterms; Beleg offen (Autor), vgl. Truong et al. 2020 zu prüfen. Der Faktor ist eine
Setzung des Autors und vorläufig (E9).

**Warum dezente Markierungen und das Wort „auffällig“?** Die Arbeit liefert eine
Plausibilisierung, keine Kausalaussage. Eine auffällige Markierung soll zum Nachsehen
einladen, nicht als Alarm oder als Ursache gelesen werden.

**Warum auf der Karte wieder Ringe?** Am 2026-10-03 wurden für die Karte nacheinander
eine kompakte Niveaudarstellung (Niveautreppe als Hauptlinie, Monatswerte blass) und
Punkte auf dem neuen Niveau ausprobiert. Der Autor hat sich danach für die Darstellung der
ersten Version entschieden: Die Karte ist der schnelle Überblick und soll den gewohnten
Monatsverlauf zeigen. Die Schwächen der Ringe aus der Prüfung (Ring auf dem verrauschten
Monatswert, Richtung nur über Farbe, Ausmaß kaum sichtbar) gelten auf der Karte deshalb
weiter; die Detailseite gleicht sie mit Stufen, Niveaulinie, Legende und Tooltip aus, und
ein Klick auf die Karte führt dorthin.

**Warum eine Stufe statt eines Punkts?** Bis 2026-10-03 markierte ein Ring das
Monatsmittel des markierten Monats. Eine Prüfung mit drei Prüfern, drei unabhängigen
Gestaltungsentwürfen und zwei Juroren ergab: Bei verrauschten Reihen saßen die Ringe auf
Spitzen und Tälern der Linie, das erkannte Niveau war unsichtbar, die Richtung war nur
über die Farbe kodiert und das Ausmaß nur über 1 px Radiusunterschied. Bei Telekom 2022-10
saß ein Abfall-Ring auf einem Monat, der noch auf dem alten Niveau lag. Die Stufe zeigt
dagegen genau, was die Erkennung gefunden hat (Ø davor → Ø danach), mit der Höhe als
Ausmaß, der Form als Richtung und der Strichstärke als Schweregrad. Die Niveaulinie auf
der Detailseite macht die Abschnitte sichtbar, auf denen die Mittel beruhen. Der
Monatswert selbst bleibt auf der blauen Linie.

**Warum eine eigene Detailseite?** Auf dem Dashboard teilt sich die Karte den Platz mit
anderen Kennzahlen. Für das Lesen eines langen Verlaufs über Jahre ist ein breites
Diagramm nötig. Die Seite folgt dem Muster des Firmenvergleichs (eigene Route, Leiste mit
Zurück-Button), damit man die Bedienung nicht neu lernen muss. Die Firma steht in
der Adresse, damit eine Ansicht in einem Interview (DZ3) gezielt geöffnet oder
weitergegeben werden kann.

**Warum Lücken gestrichelt überbrücken?** Ein durchgehender Verlauf über dünn belegte
Monate würde Stabilität vortäuschen, wo keine Aussage möglich ist. Eine nur unterbrochene
Linie zerfällt bei dünnen Reihen (z. B. Open Grid Europe) aber in viele kleine Stücke und
einzelne Punkte und wird unübersichtlich. Die gestrichelte, graue Verbindung hält das
Diagramm lesbar und zeigt trotzdem klar, wo keine bewerteten Monate liegen. Sie folgt der
Darstellung der Timeline-Karte („Gestrichelte Linie = interpolierte Werte“), damit die
Zeichen im Dashboard einheitlich sind. Aufeinanderfolgende Lücken liegen auf zwei
getrennten Datenreihen, damit die gestrichelte Linie nie über ein durchgezogenes Stück
gezeichnet wird.

**Warum ein Zeitfilter, und warum nur als Ausschnitt?** Lange Reihen (Telekom, Bechtle,
Carl Zeiss: mehr als 200 Monate) sind in voller Länge kaum zu lesen. Der Zeitfilter
vergrößert einen Ausschnitt. Die Erkennung läuft trotzdem immer auf der ganzen Reihe:
Würde sie nur den Ausschnitt auswerten, hinge eine auffällige Veränderung vom gewählten
Zoom ab, und ein 12-Monats-Fenster wäre nach E4 gar nicht geeignet. Bezugspunkt ist der
letzte bewertete Monat und nicht das heutige Datum, weil viele Reihen 2025 enden und ein
Fenster ab heute leer wäre.

**Warum leere Ränder ausblenden?** Viele Reihen beginnen mit einzelnen Bewertungen, lange
bevor ein Monat 5 Bewertungen erreicht (Open Grid Europe: 47 Monate, E.ON: 14 Monate).
Dort gibt es weder einen bewerteten Monat noch etwas zu überbrücken, das Diagramm zeigte
nur leere Fläche und stauchte den eigentlichen Verlauf. Die ausgeblendeten Monate werden
unter dem Diagramm mit Zeitraum und Anzahl genannt, damit klar bleibt, dass die Reihe
früher beginnt. Für die Erkennung ändert sich nichts, sie nutzt ohnehin nur bewertete
Monate. Damit ist die frühere Vorgabe „alle Monate zwischen erstem und letztem Monat der
Reihe zeigen“ (Abschluss Schritt A) durch die Entscheidung des Autors vom 2026-10-03
ersetzt. Die Liste nennt, wie viele Veränderungen außerhalb des
Ausschnitts liegen, damit nichts unbemerkt ausgeblendet wird.

**Warum die Dimensionsauswahl?** Eine Verschiebung der Gesamtnote sagt nicht, *in welchem
Bereich* sich etwas verändert hat. Die Einzelkategorien (z. B. Kommunikation,
Vorgesetztenverhalten) machen sichtbar, ob eine Veränderung breit oder auf ein Thema
begrenzt ist. Das bleibt eine Beschreibung und keine Ursachenaussage.

**Warum Abfälle zuerst?** Für Personalverantwortliche sind Verschlechterungen meist der
dringendere Anlass zum Handeln.

## 4. Grenzen

- Nur geeignete Reihen werden ausgewertet. Laut `docs/datenbasis.md` erfüllen das 15 von
  26 Unternehmen bei den Mitarbeitenden und 5 von 26 bei den Bewerbenden.
- Ein erkannter Wechsel sagt nichts über seine **Ursache**. Er kann auch durch eine
  Kampagne für Bewertungen, eine geänderte Belegschaft oder Zufall entstehen.
- Wegen `min_size` braucht jeder Abschnitt 3 bewertete Monate. Ein Wechsel liegt deshalb
  frühestens im 4. bewerteten Monat, und ein Bruch in den letzten 1–2 bewerteten Monaten
  ist noch nicht erkennbar. Das ist für aktuelle Entwicklungen wichtig.
- Liegt eine Lücke direkt vor dem markierten Monat, wird der erste *bewertete* Monat danach
  gemeldet; der tatsächliche Übergang kann irgendwo in der Lücke liegen. Die API liefert
  dafür `previous_period` und `gap_months`, Tooltip und Liste nennen die Lücke (z. B.
  Telekom 2009-12: 13 nicht bewertete Monate seit Okt. 2008).
- Die Mindestlänge von 3 Monaten dämpft Ausreißer, schließt sie aber nicht aus: Ein kurzer,
  starker Einbruch kann als 3-Monats-Abschnitt erscheinen, dessen erster Monat noch auf dem
  alten Niveau liegt (siehe 2.3, Telekom 2022-10). Die Prüfung zählte 6 solcher Fälle in 7
  dichten Reihen. Ob `min_size` angepasst werden soll, ist eine offene Frage für E9.
- Die Abschnitte einer Veränderung reichen bis zum benachbarten *erkannten* Wechsel, auch
  wenn dieser wegen `min_delta` nicht angezeigt wird. In den aktuellen Daten betrifft das
  nur Carl Zeiss 2021-05 (+0,25), ohne Nachbarn; die Niveaulinie bleibt dort leer.
- Die Parameter sind noch nicht gegen unabhängige Referenzzeiträume geprüft.
- Der skalierte Strafterm (seit 2026-10-04) wächst mit der Streuung und der Länge der Reihe.
  Bei sehr verrauschten Reihen braucht ein Wechsel deshalb einen großen Sprung (Cancom bei
  12/12 Monaten 0,63 Sterne); echte, aber kleinere Veränderungen können dort unerkannt
  bleiben. Mit dem neuen Standard hat Cancom keine Markierung mehr.
- `σ` wird aus derselben Reihe geschätzt, in der gesucht wird. Bei kurzen Reihen ist die
  Schätzung unsicher; die Untergrenze von 0,05 Sternen verhindert nur, dass der Strafterm
  bei fast konstanten Reihen gegen null geht.
- Mehrere Beispiele in diesem Dokument (u. a. Telekom 2022-10, Cancom mit 16 Veränderungen)
  stammen aus der Zeit des festen Strafterms 0,5. Telekom 2022-10 wird mit dem neuen
  Standard nicht mehr markiert; mit `penalty=0.5` (fester Modus) lassen sich die damaligen
  Ergebnisse reproduzieren.
- Die gestrichelte Überbrückung verbindet auch lange Lücken (Open Grid Europe: 20 nicht
  bewertete Monate zwischen 2019-07 und 2021-04, 18 zwischen 2017-01 und 2018-08). Sie ist
  dort nur eine Verbindungslinie und kein Verlauf; über die Entwicklung in dieser Zeit sagt
  sie nichts.
- Der Zeitfilter zählt vom letzten bewerteten Monat der jeweiligen Reihe zurück. Zwei Unternehmen mit
  „12 Monate“ können daher unterschiedliche Kalenderzeiträume zeigen; der Untertitel nennt
  den Zeitraum.

## 5. Prüfung und Belege

| Was | Beleg |
|---|---|
| Detektor | `backend/tests/anomaly/test_changepoint_detector.py`: Abfall, Anstieg, V-Form, konstant, nur Rauschen (10 Zufallsreihen), Parameter, zu kurze Reihe, Fallback, Lücken, Schnittstelle |
| Synthetisches Beispiel (In-Memory-Demo 3) | `fall` 2023-01 (−0,46), `rise` 2023-12 (+0,41); Demo 1 und Demo 2 ohne Anomalie |
| Gehostete Demo 3 (id 18) | `fall` 2023-01 (−1,38), `rise` 2024-01 (+1,19), `rise` 2025-01 (+0,36) |
| Dashboard | geprüft im hellen und dunklen Theme, Tooltip und Liste, keine Konsolenfehler; PDF-Export-Pfad unverändert |
| Detailseite | Klick auf Karte → `/anomalies?company=18`; Neuladen über die URL lädt den Firmennamen nach; gespeichertes Theme wird angewendet; „Zurück“ zeigt das Dashboard mit derselben Firma |
| Service und Route | `backend/tests/anomaly/test_anomaly_service.py`, `test_anomalies_route.py` (In-Memory-Store, ohne Netzwerk): Demo 3 `fall` ±1 Monat um 2023-01 und `rise` um 2023-12, Demo 1/2 ohne Veränderung, nicht geeignete Reihen, `n_reviews`-Aufteilung, `dimension=all`, 400/422 |
| Lücken, Eignung, Dimension | geprüft an Open Grid Europe (viele Lücken), PLEdoc (nicht geeignet), Demo 3 mit „Kommunikation“ und „Vorgesetztenverhalten“; helles und dunkles Theme |
| Review Zeitfilter/Interpolation | Vier unabhängige Prüfer (Interpolation, Zeitfilter, Recharts, UI) und zwei Gegenprüfer, 2026-10-03. `interpolateGaps` wurde erschöpfend über alle 32 767 Muster aus bewerteten Monaten und Lücken bis Länge 14 geprüft, auch mit allen Fensterausschnitten: nie eine gestrichelte Strecke über einer durchgezogenen, Randlücken leer, kein interpolierter Wert als Datenwert. Bestätigt und behoben: Begründung im Tooltip bei Einzeldimensionen (`n_values`), Dativ im Untertitel, Leerhinweis ohne Zeitfilter, Y-Achsenbeschriftung bei Viertelstrichen. 4 Meldungen widerlegt |
| Review Kennzeichnung | Drei Prüfer (Daten, Darstellung, Anforderungen), drei unabhängige Markierungsentwürfe (Niveaustufen, Niveaupfeil, Stufen-Marker), zwei Juroren, ein Gegenprüfer, 2026-10-03; 25 Befunde, keiner widerlegt. Umgesetzt: Stufe statt Ring, Niveaulinie auf der Detailseite, Legende, Schweregrad über Strichstärke, Theme-Tokens `--anomaly-fall` / `--anomaly-rise` (hell 700er-, dunkel 400er-Töne), Tooltip mit Abschnittszeiträumen, Lücken- und Nahe-am-alten-Niveau-Hinweis, Liste mit „ab Monat“ und Lückenhinweis. Geprüft im Browser: Telekom 3 Jahre (2022-10), Cancom (16 Veränderungen), E.ON, hell und dunkel |
| Review Anzeigebereich/Icon | Zwei Prüfer (Logik, UI) und ein Gegenprüfer, 2026-10-03. Bestätigt und behoben: Im Zeitausschnitt fehlte der Hinweis auf ausgeblendete jüngere Monate (Universität Duisburg-Essen: 17 Monate mit 30 Bewertungen nach dem letzten bewerteten Monat). Widerlegt bzw. als Gestaltungsfrage eingestuft: Lesbarkeit des Rings im Icon bei 14 px auf 1x-Bildschirmen, Kontrast der Hinweiszeile (entspricht der Konvention der übrigen Karten), Formulierung des Hinweises (trotzdem geglättet) |
| Interpolation und Zeitfilter | Hilfsfunktionen in `frontend/src/lib/anomalySeries.js` per Node-Prüfskript geprüft (Lücke in der Mitte, Ränder, benachbarte Lücken mit wechselnden Schlüsseln, einzelner Monat zwischen zwei Lücken, nicht bewerteter Monat mit Mittelwert, Fenster über den Jahreswechsel, Fenster größer als die Reihe). Im Browser: Open Grid Europe gesamt und 3 Jahre (Überbrückung am Fensterrand), Telekom 3 Jahre (2 von 9 im Zeitraum, Hinweis auf 7 außerhalb), Demo 3 12 Monate; helles und dunkles Theme |
| Parameterübersicht | `backend/data/calibration/anomaly_params_employee_durchschnittsbewertung.csv`, Stand 2026-10-03, Mitarbeitende, Gesamtbewertung, 15 geeignete Unternehmen. Summe Abfälle/Anstiege bei min_delta 0,3: penalty 0,25 → 56/60, **0,5 → 31/35 (Startwert)**, 1,0 → 16/19, 2,0 → 4/5. Bei penalty 0,5 und min_delta 0,2/0,3/0,5: 31/36, 31/35, 27/28 |
| Parameterübersicht skaliert | `backend/data/calibration/anomaly_params_scaled_employee_durchschnittsbewertung.csv`, Stand 2026-10-04, 15 geeignete Unternehmen. Gesamt (davon deutlich) bei `min_delta` 0,3: Faktor 1 → 44 (33), **Faktor 2 → 19 (15) (Standard)**, Faktor 3 → 13 (9), Faktor 4 → 10 (9); fest 0,5 → 66 (55). Synthetische Prüfung in `backend/tests/anomaly/test_changepoint_detector.py` (120 Monate, σ 0,5: ohne Sprung keine Veränderung, mit Sprung 1,0 genau dieser; höchstens 5 Fehlalarme in 50 Rauschreihen) |
| Commits Inkrement 1 | `ffeacde` (Detektor), `10b1d50` (Tests), `5042d89` (Service), `cb5101b` (API), `4f41aa0` (Karte), `8c3af1e` (Detailseite) |
| Commits Abschluss | `1faca39` (Lücken, Eignung, Datenbasis), `6c63607` (Bewertungen davor/danach), `ed9bc3c` (Dimensionsauswahl, `dimension=all`), `67e1377` (Service-/Routentests), `f7fedbb` (Parameterübersicht) |

## 6. Offene Punkte

- Detailseite im selben Browser-Tab (wie der Vergleich) oder in einem neuen Tab öffnen?
- Quellenauswahl (Bewerbende): umgesetzt in Inkrement 2 zusammen mit dem Statusfilter,
  siehe [02 – Drill-down und Vorher-Nachher-Vergleich](02-drilldown-und-vergleich.md) und E13.
- Referenzzeiträume: Die Einträge wurden am 2026-10-03 zurückgestellt; Ersatzregel und
  Einschränkung für DZ1 stehen in E5 (Annotation vor der Evaluation, ohne Einsicht in
  Erkennungsergebnisse).
- Messung gegen die Referenzzeiträume (DZ1) steht aus; bis dahin bleiben die Parameter
  vorläufig (E9). Dabei den Faktor des skalierten Strafterms (2) prüfen; Faktor 3 und 4
  liefern 13 bzw. 10 Markierungen.
- `min_size` (3): Kurze, starke Einbrüche werden mit einem unauffälligen Nachbarmonat auf
  3 Monate aufgefüllt (Telekom 2022-10). Mit `min_size=2` läge die Markierung dort auf
  2022-11. Ob das gewünscht ist, ist eine Entscheidung des Autors (E9).
- Trefferfläche des Tooltips: Bei langen Reihen ist eine Monatsspalte nur wenige Pixel
  breit; die Details einer Veränderung stehen immer auch in der Liste.
- Die Anforderungstexte FA-01 bis FA-04 und FA-26 liegen nicht im Repository.
