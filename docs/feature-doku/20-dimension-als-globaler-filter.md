# 20 – Dimension als globaler Filter der Detailseite

| | |
|---|---|
| Inkrement | Ergänzung der Detailseite „Anomalien im Verlauf“ (2026-10-23) |
| Anforderungen | keine eigene Anforderung aus der Prüfliste; Wunsch des Autors (2026-10-23): Wählt man im Dimensionsfilter eine Kategorie, soll sie im ganzen Dashboard gelten, und es sollen nur Bewertungen und Kommentare sowie Nachrichten und Quellen zu dieser Dimension angezeigt werden |
| Entscheidungen | E34 in `docs/entscheidungen.md` (Regel, wann eine Bewertung und wann ein Beleg zur Dimension gehört); schließt den offenen Punkt aus Doku 02 („ob je Dimension nur das zugehörige Thema gezeigt werden soll“) |
| Status | umgesetzt (2026-10-23), nicht committet; Regeln sind Setzungen (vorläufig) |
| Stand | 2026-10-23 |

## 1. Vorstellung

Im Kopf der Detailseite **„Anomalien im Verlauf“** (`/anomalies`) steht das Auswahlfeld
**„Dimension“** (Gesamtbewertung oder eine der 13 Kununu-Kategorien der Mitarbeitenden bzw.
10 der Bewerbenden). Bisher wählte es nur die Reihe des Monatsverlaufs, der Erkennung und des
Vorher-Nachher-Vergleichs; die Liste „Bewertungen des Zeitraums“ zeigte alle Bewertungen des
Fensters (mit markiertem Thema), die Karte „Externe Berichte“ alle Meldungen des
Ereignisfensters. Seit dem 2026-10-23 gilt die gewählte Dimension für **alle Karten der Seite**:

- **Hinweis unter dem Monatsverlauf.** Bei einer Einzeldimension steht dort: „Dimension
  Gehalt/Sozialleistungen gewählt: Die Bewertungen des Zeitraums und die externen Berichte unten
  zeigen nur, was zu dieser Dimension gehört … ‚Gesamtbewertung‘ zeigt wieder alles.“
- **Bewertungen des Zeitraums.** Die Liste enthält nur noch Bewertungen, die zur Dimension
  gehören (Regel in § 2). Untertitel und Vorschaukarte nennen die Zählung vor und nach dem
  Filter („3 von 54 Bewertungen zur Dimension Gehalt/Sozialleistungen“), die Vorschaukarte
  statt der Gesamtnote das Mittel der Sterne der Dimension über diese Bewertungen („Ø Dimension
  3,00“). Die Sternespalte jeder Zeile zeigt die **Sterne der Dimension** („★ 3,0“), die
  Gesamtnote klein darunter („Gesamt 1,8“; Nachtrag 2026-10-23 auf Wunsch des Autors, vorher
  Gesamtnote groß und Dimension als Marke); hat die Bewertung einen **Kommentar zu dieser
  Kategorie**, steht er diesen Kommentar als Textauszug („Kommentar zu Gehalt/Sozialleistungen ·
  …“) mit markierten Schlüsselwörtern; sonst den allgemeinen Textauszug wie bisher. Themenfilter
  und Sortierung (Doku 17) bleiben und wirken innerhalb der Dimension; das Auswahlfeld zählt die
  Themen nur über die Bewertungen der Dimension.
- **Einzelbewertung.** Im Detailfenster zeigt der Kopfblock oben die **Sterne der Dimension**
  groß und in ihrer Farbe („Arbeitsatmosphäre · gewählte Dimension“, 3,0 von 5,0, Balken), die
  Gesamtbewertung als kleinere Zeile darunter (Nachtrag 2026-10-23 auf Wunsch des Autors; ohne
  Dimension bleibt der Block die Gesamtbewertung). Darunter steht der Abschnitt **„Kommentar zur
  Kategorie“** mit dem Kommentar (markiert) oder dem Hinweis, dass keiner vorliegt; in
  „Detaillierte Bewertungen“ trägt die Kategorie den Zusatz „gewählte Dimension“.
- **Externe Berichte im Ereignisfenster.** Die Belegliste enthält nur Meldungen, die zur
  Dimension gehören (Regel in § 2); Vorschaukarte und Untertitel nennen „nur zur Dimension
  Gehalt/Sozialleistungen: 1 von 55 Belegen“, jede Zeile ihren **Bezug** („Bezug zur Dimension:
  Schlüsselwort ‚gehaltserhöhung‘ · Ereignisart Vergütung und Sozialleistungen“). Ist keine
  Meldung dabei, sagt die Karte, wie viele Meldungen das Fenster insgesamt hat und warum sie
  nicht dazugehören. Sortierung nach Relevanz und Filter nach Ereignisart (Doku 08) bleiben.
- **Filtermarke in den Dialogen.** Im Kopf der Dialoge „Bewertungen“ und „Externe Berichte“
  steht links von den Schaltern die bernsteinfarbene Marke **„Dimension: Arbeitsatmosphäre“**
  (Nachtrag 2026-10-23, Rückmeldung des Autors: die Liste war gefiltert, die Schalterleiste
  zeigte es nicht). Beim Darüberfahren nennt sie die Regel; das Kreuz hebt den Filter auf, also
  wechselt zur Gesamtbewertung, wobei der Zeitraum bleibt (bei einer markierten Veränderung ihr
  aktuelles Fenster als Auswahl). Die Auswahlfelder der Dialoge zeigen als Grundauswahl den
  Namen der Dimension statt „Alle Themen“ bzw. „Alle Ereignisarten“ (Wunsch des Autors,
  2026-10-23): alle Bewertungen bzw. Belege zur Dimension; ein Thema oder eine Ereignisart
  darunter schränkt weiter ein.
- **Zurück zum Dashboard.** Der Pfeil oben links nimmt Quelle, Dimension und Status mit; die
  Karte „Anomalien im Verlauf“ im Haupt-Dashboard zeigt dann dieselbe Reihe. Von der Karte zur
  Detailseite ging die Auswahl schon bisher mit. Die Dimension steht weiter in der Adresse
  (`?dimension=gehalt_sozialleistungen`), lässt sich also teilen.

Mit **„Gesamtbewertung“** ist nichts gefiltert; Listen und Karten sind dann wie vor dem
2026-10-23. Vorher-Nachher-Vergleich und Erklärungsansätze sind unverändert: Der Vergleich
rechnet weiter über alle Bewertungen der Fenster (mit „Dimension −1,20“ als Verschiebung der
Sterne der Dimension), die Erklärungsansätze über alle Meldungen des Fensters.

Nutzen: Wer eine Kategorie wählt, etwa nach einem Abfall bei „Gehalt/Sozialleistungen“, liest
nur die Bewertungen, die sich zu dieser Kategorie äußern, mit deren Kommentar und Sternen, und
nur die Meldungen, die thematisch dazu passen; die Zählungen zeigen dabei, wie viel der Filter
weglässt.

## 2. Erklärung

**Wann gehört eine Bewertung zur Dimension?** (`backend/services/dimension_scope.py`,
`review_dimension_info`; Entscheidung E34.) Eine Bewertung gehört zur Dimension, wenn sie

1. einen **Kommentar zur Kategorie** der Dimension hat. Kununu erlaubt zu jeder Kategorie einen
   kurzen Kommentar; in der Datenbank steht er in der Spalte mit dem Namen der Dimension (z. B.
   `gehalt_sozialleistungen`, nur Mitarbeitende, `CATEGORY_TEXT_FIELDS`). Platzhalter wie „-“
   zählen nicht (`has_text_content`); oder
2. das **Schlüsselwort-Thema** der Dimension nennt. Jede Dimension hat ein Thema der
   Themenübersicht (`topic_for_dimension`, über die Sternespalte in `rating_fields`, E10;
   z. B. Gehalt/Sozialleistungen → „Gehalt & Sozialleistungen“ mit `gehalt`, `bezahlung`,
   `lohn`, `vergütung`, `benefits`, …). Gesucht wird in Titel, Freitexten und allen
   Kategorie-Kommentaren (`EXPLANATION_TOPIC_TEXT_FIELDS`, Korrektur E23), dieselbe Regel wie
   bei den Themen-Marken und dem Themenfilter (Doku 17).

Die **Sterne der Dimension allein genügen nicht.** Eine nur lesende Prüfung am 2026-10-23
(Skript im Sitzungsordner, nicht im Repository) ergab für Thyssenkrupp (446 Bewertungen der
Mitarbeitenden): 445 mit Sternen für Arbeitsatmosphäre, 219 mit Kommentar dazu, 70 mit dem
Thema; für E.ON (486): 484 / 233 / 73; für Aixtron (109): 109 / 31 / 14. Fast jede Bewertung
bewertet jede Kategorie, ein Filter nach den Sternen würde also nichts unterscheiden. Bei den
TecDAX-Unternehmen mit vollständigem Export (z. B. Telekom ab 2013) hat jede Bewertung
Kommentare zu allen Kategorien; dort filtert nur die Zeit vor dem vollständigen Export, die
Liste zeigt aber in jeder Zeile den Kommentar zur Kategorie statt des allgemeinen Auszugs. Die
Sterne der Dimension werden je Bewertung mitgeliefert und angezeigt (`dimension.rating`).

**Ablauf im Backend (Bewertungen).** `GET /api/analytics/company/{id}/reviews` mit `dimension`
(Einzeldimension) liefert je Bewertung zusätzlich `dimension` = `{key, rating, comment,
mentions_topic, in_dimension}`; mit `format=full` und Kommentar auch `highlights.comment`
(Fundstellen des Themas im Kommentar, `topic_spans`). Der neue Parameter `dimension_only=true`
lässt nur Bewertungen mit `in_dimension` übrig; die Reihenfolge der Schritte ist: Zeitraum →
Status → **Dimension** → Themenzählung (`topic_summary`) → Themenfilter → Seite. `highlight`
nennt dann `n_all` (vor dem Filter), `n_dimension`, `dimension_mean` (Mittel der Sterne der
Dimension über diese Bewertungen, zwei Nachkommastellen) und `note` (den Regeltext, den der
Dialog anzeigt). Mit der Gesamtbewertung oder ohne `dimension` antwortet die Route 400. Ohne
`dimension_only` ist die Antwort bis auf das Feld `dimension` je Bewertung und
`highlights.comment` unverändert.

**Wann gehört eine Meldung zur Dimension?** (`evidence_dimension_match`.) Eine Meldung gehört
zur Dimension, wenn

1. ihr **Titel ein Schlüsselwort des Themas** nennt: als ganzes Wort wie in den Bewertungen
   (`topic_spans`) oder als **Wortanfang** nach der Regel der strengen Auswahl (E33,
   `match_terms(compound_only=True)`): Das Titelwort beginnt mit dem Schlüsselwort, und das
   Schlüsselwort hat mindestens `TERM_PREFIX_MIN_LENGTH` = 6 Zeichen. So passt
   „Gehaltserhöhung“ zu `gehalt`, aber „lohnt“ nicht zu `lohn` (vier Zeichen: nur als ganzes
   Wort). Nur die einfachen Schlüsselwörter (`\bwort\b`, Buchstaben) werden so verwendet;
   zusammengesetzte Muster wie „Work-Life-Balance“ trifft `topic_spans`; oder
2. ihre **Ereignisart** dem Thema zugeordnet ist: `classify_title` (E22, Doku 08) ordnet den
   Titel einer Ereignisart zu; jede Ereignisart mit Arbeitgeberbezug nennt in
   `backend/data/event_categories.json` ihre Themen (`topics`), z. B. „Tarifverhandlung und
   Streik“ → Gehalt & Sozialleistungen, „Führungswechsel“ → Vorgesetztenverhalten. Die Gruppe
   ohne Arbeitgeberbezug (Börse, Sport, Produkt) zählt nicht.

**Allgemeine Ereignisse** (Konjunktureinbruch, Inflationsschub; E29) haben keinen Bezug zu einer
Dimension und entfallen mit dem Filter; sie bleiben im Diagramm einblendbar.

**Ablauf im Backend (Belege).** Die Routen `GET …/anomalies/{anomaly_id}/context` und
`GET …/context?from=&to=` bekommen `dimension_only=true`; die Auswahl-Route dazu `source` und
`dimension` (die Veränderung kennt ihre Dimension aus der Kennung). `scope_evidence` filtert
nach dem Abruf der Monate und vor dem Seitenschnitt: `items` nur mit Bezug (je Beleg
`dimension_match` = `{terms, category}`), `total`, `counts` und `coverage` neu gerechnet,
`reason` = „Kein Beleg im Fenster gehört zur gewählten Dimension.“, wenn das Fenster Belege
hat, aber keiner dazugehört; die Antwort erhält `scope` = `{dimension, topic, n_all,
n_dimension, note}`. Gesamtbewertung oder fehlende Dimension: 400.

**Frontend.** `pages/Anomalies.jsx` setzt `singleDimension` (alles außer Gesamtbewertung) und
reicht es als `dimensionOnly` an `useReviewPages` und (über `EvidenceCard`) an `useEvidence`;
die Texte stehen in `lib/dimensionScope.js`. Die Zeile der Bewertung (`PeriodReviews.jsx`), das
Detailfenster (`ReviewDetailModal.jsx`, Abschnitt „Gewählte Dimension“), die Vorschaukarten
(`AnomalyDetailCards.jsx`) und die Belegliste (`EvidenceSection.jsx`, `lib/evidenceText.js`)
zeigen die neuen Felder. Beim Zurück gibt die Seite `anomalySelection` im Navigationszustand
mit; `Dashboard.jsx` reicht sie als `initialSelection` an `AnomalyCard`, die sie prüft (Quelle,
Dimension der Quelle, Status) und als Startzustand nimmt.

**Parameter.** Keine neuen Zahlenwerte außer der übernommenen Mindestlänge 6 für den
Wortanfang (E33, vorläufig). Die Feldlisten (`CATEGORY_TEXT_FIELDS`,
`EXPLANATION_TOPIC_TEXT_FIELDS`), die Schlüsselwörter der Themen (E10) und die Themen je
Ereignisart (E22) sind die bestehenden Setzungen.

## 3. Begründung

- **Dimension als ein Zustand der Seite.** Der Wunsch des Autors war, dass die Auswahl „global“
  gilt. Die Dimension stand schon in der Adresse und bestimmte Verlauf, Erkennung und Vergleich;
  nur die beiden Listen folgten ihr nicht. Eine zweite, kartenlokale Auswahl hätte zwei
  Zustände nebeneinander erzeugt (Verlauf zu einer Dimension, Liste zu einer anderen). Deshalb
  gilt eine Auswahl für alles, und der Hinweis unter dem Verlauf sagt, was sie bewirkt; der Weg
  zurück zu „alles“ ist „Gesamtbewertung“ im selben Auswahlfeld (keine zusätzlichen Schalter).
- **Kommentar oder Thema, nicht Sterne.** Nur diese beiden Signale sagen, dass sich eine
  Bewertung zur Kategorie äußert; die Sterne vergibt fast jede Bewertung (§ 2). Der Kommentar
  zur Kategorie ist das genaueste Signal („Kommentare zu dieser Dimension“ im Wunsch des Autors);
  das Schlüsselwort-Thema ergänzt die Bewertungen, die die Kategorie im Freitext ansprechen,
  und nutzt dieselbe Regel wie der Themenfilter, damit beide Filter zusammen verständlich
  bleiben. Mit Doku 02 (§ 2.8) war bereits das Thema der Dimension markiert; „nur Bewertungen,
  die das Thema nennen“ (`?thema=nur`) gab es als Schalter. Der neue Filter ist dessen
  Weiterentwicklung mit dem Kategorie-Kommentar als zweitem Kriterium.
- **Meldungen über Schlüsselwort und Ereignisart.** Beides sind die Signale der
  thematischen Korrespondenz aus Inkrement 5 (Wortbezug, Ereignisart; E21, E22), nur mit den
  Schlüsselwörtern des Themas statt der kennzeichnenden Begriffe des Vergleichs. Die
  Wortanfang-Regel ist aus E33 übernommen, weil Titel Komposita verwenden
  („Gehaltserhöhung“, „Tarifabschluss“), Bewertungen eher das einfache Wort. Eine neue
  Wortliste je Dimension hätte eine weitere Setzung ohne Prüfung bedeutet.
- **Zählung sichtbar.** „3 von 54“ und „1 von 55“ zeigen, wie viel der Filter weglässt, damit
  niemand eine kleine Liste für die ganze Datenlage hält (FA-25/FA-26, Datenbasis und n).
- **Mittel der Dimension statt Gesamtnote.** Die Vorschaukarte zeigte Ø der Gesamtnote über
  alle Bewertungen des Fensters. Mit dem Filter wäre diese Zahl eine Aussage über eine andere
  Menge; deshalb das Mittel der Sterne der Dimension über die gezeigten Bewertungen, als
  „Ø Dimension“ beschriftet.
- **Vergleich und Erklärungsansätze unverändert.** Sie sind in E12/E21–E23 festgeschrieben und
  ausgewertet; ein Filter würde die Auswertungen unvergleichbar machen. Die Belegliste zeigt
  Stufe und Ereignisart der verbliebenen Belege weiter aus den Erklärungsansätzen.

## 4. Grenzen

- Der Kategorie-Kommentar fehlt bei älteren Bewertungen und bei den Unternehmen aus Zyklus 1
  oft; dort trägt nur das Schlüsselwort-Thema (deutsch, mehrdeutige Wörter zählen mit, E10).
  Bei Unternehmen mit vollständigem Export hat jede Bewertung Kommentare zu allen Kategorien,
  dann filtert die Dimension dort nicht, zeigt aber den passenden Kommentar.
- Bewerbende haben keine Kategorie-Kommentare; für sie zählt nur das Thema.
- Meldungen: nur der Titel, nur deutsche Schlüsselwörter (englische Titel treffen kaum, außer
  über die englischen Schlüsselwörter der Ereignisarten); ein Schlüsselwort im Titel ist kein
  Beleg für einen Zusammenhang mit den Bewertungen. Die Ereignisarten und ihre Themen sind
  Setzungen (E22).
- Mit dem Filter kann die Liste leer sein, obwohl das Fenster viele Bewertungen oder Belege
  hat; die Karten nennen dann die Gesamtzahl. Eine leere Liste heißt nicht, dass die
  Dimension unauffällig ist.
- Das Mittel „Ø Dimension“ über wenige Bewertungen (z. B. 3) ist nicht belastbar; die Zahl der
  Bewertungen steht daneben.
- Der PDF-Export des Haupt-Dashboards ist nicht betroffen (die Detailseite wird nicht exportiert).

## 5. Prüfung und Belege

| Prüfung | Beleg |
|---|---|
| Regeln | `backend/tests/drilldown/test_dimension_scope.py`: Kommentar zählt, Thema zählt, Sterne allein nicht, Platzhalter „-“ nicht, Bewerbende ohne Kommentar; Wortanfang ab sechs Zeichen („Gehaltserhöhung“ ja, „lohnt“ nein), Ereignisart mit und ohne Arbeitgeberbezug, allgemeine Ereignisse ausgeschlossen, `scope_evidence` mit Zählung, Grund und unveränderter Eingabe; Gesamtbewertung abgelehnt |
| Route Bewertungen | ebenda: `dimension` je Bewertung, `dimension_only` mit `n_all`, `n_dimension`, `dimension_mean`, Themenzählung innerhalb der Dimension, Bewerbende nur über das Thema, 400 ohne Einzeldimension; `test_topic_highlight.py` um `highlights.comment` ergänzt |
| Routen Belege | `backend/tests/evidence/test_context_dimension.py`: Auswahl-Route mit `dimension_only` (Warnstreik über Ereignisart, Gehaltserhöhung über Wortanfang, Spielbericht weg), unveränderte Antwort ohne Filter, Seitenschnitt nach dem Filter, leeres Ergebnis mit Grund, 400-Fälle, Veränderung einer Einzeldimension |
| Frontend | `frontend/src/lib/__tests__/dimensionScope.test.js` (Texte); `npm run lint` ohne Befund, `npm test` 34 Tests, `npm run build` |
| Gesamtlauf | Backend `uv run python -m pytest tests` 1575 Tests bestanden (2026-10-23) |
| Browser | Telekom, Mitarbeitende, Gehalt/Sozialleistungen, Veränderung ab Juli 2010 (Backend ohne Abruf, Belegspeicher nur gelesen): Hinweis unter dem Verlauf; Karte „Bewertungen des Zeitraums“ mit „3 Bewertungen · Ø Dimension 3,00 · zur Dimension Gehalt/Sozialleistungen, von 54 insgesamt“; Dialog „3 von 54 Bewertungen zur Dimension Gehalt/Sozialleistungen“, Themenfeld „Gehalt & Sozialleistungen (3)“, Zeilen mit Sternen der Dimension „4,0“ bzw. „1,0“ (Gesamtnote klein darunter) und markiertem „gehalt“; Karte „Externe Berichte“ mit „nur zur Dimension Gehalt/Sozialleistungen: 1 von 55 Belegen“, im Dialog die Zeile „E-Plus baut Prämiensystem Gettings um … Bezug zur Dimension: Schlüsselwort ‚prämiensystem‘ · Ereignisart Vergütung und Sozialleistungen“ und der Regelhinweis; Detailfenster der Bewertung „Klasse Arbeitgeber“ mit Abschnitt zur Dimension (Sterne 4,0, „Kein Kommentar zu dieser Kategorie; das Thema wird im Text genannt (markiert)“) und Zusatz „gewählte Dimension“ in den detaillierten Bewertungen; nach dem Umbau des Kopfblocks (1&1, Arbeitsatmosphäre, Bewertung „Am Anfang verlockend …“): Kopfblock „Arbeitsatmosphäre · gewählte Dimension“ 3,0, Zeile „Gesamtbewertung 1,8“, Abschnitt „Kommentar zur Kategorie“; Pfeil „Zurück zum Dashboard“: Karte „Anomalien im Verlauf“ im Haupt-Dashboard steht auf „Mitarbeiter · Gehalt/Sozialleistungen“; Filtermarke (1&1, Arbeitsatmosphäre, Auswahl Dez. 2022): Dialogkopf „Dimension: Arbeitsatmosphäre · Zeitraum davor / Auswahl · Sortierung · Alle Themen“, Untertitel „9 von 11 Bewertungen zur Dimension Arbeitsatmosphäre“; Kreuz an der Marke setzt die Adresse auf `?company=21&from=2022-12&to=2022-12`, Kopf auf „Gesamtbewertung“, Dialog bleibt offen mit „11 Bewertungen“; Auswahlfelder zeigen mit Filter „Arbeitsatmosphäre“ als Grundauswahl (Berichte: darunter die Ereignisarten der Belege; Bewertungen: darunter die Themen mit Zahl) |

## 6. Offene Punkte

- Ob der Kategorie-Kommentar allein (ohne das Schlüsselwort-Thema) die bessere Regel ist, kann
  der Autor an echten Fällen entscheiden; die Zählungen je Kriterium stehen in § 2.
- Englische Schlüsselwörter je Thema für die Titel der Meldungen (bisher nur über die
  Ereignisarten).
- Ob die Karte des Haupt-Dashboards die Dimension auch nach einem Neuladen behalten soll
  (heute nur über den Navigationszustand beim Zurück).
