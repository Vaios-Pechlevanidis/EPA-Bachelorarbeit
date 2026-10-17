# 15 – Eigene Ereignisse im Monatsverlauf

| | |
|---|---|
| Inkrement | Ergänzung der Detailseite „Anomalien im Verlauf“ (2026-10-17) |
| Anforderungen | keine eigene Anforderung aus der Prüfliste; Wunsch des Autors (2026-10-17): Nutzerinnen und Nutzer sollen eigene Ereignisse im Anomalien-Diagramm eintragen können |
| Entscheidungen | E32 in `docs/entscheidungen.md` |
| Status | umgesetzt (2026-10-17), nicht committet; Migration `backend/migrations/007_create_user_events.sql` ist vom Autor in der Datenbank auszuführen; Feldgrenzen **vorläufig** |
| Stand | 2026-10-17 |

## 1. Vorstellung

Auf der Detailseite **„Anomalien im Verlauf“** (`/anomalies`) steht im Kopf des Monatsverlaufs
links neben dem Kästchen „Allgemeine Ereignisse“ der Knopf **„Ereignis eintragen“**. Er öffnet
ein Formular mit vier Feldern: **Titel** (Pflicht, z. B. „Führungswechsel“), **von** und **bis**
(Monatsraster wie in der Drill-down-Leiste, mit der Zahl der Bewertungen je Monat) und ein
optionaler **Vermerk** (Quelle, Stichworte). Ist gerade ein Zeitraum ausgewählt oder eine
auffällige Veränderung markiert, sind „von“ und „bis“ damit vorbelegt. „Eintragen“ speichert;
danach ist der Zeitraum des neuen Ereignisses als Auswahl gesetzt, sodass darunter sofort der
Vergleich mit dem Zeitraum davor, die Bewertungen und die externen Berichte dieser Monate stehen.

Im Diagramm erscheint jedes eigene Ereignis als **nummerierte Marke** in Violett: ein Kreis mit
der Nummer am oberen Rand und eine senkrechte Linie am Startmonat; umfasst das Ereignis mehrere
Monate, ist der Zeitraum zusätzlich schwach violett getönt. Fährt die Maus über einen Monat im
Zeitraum, nennt der Tooltip unter „Eigenes Ereignis“ Nummer, Titel, Zeitraum und Vermerk (bei
langen Vermerken die ersten 140 Zeichen) mit dem Zusatz „Eingetragen von Nutzenden; keine
Aussage über Ursachen“. Ein **Klick auf die Marke** wählt den Zeitraum des Ereignisses als
freie Auswahl, genau wie ein Klick auf eine Stufe, eine Raute oder einen Monat. Die Legende
unter dem Diagramm erklärt das Symbol und nennt die Zahl der Marken im Ausschnitt.

Die Karte **„Markierungen“** rechts neben dem Verlauf hat einen dritten Reiter **„Eigene
Ereignisse (n)“** neben „Veränderungen“ und „Einzelmonate“ (`?liste=ereignisse`). Er listet die
Ereignisse nach Beginn mit Nummer, Titel, Zeitraum und Vermerk; ein Klick auf die Zeile wählt
den Zeitraum, der Stift öffnet das Formular zum Ändern, der **Papierkorb** fragt direkt in der
Zeile nach („Wirklich löschen? Ja, löschen / Nein“) und löscht; war der Zeitraum des Ereignisses
gerade ausgewählt, wird die Auswahl aufgehoben. Löschen steht zusätzlich im Formular. Unter der
Liste stehen ein zweiter Knopf „Ereignis eintragen“ und der feste Hinweis:

> Eigene Ereignisse sind von Nutzerinnen und Nutzern eingetragene Zeiträume zur Einordnung. Sie
> sind keine Aussage über Ursachen und gehen nicht in Erkennung, Erklärungsansätze oder Belege ein.

Die Ereignisse gelten je **Unternehmen** und sind für alle sichtbar, die das Dashboard
benutzen; sie bleiben beim Neuladen, beim Wechsel der Dimension, Quelle oder Bewertendengruppe
und auf anderen Geräten erhalten. Die Karte „Anomalien im Verlauf“ im Haupt-Dashboard und der
PDF-Export zeigen sie nicht (Abschnitt 4).

Nutzen: Externe Berichte ([07](07-externe-belege.md)) und allgemeine Ereignisse (E29) kommen
automatisch von außen; was im Unternehmen selbst geschah (Führungswechsel, Umstrukturierung,
Standortschließung, Tarifabschluss), ist von außen oft nicht sichtbar. Wer das Unternehmen
kennt, kann es hier festhalten und sieht die Markierungen der Erkennung und die eigenen
Ereignisse im selben Bild – ohne dass das Dashboard daraus eine Ursache macht.

## 2. Erklärung

1. **Speicherung.** Tabelle `user_events` (Migration
   `backend/migrations/007_create_user_events.sql`): `id`, `company_id` (Fremdschlüssel auf
   `companies`, löscht mit), `date_from` und `date_to` als „JJJJ-MM“, `title`, `note`,
   `created_at`, `updated_at`. Prüfregeln liegen auch in der Datenbank: Monatsformat, `date_to ≥
   date_from`, Titel 1 bis 120 Zeichen, Vermerk bis 1000 Zeichen. Zugriff wie bei den übrigen
   Tabellen (Migration 005): `anon` liest, `service_role` schreibt. Ohne Zugangsdaten nutzt der
   In-Memory-Store dieselbe Schnittstelle; dafür entfernt sein `delete` seit 2026-10-17 die
   gefilterten Zeilen wirklich (vorher ein No-op), damit Löschen auch in der Entwicklung und in
   den Tests wirkt.
2. **Schnittstelle.** `GET /api/companies/{id}/events` liefert `{company_id, events, note}`, die
   Ereignisse nach Beginn sortiert, jedes mit `months` (Zahl der Monate). `POST …/events` legt
   an (201), `PUT …/events/{eventId}` ändert alle Felder, `DELETE …/events/{eventId}` löscht.
   Die Prüfung der Eingabe steht in `backend/services/user_events_service.py`
   (`normalize_event`): Titel getrimmt und nicht leer, Monate im Format „JJJJ-MM“, fehlendes
   „bis“ gleich „von“, „bis“ nicht vor „von“ (Fehler, kein stilles Vertauschen), leerer Vermerk
   als `null`. Eingabefehler sind 400 mit deutscher Meldung, unbekanntes Unternehmen oder
   Ereignis 404. Fehlt die Tabelle (Migration 007 nicht ausgeführt), antwortet jede Route mit
   503 und nennt die Migrationsdatei; die Liste im Dashboard zeigt diese Meldung.
3. **Laden und Ändern im Dashboard.** `useUserEvents(companyId)`
   (`frontend/src/hooks/useUserEvents.js`) lädt die Liste einmal je Unternehmen und schreibt
   sie nach jedem Anlegen, Ändern oder Löschen lokal fort, sortiert nach Beginn, Ende, Kennung
   (`lib/userEvents.js`). Die Seite vergibt die **Nummer** als Position in dieser Liste; Liste,
   Marke und Tooltip zeigen dieselbe Nummer.
4. **Formular.** `UserEventDialog` (`components/dashboard/UserEvents.jsx`) prüft vor dem
   Senden mit denselben Regeln wie das Backend (`validateUserEventInput`); Fehlermeldungen des
   Backends erscheinen im Dialog. „von“ und „bis“ nutzen das Monatsraster der Drill-down-Leiste
   (`MonthPicker`, seit 2026-10-17 exportiert) mit den Monaten der Reihe; wählt man „von“ hinter
   „bis“, rückt „bis“ mit (und umgekehrt), sodass die Reihenfolge nie falsch sein kann. Das
   Formular wird bei jedem Öffnen neu aufgebaut, sein Zustand ist also immer frisch.
5. **Marken im Diagramm.** `AnomalyChart` erhält `userEvents` und berechnet je Ereignis den
   Start- und Endmonat im sichtbaren Ausschnitt (auf den Ausschnitt begrenzt wie bei den
   allgemeinen Ereignissen). Jede Marke ist eine `ReferenceLine` am Startmonat mit eigener Form
   (`userEventShape`): Linie vom oberen Rand bis zur Achse, Kreis mit Nummer oben; mehrere
   Ereignisse mit demselben Startmonat rücken ihre Kreise untereinander. Mehrmonatige Ereignisse
   bekommen zusätzlich eine `ReferenceArea` (Tönung 7 %, bei ausgewähltem Ereignis 14 %). Maus-
   Ereignisse auf der Marke werden nicht an das Diagramm weitergereicht, damit ein Klick nicht
   zugleich die freie Auswahl per Ziehen startet. Die kompakte Karte (`compact`) zeichnet keine
   Marken. Farbe: Token `--user-event` (hell Purple-700 `#7e22ce`, dunkel Purple-400 `#c084fc`,
   `index.css`); im Tooltip, dessen Hintergrund im dunklen Theme hell wird, wird der violette
   Titel wie der bernsteinfarbene abgedunkelt.
6. **Auswahl.** Klick auf Marke oder Zeile setzt `?from=&to=` auf den Zeitraum des Ereignisses
   und `?liste=ereignisse`, sodass die Zeile hervorgehoben ist; alles Weitere (Vergleich,
   Bewertungen, Erklärungsansätze, externe Berichte) ist die freie Auswahl aus
   [06](06-freier-drilldown.md). Der Zeitfilter wirkt wie bei den anderen Listen: Ereignisse
   außerhalb des Ausschnitts stehen nicht in der Liste, ihre Zahl wird genannt.

Parameter (alle **vorläufig**, Setzungen): Titel höchstens 120 Zeichen, Vermerk höchstens 1000
Zeichen, Tooltip zeigt höchstens 140 Zeichen des Vermerks, keine Obergrenze für die Dauer.

## 3. Begründung

- **Eigene Ereignisse als dritte Quelle neben Belegen und allgemeinen Ereignissen.** Der feste
  Hinweis der Belege sagt, dass interne Auslöser von außen nicht sichtbar sind (E18). Die
  Interviewpartner (DZ3) kennen ihr Unternehmen; ein Feld, in dem sie ihr Wissen festhalten,
  macht das Bild vollständiger, ohne dass das Dashboard etwas behauptet, was es nicht wissen kann.
- **Je Unternehmen in der Datenbank, nicht im Browser.** Das Dashboard hat keine Anmeldung;
  Einträge gehören zum Unternehmen, nicht zu einer Person. Eine Speicherung im Browser
  (`localStorage`, wie beim Import-Verlauf) wäre einfacher gewesen, ginge aber beim Wechsel des
  Geräts oder Löschen der Browserdaten verloren und wäre in den Interviews auf dem Rechner des
  Autors nicht von den Teilnehmenden mitzunehmen. Die Tabelle folgt dem Muster der Migrationen
  001–006; der In-Memory-Store deckt Entwicklung und Tests ohne Zugangsdaten ab.
- **Monatsgenau.** Der Verlauf ist ein Monatsmittel; ein tagesgenaues Datum würde eine
  Genauigkeit vortäuschen, die der Verlauf nicht hat. Dieselbe Setzung gilt für die allgemeinen
  Ereignisse (E20, E29) und das Ereignisfenster (E18).
- **Keine Aussage über Ursachen, kein Eingang in Erkennung und Erklärungsansätze.** Die Regel
  des Dashboards (Feature-Doku-README) gilt auch hier. Ein eigenes Ereignis ist die Hypothese
  der Nutzenden; ginge es in die Rangfolge der Erklärungsansätze ein, wäre die Auswertung E23
  nicht mehr interpretierbar, und die Erkennung (E9) bliebe nicht datengetrieben.
- **Nummerierte Marke statt Beschriftung im Diagramm.** Titel am Diagramm überlappen bei nahen
  Ereignissen; eine Nummer verbindet Diagramm und Liste eindeutig, der Tooltip liefert den Titel
  – dasselbe Muster wie bei den allgemeinen Ereignissen seit 2026-10-13 (Name beim Überfahren).
- **Klick wählt den Zeitraum, der Stift ändert.** Im Diagramm wählt jeder Klick einen Zeitraum
  (Stufe, Raute, Monat, Ziehen; E17). Eine Marke verhält sich gleich; Ändern und Löschen liegen in
  der Liste, wo auch der Vermerk vollständig steht.
- **Violett.** Rose und Smaragd stehen für die Richtung, Bernstein für Hypothese und Auswahl,
  Orange für den Kurs, Blau für die Reihe. Violett ist frei und in beiden Themes von der Reihe
  unterscheidbar.
- **Keine Dauergrenze.** Die Grenze von sechs Monaten für allgemeine Ereignisse (E20) schützt vor
  Hypothesen, die an jeder Markierung hängen. Ein eigenes Ereignis trägt jemand bewusst ein und
  kennt seine Dauer; eine lange Fläche ist dann eine gewollte Aussage.

## 4. Grenzen

- Keine Anmeldung, keine Zuordnung zu Personen, keine Änderungshistorie: Wer das Dashboard
  benutzt, sieht und ändert die Einträge aller. Für die Evaluationsinstanz heißt das: Einträge
  der Interviewpartner bleiben dort stehen, bis sie gelöscht werden.
- Die Marken stehen nur auf der Detailseite. Die Karte im Haupt-Dashboard, das Aktien-Dashboard
  und der PDF-Export (09) zeigen keine eigenen Ereignisse; die Belegliste (07) und die
  Erklärungsansätze (08) kennen sie nicht.
- Ereignisse außerhalb des angezeigten Bereichs (erster bis letzter bewerteter Monat) stehen nur
  in der Liste; im Formular sind nur Monate der Reihe wählbar.
- Ohne Migration 007 antwortet das Backend mit 503; der Reiter zeigt die Meldung, das Übrige der
  Seite ist nicht betroffen.
- Ein eigenes Ereignis im selben Monat wie eine Markierung ist ein zeitliches Zusammentreffen,
  keine Erklärung.

## 5. Prüfung und Belege

- Tests: `backend/tests/test_user_events.py` (29 Tests: Prüfung der Eingabe, Routen GET/POST/PUT/
  DELETE gegen den In-Memory-Store, Trennung nach Unternehmen, 404, 503 mit Hinweis auf die
  Migration, Löschen im In-Memory-Store, Inhalt der Migrationsdatei). Gesamte Backend-Suite nach
  der Änderung des In-Memory-`delete` ohne Fehler (2026-10-17).
- Lint des Frontends ohne Fehler und Warnungen (2026-10-17).
- Browser (2026-10-17, In-Memory-Store ohne Zugangsdaten, Demo 1, dunkles und helles Theme):
  „Ereignis eintragen“ → Formular mit Vorbelegung „Apr. 2025“ (letzter Monat der Reihe); Titel
  „Führungswechsel“, von Juni 2023 (Jahr über die Pfeile, Monat im Raster mit Bewertungszahl),
  bis Aug. 2023, Vermerk; „Eintragen“ speichert (POST 201), die Seite setzt
  `?from=2023-06&to=2023-08&liste=ereignisse`, die Marke 1 steht mit Linie und getöntem
  Zeitraum im Verlauf, die Legende nennt „Eigenes Ereignis (1; …)“, der Reiter „Eigene
  Ereignisse (1)“ zeigt die Zeile mit Nummer, Titel, Zeitraum und Vermerk, darunter stehen
  Vergleich, Bewertungen, Erklärungsansätze und externe Berichte der Auswahl. Tooltip über
  Juli 2023: „Eigenes Ereignis · 1. Führungswechsel (Juni 2023 – Aug. 2023)“ mit Vermerk und
  Hinweis. Stift → Titel geändert → „Änderungen speichern“ (PUT), Zeile und Marke aktualisiert.
  Zweites Ereignis (ein Monat, Jan. 2024, per API angelegt): Marke 2 nur mit Linie; Klick auf
  die Marke setzt `?from=2024-01&to=2024-01&liste=ereignisse`, ohne dass die freie Auswahl per
  Ziehen anspringt. Stift → „Löschen“ → Rückfrage „Wirklich löschen?“ → „Ja, löschen“
  (DELETE): nur Ereignis 1 bleibt. `GET /api/companies/1/events` liefert die Einträge mit
  `months`; leerer Titel → 400 „Bitte einen Titel angeben.“, unbekanntes Unternehmen → 404.
  Keine Konsolenfehler; Produktions-Build ohne Fehler.
- Papierkorb in der Zeile (zweiter Durchgang, 2026-10-17): Papierkorb der ausgewählten Zeile
  → Rückfrage in der Zeile, Stift und Papierkorb der Zeile ausgeblendet, die andere Zeile
  unverändert; „Nein“ stellt die Zeile wieder her; „Ja, löschen“ entfernt die Zeile (DELETE),
  die Auswahl `?from=&to=` wird aufgehoben, der Zähler im Reiter sinkt.

## 6. Offene Punkte

- Migration 007 in der gehosteten Datenbank ausführen (Autor); bis dahin zeigt der Reiter die
  503-Meldung.
- Ob eigene Ereignisse als Belegtyp in der Belegliste und als Signal der Erklärungsansätze
  erscheinen sollen (E32: vorerst nicht, damit E23 unberührt bleibt).
- Ob der PDF-Export die Marken und die Liste übernehmen soll.
- Feldgrenzen (120 / 1000 Zeichen) und die 140 Zeichen im Tooltip sind Setzungen.
