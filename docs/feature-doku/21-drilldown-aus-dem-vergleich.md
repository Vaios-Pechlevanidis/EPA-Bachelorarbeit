# 21 – Drill-down aus dem Vorher-Nachher-Vergleich in die Bewertungen eines Themas

| | |
|---|---|
| Inkrement | Ergänzung der Detailseite „Anomalien im Verlauf“ (2026-10-23) |
| Anforderungen | keine eigene Anforderung aus der Prüfliste; Wunsch des Autors (2026-10-23): Ein Klick auf eine Kategorie im Vergleich soll den Drill-down zu dieser Kategorie und ihren Daten erweitern |
| Entscheidungen | keine neue; nutzt Themenfilter und Fensterwahl der Bewertungsliste (Doku 17, E10) und die Vergleichsfenster (E12, E17) |
| Status | umgesetzt (2026-10-23), nicht committet; keine neuen Parameter |
| Stand | 2026-10-23 |

## 1. Vorstellung

Im Dialog **„Vorher-Nachher-Vergleich“** (Karte links unter der Drill-down-Leiste der Seite
`/anomalies`) steht die Tabelle **„Größte Verschiebungen je Thema“**: je Schlüsselwort-Thema
der Anteil der Bewertungen davor und danach, die Differenz in Prozentpunkten und die Stimmung
je Fenster. Bisher war die Tabelle nur zum Lesen da. Jetzt gilt:

- **Themenzeile anklicken.** Die Zeile (Themenname gepunktet unterstrichen, Zeiger beim
  Darüberfahren) schließt den Vergleich und öffnet die Karte **„Bewertungen des Zeitraums“**
  im Dialog, gefiltert auf dieses Thema und auf das Fenster **ab dem markierten Monat** (bei
  freier Auswahl: die Auswahl). Untertitel und Themenfeld sagen „…, die Kommunikation nennen“,
  die Fundstellen sind im Text markiert.
- **Anteil davor anklicken.** Die Prozentzahl in der Spalte „Anteil davor“ ist ein eigener
  Knopf und öffnet dieselbe Liste für das Fenster **davor**.
- Im Dialog der Bewertungen lässt sich danach wie gewohnt zwischen „davor“ und „ab dem
  markierten Monat“ wechseln, das Thema bleibt gefiltert; „Alle Themen“ hebt den Filter auf.
  Eine Zeile führt weiter in das Detailfenster der Bewertung (Doku 20).
- Ein Hinweis unter der Tabelle nennt den Klickweg. Tastatur: Zeile mit Tab erreichbar,
  Eingabe oder Leertaste öffnet.

Der Themenfilter steht in der Adresse (`?thema=Kommunikation`), die Liste ist also dieselbe,
die man über das Auswahlfeld „Alle Themen“ erreicht. Mit einer gewählten Dimension (Doku 20)
gilt der Themenfilter innerhalb der Bewertungen, die zur Dimension gehören.

Nutzen: Wer in der Tabelle sieht, dass „Kommunikation“ von 7 % auf 26 % gestiegen ist, liest
mit einem Klick die 26 % – die Bewertungen ab dem markierten Monat, die Kommunikation nennen –
und mit einem zweiten Klick die 7 % davor; die Zahl der Tabelle wird so zu ihren Texten.

## 2. Erklärung

**Datenfluss.** Die Themen der Tabelle sind die Schlüsselwort-Themen des Vergleichs
(`comparison.topics` aus `GET …/anomalies/{id}/explanations` bzw. `…/compare`, E10); dieselben
Namen nimmt die Bewertungsliste als Themenfilter (`GET …/reviews?topic=<Thema>`, Doku 17).
Deshalb stimmen die Zahlen überein: „Anteil danach 26 %“ sind die Bewertungen des Fensters
ab dem markierten Monat, die das Thema nennen, geteilt durch alle Bewertungen des Fensters;
die Liste zeigt genau diese Bewertungen (mit „N von M angezeigt“ beim Nachladen). Einzige
Abweichung: Der Vergleich zählt Nennungen in allen Bewertungen des Fensters, die Liste
wendet zusätzlich einen Statusfilter oder die Dimension an, wenn gewählt.

**Frontend.** `AnomalyComparison` bekommt `onDrill(thema, seite)`; die Zeile ruft es mit
„after“, der Knopf in „Anteil davor“ mit „before“. `ExpandableCard` kann seinen Dialog jetzt
von außen steuern (`open`, `onOpenChange`); `pages/Anomalies.jsx` hält dafür `openCard`
(„comparison“ | „reviews“ | null). `drillToTopic` setzt das Fenster der Bewertungsliste
(`detail.onSide`), den Themenfilter in der Adresse (`?thema=`) und öffnet die Bewertungskarte;
der Vergleich schließt sich, weil nur eine Karte zugleich geöffnet ist. Ohne `onDrill`
(andere Verwendungen) bleibt die Tabelle wie bisher.

**Parameter.** Keine. Themenfilter, Fenster und Sortierung sind die bestehenden.

## 3. Begründung

- **Daten statt Erzählung.** Der Autor hatte am 2026-10-22 eine erzählende Zusammenfassung
  der Veränderung abgelehnt; der Drill-down soll über Datenzeilen bis zur einzelnen Bewertung
  führen. Die Tabelle des Vergleichs ist dafür der natürliche Ausgangspunkt: Jede Zahl darin
  ist eine Menge von Bewertungen, die man lesen kann.
- **Vorhandene Mechanik.** Themenfilter, Fensterwahl und Adresse der Bewertungsliste gab es
  schon (Doku 17); der Klick setzt sie nur. So bleiben Zahlen und Liste konsistent, und es
  entsteht keine zweite Filterlogik.
- **Ein Dialog zur Zeit.** Der Vergleich schließt sich beim Klick, statt dass sich ein zweiter
  Dialog darüberlegt; die Karte „Vorher-Nachher-Vergleich“ bleibt auf der Seite und ist mit
  einem Klick wieder offen.
- **„Davor“ über die Zahl.** Eine Zeile hat nur ein Ziel; das Fenster davor erreicht man
  über die Prozentzahl davor, weil sie genau diese Menge bezeichnet, ohne die Zeile mit zwei
  Knöpfen zu überladen.

## 4. Grenzen

- Der Themenfilter beruht auf deutschen Schlüsselwörtern (E10): mehrdeutige Wörter zählen
  mit, englische Texte kaum.
- Bei „kleine Basis“ sind die Anteile unsicher; die Liste zeigt dann entsprechend wenige
  Bewertungen.
- Der Vergleich zählt alle Bewertungen des Fensters, die Liste filtert zusätzlich nach Status
  oder Dimension, wenn gewählt; die Zahl kann dann kleiner sein als „Nennungen“ in der
  Tabelle.
- Kein Klick auf die Stimmungsbalken: Die Stimmung ist eine Modellschätzung je Bewertung,
  keine Teilmenge, die sich auflisten ließe.

## 5. Prüfung und Belege

| Prüfung | Beleg |
|---|---|
| Frontend | `npm run lint` ohne Befund, `npm run build` (2026-10-23); keine neue Logik außerhalb der Komponenten, daher kein eigener Test |
| Browser | 1&1, Arbeitsatmosphäre, Veränderung ab Jan. 2023 (Backend ohne Abruf): Klick auf die Zeile „Kommunikation“ (24 % → 11 %) schließt den Vergleich, die Adresse trägt `?thema=Kommunikation`, der Dialog „Bewertungen des Zeitraums“ zeigt „ab dem markierten Monat · Jan. 2023 – Juni 2023 · 5 Bewertungen, die Kommunikation nennen“, Themenfeld auf „Kommunikation“; Klick auf den Anteil davor öffnet „davor · Juli 2022 – Dez. 2022 · 10 Bewertungen, die Kommunikation nennen“ (Tabelle: 11 Nennungen; eine Bewertung gehört nicht zur gewählten Dimension, siehe § 4). Keine Konsolenfehler |

## 6. Offene Punkte

- Ob die Stimmung je Thema ebenfalls einen Klickweg bekommen soll (z. B. nur negative
  Bewertungen des Themas), entscheidet der Autor.
- Klickweg aus den Themenbalken der Vorschaukarte (ohne Dialog) ist nicht umgesetzt.
