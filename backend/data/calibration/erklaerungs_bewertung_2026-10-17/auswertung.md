# Bewertung der Erklärungsansätze: Passung und Unterschied

Stand 2026-10-17T23:00:37+00:00; Permutationen 20000, Startwert 20261017.

## Teil A: Unterscheiden die Stufen Markierungs- von Vergleichsfenstern?

Grundlage: `data/calibration/explanation_validity_korrektur_2026-10-13.json` (100 Fenster, davon 100 vollständig im Speicher; 28 Markierungen in Clustern mit 72 Vergleichsfenstern).

Lesart der Spalten: Fisher behandelt die Fenster als unabhängig; der Permutationstest vergibt die Rolle „Markierung“ innerhalb jedes Clusters (Markierung und ihre verschobenen Fenster desselben Unternehmens) zufällig neu und ist deshalb der angemessene Test. „Nachweisbar wäre“ nennt den Anteil bei Markierungen, ab dem ein Unterschied zum Vergleichsanteil mit diesen Fallzahlen überhaupt mit 80 % Teststärke gefunden würde.

**Gesamt**

| Merkmal | Markierungen | Vergleichsfenster | Differenz | 95 %-Intervall (Newcombe) | p Fisher | p Permutation (Cluster) | nachweisbar wäre (Anteil bei Markierungen) |
|---|---|---|---|---|---|---|---|
| mindestens ein Ansatz (Stufe mindestens niedrig) | 23/28 (82 %) | 57/72 (79 %) | 3 pp | [-16; +18] pp | 1,000 | 0,755 | ≥ 96 % oder ≤ 49 % |
| oberste Stufe mindestens mittel | 15/28 (54 %) | 32/72 (44 %) | 9 pp | [-12; +29] pp | 0,505 | 0,442 | ≥ 73 % oder ≤ 18 % |
| mindestens ein Bündel der Stufe hoch | 3/28 (11 %) | 5/72 (7 %) | 4 pp | [-7; +21] pp | 0,683 | 0,644 | ≥ 33 % |
| Fenster mit kennzeichnenden Begriffen | 21/28 (75 %) | 54/72 (75 %) | 0 pp | [-20; +17] pp | 1,000 | 1,000 | ≥ 94 % oder ≤ 45 % |
| oberste Stufe (offen 0, niedrig 1, mittel 2, hoch 3) | Mittel 1,46 | Mittel 1,31 | 0,16 | – | – | 0,389 | – |

Gepaart je Cluster (oberste Stufe der Markierung minus Mittel ihrer Vergleichsfenster, 27 Paare): Markierung höher 13, gleich 6, niedriger 8; mittlere Differenz 0,13.

**Niveauwechsel** (19 Markierungen, 48 Vergleichsfenster)

| Merkmal | Markierungen | Vergleichsfenster | Differenz | 95 %-Intervall (Newcombe) | p Fisher | p Permutation (Cluster) | nachweisbar wäre (Anteil bei Markierungen) |
|---|---|---|---|---|---|---|---|
| mindestens ein Ansatz (Stufe mindestens niedrig) | 14/19 (74 %) | 38/48 (79 %) | -5 pp | [-30; +14] pp | 0,747 | 0,718 | ≥ 98 % oder ≤ 43 % |
| oberste Stufe mindestens mittel | 13/19 (68 %) | 23/48 (48 %) | 20 pp | [-6; +42] pp | 0,176 | 0,168 | ≥ 80 % oder ≤ 17 % |
| mindestens ein Bündel der Stufe hoch | 2/19 (11 %) | 4/48 (8 %) | 2 pp | [-11; +24] pp | 1,000 | 1,000 | ≥ 42 % |
| Fenster mit kennzeichnenden Begriffen | 19/19 (100 %) | 45/48 (94 %) | 6 pp | [-11; +17] pp | 0,553 | 0,505 | ≤ 61 % |
| oberste Stufe (offen 0, niedrig 1, mittel 2, hoch 3) | Mittel 1,53 | Mittel 1,35 | 0,17 | – | – | 0,527 | – |

**Einzelmonate** (9 Markierungen, 24 Vergleichsfenster)

| Merkmal | Markierungen | Vergleichsfenster | Differenz | 95 %-Intervall (Newcombe) | p Fisher | p Permutation (Cluster) | nachweisbar wäre (Anteil bei Markierungen) |
|---|---|---|---|---|---|---|---|
| mindestens ein Ansatz (Stufe mindestens niedrig) | 9/9 (100 %) | 19/24 (79 %) | 21 pp | [-11; +40] pp | 0,290 | 0,126 | ≤ 30 % |
| oberste Stufe mindestens mittel | 2/9 (22 %) | 9/24 (38 %) | -15 pp | [-41; +21] pp | 0,681 | 0,556 | ≥ 83 % oder ≤ 4 % |
| mindestens ein Bündel der Stufe hoch | 1/9 (11 %) | 1/24 (4 %) | 7 pp | [-12; +40] pp | 0,477 | 1,000 | ≥ 52 % |
| Fenster mit kennzeichnenden Begriffen | 2/9 (22 %) | 9/24 (38 %) | -15 pp | [-41; +21] pp | 0,681 | 0,654 | ≥ 83 % oder ≤ 4 % |
| oberste Stufe (offen 0, niedrig 1, mittel 2, hoch 3) | Mittel 1,33 | Mittel 1,21 | 0,12 | – | – | 0,733 | – |

**Markierungen mit gegen ohne Referenzzeitraum (E5)**

| Merkmal | mit Referenzzeitraum | ohne | Differenz | 95 %-Intervall | p Fisher |
|---|---|---|---|---|---|
| mindestens ein Ansatz (Stufe mindestens niedrig) | 7/8 (88 %) | 16/20 (80 %) | 8 pp | [-29; +31] pp | 1,000 |
| oberste Stufe mindestens mittel | 6/8 (75 %) | 9/20 (45 %) | 30 pp | [-10; +56] pp | 0,221 |
| mindestens ein Bündel der Stufe hoch | 1/8 (12 %) | 2/20 (10 %) | 2 pp | [-20; +38] pp | 1,000 |
| Fenster mit kennzeichnenden Begriffen | 8/8 (100 %) | 13/20 (65 %) | 35 pp | [-2; +57] pp | 0,075 |

**Nullmodell: folgt die Stufe der Zahl der Belege?**

Spearman ρ Belege ↔ oberste Stufe: 0,40 (p < 0,001, n 100); Belege ↔ mit Ansatz: 0,55 (p < 0,001).

| Belege je Fenster (Drittel) | Spanne | Markierungen mit Ansatz | Vergleichsfenster mit Ansatz |
|---|---|---|---|
| wenige | 1–21 | 5/9 (56 %) | 11/23 (48 %) |
| mittel | 25–58 | 8/9 (89 %) | 21/24 (88 %) |
| viele | 61–510 | 10/10 (100 %) | 25/25 (100 %) |

## Teil B: Passung der Erklärungsansätze (blinde Urteile)

184 Urteile zu 80 von 100 Fenstern (die übrigen sind offen, ohne Ansatz). Schwelle „passend“: Passung mindestens 2 (teilweise passend).

**Markierungen gegen Vergleichsfenster (nur Fenster mit Ansatz)**

| Merkmal | Markierungen | Vergleichsfenster | Differenz | 95 %-Intervall | p Fisher | p Permutation (Cluster) | nachweisbar wäre |
|---|---|---|---|---|---|---|---|
| oberster Ansatz passend (≥ 2) | 6/23 (26 %) | 15/49 (31 %) | -5 pp | [-24; +19] pp | 0,786 | 0,784 | ≥ 64 % oder ≤ 7 % |
| bester Ansatz passend (≥ 2) | 10/23 (43 %) | 27/49 (55 %) | -12 pp | [-34; +12] pp | 0,450 | 0,363 | ≥ 84 % oder ≤ 23 % |
| Passung des obersten Ansatzes (Mittel 0–3) | 1,09 (n 23) | 1,22 (n 49) | -0,14 | – | – | 0,512 | – |

Verteilung der Passung des obersten Ansatzes: Markierungen {'0': 5, '1': 12, '2': 5, '3': 1}, Vergleichsfenster {'0': 8, '1': 26, '2': 11, '3': 4}.

**Alle Fenster (offen zählt als Passung 0)**

| Merkmal | Markierungen | Vergleichsfenster | Differenz | 95 %-Intervall | p Fisher | p Permutation (Cluster) | nachweisbar wäre |
|---|---|---|---|---|---|---|---|
| bester Ansatz passend (≥ 2) | 10/28 (36 %) | 30/72 (42 %) | -6 pp | [-25; +15] pp | 0,654 | 0,596 | ≥ 71 % oder ≤ 16 % |
| Passung des obersten Ansatzes (Mittel 0–3) | 0,89 (n 28) | 0,92 (n 72) | -0,02 | – | – | 1,000 | – |

**Je Art der Markierung (nur Fenster mit Ansatz)**

| Art | Markierungen: bester Ansatz passend | Vergleichsfenster | p Permutation | Passung oben (Mittel) Markierung / Vergleich | p Permutation |
|---|---|---|---|---|---|
| Niveauwechsel | 6/14 (43 %) | 15/30 (50 %) | 0,678 | 1,29 / 1,17 | 0,742 |
| Einzelmonate | 4/9 (44 %) | 12/19 (63 %) | 0,462 | 0,78 / 1,32 | 0,101 |

**Stufe des Systems gegen Passung (alle Urteile)**

| Stufe | n | Passung 0 | 1 | 2 | 3 | Mittel | passend (≥ 2) |
|---|---|---|---|---|---|---|---|
| hoch | 9 | 0 | 6 | 0 | 3 | 1,67 | 3/9 (33 %) |
| mittel | 82 | 21 | 35 | 22 | 4 | 1,11 | 26/82 (32 %) |
| niedrig | 93 | 22 | 50 | 17 | 4 | 1,03 | 21/93 (23 %) |

Spearman ρ Stufe ↔ Passung: 0,09 (p 0,203, n 184).

**Signale gegen Passung**

| Signal | mit: n / Mittel / passend | ohne: n / Mittel / passend | p Fisher (passend) |
|---|---|---|---|
| Wortbezug (term_match ≥ 0,5) | 27 / 1,26 / 5/27 (19 %) | 157 / 1,07 / 45/157 (29 %) | 0,352 |
| Ereignisart erkannt (category_match ≥ 0,5) | 167 / 1,11 / 49/167 (29 %) | 17 / 0,94 / 1/17 (6 %) | 0,044 |
| Themenverschiebung (category_match ≥ 1) | 93 / 1,18 / 32/93 (34 %) | 91 / 1,01 / 18/91 (20 %) | 0,031 |
| Ereignisart mit Arbeitgeberbezug | 167 / 1,11 / 49/167 (29 %) | 7 / 1,29 / 1/7 (14 %) | 0,675 |
| Unternehmen im Titel genannt | 114 / 1,41 / 44/114 (39 %) | 70 / 0,59 / 6/70 (9 %) | < 0,001 |
| EQS-Mitteilung | 22 / 1,45 / 11/22 (50 %) | 162 / 1,05 / 39/162 (24 %) | 0,019 |

**Ereignisarten gegen Passung**

| Ereignisart | n | Mittel | passend (≥ 2) |
|---|---|---|---|
| Übernahme, Fusion und Verkauf | 35 | 1,20 | 13/35 (37 %) |
| Rechtsstreit, Compliance und Skandal | 32 | 0,84 | 4/32 (12 %) |
| Führungswechsel | 27 | 1,44 | 16/27 (59 %) |
| Vergütung und Sozialleistungen | 14 | 1,00 | 3/14 (21 %) |
| Standort: Schließung, Verlagerung, Neubau | 12 | 0,50 | 1/12 (8 %) |
| Krise und Geschäftslage: Gewinnwarnung, Verlust, Sparprogramm | 11 | 0,82 | 1/11 (9 %) |
| ohne Ereignisart | 10 | 0,70 | 0/10 (0 %) |
| Einstellungen und Ausbildung | 8 | 0,75 | 0/8 (0 %) |
| Personalabbau und Restrukturierung | 8 | 1,62 | 4/8 (50 %) |
| Ohne Arbeitgeberbezug: Börsenbericht, Kursziel, Sport, Produkt | 7 | 1,29 | 1/7 (14 %) |
| Unternehmenskultur, Gleichstellung und Diversität | 7 | 0,86 | 1/7 (14 %) |
| Tarifverhandlung und Streik | 6 | 1,83 | 3/6 (50 %) |
| Arbeitsmodell: Homeoffice, Arbeitszeit, Büro | 4 | 2,00 | 2/4 (50 %) |
| Arbeitgeberauszeichnung und Ranking | 3 | 1,67 | 1/3 (33 %) |

**Richtung der Meldung zur Richtung der Veränderung (Urteil)**

| Gruppe | passt | neutral | widerspricht | unklar |
|---|---|---|---|---|
| Markierungen | 7 | 23 | 6 | 17 |
| Vergleichsfenster | 16 | 65 | 16 | 34 |

Rangfolge: In 37/60 (62 %) der Fenster mit mindestens zwei bewerteten Ansätzen steht der passendste (oder ein gleich passender) Ansatz oben.

Referenz (E5, nur Markierungen mit Ansatz): mit Referenzzeitraum bester Ansatz passend 3/7 (43 %), Mittel oben 1,29; ohne 7/16 (44 %), Mittel 1,00; p Fisher 1,000.

Prüfung der Urteile: 184 von 184 bewertet.

Beschreibende Zahlen und Tests gegen die Nullhypothese 'kein Unterschied'. Ein Unterschied oder dessen Fehlen sagt nichts über Ursachen; ein Erklärungsansatz bleibt ein möglicher Zusammenhang. Die Passungsurteile stammen von einer bewertenden Instanz (Agent oder Person), die den Bogen blind gelesen hat; die Verblindung ist unvollständig, weil Unternehmen, Monate und Richtung sichtbar sind.

## Anhang: alle Urteile (entblindet, ohne Titel)

| Kennung | Unternehmen | Art | Markierung | Gruppe | Versatz | Rang | Stufe | Ereignisart | Passung | Richtung | Begründung |
|---|---|---|---|---|---|---|---|---|---|---|---|
| F-011 | 1&1 AG | niveauwechsel | 2016-10 | vergleich | -24 | 1 | hoch | Übernahme, Fusion und Verkauf | 1 | neutral | Übernahmeabsichten des Mutterkonzerns, geäußert vom Konzernchef, im markierten Monat; Strategieaussage ohne Belegschaftsbezug für die Tochter, Wortbezug 'internet' ist Teil des Konzernnamens und damit mehrdeutig. |
| F-011 | 1&1 AG | niveauwechsel | 2016-10 | vergleich | -24 | 2 | niedrig | Rechtsstreit, Compliance und Skandal | 1 | neutral | Klagen zum Leistungsschutzrecht gegen das Unternehmen drei Monate vor dem Übergang; Rechtsstreit ohne Arbeitgeberbezug. |
| F-011 | 1&1 AG | niveauwechsel | 2016-10 | vergleich | -24 | 3 | niedrig | – | 1 | neutral | Mehr Geschwindigkeit für Bestandskunden im Mobilfunk drei Monate vor dem Übergang; Produktmeldung ohne Arbeitgeberbezug, Wortbezug 'internet' mehrdeutig. |
| F-021 | 1&1 AG | niveauwechsel | 2016-10 | markierung | +0 | 1 | mittel | Übernahme, Fusion und Verkauf | 0 | unklar | Vertriebsverkauf einer Tochter eines damals eigenständigen Wettbewerbers; fremder Treffer, zeitlich zudem erst nach dem markierten Monat. |
| F-076 | 1&1 AG | niveauwechsel | 2016-10 | vergleich | +12 | 1 | mittel | Führungswechsel | 2 | neutral | Wechsel des Aufsichtsratsvorsitzes nach Abschluss der Gesamttransaktion im Monat nach dem markierten Monat; der genannte Rechtsträger ist der aus der Fusion hervorgegangene heutige Träger des Unternehmens, Führungswechsel auf Kontrollebene, Richtung ohne Wertung, Lage danach. |
| F-076 | 1&1 AG | niveauwechsel | 2016-10 | vergleich | +12 | 2 | mittel | Übernahme, Fusion und Verkauf | 3 | passt | Einordnung der Fusion des Mutterkonzerns mit einem Mobilfunkanbieter zwei Monate vor dem Übergang; die eigene Gesellschaft wurde in den Partner eingebracht, die Zusammenführung betrifft die Belegschaft, Unsicherheit als belastende Stoßrichtung passt zum Abfall, der Begriff 'arbeitnehmervertretung' tritt neu auf. Das Unternehmen selbst ist im Titel nur über den Mutterkonzern genannt. |
| F-017 | Bechtle | niveauwechsel | 2016-02 | markierung | +0 | 1 | mittel | Führungswechsel | 2 | neutral | Benennung eines Nachfolgers für eine Führungsposition im Monat vor dem Übergang; Führungswechsel mit Arbeitgeberbezug, Richtung ohne Wertung. |
| F-031 | Cancom | einzelmonat | 2016-05 | markierung | +0 | 1 | niedrig | Standort: Schließung, Verlagerung, Neubau | 0 | unklar | Allgemeiner Fachartikel zum Wechsel in Cloud-Dienste im Monat nach dem auffälligen Monat; kein Unternehmen genannt, Ereignisart Standort ist ein Fehltreffer des Wortes Umzug. |
| F-088 | Cancom | einzelmonat | 2017-08 | markierung | +0 | 1 | niedrig | Führungswechsel | 1 | neutral | Neue Leitung einer Systemhaus-Einheit ohne Nennung des Unternehmens im Monat vor dem auffälligen Monat; Führungswechsel auf Bereichsebene, Zuordnung unsicher, Richtung ohne Wertung. |
| F-023 | Cancom | einzelmonat | 2017-08 | vergleich | +12 | 1 | niedrig | Führungswechsel | 2 | neutral | Übergabe des Vorstandsvorsitzes vom Gründer an einen Nachfolger im auffälligen Monat; Führungswechsel an der Spitze mit Arbeitgeberbezug, Richtung ohne Wertung. |
| F-042 | Carl Zeiss | einzelmonat | 2016-11 | vergleich | -24 | 1 | niedrig | Unternehmenskultur, Gleichstellung und Diversität | 1 | neutral | Produktvorstellung der Medizintechnik-Tochter auf einem Fachkongress zwei Monate vor dem auffälligen Monat; Produktmeldung ohne Arbeitgeberbezug, Ereignisart Diversität ist ein Fehltreffer des Wortes Vielfalt. |
| F-042 | Carl Zeiss | einzelmonat | 2016-11 | vergleich | -24 | 2 | niedrig | Führungswechsel | 0 | unklar | Abgang des Vorstandschefs eines Lichttechnikkonzerns; fremder Treffer. |
| F-083 | Carl Zeiss | einzelmonat | 2016-11 | vergleich | -12 | 1 | niedrig | Personalabbau und Restrukturierung | 1 | widerspricht | Warnung des Betriebsrats vor Gefahr für ein Werk nach Stellenabbau im Monat vor dem auffälligen Monat; Personalabbau mit klarem Arbeitgeberbezug, die belastende Stoßrichtung widerspricht dem Anstieg. |
| F-058 | Carl Zeiss | einzelmonat | 2016-11 | markierung | +0 | 1 | niedrig | Übernahme, Fusion und Verkauf | 1 | neutral | Einstieg eines Halbleiterausrüsters bei einer Tochter im auffälligen Monat; Beteiligungs- und Kapitalmarktmeldung ohne erkennbaren Belegschaftsbezug im Titel, Richtung ohne Wertung. |
| F-010 | Carl Zeiss | einzelmonat | 2016-11 | vergleich | +12 | 1 | niedrig | Einstellungen und Ausbildung | 1 | widerspricht | Preis für eine Auszubildende in einem regionalen Wettbewerb im Monat vor dem auffälligen Monat; das Unternehmen ist höchstens am Rand beteiligt, die positive Meldung widerspricht dem Abfall. |
| F-010 | Carl Zeiss | einzelmonat | 2016-11 | vergleich | +12 | 2 | niedrig | Personalabbau und Restrukturierung | 3 | passt | Geplanter umfangreicher Stellenabbau an einem Standort des Unternehmens im Monat vor dem auffälligen Monat; Personalabbau mit klarem Arbeitgeberbezug, belastende Stoßrichtung passt zum Abfall. |
| F-010 | Carl Zeiss | einzelmonat | 2016-11 | vergleich | +12 | 3 | niedrig | Führungswechsel | 1 | neutral | Einwortiger Titel zu einem Führungswechsel ohne erkennbaren Bezug zum Unternehmen; Zuordnung nicht nachvollziehbar, Richtung ohne Wertung. |
| F-064 | Carl Zeiss | einzelmonat | 2024-12 | vergleich | -24 | 1 | niedrig | Standort: Schließung, Verlagerung, Neubau | 3 | passt | Geplanter neuer Standort in einer Nachbarstadt im Monat vor dem auffälligen Monat; Standortthema mit Arbeitgeberbezug, die positive Stoßrichtung passt zum Anstieg. Der auffällige Monat hat eine sehr kleine Basis. |
| F-064 | Carl Zeiss | einzelmonat | 2024-12 | vergleich | -24 | 2 | niedrig | Einstellungen und Ausbildung | 1 | passt | Liste der besten Ausbildungsbetriebe mit offenen Lehrstellen im Monat vor dem auffälligen Monat; das Unternehmen höchstens in einer Aufzählung am Rand, positive Stoßrichtung. |
| F-064 | Carl Zeiss | einzelmonat | 2024-12 | vergleich | -24 | 3 | niedrig | Führungswechsel | 2 | neutral | Ausscheiden eines Vorstandsmitglieds der Medizintechnik-Tochter drei Monate vor dem auffälligen Monat; Führungswechsel mit allgemeinem Arbeitgeberbezug, Richtung ohne Wertung. |
| F-013 | Carl Zeiss | einzelmonat | 2024-12 | vergleich | -12 | 1 | niedrig | Übernahme, Fusion und Verkauf | 2 | neutral | Vereinbarte Übernahme eines Augenchirurgie-Anbieters durch die börsennotierte Medizintechnik-Tochter im auffälligen Monat; Konzernvorgang ohne erkennbaren Belegschaftsbezug, Richtung ohne Wertung. |
| F-013 | Carl Zeiss | einzelmonat | 2024-12 | vergleich | -12 | 2 | niedrig | Tarifverhandlung und Streik | 1 | neutral | Kameravergleich eines Smartphones mit Optik des Unternehmens im Monat vor dem auffälligen Monat; Produktmeldung ohne Arbeitgeberbezug, die Ereignisart Tarif und Streik ist ein Fehltreffer eines mehrdeutigen Schlüsselworts. |
| F-013 | Carl Zeiss | einzelmonat | 2024-12 | vergleich | -12 | 3 | niedrig | Vergütung und Sozialleistungen | 1 | widerspricht | Erfolgsbeteiligung für die Mitarbeitenden, gemeldet am Ende des auffälligen Monats; Vergütungsthema mit Arbeitgeberbezug, die entlastende Stoßrichtung widerspricht dem Abfall. |
| F-066 | Carl Zeiss | einzelmonat | 2024-12 | markierung | +0 | 1 | niedrig | Krise und Geschäftslage: Gewinnwarnung, Verlust, Sparprogramm | 0 | unklar | Forschungsmeldung einer Universität zur Antibiotikaentwicklung; kein Bezug zum Unternehmen, Ereignisart Krise ist ein Fehltreffer. |
| F-066 | Carl Zeiss | einzelmonat | 2024-12 | markierung | +0 | 2 | niedrig | Arbeitsmodell: Homeoffice, Arbeitszeit, Büro | 1 | widerspricht | Einführung der 35-Stunden-Woche an einem Standort zwei Monate vor dem auffälligen Monat; Arbeitsmodell mit Arbeitgeberbezug, die entlastende Stoßrichtung widerspricht dem Abfall. |
| F-066 | Carl Zeiss | einzelmonat | 2024-12 | markierung | +0 | 3 | niedrig | Führungswechsel | 2 | neutral | Benennung eines neuen Vorstandsvorsitzenden zwei Monate vor dem auffälligen Monat; Führungswechsel an der Spitze mit Arbeitgeberbezug, Richtung ohne Wertung. |
| F-098 | Compugroup Medical Deutschland | niveauwechsel | 2022-08 | vergleich | -24 | 1 | mittel | Übernahme, Fusion und Verkauf | 2 | neutral | Abschluss der Übernahme von Teilen des europäischen Krankenhaus-IT-Geschäfts eines US-Anbieters im Monat vor dem Übergang; Konzernvorgang ohne erkennbaren Belegschaftsbezug im Titel, Richtung ohne Wertung. |
| F-049 | Compugroup Medical Deutschland | niveauwechsel | 2022-08 | vergleich | -12 | 1 | mittel | – | 0 | unklar | Porträt des Vorstandschefs eines Telekommunikationskonzerns; fremder Treffer, Wortbezug 'erfolg' zufällig. |
| F-049 | Compugroup Medical Deutschland | niveauwechsel | 2022-08 | vergleich | -12 | 2 | niedrig | Vergütung und Sozialleistungen | 1 | neutral | Quartalsmitteilung mit Wachstumszahlen drei Monate vor dem Übergang; Kapitalmarktmitteilung ohne Arbeitgeberbezug, Ereignisart Vergütung ist ein Fehltreffer des englischen Wortes für Nutzen. |
| F-049 | Compugroup Medical Deutschland | niveauwechsel | 2022-08 | vergleich | -12 | 3 | niedrig | Übernahme, Fusion und Verkauf | 2 | neutral | Übernahme eines Anbieters für Bildmanagement zwei Monate vor dem Übergang; Konzernvorgang ohne erkennbaren Belegschaftsbezug in diesem Fenster, Richtung ohne Wertung. |
| F-051 | Compugroup Medical Deutschland | niveauwechsel | 2022-08 | markierung | +0 | 1 | mittel | Führungswechsel | 2 | neutral | Ernennung des Finanzvorstands zum Sprecher der Geschäftsführung zwei Monate vor dem Übergang; Führungswechsel an der Spitze mit Arbeitgeberbezug, Richtung ohne Wertung. |
| F-051 | Compugroup Medical Deutschland | niveauwechsel | 2022-08 | markierung | +0 | 2 | mittel | Rechtsstreit, Compliance und Skandal | 0 | unklar | Karrieren früherer Führungskräfte eines insolventen Zahlungsdienstleisters; fremder Treffer. |
| F-051 | Compugroup Medical Deutschland | niveauwechsel | 2022-08 | markierung | +0 | 3 | niedrig | – | 1 | neutral | Rekordergebnis auf der virtuellen Hauptversammlung drei Monate vor dem Übergang; Kapitalmarktmitteilung ohne Arbeitgeberbezug, Wortbezug 'meetings' zufällig. |
| F-025 | Compugroup Medical Deutschland | niveauwechsel | 2022-08 | vergleich | +12 | 1 | hoch | Führungswechsel | 3 | neutral | Geschäftsführerwechsel bei einer zwei Jahre zuvor übernommenen Tochter im markierten Monat; der stark gestiegene Begriff 'visus' in den Bewertungen benennt dieselbe Einheit, dazu treten 'übernahme' und 'früher' auf. Meldung und Bewertungen zeigen auf dasselbe Ereignis, die Stoßrichtung des Wechsels selbst ist ohne Wertung. |
| F-025 | Compugroup Medical Deutschland | niveauwechsel | 2022-08 | vergleich | +12 | 2 | niedrig | – | 0 | unklar | Ratgeber zur Praxisübernahme im Dentalbereich; kein Bezug zum Unternehmen, Wortbezug 'verkauft' ist zufällig. |
| F-099 | E.ON | niveauwechsel | 2023-11 | vergleich | -24 | 1 | mittel | Krise und Geschäftslage: Gewinnwarnung, Verlust, Sparprogramm | 1 | neutral | Halbjahresmitteilung mit starkem Ergebnis und Krisenmanagement in Flutgebieten im Übergang; Kapitalmarktmitteilung ohne Arbeitgeberbezug. |
| F-099 | E.ON | niveauwechsel | 2023-11 | vergleich | -24 | 2 | mittel | Übernahme, Fusion und Verkauf | 2 | neutral | Mehrheitsübernahme eines Energiesoftware-Start-ups im Übergang; kleiner Konzernvorgang ohne Belegschaftsbezug, Richtung ohne Wertung. |
| F-099 | E.ON | niveauwechsel | 2023-11 | vergleich | -24 | 3 | mittel | Führungswechsel | 2 | neutral | Wechsel an der Konzernspitze im Monat vor dem Übergang; Führungswechsel mit Arbeitgeberbezug, Richtung ohne Wertung. |
| F-068 | E.ON | niveauwechsel | 2023-11 | vergleich | -12 | 1 | mittel | Krise und Geschäftslage: Gewinnwarnung, Verlust, Sparprogramm | 1 | neutral | Halbjahresmitteilung mit bestätigtem Ausblick im Übergang; Kapitalmarktmitteilung ohne Arbeitgeberbezug, Ereignisart Krise über ein Schlüsselwort. |
| F-068 | E.ON | niveauwechsel | 2023-11 | vergleich | -12 | 2 | mittel | Führungswechsel | 0 | unklar | Neuer Vorstandsvorsitzender eines Gesundheitskonzerns, zuvor Finanzvorstand des Unternehmens; fremder Treffer, Handelnder ist der andere Konzern. |
| F-068 | E.ON | niveauwechsel | 2023-11 | vergleich | -12 | 3 | mittel | Vergütung und Sozialleistungen | 0 | unklar | Ratgeber zur Treibhausgasquote für Hybridfahrzeuge; kein Bezug zum Unternehmen, Ereignisart Vergütung ist ein Fehltreffer des Wortes Prämie. |
| F-071 | E.ON | niveauwechsel | 2023-11 | markierung | +0 | 1 | mittel | Führungswechsel | 1 | neutral | Neuer Geschäftsführer einer Netztochter im Monat vor dem Übergang; Führungswechsel bei einer Tochter, das Unternehmen selbst nicht genannt und nur am Rand, Richtung ohne Wertung. |
| F-071 | E.ON | niveauwechsel | 2023-11 | markierung | +0 | 2 | mittel | Vergütung und Sozialleistungen | 0 | unklar | Vereinsjubiläum in einer ostwestfälischen Stadt, deren Name dem Wort für Arbeitsentgelt gleicht; Fehltreffer ohne jeden Bezug. |
| F-071 | E.ON | niveauwechsel | 2023-11 | markierung | +0 | 3 | mittel | Tarifverhandlung und Streik | 3 | passt | Tarifeinigung mit deutlich höheren Gehältern für Zehntausende Beschäftigte im Monat vor dem Übergang; Tarifthema mit klarem Arbeitgeberbezug, entlastende Stoßrichtung passt zum Anstieg. |
| F-039 | E.ON | niveauwechsel | 2023-11 | vergleich | +12 | 1 | mittel | Vergütung und Sozialleistungen | 1 | neutral | Stimmrechtsmitteilung eines kanadischen Pensionsfonds im Übergang; Kapitalmarktmitteilung ohne Arbeitgeberbezug, Ereignisart Vergütung ist ein Fehltreffer. |
| F-039 | E.ON | niveauwechsel | 2023-11 | vergleich | +12 | 2 | mittel | Übernahme, Fusion und Verkauf | 2 | neutral | Mehrheitsverkauf einer rumänischen Landesgesellschaft im Monat nach dem markierten Monat; Konzernvorgang ohne Belegschaftsbezug im Inland, Richtung ohne Wertung, Lage danach. |
| F-039 | E.ON | niveauwechsel | 2023-11 | vergleich | +12 | 3 | mittel | Standort: Schließung, Verlagerung, Neubau | 1 | neutral | Spatenstich für den Glasfaserausbau einer regionalen Tochter in einem Ort im Übergang; Produkt- und Infrastrukturmeldung ohne Arbeitgeberbezug, Ereignisart Standort ist ein Fehltreffer. |
| F-079 | Freenet | niveauwechsel | 2015-10 | vergleich | -12 | 1 | mittel | Führungswechsel | 0 | unklar | Aufsichtsratsvorsitz des Vorstandschefs bei einem Außenwerber; Handelnder ist das andere Unternehmen, das bewertete Unternehmen ist nicht genannt, kein Bezug zu dessen Belegschaft. |
| F-008 | Freenet | niveauwechsel | 2015-10 | vergleich | +24 | 1 | niedrig | Ohne Arbeitgeberbezug: Börsenbericht, Kursziel, Sport, Produkt | 1 | passt | Kritik an gesetzlichen Ausweiskontrollen für Prepaid-Kunden mit überlasteten Hotlines im Übergang; branchenweite Kundenmeldung ohne Nennung des Unternehmens, Belegschaftsbezug nur mittelbar über den Kundenservice, der Begriff 'kunden' ist mehrdeutig. Belastende Stoßrichtung passt zum Abfall. |
| F-057 | Freenet | niveauwechsel | 2016-04 | vergleich | -24 | 1 | niedrig | Rechtsstreit, Compliance und Skandal | 0 | unklar | Allgemeiner Artikel über anonymes Surfen und Darknets; kein Unternehmen, kein Bezug zur Belegschaft. |
| F-082 | Freenet | niveauwechsel | 2016-04 | markierung | +0 | 1 | mittel | Führungswechsel | 1 | neutral | Aktienkauf des Vorstandsvorsitzenden im Monat nach dem markierten Monat; Directors'-Dealings-Mitteilung ohne Arbeitgeberbezug, Ereignisart Führungswechsel ist ein Fehltreffer der Funktionsbezeichnung. |
| F-082 | Freenet | niveauwechsel | 2016-04 | markierung | +0 | 2 | mittel | – | 0 | unklar | Interview mit einer früheren Todeskandidatin, verbreitet über das Nachrichtenportal des Unternehmens; fremder Treffer, Wortbezug 'frei' zufällig. |
| F-003 | Freenet | niveauwechsel | 2016-04 | vergleich | +12 | 1 | mittel | Rechtsstreit, Compliance und Skandal | 0 | unklar | Allgemeine Meldung zu einer Sicherheitslücke bei Fernsehgeräten ohne Nennung des Unternehmens und ohne Bezug zur Belegschaft; die Zuordnung zur Ereignisart beruht auf einem mehrdeutigen Schlüsselwort. |
| F-002 | Freenet | niveauwechsel | 2016-04 | vergleich | +24 | 1 | mittel | – | 1 | neutral | Vorstandsbesetzung bei einer Tochtergesellschaft (Streaming-Entwickler) des Konzerns; das Unternehmen selbst ist nicht genannt, die Meldung liegt im Monat nach dem markierten Monat, und der Begriff 'vorstand' ist allgemein. Kein eigener Arbeitgeberbezug für die Belegschaft des bewerteten Unternehmens, Richtung ohne Wertung. |
| F-034 | Freenet | niveauwechsel | 2019-10 | vergleich | -24 | 1 | niedrig | Ohne Arbeitgeberbezug: Börsenbericht, Kursziel, Sport, Produkt | 1 | passt | Kritik an Ausweiskontrollen für Prepaid-Kunden mit überlasteten Hotlines, hier zwei Monate vor dem Übergang; gleiche Meldung wie in einem anderen Fenster, branchenweit, Belegschaftsbezug nur mittelbar, Begriff 'kunden' mehrdeutig. Belastende Stoßrichtung passt zum Abfall. |
| F-078 | Freenet | niveauwechsel | 2019-10 | markierung | +0 | 1 | mittel | Übernahme, Fusion und Verkauf | 1 | neutral | Widerstand als Aktionär gegen die Übernahme eines Kabelanbieters durch eine Schweizer Beteiligung im markierten Monat; Kapitalmarktvorgang ohne Arbeitgeberbezug. |
| F-078 | Freenet | niveauwechsel | 2019-10 | markierung | +0 | 2 | niedrig | Personalabbau und Restrukturierung | 1 | widerspricht | Kundenkündigungen eines Mobilfunktarifs drei Monate vor dem Übergang; Produktmeldung, die Ereignisart Personalabbau ist ein Fehltreffer des Wortes Kündigungen, belastende Stoßrichtung widerspricht dem Anstieg. |
| F-078 | Freenet | niveauwechsel | 2019-10 | markierung | +0 | 3 | niedrig | Ohne Arbeitgeberbezug: Börsenbericht, Kursziel, Sport, Produkt | 1 | neutral | Strategie zum Kundenservice mit Sprachassistenten im Monat nach dem markierten Monat; Produktmeldung ohne Arbeitgeberbezug, Begriff 'kunden' mehrdeutig. |
| F-020 | Freenet | niveauwechsel | 2019-10 | vergleich | +12 | 1 | mittel | Übernahme, Fusion und Verkauf | 1 | neutral | Verkauf einer Minderheitsbeteiligung an einem Schweizer Telekommunikationsanbieter im Rahmen eines Übernahmeangebots zwei Monate vor dem Übergang; Finanztransaktion ohne Belegschaftsbezug. |
| F-020 | Freenet | niveauwechsel | 2019-10 | vergleich | +12 | 2 | mittel | Rechtsstreit, Compliance und Skandal | 0 | unklar | Gerichtsstreit zweier Schweizer Mobilfunkanbieter; fremder Treffer, das Unternehmen ist nicht genannt. |
| F-020 | Freenet | niveauwechsel | 2019-10 | vergleich | +12 | 3 | mittel | Unternehmenskultur, Gleichstellung und Diversität | 1 | neutral | Überblick über Frauenanteile in Vorständen mehrerer Digitalfirmen im Monat nach dem markierten Monat; das Unternehmen ist höchstens am Rand erwähnt, Richtung ohne Wertung. |
| F-027 | Freenet | niveauwechsel | 2021-09 | vergleich | -12 | 1 | mittel | Übernahme, Fusion und Verkauf | 1 | neutral | Verkauf einer Minderheitsbeteiligung an einem Schweizer Anbieter im Übergang; gleiche Meldung wie in einem anderen Fenster, Finanztransaktion ohne Belegschaftsbezug. |
| F-027 | Freenet | niveauwechsel | 2021-09 | vergleich | -12 | 2 | mittel | Rechtsstreit, Compliance und Skandal | 2 | passt | Bußgeld für die Hauptmarke des Unternehmens zu unerlaubter Telefonwerbung im Monat vor dem Übergang; Compliance-Vorfall im Vertrieb mit allgemeinem Bezug zur Vertriebsbelegschaft, belastende Stoßrichtung passt zum Abfall, das Unternehmen selbst ist im Titel nicht genannt. |
| F-027 | Freenet | niveauwechsel | 2021-09 | vergleich | -12 | 3 | mittel | Krise und Geschäftslage: Gewinnwarnung, Verlust, Sparprogramm | 1 | neutral | Interviewzitat zur Lage in der Pandemie ohne Nennung des Unternehmens im Monat vor dem Übergang; kein erkennbarer Arbeitgeberbezug, Richtung ohne Wertung. |
| F-073 | Freenet | niveauwechsel | 2021-09 | markierung | +0 | 1 | mittel | Vergütung und Sozialleistungen | 1 | neutral | Werbliche Meldung zum Strompreisvergleich einer Energiemarke des Unternehmens zwei Monate vor dem Übergang; Produktmeldung ohne Arbeitgeberbezug, Ereignisart Vergütung über das Wort Bonus. |
| F-073 | Freenet | niveauwechsel | 2021-09 | markierung | +0 | 2 | mittel | – | 1 | neutral | Buchvorstellung einer Aufsichtsrätin zu Geschlechterfragen zwei Monate vor dem Übergang; Personenmeldung ohne Arbeitgeberbezug, Wortbezug 'männer' mehrdeutig. |
| F-016 | Freenet | niveauwechsel | 2021-09 | vergleich | +12 | 1 | niedrig | Führungswechsel | 2 | neutral | Wahl eines neuen Aufsichtsratsvorsitzenden drei Monate vor dem Übergang; Führungswechsel auf Kontrollebene mit allgemeinem Arbeitgeberbezug, Richtung ohne Wertung. |
| F-030 | Freenet | niveauwechsel | 2021-09 | vergleich | +24 | 1 | niedrig | Ohne Arbeitgeberbezug: Börsenbericht, Kursziel, Sport, Produkt | 3 | passt | Vorstellung des fertiggestellten Neubauprojekts am Hauptstandort zum Firmenjubiläum im Monat vor dem Übergang; Standortthema mit Arbeitgeberbezug, entlastende Stoßrichtung passt zum Anstieg, und die Begriffe 'büdelsdorf' und 'büros' benennen dasselbe Ereignis. Die Rückstufung des Systems als Meldung ohne Arbeitgeberbezug trifft inhaltlich nicht zu. |
| F-030 | Freenet | niveauwechsel | 2021-09 | vergleich | +24 | 2 | niedrig | Rechtsstreit, Compliance und Skandal | 0 | unklar | Klage einer Schauspielerin gegen eine Organisation, verbreitet über das Nachrichtenportal des Unternehmens; fremder Treffer ohne Bezug zur Belegschaft. |
| F-009 | Freenet | niveauwechsel | 2022-02 | vergleich | -12 | 1 | mittel | Unternehmenskultur, Gleichstellung und Diversität | 0 | unklar | Kabinettsbeschluss zur Frauenquote; allgemeine Gesetzgebung ohne Nennung des Unternehmens und ohne Begriff in den Bewertungen. |
| F-009 | Freenet | niveauwechsel | 2022-02 | vergleich | -12 | 2 | niedrig | Ohne Arbeitgeberbezug: Börsenbericht, Kursziel, Sport, Produkt | 1 | neutral | Aktienrückkauf und Ausschüttungsvorschlag im markierten Monat; Kapitalmarktmitteilung ohne Arbeitgeberbezug, der Wortbezug 'per' ist bedeutungslos. |
| F-004 | Freenet | niveauwechsel | 2022-02 | vergleich | +24 | 1 | mittel | Krise und Geschäftslage: Gewinnwarnung, Verlust, Sparprogramm | 2 | passt | Bestätigung des bevorstehenden Endes der Einzelhandelstochter mit Filialnetz; Belegschaftsbezug gegeben und die belastende Stoßrichtung passt zum Abfall, die Meldung liegt aber erst im Monat nach dem markierten Monat. Der Begriff 'shops' ist zu allgemein, um dasselbe Ereignis eindeutig zu benennen. |
| F-004 | Freenet | niveauwechsel | 2022-02 | vergleich | +24 | 2 | niedrig | Übernahme, Fusion und Verkauf | 0 | unklar | Übernahmespekulation um einen anderen Konzern (Elektronikhandel); das bewertete Unternehmen kommt im Titel nicht vor, fremder Treffer. |
| F-062 | NTT DATA SE | niveauwechsel | 2017-11 | vergleich | -12 | 1 | mittel | Führungswechsel | 2 | neutral | Neuer Finanzvorstand im Monat vor dem Übergang; Führungswechsel mit Arbeitgeberbezug, das Unternehmen im Titel nicht genannt, Richtung ohne Wertung. |
| F-038 | NTT DATA SE | niveauwechsel | 2019-07 | vergleich | -12 | 1 | mittel | Rechtsstreit, Compliance und Skandal | 0 | unklar | Branchenbericht über zunehmende Hackerangriffe im Technologiesektor; kein Unternehmen genannt, kein Bezug zur Belegschaft. |
| F-038 | NTT DATA SE | niveauwechsel | 2019-07 | vergleich | -12 | 2 | mittel | Übernahme, Fusion und Verkauf | 2 | neutral | Mehrheitsübernahme eines kleineren Beratungshauses im markierten Monat; Konzernvorgang ohne Belegschaftsbezug für die bestehende Belegschaft, Richtung ohne Wertung. |
| F-038 | NTT DATA SE | niveauwechsel | 2019-07 | vergleich | -12 | 3 | mittel | Standort: Schließung, Verlagerung, Neubau | 1 | widerspricht | Prüfung eines Neubaus am Hauptstandort im markierten Monat; Standortthema mit Arbeitgeberbezug, die positive Stoßrichtung einer Investition widerspricht dem Abfall. |
| F-007 | NTT DATA SE | niveauwechsel | 2020-06 | vergleich | +12 | 1 | niedrig | – | 1 | passt | Auszeichnung als bestes Beratungshaus einer Softwaresparte drei Monate vor dem Übergang; Markt- und Produktauszeichnung ohne Arbeitgeberbezug, die positive Stoßrichtung passt zum Anstieg, der Begriff 'beratung' ist bei einem Beratungshaus allgemein. |
| F-007 | NTT DATA SE | niveauwechsel | 2020-06 | vergleich | +12 | 2 | niedrig | – | 1 | passt | Ausweitung einer globalen Partnerschaft zwischen Mutterkonzern und Softwarehersteller drei Monate vor dem Übergang; Geschäftsmeldung ohne Bezug zur Belegschaft, positive Stoßrichtung, Begriff 'bekanntheitsgrad' nur lose verbunden. |
| F-032 | NTT DATA SE | niveauwechsel | 2020-06 | vergleich | +24 | 1 | mittel | Krise und Geschäftslage: Gewinnwarnung, Verlust, Sparprogramm | 0 | unklar | Allgemeine Aussage zum Nutzen der Digitalisierung in der Krise ohne Nennung des Unternehmens im markierten Monat; kein Bezug zur Belegschaft, kein Begriff. |
| F-059 | NTT DATA SE | niveauwechsel | 2024-03 | vergleich | -12 | 1 | niedrig | Arbeitgeberauszeichnung und Ranking | 3 | passt | Auszeichnung als Top-Arbeitgeber in Deutschland im Übergang; Arbeitgeberthema mit klarem Bezug, die positive Stoßrichtung passt zum Anstieg. |
| F-097 | NTT DATA SE | niveauwechsel | 2024-03 | markierung | +0 | 1 | hoch | Übernahme, Fusion und Verkauf | 1 | neutral | Gemeinschaftsunternehmen eines Autokonzerns mit einer rumänischen Schwestergesellschaft im markierten Monat; Geschäftsprojekt im Ausland ohne Bezug zur Belegschaft im Inland, Wortbezug 'entwicklung' zufällig. |
| F-097 | NTT DATA SE | niveauwechsel | 2024-03 | markierung | +0 | 2 | mittel | Standort: Schließung, Verlagerung, Neubau | 0 | unklar | Porträt eines anderen Beratungshauses; fremder Treffer, Ereignisart Standort ist ein Fehltreffer des Wortes Umzug. |
| F-097 | NTT DATA SE | niveauwechsel | 2024-03 | markierung | +0 | 3 | niedrig | Arbeitgeberauszeichnung und Ranking | 1 | widerspricht | Auszeichnung als globaler Top-Arbeitgeber im Übergang; Arbeitgeberthema, die positive Stoßrichtung widerspricht dem Abfall. |
| F-052 | NTT DATA SE | niveauwechsel | 2024-03 | vergleich | +12 | 1 | hoch | Arbeitgeberauszeichnung und Ranking | 1 | widerspricht | Erneute Auszeichnung als globaler Top-Arbeitgeber im Übergang; Arbeitgeberthema, die positive Stoßrichtung widerspricht dem Abfall, Begriff 'global' allgemein. |
| F-052 | NTT DATA SE | niveauwechsel | 2024-03 | vergleich | +12 | 2 | mittel | Übernahme, Fusion und Verkauf | 0 | unklar | Neuer Deutschlandchef eines IT-Dienstleisters, der aus einem anderen Konzern hervorging; fremder Treffer. |
| F-052 | NTT DATA SE | niveauwechsel | 2024-03 | vergleich | +12 | 3 | mittel | – | 1 | neutral | Partnerauszeichnung eines Netzwerkherstellers für mehrere Systemhäuser zwei Monate vor dem Übergang; Produkt- und Vertriebsmeldung, das Unternehmen in einer Aufzählung, Wortbezug 'anderen' zufällig. |
| F-014 | RWE | niveauwechsel | 2023-02 | vergleich | -24 | 1 | niedrig | Krise und Geschäftslage: Gewinnwarnung, Verlust, Sparprogramm | 0 | unklar | Jahreszielbestätigung eines Wettbewerbers; fremder Treffer. |
| F-014 | RWE | niveauwechsel | 2023-02 | vergleich | -24 | 2 | niedrig | Einstellungen und Ausbildung | 0 | unklar | Personalie im Nachwuchsleistungszentrum des Fußballvereins Rot-Weiss Essen; fremder Treffer des Suchbegriffs. |
| F-014 | RWE | niveauwechsel | 2023-02 | vergleich | -24 | 3 | niedrig | Führungswechsel | 0 | unklar | Aufsichtsratsvorsitz eines Übertragungsnetzbetreibers für den früheren Chef einer ehemaligen Tochter; das Unternehmen ist nicht genannt und nicht Handelnder. |
| F-018 | RWE | niveauwechsel | 2023-02 | vergleich | -12 | 1 | niedrig | Rechtsstreit, Compliance und Skandal | 1 | widerspricht | Schadensersatzklage eines peruanischen Landwirts im Monat vor dem Übergang; Klimarechtsstreit ohne Arbeitgeberbezug, belastende Stoßrichtung widerspricht dem Anstieg. |
| F-018 | RWE | niveauwechsel | 2023-02 | vergleich | -12 | 2 | niedrig | Übernahme, Fusion und Verkauf | 1 | neutral | Börsen-Newsletter zu Wasserstoffplänen mehrerer Unternehmen im Monat vor dem Übergang; Kapitalmarktmeldung ohne Arbeitgeberbezug, Ereignisart ist ein Fehltreffer. |
| F-047 | RWE | niveauwechsel | 2023-02 | markierung | +0 | 1 | mittel | Tarifverhandlung und Streik | 1 | widerspricht | Demonstration gegen die Tagebauerweiterung im Monat vor dem Übergang; das Unternehmen ist als Betreiber nur mittelbar betroffen und nicht genannt, kein Arbeitgeberbezug, belastende Stoßrichtung widerspricht dem Anstieg. |
| F-047 | RWE | niveauwechsel | 2023-02 | markierung | +0 | 2 | mittel | Rechtsstreit, Compliance und Skandal | 1 | neutral | Schadensersatzforderung gegen einen russischen Gaslieferanten im Übergang; Rechts- und Geschäftsmeldung ohne Arbeitgeberbezug. |
| F-047 | RWE | niveauwechsel | 2023-02 | markierung | +0 | 3 | mittel | Standort: Schließung, Verlagerung, Neubau | 0 | unklar | Kritik einer Klimaaktivistin an der Bundesregierung; das Unternehmen ist nicht genannt, Ereignisart Standort ist ein Fehltreffer eines Nachnamens. |
| F-005 | RWE | niveauwechsel | 2023-02 | vergleich | +12 | 1 | mittel | Rechtsstreit, Compliance und Skandal | 1 | neutral | Rückzug einer Klage auf Grundlage eines internationalen Energieabkommens im Monat vor dem Übergang; richtiges Unternehmen, aber reiner Rechts- und Konzernvorgang ohne Bezug zur Belegschaft. |
| F-005 | RWE | niveauwechsel | 2023-02 | vergleich | +12 | 2 | mittel | Übernahme, Fusion und Verkauf | 1 | neutral | Beratermeldung zu einem Gemeinschaftsunternehmen für Offshore-Windprojekte im Ausland; Geschäftsprojekt ohne Arbeitgeberbezug, Richtung ohne Wertung. |
| F-005 | RWE | niveauwechsel | 2023-02 | vergleich | +12 | 3 | mittel | Einstellungen und Ausbildung | 0 | unklar | Nachwuchsfußball des gleichnamigen Vereins Rot-Weiss Essen; fremder Treffer des Suchbegriffs, kein Bezug zum Energiekonzern. |
| F-080 | RWE | einzelmonat | 2024-07 | vergleich | -24 | 1 | niedrig | Übernahme, Fusion und Verkauf | 1 | neutral | Erwerb eines Gaskraftwerks im Ausland mit Ausbau zu einem Wasserstoffstandort im Monat vor dem auffälligen Monat; Geschäfts- und Projektmeldung ohne Belegschaftsbezug im Inland. |
| F-080 | RWE | einzelmonat | 2024-07 | vergleich | -24 | 2 | niedrig | Rechtsstreit, Compliance und Skandal | 1 | widerspricht | Klage einer Klimaaktivistin gegen das Unternehmen im Monat vor dem auffälligen Monat; Rechtsstreit ohne Arbeitgeberbezug, belastende Stoßrichtung widerspricht dem Anstieg. |
| F-080 | RWE | einzelmonat | 2024-07 | vergleich | -24 | 3 | niedrig | Krise und Geschäftslage: Gewinnwarnung, Verlust, Sparprogramm | 1 | widerspricht | Vorzeitige Abschaltung eines Kraftwerks in der Gaskrise im Monat vor dem auffälligen Monat; Standortmeldung mit möglichem, im Titel nicht erkennbarem Belegschaftsbezug, belastende Stoßrichtung widerspricht dem Anstieg. |
| F-026 | RWE | einzelmonat | 2024-07 | vergleich | -12 | 1 | niedrig | Übernahme, Fusion und Verkauf | 1 | neutral | Podcast-Gespräch eines Branchenvertreters über Energiewende und einen zurückliegenden Tauschdeal zwei Monate vor dem auffälligen Monat; Kommentarformat ohne Arbeitgeberbezug. |
| F-026 | RWE | einzelmonat | 2024-07 | vergleich | -12 | 2 | niedrig | Personalabbau und Restrukturierung | 0 | unklar | Freistellung eines Zeugwarts beim Fußballverein Rot-Weiss Essen; fremder Treffer des Suchbegriffs. |
| F-026 | RWE | einzelmonat | 2024-07 | vergleich | -12 | 3 | niedrig | Rechtsstreit, Compliance und Skandal | 1 | neutral | Gerichtsentscheidung zu Klagen gegen einen Tauschdeal mit einem Wettbewerber zwei Monate vor dem auffälligen Monat; Rechtsmeldung ohne Belegschaftsbezug. |
| F-046 | RWE | einzelmonat | 2024-07 | markierung | +0 | 1 | niedrig | Rechtsstreit, Compliance und Skandal | 0 | unklar | Spielerwechsel-Streit beim Fußballverein Rot-Weiss Essen; fremder Treffer des Suchbegriffs. |
| F-046 | RWE | einzelmonat | 2024-07 | markierung | +0 | 2 | niedrig | Einstellungen und Ausbildung | 1 | widerspricht | Ausbildungskooperation mit einem Partner für ein neues Kraftwerk im auffälligen Monat; Ausbildungsthema mit Arbeitgeberbezug, die positive Stoßrichtung widerspricht dem Abfall. |
| F-046 | RWE | einzelmonat | 2024-07 | markierung | +0 | 3 | niedrig | Unternehmenskultur, Gleichstellung und Diversität | 0 | unklar | Trikotwechsel des Fußballvereins Rot-Weiss Essen; fremder Treffer. |
| F-067 | RWE | einzelmonat | 2024-07 | vergleich | +12 | 1 | niedrig | Rechtsstreit, Compliance und Skandal | 1 | neutral | Urteil eines Oberlandesgerichts in einer Klimaklage im Monat vor dem auffälligen Monat; Rechtsmeldung ohne Arbeitgeberbezug. |
| F-067 | RWE | einzelmonat | 2024-07 | vergleich | +12 | 2 | niedrig | Standort: Schließung, Verlagerung, Neubau | 0 | unklar | Neues Wohngebiet in einer Stadt im Rheinland; kein Bezug zum Unternehmen, Ereignisart Standort ist ein Fehltreffer. |
| F-067 | RWE | einzelmonat | 2024-07 | vergleich | +12 | 3 | niedrig | Vergütung und Sozialleistungen | 2 | unklar | Bericht über Millionengehälter von Energiehändlern des Unternehmens im auffälligen Monat; Vergütungsthema mit Arbeitgeberbezug, die Überschrift berichtet ohne Wertung der Regelung, Stoßrichtung für die übrige Belegschaft nicht eindeutig. |
| F-006 | SAP SE | einzelmonat | 2024-03 | markierung | +0 | 1 | hoch | Rechtsstreit, Compliance und Skandal | 1 | widerspricht | Rückendeckung eines Personalerverbands für den früheren Personalchef trotz Vorwürfen im auffälligen Monat; das Unternehmen ist im Titel nicht genannt und nur am Rand betroffen, der Wortbezug 'personal' trifft in den überwiegend englischen Bewertungen einen anderen Sinn. Eine belastende Meldung widerspricht dem Anstieg. |
| F-006 | SAP SE | einzelmonat | 2024-03 | markierung | +0 | 2 | mittel | Führungswechsel | 2 | neutral | Überraschender Austausch des designierten Aufsichtsratsvorsitzenden im Monat vor dem auffälligen Monat; Führungswechsel auf Kontrollebene mit allgemeinem Arbeitgeberbezug, Richtung ohne Wertung. |
| F-006 | SAP SE | einzelmonat | 2024-03 | markierung | +0 | 3 | mittel | Vergütung und Sozialleistungen | 2 | unklar | Entscheidung gegen einen Hersteller in der Dienstwagenregelung im Monat vor dem auffälligen Monat; Sozialleistungsthema mit Arbeitgeberbezug, Stoßrichtung für die Belegschaft nicht beurteilbar. |
| F-095 | SAP SE | einzelmonat | 2024-03 | vergleich | +12 | 1 | mittel | Einstellungen und Ausbildung | 1 | widerspricht | Junges Führungsduo aus dem eigenen Nachwuchs an einem kleinen Standort im Monat vor dem auffälligen Monat; lokale Personalie mit Arbeitgeberbezug, die positive Stoßrichtung widerspricht dem Abfall. |
| F-095 | SAP SE | einzelmonat | 2024-03 | vergleich | +12 | 2 | mittel | Tarifverhandlung und Streik | 3 | passt | Scharfe Kritik des Betriebsrats an einer als zu gering empfundenen Gehaltserhöhung im Monat vor dem auffälligen Monat; Vergütungsthema mit klarem Arbeitgeberbezug, belastende Stoßrichtung passt zum Abfall. |
| F-095 | SAP SE | einzelmonat | 2024-03 | vergleich | +12 | 3 | mittel | Arbeitsmodell: Homeoffice, Arbeitszeit, Büro | 1 | neutral | Überblick über Homeoffice-Regeln von 51 Konzernen im Monat vor dem auffälligen Monat; das Unternehmen höchstens in einer Aufzählung, Richtung ohne Wertung. |
| F-015 | SAP SE | einzelmonat | 2024-03 | vergleich | +24 | 1 | niedrig | Tarifverhandlung und Streik | 1 | widerspricht | Gewerkschaftskritik an geringen Gehaltserhöhungen für Führungskräfte im Monat vor dem auffälligen Monat; Vergütungsthema mit Arbeitgeberbezug, die belastende Stoßrichtung widerspricht dem Anstieg. |
| F-015 | SAP SE | einzelmonat | 2024-03 | vergleich | +24 | 2 | niedrig | Unternehmenskultur, Gleichstellung und Diversität | 1 | neutral | Hochschulprojekt zur Einführung der Unternehmenssoftware mit Kulturwandel beim Kunden im Monat vor dem auffälligen Monat; Produkt- und Kundenmeldung ohne Arbeitgeberbezug, Ereignisart durch mehrdeutiges Schlüsselwort. |
| F-015 | SAP SE | einzelmonat | 2024-03 | vergleich | +24 | 3 | niedrig | Vergütung und Sozialleistungen | 1 | widerspricht | Kritischer Bericht über ein neues Bonussystem für Führungskräfte im Monat vor dem auffälligen Monat; Vergütungsthema mit Arbeitgeberbezug, die Überschrift bewertet die Regelung negativ, belastende Stoßrichtung widerspricht dem Anstieg. |
| F-019 | SAP SE | niveauwechsel | 2024-07 | markierung | +0 | 1 | hoch | Personalabbau und Restrukturierung | 3 | passt | Abfindungsprogramm mit Unruhe in der Belegschaft im Monat vor dem Übergang; Personalabbau mit klarem Arbeitgeberbezug, belastende Stoßrichtung passt zum Abfall, und der Begriff 'unruhe' benennt dasselbe Ereignis. |
| F-019 | SAP SE | niveauwechsel | 2024-07 | markierung | +0 | 2 | hoch | Arbeitsmodell: Homeoffice, Arbeitszeit, Büro | 3 | passt | Ankündigung eines härteren Kurses des Vorstandschefs zu Gehalt, Homeoffice und Leistungskultur im markierten Monat; Arbeitsmodell und Kultur mit klarem Arbeitgeberbezug, belastende Stoßrichtung passt zum Abfall. |
| F-019 | SAP SE | niveauwechsel | 2024-07 | markierung | +0 | 3 | mittel | Übernahme, Fusion und Verkauf | 2 | neutral | Milliardenübernahme eines Softwareanbieters im Monat vor dem Übergang; Konzernvorgang ohne Belegschaftsbezug für die bestehende Belegschaft, Richtung ohne Wertung. |
| F-028 | SAP SE | niveauwechsel | 2024-07 | vergleich | +12 | 1 | hoch | Rechtsstreit, Compliance und Skandal | 1 | widerspricht | Kartellamtsermittlungen zu Kundenbeziehungen eines Prozessanalyse-Anbieters im Monat vor dem Übergang; Rechtsstreit ohne Arbeitgeberbezug, Begriff 'kunden' allgemein, belastende Stoßrichtung widerspricht dem Anstieg. |
| F-028 | SAP SE | niveauwechsel | 2024-07 | vergleich | +12 | 2 | mittel | Standort: Schließung, Verlagerung, Neubau | 1 | neutral | Studierendenstimmen zu Campusplänen des Unternehmensgründers an einer Universität im Monat vor dem Übergang; das Unternehmen ist nur als Zuschreibung einer Person erwähnt, kein Arbeitgeberbezug, Ereignisart Standort ist ein Fehltreffer. |
| F-028 | SAP SE | niveauwechsel | 2024-07 | vergleich | +12 | 3 | mittel | Unternehmenskultur, Gleichstellung und Diversität | 2 | unklar | Begründung des Vorstandschefs für die Abkehr von einer globalen Frauenquote im Monat vor dem Übergang; Kultur- und Gleichstellungsthema mit Arbeitgeberbezug, Stoßrichtung für die Belegschaft nicht eindeutig. |
| F-053 | Telekom | niveauwechsel | 2009-12 | markierung | +0 | 1 | niedrig | Führungswechsel | 2 | neutral | Angekündigter Rücktritt des Finanzvorstands im Übergang; Führungswechsel mit Arbeitgeberbezug, Richtung ohne Wertung. |
| F-053 | Telekom | niveauwechsel | 2009-12 | markierung | +0 | 2 | niedrig | Übernahme, Fusion und Verkauf | 2 | neutral | Geplante Fusion der britischen Mobilfunktochter mit einem Wettbewerber im Übergang; Konzernvorgang im Ausland ohne Belegschaftsbezug im Inland, Richtung ohne Wertung. |
| F-053 | Telekom | niveauwechsel | 2009-12 | markierung | +0 | 3 | niedrig | Rechtsstreit, Compliance und Skandal | 0 | unklar | Durchsuchung des Anwesens eines früheren Aufsichtsratsvorsitzenden in Italien; Privatangelegenheit einer Person, das Unternehmen ist nicht genannt. |
| F-074 | Telekom | niveauwechsel | 2010-07 | markierung | +0 | 1 | mittel | Vergütung und Sozialleistungen | 0 | unklar | Umbau eines Prämienprogramms bei einem Wettbewerber; fremder Treffer. |
| F-074 | Telekom | niveauwechsel | 2010-07 | markierung | +0 | 2 | niedrig | Standort: Schließung, Verlagerung, Neubau | 0 | unklar | Büroeröffnung einer Agentur in München; fremder Treffer. |
| F-074 | Telekom | niveauwechsel | 2010-07 | markierung | +0 | 3 | niedrig | Übernahme, Fusion und Verkauf | 0 | unklar | Neue Geschäftsführung bei einem Teehersteller; fremder Treffer. |
| F-040 | Telekom | niveauwechsel | 2010-07 | vergleich | +12 | 1 | niedrig | Übernahme, Fusion und Verkauf | 0 | unklar | Führungswechsel bei einer Tochter einer Mediaagentur; fremder Treffer. |
| F-033 | Telekom | niveauwechsel | 2010-07 | vergleich | +24 | 1 | mittel | Standort: Schließung, Verlagerung, Neubau | 0 | unklar | Büroleitung eines Dienstleisters in Frankfurt; fremder Treffer, Ereignisart Standort über das Wort Büro. |
| F-033 | Telekom | niveauwechsel | 2010-07 | vergleich | +24 | 2 | niedrig | Einstellungen und Ausbildung | 1 | neutral | Überblick über Nachwuchsgewinnung deutscher Konzerne in der Provinz im Monat vor dem Übergang; Branchenüberblick, das Unternehmen höchstens als Beispiel am Rand. |
| F-033 | Telekom | niveauwechsel | 2010-07 | vergleich | +24 | 3 | niedrig | Rechtsstreit, Compliance und Skandal | 1 | widerspricht | Rückblick auf große Compliance-Skandale deutscher Konzerne im Übergang; das Unternehmen höchstens als Beispiel aus früheren Jahren am Rand, belastende Stoßrichtung widerspricht dem Anstieg. |
| F-054 | Telekom | einzelmonat | 2015-05 | vergleich | -24 | 1 | hoch | Führungswechsel | 1 | neutral | Neuer Finanzchef der österreichischen Tochter im Monat vor dem auffälligen Monat; Führungswechsel bei einer Auslandstochter, das Unternehmen selbst nur am Rand, Wortbezug 'mobile' mehrdeutig. |
| F-054 | Telekom | einzelmonat | 2015-05 | vergleich | -24 | 2 | mittel | Rechtsstreit, Compliance und Skandal | 1 | neutral | Karte mit Echtzeitdarstellung von Cyberangriffen zwei Monate vor dem auffälligen Monat; Produkt- und Sicherheitsmeldung ohne Arbeitgeberbezug, Unternehmen nicht genannt. |
| F-054 | Telekom | einzelmonat | 2015-05 | vergleich | -24 | 3 | mittel | Übernahme, Fusion und Verkauf | 0 | unklar | Neuer Kommunikationsleiter bei einem Außenwerber; fremder Treffer. |
| F-012 | Telekom | einzelmonat | 2015-05 | vergleich | -12 | 1 | mittel | Vergütung und Sozialleistungen | 1 | neutral | Gerichtsentscheidung zur Konkurrenztätigkeit pensionierter Beamter im Monat nach dem auffälligen Monat; allgemeine Rechtsmeldung, das Unternehmen als Dienstherr höchstens am Rand, keine Begriffe. |
| F-012 | Telekom | einzelmonat | 2015-05 | vergleich | -12 | 2 | niedrig | Übernahme, Fusion und Verkauf | 0 | unklar | Börsengangsgerüchte um einen Musikstreaming-Anbieter; fremder Treffer, kein Bezug zum Unternehmen. |
| F-012 | Telekom | einzelmonat | 2015-05 | vergleich | -12 | 3 | niedrig | Führungswechsel | 2 | neutral | Ausscheiden zweier Personalvorständinnen aus DAX-Vorständen im Monat vor dem auffälligen Monat, nach dem Kontext darunter die des Unternehmens; Führungswechsel im Personalressort mit Arbeitgeberbezug, Richtung ohne Wertung, das Unternehmen ist im Titel nicht genannt. |
| F-060 | Telekom | einzelmonat | 2015-05 | markierung | +0 | 1 | niedrig | Rechtsstreit, Compliance und Skandal | 1 | passt | Anzeige eines ausländischen Abgeordneten gegen das Unternehmen in einer Geheimdienstaffäre im auffälligen Monat; Rechts- und Politikmeldung ohne Arbeitgeberbezug, belastende Stoßrichtung passt zum Abfall. |
| F-060 | Telekom | einzelmonat | 2015-05 | markierung | +0 | 2 | niedrig | Personalabbau und Restrukturierung | 2 | passt | Abbau von 70 Stellen an einem Standort, gemeldet im Monat nach dem auffälligen Monat; Personalabbau mit Arbeitgeberbezug, belastende Stoßrichtung passt zum Abfall, Lage erst danach. |
| F-087 | Telekom | einzelmonat | 2015-05 | vergleich | +12 | 1 | mittel | Rechtsstreit, Compliance und Skandal | 2 | passt | Staatsanwaltliche Ermittlungen gegen ein Vorstandsmitglied im Monat vor dem auffälligen Monat; gleiches Fenster und gleiche Meldung wie an anderer Stelle des Bogens, Compliance-Vorgang auf Führungsebene mit allgemeinem Arbeitgeberbezug, belastende Stoßrichtung passt zum Abfall. |
| F-087 | Telekom | einzelmonat | 2015-05 | vergleich | +12 | 2 | mittel | Übernahme, Fusion und Verkauf | 1 | neutral | Überblick über die größten Auslandsübernahmen deutscher Firmen im auffälligen Monat; gleiches Urteil wie an anderer Stelle, das Unternehmen höchstens als Beispiel am Rand. |
| F-069 | Telekom | einzelmonat | 2017-05 | vergleich | -12 | 1 | mittel | Rechtsstreit, Compliance und Skandal | 2 | passt | Staatsanwaltliche Ermittlungen gegen ein Vorstandsmitglied im Monat vor dem auffälligen Monat; Compliance-Vorgang auf Führungsebene mit allgemeinem Arbeitgeberbezug, belastende Stoßrichtung passt zum Abfall. |
| F-069 | Telekom | einzelmonat | 2017-05 | vergleich | -12 | 2 | mittel | Übernahme, Fusion und Verkauf | 1 | neutral | Überblick über die größten Auslandsübernahmen deutscher Firmen im auffälligen Monat; das Unternehmen höchstens als historisches Beispiel am Rand. |
| F-048 | Telekom | einzelmonat | 2017-05 | markierung | +0 | 1 | niedrig | Krise und Geschäftslage: Gewinnwarnung, Verlust, Sparprogramm | 1 | passt | Gewinneinbruch im auffälligen Monat; Geschäftszahlen ohne Belegschaftsbezug, belastende Stoßrichtung passt zum Abfall. |
| F-048 | Telekom | einzelmonat | 2017-05 | markierung | +0 | 2 | niedrig | Übernahme, Fusion und Verkauf | 1 | neutral | Interviewaussage zu möglichen Fusionen und Zukäufen ohne Nennung des Unternehmens im auffälligen Monat; Strategieaussage ohne Arbeitgeberbezug. |
| F-048 | Telekom | einzelmonat | 2017-05 | markierung | +0 | 3 | niedrig | Rechtsstreit, Compliance und Skandal | 1 | neutral | Polizeiwarnung an Kunden der Internetmarke vor Betrügern im Monat nach dem auffälligen Monat; Kundenmeldung ohne Arbeitgeberbezug. |
| F-044 | Telekom | einzelmonat | 2017-05 | vergleich | +12 | 1 | mittel | Übernahme, Fusion und Verkauf | 2 | neutral | Fusion der US-Tochter mit einem Wettbewerber im Monat vor dem auffälligen Monat; Konzernvorgang im Ausland ohne Belegschaftsbezug im Inland, Richtung ohne Wertung. |
| F-044 | Telekom | einzelmonat | 2017-05 | vergleich | +12 | 2 | niedrig | Führungswechsel | 2 | neutral | Angekündigter Abschied des Finanzvorstands drei Monate vor dem auffälligen Monat; Führungswechsel mit Arbeitgeberbezug, Richtung ohne Wertung. |
| F-044 | Telekom | einzelmonat | 2017-05 | vergleich | +12 | 3 | niedrig | Rechtsstreit, Compliance und Skandal | 1 | neutral | Gerichtsentscheidung zur Vorratsdatenspeicherung im Monat vor dem auffälligen Monat; Regulierungs- und Rechtsmeldung ohne Arbeitgeberbezug. |
| F-036 | Telekom | niveauwechsel | 2018-11 | vergleich | -24 | 1 | niedrig | Ohne Arbeitgeberbezug: Börsenbericht, Kursziel, Sport, Produkt | 1 | widerspricht | Fernsehreportage über aufgedrängte Produkte im Kundenvertrieb im Monat vor dem Übergang; Vertriebspraxis mit nur mittelbarem Belegschaftsbezug, Begriff 'kunden' unverändert häufig, belastende Stoßrichtung widerspricht dem Anstieg. |
| F-036 | Telekom | niveauwechsel | 2018-11 | vergleich | -24 | 2 | niedrig | Rechtsstreit, Compliance und Skandal | 1 | widerspricht | Netzstörung mit Hinweisen auf einen Angriff auf Router im markierten Monat; Betriebs- und Produktkrise ohne Nennung des Unternehmens, belastende Stoßrichtung widerspricht dem Anstieg. |
| F-036 | Telekom | niveauwechsel | 2018-11 | vergleich | -24 | 3 | niedrig | Personalabbau und Restrukturierung | 2 | unklar | Dementi eines Stellenabbaus zwei Monate vor dem Übergang; Personalthema mit Arbeitgeberbezug, Stoßrichtung zwischen Gerücht und Dementi nicht eindeutig. |
| F-085 | Telekom | niveauwechsel | 2018-11 | vergleich | -12 | 1 | niedrig | Übernahme, Fusion und Verkauf | 2 | neutral | Abbruch der Fusionsgespräche der US-Tochter im markierten Monat; gleiche Meldung wie in einem anderen Fenster, Konzernvorgang im Ausland ohne Belegschaftsbezug im Inland. |
| F-085 | Telekom | niveauwechsel | 2018-11 | vergleich | -12 | 2 | niedrig | Rechtsstreit, Compliance und Skandal | 0 | unklar | Methoden eines Umweltverbands im Dieselskandal; fremder Treffer, das Unternehmen ist nicht beteiligt. |
| F-022 | Telekom | niveauwechsel | 2018-11 | markierung | +0 | 1 | mittel | Übernahme, Fusion und Verkauf | 2 | neutral | Politischer Widerstand gegen den Verkauf einer Auslandstochter im Monat vor dem Übergang; Konzernvorgang ohne Belegschaftsbezug im Inland, Richtung ohne Wertung. |
| F-022 | Telekom | niveauwechsel | 2018-11 | markierung | +0 | 2 | mittel | Einstellungen und Ausbildung | 1 | neutral | Beiratsmandat eines früheren Bundesministers beim Unternehmen zwei Monate vor dem Übergang; Personalie auf Beratungsebene ohne Arbeitgeberbezug. |
| F-094 | Telekom | niveauwechsel | 2018-11 | vergleich | +12 | 1 | niedrig | Rechtsstreit, Compliance und Skandal | 1 | neutral | Markenrechtsstreit um eine Farbmarke im markierten Monat; Rechtsmeldung ohne Arbeitgeberbezug. |
| F-094 | Telekom | niveauwechsel | 2018-11 | vergleich | +12 | 2 | niedrig | Vergütung und Sozialleistungen | 1 | neutral | Mögliche Kürzung eines Kundenbonus zwei Monate vor dem Übergang; Produktmeldung, Ereignisart Vergütung ist ein Fehltreffer des Wortes Bonus. |
| F-094 | Telekom | niveauwechsel | 2018-11 | vergleich | +12 | 3 | niedrig | Führungswechsel | 1 | neutral | Neuer Leiter der TV-Sparte zwei Monate vor dem Übergang; Führungswechsel auf Bereichsebene mit geringem Bezug zur Gesamtbelegschaft, Richtung ohne Wertung. |
| F-084 | Telekom | niveauwechsel | 2019-02 | vergleich | -12 | 1 | niedrig | Übernahme, Fusion und Verkauf | 2 | neutral | Abbruch der Fusionsgespräche der US-Tochter drei Monate vor dem Übergang; Konzernvorgang im Ausland ohne Belegschaftsbezug im Inland, Richtung ohne Wertung. |
| F-084 | Telekom | niveauwechsel | 2019-02 | vergleich | -12 | 2 | niedrig | Führungswechsel | 2 | neutral | Angekündigter Abschied des Finanzvorstands im markierten Monat; Führungswechsel mit Arbeitgeberbezug, Richtung ohne Wertung. |
| F-029 | Telekom | niveauwechsel | 2019-02 | markierung | +0 | 1 | mittel | Übernahme, Fusion und Verkauf | 1 | neutral | Abwehr einer möglichen Übernahme eines britischen Konzerns im Monat vor dem Übergang; Spekulation über Konzernstrategie im Ausland ohne Belegschaftsbezug. |
| F-091 | Telekom | niveauwechsel | 2019-02 | vergleich | +12 | 1 | mittel | Tarifverhandlung und Streik | 2 | unklar | Einigung mit dem Betriebsrat über den Umbau der IT-Tochter zwei Monate vor dem Übergang; Restrukturierung mit Arbeitgeberbezug, Stoßrichtung zwischen Stellenabbau und erzielter Einigung nicht eindeutig. |
| F-091 | Telekom | niveauwechsel | 2019-02 | vergleich | +12 | 2 | niedrig | Ohne Arbeitgeberbezug: Börsenbericht, Kursziel, Sport, Produkt | 1 | neutral | Folgen der Pandemie für Hauptversammlungen mehrerer Konzerne im Monat nach dem markierten Monat; Kapitalmarktmeldung ohne Arbeitgeberbezug, der starke Begriff 'corona' benennt die Pandemie allgemein und nicht dieses Ereignis. |
| F-091 | Telekom | niveauwechsel | 2019-02 | vergleich | +12 | 3 | niedrig | Rechtsstreit, Compliance und Skandal | 1 | widerspricht | Offener Brief beamteter Beschäftigter mit Vorwurf der Altersdiskriminierung im Monat vor dem Übergang; Belegschaftsthema mit Arbeitgeberbezug, belastende Stoßrichtung widerspricht dem Anstieg. |
| F-093 | Telekom | niveauwechsel | 2019-02 | vergleich | +24 | 1 | niedrig | Standort: Schließung, Verlagerung, Neubau | 0 | unklar | Warnung vor Betrugsmails im Namen des Unternehmens drei Monate vor dem Übergang; gleiche Meldung wie in einem anderen Fenster, das Unternehmen nur missbrauchter Absendername. |
| F-093 | Telekom | niveauwechsel | 2019-02 | vergleich | +24 | 2 | niedrig | Krise und Geschäftslage: Gewinnwarnung, Verlust, Sparprogramm | 1 | neutral | Eigene Unternehmensmeldung zum Nutzen der Digitalisierung in der Krise im Monat vor dem Übergang; gleiche Meldung wie in einem anderen Fenster, Imagebotschaft ohne Belegschaftsbezug. |
| F-093 | Telekom | niveauwechsel | 2019-02 | vergleich | +24 | 3 | niedrig | Unternehmenskultur, Gleichstellung und Diversität | 1 | neutral | Barometer zu Frauenanteilen in Vorständen mehrerer Unternehmen im Monat vor dem Übergang; das Unternehmen höchstens in einer Aufzählung am Rand, Richtung ohne Wertung. |
| F-081 | Telekom | einzelmonat | 2022-12 | vergleich | -24 | 1 | mittel | Standort: Schließung, Verlagerung, Neubau | 0 | unklar | Warnung vor Betrugsmails im Namen des Unternehmens im Monat vor dem auffälligen Monat; das Unternehmen ist nur missbrauchter Absendername, kein Bezug zur Belegschaft, Ereignisart Standort ist ein Fehltreffer des Wortes Schließung. |
| F-081 | Telekom | einzelmonat | 2022-12 | vergleich | -24 | 2 | mittel | Übernahme, Fusion und Verkauf | 1 | neutral | Persönliche Zukunftspläne des Vorstandschefs und Konsolidierungswunsch in Europa im auffälligen Monat; Personen- und Strategiemeldung ohne Arbeitgeberbezug. |
| F-081 | Telekom | einzelmonat | 2022-12 | vergleich | -24 | 3 | mittel | Krise und Geschäftslage: Gewinnwarnung, Verlust, Sparprogramm | 1 | neutral | Eigene Unternehmensmeldung zum Nutzen der Digitalisierung in der Krise im Monat nach dem auffälligen Monat; Produkt- und Imagebotschaft ohne Belegschaftsbezug. |
| F-089 | Telekom | einzelmonat | 2022-12 | vergleich | -12 | 1 | mittel | Rechtsstreit, Compliance und Skandal | 1 | neutral | Gerichtliche Freigabe eines Vergleichs im Anlegerstreit im Monat vor dem auffälligen Monat; Kapitalmarkt- und Rechtsmeldung ohne Arbeitgeberbezug. |
| F-089 | Telekom | einzelmonat | 2022-12 | vergleich | -12 | 2 | mittel | Führungswechsel | 2 | neutral | Vertragsverlängerung des Vorstandschefs und designierter neuer Aufsichtsratsvorsitz im auffälligen Monat; Führungsthema an der Spitze mit Arbeitgeberbezug, Richtung ohne Wertung. |
| F-089 | Telekom | einzelmonat | 2022-12 | vergleich | -12 | 3 | mittel | Vergütung und Sozialleistungen | 1 | unklar | Gehaltserhöhung für den Vorstandschef im Monat nach dem auffälligen Monat; Vergütung einer Einzelperson ohne Bezug zur Belegschaft, Lage danach, Stoßrichtung für die Belegschaft nicht eindeutig. |
| F-065 | Telekom | einzelmonat | 2022-12 | markierung | +0 | 1 | mittel | Vergütung und Sozialleistungen | 2 | unklar | Umstellung der Dienstwagenflotte auf Elektroantrieb zwei Monate vor dem auffälligen Monat; Sozialleistungsthema mit Arbeitgeberbezug, Stoßrichtung für die Belegschaft nicht eindeutig. |
| F-065 | Telekom | einzelmonat | 2022-12 | markierung | +0 | 2 | niedrig | Rechtsstreit, Compliance und Skandal | 2 | passt | Bestechungsvorwürfe gegen eine Auslandstochter drei Monate vor dem auffälligen Monat; Compliance-Krise mit allgemeinem Bezug zum Image des Arbeitgebers, belastende Stoßrichtung passt zum Abfall. |
| F-065 | Telekom | einzelmonat | 2022-12 | markierung | +0 | 3 | niedrig | Führungswechsel | 0 | unklar | Neuer Finanzchef eines Elektronikhandelskonzerns; fremder Treffer. |
| F-090 | Telekom | einzelmonat | 2022-12 | vergleich | +12 | 1 | mittel | Rechtsstreit, Compliance und Skandal | 1 | neutral | Drohende Bußgelder für Netzbetreiber bei Funklöchern im Monat vor dem auffälligen Monat; Regulierungsmeldung für die Branche ohne Nennung des Unternehmens, kein Arbeitgeberbezug. |
| F-090 | Telekom | einzelmonat | 2022-12 | vergleich | +12 | 2 | mittel | Personalabbau und Restrukturierung | 1 | unklar | Faktencheck zu Gerüchten über Massenentlassungen bei deutschen Konzernen im auffälligen Monat; das Unternehmen höchstens in einer Aufzählung, Stoßrichtung zwischen Gerücht und Richtigstellung nicht eindeutig. |
| F-090 | Telekom | einzelmonat | 2022-12 | vergleich | +12 | 3 | mittel | Arbeitsmodell: Homeoffice, Arbeitszeit, Büro | 3 | passt | Rückruf der Mitarbeitenden ins Büro durch den Vorstandschef trotz Zufriedenheit mit Homeoffice zwei Monate vor dem auffälligen Monat; Arbeitsmodell mit klarem Arbeitgeberbezug, belastende Stoßrichtung passt zum Abfall. Der Begriff 'büro' ist danach seltener und trägt nicht. |

