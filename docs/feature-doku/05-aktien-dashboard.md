# 05 – Aktien-Dashboard

| | |
|---|---|
| Inkrement | 3 (Nachtrag, Zyklus 2) |
| Anforderungen | Wunsch des Autors vom 2026-10-04: eigenes Dashboard zum Aktienkurs mit Kursverlauf, Analystenempfehlungen, Umsatz und Gewinn sowie Nachrichten. Davon deckt nur der Teil Kurs und Kennzahlen eine Anforderung (FA-15) |
| Entscheidungen | E16 in `docs/entscheidungen.md` (mit „Rolle in der Arbeit“); E7 (Nachrichtenquelle) und E15 (Kurs, Kennzahlen, Zwischenspeicher) |
| Status | umgesetzt; **vorläufig** (Nutzungsbedingungen offen). Zusatzkarten außerhalb des evaluierten Artefakts, ausblendbar mit `VITE_SHOW_FINANCE_EXTRAS=false` |
| Stand | 2026-10-05 |

## 1. Vorstellung

> **Rolle in der Arbeit (2026-10-05, E16):** Kurs und Kennzahlen decken FA-15, die
> Anforderung an Kurs und zwei bis drei Kennzahlen. Die Karten **Analystenempfehlungen**,
> **Umsatz und Nettoergebnis** und **Aktuelle Meldungen** samt den Kacheln Nettoergebnis und
> Analysten sind ein **Zusatz** ohne Anforderung aus den Interviews und gehören nicht zum
> evaluierten Artefakt. Der Schalter `VITE_SHOW_FINANCE_EXTRAS` blendet sie aus (Standard an,
> also wie unten beschrieben). Die Beschreibung unten gilt für den Standard; ohne Zusatzkarten
> siehe „Ansicht ohne Zusatzkarten“.

Die Seite **„Aktie“** (`/aktie?company=ID`) öffnet sich über „Aktie“ in der Seitenleiste
des Dashboards oder über den Link „Aktien-Dashboard“ unter dem Diagramm der
Anomalien-Detailseite. Oben rechts lässt sich die Firma wechseln.

**Aufbau (seit 2026-10-05, Wunsch des Autors):** Alles steht auf einer Bildschirmseite
(geprüft bei 1440 × 900 Pixeln). Oben eine **Kennzahlenleiste** mit sechs Kacheln, darunter
ein Raster aus Karten: links oben die Kurskarte (zwei Spalten breit), rechts die
Nachrichten (über zwei Reihen, scrollbar), links unten Analystenempfehlungen und Umsatz und
Nettoergebnis. Ganz unten steht eine Zeile mit Wertpapier, Quelle, Abrufdatum und dem
Hinweis „Einordnung, keine Erklärung“. Wie im Haupt-Dashboard **vergrößert ein Klick** eine
Karte auf 90 % × 85 % des Fensters, mit denselben Schaltern; Zusatzzeilen (Legende des
Bewertungsverlaufs, Zusammenfassung der Empfehlungen, Währungshinweis, Quellenzeile der
Nachrichten) stehen nur dort. Schalter stehen in der Kopfzeile neben dem Titel. **Ab 1280 px
Breite füllt das Raster die Fensterhöhe** (mindestens 620 px) und die Diagramme wachsen mit
dem Fenster: bei 1280 × 800 Pixeln etwa 210 px für den Kurs, bei 1440 × 900 etwa 265 px, bei
1920 × 1080 etwa 375 px. Schmalere Fenster zeigen die Karten mit festen Höhen untereinander.
Die Größen wurden am 2026-10-05 mit dem Autor abgestimmt (erst kleiner, dann wieder etwas
größer; das Füllen der Fensterhöhe ist der Kompromiss).

1. **Kennzahlen:** letzter Monatsschlusskurs mit Veränderung im gewählten Fenster,
   Marktkapitalisierung und Mitarbeitende („aktuell, Stand …“), Umsatz und Nettoergebnis des
   letzten Geschäftsjahrs, Analystenempfehlungen als „kaufen / halten / verkaufen“.
2. **Kurskarte** mit zwei Ansichten (`?ansicht=bewertung`):
   - **Kurs:** Kursverlauf als Fläche, Zeitfenster 1, 3, 5, 10 Jahre oder alles (`?range=`).
   - **Mit Bewertung:** der Monatsverlauf der Sternebewertung (Mitarbeitende,
     Gesamtbewertung) mit den auffälligen Veränderungen und Einzelmonaten, darüber der Kurs
     als dünne Linie auf der rechten Achse (Darstellung aus Feature 04). Kästchen
     „Aktienkurs“ und Zeitfilter wie auf der Anomalien-Seite (`?kurs=aus`,
     `?verlauf=5y|3y|1y`). In der vergrößerten Ansicht öffnet ein Klick auf eine Stufe oder
     Raute die Veränderung mit Vergleich und Bewertungen auf der Anomalien-Seite. Dieses
     Diagramm stand bis zum 2026-10-04 auf der Anomalien-Seite und wurde auf Wunsch des
     Autors hierher verschoben. Seit 2026-10-05 lässt sich der Kurs dort wieder einblenden,
     Standard aus (Feature 04, E15).
3. **Analystenempfehlungen** (Zusatz): gestapelte Balken je Monat (letzte vier Monate) mit
   der Zahl der Empfehlungen „stark kaufen“ bis „stark verkaufen“; der Tooltip nennt alle
   Stufen.
4. **Umsatz und Nettoergebnis** (Zusatz): Balken je Geschäftsjahr oder, umschaltbar, je
   Quartal.
5. **Aktuelle Meldungen** (Zusatz): die neuesten Meldungen der letzten 90 Tage mit Quelle,
   Datum und Link, in der Karte scrollbar.

Für Unternehmen ohne Ticker zeigt die Seite neben den Meldungen nur „Kein Aktienkurs: …“;
unter 1280 px Breite steht dieser Hinweis über der Meldungskarte in voller Breite (vorher
blieb daneben eine Spalte leer).

**Ansicht ohne Zusatzkarten** (`VITE_SHOW_FINANCE_EXTRAS=false`): Die Kennzahlenleiste hat vier
Kacheln (Kurs, Marktkapitalisierung, Mitarbeitende, Umsatz des letzten Geschäftsjahrs; unter
768 px zwei mal zwei). Darunter nimmt die Kurskarte mit beiden Ansichten („Kurs“, „Mit
Bewertung“) das ganze Raster ein, ab 1280 px die ganze Höhe bis zur Hinweiszeile, schmaler mit
fester Höhe. Ganz unten steht die Zeile mit Wertpapier, Quelle und festem Hinweis. Ohne
Ticker steht nur „Kein Aktienkurs: …“ in voller Breite. Der Link auf der Anomalien-Seite nennt
dann „Aktienkurs und Kennzahlen“ statt „Aktienkurs, Kennzahlen und Nachrichten“.

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
- **Schalter `VITE_SHOW_FINANCE_EXTRAS`** (Frontend, `frontend/src/config.js`): Vite liest ihn
  beim Bauen bzw. beim Start des Entwicklungsservers, etwa
  `VITE_SHOW_FINANCE_EXTRAS=false npm run build` oder im Docker-Bau als Build-Argument
  (`frontend/Dockerfile`). Ohne Angabe oder mit einem anderen Wert als `false`/`0` ist er an.
  Aus heißt: Die Seite ruft `GET /api/analytics/company/{id}/market` (Kurs und Kennzahlen
  aus E15) statt `/finance` ab und `/news` gar nicht; Karten und Kacheln der Zusätze werden
  nicht gezeichnet. Backend und Endpunkte bleiben unverändert.

## 3. Begründung

- Der Aufbau folgt der Kursseite von Yahoo Finance, die der Autor als Vorbild nannte.
- Die Finanzseite der Test-Kopie hing an gelöschten Tabellen und wurde neu gebaut, auf
  demselben Zwischenspeicher wie Feature 04, ohne Datenbankänderung.
- Nachrichten kommen aus Google-News-RSS, weil yfinance für keinen der 17 Ticker Meldungen
  liefert und E7 Google News ohnehin als Hauptquelle festlegt. So gibt es Meldungen auch für
  nicht notierte Unternehmen.
- Kein Bezug zu den Bewertungen: Die Seite zeigt Marktinformationen nebeneinander, ordnet
  sie keiner auffälligen Veränderung zu und bewertet sie nicht.
- **Rolle in der Arbeit (2026-10-05, E16):** FA-15 verlangt nur den Kurs und zwei bis drei
  Kennzahlen; Empfehlungen, Erfolgszahlen und Meldungen gehen auf den Wunsch des Autors
  zurück, nicht auf die Interviews. Damit die Evaluation (DZ3) nur das Artefakt zeigt, das
  sich aus den Anforderungen ergibt, lassen sich die Zusätze ausblenden. Ein Schalter statt
  Entfernen, weil die Seite außerhalb der Evaluation wie gewünscht bestehen bleibt; Standard an,
  damit sich ohne Zutun nichts ändert. Ohne Zusatzkarten werden ihre Endpunkte auch nicht
  abgerufen, damit die Evaluationsinstanz keine Daten lädt, die sie nicht zeigt.

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
- Manuelle Prüfung 2026-10-05 (Branch `feature/korrektur-kurs-integration`), beide Zustände
  des Schalters nebeneinander (Entwicklungsserver mit und ohne `VITE_SHOW_FINANCE_EXTRAS=false`):
  - an: SAP SE bei 1440 × 900 wie vorher (sechs Kacheln, vier Karten), Abrufe `/finance` und
    `/news`; Open Grid Europe bei 1100 px ohne leere Spalte, bei 1440 px wie vorher,
  - aus: SAP SE, Telekom, RWE und NTT DATA SE mit vier Kacheln und Kurskarte über die ganze
    Fläche, nur `/market` abgerufen, kein `/finance`, kein `/news`; Ansicht „Mit Bewertung“
    und vergrößerte Karte funktionieren; NTT DATA SE mit Vermerk der Konzernmutter; Open Grid
    Europe nur mit „Kein Aktienkurs“ in voller Breite; 1440, 1100 und 375 Pixel Breite ohne
    Lücken und ohne seitliches Scrollen; hell und dunkel.
- Bau mit und ohne Schalter (`npm run build`, `VITE_SHOW_FINANCE_EXTRAS=false vite build`)
  fehlerfrei. Der Docker-Bau mit Build-Argument wurde nicht ausgeführt.

## 6. Offene Punkte

- Nutzungsbedingungen von Yahoo Finance und Google News (E7, E15, E16).
- Soll die Seite in der Evaluation (DZ3) gezeigt werden? Nachtrag 2026-10-05: Kurs und
  Kennzahlen gehören zum evaluierten Artefakt, die Zusatzkarten nicht (E16); offen bleibt, ob
  die Evaluationsinstanz mit `VITE_SHOW_FINANCE_EXTRAS=false` gebaut wird.
- Der Hinweistext des Eintrags „Aktie“ in der Seitenleiste des Dashboards nennt weiter
  „Aktienkurs, Empfehlungen, Umsatz und Nachrichten“, auch ohne Zusatzkarten
  (`frontend/src/pages/Dashboard.jsx` hat ältere Lint-Fehler und wurde nicht angefasst).
- Bessere Suchbegriffe für mehrdeutige Namen (z. B. Carl Zeiss), vom Autor festzulegen.
