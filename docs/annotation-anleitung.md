# Anleitung: Referenzzeiträume eintragen (zweite, unabhängige Person)

> **Nicht durchgeführt, keine zweite Person verfügbar (E5, 2026-10-09).** Der Autor ist einziger
> Annotator (Protokoll-Regel 8). Die Datei `backend/data/annotations_zweitperson.json` ist
> entfernt; `backend/scripts/compare_annotations.py` vergleicht zwei beliebige Dateien
> (`--b` ist Pflichtangabe). Die Anleitung bleibt als Dokument der Vorbereitung erhalten.

Stand: 2026-10-08 (E5, Iteration 2). Für eine Person, die das Dashboard nie gesehen hat und es
auch für diese Aufgabe nicht sehen soll. Sie braucht nur den Annotationsbogen (eine HTML-Datei)
und einen Texteditor.

## 1. Zweck

In Bewertungsverläufen von Arbeitgebern auf Kununu sollen Zeiträume gefunden werden, in denen die
Gesamtbewertung deutlich steigt oder fällt. Deine Einträge sind eine unabhängige Referenz: Sie werden
später mit den Einträgen des Autors verglichen, damit die Einschätzung nicht von einer einzigen
Person abhängt.

## 2. Die Regeln in einfachen Worten

Das vollständige Protokoll steht in `docs/referenzzeitraeume-literatur.md`, Abschnitt 3. Für die
Arbeit mit dem Bogen reicht diese Fassung:

1. **Einheit ist der Kalendermonat.** Ein Zeitraum ist ein zusammenhängender Bereich von einem
   ersten bis zu einem letzten Monat, zum Beispiel `2023-03` bis `2023-04`.
2. **Länge.** Der Zeitraum beginnt mit dem ersten Monat, der vom bisherigen Niveau abweicht, und
   endet mit dem ersten Monat, in dem das neue Niveau erreicht ist. Meist sind das ein bis drei
   Monate, höchstens sechs. Ein langsamer, gleichmäßiger Anstieg oder Abfall über viele Monate ist
   ein Trend und wird nicht eingetragen.
3. **Nur Monate mit genug Bewertungen zählen.** Ein Monat zählt, wenn er mindestens 5 Bewertungen
   hat; im Bogen sind Monate mit weniger Bewertungen grau. Der erste und der letzte Monat des
   Zeitraums müssen solche Monate sein; dazwischen darf höchstens ein grauer Monat liegen. Monate
   mit 5 bis 9 Bewertungen nennst du in der Begründung mit ihrer Anzahl.
4. **Wie groß muss die Veränderung sein?** Als Richtwert gilt: Der Durchschnitt der Monatsmittel im
   Zeitraum weicht um mindestens 0,5 Sterne vom Durchschnitt der bis zu sechs Monate davor ab (nur
   Monate mit genug Bewertungen). Ein einzelner Ausreißermonat reicht nicht.
5. **Selten.** Je Unternehmen erwarten wir null bis drei Zeiträume. Zwei Zeiträume desselben
   Unternehmens liegen mindestens drei bewertete Monate auseinander. Findest du nichts, bleibt das
   Unternehmen ohne Eintrag; das ist ein gültiges Ergebnis.
6. **Erst die Reihe, dann die Nachrichten.** Beurteile jeden Zeitraum zuerst allein aus dem Verlauf
   im Bogen und schreibe diese Beurteilung auf. Erst danach darfst du, wenn du möchtest, nach einem
   Ereignis suchen (zum Beispiel in einer Nachrichtensuche) und es mit Datum und Quelle vermerken.
   Ein Ereignis ohne sichtbare Veränderung im Verlauf ergibt keinen Eintrag; eine Veränderung ohne
   gefundenes Ereignis bleibt stehen.
7. **Unabhängigkeit.** Öffne keine andere Ansicht dieses Projekts als den Bogen, und sprich während
   der Arbeit nicht mit dem Autor über einzelne Unternehmen oder Zeiträume.

## 3. Ablauf

1. **Bogen öffnen.** Du bekommst die Datei `annotationsbogen.html` (der Autor erzeugt sie mit
   `cd backend && uv run python scripts/make_annotation_sheet.py`). Öffne sie im Browser. Je
   Unternehmen siehst du den Monatsverlauf der Gesamtbewertung, die Anzahl der Bewertungen je Monat
   und eine aufklappbare Tabelle mit Monat, Mittelwert, Anzahl und Differenz zum Vormonat.
2. **Zeiträume eintragen.** Trage deine Zeiträume in die Datei
   `backend/data/annotations_zweitperson.json` ein, in die Liste `annotations`. Je Zeitraum ein
   Objekt mit genau diesen Feldern:

   | Feld | Inhalt |
   |---|---|
   | `company` | Name des Unternehmens, so wie er im Bogen steht |
   | `source` | `employee` (Bewertungen von Mitarbeitenden; nur diese Quelle ist Teil der Aufgabe) |
   | `dimension` | `durchschnittsbewertung` (Gesamtbewertung) |
   | `period_from` | erster Monat, Format `JJJJ-MM` |
   | `period_to` | letzter Monat, Format `JJJJ-MM`; gleich oder später als `period_from` |
   | `direction` | `rise` (Anstieg) oder `fall` (Abfall) |
   | `note` | deine Begründung auf Deutsch, siehe Beispiel |

   Die `note` nennt in dieser Reihenfolge: Niveau davor (Mittel, Monate, Anzahl je Monat),
   Niveau im Zeitraum (Mittel, Anzahl je Monat), Differenz in Sternen, Richtung, bei Bedarf einen
   Hinweis auf starke Schwankung, dann „Anker: …“ mit Datum und Quelle oder „Anker: keiner“, und
   zum Schluss „Reihe allein“ oder „Reihe + Ereignis“.
3. **Datei prüfen.** Der Autor (oder du, wenn die Umgebung eingerichtet ist) prüft die Datei mit

   ```bash
   cd backend && uv run python scripts/validate_annotations.py --offline --file data/annotations_zweitperson.json
   ```

   Das Skript meldet Tippfehler in Namen oder Monaten, Zeiträume außerhalb der Daten, zu lange
   Zeiträume und zu dünne Randmonate. Korrigiere die gemeldeten Fehler; Warnungen sind Hinweise.
4. **Abgeben.** Die fertige Datei geht an den Autor. Sie wird unverändert in einem eigenen Commit
   abgelegt; danach vergleicht `backend/scripts/compare_annotations.py` deine Einträge mit denen
   des Autors.

## 4. Ein erfundenes Beispiel

Angenommen, der Bogen zeigt für das erfundene Unternehmen „Beispielwerk GmbH“ von Oktober 2022 bis
Februar 2023 Monatsmittel um 3,9 Sterne (7 bis 12 Bewertungen je Monat). Im März 2023 liegt das
Mittel bei 3,2 (9 Bewertungen), im April 2023 bei 3,0 (11 Bewertungen), und die folgenden Monate
bleiben um 3,1. Der Abstand zum Niveau davor beträgt rund 0,8 Sterne, zwei Monate tragen die
Abweichung, beide haben mindestens 5 Bewertungen. Das ist ein Zeitraum:

```json
{
  "company": "Beispielwerk GmbH",
  "source": "employee",
  "dimension": "durchschnittsbewertung",
  "period_from": "2023-03",
  "period_to": "2023-04",
  "direction": "fall",
  "note": "Vorniveau 3,9 (2022-10 bis 2023-02, n=7-12); Zeitraum 3,1 (n=9, 11); Δ -0,8; fall; Anker: keiner; Reihe allein."
}
```

Hätte derselbe Verlauf nur im März einen Einbruch auf 3,2 und im April schon wieder 3,9, wäre das
ein einzelner Monatssprung und kein Zeitraum (Regel 4). Wäre der Abfall über zwölf Monate
gleichmäßig verteilt, wäre es ein Trend (Regel 2).

## 5. Was nicht in diese Anleitung gehört

Diese Anleitung nennt bewusst keine Unternehmen, Monate oder Ergebnisse aus dem Projekt. Alles, was
du einträgst, kommt allein aus dem Bogen und deiner Einschätzung.
