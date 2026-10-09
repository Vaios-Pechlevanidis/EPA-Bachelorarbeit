# Abnahme Inkrement 6 – Evaluationsinstanz

Stand: 2026-10-09, Branch `feature/inkrement-6-abschluss`, Commit `e006751` (Code; dieses Protokoll
folgt im Dokumentationscommit). Nur Zahlen und Zustände; keine Inhalte von Bewertungen, keine
Schlagzeilen. Markierungen sind je Unternehmen nur nummeriert.

## 1. Aufbau

| | |
|---|---|
| Backend | `uvicorn main:app --port 8002` mit `MARKET_LIVE_FETCH=0` und `CONTEXT_LIVE_FETCH=0` (eigener Prozess; die Dev-Server des Autors auf 8000 und 5173 blieben unberührt) |
| Frontend | Produktionsbau wie die Evaluationsinstanz: `VITE_SHOW_FINANCE_EXTRAS=false`, `VITE_SHOW_FORECAST=false`, `VITE_API_URL=http://localhost:8002` (Abweichung von `docs/evaluationsinstanz.md` nur im Port), ausgeliefert mit `vite preview` auf `localhost:3000` |
| Browser | Browser-Pane der Desktop-App, Ansicht 1440 × 900, helles Schema (`agb.theme=light`, `prefers-color-scheme: light`) |
| Ablauf | je Unternehmen: Dashboard, PDF-Export, Anomalien-Seite, jede Markierung (Niveauwechsel über `?anomaly=`, Einzelmonate über `?month=`), eine freie Auswahl (`?from=2024-01&to=2024-03`), Aktie; jede Ansicht als vollständiger Seitenaufruf in einem Iframe gleicher Herkunft |
| Messung | Ladezustand: keine Ladeanzeige („Lade …“, „… werden berechnet …“, Drehsymbol) für 1,5 s, Abbruch nach 150 s; Antwortzeit: Dauer der API-Aufrufe aus dem Resource-Timing des Browsers; `console.error`, `error` und `unhandledrejection` der Seite; Fehlertexte der Oberfläche; HTTP-Status ab 400; PDF-Export mit abgefangenem Download (kein Speichern), Seitenzahl und Stichproben im Text |

Einschränkung der Messung: Das Browser-Pane war während des Durchlaufs ausgeblendet; der
Browser drosselt dann die Zeitgeber der Seite. Die Spalte „bereit nach“ ist deshalb eine
Obergrenze; die Antwortzeiten der API-Aufrufe sind davon nicht betroffen. Bei sichtbarem Pane
war das Dashboard von Telekom nach 3,6 s fertig (13 API-Aufrufe, langsamster 3,3 s).

## 2. Prüfskript

`cd backend && MARKET_LIVE_FETCH=0 CONTEXT_LIVE_FETCH=0 VITE_SHOW_FINANCE_EXTRAS=false VITE_SHOW_FORECAST=false uv run python scripts/check_evaluation_instance.py --api http://localhost:8002`
(Laufzeit 45 s, Exit-Code 0). Ohne die vier Umgebungswerte meldet dasselbe Skript vier Fehler und
Exit-Code 1, weil `backend/.env` die beiden Backend-Schalter nicht setzt und `frontend/.env.local`
fehlt.

| Bereich | Prüfung | Ergebnis | Status |
|---|---|---|---|
| Umgebung | MARKET_LIVE_FETCH | 0 (Umgebung) | ok |
| Umgebung | CONTEXT_LIVE_FETCH | 0 (Umgebung) | ok |
| Umgebung | VITE_SHOW_FINANCE_EXTRAS | false (Umgebung) | ok |
| Umgebung | VITE_SHOW_FORECAST | false (Umgebung) | ok |
| Unternehmen | geeignet (E4) | 15: Thyssenkrupp (0+0), Open Grid Europe (0+0), E.ON (1+0), RWE (1+1), Karlsruher Institut für Technologie (0+0), Technische Universität München (0+0), SAP SE (1+1), NTT DATA SE (4+0), 1&1 AG (1+0), Bechtle (1+0), Cancom (0+2), Carl Zeiss (0+2), Compugroup Medical Deutschland (1+0), Telekom (4+3), Freenet (5+0) | ok |
| Kurs | Thyssenkrupp | TKA.DE: 1999-03 bis 2026-09, 0 Fenster | ok |
| Kurs | Open Grid Europe | kein Ticker | Hinweis |
| Kurs | E.ON | EOAN.DE: 2000-01 bis 2026-09, 1 Fenster | ok |
| Kurs | RWE | RWE.DE: 1996-12 bis 2026-09, 2 Fenster | ok |
| Kurs | Karlsruher Institut für Technologie | kein Ticker | Hinweis |
| Kurs | Technische Universität München | kein Ticker | Hinweis |
| Kurs | SAP SE | SAP.DE: 1998-04 bis 2026-09, 2 Fenster | ok |
| Kurs | NTT DATA SE | 9432.T: 2000-01 bis 2026-09, 4 Fenster | ok |
| Kurs | 1&1 AG | 1U1.DE: 1998-11 bis 2026-09, 1 Fenster | ok |
| Kurs | Bechtle | BC8.DE: 2000-01 bis 2026-09, 1 Fenster | ok |
| Kurs | Cancom | COK.DE: 1999-09 bis 2026-09, 2 Fenster | ok |
| Kurs | Carl Zeiss | AFX.DE: 2000-03 bis 2026-09, 2 Fenster | ok |
| Kurs | Compugroup Medical Deutschland | kein Ticker | Hinweis |
| Kurs | Telekom | DTE.DE: 1996-11 bis 2026-09, 7 Fenster | ok |
| Kurs | Freenet | FNTN.DE: 2000-01 bis 2026-09, 5 Fenster | ok |
| Belege | Thyssenkrupp | keine Markierung | ok |
| Belege | Open Grid Europe | keine Markierung | ok |
| Belege | E.ON | 1 Fenster; eqs 11/11 Monate, gnews 11/11 Monate | ok |
| Belege | RWE | 2 Fenster; eqs 12/12 Monate, gnews 12/12 Monate | ok |
| Belege | Karlsruher Institut für Technologie | keine Markierung | ok |
| Belege | Technische Universität München | keine Markierung | ok |
| Belege | SAP SE | 2 Fenster; eqs 10/10 Monate, gnews 10/10 Monate | ok |
| Belege | NTT DATA SE | 4 Fenster; gnews 27/27 Monate | ok |
| Belege | 1&1 AG | 1 Fenster; eqs 5/5 Monate, gnews 5/5 Monate | ok |
| Belege | Bechtle | 1 Fenster; eqs 5/5 Monate, gnews 5/5 Monate | ok |
| Belege | Cancom | 2 Fenster; eqs 10/10 Monate, gnews 10/10 Monate | ok |
| Belege | Carl Zeiss | 2 Fenster; eqs 10/10 Monate, gnews 10/10 Monate | ok |
| Belege | Compugroup Medical Deutschland | 1 Fenster; eqs 5/5 Monate, gnews 5/5 Monate | ok |
| Belege | Telekom | 7 Fenster; eqs 50/50 Monate, gnews 50/50 Monate | ok |
| Belege | Freenet | 5 Fenster; eqs 28/28 Monate, gnews 28/28 Monate | ok |
| Stimmung | Modus | transformer (Laden 3.3 s, ohne Netz) | ok |
| Antwortzeit | Ø Score | Median 0.20 s, Maximum 0.67 s (Telekom), 15 Unternehmen | ok |
| Antwortzeit | Trend | Median 0.11 s, Maximum 0.52 s (Telekom), 15 Unternehmen | ok |
| Antwortzeit | 12/24 Monate | Median 0.10 s, Maximum 0.49 s (Telekom), 15 Unternehmen | ok |
| Antwortzeit | Datenstand | Median 0.34 s, Maximum 0.75 s (Telekom), 15 Unternehmen | ok |
| Antwortzeit | Zeitverlauf | Median 0.10 s, Maximum 1.54 s (Telekom), 15 Unternehmen | ok |
| Antwortzeit | Topic-Übersicht | Median 0.84 s, Maximum 2.36 s (Telekom), 15 Unternehmen | ok |
| Antwortzeit | Anomalien | Median 0.19 s, Maximum 0.89 s (Telekom), 15 Unternehmen | ok |
| Antwortzeit | Kurs | Median 0.05 s, Maximum 0.15 s (Telekom), 15 Unternehmen | ok |

## 3. Ergebnis

- 15 von 15 Unternehmen, 88 Ansichten: 88 fertig geladen, 0 mit Fehlertext, 0 API-Aufrufe mit
  HTTP-Status ab 400, 0 `console.error` der Anwendung, alle im hellen Schema.
- 15 von 15 PDF-Exporten erzeugt, je 6 Seiten; in keinem steht „Prognose“, in jedem der
  Berechnungshinweis zum Ø Score, in keinem „Most Critical“ oder „Negative Topic“.
- Netzwerk: je Seitenaufruf ein Fehler 404 für `/_vercel/speed-insights/script.js` (Vercel Speed
  Insights aus `frontend/src/App.jsx`; das Skript gibt es nur bei Auslieferung über Vercel). Die
  Konsole des Browsers zeigt diese Meldungen als Fehler (92 im Puffer des Tabs). Abgebrochene
  API-Aufrufe entstanden nur beim ersten Aufruf des Dashboards, den der Ablauf zum Setzen des
  Unternehmens neu lädt; sie sind keine Fehler der Anwendung.

| Art des Schritts | Anzahl | Median bereit nach (s) | Maximum (s) |
|---|---|---|---|
| dashboard | 15 | 1,6 | 6,4 |
| anomalien | 15 | 0,6 | 4,5 |
| freie auswahl | 15 | 2,5 | 6,8 |
| aktie | 15 | 0,6 | 4,5 |
| niveauwechsel | 19 | 1,9 | 13,3 |
| einzelmonat | 9 | 2,6 | 4,5 |

## 4. PDF-Export

| Unternehmen | Ergebnis | Dauer (s) | Seiten | Größe (KB) | Prognose im PDF | Hinweistext | englische Beschriftung | console.error |
|---|---|---|---|---|---|---|---|---|
| Thyssenkrupp | ok | 2,4 | 6 | 435 | nein | ja | nein | 0 |
| Open Grid Europe | ok | 2,3 | 6 | 540 | nein | ja | nein | 0 |
| E.ON | ok | 2,6 | 6 | 515 | nein | ja | nein | 0 |
| RWE | ok | 2,3 | 6 | 596 | nein | ja | nein | 0 |
| Karlsruher Institut für Technologie | ok | 4,0 | 6 | 606 | nein | ja | nein | 0 |
| Technische Universität München | ok | 2,3 | 6 | 623 | nein | ja | nein | 0 |
| SAP SE | ok | 2,6 | 6 | 456 | nein | ja | nein | 0 |
| NTT DATA SE | ok | 4,0 | 6 | 580 | nein | ja | nein | 0 |
| 1&1 AG | ok | 2,3 | 6 | 535 | nein | ja | nein | 0 |
| Bechtle | ok | 2,6 | 6 | 527 | nein | ja | nein | 0 |
| Cancom | ok | 2,8 | 6 | 543 | nein | ja | nein | 0 |
| Carl Zeiss | ok | 4,0 | 6 | 537 | nein | ja | nein | 0 |
| Compugroup Medical Deutschland | ok | 2,5 | 6 | 571 | nein | ja | nein | 0 |
| Telekom | ok | 2,4 | 6 | 516 | nein | ja | nein | 0 |
| Freenet | ok | 2,3 | 6 | 554 | nein | ja | nein | 0 |

## 5. Einzelne Schritte

| Unternehmen | Schritt | Ladezustand | bereit nach (s) | API-Aufrufe | langsamster Aufruf (s) | console.error | Fehlertexte | HTTP ≥ 400 |
|---|---|---|---|---|---|---|---|---|
| Thyssenkrupp | dashboard | fertig | 0,6 | 13 | 0,8 (companies) | 0 | 0 | 0 |
| Thyssenkrupp | anomalien | fertig | 0,6 | 3 | 0,8 (3/data-status) | 0 | 0 | 0 |
| Thyssenkrupp | freie auswahl | fertig | 1,9 | 6 | 2,0 (3/compare) | 0 | 0 | 0 |
| Thyssenkrupp | aktie | fertig | 0,6 | 3 | 0,3 (3/data-status) | 0 | 0 | 0 |
| Open Grid Europe | dashboard | fertig | 0,6 | 13 | 0,6 (companies) | 0 | 0 | 0 |
| Open Grid Europe | anomalien | fertig | 0,6 | 3 | 0,3 (4/data-status) | 0 | 0 | 0 |
| Open Grid Europe | freie auswahl | fertig | 0,6 | 6 | 0,3 (4/data-status) | 0 | 0 | 0 |
| Open Grid Europe | aktie | fertig | 0,6 | 3 | 0,3 (companies) | 0 | 0 | 0 |
| E.ON | dashboard | fertig | 0,6 | 13 | 0,6 (7/data-status) | 0 | 0 | 0 |
| E.ON | anomalien | fertig | 0,6 | 3 | 0,3 (companies) | 0 | 0 | 0 |
| E.ON | niveauwechsel 1 | fertig | 1,1 | 6 | 1,0 (7/anomalies/{id}/explanations) | 0 | 0 | 0 |
| E.ON | freie auswahl | fertig | 0,6 | 6 | 0,5 (7/compare) | 0 | 0 | 0 |
| E.ON | aktie | fertig | 0,6 | 3 | 0,9 (companies) | 0 | 0 | 0 |
| RWE | dashboard | fertig | 0,7 | 13 | 0,6 (8/data-status) | 0 | 0 | 0 |
| RWE | anomalien | fertig | 0,6 | 3 | 0,3 (8/data-status) | 0 | 0 | 0 |
| RWE | niveauwechsel 1 | fertig | 5,4 | 6 | 0,7 (8/anomalies/{id}/explanations) | 0 | 0 | 0 |
| RWE | einzelmonat 1 | fertig | 4,5 | 7 | 0,8 (8/compare) | 0 | 0 | 0 |
| RWE | freie auswahl | fertig | 4,5 | 6 | 0,6 (8/compare) | 0 | 0 | 0 |
| RWE | aktie | fertig | 4,5 | 3 | 0,4 (companies) | 0 | 0 | 0 |
| Karlsruher Institut für Technologie | dashboard | fertig | 4,4 | 13 | 0,6 (companies) | 0 | 0 | 0 |
| Karlsruher Institut für Technologie | anomalien | fertig | 4,5 | 3 | 0,3 (companies) | 0 | 0 | 0 |
| Karlsruher Institut für Technologie | freie auswahl | fertig | 3,0 | 6 | 0,5 (14/data-status) | 0 | 0 | 0 |
| Karlsruher Institut für Technologie | aktie | fertig | 0,6 | 3 | 0,2 (14/data-status) | 0 | 0 | 0 |
| Technische Universität München | dashboard | fertig | 0,6 | 13 | 0,6 (companies) | 0 | 0 | 0 |
| Technische Universität München | anomalien | fertig | 0,8 | 3 | 0,9 (companies) | 0 | 0 | 0 |
| Technische Universität München | freie auswahl | fertig | 0,8 | 6 | 0,9 (15/compare) | 0 | 0 | 0 |
| Technische Universität München | aktie | fertig | 0,6 | 3 | 0,4 (15/data-status) | 0 | 0 | 0 |
| SAP SE | dashboard | fertig | 1,1 | 13 | 1,2 (19/data-status) | 0 | 0 | 0 |
| SAP SE | anomalien | fertig | 0,6 | 3 | 0,3 (19/data-status) | 0 | 0 | 0 |
| SAP SE | niveauwechsel 1 | fertig | 13,3 | 6 | 9,5 (19/anomalies/{id}/explanations) | 0 | 0 | 0 |
| SAP SE | einzelmonat 1 | fertig | 4,5 | 7 | 0,9 (19/compare) | 0 | 0 | 0 |
| SAP SE | freie auswahl | fertig | 4,5 | 6 | 0,7 (19/compare) | 0 | 0 | 0 |
| SAP SE | aktie | fertig | 4,5 | 3 | 0,3 (companies) | 0 | 0 | 0 |
| NTT DATA SE | dashboard | fertig | 5,5 | 13 | 1,0 (20/topic-overview) | 0 | 0 | 0 |
| NTT DATA SE | anomalien | fertig | 3,0 | 3 | 1,0 (companies) | 0 | 0 | 0 |
| NTT DATA SE | niveauwechsel 1 | fertig | 2,1 | 6 | 1,9 (20/anomalies/{id}/explanations) | 0 | 0 | 0 |
| NTT DATA SE | niveauwechsel 2 | fertig | 1,8 | 6 | 1,8 (20/anomalies/{id}/explanations) | 0 | 0 | 0 |
| NTT DATA SE | niveauwechsel 3 | fertig | 1,1 | 6 | 1,1 (20/anomalies/{id}/explanations) | 0 | 0 | 0 |
| NTT DATA SE | niveauwechsel 4 | fertig | 0,8 | 6 | 0,8 (20/anomalies/{id}/explanations) | 0 | 0 | 0 |
| NTT DATA SE | freie auswahl | fertig | 0,6 | 6 | 0,6 (20/compare) | 0 | 0 | 0 |
| NTT DATA SE | aktie | fertig | 0,6 | 3 | 0,3 (20/data-status) | 0 | 0 | 0 |
| 1&1 AG | dashboard | fertig | 1,8 | 13 | 1,8 (21/data-status) | 0 | 0 | 0 |
| 1&1 AG | anomalien | fertig | 0,6 | 3 | 0,3 (21/data-status) | 0 | 0 | 0 |
| 1&1 AG | niveauwechsel 1 | fertig | 2,1 | 6 | 2,1 (21/anomalies/{id}/explanations) | 0 | 0 | 0 |
| 1&1 AG | freie auswahl | fertig | 2,5 | 6 | 1,1 (21/compare) | 0 | 0 | 0 |
| 1&1 AG | aktie | fertig | 3,2 | 3 | 0,3 (companies) | 0 | 0 | 0 |
| Bechtle | dashboard | fertig | 2,6 | 13 | 2,8 (24/topic-overview) | 0 | 0 | 0 |
| Bechtle | anomalien | fertig | 0,6 | 3 | 0,5 (24/data-status) | 0 | 0 | 0 |
| Bechtle | niveauwechsel 1 | fertig | 3,4 | 6 | 3,1 (24/anomalies/{id}/explanations) | 0 | 0 | 0 |
| Bechtle | freie auswahl | fertig | 3,1 | 6 | 3,3 (24/compare) | 0 | 0 | 0 |
| Bechtle | aktie | fertig | 0,8 | 3 | 0,7 (24/data-status) | 0 | 0 | 0 |
| Cancom | dashboard | fertig | 2,4 | 13 | 2,3 (25/topic-overview) | 0 | 0 | 0 |
| Cancom | anomalien | fertig | 1,2 | 3 | 1,1 (25/data-status) | 0 | 0 | 0 |
| Cancom | einzelmonat 1 | fertig | 1,3 | 7 | 1,4 (25/compare) | 0 | 0 | 0 |
| Cancom | einzelmonat 2 | fertig | 1,3 | 7 | 1,4 (25/compare) | 0 | 0 | 0 |
| Cancom | freie auswahl | fertig | 6,8 | 6 | 2,1 (25/compare) | 0 | 0 | 0 |
| Cancom | aktie | fertig | 4,5 | 3 | 0,5 (companies) | 0 | 0 | 0 |
| Carl Zeiss | dashboard | fertig | 6,4 | 13 | 2,7 (26/topic-overview) | 0 | 0 | 0 |
| Carl Zeiss | anomalien | fertig | 1,5 | 3 | 0,5 (26/data-status) | 0 | 0 | 0 |
| Carl Zeiss | einzelmonat 1 | fertig | 1,8 | 7 | 1,8 (26/compare) | 0 | 0 | 0 |
| Carl Zeiss | einzelmonat 2 | fertig | 0,8 | 7 | 0,8 (26/compare) | 0 | 0 | 0 |
| Carl Zeiss | freie auswahl | fertig | 3,4 | 6 | 3,4 (26/compare) | 0 | 0 | 0 |
| Carl Zeiss | aktie | fertig | 0,6 | 3 | 0,5 (26/data-status) | 0 | 0 | 0 |
| Compugroup Medical Deutschland | dashboard | fertig | 1,6 | 13 | 1,6 (27/data-status) | 0 | 0 | 0 |
| Compugroup Medical Deutschland | anomalien | fertig | 0,6 | 3 | 0,3 (27/data-status) | 0 | 0 | 0 |
| Compugroup Medical Deutschland | niveauwechsel 1 | fertig | 2,1 | 6 | 1,9 (27/anomalies/{id}/explanations) | 0 | 0 | 0 |
| Compugroup Medical Deutschland | freie auswahl | fertig | 2,1 | 6 | 2,2 (27/compare) | 0 | 0 | 0 |
| Compugroup Medical Deutschland | aktie | fertig | 0,6 | 3 | 0,3 (27/data-status) | 0 | 0 | 0 |
| Telekom | dashboard | fertig | 5,1 | 13 | 5,1 (28/topic-overview) | 0 | 0 | 0 |
| Telekom | anomalien | fertig | 1,4 | 3 | 1,5 (28/data-status) | 0 | 0 | 0 |
| Telekom | niveauwechsel 1 | fertig | 2,1 | 6 | 1,4 (28/anomalies/{id}/explanations) | 0 | 0 | 0 |
| Telekom | niveauwechsel 2 | fertig | 8,7 | 6 | 8,3 (28/anomalies/{id}/explanations) | 0 | 0 | 0 |
| Telekom | niveauwechsel 3 | fertig | 7,4 | 6 | 7,1 (28/anomalies/{id}/explanations) | 0 | 0 | 0 |
| Telekom | niveauwechsel 4 | fertig | 1,9 | 6 | 1,2 (28/anomalies/{id}/explanations) | 0 | 0 | 0 |
| Telekom | einzelmonat 1 | fertig | 2,7 | 7 | 2,7 (28/compare) | 0 | 0 | 0 |
| Telekom | einzelmonat 2 | fertig | 2,9 | 7 | 2,9 (28/compare) | 0 | 0 | 0 |
| Telekom | einzelmonat 3 | fertig | 2,6 | 7 | 2,6 (28/compare) | 0 | 0 | 0 |
| Telekom | freie auswahl | fertig | 5,0 | 6 | 5,0 (28/compare) | 0 | 0 | 0 |
| Telekom | aktie | fertig | 1,3 | 3 | 1,4 (28/data-status) | 0 | 0 | 0 |
| Freenet | dashboard | fertig | 1,4 | 13 | 1,6 (33/topic-overview) | 0 | 0 | 0 |
| Freenet | anomalien | fertig | 0,6 | 3 | 0,3 (33/data-status) | 0 | 0 | 0 |
| Freenet | niveauwechsel 1 | fertig | 1,6 | 6 | 1,4 (33/anomalies/{id}/explanations) | 0 | 0 | 0 |
| Freenet | niveauwechsel 2 | fertig | 1,9 | 6 | 1,8 (33/anomalies/{id}/explanations) | 0 | 0 | 0 |
| Freenet | niveauwechsel 3 | fertig | 1,9 | 6 | 1,6 (33/anomalies/{id}/explanations) | 0 | 0 | 0 |
| Freenet | niveauwechsel 4 | fertig | 1,2 | 6 | 0,8 (33/data-status) | 0 | 0 | 0 |
| Freenet | niveauwechsel 5 | fertig | 1,9 | 6 | 1,8 (33/anomalies/{id}/explanations) | 0 | 0 | 0 |
| Freenet | freie auswahl | fertig | 1,4 | 6 | 1,4 (33/compare) | 0 | 0 | 0 |
| Freenet | aktie | fertig | 0,6 | 3 | 0,4 (33/data-status) | 0 | 0 | 0 |
