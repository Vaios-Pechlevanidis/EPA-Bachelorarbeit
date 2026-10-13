> **Bereinigte Fassung für das Repository (2026-10-13).** Inhalt vollständig wie im Original vom
> 2026-10-09 (SHA-256 `3760407ce9faf2c26ed714398f995f9aaeb4d547efd9d46a15d56317f6713430`), mit einer Ausnahme: Titel von
> Meldungen sind durch „[Titel entfernt]“ ersetzt (E7), nach der Regel im `README.md` dieses Ordners
> (vollständige oder fast wörtliche Titel, wörtliche Titelstücke ab vier Wörtern außer Namen und
> Zahlenangaben, nachformulierte Titelaussagen); in drei Sätzen sind dafür Satzzeichen angepasst
> (Doppelpunkt bzw. Klammern). Datum, Herausgeber, Quellenart, Link und eigene Beschreibungen ohne
> Titelwortlaut bleiben. Methode, Zählung und Prüfung: `README.md`.

# DZ1 Entscheidungsprotokoll: Referenzzeiträume des Autors (agentengestützt)

Stand 2026-10-09. Commit f50b727 auf main, lokal, nicht gepusht. Datei backend/data/annotations.json, version 1.

## 1 Ergebnis

| Reihe | bewertete Monate | Zeiträume | Anker |
|---|---|---|---|
| Thyssenkrupp | 32 | 0 | 0 |
| Open Grid Europe | 22 | 0 | 0 |
| E.ON | 38 | 0 | 0 |
| RWE | 34 | 0 | 0 |
| Karlsruher Institut für Technologie | 27 | 0 | 0 |
| Technische Universität München | 13 | 0 | 0 |
| SAP SE | 26 | 1 | 1 |
| NTT DATA SE | 40 | 1 | 0 |
| 1&1 AG | 107 | 3 | 1 |
| Bechtle | 139 | 3 | 3 |
| Cancom | 115 | 3 | 2 |
| Carl Zeiss | 99 | 0 | 0 |
| Compugroup Medical Deutschland | 76 | 3 | 3 |
| Telekom | 165 | 3 | 1 |
| Freenet | 86 | 3 | 0 |

Gesamt: 20 Zeiträume in 8 von 15 Reihen, davon 11 mit Ereignisanker. Ein Eintrag stammt aus einem Zweifelsfall (|Δ| 0,30 bis 0,49) und steht nur wegen seines Ankers.

| Reihe | Zeitraum | Richtung | Δ | Anker |
|---|---|---|---|---|
| SAP SE | 2024-07 bis 2024-08 | rise | +0,54 | 2024-07-30: [Titel entfernt] |
| NTT DATA SE | 2020-06 bis 2020-06 | rise | +0,95 | keiner |
| 1&1 AG | 2016-10 bis 2016-10 | fall | -0,91 | keiner |
| 1&1 AG | 2018-04 bis 2018-04 | rise | +0,78 | 2018-01-12: [Titel entfernt] |
| 1&1 AG | 2018-09 bis 2018-09 | fall | -1,12 | keiner |
| Bechtle | 2021-02 bis 2021-02 | rise | +0,56 | 2021-01-28: [Titel entfernt] |
| Bechtle | 2021-08 bis 2021-09 | fall | -1,07 | 2021-08-09: [Titel entfernt] |
| Bechtle | 2023-01 bis 2023-01 | rise | +0,68 | 2022-11-03: [Titel entfernt] |
| Cancom | 2016-08 bis 2016-08 | rise | +1,04 | keiner |
| Cancom | 2021-07 bis 2021-07 | fall | -1,15 | 2021-07-07: [Titel entfernt] |
| Cancom | 2023-12 bis 2023-12 | rise | +0,85 | 2023-11-27: [Titel entfernt] |
| Compugroup Medical Deutschland | 2019-06 bis 2019-08 | fall | -0,56 | 2019-04-15: [Titel entfernt] |
| Compugroup Medical Deutschland | 2021-04 bis 2021-05 | rise | +0,47 | 2021-04-15: [Titel entfernt] |
| Compugroup Medical Deutschland | 2022-08 bis 2022-11 | fall | -0,67 | 2022-06-02: [Titel entfernt] |
| Telekom | 2009-12 bis 2009-12 | rise | +0,86 | 2009-12-08: [Titel entfernt] |
| Telekom | 2010-07 bis 2010-07 | fall | -1,10 | keiner |
| Telekom | 2013-05 bis 2013-05 | rise | +0,58 | keiner |
| Freenet | 2016-04 bis 2016-04 | rise | +1,04 | keiner |
| Freenet | 2020-02 bis 2020-02 | rise | +0,75 | keiner |
| Freenet | 2021-09 bis 2021-09 | fall | -0,75 | keiner |

## 2 Ablauf und Unabhängigkeit

- Stufe A allein aus backend/data/series/<id>_<slug>_employee.csv. Je Reihe ein blinder Annotator und ein adversarialer Prüfer (Workflow, 30 Agenten). Kein Prüfer hat ein Ergebnis geändert; ein Schiedsrichter war nicht nötig.
- Alle Zahlen stammen aus dem deterministischen Regelprüfer dz1_rechner.py (Scratchpad), der nur die CSV liest. Ein Endcheck rechnet jeden Eintrag, die note-Zahlen und Regel 5 erneut nach: keine Abweichung.
- Stufe B erst nach Abschluss aller 15 Reihen. Abruf sequenziell und gedrosselt über services.evidence_sources (Google News RSS; EQS nur bei bestätigter companyUUID), 176 Abrufe, keiner fehlgeschlagen. Je Fall ein Agent zur Ankerwahl und ein adversarialer Prüfer (42 Agenten). Die Monate der Einträge wurden in Stufe B nicht verändert.
- Nicht gelesen oder ausgeführt: Dashboard, API, backend/data/calibration/, Belegspeicher backend/data/context/, Erkennungs- und Erklärungscode, evaluate_detection.py und die übrigen Auswertungsskripte, annotations_zweitperson.json. Der abgebrochene erste Lauf wurde auf diese Sperren geprüft (66 Werkzeugaufrufe, kein Verstoß).
- validate_annotations.py (online, Datenbank nur SELECT): 20 Einträge, keine Fehler, keine Warnungen.

## 3 Setzungen des Agenten (vom Autor zu prüfen)

Diese Festlegungen füllen Lücken des Protokolls. Sie sind keine Protokollregeln.

1. **Bleiben auf dem neuen Niveau.** (a) Das Mittel der bis zu drei bewerteten Monate nach period_to liegt mindestens |Δ|/2 in Sprungrichtung vom Vorniveau entfernt. (b) Der erste bewertete Folgemonat liegt mindestens 0,25 Sterne in Sprungrichtung vom Vorniveau entfernt. (c) Ohne bewerteten Folgemonat ist das Bleiben nicht prüfbar: kein Eintrag.
2. **Vorniveau** aus mindestens drei bewerteten Monaten.
3. **Stützung dünner Monate.** Jeder Monat mit 5 bis 9 Bewertungen im Zeitraum braucht einen weiteren bewerteten Monat (im Zeitraum oder ersten Folgemonat), der selbst mindestens 0,5 Sterne in Sprungrichtung abweicht.
4. **Auswahl nach Regel 5** nach größtem |Δ|; jede note der Reihe nennt dann die Schwankung.
5. **Abgrenzung nach der Definition**, nicht nach größtem Δ: period_from ist der erste deutlich abweichende, period_to der erste Monat auf dem neuen Niveau.
6. **Anker (Stufe B)** nur bei Arbeitgeberbezug und dem Unternehmen selbst. Ausgeschlossen sind Produkt-, Zahlen-, Kurs- und Formalmeldungen sowie Rankings. Ein Ereignis mit klar entgegengesetzter erwarteter Wirkung zählt nicht; richtungsneutrale große Ereignisse wie Vorstandswechsel oder Übernahmen zählen. Beurteilt wurde nur nach Titel, Datum, Herausgeber und Kategorie, nicht nach dem Artikeltext.

## 4 Vergleich mit dem abgebrochenen ersten Lauf

Der erste Lauf (Folgeniveau-Setzung: 0,25 Sterne im Mittel der Folgemonate) hatte 26 Einträge, nicht committet. Unter der geschärften Setzung bestehen davon 12; 14 scheitern, überwiegend an der Rückkehr zum alten Niveau (Zweifelsfall-Tabelle der Anleitung, Regel 4) oder an fehlender Stützung dünner Monate.

| Erster Lauf | Ergebnis Lauf 2 |
|---|---|
| E.ON 2019-08..2019-08 fall | kein Eintrag |
| RWE 2018-08..2018-08 rise | kein Eintrag |
| RWE 2023-02..2023-02 rise | kein Eintrag |
| SAP SE 2024-07..2024-09 rise | überlappt mit 2024-07..2024-08 |
| NTT DATA SE 2018-05..2018-06 fall | kein Eintrag |
| NTT DATA SE 2019-07..2019-08 fall | kein Eintrag |
| NTT DATA SE 2020-06..2020-07 rise | überlappt mit 2020-06..2020-06 |
| 1&1 AG 2013-10..2013-10 rise | kein Eintrag |
| 1&1 AG 2017-10..2017-10 fall | kein Eintrag |
| 1&1 AG 2018-09..2018-11 fall | überlappt mit 2018-09..2018-09 |
| Bechtle 2019-08..2019-08 fall | kein Eintrag |
| Bechtle 2021-08..2021-08 fall | überlappt mit 2021-08..2021-09 |
| Bechtle 2023-08..2023-08 fall | kein Eintrag |
| Cancom 2016-08..2016-08 rise | identisch übernommen |
| Cancom 2021-07..2021-07 fall | identisch übernommen |
| Cancom 2024-05..2024-05 fall | kein Eintrag |
| Carl Zeiss 2019-11..2019-11 fall | kein Eintrag |
| Compugroup Medical Deutschland 2020-10..2020-10 fall | kein Eintrag |
| Compugroup Medical Deutschland 2021-04..2021-07 rise | überlappt mit 2021-04..2021-05 |
| Compugroup Medical Deutschland 2022-08..2022-11 fall | identisch übernommen |
| Telekom 2010-07..2010-07 fall | identisch übernommen |
| Telekom 2013-05..2013-05 rise | identisch übernommen |
| Telekom 2019-02..2019-05 rise | kein Eintrag |
| Freenet 2016-04..2016-06 rise | überlappt mit 2016-04..2016-04 |
| Freenet 2020-02..2020-02 rise | identisch übernommen |
| Freenet 2021-09..2021-12 fall | überlappt mit 2021-09..2021-09 |

## 5 Stufe B je Fall

### B01 SAP SE, 2024-07 bis 2024-08, rise, Δ +0.538 (eintrag)

Fenster 2024-04-01 bis 2024-08-31; 381 Meldungen, davon 381 im Fenster; Suchbegriff 'SAP'; EQS ja.

**Anker:** 2024-07-30, Spiegel (gnews): [Titel entfernt]  
https://news.google.com/rss/articles/CBMi5wFBVV95cUxNX2FzM2sxbFFudlVEbkxrWnhwRTRPVVlxeDBJdUt4UGJ1OHVtM1QxVmpDYnV0Z3czWmtEVnRQNXJHRU9pTlVNaW9XTFdLNi1GdlpIU0drU2lhZjI1NGdTaXE1QlFEeHp1elF6MkV6cTNyaDhWOGROWGtlNGg0SVRLbU1NTlRLVjNMWlJoa3QyRWdzV0VWWW91QTNCdGg5UXFKTHBQY0Q0d3pZMmY5X3FDaWZOZ0JjS3lzUnVjR3p2QU92TG10Y1dwRmxwN3doLTVfZUZIXzRwX3B1S0pwQWRLY1pOR093STQ?oc=5

**Wahl:** Die Fall-Liste habe ich vollständig gelesen (381 Meldungen, alle im_fenster = JA, Ankerfenster 2024-04-01 bis 2024-08-31). Der Zeitraum 2024-07 bis 2024-08 zeigt einen Anstieg (rise). Gesucht ist also ein entlastendes Ereignis oder ein großes richtungsneutrales Ereignis.

Die meisten Meldungen mit Arbeitgeberbezug wirken klar belastend und scheiden deshalb als Gegenrichtung aus:
- Stellenabbau von 2.600 Stellen (April) und die Ausweitung auf bis zu 10.000 Stellen (23.07.)
- Einschränkung des Homeoffice und härterer Ton des CEO (16./17.07.)
- Leistungsbewertung der Mitarbeitenden
- Unruhe um das überzeichnete Abfindungsprogramm
- Machtkampf im Betriebsrat

Der Vorstandsumbau vom 30.07.2024 liegt dagegen innerhalb des Zeitraums. Vorstandswechsel ist eine ausdrücklich genannte Art des Arbeitgeberbezugs und gilt als richtungsneutral groß. Er betrifft die SAP SE selbst, also auch die deutsche Belegschaft. Als Beleg habe ich idx 314 (Spiegel) gewählt, weil der Titel das Ereignis sachlich vollständig benennt.

Der stärkste Gegenkandidat war idx 61 ([Titel entfernt], 26.04.). Er wirkt entlastend, ist aber eine Begleitregelung zum belastenden Stellenabbau. Er liegt außerdem am Rand des Fensters, drei Monate vor dem Zeitraum, und wird im Juli von der Ausweitung des Abbaus überlagert.

Die WalkMe-Übernahme ist zwar richtungsneutral, betrifft aber vor allem das übernommene israelische Unternehmen. Ihr Bezug zur Belegschaft der SAP SE ist daher schwächer als der Vorstandswechsel.

Ich habe nur Titel, Datum, Herausgeber und Kategorie beurteilt. Den Inhalt der Artikel kenne ich nicht.

**Erwartete Wirkung:** richtungsneutral: Ein Vorstandsumbau ist ein großes Führungsereignis, dessen Wirkung auf die Beschäftigten nicht eindeutig belastend oder entlastend ist.

**Prüfer (bestaetigt):** Ich habe die Fall-Liste vollständig gelesen: 381 Meldungen, alle mit im_fenster = JA, Ankerfenster 2024-04-01 bis 2024-08-31. Andere Dateien habe ich nicht gelesen und keine Datei geändert.
(1) Fenster: idx 314 ist auf den 2024-07-30 datiert, im_fenster = JA. Die Meldung liegt damit sogar im Zeitraum selbst (2024-07 bis 2024-08).
(2) Unternehmen: Die Meldung betrifft eindeutig die SAP SE selbst. Kein Namensgleichheitsproblem wie bei SAP Garden, SAP Arena oder SAP-Partnerfirmen. Mehrere unabhängige Herausgeber melden dasselbe Ereignis am selben Tag: Spiegel 314, connect-professional 315, IT Reseller 316, Handelsblatt 317, FOCUS 318, Manager Magazin 310, am 31.07. zusätzlich Business Insider 320 und WiWo 321. Am 28.08. folgt ein Hintergrundbericht (372).
(3) Arbeitgeberbezug: "Wechsel in Vorstand oder Geschäftsführung" steht ausdrücklich in der Liste. Zwei Vorstandsmitglieder gehen (Vertrieb, Marketing). Es ist keine Produkt-, Zahlen-, Kurs- oder Formalmeldung.
(4) Richtung: Der Zeitraum steigt (rise). Ein Vorstandswechsel gilt laut Regel als richtungsneutral groß und ist damit zulässig. Eine klar entgegengesetzte, belastende Wirkung ist aus dem Titel nicht ableitbar. FOCUS (318) rahmt das Ereignis zwar als [Titel entfernt], der Kern bleibt aber ein Führungswechsel.
(5) Bessere Kandidaten geprüft:
- idx 61 [Titel entfernt] (26.04.): wirkt entlastend, liegt aber zwei Monate vor period_from. Die Zusage ist Teil des belastenden Abbaupakets vom April und wird am 23.07. von der Ausweitung auf bis zu 10.000 Stellen überlagert (291, 296, 301, 302). Nicht klar besser.
- idx 241 [Titel entfernt] (03.07.) und 251 [Titel entfernt] (09.07.): Wirkung offen. Zwei Wochen später folgt die Einschränkung des Homeoffice (272–280, belastend). Nicht klar entlastend.
- idx 202 [Titel entfernt] (19.06.): betrifft einen Standort und ist eher eine Forschungskooperation (199, 201, 285). Kleiner als der Vorstandsumbau.
- idx 236/248, neuer HR-Chef als Nachfolger von Younosi (01./08.07.): Der Titel zeigt keine Vorstands- oder Geschäftsführungsebene. Richtungsneutral und kleiner.
- WalkMe-Übernahme (164 ff., 364 Kartellfreigabe 23.08.): ebenfalls richtungsneutral groß, betrifft aber vor allem die übernommene Firma. Bezug zur SAP-Belegschaft schwächer.
- Plattners Abschied (104–123): Wechsel im Aufsichtsrat, nicht in Vorstand oder Geschäftsführung, zudem Hauptversammlungs-Kontext.
- Vertragsverlängerungen Klein und Müller (1, 6, 86–93): kein Wechsel.
- Alle übrigen Arbeitgebermeldungen sind belastend und laufen damit gegen die Richtung rise: Stellenabbau, Abfindungsandrang, Homeoffice-Einschränkung, Leistungsbewertung, Betriebsrats-Razzia, Vaterschaftsurlaub. Die Wahl hält. idx 314 (Spiegel, 30.07.2024) liegt im Fenster und sogar im Zeitraum selbst. Die Meldung betrifft die SAP SE selbst. Sie benennt einen Vorstandswechsel, eine ausdrücklich zugelassene Art des Arbeitgeberbezugs: [Titel entfernt]. Acht weitere Meldungen bestätigen das Ereignis übereinstimmend.

Erwartete Wirkung: richtungsneutral groß. Der Umbau der Führungsspitze ist für die Beschäftigten weder eindeutig belastend noch entlastend. Er steht damit nicht gegen den Anstieg (rise) und ist als Anker zulässig.

Ein klar besserer Kandidat fehlt:
- Die einzige deutlich entlastende Meldung ist die Jobgarantie bis Ende 2026 (idx 61). Sie liegt am Fensterrand im April, gehört zum belastenden Abbaupaket und wird im Juli durch die Ausweitung des Abbaus überlagert.
- Der Homeoffice-Vergleich (idx 241) hat eine offene Wirkung, die belastende Einschränkung folgt kurz danach.
- Die Standortinvestition München (idx 202) und die WalkMe-Übernahme sind kleiner bzw. für die SAP-Belegschaft weniger direkt.

Die Spiegel-Meldung benennt das Ereignis vollständig und neutral. Als Vertreter der Dubletten (310, 315–318, 320, 321) ist sie geeignet. Beurteilt wurden nur Titel, Datum, Herausgeber und Kategorie, der Artikelinhalt ist unbekannt.

### B02 NTT DATA SE, 2020-06 bis 2020-06, rise, Δ +0.950 (eintrag)

Fenster 2020-03-01 bis 2020-06-30; 1 Meldungen, davon 1 im Fenster; Suchbegriff '"NTT DATA" OR "NTT Data Deutschland" OR itelligence'; EQS nein.

**Anker:** keiner.

**Wahl:** Die Fall-Liste enthält genau eine Meldung (idx 1, 29.06.2020, Handelsblatt, im_fenster = JA). Der Titel lautet sinngemäß: [Titel entfernt]. Das ist eine Strategie- und Wachstumsmeldung, also eine Ambition oder Prognose. Der Titel nennt kein konkretes Ereignis mit Wirkung auf die Beschäftigten: keine Übernahme, keine Fusion oder Zusammenlegung von Gesellschaften, keinen Stellenauf- oder -abbau, keinen Vorstandswechsel und keine Restrukturierung. Nach Regel 7 wird nur nach Titel, Datum, Herausgeber und Kategorie beurteilt. Ohne erkennbaren Arbeitgeberbezug kann daraus kein Anker abgeleitet werden. Der Anstieg (rise, Δ 0.95) im Juni 2020 bleibt nach Stufe A als Veränderung ohne Ereignis stehen. Ergebnis: kein Anker.

**Erwartete Wirkung:** richtungsneutral; die einzige Meldung beschreibt eine Wachstumsambition ohne erkennbare Wirkung auf die Beschäftigten.

**Prüfer (kein_anker_bestaetigt):** Ich habe die Fall-Liste fall_B02.txt vollständig gelesen. Sie enthält genau eine Meldung: idx 1 vom 29.06.2020, Quelle gnews, Herausgeber Handelsblatt, ohne Kategorie, Titel [Titel entfernt].
Fenster: Das Ankerfenster reicht vom 01.03.2020 bis 30.06.2020. Der 29.06.2020 liegt darin, im_fenster = JA.
Unternehmen: Die Meldung nennt "NTT Data" und betrifft damit plausibel den Konzern. Einen ausdrücklichen Bezug zur deutschen Gesellschaft (NTT DATA SE bzw. NTT Data Deutschland) zeigt der Titel nicht. Er schließt ihn aber auch nicht aus.
Arbeitgeberbezug: Der Titel beschreibt eine Strategie- bzw. Wachstumsambition ([Titel entfernt]). Kein Merkmal aus der Liste ist erkennbar: keine Übernahme, keine Fusion oder Zusammenlegung, kein Umbau, kein Stellenaufbau oder -abbau, kein Vorstandswechsel, keine Standortentscheidung. Inhaltlich steht die Meldung den ausgeschlossenen Prognose- und Strategiemeldungen nahe. Ob hinter der Ambition konkrete Zukäufe oder Umstrukturierungen stehen, lässt sich nur vermuten, der Titel sagt es nicht. Nach Regel 7 entscheidet allein der Titel.
Richtung: Eine Wachstumsambition wäre bestenfalls schwach entlastend (rise). Auch dafür fehlt ein konkretes Ereignis mit Wirkung auf die Beschäftigten.
Bessere Kandidaten: Die Liste enthält keine weitere Meldung. EQS wurde nicht abgefragt (keine bestätigte companyUUID). Die Null-Wahl hält. Die einzige Meldung liegt zwar im Fenster und betrifft NTT Data. Nach Titel, Datum, Herausgeber und Kategorie ist sie aber eine Strategie- bzw. Ambitionsmeldung ohne erkennbares Ereignis mit Wirkung auf die Beschäftigten. Damit hat sie keinen Arbeitgeberbezug im Sinne der Liste. Die erwartete Wirkung ist richtungsneutral bis allenfalls schwach entlastend und nicht an ein konkretes Ereignis gebunden. Einen Bezug zu Übernahme, Umbau oder Expansion müsste man in den Titel hineinlesen. Nach der Regel "im Zweifel kein Anker" bleibt es daher bei keinem Anker. Ein übersehener Kandidat existiert nicht. Der Anstieg im Juni 2020 (rise, Δ 0.95) bleibt nach Stufe A als Veränderung ohne Ereignis stehen.

### B03 1&1 AG, 2016-10 bis 2016-10, fall, Δ -0.908 (eintrag)

Fenster 2016-07-01 bis 2016-10-31; 20 Meldungen, davon 20 im Fenster; Suchbegriff '"1&1"'; EQS ja.

**Anker:** keiner.

**Wahl:** Ich habe alle 20 Meldungen gelesen, alle liegen im Fenster vom 01.07. bis 31.10.2016. Fast alle sind Produkt- und Kundenmeldungen (Glasfaser, Messenger FreeMessage, Stromverträge, Fritz!Box), Werbung oder Blogbeiträge von 1&1 (Pokémon Go, Christian Ulmen), Lokal- oder Fremdmeldungen (Sylt, Adrian Stern, ein Ehepaar ohne Anschluss) oder Kapitalmarkt-Formalia von Drillisch (Quartalszahlen, Vorankündigungen von Finanzberichten, Stimmrechtsmitteilung der Deutschen Bank). Nichts davon ist nach Regel 7 ein Anker. Arbeitgeberbezug hat höchstens idx 1 (01.07.2016, WiWo, [Titel entfernt]). Die Meldung beschreibt aber laut Titel nur eine Markenumstellung bei der Konzernschwester Versatel innerhalb von United Internet. Eine Restrukturierung, ein Stellenabbau oder ein Umbau mit Folgen für die Beschäftigten von 1&1 ist daraus nicht zu erkennen. Betroffen ist in erster Linie Versatel, nicht das bewertete Unternehmen. Eine belastende Wirkung, die zum Rückgang im Oktober 2016 (Δ -0.908) passen würde, ist nicht erkennbar. Die Meldung liegt außerdem am äußersten Rand des Fensters. Im Zweifel setze ich keinen Anker. Der Rückgang aus Stufe A bleibt ohne Ereignis bestehen.

**Erwartete Wirkung:** Entfällt. Die einzige Grenzmeldung (idx 1, Markenumstellung von Versatel) wirkt nach dem Titel richtungsneutral und schwach, nicht belastend.

**Prüfer (kein_anker_bestaetigt):** Ich habe die ganze Fall-Liste gelesen, 20 Meldungen. Das Fenster reicht vom 01.07. bis 31.10.2016, und alle Meldungen sind mit im_fenster = JA markiert. Jede Meldung habe ich auf Arbeitgeberbezug geprüft. Produkt- und Kundenmeldungen sind idx 2, 3, 4, 5, 9, 11, 14, 15, 16 und 18: Glasfaser, Gigabit-Anschlüsse, der Messenger FreeMessage, der Stromvertrieb und eine Fritz!Box. Werbung oder Blogbeiträge von 1&1 sind idx 7 (Pokémon Go) und idx 12 (Christian Ulmen). Fremd- oder Lokalmeldungen ohne Bezug zum Unternehmen sind idx 10 (Ehepaar in Lage), idx 13 (Adrian Stern, Radio Pilatus) und idx 17 (Sylt). Zahlen und Kapitalmarkt-Formalia von Drillisch sind idx 6 (Q2-Wachstum), idx 8 und 20 (Vorankündigungen von Finanzberichten) und idx 19 (Stimmrechtsmitteilung der Deutschen Bank). Als Grenzfall bleibt nur idx 1 (01.07.2016, WiWo): [Titel entfernt]. Ich habe geprüft, ob die Markenumstellung als Umbau oder Integration mit Wirkung auf die Belegschaft gelten kann. Der Titel nennt aber nur ein neues Markenbild bei Versatel, der Konzernschwester innerhalb von United Internet. Einen Stellenabbau, eine Restrukturierung oder eine Veränderung für die Beschäftigten von 1&1 nennt er nicht. Dazu kommt die Namensunschärfe: Die EQS-Meldungen stammen von Drillisch, die Google-News-Treffer betreffen die United-Internet-Marke 1&1. Ein klar besserer Kandidat fehlt. Die Wahl „kein Anker“ hält. Im Fenster steht keine Meldung mit klarem Arbeitgeberbezug zu den Beschäftigten von 1&1. Fast alle Meldungen sind nach Regel 7 ausdrücklich ausgeschlossen. Dazu gehören Produkt- und Kundenmeldungen, Quartalszahlen, Vorankündigungen von Finanzberichten, eine Stimmrechtsmitteilung, Werbung und Meldungen über Dritte. Die einzige Grenzmeldung ist idx 1 zur Markenumstellung von Versatel auf das 1&1-Blau. Sie beschreibt laut Titel eine Marken- und Designfrage bei einer Konzernschwester. Ein Umbau, ein Stellenabbau oder eine andere Folge für die Belegschaft von 1&1 ist daraus nicht zu erkennen. Die erwartete Wirkung auf die Beschäftigten ist höchstens schwach und richtungsneutral, nicht belastend. Zum Rückgang im Oktober 2016 (Δ -0.908) passt sie deshalb nicht. Die Meldung liegt außerdem am äußersten Anfang des Fensters, und im Zweifel gilt: kein Anker. Der Rückgang aus Stufe A bleibt ohne Ereignis bestehen.

### B04 1&1 AG, 2018-04 bis 2018-04, rise, Δ +0.777 (eintrag)

Fenster 2018-01-01 bis 2018-04-30; 18 Meldungen, davon 17 im Fenster; Suchbegriff '"1&1"'; EQS ja.

**Anker:** 2018-01-12, EQS News (eqs): [Titel entfernt]  
https://www.eqs-news.com/news/corporate/drillisch-ag-drillisch-turns-into-1-1-drillisch/79a44aa5-a543-448c-81dc-35ed8e62665b

**Wahl:** Die Meldung ist vom 12.01.2018 und liegt damit im Ankerfenster (2018-01-01 bis 2018-04-30, im_fenster = JA). Sie betrifft das Unternehmen selbst: Drillisch AG bzw. 1&1 Drillisch ist die Vorgängerin der 1&1 AG, Emittent ist EQS News / 1&1 AG, Kategorie Corporate. Es geht um einen Zusammenschluss mit Umfirmierung, also um eine Fusion oder einen Umbau mit Wirkung auf die Belegschaft. Für die Richtung rise ist die Wirkung richtungsneutral groß. Von den Meldungen in der Liste ist das die einzige mit klarem Arbeitgeberbezug. Alle anderen sind Produkt- und Kundenmeldungen, Finanz- und Kapitalmarktformalia, Hauptversammlungs-Formalia oder öffentliche Äußerungen ohne Bezug zur Belegschaft. Einschränkung: Die Meldung liegt etwa drei Monate vor dem Zeitraum (2018-04). Laut Fenster-Regel ist das zulässig, der zeitliche Abstand schwächt die Stützung aber etwas ab.

**Erwartete Wirkung:** Richtungsneutral groß: Ein Zusammenschluss mit neuer Firmierung verändert den Arbeitgeber spürbar. Eine klar belastende Wirkung lässt sich aus dem Titel nicht ablesen, deshalb widerspricht die Meldung dem Anstieg nicht.

**Prüfer (bestaetigt):** Ich habe die Fall-Liste vollständig gelesen (18 Meldungen, Ankerfenster 2018-01-01 bis 2018-04-30). Geprüft habe ich fünf Punkte. (1) Fenster: idx 4 ist vom 2018-01-12 und mit im_fenster = JA markiert. Das liegt am vorderen Rand des Dreimonatsfensters, ist aber zulässig. (2) Unternehmen: Emittent ist EQS News / 1&1 AG, Kategorie Corporate. Drillisch AG bzw. 1&1 Drillisch ist die Rechtsvorgängerin der heutigen 1&1 AG. Eine Verwechslung wegen Namensgleichheit liegt nicht vor. (3) Arbeitgeberbezug: Der Titel beschreibt [Titel entfernt]. Dahinter steht der Zusammenschluss mit 1&1 Telecommunication, also Fusion bzw. Umbau der Konzernstruktur mit neuer Muttergesellschaft. Das fällt unter die Kategorie Übernahme/Fusion. Mein Einwand war, dass die Meldung nur eine Umfirmierung sein könnte. Er greift nicht, denn die Umbenennung folgt aus der Einbringung eines operativen Unternehmensteils und ist damit eine Strukturänderung. (4) Richtung: Die Wirkung ist richtungsneutral groß, aus dem Titel geht nichts klar Belastendes hervor. Sie widerspricht dem Anstieg also nicht. (5) Bessere Kandidaten: Alle anderen 17 Meldungen fallen weg. idx 1, 2 und 11 sind Produktmeldungen. idx 6, 7 und 9 sind Kunden- bzw. Verbrauchermeldungen. idx 10, 13 und 17 sind Finanzberichte und Ad-hoc-Zahlen. idx 15 gehört zu den Hauptversammlungs-Formalia. idx 12 und 14 sind Marketing bzw. öffentliche Äußerungen gegenüber der Telekom ohne Wirkung auf die Belegschaft. idx 3 ist ein Gastbeitrag ohne erkennbaren Bezug. idx 5, 8 und 16 sind Portalinhalte von WEB.DE/GMX/1&1 ohne Unternehmensbezug. idx 18 liegt außerhalb des Fensters (nein). Die Wahl hält. Die Meldung vom 12.01.2018 liegt im Ankerfenster (im_fenster = JA) und betrifft das Unternehmen selbst, nämlich die Vorgängergesellschaft der 1&1 AG, gemeldet über EQS als Corporate-Meldung. Inhalt ist ein Zusammenschluss bzw. Konzernumbau: 1&1 Telecommunication wird in Drillisch eingebracht, und es entsteht 1&1 Drillisch. Damit liegt ein Arbeitgeberbezug in der Kategorie Fusion/Übernahme vor. Die erwartete Wirkung ist richtungsneutral groß: ein neuer Konzernrahmen und eine neue Firmierung für die Beschäftigten. Ein klar belastender Effekt ist aus dem Titel nicht abzulesen, deshalb steht die Meldung nicht im Widerspruch zum Anstieg (rise) im April 2018. Kein anderer Eintrag der Liste hat einen Arbeitgeberbezug. Einschränkung: Die Meldung liegt rund drei Monate vor dem Zeitraum, am Rand des zulässigen Fensters. Die Stützung ist deshalb eher schwach, nach der Fenster-Regel aber gültig.

### B05 1&1 AG, 2018-09 bis 2018-09, fall, Δ -1.122 (eintrag)

Fenster 2018-06-01 bis 2018-09-30; 38 Meldungen, davon 38 im Fenster; Suchbegriff '"1&1"'; EQS ja.

**Anker:** keiner.

**Wahl:** Ich habe alle 38 Meldungen gelesen, alle liegen im Ankerfenster vom 2018-06-01 bis 2018-09-30. Keine nennt ein Ereignis mit klarer Wirkung auf die Beschäftigten der 1&1 (Drillisch) AG. Es gibt keine Meldung zu Stellenabbau, Umbau mit Personalfolgen, Vorstandswechsel, Standort, Tarif oder Betriebsrat. Der größte Teil sind Produkt-, Tarif- und Kundenmeldungen (Router, Super-Vectoring, Datentarife, FritzOS, Phishing-Warnung) oder Portal-Inhalte von 1&1/GMX ohne Bezug zum Unternehmen. Dazu kommen Pflicht- und Zahlenmeldungen (idx 19 Finanzberichte, idx 24 Halbjahr 2018); beide sind ausgeschlossene Kategorien. Der nächste Kandidat ist idx 38 vom 2018-09-29: [Titel entfernt]. Der Titel beschreibt eine Bereinigung des Markenportfolios, also eine Vermarktungs- und Kundenmeldung. Eine Folge für die Belegschaft (Abbau, Zusammenlegung, Standort) nennt er nicht. Nach der Ausschlussregel für Produkt- und Kundenmeldungen und dem Grundsatz „im Zweifel kein Anker“ wähle ich sie nicht. Ergebnis: kein Anker. Die Stufe-A-Beurteilung für 2018-09 bleibt unverändert.

**Erwartete Wirkung:** entfällt: Ohne Anker gibt es keine erwartete Wirkung. Der Rückgang im September 2018 bleibt als Veränderung ohne Ereignis stehen.

**Prüfer (kein_anker_bestaetigt):** Ich habe die Fall-Liste vollständig gelesen: 38 Meldungen, alle mit im_fenster = JA (Fenster 2018-06-01 bis 2018-09-30). Jede Meldung habe ich darauf geprüft, ob sie das Unternehmen betrifft, einen Arbeitgeberbezug hat und zur Richtung fall passt. (1) idx 38 (2018-09-29, [Titel entfernt]) betrifft das Unternehmen, liegt im Fenster und ist der stärkste Kandidat. Laut Titel ist es aber eine Bereinigung des Markenportfolios, also eine Vermarktungs- und Kundenmeldung. Personalfolgen wie Abbau, Zusammenlegung oder Standortschließung nennt der Titel nicht. Nur über die Deutung „Umbau“ könnte man einen Arbeitgeberbezug herstellen, und das ist unsicher. Hinzu kommt das Datum: Die Meldung erscheint am vorletzten Tag des Zeitraums 2018-09. (2) idx 22 (2018-08-05, [Titel entfernt]): Das Unternehmen ist nicht genannt, und es ist eine Marken- und Produktmeldung. (3) idx 25 (2018-08-20, [Titel entfernt]): Der Käufer ist nicht genannt. Im Hosting-Geschäft ist eher die Schwester 1&1 IONOS bzw. United Internet gemeint als die 1&1 (Drillisch) AG, und eine Wirkung auf die hiesigen Beschäftigten ist nicht erkennbar. (4) idx 23 (2018-08-10) ist ein CEO-Wechsel bei Unitymedia, also einem anderen Unternehmen. (5) idx 3, 18, 27 und 35 sind Porträts und wettbewerbspolitische Äußerungen von Dommermuth, kein Führungswechsel und kein Ereignis. (6) idx 19 und 24 sind WpHG-Vorankündigung bzw. Halbjahreszahlen und damit ausgeschlossene Kategorien; die Halbjahreszahlen wären zudem eher entlastend. (7) Der Rest sind Produkt- und Tariftests, Router- und FritzOS-Updates, eine Phishing-Warnung und Portalinhalte von 1&1/GMX ohne Unternehmensbezug (idx 1, 12, 17, 20, 21, 29, 36). Einen klar besseren oder übersehenen Kandidaten mit Arbeitgeberbezug finde ich nicht. Die Wahl „kein Anker“ hält. Keine Meldung im Fenster nennt ein Ereignis mit erkennbarer Wirkung auf die Beschäftigten der 1&1 (Drillisch) AG: kein Stellenabbau, kein Umbau mit Personalfolgen, kein Vorstandswechsel, kein Standort-, Tarif- oder Betriebsratsthema. Der einzige ernsthafte Kandidat ist idx 38, die Einstellung mehrerer Discountmarken. Nach dem Titel ist das eine Produkt- und Vermarktungsmeldung. Belastend für die Beschäftigten wäre sie nur, wenn man unbelegte Personalfolgen annimmt, und das widerspricht dem Grundsatz „im Zweifel kein Anker“. Die übrigen Konzern- und Namensbezüge (World4you, Unitymedia, Dommermuth-Porträts) betreffen andere Gesellschaften oder sind keine Ereignisse. Der Rückgang im September 2018 bleibt daher als Veränderung ohne Ereignis stehen, und die Stufe-A-Beurteilung bleibt unverändert.

### B06 Bechtle, 2021-02 bis 2021-02, rise, Δ +0.556 (eintrag)

Fenster 2020-11-01 bis 2021-02-28; 24 Meldungen, davon 24 im Fenster; Suchbegriff 'Bechtle'; EQS ja.

**Anker:** 2021-01-28, FAMILIENUNTERNEHMEN im FOKUS (gnews): [Titel entfernt]  
https://news.google.com/rss/articles/CBMiggFBVV95cUxOVjNLRDhkNzlTelFsMVoyUGVBeXlCck1EdURncTJIZjRySzJUXy1ER1hGOWpmNGhoamVzeHMxcXplZWo2NGpMb3R6RHR0TzMtMFByN0NEQUVIc3plaEJPcGdiWjFwdVJjV2hhWlJ4cEdLX1NEY2tpMks2c3l2bHVwVHd3?oc=5

**Wahl:** Das Ankerfenster reicht vom 2020-11-01 bis zum 2021-02-28. Die Meldung ist auf den 2021-01-28 datiert, liegt also im Fenster (im_fenster = JA) und etwa einen Monat vor dem Zeitraum 2021-02. Sie betrifft eindeutig die Bechtle AG (Titel: [Titel entfernt]) und fällt in die Ankerkategorie Wechsel in Vorstand oder Geschäftsführung. Idx 17 ([Titel entfernt], gleicher Tag) meldet offensichtlich dasselbe Ereignis. Idx 18 ist konkreter, weil die Meldung Person und Funktion nennt. Für den Anstieg passt die erwartete Wirkung, denn eine Erweiterung der Leitung ist kein belastendes Signal. Einschränkungen: Ein Bereichsvorstand gehört nicht zum Vorstand der AG, und die Wirkung auf die gesamte Belegschaft ist eher klein. Der Anker ist deshalb nur schwach. In der Liste gibt es aber kein klar entlastendes Ereignis mit stärkerem Arbeitgeberbezug.

**Erwartete Wirkung:** Richtungsneutral bis leicht entlastend: Ein neuer Bereichsvorstand im Zuge eines erweiterten Führungsteams deutet eher auf Wachstum als auf Abbau hin und widerspricht daher nicht der Richtung rise.

**Prüfer (bestaetigt):** Ich habe alle 24 Einträge der Fall-Liste fall_B06.txt gelesen. Das Ankerfenster reicht vom 2020-11-01 bis 2021-02-28, und alle Einträge stehen auf im_fenster = JA. Idx 18 ist auf den 2021-01-28 datiert und liegt damit im Fenster. Der Titel nennt ausdrücklich die Bechtle AG, eine Namensverwechslung ist also ausgeschlossen. Idx 17 (IT-ZOOM, gleicher Tag, [Titel entfernt]) meldet dasselbe Ereignis; idx 18 ist konkreter. Die übrigen Kandidaten habe ich so geprüft:
- Idx 22 (2021-02-14): [Titel entfernt]. Das betrifft zwar den AG-Vorstand, ist aber kein Wechsel, sondern Kontinuität. Die Wirkung ist neutral und nicht klar stärker als bei idx 18.
- Idx 19 ([Titel entfernt], Corporate, 2021-02-04): nach dem Titel eine Meldung zu Geschäftszahlen, also kein Anker.
- Idx 7 und 8 (Ladepark und E-Dienstwagen): eine Flotten- und Nachhaltigkeitsmeldung. Am Rand berührt sie Leistungen für Beschäftigte, sie fällt aber in keine der Kategorien Gehalt, Boni, Arbeitszeit oder Büroregeln. Kein klar besserer Kandidat.
- Idx 16: nennt Bechtle im Titel nicht.
- Idx 2: ein Interview, kein Ereignis.
- Idx 4: eine Prognose.
- Idx 5, 9 und 21: Stimmrechtsmitteilungen.
- Idx 14 und 15: Formalia zu Finanzberichten.
- Idx 12: ein Ranking.
- Idx 1, 3, 10, 11, 13, 20, 23 und 24: betreffen andere Unternehmen oder sind themenfremd.
Ein klar entlastendes Ereignis mit stärkerem Arbeitgeberbezug, etwa zu Einstellungen, Gehalt oder Tarif, gibt es nicht. Die Wahl hält, aber der Anker ist schwach. Die Meldung liegt im Fenster, etwa einen Monat vor dem Zeitraum 2021-02, und betrifft eindeutig die Bechtle AG. Sie meldet eine neue Besetzung in der obersten Leitungsebene (Bereichsvorstand, Erweiterung des Führungsteams) und fällt damit unter Wechsel in Vorstand oder Geschäftsführung.

Einschränkung: Ein Bereichsvorstand gehört nicht zum Vorstand der AG, und die Wirkung auf die gesamte Belegschaft ist eher klein. Die erwartete Wirkung ist richtungsneutral bis leicht entlastend, denn eine Erweiterung der Leitung deutet auf Wachstum hin. Sie widerspricht also nicht der Richtung rise.

Die einzige ernsthafte Alternative, idx 22 (Vertragsverlängerung Olemotz), ist kein Wechsel, sondern Kontinuität und damit nicht klar besser. Ein anderer Kandidat mit klarem Arbeitgeberbezug fehlt. Der Zweifel reicht nicht aus, um den Anker zu verwerfen, weil die Meldung formal in eine genannte Ankerkategorie fällt.

### B07 Bechtle, 2021-08 bis 2021-09, fall, Δ -1.071 (eintrag)

Fenster 2021-05-01 bis 2021-09-30; 21 Meldungen, davon 21 im Fenster; Suchbegriff 'Bechtle'; EQS ja.

**Anker:** 2021-08-09, IT Reseller (gnews): [Titel entfernt]  
https://news.google.com/rss/articles/CBMiekFVX3lxTE9OVzhWLXc2SFNxckdPLWRBZV85YzRwU3Q2Y2t3aXVGSTAyMF9xQ3VPVXNaVnRMMlFfZzI5YV9LSGtiOFU5WVBDRzlVYnVxLV9aNFNaMUVuaDZoNUt6S19LMnBQNjRnVG5oOElwenl2dWNNS094ejdqX3h3?oc=5

**Wahl:** Meldung vom 2021-08-09 liegt im Ankerfenster (im_fenster = JA) und sogar im Zeitraum selbst (2021-08). Der Titel nennt eine Übernahme durch Bechtle, die nach Regel 7 als Arbeitgeberbezug gilt und als richtungsneutral großes Ereignis zulässig ist; sie steht nicht im Widerspruch zur Richtung fall. Einschränkung: Nach dem Titel handelt es sich um einen einzelnen, vermutlich kleineren Zukauf, wie Bechtle sie regelmäßig tätigt. Die Wirkung auf die Gesamtbelegschaft dürfte daher gering sein, der Anker ist also eher schwach. Alle anderen Meldungen im Fenster sind Quartals- und Prognosezahlen (4, 15, 20, 21), Kapitalmarkt- und HV-Formalia (2, 3, 5, 11, 16, 19), Produkt- oder Kooperationsmeldungen (8, 10) oder betreffen andere Firmen bzw. haben keinen Bezug zu Bechtle (1, 6, 7, 9, 12, 14). Ein belastendes Ereignis wie Stellenabbau oder Restrukturierung ist in der Liste nicht enthalten.

**Erwartete Wirkung:** richtungsneutral: Ein Zukauf kann Integrationsaufwand und Umstrukturierung bringen, aber auch Wachstum signalisieren; eine klare Belastung oder Entlastung ist nicht ableitbar.

**Prüfer (bestaetigt):** Ich habe die Fall-Liste vollständig gelesen (21 Meldungen, alle im_fenster = JA, Ankerfenster 2021-05-01 bis 2021-09-30). Zum Fenster: idx 18 ist vom 2021-08-09 (gnews, IT Reseller) und liegt im Fenster, sogar im Zeitraum selbst. Zum Unternehmen: Der Titel lautet [Titel entfernt], Bechtle ist also klar die handelnde Firma. Eine Namensgleichheit gibt es nicht. Zum Arbeitgeberbezug: Eine Übernahme steht ausdrücklich in der Liste der Regel 7. Die Größe des Zukaufs geht aus dem Titel nicht hervor. Es handelt sich wohl um einen kleineren Zukauf, wie Bechtle sie regelmäßig tätigt. Dieser Einwand schwächt den Anker, schließt ihn nach Regel 7 aber nicht aus, denn dort ist keine Mindestgröße genannt. Zur Richtung: Eine Übernahme gilt nach Regel 7 als richtungsneutral und steht nicht im Widerspruch zu fall. Zu besseren Kandidaten: idx 17 ist eine PR-Managerin in Österreich, also unterhalb von Vorstand und Geschäftsführung und nicht die deutsche Gesellschaft. idx 13 ist ein Firmenbesuch des Oberbürgermeisters, ein reiner Imagetermin. idx 8 ist laut Titel eine Kooperation mit S&T und eine Geschäftsmeldung ohne genannte Übernahme oder Abspaltung. Die Nummern 4, 11, 15, 20 und 21 sind Zahlen- oder Prognosemeldungen. Die Nummern 2, 3, 5, 16 und 19 sind HV-, Stimmrechts-, Directors'-Dealings- bzw. Kapitalmarktformalia. idx 10 ist eine Produktmeldung. Die Nummern 1, 6, 7, 9, 12 und 14 betreffen andere Firmen oder haben keinen Bechtle-Bezug. In der Liste fehlt ein belastendes Ereignis wie Stellenabbau, Restrukturierung oder Vorstandswechsel. Die Meldung idx 18 liegt im Fenster und betrifft eindeutig Bechtle als Käufer. Als Übernahme fällt sie unter die Arbeitgeberbezüge der Regel 7. Erwartete Wirkung: richtungsneutral. Ein Zukauf bringt Integrationsaufwand und neue Kolleginnen und Kollegen, aber nach dem Titel keine klare Belastung oder Entlastung für die Belegschaft. Er widerspricht also nicht der Richtung fall. Der Anker ist schwach, weil es sich wohl um einen kleineren Zukauf unter vielen handelt. Ein Ausschlussgrund nach Regel 7 ist das aber nicht, und kein anderer Eintrag der Liste hat überhaupt einen Arbeitgeberbezug. Die Wahl hält deshalb.

### B08 Bechtle, 2023-01 bis 2023-01, rise, Δ +0.682 (eintrag)

Fenster 2022-10-01 bis 2023-01-31; 18 Meldungen, davon 18 im Fenster; Suchbegriff 'Bechtle'; EQS ja.

**Anker:** 2022-11-03, wir - Das Magazin für Unternehmerfamilien (gnews): [Titel entfernt]  
https://news.google.com/rss/articles/CBMiqAFBVV95cUxPdjJmclFNQk9DOW4xSnJVSmh0T3E1akhDWjRUTkdRSzA0MWZLaVBMTHJGZHVLdHFuUjJKV3JBSkY1NlZGdUE2YlRwd2ZxZHl6U1ljM21RRm9wbnRhLUdFQUVkTWhNZlZLNGVVYkpTcldRdVVweVNabi1CVVRJbC1LVFZtM1FQc0dfWG13N1ZNenhVWGV0dU5iN0J4YS1nakItb0ZDZFdreHE?oc=5

**Wahl:** Die Meldung vom 2022-11-03 liegt im Ankerfenster (2022-10-01 bis 2023-01-31, im_fenster = JA). Sie betrifft laut Titel die Bechtle AG selbst. Die Quelle ist deutschsprachig, und „Bereichsvorstand“ ist eine Leitungsebene der deutschen Konzernstruktur. Damit fällt sie unter die Kategorie Wechsel in Vorstand oder Geschäftsführung. Die erwartete Wirkung ist richtungsneutral, also kein Widerspruch zur Richtung rise. Ein klar entlastendes Ereignis gibt es in der Liste nicht. Die übrigen Meldungen im Fenster sind ausgeschlossene Typen: Stimmrechtsmitteilung (1), Arbeitgeberauszeichnung (3), Wachstums- und Geschäftszahlen (4), Kursmeldung (6), Kundenmeldung (7), Finanzbericht-Vorankündigungen (14, 15), Sponsoring (18). Hinzu kommen Meldungen ohne erkennbaren Bezug zu Bechtle: Namensgleichheit (12), Gedenksteine (11), Kongressbericht (17). Einschränkung: Der Wechsel betrifft nur eine Ebene unter dem Konzernvorstand und dürfte daher eher klein wirken. Der Abstand zum Zeitraum 2023-01 beträgt rund zwei Monate. Die Stufe-A-Beurteilung bleibt unverändert.

**Erwartete Wirkung:** richtungsneutral: Ein neuer Bereichsvorstand kann die Führung und Ausrichtung eines Unternehmensbereichs verändern, eine eindeutig be- oder entlastende Wirkung ist aber nicht vorgegeben.

**Prüfer (bestaetigt):** Ich habe alle 18 Einträge der Fall-Liste gelesen. Ankerfenster: 2022-10-01 bis 2023-01-31; alle Einträge haben im_fenster = JA.

Zu idx 2 (2022-11-03): Die Meldung liegt im Fenster (im_fenster = JA), rund zwei Monate vor period_from. Der Titel nennt Bechtle ausdrücklich. Die Quelle ist deutschsprachig, und "Bereichsvorstand" ist eine Leitungsebene der Bechtle AG, der deutschen Gesellschaft. Ein Hinweis auf eine Namensgleichheit fehlt.

Arbeitgeberbezug: Es handelt sich um einen Wechsel auf der Vorstandsebene, wenn auch nicht im Konzernvorstand. Die Meldung ist weder eine Produkt-, Zahlen-, Kurs- noch eine Formalmeldung.

Richtung: Die erwartete Wirkung ist richtungsneutral, eine neue Führung für einen Unternehmensbereich. Das widerspricht nicht der Richtung rise.

Geprüfte Gegenkandidaten:
- idx 10 (2022-12-21, Inside-it.ch, [Titel entfernt]): Die Meldung liegt näher am Zeitraum und ist ebenfalls ein Führungswechsel. Die Quelle ist aber ein Schweizer Portal. Aus dem Titel geht nicht hervor, ob die Bechtle AG oder Bechtle Schweiz gemeint ist und auf welcher Ebene die Stelle liegt. Im Zweifel ist sie daher nicht klar besser als idx 2.
- idx 8 (HR-Jobwechsel 2022): Ein Bezug zu Bechtle fehlt im Titel.
- idx 9 ([Titel entfernt], Report Verlag): Der Titel nennt weder Bechtle noch einen Bezug zu den Beschäftigten. Am ehesten ist es eine Partnerschafts- oder Kundenmeldung.
- idx 13 und idx 5 (Gütersloh): Bechtle wird nicht genannt (idx 13), oder die Meldung handelt von Geschäft und Kunden (idx 5).
- idx 16: kommunale Meldung über Unterschleißheim.
- Ausgeschlossene Typen: Stimmrechtsmitteilung (1), Arbeitgeberauszeichnung (3), Wachstumszahlen (4), Kursmeldung (6), Kundenmeldung (7), Finanzbericht-Vorankündigungen (14, 15), Sponsoring (18).
- Ohne Bezug zu Bechtle: Gedenksteine (11), Namensgleichheit "Golte-Bechtle" (12), Kongressbericht (17).

Ein klar entlastendes Ereignis, das besser zu rise passen würde, gibt es nicht. Die Wahl hält. Die Meldung vom 2022-11-03 liegt im Ankerfenster (im_fenster = JA) und betrifft laut Titel eindeutig Bechtle. Sie hat Arbeitgeberbezug, weil eine neue Person auf die Vorstandsebene eines Unternehmensbereichs kommt; das fällt unter "Wechsel in Vorstand oder Geschäftsführung".

Die erwartete Wirkung ist richtungsneutral: Die neue Bereichsführung kann Führung und Ausrichtung für einen Teil der Belegschaft verändern. Damit steht sie nicht im Widerspruch zur Richtung rise.

Einschränkungen: Die Ebene liegt unter dem Konzernvorstand, die Wirkung ist daher vermutlich klein, und der Abstand zu 2023-01 beträgt etwa zwei Monate.

Der einzige ernsthafte Gegenkandidat ist idx 10. Aus dem Titel geht dort nicht hervor, ob die Bechtle AG oder die Schweizer Gesellschaft gemeint ist, deshalb ist er nicht klar besser. Ein entlastendes Ereignis fehlt in der Liste. Die Stufe-A-Beurteilung des Zeitraums bleibt unverändert.

### B09 Cancom, 2016-08 bis 2016-08, rise, Δ +1.036 (eintrag)

Fenster 2016-05-01 bis 2016-08-31; 5 Meldungen, davon 5 im Fenster; Suchbegriff 'Cancom'; EQS ja.

**Anker:** keiner.

**Wahl:** Alle fünf Meldungen liegen im Fenster (im_fenster = JA), keine erfüllt aber den Arbeitgeberbezug nach Regel 7. idx 2 und 3 sind Directors' Dealings (Verkäufe von Klaus Weinmann und Ray Kober) und damit ausdrücklich ausgeschlossen. idx 4 meldet eine Platzierung im Experton Cloud Vendor Benchmark, also ein Ranking, und ist ebenfalls ausgeschlossen. idx 1 ([Titel entfernt], IT-ZOOM) ist dem Titel nach ein Fach- bzw. Produktbeitrag zur Cloud-Migration und kein Standortumzug. idx 5 (deutsche-startups.de, 2016-08-29) beschreibt [Titel entfernt]. Der Titel nennt Cancom nicht, und eine Beteiligung an einem Start-up ist keine Übernahme, Fusion, Abspaltung oder Restrukturierung mit erkennbarer Folge für die Cancom-Belegschaft. Deshalb ergibt die Prüfung: kein Anker.

**Erwartete Wirkung:** Nicht zutreffend: Kein Anker gewählt. Der Anstieg (rise, Δ 1.036) im August 2016 bleibt als Veränderung ohne Ereignis stehen.

**Prüfer (kein_anker_bestaetigt):** Ich habe die Fall-Liste vollständig gelesen: fünf Meldungen, Ankerfenster 2016-05-01 bis 2016-08-31, alle mit im_fenster = JA. Danach habe ich jede Meldung einzeln daraufhin geprüft, ob sie doch ein Anker sein könnte.
- idx 2 und 3 (2016-06-17, EQS, Kategorie Directors' Dealings, Verkäufe von Weinmann und Kober): Diese Meldungen sind nach Regel 7 ausdrücklich ausgeschlossen. Ein Wechsel im Vorstand lässt sich aus ihnen nicht ablesen.
- idx 4 (2016-06-30, EQS Media, Experton Cloud Vendor Benchmark): Das ist ein Ranking und damit ausgeschlossen.
- idx 1 (2016-06-06, IT-ZOOM, [Titel entfernt]): Der Titel nennt weder Cancom noch einen Standort. Er beschreibt dem Inhalt nach eine Cloud-Migration und ist damit ein Fach- oder Produktbeitrag. Die Lesart "Standortverlagerung" trägt der Titel nicht.
- idx 5 (2016-08-29, deutsche-startups.de, [Titel entfernt]): Das ist der einzige ernsthafte Kandidat, weil er zeitlich im Ausschlagsmonat liegt. Der Titel nennt Cancom aber nicht, sodass der Bezug zum Unternehmen nur vermutet ist; im Zweifel ist das kein Anker. Selbst wenn Cancom gemeint ist, beschreibt der Titel eine Investition in ein Start-up. Das ist keine Übernahme, Fusion, Abspaltung oder Restrukturierung mit Folgen für die eigenen Beschäftigten. Die erwartete Wirkung auf die Belegschaft ist neutral bis vernachlässigbar und erklärt den Anstieg nicht. Einen klar besseren Kandidaten gibt es nicht. Ein Anker ist also nicht übersehen worden. Die Wahl "kein Anker" hält. Keine der fünf Meldungen im Fenster hat einen Arbeitgeberbezug nach Regel 7:
- Zwei Meldungen sind Directors' Dealings und eine ist ein Ranking; beide Arten sind ausdrücklich ausgeschlossen.
- Der IT-ZOOM-Beitrag ist dem Titel nach ein Fachbeitrag zur Cloud-Migration und meldet keinen Standortumzug.
- Die Reparando-Meldung nennt Cancom im Titel nicht. Auch wenn Cancom gemeint wäre, wäre eine Start-up-Beteiligung keine Übernahme oder Restrukturierung mit Wirkung auf die Cancom-Belegschaft. Die erwartete Wirkung ist neutral bis gering und weder entlastend noch richtungsneutral groß.

Der Anstieg im August 2016 (rise, Δ 1.036) bleibt deshalb als Veränderung ohne Ereignis stehen.

### B10 Cancom, 2021-07 bis 2021-07, fall, Δ -1.153 (eintrag)

Fenster 2021-04-01 bis 2021-07-31; 12 Meldungen, davon 12 im Fenster; Suchbegriff 'Cancom'; EQS ja.

**Anker:** 2021-07-07, EQS News (eqs): [Titel entfernt]  
https://www.eqs-news.com/news/corporate/cancom-rudiger-rath-appointed-member-of-the-executive-board-and-coo/7cbe8d7d-ccfc-4329-a111-c09bdfce316e

**Wahl:** Das Fenster reicht vom 2021-04-01 bis 2021-07-31. Die Meldung vom 2021-07-07 liegt darin (im_fenster = JA) und im Zeitraum 2021-07 selbst. Die Ad-hoc-Meldung kommt vom Emittenten selbst (EQS, Corporate). Sie betrifft direkt die deutsche CANCOM SE, deren Beschäftigte hier bewerten. Ein Vorstandswechsel gilt als richtungsneutral großes Ereignis und darf deshalb einen Fall der Richtung fall stützen. Es gibt nur eine Alternative mit Arbeitgeberbezug: den Verkauf der Geschäfte in Großbritannien und Irland (idx 11/12). Er trifft vor allem die Beschäftigten dort, nicht die deutsche Belegschaft. Außerdem fällt er auf den 28. Juli, also ans Ende des Zeitraums, und die Meldung stellt den Buchgewinn in den Vordergrund. Für deutsche Beschäftigte ist die erwartete Wirkung daher unklar und eher gering. Gewählt wird deshalb die Vorstandsberufung. Die Stufe-A-Beurteilung des Zeitraums (2021-07, Δ -1,153) bleibt unverändert.

**Erwartete Wirkung:** Richtungsneutral groß: Ein neuer COO von außen (bisher Europa-Chef bei Logicalis) kann Umbau und Unsicherheit im operativen Geschäft bringen. Das passt zu einem Rückgang, ist aber nicht eindeutig belastend.

**Prüfer (bestaetigt):** Ich habe die Fall-Liste vollständig gelesen (12 Meldungen, alle im_fenster = JA, Fenster 2021-04-01 bis 2021-07-31). Für idx 8 gilt: Die Meldung ist vom 2021-07-07 und liegt damit im Fenster und sogar im Zeitraum 2021-07 selbst. Herausgeber ist EQS News / CANCOM SE, also der Emittent. Es gibt keine Namensgleichheit mit einer anderen Firma. Die Kategorie Corporate ist hier keine Formalmeldung, inhaltlich geht es um eine Berufung in den Vorstand. Danach habe ich die Alternativen geprüft. idx 1 und 3 sind Produkt- und Content-Meldungen von CANCOM.info. idx 2 ist eine Stimmrechtsmitteilung. idx 4 enthält Quartalszahlen und eine Prognose. idx 5 und 7 sind Hauptversammlungs-Formalia. Das alles sind keine Anker. idx 9 und 10 berichten über dasselbe Ereignis wie idx 8 und sind damit Duplikate. idx 6 (2021-05-25) meldet nur [Titel entfernt]. Das ist eine Vorstufe ohne konkrete Wirkung auf die Belegschaft. idx 11 und 12 (2021-07-28) melden den Verkauf dieser Geschäfte. Ein Verkauf von Unternehmensteilen hat zwar Arbeitgeberbezug, betrifft aber vor allem die Beschäftigten in Großbritannien und Irland und nicht die deutsche Gesellschaft, deren Beschäftigte hier bewerten. Die Titel stellen zudem den Buchgewinn in den Vordergrund, und für deutsche Beschäftigte ist keine belastende Wirkung erkennbar. Einen Kandidaten mit klar belastender Wirkung, etwa Stellenabbau, Standortschließung oder einen Tarifkonflikt in Deutschland, gibt es in der Liste nicht. Die Wahl hält. Die Emittentenmeldung idx 8 vom 7. Juli 2021 liegt im Fenster (im_fenster = JA) und im Zeitraum 2021-07 selbst. Sie betrifft direkt die CANCOM SE, also die deutsche Muttergesellschaft. Der Arbeitgeberbezug ergibt sich aus dem Wechsel im Vorstand: Ein neues Vorstandsmitglied wird berufen und übernimmt als COO das operative Geschäft. Erwartete Wirkung: richtungsneutral groß. Ein von außen geholter COO (bisher Europa-Chef bei Logicalis) kann im operativen Geschäft Umbau und Unsicherheit auslösen. Damit darf er einen Zeitraum der Richtung fall stützen, auch wenn die Wirkung nicht eindeutig belastend ist. Der einzige ernsthafte Gegenkandidat ist der Verkauf der Geschäfte in Großbritannien und Irland (idx 11 vom 28. Juli). Er ist nicht klar besser, weil er vor allem Beschäftigte außerhalb Deutschlands betrifft und die Meldung als Gewinnmeldung formuliert ist. Die Stufe-A-Beurteilung (2021-07, Δ −1,153) bleibt unverändert.

### B11 Cancom, 2023-12 bis 2023-12, rise, Δ +0.855 (eintrag)

Fenster 2023-09-01 bis 2023-12-31; 20 Meldungen, davon 20 im Fenster; Suchbegriff 'Cancom'; EQS ja.

**Anker:** 2023-11-27, EQS News (eqs): [Titel entfernt]  
https://www.eqs-news.com/news/corporate/cancom-se-cancom-strengthens-expertise-in-the-area-of-complex-it-infrastructure-and-managed-services-through-the-acquisition-of-significant-parts-of-dextradata-gmbh/cdd0ed78-0d1b-4d98-b044-bbc21f1aa760

**Wahl:** Der Zeitraum ist 2023-12, das Ankerfenster reicht vom 2023-09-01 bis 2023-12-31. Die EQS-Primärmeldung vom 2023-11-27 (Kategorie Corporate) liegt im Fenster (im_fenster = JA). Sie betrifft Cancom selbst und eine deutsche Zielgesellschaft. Eine Übernahme steht ausdrücklich in der Liste der Arbeitgeberbezüge. Ihre erwartete Wirkung (Wachstum, eher entlastend) widerspricht der Richtung rise nicht. Die übrigen Meldungen im Fenster sind fast alle Kapitalmarkt-Formalia: Stimmrechte, eigene Aktien, Kapitalmarktinformationen ohne Inhalt, Kapitalherabsetzung, Ankündigung von Quartalsberichten. Dazu kommen Geschäftszahlen. Keine davon ist ein Anker. Der Wechsel im Aufsichtsratsvorsitz (Idx 17/18/19) ist der wichtigste Gegenkandidat. Er betrifft aber das Kontrollorgan und nicht Vorstand oder Geschäftsführung, und auf die Beschäftigten wirkt er nur mittelbar. Die Fusion zu Cancom Switzerland (Idx 3) betrifft eine Schweizer Gesellschaft, nicht die deutsche Belegschaft. Unter den Meldungen im Fenster hat die DextraData-Übernahme deshalb den klarsten Arbeitgeberbezug. Den Zusammenhang mit dem Anstieg im Dezember belegt das nicht, er ist nur zeitlich plausibel.

**Erwartete Wirkung:** Richtungsneutral groß, eher entlastend: Ein Zukauf in Deutschland signalisiert Wachstum und Ausbau, ohne Hinweis auf Abbau. Das passt zur Richtung rise.

**Prüfer (bestaetigt):** Ich habe die Fall-Liste vollständig gelesen (20 Meldungen). Fenster: Ankerfenster 2023-09-01 bis 2023-12-31. Idx 10 ist am 2023-11-27 datiert und mit im_fenster = JA markiert, das hält. Unternehmen: EQS-Primärmeldung der CANCOM SE selbst, Zielgesellschaft ist die deutsche DextraData GmbH. Eine Namensverwechslung liegt nicht vor. Arbeitgeberbezug: Es ist keine Produkt-, Zahlen- oder Formalmeldung, sondern eine Übernahme von Unternehmensteilen, und die steht ausdrücklich in der Liste. Der Einwand, der Bezug sei für den Käufer schwächer als für das übernommene Unternehmen, trägt nicht. Die Regel schränkt die Übernahme nicht auf eine Seite ein, und Integration und Ausbau betreffen die deutsche Belegschaft. Richtung: Die erwartete Wirkung ist richtungsneutral bis entlastend (Wachstum, kein Hinweis auf Abbau). Das widerspricht rise nicht. Bessere Kandidaten: Idx 17/18/19 ([Titel entfernt], Dezember 2023, im Zeitraum selbst) habe ich als stärksten Gegenkandidaten geprüft. Die Regel nennt aber nur den Wechsel in Vorstand oder Geschäftsführung, und der Aufsichtsrat ist das Kontrollorgan. Weinmanns frühere Rolle bei Cancom darf ich nicht hinzuziehen, weil nur Titel, Datum, Herausgeber und Kategorie zählen. Damit ist das kein klar besserer Anker. Idx 3 (Fusion zu Cancom Switzerland) betrifft eine Schweizer Gesellschaft, nicht die deutschen Bewertenden, also im Zweifel kein Anker. Idx 12 ist eine Sekundärmeldung zum selben Ereignis wie Idx 10. Idx 8 sind Geschäftszahlen, Idx 4 ist ein Ranking zur österreichischen K-Businesscom. Idx 14 betrifft offenbar ein anderes Unternehmen (SEO, Schmidheiny). Der Rest sind Stimmrechte, eigene Aktien, Kapitalmarktinformationen ohne Inhalt, Kapitalherabsetzung und die Ankündigung von Quartalsberichten, also durchweg kein Anker. Die Wahl hält. Idx 10 liegt im Fenster (2023-11-27, im_fenster = JA) und betrifft die CANCOM SE direkt, mit einer deutschen Zielgesellschaft. Die Meldung beschreibt eine Übernahme von Unternehmensteilen, und eine Übernahme steht ausdrücklich in der Liste der Arbeitgeberbezüge. Die erwartete Wirkung ist richtungsneutral groß bis entlastend: Die Gruppe wächst und baut aus, Beschäftigte werden integriert, Hinweise auf Abbau gibt es nicht. Das passt zu rise. Es gibt keinen klar besseren Kandidaten. Der Wechsel im Aufsichtsratsvorsitz (Idx 17/18/19) fällt zwar in den Zeitraum selbst, betrifft aber nicht Vorstand oder Geschäftsführung, wie die Regel es verlangt, und wirkt auf die Beschäftigten nur mittelbar. Die Schweizer Fusion (Idx 3) betrifft nicht die deutsche Belegschaft. Alle übrigen Meldungen sind Formal-, Zahlen- oder Rankingmeldungen. Die Wahl der EQS-Primärmeldung statt der Sekundärmeldung Idx 12 ist richtig. Ob die Übernahme den Anstieg im Dezember verursacht hat, ist nicht belegt; der Zusammenhang ist nur zeitlich plausibel.

### B12 Compugroup Medical Deutschland, 2019-06 bis 2019-08, fall, Δ -0.564 (eintrag)

Fenster 2019-03-01 bis 2019-08-31; 27 Meldungen, davon 27 im Fenster; Suchbegriff '"CompuGroup Medical" OR CompuGroup'; EQS ja.

**Anker:** 2019-04-15, EQS News (eqs): [Titel entfernt]  
https://www.eqs-news.com/news/corporate/compugroup-medical-se-upcoming-changes-to-the-cgm-management-board/41976a47-8c49-4ddc-a325-1f2701112d5a

**Wahl:** Die Meldung idx 8 vom 2019-04-15 liegt im Ankerfenster (2019-03-01 bis 2019-08-31, im_fenster = JA). Sie stammt vom Unternehmen selbst (EQS, Kategorie Corporate) und betrifft direkt die CompuGroup Medical SE. Laut Titel kündigt sie Veränderungen im Vorstand an. Ein Vorstandswechsel zählt zu den ausdrücklich zugelassenen richtungsneutral großen Ereignissen. Für einen Rückgang (Δ -0.564) ist er plausibel, weil ein Führungswechsel Unsicherheit schafft und oft eine neue strategische Ausrichtung mit sich bringt. Dass sich die Vorstandsbesetzung tatsächlich ändert, zeigen auch die späteren Directors'-Dealings-Meldungen: Im Juli und August erhalten drei Vorstandsmitglieder Aktienoptionen aus dem Programm 2019. Diese Meldungen gehören aber zu einer ausgeschlossenen Kategorie und dienen nur als Indiz. Unter den Kandidaten ist dies die einzige Meldung mit klarem Arbeitgeberbezug, deren Wirkung nicht der Richtung fall widerspricht. Die übrigen Meldungen behandeln Produkte (TI-Anbindung, E-Rezept, Z1.PRO, Konnektor, eAU), Finanzberichte, Prognosen, Hauptversammlungs-Formalia oder Kapitalmarktinformationen ohne Inhalt.

**Erwartete Wirkung:** Richtungsneutral groß: Ein Vorstandsumbau kann in der Belegschaft Unsicherheit über Kurs und Organisation auslösen und ist damit mit einem Rückgang vereinbar.

**Prüfer (bestaetigt):** Ich habe die Fall-Liste mit allen 27 Meldungen gelesen. Das Ankerfenster reicht vom 2019-03-01 bis 2019-08-31, und alle Meldungen sind mit im_fenster = JA markiert. Fenster: idx 8 ist vom 2019-04-15 und liegt damit im Fenster (JA). Unternehmen: Die Meldung kommt von CompuGroup Medical SE selbst über EQS (Kategorie Corporate). Eine Verwechslung mit einer gleichnamigen Firma ist ausgeschlossen. Arbeitgeberbezug: Laut Titel geht es um [Titel entfernt]. Das ist ein ausdrücklich zugelassener Wechsel in Vorstand oder Geschäftsführung, also keine Produkt-, Zahlen-, Kurs- oder Formalmeldung. Richtung: Ein Vorstandswechsel ist ein richtungsneutral großes Ereignis und mit dem Rückgang (fall, Δ -0.564) vereinbar. Bessere Kandidaten habe ich geprüft. idx 15 ([Titel entfernt]) und idx 25 ([Titel entfernt]) wirken entlastend und laufen damit klar gegen die Richtung fall. Sie scheiden aus. idx 23/24 ([Titel entfernt]) sind Umbenennungen einer Tochter. Eine Wirkung auf die Belegschaft geht aus dem Titel nicht hervor, sie sind also schwächer. idx 9 ([Titel entfernt]) erscheint am selben Tag wie idx 8 und beschreibt wohl denselben personellen Vorgang. Der Titel ist aber unbestimmt, und es ist eine Sekundärquelle, also kein besserer Anker. idx 18/19/27 sind Directors' Dealings und damit ausgeschlossen. Die übrigen Meldungen behandeln Produkte (TI, E-Rezept, Z1.PRO, eAU, Konnektor, App auf Rezept), Finanzberichte, Prognose, HV-Einberufung oder Kapitalmarktinformationen ohne Inhalt. Eine belastende Arbeitgebermeldung wie Stellenabbau, Restrukturierung oder Streik fehlt in der Liste. Die Wahl hält. idx 8 vom 2019-04-15 liegt im Fenster (im_fenster = JA) und ist eine Corporate-Meldung der CompuGroup Medical SE selbst. Sie kündigt Veränderungen im Vorstand an und hat damit einen klaren Arbeitgeberbezug: Wechsel in der Unternehmensführung. Erwartete Wirkung: richtungsneutral groß. Ein Vorstandsumbau kann bei den Beschäftigten Unsicherheit über Kurs und Organisation auslösen und passt damit zum Rückgang der Gesamtbewertung im Zeitraum 2019-06 bis 2019-08. Einen klar besseren Kandidaten gibt es nicht. Die beiden Meldungen über Personalaufbau (idx 15, 25) wirken entgegengesetzt. Die Umbenennung von Lauer-Fischer (idx 23/24) hat keine erkennbare Wirkung auf die Belegschaft. idx 9 ist unbestimmt und betrifft vermutlich denselben Vorgang. Alle anderen Meldungen gehören zu ausgeschlossenen Kategorien.

### B13 Compugroup Medical Deutschland, 2022-08 bis 2022-11, fall, Δ -0.668 (eintrag)

Fenster 2022-05-01 bis 2022-11-30; 65 Meldungen, davon 65 im Fenster; Suchbegriff '"CompuGroup Medical" OR CompuGroup'; EQS ja.

**Anker:** 2022-06-02, EQS News (eqs): [Titel entfernt]  
https://www.eqs-news.com/news/ad-hoc/compugroup-medical-se-co-kgaa-appoints-cfo-michael-rauch-as-spokesman-of-the-managing-directors/0f184911-dfbe-47d1-9382-a5da4e1045d5

**Wahl:** Die Ad-hoc-Meldung vom 2022-06-02 liegt im Ankerfenster (2022-05-01 bis 2022-11-30, im_fenster = JA), etwa zwei Monate vor period_from 2022-08. Herausgeber ist die Gesellschaft selbst, betroffen ist also das bewertete Unternehmen. Am selben Tag berichten mehrere unabhängige Quellen über dasselbe Ereignis: Apotheke Adhoc mit [Titel entfernt] (idx 8), kma Online mit [Titel entfernt] (idx 9) und Healthcare Marketing (idx 10). Damit ist das Ereignis gut belegt. Ein Wechsel an der Spitze zählt ausdrücklich als Arbeitgeberbezug. Die Ablösung des CEO und der Umbau der Board-Struktur gehören zu den Ereignissen, die zum Rückgang der Gesamtbewertung ab August 2022 (Δ -0.668) passen. Für die übrigen Monate des Zeitraums gibt es keine Meldung mit klarem, belastendem Arbeitgeberbezug: Kursmeldungen, Prognosen, Directors' Dealings, Produktmeldungen zum KoCoBox-Hack und die SAP-Kooperation sind kein Anker. Ich wähle die Ad-hoc-Meldung, weil sie die Primärquelle ist. Die Pressemeldungen dazu sind Dubletten.

**Erwartete Wirkung:** Eher belastend: Der CEO wird abgelöst ([Titel entfernt]) und die Führungsstruktur neu geordnet. Das kann bei den Beschäftigten Unsicherheit auslösen und passt damit zur Richtung fall. Zumindest ist es ein großes, richtungsneutrales Ereignis.

**Prüfer (bestaetigt):** Ich habe die Fall-Liste mit allen 65 Einträgen vollständig gelesen.

Fenster: idx 6 ist am 2022-06-02 datiert. Das liegt im Ankerfenster 2022-05-01 bis 2022-11-30 und ist mit im_fenster = JA markiert, etwa zwei Monate vor period_from 2022-08.

Unternehmen: Herausgeber ist die CompuGroup Medical SE & Co. KGaA selbst. Das ist die deutsche Konzernmutter mit Sitz in Koblenz, zu der die bewertete deutsche Gesellschaft gehört. Eine Namensverwechslung ist ausgeschlossen. idx 8, 9 und 10 bestätigen das Ereignis aus unabhängigen Quellen ([Titel entfernt], [Titel entfernt]).

Arbeitgeberbezug: Ein Wechsel an der Unternehmensspitze steht ausdrücklich in der Liste. Die Kategorie lautet zwar "Ad-hoc", die Meldung hat aber Inhalt und ist keine Formalmeldung ohne Inhalt.

Richtung: Die Ablösung des CEO und die neu geordnete Board-Struktur sind mindestens richtungsneutral groß, eher belastend durch Unsicherheit bei den Beschäftigten. Eine entgegengesetzte Wirkung ist nicht erkennbar.

Andere Kandidaten:
- idx 7–10 sind Dubletten desselben Ereignisses.
- idx 12 ([Titel entfernt]) betrifft nur eine Tochtergesellschaft und wiegt weniger.
- idx 3, 59, 60 und 61 sind Zukäufe. Ihre Wirkung ist eher expansiv oder neutral und passt nicht zu fall.
- idx 39 ([Titel entfernt]) ist im Umfang unklar.
- idx 24–26 sind Aktienoptionen der Geschäftsführung, also Directors' Dealings und ausgeschlossen.
- idx 47 (Prognoseanpassung), idx 35 und 50 (Zahlen) sowie idx 40 (Capital Markets Day) sind ausgeschlossen.
- idx 44–46 (KoCoBox-Hack) und idx 32 und 65 (Preise, Wartungskosten) sind Produkt- und Kundenmeldungen.
- idx 63 und 64 (SAP-Kooperation) sind Produkt- bzw. Geschäftsmeldungen.
- idx 2 (Kosten der Cyber-Attacke) ist eine Zahlenmeldung ohne klare Wirkung auf die Belegschaft.
- idx 31 ([Titel entfernt]) lässt sich nach dem Titel nicht sicher CGM zuordnen.
- idx 13, 15, 30, 36–38, 41, 53–55 betreffen andere Firmen oder Personen.

Ein klar besserer Kandidat fehlt. Die Wahl hält. Die Ad-hoc-Meldung vom 2. Juni 2022 liegt im Fenster (im_fenster = JA) und betrifft die bewertete CompuGroup-Medical-Gruppe direkt. Als Wechsel an der Unternehmensspitze hat sie einen ausdrücklich zulässigen Arbeitgeberbezug: Der CEO wird abgelöst, CFO Rauch übernimmt als Sprecher, die Board-Struktur wird umgebaut.

Erwartete Wirkung: ein großes, richtungsneutrales Ereignis mit eher belastender Tendenz, weil die Führung neu geordnet wird und das Unsicherheit auslöst. Das passt zur Richtung fall (Δ -0.668 ab August 2022).

Als Anker kommen nur die Meldungen zu diesem Ereignis in Frage. Die Primärquelle idx 6 ist eine vertretbare Wahl. Alle übrigen Meldungen im Fenster sind Zahlen-, Prognose-, Produkt-, Directors'-Dealings- oder Fremdfirmenmeldungen, Zukäufe mit eher expansiver Wirkung oder ein schwächerer Wechsel bei einer Tochter (idx 12).

### B14 Telekom, 2009-12 bis 2009-12, rise, Δ +0.855 (eintrag)

Fenster 2009-09-01 bis 2009-12-31; 23 Meldungen, davon 23 im Fenster; Suchbegriff '"Deutsche Telekom"'; EQS ja.

**Anker:** 2009-12-08, Horizont.net (gnews): [Titel entfernt]  
https://news.google.com/rss/articles/CBMimwFBVV95cUxQMWMxRUxaNGZTOWNkeVhnbUJqTzU1cDY2M05rUy1YUWVKQ3U5dThyU1ZfMGQ2YWlabDc5QXlJZXdGSGNmQVdQMFFJcnVHeFF6WmhRYzdFZk42UnRNSnFwT0dDN0pVbzZLZ1RmREM2MzgxRGtTQTBDZGNKS1d6cDQ0ZDNCcTR4N2JFV3pvLVRqZ19tdU9zQ0xNRm55OA?oc=5

**Wahl:** Meldung 17 ist am 2009-12-08 datiert und liegt damit im Ankerfenster (im_fenster = JA). Sie fällt sogar in den Zeitraum 2009-12 selbst. Herausgeber ist Horizont.net. Inhaltlich betrifft sie die Deutsche Telekom AG direkt: [Titel entfernt]. Ein Wechsel in Vorstand oder Geschäftsführung zählt ausdrücklich als Arbeitgeberbezug. Nach der Regel gilt er als richtungsneutral großes Ereignis und kommt deshalb als Anker für einen Anstieg (rise) in Frage. Eine klar belastende Gegenwirkung lässt sich am Titel nicht ablesen. Die zweite starke Möglichkeit ist Meldung 3, die Fusion von T-Mobile UK und Orange UK. Sie liegt aber zeitlich weiter weg und betrifft vor allem die britische Tochter, nicht die deutschen Beschäftigten, die hier bewerten. Deshalb ist Meldung 17 der passendere Anker. Die Monate des Zeitraums bleiben unverändert.

**Erwartete Wirkung:** Richtungsneutral: Ein Vorstandsabgang ist ein großes Ereignis ohne feste Richtung. Er widerspricht dem Anstieg nicht.

**Prüfer (bestaetigt):** Ich habe alle 23 Meldungen der Fall-Liste gelesen. Das Ankerfenster reicht vom 2009-09-01 bis zum 2009-12-31, und alle Meldungen sind mit im_fenster = JA markiert. Meldung 17 ist am 2009-12-08 datiert, Herausgeber ist Horizont.net. Sie liegt im Fenster und sogar im Zeitraum 2009-12 selbst. Unternehmensbezug: Der Titel nennt ausdrücklich die Deutsche Telekom und ihren Vorstand. Eine Verwechslung mit einem anderen Telekom-Unternehmen ist damit ausgeschlossen. Arbeitgeberbezug: Ein Wechsel im Vorstand steht ausdrücklich auf der Liste. Es handelt sich nicht um eine Produkt-, Zahlen-, Kurs- oder Formalmeldung. Richtung: Der Abgang eines Vorstands ist ein großes Ereignis ohne feste Richtung. Nach dem Titel hat er keine klar belastende Gegenwirkung zum Anstieg. Die übrigen Kandidaten im Einzelnen: Meldung 3 ist die Ad-hoc-Meldung zur Fusion von T-Mobile UK und Orange UK (2009-09-08). Sie ist eine richtungsneutrale Fusion, betrifft aber die britische Tochter, nicht die deutschen Beschäftigten, und liegt am Rand des Fensters. Meldung 1, [Titel entfernt], ist eine regionale Routinemeldung von geringem Gewicht. Meldung 4 betrifft T-Mobile Austria, also eine ausländische Tochter. In Meldung 7, [Titel entfernt], ist ein Außenstehender betroffen. Ein Bezug auf die Beschäftigten ist am Titel nicht erkennbar, und die Wirkung wäre eher belastend, also gegen den Anstieg. Meldungen 13 und 15 sind Sponsoring. Meldung 6 ist eine WpHG-Formalmeldung. Meldung 9 betrifft O2 und Alice, also andere Firmen. Meldungen 2, 5, 8, 10–12, 14, 16, 18–22 sind Agentur-, Werbe- und Rankingmeldungen ohne Telekom-Arbeitgeberbezug. Meldung 23 ist ein unspezifischer Jahresrückblick. Keiner dieser Kandidaten ist klar besser. Die Wahl hält. Meldung 17 vom 2009-12-08 liegt im Fenster (im_fenster = JA) und fällt sogar in den Zeitraum selbst. Sie betrifft die Deutsche Telekom AG direkt. Mit [Titel entfernt] meldet sie einen Wechsel im Vorstand, der ausdrücklich als Arbeitgeberbezug gilt. Erwartete Wirkung: richtungsneutral groß. Ein Vorstandswechsel kann Unruhe oder Erleichterung auslösen. Eine klar belastende Wirkung, die dem Anstieg (rise) widerspräche, lässt sich am Titel nicht ablesen. Damit kommt die Meldung als Anker in Frage. Meldung 3, die Fusion in Großbritannien, betrifft vor allem die britische Tochter und liegt zeitlich weiter weg. Die übrigen Meldungen sind Sponsoring-, Formal-, Fremdfirmen- oder Randmeldungen. Ein klar besserer Anker existiert nicht. Die Monate des Zeitraums bleiben unverändert.

### B15 Telekom, 2010-07 bis 2010-07, fall, Δ -1.096 (eintrag)

Fenster 2010-04-01 bis 2010-07-31; 32 Meldungen, davon 32 im Fenster; Suchbegriff '"Deutsche Telekom"'; EQS ja.

**Anker:** keiner.

**Wahl:** Ich habe alle 32 Meldungen gelesen, alle liegen im Fenster vom 01.04. bis 31.07.2010 (im_fenster = JA). Keine davon beschreibt ein Ereignis mit Wirkung auf die Beschäftigten der Deutschen Telekom oder ihrer deutschen Gesellschaft.

- Die EQS-Meldungen sind ausgeschlossene Kategorien: Finanzberichts-Vorankündigungen nach WpHG (idx 9, 28) und Directors' Dealings (idx 14, 22).
- Die Telekom-Meldungen bei Google News betreffen Werbung, Etats und Kunden: Mobilfunk-Hotline (idx 6), Werbeetat für 11833 (idx 21) und Werbekampagne für Liga Total (idx 26). Das sind Produkt- und Kundenmeldungen, kein Anker.
- Die übrigen Treffer betreffen andere Firmen, zum Beispiel Agenturen, O2 und 1&1, oder sind Rauschen ohne Telekom-Bezug im Titel.
- Der einzige Personalwechsel mit Telekom-Bezug (idx 15) betrifft die US-Tochter T-Mobile USA, also nicht die deutsche Gesellschaft, deren Beschäftigte hier bewerten.

Nach Regel 7 bleibt der Zeitraum ohne Anker (fall, Δ -1.096) stehen. Ergebnis: kein Anker.

**Erwartete Wirkung:** entfällt, weil kein Anker gewählt wurde; keine Meldung lässt eine belastende Wirkung auf die deutsche Belegschaft erwarten.

**Prüfer (kein_anker_bestaetigt):** Ich habe die Fall-Liste fall_B15.txt vollständig gelesen. Sie enthält 32 Meldungen, alle mit im_fenster = JA, das Fenster reicht vom 01.04. bis 31.07.2010. Ich habe gesucht, ob die Wahl null einen passenden Anker übersieht.
(1) Unternehmen: Nur die Meldungen idx 6, 9, 14, 15, 21, 22, 26 und 28 nennen die Telekom im Titel. Die übrigen betreffen andere Firmen oder Personalien anderer Firmen: Agenturen, Verlage, O2, 1&1, Advocard, Weber Shandwick, Mediacom, Power of Sales. Dazu kommen Rauschtreffer: Zertifikate, iPad-Ratgeber, Arztausweis, Bus und Sponsoring-Studie.
(2) Arbeitgeberbezug: idx 9 und 28 sind WpHG-Vorankündigungen von Finanzberichten, idx 14 und 22 sind Directors' Dealings. Das sind ausgeschlossene Formal- und Kapitalmarktmeldungen. idx 6 (Mobilfunk-Hotline), idx 21 (Werbeetat 11833) und idx 26 (Werbekampagne Liga Total) sind Kunden-, Produkt- und Werbemeldungen ohne Wirkung auf die Beschäftigten.
(3) Stärkster Gegenkandidat ist idx 15 vom 26.05.2010: [Titel entfernt]. Ein Führungswechsel wäre grundsätzlich richtungsneutral groß. Er betrifft aber die US-Tochter und nicht die Deutsche Telekom AG oder ihre deutsche Gesellschaft, deren Beschäftigte hier bewerten. Am Titel ist keine Wirkung auf die deutsche Belegschaft erkennbar. Nach der Regel zu Konzernen gilt im Zweifel: kein Anker.
(4) Richtung fall: Keine Meldung im Fenster lässt eine belastende Wirkung auf die deutsche Belegschaft erwarten. Es gibt keinen Stellenabbau, keinen Umbau, keinen Tarifkonflikt und keinen Vorstandswechsel im Mutterkonzern. Die Wahl null hält. Keine der 32 Meldungen im Fenster erfüllt zugleich zwei Bedingungen: Sie betrifft die Deutsche Telekom bzw. ihre deutsche Gesellschaft, und sie hat einen Arbeitgeberbezug nach der Liste. Die EQS-Meldungen sind Finanzberichts-Vorankündigungen und Directors' Dealings, also ausdrücklich ausgeschlossen. Die Telekom-Treffer bei Google News sind Service-, Werbe- und Etatmeldungen, also Produkt- und Kundenmeldungen. Der CEO-Wechsel bei T-Mobile USA (idx 15) betrifft eine ausländische Tochter. Eine erwartete Wirkung auf die bewertenden Beschäftigten in Deutschland ist am Titel nicht erkennbar, deshalb im Zweifel kein Anker. Ein übersehener Anker ist nicht vorhanden. Nach Regel 7 bleibt der Zeitraum 2010-07 (fall, Δ -1.096) ohne Anker stehen.

### B16 Telekom, 2013-05 bis 2013-05, rise, Δ +0.578 (eintrag)

Fenster 2013-02-01 bis 2013-05-31; 34 Meldungen, davon 34 im Fenster; Suchbegriff '"Deutsche Telekom"'; EQS ja.

**Anker:** keiner.

**Wahl:** Alle 34 Meldungen liegen im Ankerfenster vom 2013-02-01 bis 2013-05-31 (im_fenster = JA). Für den Anstieg im Mai 2013 bräuchte es ein entlastendes Ereignis für die Beschäftigten der Deutschen Telekom oder ein großes richtungsneutrales Ereignis wie eine Übernahme oder einen Vorstandswechsel bei der Telekom selbst. Keine Meldung erfüllt das. Nur drei Meldungen haben einen Arbeitgeberbezug. idx 10 ([Titel entfernt]) wirkt belastend und damit entgegen der Richtung rise. idx 8 und idx 13 sind Personalwechsel auf Finanzchef-Ebene in Tochtergesellschaften. idx 13 betrifft T-Mobile Austria, also nicht die deutschen Beschäftigten. idx 8 ist eine interne Umbesetzung, kein Wechsel im Vorstand der Deutschen Telekom AG und kein großes Ereignis. Die übrigen Meldungen scheiden nach Regel 7 aus. Das sind Produkt- und Tarifmeldungen (3, 20, 25, 26, 28, 30), Werbung und Marketing (4), Hauptversammlungs-Formalia (16), eine Kapitalmarktinformation ohne Inhalt (22), Directors' Dealings (29, 31, 33), eine Kursübersicht (34) und Meldungen über andere Unternehmen oder ohne Telekom-Bezug (1, 2, 5, 6, 7, 9, 11, 12, 14, 15, 17, 18, 19, 21, 24, 27, 32). Ergebnis: kein Anker. Der Zeitraum bleibt als Veränderung ohne Ereignis stehen.

**Erwartete Wirkung:** entfällt: Keine Meldung im Fenster hat einen Arbeitgeberbezug, der klar entlastend für die Beschäftigten der Deutschen Telekom ist. Auch ein großes richtungsneutrales Ereignis fehlt.

**Prüfer (kein_anker_bestaetigt):** Ich habe die Fall-Liste vollständig gelesen: 34 Meldungen, alle mit im_fenster = JA (Ankerfenster 2013-02-01 bis 2013-05-31). Jede Meldung habe ich auf Arbeitgeberbezug, Unternehmensbezug und Richtung geprüft. Kandidaten mit möglichem Arbeitgeberbezug: idx 8, idx 10 und idx 13. idx 8 (11.03., Magenta Newsroom): [Titel entfernt]. Das ist eine Personalie auf Finanzchef-Ebene einer Tochter. Am 02.04. folgt idx 13 ([Titel entfernt]). Deshalb betrifft idx 8 sehr wahrscheinlich ebenfalls die österreichische Tochter, also nicht die deutsche Gesellschaft. In keinem Fall ist das ein Wechsel im Vorstand der Deutschen Telekom AG oder ein großes richtungsneutrales Ereignis. idx 10 (27.03., Haufe): [Titel entfernt]. Der Arbeitgeberbezug ist echt, die erwartete Wirkung ist aber belastend und damit der Richtung rise entgegengesetzt. idx 29, 31 und 33 sind Directors' Dealings, idx 16 Hauptversammlungs-Formalia und idx 22 eine WpHG-Mitteilung ohne Inhalt. Diese Kategorien sind ausdrücklich ausgeschlossen. idx 3 (Tolino-Allianz mit Bertelsmann) ist eine Produkt- und Kooperationsmeldung ohne Wirkung auf die Belegschaft. idx 4, 20, 23, 25, 26, 28 und 30 sind Werbe-, Tarif-, Netz- und Produktmeldungen. Die übrigen Meldungen betreffen andere Firmen oder haben keinen Telekom-Bezug (1, 2, 5, 6, 7, 9, 11, 12, 14, 15, 17, 18, 19, 21, 24, 27, 32, 34). Eine Übernahme, eine Restrukturierung, ein Tarifabschluss, eine Arbeitszeitregel oder ein anderes entlastendes Ereignis bei der Deutschen Telekom kommt in der Liste nicht vor. Die Wahl "kein Anker" hält. Für den Anstieg im Mai 2013 (rise) bräuchte es ein entlastendes Ereignis für die Beschäftigten der Deutschen Telekom oder ein großes richtungsneutrales Ereignis bei der Telekom selbst, zum Beispiel eine Übernahme oder einen Vorstandswechsel. Keine Meldung im Fenster erfüllt das. idx 10 hat Arbeitgeberbezug, wirkt aber belastend: [Titel entfernt]. Das ist der Richtung entgegengesetzt, also kein Anker. idx 8 und idx 13 sind kleine Personalien auf Finanzchef-Ebene. Sie betreffen sehr wahrscheinlich beide T-Mobile Austria, nicht die deutsche Gesellschaft, und bringen keine erkennbare Wirkung auf die Belegschaft. Alle übrigen Meldungen sind ausgeschlossene Kategorien oder betreffen andere Unternehmen. Im Zweifel gilt: kein Anker. Der Zeitraum bleibt als Veränderung ohne Ereignis stehen.

### B17 Freenet, 2016-04 bis 2016-04, rise, Δ +1.044 (eintrag)

Fenster 2016-01-01 bis 2016-04-30; 13 Meldungen, davon 13 im Fenster; Suchbegriff 'Freenet'; EQS ja.

**Anker:** keiner.

**Wahl:** Ich habe alle 13 Meldungen gelesen. Alle liegen im Fenster vom 2016-01-01 bis 2016-04-30.

Ohne Arbeitgeberbezug sind:
- Die Meldungen 1, 2, 3, 5, 6, 7, 8 und 12. Das sind Promi- und Unterhaltungsartikel des Portals freenet Mail. Hier wird „freenet“ nur als Name des Portals verwendet.
- Meldung 4, eine Produkt- und Login-Anleitung von Giga.de.
- Meldung 13, ein Technik-Ratgeber, der nichts mit freenet zu tun hat.

Kein Anker sind nach Regel 7:
- Meldung 9, eine Stimmrechtsmitteilung.
- Meldung 11, ein Directors' Dealing.

Einzig möglicher Kandidat ist Meldung 10 ([Titel entfernt], 2016-03-18). Dem Titel nach kauft freenet eine Beteiligung an einem Schweizer Telekomunternehmen. Freenet übernimmt dabei weder das Unternehmen selbst noch einen eigenen Unternehmensteil, verkauft nichts und spaltet nichts ab. Eine Wirkung auf die Beschäftigten der deutschen freenet AG ist aus dem Titel nicht zu erkennen, etwa ein Stellenabbau, ein Umbau oder ein Wechsel im Vorstand. Erwartbar ist höchstens eine schwache, richtungsneutrale Wirkung. Es handelt sich eher um eine Finanzbeteiligung und damit um eine Kapitalmarktmeldung. Im Zweifel setze ich deshalb keinen Anker.

Ergebnis: kein Anker. Die Veränderung vom April 2016 bleibt als Stufe-A-Eintrag ohne Ereignis stehen.

**Erwartete Wirkung:** Richtungsneutral. Ohne Anker gibt es keine erwartete Wirkung, und der Stufe-A-Eintrag für 2016-04 (rise) bleibt unverändert.

**Prüfer (kein_anker_bestaetigt):** Ich habe die Fall-Liste vollständig gelesen (13 Meldungen). Alle 13 haben im_fenster = JA, das Ankerfenster reicht vom 2016-01-01 bis 2016-04-30. Danach habe ich jede Meldung einzeln auf einen übersehenen Anker geprüft:
- Meldungen 1, 2, 3, 5, 6, 7, 8 und 12 sind Promi- und Unterhaltungsartikel des Portals freenet Mail. Sie handeln nicht vom Unternehmen.
- Meldung 4 (Giga.de) ist eine Login- und Produktanleitung.
- Meldung 13 (Computerhilfen.de) ist ein Samsung-TV-Ratgeber ohne Bezug zu freenet.
- Meldung 9 (EQS) ist eine Stimmrechtsmitteilung von Capital Income Builder. Nach Regel 7 ist das ausdrücklich kein Anker.
- Meldung 11 (EQS) ist ein Directors' Dealing, ein Aktienkauf von Robert Weidinger. Auch das ist ausdrücklich kein Anker, und die Meldung zeigt keinen Wechsel in Vorstand oder Geschäftsführung.
- Meldung 10 ist der einzige ernsthafte Kandidat: [Titel entfernt] (2016-03-18, Vaterland online). Sie liegt im Fenster und betrifft die freenet AG. Ich habe geprüft, ob sie als „Übernahme“ gelten kann. Dem Titel nach erwirbt freenet einen Anteil an einem Schweizer Unternehmen, Sunrise wird also nicht übernommen. Freenet verkauft auch keine eigenen Teile und spaltet nichts ab. Für die Beschäftigten der deutschen freenet AG folgt daraus weder ein Umbau noch ein Stellenabbau, ein Vorstandswechsel oder eine Standortänderung. Die Meldung ist eher eine Finanz- bzw. Kapitalmarktmeldung.
Einen klar besseren Kandidaten gibt es nicht. Die Null-Wahl hält. Fast alle Meldungen verwenden „freenet“ nur als Namen des Mailportals oder sind Produkt- und Ratgebertexte. Das sind nach Regel 7 keine Anker.

Die beiden EQS-Meldungen fallen unter ausdrücklich ausgeschlossene Kategorien: Meldung 9 ist eine Stimmrechtsmitteilung, Meldung 11 ein Directors' Dealing.

Meldung 10, der Kauf des Sunrise-Anteils, ist eine Minderheits- bzw. Finanzbeteiligung an einem anderen Unternehmen. Freenet übernimmt dabei kein Unternehmen und gibt keine eigenen Unternehmensteile ab. Ein Arbeitgeberbezug zu den Beschäftigten der freenet AG ist aus dem Titel nicht erkennbar. Die erwartete Wirkung auf die Belegschaft ist höchstens schwach und richtungsneutral. Sie gehört nicht zu den großen richtungsneutralen Ereignissen wie einer Übernahme oder einem Vorstandswechsel und erklärt den Anstieg (rise) im April 2016 nicht.

Nach dem Grundsatz „im Zweifel kein Anker“ bleibt es deshalb beim Ergebnis „kein Anker“. Der Stufe-A-Eintrag für 2016-04 (rise) bleibt unverändert und ohne Ereignis stehen.

### B18 Freenet, 2020-02 bis 2020-02, rise, Δ +0.747 (eintrag)

Fenster 2019-11-01 bis 2020-02-29; 35 Meldungen, davon 35 im Fenster; Suchbegriff 'Freenet'; EQS ja.

**Anker:** keiner.

**Wahl:** Alle 35 Meldungen liegen im Ankerfenster (2019-11-01 bis 2020-02-29). Keine davon nennt ein Ereignis mit Arbeitgeberbezug für die Beschäftigten der freenet AG. Die Liste enthält Produkt- und Tarifmeldungen (Freenet Funk, Allnet-Flat, freenet.de WiFi, Klarmobil, Aldi Talk), Marketingmeldungen (Agenturwechsel von mobilcom-debitel, Marketing-Manager-Porträt) und Stimmrechtsmitteilungen (Flossbach von Storch, BlackRock). Dazu kommen Meldungen über andere Unternehmen, an denen freenet nur beteiligt ist: Personalwechsel und der UPC-Deal bei Sunrise sowie der Aufsichtsratsstreit bei Ceconomy/Media-Saturn. Diese betreffen die Beschäftigten jener Firmen, nicht die von freenet. Der Rest sind Treffer ohne Bezug wegen des Suchbegriffs (Filmdienst, TLGG, Promi-Meldungen, Ranking). [Titel entfernt] (Media Broadcast, eine freenet-Tochter) ist eine Produktmeldung. Ihre erwartete Wirkung wäre eher belastend, also gegen die Richtung rise. Damit ist sie kein Anker. Die Veränderung aus Stufe A (rise, Δ 0,747) bleibt ohne Ereignisanker stehen.

**Erwartete Wirkung:** richtungsneutral: Es gibt kein Ereignis mit Wirkung auf die Beschäftigten der freenet AG, daher entfällt eine erwartete Wirkung.

**Prüfer (kein_anker_bestaetigt):** Ich habe die Fall-Liste vollständig gelesen (35 Meldungen). Alle stehen auf im_fenster = JA (Ankerfenster 2019-11-01 bis 2020-02-29), das Fenster schließt also keine aus. Danach habe ich jede Meldung auf Unternehmen und Arbeitgeberbezug geprüft.
(1) Meldungen über freenet selbst oder seine Töchter und Marken: Allnet-Flat (1), Voice im Kundenservice (2), Freenet-Funk-Änderungen (6, 22, 25), Klarmobil (8), freenet.de WiFi (32), Agenturwechsel von mobilcom-debitel (26), Porträt des Marketing-Managers (7). Das sind Produkt-, Kunden- und Marketingmeldungen ohne Wirkung auf die Belegschaft. [Titel entfernt] (27, 28, 34) ist eine Produkteinstellung. Eine Folge für die Beschäftigten (Abbau, Umbau) nennt der Titel nicht. Wäre sie belastend, liefe sie gegen die Richtung rise. Die EQS-Meldungen 4 und 15 sind Stimmrechtsmitteilungen und damit ausgeschlossen.
(2) Andere Firmen: Personalwechsel, CEO-Wechsel und UPC-Deal bei Sunrise (3, 17, 18, 35) betreffen die Schweizer Beteiligung, nicht die Beschäftigten der freenet AG. Der Streit um Kellerhals und Ceconomy (21, 23, 24, 30, 31) betrifft ebenfalls eine Beteiligung. TLGG (10, 11) ist eine andere Firma.
(3) Treffer nur über den Suchbegriff: Filmdienst (9, 13, 14, 20), Promi-Meldung (19), Ranking (16), DVB-T2-Ratgeber (29), WLAN-Vergleich (33), [Titel entfernt] (12, Blick aktuell). Bei 12 lässt der Titel keinen freenet-Bezug erkennen, deshalb gilt im Zweifel: kein Anker.
Einen Vorstandswechsel, eine Übernahme oder eine Restrukturierung bei freenet selbst gibt es in der Liste nicht. Einen klar besseren, übersehenen Kandidaten habe ich nicht gefunden. Die Wahl "kein Anker" hält. Alle 35 Meldungen liegen im Fenster, aber keine hat einen Arbeitgeberbezug für die Beschäftigten der freenet AG.
Der stärkste Kandidat ist [Titel entfernt] (idx 27, 28, 34). Das bleibt eine Produktmeldung ohne genannte Folge für die Belegschaft. Ihre erwartete Wirkung wäre allenfalls belastend und passt damit nicht zur Richtung rise.
Die Vorstandswechsel (Sunrise) und Gremienkonflikte (Ceconomy) betreffen Beteiligungen, nicht freenet selbst. Der Rest sind Produkt-, Marketing-, Stimmrechts- oder Fremdtreffer.
Die Veränderung aus Stufe A (rise, Δ 0,747, 2020-02) bleibt ohne Ereignisanker stehen.

### B19 Freenet, 2021-09 bis 2021-09, fall, Δ -0.746 (eintrag)

Fenster 2021-06-01 bis 2021-09-30; 44 Meldungen, davon 44 im Fenster; Suchbegriff 'Freenet'; EQS ja.

**Anker:** keiner.

**Wahl:** Ich habe alle 44 Meldungen der Liste gelesen, alle liegen im Fenster vom 01.06. bis 30.09.2021. Keine davon zeigt laut Titel eine Wirkung auf die Beschäftigten der freenet AG. Die EQS-Meldungen sind Stimmrechtsmitteilungen, Kapitalmarktinformationen ohne Inhalt, Ankündigungen von Finanzberichten, HV-Formalia (Dividende) und eine Prognoseanhebung. Das sind nach Regel 7 alles ausgeschlossene Kategorien. Die Prognoseanhebung wäre außerdem eher entlastend, passt also nicht zur Richtung fall. Die meisten Google-News-Treffer sind Produkt- und Tarifmeldungen, Ratgeber zu Marken anderer Anbieter oder Boulevardinhalte aus dem freenet-Mailportal, also kein Ereignis des Unternehmens. Am nächsten kommt [Titel entfernt] Ende August 2021 (idx 31 bis 33). Horizont (idx 28) beschreibt sie aber als "großen Werbevertrag". Es ist also eine Werbe- und Testimonialvereinbarung mit Fantasietitel, kein Wechsel in Vorstand oder Geschäftsführung. Sie fällt unter Marketing und Sponsoring. Eine belastende Wirkung auf die Belegschaft ist aus dem Titel nicht ableitbar. Im Zweifel setze ich daher keinen Anker. Der Stufe-A-Eintrag für 2021-09 bleibt als Veränderung ohne Ereignis stehen.

**Erwartete Wirkung:** entfällt, weil kein Anker gewählt wurde.

**Prüfer (kein_anker_bestaetigt):** Ich habe die Fall-Liste fall_B19.txt vollständig gelesen, alle 44 Meldungen. Das Ankerfenster reicht vom 01.06. bis 30.09.2021 und alle 44 Meldungen haben im_fenster = JA. Das Fenster schließt also nichts aus, entscheidend ist der Arbeitgeberbezug.

EQS-Meldungen:
- idx 2, 6 und 23 sind Stimmrechtsmitteilungen beziehungsweise Meldungen zu eigenen Aktien.
- idx 7, 21, 24, 29 und 37 sind Kapitalmarktinformationen ohne Inhalt.
- idx 14 kündigt Finanzberichte an.
- idx 5 ist HV-Formalia (Dividende).
- idx 25 und 26 melden eine Prognoseanhebung für EBITDA und Free Cashflow. Das sind ausgeschlossene Kategorien, und die erwartete Wirkung wäre eher entlastend, also entgegen der Richtung fall.

Google-News-Meldungen:
- Produkt- und Tarifmeldungen: idx 1, 13, 15, 35, 39, 40 und 44 (freenet Energy, SIMon mobile, freenet Flex, Mobilcom Debitel).
- Ratgeber zu fremden Marken oder Anbietern: idx 8–10, 12, 16–20 und 22 (Blau, Lidl Connect, Telekom, Aldi Talk; bei klarmobil und Otelo ist der Unternehmensbezug unklar).
- Werbeanzeige: idx 27.
- Boulevardinhalte aus dem freenet-Mailportal: idx 4, 11 und 43. Sie betreffen nicht das Unternehmen als Arbeitgeber.
- idx 42 (SZ, Impostor-Syndrom) hat laut Titel keinen erkennbaren Freenet-Bezug.
- idx 3: [Titel entfernt]. Das ist ein Personenporträt und kein Wechsel im Gremium.

Stärkster Gegenkandidat ist die Bohlen-Gruppe (idx 28, 30–34, 36, 38, 41):
- idx 32 nennt einen "Management-Posten", idx 33 schreibt [Titel entfernt].
- idx 28 bezeichnet es aber ausdrücklich als "Großer Werbevertrag", und idx 31 spricht vom "Chief Entertainment Officer".
- idx 36 und 38 zeigen Werbekampagnen mit Bohlen.

Nach den Titeln ist das eine Testimonial- und Werbeverpflichtung, kein Wechsel in Vorstand oder Geschäftsführung. Damit fällt es unter Marketing und Sponsoring. Eine belastende Wirkung auf die Beschäftigten ist nicht ableitbar.

Es gibt keine Meldung zu Stellenabbau, Restrukturierung, Übernahme, Verkauf, Vorstandswechsel, Standort, Tarif, Betriebsrat, Gehalt, Homeoffice oder einer Krise. Die Wahl "kein Anker" hält. Alle 44 Meldungen liegen im Fenster, aber keine hat laut Titel einen Arbeitgeberbezug zur freenet AG.

Die EQS-Meldungen fallen ausnahmslos unter ausgeschlossene Kategorien: Stimmrechte, Kapitalmarktinformationen ohne Inhalt, Finanzberichtstermine, HV-Formalia und Prognoseanhebung. Die Prognoseanhebung wäre zudem eher entlastend und passt nicht zur Richtung fall.

Die Google-News-Treffer sind Produkt- und Tarifmeldungen, Ratgeber zu anderen Anbietern, Boulevard aus dem Mailportal oder Meldungen ohne Unternehmensbezug.

[Titel entfernt] Ende August 2021 ist laut Horizont ausdrücklich ein Werbevertrag. Der Titel "Chief Entertainment Officer" ist ein Showtitel und keine Organfunktion. Damit ist es Marketing und Sponsoring, kein Wechsel in der Geschäftsführung, und eine belastende Wirkung auf die Belegschaft ist nicht erkennbar. Auch der Titel "Management-Posten" in idx 32 reicht im Zweifel nicht als Anker, weil zwei andere Titel denselben Vorgang eindeutig als Werbevertrag beschreiben.

Ein übersehener passender Anker existiert nicht. Der Stufe-A-Eintrag für 2021-09 bleibt als Veränderung ohne Ereignis stehen.

### Z01 NTT DATA SE, 2024-03 bis 2024-03, fall, Δ -0.486 (zweifel)

Fenster 2023-12-01 bis 2024-03-31; 13 Meldungen, davon 13 im Fenster; Suchbegriff '"NTT DATA" OR "NTT Data Deutschland" OR itelligence'; EQS nein.

**Anker:** keiner.

**Wahl:** Alle 13 Meldungen liegen im Fenster (2023-12-01 bis 2024-03-31). Keine hat aber einen tragfähigen Arbeitgeberbezug. 1, 4 und 7 sind Produkt-, Partner- oder Award-Meldungen. 5 ist ein Ranking. 10, 11 und 13 betreffen das Sponsoring des Citylaufs Dresden. 3 (cbs) und 8 (Volkswagen) betreffen andere Firmen, 9 (Natuvion) ist ein Firmenporträt eines anderen SAP-Partners. 2 ist eine Arbeitgeberauszeichnung, die laut Regel ausgeschlossen ist und außerdem eher entlastend wirken würde. 6 (Joint Venture mit BMW) betrifft NTT DATA Rumänien, nicht die deutschen Beschäftigte. Nach dem Titel ist es eine Kunden- und Geschäftsmeldung. 12 ([Titel entfernt]) ist eine Investition in Infrastruktur ohne erkennbare Wirkung auf die Belegschaft und wäre allenfalls entlastend. Weil der Fall ein Zweifelsfall ist (|Δ| 0,486) und laut Regel nur mit Anker eingetragen wird, ist das Ergebnis "kein Anker".

**Erwartete Wirkung:** entfällt; keine der Meldungen lässt eine belastende Wirkung auf die Beschäftigten erwarten, die zum Rückgang im März 2024 passen würde.

**Prüfer (kein_anker_bestaetigt):** Ich habe die Fall-Liste vollständig gelesen: 13 Meldungen, alle mit im_fenster = JA (2024-01-08 bis 2024-03-30, Fenster 2023-12-01 bis 2024-03-31). Jede Meldung habe ich auf drei Punkte geprüft: Arbeitgeberbezug, Bezug zu NTT DATA SE und deutschen Beschäftigten, Richtung. Die stärksten Kandidaten gegen null waren 6, 12 und 2. Nr. 6 ist [Titel entfernt] (2024-03-05). Ein Joint Venture käme als Kategorie Übernahme, Fusion oder Abspaltung in Betracht. Laut Titel betrifft es aber die rumänische Gesellschaft und ist ein Kundengeschäft mit BMW. Eine Wirkung auf die in Deutschland bewertenden Beschäftigten ist nicht erkennbar und auch keine belastende Richtung. Nr. 12 ist [Titel entfernt], Herausgeber NTT, Inc. (2024-03-28). Das ist eine Infrastrukturinvestition, vermutlich aus dem Rechenzentrumsgeschäft des NTT-Konzerns. Sie hat keinen Arbeitgeberbezug und wäre allenfalls entlastend, also der Richtung fall entgegengesetzt. Nr. 2 (Global Top Employer) ist eine Arbeitgeberauszeichnung und damit ausdrücklich ausgeschlossen. Sie wäre außerdem entlastend. Die übrigen Meldungen scheiden ebenfalls aus. 1, 4 und 7 sind Produkt-, Partner- oder Award-Meldungen. 5 ist ein Ranking. 10, 11 und 13 sind Citylauf-Sponsoring. 3 (cbs), 8 (Volkswagen) und 9 (Natuvion) betreffen andere Firmen. Keine Meldung nennt Stellenabbau, Restrukturierung, einen Vorstandswechsel, einen Tarifkonflikt, Standortmaßnahmen oder eine Krise. Die Wahl "kein Anker" hält. Alle Meldungen liegen zwar im Fenster, aber keine hat einen Arbeitgeberbezug zu den Beschäftigten der NTT DATA SE in Deutschland mit einer belastenden Wirkung, die zum Rückgang im März 2024 passt. Das Joint Venture mit BMW (6) betrifft NTT DATA Rumänien und ist nach dem Titel eine Kunden- und Geschäftsmeldung. Der Rechenzentrumscampus (12) ist eine Investition ohne Bezug zur Belegschaft und wäre eher entlastend. Die Auszeichnung (2) ist laut Regel ausgeschlossen und wäre ebenfalls entlastend. Der Fall ist ein Zweifelsfall, es gilt "im Zweifel kein Anker", und es gibt keinen tragfähigen Kandidaten. Damit bleibt das Ergebnis "kein Anker".

### Z02 Compugroup Medical Deutschland, 2021-04 bis 2021-05, rise, Δ +0.466 (zweifel)

Fenster 2021-01-01 bis 2021-05-31; 29 Meldungen, davon 28 im Fenster; Suchbegriff '"CompuGroup Medical" OR CompuGroup'; EQS ja.

**Anker:** 2021-04-15, ZWP online (gnews): [Titel entfernt]  
https://news.google.com/rss/articles/CBMiwwFBVV95cUxNbHZwdDJuajg1YUJ0b3BpNkhaNHh2dllnVFhlSXNtOU9aVWhBbEI2LTR1NWdRUFR5Ry16RmlGeUROaElqOE42aElaanY1WW1YM2VsQ1cyaWdENWFEcHhkSUR1T3lKUnVUYzdRNzduNkh1UGg2eExJMGFlMlk4LWV1YjNDTDlZVGhfUWNabDNMYks4dTJOdWdyV1d1MGIyVEIwcG9IOVZnQkdjY2gzRXNtNy1tWWFSWHRxaUg0LVllSFpmN0U?oc=5

**Wahl:** Meldung idx 21 (ZWP online, 2021-04-15, im_fenster = JA) liegt im Zeitraum selbst (2021-04). Laut Titel: [Titel entfernt]. Das betrifft den deutschen Hauptstandort und damit die Arbeitsumgebung der Beschäftigten, die hier bewerten. Der Bezug fällt unter Büroregeln und Arbeitsplatz/Standort. Die erwartete Wirkung ist entlastend und passt damit zur Richtung rise (Δ +0,466). Gegenüber dem CEO-Wechsel (idx 3) bevorzuge ich diese Meldung aus zwei Gründen: Sie liegt zeitlich im Zeitraum und nicht am Rand des Fensters, und ihre Wirkung passt zur Richtung, während der Vorstandswechsel nur richtungsneutral ist. Einschränkung: Ich beurteile nur nach dem Titel. Ob der Neubau im April 2021 schon bezogen war oder nur angekündigt wurde, geht daraus nicht hervor. Die Stufe-A-Monate bleiben unverändert.

**Erwartete Wirkung:** entlastend: eine Investition in moderne Arbeitsplätze und flexible Arbeitsformen am Hauptsitz lässt eher eine bessere Bewertung durch die Beschäftigten erwarten.

**Prüfer (bestaetigt):** Ich habe die Fall-Liste fall_Z02.txt vollständig gelesen (29 Meldungen, Ankerfenster 2021-01-01 bis 2021-05-31).
Fenster: Idx 21 ist am 2021-04-15 datiert, hat im_fenster = JA und liegt im Zeitraum selbst (2021-04).
Unternehmen: CGM ist das Kürzel von CompuGroup Medical. Koblenz ist der deutsche Hauptsitz. Den Namen gibt es nicht doppelt, die Meldung betrifft also die deutschen Beschäftigten, die hier bewerten. Herausgeber ist ZWP online, eine Fachpresse. Das spricht für eine PR-nahe Meldung, ändert aber nichts am Inhalt.
Arbeitgeberbezug: Ein Neubau ausdrücklich „für New Work“ betrifft die Arbeitsumgebung und die Arbeitsformen am Standort. Das fällt unter Homeoffice- oder Büroregeln bzw. Standort. Ich habe geprüft, ob es nur eine Immobilien- oder Imagemeldung ist. Der Titel nennt aber ausdrücklich den Zweck für die Arbeitsweise der Beschäftigten. Es ist keine Produkt-, Zahlen-, Kurs- oder Formalmeldung.
Richtung: Die erwartete Wirkung ist entlastend (bessere Arbeitsplätze, flexiblere Arbeitsformen). Das passt zu rise (Δ +0,466).
Bessere Kandidaten: Idx 3 ([Titel entfernt], 2021-01-22, JA) ist ein gültiger Anker, weil ein Vorstandswechsel richtungsneutral groß ist. Die Regel stellt ihn aber gleichrangig neben richtungspassende Ereignisse. Er liegt am Fensteranfang, knapp 2,5 Monate vor period_from. Er ist damit nicht klar besser, ein Ersetzen ist nicht begründet.
Übrige Meldungen:
- Idx 29: Übernahme VISUS, im_fenster = nein.
- Idx 26: HENSOLDT, eine andere Firma.
- Idx 4, 25 und 28: Zahlen und Prognosen.
- Idx 20 und 2: Kunden- und Produktmeldungen.
- Alle übrigen: Directors' Dealings, Stimmrechtsmitteilungen, Aktienrückkauf, Kapitalmarktinformationen ohne Inhalt, HV-Formalia.
Keine dieser Meldungen ist ein Anker. Die Wahl hält.
- Fenster und Unternehmen: Idx 21 liegt im Fenster und im Zeitraum. Sie betrifft eindeutig CompuGroup Medical am deutschen Hauptsitz Koblenz.
- Arbeitgeberbezug: Er ist gegeben, denn ein Neubau für „New Work“ verändert Arbeitsplatz und Arbeitsformen der Beschäftigten (Büroregeln/Standort).
- Erwartete Wirkung: entlastend, sie passt zur Richtung rise.
- Alternative idx 3: Der CEO-Wechsel ist ein gültiger, richtungsneutraler Anker. Er ist aber nicht klar besser, weil die Regel richtungspassende und richtungsneutral große Ereignisse gleich behandelt und idx 21 zeitlich näher am Zeitraum liegt.
- Zweifelsfall: Wegen des Zweifelsfalls habe ich streng geprüft. Selbst wenn man idx 21 verwürfe, bliebe mit idx 3 ein gültiger Anker. Das Ergebnis „Eintrag“ hängt also nicht an einer wackligen Einzelmeldung.
- Einschränkungen: Ich beurteile nur nach dem Titel. Ob der Bau im April 2021 schon bezogen oder nur angekündigt war, bleibt offen. Die Stufe-A-Monate bleiben unverändert.


## 6 Stufe A je Reihe (vollständig)



## Thyssenkrupp (ID 3, 32 bewertete Monate)

**Ergebnis:** 0 Einträge, 0 Zweifelsfälle für Stufe B.


**Auswahl (Annotator):** Thyssenkrupp, Mitarbeitende, Gesamtbewertung (32 bewertete Monate): Die Reihe schwankt stark von Monat zu Monat, die Ausschläge liegen oft zwischen 0,5 und 1,3. Fast alle großen Monatsdifferenzen sind Einzelmonatsausreißer, nach denen das alte Niveau gleich wieder erreicht wird, etwa 2023-04, 2024-01, 2024-02, 2024-09, 2024-10, 2024-12, 2025-07 und 2026-02. Sie scheitern an Regel 4 und an den Setzungen (a) und (b). Der Scan fand keinen regelkonformen Zeitraum und nur einen Zweifelsfall: 2023-04..2023-07, Δ +0,3036. Diese Variante ist nicht definitionsgemäß abgegrenzt. Ihr period_to 2023-07 (3,283) liegt auf dem Vorniveau (3,249) und nicht auf dem neuen Niveau (Folgemittel 3,764). Im Zeitraum wechseln sich hohe und niedrige Monate ab (4,09/2,96/3,88/3,28), und das Vorniveau aus nur drei Monaten fällt selbst steil (4,10/3,21/2,43). Die definitionsgemäße Abgrenzung 2023-04..2023-06 scheitert an Setzung (b): Der erste Folgemonat liegt nur 0,0343 über dem Vorniveau, verlangt sind 0,25. Diese Stelle bekommt daher weder einen Eintrag noch einen Zweifelsfall. Den Anstieg 2023-07..2023-10 und den allmählichen Rückgang von etwa 3,6 (2023/2024) auf etwa 3,2 (2025) habe ich auf den Trendfall nach Regel 2 geprüft. Bei 2023-07..2023-10 meldet der Rechner einen Vortrend von +0,39, und keine Variante hält das neue Niveau. Der Rückgang verläuft über mehr als sechs Monate. Den Anfang der Reihe (2023-02/03) kann ich nicht prüfen, weil weniger als drei Vorniveau-Monate vorliegen. Das Ende (2026-03) kann ich nicht prüfen, weil kein Folgemonat vorliegt (Setzung (c)). Die leere Auswahl habe ich mit satz geprüft: anzahl 0, ok. Ergebnis für Stufe A: kein Referenzzeitraum. Das ist ein gültiges Ergebnis.

**Verworfene Kandidaten (35):**

- 2023-02..2023-03 (fall): Setzung Vorniveau mindestens drei bewertete Monate (S_vorniveau_min3); nicht prüfbar. Vorniveau nur 1 bewerteter Monat (2023-01 = 4,10, n=17); Zeitraum 3,213 (n=15), 2,433 (n=9)
- 2023-03..2023-03 (fall): Setzung Vorniveau mindestens drei bewertete Monate; nicht prüfbar. Vorniveau nur 2 bewertete Monate (2023-01, 2023-02); 2023-03 = 2,433 (n=9)
- 2023-04..2023-04 (rise): Regel 4 (einzelner Monatssprung mit Rückkehr) / Setzung (a) und (b). Δ +0,8373; Vorniveau 3,249 (2023-01 bis 2023-03); Folgemittel-Abstand 0,1257 < verlangt 0,4187; erster Folgemonat 2023-05 = 2,962 (Abstand -0,2867, unter Vorniveau)
- 2023-04..2023-07 (rise), Scan-Zweifelsfall: Abgrenzung nach der Definition: nicht definitionsgemäß, daher auch kein Zweifelsfall. Δ +0,3036 (Zweifelsbereich), Scan nennt die Variante sonst regelkonform (Folgemittel-Abstand 0,515, erster Folgemonat 2023-08 Abstand 0,2513). Aber period_to 2023-07 = 3,283 (n=6) liegt auf dem Vorniveau 3,249 und nicht auf dem neuen Niveau (Folgemittel 3,764); im Zeitraum liegt 2023-05 = 2,962 unter dem Vorniveau (Hin-und-her-Schwankung 4,09/2,96/3,88/3,28); das Vorniveau selbst (4,10/3,21/2,43) ist kein stabiles Niveau. Die Ausdehnung bis 2023-07 wäre eine Verlängerung nur, damit (b) besteht.
- 2023-04..2023-06 (rise), definitionsgemäße Abgrenzung der Stelle 2023-04: Regel 4 Zweifelsbereich und Setzung (b) gescheitert; Stelle ohne Eintrag und ohne Zweifelsfall. Δ +0,3933; Vorniveau 3,249; Folgemittel-Abstand 0,2457 >= 0,1967 (a ok); erster Folgemonat 2023-07 = 3,283, Abstand 0,0343 < 0,25 (b gescheitert)
- 2023-04..2023-05 (rise): Regel 4. Δ +0,2753 < 0,30
- 2023-05..2023-06: Regel 4, Setzung (a)/(b), Stützung dünner Monate. Δ -0,0380; 2023-06 (n=9) ohne Stützung
- 2023-06..2023-06 (rise): Setzung (a)/(b), Stützung dünner Monate. Δ +0,5192; Folgemittel-Abstand 0,1355 < 0,2596; erster Folgemonat 2023-07 Abstand -0,0758; 2023-06 (n=9) ohne Stützung
- 2023-06..2023-10 (rise): Regel 4 Zweifelsbereich, Setzung (a)/(b) gescheitert. Δ +0,3316; Folgemittel 3,351, Abstand -0,0078 < 0,1658; erster Folgemonat 2023-11 Abstand 0,2472 < 0,25
- 2023-07..2023-10 (rise): Regel 4, Setzung (a)/(b); Trendhinweis Regel 2. Δ +0,1982; Folgemittel-Abstand -0,0943; erster Folgemonat 2023-11 Abstand 0,1607; Vortrend +0,39 (Anstieg läuft schon in den Vormonaten)
- 2023-08..2023-10 (rise): Regel 4 Zweifelsbereich, Setzung (a) gescheitert. Δ +0,4545; Vorniveau 3,309; Folgemittel 3,351, Abstand 0,0418 < 0,2273; erster Folgemonat 2023-11 Abstand 0,2968 (b ok)
- 2023-09..2023-10 (rise): Setzung (a)/(b); Trendhinweis Regel 2. Δ +0,5385; Folgemittel-Abstand -0,006 < 0,2693; erster Folgemonat 2023-11 Abstand 0,249 < 0,25; Vortrend +0,39
- 2023-10..2023-10 (rise): Setzung (a)/(b) (Einzelmonat, kein Bleiben). Δ +0,5228; Folgemittel-Abstand -0,2172 < 0,2614; erster Folgemonat 2023-11 = 3,606, Abstand 0,0378
- 2024-01..2024-01 (fall): Regel 4 (Einzelmonatsausreißer mit Rückkehr), Setzung (a)/(b), Stützung dünner Monate. Δ -1,2593; Vorniveau 3,676; Folgemittel 3,681, Abstand -0,0043 < 0,6297; erster Folgemonat 2024-02 = 4,030, Abstand -0,3537; 2024-01 (n=6) ohne Stützung; 2023-12 grau (n=3)
- 2024-01..2024-02 (fall): Regel 4 Zweifelsbereich, Setzung (a)/(b), Stützung gescheitert. Δ -0,4528; Folgemittel-Abstand 0,1057 < 0,2264; erster Folgemonat 2024-03 Abstand 0,0543; 2024-01 (n=6) ohne Stützung
- 2024-02..2024-02 (rise): Setzung (a)/(b). Δ +0,5972; Vorniveau 3,433; Folgemittel-Abstand 0,1378 < 0,2986; erster Folgemonat 2024-03 = 3,622, Abstand 0,1892 < 0,25
- 2024-02..2024-03 (rise): Regel 4 Zweifelsbereich, Setzung (a)/(b) gescheitert. Δ +0,3932; Folgemittel-Abstand 0,0115 < 0,1966; erster Folgemonat 2024-04 Abstand -0,0428
- 2024-04..2024-05: Regel 4, Stützung dünner Monate. Δ -0,0327; 2024-05 (n=5) ohne Stützung
- 2024-07..2024-09 (fall): Regel 4 Zweifelsbereich, Setzung (a)/(b) gescheitert. Δ -0,3572; Folgemittel-Abstand 0,0268 < 0,1786; erster Folgemonat 2024-10 = 3,964, Abstand -0,5032 (Rückkehr über Vorniveau)
- 2024-09..2024-09 (fall): Regel 4 (Einzelmonatssprung mit Rückkehr), Setzung (a)/(b). Δ -0,7935; Vorniveau 3,550; Folgemittel-Abstand 0,1155 < 0,3968; erster Folgemonat 2024-10 Abstand -0,4145; Vortrend -0,26
- 2024-09..2024-10: Regel 4. Δ -0,1895
- 2024-10..2024-10 (rise): Setzung (a)/(b) (Einzelmonat mit Rückkehr). Δ +0,6268; Folgemittel-Abstand -0,1688 < 0,3134; erster Folgemonat 2024-12 = 2,671, Abstand -0,6662; 2024-11 grau (n=3)
- 2024-12..2024-12 (fall): Setzung (a)/(b), Stützung dünner Monate. Δ -0,7232; Folgemittel-Abstand -0,0542 < 0,3616; erster Folgemonat 2025-01 = 3,667, Abstand -0,2728; 2024-12 (n=7) ohne Stützung
- 2024-12..2025-02 (fall): Regel 4, Setzung (a)/(b), Stützung. Δ -0,2258
- 2025-01..2025-01 (rise): Regel 4 Zweifelsbereich, Setzung (a)/(b) gescheitert. Δ +0,3927; Folgemittel-Abstand -0,0317 < 0,1963; erster Folgemonat 2025-02 Abstand -0,1073
- 2025-05..2025-07 (fall): Regel 4 Zweifelsbereich, Setzung (a)/(b) und Stützung gescheitert. Δ -0,3828; Vorniveau 3,289; 2025-06 nicht bewertet (n=3); Folgemittel-Abstand -0,16 < 0,1914; erster Folgemonat 2025-08 = 3,094, Abstand 0,1953 < 0,25; 2025-07 (n=8) ohne Stützung
- 2025-07..2025-07 (fall): Setzung (a)/(b), Stützung dünner Monate. Δ -0,5753; Folgemittel-Abstand -0,111 < 0,2877; erster Folgemonat 2025-08 Abstand 0,2443 < 0,25; 2025-07 (n=8) ohne Stützung
- 2025-05..2025-08 / 2025-07..2025-08 (fall): Regel 4 Zweifelsbereich, Setzung (a)/(b), Stützung gescheitert. Δ -0,3203 bzw. -0,4098; erster Folgemonat 2025-09 = 3,690, Abstand -0,4007 bzw. -0,3517 (Rückkehr über Vorniveau)
- 2025-08..2025-09 (rise): Regel 4. Δ +0,2538
- 2025-09..2025-09 (rise): Regel 4 Zweifelsbereich, Setzung (a) gescheitert. Δ +0,4813; Vorniveau 3,209; Folgemittel 3,242, Abstand 0,0337 < 0,2407; erster Folgemonat 2025-11 Abstand 0,3553 (b ok); Vortrend -0,48 (Gegenrichtung)
- 2025-09..2025-11 (rise): Regel 4 Zweifelsbereich, Setzung (a)/(b) gescheitert. Δ +0,4183; 2025-10 nicht bewertet (n=2); Folgemittel-Abstand 0,1357 < 0,2092; erster Folgemonat 2026-01 = 3,263, Abstand 0,0543
- 2026-02..2026-02 (fall): Regel 4 Zweifelsbereich, Setzung (a)/(b) gescheitert. Δ -0,3373; erster und einziger Folgemonat 2026-03 = 3,870, Abstand -0,6327 (Rückkehr nach oben)
- 2026-03..2026-03 (rise): Setzung (c): kein bewerteter Folgemonat, nicht prüfbar. Δ +0,6577; Vorniveau 3,212; 2026-03 ist der letzte bewertete Monat der Reihe
- 2026-02..2026-03: Regel 4, Setzung (c). Δ +0,1477; kein Folgemonat
- Abwärtsbewegung 2023/2024 (um 3,6) bis 2025 (um 3,2): Regel 2: allmählicher Rückgang über mehr als sechs Monate = Trend, kein Sprung. Vor6-Mittel sinkt von 3,57-3,68 (2023-10 bis 2024-02) auf 3,14-3,29 (2025-02 bis 2025-08), ohne einzelne Stelle, die die Regeln besteht

**Widerlegungsversuche (Prüfer):** Der Annotator hat keine Einträge und keine Zweifelsfälle gesetzt. Deshalb habe ich versucht, die leere Auswahl zu widerlegen, also eine regelkonforme Stelle oder einen Zweifelsfall zu finden, der fehlt.

(1) Einziger Scan-Kandidat 2023-04..2023-07, rise. pruefe ergibt "zweifelsfall_0_3_bis_0_49": Δ +0,3036, Vorniveau 3,249 (2023-01 bis 2023-03, n=9-17), Folgemittel 3,7637, Abstand 0,515, erster Folgemonat 2023-08 mit Abstand 0,2513, Stützung ok. Die Zahlen des Annotators stimmen. Den Ausschluss als nicht definitionsgemäß halte ich für tragfähig:
- period_to 2023-07 = 3,283 liegt praktisch auf dem Vorniveau 3,249 und nicht auf dem neuen Niveau (Folgemittel 3,76). Es ist also nicht der erste Monat auf dem neuen Niveau.
- Im Zeitraum wechseln sich hohe und niedrige Monate ab: 4,09, 2,96, 3,88, 3,28. 2023-05 liegt sogar unter dem Vorniveau.
- Das Vorniveau ist selbst ein steiler Abfall (4,10 / 3,21 / 2,43). Das Δ von +0,30 entsteht vor allem durch den Tiefpunkt 2023-03.

Die definitionsgemäßen Abgrenzungen scheitern beide an S_folgeniveau:
- 2023-04..2023-04: Δ +0,8373; Folgemittel-Abstand 0,1257 < 0,4187; erster Folgemonat 2023-05 mit -0,2867.
- 2023-04..2023-06: Δ +0,3933; erster Folgemonat 2023-07 mit Abstand 0,0343 < 0,25.

Die Ausdehnung bis 2023-07 wäre eine Verlängerung nur, damit (b) besteht. Das verbietet die Abgrenzungsvorgabe. Eine weitere Verlängerung auf 2023-04..2023-08 ergibt Δ +0,2931 < 0,30, also R4 verworfen. Kein Zweifelsfall, Ergebnis des Annotators bleibt.

(2) Stichproben gegen die verworfen-Liste, alle mit pruefe nachgerechnet und mit den Zahlen des Annotators identisch:
- 2023-02..2023-03: S_vorniveau_min3, Wert 1.
- 2023-08..2023-10: Δ +0,4545; (a) Abstand 0,0418 < 0,2273.
- 2024-01: Δ -1,2593; (a) -0,0043 < 0,6297; (b) -0,3537; 2024-01 (n=6) ohne Stützung.
- 2024-07..2024-09: Δ -0,3572; erster Folgemonat -0,5032.
- 2024-09: Δ -0,7935; (a) 0,1155 < 0,3968; (b) -0,4145; Vortrend -0,26.
- 2025-07..2025-08: Δ -0,4098; (b) -0,3517.
- 2025-09: Δ +0,4813; (a) 0,0337 < 0,2407.
- 2026-03: Δ +0,6577; kein Folgemonat, Setzung (c).

Alle großen Monatsdifferenzen sind Einmonatsausreißer mit Rückkehr. Der Rückgang von etwa 3,6 auf etwa 3,2 über 2024/2025 verläuft über mehr als sechs Monate und ist damit ein Trend nach Regel 2.

(3) Regel 5: satz mit leerer Auswahl ergibt anzahl 0, anzahl_ok true, ok true. Notes gibt es mangels Einträgen keine.

**Vollständigkeit (Prüfer):** scan ergibt 0 regelkonforme Zeiträume in 0 Gruppen und 1 Zweifelsfall in 1 Gruppe (2023-04..2023-07, rise, Δ +0,304).

Diese einzige Gruppe ist begründet verworfen. Die Variante ist nicht definitionsgemäß: period_to 2023-07 liegt auf dem Vorniveau und nicht auf dem neuen Niveau. Die definitionsgemäßen Abgrenzungen 2023-04..2023-04 und 2023-04..2023-06 scheitern an Setzung (a) bzw. (b). Damit gibt es für diese Stelle weder einen Eintrag noch einen Zweifelsfall.

Der frühere Lauf mit weicherer Setzung hatte keine Kandidaten ([]), daher gibt es dort nichts zusätzlich zu prüfen.

Die übrigen sichtbaren Sprungstellen hat der Annotator vollständig mit Regel und Zahlen verworfen; die Stichproben aus (2) habe ich mit pruefe nachgerechnet und bestätigt:
- 2023-02/03: Vorniveau zu kurz.
- 2023-04, 2024-01, 2024-02, 2024-09, 2024-10, 2024-12, 2025-07, 2026-02: Einmonatsausreißer mit Rückkehr.
- 2023-08..10 und 2025-09: Setzung (a).
- 2026-03: kein Folgemonat.
- Der allmähliche Rückgang 2024/2025 ist ein Trend nach Regel 2.

Es fehlt keine regelkonforme, definitionsgemäße Stelle. Endergebnis für Stufe A: kein Referenzzeitraum und kein Zweifelsfall. Die leere Auswahl ist mit satz geprüft (ok).


## Open Grid Europe (ID 4, 22 bewertete Monate)

**Ergebnis:** 0 Einträge, 0 Zweifelsfälle für Stufe B.


**Auswahl (Annotator):** Open Grid Europe, Mitarbeitende, Gesamtbewertung: Die Reihe hat 22 bewertete Monate. Fast alle anderen Monate haben weniger als 5 Bewertungen und zählen deshalb nicht; Regel 3 schließt damit die meisten mehrmonatigen Zeiträume aus. Der Scan findet keine regelkonforme Variante und genau einen Zweifelsfall (2024-08..2024-10, Δ +0,391). Diese Stelle ist der einzige sichtbare Niveauwechsel: von etwa 4,0-4,3 (2022-09 bis 2023-12) auf etwa 4,6 (2024-04 bis 2024-10). Der erste abweichende bewertete Monat ist 2024-04 (4,667, n=6, Δ +0,4777), und er liegt zugleich schon auf dem neuen Niveau. Definitionsgemäß ist der Zeitraum daher 2024-04..2024-04. Diese Abgrenzung besteht die Regeln nicht: Δ liegt im Zweifelsband, und der dünne Monat mit n=6 ist nicht gestützt, denn 2024-08 liegt nur +0,39 und damit unter 0,5 über dem Vorniveau. Die Verlängerung bis 2024-08 verletzt Regel 3, weil drei Monate dazwischen nicht bewertet sind. Die Scan-Variante 2024-08..2024-10 verschiebt period_from hinter den eigentlichen Sprung. 2024-04 steht dabei bereits im Vorniveau, und der Rechner meldet einen Vortrend von +0,37 in Sprungrichtung. Nach der Abgrenzungsregel gibt es für diese Stelle deshalb keinen Eintrag und auch keinen Zweifelsfall. Alle übrigen Ausschläge sind entweder einzelne Monate, nach denen das alte Niveau zurückkehrt (2021-04, 2023-08/09, 2025-02, 2025-12, 2025-09..11), oder sie liegen unter 0,30. 2026-02 (Δ -0,65) ist nicht prüfbar, weil danach kein bewerteter Monat folgt. Bei 2018-08 und 2019-01..02 ist das Vorniveau zu kurz. Ergebnis: 0 Einträge und 0 Zweifelsfälle. Der Rechner bestätigt mit satz für die leere Auswahl ok (anzahl 0).

**Verworfene Kandidaten (15):**

- 2024-08..2024-10 (einzige Scan-Gruppe, Zweifelsfall laut Scan): Abgrenzung nach Definition; Regel 2 (Vortrend). Δ +0,391 (Vor 4,1905 aus 2022-09 bis 2024-04, Niveau 4,5815, n=5, 6; 2024-09 nicht bewertet n=1); Folgemittel 4,581, erster Folgemonat 2024-12 = 4,82; Hinweis Rechner: Vorniveau bewegt sich bereits in Sprungrichtung (+0,37). 2024-08 ist nicht der erste abweichende bewertete Monat: 2024-04 (4,667, n=6) liegt schon +0,48 über dem Vorniveau 4,19 und steht im Vorniveau dieser Variante; gegenüber 2024-04 weicht 2024-08 (4,58) nicht ab. Die Variante verschiebt period_from hinter den eigentlichen Sprung und ist deshalb nicht die definitionsgemäße Abgrenzung; kein Eintrag, auch kein Zweifelsfall.
- 2024-04..2024-04 (definitionsgemäße Abgrenzung der Stelle 2023-12 → 2024-04): Regel 4 (Zweifelsband) und Setzung Stützung dünner Monate. Vorniveau 4,1893 (2021-04 bis 2023-12, n=5-9), Niveau 4,667 (n=6), Δ +0,4777 (0,30-0,49); Folgemittel 4,661 (a erfüllt), erster Folgemonat 2024-08 = 4,58 mit Abstand +0,3907 (b erfüllt); 2024-06 hat aber n=6 und keine Stützung: 2024-08 liegt nur +0,39 über dem Vorniveau, verlangt sind >= 0,5. Damit nicht 'sonst regelkonform'; laut Protokoll kein Eintrag und kein Zweifelsfall für diese Stelle.
- 2024-04..2024-08: Regel 3 (innen mehr als ein nicht bewerteter Monat), Regel 4, Stützung. Innen nicht bewertet: 2024-05 (n=2), 2024-06 (n=0), 2024-07 (n=3); Δ +0,4342; 2024-04 (n=6) und 2024-08 (n=5) ohne Stützung
- 2024-08..2024-12: Regel 3, Regel 4, Setzung a/b (Folgeniveau), Stützung. Innen nicht bewertet 2024-09 (n=1), 2024-11 (n=3); Δ +0,4705; Folgemittel-Abstand 0,2238 < verlangt 0,2353; erster Folgemonat 2025-02 = 4,243 (Abstand +0,0525 < 0,25)
- 2024-10..2024-12: Regel 4, Setzung a/b, Stützung. Vor 4,2872, Niveau 4,7015, Δ +0,4143; Folgemittel-Abstand 0,1272 < 0,2072; erster Folgemonat 2025-02 = 4,243 (Abstand -0,0442), Rückkehr; 2024-12 (n=5) ohne Stützung
- 2026-02..2026-02: Setzung c (kein bewerteter Folgemonat) und Stützung. Vor 4,5472 (2024-12 bis 2025-12, n=5-7), Niveau 3,9 (n=5), Δ -0,6472; 2026-03 nur n=3 (grau), Bleiben nicht prüfbar; 2026-02 (n=5) ohne Stützung
- 2022-09..2022-09: Regel 4 (Zweifelsband) und Stützung. Vor 4,362 (2018-08 bis 2021-04, n=5-22), Niveau 4,0 (n=5), Δ -0,362; Folgeniveau erfüllt (Folgemittel 4,1157, erster Folgemonat 2023-08 = 4,04); kein Monat >= 0,5 unter dem Vorniveau zur Stützung des n=5-Monats; nicht sonst regelkonform, kein Zweifelsfall
- 2023-08..2023-09: Regel 4, Setzung a/b, Stützung. Vor 4,3753, Niveau 4,009 (n=5, 9), Δ -0,3663; Folgemittel 4,375 (Abstand 0,0003 < 0,1832), erster Folgemonat 2023-11 = 4,329, Rückkehr
- 2021-04..2021-04: Regel 4, Setzung a/b, Stützung; einzelner Ausreißer. Vor 4,277, Niveau 4,66 (n=5), Δ +0,383; Folgemittel 4,006 (Abstand -0,271), erster Folgemonat 2022-09 = 4,0, Rückkehr unter das Vorniveau
- 2025-02..2025-02: Regel 4, Setzung a/b, Stützung. Vor 4,518, Niveau 4,243 (n=7), Δ -0,275; erster Folgemonat 2025-08 = 4,68 (Abstand -0,162), Rückkehr
- 2025-12..2025-12: Regel 4, Setzung a/b, Stützung. Vor 4,5077, Niveau 4,82 (n=5), Δ +0,3123; erster Folgemonat 2026-02 = 3,9 (Abstand -0,6077), Rückkehr
- 2025-09..2025-11: Regel 4, Setzung b, Stützung. Vor 4,5955, Δ -0,2355; erster Folgemonat 2025-12 = 4,82 (Abstand -0,2245), Rückkehr
- 2019-02..2019-07: Regel 3, Regel 4, Setzung a. Innen nicht bewertet 2019-03 (n=3), 2019-04 (n=2), 2019-06 (n=3); Vor 4,1157 (nur 3 Monate), Δ +0,3227; Folgemittel-Abstand 0,1177 < 0,1613
- 2018-08..2018-08: Setzung Vorniveau mindestens drei bewertete Monate. Vorniveau nur 1 bewerteter Monat (2017-01 = 4,15, n=16); Niveau 3,92 (n=5)
- 2019-01..2019-02: Setzung Vorniveau mindestens drei bewertete Monate. Vorniveau nur 2 bewertete Monate (2017-01, 2018-08); Tabelle Diff +0,24/+0,21 ohnehin unter 0,30

**Widerlegungsversuche (Prüfer):** Der Annotator hat keine Einträge und keine Zweifelsfälle. Ich habe deshalb vor allem versucht, sein Verwerfen der einzigen Scan-Gruppe zu widerlegen, und dazu seine Gegenkandidaten nachgerechnet.

(1) 2024-08..2024-10. Laut scan ein Zweifelsfall: Δ +0,391 bei Vorniveau 4,1905; Folgemittel 4,581 (a erfüllt); erster Folgemonat 2024-12 = 4,82 (b erfüllt); Stützung über 2024-12 ok. Es ist der einzige Kandidat, der ein Zweifelsfall sein könnte. Gegenprüfung mit pruefe: Im Vorniveau dieser Variante steht 2024-04 (4,667, n=6). Dieser Monat liegt bereits +0,48 über dem alten Niveau, also über 2022-09 bis 2023-12 mit etwa 4,0 bis 4,3. Danach bleibt die Reihe oben: 2024-08 4,58, 2024-10 4,583, 2024-12 4,82. Der Rechner meldet außerdem einen Vortrend von +0,37 in Sprungrichtung. Der erste abweichende bewertete Monat ist damit 2024-04, und er ist zugleich der erste Monat auf dem neuen Niveau. Definitionsgemäß ergibt das 2024-04..2024-04. pruefe dafür: Δ +0,4777 (Zweifelsband); Folgeniveau a/b erfüllt (Folgemittel-Abstand 0,4717, erster Folgemonat 2024-08 mit +0,3907); Stützung jedoch nicht erfüllt. 2024-04 hat n=6 und keinen gestützten Partner, denn 2024-08 liegt nur +0,39 über dem Vorniveau, verlangt sind 0,5. Ergebnis: verworfen und nicht "sonst regelkonform". Damit bleibt diese Stelle auch kein Zweifelsfall. Würde man period_from auf 2024-08 verschieben, hinge die Stützung an 2024-12. Das wäre das verbotene Kürzen, nur damit eine Regel besteht. Die Verlängerungen bestehen ebenfalls nicht: 2024-04..2024-08 und 2024-04..2024-10 scheitern an R3 innen (2024-05/06/07 nicht bewertet), 2024-04..2024-10 zusätzlich an R2 (7 Monate). 2024-04..2024-12 scheitert an R2, R3, Folgeniveau und Stützung. Der Widerlegungsversuch scheitert, das Verwerfen des Annotators ist regelkonform.

(2) Die Nachbarvarianten habe ich nachgerechnet. 2024-08..2024-08 ist verworfen (R4 Zweifel, Stützung). 2024-08..2024-12 ist verworfen (R3 innen 2024-09 und 2024-11, Folgeniveau mit Abstand 0,2238 < 0,2353, Stützung 2024-12). 2024-10..2024-12 ist verworfen (Folgeniveau, Rückkehr 2025-02 mit 4,243, Stützung). 2024-12..2024-12 ist verworfen (Δ +0,44, Folgeniveau, Stützung).

(3) 2026-02..2026-02: Δ -0,6472 erfüllt R4. Es gibt aber keinen bewerteten Folgemonat (Setzung c), und der n=5-Monat ist ohne Stützung. Verworfen, bestätigt. 2025-12..2026-02 ist ebenfalls verworfen.

(4) Die übrigen Kandidaten des Annotators habe ich mit pruefe geprüft, alle sind verworfen. 2022-09 (Δ -0,362, Stützung), 2023-08..2023-09 (Δ -0,3663, Folgemittel-Abstand 0,0003, Stützung) und 2023-09 (Rückkehr 2023-11). 2021-04 (Δ +0,383, Rückkehr 2022-09 mit 4,0), 2025-02 (Δ -0,275), 2025-12 (Δ +0,3123, Rückkehr 2026-02) und 2025-09..2025-11 (Δ -0,2355). 2019-02..2019-07 (R3 innen, Δ +0,3227, Folgeniveau). 2018-08 und 2019-01..2019-02 scheitern an S_vorniveau_min3 (1 bzw. 2 Monate). Alle Zahlen des Annotators stimmen mit pruefe überein.

(5) Regel 2 (Trend): Es gibt keinen Eintrag, der ein Trend sein könnte. Der Verlauf um 2024-04 ist eher eine Stufe als ein Trend, ändert am Ergebnis aber nichts. Regel 5: satz für die leere Auswahl liefert ok (anzahl 0). Regel 11 (notes) ist nicht anwendbar, weil es keinen Eintrag gibt.

**Vollständigkeit (Prüfer):** scan über /Users/vaios/EPA-Bachelorarbeit/EPA-Bachelorarbeit/backend/data/series/4_open_grid_europe_employee.csv: 22 bewertete Monate, 0 regelkonforme Zeiträume in 0 Gruppen, 1 Zweifelsfall in 1 Gruppe (2024-08..2024-10, rise, Δ +0,391). Diese einzige Gruppe ist begründet verworfen. Sie verschiebt period_from hinter den ersten abweichenden Monat 2024-04, der schon im Vorniveau steht (Vortrend +0,37). Die definitionsgemäße Abgrenzung 2024-04..2024-04 scheitert an der Stützung des n=6-Monats (2024-08 nur +0,39 < 0,5). Damit ist sie nicht sonst regelkonform, und es gibt weder einen Eintrag noch einen Zweifelsfall. Laut Protokoll ist das als Stelle ohne Eintrag zu vermerken. Der frühere Lauf hatte keine Kandidaten ([]), also war dort nichts zusätzlich zu prüfen. Eine regelkonforme, definitionsgemäße Stelle fehlt nicht. Endergebnis wie beim Annotator: 0 Einträge, 0 Zweifelsfälle. satz für die leere Auswahl: ok.


## E.ON (ID 7, 38 bewertete Monate)

**Ergebnis:** 0 Einträge, 0 Zweifelsfälle für Stufe B.


**Auswahl (Annotator):** Für diese Reihe gibt es keinen Eintrag und keinen Zweifelsfall. Grundlage: tabelle, scan und pruefe des Rechners. Die Reihe E.ON Mitarbeitende hat 38 bewertete Monate, viele graue Monate ab 2020-08 und einige dünne Monate. Sie schwankt stark um etwa 4,0 und zeigt mehrere einzelne Ausreißer, nach denen das alte Niveau zurückkehrt: abwärts 2019-08, 2019-10, 2020-07 und 2024-12, aufwärts 2019-04 und 2022-09. Daher findet der Scan 0 regelkonforme Zeiträume. Alle von Hand definitionsgemäß abgegrenzten Stellen scheitern an der Folgeniveau-Setzung (a)/(b), an Regel 4 oder an der Stützung dünner Monate. Die Tiefphase 2019-08 bis 2020-01 (Δ -0,51 bis -0,64 je nach Abgrenzung) ist vorübergehend, denn ab 2020-04 kehrt das alte Niveau zurück (4,20-4,44). Die einzige Scan-Zweifelsgruppe (2019-06/07/08..2019-09, Δ -0,31 bis -0,48) nehme ich nicht als Zweifelsfall auf. In allen Varianten ist period_to 2019-09 = 4,175, und dieser Wert liegt über dem Vorniveau 4,007, also nicht auf dem neuen Niveau. Die Folgeniveau-Setzung besteht nur, weil der Zeitraum über diesen Rückkehrmonat verlängert wird. Die definitionsgemäßen Abgrenzungen 2019-08..2019-08 (Δ -1,1252) und 2019-08..2019-10 (Δ -0,6439) scheitern am Folgeniveau. Nach dem Protokoll gibt es für diese Stelle deshalb keinen Eintrag (vermerkt in verworfen). Die Kandidaten mit |Δ| zwischen 0,30 und 0,49 (2021-10, 2025-01, 2025-09 und weitere) sind keine Zweifelsfälle, weil sie zusätzlich an Folgeniveau oder Stützung scheitern. Den langsamen Anstieg 2023-11 bis 2026-03 von etwa 4,0 auf 4,3-4,5 werte ich nach Regel 2 als Trend. Auch die Vortrend-Hinweise des Rechners habe ich geprüft (2019-10, 2021-07, 2022-09, 2026-03). Das Prüfprotokoll mit satz für die leere Auswahl ergibt: anzahl 0, ok true. Ergebnis: Reihe ohne Referenzzeitraum (gültiges Ergebnis).

**Verworfene Kandidaten (24):**

- 2019-04..2019-04 (rise): Setzung Vorniveau mindestens drei bewertete Monate. Vorniveau nur 1 bewerteter Monat (2019-03 = 3,50, n=8); 2019-04 = 4,55 (n=8); Folgemonate 2019-05..07 = 4,087/4,031/3,868, also kein Sprung mit Verbleib prüfbar; Rechner: verworfen.
- 2019-08..2019-08 (fall): Setzung Folgeniveau (a) und (b); Regel 4 Satz 2: einzelner Monatssprung mit Rückkehr. Vorniveau 4,007 (2019-03 bis 2019-07, n=8-30), Niveau 2,882 (n=11), Δ -1,1252; Folgemittel 3,6657, Abstand 0,3415 < verlangt 0,5626; erster Folgemonat 2019-09 = 4,175 (n=8), Abstand -0,1678 (über dem Vorniveau, Rückkehr).
- 2019-08..2019-09 (fall), Scan-Zweifelsgruppe: Abgrenzung nach der Definition (period_to nicht auf dem neuen Niveau); kein Verlängern, damit eine Setzung besteht. Rechner: Zweifelsfall, Δ -0,4787 (Vor 4,007, Niv 3,5285), Folgemittel 3,4693. period_to 2019-09 = 4,175 liegt über dem Vorniveau 4,007, ist also eine Rückkehr und nicht der erste Monat auf dem neuen, niedrigeren Niveau. Nur weil 2019-09 eingeschlossen wird, verschiebt sich das Folgefenster auf die tiefen Monate 2019-10/12, 2020-01, und die Folgeniveau-Setzung besteht. Die definitionsgemäßen Abgrenzungen 2019-08..2019-08 (Δ -1,1252) und 2019-08..2019-10 (Δ -0,6439) scheitern am Folgeniveau, daher kein Eintrag und kein Zweifelsfall für diese Stelle.
- 2019-07..2019-09 und 2019-06..2019-09 (fall), Scan-Zweifelsgruppe: Abgrenzung nach der Definition (period_from nicht der erste deutlich abweichende Monat; period_to wie oben). 2019-07..09: Δ -0,4003 (Vor 4,042, 2019-03 bis 2019-06); 2019-06..09: Δ -0,3067 (Vor 4,0457, 2019-03 bis 2019-05). 2019-06 = 4,031 (Diff zu Vor6 -0,01) und 2019-07 = 3,868 (Diff -0,17) weichen nicht deutlich ab, erst 2019-08 = 2,882 (Diff -1,13). period_to 2019-09 = 4,175 liegt nicht auf dem neuen Niveau.
- 2019-08..2019-10 (fall): Setzung Folgeniveau (a) und (b). Definitionsgemäße Variante mit 2019-10 (3,033, n=12) als erstem Monat auf dem neuen Niveau: Δ -0,6439 (Vor 4,007, Niv 3,3633); Folgemittel 3,8583, Abstand 0,1489 < 0,3219; erster Folgemonat 2019-12 = 3,789, Abstand 0,2182 < 0,25.
- 2019-08..2019-12 und 2019-08..2020-01 (fall), gesamte Tiefphase: Setzung Folgeniveau (a); altes Niveau kehrt ab 2020-04 zurück. 2019-08..12: Δ -0,5374, Folgemittel 4,0167, Abstand -0,0095 < 0,2687. 2019-08..2020-01: Δ -0,5142, Folgemittel 4,3023, Abstand -0,2951 < 0,2571; erster Folgemonat 2020-04 = 4,200 (Abstand -0,1928). Die Tiefphase 2019-08 bis 2020-01 ist vorübergehend.
- 2019-10..2019-10 / 2019-10..2019-12 / 2019-10..2020-01 (fall): Setzung Folgeniveau; bei ..2020-01 zusätzlich Regel 4; Vortrend-Hinweis (Regel 2 geprüft). 2019-10..10: Δ -0,8992 (Vor 3,9322), Folgemittel 3,8583, Abstand 0,0738 < 0,4496, erster Folgemonat 2019-12 = 3,789 (0,1432 < 0,25). 2019-10..12: Δ -0,5212, Folgemittel 4,0167 (Abstand -0,0845). 2019-10..2020-01: Δ -0,4628, Folgemittel 4,3023 (Abstand -0,3702). Rechner-Hinweis Vortrend -0,58, aber kein gleichmäßiger Verlauf: Vormonate wechseln (2019-08 = 2,882, 2019-09 = 4,175).
- 2020-04..2020-04 / 2020-04..2020-05 / 2020-04..2020-06 (rise): Setzung Folgeniveau (a), bei ..06 auch (b). Vorniveau 3,5555 (2019-07 bis 2020-01, enthält die Tiefmonate 2019-08/10). ..04: Δ +0,6445, Folgemittel 3,8607, Abstand 0,3052 < 0,3223. ..05: Δ +0,6765, Folgemittel 3,8187, Abstand 0,2632 < 0,3383. ..06: Δ +0,7468, erster Folgemonat 2020-07 = 2,875 (Abstand -0,6805), Folgemittel 3,4233. Das ist eher die Rückkehr zum Niveau von 2019 als ein neues Niveau.
- 2020-07..2020-07 (fall): Setzung Folgeniveau (a) und (b); Setzung Stützung dünner Monate. Δ -1,0108 (Vor 3,8858, Niv 2,875, n=8); Folgemittel 3,5873, Abstand 0,2985 < 0,5054; erster Folgemonat 2021-04 = 4,138, Abstand -0,2522 (Rückkehr); 2020-07 (n=8) ohne Stützung.
- 2020-07..2021-04 (fall): Regel 2 Länge; Regel 3 innen höchstens ein nicht bewerteter Monat; Regel 4. 10 Kalendermonate, 8 nicht bewertete Monate innen (2020-08 bis 2021-03), Δ -0,3793.
- 2021-04..2021-04 (rise): Regel 4; Setzung Folgeniveau; Stützung. Δ +0,2785 (Vor 3,8595, Niv 4,138); erster Folgemonat 2021-05 = 3,257 (Abstand -0,6025); 2021-04 (n=8) ohne Stützung.
- 2021-05..2021-05 / 2021-05..2021-07 (fall): Setzung Folgeniveau (a), bei ..07 auch (b). ..05: Δ -0,6607 (Vor 3,9177, 2020-01 bis 2021-04, über 16 Kalendermonate verteilt), Folgemittel 3,809, Abstand 0,1087 < 0,3303. ..07: Δ -0,6057, Folgemittel 3,9757 (Abstand -0,058), erster Folgemonat 2021-10 = 4,217 (Abstand -0,2993).
- 2021-07..2021-07 (fall): Regel 4; Setzung Folgeniveau; Stützung. Δ -0,4958; erster Folgemonat 2021-10 = 4,217 (Abstand -0,3542); 2021-07 (n=6) ohne Stützung; Vortrend-Hinweis -0,88. Kein Zweifelsfall, weil Folgeniveau und Stützung scheitern.
- 2021-10..2021-10 / 2021-10..2021-11 (rise): Regel 4 (Zweifelsbereich); Setzung Folgeniveau (b); Stützung. ..10: Δ +0,4930, aber erster Folgemonat 2021-11 = 3,843 (Abstand 0,119 < 0,25) und 2021-10 (n=6) ohne Stützung, also nicht 'sonst regelkonform' und kein Zweifelsfall. ..11: Δ +0,306, (b) 2022-01 = 3,867 (0,143), 2021-10/11 ohne Stützung.
- 2022-09..2022-09 / 2022-09..2022-10 (rise): Setzung Folgeniveau (a) und (b); Stützung; bei ..10 Regel 4. ..09: Δ +0,5685 (Vor 3,7815), Folgemittel 3,8723, Abstand 0,0908 < 0,2842; erster Folgemonat 2022-10 = 3,850 (0,0685); 2022-09 (n=8) ohne Stützung; Vortrend-Hinweis +0,39. ..10: Δ +0,3185, erster Folgemonat 2023-02 = 3,767 (-0,0145).
- 2023-12..2023-12 / 2023-11..2023-12 (rise): Regel 4; Setzung Folgeniveau (b); Stützung. ..12: Δ +0,3372, erster Folgemonat 2024-02 = 3,840 (Abstand -0,1398), 2023-12 (n=6) ohne Stützung. 2023-11..12: Δ +0,2348.
- 2024-03..2024-03 / 2024-03..2024-05 (rise): Regel 4; Setzung Folgeniveau; Stützung. ..03: Δ +0,3932, Folgemittel 4,152, Abstand 0,1822 < 0,1966, 2024-03 (n=8) ohne Stützung. ..05: Δ +0,3432, erster Folgemonat 2024-08 = 3,880 (Abstand -0,0898), 2024-03/04/05 ohne Stützung.
- 2024-08..2024-08 (fall): Regel 4; Setzung Folgeniveau; Stützung. Δ -0,3102 (Vor 4,1902, Niv 3,88, n=5); Folgemittel 4,0927 (Abstand 0,0975 < 0,1551); erster Folgemonat 2024-09 = 4,438 (Abstand -0,2478); ohne Stützung.
- 2024-09..2024-10 / 2024-10..2024-10 (rise): Regel 4; Setzung Folgeniveau (a) und (b). ..09-10: Δ +0,3363; ..10: Δ +0,3772; beide mit erstem Folgemonat 2024-12 = 3,280 (Abstand -0,8827 bzw. -0,9028), Folgemittel 4,0803 unter dem Vorniveau.
- 2024-12..2024-12 / 2024-12..2025-01 (fall): Setzung Folgeniveau (a) und (b); Stützung; bei ..2025-01 Regel 4. ..12: Δ -1,0228 (Vor 4,3028, Niv 3,28, n=5), erster Folgemonat 2025-01 = 4,583 (Abstand -0,2802, Rückkehr), Folgemittel 4,4967 (Abstand -0,1938 < 0,5114), ohne Stützung. ..2025-01: Δ -0,3713, Folgemittel 4,4787 (Abstand -0,1758).
- 2025-01..2025-01 / 2025-01..2025-02 (rise): Regel 4 (Zweifelsbereich); Setzung Stützung dünner Monate. ..01: Δ +0,4607, Folgeniveau ok (Folgemittel 4,4787, Abstand 0,3563), aber 2025-01 (n=6) ohne Stützung, daher nicht 'sonst regelkonform' und kein Zweifelsfall. ..02: Δ +0,3582, 2025-01 (n=6) und 2025-02 (n=9) ohne Stützung.
- 2025-09..2025-09 (rise): Regel 4; Setzung Stützung dünner Monate. Δ +0,3425 (Vor 4,1865, Niv 4,529, n=7); Folgeniveau ok (2026-03 = 4,529); 2025-09 ohne Stützung, also kein Zweifelsfall.
- 2026-03..2026-03 (rise): Regel 4; Setzung (c) kein bewerteter Folgemonat; Stützung; Vortrend (Regel 2). Δ +0,2343; kein bewerteter Monat nach 2026-03, Bleiben nicht prüfbar; ohne Stützung (n=7); Vortrend-Hinweis +0,40.
- 2023-11..2026-03 Anstieg von etwa 4,0 auf 4,3-4,5: Regel 2 Trend (gleichmäßige Bewegung über mehr als sechs Monate). Mittel steigt allmählich (2023-11 = 4,045; 2024-03 bis 05 = 4,24-4,36; 2024-09/10 = 4,44/4,56; 2025-09 und 2026-03 = 4,529), kein abgrenzbarer Sprung; alle Teilstellen oben mit |Δ| < 0,5 oder an Folgeniveau/Stützung gescheitert.

**Widerlegungsversuche (Prüfer):** Der Annotator hat keine Einträge und keine Zweifelsfälle. Ich habe daher versucht, seine leere Auswahl zu widerlegen, also eine regelkonforme Stelle zu finden, die er übersehen oder zu Unrecht verworfen hat. Alle seine Zahlen habe ich mit pruefe nachgerechnet. Sie stimmen überein.

(1) Kandidat des früheren Laufs 2019-08..2019-08 (fall): pruefe ergibt "verworfen", gescheitert an S_folgeniveau. Δ -1,1252 (Vor 4,0072, Niv 2,882, n=11). Folgemittel 3,6657, Abstand 0,3415 < 0,5626, also (a) nicht erfüllt. Erster Folgemonat 2019-09 = 4,175, Abstand -0,1678, also (b) nicht erfüllt. Das ist ein Einmonatsausreißer mit Rückkehr über das Vorniveau (Regel 4 Satz 2). Ein Eintrag ist widerlegt.

(2) Scan-Zweifelsgruppe 2019-08..09 / 2019-07..09 / 2019-06..09 (Δ -0,4787 / -0,4003 / -0,3067, Rechner: zweifelsfall): In allen Varianten ist period_to 2019-09 = 4,175. Dieser Wert liegt über dem Vorniveau 4,007, ist also nicht der erste Monat auf dem neuen, niedrigeren Niveau. Die Folgeniveau-Setzung besteht nur, weil das Folgefenster durch das Einschließen des Rückkehrmonats auf 2019-10/12 und 2020-01 rückt. Das Protokoll verbietet es, einen Zeitraum zu verlängern, nur damit eine Regel besteht. Bei 2019-07..09 und 2019-06..09 ist außerdem period_from nicht der erste deutlich abweichende Monat: 2019-06 liegt bei -0,01, 2019-07 bei -0,17, erst 2019-08 bei -1,13. Die definitionsgemäßen Abgrenzungen 2019-08..08 und 2019-08..10 scheitern am Folgeniveau. Bei 2019-08..10: Δ -0,6439, Folgemittel-Abstand 0,1489 < 0,3219, erster Folgemonat 2019-12 mit Abstand 0,2182 < 0,25. Die Verwerfung durch den Annotator folgt also der Abgrenzungsregel. Damit ist für diese Stelle auch kein Zweifelsfall zu setzen.

(3) Weitere Prüfungen zur Tiefphase 2019: 2019-07..10 (Δ -0,5525) ist verworfen (S_folgeniveau (a)). 2019-08..12 (Δ -0,5374, Folgemittel-Abstand -0,0095) und 2019-08..2020-01 (Δ -0,5142, erster Folgemonat 2020-04 = 4,20, Rückkehr) sind verworfen. 2019-10..10 (Δ -0,8992) ist verworfen (Folgeabstand 0,0738 bzw. 0,1432). 2019-09..10 ist verworfen (R4, Folgeniveau). Die Tiefphase ist vorübergehend.

(4) 2020-04..04 (Δ +0,6445) ist knapp verworfen: Folgemittel-Abstand 0,3052 < 0,3223. 2020-04..06 (Δ +0,7468) ist verworfen, weil 2020-07 = 2,875 eine Rückkehr ist. Das Vorniveau enthält die Tiefmonate. Kein Eintrag.

(5) Einzelne Ausreißer 2020-07 (Δ -1,0108), 2021-05 (Δ -0,6607), 2022-09 (Δ +0,5685) und 2024-12 (Δ -1,0228) sind alle verworfen, jeweils an S_folgeniveau, zum Teil zusätzlich an der Stützung dünner Monate. 2019-04 scheitert an S_vorniveau_min3 (1 Monat).

(6) Bereich 0,30 bis 0,49: 2021-10 (+0,493), 2021-07 (-0,4958), 2025-01 (+0,4607), 2025-09 (+0,3425), 2024-03 (+0,3932), 2024-10 (+0,3772) und 2023-12 (+0,3372) scheitern jeweils zusätzlich an Folgeniveau und/oder Stützung (R3_stuetzung_duenn). Keiner ist "sonst regelkonform", also gibt es keinen Zweifelsfall. 2026-03 (+0,2343) ist ohne bewerteten Folgemonat nicht prüfbar.

(7) Regel 2: Der langsame Anstieg von 2023-11 bis 2026-03 enthält keinen abgrenzbaren Sprung mit |Δ| >= 0,5. Die Vortrend-Hinweise habe ich geprüft. Sie ändern nichts, denn die betroffenen Stellen scheitern ohnehin.

(8) satz mit leerer Auswahl: anzahl 0, ok true.

Ergebnis: Der Annotator ist nicht widerlegt. Die Reihe bleibt ohne Referenzzeitraum und ohne Zweifelsfall.

**Vollständigkeit (Prüfer):** Der scan ergibt 0 regelkonforme Zeiträume in 0 Gruppen und 1 Zweifelsgruppe (2019-06..2019-09, 2019-07..2019-09, 2019-08..2019-09; fall; Δ -0,31 bis -0,48). Die Zweifelsgruppe hat der Annotator begründet verworfen. Die Begründung ist eine Abgrenzung nach der Definition: period_to 2019-09 = 4,175 liegt über dem Vorniveau 4,007 und ist ein Rückkehrmonat, period_from 2019-06/07 weicht nicht deutlich ab, und es gilt das Verlängerungsverbot. Die definitionsgemäßen Abgrenzungen 2019-08..08 und 2019-08..10 scheitern am Folgeniveau. Ich bestätige diese Behandlung. Den Kandidaten des früheren Laufs 2019-08..2019-08 habe ich geprüft: verworfen (S_folgeniveau, Rückkehr 2019-09). Weitere Stellen außerhalb des Scans habe ich von Hand gegengeprüft, darunter 2019-04, 2019-07..10, 2019-08..12, 2019-08..2020-01, 2019-10, 2020-04..06, 2020-07, 2021-05, 2021-07, 2021-10, 2022-09, 2023-12, 2024-03, 2024-10, 2024-12, 2025-01, 2025-09 und 2026-03. Keine davon ist regelkonform, und keine ist ein Zweifelsfall, der sonst regelkonform wäre. Es fehlt also keine Stelle. Die leere Auswahl besteht satz (anzahl 0, ok true).


## RWE (ID 8, 34 bewertete Monate)

**Ergebnis:** 0 Einträge, 0 Zweifelsfälle für Stufe B.


**Auswahl (Annotator):** Die RWE-Reihe (Mitarbeitende, Gesamtbewertung) bekommt keinen Eintrag. Das ist ein gültiges Ergebnis. Die Reihe ist sehr lückig: 34 bewertete Monate, oft mit n=5-10 und langen grauen Strecken. Sie schwankt stark um etwa 3,5 (2014-2019) bzw. etwa 4,0-4,2 (ab 2019).

Der Scan fand 0 regelkonforme Varianten und 2 Zweifelsfälle. Auch die Prüfung aller weiteren Stellen mit pruefe ergab keine regelkonforme Variante. Geprüft wurden alle Monate mit |Diff| >= 0,3 in der Tabelle sowie die zusammengefassten Varianten. Alle großen Ausschläge sind Einzelmonate oder kurze Einbrüche, nach denen das alte Niveau zurückkehrt:
- 2016-01 und 2018-08 nach oben
- 2022-09 bis 2022-11 nach unten, Rückkehr 2023-02
- 2023-05 nach oben
- 2024-07 nach unten, Rückkehr 2024-09

Diese Fälle scheitern an Setzung a/b (Regel 4: ein einzelner Sprung mit Rückkehr reicht nicht) und meist zusätzlich an der Stützungs-Setzung für dünne Monate.

Keiner der beiden Zweifelsfälle des Scans wurde übernommen:
- 2015-09 (Δ +0,3505): Bei der Trendprüfung nach Regel 2 zeigt sich ein gleichmäßiger Anstieg seit 2014-06 (3,00 -> 3,35 -> 3,40 -> 3,773 -> 4,067 bis 2016-01) über mehr als sechs Kalendermonate, ohne sichtbare Stufe. Danach fällt die Reihe auf 3,48-3,63 zurück.
- 2023-02..2023-04 (Δ +0,4073): Die Variante ist nicht definitionsgemäß, weil 2023-02 schon auf dem neuen Niveau liegt. Die definitionsgemäße Variante 2023-02..2023-02 (Δ +0,5258) scheitert an der Stützung. In der Sache kehrt hier nur das alte Niveau nach dem Einbruch 2022-09/2022-11 zurück; das Vorniveau 3,7612 ist eine Mischung aus beiden Niveaus.

satz mit leerer Auswahl: anzahl 0, ok true (34 bewertete Monate). Alle Zahlen stammen aus dz1_rechner.py (tabelle, scan, pruefe, satz). Es wurde keine Datei geändert.

**Verworfene Kandidaten (22):**

- 2014-06..2014-06: Setzung Vorniveau mindestens drei bewertete Monate (S_vorniveau_min3): nicht prüfbar. Vorniveau nur 1 bewerteter Monat (2013-12 = 3,94, n=5); Zeitraum 3,00 (n=5); tabelle-Diff -0,94; Rechner: verworfen
- 2015-09..2015-09: Regel 2 Trend (eigene Prüfung); kein bleibender Niveausprung. Rechner: Zweifelsfall 0,30-0,49, sonst regelkonform. Δ +0,3505; Vorniveau 3,4225 (2013-12 3,94; 2014-06 3,00; 2014-11 3,35; 2015-03 3,40). Bewegung läuft seit 2014-06 gleichmäßig aufwärts: 3,00 -> 3,35 -> 3,40 -> 3,773 (2015-09) -> 4,067 (2016-01), also über 19 Kalendermonate ohne sichtbare Stufe. Danach fällt die Reihe wieder auf 3,629 (2016-04), 3,476 (2016-06) und 3,60 (2016-07) zurück. Deshalb kein Zweifelsfall.
- 2015-09..2016-01: Regel 3 innen (3 nicht bewertete Monate), Regel 4 (Zweifelsbereich), Setzung a/b, Stützung dünn. Δ +0,4975; 2015-10 (n=1), 2015-11 (n=2) und 2015-12 (n=2) nicht bewertet; Folgemittel 3,5683, Abstand 0,1458 < 0,2488 verlangt; erster Folgemonat 2016-04 = 3,629 mit Abstand 0,2065 < 0,25; 2016-01 (n=6) ohne Stützung
- 2016-01..2016-01: Setzung a/b (Rückkehr nach Einzelmonat, Regel 4), Stützung dünn. Δ +0,5744; Vorniveau 3,4926; Folgemittel 3,5683, Abstand 0,0757 < 0,2872; erster Folgemonat 2016-04 = 3,629 mit Abstand 0,1364 < 0,25; 2016-01 (n=6) ohne Stützung
- 2017-11..2017-11: Regel 4 (Zweifelsbereich), Setzung a/b, Stützung dünn. Δ -0,3113; Vorniveau 3,7253; Folgemittel 3,651, Abstand 0,0743 < 0,1557; erster Folgemonat 2018-06 = 3,536 mit Abstand 0,1893 < 0,25; 2017-11 (n=7) ohne Stützung
- 2018-08..2018-08: Setzung b (Rückkehr im ersten Folgemonat; Einzelmonatssprung, Regel 4). Δ +0,5015; Vorniveau 3,5355; erster Folgemonat 2018-10 = 3,540 mit Abstand 0,0045 < 0,25; Folgemittel 3,7933 (Abstand 0,2578, Setzung a knapp erfüllt)
- 2019-05..2019-05: Regel 4 (Zweifelsbereich), Stützung dünn. Δ +0,321; Vorniveau 3,619; 2019-05 (n=5) ohne Stützung
- 2019-05..2019-07: Regel 4 (Zweifelsbereich), Stützung dünn. Δ +0,311; Vorniveau 3,619; Zeitraum 3,93 (n=5, 7, 10); 2019-05 (n=5) und 2019-06 (n=7) ohne Stützung
- 2021-09..2021-09: Regel 4 (Zweifelsbereich), Setzung a/b, Stützung dünn. Δ +0,3255; Vorniveau 3,8945; Folgemittel 3,4657, Abstand -0,4288 (gegen Sprungrichtung); erster Folgemonat 2021-10 = 4,017 mit Abstand 0,1225 < 0,25; 2021-09 (n=5) ohne Stützung
- 2021-09..2021-10: Regel 4 (< 0,30), Setzung a/b, Stützung dünn. Δ +0,224; Folgemittel 3,5557, Abstand -0,3388; erster Folgemonat 2022-09 = 3,10 mit Abstand -0,7945
- 2022-09..2022-09: Setzung a (altes Niveau kehrt zurück, Regel 4). Δ -0,9045; Vorniveau 4,0045 (2019-05 bis 2021-10); Folgemittel 3,8723, Abstand 0,1322 < 0,4523; erster Folgemonat 2022-11 = 3,28 (Setzung b erfüllt)
- 2022-09..2022-11: Definitionsgemäße Abgrenzung des Einbruchs; Setzung a/b, Regel 4 (Einbruch mit Rückkehr). Δ -0,8145; Zeitraum 3,19 (n=8, 5), 2022-10 nicht bewertet (n=2); Folgemittel 4,3323, Abstand -0,3278 < 0,4073; erster Folgemonat 2023-02 = 4,287 mit Abstand -0,2825 (liegt über dem Vorniveau). Für diese Stelle gibt es keinen Eintrag.
- 2022-11..2022-11: Nicht definitionsgemäß (die Abweichung beginnt 2022-09), Setzung a/b, Stützung dünn. Δ -0,5845; Vorniveau 3,8645 (enthält 2022-09); Folgemittel 4,3323, Abstand -0,4678; erster Folgemonat 2023-02 mit Abstand -0,4225; 2022-11 (n=5) ohne Stützung
- 2023-02..2023-02: Definitionsgemäße Abgrenzung; Stützung dünn (Setzung); in der Sache Rückkehr auf das alte Niveau nach dem Einbruch 2022-09/2022-11. Δ +0,5258; das Vorniveau 3,7612 mischt das alte Niveau (2019-07 bis 2021-10: 3,95-4,22) mit dem Einbruch (2022-09 3,10, 2022-11 3,28); Vortrend -0,591; 2023-02 (n=8) ohne Stützung, weil 2023-04 = 4,05 keine 0,5 über dem Vorniveau liegt. Für diese Stelle gibt es keinen Eintrag.
- 2023-02..2023-04: Nicht definitionsgemäß; Regel 4 Zweifelsbereich. Kein Zweifelsfall, weil die definitionsgemäße Variante 2023-02..2023-02 ist (Δ >= 0,5, scheitert an der Stützung). Δ +0,4073 (laut Rechner sonst regelkonform); 2023-03 nicht bewertet (n=2). 2023-02 = 4,287 liegt schon auf dem neuen Niveau; die Verlängerung bis 2023-04 (4,05) besteht die Stützungsregel nur durch die Verlängerung. Zudem kehrt hier das alte Niveau nach dem Einbruch zurück.
- 2023-02..2023-05: Setzung a. Δ +0,5712; Länge 4; Folgemittel 3,911 (2023-11 4,483; 2024-02 3,97; 2024-07 3,28), Abstand 0,1498 < 0,2856
- 2023-05..2023-05: Setzung a (Einzelmonatsspitze). Δ +0,8343; Vorniveau 3,8257; Folgemittel 3,911, Abstand 0,0853 < 0,4172
- 2023-11..2023-11: Setzung a/b, Stützung dünn; Rechner-Hinweis Vortrend +0,87 (Regel 2). Δ +0,584; Vorniveau 3,899; Folgemittel 3,8403, Abstand -0,0587; erster Folgemonat 2024-02 = 3,97 mit Abstand 0,071 < 0,25; 2023-11 (n=6) ohne Stützung
- 2024-07..2024-07: Setzung a/b (Einzelmonatssprung mit Rückkehr, Regel 4), Stützung dünn. Δ -0,8417; Vorniveau 4,1217; Folgemittel 4,2313, Abstand -0,1097 < 0,4208; erster Folgemonat 2024-09 = 4,271 mit Abstand -0,1493; 2024-07 (n=5) ohne Stützung
- 2025-07..2025-07: Regel 4 (Zweifelsbereich), Setzung a/b, Stützung dünn. Δ +0,324; Vorniveau 4,109; Folgemittel 3,7685, Abstand -0,3405; erster Folgemonat 2025-08 = 3,62 mit Abstand -0,489; 2025-07 (n=6) ohne Stützung
- 2025-08..2025-08: Regel 4 (Zweifelsbereich), Setzung a/b, Stützung dünn. Δ -0,4512; Vorniveau 4,0712; einziger Folgemonat 2025-09 = 3,917 mit Abstand 0,1542 < 0,2256 (a) und < 0,25 (b); 2025-08 (n=5) ohne Stützung
- 2025-08..2025-09: Setzung c (kein bewerteter Folgemonat, nicht prüfbar), Regel 4 (Zweifelsbereich), Stützung dünn. Δ -0,3027; nach 2025-09 kein bewerteter Monat mehr; 2025-08 (n=5) und 2025-09 (n=6) ohne Stützung

**Widerlegungsversuche (Prüfer):** Der Annotator hat keine Einträge und keine Zweifelsfälle. Deshalb galt der Widerlegungsversuch drei Fragen: (1) Gibt es doch eine regelkonforme Stelle? (2) Sind seine Verwerfungen falsch? (3) Hätte ein Scan-Zweifelsfall übernommen werden müssen?

(1) Regelkonforme Stellen: Der scan meldet 0 regelkonforme Varianten in 0 Gruppen. Mit pruefe habe ich zusätzlich alle Randvarianten nachgerechnet. Keine ist regelkonform:
- 2014-06..2014-11, 2014-11, 2015-03..2015-09, 2016-01..2016-04
- 2018-07..2018-08, 2018-08..2018-10, 2019-05..2019-06, 2019-07, 2020-04
- 2022-09..2023-02, 2023-04..2023-05, 2024-07..2024-09, 2025-07..2025-08

(2) Verwerfungen: Alle 22 Verwerfungen des Annotators habe ich mit pruefe nachgerechnet. Ergebnis und Gründe stimmen mit dem Rechner überein:
- 2014-06: Vorniveau nur 1 bewerteter Monat.
- 2015-09..2016-01: Regel 3 innen, Regel 4, Folgeniveau, Stützung.
- 2016-01: Folgeniveau (Folgeabstand 0,0757, erster Folgemonat 0,1364) und Stützung (n=6).
- 2017-11: Regel 4 (-0,31), Folgeniveau, Stützung.
- 2018-08: Setzung b, weil 2018-10 = 3,54 nur 0,0045 über dem Vorniveau liegt.
- 2019-05 und 2019-05..2019-07: Regel 4 (0,32 bzw. 0,31) und Stützung. Deshalb ist auch kein Zweifelsfall möglich.
- 2021-09 und 2021-09..2021-10: Regel 4, Folgeniveau, Stützung.
- 2022-09: Setzung a (0,1322 < 0,4523).
- 2022-09..2022-11: Setzung a/b. Rückkehr 2023-02 = 4,287 liegt über dem Vorniveau 4,0045.
- 2022-11: Folgeniveau, Stützung.
- 2023-02..2023-05: Setzung a.
- 2023-05: Setzung a (0,0853 < 0,4172).
- 2023-11: Folgeniveau, Stützung.
- 2024-07: Folgeniveau (Rückkehr 2024-09 = 4,271), Stützung.
- 2025-07, 2025-08: Regel 4, Folgeniveau, Stützung.
- 2025-08..2025-09: kein bewerteter Folgemonat (Setzung c), dazu Regel 4 und Stützung.

Kandidaten des früheren Laufs:
- 2018-08..2018-08: Der Rechner verwirft wegen S_folgeniveau. Setzung b scheitert: erster Folgemonat 2018-10 = 3,540, Abstand 0,0045 < 0,25. Das ist ein Einmonatsausreißer mit Rückkehr. Kein Eintrag.
- 2023-02..2023-02: Der Rechner verwirft wegen R3_stuetzung_duenn. 2023-02 hat n=8, und der erste Folgemonat 2023-04 = 4,05 liegt nur 0,289 über dem Vorniveau 3,761. Kein Eintrag.

(3) Scan-Zweifelsfälle:

2015-09..2015-09 (Δ +0,3505, laut Rechner sonst regelkonform). Der Annotator verwirft nach Regel 2 als Trend. Ich habe versucht, das zu widerlegen.
- Gegen den Annotator spricht: Der Rechner meldet keinen Vortrend. Mittel der ersten zwei Vorniveaumonate 3,47, der letzten zwei 3,375.
- Für den Annotator spricht: Ab 2014-06 steigen die bewerteten Monate stetig: 3,00 -> 3,35 -> 3,40 -> 3,773 -> 4,067. Das sind 19 Kalendermonate ohne erkennbare Stufe. Danach kehrt die Reihe zurück (2016-04 3,629; 2016-06 3,476; 2016-07 3,60). Der Abstand dieser drei Monate zum Vorniveau 3,4225 beträgt im Mittel 0,15 und liegt damit unter Δ/2 = 0,175.
- Setzung a/b besteht nur, weil 2016-01 als Folgemonat zählt. 2016-01 gehört selbst zur erhöhten Phase. Deren durchgehende Abgrenzung 2015-09..2016-01 scheitert an Regel 3 innen (drei graue Monate) und an a/b.
- Das Vorniveau stützt sich auf vier dünne Monate (n=5-8) über 16 Kalendermonate.
- Der Grundsatz "Gesucht sind Stellen, an denen das Niveau ... danach auf dem neuen Niveau bleibt" ist also nicht erkennbar erfüllt.

Die Begründung des Annotators ist regelgestützt (Regel 2, Regel 4 Rückkehr). Keine Regel verlangt zwingend die Aufnahme. Nach "im Zweifel bleibt das Ergebnis des Annotators" bleibt es ohne Zweifelsfall.

2023-02..2023-04 (Δ +0,4073, laut Rechner sonst regelkonform):
- period_from 2023-02 ist der erste abweichende Monat. 2023-02 = 4,287 liegt bereits auf dem neuen Niveau; die Folgemonate liegen bei etwa 4,0-4,7. Definitionsgemäß ist deshalb 2023-02..2023-02.
- Die Verlängerung bis 2023-04 besteht die Stützungsregel nur, weil dann 2023-05 (4,66) erster Folgemonat wird. Das Protokoll verbietet ausdrücklich, einen Zeitraum nur zu verlängern, damit eine Regel besteht.
- Die definitionsgemäße Variante scheitert an der Stützung, einer harten Regel. Damit ist sie nicht "sonst regelkonform" und kann kein Zweifelsfall sein.
- In der Sache kehrt hier das alte Niveau nach dem Einbruch 2022-09/2022-11 zurück. Das Vorniveau 3,761 mischt beide Niveaus (Vortrend -0,591).

Die Verwerfung ist korrekt. Ergebnis: keine Abweichung vom Annotator.

**Vollständigkeit (Prüfer):** Der scan meldet für die Reihe (34 bewertete Monate) 0 regelkonforme Gruppen und 2 Zweifelsfall-Gruppen. Behandlung:

- Gruppe 2015-09..2015-09 (rise, Δ +0,351): vom Annotator begründet verworfen. Gründe: Regel 2 Trend 2014-06 bis 2016-01; Rückkehr auf etwa 3,5-3,6 ab 2016-04. Bestätigt, kein Zweifelsfall.
- Gruppe 2023-02..2023-04 (rise, Δ +0,407): vom Annotator begründet verworfen. Die Variante ist nicht definitionsgemäß. Die definitionsgemäße Variante 2023-02..2023-02 scheitert an der Stützung. Bestätigt, kein Zweifelsfall.

Alle weiteren Monate mit |Diff| >= 0,3 aus der Tabelle sind vom Annotator begründet verworfen; ich habe jeden mit pruefe nachgerechnet (Ergebnis jeweils "verworfen"):
- 2014-06, 2016-01, 2017-11, 2018-08, 2019-05, 2021-09, 2022-09, 2022-11, 2023-02, 2023-05, 2023-11, 2024-07, 2025-07, 2025-08

Die Kandidaten des früheren Laufs (2018-08..2018-08 und 2023-02..2023-02) sind beide verworfen: S_folgeniveau bzw. R3_stuetzung_duenn.

Es fehlt keine regelkonforme, definitionsgemäße Stelle. satz mit leerer Auswahl: anzahl 0, anzahl_ok true, ok true. Die Reihe bleibt ohne Eintrag; das ist ein gültiges Ergebnis. Es wurde keine Datei geändert.


## Karlsruher Institut für Technologie (ID 14, 27 bewertete Monate)

**Ergebnis:** 0 Einträge, 0 Zweifelsfälle für Stufe B.


**Auswahl (Annotator):** Reihe KIT (ID 14), Mitarbeitende, Gesamtbewertung, 27 bewertete Monate, sehr lückig (Vorniveaus über 13 bis 63 Kalendermonate verteilt, überwiegend dünne Monate mit 5-9 Bewertungen). Der Scan meldet 0 regelkonforme Zeiträume und 0 Zweifelsfälle. Alle in der Tabelle auffälligen Stellen habe ich definitionsgemäß abgegrenzt und mit pruefe nachgerechnet: 2017-11 und 2018-05/06 (Vorniveau unter drei bewerteten Monaten), Abfall 2018-07 bis 2018-08 (Δ -0,34, kein Bleiben auf neuem Niveau, dünne Monate ohne Stützung), Anstieg 2021-12 bis 2022-01 (Δ +0,43, Vortrend +0,37 deutet auf allmähliche Bewegung, danach Rückkehr bzw. kein stabiles Folgeniveau), 2022-09 (Δ -0,50, aber Einzelmonatssprung mit sofortiger Rückkehr 2022-10), 2024-08, 2024-09 und 2025-02 (Δ 0,31-0,37, jeweils Einzelmonate mit Rückkehr), 2023-05 und 2025-08/09 (Δ unter 0,30). Keine Variante ist regelkonform. Kein Zweifelsfall: Jeder Kandidat im Bereich 0,30-0,49 scheitert zusätzlich an der Folgeniveau-Setzung und/oder der Stützung dünner Monate, ist also nicht "sonst regelkonform". Ergebnis nach Regel 5: 0 Zeiträume (satz mit leerer Auswahl: ok). Eine Reihe ohne Zeitraum ist ein gültiges Ergebnis.

**Verworfene Kandidaten (14):**

- 2017-11 bis 2017-11 (fall): Setzung Vorniveau mindestens drei bewertete Monate; zudem Einzelmonat mit Rückkehr. Vorniveau nur 1 bewerteter Monat (2013-05=4,087, n=8); Monat 3,14 (n=5); erste Folgemonate 2018-05=4,025, 2018-06=4,033: altes Niveau kehrt zurück
- 2018-05 bis 2018-06 (rise): Setzung Vorniveau mindestens drei bewertete Monate. Vorniveau nur 2 bewertete Monate (2013-05, 2017-11); Länge 2
- 2018-07 bis 2018-08 (fall, definitionsgemäße Abgrenzung des Abfalls 2018): R4 (Zweifelsbereich), Setzung Folgeniveau (a)/(b), Stützung dünner Monate. Vorniveau 3,82125 (2013-05 bis 2018-06, n=5-8), Niveau 3,4845, Δ -0,33675; Folgemittel-Abstand 0,0349 < verlangt 0,1684; erster Folgemonat 2019-05=3,576 (n=17), Abstand 0,2452 < 0,25; 2018-07 (n=7) und 2018-08 (n=6) ohne Stützung. Kein Zweifelsfall, da außer R4 weitere Regeln scheitern
- 2018-07 bis 2018-07 (fall, Variante): R4, Stützung dünner Monate. Δ -0,23525 (< 0,30); 2018-07 (n=7) ohne Stützung
- 2018-08 bis 2018-08 (fall, Variante): R4 (Zweifelsbereich), Setzung Folgeniveau (a)/(b), Stützung dünner Monate. Vorniveau 3,7742, Niveau 3,383, Δ -0,3912; Folgemittel-Abstand -0,0121 < 0,1956; erster Folgemonat 2019-05 Abstand 0,1982 < 0,25; 2018-08 (n=6) ohne Stützung
- 2018-07 bis 2019-05 (fall, lange Variante): R2 Länge, R3 innen, R4, Folgeniveau, Stützung. Länge 11 Kalendermonate > 6; mehr als ein nicht bewerteter Monat innen; Δ -0,30625
- 2021-12 bis 2022-01 (rise, definitionsgemäße Abgrenzung): R4 (Zweifelsbereich), Setzung Folgeniveau (a)/(b), Stützung dünner Monate, Trendhinweis Regel 2. Vorniveau 3,7018 (2018-07 bis 2021-11, n=5-17), Niveau 4,135, Δ +0,43317; Vortrend +0,37 (Vorniveau steigt bereits gleichmäßig von 3,38/3,58 über 3,84/3,94/3,88: Trendverdacht); Folgemittel-Abstand 0,1302 < 0,2166; erster Folgemonat 2022-09=3,417 (n=6), Abstand -0,2848 (Rückkehr); 2021-12 (n=5) ohne Stützung. Kein Zweifelsfall
- 2021-12 bis 2021-12 (rise, Variante): R4 (Zweifelsbereich), Setzung Folgeniveau (a), Stützung dünner Monate. Δ +0,45817; Folgemittel-Abstand 0,1572 < 0,2291; 2021-12 (n=5) ohne Stützung; Vortrend +0,37
- 2022-09 bis 2022-09 (fall): Einzelmonatssprung mit Rückkehr: Setzung Folgeniveau (a)/(b), Stützung dünner Monate. Vorniveau 3,9187 (2019-05 bis 2022-01, n=5-17), Monat 3,417 (n=6), Δ -0,50167 (R4 erfüllt); Folgemonat 2022-10=4,05 (Abstand -0,1313), Folgemittel 3,9597 (Abstand -0,041 < 0,2508): altes Niveau kehrt sofort zurück; 2022-09 (n=6) ohne Stützung
- 2023-05 bis 2023-05 (rise): R4, Folgeniveau, Stützung dünner Monate. Δ +0,29233 (< 0,30); 2023-05 (n=5) ohne Stützung
- 2024-08 bis 2024-08 (rise): R4 (Zweifelsbereich), Setzung Folgeniveau (a)/(b), Stützung dünner Monate. Vorniveau 3,8932 (2023-01 bis 2024-03), Monat 4,233 (n=9), Δ +0,33983; erster Folgemonat 2024-09=3,614, Abstand -0,2792 (Rückkehr); Folgemittel-Abstand -0,1945 < 0,1699; 2024-08 (n=9) ohne Stützung
- 2024-09 bis 2024-09 (fall): R4 (Zweifelsbereich), Setzung Folgeniveau (a)/(b), Stützung dünner Monate. Vorniveau 3,9272 (2023-02 bis 2024-08), Monat 3,614 (n=7), Δ -0,31317; erster Folgemonat 2025-01=3,99, Abstand -0,0628 (Rückkehr); Folgemittel-Abstand 0,1378 < 0,1566; 2024-09 (n=7) ohne Stützung
- 2025-02 bis 2025-02 (fall): R4 (Zweifelsbereich), Setzung Folgeniveau (a)/(b). Vorniveau 3,8578 (2023-11 bis 2025-01, n=6-10), Monat 3,492 (n=13), Δ -0,36583; erster Folgemonat 2025-08=3,886, Abstand -0,0282 (Rückkehr); Folgemittel 4,033, Abstand -0,1752 < 0,1829
- 2025-08 bis 2025-09 (rise): R4, Stützung dünner Monate. Δ +0,1935 (< 0,30); 2025-08 (n=7), 2025-09 (n=9) ohne Stützung

**Widerlegungsversuche (Prüfer):** Der Annotator hat keine Einträge. Deshalb habe ich versucht, sein Ergebnis von 0 Zeiträumen zu widerlegen. Dazu habe ich jeden seiner Kandidaten und zusätzlich alle Paare bewerteter Monate bis 6 Kalendermonate Länge mit pruefe nachgerechnet. Keine Variante ist regelkonform.

Einzelne Stellen:
- 2017-11: Vorniveau hat nur 1 bewerteten Monat (S_vorniveau_min3).
- 2018-05 und 2018-05 bis 2018-06: Vorniveau hat nur 2 bewertete Monate. Das gilt auch für 2018-05 bis 2018-07 und 2018-05 bis 2018-08.
- Abfall 2018-07 bis 2018-08, definitionsgemäße Abgrenzung: Δ -0,3368 liegt im Zweifelsbereich. Die Folgeniveau-Setzung ist nicht erfüllt: Folgemittel-Abstand 0,0349 bei verlangt 0,1684; erster Folgemonat 2019-05 mit Abstand 0,2452 < 0,25. 2018-07 (n=7) und 2018-08 (n=6) haben keine Stützung. Die Varianten 2018-07 (Δ -0,24) und 2018-08 (Δ -0,39) scheitern ebenfalls an R4 und Stützung, 2018-08 zusätzlich am Folgeniveau. Damit ist es weder Eintrag noch Zweifelsfall.
- Anstieg 2021-12 bis 2022-01: Δ +0,4332 im Zweifelsbereich. Vortrend +0,37, also Trendverdacht nach Regel 2. Folgeniveau nicht erfüllt: Abstand 0,1302 < 0,2166; erster Folgemonat 2022-09 mit Abstand -0,2848, also Rückkehr. 2021-12 (n=5) hat keine Stützung. Die Varianten 2021-12 (Δ +0,46), 2022-01 (Δ +0,31) und 2021-11 bis 2022-01 (Δ +0,32) scheitern ebenso am Folgeniveau.
- 2022-09: Δ -0,5017 erfüllt R4. Es ist aber ein Einzelmonatssprung mit sofortiger Rückkehr: 2022-10 = 4,05, Folgemittel-Abstand -0,041. 2022-09 (n=6) hat keine Stützung. Damit ist der Fall nach Regel 4 ausdrücklich ausgeschlossen. Die Verlängerungen bis 2022-10, 2023-01 und 2023-02 haben Δ unter 0,30 und mehr als einen nicht bewerteten Monat innen.
- 2024-08 (Δ +0,34), 2024-09 (Δ -0,31) und 2025-02 (Δ -0,37): jeweils Einzelmonat mit Rückkehr, Folgeniveau-Setzung nicht erfüllt. 2024-08 und 2024-09 haben außerdem keine Stützung.
- 2023-05 (Δ +0,29), 2025-08 bis 2025-09 (Δ +0,19), 2025-09 (Δ +0,27) und 2026-03 (Δ +0,19, ohne Folgemonat, also nicht prüfbar) scheitern an R4.

Die Zahlen des Annotators stimmen mit pruefe überein: Vorniveaus, Δ, Folgemittel-Abstände, erste Folgemonate und Vortrend.

Zweifelsfälle: Kein Kandidat mit |Δ| 0,30-0,49 ist sonst regelkonform. Jeder scheitert zusätzlich mindestens an S_folgeniveau, so auch 2025-02 und 2022-01, die nur an R4 und S_folgeniveau scheitern. Der Annotator hat zu Recht keinen Zweifelsfall eingetragen.

Regel 5: satz mit leerer Auswahl ergibt ok (anzahl 0).

Ergebnis: Das Ergebnis des Annotators ist nicht widerlegt.

**Vollständigkeit (Prüfer):** Der Scan meldet 0 regelkonforme Zeiträume in 0 Gruppen und 0 Zweifelsfälle in 0 Gruppen. Es gibt also keine Scan-Gruppe, die behandelt werden müsste.

Zusätzlich habe ich alle Paare bewerteter Monate (27 Monate) bis 6 Kalendermonate Länge mit pruefe nachgerechnet. Ergebnis: durchweg "verworfen", keine regelkonforme Variante.

Die Tabelle zeigt folgende auffälligen Stellen. Alle hat der Annotator begründet verworfen, und ich habe sie bestätigt:
- 2017-11
- 2018-05/06
- 2018-07/08
- 2021-12/2022-01
- 2022-09
- 2023-05
- 2024-08
- 2024-09
- 2025-02
- 2025-08/09

2026-03 hat keinen Folgemonat, ist also nicht prüfbar und hat Δ +0,19. Diese Stelle hat der Annotator nicht eigens erwähnt; sie ist für das Ergebnis unerheblich.

Der frühere Lauf hatte keine Kandidaten (leere Liste), also war nichts zusätzlich zu prüfen.

Endergebnis: 0 Einträge, 0 Zweifelsfälle, satz ok. Eine Reihe ohne Zeitraum ist ein gültiges Ergebnis.


## Technische Universität München (ID 15, 13 bewertete Monate)

**Ergebnis:** 0 Einträge, 0 Zweifelsfälle für Stufe B.


**Auswahl (Annotator):** Reihe mit nur 13 bewerteten Monaten (2018-05, 2018-06, 2019-05, 2019-07, 2019-08, 2022-10, 2023-11, 2024-02, 2024-03, 2024-09, 2025-01, 2025-02, 2025-08), weit verstreut, meist mit 5-8 Bewertungen und großen grauen Lücken. Der Scan fand 0 regelkonforme Zeiträume und 0 Zweifelsfälle. Alle auffälligen Stellen wurden einzeln mit pruefe nachgerechnet: Die beiden Stellen mit |Δ| >= 0,5 (2023-11 +0,61 und 2024-03 -0,61) sind einzelne Monatsausschläge mit n=5, nach denen das alte Niveau sofort zurückkehrt (Setzung (a)/(b) und Stützung scheitern; Regel 4: einzelner Monatssprung reicht nicht). 2018-06 hat kein ausreichendes Vorniveau (1 bewerteter Monat). Die übrigen Kandidaten (2019-07, 2022-10, 2024-02 bis 2024-03, 2024-09, 2025-08) liegen unter 0,5 bzw. unter 0,30 und scheitern zusätzlich an Folgeniveau-Setzungen oder fehlendem Folgemonat; damit sind sie nicht "sonst regelkonform" und werden auch nicht als Zweifelsfall geführt. Ein gleichmäßiger Trend über mehr als sechs Monate ist nicht erkennbar (das Niveau schwankt um etwa 3,7-3,9 ohne Richtung). Ergebnis: Reihe ohne Eintrag (gültiges Ergebnis); satz mit leerer Auswahl: anzahl 0, ok.

**Verworfene Kandidaten (9):**

- 2018-06 bis 2018-06: Setzung Vorniveau mindestens drei bewertete Monate. Vorniveau nur 1 bewerteter Monat (2018-05: 4,314, n=14); 2018-06: 3,646 (n=13); Diff laut Tabelle -0,67; ergebnis verworfen
- 2019-07 bis 2019-07: R4 (Zweifelsbereich, kein Eintrag), Setzung (a)/(b) Folgeniveau, Stützung dünner Monate. Vorniveau 3,9533 (2018-05 bis 2019-05, n=7-14); Zeitraum 3,462 (n=8); Δ -0,4913; Folgemittel-Abstand 0,0177 < 0,2457; erster Folgemonat 2019-08=3,867 (Abstand 0,0863 < 0,25, Rückkehr); 2019-07 (n=8) ohne Stützung. Nicht als Zweifelsfall aufgenommen, da Setzungen (a)/(b) und Stützung scheitern (nicht sonst regelkonform).
- 2019-07 bis 2019-08: R4 (|Δ| < 0,30), Setzung (a), Stützung dünner Monate. Vorniveau 3,9533; Zeitraum 3,6645 (n=8, 6); Δ -0,2888; Folgemittel-Abstand 0,083 < 0,1444; 2019-07 (n=8) und 2019-08 (n=6) ohne Stützung
- 2022-10 bis 2022-10: R4 (|Δ| < 0,30), Setzung (a)/(b), Stützung dünner Monate. Vorniveau 3,8378 (2018-05 bis 2019-08, n=6-14); Zeitraum 3,54 (n=5); Δ -0,2978; erster Folgemonat 2023-11=4,40 (Abstand -0,5622, Gegenrichtung); Folgemittel-Abstand 0,0808 < 0,1489; 2022-10 (n=5) ohne Stützung
- 2023-11 bis 2023-11: Setzung (a)/(b) Folgeniveau (einzelner Monatssprung, altes Niveau kehrt zurück), Stützung dünner Monate. Vorniveau 3,7882 (2018-05 bis 2022-10, n=5-14); Zeitraum 4,40 (n=5); Δ +0,6118 (R4 erfüllt); erster Folgemonat 2024-02=3,671 (Abstand -0,1172 < 0,25); Folgemittel 3,6303 (Abstand -0,1578 < 0,3059); 2023-11 (n=5) ohne Stützung
- 2024-03 bis 2024-03: Setzung (a)/(b) Folgeniveau (einzelner Monatssprung, altes Niveau kehrt zurück), Stützung dünner Monate. Vorniveau 3,8067 (2019-05 bis 2024-02, n=5-8); Zeitraum 3,20 (n=5); Δ -0,6067 (R4 erfüllt); erster Folgemonat 2024-09=4,02 (Abstand -0,2133, Gegenrichtung); Folgemittel 3,78 (Abstand 0,0267 < 0,3033); 2024-03 (n=5) ohne Stützung
- 2024-02 bis 2024-03: R4 (Zweifelsbereich), Setzung (a)/(b), Stützung dünner Monate. Vorniveau 3,8025 (2018-06 bis 2023-11, n=5-13); Zeitraum 3,4355 (n=7, 5); Δ -0,367; Folgemittel-Abstand 0,0225 < 0,1835; erster Folgemonat 2024-09 Abstand -0,2175 (Gegenrichtung); 2024-03 (n=5) ohne Stützung. Zudem ist 2024-02 (3,671) nicht der erste deutlich abweichende Monat. Kein Zweifelsfall, da nicht sonst regelkonform.
- 2024-09 bis 2024-09: R4 (Zweifelsbereich), Setzung (a)/(b) Folgeniveau. Vorniveau 3,69 (2019-07 bis 2024-03, n=5-8); Zeitraum 4,02 (n=10); Δ +0,33; erster Folgemonat 2025-01=3,66 (Abstand -0,03 < 0,25); Folgemittel 3,5867 (Abstand -0,1033 < 0,165). Kein Zweifelsfall, da Setzungen (a)/(b) scheitern.
- 2025-08 bis 2025-08: R4 (Zweifelsbereich), Setzung (c) kein bewerteter Folgemonat, Stützung dünner Monate. Vorniveau 3,7685 (2023-11 bis 2025-02, n=5-10); Zeitraum 3,44 (n=5); Δ -0,3285; kein bewerteter Monat nach 2025-08 (nicht prüfbar); 2025-08 (n=5) ohne Stützung. Kein Zweifelsfall, da nicht sonst regelkonform.

**Widerlegungsversuche (Prüfer):** Der Annotator hat keine Einträge gesetzt. Ich habe deshalb versucht, sein Leerergebnis zu widerlegen, und jede verworfene Stelle mit pruefe nachgerechnet. Alle Zahlen stimmen mit seinen Angaben überein.

2018-06: wird verworfen, weil das Vorniveau nur einen bewerteten Monat hat (2018-05; Setzung verlangt mindestens 3).

2019-07: Δ -0,4913, das ist ein Zweifelsbereich. Die Stelle scheitert zusätzlich an der Folgeniveau-Setzung (Folgemittel-Abstand 0,0177 < 0,2457). Der erste Folgemonat 2019-08 liegt bei 3,867, nur 0,0863 vom Vorniveau entfernt; das alte Niveau kehrt also zurück. 2019-07 (n=8) hat keine Stützung. Damit ist die Stelle nicht sonst regelkonform und wird kein Zweifelsfall.

2019-07 bis 2019-08: Δ -0,2888 < 0,30; scheitert außerdem an Setzung (a) und an der Stützung.

2022-10: Δ -0,2978 < 0,30. Der Folgemonat 2023-11 weicht in Gegenrichtung ab. Keine Stützung.

2023-11: Δ +0,6118, Regel 4 ist erfüllt. Es ist aber ein Einmonatsausreißer mit n=5: Der erste Folgemonat 2024-02 liegt bei 3,671 (Abstand -0,1172, also Rückkehr), das Folgemittel bei 3,6303 (Abstand -0,1578 < 0,3059). Keine Stützung. Ergebnis: verworfen.

2024-03: Δ -0,6067, Regel 4 ist erfüllt. Auch hier ein Einmonatsausreißer mit n=5: Der erste Folgemonat 2024-09 liegt bei 4,02 (Gegenrichtung), das Folgemittel bei 3,78 (Abstand 0,0267). Keine Stützung. Ergebnis: verworfen.

2024-02 bis 2024-03: Δ -0,367, Zweifelsbereich. Scheitert an der Folgeniveau-Setzung, 2024-03 hat keine Stützung, und 2024-02 ist nicht der erste deutlich abweichende Monat. Kein Zweifelsfall.

2024-09: Δ +0,33, Zweifelsbereich. Scheitert an den Setzungen (a) und (b): Der erste Folgemonat 2025-01 liegt bei 3,66, das ist eine Rückkehr. Kein Zweifelsfall.

2025-08: Δ -0,3285. Es gibt keinen bewerteten Folgemonat, also ist die Stelle nach Setzung (c) nicht prüfbar. Keine Stützung. Kein Zweifelsfall.

Zusätzlich habe ich drei Varianten geprüft, die der Annotator nicht aufführt:
- 2025-01 bis 2025-02: Δ -0,123, scheitert an Regel 4.
- 2023-11 bis 2024-02: Δ +0,247, scheitert an Regel 4, hat zwei nicht bewertete Monate innen (Regel 3) und scheitert an der Folgeniveau-Setzung.
- 2019-07 bis 2019-08: bestätigt die Angaben des Annotators.

Einen Trend über mehr als sechs Monate (Regel 2) gibt es nicht; das Niveau schwankt ohne Richtung um 3,7 bis 3,9. Die Prüfung mit satz bei leerer Auswahl ergibt anzahl 0, ok.

**Vollständigkeit (Prüfer):** Der Scan über die ganze Reihe (13 bewertete Monate) ergibt 0 regelkonforme Zeiträume in 0 Gruppen und 0 Zweifelsfälle (0,30 bis 0,49, sonst regelkonform) in 0 Gruppen. Es gibt also keine Scan-Gruppe, die eingetragen oder begründet verworfen werden müsste. Alle auffälligen Einzelstellen hat der Annotator begründet verworfen, und pruefe bestätigt das: 2018-06, 2019-07, 2019-07 bis 2019-08, 2022-10, 2023-11, 2024-03, 2024-02 bis 2024-03, 2024-09 und 2025-08. Der frühere Lauf hatte keine Kandidaten. Es fehlt keine regelkonforme, definitionsgemäße Stelle. Die Reihe bleibt ohne Eintrag; das ist ein gültiges Ergebnis.


## SAP SE (ID 19, 26 bewertete Monate)

**Ergebnis:** 1 Einträge, 0 Zweifelsfälle für Stufe B.

- Eintrag 2024-07 bis 2024-08, rise, Δ +0.538: Vorniveau 3,1 (2024-01 bis 2024-06, n=6-174); Zeitraum 3,6 (n=12, 12); Δ +0,54; rise; Vorniveau streut stark (2024-01 2,35 mit n=10, 2024-03 4,16 mit n=174, 2024-04 bis 2024-06 nur 2,85 bis 2,99, darin 2024-05 n=8 und 2024-06 n=6); Anstieg läuft bis 2024-09 (3,95) weiter, Folgemittel 3,69; Anker: keiner; Reihe allein.

**Auswahl (Annotator):** Für SAP SE (Mitarbeitende, Gesamtbewertung) gibt es einen Eintrag: 2024-07 bis 2024-08, Anstieg, Δ +0,5385. Der Rechner meldet ihn als regelkonform, und der satz-Check besteht (Anzahl 1). Weitere Einträge gibt es nicht, und es bleibt auch kein Zweifelsfall.

Warum dieser Zeitraum: Von 2024-04 bis 2024-06 liegt die Reihe bei 2,85 bis 2,99. Der erste deutlich abweichende bewertete Monat ist 2024-07 mit 3,50 (n=12). Von dort steigt die Reihe auf 3,717 im August und 3,954 im September und hält danach ein Niveau von etwa 3,5 bis 4,0 (2024-10 bis 2025-07, Folgemittel 3,69). 2024-07 sehe ich als Übergangsmonat. Der erste bewertete Monat auf dem neuen Niveau ist 2024-08 mit 3,717, deshalb ist das period_to.

Längere Varianten bis 2024-09, 2024-10 oder 2024-12 hätten zwar ein größeres Δ (bis +0,665). Sie gehen aber über den ersten Monat auf dem neuen Niveau hinaus und reichen in das Überschießen von 2024-09 hinein. Nach der Abgrenzungsregel scheiden sie deshalb aus. Spätere Starts (2024-08, 2024-09) scheiden aus, weil 2024-07 bereits abweicht.

Trendprüfung nach Regel 2: In den Vormonaten 2024-04 bis 2024-06 ist die Reihe flach, der vortrend im Rechner liegt bei -0,29. Die Bewegung beginnt also erst 2024-07, dauert drei Monate bis 2024-09 und wird dann zum Plateau. Ein gleichmäßiger Trend über mehr als sechs Monate liegt nicht vor.

Einschränkung: Das Vorniveau (Mittel 3,07) streut stark. Es enthält 2024-01 mit 2,35 und die Spitze 2024-03 mit 4,16 (n=174). Gemessen an 2024-04 bis 2024-06 allein wäre der Sprung sichtbar größer. Wer 2024-07 mit 3,50 schon als neues Niveau liest, kommt auf 2024-07..2024-07 mit Δ +0,43. Das wäre nur ein Zweifelsfall, und für diese Stelle gäbe es dann keinen Eintrag.

Die übrigen auffälligen Stellen fallen alle weg:
- 2024-02 und 2024-03: weniger als drei Monate Vorniveau, und 2024-03 ist eine Einzelspitze.
- 2024-04, 2024-12, 2025-01, 2025-08, 2025-10 und 2026-01: Einzelausschläge mit Rückkehr zum alten Niveau, die an Setzung (a) oder (b) bzw. Regel 4 scheitern.
- 2026-05/06: kein bewerteter Folgemonat, damit nach Setzung (c) nicht prüfbar.

Zum Zweifelsfall: Die Zweifelsfall-Varianten aus dem Scan betreffen alle dieselbe Stelle wie der Eintrag. Sie überlappen ihn oder liegen weniger als drei bewertete Monate entfernt und passen daher nicht zu Regel 5. Die anderen Δ im Bereich 0,30 bis 0,49 (2024-04, 2025-01, 2025-08..09, 2026-01) verletzen zusätzlich Setzungen, sind also nicht 'sonst regelkonform'. Deshalb wird kein Zweifelsfall aufgenommen.

Verwendete Dateien: CSV /Users/vaios/EPA-Bachelorarbeit/EPA-Bachelorarbeit/backend/data/series/19_sap_se_employee.csv, Rechner /private/tmp/claude-501/-Users-vaios-EPA-Bachelorarbeit/1503df89-f281-4f80-8ff4-54d8dcdd0ffc/scratchpad/lauf2/dz1_rechner.py.

**Verworfene Kandidaten (25):**

- 2024-07..2024-09: Abgrenzung nach Definition (period_to wäre Überschießen über das neue Niveau, nur größeres Δ); Regel 5 (gleiche Stelle wie Eintrag). Δ +0,6537; Vor 3,070; Niv 3,724; regelkonform laut pruefe
- 2024-07..2024-10: Abgrenzung nach Definition (über den ersten Monat auf neuem Niveau hinaus verlängert); Regel 5 (gleiche Stelle). Δ +0,665; Vor 3,070; Niv 3,735; regelkonform laut pruefe
- 2024-07..2024-12: Abgrenzung nach Definition (verlängert); Regel 5 (gleiche Stelle). Δ +0,587; Vor 3,070; Niv 3,657 (scan)
- 2024-08..2024-09: Abgrenzung nach Definition (period_from nicht der erste abweichende Monat, 2024-07 weicht bereits ab); Regel 5 (überlappend). Δ +0,5738; Vor 3,262; Niv 3,836; regelkonform laut pruefe
- 2024-09..2024-09: Abgrenzung nach Definition (später Beginn, 2024-07 und 2024-08 im Vorniveau); Regel 5 (Abstand zum Eintrag < 3 bewertete Monate). Δ +0,5955; Vor 3,3585; Niv 3,954; regelkonform laut pruefe
- 2024-07..2024-07: Regel 4 Zweifelsfall; Abgrenzung: 2024-07 (3,50) ist Übergangsmonat, erster Monat auf neuem Niveau ist 2024-08; überlappt Eintrag (Regel 5). Δ +0,43; Vor 3,070; Niv 3,500; Ergebnis zweifelsfall_0_3_bis_0_49
- 2024-06..2024-09: Regel 4 Zweifelsfall; Abgrenzung (2024-06 = 2,933 noch altes Niveau); überlappt Eintrag (Regel 5). Δ +0,429; Vor 3,097; Niv 3,526 (scan)
- 2024-08..2024-08: Regel 4 Zweifelsfall; Abgrenzung (später Beginn); überlappt Eintrag (Regel 5). Δ +0,455; Vor 3,262; Niv 3,717 (scan)
- 2024-08..2024-12: Regel 4 Zweifelsfall; Abgrenzung; überlappt Eintrag (Regel 5). Δ +0,434; Vor 3,262; Niv 3,696 (scan)
- 2024-08..2025-01: Regel 4 Zweifelsfall; Abgrenzung; überlappt Eintrag (Regel 5). Δ +0,494; Vor 3,262; Niv 3,755 (scan)
- 2024-09..2024-12: Regel 4 Zweifelsfall; Abgrenzung; Abstand zum Eintrag < 3 bewertete Monate (Regel 5). Δ +0,330; Vor 3,358; Niv 3,689 (scan)
- 2024-10..2025-01: Regel 4 Zweifelsfall; kein eigener Sprung (Fortsetzung des Niveaus nach 2024-07/08); Abstand zum Eintrag < 3 bewertete Monate (Regel 5). Δ +0,377; Vor 3,324; Niv 3,702 (scan)
- 2024-02..2024-02: Setzung Vorniveau mindestens drei bewertete Monate. Vorniveau nur 1 bewerteter Monat (2024-01 = 2,35); 2024-02 = 3,136
- 2024-02..2024-03: Setzung Vorniveau mindestens drei bewertete Monate; zudem Rückkehr 2024-04 (2,854). Vorniveau 1 bewerteter Monat; Folgemonate 2,854 / 2,987 / 2,933
- 2024-03..2024-03: Setzung Vorniveau mindestens drei bewertete Monate; Einzelspitze (Regel 4: altes Niveau kehrt zurück). Vorniveau 2 bewertete Monate; 2024-03 = 4,16 (n=174), 2024-04 = 2,854
- 2024-04..2024-04: Regel 4 (Zweifelsbereich) und Setzungen (a)/(b) nicht erfüllt. Δ -0,3613; Vor 3,2153; Folgemittel-Abstand 0,0753 < 0,1807; erster Folgemonat 2024-05 2,987 Abstand 0,2283 < 0,25
- 2024-04..2024-06: Regel 4 (|Δ| < 0,30); Setzungen (a)/(b); Stützung dünner Monate. Δ -0,2907; Folgemittel 3,7237 (Gegenrichtung); 2024-05 (n=8), 2024-06 (n=6) ohne Stützung
- 2024-12..2024-12: Regel 4 (|Δ| < 0,30); Setzungen (a)/(b); Stützung dünn (n=7). Δ -0,1337; Vor 3,4767; Folgemonat 2025-01 3,993 (Gegenrichtung)
- 2025-01..2025-01: Regel 4 (Zweifelsbereich) und Setzungen (a)/(b): Einzelspitze, altes Niveau kehrt zurück. Δ +0,457; Vor 3,536; Folgemittel-Abstand 0,0123 < 0,2285; erster Folgemonat 2025-02 3,618 Abstand 0,082
- 2025-08..2025-08: Setzung (a): Einzelspitze, Niveau bleibt nicht (Regel 4 Einzelsprung). Δ +0,6328; Vor 3,5672; Folgemittel 3,4957 (Abstand -0,0715 < 0,3164)
- 2025-08..2025-09: Regel 4 (Zweifelsbereich) und Setzungen (a)/(b): Rückfall 2025-10. Δ +0,4978; Folgemittel-Abstand -0,0482; erster Folgemonat 2025-10 2,957 Abstand -0,6102
- 2025-10..2025-10: Setzungen (a)/(b): Einzelsenke, altes Niveau kehrt zurück; Stützung dünn (n=7). Δ -0,7777; Vor 3,7347; Folgemittel 3,7777; erster Folgemonat 2025-11 3,600 Abstand 0,1347
- 2026-01..2026-01: Regel 4 (Zweifelsbereich); Setzung (b); Stützung dünn (n=8). Δ +0,3488; Vor 3,6512; erster Folgemonat 2026-03 3,733 Abstand 0,0818 < 0,25
- 2026-05..2026-06: Setzung (c): kein bewerteter Folgemonat, nicht prüfbar. Δ +0,5888; Vor 3,7367; Niv 4,3255; Folgemonate keine
- 2026-06..2026-06: Setzung (c): kein bewerteter Folgemonat, nicht prüfbar; Vorniveau bewegt sich bereits in Sprungrichtung (+0,43). Δ +0,9092; Vor 3,7088; Niv 4,618 (n=11); Folgemonate keine

**Widerlegungsversuche (Prüfer):** Eintrag 2024-07..2024-08 (rise, Δ +0,5385). Nachgerechnet mit pruefe: Ergebnis "regelkonform". Alle Regeln sind erfüllt: Länge 2 (R2), Ränder n=12/12 (R3), keine Lücke im Zeitraum, Vorniveau 6 bewertete Monate (Setzung), |Δ| 0,5385 >= 0,5 (R4). Setzung (a): Folgemittel 3,6887, Abstand 0,6187 >= 0,2692. Setzung (b): erster Folgemonat 2024-09 = 3,954, Abstand 0,884 >= 0,25. Im Zeitraum liegt kein Monat mit 5-9 Bewertungen, eine Stützung ist also nicht nötig.

(1) Abgrenzungsangriff A, 2024-07 schon auf dem neuen Niveau: Dann wäre die definitionsgemäße Abgrenzung 2024-07..2024-07 mit Δ +0,43. Das wäre nur ein Zweifelsfall (pruefe: zweifelsfall_0_3_bis_0_49, nur R4 verfehlt), und die Stelle bekäme keinen Eintrag. Für diese Lesart spricht, dass das spätere Plateau 2025-02 bis 2025-07 bei 3,51-3,62 liegt und 3,50 in dieses Band fällt. Dagegen sprechen die unmittelbar folgenden Monate 2024-08 bis 2024-10 (3,717 / 3,954 / 3,769). Ihr Mittel liegt bei etwa 3,81, und das Folgemittel nach 2024-07 laut scan bei 3,8133. 2024-07 liegt damit rund 0,3 unter dem unmittelbar erreichten neuen Niveau, und die Reihe steigt noch zwei Monate weiter. 2024-08 mit 3,717 trifft das Folgemittel 3,69 dagegen fast genau. Beide Lesarten sind vertretbar. Der Annotator hat die Alternative ausdrücklich benannt und in der Begründung offengelegt. Er hat außerdem nicht die Variante mit dem größten Δ gewählt (das wäre 07..10 mit +0,665), sondern die kürzeste Variante mit inhaltlicher Begründung. Eine Regel, die die Änderung zwingend verlangt, gibt es nicht. Nach "im Zweifel bleibt das Ergebnis des Annotators" bleibt der Eintrag.

(2) Abgrenzungsangriff B, 2024-07..2024-09 aus dem früheren Lauf (pruefe: regelkonform, Δ +0,6537): 2024-09 mit 3,954 ist der Höchstwert über dem späteren Niveau, also ein Überschießen. Der erste Monat auf dem neuen Niveau ist spätestens 2024-08. Die Verlängerung bis 09 würde nur Δ erhöhen. Sie wird zu Recht verworfen. Dasselbe gilt für 07..10 und 07..12. Spätere Starts (08..09, 09..09) scheiden aus, weil 2024-07 schon deutlich abweicht: 3,50 gegenüber 2,85-2,99 in 2024-04 bis 2024-06.

(3) Trend (R2): 2024-04 bis 2024-06 sind flach (vortrend -0,29, also eher fallend). Der Anstieg dauert 3 Monate (07 bis 09), danach folgt ein Plateau. Das ist kein Trend über mehr als 6 Monate.

(4) Einmonatsausreißer mit Rückkehr: Nein. Die Folgemonate 3,954 / 3,769 / 3,343 (n=7) und danach 3,99 und 3,5-3,6 bis 2025-07 liegen alle über dem Vorniveau 3,07. Das alte Niveau von etwa 2,9 kehrt nicht zurück.

(5) Regel 5: satz 2024-07:2024-08 ergibt anzahl 1, ok=true. Es gibt nicht mehr als drei Stellen, ein Schwankungshinweis nach Regel 5 ist also nicht nötig.

(6) note nach Regel 11: Reihenfolge und Zahlen entsprechen dem note_geruest aus pruefe (Vorniveau 3,1, 2024-01 bis 2024-06, n=6-174; Zeitraum 3,6, n=12, 12; Δ +0,54; rise). Auch die Zahlen im Streuungshinweis stimmen mit der Tabelle überein: 2,35 n=10; 4,16 n=174; 2,854-2,987; n=8; n=6; 3,954; Folgemittel 3,6887. Die Dezimalkommas sind korrekt, der Hinweis steht vor "Anker: keiner; Reihe allein." Im Zeitraum gibt es keinen dünnen Monat. Die Nennung der dünnen Vorniveau-Monate ist zusätzlich und nicht falsch. delta 0,5385 und direction rise sind identisch mit pruefe.

Gegenproben zu den verworfenen Stellen (pruefe): 2026-05..06 verworfen (S_folgeniveau, kein Folgemonat), 2026-06..06 verworfen (S_folgeniveau), 2025-08..08 verworfen (S_folgeniveau), 2025-10..10 verworfen (S_folgeniveau, Stützung dünn), 2025-08..09 verworfen (R4, S_folgeniveau), 2026-01..01 verworfen (R4, S_folgeniveau, Stützung dünn), 2025-01..01 verworfen (R4, S_folgeniveau). Die Angaben des Annotators bestätigen sich durchweg.

**Vollständigkeit (Prüfer):** Der scan ergibt 6 regelkonforme Zeiträume in 1 Gruppe: 2024-07..08, 07..09, 07..10, 07..12, 08..09 und 09..09. Die Gruppe ist durch den Eintrag 2024-07..2024-08 abgedeckt, der als definitionsgemäße Variante gewählt wurde. Die übrigen fünf Varianten sind nach der Abgrenzung (Verlängerung ins Überschießen oder späterer Start) und nach Regel 5 (Überlappung) begründet verworfen.

Dazu kommen 7 Zweifelsfälle (0,30-0,49) in 1 Gruppe: 2024-06..09, 07..07, 08..08, 08..12, 08..2025-01, 09..12 und 2024-10..2025-01. Alle betreffen dieselbe Stelle und überlappen den Eintrag oder liegen weniger als drei bewertete Monate davon entfernt. Mit dem endgültigen Eintrag sind sie nach Regel 5 nicht vereinbar, daher gibt es keinen Zweifelsfall.

Stellen außerhalb des scans sind vom Annotator begründet verworfen und hier mit pruefe gegengeprüft:
- 2024-02 und 2024-03: Vorniveau unter 3 Monaten, 2024-03 ist eine Einzelspitze.
- 2024-04 und 2024-04..06: R4 bzw. Setzungen.
- 2024-12: R4 und Setzungen.
- 2025-01, 2025-08, 2025-08..09, 2025-10 und 2026-01: Einzelausschläge, Setzung (a)/(b) bzw. R4.
- 2026-05..06 und 2026-06: Setzung (c), kein bewerteter Folgemonat.

Der Kandidat des früheren Laufs (2024-07..2024-09) ist regelkonform, aber nicht definitionsgemäß abgegrenzt, weil er ins Überschießen 2024-09 verlängert wäre. Er ist durch den Eintrag an derselben Stelle ersetzt. Eine fehlende regelkonforme, definitionsgemäße Stelle gibt es nicht. Endergebnis: 1 Eintrag, 0 Zweifelsfälle, keine Änderung gegenüber dem Annotator.


## NTT DATA SE (ID 20, 40 bewertete Monate)

**Ergebnis:** 1 Einträge, 1 Zweifelsfälle für Stufe B.

- Eintrag 2020-06 bis 2020-06, rise, Δ +0.950: Vorniveau 2,8 (2019-05 bis 2020-02, n=5-10); Zeitraum 3,7 (n=5); Δ +0,95; rise; dünner Monat 2020-06 (n=5), gestützt durch 2020-07 (4,05, n=6); Anker: keiner; Reihe allein.
- Zweifelsfall 2024-03 bis 2024-03, fall, Δ -0.486: R4_groesse -0,4865 liegt im Zweifelsbereich 0,30-0,49. Alle übrigen Regeln und Setzungen sind erfüllt (pruefe: zweifelsfall_0_3_bis_0_49; Folgemittel 3,69, Abstand 0,2965 >= 0,2432; erster Folgemonat 2024-07=3,40, Abstand 0,5865; der dünne Monat 2024-03 wird durch 2024-07 gestützt). Die Abgrenzung ist definitionsgemäß: 2023-11 weicht nur -0,15 ab, also ist 2024-03 der erste abweichende Monat und liegt schon auf dem Folgeniveau. Mit dem Eintrag 2020-06 nach Regel 5 vereinbar (satz: 10 bewertete Monate dazwischen, ok). Das Bleiben ist schwach, weil 2024-09 mit 4,02 wieder am Vorniveau liegt. Entscheidung erst in Stufe B mit Ereignisanker.

**Auswahl (Annotator):** Reihe 20 (NTT DATA SE, Mitarbeitende, Gesamtbewertung, 40 bewertete Monate), Stufe A nur aus der Reihe. Der Scan liefert 6 Gruppen regelkonformer Varianten (2018, 2019, 2020, 2021-03, 2021-07, 2021-12) und 4 Gruppen von Zweifelsfällen. Nach definitionsgemäßer Abgrenzung bleibt ein Eintrag: 2020-06..2020-06, rise, Δ +0,9497 (pruefe regelkonform, satz ok). 2020-06 ist der erste deutlich abweichende bewertete Monat nach dem niedrigen Niveau 2019-07 bis 2020-02 (2,5/2,74/2,811/2,371/2,3) und liegt bereits auf dem neuen Niveau (2020-07 4,05, 2021-03 3,74, 2021-07 4,211). Regel 2: kein Vorlauf in Sprungrichtung (Vortrend -0,55), es ist ein Sprung, kein Trend. Die Gruppen 2021-03, 2021-07 und 2021-12 sind keine eigenen Sprünge. Ihr Δ entsteht, weil das Sechs-Monats-Vorfenster noch Monate vor dem Sprung 2020-06 enthält (Vortrend-Hinweise +0,72/+1,34/+1,20). Der weitere Anstieg bis 2022-01 verläuft allmählich. 2021-03 und 2021-07 liegen zudem nach Regel 5 zu nah an 2020-06 und lassen sich nicht in höchstens sechs Kalendermonaten zusammenfassen. Bei der Stelle 2018 ist 2018-04 (-0,17) nicht deutlich abweichend. Die definitionsgemäße Abgrenzung 2018-05..2018-06 scheitert an Setzung (a) und an der Stützung (Rückkehr 2019-03..2019-05). Die regelkonformen Varianten ab 2018-04 bestehen nur durch die Verlängerung, daher kein Eintrag. Bei der Stelle 2019 ist die definitionsgemäße Abgrenzung 2019-07..2019-07 (Δ -0,7273). Sie scheitert an der Stützung des dünnen Monats (2019-08 nur 0,4873 vom Vorniveau). 2019-07..2019-09 wäre eine Verlängerung und läge nach Regel 5 ohnehin zu nah an 2020-06, daher kein Eintrag. Mit nur einem Eintrag greift die Kappung nach Regel 5 nicht, deshalb kein Schwankungshinweis in der note. Ein Zweifelsfall wird aufgenommen: 2024-03..2024-03 (Δ -0,4865, sonst regelkonform, definitionsgemäß einmonatig, mit 2020-06 nach Regel 5 vereinbar, satz ok mit 10 bewerteten Monaten Abstand). Die übrigen Zweifelsfall-Gruppen (2018, 2019, 2025) sind nicht definitionsgemäß abgegrenzt bzw. nach Regel 5 unvereinbar. Ihre definitionsgemäßen Varianten scheitern an Setzungen. Alle Zahlen stammen aus dz1_rechner.py (tabelle, scan, pruefe, satz). Keine Datei im Repository wurde geändert.

**Verworfene Kandidaten (27):**

- 2018-04..2018-06: Abgrenzung nach Definition (period_from) / Regel 2 Hinweis. pruefe regelkonform, Δ -0,6668 (Vor 3,702 aus 2016-06 bis 2018-02, Niveau 3,035). 2018-04 (3,529, n=7) weicht laut Tabelle nur -0,17 vom Vorniveau ab und liegt in der Spanne des alten Niveaus (2017-07 3,667, 2017-10 3,68); erster deutlich abweichender Monat ist 2018-05 (3,237, Δ allein -0,372). Regelkonform nur durch Einschluss von 2018-04 (verschiebt das Vorfenster auf 2016-06 = 4,088), also verlängert, damit Regeln bestehen. Zusätzlich Hinweis Vortrend -0,38 (Vorniveau sinkt bereits) und Rückkehr 2019-03..2019-05 (3,6/3,437/3,9). Definitionsgemäße Abgrenzung 2018-05..2018-06 besteht die Regeln nicht, daher kein Eintrag für diese Stelle.
- 2018-04..2018-07: Abgrenzung nach Definition (period_from und period_to). pruefe regelkonform, Δ -0,6339 (Vor 3,702, Niveau 3,068, Folgemittel 3,319). Wie 2018-04..2018-06: 2018-04 nicht deutlich abweichend (-0,17); außerdem ist 2018-07 (3,167) nicht der erste Monat auf dem neuen Niveau (2018-06 2,34 schon dort). Vortrend -0,38.
- 2018-05..2018-06: Setzung (a) Folgeniveau und Setzung Stützung dünner Monate (definitionsgemäße Abgrenzung der Stelle 2018). Δ -0,8205 (Vor 3,609 aus 2017-06 bis 2018-04, Niveau 2,7885); Folgemittel 3,229, Abstand 0,38 < verlangt 0,4103; 2018-06 (n=5) ohne Stützung (2018-07 3,167 nur 0,442 vom Vorniveau). Ergebnis verworfen; nach Vorgabe kein Eintrag für diese Stelle.
- 2018-05..2018-07: Setzung (a) Folgeniveau. Δ -0,6943 (Vor 3,609, Niveau 2,9147); Folgemittel 3,319, Abstand 0,29 < verlangt 0,3472 (Rückkehr 2019-03 3,6, 2019-04 3,437).
- 2018-06..2018-06: Setzung (a) Folgeniveau, Stützung dünner Monate. Δ -1,1557 (Vor 3,4957, Niveau 2,34, n=5); Folgemittel 3,229, Abstand 0,2667 < verlangt 0,5778; 2018-06 (n=5) keine Stützung (2018-07 Abstand 0,3287).
- 2018-06..2018-07: Setzung (a) Folgeniveau. Δ -0,7422 (Vor 3,4957, Niveau 2,7535); Folgemittel 3,319, Abstand 0,1767 < verlangt 0,3711.
- 2018-02..2018-06, 2018-02..2018-07, 2018-04..2018-05, 2018-05..2018-05 (Zweifelsfälle): Abgrenzung nach Definition / Regel 2. Δ -0,4697 / -0,4909 / -0,3192 / -0,372. 2018-02 (3,986) liegt über dem Vorniveau 3,7427 und weicht nicht ab, Vortrend -0,67; 2018-04 nicht deutlich abweichend (-0,17); 2018-05 (3,237) ist Übergangsmonat zwischen Vorniveau 3,609 und Folgeniveau 2,809, nicht erster Monat auf dem neuen Niveau. Definitionsgemäße Variante 2018-05..2018-06 hat Δ -0,8205 und scheitert an Setzungen, ist also kein Zweifelsfall.
- 2019-07..2019-07: Setzung Stützung dünner Monate (definitionsgemäße Abgrenzung der Stelle 2019). Δ -0,7273 (Vor 3,2273 aus 2018-06 bis 2019-05, Niveau 2,5, n=8); S_folgeniveau erfüllt (Folgemittel 2,6407); aber 2019-07 (n=8) ohne Stützung: erster Folgemonat 2019-08 (2,74) nur 0,4873 vom Vorniveau (< 0,5). 2019-07 ist erster abweichender Monat und liegt schon auf dem neuen Niveau (2019-08 2,74, 2019-09 2,811, 2019-12 2,371, 2020-02 2,3). Ergebnis verworfen, daher kein Eintrag für diese Stelle.
- 2019-07..2019-08: Abgrenzung nach Definition (period_to) / Setzung Stützung. Δ -0,6073; 2019-07 (n=8) ohne Stützung (2019-08 2,74 und Folgemonat 2019-09 2,811 unter 0,5 Abstand); 2019-08 ist nicht erster Monat auf dem neuen Niveau.
- 2019-07..2019-09: Abgrenzung nach Definition (period_to) / Regel 5. pruefe regelkonform, Δ -0,5437 (Vor 3,2273, Niveau 2,6837). Verlängerung bis 2019-09 ist nicht definitionsgemäß (2019-07 schon auf dem neuen Niveau); erst durch die Verlängerung wird 2019-12 (2,371) erster Folgemonat und stützt den dünnen Monat 2019-07. Zudem Regel 5: satz 2019-09..2020-06 nur 2 bewertete Monate dazwischen (nicht ok); Zusammenfassen 2019-07..2020-06 wären 12 Kalendermonate > 6, deutlicher ist 2020-06 (Δ +0,9497 gegen -0,5437).
- 2019-08..2019-09, 2019-09..2019-09 (Zweifelsfälle): Abgrenzung nach Definition (period_from) / Regel 5. Δ -0,4785 / -0,3718. Beginn nach dem ersten abweichenden Monat 2019-07, also nicht definitionsgemäß; Vortrend bei 2019-09 -0,27; mit 2020-06 nach Regel 5 nicht vereinbar (nur 2019-12, 2020-02 dazwischen).
- 2020-06..2020-07: Abgrenzung nach Definition (period_to). pruefe regelkonform, Δ +1,1147 (Vor 2,7703, Niveau 3,885). 2020-06 (3,72) liegt bereits auf dem neuen Niveau (vgl. 2021-03 3,74; Folgemittel nach 2020-06 4,0003); Verlängerung auf 2020-07 vergrößert nur Δ. Gewählt: 2020-06..2020-06.
- 2020-07..2020-07: Abgrenzung nach Definition (period_from). pruefe regelkonform, Δ +1,3097 (Vor 2,7403 mit 2020-06 im Vorfenster). Erster deutlich abweichender Monat ist 2020-06 (+0,95), nicht 2020-07; größeres Δ ist kein Auswahlgrund.
- 2021-03..2021-03: kein eigener Sprung (Vorfenster überspannt den Sprung 2020-06) / Regel 5. pruefe regelkonform, Δ +0,7413 (Vor 2,9987 aus 2019-08 bis 2020-07); Hinweis Vortrend +0,72. 2021-03 (3,74) liegt auf dem seit 2020-06 erreichten Niveau (2020-06 3,72, 2020-07 4,05); Δ entsteht nur aus den Vormonaten 2019-08 bis 2020-02. Regel 5: satz 2020-06..2021-03 nur 1 bewerteter Monat dazwischen (nicht ok); Zusammenfassen 2020-06..2021-03 wären 10 Kalendermonate > 6; definitionsgemäß gehört die Stelle zu 2020-06.
- 2021-07..2021-07: kein eigener Sprung (Vorfenster überspannt den Sprung 2020-06) / Regel 2 / Regel 5. pruefe regelkonform, Δ +1,0457 (Vor 3,1653 aus 2019-09 bis 2021-03, darin 2019-09 2,811, 2019-12 2,371, 2020-02 2,3 vom alten Niveau); Hinweis Vortrend +1,34. Gegenüber dem Niveau seit 2020-06 (3,72/4,05/3,74) nur leichter weiterer Anstieg auf 4,211. Regel 5: satz 2020-06..2021-07 nur 2 bewertete Monate dazwischen (nicht ok); Zusammenfassen 2020-06..2021-07 wären 14 Kalendermonate > 6. Der erste deutlich abweichende Monat dieser Niveauverschiebung ist 2020-06, ein höheres Δ allein ist kein Auswahlgrund.
- 2021-12..2021-12, 2021-12..2022-01: kein eigener Sprung (Vorfenster überspannt den Sprung 2020-06) / Regel 2 Trend. pruefe regelkonform, Δ +0,9013 / +0,9313 (Vor 3,3987 aus 2019-12 bis 2021-07, darin 2019-12 2,371 und 2020-02 2,3); Hinweis Vortrend +1,20. 2021-12 (4,30) springt nicht gegenüber 2021-07 (4,211); der weitere Anstieg 2021-03 3,74 → 2021-07 4,211 → 2021-12 4,30 → 2022-01 4,36 verläuft allmählich über rund zehn Monate (Trend, kein Sprung). Abstand zu 2020-06 nach satz wäre ok (3), verworfen nach Definition und Regel 2.
- 2017-11..2017-11: Regel 4 (einzelner Monatssprung mit Rückkehr), Setzungen (a)/(b), Stützung. Δ -1,0412 (Vor 3,9162, Niveau 2,875, n=8); erster Folgemonat 2018-02 (3,986) Abstand -0,0698 (Rückkehr), Folgemittel 3,584 Abstand 0,3322 < 0,5206; keine Stützung.
- 2017-07..2017-07, 2017-06..2017-07: Regel 4 / Stützung / Setzung Vorniveau mindestens drei Monate. 2017-07: Δ -0,411 (Zweifelsbereich), aber 2017-07 (n=9) ohne Stützung, also kein Zweifelsfall. 2017-06..2017-07: Vorniveau nur 2 bewertete Monate (S_vorniveau_min3 nicht erfüllt).
- 2019-03..2019-03, 2019-03..2019-05, 2019-05..2019-05: Setzung (a)/(b) Folgeniveau (Rückkehr nur vorübergehend). Δ +0,4035 / +0,4492 / +0,7832. Folgemittel 3,279 (Abstand 0,0825 < 0,2018) bzw. 2,6837 (Abstand -0,5128 bzw. -0,4332); erster Folgemonat 2019-07 (2,5) fällt unter das Vorniveau. 2019-03 zusätzlich ohne Stützung. Keine Zweifelsfälle, da Setzungen verletzt.
- 2019-12..2019-12: Setzung (a) Folgeniveau / Regel 2 Hinweis. Δ -0,7937 (Vor 3,1647 mit 2019-03 bis 2019-05 im Fenster); Folgemittel 3,3567, Abstand -0,192 < 0,3968; Vortrend -0,96. 2019-12 gehört zum seit 2019-07 bestehenden niedrigen Niveau, kein neuer Sprung.
- 2023-03..2023-03: Regel 4 (einzelner Monatssprung mit Rückkehr), Setzungen (a)/(b), Stützung. Δ -0,6258 (Vor 4,1458, Niveau 3,52, n=5); erster Folgemonat 2023-04 (4,125) Abstand 0,0208; Folgemittel 3,9417 Abstand 0,2042 < 0,3129; keine Stützung.
- 2024-03..2024-07: Regel 3 (mehr als ein nicht bewerteter Monat im Zeitraum), Setzung (b), Stützung. Δ -0,5365; 2024-04 (n=3), 2024-05 (n=3), 2024-06 (n=1) nicht bewertet; erster Folgemonat 2024-09 (4,02) Abstand -0,0335; 2024-07 (n=7) ohne Stützung. Definitionsgemäß ist die Stelle 2024-03..2024-03 (als Zweifelsfall geführt).
- 2024-09..2024-09: Regel 4 Zweifelsbereich, aber Setzungen (a)/(b) und Stützung verletzt. Δ +0,3125; Folgemittel 3,4643, Abstand -0,2432; erster Folgemonat 2025-01 (3,65) Abstand -0,0575; keine Stützung. Kein Zweifelsfall.
- 2025-02..2025-02: Regel 4 (einzelner Monatssprung mit Rückkehr), Setzungen (a)/(b), Stützung (definitionsgemäße Variante der Gruppe 2025). Δ -0,8287 (Vor 3,7117, Niveau 2,883, n=6); erster Folgemonat 2025-03 (3,86) Abstand -0,1483 (Rückkehr); Folgemittel 3,379 Abstand 0,3327 < 0,4143; keine Stützung.
- 2025-01..2025-03, 2025-02..2025-03 (Zweifelsfälle): Abgrenzung nach Definition / Regel 2 Hinweis. Δ -0,3265 / -0,3402. 2025-01 (3,65) weicht laut Tabelle nur -0,14 ab (Vortrend -0,30); 2025-03 (3,86) liegt über dem Vorniveau 3,7117 und damit nicht auf einem neuen Niveau; Δ entsteht nur durch Mittelung des Einzeltiefs 2025-02. Die definitionsgemäße Variante 2025-02..2025-02 ist verworfen, daher kein Zweifelsfall.
- 2025-07..2025-07: Setzung (a) Folgeniveau, Stützung. Δ -0,5352 (Vor 3,5522, Niveau 3,017, n=6); Folgemittel 3,55, Abstand 0,0022 < 0,2676; keine Stützung (2026-03 3,26 Abstand 0,2922).
- 2026-07..2026-07: Setzung (c) kein bewerteter Folgemonat, Regel 4 Zweifelsbereich, Stützung. Δ +0,3917; kein bewerteter Monat nach period_to, also nicht prüfbar; 2026-07 (n=5) ohne Stützung.

**Widerlegungsversuche (Prüfer):** Eintrag 2020-06..2020-06 (rise, Δ +0,9497):
(1) pruefe ergibt "regelkonform": Vorniveau 2,7703 aus 6 Monaten, Folgemittel 4,0003 (Abstand 1,23 >= 0,4748), erster Folgemonat 2020-07 mit Abstand 1,2797. Der dünne Monat 2020-06 (n=5) wird durch 2020-07 (4,05, n=6) gestützt.
(2) Abgrenzung: Die Variante 2020-06..2020-07 (Δ +1,1147; auch der frühere Lauf) und 2020-07..2020-07 (Δ +1,3097) habe ich als Alternativen geprüft. 2020-06 ist der erste abweichende bewertete Monat nach dem Tiefniveau 2019-07 bis 2020-02 (2,5/2,74/2,811/2,371/2,3). Mit 3,72 liegt er schon auf dem neuen Niveau, denn 2021-03 hat mit 3,74 fast denselben Wert und das Folgemittel ist 4,00. Die Verlängerung auf 2020-07 würde nur Δ vergrößern. Die Wahl des Annotators ist die mit dem kleineren Δ, also nicht auf Δ optimiert. Widerlegung gescheitert.
(3) Regel 2: Der Vortrend ist -0,55, also kein Lauf in Sprungrichtung. Der Hauptschritt 2,3 auf 3,72 liegt innerhalb von 4 Kalendermonaten. Das ist ein Sprung, kein Trend.
(4) Rückkehr: Danach erreicht kein bewerteter Monat wieder das Niveau von 2,3 bis 2,8. Die späteren Werte liegen zwischen 3,5 und 4,4.
(5) Regel 5: 2021-07 (Δ +1,0457, regelkonform) hat ein größeres |Δ| und liegt zu nah an 2020-06 (satz: 2 bewertete Monate dazwischen, nicht ok). Zusammenfassen ergäbe 14 Kalendermonate. Dennoch ist 2021-07 kein eigener Sprung. Gegenüber dem seit 2020-06 erreichten Niveau (3,72/4,05/3,74, Mittel rund 3,84) steigt es nur um rund 0,37. Sein Δ entsteht, weil das Vorfenster 2019-09, 2019-12 und 2020-02 vom alten Niveau enthält (Hinweis Vortrend +1,34). Nach der Definition beginnt diese Niveauverschiebung bei 2020-06, und das größte Δ ist kein Auswahlgrund. Dasselbe gilt für 2021-03 (satz: 1 Monat dazwischen, nicht ok) und für 2021-12. Bei 2021-12 wäre der Abstand nach satz zwar ok (3 Monate), aber 4,30 springt nicht gegenüber 2021-07 (4,211), und der Hinweis Vortrend lautet +1,20. Mit nur einem Eintrag greift die Kappung nicht, also braucht die note keinen Schwankungshinweis.
(6) note: Sie stimmt mit dem note_geruest aus pruefe überein. Der Hinweis zum dünnen Monat nennt die Anzahl (n=5) und den stützenden Monat. Die Reihenfolge nach Regel 11 ist eingehalten.
Ergebnis: Der Eintrag bleibt.

Zweifelsfall 2024-03..2024-03: pruefe ergibt "zweifelsfall_0_3_bis_0_49" mit Δ -0,4865. Gerundet -0,49, das liegt unter 0,5, also im Bereich 0,30-0,49. Alle anderen Prüfungen sind ok. Die Abgrenzung ist definitionsgemäß, denn 2023-11 weicht nur -0,15 ab und 2024-03 ist der erste abweichende Monat. Die Variante 2024-03..2024-07 verletzt Regel 3, weil 2024-04, 2024-05 und 2024-06 nicht bewertet sind. Mit 2020-06 ist der Zweifelsfall nach satz vereinbar (10 Monate Abstand). Der Rechner meldet außerdem "Vorniveau über 23 Kalendermonate verteilt". Das betrifft kein nicht bewerteter Monat im Zeitraum, und Regel 11 verlangt dafür keinen Hinweis. Der Zweifelsfall bleibt.

Kandidaten des früheren Laufs:
- 2018-05..2018-06: pruefe "verworfen". Setzung (a) scheitert (Folgemittel-Abstand 0,38 < 0,4103), und der dünne Monat 2018-06 (n=5) hat keine Stützung.
- 2019-07..2019-08: pruefe "verworfen". 2019-07 (n=8) hat keine Stützung, weil 2019-08 nur 0,487 und 2019-09 nur 0,416 vom Vorniveau abweichen. Die definitionsgemäße Variante 2019-07..2019-07 wird aus demselben Grund verworfen.
- 2020-06..2020-07: regelkonform, aber nicht definitionsgemäß, weil 2020-06 schon auf dem neuen Niveau liegt (siehe oben).
Keiner der drei wird aufgenommen.

**Vollständigkeit (Prüfer):** Grundlage ist der Scan: 10 regelkonforme Varianten in 6 Gruppen und 9 Zweifelsfälle in 4 Gruppen.

Regelkonforme Gruppen:
- Gruppe 2018 (2018-04..2018-06, 2018-04..2018-07): verworfen. 2018-04 (3,529) weicht nur -0,17 ab und liegt innerhalb des alten Niveaus. Die Varianten bestehen nur, weil 2018-04 das Vorfenster auf 2016-06 (4,088) verschiebt; das ist eine Verlängerung, damit eine Regel besteht. Die definitionsgemäßen Abgrenzungen 2018-05..2018-06 und 2018-06..2018-06 sind laut pruefe verworfen (Setzung (a), Stützung). Daher kein Eintrag für diese Stelle.
- Gruppe 2019 (2019-07..2019-09): verworfen. Das ist nicht definitionsgemäß, weil 2019-07 schon auf dem neuen Niveau liegt; die definitionsgemäße Variante 2019-07..2019-07 ist laut pruefe verworfen (Stützung). Außerdem ist der Abstand zu 2020-06 nach satz zu klein (2 Monate), und Zusammenfassen ergäbe 12 Kalendermonate. 2020-06 ist deutlicher.
- Gruppe 2020 (2020-06..2020-06, 2020-06..2020-07, 2020-07..2020-07): eingetragen als 2020-06..2020-06.
- Gruppen 2021-03, 2021-07 und 2021-12/2022-01: verworfen. Sie sind keine eigenen Sprünge; ihr Δ entsteht nur, weil das Vorfenster über den Sprung 2020-06 reicht (Vortrend +0,72/+1,34/+1,20). Danach folgt ein allmählicher Anstieg. 2021-03 und 2021-07 verletzen zudem Regel 5 gegenüber 2020-06.

Zweifelsfall-Gruppen:
- Gruppe 2018: nicht definitionsgemäß, weil 2018-02 und 2018-04 nicht abweichen und 2018-05 ein Übergangsmonat zwischen 3,609 und dem Folgeniveau 2,809 ist. Die definitionsgemäße Variante scheitert an den Setzungen. Kein Zweifelsfall.
- Gruppe 2019 (2019-08..2019-09, 2019-09..2019-09): beginnt erst nach dem ersten abweichenden Monat 2019-07 und ist mit 2020-06 nach Regel 5 nicht vereinbar (2 Monate Abstand). Kein Zweifelsfall.
- Gruppe 2024: als Zweifelsfall 2024-03..2024-03 geführt.
- Gruppe 2025: 2025-01 weicht nur -0,14 ab, und 2025-03 (3,86) liegt über dem Vorniveau. 2025-02 ist ein Einzeltief mit Rückkehr; die definitionsgemäße Variante 2025-02..2025-02 wird laut Annotator wegen der Setzungen verworfen. Kein Zweifelsfall.

Es fehlt keine regelkonforme, definitionsgemäße Stelle, die nach Regel 5 hineingehört. Endstand: 1 Eintrag und 1 Zweifelsfall. Am Annotator-Ergebnis ändert sich nichts.


## 1&1 AG (ID 21, 107 bewertete Monate)

**Ergebnis:** 3 Einträge, 0 Zweifelsfälle für Stufe B.

- Eintrag 2016-10 bis 2016-10, fall, Δ -0.908: Vorniveau 3,9 (2016-04 bis 2016-09, n=5-16); Zeitraum 3,0 (n=6); Δ -0,91; fall; dünn: 2016-10 mit 6 Bewertungen; Reihe schwankt: mehr als drei regelkonforme Kandidaten, nur die drei deutlichsten nach |Δ| eingetragen; Anker: keiner; Reihe allein.
- Eintrag 2018-04 bis 2018-04, rise, Δ +0.777: Vorniveau 3,0 (2017-07 bis 2018-03, n=5-11); Zeitraum 3,8 (n=12); Δ +0,78; rise; Reihe schwankt: mehr als drei regelkonforme Kandidaten, nur die drei deutlichsten nach |Δ| eingetragen; Anker: keiner; Reihe allein.
- Eintrag 2018-09 bis 2018-09, fall, Δ -1.122: Vorniveau 3,5 (2018-03 bis 2018-08, n=6-33); Zeitraum 2,4 (n=8); Δ -1,12; fall; dünn: 2018-09 mit 8 Bewertungen; Reihe schwankt: mehr als drei regelkonforme Kandidaten, nur die drei deutlichsten nach |Δ| eingetragen; Anker: keiner; Reihe allein.

**Auswahl (Annotator):** Die Reihe 1&1 Mitarbeitende schwankt stark. Nach definitionsgemäßer Abgrenzung (Start im ersten deutlich abweichenden Monat, Ende im ersten Monat auf dem neuen Niveau) bleiben sechs regelkonforme Kandidaten: 2018-09 (Δ -1,122), 2016-10 (-0,908), 2018-04 (+0,777), 2015-04 (+0,709), 2019-12..2020-05 (-0,666) und 2014-07..2014-11 (-0,508). Nach Regel 5 sind nur die drei mit dem größten |Δ| eingetragen: 2016-10, 2018-04 und 2018-09. Alle drei sind abrupte Sprünge in einem einzigen Monat, der schon auf dem neuen Niveau liegt. Keiner hat einen Vortrend in Sprungrichtung (Vortrend +0,157, -0,281 und -0,068). Alle drei sind im Rechner regelkonform, und der Satz-Check ist ok (Abstände 11 und 4 bewertete Monate). Die Schwankung steht in jeder note. Für 2018-09 wurde die Abgrenzung bis 2018-11 geprüft. Sie scheitert an Setzung (a). Weil 2018-09 mit 2,388 in Fallrichtung über das Folgeniveau von 2,857 hinausgeht, gilt der Monat als erreichtes neues Niveau. Die Scan-Gruppen 2013 und 2019 (Anstieg) bestehen R4 nur in Varianten, deren Ende über den ersten Monat auf dem neuen Niveau hinaus verlängert ist. Ihre definitionsgemäßen Abgrenzungen liegen im Zweifelsbereich (2013-01..2013-05 mit +0,477, 2019-03..2019-03 mit +0,486). Keinen Eintrag, nur Protokollvermerk. Zweifelsfälle werden keine aufgenommen, weil schon drei Einträge stehen und ein weiterer Zeitraum nach Regel 5 nicht vereinbar wäre.

**Verworfene Kandidaten (33):**

- 2013-01..2013-06 (regelkonform laut Scan): Abgrenzung nach Definition (Ende nach erstem Monat auf neuem Niveau verlängert); definitionsgemäße Variante 2013-01..2013-05 ist nur Zweifelsfall (R4). 2013-01..2013-06 Δ +0,538; definitionsgemäß 2013-01..2013-05 Δ +0,477 (Vorniveau 2,909 aus nur 3 bewerteten Monaten über 21 Kalendermonate, lückig); 2013-05 = 3,712 bereits auf neuem Niveau, 2013-06 = 3,750; Zweifelsfall wegen Regel 5 (Anzahl, 3 Einträge) nicht aufgenommen
- 2013-01..2013-01: S_folgeniveau (a) und (b). Δ +0,819; erster Folgemonat 2013-02 = 3,073, Abstand 0,164 < 0,25; Folgemittel 3,165, Abstand 0,255 < 0,409
- 2013-05..2013-05 (alternative Abgrenzung): R4 Zweifelsbereich; Regel 5 (Anzahl) nicht vereinbar. Δ +0,477, Vorniveau 3,235 (2011-02 bis 2013-04, lückig über 27 Kalendermonate); 2013-05..2013-06 Δ +0,496 scheitert an R4 und S_folgeniveau (erster Folgemonat 2013-07 = 3,273, Abstand 0,038)
- 2013-05..2013-10, 2013-06..2013-10, 2013-08..2013-10, 2013-08..2013-12, 2013-09..2013-10 (regelkonform laut Scan): Abgrenzung nach Definition; Regel 2 (Vorniveau steigt bereits); einzelner Monatssprung 2013-10 ohne Bleiben. Δ +0,545 / +0,551 / +0,610 (Vortrend +0,41) / +0,515 / +0,670; Startmonate 2013-08 = 3,663 und 2013-09 = 3,737 weichen nicht vom Niveau 2013-05/06 (3,712/3,750) ab; Sprungmonat 2013-10 = 4,543 (n=7): 2013-10..2013-10 Δ +1,006 scheitert an S_folgeniveau (Folgemittel-Abstand 0,348 < 0,503) und Stützung dünn; 2013-10..2013-11 Δ +0,744 scheitert an S_folgeniveau (0,127 < 0,372); 2013-12 = 3,468 (n=47) wieder auf altem Niveau
- 2013 Zweifelsfälle laut Scan (2013-01..2013-02, 2013-03..2013-08, 2013-04..2013-09, 2013-07..2013-12, 2013-09..2013-12, 2013-10..2013-12 u. a.): R4 Zweifelsbereich; nicht definitionsgemäß; Regel 5 (Anzahl) nicht vereinbar. Δ +0,312 bis +0,491
- 2014-07..2014-11 (regelkonform): Regel 5 (Rang 6 von 6 nach |Δ|); zudem Bleiben fraglich. Δ -0,508, Vorniveau 3,933 (enthält dünne Spitze 2013-10/11); 2014-08 = 3,900 schon wieder auf Vorniveau; Folgemittel 3,629 (Abstand 0,304 >= 0,254), danach 2015-04 = 4,120 zurück über altem Niveau
- 2014-07..2014-07, 2014-09..2014-11, 2014-11..2014-11: S_folgeniveau (2014-07 zusätzlich Stützung dünn). Δ -0,576 (erster Folgemonat 2014-08 Abstand 0,033) / -0,688 (Folgemittel-Abstand 0,280 < 0,344) / -0,734 (Folgemittel-Abstand 0,098 < 0,367)
- 2014-07..2014-09, 2014-08..2014-11, 2014-09..2014-09: R4 Zweifelsbereich; Regel 5 (Anzahl) nicht vereinbar. Δ -0,364 / -0,434 / -0,459
- 2015-04..2015-04 (regelkonform): Regel 5 (Rang 4 nach |Δ|, 0,709 < 0,777). Δ +0,709, Vorniveau 3,411 (2014-07 bis 2015-03); 2015-04 nur n=5; Erholung nach Dip, Werte steigen schon vorher (2014-11 = 2,993, 2014-12 = 3,217, 2015-03 = 3,550); Folgemittel 3,802 (Abstand 0,391 >= 0,354)
- 2015-04..2015-07; 2015-03..2015-04: R3 (zwei nicht bewertete Monate 2015-05, 2015-06) und S_folgeniveau; bzw. R4 Zweifelsbereich. Δ +0,711 (Folgemittel-Abstand 0,090 < 0,356); 2015-03..2015-04 Δ +0,321
- 2016-10..2016-11, 2016-09..2016-10, 2016-09..2016-11, 2016-09..2017-01, 2016-10..2017-01, 2016-11..2016-11, 2016-11..2017-01, 2017-01..2017-01 (regelkonform): Abgrenzung nach Definition (gleiche Stelle wie Eintrag 2016-10..2016-10). Δ -0,814 / -0,513 / -0,559 / -0,592 / -0,797 / -0,597 / -0,618 / -0,520; 2016-09 = 3,636 nur -0,19 zum Vorniveau, also nicht erster abweichender Monat; 2016-10 = 2,983 ist erster abweichender Monat und bereits auf neuem Niveau (2016-11 = 3,171, 2017-01 = 3,129, 2017-03 = 3,071)
- 2016-07..2016-07; 2016-08..2016-11, 2016-08..2017-01: S_folgeniveau und Stützung dünn; bzw. R4 Zweifelsbereich. 2016-07 Δ +0,683 (Folgemittel-Abstand -0,140); Zweifelsfälle Δ -0,343 / -0,403
- 2017-10..2017-10, 2017-10..2017-11: S_folgeniveau. Δ -1,078 (Folgemittel-Abstand 0,498 < 0,539) / Δ -0,804 (0,181 < 0,402)
- 2018-04..2018-05 (regelkonform): Abgrenzung nach Definition (2018-04 bereits auf neuem Niveau). Δ +0,809; 2018-04 = 3,817, Folgeniveau 2018-05 bis 2018-08 = 3,882 / 3,307 / 3,476 / 3,645
- 2018-09..2018-11 (alternative Abgrenzung): S_folgeniveau (a). Δ -0,941; Folgemittel 3,107, Abstand 0,403 < 0,471; 2018-10 nicht bewertet (n=4)
- 2018-08..2018-09: R4 Zweifelsbereich; nicht definitionsgemäß (2018-08 = 3,645 weicht nicht ab). Δ -0,369
- 2019-03..2019-03 (definitionsgemäße Abgrenzung des Anstiegs 2019): R4 Zweifelsbereich (0,30-0,49); Regel 5 (Anzahl, bereits 3 Einträge) nicht vereinbar. Δ +0,486, Vorniveau 3,014 (2018-07 bis 2019-01); 2019-03 = 3,500 bereits auf neuem Niveau (2019-05 = 3,509, 2019-06 = 3,419); Folgemittel 3,648
- 2019-03..2019-07, 2019-05..2019-07, 2019-05..2019-09, 2019-05..2019-10, 2019-06..2019-07, 2019-06..2019-08, 2019-06..2019-09, 2019-06..2019-10 (regelkonform laut Scan): Abgrenzung nach Definition (über das in 2019-03 erreichte neue Niveau bis zur Spitze 2019-07 verlängert); 2019-06..2019-07 mit Vortrend +0,45 (Regel 2). Δ +0,598 / +0,631 / +0,587 / +0,569 / +0,723 / +0,760 / +0,633 / +0,607
- 2019-07..2019-07; 2019-03..2019-05, 2019-03..2019-06, 2019-05..2019-05, 2019-05..2019-06, 2019-06..2019-06: S_folgeniveau (Vortrend +0,62); bzw. R4 Zweifelsbereich. 2019-07 Δ +0,850 (Folgemittel-Abstand 0,358 < 0,425); Zweifelsfälle Δ +0,424 bis +0,491
- 2019-12..2020-05 (regelkonform, definitionsgemäß): Regel 5 (Rang 5 nach |Δ|, 0,666 < 0,777). Δ -0,666, Vorniveau 3,663 (2019-06 bis 2019-11, n=10-24); Zeitraum n=7, 15, 5, 6, 7, 2020-04 nicht bewertet (n=1); Folgemittel 2,809 (Abstand 0,854); kein Trend (Vortrend -0,18, Monatswerte pendeln)
- 2019-12..2019-12, 2019-12..2020-01, 2019-12..2020-03, 2020-02..2020-05, 2020-02..2020-06, 2020-02..2020-07, 2020-05..2020-08, 2020-05..2020-09, 2020-05..2020-10: 2019-12 allein: S_folgeniveau und Stützung dünn; übrige: Abgrenzung nach Definition (Ende nicht auf neuem Niveau bzw. Start nicht erster abweichender Monat). 2019-12 Δ -1,134 (2020-01 = 3,660 zurück, Abstand 0,003); Δ -0,569 / -0,570 / -0,523 / -0,518 / -0,534 / -0,546 / -0,550 / -0,513
- 2020-05..2020-05, 2020-05..2020-06: R3_stuetzung_duenn. Δ -0,693 / -0,523; 2020-05 (n=7) ohne weiteren Monat >= 0,5 Abweichung (2020-06 Abstand 0,354, 2020-07 0,452)
- 2019-11..2020-03, 2020-01..2020-05, 2020-01..2020-06, 2020-02..2020-03, 2020-03..2020-08, 2020-05..2020-07, 2020-06..2020-08: R4 Zweifelsbereich; nicht definitionsgemäß; Regel 5 (Anzahl) nicht vereinbar. Δ -0,319 bis -0,499
- 2011-02..2011-02, 2012-08..2012-08: S_vorniveau_min3 (Vorniveau unter drei bewerteten Monaten). Δ +1,13 (1 Vormonat) / -0,58 (2 Vormonate)
- 2021-12..2021-12: S_folgeniveau und Stützung dünn (einzelner Monatssprung). Δ -1,004; 2022-01 = 3,360 über Vorniveau (Abstand -0,299)
- 2022-06..2022-06, 2022-08..2022-08: S_folgeniveau und Stützung dünn. Δ +0,774 (2022-07 = 2,657, Abstand -0,206) / +0,971 (Folgemittel-Abstand -0,029)
- 2022-12..2022-12: S_folgeniveau (einzelner Monatssprung). Δ -1,031; 2023-01 = 3,300 über Vorniveau (Abstand -0,105)
- 2023-09..2023-09: R4, S_folgeniveau, Stützung dünn. Δ -0,4995; 2023-10 = 3,460 Gegenrichtung
- 2023-10..2023-10; 2023-10..2023-11, 2023-11..2023-11: R4 Zweifelsbereich, Regel 5 (Anzahl) nicht vereinbar; bzw. S_folgeniveau. Δ +0,472; Δ +0,824 (Folgemittel-Abstand 0,263 < 0,412) / +0,959 (0,047 < 0,480)
- 2024-03..2024-03: S_folgeniveau (Vortrend +0,67). Δ +0,514; Folgemittel-Abstand -0,312
- 2024-05..2024-05, 2024-05..2024-06: S_folgeniveau. Δ -0,819 (Folgemittel-Abstand 0,070 < 0,410) / -0,768 (2024-07 = 3,657 zurück, Abstand -0,221)
- 2024-07..2024-07; 2024-07..2024-09, 2024-08..2024-08, 2024-08..2024-09, 2024-09..2024-09: R4 und Stützung dünn; bzw. R4 Zweifelsbereich, Regel 5 (Anzahl) nicht vereinbar. Δ +0,308; Zweifelsfälle Δ +0,344 / +0,339 / +0,329 / +0,392
- 2025-06..2025-06: S_folgeniveau (c) kein bewerteter Folgemonat, Stützung dünn. Δ -0,722; 2025-07 nur n=4

**Widerlegungsversuche (Prüfer):** Eintrag 2016-10..2016-10 (fall): Der Rechner meldet mit pruefe "regelkonform" (Δ -0,9082, Vorniveau 3,891 aus 6 Monaten, Folgemittel 3,124 mit Abstand 0,768 bei verlangten 0,454, erster Folgemonat 2016-11 = 3,171 mit Abstand 0,720, Stützung für den dünnen Monat durch 2016-11). Geprüft habe ich die Abgrenzung: 2016-09 = 3,636 liegt nur -0,19 unter seinem Vorniveau 3,822 und ist deshalb nicht der erste deutlich abweichende Monat. 2016-10 = 2,983 ist der erste abweichende Monat und liegt schon auf dem neuen Niveau (2016-11 3,171, 2017-01 3,129, 2017-03 3,071, 2017-04 3,200) bzw. leicht darüber hinaus. Die Abgrenzung ist also definitionsgemäß und nicht auf Δ optimiert. Dass sie mit dem größten Δ der Gruppe zusammenfällt, ist Zufall. Einen Trend sehe ich nicht: Vortrend +0,157, der Abstieg 2016-08..2016-10 dauert unter sechs Monate. Ein Ausreißer mit Rückkehr ist es auch nicht, die nächsten drei bewerteten Monate bleiben ca. 0,7 unter dem Vorniveau. Die note stimmt mit dem note_geruest überein und nennt den dünnen Monat (n=6) und die Schwankung. Widerlegung gescheitert.

Eintrag 2018-04..2018-04 (rise): Der Rechner meldet "regelkonform" (Δ +0,7765, Folgemittel 3,555 mit Abstand 0,515 bei verlangten 0,388, erster Folgemonat 2018-05 = 3,882). Die Variante 2018-04..2018-05 ist ebenfalls regelkonform und hätte das größere Δ +0,809. Der Annotator hat trotzdem die definitionsgemäße kürzere Variante gewählt, weil 2018-04 schon auf dem neuen Niveau liegt (Folgemonate 3,882 / 3,307 / 3,476 / 3,645). Eine Δ-Optimierung liegt also nicht vor. Einen Trend gibt es nicht (Vortrend -0,281, also gegen die Sprungrichtung). Ein Einmonatsausreißer ist es nicht, denn 2018-05 bis 2018-08 bleiben über dem Vorniveau 3,04. Das Vorniveau enthält nach Regel 4 die sechs bewerteten Vormonate einschließlich 2017-07/08. Das ist protokollgemäß. Die note stimmt und braucht keinen Dünn-Hinweis (n=12). Widerlegung gescheitert.

Eintrag 2018-09..2018-09 (fall): Der Rechner meldet "regelkonform" (Δ -1,122, Folgemittel 2,857 mit Abstand 0,653 bei verlangten 0,561, erster Folgemonat 2018-11 = 2,750 mit Abstand 0,76, Stützung durch 2018-11). Die längere Abgrenzung 2018-09..2018-11 (Kandidat des früheren Laufs) habe ich nachgerechnet. Sie wird verworfen, weil S_folgeniveau (a) mit 0,403 < 0,471 nicht erfüllt ist, 2018-10 ist ohnehin grau (n=4). 2018-09 = 2,388 liegt in Fallrichtung über das Folgeniveau hinaus und ist damit der erste Monat auf dem neuen Niveau. Ein Ausreißer mit Rückkehr ist es nicht: 2018-11 2,750, 2018-12 3,167 und 2019-01 2,655 bleiben 0,34 bis 0,86 unter dem Vorniveau 3,51. Einen Trend gibt es nicht (Vortrend -0,068). Die note stimmt und nennt n=8 und die Schwankung. Widerlegung gescheitert.

Regel 5: satz 2016-10:2016-10 2018-04:2018-04 2018-09:2018-09 ergibt ok (3 Zeiträume, Abstände 11 und 4 bewertete Monate). Es gibt mehr als drei regelkonforme Stellen. Den Rang habe ich mit pruefe nachgerechnet: 2015-04 +0,709, 2019-12..2020-05 -0,666, 2014-07..2014-11 -0,508. Auch die nicht definitionsgemäßen Maxima der Gruppen 2013 (+0,670) und 2019-Anstieg (2019-06..2019-08 +0,760) liegen unter 0,777. Die drei Einträge bleiben also die deutlichsten, auch wenn man die Abgrenzungsentscheidungen des Annotators in diesen Gruppen anders träfe. Jede note nennt die Schwankung.

Kandidaten des früheren Laufs: 2013-10..2013-10 wird verworfen, weil S_folgeniveau mit 0,348 < 0,503 nicht erfüllt ist und die Stützung für n=7 fehlt. 2017-10..2017-10 wird verworfen, weil S_folgeniveau (a) mit 0,4975 < 0,5388 nicht erfüllt ist. 2017-10..2017-11 ist ebenfalls verworfen (0,181 < 0,402). 2018-09..2018-11 wird wie oben beschrieben verworfen. Keiner davon gehört hinein.

Zweifelsfälle: Bei drei Einträgen wäre jeder weitere Zeitraum nach Regel 5 (höchstens 3) nicht vereinbar. Deshalb bleibt die Liste leer, wie beim Annotator.

**Vollständigkeit (Prüfer):** Der Scan meldet 37 regelkonforme Zeiträume in 8 Gruppen und 44 Zweifelsfälle in 9 Gruppen. Die regelkonformen Gruppen sind so behandelt:
- 2013 (6 Varianten): verworfen nach Definition. Die definitionsgemäße Abgrenzung 2013-01..2013-05 ist ein Zweifelsfall (+0,477, laut pruefe zweifelsfall). Der Sprungmonat 2013-10 scheitert an S_folgeniveau. Selbst das Maximum +0,670 würde Regel 5 nicht ändern.
- 2014-07..2014-11: regelkonform, nach Regel 5 Rang 6 und deshalb nicht eingetragen.
- 2015-04: regelkonform, Rang 4 (+0,709 < 0,777).
- 2016 (9 Varianten): eingetragen als 2016-10..2016-10, die übrigen Varianten sind nach Definition verworfen.
- 2018-04 (2 Varianten): eingetragen als 2018-04..2018-04. 2018-05 als Ende ist nicht definitionsgemäß.
- 2018-09: eingetragen.
- 2019-Anstieg (8 Varianten): verworfen nach Definition. Die definitionsgemäße Abgrenzung 2019-03..2019-03 ist ein Zweifelsfall (+0,486). Das Maximum +0,760 liegt ohnehin unter Rang 3.
- 2019-12/2020 (9 Varianten): die definitionsgemäße Abgrenzung 2019-12..2020-05 ist regelkonform, nach Regel 5 Rang 5.

Die Zweifelsgruppen sind alle im Protokoll des Annotators vermerkt und wegen Regel 5 (Anzahl) nicht aufgenommen: 2013, 2014-07..2014-09 u. a., 2015-03..2015-04, 2016-08..2016-11/2017-01, 2018-08..2018-09, 2019-03..2019-06, 2019-11..2020-08, 2023-10, 2024-07..2024-09.

Auch die Kandidaten des früheren Laufs (2013-10, 2017-10, 2018-09..2018-11) sind verworfen. Eine regelkonforme, definitionsgemäße Stelle, die nach Regel 5 hineingehört, fehlt nicht. Gegenüber dem Annotator gibt es keine Änderung.


## Bechtle (ID 24, 139 bewertete Monate)

**Ergebnis:** 3 Einträge, 0 Zweifelsfälle für Stufe B.

- Eintrag 2021-02 bis 2021-02, rise, Δ +0.556: Vorniveau 3,4 (2020-08 bis 2021-01, n=6-20); Zeitraum 4,0 (n=10); Δ +0,56; rise; Vorniveau streut stark (Monatsmittel 2,50 bis 4,01); Anker: keiner; Reihe allein.
- Eintrag 2021-08 bis 2021-09, fall, Δ -1.071: Vorniveau 4,0 (2021-02 bis 2021-07, n=7-24); Zeitraum 2,9 (n=7, 24); Δ -1,07; fall; 2021-08 dünn (n=7, Mittel 2,47), gestützt durch 2021-09 (3,38, n=24); Anker: keiner; Reihe allein.
- Eintrag 2023-01 bis 2023-01, rise, Δ +0.682: Vorniveau 3,4 (2022-07 bis 2022-12, n=7-33); Zeitraum 4,1 (n=41); Δ +0,68; rise; Vorniveau streut (Monatsmittel 2,76 bis 4,05); Anker: keiner; Reihe allein.

**Auswahl (Annotator):** Bechtle Mitarbeitende, Gesamtbewertung, 139 bewertete Monate, bis 2012 fast nur graue Monate. Der Scan liefert 7 Gruppen mit regelkonformen Varianten. Abgegrenzt habe ich nach der Definition und nicht nach dem größten Δ. Danach bleiben drei Kandidaten, die alle eingetragen sind (satz: Anzahl 3, Abstände 5 und 15 bewertete Monate, ok).

(1) 2021-02..2021-02, Δ +0,556: 2021-02 ist der erste abweichende Monat und liegt schon auf dem neuen Niveau. Das Niveau hält sechs Monate stabil bei etwa 4,0 (2021-02 bis 2021-07). Vortrend -0,10, also kein Trend.

(2) 2021-08..2021-09, Δ -1,0715: 2021-08 (2,47, n=7) unterschießt, 2021-09 (3,38) ist der erste Monat auf dem neuen Niveau. Das Niveau bleibt danach bei etwa 3,3 bis 3,6. Davor ist die Reihe flach, kein Trend.

(3) 2023-01..2023-01, Δ +0,682: abrupter Sprung nach fallenden Vormonaten, danach mehrere Monate erhöht. Vortrend -0,10.

Verworfen trotz Scan-Ergebnis regelkonform:
- 2016-02: Die definitionsgemäße Abgrenzung beginnt mit 2016-01 (Übergangsmonat 3,26, Rechnerhinweis Vortrend +0,32). Die Variante 2016-01..2016-02 hat Δ +0,458, ist also ein Zweifelsfall.
- 2017-09: zwei dünne Einbruchmonate (n=6, n=8), danach kehrt das alte Niveau zurück (2017-11 3,50). Setzung (a) ist nur knapp erfüllt.
- 2020-04..2020-05: Die definitionsgemäße Variante 2020-04..2020-04 verfehlt Setzung (a). Die Verlängerung wäre nur eine Regelrettung.
- 2023-08..2023-09: einzelner Einbruch, 2023-09 ist wieder auf altem Niveau.

Damit gibt es genau drei Kandidaten, die Schwankungsklausel nach Regel 5 greift nicht. In zwei notes steht trotzdem ein Streuungshinweis zum Vorniveau. Zweifelsfälle sind keine aufgenommen: Bei drei Einträgen würde jeder weitere das Maximum von drei Zeiträumen nach Regel 5 überschreiten. Die Unabhängigkeit ist gewahrt: Gelesen habe ich nur die Serien-CSV über den Rechner (tabelle, scan, pruefe, satz).

**Verworfene Kandidaten (26):**

- 2016-01..2016-02 (definitionsgemäße Abgrenzung der Stelle 2016): Regel 4 Zweifelsfall (0,30-0,49); mit drei Einträgen nach Regel 5 nicht vereinbar (Anzahl). Vor 2,917 (2015-04 bis 2015-12, n=6-12); Niveau 3,375 (n=12, 11); Δ +0,4577; Folge 3,488 (a ok, b ok); Vortrend +0,13. 2016-01 (3,258, +0,34) ist der erste abweichende Monat, 2016-02 (3,491) der erste auf dem neuen Niveau
- 2016-02..2016-02 (Scan regelkonform): Abgrenzung nach Definition: period_from wäre 2016-01, nicht 2016-02; Verkürzung nur zur Δ-Vergrößerung unzulässig; Rechnerhinweis Vortrend (Regel 2). Δ +0,5507; Vor 2,940 enthält 2016-01 (3,258); Rechnerhinweis: Vorniveau bewegt sich bereits in Sprungrichtung (+0,32)
- 2016-01..2016-06, 2016-02..2016-06, 2016-02..2016-07 (Scan regelkonform): Abgrenzung nach Definition: period_to läge hinter dem ersten Monat auf neuem Niveau (2016-02); Verlängerung unzulässig. Δ +0,526 / +0,548 / +0,557
- 2016-01..2016-01, 2015-11..2016-04, 2016-01..2016-04, 2016-02..2016-04, 2016-04..2016-07, 2016-04..2016-08, 2016-05..2016-07, 2016-05..2016-08 (Scan-Zweifelsfälle): Regel 4 Zweifelsfall; nicht definitionsgemäß; mit Regel 5 nicht vereinbar. Δ +0,341 / +0,310 / +0,418 / +0,432 / +0,402 / +0,438 / +0,422 / +0,447
- 2017-09..2017-09 (Scan regelkonform): Regel 4 Satz 2 / Bleiben: zweimonatiger Einbruch aus zwei dünnen Monaten, danach kehrt das alte Niveau zurück; Setzung (a) nur knapp und nur durch den zweiten Einbruchmonat 2017-10 erfüllt. Vor 3,525 (2017-01 bis 2017-07, n=6-28); Niveau 2,85 (n=6); Δ -0,6747; Folge 3,175 (Abstand 0,349 bei verlangt 0,337); 2017-11 = 3,50 (n=10), also wieder auf Vorniveau
- 2017-09..2017-10: Setzung (a) und (b) verfehlt (Rückkehr zum alten Niveau). Δ -0,6687; Niveau 2,856 (n=6, 8); Folge 3,361 (Abstand 0,163 < 0,334); erster Folgemonat 2017-11 = 3,50, Abstand 0,025
- 2020-04..2020-05 (Scan regelkonform): Abgrenzung nach Definition: 2020-04 (3,867) ist schon auf dem neuen Niveau, also wäre 2020-04..2020-04 die Abgrenzung, und die verfehlt Setzung (a); Verlängerung auf 2020-05 nur, damit die Regel besteht, ist unzulässig, also kein Eintrag. 2020-04..2020-05: Δ +0,5422, Folge 3,503. 2020-04..2020-04: Vor 3,203 (2019-10 bis 2020-03, n=12-28), Δ +0,6637, Folge 3,424 (Abstand 0,221 < 0,332); 2020-07 fällt auf 2,917 zurück
- 2020-03..2020-04, 2020-03..2020-05, 2020-03..2020-08, 2020-04..2020-07, 2020-04..2020-08, 2020-05..2020-05 (Scan-Zweifelsfälle): Regel 4 Zweifelsfall; selbe Stelle, nicht definitionsgemäß; mit Regel 5 nicht vereinbar. Δ +0,312 / +0,340 / +0,307 / +0,332 / +0,397 / +0,341
- 2021-02..2021-03, 2021-02..2021-04, 2021-03..2021-04, 2021-04..2021-04 (Scan regelkonform, Gruppe des Eintrags 2021-02): Abgrenzung nach Definition: 2021-02 ist erster abweichender Monat und bereits auf neuem Niveau; andere Ränder nur Δ-Vergrößerung. Δ +0,526 / +0,639 / +0,664 / +0,867
- 2021-01..2021-04, 2021-03..2021-03 (Scan-Zweifelsfälle); 2021-01..2021-02: Regel 4 Zweifelsfall bzw. Regel 4 verfehlt; nicht definitionsgemäß (2021-01 = 3,067 weicht nicht ab). Δ +0,420 / +0,479; 2021-01..2021-02 Δ +0,1345
- 2021-07..2021-10, 2021-07..2021-11 (Scan regelkonform): Abgrenzung nach Definition: 2021-07 (3,946) weicht nicht vom Vorniveau ab. Δ -0,512 / -0,521
- 2021-08..2021-10, 2021-08..2021-11, 2021-08..2022-01 (Scan regelkonform): Abgrenzung nach Definition: period_to läge hinter dem ersten Monat auf neuem Niveau (2021-09 = 3,379). Δ -0,861 / -0,821 / -0,694
- 2021-08..2021-08: Setzung (a) verfehlt; 2021-08 (2,471, n=7) unterschießt das neue Niveau, kein eigener Endmonat. Δ -1,5255; Folge 3,41 (Abstand 0,587 < 0,763)
- 2021-09..2021-11 (Scan-Zweifelsfall): Regel 4 Zweifelsfall; selbe Stelle wie Eintrag 2021-08..2021-09, Abstand nach Regel 5 zu gering. Δ -0,338
- 2022-12..2023-04, 2023-01..2023-03, 2023-01..2023-04 (Scan-Zweifelsfälle, Gruppe des Eintrags 2023-01): Regel 4 Zweifelsfall; nicht definitionsgemäß (period_from 2022-12 = 3,181 weicht nicht ab bzw. period_to hinter 2023-01). Δ +0,313 / +0,474 / +0,469
- 2023-08..2023-09 (Scan regelkonform): Regel 4 Satz 2: Einzelmonatseinbruch 2023-08 (2,90), danach ist 2023-09 (3,75) wieder auf altem Niveau und kein erster Monat auf neuem Niveau; Setzung (a) nur durch den nächsten Einzeleinbruch 2023-10 (2,722) erfüllt. Vor 3,873 (2023-02 bis 2023-07, n=10-35); Δ -0,5482; Folge 3,491. 2023-08..2023-08: Δ -0,9732, Folge 3,485 (Abstand 0,389 < 0,487), erster Folgemonat 2023-09 Abstand 0,123 (a und b verfehlt)
- 2023-06..2023-09, 2023-07..2023-09, 2023-07..2023-12, 2023-08..2024-01 (Scan-Zweifelsfälle): Regel 4 Zweifelsfall; selbe Stelle, gleiche Einzeleinbrüche; mit Regel 5 nicht vereinbar. Δ -0,334 / -0,478 / -0,460 / -0,409
- 2013-06..2013-06 (auch 2013-06..2013-07, 2013-06..2013-08, 2013-08..2013-08): Regel 4 Zweifelsfall; mit drei Einträgen nach Regel 5 nicht vereinbar. Vor 3,253 (2011-02 bis 2013-05 über Lücke, n=6-24); Δ -0,333 (Varianten -0,303 / -0,307 / -0,332)
- 2014-06..2014-10: Regel 4 Zweifelsfall; mit Regel 5 nicht vereinbar. Vor 2,850; Niveau 3,212; Δ +0,3619; 2014-07 nicht bewertet (n=4); Vortrend -0,40
- 2015-07..2015-07 und 2015-07..2015-09: Setzung (a) und (b) verfehlt (kein Bleiben). Vor 3,118; Δ -0,5678 (Folge 2,978, erster Folgemonat Abstand 0,235) bzw. Δ -0,4013 (Folge 2,984, erster Folgemonat Abstand 0,209)
- 2018-07..2018-07 (Scan-Zweifelsfall); 2018-07..2018-08: Regel 4 Zweifelsfall, mit Regel 5 nicht vereinbar; 2018-07..2018-08 verfehlt Setzung (b). Vor 3,568; Δ -0,4213 (Folge 3,116); 2018-07..2018-08 Δ -0,4313, erster Folgemonat 2018-09 = 3,55, Abstand 0,018
- 2019-02..2019-02 und 2019-02..2019-03; Scan-Zweifelsfälle 2019-01..2019-02, 2019-02..2019-04: Setzung (a)/(b) verfehlt bzw. (b) verfehlt; Zweifelsfälle mit Regel 5 nicht vereinbar. Vor 3,227; Δ +0,6875 (Folge 3,562, erster Folgemonat Abstand 0,2495) bzw. Δ +0,4685 (erster Folgemonat 2019-04 Abstand 0,179); Zweifel Δ +0,305 / +0,372
- 2019-08..2019-08 und 2019-08..2019-09; Scan-Zweifelsfälle 2019-08..2019-10/-11/-12/2020-01: Setzung (a)/(b) verfehlt bzw. (b) verfehlt; Zweifelsfälle mit Regel 5 nicht vereinbar. Vor 3,595; Δ -0,8803 (Folge 3,338, erster Folgemonat Abstand 0,231) bzw. Δ -0,5558 (erster Folgemonat 2019-10 Abstand 0,203); Zweifel Δ -0,438 / -0,413 / -0,446 / -0,414
- 2024-07..2024-07; Scan-Zweifelsfälle 2024-07..2024-09/-10/-12, 2024-09..2024-09, 2024-09..2024-10, 2024-10..2024-10: 2024-07..2024-07 verfehlt Setzung (b); Zweifelsfälle mit drei Einträgen nach Regel 5 nicht vereinbar. Vor 3,375; Δ +0,5008, erster Folgemonat 2024-08 = 3,426, Abstand 0,051; Zweifel Δ +0,327 / +0,355 / +0,322 / +0,410 / +0,414 / +0,392
- 2011-03..2011-03 und 2013-01..2013-01: Setzung Vorniveau mindestens drei bewertete Monate verfehlt (nicht prüfbar). Vorniveau nur 1 bzw. 2 bewertete Monate (Tabelle: 2011-03 Diff -1,16; 2013-01 Diff +0,79)
- Einzelmonatsausschläge laut Tabelle: 2014-10, 2015-02, 2016-05, 2017-04, 2018-03, 2018-10, 2020-07, 2020-10, 2022-07, 2022-09, 2023-05, 2023-10, 2024-06: Regel 4 Satz 2: einzelner Monatssprung, danach kehrt das alte Niveau zurück; im Scan nicht regelkonform. Diff zu Vor6 laut Tabelle: +0,62 / -0,72 / +0,92 / +0,72 / +0,70 / -0,78 / -0,55 / -1,17 / -0,75 / +0,68 / +0,81 / -1,01 / -0,97

**Widerlegungsversuche (Prüfer):** Alle drei Einträge habe ich mit pruefe nachgerechnet. Jeder ist "regelkonform", und die Zahlen stimmen exakt mit dem note_geruest überein. satz für 2021-02:2021-02, 2021-08:2021-09 und 2023-01:2023-01 ergibt: Anzahl 3, Abstände 5 und 15 bewertete Monate, ok.

(1) 2021-02..2021-02, Δ +0,556. Vor 3,404 (2020-08 bis 2021-01). Folge 4,013, verlangt sind 0,278 Abstand, erreicht 0,609. Erster Folgemonat 2021-03 mit Abstand 0,496. Vortrend -0,10, kein Hinweis.
- Angriff Rückkehr/Ausreißer: Das neue Niveau hält sechs Monate bei 3,87 bis 4,27. Kein Einmonatsausreißer.
- Angriff Abgrenzung: 2021-01 (3,067) weicht nicht in Sprungrichtung ab. 2021-02 (3,96) ist der erste abweichende Monat und liegt schon auf dem neuen Niveau. Die Varianten 2021-02..04 (+0,639), 2021-03..04 (+0,664) und 2021-04 (+0,867) wären nur Δ-Optimierung. Die Abgrenzung ist also definitionsgemäß.
- Schwachpunkt: Δ hängt stark am dünnen Ausreißer 2020-10 (2,50, n=8). Ohne ihn läge Δ bei etwa 0,38. Regel 4 rechnet aber mechanisch mit den bis zu sechs Vormonaten, daher besteht keine Regelverletzung. Die note nennt die starke Streuung des Vorniveaus. Nicht widerlegt.

(2) 2021-08..2021-09, Δ -1,0715. Vor 3,9965. Folge 3,395, verlangt 0,536, erreicht 0,602. Erster Folgemonat 2021-10 mit Abstand 0,4415. Der dünne Monat 2021-08 (n=7) wird durch 2021-09 (n=24) gestützt. Vortrend -0,09.
- Angriff "Verlängerung zur Regelrettung": 2021-08..2021-08 verfehlt Setzung (a) (0,587 < 0,763). Die Verlängerung ist aber definitionsgemäß begründet. 2021-08 (2,47) unterschießt das neue Niveau (2021-09 bis 2021-12: 3,30 bis 3,56) um etwa 0,9 und liegt damit außerhalb seiner Spanne. 2021-09 ist der erste Monat auf dem neuen Niveau und 0,62 vom alten entfernt.
- Gegenprobe Konsistenz: 2020-04 (3,867) liegt in der Spanne der Folgemonate 3,62 bis 3,73, ist also kein Unterschießen. 2023-09 (3,75) liegt nur 0,12 unter dem alten Niveau, ist also Rückkehr und nicht neues Niveau. Die Behandlung ist konsistent.
- Längere Varianten bis 2021-10, 2021-11 und 2022-01 sowie 2021-07..: period_to liegt hinter dem ersten Monat auf neuem Niveau, bzw. 2021-07 weicht nicht ab. Nicht widerlegt.

(3) 2023-01..2023-01, Δ +0,6823. Vor 3,391. Folge 3,788, verlangt 0,341, erreicht 0,397. Erster Folgemonat 2023-02 mit Abstand 0,592. Vortrend -0,10.
- Das Niveau hält etwa sieben Monate bei rund 3,9.
- Angriff Abgrenzung: 2022-12 (3,181) weicht nicht ab. 2023-01..2023-02 ist "verworfen", weil (b) mit 0,147 verfehlt wird. 2023-01 liegt schon auf dem neuen Niveau.
- Δ hängt teils am Ausreißer 2022-07 (2,756, n=9). Ohne ihn bleibt Δ bei etwa 0,555, also weiter ≥ 0,5. Nicht widerlegt.

Hauptangriff Regel 5, Schwankungsklausel: 2017-09..2017-09 ist im Rechner "regelkonform", Δ -0,675. Als Kandidat würde die Stelle 2021-02 (0,556) als vierte verdrängen und eine Schwankungsangabe in jeder note erzwingen.
- Die Prüfung stützt den Annotator: Zwei dünne Einbruchmonate (n=6, n=8) stützen sich nur gegenseitig. 2017-11 liegt mit 3,50 wieder auf dem Vorniveau 3,525.
- 2017-09..2017-10 ist "verworfen": erster Folgemonat mit Abstand 0,025, Folge-Abstand 0,163 < 0,334.
- 2017-09 allein besteht Setzung (a) nur mit 0,349 gegen verlangt 0,337, und das nur durch 2017-10.
- Damit fehlt das von der Definition verlangte Bleiben auf neuem Niveau (Regel 4 Satz 2 sinngemäß). Ich verwerfe die Stelle zu Recht. Eine Regel, die sie als Kandidaten erzwingt, gibt es nicht.

Weitere regelkonforme Scan-Stellen:
- 2016-02..2016-02 (+0,551): Der Rechner meldet selbst "Vorniveau bewegt sich bereits in Richtung des Sprungs (+0,32); Trend prüfen (Regel 2)". 2016-01 (3,258) liegt über allen Vorniveau-Monaten (2,55 bis 3,14) und ist der erste abweichende Monat. Die definitionsgemäße Abgrenzung 2016-01..2016-02 ist ein Zweifelsfall (+0,458).
- 2020-04..2020-05 (+0,542): Definitionsgemäß ist 2020-04..2020-04, und das ist "verworfen" (Setzung (a) 0,221 < 0,332).
- 2023-08..2023-09 (-0,548): Einzeleinbruch, 2023-09 ist zurück auf dem alten Niveau. 2023-08..2023-08 ist "verworfen".
- Selbst wenn man eine dieser drei Stellen zählte: Ihr |Δ| liegt unter 0,556, die Auswahl bliebe also gleich. Nur die Schwankungsklausel würde dann greifen. Weil die Verwerfungen definitionsgemäß begründet sind, bleibt das Ergebnis des Annotators.

Kandidaten des früheren Laufs:
- 2019-08..2019-08: "verworfen", (a) 0,258 < 0,440, (b) 0,231 < 0,25. Auch 2019-08..2019-09 ist "verworfen" ((b) 0,203).
- 2021-08..2021-08: "verworfen" ((a) 0,587 < 0,763). Die Stelle ist durch den Eintrag 2021-08..2021-09 abgedeckt.
- 2023-08..2023-08: "verworfen" ((a) 0,389 < 0,487, (b) 0,123).
- Keiner der drei wird damit ein Eintrag.

Notes: Die Reihenfolge nach Regel 11 ist eingehalten. Die Zahlen sind identisch mit pruefe. Der dünne Monat im Zeitraum ist mit Anzahl genannt: 2021-08, n=7. Die Streuungshinweise stimmen: 2,50/4,01 sind 2020-10/2020-09, 2,76/4,05 sind 2022-07/2022-09.

Zweifelsfälle: Bei drei Einträgen mit |Δ| ≥ 0,556 kann kein Zweifelsfall unter 0,5 nach Regel 5 je zu den drei deutlichsten gehören. Die leere Liste ist daher korrekt.

**Vollständigkeit (Prüfer):** Der Scan liefert 19 regelkonforme Varianten in 7 Gruppen und 43 Zweifelsfall-Varianten in 12 Gruppen. Alle Gruppen sind behandelt.

Regelkonforme Gruppen:
- 2016-01..07: verworfen. Die definitionsgemäße Abgrenzung 2016-01..2016-02 ist ein Zweifelsfall (+0,458). Der Rechner meldet einen Trendhinweis für 2016-02. Die übrigen Varianten wären nur Verlängerung.
- 2017-09: verworfen. Zweimonatiger dünner Einbruch mit Rückkehr, 2017-11 liegt mit 3,50 auf dem Vorniveau. Die Variante 2017-09..10 ist "verworfen".
- 2020-04..05: verworfen. Die definitionsgemäße Abgrenzung 2020-04..2020-04 ist "verworfen" (Setzung a).
- 2021-02..04: eingetragen als 2021-02..2021-02.
- 2021-07/08..2022-01: eingetragen als 2021-08..2021-09.
- 2023-01: eingetragen.
- 2023-08..09: verworfen. Einzeleinbruch, 2023-09 zurück auf altem Niveau. 2023-08..08 ist "verworfen".

Zweifelsfall-Gruppen: 2013-06/08, 2014-06..10, 2015-11..2016-08, 2018-07, 2019-01..04, 2019-08..2020-01, 2020-03..08, 2021-01..04, 2021-09..11, 2022-12..2023-04, 2023-06..2024-01 und 2024-07..12. Keine davon ist ein Eintrag, und keine wird als Zweifelsfall geführt.
- Bei drei Einträgen ist keine mit Regel 5 vereinbar: Ein vierter Zeitraum mit |Δ| < 0,5 würde nie zu den drei deutlichsten gehören.
- Mehrere sind zudem nicht definitionsgemäß abgegrenzt oder liegen unter drei bewerteten Monaten Abstand zu einem Eintrag. Das betrifft 2021-01..04, 2021-03, 2021-09..11 und 2023-01..04.

Weitere Prüfungen:
- 2011-03 und 2013-01: "verworfen", weil das Vorniveau weniger als drei bewertete Monate umfasst.
- Kandidaten des früheren Laufs (2019-08, 2021-08, 2023-08, jeweils einmonatig): alle drei im Rechner "verworfen" (Setzung a bzw. a und b).

Ergebnis: Eine regelkonforme, definitionsgemäße Stelle, die nach Regel 5 fehlt, gibt es nicht. Das Ergebnis des Annotators bleibt unverändert.

Unabhängigkeit: Gelesen bzw. genutzt habe ich nur die Serien-CSV über dz1_rechner.py (tabelle, scan, pruefe, satz). Keine Repository-Datei wurde geändert.


## Cancom (ID 25, 115 bewertete Monate)

**Ergebnis:** 3 Einträge, 0 Zweifelsfälle für Stufe B.

- Eintrag 2016-08 bis 2016-08, rise, Δ +1.036: Vorniveau 3,3 (2015-11 bis 2016-06, n=5-10); Zeitraum 4,3 (n=5); Δ +1,04; rise; Reihe schwankt stark (13 regelkonforme Kandidatengruppen), nur die drei deutlichsten behalten; Vorniveau streut 2,46 bis 4,29; dünn: 2016-08 mit n=5, gestützt durch 2016-10 (4,26, n=5); Anker: keiner; Reihe allein.
- Eintrag 2021-07 bis 2021-07, fall, Δ -1.153: Vorniveau 3,8 (2020-11 bis 2021-04, n=5-19); Zeitraum 2,6 (n=8); Δ -1,15; fall; Reihe schwankt stark (13 regelkonforme Kandidatengruppen), nur die drei deutlichsten behalten; dünn: 2021-07 mit n=8, gestützt durch 2021-09 (3,08, n=11); neues Niveau hält bis 2021-10 (2,77), 2021-11 wieder 3,69; Anker: keiner; Reihe allein.
- Eintrag 2023-12 bis 2023-12, rise, Δ +0.855: Vorniveau 3,0 (2023-06 bis 2023-11, n=6-24); Zeitraum 3,8 (n=7); Δ +0,85; rise; Reihe schwankt stark (13 regelkonforme Kandidatengruppen), nur die drei deutlichsten behalten; Vorniveau enthält Einbruch 2023-06 bis 2023-08 und Zwischenhoch 2023-09/2023-10 (Vortrend +0,86, kein gleichmäßiger Trend); dünn: 2023-12 mit n=7, gestützt durch 2024-01 (3,78, n=5); Anker: keiner; Reihe allein.

**Auswahl (Annotator):** Die Cancom-Reihe der Mitarbeitenden (115 bewertete Monate) schwankt stark. Der Scan findet 13 regelkonforme Gruppen. Je Gruppe habe ich die definitionsgemäße Abgrenzung bestimmt: period_from ist der erste deutlich abweichende Monat, period_to der erste Monat auf dem neuen Niveau. Danach habe ich den Trendfall geprüft. Nicht definitionsgemäß sind 2024-04..05 (erster abweichender Monat ist 2024-05, scheitert an Setzung a) und 2018-11..12 (2018-11 allein scheitert, 2018-12 liegt nicht auf dem neuen Niveau). Damit bleiben mehr als drei Kandidaten. Nach Regel 5 behalte ich die drei mit dem größten |Δ|: 2021-07 (-1,153), 2016-08 (+1,036) und 2023-12 (+0,855). Im Cluster 2023 liegen 2023-06, 2023-09 und 2023-12 jeweils nur 2 bewertete Monate auseinander. Die Zusammenfassung 2023-09..12 ist nur ein Zweifelsfall (+0,472), darum bleibt der deutlichere Sprung 2023-12. Dessen Vortrend-Hinweis (+0,86) geht auf den Einbruch 2023-06 bis 08 zurück, nicht auf einen gleichmäßigen Anstieg über mehr als sechs Monate. Regel 2 greift also nicht. Der Rechner (satz) bestätigt die Auswahl: Anzahl 3, Abstände 48 und 24 bewertete Monate. Jede note nennt die Schwankung der Reihe. Zweifelsfälle nehme ich keine auf, weil ein vierter Zeitraum nach Regel 5 nicht mehr zulässig ist. Alle Zahlen stammen aus dem Rechner dz1_rechner.py (tabelle, scan, pruefe, satz) für /Users/vaios/EPA-Bachelorarbeit/EPA-Bachelorarbeit/backend/data/series/25_cancom_employee.csv.

**Verworfene Kandidaten (32):**

- 2023-01..2023-01 (rise): Regel 5 Anzahl: regelkonform und definitionsgemäß, aber nur viertgrößtes |Δ|, nicht unter den drei deutlichsten. Δ +0,728 (Vor 3,176, Niv 3,904, n=24); Folgemittel 3,679, Abstand 0,503 >= 0,364
- 2024-10..2024-10 (rise; Gruppe 2024-08..2024-12): Regel 5 Anzahl (nicht unter den drei deutlichsten). Definitionsgemäß 2024-10 (2024-08 nur +0,49 und Rückfall 2024-09 auf 3,266); Trendprüfung Regel 2: Vortrend +0,62 stammt aus Einbruch 2024-05/06, kein gleichmäßiger Anstieg über >6 Monate. 2024-10..10 Δ +0,717 (Vor 3,012, Niv 3,728), regelkonform; Alternative 2024-08..2024-10 Δ +0,512 regelkonform; weitere Varianten bis +0,809 (2024-11..11) nicht definitionsgemäß
- 2023-06..2023-06 (fall): Regel 5: Abstand zu 2023-09 nur 2 bewertete Monate, gegenläufig; insgesamt nicht unter den drei deutlichsten. Δ -0,6685 (Vor 3,506, Niv 2,837), regelkonform; 2023-06..2023-08 Δ -0,947 scheitert an Setzung (a) (Folgeabstand 0,088 < 0,473; Rückkehr 2023-09 auf 3,72)
- 2023-09..2023-09 (rise): Regel 5 Abstand: nur 2 bewertete Monate zu 2023-12 (und zu 2023-06); Zusammenfassung 2023-09..2023-12 nur Zweifelsfall, daher nur der deutlichere Sprung 2023-12 behalten. Δ +0,668 (Vor 3,052, Niv 3,72), regelkonform; 2023-09..2023-12 Δ +0,472 (Zweifelsfall); 2023-12 Δ +0,855
- 2025-03..2025-05 (fall; Gruppe 2025-02..2025-06): Regel 5 Anzahl (nicht unter den drei deutlichsten). Definitionsgemäß: erster deutlich abweichender Monat 2025-03 (-0,48), erster Monat auf neuem Niveau 2025-05; schrittweiser Abfall über 5 Kalendermonate, kein Trend nach Regel 2; Bleiben nur mit zwei Folgemonaten prüfbar (Reihenende). Δ -0,586 (Vor 3,702, Niv 3,116), regelkonform; Alternativen 2025-04..05 Δ -0,631, 2025-05..05 Δ -0,666, 2025-02..06 Δ -0,607 nicht definitionsgemäß; 2025-06..06 Δ -0,956 scheitert an Setzung (a) (0,085 < 0,478) und Dünn-Stützung
- 2022-07..2022-07 (fall): Regel 5 Anzahl: regelkonform und definitionsgemäß (period_to = erster Monat auf neuem Niveau = 2022-07), aber nicht unter den drei deutlichsten. Δ -0,583 (Vor 3,697, Niv 3,114); Variante 2022-07..2022-08 Δ -0,597 nicht definitionsgemäß
- 2020-03..2020-04 (rise): Regel 5 Anzahl: regelkonform (2020-03 erster abweichender Monat +0,33, 2020-04 erster Monat auf neuem Niveau), nicht unter den drei deutlichsten. Δ +0,572 (Vor 3,044, Niv 3,616); 2020-04..04 Δ +0,749 scheitert an Setzung (a) (0,347 < 0,375); 2020-04..05 Δ +0,819 scheitert an Setzung (a) (0,047 < 0,410)
- 2018-11..2018-11 (fall): Definition/Setzungen: definitionsgemäße Abgrenzung besteht die Regeln nicht (Setzung (a) und Dünn-Stützung); 2018-11..2018-12 nicht definitionsgemäß, da 2018-12 (3,555) nicht auf neuem Niveau; zudem Regel 5. 2018-11..11 Δ -1,213, Folgeabstand 0,472 < 0,606, n=5 ohne Stützung; 2018-11..12 Δ -0,535 regelkonform
- 2014-01..2014-01 (fall): Regel 5 Anzahl: kleinstes |Δ| der regelkonformen Gruppen; zudem 2014-03 (3,825) wieder auf altem Niveau. Δ -0,506 (Vor 3,773, Niv 3,267, n=6); 2014-01..2014-02 Δ -0,750 scheitert an Setzung (a) (0,137 < 0,375)
- 2024-05..2024-05 (fall; Scan-Variante 2024-04..2024-05): Definition: erster abweichender Monat ist 2024-05 (2024-04 = 3,65 liegt über dem Vorniveau); definitionsgemäße Abgrenzung scheitert an Setzung (a), Rückkehr ab 2024-07; 2024-04..05 nur durch Verlängerung nach vorn regelkonform, daher kein Eintrag. 2024-05..05 Δ -1,432, Folgeabstand 0,397 < 0,716; 2024-05..06 Δ -1,218, 0,122 < 0,609; 2024-04..05 Δ -0,616 regelkonform
- 2013-02..2013-02 (rise): Setzung (a) und Dünn-Stützung nicht erfüllt; Vorniveau über 52 Kalendermonate verteilt. Δ +1,057 (Vor 2,983, Niv 4,04, n=5); Folgeabstand 0,465 < 0,528; 2013-01: Vorniveau nur 2 bewertete Monate
- 2017-08..2017-08 (fall): Regel 4 Einzelmonat mit Rückkehr; Setzung (a) und Dünn-Stützung nicht erfüllt. Δ -1,725 (n=5); Folgeabstand 0,087 < 0,863
- 2016-04..2016-04 (rise) und 2016-05..2016-05 (fall): Regel 4 Einzelmonatssprünge mit Rückkehr; Setzung (a) nicht erfüllt. 2016-04 Δ +1,030, Folgeabstand 0,007 < 0,515; 2016-05 Δ -0,942, Folgeabstand -0,465 < 0,471, n=5 ohne Stützung
- 2019-01..2019-01 (fall): Regel 4 Einzelmonat mit Rückkehr; Setzung (a) nicht erfüllt. Δ -1,028; Folgeabstand -0,010 < 0,514
- 2019-08..2019-08 (fall): Regel 4 Einzelmonat mit Rückkehr; Setzung (a) und Dünn-Stützung nicht erfüllt. Δ -1,041 (n=5); Folgeabstand 0,192 < 0,521
- 2022-12..2022-12 (fall): Regel 4 Einzelmonat mit Rückkehr; Setzung (a) und Dünn-Stützung nicht erfüllt. Δ -0,897 (n=7); Folgeabstand -0,386 < 0,449
- 2021-02..2021-02 (rise): Setzung (a) nicht erfüllt (Folgemittel zurück auf Vorniveau). Δ +0,874; Folgeabstand 0,037 < 0,437
- 2015-07..2015-07 (fall): Regel 4 Einzelmonat mit Rückkehr; Setzung (a) und Dünn-Stützung nicht erfüllt. Δ -0,862 (n=5); Folgeabstand 0,093 < 0,431
- 2019-03..2019-03 (rise): Regel 4 Einzelmonat mit Rückkehr; Setzung (a) nicht erfüllt. Δ +0,778; Folgeabstand 0,271 < 0,389
- 2020-07..2020-07 (fall): Regel 4 Einzelmonat mit Rückkehr; Setzung (a) und Dünn-Stützung nicht erfüllt. Δ -0,587 (n=7); Folgeabstand -0,109 < 0,293
- 2023-11..2023-11 (fall): Regel 4 Größe nicht erreicht; Setzung (a) nicht erfüllt. Δ -0,240
- 2013-06..2013-07 (rise): Regel 4 Zweifelsfall; nicht aufgenommen, da mit drei Einträgen nach Regel 5 (Anzahl) nicht vereinbar. Δ +0,323
- 2016-06..2016-08 (rise): Regel 4 Zweifelsfall; überlappt Eintrag 2016-08, nicht definitionsgemäß. Δ +0,308
- 2018-10..2018-12 / 2018-08..2018-12 / 2018-10..2019-03 (fall); 2019-03..2019-05 (rise): Regel 4 Zweifelsfälle; Regel 5 Anzahl nicht vereinbar. Δ -0,420 / -0,450 / -0,453; 2019-03..05 Δ +0,351
- 2020-03..2020-03 / 2020-03..2020-08 / 2020-04..2020-08 (rise): Regel 4 Zweifelsfälle; überlappen regelkonforme Variante 2020-03..2020-04; Regel 5 Anzahl. Δ +0,328 / +0,407 / +0,356
- 2021-11..2021-11 (rise): Regel 4 Zweifelsfall; Regel 5 Abstand zu Eintrag 2021-07 nur 2 bewertete Monate, Anzahl. Δ +0,303
- 2021-12..2022-02 / 2022-02..2022-02 (rise): Regel 4 Zweifelsfälle; Regel 5 Anzahl nicht vereinbar. Δ +0,397 / +0,454
- 2022-07..2022-09 / 2022-07..2022-10 (fall): Regel 4 Zweifelsfälle; überlappen regelkonforme Variante 2022-07; Regel 5 Anzahl. Δ -0,482 / -0,433
- 2023-09..2023-11 / 2023-09..2023-12 / 2023-10..2023-12 (rise): Regel 4 Zweifelsfälle; überlappen Eintrag 2023-12. Δ +0,366 / +0,472 / +0,372
- 2024-02..2024-05 / 2024-03..2024-05 (fall): Regel 4 Zweifelsfälle; nicht definitionsgemäß (erster abweichender Monat 2024-05, dessen Abgrenzung scheitert); Regel 5 Anzahl. Δ -0,370 / -0,451
- 2024-07..2024-10 bis 2024-07..2024-12, 2024-08..2024-08, 2024-08..2024-09, 2024-09..2024-10, 2024-12..2024-12 (rise): Regel 4 Zweifelsfälle; überlappen regelkonforme Gruppe 2024-08..2024-12; Regel 5 Anzahl. Δ +0,356 / +0,438 / +0,482 / +0,494 / +0,392 / +0,454 / +0,442
- 2025-02..2025-03 bis 2025-02..2025-05, 2025-03..2025-03, 2025-03..2025-04 (fall): Regel 4 Zweifelsfälle; überlappen regelkonforme Gruppe 2025; Regel 5 Anzahl. Δ -0,300 / -0,367 / -0,462 / -0,481 / -0,497

**Widerlegungsversuche (Prüfer):** Grundlage: dz1_rechner.py (tabelle, scan, pruefe, satz) auf 25_cancom_employee.csv.

(1) 2016-08..2016-08 rise. pruefe: regelkonform, Δ +1,0355, Vor 3,3045, Niv 4,34. Setzung (a): Folgeabstand 0,5378 >= 0,5178, also knapp bestanden. (b) 2016-10 liegt 0,9555 über dem Vorniveau. Dünn-Stützung durch 2016-10 (4,26, n=5) erfüllt. Widerlegungsversuche: (i) Einmonatsausreißer mit Rückkehr? Das neue Niveau hält über 2016-10 und die grauen Monate 2016-09/2016-11. Erst 2017-02 fällt der Wert auf 3,37; Setzung (a) ist erfüllt. Keine Widerlegung. (ii) Abgrenzung: 2016-07 ist grau, daher liegt der Rand nach Regel 3 auf 2016-08. Der erste abweichende Monat ist zugleich der erste Monat auf dem neuen Niveau, die Abgrenzung ist also definitionsgemäß. Die Verlängerung 2016-08..2016-10 scheitert an Setzung (a) (0,208 < 0,498). Sie wäre aber ohnehin nicht definitionsgemäß. (iii) Trend? Vortrend -0,109, kein Trend. (iv) Das Vorniveau streut stark: 2016-01 (4,06) und 2016-04 (4,29) lagen ähnlich hoch wie 2016-08. Das ist ein inhaltlicher Zweifel, aber keine Regelverletzung, und die note nennt die Streuung. Eintrag bleibt.

(2) 2021-07..2021-07 fall. pruefe: regelkonform, Δ -1,153, Vor 3,765, Niv 2,612. Setzung (a): 0,5843 >= 0,5765, knapp bestanden. (b) 2021-09 liegt 0,683 unter dem Vorniveau. Dünn-Stützung durch 2021-09 (3,08, n=11) erfüllt. Widerlegungsversuche: (i) Der Abfall beginnt schon in den grauen Monaten 2021-05/2021-06. Nach Regel 3 liegt der Rand auf dem nächsten bewerteten Monat, also 2021-07. Definitionsgemäß. (ii) Die Verlängerungen 2021-07..09 und 2021-07..10 scheitern an Setzung (a) und wären nicht definitionsgemäß, da 2021-07 schon auf dem neuen Niveau liegt. (iii) Rückkehr erst 2021-11 (3,69), das Niveau hält zwei bewertete Folgemonate lang. Kein Trend (Vortrend +0,388, nicht gleichmäßig). Eintrag bleibt.

(3) 2023-12..2023-12 rise. pruefe: regelkonform, Δ +0,8547, Vor 2,9883, Niv 3,843. Setzung (a): 0,4463 >= 0,4273. (b) 2024-01 liegt +0,79 über dem Vorniveau. Dünn-Stützung durch 2024-01 (3,78, n=5) erfüllt. Der Rechner gibt den Hinweis Vortrend +0,86. Widerlegungsversuche: (i) Trend nach Regel 2? Die Folge 2023-06..2024-01 lautet 2,84 / 2,22 / 2,62 / 3,72 / 3,67 / 2,87 / 3,84 / 3,78. Das ist ein Einbruch mit Erholung und Rückschlag, kein gleichmäßiger Anstieg über mehr als sechs Monate. Kein Trend. (ii) Ist 2023-12 nur eine Erholung nach dem Einmonatstief 2023-11 (n=24)? Dann wäre der eigentliche Sprung 2023-09 (regelkonform, Δ +0,668). Allerdings liegen 2023-09 und 2023-12 laut satz nur 2 bewertete Monate auseinander (ok=false). Die Zusammenfassung 2023-09..2023-12 ist nur ein Zweifelsfall (+0,472). Regel 5 verlangt dann ausdrücklich den deutlicheren Sprung, also 2023-12 (|Δ| 0,855 > 0,668). Das ist eine Regelfolge und keine Δ-Optimierung. (iii) Rückkehr? Die Folgemonate 3,78 / 3,07 / 3,46 liegen alle über dem Vorniveau von 2,99. Keine Rückkehr zum alten Niveau. (iv) Abgrenzung: 2023-11 (2,867) liegt unter dem Vorniveau. Der erste abweichende Monat und der erste Monat auf dem neuen Niveau sind beide 2023-12. Die Verlängerung 2023-12..2024-01 scheitert an Setzung (a). Eintrag bleibt.

Regel 5 Anzahl: Der Scan liefert 13 regelkonforme Gruppen, also mehr als drei Kandidaten. Die definitionsgemäßen |Δ| der übrigen Gruppen: 2023-01 0,728; 2024-10 0,717 (keine Variante der Gruppe 2024-08..12 übersteigt 0,809); 2023-06 und 2023-09 je 0,668; 2025-Gruppe höchstens 0,666; 2024-04..05 0,616; 2022-07 0,583 bzw. 0,597; 2020-03..04 0,572; 2018-11..12 0,535; 2014-01 0,506. Alle liegen unter 0,855. Damit sind 2021-07, 2016-08 und 2023-12 die drei deutlichsten. Das gilt unabhängig davon, wie die Abgrenzungsfragen in den kleineren Gruppen (2018, 2024-04/05, 2024-08..12, 2025) entschieden werden. satz für die Auswahl: Anzahl 3, Abstände 48 und 24 bewertete Monate, ok. Jede note nennt die Schwankung der Reihe.

Notes nach Regel 11: Vorniveau, Zeitraum, Δ, Richtung und Anker stimmen in allen drei Einträgen wörtlich mit dem note_geruest aus pruefe überein. Die n-Spannen 5-10, 5-19 und 6-24 stimmen. Die Zeitraum-Monate mit 5-9 Bewertungen sind mit Anzahl genannt (2016-08 n=5, 2021-07 n=8, 2023-12 n=7). Im Zeitraum liegt kein nicht bewerteter Monat. Die Zusatzangaben sind gegen die Tabelle geprüft: Vorniveau-Streuung 2,46 bis 4,29; 2021-10 = 2,77; 2021-11 = 3,69.

Kandidaten des früheren Laufs: 2016-08 und 2021-07 sind identisch mit den Einträgen. 2024-05..2024-05 ist nach pruefe verworfen (S_folgeniveau: 0,397 < 0,716, Rückkehr ab 2024-07). 2024-05..2024-06 ist ebenfalls verworfen (0,122 < 0,609). 2024-04..05 ist zwar regelkonform (Δ -0,616), aber nicht definitionsgemäß: 2024-04 (3,65) liegt über dem Vorniveau. Zudem läge es nach Regel 5 nicht unter den drei deutlichsten. Kein Eintrag. Ergebnis: Keiner der drei Einträge ist widerlegt.

**Vollständigkeit (Prüfer):** Scan: 27 regelkonforme Zeiträume in 13 Gruppen, 31 Zweifelsfälle in 11 Gruppen.

Regelkonforme Gruppen:
- 2014-01: verworfen nach Regel 5 Anzahl (Δ -0,506)
- 2016-08: Eintrag
- 2018-11..12: verworfen. Nicht definitionsgemäß, weil 2018-11 allein an Setzung (a) und an der Dünn-Stützung scheitert und 2018-12 nicht auf dem neuen Niveau liegt; zudem Regel 5 Anzahl (0,535)
- 2020-03..04: verworfen nach Regel 5 Anzahl (0,572)
- 2021-07: Eintrag
- 2022-07 (und Variante 2022-07..08): verworfen nach Regel 5 Anzahl (0,583/0,597)
- 2023-01: verworfen nach Regel 5 Anzahl; viertgrößtes |Δ| 0,728
- 2023-06: verworfen; Abstand zu 2023-09 nur 2 bewertete Monate, gegenläufig, und Regel 5 Anzahl (0,668)
- 2023-09: verworfen; Abstand zu 2023-12 nur 2 bewertete Monate, die Zusammenfassung ist nur ein Zweifelsfall, daher bleibt der deutlichere Sprung 2023-12 (0,668 < 0,855)
- 2023-12: Eintrag
- 2024-04..05: verworfen. Nicht definitionsgemäß, weil der erste abweichende Monat 2024-05 ist und dessen Abgrenzung an Setzung (a) scheitert; zudem Regel 5 Anzahl (0,616)
- Gruppe 2024-08..12 (10 Varianten): verworfen nach Regel 5 Anzahl. Höchstes |Δ| 0,809, unter 0,855 bei jeder Abgrenzung
- Gruppe 2025-02..06 (5 Varianten): verworfen nach Regel 5 Anzahl. Höchstens 0,666

Zweifelsfall-Gruppen: 2013-06..07, 2016-06..08, 2018-08/10..2018-12/2019-03 mit 2019-03..05, 2020-03-Gruppe, 2021-11, 2021-12..2022-02/2022-02, 2022-07..09/10, 2023-09/10..2023-11/12, 2024-02/03..2024-05, 2024-07..12-Gruppe, 2025-02/03..-Gruppe. Alle sind beim Annotator begründet verworfen: Sie überlappen einen Eintrag oder eine regelkonforme Gruppe, und mit drei Einträgen wäre jeder weitere Zeitraum nach Regel 5 (höchstens 3) nicht vereinbar. Darum keine Zweifelsfälle.

Kandidaten des früheren Laufs: 2016-08 und 2021-07 sind übernommen. 2024-05 scheitert an Setzung (a).

Es fehlt keine regelkonforme, definitionsgemäße Stelle, die nach Regel 5 in die Auswahl gehört. Alle 13 regelkonformen und alle 11 Zweifelsfall-Gruppen sind behandelt.


## Carl Zeiss (ID 26, 99 bewertete Monate)

**Ergebnis:** 0 Einträge, 0 Zweifelsfälle für Stufe B.


**Auswahl (Annotator):** Carl Zeiss, Mitarbeitende, Gesamtbewertung (99 bewertete Monate): kein Eintrag und kein Zweifelsfall. Die Reihe pendelt ab 2018-09 um etwa 4,0 bis 4,3 und davor um etwa 3,7. Viele Einzelmonatsausschläge liegen dazwischen (2016-11, 2019-04, 2019-11, 2021-02, 2023-03, 2024-12, 2025-04 u. a.), und jeder kehrt sofort zurück.

Der Scan liefert nur eine regelkonforme Variante, 2023-04..2023-04 (Δ +0,5035). Sie ist aber nach der Definition kein bleibender Niveausprung. Das Vorniveau 4,0175 ist durch den Dip 2023-03 (3,278, n=9) gedrückt. Das erhöhte Niveau hält nur 2023-04/05. Ab 2023-07 liegt die Reihe wieder beim Vorniveau: Die Zwei-Monats-Variante scheitert an S_folgeniveau mit Folgemittel 4,0527 und Abstand +0,0352. Das Niveau vor dem Dip lag bei 4,1823. Setzung (a) wird nur mit 0,0005 Reserve erfüllt, weil 2023-05 im Folgefenster liegt. Deshalb verworfen.

Die sichtbarste Niveauverschiebung, um 2018-09 von etwa 3,7 auf etwa 4,1, ist kein Trend (Vortrend -0,0283). Ihre definitionsgemäße Abgrenzung 2018-09..2018-09 (Δ +0,4975) und ebenso 2018-09..2018-10 (Δ +0,464) scheitert aber an der Stützungsregel: 2018-09 hat nur n=7, und 2018-10 liegt bloß +0,43 über dem Vorniveau. Sie ist daher nicht 'sonst regelkonform' und kein Zweifelsfall. Die Rechner-Zweifelsfälle 2018-09..2018-11 (verlängert) und 2018-10..2018-10 (Beginn nach dem ersten abweichenden Monat) sind nicht definitionsgemäß. Der Autor kann diese Stelle in Stufe B gesondert betrachten.

Die übrigen Rechner-Zweifelsfälle sind nicht definitionsgemäß. 2020-05..2020-08 ist Einzelspitze plus Erholung nach dem Dip 2019-11. 2024-11..2025-03 enthält den Einzeldip 2024-12 samt Rückkehr. 2025-05 ist die Rückkehr nach den Dips 2024-12 und 2025-04.

satz mit leerer Auswahl: ok (Anzahl 0).

**Verworfene Kandidaten (33):**

- 2023-04..2023-04 (rise): Definition, Niveau bleibt nicht (Regel 4 Satz 2 sinngemäß): Im Rechner formal regelkonform, aber kein bleibender Niveausprung. Δ >= 0,5 kommt nur zustande, weil der Einzelmonatsdip 2023-03 im Vorniveau steckt. Setzung (a) ist nur knapp erfüllt, weil 2023-05 als Teil desselben kurzen Ausschlags im Folgefenster liegt. Ab 2023-07 kehrt die Reihe auf das Vorniveau zurück.. Δ +0,5035; Vor 4,0175 (2022-08..2023-03, darin 2023-03 = 3,278 mit n=9); Niv 4,521 (n=24); Folgemittel 4,2697, Abstand 0,2522 bei verlangten 0,2517; Folgemonate 2023-05 4,608, 2023-07 4,123, 2023-08 4,078. Die Variante 2023-04..2023-05 (Δ +0,547) scheitert an S_folgeniveau: Folgemittel 4,0527 (2023-07..09), Abstand +0,0352 bei verlangten 0,2735; erster Folgemonat 2023-07 mit Abstand +0,1055. Vor-Dip-Niveau 4,1823 (2022-07..2023-02). Vortrend -0,3697, also kein Trend.
- 2023-03..2023-03 (fall): S_folgeniveau und R3_stuetzung_duenn: Einzelmonatsdip mit sofortiger Rückkehr. Δ -0,9043; Vor 4,1823 (2022-07..2023-02); Niv 3,278 (n=9); Folgemittel 4,4173; erster Folgemonat 2023-04 4,521 mit Abstand -0,3387; 2023-03 (n=9) ohne Stützung
- 2023-03..2023-05 (fall): R4_groesse, S_folgeniveau, R3_stuetzung_duenn: Dip und Rückprall heben sich auf. Δ -0,0467; Vor 4,1823; Niv 4,1357 (n=9, 24, 13)
- 2018-09..2018-09 (rise), definitionsgemäße Abgrenzung der Stelle 2018: R4_groesse (Zweifelsbereich) und R3_stuetzung_duenn gescheitert. Damit nicht 'sonst regelkonform', also weder Eintrag noch Zweifelsfall (im Protokoll vermerkt). Kein Trend (Vortrend -0,0283).. Δ +0,4975; Vor 3,7165 (2018-02..2018-08, n=8-25); Niv 4,214 (n=7); Folgemittel 4,1547; erster Folgemonat 2018-10 4,147 (n=85) mit Abstand +0,4305 < 0,5, damit keine Stützung für 2018-09 (n=7)
- 2018-09..2018-10 (rise): R4_groesse (Zweifelsbereich) und R3_stuetzung_duenn gescheitert. Δ +0,464; Vor 3,7165; Niv 4,1805 (n=7, 85); 2018-09 (n=7) ohne Stützung: 2018-10 +0,43, erster Folgemonat 2018-11 4,067 mit Abstand +0,3505
- 2018-09..2018-11 (rise): Im Rechner Zweifelsfall, aber nicht definitionsgemäß: period_to liegt hinter dem ersten Monat auf dem neuen Niveau (2018-09 und 2018-10 liegen schon darauf). Die Verlängerung besteht die Stützung nur über 2019-02 (Verlängern, damit eine Regel besteht).. Δ +0,4262; Vor 3,7165; Niv 4,1427 (n=7, 85, 6); Folgemittel 3,9333 (2019-02 4,25, 2019-03 4,383, 2019-04 3,167); Stützung über 2019-02 mit Abstand +0,5335
- 2018-10..2018-10 (rise): Im Rechner Zweifelsfall, aber nicht definitionsgemäß: Der Zeitraum beginnt nach dem ersten abweichenden bewerteten Monat 2018-09, der dadurch ins Vorniveau fällt (Kürzen, damit die Stützungsregel besteht). Δ +0,356; Vor 3,791 (2018-04..2018-09, darin 2018-09 4,214); Niv 4,147 (n=85); Folgemittel 4,2333
- 2018-10..2018-11 (rise): R4_groesse, S_folgeniveau, R3_stuetzung_duenn. Δ +0,316; Vor 3,791; Niv 4,107; Folgemittel 3,9333, Abstand 0,1423 bei verlangten 0,158
- 2020-05..2020-08 (rise): Im Rechner Zweifelsfall, aber nicht definitionsgemäß. 2020-05 ist ein einzelner Ausschlag, 2020-06 fällt sogar unter das Vorniveau zurück. Die definitionsgemäße Variante 2020-05..2020-05 scheitert an S_folgeniveau. Trendfall/Rückprall: Das Vorniveau ist durch den Dip 2019-11 gedrückt (Vortrend +0,1907). Gemessen am Niveau vor dem Dip gibt es keinen Sprung.. Δ +0,3257; Vor 3,7413 (2019-10..2020-04, darin 2019-11 3,2 mit n=5); Monate 4,446 / 3,679 / 3,963 / 4,18 (n=13, 14, 16, 5); Folgemittel 4,1817; Vor-Dip-Niveau 4,0473 (2019-05..2019-10)
- 2020-05..2020-05 (rise): S_folgeniveau: Einzelmonatsspitze mit Rückkehr. Δ +0,7047; Vor 3,7413; Niv 4,446 (n=13); Folgemittel 3,9407, Abstand 0,1993 bei verlangten 0,3523; erster Folgemonat 2020-06 3,679 mit Abstand -0,0623
- 2020-07..2020-08 und 2020-08..2020-08 (rise): R4_groesse (unter 0,30) und R3_stuetzung_duenn: allmähliche Erholung, kein Sprung. 2020-07..08: Δ +0,1927, Vor 3,8788; 2020-08..08: Δ +0,247, Vor 3,933; 2020-08 (n=5) ohne Stützung
- 2019-11..2019-11 und 2019-11..2019-12 (fall): S_folgeniveau und R3_stuetzung_duenn: Dip mit Rückkehr. 2019-11: Δ -0,8473, Vor 4,0473, Niv 3,2 (n=5), Folgemittel 3,7937 (Abstand 0,2537 bei verlangten 0,4237); 2019-11..12: Δ -0,6283, Folgemittel 3,8367, erster Folgemonat 2020-01 3,986 mit Abstand 0,0613
- 2024-11..2025-03 (fall): Im Rechner Zweifelsfall, aber nicht definitionsgemäß: 2024-11 weicht nicht deutlich ab. Der Zeitraum enthält den Einzeldip 2024-12 und die Rückkehrmonate 2025-01..03. Die definitionsgemäße Variante 2024-12..2024-12 scheitert.. Δ -0,3027; Vor 4,2215 (2024-05..2024-10); Monate 3,971 / 2,944 / 4,381 / 4,131 / 4,167 (n=21, 9, 37, 35, 18); Folgemittel 4,0387
- 2024-12..2024-12 (fall): S_folgeniveau und R3_stuetzung_duenn: Einzelmonatsdip mit sofortiger Rückkehr. Δ -1,2512; Vor 4,1952 (2024-06..2024-11); Niv 2,944 (n=9); Folgemittel 4,2263, Abstand -0,0312; erster Folgemonat 2025-01 4,381
- 2024-11..2024-12 (fall): S_folgeniveau, R3_stuetzung_duenn. Δ -0,764; Vor 4,2215; Folgemittel 4,2263, Abstand -0,0048
- 2025-04..2025-04 (fall): R4_groesse (Zweifelsbereich) und S_folgeniveau: Einzelmonatsdip mit Rückkehr. Δ -0,4568; Vor 3,9878; Niv 3,531 (n=13); Folgemittel 4,2053; erster Folgemonat 2025-05 4,271 mit Abstand -0,2832
- 2025-05..2025-05 (rise): Im Rechner Zweifelsfall, aber nicht definitionsgemäß: Das Vorniveau ist durch die Einzeldips 2024-12 und 2025-04 gedrückt. 2025-05 ist die Rückkehr auf das bisherige Niveau, nicht die Abweichung davon. Am Reihenende gibt es nur 2 Folgemonate.. Δ +0,4168; Vor 3,8542 (2024-11..2025-04, darin 2,944 und 3,531); Niv 4,271 (n=14); Niveau 2025-01..03: 4,381 / 4,131 / 4,167; Vor-Dip-Niveau 4,1952 (2024-06..2024-11); Folgemittel 4,1725
- 2025-05..2025-06 (rise): R4_groesse (Zweifelsbereich), S_folgeniveau, R3_stuetzung_duenn. Δ +0,4383; Folgemonat 2025-07 4,031 mit Abstand 0,1768 bei verlangten 0,2192; 2025-06 (n=7) ohne Stützung
- 2013-01..2013-01 (fall): S_vorniveau_min3: nur 1 bewerteter Vormonat. Niv 3,76 (n=5); Vorniveau nur 2010-10 4,46 (n=5)
- 2013-08..2013-08 (fall): R4_groesse (Zweifelsbereich) und R3_stuetzung_duenn, daher kein Zweifelsfall; Vorniveau lückig über 32 Kalendermonate. Δ -0,448; Niv 3,583 (n=6), ohne Stützung
- 2015-10..2015-10 (rise): S_folgeniveau, R3_stuetzung_duenn: Einzelmonatsspitze. Δ +0,5233; Vor 3,7627; Niv 4,286 (n=7); Folgemittel 3,741; erster Folgemonat 2016-03 3,75
- 2016-06..2016-08 (fall), dazu 2016-06..2016-06 und 2016-08..2016-08: S_folgeniveau (bei 2016-08 allein zusätzlich R3_stuetzung_duenn): kurzer Abfall mit Rückkehr, danach Gegenspitze 2016-11. 2016-06..08: Δ -0,6957, Vor 3,9242, Niv 3,2285 (n=5, 3 grau, 6), Folgemittel 3,9093, erster Folgemonat 2016-11 4,671; 2016-06: Δ -0,5842, Folgemittel 3,8483; 2016-08: Δ -0,7577, Folgemittel 3,9093
- 2016-11..2016-11 (rise): S_folgeniveau, R3_stuetzung_duenn: Einzelmonatsspitze. Δ +0,9528; Vor 3,7182; Niv 4,671 (n=7); Folgemittel 3,5347; erster Folgemonat 2017-01 3,757
- 2017-02..2017-02 (fall): R4_groesse, S_folgeniveau, R3_stuetzung_duenn. Δ -0,4947; Niv 3,3 (n=5); Folgemittel 3,79
- 2017-09..2017-09 (rise): S_folgeniveau, R3_stuetzung_duenn: Einzelmonatsspitze. Δ +0,5168; Vor 3,6712; Niv 4,188 (n=8); Folgemittel 3,627; erster Folgemonat 2017-10 3,614
- 2019-04..2019-04 (fall): S_folgeniveau, R3_stuetzung_duenn: Einzelmonatsdip. Δ -0,9337; Vor 4,1007; Niv 3,167 (n=6); Folgemittel 3,998; erster Folgemonat 2019-05 4,094
- 2019-08..2019-08 (rise): R4_groesse, S_folgeniveau, R3_stuetzung_duenn. Δ +0,4843; Niv 4,45 (n=6); Folgemittel 3,68
- 2021-02..2021-02 (fall): S_folgeniveau, R3_stuetzung_duenn: Einzelmonatsdip. Δ -0,7322; Vor 4,0612; Niv 3,329 (n=7); Folgemittel 3,9207; erster Folgemonat 2021-03 4,083
- 2021-04..2021-04 (fall): S_folgeniveau: Einzelmonatsdip. Δ -0,5138; Vor 4,0228; Niv 3,509 (n=11); Folgemittel 4,2527; erster Folgemonat 2021-05 4,17
- 2021-05..2021-06 und 2021-06..2021-06 (rise): R4_groesse, S_folgeniveau, R3_stuetzung_duenn. 2021-05..06: Δ +0,349, Vor 3,911; 2021-06: Δ +0,4447, Vor 3,9053; Folgemittel jeweils 4,0757; 2021-06 (n=6) ohne Stützung
- 2022-01..2022-01 (rise): R4_groesse, S_folgeniveau. Δ +0,3183; Folgemittel 4,1607; erster Folgemonat 2022-02 3,93
- 2024-04..2024-04 (fall): R4_groesse, S_folgeniveau. Δ -0,3847; Folgemittel 4,126; erster Folgemonat 2024-05 4,129
- 2024-08..2024-08 (rise): R4_groesse, S_folgeniveau. Δ +0,3223; Folgemittel 4,1687; erster Folgemonat 2024-09 4,202

**Widerlegungsversuche (Prüfer):** Der Annotator hat keine Einträge und keine Zweifelsfälle. Geprüft habe ich deshalb, ob eine Verwerfung zu Unrecht erfolgte. Alle Zahlen habe ich mit pruefe nachgerechnet; sie stimmen mit den Angaben des Annotators überein.

1) 2023-04..2023-04 (rise, einzige im Rechner regelkonforme Variante)
- Rechner: regelkonform. Δ +0,5035; Vor 4,0175 (2022-08..2023-03, darin 2023-03 = 3,278 mit n=9); Niv 4,521 (n=24).
- Folgemittel 4,2697: Abstand 0,2522 bei verlangten 0,2517, also nur 0,0005 Reserve. Erster Folgemonat 2023-05 = 4,608.
- Widerlegungsversuch zugunsten eines Eintrags: Die Grenzen sind formal definitionsgemäß. 2023-04 ist der erste Monat, der nach oben abweicht, und zugleich der erste auf dem höheren Wert.
- Dagegen spricht: Das erhöhte Niveau hält nur 2023-04/05. Die Variante 2023-04..2023-05 scheitert klar an S_folgeniveau (Folgemittel 4,0527 aus 2023-07..09, Abstand +0,0352 bei verlangten 0,2735). Auch 2023-04..2023-07 scheitert an R4 (Δ +0,3998) und S_folgeniveau. Ab 2023-07 liegt die Reihe bei etwa 4,0 bis 4,1, also auf dem Vorniveau und sogar unter dem Niveau vor dem Dip (4,1823).
- Der Δ von mindestens 0,5 entsteht nur, weil der Einzelmonatsdip 2023-03 im Vorniveau steckt. Setzung (a) besteht nur, weil 2023-05 als Teil desselben kurzen Ausschlags im Folgefenster liegt.
- Die Definition verlangt, dass das Niveau nach dem Sprung auf dem neuen Niveau bleibt. Regel 4 Satz 2 schließt Ausschläge mit Rückkehr aus. Beides ist nicht erfüllt.
- Ergebnis: Die Verwerfung ist regelgedeckt. Ein Zweifelsfall ist nicht möglich, weil |Δ| = 0,5035 über 0,49 liegt. Das Ergebnis des Annotators bleibt.

2) Stelle 2018-09 (sichtbarste Niveauverschiebung, etwa 3,7 auf etwa 4,1; Vortrend -0,0283, also kein Trend)
- Definitionsgemäße Grenzen: 2018-09 ist der erste deutlich abweichende Monat (+0,50 zu Vor6). Er liegt mit 4,214 schon auf dem neuen Niveau, also gilt 2018-09..2018-09.
- 2018-09..2018-09 ist verworfen wegen R4_groesse (Δ +0,4975 < 0,5) und R3_stuetzung_duenn. 2018-09 hat n=7, und 2018-10 liegt nur +0,4305 über dem Vorniveau. Damit ist die Variante nicht 'sonst regelkonform' und kein Zweifelsfall.
- 2018-09..2018-10 ist ebenfalls verworfen (Δ +0,464; 2018-09 ohne Stützung, erster Folgemonat 2018-11 nur +0,3505).
- Die Rechner-Zweifelsfälle dieser Stelle sind nicht definitionsgemäß:
  - 2018-09..2018-11 (Δ +0,4262) ist über den ersten Monat auf dem neuen Niveau hinaus verlängert. Die Stützung besteht nur über 2019-02.
  - 2018-10..2018-10 (Δ +0,356) beginnt nach dem ersten abweichenden Monat 2018-09.
- Die Protokollregel 'Kürze oder verlängere keinen Zeitraum, damit eine Regel besteht' schließt beide aus. Bestätigt.

3) 2020-05..2020-08 (Rechner-Zweifelsfall, Δ +0,3257)
- 2020-05 (4,446) ist eine Einzelspitze. 2020-06 (3,679) fällt unter das Vorniveau 3,7413 zurück.
- Das Vorniveau ist durch den Dip 2019-11 (3,2, n=5) gedrückt.
- 2020-05..2020-05 scheitert an S_folgeniveau: Folgemittel 3,9407 bei verlangtem Abstand 0,3523; erster Folgemonat -0,0623.
- 2020-05..2020-07 scheitert an R4 (Δ +0,288).
- Der Zeitraum bis 2020-08 reicht über den ersten Monat auf dem Folgeniveau hinaus. Er ist keine definitionsgemäße Abgrenzung. Bestätigt.

4) 2024-11..2025-03 (Rechner-Zweifelsfall, Δ -0,3027)
- 2024-11 weicht nur -0,25 ab. Der Zeitraum enthält den Einzeldip 2024-12 (2,944, n=9) und die Monate 2025-01..03 (4,381 / 4,131 / 4,167), die auf dem alten Niveau liegen.
- Die Stützung gelingt nur über den nächsten Dip 2025-04.
- Die definitionsgemäße Variante 2024-12..2024-12 scheitert an S_folgeniveau (Abstand -0,0312) und an der Stützung. Bestätigt.

5) 2025-05..2025-05 (Rechner-Zweifelsfall, Δ +0,4168)
- Das Vorniveau 3,8542 ist durch die Einzeldips 2024-12 und 2025-04 gedrückt. 2025-05 (4,271) liegt auf dem Niveau von 2025-01..03 (Mittel etwa 4,23). Er ist also die Rückkehr zum bisherigen Niveau, kein sichtbarer Sprung.
- Ein Einwand wäre, die Grenzen seien formal definitionsgemäß. Die Definition verlangt aber eine Abweichung vom bisherigen Niveau, und die fehlt hier.
- Die Verwerfung bleibt (im Zweifel Ergebnis des Annotators).

6) Kandidat des früheren Laufs 2019-11..2019-11 (fall)
- Verworfen wegen S_folgeniveau (Folgemittel 3,7937, Abstand 0,2537 bei verlangten 0,4237) und R3_stuetzung_duenn (2019-11 n=5; 2019-12 nur -0,41).
- Auch die Varianten scheitern:
  - 2019-11..2019-12: S_folgeniveau, Stützung
  - 2019-11..2020-01: R4 -0,4393, S_folgeniveau, Stützung
  - 2019-11..2020-04: R4 -0,3777, Folgemittel 4,0293 mit Rückkehr
- Kein Eintrag, kein Zweifelsfall.

7) Stichproben der übrigen Verwerfungen
- Mit pruefe nachgerechnet: 2013-01, 2013-08, 2015-10, 2016-06..08, 2016-11, 2017-09, 2019-04, 2021-02, 2021-04, 2021-06, 2022-01, 2024-04, 2024-08, 2024-12..2025-01, 2025-04, 2025-01 und 2023-03 samt Varianten.
- Ergebnisse, Gründe und Zahlen stimmen mit den Angaben des Annotators überein. Es handelt sich durchweg um Einzelmonatsausschläge mit Rückkehr oder um |Δ| < 0,5.

8) satz
- Mit leerer Auswahl: ok (Anzahl 0).
- Regel 5 ist unproblematisch.

**Vollständigkeit (Prüfer):** Der Scan liefert eine regelkonforme Gruppe und vier Zweifelsfall-Gruppen. Alle sind behandelt:

- Regelkonforme Gruppe 2023-04..2023-04 (rise, Δ +0,503): begründet verworfen. Der Ausschlag dauert nur 2 Monate, danach kehrt das Vorniveau ab 2023-07 zurück. Der Δ ist nur durch den Dip 2023-03 im Vorniveau erreicht. Für einen Zweifelsfall ist |Δ| zu groß.
- Zweifelsfall-Gruppe 2018-09..2018-11 / 2018-10..2018-10: begründet verworfen. Beide Varianten sind nicht definitionsgemäß (verlängert bzw. verkürzt). Die definitionsgemäße Abgrenzung 2018-09..2018-09 scheitert an R4 (+0,4975) und an der Stützung (n=7). Vermerkt als Stelle, die der Autor in Stufe B gesondert betrachten kann.
- Zweifelsfall-Gruppe 2020-05..2020-08: begründet verworfen. Einzelspitze 2020-05 mit Rückfall 2020-06, dann Erholung nach dem Dip 2019-11. Nicht definitionsgemäß.
- Zweifelsfall-Gruppe 2024-11..2025-03: begründet verworfen. Enthält den Einzeldip 2024-12 samt Rückkehr. Die definitionsgemäße Variante 2024-12..2024-12 scheitert.
- Zweifelsfall-Gruppe 2025-05..2025-05: begründet verworfen. Rückkehr auf das bisherige Niveau nach den Einzeldips 2024-12 und 2025-04, keine Abweichung davon.
- Kandidat des früheren Laufs 2019-11..2019-11: verworfen (S_folgeniveau, R3_stuetzung_duenn). Auch alle Verlängerungen bis 2020-04 scheitern.

Es fehlt keine regelkonforme, definitionsgemäße Stelle. Endergebnis wie beim Annotator: 0 Einträge, 0 Zweifelsfälle; satz ok (Anzahl 0).


## Compugroup Medical Deutschland (ID 27, 76 bewertete Monate)

**Ergebnis:** 2 Einträge, 1 Zweifelsfälle für Stufe B.

- Eintrag 2019-06 bis 2019-08, fall, Δ -0.564: Vorniveau 4,2 (2018-06 bis 2019-05, n=5-22); Zeitraum 3,7 (n=6, 6, 6); Δ -0,56; fall; starke Streuung im Zeitraum: 2019-06 2,92, 2019-07 4,62 (über dem Vorniveau), 2019-08 3,47; dünn: 2019-06 (n=6), 2019-07 (n=6), 2019-08 (n=6); nächster bewerteter Monat erst 2020-04 (3,36), Folgemittel 3,94 knapp über der Mindestanforderung; Anker: keiner; Reihe allein.
- Eintrag 2022-08 bis 2022-11, fall, Δ -0.668: Vorniveau 3,7 (2021-11 bis 2022-07, n=5-13); Zeitraum 3,1 (n=8, 13, 6, 10); Δ -0,67; fall; Zwischenstufe 2022-09 (3,42) und 2022-10 (3,43) zwischen erstem Abfall 2022-08 (2,93) und Tiefpunkt 2022-11 (2,47); dünn: 2022-08 (n=8), 2022-10 (n=6); Anker: keiner; Reihe allein.
- Zweifelsfall 2021-04 bis 2021-05, rise, Δ +0.466: |Δ| 0,47 liegt im Band 0,30-0,49 (Regel 4), alle übrigen Regeln sind erfüllt (Rechner: zweifelsfall_0_3_bis_0_49). Folgemittel 3,93, Abstand 0,37 bei verlangten 0,23. Erster Folgemonat 2021-07 liegt +0,84 über dem Vorniveau. 2021-05 (n=7) wird durch 2021-04 und 2021-07 gestützt. 2021-04 ist der erste abweichende Monat; 2021-04 allein scheitert an Setzung (b), weil 2021-05 nur +0,15 über dem Vorniveau liegt. Es gibt keinen Vortrend in Sprungrichtung (Vortrend -0,355). Zweifel: Der Anstieg ist teilweise eine Rückkehr nach dem selbst nicht regelkonformen Einbruch 2020-10/2020-11. Mit den Einträgen nach Regel 5 vereinbar: satz mit 3 Zeiträumen ok, Abstände 7 und 9 bewertete Monate.

**Auswahl (Annotator):** Die Reihe ist bis 2015-08 grau. Danach liegt sie bis 2019-05 bei etwa 3,6-4,3 und von 2019-06 bis 2022-07 stark streuend bei etwa 3,7. Ab 2022-11 liegt sie bei 2,4-3,2, ab 2024-05 folgen mehrere Einmonatsspitzen (2024-05, 2024-10, 2024-12, 2025-03). Der Scan fand 3 regelkonforme Gruppen.

(1) 2019: Definitionsgemäß beginnt der Zeitraum 2019-06 (erster deutlich abweichender Monat, -1,31) und endet 2019-08 (erster Monat auf dem neuen Niveau). Ergebnis Δ -0,56, regelkonform. Trendprüfung: Die Vormonate 4,26/4,28/4,55/4,13/4,21/3,96 sinken nicht gleichmäßig, der Rechner meldet Vortrend -0,26. Der Abfall 2019-05 -> 2019-06 (-1,04) ist ein Sprung und kein Trend. Eingetragen mit Streuungs- und Dünn-Hinweis, denn alle Monate haben n=6, 2019-07 liegt über dem Vorniveau und das Folgemittel 3,94 erfüllt die Mindestanforderung nur knapp.

(2) 2022: Definitionsgemäß 2022-08 (erster Abfall, -0,81) bis 2022-11 (erster Monat auf dem neuen Niveau). Ergebnis Δ -0,67, regelkonform. Die Vormonate 2021-11 bis 2022-07 sind flach (Vortrend -0,16). Danach bleibt die Reihe ohne weiteren gleichmäßigen Abfall bei 2,4-3,2, daher ein Sprung und kein Trend.

(3) 2024: Die definitionsgemäße Abgrenzung 2024-05..2024-05 ist eine Einmonatsspitze mit sofortiger Rückkehr zum alten Niveau und scheitert an den Setzungen (a) und (b). Die Scan-Varianten bis 2024-07/08/09 würden den Zeitraum nur verlängern, damit die Regeln bestehen. Kein Eintrag.

Alle übrigen Einzelmonatssprünge scheitern an den Setzungen zum Folgeniveau oder an der Dünn-Stützung.

satz für 2019-06:2019-08 und 2022-08:2022-11 ist ok: 2 Zeiträume, Abstand 18 bewertete Monate. Es gibt nicht mehr als drei Kandidaten, daher keinen Schwankungshinweis.

Zweifelsfälle:
- 2021-04..2021-05 (Δ +0,47) wird aufgenommen. Es ist die definitionsgemäße Variante der Stelle und mit den Einträgen nach Regel 5 vereinbar (satz ok).
- 2017-07 wird wegen Trend (Regel 2) verworfen.
- Die Gruppen 2019, 2022 und 2023 werden nach Regel 5 verworfen (Überlappung oder Abstand), die Gruppe 2024-04 wegen der Abgrenzung.

Alle Zahlen stammen aus dem Rechner: dz1_rechner.py (tabelle, scan, pruefe, satz) auf /Users/vaios/EPA-Bachelorarbeit/EPA-Bachelorarbeit/backend/data/series/27_compugroup_medical_deutschland_employee.csv.

**Verworfene Kandidaten (29):**

- 2024-05..2024-05: Regel 4 (einzelner Monatssprung, altes Niveau kehrt zurück) / Setzung (a)+(b). Δ +1,51 (Vorniveau 2,65, Monat 4,15, n=15); erster Folgemonat 2024-06 2,86 nur +0,21 (<0,25); Folgemittel 2,84, Abstand 0,19 < verlangt 0,75; Rechner: verworfen (S_folgeniveau). Definitionsgemäße Abgrenzung der Stelle besteht die Regeln nicht, daher kein Eintrag.
- 2024-05..2024-07, 2024-05..2024-08, 2024-05..2024-09 (Scan regelkonform): Abgrenzung nach Definition (Verlängerung nur, damit die Regeln bestehen); Regel 4 einzelner Monatssprung. Δ +0,61 / +0,52 / +0,51; Niveau nur durch die Spitze 2024-05 (4,15) getragen; 2024-06 2,86 (n=16) und 2024-07 2,76 (n=18) liegen auf dem alten Niveau (Vorniveau 2,65, Vormonate 2,17-2,95); 2024-07 ist nicht der erste Monat auf einem neuen Niveau. 2024-05..2024-06: Δ +0,86, verworfen (S_folgeniveau, 2024-07 nur +0,11; Folgemittel-Abstand 0,27 < 0,43).
- 2024-04..2024-08, 2024-04..2024-09 (Zweifelsfall): Abgrenzung nach Definition. Δ +0,35 / +0,36; period_from 2024-04 (2,67) weicht nicht ab (Vorniveau 2,72); gleiche Einmonatsspitze 2024-05.
- 2019-05..2019-08 (Scan regelkonform): Abgrenzung nach Definition. Δ -0,50 regelkonform, aber 2019-05 (3,96, n=5) nur -0,28 vom Vor6 und damit nicht deutlich abweichend; erster deutlich abweichender Monat ist 2019-06 (2,92, -1,31) -> Eintrag 2019-06..2019-08 (Δ -0,56).
- 2019-06..2019-06: Setzung (a)+(b), Dünn-Stützung. Δ -1,31; erster Folgemonat 2019-07 4,62 über dem Vorniveau 4,23 (Abstand -0,39); Folgemittel-Abstand 0,42 < 0,66; 2019-06 (n=6) ohne Stützung.
- 2019-02..2019-07, 2019-04..2019-08, 2019-05..2019-07, 2019-06..2019-07 (Zweifelsfälle): Regel 5 (gleiche Stelle wie Eintrag 2019-06..2019-08) / Abgrenzung. Δ -0,31 / -0,34 / -0,41 / -0,46; überlappen den Eintrag; 2019-07 (4,62) liegt nicht auf dem neuen Niveau.
- 2022-08..2023-01, 2022-10..2022-11, 2022-10..2023-01, 2022-10..2023-03, 2022-11..2022-11, 2022-11..2023-01, 2022-11..2023-02, 2022-11..2023-03, 2022-11..2023-04 (Scan regelkonform): Abgrenzung nach Definition / Regel 5 (Überlappung mit Eintrag 2022-08..2022-11). Δ -0,66 / -0,55 / -0,50 / -0,58 / -0,99 / -0,67 / -0,54 / -0,67 / -0,65; erster deutlich abweichender Monat ist 2022-08 (2,93, -0,81 vom Vorniveau 3,73), erster Monat auf dem neuen Niveau 2022-11 (2,47), danach bleibt die Reihe bei 2,4-3,2. 2022-11..2022-11 hätte zudem Vortrend -0,39 (Vorniveau enthält bereits 2022-08..2022-10).
- 2022-08..2022-08: Dünn-Stützung (Setzung). Δ -0,81; 2022-08 (n=8) ohne Stützung, 2022-09 3,42 nur 0,31 unter dem Vorniveau 3,73; Rechner: verworfen (R3_stuetzung_duenn).
- 2022-06..2022-11, 2022-07..2022-10, 2022-07..2022-11, 2022-08..2022-10, 2022-09..2022-11, 2022-09..2023-01, 2022-09..2023-02, 2022-10..2023-02 (Zweifelsfälle): Regel 5 (Überlappung mit Eintrag 2022-08..2022-11). Δ -0,42 / -0,31 / -0,49 / -0,47 / -0,44 / -0,44 / -0,43 / -0,46; gleiche Stelle wie der Eintrag.
- 2023-01..2023-03, 2023-01..2023-04, 2023-01..2023-05, 2023-02..2023-03, 2023-02..2023-04, 2023-02..2023-05, 2023-02..2023-07, 2023-03..2023-05, 2023-03..2023-07 (Zweifelsfälle): Regel 5 (Abstand) / kein eigener Sprung. Δ -0,40 / -0,40 / -0,39 / -0,38 / -0,36 / -0,33 / -0,40 / -0,35 / -0,40; satz mit 2023-03..2023-05: Abstand 2022-11..2023-03 nur 2 bewertete Monate (nicht ok); Vorniveau (3,09-3,29) enthält noch die Übergangsmonate des Abfalls 2022, das neue Niveau ab 2022-11 liegt bereits bei 2,4-3,2.
- 2023-03..2023-03: Setzung (a)+(b). Δ -0,66 (Vorniveau 3,09, Monat 2,42); 2023-04 2,87 nur 0,21 unter dem Vorniveau (<0,25); Folgemittel-Abstand 0,31 < 0,33; Vortrend -0,35.
- 2017-07..2017-07 (Zweifelsfall): Regel 2 (Trend) und Regel 4 (|Δ| < 0,5). Δ +0,37 (Vorniveau 3,83, 2017-07 4,20, n=10); Rechner-Hinweis Vortrend +0,70; Anstieg in Stufen ohne abgrenzbaren Sprung: 2016-10/2016-11 3,70/3,56 -> 2017-03/2017-04 3,94/3,88 -> 2017-07 4,20 -> 2018-06..2018-08 4,26-4,55, also über mehr als sechs Kalendermonate; Sprung zum Vormonat (+0,32) nicht größer als die vorherigen Stufen.
- 2017-02..2017-02: Setzung (a)+(b), Dünn-Stützung. Δ +1,01 (Vorniveau 3,72, Monat 4,73, n=7); 2017-03 3,94 nur +0,22; Folgemittel-Abstand 0,29 < 0,50; ohne Stützung.
- 2017-11..2017-11: Setzung (a)+(b), Dünn-Stützung. Δ +0,85 (Vorniveau 3,91, Monat 4,76, n=5); 2018-02 3,77 unter dem Vorniveau (-0,14); Folgemittel-Abstand 0,10 < 0,42.
- 2016-12..2016-12: Setzung (a)+(b), Dünn-Stützung. Δ -0,64 (Vorniveau 3,82, Monat 3,18, n=5); 2017-02 4,73 (Abstand -0,91); Folgemittel 4,18 über dem Vorniveau.
- 2016-05..2016-05, 2016-05..2016-06: Setzung (a) bzw. (a)+(b), Dünn-Stützung. Δ +0,53 / +0,51 (Vorniveau 3,63, lückig über 31 Kalendermonate); Folgemittel 3,80 bzw. 3,615 (Abstand 0,17 < 0,27 bzw. -0,02); 2016-07 3,58 unter dem Vorniveau; 2016-05 (n=6) ohne Stützung.
- 2015-09..2015-09: Setzung Vorniveau mindestens drei bewertete Monate. nur 1 bewerteter Vormonat (2013-08, 3,10, n=5); nicht prüfbar.
- 2020-04..2020-04: Setzung (a)+(b), Dünn-Stützung. Δ -0,52 (Vorniveau 3,88, Monat 3,36, n=5); 2020-05 4,12 über dem Vorniveau (Abstand -0,23); Folgemittel-Abstand 0,15 < 0,26.
- 2020-07..2020-07: Setzung (a)+(b), Dünn-Stützung. Δ +0,62 (Vorniveau 3,74, Monat 4,36, n=7); 2020-10 2,72 (Abstand -1,02); Folgemittel 3,25 unter dem Vorniveau.
- 2020-10..2020-10, 2020-10..2020-11: Setzung (a) bzw. (a)+(b). Δ -1,09 / -0,81 (Vorniveau 3,81); 2020-10..2020-10: Folgemittel-Abstand 0,43 < 0,54; 2020-10..2020-11: 2020-12 3,75 nur 0,06 unter dem Vorniveau, Folgemittel-Abstand 0,07 < 0,41; altes Niveau kehrt zurück.
- 2021-03..2021-03: Regel 4, Setzung (a)+(b), Dünn-Stützung. Δ -0,48 (Vorniveau 3,60, Monat 3,11, n=8); 2021-04 4,34 über dem Vorniveau (Abstand -0,74).
- 2021-04..2021-04: Setzung (b). Δ +0,79 (Vorniveau 3,55, Monat 4,34, n=10); erster Folgemonat 2021-05 3,70 nur +0,15 (<0,25). Stelle als Zweifelsfall 2021-04..2021-05 geführt.
- 2021-04..2021-07: Setzung (a); Abgrenzung. Δ +0,59; Folgemittel-Abstand 0,25 < verlangt 0,29; zudem 2021-07 nicht der erste Monat auf dem neuen Niveau (das ist 2021-05).
- 2021-07..2021-07: Setzung (a), Dünn-Stützung. Δ +0,91 (Vorniveau 3,48, Monat 4,39, n=9); Folgemittel-Abstand 0,32 < 0,45; ohne Stützung.
- 2021-07..2021-10 (Zweifelsfall): Abgrenzung nach Definition / Regel 5 (Zusammenfassung). Δ +0,44; Anstieg beginnt bereits 2021-04, 2021-07 ist kein erster abweichender Monat; Abstand zu 2021-04..2021-05: 0 bewertete Monate; Zusammenfassung 2021-04..2021-10 = 7 Kalendermonate, verworfen (R2, R3, R4; Δ +0,41) -> nur die deutlichere Variante 2021-04..2021-05 (|Δ| 0,47) bleibt.
- 2024-01..2024-01: Setzung (a)+(b). Δ -0,67 (Vorniveau 2,835, Monat 2,17, n=13); 2024-02 2,88 über dem Vorniveau (Abstand -0,04); Folgemittel-Abstand 0,16 < 0,33.
- 2024-10..2024-10: Setzung (a), Dünn-Stützung. Δ +0,98 (Vorniveau 3,07, Monat 4,06, n=7); Folgemittel 2,84 unter dem Vorniveau (Abstand -0,23); ohne Stützung.
- 2024-12..2024-12: Setzung (a), Dünn-Stützung. Δ -0,85 (Vorniveau 3,17, Monat 2,31, n=7); Folgemittel 3,23 über dem Vorniveau (Abstand -0,06); ohne Stützung.
- 2025-03..2025-03: Setzung (a)+(b), Dünn-Stützung. Δ +0,68 (Vorniveau 3,11, Monat 3,79, n=8); einziger Folgemonat 2025-05 3,10 (Abstand -0,01); ohne Stützung.

**Widerlegungsversuche (Prüfer):** Eintrag 2019-06..2019-08 (fall, Δ -0,5642):
- pruefe: regelkonform. Vorniveau 4,231 aus 2018-06..2019-05 (n=5-22), Niveau 3,667, Folgemittel 3,9447. Abstand 0,2865 bei verlangten 0,2821, also knapp bestanden; erster Folgemonat 2020-04 mit Abstand 0,87. Dünn-Stützung für alle drei n=6-Monate ok.
- Widerlegungsversuch 1, Einmonatsausreißer mit Rückkehr (Regel 4): 2019-07 (4,62) liegt über dem Vorniveau; von den Folgemonaten liegen 2020-05 (4,12) und 2020-07 (4,36) wieder nahe am bzw. über dem alten Niveau. Die Setzungen (a) und (b) als Operationalisierung von Regel 4 sind aber erfüllt. Langfristig liegt die Reihe 2017-07..2019-05 im Mittel bei etwa 4,2 und 2019-06..2022-07 bei etwa 3,7 (eigene Mittelung der tabelle-Werte). Der Niveauwechsel ist also real, nur verrauscht. Nicht widerlegt.
- Versuch 2, Trend (Regel 2): Der Rechner-Hinweis Vortrend -0,26 kommt von 2019-05 (3,96) nach den Werten 4,13-4,55. Ein gleichmäßiger Abfall über mehr als sechs Monate liegt nicht vor; 2019-05→2019-06 ist ein Sprung von -1,04. Nicht widerlegt.
- Versuch 3, Abgrenzung: 2019-05..2019-08 (Δ -0,50, regelkonform, Vortrend +0,11) beginnt mit 2019-05, das nur -0,28 vom Vor6 abweicht und damit nicht deutlich. Erster deutlich abweichender Monat ist 2019-06. 2019-06..2019-06 ist verworfen (a, b, Dünn). 2019-08 (3,47) ist der erste Monat nahe dem neuen Niveau von etwa 3,7. Die Wahl ist nicht auf Δ optimiert. Bestätigt.
- note: Zahlen stimmen mit pruefe überein (4,2 / 3,7 / -0,56); n=6-Monate mit Anzahl genannt; Lücke nach dem Zeitraum genannt; Reihenfolge nach Regel 11 ok.

Eintrag 2022-08..2022-11 (fall, Δ -0,6678):
- pruefe: regelkonform. Vorniveau 3,7305 aus 2021-11..2022-07 (n=5-13), Niveau 3,063, Folgemittel 2,8967 (Abstand 0,83 bei verlangten 0,33), erster Folgemonat 2023-01 mit Abstand 0,64. Dünn-Stützung für 2022-08 (n=8) und 2022-10 (n=6) ok. Vortrend -0,157, kein Hinweis.
- Versuch 1, Abgrenzung: Alternative wäre 2022-11..2022-11 (Δ -0,99, größer). Deren Vorniveau enthält aber bereits 2022-08..10, und der Rechner meldet einen Trendhinweis (-0,39). Der erste abweichende Monat ist 2022-08 (-0,81). 2022-09 und 2022-10 kehren nicht auf das alte Niveau zurück (je etwa -0,30). Ab 2022-11 bleibt die Reihe bei 2,4-3,2. 2022-08..2022-08 ist verworfen (Dünn-Stützung). Die Wahl ist nicht auf Δ optimiert, denn 2022-11..2022-11 und 2022-11..2023-01 hätten ein größeres |Δ|. Bestätigt.
- Versuch 2, Trend: 2022-01..2022-07 ist flach (3,46-3,76), danach folgt eine Stufe innerhalb von 4 Monaten. Der leichte Weiterabfall 2023/24 ist kein Grund gegen den Sprung. Nicht widerlegt.
- note: Zahlen identisch mit pruefe (3,7 / 3,1 / -0,67); 2022-08 (n=8) und 2022-10 (n=6) genannt; Regel 11 ok.

Zweifelsfall 2021-04..2021-05 (rise, Δ +0,4662):
- pruefe: zweifelsfall_0_3_bis_0_49; nur R4 im Band, alles andere ok.
- satz 2019-06:2019-08, 2021-04:2021-05, 2022-08:2022-11: ok (Abstände 7 und 9).
- Kritik: Ob 2021-05 (3,70) wirklich auf dem neuen Niveau von etwa 3,9 liegt, ist fraglich. Als Zweifelsfall für Stufe B ist das aber zulässig und im grund dokumentiert. Bleibt.

Regel 5:
- satz für die beiden Einträge: ok (Abstand 18 bewertete Monate). Es gibt nur 3 regelkonforme Gruppen, davon eine definitionsgemäß verworfen. Ein Schwankungshinweis ist nicht nötig.

Kandidaten des früheren Laufs:
- 2020-10..2020-10: verworfen (S_folgeniveau, Abstand 0,43 < 0,54).
- 2021-04..2021-07: verworfen (S_folgeniveau, Abstand 0,25 < 0,29; erster Folgemonat 2021-09 +0,35).
- 2022-08..2022-11: identisch mit Eintrag 2.
- Keiner ist nach den Setzungen von Lauf 2 regelkonform.

Weitere geprüfte Varianten:
- 2024-05..2024-07 und 2024-05..2024-09: regelkonform. Die definitionsgemäße Abgrenzung 2024-05..2024-05 ist verworfen (Folgemittel-Abstand 0,19 < 0,75; erster Folgemonat nur +0,21). 2024-06 (2,86) und 2024-07 (2,76) liegen auf dem alten Niveau (2023-07..2024-04 etwa 2,7). Das ist ein Einmonatssprung mit Rückkehr nach Regel 4. Ohne 2024-05 läge 2024-06..2024-09 nur bei etwa +0,25. Die Verlängerung würde die Regeln nur durch Verlängerung erfüllen. Die Verwerfung durch den Annotator hält.
- 2017-07..2017-07: Zweifelsband; der Rechner meldet Vortrend +0,70. Langsamer stufiger Anstieg von 2016 bis 2018, Sprung zum Vormonat nur +0,32. Die Verwerfung nach Regel 2 ist vertretbar und bleibt. Zusätzlich hätte satz mit allen vier Zeiträumen anzahl_ok=false.

**Vollständigkeit (Prüfer):** Der scan findet 15 regelkonforme Zeiträume in 3 Gruppen und 26 Zweifelsfälle in 6 Gruppen.

Regelkonforme Gruppen:
1. 2019 (2019-05..08, 2019-06..08): eingetragen als 2019-06..2019-08. 2019-05..08 ist verworfen, weil 2019-05 nicht deutlich abweicht.
2. 2022 (10 Varianten 2022-08..2023-04): eingetragen als 2022-08..2022-11. Die übrigen Varianten sind nach Definition bzw. Regel 5 (Überlappung) verworfen.
3. 2024 (2024-05..07/08/09): verworfen. Die definitionsgemäße Abgrenzung 2024-05..2024-05 scheitert an den Setzungen (a) und (b); es ist ein Einmonatssprung mit Rückkehr (Regel 4), und die Verlängerung dient nur dem Bestehen.

Zweifelsgruppen:
- 2017-07: verworfen wegen Trend (Regel 2, Vortrend +0,70).
- 2019 (4 Varianten): überlappen Eintrag 1, verworfen nach Regel 5.
- 2021-04..2021-05: als Zweifelsfall geführt; satz mit beiden Einträgen ok.
- 2021-07..2021-10: verworfen nach Abgrenzung und Regel 5 (0 bewertete Monate Abstand zu 2021-04..05; Zusammenfassung 7 Kalendermonate).
- 2022 (8 Varianten): überlappen Eintrag 2, verworfen nach Regel 5.
- 2023 (11 Varianten): weniger als 3 bewertete Monate Abstand zu 2022-11, verworfen nach Regel 5.
- 2024-04..08/09: verworfen nach Abgrenzung (2024-04 weicht nicht ab).

Kandidaten des früheren Laufs: 2020-10..2020-10 und 2021-04..2021-07 sind nach pruefe verworfen; 2022-08..2022-11 ist eingetragen.

Es fehlt keine regelkonforme, definitionsgemäße Stelle. Es gibt keine Änderungen gegenüber dem Annotator.


## Telekom (ID 28, 165 bewertete Monate)

**Ergebnis:** 3 Einträge, 0 Zweifelsfälle für Stufe B.

- Eintrag 2009-12 bis 2009-12, rise, Δ +0.855: Vorniveau 3,4 (2008-01 bis 2008-10, n=5-12); Zeitraum 4,2 (n=21); Δ +0,86; rise; Lücke: 2008-11 bis 2009-11 ohne bewerteten Monat zwischen Vorniveau und Zeitraum, Vorniveau dünn (2008-01 n=7, 2008-05 n=5, 2008-06 n=8, 2008-08 n=9); Reihe schwankt: fünf regelkonforme Kandidaten, nur die drei deutlichsten behalten; Anker: keiner; Reihe allein.
- Eintrag 2010-07 bis 2010-07, fall, Δ -1.096: Vorniveau 4,1 (2008-08 bis 2010-04, n=6-21); Zeitraum 3,0 (n=7); Δ -1,10; fall; dünn: 2010-07 mit 7 Bewertungen (gestützt durch 2010-08, n=11), Vorniveau lückig über 21 Kalendermonate; Reihe schwankt: fünf regelkonforme Kandidaten, nur die drei deutlichsten behalten; Anker: keiner; Reihe allein.
- Eintrag 2013-05 bis 2013-05, rise, Δ +0.578: Vorniveau 3,5 (2010-12 bis 2013-04, n=5-79); Zeitraum 4,1 (n=78); Δ +0,58; rise; Vorniveau lückig über 29 Kalendermonate (2011-03 bis 2012-07 ohne bewerteten Monat); Reihe schwankt: fünf regelkonforme Kandidaten, nur die drei deutlichsten behalten; Anker: keiner; Reihe allein.

**Auswahl (Annotator):** Fünf Stellen ergeben definitionsgemäß abgegrenzte, regelkonforme Zeiträume (Rechner pruefe): 2009-12 (+0,8552), 2010-07 (-1,0958), 2013-05 (+0,5775), 2019-02 (+0,5753) und 2018-05 (+0,5115). Bei allen ist der erste deutlich abweichende bewertete Monat schon der erste Monat auf dem neuen Niveau, deshalb gilt jeweils von = bis.

Trendprüfung nach Regel 2: 2010-07 hat einen Vortrend von +0,55, 2018-05 von -0,36 und 2019-02 von -0,66. Diese Vortrends laufen jeweils gegen die Sprungrichtung. 2013-05 hat einen Vortrend von +0,01, also flach. Bei 2009-12 gibt es kein gleichmäßiges Vorlaufen: Das Vorniveau 2008 schwankt (2,90 / 3,14 / 3,71 / 3,94 / 3,27), danach folgen 13 Monate ohne bewerteten Monat. Keine dieser Stellen ist also ein Trend.

Der Herbst 2018 ist eine gleichmäßige Rampe bis 2018-12, auf die 2019-02 die Rückkehr folgt. Die definitionsgemäße Abgrenzung 2018-10..2018-12 und ebenso 2018-11..2018-12 verletzt Setzung (a), deshalb gibt es dort keinen Eintrag. Die Kurzvariante 2018-11..2018-11 wurde nicht gewählt: Sie würde den Zeitraum nur kürzen, damit eine Regel besteht.

Regel 5: Bei fünf Kandidaten bleiben die drei mit dem größten ungerundeten |Δ|, also 2010-07, 2009-12 und 2013-05. Die Prüfung mit satz ergibt ok: 3 Einträge, Abstände von 3 und 10 bewerteten Monaten. In jeder note ist die Schwankung genannt.

Zweifelsfälle: Bei drei Einträgen wäre jeder weitere Zeitraum der vierte. Das ist mit Regel 5 (Anzahl) nicht vereinbar, daher bleibt die Liste leer.

Hinweise für den Autor:
(1) 2013-05 liegt nur 0,0022 vor 2019-02. Nach der Lesart „Gleichstand auf zwei Nachkommastellen“ (beide +0,58) würde 2019-02 wegen des klareren Bleibens den Platz von 2013-05 übernehmen. Dann ergäbe sich der Satz 2009-12, 2010-07, 2019-02.
(2) Die beiden frühen Einträge liegen in einer dünnen, lückigen Phase. Bei 2009-12 trennen 13 nicht bewertete Monate das Vorniveau vom Zeitraum, und die grauen Monate 2009 liegen schon überwiegend bei 4,1 bis 4,6. Der Sprung lässt sich daher zeitlich nur auf den ersten bewerteten Monat legen. Das Vorniveau von 2010-07 und 2013-05 verteilt sich über 21 bzw. 29 Kalendermonate.

**Verworfene Kandidaten (31):**

- 2019-02..2019-02: Regel 5 (mehr als drei Kandidaten; Rang 4 nach |Δ|). regelkonform, Δ +0,5753 (Vor 3,385, Niv 3,960, Folgemittel 4,009, Folgeabstand 0,6247); nur 0,0022 unter 2013-05 (+0,5775). Bei einer Gleichstandslesart auf zwei Nachkommastellen (beide +0,58) wäre 2019-02 nach dem klareren Bleiben zu wählen (Folgeabstand 0,6247 gegenüber 0,5902, erster Folgemonat 0,3393 gegenüber 0,3265). Vortrend -0,6627, gegen die Sprungrichtung, also kein Trend.
- 2018-05..2018-05: Regel 5 (Rang 5 nach |Δ|). regelkonform, Δ +0,5115 (Vor 3,508, Niv 4,019, Folgemittel 3,896); Vortrend -0,3563, gegen die Sprungrichtung, also kein Trend
- 2018-10..2018-12 (definitionsgemäß; Scan-Variante 2018-11..2018-11): Abgrenzung nach Definition und Setzung (a). Gleichmäßige Rampe 2018-08 3,972, 2018-09 3,719, 2018-10 3,457, 2018-11 3,212, 2018-12 2,986, 2019-01 2,962, danach Rückkehr 2019-02 3,960. Erster Monat auf dem neuen Niveau ist 2018-12. 2018-10..2018-12: Δ -0,5707, Folgemittel 3,5487, Abstand 0,2403 < 0,2853 verlangt, verworfen. 2018-11..2018-12: Δ -0,7150, Abstand 0,2653 < 0,3575, verworfen. 2018-11..2018-11 ist zwar regelkonform (Δ -0,6020), aber 2018-11 liegt mitten in der Rampe und nicht auf dem neuen Niveau; außerdem nur 2 bewertete Monate Abstand zu 2019-02 (satz: nicht ok). Daher kein Eintrag für diese Stelle.
- 2009-12..2010-01: Abgrenzung (nicht definitionsgemäß). regelkonform, Δ +0,8977; 2009-12 liegt bereits auf dem neuen Niveau, daher period_to = 2009-12
- 2010-07..2010-08 / 2010-07..2010-09 / 2010-07..2010-11: Abgrenzung (nicht definitionsgemäß). regelkonform, Δ -0,8733 / -0,686 / -0,651; 2010-07 (3,000) liegt bereits innerhalb der Streuung des neuen Niveaus (2010-08 bis 2011-02: 2,911 bis 4,083), daher period_to = 2010-07
- 2013-05..2013-07 / 2013-05..2013-08 / 2013-05..2013-09 / 2013-07..2013-07: Abgrenzung (nicht definitionsgemäß). regelkonform, Δ +0,5255 / +0,587 / +0,563 / +0,591; erster abweichender Monat ist 2013-05 und liegt bereits auf dem neuen Niveau
- 2019-03.. und 2019-04.. und 2019-05.. Varianten (z. B. 2019-04..2019-04, 2019-04..2019-05): Abgrenzung (nicht definitionsgemäß) und Regel 5. regelkonform, z. B. Δ +0,7195 (2019-04..2019-04), +0,768 (2019-04..2019-05), +0,627 (2019-03..2019-05); der erste abweichende Monat ist 2019-02. Eine Verlängerung oder Verschiebung nur für ein größeres Δ ist unzulässig.
- 2008-06..2008-06: Setzung Vorniveau mindestens drei Monate. Vorniveau nur 2 bewertete Monate
- 2008-08..2008-08: Setzung (b) und Dünn-Stützung. Δ +0,693; erster Folgemonat 2008-10 3,267, Abstand 0,016 < 0,25; 2008-08 (n=9) ohne Stützung
- 2008-08..2008-10: Regel 4 Zweifelsfall, Regel 5 Anzahl. Δ +0,3545 (Vor 3,251); bei bereits drei Einträgen nicht vereinbar
- 2010-08..2010-11 (Gruppe inkl. 2010-08..2010-09, 2010-09..2010-11, 2010-09..2011-02, 2010-10..2011-02): Regel 4 Zweifelsfall, Regel 5 Anzahl und Abstand. Δ -0,3825 (2010-08..2010-11), -0,3752 (2010-09..2010-11), -0,323 bis -0,300; Fortsetzung der Stelle 2010-07, weniger als drei bewertete Monate Abstand
- 2011-02..2011-02: Setzung (a). Δ +0,5165; Folgemittel 3,4367, Abstand -0,0028 < 0,2582
- 2012-08..2012-08: Setzung (a) und Dünn-Stützung. Δ -0,5588; Folgeabstand 0,1155 < 0,2794; 2012-08 (n=5) ohne Stützung
- 2013-05..2013-06 (Gruppe inkl. 2013-06..2013-07, 2013-06..2013-11, 2013-07..2013-11, 2013-07..2013-12): Regel 4 Zweifelsfall, Regel 5. Δ +0,452 / +0,393 / +0,346 / +0,397 / +0,384; dieselbe Stelle wie der Eintrag 2013-05
- 2015-04..2015-05: Setzung (a). Δ -0,9095; Folgemittel 3,8347, Abstand -0,0662 < 0,4547 (Rückkehr 2015-06/07); 2015-04..2015-04: Δ -0,7505, Abstand 0,1838 < 0,3753
- 2015-12..2015-12: Setzung (a) und Dünn-Stützung. Δ -0,6483; Folgeabstand 0,0033 < 0,3242; 2015-12 (n=8) ohne Stützung
- 2016-11..2016-11: Setzung (a). Δ +0,5177; Folgeabstand 0,152 < 0,2588
- 2017-05..2017-05: Setzung (a) und Dünn-Stützung. Δ -1,035; Folgeabstand 0,2003 < 0,5175; 2017-05 (n=6) ohne Stützung
- 2017-09..2017-09: Regel 4 und Setzung (a). Δ +0,4972; Folgeabstand 0,1075 < 0,2486
- 2017-12..2018-02: Regel 4 Zweifelsfall, Regel 5 Anzahl. Δ -0,3282; 2018-01..2018-02: Δ -0,424, Setzung (a) 0,1892 < 0,212; 2018-02..2018-02: Δ -0,518, Setzung (a) 0,1397 < 0,259
- 2018-05..2018-06 (Gruppe inkl. 2018-05..2018-07, 2018-06..2018-07): Regel 4 Zweifelsfall, Regel 5. Δ +0,408 / +0,405 / +0,318; dieselbe Stelle wie der verworfene Kandidat 2018-05
- 2018-10..2018-11 (inkl. 2018-10..2018-10): Regel 4 Zweifelsfall, Regel 5. Δ -0,4545 / -0,332; Stelle Herbst 2018, definitionsgemäß 2018-10..2018-12 verworfen (Setzung a)
- 2019-02..2019-03 (inkl. 2019-03..2019-03) und 2019-06..2019-07 (inkl. 2019-06..2019-09/-10/-11): Regel 4 Zweifelsfall, Regel 5. Δ +0,457 / +0,341; +0,382 / +0,315 / +0,337 / +0,343; Stelle 2019, bei bereits drei Einträgen nicht vereinbar
- 2020-03..2020-05 (inkl. 2020-04..2020-05): Regel 4 Zweifelsfall, Regel 5 Anzahl. Δ +0,3217 / +0,317; 2020-04..2020-07: Δ +0,3653 und Setzung (a) verletzt (Rückfall 2020-08 3,838)
- 2020-08..2020-08: Regel 4 Zweifelsfall, Regel 5 Anzahl. Δ -0,427 (Vor 4,265), Folgemittel 4,0203
- 2021-09..2021-11 (Gruppe inkl. 2021-09..2022-01, 2021-09..2022-02, 2021-10..2021-11, 2021-11..2021-11): Regel 4 Zweifelsfall, Regel 5 Anzahl. Δ -0,3205 / -0,301 / -0,321 / -0,316 / -0,306; 2021-09..2021-12: Δ -0,3529, Setzung (a) verletzt
- 2022-11..2022-11 (inkl. 2022-10..2023-02): Regel 4 Zweifelsfall, Regel 5 Anzahl. Δ -0,3303 / -0,303
- 2022-12..2022-12: Setzung (a). Δ -1,3783; Folgeabstand 0,089 < 0,6892 (Einmonatsausreißer, Rückkehr 2023-01 4,168)
- 2023-04..2023-04: Setzung (a). Δ +0,5412; Folgeabstand 0,2245 < 0,2706
- 2023-09..2023-09: Setzung (a). Δ +0,5265; Folgeabstand 0,0692 < 0,2632
- 2024-04..2024-04 (inkl. 2024-04..2024-05, 2024-05..2024-05): Regel 4 Zweifelsfall, Regel 5 Anzahl. Δ -0,399 / -0,374 / -0,314; 2024-04..2024-06: Δ -0,47, Setzung (a) verletzt; 2024-06..2024-06: Δ -0,5333, Folgeabstand -0,0917 < 0,2667

**Widerlegungsversuche (Prüfer):** Ich habe jeden Eintrag mit pruefe nachgerechnet und die Auswahl mit satz geprüft.

2009-12..2009-12 (rise): pruefe ergibt regelkonform, Δ +0,8552. Vorniveau 3,3928 aus 5 Monaten (2008-01 bis 2008-10, n=5-12). Folgemittel 4,372, Abstand 0,9792 bei verlangten 0,4276. Erster Folgemonat 2010-01 mit 4,333, Abstand 0,9402.
- Widerlegungsversuch 1, Lücke: Zwischen Vorniveau und Zeitraum liegen 13 nicht bewertete Monate. Der Sprung ist darum zeitlich nicht genau festzulegen. Regel 3 regelt aber genau diesen Fall: Ist ein Randmonat grau, wird der Rand auf den nächsten bewerteten Monat gelegt. Innerhalb des Zeitraums liegt kein grauer Monat. Nicht widerlegt; die Lücke ist in der note genannt.
- Widerlegungsversuch 2, Trend: Das Vorniveau verläuft 2,90 / 3,14 / 3,71 / 3,94 / 3,27, ist also nicht gleichmäßig. Einen Vortrend kann der Rechner nicht berechnen. Ein Trend nach Regel 2 liegt nicht vor.
- Widerlegungsversuch 3, Rückkehr: Die Folgemonate 4,33 / 4,15 / 4,63 bleiben hoch.
- Abgrenzung: 2009-12 liegt schon auf dem neuen Niveau. Die Variante 2009-12..2010-01 (Δ +0,8977) wäre nur eine Verlängerung.
- note: entspricht dem note_geruest. Im Zeitraum gibt es keinen Monat mit 5-9 Bewertungen. Die dünnen Vorniveau-Monate sind korrekt mit Anzahl genannt.
Ergebnis: Eintrag bleibt.

2010-07..2010-07 (fall): pruefe ergibt regelkonform, Δ -1,0958. Vortrend +0,5523, also gegen die Sprungrichtung und kein Trend. Folgemittel 3,3803, Abstand 0,7155 bei verlangten 0,5479. Erster Folgemonat 2010-08 mit 3,445, Abstand 0,6508. Der dünne Monat 2010-07 (n=7) ist durch 2010-08 gestützt.
- Widerlegungsversuch 1, Einmonatsausreißer: Die Folgemonate 3,445 / 3,785 / 2,911 / 4,083 / 3,413 kehren nicht auf etwa 4,2-4,6 zurück. Nicht widerlegt.
- Widerlegungsversuch 2, Abgrenzung: 2010-07 (3,000) liegt in der Streuung des neuen Niveaus (2,91 bis 4,08). period_to = 2010-07 ist vertretbar. Die Variante 2010-07..2010-08 (Δ -0,8733) wäre ebenfalls Rang 1 und würde die Auswahl nicht ändern.
- Abstand zu 2009-12: genau 3 bewertete Monate (satz ok).
- note: entspricht dem note_geruest. Der dünne Monat ist mit Anzahl und Stützung genannt, die Lückigkeit über 21 Kalendermonate ebenfalls.
Ergebnis: Eintrag bleibt.

2013-05..2013-05 (rise): pruefe ergibt regelkonform, Δ +0,5775. Vortrend +0,0137, also flach. Folgemittel 4,0667, Abstand 0,5902 bei verlangten 0,2888. Erster Folgemonat 2013-06 mit 3,803, Abstand 0,3265 (mindestens 0,25 verlangt).
- Widerlegungsversuch 1, Abgrenzung: 2013-05 (4,054) liegt auf dem neuen Niveau (Mittel 2013-05 bis 2013-10 etwa 4,02). Die Abgrenzung ist definitionsgemäß. Die größeren Varianten 2013-05..2013-08 (0,587) und 2013-07..2013-07 (0,591) wären auf Δ optimiert bzw. verschoben.
- Widerlegungsversuch 2, Regel-5-Rang gegen 2019-02 (+0,5753): Ungerundet liegt 2013-05 um 0,0022 vorn. Das Protokoll verlangt das größte |Δ|, und Δ ist der Rechenwert aus Regel 4. Die Rundung auf zwei Nachkommastellen gilt nur für die note. Ein Gleichstand liegt also nicht vor. Die Gegenlesart hat der Annotator offen als Hinweis an den Autor vermerkt.
- Widerlegungsversuch 3, Herbst 2018: 2018-11..2018-11 (Δ -0,602) wäre zwar regelkonform und läge vor 2013-05. 2018-11 (3,212) liegt aber mitten in einer gleichmäßigen Rampe (3,97 / 3,72 / 3,46 / 3,21 / 2,99). Der erste Monat auf dem neuen Niveau ist 2018-12. Die definitionsgemäßen Abgrenzungen verletzen alle Setzung (a): 2018-10..2018-12 mit 0,2403 < 0,2853, 2018-11..2018-12 mit 0,2653 < 0,3575, 2018-09..2018-12 zusätzlich Regel 4 (Δ -0,40). Dazu kehrt das alte Niveau schon 2019-02 zurück, das neue Niveau bleibt also nicht. Ein Kürzen auf 2018-11..2018-11, nur damit die Regel besteht, ist unzulässig. 2013-05 wird dadurch nicht verdrängt.
- Widerlegungsversuch 4, Kandidat 2019-02..2019-05 aus dem früheren Lauf: regelkonform mit Δ +0,6123, aber nicht definitionsgemäß. 2019-02 (3,96) liegt schon auf dem neuen Niveau (etwa 4,05). Auch die Lesart „neues Niveau erst ab 2019-04“ ergäbe nur 2019-02..2019-04 mit Δ +0,5443 und damit weniger als 2013-05.
- note: entspricht dem note_geruest. Die Lückigkeit über 29 Kalendermonate (2011-03 bis 2012-07) ist korrekt genannt.
Ergebnis: Eintrag bleibt.

Regel 5: satz ergibt für 2009-12, 2010-07 und 2013-05 ok (3 Einträge, Abstände 3 und 10 bewertete Monate). Es gibt fünf definitionsgemäß regelkonforme Stellen. Die drei mit dem größten |Δ| sind gewählt, und jede note nennt die Schwankung. Zur Kontrolle ergäbe auch der Alternativsatz mit 2019-02 satz ok; er ist aber nach |Δ| nachrangig. Alle delta-Werte stimmen mit pruefe überein.

Zweifelsfälle: Bei drei Einträgen wäre jeder weitere Zeitraum der vierte. Das ist mit Regel 5 nicht vereinbar, deshalb bleibt die Liste leer, wie beim Annotator.

**Vollständigkeit (Prüfer):** scan: 6 regelkonforme Gruppen und 13 Zweifelsfall-Gruppen. Jede Gruppe ist behandelt:

Regelkonforme Gruppen:
- 2009-12: eingetragen als 2009-12..2009-12. Die Variante ..2010-01 ist als nicht definitionsgemäß verworfen.
- 2010-07: eingetragen als 2010-07..2010-07. Die Varianten ..2010-08, ..2010-09 und ..2010-11 sind als nicht definitionsgemäß verworfen.
- 2013-05: eingetragen als 2013-05..2013-05. Die Varianten ..2013-07, ..2013-08, ..2013-09 und 2013-07..2013-07 sind als nicht definitionsgemäß verworfen.
- 2018-05..2018-05: verworfen nach Regel 5, Rang 5 (Δ +0,5115).
- 2018-11..2018-11: verworfen. Definitionsgemäß wäre 2018-10..2018-12 (bzw. 2018-11..2018-12) abzugrenzen, und beide verletzen Setzung (a). Dazu kommt eine Rückkehr 2019-02. Für diese Stelle gibt es keinen Eintrag.
- 2019: definitionsgemäß 2019-02..2019-02, verworfen nach Regel 5, Rang 4 (Δ +0,5753 < +0,5775). Alle Varianten 2019-02..2019-04 bis 2019-05..2019-10 sind Verlängerungen oder Verschiebungen. Darunter fällt auch der Kandidat des früheren Laufs 2019-02..2019-05.

Zweifelsfall-Gruppen (0,30-0,49): Alle 13 sind nach Regel 5 (Anzahl bzw. Abstand) mit drei Einträgen nicht vereinbar und darum ohne Zweifelsfall-Eintrag:
- 2008-08..2008-10
- 2010-08/09/10-Gruppe
- 2013-05..2013-06/2013-06/07-Gruppe
- 2017-12..2018-02
- 2018-05..2018-06/07-Gruppe
- 2018-10-Gruppe
- 2019-02..2019-03/2019-03-Gruppe
- 2019-06-Gruppe
- 2020-03/04-Gruppe
- 2020-08..2020-08
- 2021-09/10/11-Gruppe
- 2022-10..2023-02/2022-11-Gruppe
- 2024-04/05-Gruppe

Kandidaten des früheren Laufs:
- 2010-07..2010-07 und 2013-05..2013-05 sind eingetragen.
- 2019-02..2019-05 ist regelkonform, aber nicht definitionsgemäß abgegrenzt und deshalb nicht aufgenommen.

Es fehlt keine regelkonforme, definitionsgemäße Stelle, die nach Regel 5 hineingehört.


## Freenet (ID 33, 86 bewertete Monate)

**Ergebnis:** 3 Einträge, 0 Zweifelsfälle für Stufe B.

- Eintrag 2016-04 bis 2016-04, rise, Δ +1.044: Vorniveau 2,5 (2015-10 bis 2016-03, n=6-13); Zeitraum 3,5 (n=12); Δ +1,04; rise; Reihe schwankt stark: fünf regelkonforme Sprungstellen (2015-10, 2016-04, 2018-03 bis 2018-05, 2020-02, 2021-09), nur die drei deutlichsten eingetragen; Anker: keiner; Reihe allein.
- Eintrag 2020-02 bis 2020-02, rise, Δ +0.747: Vorniveau 3,7 (2019-05 bis 2019-10, n=5-28); Zeitraum 4,4 (n=6); Δ +0,75; rise; 2020-02 mit nur 6 Bewertungen, gestützt durch 2020-05 (4,33, n=7); davor 2019-11 bis 2020-01 nicht bewertet (je n=3); Reihe schwankt stark: fünf regelkonforme Sprungstellen (2015-10, 2016-04, 2018-03 bis 2018-05, 2020-02, 2021-09), nur die drei deutlichsten eingetragen; Anker: keiner; Reihe allein.
- Eintrag 2021-09 bis 2021-09, fall, Δ -0.746: Vorniveau 4,1 (2020-07 bis 2021-07, n=6-24); Zeitraum 3,4 (n=8); Δ -0,75; fall; 2021-09 mit nur 8 Bewertungen, gestützt durch 2021-10 (3,38, n=8); Reihe schwankt stark: fünf regelkonforme Sprungstellen (2015-10, 2016-04, 2018-03 bis 2018-05, 2020-02, 2021-09), nur die drei deutlichsten eingetragen; Anker: keiner; Reihe allein.

**Auswahl (Annotator):** Reihe Freenet Mitarbeitende Gesamtbewertung, 86 bewertete Monate, bis 2015 sehr lückig. Definitionsgemäß abgegrenzt und regelkonform sind fünf Sprungstellen: 2015-10 (Δ -0,549), 2016-04 (Δ +1,044), 2018-03..2018-05 (Δ +0,555), 2020-02 (Δ +0,7465) und 2021-09 (Δ -0,7463). Der Kandidat 2019-10 (Δ +0,5345) liegt 0 bewertete Monate vor 2020-02. Die Zusammenfassung 2019-10..2020-02 scheitert an Regel 3, weil drei Monate innen nicht bewertet sind. Nach Regel 5 bleibt deshalb nur der deutlichere Sprung 2020-02. Die 2022-08-Gruppe ist nicht definitionsgemäß: Der Anstieg beginnt 2022-02, und diese Abgrenzung besteht die Regeln nicht. Bei mehr als drei Kandidaten bleiben nach Regel 5 die drei mit größtem |Δ|: 2016-04, 2020-02 und 2021-09. Die Schwankung ist in jeder note genannt. Trendprüfung nach Regel 2: Bei 2016-04 liegt der Vortrend bei -0,04 und läuft gegen die Sprungrichtung. Bei 2020-02 liegt er bei +0,10, die Vormonate schwanken ohne gleichmäßigen Anstieg um 3,65. Bei 2021-09 liegt er bei -0,24, die Vormonate sind flach um 4,15 mit einem Einzeleinbruch 2021-05. Keiner der drei Fälle ist ein Trend. Abgrenzung: 2016-04 statt 2016-03, weil 2016-03 (2,838) in der Spanne des Vorniveaus liegt und nur +0,26 abweicht. 2020-02 und 2021-09 sind jeweils erster abweichender Monat und erster Monat auf dem neuen Niveau. Alle drei sind laut pruefe regelkonform. satz meldet ok mit 3 Zeiträumen und Abständen von 23 und 8 bewerteten Monaten. Es gibt keine Zweifelsfälle: Bei drei Einträgen wäre ein vierter Zeitraum mit Regel 5 nicht vereinbar. Alle Zahlen stammen aus /private/tmp/claude-501/-Users-vaios-EPA-Bachelorarbeit/1503df89-f281-4f80-8ff4-54d8dcdd0ffc/scratchpad/lauf2/dz1_rechner.py. Gelesen wurde nur /Users/vaios/EPA-Bachelorarbeit/EPA-Bachelorarbeit/backend/data/series/33_freenet_employee.csv.

**Verworfene Kandidaten (21):**

- 2015-10..2015-10 (fall): Regel 5 (mehr als drei Kandidaten, nur die drei deutlichsten behalten); sonst regelkonform, definitionsgemäße Abgrenzung (2015-10 ist der erste abweichende Monat und liegt bereits auf dem neuen Niveau, 2015-11 = 2,667). Δ -0,549; Vorniveau 3,261 (2013-02 bis 2015-07); Niveau 2,712 (n=8); Folgemittel 2,483; Hinweis Vortrend -0,25 geprüft: kein gleichmäßiger Abfall (Vormonate 3,08/3,17/3,92/3,36/2,76/3,29), kein Trend. |Δ| 0,549 liegt unter dem dritten Eintrag (0,746)
- 2015-10..2015-12 und weitere Varianten der Gruppe (2015-10..2015-11, 2015-10..2016-01, 2015-11.., 2015-12..2015-12): Abgrenzung nach Definition: nicht die definitionsgemäße Variante (2015-10 liegt schon auf dem neuen Niveau); außerdem Regel 5. 2015-10..2015-12 Δ -0,740; 2015-11..2015-12 Δ -0,774; 2015-12..2015-12 Δ -0,933; alle unter |Δ| der drei Einträge oder nicht definitionsgemäß
- 2016-03..2016-04 (rise) und Varianten 2016-03..2016-05/06/07, 2016-04..2016-05/06/07, 2016-05.., 2016-06..: Abgrenzung nach Definition: 2016-03 (2,838) liegt innerhalb der Spanne der Vorniveau-Monate (1,99-3,29) und weicht nur +0,26 ab (pruefe 2016-03..2016-03: R4 nicht erfüllt, Δ +0,265); erster deutlich abweichender Monat ist 2016-04, der bereits auf dem neuen Niveau liegt (Folgemonate 3,70/3,73/3,33). 2016-03..2016-04 Δ +0,617 (regelkonform, aber nicht definitionsgemäß); eingetragen stattdessen 2016-04..2016-04 Δ +1,044
- 2018-03..2018-05 (rise): Regel 5 (nur die drei deutlichsten); sonst regelkonform und definitionsgemäß (2018-03 = 3,56 liegt außerhalb der Vorniveau-Spanne 2,90-3,44; 2018-05 = 3,90 erster Monat auf neuem Niveau); 2018-04 nicht bewertet (n=3). Δ +0,555; Vorniveau 3,175; Niveau 3,730; Folgemittel 3,692 (2018-06 4,09, 2018-07 3,63, 2018-08 3,36: Niveau kehrt ab 2018-08 zum Vorniveau zurück, schwaches Bleiben). Trendprüfung: Anstieg 2018-02 bis 2018-06 über 4 Monate, kein Trend nach Regel 2. Variante 2018-05..2018-05 Δ +0,656 nicht definitionsgemäß
- 2019-10..2019-10 (rise): Regel 5, zwei Sprünge mit weniger als drei bewerteten Monaten Abstand (0 bewertete Monate bis 2020-02): Zusammenfassung 2019-10..2020-02 scheitert an Regel 3 (2019-11, 2019-12, 2020-01 nicht bewertet, je n=3), daher nur der deutlichere (2020-02) behalten. 2019-10..2019-10 Δ +0,5345 (regelkonform, n=8); 2019-10..2020-02 Δ +0,7095 verworfen (R3_innen_nicht_bewertet); 2020-02..2020-02 Δ +0,7465
- 2021-07..2021-10/11/12, 2021-09..2021-10/11/12, 2021-10..2021-10/11/12 (fall): Abgrenzung nach Definition: 2021-07 (4,119) liegt noch auf dem alten Niveau; 2021-09 ist erster abweichender Monat und liegt bereits auf dem neuen Niveau (2021-10 3,375, 2021-11 3,40); Verlängerungen bis 2021-12 (2,54, n=5) nicht definitionsgemäß. 2021-07..2021-12 Δ -0,824; 2021-09..2021-12 Δ -0,968; 2021-10..2021-12 Δ -0,933; eingetragen 2021-09..2021-09 Δ -0,746
- 2022-08..2022-09, 2022-08..2022-10, 2022-08..2023-01, 2022-10..2023-02 (rise): Abgrenzung nach Definition: der Anstieg beginnt bereits 2022-02 (Rechnerhinweis Vortrend +0,40); 2022-08 ist nicht der erste abweichende Monat und gegenüber 2022-02/2022-04 (3,80/3,70) kein neues Niveau. Definitionsgemäße Abgrenzung 2022-02..2022-02 besteht die Regeln nicht (R4 und Stützung dünner Monat), 2022-02..2022-08 scheitert an R2/R3/Folgeniveau. Zusätzlich Regel 5. 2022-08..2022-09 Δ +0,521; 2022-08..2022-10 Δ +0,513; 2022-08..2023-01 Δ +0,629; 2022-10..2023-02 Δ +0,531; 2022-02..2022-02 Δ +0,493 (verworfen: R4_groesse, R3_stuetzung_duenn, n=5); 2022-02..2022-08 Δ +0,588 (verworfen: R2_laenge, R3_innen_nicht_bewertet mit 2022-03/05/06/07, S_folgeniveau)
- 2022-02..2022-04 (rise, Zweifelsfall): Abgrenzung nach Definition (2022-02 liegt schon auf dem neuen Niveau; Verlängerung auf 2022-04 nur zur Rettung der Stützungsregel) und Regel 5 (drei Einträge, kein vierter Zeitraum zulässig). Δ +0,443; Vorniveau 3,307; 2022-03 nicht bewertet
- 2013-12..2013-12 (rise): Setzung (a)/(b) Folgeniveau: einzelner Monatssprung, altes Niveau kehrt zurück. Δ +0,642; Vorniveau 3,274; Folgemittel 3,134; erster Folgemonat 2015-02 = 3,357 (Abstand +0,08)
- 2015-03..2015-03 (fall): Setzung (b) Folgeniveau und Stützung dünner Monat (n=7, keine Stützung): einzelner Einbruch. Δ -0,637; Vorniveau 3,394; erster Folgemonat 2015-07 = 3,288 (Abstand 0,11)
- 2016-02..2016-02 (fall): Setzung (a)/(b) Folgeniveau: Tiefpunkt innerhalb des niedrigen Niveaus, danach Anstieg. Δ -0,711; Vorniveau 2,701; Folgemittel 3,36; erster Folgemonat 2016-03 = 2,838
- 2016-11..2016-11 (rise): Setzung (a)/(b) Folgeniveau: einzelner Monatssprung. Δ +0,974; Vorniveau 3,188; Folgemittel 3,198; erster Folgemonat 2017-01 = 3,150
- 2017-11..2017-11 (fall): Setzung (a) Folgeniveau und Stützung dünner Monat (n=9, keine Stützung). Δ -0,522; Vorniveau 3,422; Folgemittel 3,526
- 2019-02..2019-02 (fall): Setzung (a) Folgeniveau und Stützung dünner Monat (n=7, keine Stützung): einzelner Einbruch. Δ -1,052; Vorniveau 3,609; Folgemittel 3,42 (verlangt Abstand 0,526, erreicht 0,189)
- 2021-05..2021-05 (fall): Setzung (b) Folgeniveau und Stützung dünner Monat (n=7, keine Stützung): einzelner Einbruch, 2021-07 wieder 4,119. Δ -0,612; Vorniveau 4,298; erster Folgemonat Abstand 0,18
- 2021-12..2021-12 (fall): Setzung (a) Folgeniveau; liegt im bereits eingetragenen Abfall ab 2021-09 (Abstand zu 2021-09 nur 2 bewertete Monate). Δ -1,168; Vorniveau 3,708; Folgemittel 3,502 (verlangt 0,584, erreicht 0,206)
- 2022-08..2022-08 (rise): Setzung (b) Folgeniveau: erster Folgemonat 2022-09 = 3,467 kehrt zurück. Δ +0,879; Vorniveau 3,304; erster Folgemonat Abstand 0,16
- 2022-11..2022-11 (rise): Setzung (a)/(b) Folgeniveau und Stützung dünner Monat (n=5): einzelner Monatssprung. Δ +1,041; Vorniveau 3,660; Folgemittel 3,868; erster Folgemonat 2023-01 = 3,513
- 2024-10..2024-11 und 2024-11..2024-11 (fall): Setzung (a)/(b) Folgeniveau und Stützung dünner Monat (2024-11 n=5): Rückkehr ab 2025-01. 2024-10..2024-11 Δ -0,508, Folgemittel 4,124; 2024-11..2024-11 Δ -0,607; erster Folgemonat 2025-01 = 4,025
- 2025-08..2025-08 (fall): Setzung (c): kein bewerteter Folgemonat, Bleiben nicht prüfbar; zusätzlich Stützung dünner Monat (n=5). Δ -0,792; Vorniveau 4,112
- Zweifelsfälle 0,30-0,49: 2016-02..2016-05/06/07, 2017-06..2017-06, 2017-06..2017-08, 2018-03..2018-03, 2019-06..2019-06/07/09/10, 2019-07..2019-07/09/10, 2019-08..2019-10, 2020-05..2020-05, 2020-05..2020-08, 2021-05..2021-07, 2021-07..2021-09, 2021-11..2021-11, 2022-04..2022-04, 2022-09..2023-02, 2022-10..2022-10, 2022-11..2023-02, 2024-10..2024-10: Regel 4 (|Δ| 0,30-0,49) und Regel 5: drei Einträge bereits vorhanden, ein vierter Zeitraum wäre nicht vereinbar; mehrere zudem überlappend oder mit weniger als drei bewerteten Monaten Abstand zu einem Eintrag (2016-02.. mit 2016-04; 2020-05.. mit 2020-02; 2021-07..2021-09, 2021-11 mit 2021-09) oder nicht definitionsgemäß. 2016-02..2016-07 +0,487; 2017-06 -0,392; 2018-03 +0,385; 2019-06 +0,472; 2019-07 +0,475; 2020-05 +0,479; 2020-05..2020-08 +0,409; 2021-05..2021-07 -0,395; 2021-07..2021-09 -0,431; 2021-11 -0,488; 2022-04 +0,446; 2022-09..2023-02 +0,439; 2022-10 +0,350; 2022-11..2023-02 +0,381; 2024-10 -0,392

**Widerlegungsversuche (Prüfer):** 2016-04..2016-04 (rise): pruefe meldet regelkonform, Δ +1,0437, Vorniveau 2,498 (2015-10 bis 2016-03, n=6-13), Folgemittel 3,5867 (verlangt 0,5218), erster Folgemonat 2016-05 3,700 mit Abstand 1,20, kein dünner Monat im Zeitraum, Vortrend -0,04. Widerlegungsversuch 1, Abgrenzung beginnt zu spät: 2016-03 (2,838) als period_from. pruefe 2016-03..2016-03 ergibt R4 nicht erfüllt (Δ +0,265), und 2,838 liegt in der Spanne der Vorniveau-Monate. Erster deutlich abweichender Monat ist also 2016-04. Widerlegungsversuch 2, Abgrenzung des früheren Laufs 2016-04..2016-06 (Δ +1,158, regelkonform): 2016-04 liegt bereits auf dem neuen Niveau (Folgemonate 3,70/3,73/3,33). Die Verlängerung würde nur Δ vergrößern und ist nicht definitionsgemäß. Kein Trend, kein Einmonatsausreißer. Eintrag bleibt. 2020-02..2020-02 (rise): regelkonform, Δ +0,7465, Vorniveau 3,6535 (2019-05 bis 2019-10), Folgemittel 4,254 (verlangt 0,3733), erster Folgemonat 2020-05 4,329, Abstand 0,68. Dünner Monat n=6, gestützt durch 2020-05 (4,33, n=7). Vortrend +0,10: Die Vormonate schwanken (3,22/3,82/3,78/3,84/3,22/4,05), es gibt keinen gleichmäßigen Anstieg, also keinen Trend nach Regel 2. Widerlegungsversuch: 2019-10 (4,05) als erster abweichender Monat derselben Stelle. pruefe 2019-10..2020-02 ergibt verworfen (R3_innen_nicht_bewertet, 2019-11 bis 2020-01 je n=3). 2019-10..2019-10 ist allein regelkonform (Δ +0,5345), liegt aber 0 bewertete Monate vor 2020-02. Für genau diesen Fall schreibt Regel 5 vor: zusammenfassen, wenn regelkonform, sonst nur den deutlicheren. Der deutlichere Sprung ist 2020-02. Die Regelanwendung des Annotators ist korrekt. Die Folgemonate 2020-05 bis 2020-08 bleiben bei 4,05-4,38, eine Rückkehr gibt es nicht. Eintrag bleibt. 2021-09..2021-09 (fall): regelkonform, Δ -0,7463, Vorniveau 4,146 (2020-07 bis 2021-07, lückig über 13 Kalendermonate), Folgemittel 3,105 (verlangt 0,3732), erster Folgemonat 2021-10 3,375. Dünner Monat n=8, gestützt durch 2021-10. Vortrend -0,24: Die Vormonate sind flach um 4,15 mit Einzeleinbruch 2021-05, das ist kein Trend. Widerlegungsversuch 1, früherer Lauf 2021-09..2021-12 (Δ -0,968, regelkonform): 2021-09 liegt bereits auf dem neuen Niveau (2021-10 3,375, 2021-11 3,40). 2021-12 (2,54, n=5) ist ein Tiefpunkt, nach dem 2022-01 bis 2022-04 wieder steigen. pruefe 2021-12..2021-12 ergibt S_folgeniveau nicht erfüllt. Die Verlängerung ist nicht definitionsgemäß. Widerlegungsversuch 2, Beginn 2021-07: 2021-07 (4,119) liegt auf dem alten Niveau. Eintrag bleibt. Regel 5: satz meldet ok, 3 Zeiträume, Abstände 23 und 8 bewertete Monate. Es gibt mehr als drei regelkonforme Stellen: 2015-10 |Δ| 0,549 (beste Variante 2015-10..2015-12 mit 0,740), 2018-03..2018-05 |Δ| 0,555 (Variante 2018-05 mit 0,656), 2019-10 |Δ| 0,5345 und 2022-08-Gruppe max. |Δ| 0,629. Jede bleibt unter dem dritten Eintrag (0,7463), auch in jeder anderen Abgrenzungsvariante, die definitionsgemäß sein könnte. Die drei Einträge sind also die drei deutlichsten. Alle drei notes nennen die Schwankung. notes nach Regel 11: Sie stimmen mit dem note_geruest aus pruefe überein (Vorniveau, Monate, n-Spanne, Zeitraum, Δ mit Dezimalkomma, Richtung). Die dünnen Monate (2020-02 n=6, 2021-09 n=8) sind mit Anzahl genannt, 2016-04 hat n=12, die delta-Werte sind identisch mit pruefe. Zweifelsfälle: Bei drei Einträgen und mehr als drei Kandidaten wäre ein Zeitraum mit |Δ| 0,30-0,49 nach Regel 5 weder ein vierter Zeitraum noch einer der drei deutlichsten. Keiner ist mit den Einträgen vereinbar, die leere Liste ist korrekt. Ergebnis: Keine Regel verlangt eine Änderung, das Ergebnis des Annotators bleibt unverändert.

**Vollständigkeit (Prüfer):** scan: 39 regelkonforme Zeiträume in 7 Gruppen, 25 Zweifelsfälle in 10 Gruppen. Regelkonforme Gruppen: (1) 2015-10..2016-01-Gruppe (fall): begründet verworfen nach Regel 5. Definitionsgemäß ist 2015-10..2015-10 mit |Δ| 0,549, und auch 2015-10..2015-12 (0,740) bliebe unter 0,7463. (2) 2016-03..2016-07-Gruppe (rise): eingetragen als 2016-04..2016-04. 2016-03.. ist nicht definitionsgemäß (R4 für 2016-03 allein nicht erfüllt), Verlängerungen bis 2016-05/06/07 sind auf Δ optimiert. (3) 2018-03..2018-05 / 2018-05 (rise): begründet verworfen nach Regel 5 (|Δ| 0,555 bzw. 0,656). (4) 2019-10..2019-10 (rise): begründet verworfen nach Regel 5. 0 bewertete Monate bis 2020-02, die Zusammenfassung 2019-10..2020-02 scheitert an R3, daher nur der deutlichere Sprung. (5) 2020-02..2020-02: eingetragen. (6) 2021-07/09/10-Gruppe (fall): eingetragen als 2021-09..2021-09. 2021-07.. liegt auf dem alten Niveau, die Verlängerungen bis 2021-10/11/12 sind nicht definitionsgemäß. (7) 2022-08/2022-10-Gruppe (rise): begründet verworfen. Der Anstieg beginnt definitionsgemäß 2022-02, und 2022-02..2022-02 scheitert an R4 und R3_stuetzung_duenn. Zusätzlich greift Regel 5 (max. |Δ| 0,629 < 0,7463). Die 10 Zweifelsfall-Gruppen (2016-02.., 2017-06.., 2018-03, 2019-06/07/08.., 2020-05.., 2021-05..2021-07/2021-07..2021-09, 2021-11, 2022-02..2022-04/2022-04, 2022-09/10/11..2023-02, 2024-10) hat der Annotator alle wegen Regel 5 ohne Zweifelsfall vermerkt. Mehrere überlappen zudem mit Einträgen oder liegen weniger als drei bewertete Monate daneben. Kandidaten des früheren Laufs: 2016-04..2016-06 und 2021-09..2021-12 sind regelkonform, aber nicht definitionsgemäß (Verlängerung über den ersten Monat auf neuem Niveau hinaus). 2020-02..2020-02 ist identisch mit dem Eintrag. Es fehlt keine regelkonforme, definitionsgemäße Stelle, die nach Regel 5 hineingehört.
