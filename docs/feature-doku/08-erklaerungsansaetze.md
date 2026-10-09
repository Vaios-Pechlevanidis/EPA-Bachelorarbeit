# 08 – Erklärungsansätze: Mögliche Zusammenhänge

| | |
|---|---|
| Inkrement | 5 (Zyklus 2) |
| Anforderungen | Erklärungsansätze neben dem Bewertungsverlauf laut Exposé (TF4); Abdeckungsquote nach NFA-05 (Anforderungstexte liegen nicht im Repository; Lesart in E23) |
| Entscheidungen | E21 (Signale, Stufen, Bündelung, Schnittstelle; Iteration 2: zweite Fassung der Stufenregeln, Darstellung, Bündelung nach Ereignisart), E22 (Ereignisarten und Zuordnung), E23 (Auswertung, Nachtrag zur zweiten Fassung), E5 (Referenzzeiträume, zweite Person) in `docs/entscheidungen.md`; baut auf E7, E10–E12, E17–E20 |
| Status | umgesetzt; Ereignisarten und Schwellen vom Autor am 2026-10-08 bestätigt (D1, D2); Stufenregeln seit Iteration 2 (2026-10-08) in der zweiten Fassung, festgeschrieben; Auswertung mit jeder Fassung genau einmal gelaufen; alle Werte bleiben Setzungen |
| Stand | 2026-10-08 (Iteration 2) |

## 1. Vorstellung

Auf der Detailseite **„Anomalien im Verlauf“** (`/anomalies`) steht zwischen dem
Vorher-Nachher-Vergleich und den externen Belegen ein neuer Abschnitt **„Mögliche
Zusammenhänge“**, sobald eine auffällige Veränderung, ein auffälliger Einzelmonat oder ein frei
gewählter Zeitraum ausgewählt ist. Ein **Erklärungsansatz** ist ein möglicher Zusammenhang
zwischen der Veränderung und einem extern belegten Ereignis, begründet durch zeitliche und
thematische Korrespondenz. Er ist nie eine Ursache; jeder Eintrag zeigt, worauf seine Einstufung
beruht.

Der Kopf nennt, wie viele Ansätze aus wie vielen Belegen, Bündeln und Gruppen entstanden sind
und wie viele Bündel je Stufe es gibt („3 Ansätze aus 38 Belegen (34 Bündel, 3 Gruppen nach
Ereignisart) · Bündel je Stufe: Wortbezug oder Themenbezug 5, nur Ereignisart 1“). In der
obersten Liste steht höchstens ein Eintrag je Ereignisart (ohne Ereignisart je getroffenem
Begriff); Stellvertreter ist der beste Eintrag der Gruppe nach der Sortierung. Je Eintrag
stehen:

- die **Stufe** als Badge mit ihrer Bezeichnung: **Wortbezug und Ereignisart** (Schlüssel
  hoch), **Wortbezug oder Themenbezug** (mittel), **nur Ereignisart** (niedrig); alle Badges in
  derselben neutralen Farbe, keine Ampel; der Tooltip nennt Schlüssel und Regel (Iteration 2),
- die **Begründung in Klartext**, zum Beispiel: „Möglicher Zusammenhang: 2 Meldungen zu
  Personalabbau und Restrukturierung im Monat vor dem Übergang; in den Bewertungen danach wird
  ‚stellenabbau‘ häufiger genannt (12 gegenüber 1 Bewertungen); im Vergleich verschiebt sich das
  zugeordnete Thema Arbeitsatmosphäre um −8,5 Prozentpunkte.“,
- der **Titel als Link** (neuer Tab) mit Datum, Herausgeber und bei Bündeln der Anzahl der
  Meldungen und ihren Herausgebern,
- die **Signale als kleine Kennzeichen**: je getroffener Begriff mit den Zählungen („Begriff
  ‚stellenabbau‘ 12 ggü. 1“), die Ereignisart mit der Themenverschiebung oder dem Vermerk „nur
  erkannt“, die zeitliche Nähe („im Monat vor dem Übergang · 1,00“), die Quellenart (Ad-hoc,
  Meldung, EN), die Stimmung des Titels mit dem Vermerk, ob sie zur Richtung der Veränderung
  passt (ohne Einfluss auf die Stufe), und der Hinweis „Unternehmen im Titel nicht genannt“, wenn
  der Titel den Unternehmensnamen nicht enthält,
- bei Bündeln aufklappbar die **gebündelten Meldungen** mit Datum, Titel, Herausgeber und je
  Meldung Signalen und Stufe,
- bei Gruppen aufklappbar die **weiteren Einträge derselben Ereignisart** (oder desselben
  Begriffs) mit Anzahl der Bündel und Meldungen und den Herausgebern der Gruppe („24 weitere
  Einträge zu Ereignisart Personalabbau und Restrukturierung anzeigen · Gruppe: 25 Bündel, 25
  Meldungen (…)“); je Eintrag Datum, Titel, Herausgeber, Lage im Fenster, Signale und Stufe.

Erreicht kein Beleg die Stufe niedrig, zeigt der Abschnitt den Zustand **„Offen.“** mit dem
Hinweis, dass keine Meldung im Ereignisfenster einen Wortbezug zu den Bewertungen oder eine
erkannte Ereignisart mit Arbeitgeberbezug hat und interne Auslöser von außen nicht sichtbar
sind. Ein aufklappbarer Absatz „Wie wird eingestuft?“ erklärt Signale und Regeln mit den
geltenden Werten und der Fassung der Stufenregeln und endet mit dem Satz: „In der Auswertung vom
08.10.2026 traten Einträge dieser Art in Zeiträumen ohne Markierung ähnlich häufig auf wie bei
Markierungen. Sie sind Kandidaten für die eigene Einordnung.“ Der Abschnitt endet mit dem festen
Hinweis:

> Die Einstufung beruht auf Titeln und Wortbezügen. Sie zeigt mögliche Zusammenhänge, keine
> Ursachen.

Die **Belegliste** darunter (Abschnitt „Externe Belege im Ereignisfenster“, [07](07-externe-belege.md))
erhält eine Umschaltung der Sortierung (**Datum**, **Relevanz** = Rang der Erklärungsansätze)
und einen **Filter nach Ereignisart**; je Beleg stehen dann Stufe, Ereignisart und getroffene
Begriffe. Für Sortierung und Filter lädt die Liste alle Belege des Fensters.

Nutzen: Wer eine auffällige Veränderung betrachtet, sieht, welche der oft hunderten Meldungen im
Fenster überhaupt einen Bezug zu dem haben, was die Bewertenden danach schreiben, und mit welcher
Begründung; die Liste der Belege bleibt vollständig und prüfbar.

## 2. Erklärung

1. **Belege und Fenster.** Grundlage sind die Belege des Ereignisfensters aus Inkrement 4 (E18:
   3 Monate vor dem Übergang bis 1 Monat nach dem markierten Monat; für Einzelmonat und Auswahl um
   den Monat bzw. die Auswahl) und die Bewertungen der Vergleichsfenster des Vorher-Nachher-
   Vergleichs (E12; für die freie Auswahl E17). Allgemeine Ereignisse (E20) bleiben außen vor.
2. **Begriffe aus den Bewertungen** (`backend/services/review_terms.py`). Kennzeichnend ist ein
   Wort, das mindestens 3 Bewertungen und mindestens 3 % der Bewertungen des Fensters danach
   nennen und dessen Anteil danach mindestens doppelt so groß ist wie davor. Gezählt werden
   Freitexte und Titel der Bewertungen, je Bewertung ein Mal je Wort; nicht gezählt werden
   Stoppwörter, allgemeine Bewertungswörter (Arbeitgeber, Mitarbeiter, gut, schlecht, neu, …) und
   die Wortteile des Unternehmensnamens. Bei kleiner Basis (ein Fenster unter 10 Bewertungen)
   gibt es keine Begriffe. Die Vorverarbeitung des LDA-Modells aus Zyklus 1 wurde geprüft und
   nicht übernommen (sie faltet Umlaute und hängt an der Modellinstanz).
3. **Ereignisart aus dem Titel** (`backend/data/event_categories.json`,
   `services/event_categories.py`, E22). Zwölf Ereignisarten mit Arbeitgeberbezug (Personalabbau,
   Führungswechsel, Übernahme, Tarif und Streik, Standort, Vergütung, Arbeitsmodell, Rechtsstreit,
   Arbeitgeberauszeichnung, Krise, Einstellungen, Unternehmenskultur) mit Schlüsselwörtern deutsch
   und englisch und zugeordneten Themen aus E10; dazu die Gruppe ohne Arbeitgeberbezug
   (Börsenbericht, Kursziel, Sport, Produkt, Kapitalmarktmitteilungen von EQS). Schlüsselwörter
   gelten als Wortanfang, `*` steht für bis zu drei Wörter dazwischen.
4. **Drei Signale je Beleg** (`services/explanation_ranking.py`, E21), alle 0 bis 1:
   - `term_match`: kennzeichnende Begriffe im Titel; je Begriff 0,5, ein starker Begriff
     (mindestens 5 Bewertungen danach, Anteil mindestens dreifach und mindestens 5 Prozentpunkte
     über davor) 1; höchstens 1.
   - `category_match`: 1, wenn sich ein zugeordnetes Thema der erkannten Ereignisart im Vergleich
     um mindestens 5 Prozentpunkte verschoben hat (ohne kleine Basis); 0,5, wenn nur die
     Ereignisart erkannt ist; sonst 0.
   - `time_match`: 1 im Monat vor dem Übergang und im Übergang bis zum markierten Monat, davor
     abnehmend zum Rand des Fensters (0,67; 0,33), nach dem markierten Monat 0,5.
   - `topic_match` = Maximum aus `term_match` und `category_match`.
5. **Stufen** nach festen Regeln, **zweite Fassung** (Version 2, vom Autor am 2026-10-08
   festgelegt, E21 Iteration 2): hoch bei Begriff ≥ 0,5 und erkannter Ereignisart und Zeit ≥ 1;
   mittel bei Begriff ≥ 0,5 oder Ereignisart ≥ 1 (mit Themenverschiebung), und Zeit ≥ 0,5;
   niedrig bei erkannter Ereignisart oder Begriff ≥ 0,5, und Zeit ≥ 0,3; sonst keine. Zeitliche
   Nähe allein genügt nie; die Gruppe ohne Arbeitgeberbezug stuft eine Stufe zurück. Erste
   Fassung (Version 1, Lauf vom 2026-10-08, Commit 59f5d82): hoch bei Thema ≥ 1 und Zeit ≥ 1;
   mittel bei Thema ≥ 1 und Zeit ≥ 0,5 oder Thema ≥ 0,5 und Zeit ≥ 1; niedrig bei Thema ≥ 0,5
   und Zeit ≥ 0,3. Die Bezeichnungen der Oberfläche (Wortbezug und Ereignisart, Wortbezug oder
   Themenbezug, nur Ereignisart) sind Kurzformen dieser Regeln.
6. **Bündelung.** Meldungen zum selben Ereignis (gleiche Ereignisart, höchstens 3 Tage
   Abstand, Titelähnlichkeit mindestens 0,5 nach Jaccard über die Begriffe) werden ein Eintrag;
   Stellvertreter ist die Ad-hoc-Mitteilung, sonst die früheste Meldung; das Bündel trägt die
   höchsten Signale seiner Meldungen.
7. **Sortierung und Auswahl.** Stufe, dann Quellenart (Ad-hoc vor Meldung, nur innerhalb der
   Stufe), dann Thema, Zeit, Anzahl der Meldungen, Datum. Die oberste Liste führt höchstens
   einen Eintrag je Ereignisart (ohne Ereignisart je Begriffsmenge); Stellvertreter ist das
   beste Bündel der Gruppe, die übrigen Bündel stehen im Eintrag unter `group`; höchstens fünf
   Einträge. Ohne Bündel der Stufe niedrig ist die Liste leer und der Zustand „offen“. Die
   Gruppierung ist nur Darstellung: Stufe je Fenster, Bündel je Stufe und Signale je Beleg
   bleiben gleich (E21 Iteration 2).
8. **Stimmung des Titels** über den `SentimentAnalyzer` aus E11 nur für die fünf Einträge
   (Vermerk, ob sie zur Richtung passt; bei freier Auswahl folgt die Richtung aus der
   Verschiebung der Gesamtnote); ohne Einfluss auf die Stufe. Die Stimmung der Bewertungen wird
   nicht erneut berechnet.
9. **Schnittstelle.** `GET /api/analytics/company/{id}/anomalies/{anomaly_id}/explanations` und
   `GET /api/analytics/company/{id}/compare?from=&to=` (Einzelmonat als Auswahl von = bis)
   liefern `explanations` (höchstens fünf, je mit Stufe, Titel, Datum, Herausgeber, Link,
   Quellenart, Anzahl der Meldungen, Signalen, Begriffen mit Zählungen, Ereignisart mit
   Themenverschiebung, Stimmung, Text und den gebündelten Meldungen) und `explanation_summary`
   (Zustand, Fenster, Stand je Quelle, Begriffe, Signale und Rang je Beleg für die Belegliste,
   Regeln). Ein Fehler in diesem Teil ergibt den Zustand offen mit Fehlertext, nie einen Fehler
   der Route. Eine Sperre je Monat verhindert, dass Belegliste und Erklärungsansätze denselben
   Monat zugleich von den Quellen abrufen.
10. **Auswertung** (`backend/scripts/report_explanation_validity.py`, E23): dieselbe Rangfolge
    für jedes Markierungs- und jedes Vergleichsfenster aus E18, nur aus dem Speicher, ohne
    Stimmung; Anteil der Fenster mit Ansatz je Stufe, oberste Stufe, Abdeckungsquote nach
    NFA-05 (`--json`, `--md`). Genau einmal gelaufen (Abschnitt 5).

## 3. Begründung

- **Thematische statt zeitlicher Korrespondenz:** Nach E18 hat fast jedes Fenster Belege; nur
  der Bezug zwischen Titel und Bewertungen kann eine Meldung von hundert anderen abheben. Die
  Begriffe kommen aus den Bewertungen selbst, nicht aus einer Wortliste, damit der Bezug zum
  Text der Bewertenden in der Begründung lesbar bleibt.
- **Feste Regeln statt Gewichten:** Eine gewichtete Summe würde die Gewichte zur Aussage
  machen; feste Regeln lassen sich in einem Satz begründen und in der Oberfläche nachlesen.
- **Ereignisarten mit Themen aus E10:** Die Meldung steht so neben der Verschiebung derselben
  Kategorie, die der Vergleich schon zeigt; die Themen tragen die Namen der Kununu-Kategorien.
- **Rückstufung ohne Arbeitgeberbezug:** Börsenberichte, Spielberichte und Produktmeldungen
  sind die häufigsten Meldungen großer Unternehmen (6 436 von 18 936 gespeicherten Titeln) und
  sagen nichts über den Arbeitgeber.
- **Bündel:** Mehrere Herausgeber zu einem Ereignis sind ein Ereignis, nicht fünf Einträge.
- **Nachschärfung vor dem Festschreiben:** Ein Lauf über die 19 Niveauwechsel und eine Zählung
  der Schlüsselwörter über alle gespeicherten Titel (2026-10-08) zeigten generische Begriffe
  („neue“, „top“, Jobbezeichnungen wie „student“) und mehrdeutige Schlüsselwörter („übernimmt“,
  „betrug“, „hybrid“); daraus folgen Mindestanteil, kleine Basis, Namensteile als Wortanfang,
  die erweiterte Wortliste und die Wortfolgen in den Ereignisarten (E21, E22).
- **Keine Ursachen, sichtbare Begründung:** Jeder Eintrag zeigt die Signale; die Stimmung des
  Titels ist nur Vermerk, weil das Modell an Bewertungen und nicht an Schlagzeilen geprüft ist.
- **Beschreiben statt bewerten (Iteration 2):** Die Auswertung (E23) ergab, dass die Stufe hoch
  in Vergleichsfenstern so oft auftrat wie bei Markierungen; ein grünes Badge „hoch“ las sich
  trotzdem wie eine Bestätigung. Die Bezeichnung nennt deshalb, was gefunden wurde, und der
  Satz zur Auswertung steht bei den Regeln.
- **Wortbezug für die oberste Stufe (Iteration 2):** Eine erkannte Ereignisart mit einer
  Themenverschiebung von 5 Prozentpunkten ist in großen Fenstern häufig; die zweite Fassung
  verlangt für hoch zusätzlich einen Begriff aus den Bewertungen im Titel.
- **Eine Zeile je Ereignisart (Iteration 2):** Die Bündelung nach Titelähnlichkeit fasste kaum
  zusammen; mehrere Einträge zum selben Ereignis verdrängten andere Ereignisarten aus der
  obersten Liste.

## 4. Grenzen

- **Nur Titel.** Eine Meldung mit passendem Inhalt und unpassendem Titel bleibt unerkannt; ein
  Titel ohne Schlüsselwort und ohne Begriff hat keine Stufe.
- **Sprache.** Deutsche Begriffe greifen bei englischen Titeln nicht und umgekehrt; EQS-
  Mitteilungen liegen meist auf Englisch vor und treffen Begriffe aus deutschen Bewertungen kaum.
- **Stimmungsmodell** an Bewertungen geprüft, nicht an Schlagzeilen (E11).
- **Schwellen sind Setzungen.** Eine Themenverschiebung von 5 Prozentpunkten ist in großen
  Fenstern häufig; in der ersten Fassung erreichten dort viele Belege die Stufe hoch allein über
  die Ereignisart (SAP SE, Anstieg ab 2024-07: 33 Bündel hoch unter 362 Belegen; zweite Fassung:
  4 hoch, 51 mittel). Die Bündelung nach Titelähnlichkeit fasst Meldungen selten zusammen (362
  Belege, 353 Bündel); die Gruppierung der obersten Liste nach Ereignisart gleicht das nur in der
  Darstellung aus.
- **Bezeichnungen sind Kurzformen.** „nur Ereignisart“ (niedrig) erreicht auch ein Wortbezug am
  Rand des Fensters; „Wortbezug oder Themenbezug“ (mittel) umfasst auch Wortbezug mit
  Ereignisart bei zeitlicher Nähe unter 1. Der Tooltip nennt die Regel.
- **Fremde Treffer** des Suchbegriffs (E18) bekommen eine Stufe wie jede andere Meldung; der
  Hinweis „Unternehmen im Titel nicht genannt“ macht das sichtbar, entscheidet aber nicht
  (Compugroup: eine Telekom-Meldung auf Stufe hoch; RWE-Speicher mit Fußballmeldungen).
- **Kleine Basis.** Bei Einzelmonaten mit weniger als 10 Bewertungen gibt es keine Begriffe; die
  Ansätze beruhen dann allein auf der Ereignisart.
- **Einzelmonat** läuft über die Auswahl von = bis; die Zeitangaben sagen „Auswahl“.
- **Die Auswertung (E23) zeigt, dass die Rangfolge Markierungsfenster nicht von
  Vergleichsfenstern unterscheidet**, in der ersten wie in der zweiten Fassung der Stufenregeln.
  Ein Erklärungsansatz ist damit ein geordneter Hinweis zum Nachsehen, kein Beleg für einen
  Zusammenhang.
- **Referenzzeiträume fehlen noch (DZ1).** Die Zusatzauswertung getrennt nach Markierungen mit
  und ohne Referenzzeitraum ist festgelegt, aber bis zur Annotation „nicht verfügbar“ (E5).

## 5. Prüfung und Belege

| Was | Beleg |
|---|---|
| Begriffe | `backend/tests/explanations/test_review_terms.py`: Normalisierung, Stoppwörter, Namensteile, Mindestanzahl, Mindestanteil, Verhältnis, kleine Basis, Treffer im Titel |
| Ereignisarten | `test_event_categories.py`: Aufbau der Datei, Themen aus E10, Wortanfang, Platzhalter, Vorrang, Gruppe ohne Arbeitgeberbezug, EQS-Kategorien, fehlerhafte Dateien |
| Signale, Stufen, Bündel, Text | `test_explanation_ranking.py`: Zeitfunktion je Fensterart, Begriffsgewichte, Themenverschiebung, Stufenregeln (zweite Fassung, Version), Rückstufung, Bezeichnungen je Stufe ohne Ursache-Wörter, Bündelung, Sortierung, Textbausteine ohne Ursache, Auslöser, Grund, weil, führte, Stimmung ohne Einfluss, Zustand offen; `TestGroupByCategory`: ein Eintrag je Ereignisart, Stellvertreter nach bestehender Sortierung, Stufe je Fenster, Bündel je Stufe und `item_scores` mit und ohne Gruppierung gleich |
| Schnittstelle | `test_explanations_in_responses.py` (In-Memory-Store, Demo 3): Einträge aus dem Speicher, Begriff erreicht den Titel, offen ohne Belege, kein Fehler der Route bei unlesbarem Speicher, Auswahl und Einzelmonat, Sperre je Monat |
| Festschreibung | `test_frozen_rules.py`: alle Schwellen, Ereignisarten und Themenzuordnungen (D1, D2); Stufenregeln in der zweiten Fassung (Version 2) eingefroren, erste Fassung als Datensatz mit Commit 59f5d82 und Prüfung gegen die Datei des ersten Laufs |
| Auswertung | `test_explanation_validity.py`: Markierungs- und Vergleichsfenster aus nachgebildetem Speicher, Anteile, Abdeckungsquote, Markdown ohne Titel, kein Abruf; Zusatzauswertung nach Referenzzeiträumen mit konstruierter Annotationsdatei und „nicht verfügbar“ ohne Einträge |
| Abgleich zweier Annotationen (DZ1) | `backend/tests/test_compare_annotations.py`: Regel 6 auf zwei Zeiträume (Toleranz, Lücken, Richtung, Eins-zu-eins), Reihen aus CSVs, Anteil ohne Zeitraum in beiden Dateien, Bericht ohne note-Texte |
| Browser (2026-10-08) | Compugroup Medical, Abfall ab 2022-08: fünf Ansätze (hoch 2, mittel 3), Kennzeichen und Links, Bündel von zwei Ad-hoc-Mitteilungen aufklappbar; Belegliste nach Relevanz sortiert und nach Führungswechsel gefiltert (4 von 39); helles und dunkles Farbschema; keine Konsolenfehler |
| Browser (2026-10-08, Iteration 2) | SAP SE, Anstieg ab 2024-07: fünf Einträge mit Bezeichnung statt Ampel, Kopf „5 Ansätze aus 362 Belegen (353 Bündel, 22 Gruppen nach Ereignisart)“, Gruppe Personalabbau mit 24 weiteren Einträgen aufklappbar (25 Meldungen, Herausgeber), Abschnitt „Wie wird eingestuft?“ mit Fassung und Satz zur Auswertung; helles und dunkles Farbschema; keine Konsolenfehler |
| Antwortzeit (gefüllter Speicher) | `/explanations` SAP SE 2024-07: 11,8 s beim ersten Aufruf (Stimmung von 318 Bewertungen, E11), 0,64 s danach; `/compare` Telekom 2019-02 bis 2019-03: 5,1 s und 0,36 s; die Erklärungsansätze selbst unter 0,15 s; `/context` unverändert 0,13 s |
| Lint | eslint für die berührten Frontend-Dateien, ruff (E, F, W ohne E501) für die Backend-Dateien, ohne Befund; 1028 Backend-Tests grün (Inkrement 5), 1058 nach Iteration 2 |

### Auswertung (Stand 2026-10-08, ein Lauf)

`cd backend && uv run python scripts/report_explanation_validity.py --json data/calibration/explanation_validity_2026-10-08.json`
mit den bestätigten Ereignisarten und Schwellen, Belege nur aus dem Speicher (Stand nach dem
Vorabruf der Nachschärfung von Inkrement 4), ohne Stimmung der Titel. Unternehmen ohne
Markierung (Thyssenkrupp, Open Grid Europe, KIT, TU München) fehlen in den Tabellen.

**Markierungsfenster**

| Unternehmen | Fenster (vollständig) | mit Ansatz | mit hoch | mit mittel | mit niedrig | Belege / Bündel je Fenster (Median) |
|---|---|---|---|---|---|---|
| E.ON | 1 (1) | 1/1 (100 %) | 0/1 (0 %) | 1/1 (100 %) | 1/1 (100 %) | 373 / 368 |
| RWE | 2 (2) | 2/2 (100 %) | 0/2 (0 %) | 2/2 (100 %) | 2/2 (100 %) | 304.5 / 298 |
| SAP SE | 2 (2) | 2/2 (100 %) | 2/2 (100 %) | 2/2 (100 %) | 2/2 (100 %) | 345.5 / 336 |
| NTT DATA SE | 4 (4) | 1/4 (25 %) | 1/4 (25 %) | 1/4 (25 %) | 1/4 (25 %) | 2 / 2 |
| 1&1 AG | 1 (1) | 1/1 (100 %) | 0/1 (0 %) | 1/1 (100 %) | 0/1 (0 %) | 25 / 25 |
| Bechtle | 1 (1) | 1/1 (100 %) | 1/1 (100 %) | 0/1 (0 %) | 0/1 (0 %) | 6 / 6 |
| Cancom | 2 (2) | 2/2 (100 %) | 0/2 (0 %) | 1/2 (50 %) | 1/2 (50 %) | 7 / 7 |
| Carl Zeiss | 2 (2) | 2/2 (100 %) | 0/2 (0 %) | 2/2 (100 %) | 1/2 (50 %) | 59.5 / 58.5 |
| Compugroup Medical Deutschland | 1 (1) | 1/1 (100 %) | 1/1 (100 %) | 1/1 (100 %) | 1/1 (100 %) | 38 / 34 |
| Telekom | 7 (7) | 7/7 (100 %) | 0/7 (0 %) | 7/7 (100 %) | 6/7 (86 %) | 61 / 61 |
| Freenet | 5 (5) | 3/5 (60 %) | 1/5 (20 %) | 0/5 (0 %) | 3/5 (60 %) | 31 / 29 |
| **Gesamt** | 28 (28) | 23/28 (82 %) | 6/28 (21 %) | 18/28 (64 %) | 18/28 (64 %) | 45 / 43 |

**Vergleichsfenster**

| Unternehmen | Fenster (vollständig) | mit Ansatz | mit hoch | mit mittel | mit niedrig | Belege / Bündel je Fenster (Median) |
|---|---|---|---|---|---|---|
| E.ON | 3 (3) | 3/3 (100 %) | 1/3 (33 %) | 3/3 (100 %) | 3/3 (100 %) | 335 / 334 |
| RWE | 6 (6) | 6/6 (100 %) | 0/6 (0 %) | 5/6 (83 %) | 6/6 (100 %) | 171 / 170 |
| SAP SE | 6 (6) | 6/6 (100 %) | 2/6 (33 %) | 6/6 (100 %) | 6/6 (100 %) | 195.5 / 190.5 |
| NTT DATA SE | 10 (10) | 6/10 (60 %) | 2/10 (20 %) | 4/10 (40 %) | 1/10 (10 %) | 5 / 5 |
| 1&1 AG | 3 (3) | 2/3 (67 %) | 1/3 (33 %) | 2/3 (67 %) | 2/3 (67 %) | 30 / 30 |
| Bechtle | 3 (3) | 0/3 (0 %) | 0/3 (0 %) | 0/3 (0 %) | 0/3 (0 %) | 7 / 7 |
| Cancom | 6 (6) | 1/6 (17 %) | 0/6 (0 %) | 1/6 (17 %) | 0/6 (0 %) | 4 / 4 |
| Carl Zeiss | 5 (5) | 5/5 (100 %) | 1/5 (20 %) | 4/5 (80 %) | 3/5 (60 %) | 34 / 34 |
| Compugroup Medical Deutschland | 3 (3) | 3/3 (100 %) | 1/3 (33 %) | 1/3 (33 %) | 2/3 (67 %) | 25 / 23 |
| Telekom | 16 (16) | 16/16 (100 %) | 5/16 (31 %) | 16/16 (100 %) | 12/16 (75 %) | 60 / 59.5 |
| Freenet | 15 (15) | 10/15 (67 %) | 3/15 (20 %) | 5/15 (33 %) | 7/15 (47 %) | 41 / 41 |
| **Gesamt** | 76 (76) | 58/76 (76 %) | 16/76 (21 %) | 47/76 (62 %) | 42/76 (55 %) | 47.5 / 47 |

„mit Ansatz“ = mindestens ein Bündel der Stufe niedrig oder höher; „mit hoch/mittel/niedrig“ = mindestens ein Bündel dieser Stufe. Anteile beziehen sich auf die vollständig im Speicher liegenden Fenster (in Klammern).

| Unternehmen | Abdeckungsquote NFA-05 (Markierungen mit Ansatz) | Niveauwechsel | Einzelmonate | Vergleichsfenster mit Ansatz |
|---|---|---|---|---|
| E.ON | 1/1 (100 %) | 1/1 (100 %) | – | 3/3 (100 %) |
| RWE | 2/2 (100 %) | 1/1 (100 %) | 1/1 (100 %) | 6/6 (100 %) |
| SAP SE | 2/2 (100 %) | 1/1 (100 %) | 1/1 (100 %) | 6/6 (100 %) |
| NTT DATA SE | 1/4 (25 %) | 1/4 (25 %) | – | 6/10 (60 %) |
| 1&1 AG | 1/1 (100 %) | 1/1 (100 %) | – | 2/3 (67 %) |
| Bechtle | 1/1 (100 %) | 1/1 (100 %) | – | 0/3 (0 %) |
| Cancom | 2/2 (100 %) | – | 2/2 (100 %) | 1/6 (17 %) |
| Carl Zeiss | 2/2 (100 %) | – | 2/2 (100 %) | 5/5 (100 %) |
| Compugroup Medical Deutschland | 1/1 (100 %) | 1/1 (100 %) | – | 3/3 (100 %) |
| Telekom | 7/7 (100 %) | 4/4 (100 %) | 3/3 (100 %) | 16/16 (100 %) |
| Freenet | 3/5 (60 %) | 3/5 (60 %) | – | 10/15 (67 %) |
| **Gesamt** | 23/28 (82 %) | 14/19 (74 %) | 9/9 (100 %) | 58/76 (76 %) |

| Oberste Stufe je Fenster (gesamt) | hoch | mittel | niedrig | offen |
|---|---|---|---|---|
| Markierungsfenster | 6 | 14 | 3 | 5 |
| Vergleichsfenster | 16 | 35 | 7 | 18 |

Beschreibende Zahlen ohne Signifikanzaussage. Ein Erklärungsansatz ist ein möglicher Zusammenhang, keine Ursache; die Einstufung beruht auf Titeln und Wortbezügen. Fenster mit fehlenden Monaten im Speicher zählen nicht als 'ohne Ansatz'. Die Stimmung der Titel wurde nicht berechnet (ohne Einfluss auf die Stufe).

**Befund in einem Satz:** Die Rangfolge unterscheidet Markierungsfenster nicht erkennbar von
Vergleichsfenstern desselben Unternehmens (mit Ansatz 82 % gegen 76 %, mit Stufe hoch 21 % gegen
21 %); die Abdeckungsquote nach NFA-05 liegt bei 23 von 28 Markierungen (82 %). Einordnung und
Grenzen in E23.

### Auswertung, zweite Fassung der Stufenregeln (Iteration 2, Stand 2026-10-08, ein Lauf)

`cd backend && uv run python scripts/report_explanation_validity.py --json data/calibration/explanation_validity_v2_2026-10-08.json`
mit der zweiten Fassung der Stufenregeln (Version 2, E21 Iteration 2), sonst unverändert
(gleicher Speicher, gleiche Bewertungen, gleiche Fenster, ohne Stimmung der Titel). Die Zahlen
der ersten Fassung oben bleiben stehen; Lesart und Gegenüberstellung in E23 (Nachtrag).

**Markierungsfenster**

| Unternehmen | Fenster (vollständig) | mit Ansatz | mit hoch | mit mittel | mit niedrig | Belege / Bündel je Fenster (Median) |
|---|---|---|---|---|---|---|
| E.ON | 1 (1) | 1/1 (100 %) | 0/1 (0 %) | 0/1 (0 %) | 1/1 (100 %) | 373 / 368 |
| RWE | 2 (2) | 2/2 (100 %) | 0/2 (0 %) | 0/2 (0 %) | 2/2 (100 %) | 304.5 / 298 |
| SAP SE | 2 (2) | 2/2 (100 %) | 2/2 (100 %) | 2/2 (100 %) | 2/2 (100 %) | 345.5 / 336 |
| NTT DATA SE | 4 (4) | 1/4 (25 %) | 0/4 (0 %) | 1/4 (25 %) | 1/4 (25 %) | 2 / 2 |
| 1&1 AG | 1 (1) | 1/1 (100 %) | 0/1 (0 %) | 1/1 (100 %) | 0/1 (0 %) | 25 / 25 |
| Bechtle | 1 (1) | 1/1 (100 %) | 0/1 (0 %) | 1/1 (100 %) | 0/1 (0 %) | 6 / 6 |
| Cancom | 2 (2) | 2/2 (100 %) | 0/2 (0 %) | 0/2 (0 %) | 2/2 (100 %) | 7 / 7 |
| Carl Zeiss | 2 (2) | 2/2 (100 %) | 0/2 (0 %) | 0/2 (0 %) | 2/2 (100 %) | 59.5 / 58.5 |
| Compugroup Medical Deutschland | 1 (1) | 1/1 (100 %) | 0/1 (0 %) | 1/1 (100 %) | 1/1 (100 %) | 38 / 34 |
| Telekom | 7 (7) | 7/7 (100 %) | 0/7 (0 %) | 2/7 (29 %) | 7/7 (100 %) | 61 / 61 |
| Freenet | 5 (5) | 3/5 (60 %) | 0/5 (0 %) | 1/5 (20 %) | 3/5 (60 %) | 31 / 29 |
| **Gesamt** | 28 (28) | 23/28 (82 %) | 2/28 (7 %) | 9/28 (32 %) | 21/28 (75 %) | 45 / 43 |

**Vergleichsfenster**

| Unternehmen | Fenster (vollständig) | mit Ansatz | mit hoch | mit mittel | mit niedrig | Belege / Bündel je Fenster (Median) |
|---|---|---|---|---|---|---|
| E.ON | 3 (3) | 3/3 (100 %) | 0/3 (0 %) | 1/3 (33 %) | 3/3 (100 %) | 335 / 334 |
| RWE | 6 (6) | 6/6 (100 %) | 0/6 (0 %) | 0/6 (0 %) | 6/6 (100 %) | 171 / 170 |
| SAP SE | 6 (6) | 6/6 (100 %) | 0/6 (0 %) | 2/6 (33 %) | 6/6 (100 %) | 195.5 / 190.5 |
| NTT DATA SE | 10 (10) | 6/10 (60 %) | 0/10 (0 %) | 2/10 (20 %) | 5/10 (50 %) | 5 / 5 |
| 1&1 AG | 3 (3) | 2/3 (67 %) | 1/3 (33 %) | 2/3 (67 %) | 2/3 (67 %) | 30 / 30 |
| Bechtle | 3 (3) | 0/3 (0 %) | 0/3 (0 %) | 0/3 (0 %) | 0/3 (0 %) | 7 / 7 |
| Cancom | 6 (6) | 1/6 (17 %) | 0/6 (0 %) | 0/6 (0 %) | 1/6 (17 %) | 4 / 4 |
| Carl Zeiss | 5 (5) | 5/5 (100 %) | 0/5 (0 %) | 1/5 (20 %) | 4/5 (80 %) | 34 / 34 |
| Compugroup Medical Deutschland | 3 (3) | 3/3 (100 %) | 1/3 (33 %) | 0/3 (0 %) | 3/3 (100 %) | 25 / 23 |
| Telekom | 16 (16) | 16/16 (100 %) | 1/16 (6 %) | 10/16 (62 %) | 16/16 (100 %) | 60 / 59.5 |
| Freenet | 15 (15) | 10/15 (67 %) | 0/15 (0 %) | 4/15 (27 %) | 10/15 (67 %) | 41 / 41 |
| **Gesamt** | 76 (76) | 58/76 (76 %) | 3/76 (4 %) | 22/76 (29 %) | 56/76 (74 %) | 47.5 / 47 |

„mit Ansatz“ = mindestens ein Bündel der Stufe niedrig oder höher; „mit hoch/mittel/niedrig“ = mindestens ein Bündel dieser Stufe. Anteile beziehen sich auf die vollständig im Speicher liegenden Fenster (in Klammern). Die Abdeckungsquote nach NFA-05 (23/28, 82 %; Niveauwechsel 14/19, Einzelmonate 9/9) und die Vergleichsfenster mit Ansatz (58/76) sind dieselben wie in der ersten Fassung, weil die Menge der Bündel mit Stufe mindestens niedrig gleich bleibt.

| Oberste Stufe je Fenster (gesamt), zweite Fassung | hoch | mittel | niedrig | offen |
|---|---|---|---|---|
| Markierungsfenster | 2 | 7 | 14 | 5 |
| Vergleichsfenster | 3 | 20 | 35 | 18 |

Zusatzauswertung nach Referenzzeiträumen (E5): nicht verfügbar, Annotationsdatei ohne Einträge.

**Befund in einem Satz (zweite Fassung):** Auch mit der zweiten Fassung liegen die Anteile von
Markierungs- und Vergleichsfenstern in derselben Größenordnung (mit Stufe hoch 7 % gegen 4 %,
mittel 32 % gegen 29 %, niedrig 75 % gegen 74 %); die Rangfolge unterscheidet Markierungen nicht
erkennbar von Vergleichsfenstern, und keine der beiden Fassungen wird als „besser“ bewertet (E23).

## 6. Offene Punkte

- Ob ein Hinweis „Unternehmen im Titel nicht genannt“ die Stufe deckeln soll, oder ob
  Ausschlussbegriffe (`news_exclude`, zum Beispiel Rot-Weiss Essen bei RWE) besser sind (E18, D1).
- Ob die Themenverschiebung von 5 Prozentpunkten in großen Fenstern zu leicht erreicht wird; ein
  neuer Wert bräuchte einen dokumentierten Grund und einen neuen Auswertungslauf (E23).
- Eigene Wortangaben für Einzelmonate („im auffälligen Monat“) statt „Auswahl“ in der Antwort
  von `/compare`.
- Prüfung der Ansätze gegen die Referenzzeiträume (E5): Die Zusatzauswertung in
  `report_explanation_validity.py --annotations` ist festgelegt; sie läuft mit dem DZ1-Abgleich
  auf der geprüften Annotationsdatei des Autors (eine zweite Person stand nicht zur Verfügung,
  E5, Aktualisierung 2026-10-09).
- Ob die Bezeichnungen der Stufen (Kurzformen der Regeln) in den Interviews (DZ3) verständlich
  sind, oder ob die Regel selbst im Badge stehen sollte.
