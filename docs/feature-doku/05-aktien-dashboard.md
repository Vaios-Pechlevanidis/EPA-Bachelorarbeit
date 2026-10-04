# 05 – Aktien-Dashboard

| | |
|---|---|
| Inkrement | 3 (Nachtrag, Zyklus 2) |
| Anforderungen | Wunsch des Autors vom 2026-10-04: eigenes Dashboard zum Aktienkurs mit Kursverlauf, Analystenempfehlungen, Umsatz und Gewinn sowie Nachrichten |
| Entscheidungen | E16 in `docs/entscheidungen.md`; E7 (Nachrichtenquelle) und E15 (Kurs, Kennzahlen, Zwischenspeicher) |
| Status | umgesetzt; **vorläufig** (Nutzungsbedingungen offen) |
| Stand | 2026-10-04 |

## 1. Vorstellung

Die Seite **„Aktie“** (`/aktie?company=ID`) öffnet sich über „Aktie“ in der Seitenleiste
des Dashboards oder über den Link „Aktien-Dashboard öffnen“ unter dem Diagramm der
Anomalien-Detailseite. Oben rechts lässt sich die Firma wechseln. Die Seite hat vier
Bereiche:

1. **Aktienkurs:** Kursverlauf als Fläche mit Zeitfenster 1, 3, 5, 10 Jahre oder alles.
   Der Untertitel nennt den letzten Monatsschlusskurs und die Veränderung im Fenster.
   Darunter stehen Marktkapitalisierung, Mitarbeitende und Umsatz je Geschäftsjahr (wie in
   Feature 04), die Quelle und der Hinweis „Einordnung, keine Erklärung“.
2. **Analystenempfehlungen:** gestapelte Balken je Monat (letzte vier Monate) mit der Zahl
   der Empfehlungen „stark kaufen“ bis „stark verkaufen“; der Tooltip nennt alle Stufen.
3. **Umsatz und Nettoergebnis:** Balken je Geschäftsjahr oder, umschaltbar, je Quartal.
4. **Aktuelle Meldungen:** die neuesten Meldungen der letzten 90 Tage mit Quelle, Datum
   und Link; darunter Suchbegriff, Quelle und Abrufdatum.

Für Unternehmen ohne Ticker zeigt die Seite „Kein Aktienkurs: …“ und nur die Meldungen.

Nutzen: Wer die Bewertungen eines börsennotierten Unternehmens betrachtet, findet die
wichtigsten Marktinformationen auf einer Seite, ohne die Anomalien-Ansicht zu überladen.

## 2. Erklärung

- **Daten:** `GET /api/analytics/company/{id}/finance` liefert Kurs, Kennzahlen,
  Empfehlungen und Erfolgszahlen aus dem Zwischenspeicher von Feature 04
  (`backend/data/market/<ticker>.json`); `GET /api/analytics/company/{id}/news` liefert
  die Meldungen.
- **Analystenempfehlungen** („analyst recommendations“, Begriff von Yahoo Finance):
  Zahl der Analysten, die die Aktie in einem Monat mit der jeweiligen Stufe einstufen.
  yfinance nennt die Monate relativ (`0m` = laufender Monat); sie werden auf den Monat des
  Abrufs bezogen.
- **Umsatz** („Total Revenue“) und **Nettoergebnis** („Net Income“, Gewinn oder Verlust
  nach Steuern) stammen aus der Erfolgsrechnung, die yfinance liefert, in Berichtswährung.
  Fehlt ein Wert, bleibt der Balken leer; nichts wird geschätzt.
- **Meldungen:** Google-News-RSS, Suche nach dem Firmennamen ohne Rechtsform (z. B.
  „SAP“, „"NTT DATA"“), deutsch, letzte 90 Tage, höchstens 30. Der Abruf wird 12 Stunden
  zwischengespeichert (`backend/data/market/news/`).
- **Abruf:** `uv run python scripts/fetch_market_data.py --news` füllt beide Speicher. Zur
  Laufzeit gilt `MARKET_LIVE_FETCH` wie in Feature 04.

## 3. Begründung

- Der Aufbau folgt der Kursseite von Yahoo Finance, die der Autor als Vorbild nannte.
- Die Finanzseite der Test-Kopie hing an gelöschten Tabellen und wurde neu gebaut, auf
  demselben Zwischenspeicher wie Feature 04, ohne Datenbankänderung.
- Nachrichten kommen aus Google-News-RSS, weil yfinance für keinen der 17 Ticker Meldungen
  liefert und E7 Google News ohnehin als Hauptquelle festlegt. So gibt es Meldungen auch für
  nicht notierte Unternehmen.
- Kein Bezug zu den Bewertungen: Die Seite zeigt Marktinformationen nebeneinander, ordnet
  sie keiner auffälligen Veränderung zu und bewertet sie nicht.

## 4. Grenzen

- Empfehlungen nur für vier Monate, Erfolgszahlen nur für etwa vier Jahre bzw. sechs
  Quartale; für ältere Veränderungen der Bewertungen gibt es keine Vergleichsdaten.
- Meldungen nur aus den letzten 90 Tagen; die Namenssuche liefert bei mehrdeutigen Namen
  fremde Treffer und bei sehr kleinen Unternehmen keine.
- NTT DATA SE: Kurs, Empfehlungen und Zahlen gehören der Konzernmutter NTT, Inc.
- Die Seite ist keine Anlageberatung; Empfehlungen sind die von Analysten, nicht des
  Dashboards.

## 5. Prüfung und Belege

- Tests ohne Netzwerk: `backend/tests/market/test_finance_dashboard.py` (Empfehlungen,
  Umsatz und Gewinn, `/finance`, RSS-Auswertung, Zwischenspeicher der Meldungen, Abruf
  schlägt fehl, `MARKET_LIVE_FETCH=0`, `/news`).
- Manuelle Prüfung im Browser (SAP SE, NTT DATA SE, Open Grid Europe; hell und dunkel).

## 6. Offene Punkte

- Nutzungsbedingungen von Yahoo Finance und Google News (E7, E15, E16).
- Soll die Seite in der Evaluation (DZ3) gezeigt werden?
- Bessere Suchbegriffe für mehrdeutige Namen (z. B. Carl Zeiss), vom Autor festzulegen.
