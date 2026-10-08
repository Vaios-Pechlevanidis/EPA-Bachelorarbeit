# Nutzungsbedingungen der externen Datenquellen (E7, E15, E16)

Stand: 2026-10-08. Zusammenstellung der Fundstellen für die drei Quellen, die das Projekt für
Kurs, Kennzahlen und Nachrichten nutzt: Yahoo Finance über die Bibliothek `yfinance`, Google
News RSS und EQS News. Alle Seiten wurden am **2026-10-08** abgerufen (HTTP-Abruf mit
Browser-Kennung, HTML in Text umgewandelt); die Zitate sind wörtlich und kurz. Dieses Dokument
enthält **keine rechtliche Bewertung**; die Spalte „Bewertung“ bleibt leer und wird mit dem
Betreuer geklärt. Kununu als Quelle der Bewertungen ist nicht Gegenstand dieses Dokuments.

## 1. Yahoo Finance über `yfinance`

Verwendet werden Monatsschlusskurse (`period="max"`, `interval="1mo"`, `auto_adjust=True`),
Marktkapitalisierung, Zahl der Mitarbeitenden, Umsatz und Nettoergebnis (`income_stmt`,
`quarterly_income_stmt`) sowie Analystenempfehlungen (`recommendations`) für 17 Ticker
(`backend/services/context_service.py`, `backend/scripts/fetch_market_data.py`). Installierte
Version: `yfinance` 1.7.0 (Apache-Lizenz). `yfinance` nutzt keinen registrierten API-Schlüssel,
sondern die Endpunkte der Yahoo-Finance-Website (Host `query2.finance.yahoo.com`).

### 1.1 Allgemeine Geschäftsbedingungen von Yahoo (deutsche Fassung für Europa)

- Adresse: <https://legal.yahoo.com/ie/de/yahoo/terms/otos/index.html>, Anbieter laut Abschnitt
  „Europa, Mittlerer Osten und Afrika“: Yahoo International Limited, Dublin. Stand der Seite:
  „Zuletzt aktualisiert: 19. August 2026“. Englische Fassung (USA):
  <https://legal.yahoo.com/us/en/yahoo/terms/otos/index.html>, „Last updated: 4 August 2026“.
- Einschlägige Stellen (wörtlich):
  - Liste der untersagten Handlungen: „ohne unsere ausdrückliche, vorherige Genehmigung auf
    Daten unserer Dienste zuzugreifen oder Daten unserer Dienste zu erfassen oder zu versuchen,
    auf Daten zuzugreifen oder Daten zu erfassen, indem Sie automatisierte Hilfsmittel, Geräte,
    Programme, Algorithmen oder Methoden verwenden, insbesondere Roboter, Spiders, Scraper,
    Data-Mining-Tools oder Tools zum Erfassen oder Extrahieren von Daten, zu welchem Zweck auch
    immer.“
  - Ebenda: „Materialien oder Inhalte zu verwenden, um (a) Datenbanken, Archive, mobile
    Anwendungen, Datenfeeds, Widgets oder andere aggregierte Datenquellen zu erstellen, die mit
    den Diensten oder den von Yahoo oder unseren Datenanbietern angebotenen Diensten
    konkurrieren oder einen wesentlichen Ersatz darstellen, oder (b) einen Dienst
    bereitzustellen, der mit unseren Diensten oder den von Yahoo oder unseren Datenanbietern
    angebotenen Daten konkurriert oder einen wesentlichen Ersatz darstellt.“
  - Abschnitt zu den Rechten an den Diensten: „Ohne ausdrückliche schriftliche Genehmigung ist
    es Ihnen nicht gestattet, Teile der Dienste, deren Nutzung oder den Zugriff darauf
    (einschließlich Inhalte, Werbung, APIs und Software) zu reproduzieren, zu verändern, zu
    vermieten, zu verpachten, zu verkaufen, zu handeln, zu verbreiten, zu übertragen,
    öffentlich aufzuführen, abgeleitete Werke daraus zu erstellen oder sie für kommerzielle
    Zwecke zu nutzen.“
  - „Softwarelizenz. Vorbehaltlich Ihrer fortdauernden Einhaltung dieser AGB gewähren wir Ihnen
    eine persönliche, gebührenfreie, nicht übertragbare, nicht abtretbare, widerrufliche und
    nicht-exklusive Lizenz zur Nutzung der Software und APIs, die wir Ihnen im Rahmen der
    Dienste bereitstellen.“
  - „Richtlinie gegen Missbrauch. […] Ohne unsere vorherige schriftliche Zustimmung ist es
    Ihnen nicht gestattet, im Rahmen der Nutzung unserer Dienste auf nicht-kommerziellen
    Websites oder Apps kommerzielle Aktivitäten durchzuführen oder Aktivitäten mit hohem
    Volumen auszuüben.“

### 1.2 Yahoo-Finance-Hilfeseite „Exchanges and data providers on Yahoo Finance“

- Adresse: <https://help.yahoo.com/kb/finance-for-web/SLN2310.html> (ohne Datumsangabe auf der
  Seite).
- Wörtlich: „Do not redistribute information - Yahoo Finance provides all information as is.
  You must not redistribute information displayed on or provided by Yahoo Finance.“ und „All
  data provided on Yahoo Finance is provided for informational purposes only, and is not
  intended for trading or investing purposes.“
- Datenlieferanten laut dieser Seite, soweit das Projekt die Daten nutzt: Kurse der Deutschen
  Börse XETRA („.DE 15 min ICE Data Services“) und der Tokyo Stock Exchange („.T 20 min ICE
  Data Services“); „International historical chart data and daily updates provided by
  Morningstar“; „Financial statements, valuation ratios, market cap and shares outstanding data
  provided by Morningstar“; „Global company profile, EPS and revenue estimates & actuals,
  analyst recommendations and price target data provided by S&P Global Market Intelligence“.
  Für LSEG-Inhalte (vom Projekt nicht genutzt) heißt es: „Any copying, republication or
  redistribution of LSEG content, including by caching, framing or similar means, is expressly
  prohibited without the prior written consent of LSEG.“

### 1.3 Yahoo Developer API Terms of Use

- Adresse: <https://legal.yahoo.com/us/en/yahoo/terms/product-atos/apiforydn/index.html> (ohne
  Datumsangabe auf der Seite). Gilt für die registrierten „Yahoo APIs“ mit API-Schlüssel: „The
  individual who accepts these terms and conditions must be aged 13 years or older, must
  possess his or her own valid Yahoo account“. Untersagt ist unter anderem: „Sell, lease,
  share, transfer, or sublicense the Yahoo APIs or access or access codes thereto or derive
  income from the use or provision of the Yahoo APIs“. Ob diese Bedingungen für die von
  `yfinance` genutzten Endpunkte gelten, ist offen (kein API-Schlüssel, keine Registrierung);
  die `yfinance`-Dokumentation verweist auf sie.

### 1.4 Hinweise der Bibliothek `yfinance` (README des Projekts ranaroussi/yfinance)

- Adresse: <https://github.com/ranaroussi/yfinance> (README, Stand des Hauptzweigs am
  2026-10-08).
- Wörtlich: „yfinance is not affiliated, endorsed, or vetted by Yahoo, Inc. It's an open-source
  tool that uses Yahoo's publicly available APIs, and is intended for research and educational
  purposes.“ und „You should refer to Yahoo!'s terms of use […] for details on your rights to
  use the actual data downloaded. Remember - the Yahoo! finance API is intended for personal
  use only.“

### 1.5 robots.txt

- <https://query2.finance.yahoo.com/robots.txt> (Host der von `yfinance` genutzten Endpunkte),
  vollständiger Inhalt: „User-agent: * / Disallow: /“.
- <https://finance.yahoo.com/robots.txt>: lange Liste gesperrter Crawler-Kennungen; die
  Pfade der Datenendpunkte (`/xhr`, `/_remote`, `/_td_api`) sind für die dort genannte
  Kennung gesperrt.

### 1.6 Geprüft, aber nicht einschlägig

- „Yahoo Finance Community – Additional Terms and Conditions“ (Stand „November 2025“,
  <https://legal.yahoo.com/us/en/yahoo/terms/product-atos/finance/index.html>): betrifft das
  Nutzerforum, nicht die Kursdaten.

## 2. Google News RSS

Verwendet wird die Suche `https://news.google.com/rss/search?q=<Name> when:90d&hl=de&gl=DE&ceid=DE:de`
(eine Anfrage je Unternehmen, `backend/services/news_service.py`, Kennung
„EPA-Bachelorarbeit/0.1; research, non-commercial“); im Spike vom 2026-10-02 außerdem mit den
Operatoren `after:`/`before:` je Monat (`backend/scripts/spike_news_sources.py`). Gespeichert
werden je Meldung Titel, Quelle, Link (Google-Weiterleitung) und Datum; keine Volltexte.

### 2.1 Vermerk im Feed selbst

- Abgerufen am 2026-10-08 über die oben genannte Adresse; Element `<copyright>` der Antwort,
  wörtlich: „Copyright © 2026 Google. All rights reserved. This XML feed is made available solely
  for the purpose of rendering Google News results within a personal feed reader for personal,
  non-commercial use. Any other use of the feed is expressly prohibited. By accessing this feed
  or using these results in any manner whatsoever, you agree to be bound by the foregoing
  restrictions.“

### 2.2 Google-Nutzungsbedingungen (Landesversion Deutschland)

- Adresse: <https://policies.google.com/terms?hl=de>, „Wirksam ab dem 30. Juli 2026 |
  Landesversion: Deutschland“ (englisch: <https://policies.google.com/terms?hl=en>, „Effective
  July 30, 2026“).
- Abschnitt „Sie missbrauchen unsere Dienste nicht“, wörtlich: „Sie dürfen unsere Dienste oder
  Systeme nicht missbrauchen, schädigen, beeinträchtigen oder stören etwa durch: […] Verwendung
  automatisierter Mittel, um auf Inhalte unserer Dienste zuzugreifen, wobei diese Mittel gegen
  die maschinenlesbaren Vorgaben auf unseren Webseiten verstoßen (z. B. robots.txt-Dateien, mit
  denen Crawling, Training oder andere Aktivitäten verhindert werden)“.
- Abschnitt „Andere Inhalte“, wörtlich: „Über einige unserer Dienste haben Sie zudem Zugriff
  auf Inhalte, die anderen Personen oder Organisationen gehören, beispielsweise die Beschreibung
  des eigenen Unternehmens durch den Inhaber oder ein Zeitungsartikel in Google News. Sie dürfen
  diese Inhalte nicht ohne die Erlaubnis dieser Person oder Organisation nutzen, sofern dies
  nicht anderweitig gesetzlich zulässig ist.“
- Abschnitt „Google-Inhalte“, wörtlich: „Sie dürfen die Inhalte von Google gemäß diesen
  Nutzungsbedingungen und etwaigen dienstspezifischen Zusatzbedingungen verwenden, wir behalten
  jedoch sämtliche geistige Eigentumsrechte, die wir an unseren Inhalten haben.“

### 2.3 robots.txt

- <https://news.google.com/robots.txt>, Anfang wörtlich: „User-agent: * / Disallow: / /
  Allow: /$ / Allow: /? / Allow: /home$ / Allow: /home? / Allow: /home/ / Allow: /nwshp$ /
  Allow: /topics/ / Allow: /publications/ / Allow: /stories/ / Allow: /swg/ / Allow: /about$ /
  Allow: /about? / Allow: /about/“. Der Pfad `/rss/` steht nicht unter den erlaubten Pfaden.

## 3. EQS News

EQS wird bisher **nur im Spike** genutzt (`backend/scripts/spike_news_sources.py`, Ergebnisse in
`backend/data/spike_news_sources.json`), nicht im Dashboard. E7 sieht EQS als sekundäre Quelle
für börsennotierte Unternehmen vor. Genutzt wurde die undokumentierte REST-Route
`https://www.eqs-news.com/wp-json/eqsnews/v1/news` (Parameter `company_name`=companyUUID,
`start_date`, `end_date`); die UUID je Emittent wurde über die datumsgefilterte Gesamtliste
ermittelt (mehrere Anfragen je Unternehmen).

### 3.1 Legal Notice von eqs-news.com

- Adresse: <https://www.eqs-news.com/legal-notice/>; Betreiber laut Seite: EQS Group GmbH,
  München; Fußzeile „© 2026 EQS Group GmbH. All rights reserved.“
- Wörtlich: „All texts, images, graphics, audio and video files used on the EQS Group website
  are subject to copyright and other laws for the protection of intellectual property. They are
  intended for personal use only and may not be copied, either for trading purposes or for
  transfer to third parties, nor modified and used on other websites.“
- Wörtlich: „EQS Group does not permit the use or downloading of content from this website by
  third parties for the development, training or operation of artificial intelligence or other
  machine learning systems (“text and data mining”) without the express written consent of EQS
  Group.“
- Wörtlich: „EQS Group does not assume liability for the content of the information provided.“

### 3.2 Terms and Conditions (Fußzeile von eqs-news.com)

- Der Link „Terms and Conditions“ führt auf <https://www.eqs.com/about-eqs/terms-and-conditions/>.
  Die Seite listet PDF-Dateien zum Herunterladen („EQS Group Terms – Worldwide – English /
  German“, Dateien `260602-EQS-Terms_worldwide_EN.pdf` und `_DE.pdf`, dazu produktspezifische
  Bedingungen und Vereinbarungen zu Cloud-Diensten). Das sind erkennbar Vertragsbedingungen für
  Kunden der EQS Group; ob sie für das Lesen von eqs-news.com gelten, ist offen. **Die PDFs
  wurden nicht ausgewertet; ein Wortlaut wird hier nicht wiedergegeben.**

### 3.3 Nicht abrufbar oder nicht vorhanden

- `https://www.eqs-news.com/terms-of-use/`, `https://www.eqs-news.com/de/nutzungsbedingungen/`,
  `https://www.eqs-news.com/imprint/`, `https://www.eqs-news.com/privacy-policy/`: HTTP 404.
- Die REST-Route `https://www.eqs-news.com/wp-json/eqsnews/v1/` liefert nur die Routenliste und
  keine Nutzungsbedingungen (undokumentierte Schnittstelle, E7).

### 3.4 robots.txt

- <https://www.eqs-news.com/robots.txt>: umfangreiche Sperrliste für KI- und Scraping-Crawler,
  danach für alle Kennungen wörtlich: „User-agent: * / Disallow: /wp-admin/ / Disallow:
  /wp-includes/ / Disallow: /wp-content/plugins/ / Disallow: /wp-content/uploads/wflogs/ /
  Disallow: /wp-json/ / Disallow: /wp/ / Disallow: /login/ / Disallow: /wp-login.php / Disallow:
  /xmlrpc.php / Disallow: /?s= / Disallow: /search/ / Allow: /“. Die im Spike genutzte Route
  liegt unter `/wp-json/`.

## 4. Verwendungen im Projekt

| Verwendung | Yahoo Finance (`yfinance`) | Google News RSS | EQS News | Bewertung |
|---|---|---|---|---|
| Abruf | `scripts/fetch_market_data.py` einmal je Ticker (17 Ticker, Kurse, Kennzahlen, Empfehlungen, Erfolgszahlen); zur Laufzeit ein Live-Abruf nur ohne Zwischenspeicher, abschaltbar mit `MARKET_LIVE_FETCH=0` | `news_service.fetch_rss`: eine Anfrage je Unternehmen, frühestens alle 12 Stunden; `fetch_market_data.py --news`; im Spike zusätzlich Monatsabfragen mit `after:`/`before:` | nur im Spike vom 2026-10-02 (Routenliste, Tageslisten zur UUID-Suche, Abfragen je Emittent und Monat) | mit dem Betreuer klären |
| Lokaler Zwischenspeicher | `backend/data/market/<ticker>.json` (17 Dateien: Monatsschlusskurse ab Beginn der Reihe, Kennzahlen, Empfehlungen, Erfolgszahlen); in `.gitignore` | `backend/data/market/news/<company_id>.json` (Titel, Quelle, Link, Datum, höchstens 30 je Unternehmen); in `.gitignore` | kein Zwischenspeicher; die Spike-Ergebnisse stehen in `backend/data/spike_news_sources.json` | mit dem Betreuer klären |
| Anzeige im Dashboard während der Interviews | Kurslinie, Marktkapitalisierung, Mitarbeitende, Umsatz auf `/aktie` und auf Wunsch auf `/anomalies`; mit Zusatzkarten auch Empfehlungen, Umsatz und Nettoergebnis; Quelle und Abrufdatum werden genannt | Karte „Aktuelle Meldungen“ (Titel, Quelle, Datum, Link) nur mit Zusatzkarten (`VITE_SHOW_FINANCE_EXTRAS`) | keine Anzeige | mit dem Betreuer klären |
| Abbildungen in der Arbeit | Bildschirmfotos der Kursansichten enthielten Kursverlauf und Kennzahlen (Werte Dritter) | Bildschirmfotos der Meldungskarte enthielten Schlagzeilen und Quellennamen; `docs/quellen-spike.md` nennt Trefferzahlen und einzelne Ereignisse | `docs/quellen-spike.md` nennt Trefferzahlen, Kategorien und zwei companyUUIDs | mit dem Betreuer klären |
| Öffentliches Repository | Code, Tests mit nachgebildeten Daten; keine Kursdaten eingecheckt | Code, Dokumentation; `backend/data/spike_news_sources.json` enthält je Lauf und Quelle Anfrage-URLs und bis zu drei Beispieltitel | Spike-Skript, `spike_news_sources.json` (Beispieltitel, Anfrage-URLs, UUIDs), `docs/quellen-spike.md` | mit dem Betreuer klären |
| Gehostete Demo | Die Konfiguration sieht ein gehostetes Frontend vor (CORS-Eintrag `epa-bachelorprojekt.vercel.app` in `backend/main.py`, Backend-Dockerfile für Hugging Face Spaces); dort würden die Daten an beliebige Besucher ausgeliefert. Ob eine Instanz läuft, wurde nicht geprüft | wie Yahoo | nicht betroffen | mit dem Betreuer klären |

## 5. Fragen an den Betreuer

1. Yahoo Finance: Dürfen Abbildungen der Arbeit Kursverläufe und Kennzahlen aus Yahoo Finance
   zeigen, und wie ist die Quelle anzugeben (Yahoo Finance; laut Hilfeseite ICE Data Services,
   Morningstar, S&P Global Market Intelligence)?
2. Yahoo Finance: Ist der Abruf über `yfinance` (ohne Registrierung, `robots.txt` von
   `query2.finance.yahoo.com` sperrt alle Pfade, AGB untersagen automatisierte Erfassung ohne
   Genehmigung) für die Arbeit vertretbar, oder soll der Kurs aus einer anderen Quelle bezogen
   werden (z. B. Daten der Deutschen Börse oder Investor-Relations-Seiten der Unternehmen)?
3. Yahoo Finance: Darf die lokale Evaluationsinstanz die Daten in den Interviews zeigen? Darf
   eine gehostete Demo sie zeigen (Weitergabe an Dritte, „must not redistribute“)?
4. Google News RSS: Der Feed ist laut eigenem Vermerk nur für persönliche, nicht-kommerzielle
   Feed-Reader bestimmt, und `robots.txt` führt `/rss/` nicht unter den erlaubten Pfaden. Ist
   der Abruf im Backend (Zwischenspeicher, Anzeige in den Interviews) vertretbar? Alternative:
   Meldungen manuell recherchieren und nur als Ereignisanker mit Datum und Link in den
   Annotationen (Protokoll-Regel 7) nennen.
5. Google News RSS: Dürfen Schlagzeilen mit Quellennamen in Abbildungen der Arbeit und in
   `backend/data/spike_news_sources.json` im öffentlichen Repository stehen, oder sind sie zu
   entfernen oder zu paraphrasieren?
6. EQS News: Die REST-Route ist undokumentiert und per `robots.txt` gesperrt; das Impressum
   beschränkt die Inhalte auf persönliche Nutzung und untersagt Kopieren und Weitergabe. Soll
   EQS als sekundäre Quelle (E7, Inkrement 5) weiterverfolgt werden, oder genügt die manuelle
   Nutzung der öffentlichen Webseite als Ereignisanker mit Datum und Link?
7. EQS News: Sind die „EQS Group Terms“ (PDF) für das Lesen von eqs-news.com maßgeblich? Falls
   ja, müssen sie noch ausgewertet werden.
8. Allgemein: Soll die Arbeit einen Abschnitt zu den Nutzungsbedingungen der Datenquellen mit
   Fundstellen und Abrufdatum enthalten? Soll die gehostete Demo vor der Abgabe ohne Marktdaten
   betrieben oder abgeschaltet werden (`MARKET_LIVE_FETCH=0` ohne Zwischenspeicher, Zusatzkarten
   aus)?
