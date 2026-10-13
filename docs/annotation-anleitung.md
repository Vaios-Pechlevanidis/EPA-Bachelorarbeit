# Anleitung: Referenzzeiträume eintragen (zweite, unabhängige Person, blinde Fassung)

> **Status (2026-10-13): vorbereitet, Durchführung offen.** Bisher ist der Autor einziger
> Annotator (E5, Aktualisierung 2026-10-09; Protokoll-Regel 8). Für eine blinde Zweitannotation
> liegen Bogen, Vorlage, Rückübersetzung und Vergleich bereit (Abschnitt 5). **Der Autor bestimmt
> Teilmenge und Person**; beides wird festgelegt und notiert, bevor die Person beginnt. Die
> frühere, nicht blinde Fassung dieser Anleitung (Bogen mit Unternehmen und Kalendermonaten,
> Ereignissuche nach der Beurteilung) wurde nicht durchgeführt und ist durch diese ersetzt.

Stand: 2026-10-13 (E5). Abschnitte 1 bis 4 und 6 sind für die Person, die die Zeiträume einträgt; sie
hat das Dashboard nie gesehen und soll es auch für diese Aufgabe nicht sehen. Sie braucht nur den
blinden Annotationsbogen (eine HTML-Datei), die Vorlage (eine JSON-Datei) und einen Texteditor.
Abschnitt 5 beschreibt den Ablauf für den Autor.

## 1. Zweck

In Bewertungsverläufen von Arbeitgebern (Bewertungen von Mitarbeitenden auf einer
Bewertungsplattform, 1 bis 5 Sterne) sollen Zeiträume gefunden werden, in denen die
Gesamtbewertung deutlich steigt oder fällt. Deine Einträge sind eine unabhängige Referenz: Sie werden
später mit den Einträgen des Autors verglichen, damit die Einschätzung nicht von einer einzigen
Person abhängt.

Der Bogen ist **blind**: Er nennt weder das Unternehmen noch die Kalendermonate. Die Reihen heißen
„Reihe A“, „Reihe B“ und so weiter, die Monate M001, M002 und so weiter. So beruht deine
Einschätzung allein auf dem Verlauf und nicht auf dem, was du über ein Unternehmen oder eine Zeit
weißt.

## 2. Die Regeln in einfachen Worten

Das vollständige Protokoll steht im Bogen (Kasten oben). Für die Arbeit reicht diese Fassung:

1. **Einheit ist der Monat.** Die Monate sind je Reihe fortlaufend nummeriert: M001 ist der erste
   Monat der Reihe, M002 der folgende Kalendermonat und so weiter; Monate ohne Bewertung sind
   mitgezählt. Die Nummern zweier Reihen gehören nicht zusammen (M010 in Reihe A ist nicht derselbe
   Monat wie M010 in Reihe B). Ein Zeitraum ist ein zusammenhängender Bereich von einem ersten bis
   zu einem letzten Monat, zum Beispiel `M015` bis `M016`.
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
5. **Selten.** Je Reihe erwarten wir null bis drei Zeiträume. Zwei Zeiträume derselben Reihe liegen
   mindestens drei bewertete Monate auseinander. Findest du nichts, bleibt die Reihe ohne Eintrag;
   das ist ein gültiges Ergebnis.
6. **Nur die Reihe.** Beurteile jede Reihe für sich und jeden Zeitraum allein aus ihrem eigenen
   Verlauf im Bogen. Suche nicht nach Nachrichten oder Ereignissen und versuche nicht, das
   Unternehmen oder die Kalendermonate zu erraten. Deine Begründung endet immer mit „Reihe allein“.
7. **Unabhängigkeit.** Öffne keine andere Ansicht dieses Projekts als den Bogen, gib den Bogen nicht
   weiter, und sprich während der Arbeit nicht mit dem Autor über einzelne Reihen oder Zeiträume.

## 3. Ablauf

1. **Bogen öffnen.** Du bekommst die Datei `annotationsbogen_blind.html`. Öffne sie im Browser. Je
   Reihe siehst du den Monatsverlauf der Gesamtbewertung, die Anzahl der Bewertungen je Monat
   (senkrechte Linien alle zwölf Monate ab M001) und eine aufklappbare Tabelle mit Monat (Mxxx),
   Mittelwert, Anzahl und Differenz zum letzten Monat mit Wert.
2. **Zeiträume eintragen.** Trage deine Zeiträume in die Vorlage `annotations_zweitperson_blind.json`
   ein, in die Liste `annotations`. Unter `hinweise.reihen_im_bogen` stehen die Reihen mit ihrem
   ersten und letzten Monat. Je Zeitraum ein Objekt mit genau diesen Feldern:

   | Feld | Inhalt |
   |---|---|
   | `company` | Bezeichnung der Reihe, so wie sie im Bogen steht, zum Beispiel `Reihe A` |
   | `source` | `employee` (Bewertungen von Mitarbeitenden; nur diese Quelle ist Teil der Aufgabe) |
   | `dimension` | `durchschnittsbewertung` (Gesamtbewertung) |
   | `period_from` | erster Monat, wie in der Monatstabelle, zum Beispiel `M015` |
   | `period_to` | letzter Monat; gleich oder später als `period_from` |
   | `direction` | `rise` (Anstieg) oder `fall` (Abfall) |
   | `note` | deine Begründung auf Deutsch, siehe Beispiel |

   Die `note` nennt in dieser Reihenfolge: Niveau davor (Mittel, Monate, Anzahl je Monat),
   Niveau im Zeitraum (Mittel, Anzahl je Monat), Differenz in Sternen, Richtung, bei Bedarf einen
   Hinweis auf starke Schwankung und zum Schluss „Reihe allein“. Monate schreibst du wie im Bogen
   (Mxxx).
3. **Abgeben.** Die fertige Datei geht an den Autor. Er übersetzt sie, prüft sie und schickt dir
   gemeldete Fehler in der Schreibweise des Bogens (Reihe, Mxxx) zurück. Korrigiere die Fehler in
   deiner Datei; Warnungen sind Hinweise.

## 4. Ein erfundenes Beispiel

Angenommen, der Bogen zeigt für „Reihe B“ von M010 bis M014 Monatsmittel um 3,9 Sterne (7 bis 12
Bewertungen je Monat). In M015 liegt das Mittel bei 3,2 (9 Bewertungen), in M016 bei 3,0 (11
Bewertungen), und die folgenden Monate bleiben um 3,1. Der Abstand zum Niveau davor beträgt rund
0,8 Sterne, zwei Monate tragen die Abweichung, beide haben mindestens 5 Bewertungen. Das ist ein
Zeitraum:

```json
{
  "company": "Reihe B",
  "source": "employee",
  "dimension": "durchschnittsbewertung",
  "period_from": "M015",
  "period_to": "M016",
  "direction": "fall",
  "note": "Vorniveau 3,9 (M010 bis M014, n=7-12); Zeitraum 3,1 (n=9, 11); Δ -0,8; fall; Reihe allein."
}
```

Hätte derselbe Verlauf nur in M015 einen Einbruch auf 3,2 und in M016 schon wieder 3,9, wäre das
ein einzelner Monatssprung und kein Zeitraum (Regel 4). Wäre der Abfall über zwölf Monate
gleichmäßig verteilt, wäre es ein Trend (Regel 2).

## 5. Ablauf für den Autor (Vorbereitung, Rückweg, Vergleich)

Alle Befehle aus `backend/`. Kein Schritt liest Erkennungsergebnisse; die Skripte importieren keinen
Erkennungscode und lesen nur Dateien.

1. **Teilmenge und Person festlegen.** Der Autor bestimmt, welche Reihen (Unternehmens-ids aus
   `data/data_density.json`) und welche Person, und notiert beides vor Beginn, etwa in E5. Die
   Auswahl hängt nicht davon ab, wie die Erkennung in einer Reihe abschneidet.
2. **Blinden Bogen erzeugen.**

   ```bash
   uv run python scripts/make_annotation_sheet.py --blind --companies <ids, kommagetrennt> --seed <Zahl>
   ```

   Ergebnis: `data/annotationsbogen_blind.html` (für die Person) und
   `data/annotationsbogen_blind_schluessel.json` (nur für den Autor). Beide sind über `.gitignore`
   ausgeschlossen. Die Reihen stehen in zufälliger, durch `--seed` fester Reihenfolge; ohne `--seed`
   wird eine Zahl gezogen und im Schlüssel vermerkt. Der Bogen enthält keine Jahreszahl, keinen
   Namen, keine Unternehmens-id, keinen Dateinamen und kein Erzeugungsdatum; das Skript prüft das vor
   dem Schreiben (Test `backend/tests/test_make_annotation_sheet.py`). Ohne `--companies` enthält er
   alle nach E4 geeigneten Reihen.
3. **Vorlage erzeugen.**

   ```bash
   uv run python scripts/blind_annotations.py --template
   ```

   Ergebnis: `data/annotations_zweitperson_blind.json` mit leerer Liste und den Reihen des Bogens
   samt Indexbereich, ohne Zuordnung. Eine vorhandene Datei wird nur mit `--force` überschrieben.
4. **Übergabe.** Die Person erhält den Bogen, die Vorlage und die Abschnitte 1 bis 4 und 6 dieser
   Anleitung (ohne den Kopf mit Status und Datum). Sie erhält **nicht**: den Schlüssel, das
   Repository, das Dashboard, `data/annotations.json`, `docs/` oder die Serien-CSVs (deren
   Dateinamen nennen Unternehmen).
   Auch mündlich nennt der Autor weder die Plattform noch den Zeitraum oder Stand der Daten (wann
   sie abgerufen wurden, bis wann sie reichen) und weist nicht darauf hin, dass Reihen im selben
   Monat enden (siehe Punkt 8).
5. **Rückübersetzung und Validierung.**

   ```bash
   uv run python scripts/blind_annotations.py --for-person
   ```

   Das Skript liest die blinde Datei und den Schlüssel, übersetzt `Reihe X` in den Namen aus
   `data_density.json` und Mxxx in YYYY-MM (auch in der `note`), schreibt
   `data/annotations_zweitperson.json` im Schema von `annotations.json` und prüft sie mit
   `validate_annotations` (offline, mit den Serien-CSVs für die Regeln 2, 3 und 5). Die Zuordnung
   Reihe → Unternehmen steht in `hinweise.herkunft`. Mit `--for-person` folgt der Prüfbericht
   zusätzlich in der Schreibweise des Bogens; nur dieser Teil geht an die Person zurück. Fehler in
   der blinden Datei selbst (unbekannte Reihe, Monat außerhalb der Reihe) meldet das Skript, ohne
   etwas zu schreiben. `data/annotations.json` schreibt es nie.
6. **Ablage.** Blinde Datei und übersetzte Datei unverändert in einem eigenen Commit. Ob der
   Schlüssel nach Abschluss offengelegt oder nur archiviert wird, entscheidet der Autor; die
   übersetzte Datei hält die Zuordnung der Reihen ohnehin fest.
7. **Vergleich.**

   ```bash
   uv run python scripts/compare_annotations.py --b data/annotations_zweitperson.json \
       --series data/annotations_zweitperson.json --json data/calibration/<dateiname>.json
   ```

   `--series` begrenzt den Vergleich auf die Reihen des blinden Bogens (ebenso möglich: der
   Schlüssel oder eine Liste von Unternehmens-ids). Ausgabe:
   - **Abgleich nach Regel 6** wie bisher: übereinstimmende Zeiträume (Toleranz ±1 Monat, gleiche
     Richtung, Eins-zu-eins), nur beim Autor, nur bei der Person, Anteil der Reihen, in denen beide
     keinen Zeitraum sehen.
   - **Cohens κ auf Monatsebene**, gesamt und je Reihe: jeder bewertete Monat erhält je Datei
     `rise`, `fall` oder `keine` (Monate innerhalb eines Zeitraums tragen dessen Richtung);
     κ = (p_o − p_e) / (1 − p_e) mit beobachteter Übereinstimmung p_o und aus den Randverteilungen
     erwarteter Übereinstimmung p_e. 1 heißt vollständige Übereinstimmung, 0 so viel wie zufällig
     erwartet. Der Bericht nennt p_o, p_e und die Kreuztabelle mit.
   - **Lesart:** Fast alle Monate liegen in keinem Zeitraum; p_e ist deshalb hoch, und κ reagiert
     stark auf kleine Verschiebungen. κ kennt anders als Regel 6 keine Toleranz: Ein um einen Monat
     verschobener, nach Regel 6 übereinstimmender Zeitraum senkt κ. Beide Maße werden zusammen
     berichtet; keines sagt, welche Person richtig liegt. In einer Reihe, in der beide Dateien
     keinen Zeitraum haben, ist κ nicht definiert („–“); sie geht aber in κ gesamt ein.
8. **Grenzen der blinden Fassung.**
   - Länge der Reihe und Anzahl der Bewertungen je Monat bleiben sichtbar und lassen grobe
     Rückschlüsse auf die Größe eines Unternehmens zu.
   - Die Indizes zählen je Reihe ab M001, die Reihen liegen aber nicht beliebig zueinander. Von den
     15 nach E4 geeigneten Reihen enden 6 im selben Kalendermonat, 4 in einem zweiten und 2 in
     einem dritten; 8 Reihen beginnen innerhalb von 13 Kalendermonaten (Stand der Serien-CSVs am
     2026-10-13). Wer die Reihen am Ende ausrichtet, bringt die Reihen mit gleichem Endmonat genau
     zur Deckung und sieht gleichzeitige Veränderungen. Wer den Stand der Daten kennt oder schätzt
     oder weiß, seit wann die Plattform besteht, kann Indizes ungefähr Kalendermonaten zuordnen und
     so doch Wissen über allgemeine Ereignisse einbeziehen. Der Bogen schließt das nicht aus.
   - Abschwächung ohne Eingriff in die Daten: Abschnitte 1 bis 4 und 6 und der Bogen nennen weder
     Plattform noch Zeitraum noch Stand der Daten, der Autor nennt sie auch mündlich nicht
     (Punkt 4), und die Person beurteilt jede Reihe für sich (Abschnitt 2, Regel 6). Ausschließen
     ließe sich die Ausrichtung nur, indem man Reihen am Anfang oder Ende kürzt; das verändert die
     Daten und ist nicht vorgesehen.
   - Ob die Person Reihen ausgerichtet oder Kalendermonate vermutet hat, lässt sich nicht prüfen.
     Der Autor kann sie nach der Abgabe danach fragen und die Antwort mit dem Ergebnis festhalten.
   - Die Einträge des Autors sind nicht blind entstanden (E5); der Vergleich misst die
     Übereinstimmung einer blinden Person mit dieser Referenz, nicht mit einem Goldstandard.

## 6. Was nicht in diese Anleitung gehört

Die Abschnitte 1 bis 4 nennen bewusst keine Unternehmen und keine Kalendermonate, weder Zeitraum noch
Stand der Daten und keine Ergebnisse aus dem Projekt (Abschnitt 5 ist nur für den Autor). Alles, was du
einträgst, kommt allein aus dem Bogen und deiner Einschätzung.
