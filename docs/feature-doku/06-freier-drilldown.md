# 06 – Freier Drill-down

| | |
|---|---|
| Inkrement | 2 (Nachtrag, Zyklus 2) |
| Anforderungen | Wunsch des Autors vom 2026-10-05: Drill-down bei Bedarf auch für Unternehmen ohne erkannte Veränderung |
| Entscheidungen | E17 in `docs/entscheidungen.md`; E10–E12 (Themen, Stimmung, Fenster) gelten für den Vergleich weiter |
| Status | umgesetzt; Mindestlänge des Vergleichszeitraums **vorläufig** |
| Stand | 2026-10-05 |

## 1. Vorstellung

Auf der Detailseite „Anomalien im Verlauf“ lässt sich jetzt **jeder Zeitraum** untersuchen,
nicht nur eine erkannte Veränderung:

- **Klick auf einen Monat** im Diagramm wählt diesen Monat.
- **Ziehen mit gedrückter Maustaste** wählt mehrere Monate; die Auswahl erscheint als
  getönte Fläche, der Vergleichszeitraum davor grau.
- Der Abschnitt **„Bewertungen eines Zeitraums ansehen“** unter dem Diagramm bietet „von /
  bis“ und die Schnellwahl „Letzter Monat“, „Letzte 6 Monate“, „Letzte 12 Monate“. Er hilft
  auch bei Reihen, deren Monate im Diagramm nicht anklickbar sind (z. B. dünne
  Bewerberreihen ohne bewerteten Monat).

Darunter erscheinen **„Vergleich mit dem Zeitraum davor“** (gleiche Darstellung wie der
Vorher-Nachher-Vergleich: Anzahl, Gesamtnote, Stimmung, Verschiebungen je Thema, kleine
Basis) und **„Bewertungen der Auswahl“** mit Umschalter auf den Zeitraum davor, Detailfenster,
Markierung des Themas der Dimension und Filter „nur Bewertungen, die … nennen“.

Die Auswahl steht in der Adresse (`?from=2020-02&to=2022-01`) und bleibt beim Wechsel von
Quelle, Status oder Dimension stehen, so lässt sich derselbe Zeitraum für verschiedene
Gruppen ansehen. Ein Klick auf eine Stufe wählt wie bisher die erkannte Veränderung, ein
Klick auf eine Raute den auffälligen Einzelmonat (mit Hinweis im Vergleich).

Nutzen: Auch bei Unternehmen ohne erkannte Veränderung (z. B. Cancom) oder ohne
automatische Erkennung (z. B. Aixtron) kommt man direkt zu den Bewertungen eines
Zeitraums und sieht, was sich gegenüber der Zeit davor in den Texten verschoben hat.

## 2. Erklärung

- **Auswahl:** Kalendermonate `from` bis `to` einschließlich; in die Liste gehen alle
  Bewertungen dieser Monate, auch aus Monaten mit weniger als 5 Bewertungen.
- **Vergleichszeitraum:** die gleich vielen Monate direkt davor, mindestens 6
  (`period_windows`). Beispiel: Auswahl März 2024 → Vergleich September 2023 bis Februar
  2024; Auswahl Februar 2020 bis Januar 2022 → Vergleich Februar 2018 bis Januar 2020.
- **Vergleich:** `GET /api/analytics/company/{id}/compare?from=&to=&source=&dimension=&status=`
  mit denselben Kennzahlen wie der Vorher-Nachher-Vergleich (E10–E12): Anteile der
  Schlüsselwort-Themen, Stimmung (Transformer mit Rückfall, Stichprobe 300), kleine Basis.
- **Beispiel (2026-10-05, echte Daten):** Cancom, Mitarbeitende, Auswahl Februar 2020 bis
  Januar 2022: 211 Bewertungen, Ø Gesamtnote 3,51; Zeitraum davor (Februar 2018 bis Januar
  2020) 269 Bewertungen, Ø 3,28; Verschiebung +0,24 Sterne.

## 3. Begründung

- Der Drill-down ist ein Werkzeug zum Nachsehen und soll nicht von der Erkennung abhängen;
  die Erkennung markiert nur, wo es sich besonders lohnt.
- Klick und Ziehen im Diagramm sind der direkte Weg; das Auswahlfeld ist der Weg ohne
  Maus und für Reihen ohne anklickbare Monate.
- Ein gleich langer Zeitraum davor ist die einfachste Bezugsgröße; mindestens 6 Monate wie
  die Fensterlänge in E12, damit ein einzelner Monat nicht gegen einen einzelnen Monat
  verglichen wird.

## 4. Grenzen

- Eine frei gewählte Auswahl ist keine erkannte Veränderung. Wer einen sichtbaren
  Einbruch auswählt, findet erwartbar Unterschiede; das ist kein Beleg.
- Keine Aussage über Ursachen; kleine Basis und Stichprobe wie in E11 und E12.
- Ziehen setzt eine Maus oder ein Trackpad voraus; auf Touch-Geräten gilt das Auswahlfeld.

## 5. Prüfung und Belege

| Was | Beleg |
|---|---|
| Backend | `backend/tests/drilldown/test_period_comparison.py`: Fenster (ein Monat, lange Auswahl, Jahreswechsel, ungültige Angaben), Form der Antwort, Zählung je Fenster, Demo 1 ohne Veränderung, Dimension und Status, leerer Zeitraum, 400/422 |
| Browser (2026-10-05) | Cancom (keine erkannte Veränderung): Ziehen Feb. 2020 – Jan. 2022 → Vergleich 269 / 211 Bewertungen, Liste 211; Klick auf einen Monat → `from=to=2024-02`. Aixtron (keine automatische Erkennung): „Letzte 12 Monate“ → Aug. 2024 – Juli 2025, 28 / 25 Bewertungen |

## 6. Offene Punkte

- Mindestlänge 6 Monate für den Vergleichszeitraum ist vorläufig.
- Vergleich zweier frei gewählter Zeiträume (statt „Zeitraum davor“) ist nicht umgesetzt.
