# 19 – Branche im Firmenvergleich: Vorschlag „gleiche Branche“

| | |
|---|---|
| Inkrement | Ergänzung des Firmenvergleichs (2026-10-22) |
| Anforderungen | Meta-Requirement 4 der Arbeit (Vergleich mit strukturell ähnlichen Organisationen, Interviewkategorie H4.8); keine FA-Nummer |
| Entscheidungen | E6 (Branche laut Kununu, Nachtrag 2026-10-22) in `docs/entscheidungen.md` |
| Status | umgesetzt, nicht committet; keine Parameter |
| Stand | 2026-10-22 |

## 1. Vorstellung

Auf der Seite „Firmen vergleichen“ (`/compare`) steht unter jeder gewählten Firma ihre
Branche und Vergleichsgruppe, etwa „Energie · Nicht börsennotiert“. Sobald eine Firma gewählt
ist, erscheint unter der Auswahl die Zeile „Gleiche Branche wie <Firma> (<Branche>, laut
Kununu-Profil)“ mit einer Marke je weiterer Firma dieser Branche, jeweils mit der Zahl ihrer
Bewertungen. Ein Klick nimmt die Firma in den ersten freien Platz auf oder legt einen neuen
Platz an; bei drei besetzten Plätzen sind die Marken gesperrt (Hinweis: erst eine Firma
entfernen). Gibt es keine weitere Firma der Branche, steht das dort. Darunter steht immer:
„Vorschlag nach Branche; ob die Firmen vergleichbar sind, zeigt die Branche nicht.“

Im Suchfeld der Firmenauswahl (alle Seiten) trägt jede Firma zusätzlich ihre Branche als
kleine Marke; die Suche findet jetzt auch Branchen, „Energie“ listet also alle Energie-Firmen.

Nutzen: Die Befragten wollen Veränderungen gegen „strukturell ähnliche“ Organisationen
einordnen, um organisationsspezifische von allgemeinen Entwicklungen zu unterscheiden. Bisher
musste man die passenden Firmen kennen; jetzt schlägt das System sie vor.

## 2. Erklärung

1. `GET /companies` liefert je Firma `sector` (Branche laut Kununu-Profil, E6) und
   `peer_group` (Börsennotiert DE / Börsennotiert Ausland / Nicht börsennotiert / Demo) aus
   Migration 006. Die Vergleichsseite lädt diese Liste einmal (`lib/companies.js`, dieselbe
   Liste wie das Suchfeld, fünf Minuten im Speicher).
2. **Bezugsfirma** ist die erste besetzte Stelle („Firma 1“, sonst die nächste besetzte).
3. `sameSectorCompanies(liste, bezug, gewählteIds)` liefert alle Firmen mit derselben
   Branche (Textvergleich nach Trimmen, Groß-/Kleinschreibung unverändert), ohne die Bezugsfirma
   und ohne bereits gewählte Firmen, sortiert nach Zahl der Bewertungen absteigend, bei
   Gleichstand nach Name. Ohne Branche (leer oder fehlend): keine Vorschläge, und die Zeile sagt
   das.
4. Klick auf eine Marke: erster Platz ohne Firma, sonst neuer Platz (höchstens drei, wie
   bisher); Farbe wie beim Knopf „Firma hinzufügen“. Danach rechnet die Seite wie bei jeder
   Auswahl.

Keine Schwelle, kein Gewicht: Die Branche entscheidet nur, wer vorgeschlagen wird. Die
Vergleichsgruppe (`peer_group`) wird nur angezeigt, nicht als Filter genutzt.

## 3. Begründung

- **Warum Branche:** Die Interviews nennen als Bezug „strukturell ähnliche Organisationen“,
  etwa Einrichtungen im selben Bundesland (H4.8, ein Beleg). Von den gespeicherten Merkmalen
  ist die Branche das einzige, das diese Ähnlichkeit annähert; Bundesland, Größe oder
  Rechtsform liegen nicht vor. Die Branche stammt vom Kununu-Profil (E6), also aus derselben
  Quelle wie die Bewertungen, und ist für die Befragten unmittelbar nachvollziehbar.
- **Warum Vorschlag statt Filter:** Die freie Auswahl bleibt vollständig erhalten; die
  Befragten haben eigene Vorstellungen davon, wer vergleichbar ist. Ein Filter hätte die
  Auswahl auf höchstens sechs Firmen (IT) beschränkt, bei vier Branchen auf eine einzige.
- **Warum der Hinweissatz:** Branchengleichheit ist eine grobe Annäherung; Kununu ordnet etwa
  das KIT und Carl Zeiss derselben Branche zu (E6). Der Vergleich darf nicht als Beleg für
  „vergleichbar“ gelesen werden; das entspricht der Linie der Arbeit, keine Ursachen und
  keine Gleichheit zu unterstellen.
- **Warum Bezugsfirma = Firma 1:** Die Seite wird in der Regel vom Dashboard einer Firma aus
  geöffnet (`location.state.companies`); diese Firma steht dann an erster Stelle und ist der
  natürliche Bezug.

## 4. Grenzen

- Zehn Branchen bei 26 Unternehmen: Beratung/Consulting, Maschinenbau, Medizin/Pharma und
  Chemie haben je eine Firma; dort gibt es keinen Vorschlag.
- Die Branche sagt nichts über Größe, Region, Tarifbindung oder Bewertungszahl; die
  Vorschläge sind nach Bewertungszahl sortiert, damit große Vergleichsbasen oben stehen, mehr
  nicht.
- Kein Branchenmittel als Bezugslinie: Mit ein bis sechs Firmen je Branche wäre ein Mittel
  nicht belastbar und würde einzelne Firmen überdecken. Das bleibt ein offener Punkt.
- Demo-Firmen tragen die Branche „Demo“ und schlagen sich gegenseitig vor.

## 5. Prüfung und Belege

| Was | Beleg |
|---|---|
| Auswahl und Sortierung | `frontend/src/lib/__tests__/companies.test.js`: gleiche Branche ohne Bezugsfirma, Ausschluss gewählter Firmen, Sortierung nach Bewertungen und Name, leer ohne Branche oder ohne zweite Firma |
| Lint | `npx eslint src` ohne Befund |
| Browser (2026-10-22, In-Memory-Backend, Demo 1–3) | Suchfeld mit Branchenmarke „Demo“; nach Wahl von Demo 1 zeigt die Zeile „Gleiche Branche wie Demo 1 (Demo, laut Kununu-Profil)“ mit Demo 2 und Demo 3; Klick auf Demo 2 besetzt Platz 2 und der Vergleich lädt; danach nur noch Demo 3 als Marke; Klick auf Demo 3 legt Platz 3 an; danach „keine weitere Firma dieser Branche im Datensatz“; Konsole ohne Fehler |
| PDF-Export | unverändert; die Branche steht nicht im Export |

## 6. Offene Punkte

- Soll die Branche auch im PDF-Export des Vergleichs stehen (Zeile unter den Firmennamen)?
- Branchenmittel als Bezugslinie im Zeitverlauf: erst sinnvoll, wenn eine Branche deutlich mehr
  Firmen enthält.
- Ob die Vergleichsgruppe (börsennotiert / nicht börsennotiert) als zweites Vorschlagskriterium
  dienen soll, ist offen; derzeit nur angezeigt.
