# Quellen-Spike: Historische Nachrichten je Unternehmen und Monat

Inkrement 0 „Fundament“, Prüfpunkt 9. Stand: 2026-10-02.
Skript: `backend/scripts/spike_news_sources.py`, Rohdaten: `backend/data/spike_news_sources.json`.

## 1. Zweck

Cycle 2 der Arbeit („Erkennung und Erklärung extremer Veränderungen in Kununu-Bewertungen“)
braucht für einen erkannten Ausreißer-Monat eines Unternehmens **nachträglich** Nachrichten
aus genau diesem Monat, um die Veränderung erklären zu können. Der Spike klärt, welche frei
zugängliche Quelle das (a) überhaupt historisch, (b) je Unternehmen eingrenzbar und
(c) ohne neue Abhängigkeiten liefern kann, getrennt für börsennotierte und nicht
börsennotierte Unternehmen.

## 2. Methode

### 2.1 Geprüfte Quellen

| Kürzel | Quelle | Abfrage | Historie |
|---|---|---|---|
| `gdelt` | GDELT DOC 2.0 API (`api.gdeltproject.org/api/v2/doc/doc`) | `query="<Name>"`, `mode=artlist`, `format=json`, `startdatetime`/`enddatetime` (YYYYMMDDHHMMSS), `maxrecords=75`, `sort=datedesc`, optional `sourcelang:<x>` | ab 2017 |
| `gnews` | Google News RSS (`news.google.com/rss/search`) | `q="<Name>" after:YYYY-MM-DD before:YYYY-MM-DD`, `hl=de&gl=DE&ceid=DE:de`, Parsing mit `xml.etree` | offen (praktisch bis ca. 2000er, dünn vor 2020) |
| `eqs` | EQS News REST (`www.eqs-news.com/wp-json/eqsnews/v1/news`, **undokumentiert**) | `company_name`, `start_date`, `end_date`, `per_page`, `page` | Pflichtmitteilungen seit Bestehen (Thyssenkrupp-UUID: 543 Einträge) |
| `yfinance` | `yfinance.Ticker(<Ticker>).get_news()` und zum Vergleich `yfinance.Search(<Name>).news` | **kein Datumsparameter** | nur die jüngsten Wochen/Monate |

Jede Quelle läuft isoliert in einem eigenen `try/except`, alle `urllib`-Aufrufe mit 20 s
Timeout. Pro Quelle und Lauf wird eine Anfrage gestellt; dokumentierte Ausnahmen:
GDELT erhält bei HTTP 429 genau einen Retry nach 6 s, EQS braucht für die UUID-Ermittlung
mehrere Seiten (siehe 4.3), yfinance stellt zwei Anfragen (`get_news` + `Search`).
Es werden nur `urllib`, `xml.etree`, `json` und das bereits vorhandene `yfinance` genutzt.

Erfasst werden je Quelle: Trefferzahl, davon im Fenster, frühestes/spätestes
Veröffentlichungsdatum, Sprachschätzung (Stoppwort-Heuristik über die Titel plus das
Sprachfeld der Quelle, falls vorhanden), drei Beispieltitel, HTTP-Status, Fehler, Dauer.
Nachtrag 2026-10-08: Die Beispieltitel wurden aus `backend/data/spike_news_sources.json`
entfernt (Maßnahme zu den Nutzungsbedingungen, E7); die Zahlen und Anfrage-URLs bleiben.

### 2.2 Monatswahl (lesend aus der DB)

Für jedes Unternehmen wurde die Employee-Zeitreihe von `durchschnittsbewertung` monatlich
gemittelt. Gewählt wurde der Monat **≥ 2019-01 mit ≥ 5 Bewertungen und der größten absoluten
Änderung des Monatsmittels gegenüber dem Vormonat** (Vormonat = letzter Monat mit Daten,
seine Fallzahl ist nicht beschränkt). Unternehmen werden per normalisiertem Namen
(trim, Whitespace zusammengefasst, casefold) gematcht; die Demo-Firmen sind nicht betroffen.

| Fall | id | Monat | Δ Monatsmittel | Mittel (n) | Vormonat Mittel (n) |
|---|---|---|---|---|---|
| Thyssenkrupp (TKA.DE, DE0007500001) | 3 | **2023-04** | **+1,652** | 4,086 (14) | 2023-03: 2,433 (9) |
| Bechtle (BC8.DE, DE0005158703) | 24 | **2020-10** | **−1,508** | 2,500 (8) | 2020-09: 4,008 (12) |
| Karlsruher Institut für Technologie | 14 | **2023-01** | **+3,029** | 4,029 (7) | 2022-12: 1,000 (1) |
| Open Grid Europe | 4 | **2019-01** | **+1,577** | 4,277 (22) | 2018-12: 2,700 (1) |

Hinweis: Bei KIT und Open Grid Europe beruht der Vormonat auf genau einer Bewertung; die
Deltas sind daher methodisch schwach. Für den Spike (Frage: „liefert die Quelle für diesen
Monat etwas?“) ist das unerheblich, für die spätere Ausreißer-Erkennung muss die
Mindestfallzahl auch für den Vergleichsmonat gelten (offener Punkt für Inkrement 1).

## 3. Ergebnisse

Zahlen = Treffer gesamt / davon im Fenster; Datum = frühester..spätester Treffer; Sprache =
Angabe der Quelle (GDELT, EQS) bzw. Heuristik (Google News).

| Fall / Monat | GDELT DOC | Google News RSS | EQS News REST | yfinance `get_news` / `Search` |
|---|---|---|---|---|
| **Thyssenkrupp 2023-04** | **75 / 68** (Cap `maxrecords=75` erreicht), 04-26..05-01, 63 de / 11 en / 1 es; Domains boerse-social.com, finanznachrichten.de, wiwo.de | **28 / 28**, 04-02..04-28, de; SZ, WiWo, FAZ, Handelsblatt; Treffer u. a. Rücktritt Martina Merz (24.04.) | **5 / 5** (UUID per Discovery, Seite 2), 04-04..04-28, 4 en / 1 de; Kategorien Ad-hoc (Merz-Rücktritt), Finanzbericht-Vorankündigung, 3× Stimmrechte | `get_news`: **0** Einträge; `Search`: 11 / **0 im Fenster** (2026-07..2026-10) |
| **Bechtle 2020-10** | **17 / 17** (nach einem 429-Retry), 10-01..10-30, 12 en / 5 de; telecompaper.com, channelweb.co.uk, stock-world.de | **6 / 6**, 10-11..10-30, de; Regionalpresse, finanzen.net, Netzwoche | **1 / 1** (UUID per Discovery, Seite 6), 26.10.: Ad-hoc „Q3 earnings with above-average climb“ | `get_news`: **0**; `Search`: 2 / **0 im Fenster** (2026-08) |
| **KIT 2023-01** (nicht notiert) | **1 / 1**, 14.01., en (techtimes.com, Themenrelevanz gering) | **9 / 8**, 01-10..02-01, de; WELT, Helmholtz, t3n, BNN – inhaltlich zum KIT, aber keine Personal-/Arbeitgeberthemen | n/a: `company_name=<Klarname>` → Backend-Fehler 500 „API Unavailable“ (kein Emittent, keine UUID) | `get_news`: kein Ticker; `Search`: 0 |
| **Open Grid Europe 2019-01** (nicht notiert) | **0 / 0** (HTTP 200, leere Liste; zwei vorherige Läufe scheiterten mit 429) | **0 / 0** | n/a: wie KIT (500 „API Unavailable“) | `get_news`: kein Ticker; `Search`: 0 |
| Open Grid Europe 2019-01..03 (3-Monats-Fenster, Zusatzlauf) | 13 / 13, 02-03..03-26, 13 en (reuters.com u. a., Power-to-Gas-Themen mit OGE-Nennung) | 2 / 2, 02-03..02-12, 1 relevant (edison.media), 1 irrelevant (WAZ/Aldi Nord) | – | – |

## 4. Qualitative Beobachtungen

### 4.1 GDELT DOC 2.0
- Liefert historische Treffer ab 2017 mit Datum, Sprache, Land und Domain je Artikel; für
  große Namen (Thyssenkrupp) wird das Cap von 75 Datensätzen sofort erreicht, d. h. die
  Monatsabdeckung ist unvollständig (`maxrecords` erlaubt laut Doku bis 250; `artlist`
  liefert keine Gesamtzahl, dafür gäbe es `mode=timelinevolraw`).
- Der Datumsfilter ist nicht exakt: 7 der 75 Thyssenkrupp-Treffer tragen ein `seendate`
  vom 01.05. (vermutlich Zeitzonen-/Crawl-Versatz). `in_window` wird deshalb separat gezählt.
- Titel sind tokenisiert („Kein Gerücht , sondern Faktencheck !“), teils ohne Umlaut-Normalisierung.
- Für kleine Unternehmen (OGE, KIT) sehr dünn und überwiegend englischsprachige
  Branchen-/Agenturmeldungen; deutsche Regionalpresse fehlt weitgehend.
- **Rate-Limit ist das Hauptproblem**: „one request every 5 seconds“ wird per HTTP 429
  durchgesetzt; im Spike schlug mehrfach schon die erste Anfrage fehl und auch der Retry
  nach 6 s war nicht immer erfolgreich (OGE: erst der dritte Lauf lieferte 200). Vermutlich
  zählt das Limit je IP und wurde durch parallele Nutzung verschärft. Für Batch-Läufe ist ein
  Abstand deutlich über 5 s und ein robuster Retry mit Backoff nötig.

### 4.2 Google News RSS
- Historische Treffer über `after:`/`before:` funktionieren für alle vier Fälle, auch 2019/2020,
  mit deutscher Presse (SZ, FAZ, Handelsblatt, WiWo, Regionalzeitungen) und deutschen Titeln.
- Das Feed liefert maximal rund 100 Einträge ohne Paginierung, keine Gesamtzahl; die
  Datumsoperatoren sind nicht ganz scharf (KIT: 1 Treffer vom 01.02. bei `before:2023-02-01`).
- Treffer enthalten Titel, `pubDate`, Quelle und einen Google-Redirect-Link; keine Volltexte,
  keine Sprachangabe je Eintrag (nur `channel/language = de`).
- Relevanz: Für Thyssenkrupp und Bechtle sehr gut (Unternehmens-Ereignisse); für KIT
  thematisch zum Institut, aber keine Arbeitgeberthemen; für OGE 2019 null Treffer, im
  Dreimonatsfenster teils Streutreffer (Artikel nennt das Unternehmen nur beiläufig).
- Inoffiziell: kein dokumentiertes Rate-Limit, aber das Feed ist laut `<copyright>` nur für
  persönliche, nicht-kommerzielle Feed-Reader gedacht. Für eine Bachelorarbeit mit wenigen
  Anfragen vertretbar, muss in der Arbeit aber als Einschränkung genannt werden.

### 4.3 EQS News REST (undokumentiert)
- `GET /wp-json/eqsnews/v1/` listet die Routen; `/news` akzeptiert `per_page`, `page`,
  `company_name`, `start_date`, `end_date`, `category`, `region`, `market`, `sector`.
- Was **nicht** funktioniert (jeweils HTTP 200 mit `{"error":{"status":500,"message":"API
  Unavailable"}}`): `company_name=Thyssenkrupp`, `company_name=thyssenkrupp AG`,
  `company_name=Bechtle`, `company_name=Bechtle AG`, `company_name=DE0007500001` (ISIN).
  Das Antwortfeld `post_fields.companyId` zeigt, dass der Wert unverändert als **companyUUID**
  an das EQS-Backend weitergereicht wird. `category=adhoc` ändert die Treffermenge, filtert
  aber erkennbar nicht auf Ad-hoc; `market`, `region` zeigten keine Wirkung; `per_page=500`
  wird serverseitig auf 100 gekappt. WordPress-Suche (`/wp-json/wp/v2/search?search=…`)
  liefert `[]`, eine Unternehmensseite `/company/thyssenkrupp-ag/` existiert nicht (404).
- Was funktioniert:
  1. Datumsgefilterte Gesamtliste `start_date=YYYY-MM-DD&end_date=YYYY-MM-DD&per_page=100&page=N`
     (April 2023: 4 758 Mitteilungen, Oktober 2020: 2 460). Jeder Datensatz enthält
     `companyName`, `companyUUID`, `isin`, `headline`, `language`, `category`, `date`/`dateUtc`.
  2. `company_name=<companyUUID>&start_date&end_date` liefert dann exakt die Mitteilungen des
     Emittenten im Fenster (Thyssenkrupp 2023-04: 5, Bechtle 2020-10: 1), ohne Fenster die
     gesamte Historie (Thyssenkrupp: 543).
  Das Skript ermittelt die UUID per ISIN-/Namensabgleich über die Monatsliste
  (`--eqs-find-uuid N`, 1 s Pause je Seite; Thyssenkrupp: 2 Seiten, Bechtle: 6 Seiten) und
  speichert sie; danach genügt `--eqs-uuid <uuid>` mit einer Anfrage.
- Kuriosum: `end_date=2023-04-30` wird backendseitig zu `2023-04-30 23:23:59` (nicht 23:59:59).
- Inhalt: Pflichtmitteilungen (Ad-hoc, Stimmrechte, Finanzberichte), meist Englisch, sehr
  präzise und datiert, aber kein journalistischer Kontext und nur für Emittenten;
  für KIT und OGE strukturell ungeeignet. Rechtlich/organisatorisch ungesichert
  (undokumentiert, ohne Nutzungsbedingungen für die API).

### 4.4 yfinance
- **`yfinance.Ticker(ticker).get_news()` hat keinen Datumsfilter** (Signatur
  `get_news(count=10, tab='news')`). Im Spike lieferte es für TKA.DE, BC8.DE und auch
  SAP.DE/TKAMY **0 Einträge** (yfinance 1.7.0; der Yahoo-Endpunkt
  `finance.yahoo.com/xhr/ncp?queryRef=latestNews` antwortet leer).
- `yfinance.Search(<Name>, news_count=20).news` liefert 2–11 aktuelle Einträge (ältester
  2026-07), **0 im jeweiligen Fenster**, ausschließlich Englisch (Zacks, GuruFocus, Business
  Wire). Für nicht notierte Namen 0 Treffer.
- Damit ist yfinance für historische Nachrichten unbrauchbar (blinder Fleck dokumentiert);
  es bleibt allenfalls für Kursdaten (`history()`) relevant, nicht für Nachrichten.

## 5. Empfehlung

| | Primär | Sekundär | Nicht geeignet |
|---|---|---|---|
| **Börsennotiert** (Ticker/ISIN vorhanden) | Google News RSS (deutsche Presse, alle Jahre, 1 Anfrage) | EQS News REST per companyUUID (exakte, datierte Pflichtmitteilungen als „harte“ Ereignisanker); GDELT DOC als Ergänzung mit Sprach-/Länderfeld, aber Rate-Limit und 75er-Cap | yfinance (kein Datumsfilter, 0 historische Treffer) |
| **Nicht börsennotiert** | Google News RSS | GDELT DOC (dünn, meist Englisch, nur ab 2017; sinnvoll erst mit Fenster ≥ 3 Monate) | EQS (kein Emittent), yfinance |

Begründung: Google News RSS war die einzige Quelle mit relevanten, deutschsprachigen Treffern
in allen Fällen mit Berichterstattung und ohne Rate-Limit-Probleme; EQS liefert für
Emittenten die präzisesten Ereignisdaten, erfordert aber den UUID-Umweg und ist
undokumentiert; GDELT ist historisch breit, aber praktisch durch 429-Antworten und das
Trefferlimit gebremst. Für Unternehmen mit geringer Medienpräsenz (OGE 2019) liefert keine
Quelle einen Monatstreffer; hier ist ein weiteres Fenster (±1 Monat) oder eine andere
Erklärungsquelle (z. B. Review-Texte selbst) nötig.

## 6. Entscheidung (vorläufig, vom Autor zu bestätigen)

1. **Google News RSS** wird primäre Nachrichtenquelle für die Erklärungskomponente, für
   notierte und nicht notierte Unternehmen, mit Monatsfenster und Fallback auf ±1 Monat
   bei 0 Treffern.
2. **EQS News REST** wird für börsennotierte Unternehmen als sekundäre Quelle aufgenommen;
   die companyUUID wird einmalig je Unternehmen ermittelt und in der Konfiguration abgelegt
   (Thyssenkrupp `5b6db068-ea7c-11e8-902f-2c44fd856d8c`, Bechtle
   `5b745f9b-ea7c-11e8-902f-2c44fd856d8c`). Die Nutzung ist als „undokumentierte,
   jederzeit änderbare Schnittstelle“ in der Arbeit zu kennzeichnen.
3. **GDELT DOC** bleibt optional (Flag), nicht im Standardpfad, wegen Rate-Limit und Cap.
4. **yfinance** wird für Nachrichten nicht verwendet; der fehlende Datumsfilter wird in der
   Arbeit als Begründung genannt.
5. Die Monatswahl-Regel wird in Inkrement 1 um eine Mindestfallzahl für den Vergleichsmonat
   ergänzt (siehe 2.2).

Zu bestätigen durch den Autor: Nutzungsbedingungen von Google News RSS und EQS für den
Einsatz in der Arbeit; ob englischsprachige Treffer (EQS, GDELT) in die Erklärung einfließen
oder gefiltert werden; Fenstergröße (1 vs. 3 Monate).

## 7. Reproduktion

Alle Befehle aus `backend/`; Ergebnisse werden in `backend/data/spike_news_sources.json`
gemerged (Schlüssel `name|YYYY-MM`, bei `--window-months N>1` mit Suffix `+Nm`). Der
DB-Zugriff (`--pick-month`) ist strikt lesend. Zwischen Läufen mindestens 10 s warten
(GDELT-Limit).

```bash
cd backend
uv run python scripts/spike_news_sources.py --company "Thyssenkrupp" --pick-month \
    --ticker TKA.DE --isin DE0007500001 --eqs-find-uuid 60
uv run python scripts/spike_news_sources.py --company "Bechtle" --pick-month \
    --ticker BC8.DE --isin DE0005158703 --eqs-find-uuid 60
uv run python scripts/spike_news_sources.py --company "Karlsruher Institut für Technologie" --pick-month
uv run python scripts/spike_news_sources.py --company "Open Grid Europe" --pick-month

# Einzelne Quelle nachziehen (z. B. nach GDELT-429), Ergebnis wird je Quelle gemerged:
uv run python scripts/spike_news_sources.py --company "Open Grid Europe" --month 2019-01 --sources gdelt

# Zusatzlauf mit 3-Monats-Fenster (eigener Schlüssel):
uv run python scripts/spike_news_sources.py --company "Open Grid Europe" --month 2019-01 \
    --window-months 3 --sources gdelt,gnews

# Mit bekannter EQS-UUID (eine Anfrage statt Discovery):
uv run python scripts/spike_news_sources.py --company "Thyssenkrupp" --month 2023-04 \
    --ticker TKA.DE --isin DE0007500001 --eqs-uuid 5b6db068-ea7c-11e8-902f-2c44fd856d8c
```

Manuelle Prüfungen des EQS-Endpunkts (nur Lesezugriffe):

```bash
curl -s "https://www.eqs-news.com/wp-json/eqsnews/v1/"                      # Routenliste
curl -s "https://www.eqs-news.com/wp-json/eqsnews/v1/news?company_name=Thyssenkrupp&per_page=5"   # -> 500 "API Unavailable"
curl -s "https://www.eqs-news.com/wp-json/eqsnews/v1/news?start_date=2023-04-24&end_date=2023-04-24&per_page=100"   # Tagesliste
curl -s "https://www.eqs-news.com/wp-json/eqsnews/v1/news?company_name=5b6db068-ea7c-11e8-902f-2c44fd856d8c&start_date=2023-04-01&end_date=2023-04-30"
```

## 8. Offene Punkte

- GDELT-429 trat auch bei Einzelanfragen auf; Ursache (geteilte IP, parallele Nutzung) ist
  nicht geklärt. Vor einem Einsatz: Backoff-Strategie und Abstand ≥ 10 s testen.
- Google News liefert Redirect-Links; für Volltexte wäre ein weiterer Abruf je Artikel nötig
  (im Spike nicht geprüft, Nutzungsbedingungen beachten).
- EQS-UUIDs für weitere notierte Unternehmen der DB (SAP, Telekom, TecDAX-Werte) sind noch
  nicht ermittelt; die Discovery benötigt pro Unternehmen bis zu ~50 Anfragen.
- Die Sprachschätzung ist eine Heuristik über Titel; bei EQS/GDELT ist das Quellfeld maßgeblich.
