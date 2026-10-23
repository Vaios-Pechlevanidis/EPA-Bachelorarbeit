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
| 02 | [Drill-down und Vorher-Nachher-Vergleich](02-drilldown-und-vergleich.md) | 2 | Drill-down, Vergleich, Quelle und Status; seit 2026-10-22 Zahl der Bewertungen ohne Freitext je Fenster | umgesetzt; Fenster und Schwellen vorläufig (E10–E13) |
| 03 | [Auffällige Einzelmonate](03-auffaellige-einzelmonate.md) | 2 (Nachtrag) | Markierung einzelner auffälliger Monate | umgesetzt; Schwellen vorläufig (E14); seit 2026-10-13 als „ungeprüft“ gekennzeichnet (Zufallsniveau, E30) und per `VITE_SHOW_OUTLIER_MONTHS` ausblendbar |
| 04 | [Aktienkurs und Kennzahlen](04-kurs-und-kennzahlen.md) | 3 | Kurs und Kennzahlen als Einordnung (FA-15); Kurs auch auf der Anomalien-Seite einblendbar (TF4) | umgesetzt; vorläufig (E15, Nutzungsbedingungen offen) |
| 05 | [Aktien-Dashboard](05-aktien-dashboard.md) | 3 (Nachtrag) | Kursverlauf, Analystenempfehlungen, Umsatz und Gewinn, Nachrichten; Anforderung nur für Kurs und Kennzahlen (FA-15) | umgesetzt; vorläufig (E16); Zusatzkarten ausblendbar (`VITE_SHOW_FINANCE_EXTRAS`) |
| 06 | [Freier Drill-down](06-freier-drilldown.md) | 2 (Nachtrag) | Bewertungen und Vergleich für jeden Zeitraum, auch ohne Anomalie | umgesetzt; vorläufig (E17) |
| 07 | [Externe Berichte im Ereignisfenster](07-externe-belege.md) | 4 | zeitlich nahe Meldungen externer Quellen zu Veränderung, Einzelmonat und Auswahl; allgemeine Ereignisse als Hypothese | umgesetzt; vorläufig (E7, E18–E20) |
| 08 | [Erklärungsansätze: Mögliche Zusammenhänge](08-erklaerungsansaetze.md) | 5 | Rangfolge der Belege nach zeitlicher und thematischer Korrespondenz mit Stufe und sichtbarer Begründung; Sortierung und Filter der Belegliste; Auswertung gegen Vergleichsfenster | umgesetzt; Ereignisarten und Schwellen bestätigt und festgeschrieben (E21–E23); Iteration 2 (2026-10-08): Stufenregeln in zweiter Fassung, Bezeichnungen statt Ampel, oberste Liste je Ereignisart; alle Werte Setzungen |
| 09 | [PDF-Export des Dashboards](09-pdf-export.md) | 6 (Nachtrag) | keine eigene Anforderung; der Export übernimmt alle Elemente des Dashboards vollständig, darunter Datenstand (FA-37), n und Datenbasis (FA-25, FA-26), rollierende Schnitte (FA-08) und die Anomalien-Karte | umgesetzt (2026-10-09); Layout vorläufig, Export im hellen Theme geprüft; seit 2026-10-17 stehen alle technischen Angaben auf der letzten Seite „Technische Hinweise“ |
| 10 | [Transparenz und Datenstand](10-transparenz-und-datenstand.md) | 6 | FA-08, FA-25, FA-26, FA-37, FA-38, NFA-07: rollierende Schnitte, Datenbasis und n, Datenstand, Ø Score als Mittel der Gesamtnote mit Hinweistext, Prognose-Schalter, Beispielzitate ohne Beschreibungsfelder, Bezeichnung der Erklärungsansätze nach Signalen | umgesetzt (2026-10-09); Schwelle der kleinen Basis vorläufig (T5); Beschreibungsfelder in der Einzelbewertung offen |
| 11 | [Prognose im Zeitverlauf erklären](11-prognose-erklaeren.md) | 6 (Nachtrag) | keine eigene Anforderung; „?“ mit Erklärung der Holt-Prognose, geglättetes Niveau und Ø Historisch im Detailfenster, Trend-Kachel nach Steigung | umgesetzt (2026-10-13), committet |
| 12 | [Verteilung der Bewertungen im Topic-Detail](12-verteilung-der-topic-bewertungen.md) | Korrektur (2026-10-13) | keine eigene Anforderung; ersetzt die aus dem Durchschnitt abgeleiteten festen Anteile (z. B. 15/15/70) durch gezählte Anteile mit n | umgesetzt (2026-10-13), committet; Schwellen 2,5/3,5 vorläufig |
| 13 | [Vorschau-Karten auf der Anomalien-Seite](13-vorschau-karten-anomalien.md) | Korrektur der Darstellung (2026-10-16) | keine eigene Anforderung; Vergleich, Bewertungen, Erklärungsansätze und externe Berichte als vier Karten mit je einer Kennzahl und einem kleinen Diagramm, Klick öffnet die volle Ansicht im Dialog (wie im Haupt-Dashboard) | umgesetzt (2026-10-16), nicht committet; Zahl der gezeigten Themen und Ansätze vorläufig |
| 14 | [Kurzbericht im PDF-Export](14-kurzbericht-pdf.md) | Nachtrag zum PDF-Export (2026-10-17) | keine eigene Anforderung; Wunsch des Autors: Seite „Kurzbericht“ nach dem Cover mit Lage der Bewertung, den jüngsten auffälligen Veränderungen samt Folge für das Niveau und zwei Spalten „Was gut läuft“ / „Was verbessert werden sollte“ nach festen Regeln | umgesetzt (2026-10-17), nicht committet; Regeln und Schwellen vorläufig |
| 15 | [Eigene Ereignisse im Monatsverlauf](15-eigene-ereignisse.md) | Ergänzung der Detailseite (2026-10-17) | keine eigene Anforderung; Wunsch des Autors: Nutzerinnen und Nutzer tragen Zeiträume mit Titel und Vermerk ein, nummerierte Marken im Verlauf, Reiter „Eigene Ereignisse“ mit Ändern und Löschen, Klick wählt den Zeitraum; keine Aussage über Ursachen, kein Eingang in Erkennung oder Rangfolge (E32); seit 2026-10-22 bei den Erklärungsansätzen, in der Vorschau-Karte, im PDF und im Kurzbericht als „Eigenes Ereignis im Ereignisfenster · möglicher Zusammenhang“ (Meta-Requirement 3) | umgesetzt (2026-10-17, Nachtrag 2026-10-22), nicht committet; Migration 007 vom Autor auszuführen; Feldgrenzen vorläufig |
| 16 | [Qualität des Analytics Reports: Befund und Korrekturen](16-report-qualitaet.md) | Prüfung (2026-10-17) | Prüfauftrag des Autors: Kennzahlen, Zeitreihe, Prognose, Topics, Unsicherheit, Zusammenfassung; Befund B1–B15, Korrekturen (Intervalle, Stabilität, Backtest mit Bandbreite, Einstufung statt Sentiment, Nenner, Duplikate, Kurzbericht mit Datenstand, Warnungen und nächsten Schritten) | umgesetzt (2026-10-17), nicht committet; Entscheidungen zu Prognose, Duplikaten und Dashboard-Anzeige offen |
| 17 | [Themen, Themenfilter und Sortierung in „Bewertungen des Zeitraums“](17-themen-in-der-bewertungsliste.md) | Ergänzung der Detailseite (2026-10-18) | keine eigene Anforderung; Wunsch des Autors: Schlüsselwort-Themen je Bewertung als Marken, Auswahlfeld „Alle Themen“ mit Zahl je Thema (ersetzt das Kästchen „nur Bewertungen, die … nennen“), Sortierung „neueste / älteste zuerst“ nach dem Datum der Bewertung | umgesetzt (2026-10-18), nicht committet; keine neuen Parameter |
| 19 | [Branche im Firmenvergleich: Vorschlag „gleiche Branche“](19-branchenvorschlag-vergleich.md) | Ergänzung des Firmenvergleichs (2026-10-22) | Meta-Requirement 4 der Arbeit (Vergleich mit strukturell ähnlichen Organisationen, H4.8); Branche und Vergleichsgruppe unter der gewählten Firma, Vorschlagsmarken „gleiche Branche“ mit Klick in den Vergleich, Branchenmarke und Branchensuche im Firmen-Suchfeld | umgesetzt (2026-10-22), nicht committet; keine Parameter |
| 18 | [Strenge Auswahl der Berichte für die Erklärungsansätze](18-strenge-artikelauswahl.md) | Korrektur der Erklärungsansätze (2026-10-18) | keine eigene Anforderung; Wunsch des Autors: nur passende Meldungen in „Mögliche Zusammenhänge“; vier Ausschlussregeln je Meldung (Unternehmen im Titel, Arbeitgeberbezug, Wortbezug oder Themenverschiebung, zeitliche Nähe) vor Bündelung und Rangfolge; ausgeschlossene Meldungen mit nicht erfüllter Regel in der Belegliste (E33) | umgesetzt (2026-10-18), nicht committet; Regeln und Werte Setzungen; `title_words` vom Autor zu bestätigen |
| 20 | [Dimension als globaler Filter der Detailseite](20-dimension-als-globaler-filter.md) | Ergänzung der Detailseite (2026-10-23) | keine eigene Anforderung; Wunsch des Autors: die im Kopf gewählte Dimension gilt für alle Karten der Seite; „Bewertungen des Zeitraums“ nur mit Bewertungen, die zur Dimension gehören (Kommentar zur Kategorie oder Schlüsselwort des Themas), je Zeile Sterne der Dimension und Kommentar; „Externe Berichte“ nur mit Meldungen mit Schlüsselwort im Titel oder zugeordneter Ereignisart; Zählung vor und nach dem Filter; Zurück zum Dashboard nimmt die Auswahl mit (E34) | umgesetzt (2026-10-23), nicht committet; Regeln Setzungen (vorläufig) |
