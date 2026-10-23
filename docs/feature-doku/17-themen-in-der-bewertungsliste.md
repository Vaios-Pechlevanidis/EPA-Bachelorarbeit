# 17 – Themen, Themenfilter und Sortierung in „Bewertungen des Zeitraums“

| | |
|---|---|
| Inkrement | Ergänzung der Detailseite „Anomalien im Verlauf“ (2026-10-18) |
| Anforderungen | keine eigene Anforderung aus der Prüfliste; Wunsch des Autors (2026-10-18): bei den Bewertungen des Zeitraums das jeweilige Thema zeigen, nach Thema filtern und auf- oder absteigend nach dem Datum sortieren, an dem die Bewertung geschrieben wurde |
| Entscheidungen | keine neue; Themenregel aus E10 (Schlüsselwort-Themen) mit den Feldern der Korrektur E23 (Kategorie-Kommentare) |
| Status | umgesetzt (2026-10-18), nicht committet; keine neuen Parameter |
| Stand | 2026-10-18; Nachtrag 2026-10-23: bei einer Einzeldimension gilt der Themenfilter innerhalb der Bewertungen, die zur Dimension gehören, und das Auswahlfeld zählt nur diese (Doku 20, E34) |

## 1. Vorstellung

Auf der Detailseite **„Anomalien im Verlauf“** (`/anomalies`) öffnet ein Klick auf die Karte
**„Bewertungen des Zeitraums“** (bei freier Auswahl „Bewertungen der Auswahl“) die Liste der
Einzelbewertungen im Dialog. Dort gilt jetzt:

- **Thema je Bewertung.** Unter dem Textauszug jeder Bewertung stehen ihre Themen als kleine
  graue Marken, z. B. „Gehalt & Sozialleistungen“, „Kommunikation“. Nennt eine Bewertung keines
  der Themen, steht dort „kein Thema erkannt“. Das gerade markierte Thema (siehe unten) ist
  bernsteinfarben, wie seine Fundstellen im Text.
- **Filter nach Thema.** Im Kopf des Dialogs steht neben „davor / ab dem markierten Monat“ ein
  Auswahlfeld **„Alle Themen“**. Es bietet jedes Thema an, das im Zeitraum vorkommt, mit der Zahl
  der Bewertungen, die es nennen, z. B. „Kommunikation (52)“. Mit einem Thema bleiben nur diese
  Bewertungen übrig, ihre Schlüsselwörter sind im Text markiert, und Untertitel und Vorschaukarte
  sagen „… Bewertungen, die Kommunikation nennen“. Die mittlere Note auf der Karte entfällt dann,
  weil sie für alle Bewertungen des Fensters gilt.
- **Sortierung nach Datum.** Daneben schaltet **„neueste zuerst / älteste zuerst“** die
  Reihenfolge um. Maßgeblich ist das Datum der Bewertung (Spalte `datum`, der Tag, an dem sie
  auf Kununu geschrieben wurde). Standard bleibt „neueste zuerst“.

Filter und Sortierung stehen in der Adresse (`?thema=Kommunikation`, `?sortierung=aelteste`),
bleiben beim Wechsel zwischen „davor“ und „ab dem markierten Monat“ erhalten und lassen sich
teilen. Beim Wechsel zwischen Mitarbeitenden und Bewerbenden wird der Themenfilter
zurückgesetzt, weil beide Quellen verschiedene Themen haben. *Nachtrag 2026-10-23:* Er wird auch
zurückgesetzt, wenn Dimension, Status, Firma oder die Auswahl (Veränderung, Einzelmonat,
Zeitraum, eigenes Ereignis) wechseln; der Filter gehört zur aktuellen Auswahl (Rückmeldung des
Autors: ein alter Filter blieb nach dem Wechsel der Dimension stehen). Unter der Liste erklärt ein
Hinweis, woher die Themen kommen, und nennt, wie viele Bewertungen des Zeitraums kein Thema
haben.

Nutzen: Man sieht beim Durchlesen sofort, worüber eine Bewertung spricht, kann gezielt die
Bewertungen zu einem Thema eines auffälligen Zeitraums lesen (etwa nach einem Abfall nur
„Vorgesetztenverhalten“) und den Zeitraum chronologisch von seinem Beginn her lesen.

## 2. Erklärung

**Herkunft der Themen.** Die Themen sind die **Schlüsselwort-Themen** der Themenübersicht aus
Zyklus 1 (`services/keyword_topic_service.py`, `EMPLOYEE_TOPIC_DEFINITIONS` mit 13 Themen,
`CANDIDATE_TOPIC_DEFINITIONS` mit 10 Themen für Bewerbende). Jedes Thema hat eine Liste von
Schlüsselwörtern als reguläre Ausdrücke mit Wortgrenzen, z. B. für „Kommunikation“
`\bkommunikation\b`, `\btransparenz\b`, `\bfeedback\b`. Eine Bewertung **nennt** ein Thema, wenn
eines seiner Schlüsselwörter in einem ihrer Textfelder vorkommt (ohne Groß-/Kleinschreibung):
Titel, Jobbeschreibung bzw. Stellenbeschreibung, „Gut am Arbeitgeber“, „Schlecht am
Arbeitgeber“, Verbesserungsvorschläge und die Kommentare zu den Kategorien
(`EXPLANATION_TOPIC_TEXT_FIELDS`). Das ist dieselbe Regel und dieselbe Feldmenge wie beim
Vorher-Nachher-Vergleich und bei der Markierung des Themas der gewählten Dimension (Doku 02,
§ 2.8; Korrektur vom 2026-10-13). Eine Bewertung kann mehrere Themen oder keines nennen.

**Ablauf im Backend.** `GET /api/analytics/company/{id}/reviews` mit `start`, `end`, `source`
(und optional `status`, `dimension`) liest alle Bewertungen des Zeitraums, filtert nach der
Statusgruppe und bestimmt für jede die Themen (`topics_in_review`). Neu in der Antwort:

- je Bewertung `topics`: die Themen in der Reihenfolge der Definitionen;
- `topic_summary.counts`: je Thema die Zahl der Bewertungen des Zeitraums, die es nennen, und
  `topic_summary.without_topic`; gezählt **vor** dem Themenfilter, damit das Auswahlfeld alle
  Themen mit ihrer Zahl anbieten kann;
- `topic_summary.filter` und `topic_summary.marked`: das gefilterte und das markierte Thema.

Neue Parameter: `topic=<Thema>` lässt nur Bewertungen mit diesem Thema übrig und markiert
dessen Fundstellen (`highlights`); ein unbekanntes Thema oder `topic` zusammen mit dem älteren
`topic_only` ergibt 400. `order=asc` sortiert nach Datum aufsteigend, `order=desc` (Standard)
absteigend; bei gleichem Tag entscheidet die `id`, Bewertungen ohne Datum stehen in beiden
Fällen am Ende (`sort_by_date` in `services/review_service.py`). Sortiert und gefiltert wird
vor dem Seitenschnitt, deshalb setzt „Weitere 25 laden“ die gewählte Reihenfolge fort.

**Markiertes Thema.** Ist ein Thema gefiltert, werden dessen Schlüsselwörter markiert; sonst,
wie bisher, das Thema der gewählten Dimension (bei der Gesamtbewertung keines). Die Zahl
„davon N nennen Image“ zur Dimension bleibt unverändert.

**Frontend.** `useReviewPages` reicht `topic` und `order` durch und behält die Zählung je Thema,
solange sich nur Filter oder Sortierung ändern (kein Flackern des Auswahlfelds).
`ReviewListControls` und `TopicTags` stehen in `components/dashboard/PeriodReviews.jsx`, die
Adressparameter in `pages/Anomalies.jsx`. Das ältere `?thema=nur` (nur das Thema der Dimension)
funktioniert weiter und zeigt im Auswahlfeld dieses Thema an.

**Geschwindigkeit.** Weil die Themen jetzt bei jeder Seite für alle Bewertungen des Zeitraums
bestimmt werden, fasst `topics_in_review` die Schlüsselwörter eines Themas zu einem einzigen
regulären Ausdruck (Alternative) zusammen. Er findet genau dann etwas, wenn eines der
Einzelmuster etwas findet; die Ergebnisse sind gleich (Test über alle Demo-Bewertungen), die
Laufzeit sinkt bei 1000 Bewertungen mit realistischer Textlänge von etwa 0,7 s auf 0,3 s.

## 3. Begründung

- **Schlüsselwort-Themen statt neuer Klassifikation.** Die Themen sind dieselben wie in der
  Themenübersicht, im Vorher-Nachher-Vergleich („Stärkste Verschiebungen je Thema“) und bei der
  Markierung der Dimension. So meint „Kommunikation“ überall dasselbe, und jede Zuordnung ist
  am markierten Schlüsselwort nachprüfbar. Ein Sprachmodell oder ein Themenmodell würde eine
  zweite, schwer prüfbare Definition einführen.
- **Mehrere Themen je Bewertung.** Kununu-Freitexte sprechen oft mehrere Punkte an; ein
  einziges „Hauptthema“ müsste nach einer zusätzlichen, willkürlichen Regel gewählt werden.
- **Zählung vor dem Filter, im Backend.** Die Liste wird seitenweise geladen; im Browser wären
  nur die geladenen 25 Bewertungen bekannt. Nur das Backend kennt alle Bewertungen des Zeitraums
  und kann Filter, Zählung und Sortierung vor dem Seitenschnitt anwenden.
- **Auswahlfeld statt Kästchen.** Das bisherige Kästchen „nur Bewertungen, die Image nennen“
  ging nur bei einer Einzeldimension und nur für deren Thema. Das Auswahlfeld deckt diesen Fall
  ab und funktioniert auch bei der Gesamtbewertung; ein zweites Bedienelement für dasselbe wäre
  doppelt. Gestaltung wie bei „Externe Berichte“ (Sortierung als Umschalter, Filter als
  Auswahlfeld im Dialogkopf).
- **Sortierung nach dem Datum der Bewertung.** Die Frage zu einem auffälligen Zeitraum ist
  oft, was zu Beginn geschrieben wurde; „älteste zuerst“ liest den Zeitraum in seiner
  zeitlichen Abfolge.

## 4. Grenzen

- Ein Thema „nennt“ eine Bewertung nur, wenn ein Schlüsselwort wörtlich vorkommt. Umschreibungen
  ohne Schlüsselwort („der Chef redet nicht mit uns“ ohne „Kommunikation“) werden nicht erkannt;
  ein Schlüsselwort in verneinter oder ironischer Form wird mitgezählt. Das Thema sagt nichts
  darüber, ob die Bewertung das Thema lobt oder kritisiert.
- Die Zahl je Thema ist die Zahl der Bewertungen mit Treffer, nicht die Bedeutung des Themas
  für den Zeitraum. Unterschiede zwischen den Fenstern zeigt der Vorher-Nachher-Vergleich.
- Die Themenliste ist die aus Zyklus 1 und unverändert; Themen außerhalb der Liste fehlen.
- Kein Filter „ohne erkanntes Thema“; die Zahl steht nur im Hinweis unter der Liste.

## 5. Prüfung und Belege

- Backend: `backend/tests/drilldown/test_review_topics.py` (Themen je Bewertung gleich
  `topics_in_review`, Zählung über den ganzen Zeitraum und unabhängig von der Seite, Filter
  samt Markierung, Filter mit Dimension, `topic_only`, ungültige Angaben 400/422, Sortierung
  auf- und absteigend, Seiten in aufsteigender Folge, `sort_by_date` mit Zeilen ohne Datum,
  zusammengefasste Muster gleich Einzelmustern für alle Demo-Bewertungen beider Quellen).
  Zwei bestehende Tests prüften die genaue Feldmenge einer Bewertung und kennen jetzt `topics`.
  Gesamte Backend-Suite: 1510 bestanden (2026-10-18).
- Frontend: Lint ohne Befund, Build erfolgreich.
- Manuell (2026-10-18, In-Memory-Backend, Demo 3, Veränderung ab Dez. 2023): Themen-Marken je
  Bewertung; „Kommunikation (52)“ filtert auf 52 Bewertungen, Marke und Fundstellen
  bernsteinfarben; „älteste zuerst“ beginnt am 01.12.2023, nach „Weitere 25 laden“ 50 von 52
  in aufsteigender Folge; Wechsel auf „davor“ behält Filter und Sortierung (64 Bewertungen);
  Vorschaukarte nennt den Filter; `?thema=nur` mit Dimension Kommunikation zeigt weiter nur
  deren Bewertungen; keine Fehler in der Konsole.

## 6. Offene Punkte

- Ob ein Filter „ohne erkanntes Thema“ gebraucht wird, entscheidet der Autor nach den
  Gesprächen mit den Fachleuten.
- Der PDF-Export enthält die Bewertungsliste nicht; daran ändert sich nichts.
