# 04 – Aktienkurs und Kennzahlen

| | |
|---|---|
| Inkrement | 3 (Zyklus 2) |
| Anforderungen | Kurs und Kennzahlen als Einordnung neben dem Bewertungsverlauf (Auftrag Inkrement 3) |
| Entscheidungen | E15 in `docs/entscheidungen.md`; E6 (Ticker, Sonderfälle) und E8 (yfinance als Abhängigkeit) unverändert |
| Status | umgesetzt; **vorläufig** (Nutzungsbedingungen von Yahoo Finance offen) |
| Stand | 2026-10-05 |

## 1. Vorstellung

> **Stand 2026-10-04 (Nachtrag):** Auf Wunsch des Autors steht der Kurs nicht mehr auf der
> Anomalien-Detailseite, sondern im Aktien-Dashboard (Feature 05, Bereich „Kurs und
> Bewertungsverlauf“). Die Anomalien-Seite zeigt unter dem Diagramm nur einen Link dorthin.
> Darstellung, Umschalter und Kennzahlen sind unverändert; die Beschreibung unten gilt dort.

Im Monatsverlauf der Sternebewertung läuft der **Aktienkurs** als dünne,
violette Linie mit. Er hat eine eigene **rechte Y-Achse**, beschriftet mit der Währung
(„Kurs in EUR“). Die Legende nennt Ticker, Währung und Bereinigung, der Tooltip eines Monats
zeigt neben Monatsmittel und Zahl der Bewertungen den **Monatsschlusskurs**. Der Kurs wird
nur für die angezeigten Monate gezeichnet; der Zeitfilter (Gesamt, 5 Jahre, 3 Jahre,
12 Monate) gilt also auch für ihn.

Im Kopf des Diagrammabschnitts schaltet das Kästchen **„Aktienkurs“** die Linie ein und aus.
Der Zustand steht in der Adresse (`?kurs=aus`); ohne Angabe ist der Kurs an, sofern es einen
gibt.

Unter dem Diagramm steht eine **Kennzahlenzeile**: Marktkapitalisierung und Mitarbeitende
mit „aktuell, Stand …“ sowie der Umsatz der letzten Geschäftsjahre. Darunter nennt die
Ansicht, wessen Kurs gezeigt wird, die Quelle mit Abrufdatum und den festen Hinweis:

> **Einordnung, keine Erklärung.** Der Kurs zeigt das Marktumfeld; ein Zusammenhang mit den
> Bewertungen wird nicht behauptet.

Für Unternehmen ohne Ticker (Hochschulen, Netzbetreiber, Demo) funktioniert die Seite wie
bisher; statt des Kurses steht dort „Kein Aktienkurs: nicht börsennotiert“ oder der jeweilige
Grund. Die kompakte Karte im Dashboard und der PDF-Export bleiben unverändert.

Nutzen: Wer eine auffällige Veränderung betrachtet, sieht auf einen Blick, ob das
Unternehmen zur gleichen Zeit an der Börse ruhig, steigend oder fallend notierte, und kann
das bei der Einordnung im Kopf behalten, ohne dass das Dashboard daraus eine Ursache macht.

## 2. Erklärung

1. **Ticker.** Der Ticker in Yahoo-Finance-Notation (z. B. `SAP.DE`) kommt aus der Spalte
   `companies.ticker` (Migration 006, E6). Fehlt die Spalte oder der Wert, gilt der Eintrag
   in `backend/data/company_metadata.json` mit derselben `company_id`, aber nur, wenn der
   Name übereinstimmt. Das neue Feld `ticker_scope` sagt, ob der Ticker die **eigene Aktie**
   ist oder die der **Konzernmutter**.
2. **Kursreihe.** Über die Bibliothek `yfinance` werden die Monatskurse des ganzen
   verfügbaren Zeitraums geladen (`interval="1mo"`, `auto_adjust=True`). **Bereinigt**
   heißt: Frühere Kurse sind so umgerechnet, dass Aktiensplits und Dividenden keine Sprünge
   erzeugen (Begriff aus der Kursstatistik; Zweck: Bewegungen der Reihe sollen
   Marktbewegungen sein, keine Kapitalmaßnahmen). Je Kalendermonat zählt der letzte Kurs,
   der **Monatsschluss**. Der laufende Monat fehlt, weil er noch nicht abgeschlossen ist.
3. **Zwischenspeicher.** Das Ergebnis liegt je Ticker als JSON-Datei in
   `backend/data/market/` (nicht im Repository). Gefüllt wird er mit
   `uv run python scripts/fetch_market_data.py`. Fehlt eine Datei, ruft das Backend einmal
   live ab und speichert, außer bei `MARKET_LIVE_FETCH=0`. Schlägt der Abruf fehl, liefert
   der Endpunkt `available: false` mit Begründung.
4. **Kennzahlen** aus yfinance:
   - Marktkapitalisierung (Börsenwert aller Aktien), aktueller Wert in Kurswährung, Stand =
     Tag des letzten Kurses,
   - Mitarbeitende, aktueller Wert, Stand = Abrufdatum (yfinance nennt keinen Stichtag),
   - Umsatz je Geschäftsjahr in Berichtswährung; das Geschäftsjahr wird mit seinem Ende
     benannt („GJ 2025“, bei abweichendem Geschäftsjahr „GJ bis 09/2025“).
   Fehlende Werte bleiben leer.
5. **Endpunkt.** `GET /api/analytics/company/{id}/market?start=YYYY-MM&end=YYYY-MM` liefert
   Ticker, `ticker_scope`, Wertpapiername, Währung, `available`, `reason`, Kurse, Kennzahlen,
   Abrufzeit und Quelle. Das Aktien-Dashboard lädt die ganze Reihe (über `/finance`) und
   legt sie über die angezeigten Monate.

Stand der Daten (Abruf 2026-10-04): Alle 17 Ticker liefern Kurse bis 2026-09 und alle drei
Kennzahlen; der Umsatz reicht vier Geschäftsjahre zurück (2022 bis 2025, NTT 03/2023 bis
03/2026, Thyssenkrupp und Carl Zeiss Meditec mit Geschäftsjahr bis September).

## 3. Begründung

- **Einordnung statt Erklärung:** Die Arbeit beschreibt auffällige Veränderungen in
  Bewertungen, keine Ursachen (Regel der Feature-Doku). Ein Kurs hängt von vielen Einflüssen
  ab; ein gemeinsamer Verlauf belegt nichts. Deshalb gibt es keine Korrelation, keinen
  Vergleichswert und den festen Hinweis.
- **Zweite Achse statt eigenem Diagramm:** Kurs und Bewertung haben verschiedene Einheiten.
  Eine eigene Achse lässt beide Verläufe in ihrem Maßstab und zeigt die zeitliche Lage ohne
  Umblättern. Die Kurslinie ist dünner und blasser als die Bewertungslinie und hat eine
  eigene Farbe, die weder Rot noch Grün ist, damit sie nicht wie eine Markierung wirkt.
- **Monatsschluss:** passt zur Auflösung der Bewertungsreihe (Monatsmittel, E3).
- **Zwischenspeicher:** Die Seite hängt nicht von der Erreichbarkeit von Yahoo Finance ab,
  Kursdaten Dritter liegen nicht im Repository, und `fetched_at` macht den Stand
  nachvollziehbar.
- **Kennzahlen mit Stand:** Aktuelle Werte könnten sonst auf den Zeitraum einer
  Veränderung bezogen werden, die Jahre zurückliegt.
- **Nicht gewählt (Setzung des Entwicklers, vom Autor zu bestätigen):** Indexierter Kurs (Start = 100) auf der Bewertungsachse, weil er eine
  gemeinsame Skala vortäuscht; Kursänderung im Vergleichsfenster des Vorher-Nachher-Vergleichs,
  weil sie als Erklärung gelesen würde.

## 4. Grenzen

- Nur 17 von 26 Unternehmen haben einen Kurs. Für nicht notierte Unternehmen gibt es keinen
  Ersatz.
- **NTT DATA SE** zeigt Kurs und Kennzahlen der Konzernmutter NTT, Inc. (9432.T, JPY); sie
  bilden die deutsche Landesgesellschaft nur mittelbar ab. Die Ansicht sagt das ausdrücklich.
- **Carl Zeiss** zeigt die Carl Zeiss Meditec AG (AFX.DE); ob das Kununu-Profil die Meditec
  oder die nicht notierte Carl Zeiss AG meint, ist offen.
- **Compugroup Medical** war bis 2025 notiert, yfinance liefert nach dem Delisting keine
  Kurse mehr; die Ansicht zeigt „nicht börsennotiert“, obwohl es für frühere Jahre einen Kurs
  gab.
- Marktkapitalisierung und Mitarbeitende gibt es nur als aktuellen Wert, den Umsatz nur für
  etwa vier Geschäftsjahre.
- Bereinigte Kurse ändern sich rückwirkend mit jeder Dividende; ein neuer Abruf kann ältere
  Werte leicht verschieben. Der Zwischenspeicher wird nicht automatisch erneuert.
- Aus dem gemeinsamen Bild von Kurs und Bewertung darf kein Zusammenhang geschlossen werden.

## 5. Prüfung und Belege

- Tests ohne Netzwerk: `backend/tests/market/test_context_service.py` (Monatsreihe,
  Kennzahlen, Zwischenspeicher, Rückfall auf die Metadatei, fehlgeschlagener Abruf,
  `MARKET_LIVE_FETCH=0`) und `backend/tests/market/test_market_route.py` (Form der Antwort
  mit und ohne Ticker, `start`/`end`, kein 500 bei fehlenden Daten, Demo im In-Memory-Store).
- Commits auf `feature/inkrement-3-kurs`: Kursreihe und Zwischenspeicher, Endpunkt,
  Diagramm, Kennzahlen, Sonderfälle, Tests, Dokumentation.
- Manuelle Prüfung 2026-10-04 im Browser: SAP SE (Kurs, Tooltip, Umschalter, 12 Monate),
  NTT DATA SE (Konzernmutter in Legende und Hinweis, JPY), Open Grid Europe (kein Kurs),
  helles und dunkles Farbschema. Dashboard-Karte und PDF-Export nicht verändert.

### Bestand des Zwischenspeichers (Beleg für die Abnahme von Inkrement 3)

Ausgegeben am 2026-10-05 mit `cd backend && uv run python scripts/fetch_market_data.py --summary`.
Die Option liest nur Metadatei und Zwischenspeicher: kein Abruf, keine Datenbank, keine
Schreibzugriffe (Test: `backend/tests/market/test_market_summary.py`). Exit-Code 0 heißt, dass
jeder Ticker der Metadatei eine Kursreihe hat. **Abrufdatum** des Zwischenspeichers
(`fetched_at`) ist für alle 17 Ticker der **2026-10-04**.

Die Tabelle nennt nur Zeiträume und Verfügbarkeit, keine Kurs- oder Kennzahlwerte. Der Stand
der Marktkapitalisierung ist der Tag des letzten Kurses, der Stand der Mitarbeitenden das
Abrufdatum (E15). Beim Umsatz steht die Zahl der Geschäftsjahre (GJ) mit dem Monat, in dem das
erste und das letzte Geschäftsjahr enden. Alle Kursreihen sind lückenlos: Die Zahl der Monate
entspricht der Spanne vom ersten bis zum letzten Monat.

| Unternehmen (id) | Ticker | ticker_scope | Erster Monat | Letzter Monat | Monate | Währung | Marktkapitalisierung | Mitarbeitende | Umsatz je Geschäftsjahr | Abruf |
|---|---|---|---|---|---|---|---|---|---|---|
| Thyssenkrupp (3) | TKA.DE | eigene Aktie | 1999-03 | 2026-09 | 331 | EUR | Stand 2026-10-02 | Stand 2026-10-04 | 4 GJ, Ende 2022-09 bis 2025-09 | 2026-10-04 |
| E.ON (7) | EOAN.DE | eigene Aktie | 2000-01 | 2026-09 | 321 | EUR | Stand 2026-10-02 | Stand 2026-10-04 | 4 GJ, Ende 2022-12 bis 2025-12 | 2026-10-04 |
| RWE (8) | RWE.DE | eigene Aktie | 1996-12 | 2026-09 | 358 | EUR | Stand 2026-10-02 | Stand 2026-10-04 | 4 GJ, Ende 2022-12 bis 2025-12 | 2026-10-04 |
| SAP SE (19) | SAP.DE | eigene Aktie | 1998-04 | 2026-09 | 342 | EUR | Stand 2026-10-02 | Stand 2026-10-04 | 4 GJ, Ende 2022-12 bis 2025-12 | 2026-10-04 |
| NTT DATA SE (20) | 9432.T | Konzernmutter | 2000-01 | 2026-09 | 321 | JPY | Stand 2026-10-02 | Stand 2026-10-04 | 4 GJ, Ende 2023-03 bis 2026-03 | 2026-10-04 |
| 1&1 AG (21) | 1U1.DE | eigene Aktie | 1998-11 | 2026-09 | 335 | EUR | Stand 2026-10-02 | Stand 2026-10-04 | 4 GJ, Ende 2022-12 bis 2025-12 | 2026-10-04 |
| Aixtron (22) | AIXA.DE | eigene Aktie | 1997-11 | 2026-09 | 347 | EUR | Stand 2026-10-02 | Stand 2026-10-04 | 4 GJ, Ende 2022-12 bis 2025-12 | 2026-10-04 |
| Atoss (23) | AOF.DE | eigene Aktie | 1999-06 | 2026-09 | 328 | EUR | Stand 2026-10-02 | Stand 2026-10-04 | 4 GJ, Ende 2022-12 bis 2025-12 | 2026-10-04 |
| Bechtle (24) | BC8.DE | eigene Aktie | 2000-01 | 2026-09 | 321 | EUR | Stand 2026-10-02 | Stand 2026-10-04 | 4 GJ, Ende 2022-12 bis 2025-12 | 2026-10-04 |
| Cancom (25) | COK.DE | eigene Aktie | 1999-09 | 2026-09 | 325 | EUR | Stand 2026-10-02 | Stand 2026-10-04 | 4 GJ, Ende 2022-12 bis 2025-12 | 2026-10-04 |
| Carl Zeiss (26) | AFX.DE | – | 2000-03 | 2026-09 | 319 | EUR | Stand 2026-10-02 | Stand 2026-10-04 | 4 GJ, Ende 2022-09 bis 2025-09 | 2026-10-04 |
| Telekom (28) | DTE.DE | eigene Aktie | 1996-11 | 2026-09 | 359 | EUR | Stand 2026-10-02 | Stand 2026-10-04 | 4 GJ, Ende 2022-12 bis 2025-12 | 2026-10-04 |
| Eckert Ziegler (29) | EUZ.DE | eigene Aktie | 1999-05 | 2026-09 | 329 | EUR | Stand 2026-10-02 | Stand 2026-10-04 | 4 GJ, Ende 2022-12 bis 2025-12 | 2026-10-04 |
| Elmos Semiconductor (30) | ELG.DE | eigene Aktie | 1999-10 | 2026-09 | 324 | EUR | Stand 2026-10-02 | Stand 2026-10-04 | 4 GJ, Ende 2022-12 bis 2025-12 | 2026-10-04 |
| Evotec (31) | EVT.DE | eigene Aktie | 1999-11 | 2026-09 | 323 | EUR | Stand 2026-10-02 | Stand 2026-10-04 | 4 GJ, Ende 2022-12 bis 2025-12 | 2026-10-04 |
| Formycon (32) | FYB.DE | eigene Aktie | 2011-01 | 2026-09 | 189 | EUR | Stand 2026-10-02 | Stand 2026-10-04 | 4 GJ, Ende 2022-12 bis 2025-12 | 2026-10-04 |
| Freenet (33) | FNTN.DE | eigene Aktie | 2000-01 | 2026-09 | 321 | EUR | Stand 2026-10-02 | Stand 2026-10-04 | 4 GJ, Ende 2022-12 bis 2025-12 | 2026-10-04 |

`ticker_scope` „–“ bei Carl Zeiss: Die Zuordnung zur Carl Zeiss Meditec AG ist offen (E15).
Nicht in der Tabelle, weil ohne Ticker: die 9 nicht notierten Unternehmen (darunter
Compugroup Medical, E6) und die Demo-Unternehmen.

## 6. Offene Punkte

- Nutzungsbedingungen von Yahoo Finance für die Verwendung in der Arbeit (E15).
- Zuordnung Carl Zeiss (Meditec oder Carl Zeiss AG).
- Historische Kurse für Compugroup aus einer anderen Quelle?
- Wie oft der Zwischenspeicher vor der Auswertung erneuert wird (Stand festhalten).
