# 21 – Drill-down aus dem Vorher-Nachher-Vergleich in die Kategorie eines Themas

| | |
|---|---|
| Inkrement | Ergänzung der Detailseite „Anomalien im Verlauf“ (2026-10-23) |
| Anforderungen | keine eigene Anforderung aus der Prüfliste; Wunsch des Autors (2026-10-23): Ein Klick auf eine Kategorie im Vergleich soll den Drill-down zu dieser Kategorie und ihren Daten erweitern; zweite Rückmeldung am selben Tag: Die Kategorie muss dabei die Dimension der Seite werden, nicht nur ein Themenfilter („die Kommentare haben noch einen alten Filter“) |
| Entscheidungen | keine neue; nutzt die Dimension als globalen Filter (Doku 20, E34), die freie Auswahl (E17) und die Zuordnung Thema ↔ Dimension über die Sternespalte (E10) |
| Status | umgesetzt (2026-10-23), nicht committet; keine neuen Parameter |
| Stand | 2026-10-23 |

## 1. Vorstellung

Im Dialog **„Vorher-Nachher-Vergleich“** (Karte links unter der Drill-down-Leiste der Seite
`/anomalies`) steht die Tabelle **„Größte Verschiebungen je Thema“**: je Schlüsselwort-Thema
der Anteil der Bewertungen davor und danach, die Differenz in Prozentpunkten und die Stimmung
je Fenster. Bisher war die Tabelle nur zum Lesen da. Jetzt gilt:

- **Themenzeile anklicken.** Jedes Thema der Tabelle ist eine Kununu-Kategorie und damit eine
  Dimension der Seite (Kommunikation ↔ Sterne „Kommunikation“). Die Zeile (Themenname
  gepunktet unterstrichen, Zeiger beim Darüberfahren) schließt den Vergleich, **wechselt die
  Dimension im Kopf der Seite** auf diese Kategorie und behält den Zeitraum des Fensters **ab
  dem markierten Monat** (bei freier Auswahl: die Auswahl) als Auswahl. Dann öffnet sich die
  Karte **„Bewertungen der Auswahl“** im Dialog: nur Bewertungen, die zu dieser Kategorie
  gehören, mit ihren Sternen und dem Kommentar zur Kategorie (Doku 20). Monatsverlauf,
  Vergleich und externe Berichte stehen danach ebenfalls auf dieser Kategorie.
- **Anteil davor anklicken.** Die Prozentzahl in der Spalte „Anteil davor“ ist ein eigener
  Knopf und nimmt das Fenster **davor** als Auswahl.
- Steht die Seite schon auf der angeklickten Kategorie, bleibt die Auswahl, und die
  Bewertungsliste öffnet sich im gewählten Fenster.
- Themen ohne eigene Sternespalte (gibt es bei Kununu derzeit nicht) würden stattdessen den
  Themenfilter der Liste setzen (`?thema=`).
- Ein Hinweis unter der Tabelle nennt den Klickweg. Tastatur: Zeile mit Tab erreichbar,
  Eingabe oder Leertaste öffnet.

Der Zustand steht in der Adresse (`?dimension=kommunikation&from=2023-01&to=2023-06`), ist
also teilbar. Zurück zur vorigen Reihe führt das Auswahlfeld „Dimension“ im Kopf; die
markierte Veränderung gehört zur vorigen Dimension und ist dort wieder wählbar.

Nutzen: Wer in der Tabelle sieht, dass „Kommunikation“ von 7 % auf 26 % gestiegen ist,
wechselt mit einem Klick auf die Kategorie Kommunikation für genau diese Monate: die Seite
zeigt deren Sterneverlauf, die Bewertungen mit Sternen und Kommentar zu Kommunikation und die
Meldungen dazu. Die erste Fassung vom selben Tag setzte nur einen Themenfilter auf die Liste;
dann stand oben eine andere Dimension als im Filter, was der Autor als „alten Filter“
zurückwies.

## 2. Erklärung

**Zuordnung Thema → Dimension.** Jedes Schlüsselwort-Thema nennt in seiner Definition die
Sternespalte der Kategorie (`rating_fields`, E10); `dimension_for_topic` in
`services/keyword_topic_service.py` kehrt `topic_for_dimension` um (Image → `image`). Der
Vergleich (`GET …/anomalies/{id}/explanations` bzw. `…/compare`) liefert je Themenzeile
zusätzlich `dimension`. Bei Kununu hat jedes Thema beider Quellen genau eine Sternespalte
(Test in `tests/drilldown/test_topic_highlight.py`).

**Was der Klick setzt.** `pages/Anomalies.jsx`, `drillToTopic(thema, seite, dimension)`:
Das Fenster der Seite (`comparisonWindows` der Veränderung bzw. `periodWindows` der Auswahl,
E12/E17) wird zur freien Auswahl `?from=&to=`, die Dimension zur angeklickten, die markierte
Veränderung und ein Themenfilter werden aufgehoben; dann öffnet sich die Bewertungskarte
(`openCard`, `ExpandableCard` mit `open`/`onOpenChange`), der Vergleich schließt sich, weil
nur eine Karte zugleich geöffnet ist. Die Liste ist dann die der Dimension (Doku 20:
Kommentar zur Kategorie oder Schlüsselwort des Themas, `dimension_only`). Ist die Dimension
schon gewählt, wechselt nur das Fenster der Liste (`detail.onSide`).

**Zahlen.** „Anteil danach 26 %“ zählt die Bewertungen des Fensters, die das Thema nennen;
die Liste der Dimension zeigt zusätzlich die Bewertungen mit Kommentar zur Kategorie, also in
der Regel mehr (bei vollständigen Exporten alle). Die Zahl der Tabelle ist deshalb eine
Untergrenze dessen, was die Liste zeigt; die Fundstellen des Themas bleiben markiert.

**Parameter.** Keine. Fenster, Dimension und Auswahl sind die bestehenden.

## 3. Begründung

- **Daten statt Erzählung.** Der Autor hatte am 2026-10-22 eine erzählende Zusammenfassung
  der Veränderung abgelehnt; der Drill-down soll über Datenzeilen bis zur einzelnen Bewertung
  führen. Die Tabelle des Vergleichs ist dafür der natürliche Ausgangspunkt.
- **Kategorie = Dimension, ein Zustand.** Seit Doku 20 ist die Dimension der eine Zustand der
  Seite. Ein Themenfilter neben einer anderen Dimension erzeugt zwei Zustände nebeneinander
  (Rückmeldung des Autors). Der Klick auf eine Kategorie setzt deshalb die Dimension selbst;
  alles Weitere (Liste, Belege, Verlauf, Vergleich) folgt aus Doku 20.
- **Zeitraum bleibt.** Die markierte Veränderung gehört zur alten Reihe; ihr Fenster wird zur
  freien Auswahl (E17), damit man dieselben Monate in der neuen Kategorie sieht.
- **Ein Dialog zur Zeit.** Der Vergleich schließt sich beim Klick, statt dass sich ein zweiter
  Dialog darüberlegt; die Karte „Vorher-Nachher-Vergleich“ bleibt auf der Seite.
- **„Davor“ über die Zahl.** Eine Zeile hat nur ein Ziel; das Fenster davor erreicht man
  über die Prozentzahl davor, ohne die Zeile mit zwei Knöpfen zu überladen.

## 4. Grenzen

- Die Themen beruhen auf deutschen Schlüsselwörtern (E10): mehrdeutige Wörter zählen mit,
  englische Texte kaum.
- Bei „kleine Basis“ sind die Anteile unsicher.
- Die Liste der Dimension ist nicht die Menge hinter der Prozentzahl: Sie enthält auch
  Bewertungen mit Kommentar zur Kategorie ohne Schlüsselwort und wendet einen Statusfilter an,
  wenn gewählt. Wer genau die Nennungen lesen will, wählt im Dialog das Thema im Auswahlfeld.
- Nach dem Wechsel ist die markierte Veränderung nicht mehr ausgewählt (sie gehört zur
  vorigen Reihe); der Vergleich ist dann der der freien Auswahl mit dem gleich langen Zeitraum
  davor (E17), nicht der Vergleich der Veränderung (E12).
- Kein Klick auf die Stimmungsbalken: Die Stimmung ist eine Modellschätzung je Bewertung,
  keine Teilmenge, die sich auflisten ließe.

## 5. Prüfung und Belege

| Prüfung | Beleg |
|---|---|
| Zuordnung | `backend/tests/drilldown/test_topic_highlight.py`: `dimension_for_topic` ist die Umkehrung von `topic_for_dimension` für alle Dimensionen beider Quellen; Drill-down-Suite 219 Tests bestanden |
| Frontend | `npm run lint` ohne Befund, `npm run build` (2026-10-23); keine neue Logik außerhalb der Komponenten, daher kein eigener Test |
| Browser | 1&1, Arbeitsatmosphäre, Veränderung ab Jan. 2023 (Backend ohne Abruf): Klick auf die Zeile „Kommunikation“ (24 % → 11 %) schließt den Vergleich; die Adresse wird `?dimension=kommunikation&from=2023-01&to=2023-06`, im Kopf steht „Dimension: Kommunikation“, der Dialog „Bewertungen der Auswahl“ zeigt „Auswahl · Jan. 2023 – Juni 2023 · 15 von 47 Bewertungen zur Dimension Kommunikation“, Themenfeld auf „Alle Themen“, Zeilen mit Sternen und „Kommentar zu Kommunikation“ (Tabelle: 11 Nennungen danach; die Liste enthält zusätzlich die Kommentare, siehe § 2). Keine Konsolenfehler. Erste Fassung (Themenfilter, 5 bzw. 10 Bewertungen) am selben Tag geprüft und ersetzt |

## 6. Offene Punkte

- Ob die Stimmung je Thema ebenfalls einen Klickweg bekommen soll (z. B. nur negative
  Bewertungen des Themas), entscheidet der Autor.
- Ob die markierte Veränderung nach dem Wechsel der Kategorie als Marke in Erinnerung bleiben
  soll (etwa als eigenes Ereignis), ist offen.
- Klickweg aus den Themenbalken der Vorschaukarte (ohne Dialog) ist nicht umgesetzt.
