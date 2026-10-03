# Datenbasis: Dichte der Kununu-Bewertungen je Unternehmen

Stand: 2026-10-02T22:55:32+02:00 (automatisch erzeugt durch `backend/scripts/report_data_density.py`, Quelle: gehostete Supabase-Datenbank, Tabellen `employee` und `candidates`). Diese Datei nicht von Hand bearbeiten; die Rohwerte liegen in `backend/data/data_density.json`.

## Methode

- **Unternehmen:** Alle Einträge der Tabelle `companies` außer den synthetischen Demo-Unternehmen (Demo 1/2/3), die aus jeder Analyse ausgeschlossen sind. Die Rohnamen enthalten Whitespace-Defekte (z. B. `'E.ON\n'`, doppelte Leerzeichen); Unternehmen werden deshalb über den bereinigten Namen (strip, Whitespace-Kollaps, casefold) oder die `id` identifiziert. Die Tabellen zeigen den bereinigten Namen.
- **Ausgeschlossen:** Demo 1 (id 10), Demo 2 (id 17), Demo 3 (id 18).
- **Zeilen:** Anzahl aller Bewertungen des Unternehmens in der jeweiligen Quelle, einschließlich Zeilen ohne Datum. **Ohne Datum:** Zeilen mit `datum IS NULL`; sie fließen nicht in die Monatsstatistik ein.
- **Zeitraum:** Kalendermonat (`YYYY-MM`) der ältesten und der jüngsten datierten Bewertung.
- **Kalendermonate:** Anzahl der Kalendermonate zwischen erster und letzter Bewertung, beide inklusive. Monate ohne Bewertung werden mitgezählt (Lücken verkürzen den Zeitraum nicht).
- **Bewertungen je Monat:** Anzahl datierter Bewertungen je Kalendermonat im Zeitraum; Minimum und Median werden über alle Kalendermonate gebildet, Monate ohne Bewertung gehen mit 0 ein.
- **Monate = 0 / < 5 / ≥ 5:** Anzahl Kalendermonate im Zeitraum mit genau 0, weniger als 5 bzw. mindestens 5 Bewertungen (die 0-Monate sind in „< 5“ enthalten).
- **Nicht-null-Anteil:** Anteil der Zeilen mit nicht-leerem Wert je Sternekategorie (`durchschnittsbewertung` sowie alle `sternebewertung_*`-Spalten der Quelle); Nenner sind alle Zeilen der Quelle. Die Haupttabellen zeigen den Anteil für die Durchschnittsbewertung und die Spannweite über die Themen; die Aufschlüsselung je Thema steht im Anhang.
- **Schwelle:** Ein Monat gilt als ausreichend belegt, wenn er mindestens 5 Bewertungen enthält. Ein Unternehmen gilt für die Monatsanalyse als ausreichend dicht, wenn mindestens 12 solcher Monate vorliegen (siehe Konsequenzen).

## Mitarbeitende (`employee`), 26 Unternehmen

| ID | Unternehmen | Zeilen | ohne Datum | Zeitraum | Kal.-Monate | Min/Monat | Median/Monat | Monate = 0 | Monate < 5 | Monate ≥ 5 | Ø-Bew. nicht-null | Themen nicht-null (min – max) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 3 | Thyssenkrupp | 446 | 0 | 2022-10 – 2026-03 | 42 | 1 | 9,0 | 0 | 10 | 32 | 100,0 % | 96,4 % – 99,8 % |
| 4 | Open Grid Europe | 361 | 1 | 2013-02 – 2026-03 | 158 | 0 | 2,0 | 44 | 136 | 22 | 99,7 % | 95,3 % – 99,5 % |
| 5 | PLEdoc GmbH | 97 | 0 | 2018-04 – 2026-02 | 95 | 0 | 0,0 | 52 | 90 | 5 | 100,0 % | 91,8 % – 100,0 % |
| 6 | E.ON Digital Technology | 12 | 1 | 2025-02 – 2026-04 | 15 | 0 | 1,0 | 7 | 15 | 0 | 91,7 % | 83,3 % – 91,7 % |
| 7 | E.ON | 486 | 0 | 2018-01 – 2026-04 | 100 | 0 | 3,0 | 16 | 62 | 38 | 100,0 % | 95,7 % – 100,0 % |
| 8 | RWE | 475 | 0 | 2013-05 – 2026-03 | 155 | 0 | 2,0 | 24 | 121 | 34 | 100,0 % | 96,2 % – 100,0 % |
| 9 | Thyssengas GmbH | 184 | 1 | 2011-09 – 2026-04 | 176 | 0 | 0,0 | 108 | 167 | 9 | 99,5 % | 94,6 % – 99,5 % |
| 13 | Universität Duisburg-Essen | 261 | 0 | 2008-10 – 2026-04 | 211 | 0 | 0,0 | 112 | 200 | 11 | 100,0 % | 95,8 % – 100,0 % |
| 14 | Karlsruher Institut für Technologie | 387 | 0 | 2011-02 – 2026-04 | 183 | 0 | 1,0 | 65 | 156 | 27 | 100,0 % | 93,3 % – 99,5 % |
| 15 | Technische Universität München | 302 | 0 | 2008-07 – 2026-03 | 213 | 0 | 1,0 | 92 | 200 | 13 | 100,0 % | 96,0 % – 99,3 % |
| 16 | Universität zu Köln | 181 | 0 | 2008-06 – 2026-03 | 214 | 0 | 0,0 | 125 | 207 | 7 | 100,0 % | 92,3 % – 100,0 % |
| 19 | SAP SE | 496 | 0 | 2020-07 – 2026-06 | 72 | 0 | 0,0 | 37 | 46 | 26 | 100,0 % | 92,9 % – 99,8 % |
| 20 | NTT DATA SE | 430 | 0 | 2015-07 – 2026-07 | 133 | 0 | 3,0 | 17 | 93 | 40 | 100,0 % | 89,3 % – 99,8 % |
| 21 | 1 und 1 | 1291 | 0 | 2007-06 – 2025-07 | 218 | 0 | 4,0 | 23 | 111 | 107 | 100,0 % | 91,3 % – 97,2 % |
| 22 | Aixtron | 109 | 0 | 2011-02 – 2025-07 | 174 | 0 | 0,0 | 111 | 171 | 3 | 100,0 % | 95,4 % – 100,0 % |
| 23 | Atoss | 171 | 0 | 2008-10 – 2025-03 | 198 | 0 | 0,0 | 102 | 194 | 4 | 100,0 % | 86,0 % – 95,9 % |
| 24 | Bechtle | 2369 | 0 | 2007-12 – 2025-07 | 212 | 0 | 9,0 | 23 | 73 | 139 | 100,0 % | 90,5 % – 96,8 % |
| 25 | Cancom | 1474 | 0 | 2008-01 – 2025-07 | 211 | 0 | 5,0 | 34 | 96 | 115 | 100,0 % | 87,5 % – 94,6 % |
| 26 | Carl Zeiss | 1700 | 0 | 2007-09 – 2025-07 | 215 | 0 | 4,0 | 40 | 116 | 99 | 100,0 % | 93,2 % – 98,3 % |
| 27 | Compugroup Medical Deutschland | 980 | 0 | 2008-06 – 2025-07 | 206 | 0 | 3,0 | 40 | 130 | 76 | 100,0 % | 85,1 % – 93,2 % |
| 28 | Telekom | 6899 | 0 | 2007-09 – 2025-07 | 215 | 0 | 18,0 | 8 | 50 | 165 | 100,0 % | 86,3 % – 87,8 % |
| 29 | Eckert Ziegler | 27 | 0 | 2011-02 – 2025-07 | 174 | 0 | 0,0 | 150 | 174 | 0 | 100,0 % | 70,4 % – 77,8 % |
| 30 | Elmos Semiconductor | 72 | 0 | 2008-05 – 2025-07 | 207 | 0 | 0,0 | 152 | 207 | 0 | 100,0 % | 91,7 % – 97,2 % |
| 31 | Evotec | 102 | 0 | 2014-04 – 2025-07 | 136 | 0 | 0,0 | 79 | 135 | 1 | 100,0 % | 87,2 % – 100,0 % |
| 32 | Formycon | 15 | 0 | 2016-11 – 2025-01 | 99 | 0 | 0,0 | 85 | 99 | 0 | 100,0 % | 80,0 % – 100,0 % |
| 33 | Freenet | 1027 | 0 | 2007-11 – 2025-08 | 214 | 0 | 3,0 | 55 | 128 | 86 | 100,0 % | 83,1 % – 86,5 % |

## Bewerbende (`candidates`), 26 Unternehmen

| ID | Unternehmen | Zeilen | ohne Datum | Zeitraum | Kal.-Monate | Min/Monat | Median/Monat | Monate = 0 | Monate < 5 | Monate ≥ 5 | Ø-Bew. nicht-null | Themen nicht-null (min – max) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 3 | Thyssenkrupp | 424 | 1 | 2008-09 – 2026-04 | 212 | 0 | 1,0 | 72 | 182 | 30 | 99,8 % | 80,9 % – 98,1 % |
| 4 | Open Grid Europe | 66 | 1 | 2015-04 – 2026-03 | 132 | 0 | 0,0 | 85 | 132 | 0 | 98,5 % | 90,9 % – 98,5 % |
| 5 | PLEdoc GmbH | 7 | 1 | 2019-06 – 2024-07 | 62 | 0 | 0,0 | 57 | 62 | 0 | 85,7 % | 85,7 % – 85,7 % |
| 6 | E.ON Digital Technology | 10 | 1 | 2025-03 – 2026-01 | 11 | 0 | 1,0 | 4 | 11 | 0 | 90,0 % | 80,0 % – 90,0 % |
| 7 | E.ON | 315 | 1 | 2008-10 – 2026-03 | 210 | 0 | 1,0 | 88 | 190 | 20 | 99,7 % | 84,1 % – 98,4 % |
| 8 | RWE | 164 | 1 | 2008-12 – 2025-12 | 205 | 0 | 0,0 | 118 | 202 | 3 | 99,4 % | 84,8 % – 97,0 % |
| 9 | Thyssengas GmbH | 363 | 1 | 2019-10 – 2026-03 | 78 | 0 | 3,5 | 12 | 46 | 32 | 99,7 % | 2,8 % – 98,9 % |
| 13 | Universität Duisburg-Essen | 9 | 0 | 2015-10 – 2026-03 | 126 | 0 | 0,0 | 118 | 126 | 0 | 100,0 % | 66,7 % – 100,0 % |
| 14 | Karlsruher Institut für Technologie | 28 | 0 | 2012-08 – 2026-02 | 163 | 0 | 0,0 | 137 | 163 | 0 | 100,0 % | 64,3 % – 100,0 % |
| 15 | Technische Universität München | 19 | 0 | 2012-02 – 2026-03 | 170 | 0 | 0,0 | 153 | 170 | 0 | 100,0 % | 52,6 % – 100,0 % |
| 16 | Universität zu Köln | 20 | 0 | 2012-05 – 2026-01 | 165 | 0 | 0,0 | 146 | 165 | 0 | 100,0 % | 40,0 % – 95,0 % |
| 19 | SAP SE | 259 | 0 | 2011-08 – 2026-05 | 178 | 0 | 1,0 | 49 | 172 | 6 | 100,0 % | 83,8 % – 97,3 % |
| 20 | NTT DATA SE | 0 | 0 | – | 0 | – | – | 0 | 0 | 0 | – | – |
| 21 | 1 und 1 | 195 | 0 | 2008-10 – 2025-06 | 201 | 0 | 1,0 | 87 | 201 | 0 | 100,0 % | 87,7 % – 99,0 % |
| 22 | Aixtron | 116 | 0 | 2018-09 – 2025-07 | 83 | 0 | 0,0 | 54 | 71 | 12 | 100,0 % | 6,0 % – 99,1 % |
| 23 | Atoss | 192 | 0 | 2012-08 – 2025-06 | 155 | 0 | 1,0 | 59 | 151 | 4 | 100,0 % | 89,1 % – 99,5 % |
| 24 | Bechtle | 295 | 0 | 2011-10 – 2025-07 | 166 | 0 | 1,0 | 43 | 157 | 9 | 100,0 % | 82,0 % – 98,6 % |
| 25 | Cancom | 139 | 0 | 2011-03 – 2025-06 | 172 | 0 | 0,0 | 87 | 167 | 5 | 100,0 % | 86,3 % – 98,6 % |
| 26 | Carl Zeiss | 704 | 0 | 2011-04 – 2025-07 | 172 | 0 | 3,0 | 47 | 107 | 65 | 100,0 % | 89,1 % – 98,2 % |
| 27 | Compugroup Medical Deutschland | 169 | 0 | 2011-03 – 2025-07 | 173 | 0 | 1,0 | 85 | 168 | 5 | 100,0 % | 88,2 % – 99,4 % |
| 28 | Telekom | 219 | 0 | 2009-11 – 2025-07 | 189 | 0 | 1,0 | 66 | 186 | 3 | 100,0 % | 79,0 % – 98,2 % |
| 29 | Eckert Ziegler | 4 | 0 | 2014-11 – 2018-08 | 46 | 0 | 0,0 | 42 | 46 | 0 | 100,0 % | 50,0 % – 100,0 % |
| 30 | Elmos Semiconductor | 10 | 0 | 2018-09 – 2025-05 | 81 | 0 | 0,0 | 71 | 81 | 0 | 100,0 % | 90,0 % – 100,0 % |
| 31 | Evotec | 23 | 0 | 2015-11 – 2024-12 | 110 | 0 | 0,0 | 92 | 110 | 0 | 100,0 % | 78,3 % – 100,0 % |
| 32 | Formycon | 4 | 0 | 2017-08 – 2024-09 | 86 | 0 | 0,0 | 82 | 86 | 0 | 100,0 % | 50,0 % – 100,0 % |
| 33 | Freenet | 130 | 0 | 2011-10 – 2025-08 | 167 | 0 | 0,0 | 86 | 165 | 2 | 100,0 % | 89,2 % – 99,2 % |

## Konsequenzen

**Mitarbeitende (`employee`):** 15 von 26 Unternehmen haben mindestens 12 Monate mit ≥ 5 Bewertungen: Thyssenkrupp (32), Open Grid Europe (22), E.ON (38), RWE (34), Karlsruher Institut für Technologie (27), Technische Universität München (13), SAP SE (26), NTT DATA SE (40), 1 und 1 (107), Bechtle (139), Cancom (115), Carl Zeiss (99), Compugroup Medical Deutschland (76), Telekom (165), Freenet (86).

Weniger als 12 Monate mit ≥ 5 Bewertungen (11 Unternehmen):

- PLEdoc GmbH (id 5): Monate ≥ 5: 5; 97 Zeilen über 95 Kalendermonate; Median 0,0 Bewertungen/Monat
- E.ON Digital Technology (id 6): Monate ≥ 5: 0; 12 Zeilen über 15 Kalendermonate; Median 1,0 Bewertungen/Monat
- Thyssengas GmbH (id 9): Monate ≥ 5: 9; 184 Zeilen über 176 Kalendermonate; Median 0,0 Bewertungen/Monat
- Universität Duisburg-Essen (id 13): Monate ≥ 5: 11; 261 Zeilen über 211 Kalendermonate; Median 0,0 Bewertungen/Monat
- Universität zu Köln (id 16): Monate ≥ 5: 7; 181 Zeilen über 214 Kalendermonate; Median 0,0 Bewertungen/Monat
- Aixtron (id 22): Monate ≥ 5: 3; 109 Zeilen über 174 Kalendermonate; Median 0,0 Bewertungen/Monat
- Atoss (id 23): Monate ≥ 5: 4; 171 Zeilen über 198 Kalendermonate; Median 0,0 Bewertungen/Monat
- Eckert Ziegler (id 29): Monate ≥ 5: 0; 27 Zeilen über 174 Kalendermonate; Median 0,0 Bewertungen/Monat
- Elmos Semiconductor (id 30): Monate ≥ 5: 0; 72 Zeilen über 207 Kalendermonate; Median 0,0 Bewertungen/Monat
- Evotec (id 31): Monate ≥ 5: 1; 102 Zeilen über 136 Kalendermonate; Median 0,0 Bewertungen/Monat
- Formycon (id 32): Monate ≥ 5: 0; 15 Zeilen über 99 Kalendermonate; Median 0,0 Bewertungen/Monat

**Bewerbende (`candidates`):** 5 von 26 Unternehmen haben mindestens 12 Monate mit ≥ 5 Bewertungen: Thyssenkrupp (30), E.ON (20), Thyssengas GmbH (32), Aixtron (12), Carl Zeiss (65).

Weniger als 12 Monate mit ≥ 5 Bewertungen (21 Unternehmen):

- Open Grid Europe (id 4): Monate ≥ 5: 0; 66 Zeilen über 132 Kalendermonate; Median 0,0 Bewertungen/Monat
- PLEdoc GmbH (id 5): Monate ≥ 5: 0; 7 Zeilen über 62 Kalendermonate; Median 0,0 Bewertungen/Monat
- E.ON Digital Technology (id 6): Monate ≥ 5: 0; 10 Zeilen über 11 Kalendermonate; Median 1,0 Bewertungen/Monat
- RWE (id 8): Monate ≥ 5: 3; 164 Zeilen über 205 Kalendermonate; Median 0,0 Bewertungen/Monat
- Universität Duisburg-Essen (id 13): Monate ≥ 5: 0; 9 Zeilen über 126 Kalendermonate; Median 0,0 Bewertungen/Monat
- Karlsruher Institut für Technologie (id 14): Monate ≥ 5: 0; 28 Zeilen über 163 Kalendermonate; Median 0,0 Bewertungen/Monat
- Technische Universität München (id 15): Monate ≥ 5: 0; 19 Zeilen über 170 Kalendermonate; Median 0,0 Bewertungen/Monat
- Universität zu Köln (id 16): Monate ≥ 5: 0; 20 Zeilen über 165 Kalendermonate; Median 0,0 Bewertungen/Monat
- SAP SE (id 19): Monate ≥ 5: 6; 259 Zeilen über 178 Kalendermonate; Median 1,0 Bewertungen/Monat
- NTT DATA SE (id 20): keine Bewertungen in dieser Quelle
- 1 und 1 (id 21): Monate ≥ 5: 0; 195 Zeilen über 201 Kalendermonate; Median 1,0 Bewertungen/Monat
- Atoss (id 23): Monate ≥ 5: 4; 192 Zeilen über 155 Kalendermonate; Median 1,0 Bewertungen/Monat
- Bechtle (id 24): Monate ≥ 5: 9; 295 Zeilen über 166 Kalendermonate; Median 1,0 Bewertungen/Monat
- Cancom (id 25): Monate ≥ 5: 5; 139 Zeilen über 172 Kalendermonate; Median 0,0 Bewertungen/Monat
- Compugroup Medical Deutschland (id 27): Monate ≥ 5: 5; 169 Zeilen über 173 Kalendermonate; Median 1,0 Bewertungen/Monat
- Telekom (id 28): Monate ≥ 5: 3; 219 Zeilen über 189 Kalendermonate; Median 1,0 Bewertungen/Monat
- Eckert Ziegler (id 29): Monate ≥ 5: 0; 4 Zeilen über 46 Kalendermonate; Median 0,0 Bewertungen/Monat
- Elmos Semiconductor (id 30): Monate ≥ 5: 0; 10 Zeilen über 81 Kalendermonate; Median 0,0 Bewertungen/Monat
- Evotec (id 31): Monate ≥ 5: 0; 23 Zeilen über 110 Kalendermonate; Median 0,0 Bewertungen/Monat
- Formycon (id 32): Monate ≥ 5: 0; 4 Zeilen über 86 Kalendermonate; Median 0,0 Bewertungen/Monat
- Freenet (id 33): Monate ≥ 5: 2; 130 Zeilen über 167 Kalendermonate; Median 0,0 Bewertungen/Monat

**Zeilen ohne Datum** (nicht zeitlich zuordenbar, in Monatsstatistiken ignoriert): Thyssenkrupp/candidates: 1, Open Grid Europe/employee: 1, Open Grid Europe/candidates: 1, PLEdoc GmbH/candidates: 1, E.ON Digital Technology/employee: 1, E.ON Digital Technology/candidates: 1, E.ON/candidates: 1, RWE/candidates: 1, Thyssengas GmbH/employee: 1, Thyssengas GmbH/candidates: 1.

Für sehr dünn belegte Unternehmen ist eine Monatsauflösung nicht tragfähig; dort kommen nur gröbere Zeitfenster (Quartal/Jahr) oder ein Ausschluss aus der quantitativen Evaluation in Frage. Diese Entscheidung wird im Design der Erkennung (nachfolgende Inkremente) getroffen und hier nur vorbereitet.

## Anhang: Nicht-null-Anteil je Sternekategorie

<details>
<summary>Mitarbeitende (`employee`)</summary>

| ID | Unternehmen | durchschnittsbewertung | arbeitsatmosphaere | image | work_life_balance | karriere_weiterbildung | gehalt_sozialleistungen | kollegenzusammenhalt | umwelt_sozialbewusstsein | vorgesetztenverhalten | kommunikation | interessante_aufgaben | umgang_mit_aelteren_kollegen | arbeitsbedingungen | gleichberechtigung |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 3 | Thyssenkrupp | 100,0 % | 99,8 % | 98,4 % | 99,1 % | 98,4 % | 99,6 % | 99,3 % | 96,4 % | 99,3 % | 99,3 % | 98,7 % | 97,1 % | 99,3 % | 97,1 % |
| 4 | Open Grid Europe | 99,7 % | 99,5 % | 97,8 % | 99,5 % | 99,2 % | 99,2 % | 99,5 % | 98,6 % | 99,5 % | 99,2 % | 99,5 % | 95,3 % | 99,5 % | 97,8 % |
| 5 | PLEdoc GmbH | 100,0 % | 100,0 % | 94,8 % | 100,0 % | 99,0 % | 100,0 % | 100,0 % | 92,8 % | 100,0 % | 100,0 % | 99,0 % | 91,8 % | 99,0 % | 95,9 % |
| 6 | E.ON Digital Technology | 91,7 % | 83,3 % | 83,3 % | 83,3 % | 83,3 % | 83,3 % | 83,3 % | 83,3 % | 83,3 % | 91,7 % | 83,3 % | 83,3 % | 83,3 % | 83,3 % |
| 7 | E.ON | 100,0 % | 99,6 % | 97,5 % | 99,4 % | 97,1 % | 98,6 % | 99,6 % | 97,3 % | 99,6 % | 100,0 % | 99,2 % | 95,7 % | 98,2 % | 97,3 % |
| 8 | RWE | 100,0 % | 99,6 % | 97,7 % | 98,7 % | 99,2 % | 99,4 % | 99,4 % | 96,8 % | 99,8 % | 100,0 % | 99,8 % | 96,2 % | 99,4 % | 97,5 % |
| 9 | Thyssengas GmbH | 99,5 % | 99,5 % | 95,7 % | 98,4 % | 95,1 % | 98,9 % | 98,9 % | 94,6 % | 98,9 % | 97,8 % | 98,4 % | 95,7 % | 97,8 % | 95,1 % |
| 13 | Universität Duisburg-Essen | 100,0 % | 100,0 % | 97,7 % | 98,9 % | 98,5 % | 98,5 % | 99,6 % | 95,8 % | 100,0 % | 99,2 % | 99,2 % | 96,2 % | 99,2 % | 97,7 % |
| 14 | Karlsruher Institut für Technologie | 100,0 % | 99,5 % | 96,9 % | 97,2 % | 97,4 % | 97,9 % | 98,5 % | 96,4 % | 98,5 % | 98,7 % | 97,9 % | 93,3 % | 98,2 % | 96,4 % |
| 15 | Technische Universität München | 100,0 % | 99,3 % | 98,7 % | 98,7 % | 97,7 % | 98,3 % | 99,3 % | 96,0 % | 99,0 % | 99,3 % | 99,0 % | 96,4 % | 99,0 % | 97,4 % |
| 16 | Universität zu Köln | 100,0 % | 100,0 % | 96,7 % | 100,0 % | 98,3 % | 99,5 % | 100,0 % | 95,6 % | 100,0 % | 100,0 % | 100,0 % | 92,3 % | 100,0 % | 98,3 % |
| 19 | SAP SE | 100,0 % | 99,8 % | 97,8 % | 98,8 % | 98,4 % | 99,2 % | 99,0 % | 96,6 % | 98,6 % | 98,6 % | 98,0 % | 92,9 % | 98,0 % | 95,6 % |
| 20 | NTT DATA SE | 100,0 % | 99,5 % | 96,7 % | 98,4 % | 98,4 % | 99,1 % | 99,3 % | 89,3 % | 99,1 % | 99,8 % | 99,3 % | 93,7 % | 98,8 % | 96,7 % |
| 21 | 1 und 1 | 100,0 % | 97,2 % | 95,3 % | 96,5 % | 95,2 % | 96,4 % | 97,1 % | 91,9 % | 96,9 % | 96,8 % | 96,4 % | 91,3 % | 96,4 % | 94,7 % |
| 22 | Aixtron | 100,0 % | 100,0 % | 96,3 % | 100,0 % | 96,3 % | 100,0 % | 100,0 % | 98,2 % | 99,1 % | 100,0 % | 100,0 % | 96,3 % | 100,0 % | 95,4 % |
| 23 | Atoss | 100,0 % | 95,9 % | 90,1 % | 95,3 % | 93,6 % | 94,7 % | 95,3 % | 86,0 % | 95,9 % | 95,3 % | 94,7 % | 89,5 % | 95,3 % | 93,0 % |
| 24 | Bechtle | 100,0 % | 96,8 % | 94,7 % | 96,0 % | 94,6 % | 96,0 % | 96,5 % | 91,6 % | 96,4 % | 96,3 % | 96,1 % | 90,5 % | 95,7 % | 92,7 % |
| 25 | Cancom | 100,0 % | 94,6 % | 90,3 % | 93,1 % | 92,8 % | 94,2 % | 93,8 % | 88,3 % | 94,5 % | 94,5 % | 93,8 % | 87,5 % | 93,0 % | 89,1 % |
| 26 | Carl Zeiss | 100,0 % | 98,3 % | 97,0 % | 97,7 % | 96,5 % | 97,8 % | 97,9 % | 95,5 % | 97,9 % | 97,9 % | 97,3 % | 93,2 % | 97,2 % | 95,5 % |
| 27 | Compugroup Medical Deutschland | 100,0 % | 92,9 % | 90,3 % | 92,7 % | 89,2 % | 92,5 % | 93,2 % | 85,3 % | 92,1 % | 92,8 % | 91,3 % | 85,1 % | 91,5 % | 88,0 % |
| 28 | Telekom | 100,0 % | 87,8 % | 86,9 % | 87,5 % | 87,2 % | 87,4 % | 87,6 % | 86,3 % | 87,7 % | 87,4 % | 87,4 % | 86,6 % | 87,4 % | 87,0 % |
| 29 | Eckert Ziegler | 100,0 % | 77,8 % | 74,1 % | 77,8 % | 77,8 % | 77,8 % | 77,8 % | 74,1 % | 77,8 % | 77,8 % | 77,8 % | 74,1 % | 70,4 % | 74,1 % |
| 30 | Elmos Semiconductor | 100,0 % | 97,2 % | 93,1 % | 97,2 % | 95,8 % | 97,2 % | 97,2 % | 93,1 % | 97,2 % | 97,2 % | 97,2 % | 91,7 % | 95,8 % | 91,7 % |
| 31 | Evotec | 100,0 % | 99,0 % | 94,1 % | 97,1 % | 95,1 % | 98,0 % | 100,0 % | 89,2 % | 99,0 % | 98,0 % | 99,0 % | 87,2 % | 94,1 % | 94,1 % |
| 32 | Formycon | 100,0 % | 100,0 % | 86,7 % | 100,0 % | 100,0 % | 93,3 % | 100,0 % | 93,3 % | 100,0 % | 100,0 % | 93,3 % | 80,0 % | 93,3 % | 100,0 % |
| 33 | Freenet | 100,0 % | 86,4 % | 84,4 % | 86,1 % | 85,3 % | 85,9 % | 86,4 % | 84,0 % | 86,4 % | 86,5 % | 85,9 % | 83,1 % | 85,6 % | 84,9 % |

</details>

<details>
<summary>Bewerbende (`candidates`)</summary>

| ID | Unternehmen | durchschnittsbewertung | erklaerung_der_weiteren_schritte | zufriedenstellende_reaktion | vollstaendigkeit_der_infos | zufriedenstellende_antworten | angenehme_atmosphaere | professionalitaet_des_gespraechs | wertschaetzende_behandlung | erwartbarkeit_des_prozesses | zeitgerechte_zu_oder_absage | schnelle_antwort |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 3 | Thyssenkrupp | 99,8 % | 81,6 % | 98,1 % | 82,1 % | 81,4 % | 80,9 % | 83,0 % | 81,8 % | 96,2 % | 85,6 % | 97,2 % |
| 4 | Open Grid Europe | 98,5 % | 90,9 % | 98,5 % | 90,9 % | 90,9 % | 90,9 % | 90,9 % | 90,9 % | 98,5 % | 90,9 % | 98,5 % |
| 5 | PLEdoc GmbH | 85,7 % | 85,7 % | 85,7 % | 85,7 % | 85,7 % | 85,7 % | 85,7 % | 85,7 % | 85,7 % | 85,7 % | 85,7 % |
| 6 | E.ON Digital Technology | 90,0 % | 80,0 % | 90,0 % | 80,0 % | 80,0 % | 80,0 % | 80,0 % | 80,0 % | 90,0 % | 80,0 % | 90,0 % |
| 7 | E.ON | 99,7 % | 86,0 % | 98,4 % | 84,4 % | 85,1 % | 84,1 % | 84,8 % | 86,7 % | 96,5 % | 90,8 % | 98,1 % |
| 8 | RWE | 99,4 % | 86,0 % | 97,0 % | 85,4 % | 84,8 % | 85,4 % | 86,0 % | 85,4 % | 97,0 % | 88,4 % | 96,3 % |
| 9 | Thyssengas GmbH | 99,7 % | 98,9 % | 97,2 % | 98,1 % | 94,5 % | 98,4 % | 98,6 % | 98,6 % | 98,4 % | 2,8 % | 96,4 % |
| 13 | Universität Duisburg-Essen | 100,0 % | 66,7 % | 100,0 % | 77,8 % | 77,8 % | 77,8 % | 66,7 % | 77,8 % | 100,0 % | 66,7 % | 100,0 % |
| 14 | Karlsruher Institut für Technologie | 100,0 % | 64,3 % | 92,9 % | 64,3 % | 64,3 % | 64,3 % | 64,3 % | 64,3 % | 100,0 % | 64,3 % | 96,4 % |
| 15 | Technische Universität München | 100,0 % | 63,2 % | 89,5 % | 57,9 % | 52,6 % | 52,6 % | 52,6 % | 52,6 % | 100,0 % | 63,2 % | 89,5 % |
| 16 | Universität zu Köln | 100,0 % | 40,0 % | 95,0 % | 45,0 % | 40,0 % | 40,0 % | 40,0 % | 45,0 % | 95,0 % | 55,0 % | 95,0 % |
| 19 | SAP SE | 100,0 % | 85,3 % | 96,5 % | 84,6 % | 83,8 % | 83,8 % | 84,6 % | 85,3 % | 96,9 % | 86,1 % | 97,3 % |
| 20 | NTT DATA SE | – | – | – | – | – | – | – | – | – | – | – |
| 21 | 1 und 1 | 100,0 % | 88,2 % | 91,3 % | 98,0 % | 91,8 % | 91,3 % | 96,4 % | 90,8 % | 87,7 % | 91,3 % | 99,0 % |
| 22 | Aixtron | 100,0 % | 99,1 % | 99,1 % | 97,4 % | 99,1 % | 98,3 % | 98,3 % | 94,8 % | 6,0 % | 99,1 % | 99,1 % |
| 23 | Atoss | 100,0 % | 91,1 % | 89,6 % | 99,5 % | 91,1 % | 89,6 % | 97,4 % | 90,6 % | 89,1 % | 89,1 % | 99,0 % |
| 24 | Bechtle | 100,0 % | 82,7 % | 82,4 % | 98,3 % | 82,4 % | 82,0 % | 95,9 % | 82,0 % | 83,4 % | 82,0 % | 98,6 % |
| 25 | Cancom | 100,0 % | 87,8 % | 87,1 % | 97,8 % | 88,5 % | 87,8 % | 97,8 % | 87,8 % | 87,1 % | 86,3 % | 98,6 % |
| 26 | Carl Zeiss | 100,0 % | 90,9 % | 89,9 % | 97,3 % | 89,9 % | 89,9 % | 98,2 % | 89,8 % | 90,6 % | 89,1 % | 97,7 % |
| 27 | Compugroup Medical Deutschland | 100,0 % | 88,8 % | 88,8 % | 99,4 % | 89,3 % | 88,8 % | 96,5 % | 89,3 % | 89,9 % | 88,2 % | 98,2 % |
| 28 | Telekom | 100,0 % | 81,3 % | 81,7 % | 98,2 % | 81,3 % | 81,7 % | 95,0 % | 80,4 % | 80,8 % | 79,0 % | 97,7 % |
| 29 | Eckert Ziegler | 100,0 % | 50,0 % | 50,0 % | 100,0 % | 50,0 % | 50,0 % | 100,0 % | 50,0 % | 50,0 % | 50,0 % | 100,0 % |
| 30 | Elmos Semiconductor | 100,0 % | 100,0 % | 100,0 % | 100,0 % | 100,0 % | 100,0 % | 90,0 % | 90,0 % | 100,0 % | 100,0 % | 100,0 % |
| 31 | Evotec | 100,0 % | 78,3 % | 78,3 % | 100,0 % | 78,3 % | 78,3 % | 100,0 % | 78,3 % | 87,0 % | 78,3 % | 100,0 % |
| 32 | Formycon | 100,0 % | 75,0 % | 50,0 % | 50,0 % | 50,0 % | 75,0 % | 100,0 % | 50,0 % | 50,0 % | 50,0 % | 50,0 % |
| 33 | Freenet | 100,0 % | 89,2 % | 92,3 % | 99,2 % | 91,5 % | 91,5 % | 97,7 % | 91,5 % | 89,2 % | 91,5 % | 99,2 % |

</details>
