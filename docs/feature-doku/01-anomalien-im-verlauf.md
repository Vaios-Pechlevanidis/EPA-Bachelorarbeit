# 01 – Anomalien im Verlauf

| | |
|---|---|
| Inkrement | 1 (Zyklus 2) |
| Anforderungen | FA-01 bis FA-04, Zähler aus FA-26 |
| Entscheidungen | E3 (Erkennungsreihe), E4 (Mindestdichte), E5 (Referenzzeiträume), E9 (Verfahren und Parameter, folgt) |
| Status | Durchstich fertig (Quelle Mitarbeitende, Gesamtbewertung); Dimensionsauswahl und Hinweise folgen. Parameter **vorläufig** |
| Stand | 2026-10-03 |

## 1. Vorstellung

Im Dashboard steht unter der Diagrammzeile (Timeline, Topics im Detail) die Karte
**„Anomalien im Verlauf“**. Sie zeigt:

- den **Monatsverlauf** der Gesamtbewertung, also den Durchschnitt der Sterne je Kalendermonat,
- **dezente Punkte** an den Monaten, in denen sich das Bewertungsniveau auffällig
  verändert hat: rot für einen Abfall, grün für einen Anstieg, etwas größer bei
  deutlichen Veränderungen,
- einen **Tooltip** je Monat mit dem Monatsmittel und der Zahl der Bewertungen. Auf einem
  markierten Monat zeigt er zusätzlich Delta, Mittel davor und danach und die Zahl der zugrunde
  liegenden Bewertungen,
- eine **Liste** der Veränderungen unter dem Diagramm, Abfälle zuerst, innerhalb nach Größe,
- die **Anzahl** der auffälligen Veränderungen im Untertitel der Karte (Zähler aus FA-26).

Nutzen: Statt einen langen Verlauf selbst nach Brüchen abzusuchen, sieht man sofort,
*wann* sich die Stimmung der Mitarbeitenden spürbar verschoben hat und *wie stark*.
Diese Zeitpunkte sind der Ausgangspunkt für die spätere Kontextsuche (Nachrichten, Kurse),
die in einem folgenden Inkrement entsteht.

## 2. Erklärung

### 2.1 Von den Bewertungen zur Monatsreihe

1. Alle Bewertungen eines Unternehmens aus der gewählten Quelle (zunächst
   `employee`, also Mitarbeitende) werden gelesen. Die Datenbank wird nur gelesen.
2. Je Kalendermonat wird der Mittelwert der Spalte `durchschnittsbewertung` gebildet.
   Das ist die Gesamtnote, die Kununu je Bewertung anzeigt (Entscheidung **E3**).
3. Ein Monat gilt als **bewertet**, wenn mindestens **5 Bewertungen** vorliegen. Monate mit
   weniger Bewertungen bleiben Lücken und gehen nicht in die Erkennung ein (**E4**).
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
| `penalty` | 0,5 | Strafterm je zusätzlichem Wechsel (Einheit: quadrierte Sterne). Größer heißt weniger, aber robustere Wechsel |
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
| 3 | Der Wechsel **erklärt die Reihe deutlich besser**, als er kostet. | Gewinn > Strafterm 0,5 (`penalty`), siehe unten | Zufällige Schwankungen sollen keine Wechsel erzeugen. |
| 4 | Der Unterschied ist **groß genug**. | \|Delta\| ≥ 0,3 Sterne (`min_delta`) | Statistisch erkennbare, aber praktisch belanglose Verschiebungen fallen weg. |

**Bedingung 3 in Zahlen:** Teilt man einen Abschnitt in zwei Teile mit *n₁* und *n₂*
Monaten und den Mitteln *m₁* und *m₂*, sinkt die Summe der quadrierten Abweichungen um

> Gewinn = n₁ · n₂ / (n₁ + n₂) · (m₂ − m₁)²

PELT setzt den Wechsel nur, wenn dieser Gewinn den Strafterm 0,5 übersteigt. Daraus folgt
eine einfache Faustregel: **Je kürzer die Abschnitte, desto größer muss der Sprung sein.**

| Monate davor / danach | nötiger Sprung allein durch den Strafterm | wirksame Schwelle (mit `min_delta` 0,3) |
|---|---|---|
| 3 / 3 | 0,58 Sterne | 0,58 Sterne |
| 3 / 12 | 0,46 Sterne | 0,46 Sterne |
| 6 / 6 | 0,41 Sterne | 0,41 Sterne |
| 12 / 12 | 0,29 Sterne | 0,30 Sterne |
| 24 / 24 | 0,20 Sterne | 0,30 Sterne |

Bei kurzen Abschnitten entscheidet also der Strafterm, bei langen der Mindestbetrag
`min_delta`. Die Faustregel gilt für einen einzelnen Wechsel; bei mehreren Wechseln wägt
PELT alle Zerlegungen gemeinsam ab.

**Einordnung nach Richtung und Stärke:**

- **Richtung:** Abfall (`fall`), wenn das Niveau danach niedriger ist, sonst Anstieg (`rise`).
- **Stärke:** „deutlich“ (`high`) ab 0,5 Sternen, sonst „mäßig“ (`medium`). 0,5 Sterne ist
  der Richtwert des Annotationsprotokolls (E5); die Grenze ist noch zu bestätigen.
  „Deutlich“ markierte Punkte sind im Diagramm etwas größer.

**Beispiel (gehostete Demo 3, synthetisch):**

| Monat | davor / danach (bewertete Monate) | Delta | Gewinn | Ergebnis |
|---|---|---|---|---|
| 2023-01 | 12 / 12 | −1,38 | 11,3 | Abfall, deutlich |
| 2024-01 | 12 / 11 | +1,19 | 8,1 | Anstieg, deutlich |
| 2025-01 | 11 / 15 | +0,36 | 0,8 | Anstieg, mäßig (knapp über beiden Schwellen) |

**Was nicht markiert wird:**

- ein einzelner Ausreißermonat oder ein Ausreißer über zwei Monate (Bedingung 2),
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
| `n_reviews` | Zahl der Bewertungen in beiden verglichenen Abschnitten zusammen (Definition noch zu bestätigen) |
| `severity` | `high` ab 0,5 Sternen, sonst `medium` (Definition noch zu bestätigen) |
| `method`, `params` | verwendetes Verfahren und seine Parameter, damit jedes Ergebnis nachvollziehbar bleibt |

Umsetzung: `backend/services/anomaly_service.py`. Die API dazu ist
`GET /api/analytics/company/{id}/anomalies` (`backend/routes/anomalies.py`). Sie rechnet
bei jedem Aufruf live und legt nichts in der Datenbank ab.

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
würde Scheinwechsel erzeugen (E4). Lücken aufzufüllen, etwa durch Interpolation, hieße,
Daten zu erfinden.

**Warum die Gesamtnote aus `durchschnittsbewertung`?** Das ist dieselbe Reihe, die die
Timeline-Karte zeigt. Nutzerinnen und Nutzer sehen also keinen zweiten, abweichenden
Verlauf (E3).

**Warum diese Startwerte?** Sie sind Setzungen des Autors für den Start. Sie passen zu den
Größenordnungen aus der Literaturnotiz (`docs/referenzzeitraeume-literatur.md`), unter
anderem zur Standardabweichung der Quartalsänderung von etwa 0,45 Sternen bei Green et al.
(2019) und zum Richtwert von 0,5 Sternen im Annotationsprotokoll. Gemessen sind sie noch
nicht; das folgt über `backend/scripts/explore_anomaly_params.py` und später gegen die
Referenzzeiträume (DZ1).

**Warum dezente Markierungen und das Wort „auffällig“?** Die Arbeit liefert eine
Plausibilisierung, keine Kausalaussage. Ein auffälliger Punkt soll zum Nachsehen einladen,
nicht als Alarm oder als Ursache gelesen werden.

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
- Liegt eine Lücke direkt nach dem Wechsel, wird der erste *bewertete* Monat danach
  gemeldet. Der tatsächliche Wechsel kann früher liegen.
- Die Parameter sind noch nicht gegen unabhängige Referenzzeiträume geprüft.

## 5. Prüfung und Belege

| Was | Beleg |
|---|---|
| Detektor | `backend/tests/anomaly/test_changepoint_detector.py`: Abfall, Anstieg, V-Form, konstant, nur Rauschen (10 Zufallsreihen), Parameter, zu kurze Reihe, Fallback, Lücken, Schnittstelle |
| Synthetisches Beispiel (In-Memory-Demo 3) | `fall` 2023-01 (−0,46), `rise` 2023-12 (+0,41); Demo 1 und Demo 2 ohne Anomalie |
| Gehostete Demo 3 (id 18) | `fall` 2023-01 (−1,38), `rise` 2024-01 (+1,19), `rise` 2025-01 (+0,36) |
| Dashboard | geprüft im hellen und dunklen Theme, Tooltip und Liste, keine Konsolenfehler; PDF-Export-Pfad unverändert |
| Commits | `ffeacde` (Detektor), `10b1d50` (Tests), `5042d89` (Service), `cb5101b` (API), `4f41aa0` (Karte) |

## 6. Offene Punkte

- Definition von `n_reviews` und `severity` bestätigen.
- Verbreiterung (Schritt 6): Auswahl der Dimension, `dimension=all`, sichtbare Lücken,
  Hinweis zur Datenbasis, Hinweis bei nicht geeigneten Unternehmen.
- Service- und Routentests (Schritt 7), Parameterraster (Schritt 8), Eintrag E9 (Schritt 9).
- Reihenfolge laut E5: Der Erkennungscode liegt vor den Annotationen in der Git-Historie.
  Die Referenzzeiträume müssen deshalb ohne Blick auf die Erkennungsergebnisse entstehen;
  E9 soll das vermerken.
- Messung gegen die Referenzzeiträume (DZ1) steht aus; bis dahin bleiben die Parameter vorläufig.
