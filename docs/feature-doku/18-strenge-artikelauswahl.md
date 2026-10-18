# 18 – Strenge Auswahl der Berichte für die Erklärungsansätze

| | |
|---|---|
| Inkrement | Korrektur der Erklärungsansätze (2026-10-18) |
| Anforderungen | keine eigene Anforderung; Wunsch des Autors: In „Mögliche Zusammenhänge“ sollen nur passende Meldungen stehen, das Auswahlverfahren soll streng sein; baut auf TF4 (Erklärungsansätze) und NFA-05 (Abdeckungsquote) |
| Entscheidungen | E33 (strenge Auswahl, vier Regeln) in `docs/entscheidungen.md`; baut auf E18, E21–E23 |
| Status | umgesetzt (2026-10-18), nicht committet; die vier Regeln vom Autor am 2026-10-18 bestätigt („keine weitere Verschärfung“); Werte (zwei Zeichen Genitiv, zeitliche Nähe 0,5, Liste der allgemeinen Wörter) bleiben Setzungen; zusätzliche Kennung „CGM“ für Compugroup vom Autor zu bestätigen |
| Stand | 2026-10-18 |

## 1. Vorstellung

Die Karte **„Mögliche Zusammenhänge“** auf der Seite „Anomalien im Verlauf“ (`/anomalies`,
[08](08-erklaerungsansaetze.md)) zeigt seit dem 2026-10-18 nur noch Meldungen, die **vier
Auswahlregeln** erfüllen. Eine Meldung wird nur dann zum Erklärungsansatz, wenn

1. ihr **Titel das Unternehmen nennt** (EQS-Mitteilungen des Emittenten gelten als genannt),
2. sie **Arbeitgeberbezug** hat (Börsenberichte, Kursziele, Sport- und Produktmeldungen bleiben
   draußen, statt nur eine Stufe tiefer zu stehen),
3. sie **thematisch zu den Bewertungen passt**: ein kennzeichnender Begriff der Bewertungen steht im
   Titel (Wortbezug) oder die erkannte Ereignisart hat ein zugeordnetes Thema, das sich im
   Vorher-Nachher-Vergleich merklich verschiebt (Themenverschiebung); eine nur erkannte
   Ereignisart genügt nicht mehr,
4. sie **nahe am Übergang** liegt (zeitliche Nähe mindestens 0,5), also nicht am Rand des Fensters
   davor.

Was Nutzerinnen und Nutzer sehen:

- Auf der **Karte** steht neben der Zahl der Ansätze, wie viele Belege geeignet sind (SAP SE,
  Anstieg ab Juli 2024: „5 Ansätze · aus 362 Belege · 37 geeignet · 37 Bündel“). Erreicht keine
  Meldung die Auswahl, heißt es „Offen · 362 Belege im Ereignisfenster · keiner erfüllt die
  strengen Auswahlregeln“.
- Im **Dialog** stehen nur Einträge, die alle Regeln erfüllen; darunter eine Zeile wie „Strenge
  Auswahl: 37 von 362 Belegen erfüllen alle vier Regeln, 325 ausgeschlossen (Unternehmen im Titel
  nicht genannt 103, ohne Arbeitgeberbezug 111, kein Wortbezug und keine Themenverschiebung 99,
  zeitliche Nähe unter 0,5 12). Die Belegliste nennt je Meldung die nicht erfüllte Regel.“ Der
  aufklappbare Absatz **„Wie wird eingestuft?“** nennt die vier Regeln im Wortlaut.
- In der **Belegliste** („Externe Berichte im Ereignisfenster“, [07](07-externe-belege.md)) steht
  bei jeder ausgeschlossenen Meldung „nicht in den Ansätzen: ohne Arbeitgeberbezug“ (bzw. die
  andere nicht erfüllte Regel); ihr Signal-Kennzeichen bleibt sichtbar. Bei Sortierung nach
  Relevanz stehen ausgeschlossene Meldungen hinter allen Ansätzen.

Nutzen: Die Liste der möglichen Zusammenhänge enthält nur noch Meldungen, bei denen das
Unternehmen, der Arbeitgeberbezug und der Bezug zu den Bewertungen aus dem Titel selbst hervorgehen;
die vollständige Belegliste bleibt prüfbar, und jede Meldung sagt, warum sie nicht dabei ist.
Kein Eintrag behauptet eine Ursache.

## 2. Erklärung

1. **Signale wie bisher.** Je Beleg werden Wortbezug (`term_match`), Ereignisart
   (`category_match`) und zeitliche Nähe (`time_match`) berechnet und die Stufe nach den
   Stufenregeln der zweiten Fassung bestimmt ([08](08-erklaerungsansaetze.md), E21). Daran ändert
   sich nichts; auch die Schwellen bleiben (`tests/explanations/test_frozen_rules.py`).
2. **Vier Ausschlussregeln je Beleg** (`backend/services/explanation_ranking.py`,
   `exclusion_reason`, `SELECTION_VERSION` 1), geprüft in dieser Reihenfolge; die erste nicht
   erfüllte Regel wird als Text vermerkt:
   - **Unternehmen im Titel genannt** (`company_in_title`): Ein Wort des Titels gleicht einem
     Namenswort oder beginnt damit und ist höchstens zwei Zeichen länger („Telekoms“, nicht
     „Telekommunikation“). Namenswörter sind die Wortteile des Unternehmensnamens und des
     Suchbegriffs (`review_terms.company_terms`) ohne Stoppwörter und allgemeine Bewertungswörter
     („Deutsche“ bei Deutsche Telekom zählt nicht) und ohne allgemeine Beschreibungen
     (`GENERIC_NAME_WORDS`: Medical, Software, Semiconductor, Digital, Technology, Europe, Data,
     Institut, Universität, Group, …); diese zählen nur, wenn kein anderes Wort bleibt.
     Zusätzliche Kennungen je Unternehmen stehen in `backend/data/company_metadata.json` im Feld
     `title_words` (Vorschlag: „CGM“ für Compugroup Medical, weil Meldungen das Unternehmen oft
     nur so nennen). EQS-Mitteilungen (Quelltyp `adhoc`) stammen aus dem Feed des Emittenten und
     gelten als genannt. Ohne Namenswörter ist die Regel nicht prüfbar und schließt nicht aus.
   - **Arbeitgeberbezug**: Belege der Gruppe ohne Arbeitgeberbezug (E22: Börsenbericht,
     Kursziel, Sport, Produkt, Kapitalmarktmitteilungen von EQS) sind ausgeschlossen.
   - **Thematische Korrespondenz**: `term_match ≥ 0,5` (mindestens ein kennzeichnender Begriff im
     Titel) oder `category_match ≥ 1` (Ereignisart erkannt und ein zugeordnetes Thema um mindestens
     5 Prozentpunkte verschoben, ohne kleine Basis). `category_match` 0,5 (nur erkannt) genügt nicht.
     Der Wortbezug gilt in der strengen Auswahl nur in einer Richtung
     (`review_terms.match_terms(compound_only=True)`): Das Titelwort ist der Begriff selbst oder
     ein Wort, das mit ihm beginnt („Stellenabbauprogramm“ für „stellenabbau“); ein kürzeres
     Titelwort, mit dem der Begriff beginnt („Firmen“ für „firmenwagen“, „Arbeit“ für
     „arbeitsbedingungen“), zählt nicht mehr. Ohne strenge Auswahl bleibt die Regel aus E21
     (Wortanfang ab sechs Zeichen in beide Richtungen).
   - **Zeitliche Nähe** `time_match ≥ 0,5` (`SELECTION_MIN_TIME`): Monat vor dem Übergang, Übergang
     und markierter Monat (1), der zweite Monat davor (0,67) und der Monat danach (0,5) zählen; der
     Rand des Fensters davor (0,33) nicht.
3. **Folge für die Stufen.** Wer alle vier Regeln erfüllt, erreicht nach den Stufenregeln
   mindestens die Stufe mittel (Wortbezug oder Themenbezug); die Stufe niedrig (nur Ereignisart)
   kommt in den Ansätzen nicht mehr vor. Bündelung (gleiche Ereignisart, höchstens 3 Tage,
   ähnlicher Titel), Sortierung, Gruppierung je Ereignisart und die Obergrenze von fünf Einträgen
   gelten unverändert, aber nur für die ausgewählten Belege; eine ungenannte Meldung wird auch nicht
   mehr in ein Bündel mit einer genannten gezogen.
4. **Ausgeschlossene Belege bleiben sichtbar.** `item_scores` in `explanation_summary` nennt je
   Beleg `selected` (ja/nein) und `excluded` (die nicht erfüllte Regel als Text) und vergibt den Rang
   hinter allen Bündeln (geordnet nach eigener Stufe, Quellenart, Signalen, Datum). Die eigene Stufe
   und das Signal-Kennzeichen des Belegs bleiben in der Belegliste sichtbar, damit erkennbar ist,
   was die Meldung hat und was ihr fehlt. Zusätzlich nennt die Zusammenfassung `n_selected`,
   `n_excluded`, `n_excluded_by_reason` (je Regel) und `selection` (Regeln mit Werten und Wortlaut,
   auch unter `rules.selection`).
5. **Schnittstelle und Skripte.** `GET …/anomalies/{id}/explanations` und `GET …/compare` liefern
   die neuen Felder; die Schlüssel der Stufen und alle bisherigen Felder bleiben.
   `rank_evidence(strict=False)` rechnet die Fassung bis 2026-10-17; die Auswertung
   (`scripts/report_explanation_validity.py`) und der Bewertungsbogen (`scripts/rate_explanations.py
   bogen`) nutzen standardmäßig die strenge Auswahl und haben dafür `--no-strict`, damit die Läufe
   aus E23 und der Bogen vom 2026-10-17 reproduzierbar bleiben. Die JSON-Ausgabe der Auswertung
   nennt `strict` und je Fenster `n_selected` und `n_excluded`.
6. **Oberfläche.** `ExplanationPanel.jsx` (Karte, Dialog, „Wie wird eingestuft?“),
   `explanationText.js` (Untertitel, Satz zur Auswahl) und `EvidenceSection.jsx` (Vermerk je
   Beleg) lesen die neuen Felder; fehlen sie (ältere Antwort), zeigen sie die bisherigen Texte.

## 3. Begründung

- **Nennung im Titel als harte Regel:** Nach E18 bringt die Namenssuche bei großen und mehrdeutigen
  Namen fremde Treffer (Compugroup: eine Telekom-Meldung auf Stufe hoch; RWE: Fußballmeldungen).
  Bisher war „Unternehmen im Titel nicht genannt“ nur ein Hinweis (offener Punkt in E18/E21). Eine
  Meldung, deren Titel das Unternehmen nicht nennt, kann im Dashboard nicht als Zusammenhang zu
  diesem Unternehmen gelesen werden; sie bleibt in der Belegliste.
- **Ausschluss statt Rückstufung:** Börsenberichte, Spielberichte und Produktmeldungen sind die
  häufigsten Meldungen großer Unternehmen (E22) und sagen nichts über den Arbeitgeber; eine Stufe
  tiefer stand ein Kursziel trotzdem noch unter den Ansätzen.
- **Nur Ereignisart genügt nicht:** Die Auswertung E23 zeigte, dass Einträge der Stufe niedrig in
  Vergleichsfenstern ebenso häufig sind wie bei Markierungen (75 % gegen 74 %). Ein Schlüsselwort
  im Titel ohne Spur in den Bewertungen ist kein Bezug zu den Bewertungen. Verlangt wird deshalb der
  Wortbezug oder die Themenverschiebung, also eine Verbindung zum Text oder zu den Themen der
  Bewertenden.
- **Zeitliche Nähe 0,5:** Eine Meldung drei Monate vor dem Übergang (0,33) liegt am Rand des
  Fensters; sie bleibt in der Belegliste, trägt aber nicht als Ansatz.
- **Regeln vor der Bündelung, nicht danach:** Ein Bündel trägt die höchsten Signale seiner
  Meldungen; prüfte man erst das Bündel, könnte eine genannte Meldung eine ungenannte mitziehen.
- **Stufenregeln unverändert, lenient-Pfad behalten:** Die Schwellen und Stufen sind in E21/E23
  festgeschrieben und ausgewertet; die strenge Auswahl ist eine zusätzliche Schicht mit eigener
  Fassung (`SELECTION_VERSION`), damit die Läufe aus E23 und der Bogen vom 2026-10-17 mit
  `--no-strict` reproduzierbar bleiben und ein neuer Lauf die beiden Fassungen gegenüberstellt.
- **Nicht noch strenger (nur Stufe hoch):** Hoch verlangt Wortbezug, Ereignisart und zeitliche Nähe
  1 zugleich und trat in E23 in 2 von 28 Markierungsfenstern auf; die Karte wäre fast immer leer.
  Die Themenverschiebung ohne Wortbezug bleibt zugelassen, weil sie die Ereignisart mit der
  Verschiebung derselben Kategorie im Vergleich verbindet.
- **Wortbezug nur in einer Richtung:** Bei SAP SE (Anstieg ab 2024-07) stand „So wollen SAP, DHL
  und andere Firmen mehr Geflüchtete in Arbeit bringen“ mit „Wortbezug“ unter den Ansätzen, weil
  „Firmen“ den Begriff „firmenwagen“ und „Arbeit“ den Begriff „arbeitsbedingungen“ anfängt. Ein
  kürzeres, allgemeineres Titelwort ist kein Bezug zu dem, was die Bewertenden schreiben.
- **Allgemeine Wörter im Namen:** „Deutsche“, „Medical“ oder „Data“ allein würden jede Meldung
  passieren lassen; die Liste ist klein, im Code dokumentiert und greift nur, wenn ein anderes
  Namenswort bleibt.
- **Nicht erfüllte Regel statt Begründung:** Die Belegliste nennt die Regel, die fehlt, nicht
  eine Bewertung der Meldung; die Wortwahl kommt ohne Ursache-Wörter aus (Projektregel).

## 4. Grenzen

- **Nur Titel.** Nennt der Text, aber nicht der Titel das Unternehmen, ist die Meldung
  ausgeschlossen; Abkürzungen (CGM) und Spitznamen brauchen einen Eintrag in `title_words`.
- **Genitiv-Regel.** Zwei Zeichen mehr decken „Telekoms“ und „Bechtles“ ab, nicht Komposita ohne
  Bindestrich („Telekomtochter“); Bindestriche gelten als Wortgrenze.
- **EQS-Mitteilungen** gelten als genannt, auch wenn sie von einer Konzerngesellschaft stammen
  (Carl Zeiss: Carl Zeiss Meditec AG, E19); die Belegliste nennt den Emittenten.
- **Weniger Ansätze.** Die Abdeckungsquote nach NFA-05 (Anteil der Markierungen mit Ansatz) sinkt
  gegenüber E23 von 82 % auf 50 % (Lauf in Abschnitt 5); Cancom und Carl Zeiss haben keinen Ansatz
  mehr, die Einzelmonate fast keinen. Bei kleiner Basis (ein Fenster unter
  10 Bewertungen) gibt es keine Begriffe; dann bleibt nur die Themenverschiebung als Weg in die
  Auswahl.
- **Sprache.** Englische EQS-Titel treffen deutsche Begriffe kaum; sie kommen fast nur über die
  Themenverschiebung in die Auswahl.
- **Keine Ursachen.** Auch ein Beleg, der alle vier Regeln erfüllt, ist ein geordneter Hinweis zum
  Nachsehen, kein Beleg für einen Zusammenhang (E23).
- **Werte sind Setzungen:** zwei Zeichen Genitiv, 0,5 zeitliche Nähe, die Liste der allgemeinen
  Wörter.

## 5. Prüfung und Belege

| Was | Beleg |
|---|---|
| Festschreibung, Namensregel, Ausschlussregeln, Rangfolge, `title_words` | `backend/tests/explanations/test_strict_selection.py`: Konstanten und `rules()["selection"]`, Texte ohne Ursache-Wörter, allgemeine Wörter und Stoppwörter, Genitiv und „Telekommunikation“, E.ON und 1&1, CGM nur mit `title_words`, Wortbezug nur in einer Richtung („Firmen“ trifft „firmenwagen“ nicht mehr, „Stellenabbauprogramm“ trifft „stellenabbau“), jede Regel einzeln und ihre Reihenfolge, EQS-Ausnahme, jeder ausgewählte Beleg mindestens mittel, Rangfolge mit sieben konstruierten Belegen (2 ausgewählt, 5 ausgeschlossen je Regel), `item_scores` mit Regel und Rang hinter den Bündeln, Zustand offen, `strict=False` wie bisher, allgemeine Ereignisse außen vor, `explanations_for` mit und ohne `title_words`, `company_context_info` liest `title_words` |
| Bestehende Tests angepasst | `test_explanation_ranking.py` (Ausschluss statt Rückstufung, Obergrenze mit `strict=False`), `test_explanations_in_responses.py` (Titel nennen Demo 3; Felder `n_selected`, `n_excluded`, `n_excluded_by_reason`, `selection`; Auswahl und Einzelmonat), `test_signal_labels.py` (Referenzzahlen mit `strict=False`, Felder auch bei Ausschluss), `test_rate_explanations.py` (Bogen vom 2026-10-17 mit `strict=False`, neuer Test für den Standard), `test_explanation_validity.py` (`n_selected`/`n_excluded`, `strict=False` liefert dieselben Fenster) |
| Unverändert | `test_frozen_rules.py` (Schwellen, Stufenregeln Fassung 2, Ereignisarten), `test_corrections_2026_10_13.py` (Unternehmen im Titel mit Punkt und Ziffern) |
| Suites | `tests/explanations`, `tests/drilldown`, `tests/evidence`: 614 Tests ohne Fehler; gesamte Backend-Suite 1531 Tests ohne Fehler (2026-10-18) |
| Frontend | `npx vitest run` (11 Tests) und eslint für `ExplanationPanel.jsx`, `EvidenceSection.jsx`, `explanationText.js` ohne Befund |
| Lint Backend | ruff (E, F, W ohne E501) für die berührten Dateien ohne Befund |
| Schnittstelle mit echten Daten (2026-10-18) | `GET …/company/19/anomalies/employee:durchschnittsbewertung:2024-07/explanations` (SAP SE, Speicher und Datenbank): 362 Belege, 37 geeignet, 325 ausgeschlossen (Unternehmen im Titel nicht genannt 103, ohne Arbeitgeberbezug 111, kein Wortbezug und keine Themenverschiebung 99, zeitliche Nähe unter 0,5 12); Ansätze: „Next Level: Abfindungsprogramm führt zu Unruhe bei SAP“ und „Konzernchef Christian Klein will Homeoffice bei SAP stark einschränken“ (hoch), Übernahme WalkMe und SAP Labs Garching (Themenverschiebung), „Mit RISE with SAP noch mehr erreichen“ (nur Wortbezug ‚erreichen‘). Vor der Richtungsregel des Wortbezugs stand „So wollen SAP, DHL und andere Firmen mehr Geflüchtete in Arbeit bringen“ mit ‚firmen‘ → ‚firmenwagen‘ darunter; danach nicht mehr |
| Browser (2026-10-18) | `/anomalies?company=19&anomaly=employee:durchschnittsbewertung:2024-07` gegen den Backend-Server auf Port 8000: Karte „5 Ansätze · aus 362 Belege · 37 geeignet · 37 Bündel“; Dialog mit Untertitel „5 Ansätze aus 362 Belegen (37 geeignet nach strenger Auswahl, 325 ausgeschlossen; 37 Bündel, 9 Gruppen nach Ereignisart)“, der Zeile zur strengen Auswahl mit Ausschlüssen je Regel und dem Absatz „Strenge Auswahl (seit 2026-10-18)“ unter „Wie wird eingestuft?“ („sind ausgeschlossen“ statt „eine Stufe tiefer“); Belegliste nach Relevanz: die 37 geeigneten Meldungen zuerst, danach alle 325 übrigen mit „nicht in den Ansätzen: …“; keine Konsolenfehler |


### Auswertung mit strenger Auswahl (Stand 2026-10-18, ein Lauf)

`cd backend && uv run python scripts/report_explanation_validity.py --json data/calibration/explanation_validity_strict_2026-10-18.json`
(Tabellen in `explanation_validity_strict_2026-10-18.md`), Belege nur aus dem Speicher, Bewertungen
aus der Datenbank, Annotationsdatei Version 3 mit 20 Einträgen, ohne Stimmung der Titel; sonst wie
der Lauf nach der Korrektur vom 2026-10-13 (E23, `explanation_validity_korrektur_2026-10-13.json`,
72 Vergleichsfenster). Die Zahlen sind beschreibend, ohne Test und ohne Aussage über Ursachen.

| | Korrektur 2026-10-13 (ohne strenge Auswahl) | strenge Auswahl 2026-10-18 |
|---|---|---|
| Markierungsfenster mit Ansatz | 23/28 (82 %) | 14/28 (50 %) |
| Vergleichsfenster mit Ansatz | 57/72 (79 %) | 23/72 (32 %) |
| Oberste Stufe Markierungsfenster (hoch / mittel / niedrig / offen) | 3 / 12 / 8 / 5 | 2 / 12 / 0 / 14 |
| Oberste Stufe Vergleichsfenster (hoch / mittel / niedrig / offen) | 5 / 27 / 25 / 15 | 2 / 21 / 0 / 49 |
| Abdeckungsquote NFA-05 (Niveauwechsel / Einzelmonate) | 23/28: 14/19 (74 %) / 9/9 (100 %) | 14/28: 12/19 (63 %) / 2/9 (22 %) |
| Bündel je Fenster (Median, Markierung / Vergleich) | 43 / 47 | 0,5 / 0 |

Je Unternehmen (Markierungsfenster mit Ansatz): E.ON 1/1, RWE 1/2, SAP SE 2/2, NTT DATA SE 1/4,
1&1 AG 1/1, Bechtle 1/1, Cancom 0/2, Carl Zeiss 0/2, Compugroup 1/1, Telekom 3/7, Freenet 3/5.
Nach Referenzzeiträumen (E5): Markierungen mit Referenzzeitraum 5/8 mit Ansatz, ohne Referenzzeitraum
9/20.

**Befund in einem Satz:** Die strenge Auswahl halbiert die Ansätze bei Markierungen (50 %) und
drittelt sie bei Vergleichsfenstern (32 %); der Abstand zwischen beiden Gruppen, der in E23 nicht
erkennbar war (82 % gegen 79 %), ist damit größer (50 % gegen 32 %), bleibt aber eine beschreibende
Zahl aus 28 Markierungen ohne Signifikanzaussage. Die Abdeckungsquote nach NFA-05 sinkt von 82 % auf
50 %; bei den Einzelmonaten auf 22 %, weil dort meist nur die Ereignisart trifft (kleine Basis, keine
Begriffe). Ob diese Quote als erfüllt gilt, entscheidet der Autor (E33).

## 6. Offene Punkte

- Die vier Regeln sind am 2026-10-18 vom Autor bestätigt (Wortbezug allein bleibt zugelassen, keine
  Pflicht zur Ereignisart). Offen bleiben die Werte (zwei Zeichen, 0,5), die Liste der allgemeinen
  Wörter und `title_words` („CGM“); weitere Kennungen für andere Unternehmen nach Sichtung der
  Belegliste.
- Der Auswertungslauf mit strenger Auswahl (Abschnitt 5) ersetzt nicht die Läufe aus E23; ob die
  Abdeckungsquote nach NFA-05 (jetzt 50 %) noch als erfüllt gilt, entscheidet der Autor.
- Ob die Karte die Ausschlüsse je Regel schon in der Vorschau nennen soll (jetzt nur im Dialog).
- Ob EQS-Mitteilungen einer Konzerngesellschaft weiter als „genannt“ gelten sollen.
