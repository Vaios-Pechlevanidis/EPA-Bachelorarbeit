# Referenzzeiträume für die Validierung der Veränderungserkennung (DZ1) – Literaturnotiz

Stand: 2026-10-03, Zyklus 2 (Design Science Research). Begründet das Annotationsprotokoll für
`backend/data/annotations.json` (E5), ergänzt E3–E5 (`docs/entscheidungen.md`) und nutzt `docs/datenbasis.md`.
Wörtliche Zitate sind auf höchstens 20 Wörter gekürzt; die Fundstelle steht beim Zitat oder im Literatureintrag.

## 1 Fragestellung

Die Erkennung (DZ1) arbeitet auf Monatsreihen je Unternehmen, Quelle und Dimension (arithmetisches Mittel der
`durchschnittsbewertung`; Monate mit weniger als 5 Bewertungen werden nicht bewertet, E3/E4). Ihre Güte soll als
F1-Wert gegen manuell annotierte Referenzzeiträume extremer Anstiege/Abfälle gemessen werden. Vor dem ersten
Erkennungscode muss deshalb festgelegt sein:

- (a) Wie schnell und über welches Fenster reagieren Arbeitgeberbewertungen auf Unternehmensereignisse?
- (b) Welche Aggregationsfenster (Monat/Quartal/Jahr) verwendet die Literatur für Bewertungsreihen?
- (c) Wie werden menschlich annotierte Changepoints/Anomalien definiert und mit Detektionen abgeglichen
  (Toleranzmarge, Fensterlänge)?
- (d) Welche Mindestfallzahl je Periode gilt als tragfähig?

Vorweg: Keine der gefundenen Arbeiten untersucht „optimale Referenzzeiträume" für Arbeitgeberbewertungen
(Abschnitt 4). Das Protokoll in Abschnitt 3 überträgt deshalb Konventionen aus zwei Literatursträngen: Studien zu
Arbeitgeberbewertungsreihen (Finance/Accounting/HR) und Evaluationspraxis der Changepoint-/Anomalieerkennung.

## 2 Befunde

### 2.1 Reaktionsfenster von Arbeitgeberbewertungen auf Ereignisse

- **Quartal als belegter Reaktionshorizont.** Green et al. (2019) messen die Veränderung der Glassdoor-Bewertung
  als Mittel in Quartal t minus Mittel in Quartal t−1. Der Zusammenhang mit Aktienrenditen ist „concentrated in
  the calendar quarter following the change in employer ratings"; Renditen 4–6, 7–9 und 10–12 Monate nach der
  Änderung sind nicht signifikant, Gewinnüberraschungen 2–4 Quartale voraus „statistically indistinguishable from
  zero" (Manuskript Juli 2018, Fama-MacBeth-Abschnitt und Tab. IA.12;
  https://faculty.georgetown.edu/qw50/Green,Huang,Wen,Zhou_EmpRatings.pdf). Bewertungsänderungen selbst sind wenig
  persistent (adjustiertes R² 7,4 % bei Regression auf Vorquartale). Für DZ1 heißt das: Die Information einer
  Veränderung ist nach etwa einem Quartal „verbraucht"; ein Referenzzeitraum sollte in dieser Größenordnung liegen.
- **Tage bei exogenen, salienten Schocks.** Becker et al. (2022) aggregieren Glassdoor-Bewertungen auf Tagesebene
  (24-h-Fenster bis 16:00 ET) für 13.03.–31.12.2020 und finden sofortige Renditeeffekte (Koeffizient ≈ 0,05).
  Reaktionen in Tagen sind also möglich, setzen aber Russell-3000-Unternehmen und ein exogen vorgegebenes
  Ereignisfenster voraus; auf Kununu-Dichten nicht übertragbar.
- **Bewertungen laufen Ereignissen voraus.** Hales et al. (2018) und Huang et al. (2020) zeigen auf Abstract-Ebene,
  dass der Mitarbeiterausblick spätere Offenlegungen, Restrukturierungsaufwendungen und operative Leistung
  vorhersagt; Huang et al.: er „predicts bad news events more strongly than good news events"
  (https://doi.org/10.2308/accr-52519). Ein Ereignisanker kann also nach dem Referenzzeitraum liegen; Abfälle sind
  schärfer als Anstiege. Ein konkreter Vorlauf in Monaten ist aus Hales et al. nicht verifizierbar.
- **Größenordnung und Persistenz bei Restrukturierungen (Kununu).** Die Branchenstudie Restart Career & kununu
  (2024; ≈ 14.000 Sternebewertungen, 541 Kommentare, 16 Unternehmen mit Restrukturierung in den vorangegangenen
  drei Jahren) berichtet einen mittleren Rückgang des kununu-Scores um 11 % (bei Score 3,5 ≈ 0,4 Sterne),
  Extremfälle über 25 % (≈ 0,9 Sterne) und keine Erholung bei zwei Dritteln; „der kununu Score blieb
  durchschnittlich 6 Prozent im Minus"
  (https://www.personalintern.de/artikel/einfluss-von-restrukturierungen-auf-die-employer-brand/). Eine
  Vorher/Nachher-Fensterlänge nennt keine der drei Berichtsquellen.
- **Langsame Anpassung, Plattformfenster.** Cloos (2021, S. 166) illustriert hedonische Anpassung mit „After two
  months … After a further six months"; Kununu bietet Filter für Bewertungen „written in the last month, the last 6
  or 12 months" (S. 158; https://storage.imrpress.com/imr/journal/MRev/article/504088/1752843147684.pdf). Hoon et
  al. (2019, nach Cloos 2021, S. 155) finden nach „Dieselgate" in über 1.000 VW-Bewertungen keinen Anstieg
  destruktiver, aber einen Rückgang konstruktiver Stimme – Textverhalten, keine Sterne, Fenster unbekannt.
- **Jahresebene.** Chang et al. (2024) und Abdulsalam et al. (2025) zeigen, dass jährliche bzw. rollierend
  12-monatige Bewertungsänderungen CEO-Wechsel und Boni erklären; zur Monatsdynamik sagen sie nichts.

Fazit (a): Belegt ist ein Reaktionshorizont „innerhalb des Folgequartals" (Green et al.) und, bei exogenen
Schocks, von Tagen (Becker et al.). Eine Monatsauflösung der Reaktionsgeschwindigkeit auf Kununu ist nicht publiziert.

### 2.2 Aggregationsfenster und Mindestfallzahlen

| Quelle | Plattform | Aggregationseinheit | Mindestfallzahl |
|---|---|---|---|
| Green et al. 2019 | Glassdoor | Kalenderquartal; ΔRating = Mittel Q_t − Mittel Q_(t−1) | „a minimum of 15 reviews in each quarter" (Robustheit mit 10/20, Tab. IA.3) |
| Höllig et al. 2025 | Kununu | Quartal (Zeit-Fixed-Effects, 45 Quartale); Ereignisse nur monatsgenau: „Kununu discloses only the month of an employer response, not the exact date" (S. 1497) | ≥ 2 Bewertungen je Arbeitgeber (Stichprobenkriterium); Monats- und Quartalsergebnisse „fundamentally the same" |
| Chang et al. 2024 | Glassdoor | Geschäftsjahr; Monatstests mit rollierendem 12-Monats-Score | „we require a minimum of 10 employee reviews when averaging" (Abschn. 2.1) |
| Brede et al. 2025 | Glassdoor | kumuliertes Mittel aller Bewertungen vor der Ankündigung | „we require at least 10 Glassdoor reviews for both the acquirer and the target" |
| Cloos 2021 | Kununu/Glassdoor | Querschnitt; Kununu-Filter 1/6/12 Monate; Vorschlag „display the average review score of the last 12 or 24 months by default" (S. 173) | ≥ 10 Bewertungen je Unternehmen (S. 159); Kununu-Median 534 gesamt, 116,5 in 12 Monaten (Tab. 1) |
| Glassdoor 2022 (Awards DE) | Glassdoor | 12-Monats-Fenster: „Alle Bewertungen wurden zwischen dem 20. Oktober 2020 und dem 18. Oktober 2021 abgegeben." | ≥ 20 Bewertungen im Fenster |
| Becker et al. 2022 | Glassdoor | Kalendertag (Tagesmittel) | kein Minimum genannt |

Fazit (b)/(d): Die peer-reviewte Literatur arbeitet mit Quartal, Jahr oder rollierenden 12 Monaten; der Monat
kommt nur als Zeitstempel (Höllig et al.) oder Plattformfilter (Cloos) vor. Mindestfallzahlen liegen bei 10–20 je
Aggregat; eine Mindestzahl je Monat nennt keine Quelle. Die Schwelle 5/Monat aus E4 entspricht rechnerisch Greens
15/Quartal und liegt damit am unteren Rand des Üblichen.

### 2.3 Annotation und Abgleich bei Changepoint-/Anomalie-Evaluation

- **Menschliche Changepoint-Annotation (van den Burg & Williams 2020).** 42 reale Reihen (Länge 15–991, Mittel
  327,7), je fünf Annotatoren ohne Domänenwissen; Achsen ohne Datum und Werte, Reihennamen verborgen, damit kein
  Ereigniswissen einfließt. Rubrik: „Please mark the point(s) in the time series where an abrupt change in the
  behavior of the series occurs." Im Mittel 7,4 Changepoints je Reihe. Labels sind Zeitpunkte; Regionslabels
  (Hocking et al., nach van den Burg & Williams) gelten als zulässige, für lange Reihen einfachere Alternative;
  Übergänge über mehrere Schritte waren mehrdeutig: „ambiguity about whether the transition period should be
  marked as a separate segment or not" (Abschn. 4). Abgleich: F1 mit Toleranzmarge – „In the experiments we use a
  margin of error of M = 5." (≈ 1,5 % der mittleren Reihenlänge; Marge als Konvention nach Killick et al. 2012 und
  Truong et al. 2020) – und eigener Eins-zu-eins-Regel: „only one x ∈ X can be used for a single τ ∈ T" (Abschn. 3);
  Recall als Mittel über Annotatoren, zusätzlich Covering-Metrik; mediane Übereinstimmung der Annotatoren ≈ 0,8
  (Covering). https://arxiv.org/abs/2003.06222 (PDF Abschn. 3, 4.2–4.4).
- **Marge kleiner als Mindestabstand (Truong et al. 2020).** Precision/Recall mit nutzerdefinierter Marge M, ein
  wahrer Changepoint gilt als erkannt, wenn eine Detektion weniger als M Punkte entfernt liegt; „Precision and
  Recall are well-defined (ie. between 0 and 1) if the margin M is smaller than the minimum spacing" zweier wahrer
  Changepoints (Abschn. 3.2.4; https://arxiv.org/abs/1801.00718). Das Review ist zugleich die Grundlage der im
  Projekt eingesetzten Bibliothek `ruptures`, die einen Mindestabstand zwischen Changepoints als Parameter führt.
- **PELT (Killick et al. 2012).** Die in `ruptures` genutzte Suche minimiert Segmentkosten plus Strafterm, „βf(m)
  is a penalty to guard against over fitting"; „A larger minimum segment length is easily implemented when
  appropriate" (Abschn. 2; https://arxiv.org/abs/1101.1438) – das detektorseitige Gegenstück zu Regel 5.
- **Anomaliefenster statt Punkte (Lavin & Ahmad 2015, NAB).** 58 Dateien, 365.551 Punkte, Labels mehrerer Labeler
  nach dokumentierten Regeln, per Algorithmus kombiniert; Fenster je Label: „we define anomaly window length to be
  10% the length of a data file, divided by the number of anomalies"; nur die früheste Detektion im Fenster zählt;
  Anomalien gelten als selten; Fenstergröße (5–20 % geprüft): „the exact number is not critical" (Abschn. II.B; https://arxiv.org/abs/1510.03336).
- **Bereichsbasierte Metriken (Tatbul et al. 2018).** Recall je Bereich = α · Existenzbelohnung + (1 − α) ·
  Überlappungsbelohnung (Kardinalität, Größe, Lage), Precision nur über Überlappung; Einheitsbereiche und α = 0
  ergeben die klassischen Maße (Abschn. 4); NAB „remains point-based in nature and has a fixed bias (early
  detection)" (Abschn. 3). Regel 6 ist das Existenzkriterium je Annotation ohne Frühbonus. https://proceedings.neurips.cc/paper/2018/hash/8f468c873a32bb0619eaeb2050ba45d1-Abstract.html
- **Point-Adjust-Kritik (Kim et al. 2022).** Beim verbreiteten Point Adjustment gilt ein Segment als erkannt, sobald
  ein Punkt darin detektiert ist, und alle seine Punkte zählen als True Positives: „even a random anomaly score
  can easily turn into a state-of-the-art TAD method"; „its effect becomes less conspicuous with shorter anomaly
  segments" (Abschn. 5); Vorschlag PA%K (Abschn. 4.2; https://doi.org/10.1609/aaai.v36i7.20680). Für DZ1: Zählung
  je Annotation statt je Punkt, Regionen von 1–6 Monaten, Detektionen außerhalb als False Positives.
- **Benchmarkfehler (Wu & Keogh 2023).** „These flaws are triviality, unrealistic anomaly density, mislabeled
  ground truth and run-to-failure bias." Detektoren setzen ihr Label an Anfang, Ende oder Mitte einer Subsequenz
  und werden sonst „penalized because it reports a positive just to the left (or just to the right) of a labeled
  region" (Abschn. 2.4); daher „build some ‚slop' into what we accept as a correct answer" (Abschn. 4.4). Run-to-
  failure: Anomalien häufen sich am Reihenende (Abschn. 2.5) – nicht bevorzugt dort suchen. https://arxiv.org/abs/2009.13807
- **Verschiebungsrobustheit (Paparrizos et al. 2022, TSB-UAD).** 13.766 Reihen; F, Range-F und AUC-ROC gegen
  verschobene Scores, Rauschen und Anomalieanteil geprüft: „F and RF are less sensitive to lag" (Abschn. 6.1;
  https://doi.org/10.14778/3529337.3529354).

Fazit (c): Standard sind (1) Labeln durch Menschen ohne Kontextinformation, (2) eine kleine, vorab fixierte
Toleranzmarge (wenige Beobachtungen oder ein Anteil der Reihenlänge, kleiner als der Mindestabstand zweier Labels;
genaue Größe unkritisch, Spielraum nötig), (3) Eins-zu-eins-Zuordnung je Annotation statt je Punkt, (4) F1 als
Hauptmaß. Für Monatsreihen mit Reaktionen über 1–3 Monate (2.1) sind Regionslabels (period_from–period_to) passend.

### 2.4 Dynamik von Online-Bewertungsreihen

- **Rauschen dominiert kurze Differenzen.** Bei Green et al. (2019) hat die Quartalsänderung Mittel ≈ 0,01 und
  Standardabweichung 0,45 (bei ≥ 15 Bewertungen je Quartal). Kontrollrechnung auf den eigenen Serien-CSVs
  (`backend/data/series/*_employee.csv`, 15 Unternehmen mit ≥ 12 bewerteten Monaten, 1.004 Differenzen zwischen
  aufeinanderfolgenden bewerteten Monaten, berechnet am 2026-10-03): Median |Δ| = 0,36, 90-%-Quantil 0,95,
  Standardabweichung je Reihe im Median 0,52. Ein einzelner Monatssprung von 0,5 Sternen ist also kein Extrem,
  sondern etwa eine Standardabweichung Rauschen.
- **Drift und Plattformeffekte.** Cloos (2021, S. 169): Monate seit erster Bewertung wirken bei Kununu positiv auf
  den Score; 10 % mehr Bewertungen senken ihn um 0,1 Sterne. Plattformdesign (Filter, Standardfenster) verändert,
  was Nutzer sehen, nicht die Rohreihe.
- **Asymmetrie.** Negative Verschiebungen sind schärfer und persistenter (Huang et al. 2020; Restart Career &
  kununu 2024: zwei Drittel ohne Erholung); Anstiege verlaufen eher graduell.
- **Dünne Belegung.** Höllig et al. (2025): 298.269 Bewertungen auf 21.099 Arbeitgeber über 45 Quartale (≈ 14 je
  Arbeitgeber, eigene Division); Cloos (2021, Tab. 1): Median 116,5 in 12 Monaten bei 114 Großunternehmen. Die
  eigenen Dichten (Median 0–18 je Monat, `docs/datenbasis.md`) liegen darunter.
- **Streuung als Signal.** Könsgen et al. (2018): widersprüchliche Kununu-Bewertungen senken Bewerbungsabsichten;
  neben dem Monatsmittel ist also auch die Streuung informativ (hier nur als Angabe in der note genutzt).
- **Reihenfolge- und Kalenderzeiteffekte (Godes & Silva 2012).** Amazon-Buchbewertungen: „the nth rating is, on
  average, lower than the n-1th when controlling for time", nach Datumskontrolle dagegen „the residual average
  temporal pattern is increasing" (Abstract; https://doi.org/10.1287/mksc.1110.0653); Vorniveau daher lokal bestimmen.
- **Autokorrelation durch soziale Dynamik (Moe & Trusov 2011).** Produktbewertungen: „ratings behavior is
  significantly influenced by previously posted ratings", Effekte „relatively short lived once indirect effects
  are considered" (Abstract; https://doi.org/10.1509/jmkr.48.3.444); aufeinanderfolgende Monate sind nicht unabhängig.
- **Aggregation (Dai et al. 2018).** Yelp-Modell mit quartalsweise driftender Qualität: „the simple average weights
  every rating equally despite quality changes"; daher „more weight should be given to more recent reviews and more
  precise reviews" (NBER WP 18567; https://www.nber.org/papers/w18567). Kumulierte Plattform-Scores bilden
  Niveauwechsel verzögert ab; Monatsmittel (E3) sind die passendere Erkennungsbasis.
- **Verzögerte, persistente Reaktion auf ein datiertes Ereignis (Li & Pinto 2026).** 3,7 Mio. Glassdoor-Bewertungen
  2008–2022, Differenz-in-Differenzen um Börsengänge: „We observe no decline in satisfaction in the months and years
  leading up to the IPO", danach „The ratings decline after an IPO and remain lower for years" (Autorenzusammenfassung,
  CLS Blue Sky Blog 08.10.2025; https://doi.org/10.1287/mnsc.2023.04285); Fensterlänge im Volltext nicht prüfbar.

## 3 Abgeleitetes Annotationsprotokoll

Gilt für `backend/data/annotations.json` (Felder company, source, dimension, period_from, period_to, direction,
note; Prüfung mit `backend/scripts/validate_annotations.py`). Jede Regel nennt ihre Grundlage; „Setzung des
Autors" kennzeichnet Festlegungen ohne direkten Literaturbeleg.

1. **Einheit.** Einheit ist der Kalendermonat (YYYY-MM) der Erkennungsreihe aus E3. Ein Referenzzeitraum ist ein
   zusammenhängender Bereich [period_from, period_to] (Regionslabel), kein Einzelzeitpunkt. – Grundlage: E3/E5;
   Monat als feinste auf Kununu belegte Zeitauflösung (Höllig et al. 2025); Regionslabels als anerkannte
   Alternative zu Punktlabels (van den Burg & Williams 2020; Tatbul et al. 2018).
2. **Länge.** Der Zeitraum reicht vom ersten bewerteten Monat, in dem das Niveau abweicht, bis zum ersten
   bewerteten Monat, in dem das neue Niveau erreicht ist. Regelfall 1–3 Monate, Obergrenze 6 Kalendermonate.
   Längere monotone Verläufe sind Trends und werden nicht als Referenzzeitraum annotiert. – Grundlage: Reaktion
   innerhalb des Folgequartals (Green et al. 2019); 6 Monate als mittleres Plattformfenster und
   Anpassungshorizont (Cloos 2021); die Obergrenze 6 ist Setzung des Autors.
3. **Mindestfallzahl je Monat.** Betrachtet werden nur bewertete Monate (≥ 5 Bewertungen, E4); period_from und
   period_to müssen bewertete Monate sein; innerhalb des Zeitraums ist höchstens ein nicht bewerteter Monat
   zulässig. Monate mit 5–9 Bewertungen werden in der note mit Anzahl genannt und tragen einen Zeitraum nur, wenn
   mindestens ein weiterer bewerteter Monat die Abweichung stützt. – Grundlage: 5/Monat ≙ 15/Quartal (Green et al.
   2019); 10 je Aggregat als häufigster Literaturwert (Chang et al. 2024; Brede et al. 2025; Cloos 2021); die
   Lückenregel ist Setzung des Autors.
4. **Größenordnung (Richtwert).** Das Mittel der Monatsmittel im Referenzzeitraum weicht vom Mittel der bis zu
   sechs vorangehenden bewerteten Monate um mindestens 0,5 Sterne ab (bei Scores 3,5–4,0 ≈ 12–14 %). Ein einzelner
   Monatssprung reicht nicht. Kleinere Abweichungen werden nur mit Ereignisanker (Regel 7) und ausdrücklicher
   Begründung annotiert. – Grundlage: SD der Quartalsänderung 0,45 (Green et al. 2019); mittlerer Einbruch −11 %,
   Extreme über −25 % (Restart Career & kununu 2024); Kontrollrechnung in 2.4 (SD der Monatsdifferenzen ≈ 0,5);
   lokales Vorniveau wegen Drift (Godes & Silva 2012; Dai et al. 2018); der Wert 0,5 ist Setzung des Autors.
5. **Seltenheit.** Erwartet werden 0–3 Referenzzeiträume je Reihe; mehr als ein Zeitraum je 12 bewertete Monate
   deutet auf zu weiche Anwendung von Regel 4. Zwei Zeiträume derselben Reihe sind durch mindestens drei bewertete
   Monate getrennt. – Grundlage: Seltenheitsannahme (Lavin & Ahmad 2015; Wu & Keogh 2023); 7,4 Changepoints je
   Reihe mittlerer Länge 328 (van den Burg & Williams 2020); Marge kleiner als Mindestabstand (Truong et al.
   2020); Mindestsegmentlänge als Detektorparameter (Killick et al. 2012); die Zahlen sind Setzung des Autors.
6. **Toleranz beim Abgleich.** Eine Detektion im Monat m gilt als Treffer für einen Referenzzeitraum, wenn
   period_from − 1 ≤ m ≤ period_to + 1 (Kalendermonate). Ist der Nachbarmonat nicht bewertet, verschiebt sich die
   Grenze auf den nächsten bewerteten Monat, höchstens um 3 Kalendermonate. Jede Annotation zählt höchstens einmal
   als True Positive (früheste Detektion im Fenster, weitere werden ignoriert); Detektionen außerhalb jedes
   Fensters sind False Positives, nicht getroffene Annotationen False Negatives; Hauptmaß ist F1 je Quelle und
   über alle Reihen. – Grundlage: M = 5 bei mittlerer Länge 328 (≈ 1,5 %; van den Burg & Williams 2020) ergäbe bei
   12–165 bewerteten Monaten weniger als einen Monat; Monat und Quartal liefern gleiche Ergebnisse (Höllig et al.
   2025); Eins-zu-eins-Zuordnung (van den Burg & Williams 2020, Marge nach Killick et al. 2012; Lavin & Ahmad
   2015); Zählung je Annotation statt je Punkt vermeidet die Point-Adjust-Überschätzung (Kim et al. 2022);
   Spielraum um die Labelregion (Wu & Keogh 2023); ±1 Monat und die Lückenkappung sind Setzung des Autors.
7. **Ereignisanker.** Zweistufig: (A) Der Zeitraum wird zuerst allein aus der Serien-CSV beurteilt und die
   Beurteilung in der note festgehalten. (B) Erst danach wird nach einem unabhängigen Ereignis gesucht (Quellen
   aus E7: Google-News-RSS, EQS; nicht notierte Unternehmen per Namenssuche) und mit Datum und Quelle vermerkt.
   Ein Ereignis stützt den Zeitraum, wenn es frühestens 3 Monate vor period_from und spätestens in period_to
   datiert ist. Ein Ereignis ohne sichtbare Veränderung erzeugt keine Annotation; eine Veränderung ohne Ereignis
   wird nicht gelöscht. – Grundlage: Annotation ohne Kontextwissen (van den Burg & Williams 2020); Reaktion
   innerhalb eines Quartals (Green et al. 2019; Becker et al. 2022); Bewertungen laufen Ereignissen voraus (Hales
   et al. 2018; Huang et al. 2020; verzögert: Li & Pinto 2026); die 3-Monats-Grenze ist Setzung des Autors.
8. **Unabhängigkeit vom Erkennungscode.** annotations.json wird vollständig erstellt, validiert und in einem
   eigenen Commit versioniert, bevor Erkennungscode entsteht (E5). Regel 6 (Toleranz, Zuordnung, Maß) ist mit
   dieser Notiz fixiert und wird nach dem ersten Erkennungslauf nicht mehr geändert. Nachträgliche Änderungen an
   Annotationen erhöhen das Feld version, werden im Commit begründet und in der Arbeit ausgewiesen. Der Autor ist
   einziger Annotator; das wird als Limitation benannt. Optional annotiert eine zweite Person (z. B. aus DZ3) eine
   Teilmenge blind, um die Übereinstimmung zu schätzen. – Grundlage: E5; fünf Annotatoren mit medianer
   Covering-Übereinstimmung ≈ 0,8 (van den Burg & Williams 2020); fehlerhafte Labels als Benchmarkfehler, daher
   Versionierung (Wu & Keogh 2023); die Ein-Annotator-Lösung ist Setzung des Autors.
9. **Dünn belegte Unternehmen.** Unternehmen/Quellen mit weniger als 12 bewerteten Monaten (E4; Liste in
   `docs/datenbasis.md`) erhalten keine Einträge; sie gehen nicht in den F1-Wert ein und werden als Fallstudien ohne
   Zeitreihenevaluation geführt. Bei Quellen mit ≥ 12 bewerteten, aber stark lückigen Monaten gilt Regel 3 strikt.
   Eine spätere Quartalsreihe für dünne Unternehmen bräuchte eine eigene Annotationsdatei (Schema ist
   monatsbasiert). – Grundlage: Quartal/12 Monate als gröbere Einheiten (Green et al. 2019; Chang et al. 2024);
   die Ausschlussregel ist Setzung des Autors.
10. **Dimensionen.** Primär wird dimension = durchschnittsbewertung annotiert. Themen-Dimensionen nur, wenn eine
    von Erkennungscode unabhängige Begründung möglich ist (annotations.json, Vorgehen 4), nach denselben Regeln.
    – Grundlage: E3; Setzung des Autors.
11. **Dokumentation in note.** Pflichtinhalt, deutsch, in dieser Reihenfolge: Vorniveau (Mittel, Monate, n je
    Monat) – Niveau im Zeitraum (Mittel, n je Monat) – Differenz in Sternen – Richtung – ggf. Streuungshinweis –
    Ereignisanker: Datum, Quelle, URL oder „keiner" – Beurteilung: „Reihe allein" oder „Reihe + Ereignis".
    Beispiel: „Vorniveau 3,9 (2022-10 bis 2023-02, n=7–12); Zeitraum 3,1 (n=9, 11); Δ −0,8; fall; Anker:
    Vorstandswechsel 2023-04 (EQS, URL); Reihe + Ereignis." – Grundlage: Validator verlangt nicht-leere note; der
    Inhalt ist Setzung des Autors nach dem NAB-Prinzip dokumentierter Labelregeln (Lavin & Ahmad 2015).

Kurzfassung: Einheit Monat; Zeitraum 1–3 (max. 6) Monate; Toleranz ±1 bewerteter Monat (max. 3 Kalendermonate);
≥ 5 Bewertungen je Monat; Richtwert ≥ 0,5 Sterne Niveauunterschied; Ereignisanker nachgelagert und dokumentiert;
Annotation vor Code; Eins-zu-eins-Zuordnung und F1.

## 4 Was die Literatur NICHT hergibt

- **Kein Paper definiert oder optimiert „Referenzzeiträume" für Arbeitgeberbewertungen.** Weder für Kununu noch
  für Glassdoor existiert eine Arbeit, die Changepoints oder Anomalien in Bewertungsreihen menschlich annotiert,
  Toleranzmargen in Monaten festlegt oder eine Mindestzahl je Monat begründet. Das Protokoll ist eine Übertragung:
  Reaktionshorizont und Fallzahlen aus Ereignis-/Panelstudien (Quartal, 10–20 Bewertungen je Aggregat), Toleranz
  und Zuordnung aus der Changepoint-Evaluation (Marge, Eins-zu-eins-Zuordnung, F1). Die Zahlen in den Regeln 2,
  4, 5, 6 und 7 sind Setzungen des Autors innerhalb der von der Literatur gezogenen Spannen.
- **Reaktionsgeschwindigkeit auf Monatsebene** ist nicht publiziert; belegt sind „Folgequartal" (Green et al.
  2019) und „Tage" bei einem exogenen Schock (Becker et al. 2022). Für Hales et al. (2018) ließ sich ein konkreter
  Vorlauf nicht im Volltext prüfen; für Huang et al. (2020) ist die Aggregationsebene nicht verifiziert; die
  Zahlen zu Chang et al. (2024) stammen aus dem Arbeitspapier von 2021, nicht aus der Verlagsfassung.
- **Kununu-spezifisch** gibt es keine Zeitreihen- oder Ereignisstudie zu Sternebewertungen. Höllig, Tumasjan &
  Lievens (2024) und Koncar & Helic (2020) sind Querschnittsanalysen (nicht geöffnet, nicht zitiert). Hoon et al.
  (2019) ist nur über Cloos (2021) zugänglich und betrifft Texte, nicht Sterne. Die Restart-Career-Studie nennt
  keine Fensterlängen; ihr Primärbericht war nicht abrufbar, sie ist graue Literatur ohne Signifikanztests.
  Kununus eigene Methodenseiten (Score, Top-Company-Kriterien, Altersgewichtung ab 09/2026) waren nicht abrufbar
  (HTTP 405) und werden nicht zitiert; Glassdoors „Layoffs Cast a Long Shadow" ebenso (HTTP 403).
- **Changepoint-Konventionen stammen aus anderen Domänen** (Sensor-, Wirtschafts- und Serverdaten mit hunderten
  bis tausenden Punkten). M = 5 und „10 % der Reihenlänge" sind auf Monatsreihen mit 12–165 Punkten nicht direkt
  übertragbar; ±1 Monat ist eine Analogie, keine Ableitung; Point-Adjust-Kritik und Benchmarkfehler (Kim et al.
  2022; Wu & Keogh 2023) sind ebenfalls an Server- und Sensordaten formuliert.
- **Bewertungsdynamik stammt aus Produktmärkten.** Godes & Silva (2012), Moe & Trusov (2011) und Dai et al. (2018)
  betreffen Bücher, Konsumgüter und Restaurants; die Übertragung auf Arbeitgeberbewertungen ist ungeprüft.
- **Ein Annotator.** Die Literatur arbeitet mit mehreren Annotatoren und berichtet deren Übereinstimmung; hier
  nur optional vorgesehen, die Verlässlichkeit der Referenz ist daher nicht bezifferbar.
- **Nicht gefunden:** eine peer-reviewte Ereignisstudie zu Glassdoor-/Kununu-Sternen um Entlassungen oder
  CEO-Wechsel mit Monatsfenstern (Li & Pinto 2026 betrifft Börsengänge; Fensterlänge und Aggregationsebene ohne
  Volltext nicht prüfbar); eine Quelle, die ≥ 5 oder ≥ 10 Bewertungen je Monat empfiehlt; Kontrollkarten-/
  CUSUM-Anwendungen auf Arbeitgeberbewertungen (Funde betreffen nur Produkt-/Hotelbewertungen).

## 5 Literatur

Alle Einträge geprüft (Crossref/Semantic Scholar bzw. arXiv/NBER sowie Verlags-, Proceedings- oder Volltextseite geöffnet; Quellen zu 2.3/2.4 am 2026-10-03):

- Abdulsalam, K., Christensen, D. M., Graffin, S. D., & Li, J. (2025). Do Boards Reward and Punish CEOs Based on Employee Satisfaction Ratings? Organization Science, 36(2), 881–902. https://doi.org/10.1287/orsc.2021.15818
- Becker, M., Cardazzi, A., & McGurk, Z. (2022). Employee satisfaction and stock returns during the COVID-19 Pandemic. Journal of Behavioral and Experimental Finance, 33, 100603 (online 10 Nov 2021). https://doi.org/10.1016/j.jbef.2021.100603
- Brede, M., Gerstel, H., Wöhrmann, A., & Bausch, A. (2025). Mind the gap: the effect of cultural distance on mergers and acquisitions—evidence from glassdoor reviews. Review of Managerial Science, 19(8), 2279–2326 (online 5 Oct 2024). https://doi.org/10.1007/s11846-024-00811-8 (Zitat von https://link.springer.com/article/10.1007/s11846-024-00811-8)
- Chang, S.-J., Oh, J. Y. J., & Park, K. (2024). Crowd-sourced CEO approval and turnover. International Review of Financial Analysis, 96, 103587. https://doi.org/10.1016/j.irfa.2024.103587 (Zahlen aus dem Arbeitspapier vom 20.08.2021, https://apjfs.org/file/download/6737?view=1)
- Cloos, J. (2021). Employer Review Platforms – Do the Rating Environment and Platform Design affect the Informativeness of Reviews? Theory, Evidence, and Suggestions. management revue – Socio-Economic Studies, 32(3), 152–181. https://doi.org/10.5771/0935-9915-2021-3-152
- Dai, W., Jin, G. Z., Lee, J., & Luca, M. (2018). Aggregation of consumer ratings: an application to Yelp.com. Quantitative Marketing and Economics, 16(3), 289–339 (online 29 Dec 2017). https://doi.org/10.1007/s11129-017-9194-9 (Zitate aus NBER Working Paper 18567, November 2012, https://www.nber.org/papers/w18567)
- Glassdoor (2022). Die 25 besten Arbeitgeber Deutschlands für 2022: Glassdoor verleiht Awards für Mitarbeiterzufriedenheit [Pressemitteilung]. PR Newswire, 12.01.2022. https://www.prnewswire.com/de/pressemitteilungen/die-25-besten-arbeitgeber-deutschlands-fur-2022-glassdoor-verleiht-awards-fur-mitarbeiterzufriedenheit-837885895.html ; Gewichtung nach Aktualität: Ellis, J. (2017). What Everyone Gets Wrong About Glassdoor. ERE.net, 27.12.2017. https://www.ere.net/what-everyone-gets-wrong-about-glassdoor/
- Godes, D., & Silva, J. C. (2012). Sequential and Temporal Dynamics of Online Opinion. Marketing Science, 31(3), 448–473. https://doi.org/10.1287/mksc.1110.0653
- Green, T. C., Huang, R., Wen, Q., & Zhou, D. (2019). Crowdsourced employer reviews and stock returns. Journal of Financial Economics, 134(1), 236–251. https://doi.org/10.1016/j.jfineco.2019.03.012 (Zitate aus dem Manuskript Juli 2018, https://faculty.georgetown.edu/qw50/Green,Huang,Wen,Zhou_EmpRatings.pdf)
- Hales, J., Moon, J. R., Jr., & Swenson, L. A. (2018). A new era of voluntary disclosure? Empirical evidence on how employee postings on social media relate to future corporate disclosures. Accounting, Organizations and Society, 68–69, 88–108. https://doi.org/10.1016/j.aos.2018.04.004
- Höllig, C. E., Ademi, E., & Tumasjan, A. (2025). Employer Responsiveness to Online Reviews: A Signal of Caring About Employees. Human Resource Management, 64(5), 1481–1502. https://doi.org/10.1002/hrm.22316 (open access, CC BY 4.0; Zitate aus dem Volltext https://openscience.ub.uni-mainz.de/server/api/core/bitstreams/e3fb3c2d-b81e-4b4c-9336-d209c9a22e97/content)
- Hoon, C., Bormann, K. C., Graffius, M., & Hansen, C. (2019). The Impact of Organizational Scandals on Employee Voice Behaviors. Academy of Management Proceedings, 2019(1), 17206. https://doi.org/10.5465/AMBPP.2019.17206abstract (Inhalt nur nach Cloos 2021, S. 155, zitiert)
- Huang, K., Li, M., & Markov, S. (2020). What do employees know? Evidence from a social media platform. The Accounting Review, 95(2), 199–226. https://doi.org/10.2308/accr-52519 (online 1 Aug 2019)
- Killick, R., Fearnhead, P., & Eckley, I. A. (2012). Optimal Detection of Changepoints With a Linear Computational Cost. Journal of the American Statistical Association, 107(500), 1590–1598. https://doi.org/10.1080/01621459.2012.737745 (Preprint: https://arxiv.org/abs/1101.1438)
- Kim, S., Choi, K., Choi, H.-S., Lee, B., & Yoon, S. (2022). Towards a Rigorous Evaluation of Time-Series Anomaly Detection. Proceedings of the AAAI Conference on Artificial Intelligence, 36(7), 7194–7201. https://doi.org/10.1609/aaai.v36i7.20680 (Preprint: https://arxiv.org/abs/2109.05257)
- Könsgen, R., Schaarschmidt, M., Ivens, S., & Munzel, A. (2018). Finding Meaning in Contradiction on Employee Review Sites — Effects of Discrepant Online Reviews on Job Application Intentions. Journal of Interactive Marketing, 43, 165–177. https://doi.org/10.1016/j.intmar.2018.05.001
- Lavin, A., & Ahmad, S. (2015). Evaluating Real-Time Anomaly Detection Algorithms – The Numenta Anomaly Benchmark. In 2015 IEEE 14th International Conference on Machine Learning and Applications (ICMLA), Miami, FL (pp. 38–44). IEEE. https://doi.org/10.1109/ICMLA.2015.141 (Preprint: https://arxiv.org/abs/1510.03336)
- Li, M., & Pinto, J. (2026). How Does Going Public Affect Employee Satisfaction? Evidence from Glassdoor Reviews. Management Science, 72(6), 4871–4888 (online 22 Sep 2025). https://doi.org/10.1287/mnsc.2023.04285 (Volltext nicht geöffnet; Ereignisbefunde nach der Zusammenfassung der Autoren: CLS Blue Sky Blog, 08.10.2025, https://clsbluesky.law.columbia.edu/2025/10/08/the-hidden-cost-of-going-public-why-employees-become-less-happy-after-ipos/)
- Moe, W. W., & Trusov, M. (2011). The Value of Social Dynamics in Online Product Ratings Forums. Journal of Marketing Research, 48(3), 444–456. https://doi.org/10.1509/jmkr.48.3.444
- Paparrizos, J., Kang, Y., Boniol, P., Tsay, R. S., Palpanas, T., & Franklin, M. J. (2022). TSB-UAD: An End-to-End Benchmark Suite for Univariate Time-Series Anomaly Detection. Proceedings of the VLDB Endowment, 15(8), 1697–1711. https://doi.org/10.14778/3529337.3529354 (Volltext: https://www.vldb.org/pvldb/vol15/p1697-paparrizos.pdf)
- Restart Career GmbH & kununu (2024). Auswirkungen von Restrukturierungen auf die Employer Brand [Branchenstudie, Leitung: Dr. Sabrina Zeplin; Primärbericht nicht geöffnet]. Berichtet in: PERSONALintern (21.03.2024). Einfluss von Restrukturierungen auf die Employer Brand. https://www.personalintern.de/artikel/einfluss-von-restrukturierungen-auf-die-employer-brand/ ; Handelsblatt (08.05.2024). Arbeitgeber-Image: Wie schlechtes Krisenmanagement langfristig schadet. https://www.handelsblatt.com/unternehmen/management/arbeitgeber-image-wie-schlechtes-krisenmanagement-langfristig-schadet/100035300.html ; Haupt, F. (2024). Schlechte Kununu-Bewertung nach Stellenabbau: Was tun? Personalwirtschaft, 21.11.2024. https://www.personalwirtschaft.de/news/hr-organisation/schlechte-kununu-bewertung-und-jetzt-184173/
- Tatbul, N., Lee, T. J., Zdonik, S., Alam, M., & Gottschlich, J. (2018). Precision and Recall for Time Series. In Advances in Neural Information Processing Systems 31 (NeurIPS 2018). Curran Associates. https://proceedings.neurips.cc/paper/2018/hash/8f468c873a32bb0619eaeb2050ba45d1-Abstract.html (Preprint: https://arxiv.org/abs/1803.03639)
- Truong, C., Oudre, L., & Vayatis, N. (2020). Selective review of offline change point detection methods. Signal Processing, 167, 107299. https://doi.org/10.1016/j.sigpro.2019.107299 (Preprint: https://arxiv.org/abs/1801.00718)
- van den Burg, G. J. J., & Williams, C. K. I. (2020). An Evaluation of Change Point Detection Algorithms. arXiv:2003.06222 [stat.ML] (v3, 12 Feb 2022). https://arxiv.org/abs/2003.06222
- Wu, R., & Keogh, E. J. (2023). Current Time Series Anomaly Detection Benchmarks are Flawed and are Creating the Illusion of Progress. IEEE Transactions on Knowledge and Data Engineering, 35, 2421–2429 (online 14 Sep 2021). https://doi.org/10.1109/TKDE.2021.3112126 (Preprint: https://arxiv.org/abs/2009.13807; Band und Seiten nach Semantic Scholar, Heftnummer nicht geprüft)
