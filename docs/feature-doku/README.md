# Feature-Doku

Jedes neue Feature des Dashboards bekommt hier eine eigene Datei. Sie stellt das
Feature vor (was sieht die Nutzerin oder der Nutzer?), erklärt es (wie entsteht das
Ergebnis?) und begründet es (warum so und nicht anders?).

Abgrenzung zu den anderen Dokumenten:

- `docs/entscheidungen.md` hält einzelne Entscheidungen fest (E1, E2, …) mit Status.
  Die Feature-Doku verweist darauf, statt sie zu wiederholen.
- `docs/datenbasis.md` beschreibt die Daten; sie wird automatisch erzeugt.
- Die Feature-Doku richtet sich an Leserinnen und Leser der Arbeit, an die
  Interviewpartner (DZ3) und an die Betreuung: verständlich, ohne Code lesen zu müssen.

## Regeln

- Eine Datei je Feature, nummeriert in der Reihenfolge der Entstehung:
  `NN-kurzname.md`. Neue Einträge mit [`_vorlage.md`](_vorlage.md) beginnen.
- Fachbegriffe beim ersten Auftreten erklären, mit Herkunft (Literatur, Prüfliste,
  Exposé, eigene Setzung) und Zweck für die Arbeit.
- Zahlenwerte (Schwellen, Parameter) immer mit Status: „endgültig“ oder „vorläufig“.
- Keine Kausalaussagen. Das Dashboard zeigt „auffällige Veränderungen“, keine Ursachen.
- Belege als Pfad zu Datei, Test oder Commit.
- Datei im selben Commit wie das Feature anlegen oder aktualisieren.

## Übersicht

| Nr. | Feature | Inkrement | Anforderungen | Status |
|---|---|---|---|---|
| 01 | [Anomalien im Verlauf](01-anomalien-im-verlauf.md) | 1 | FA-01 bis FA-04, Zähler aus FA-26 | abgeschlossen; Parameter vorläufig (E9) |
| 02 | [Drill-down und Vorher-Nachher-Vergleich](02-drilldown-und-vergleich.md) | 2 | Drill-down, Vergleich, Quelle und Status | umgesetzt; Fenster und Schwellen vorläufig (E10–E13) |
| 03 | [Auffällige Einzelmonate](03-auffaellige-einzelmonate.md) | 2 (Nachtrag) | Markierung einzelner auffälliger Monate | umgesetzt; Schwellen vorläufig (E14) |
| 04 | [Aktienkurs und Kennzahlen](04-kurs-und-kennzahlen.md) | 3 | Kurs und Kennzahlen als Einordnung (FA-15); Kurs auch auf der Anomalien-Seite einblendbar (TF4) | umgesetzt; vorläufig (E15, Nutzungsbedingungen offen) |
| 05 | [Aktien-Dashboard](05-aktien-dashboard.md) | 3 (Nachtrag) | Kursverlauf, Analystenempfehlungen, Umsatz und Gewinn, Nachrichten; Anforderung nur für Kurs und Kennzahlen (FA-15) | umgesetzt; vorläufig (E16); Zusatzkarten ausblendbar (`VITE_SHOW_FINANCE_EXTRAS`) |
| 06 | [Freier Drill-down](06-freier-drilldown.md) | 2 (Nachtrag) | Bewertungen und Vergleich für jeden Zeitraum, auch ohne Anomalie | umgesetzt; vorläufig (E17) |
| 07 | [Externe Belege im Ereignisfenster](07-externe-belege.md) | 4 | zeitlich nahe Meldungen externer Quellen zu Veränderung, Einzelmonat und Auswahl; allgemeine Ereignisse als Hypothese | umgesetzt; vorläufig (E7, E18–E20) |
| 08 | [Erklärungsansätze: Mögliche Zusammenhänge](08-erklaerungsansaetze.md) | 5 | Rangfolge der Belege nach zeitlicher und thematischer Korrespondenz mit Stufe und sichtbarer Begründung; Sortierung und Filter der Belegliste; Auswertung gegen Vergleichsfenster | umgesetzt; Ereignisarten und Schwellen bestätigt und festgeschrieben (E21–E23); Iteration 2 (2026-10-08): Stufenregeln in zweiter Fassung, Bezeichnungen statt Ampel, oberste Liste je Ereignisart; alle Werte Setzungen |
