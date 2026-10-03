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
