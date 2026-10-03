# Entscheidungen Zyklus 2 – Inkrement 0 „Fundament“

Stand: 2026-10-02. Jede Entscheidung nennt Kontext, Entscheidung, Begründung und Status.
Status „vorläufig“ heißt: gilt, bis die manuellen Annotationen (DZ1) eine belastbare
Kalibrierung erlauben; dann wird der Eintrag mit Beleg aktualisiert.

## E1 – Kanonisches Repository

- **Kontext:** Neben diesem Repository existierte eine testweise angelegte Kopie
  (`Vaios-Pechlevanidis/Bachelorarbeit`), die in dieselbe gehostete Supabase-Datenbank
  geschrieben hatte (Tabellen `anomalies`, `context_items`, `stock_prices`, `explanations`,
  `financial_kpis`, `analyst_recommendations`, Spalten `companies.ticker/isin`).
- **Entscheidung:** `EPA-Bachelorarbeit` ist das einzige Repository der Arbeit. Zyklus 2 wird
  hier vollständig neu aufgebaut. Die fremden Datenbankobjekte wurden am 2026-10-02 per
  SQL-Editor entfernt; die Datenbank entspricht wieder genau den Migrationen 001–005.
- **Status:** endgültig.

## E2 – Datenbasis und Untersuchungsunternehmen

- **Kontext:** Die Datenbank enthält 26 reale Kununu-Profile (13 aus Zyklus 1, 13 TecDAX-
  Unternehmen, importiert am 2026-10-02) sowie die synthetischen Firmen Demo 1–3.
- **Entscheidung:** Alle 26 realen Unternehmen sind Untersuchungsunternehmen. Demo 1–3
  dienen nur der Entwicklung und gehen in keine Auswertung ein. Beide Quellen, `employee`
  und `candidates`, gehen in die Erkennung ein.
- **Begründung:** Breite Fallbasis für die Experteninterviews (DZ3); die Kandidatenquelle ist
  bei mehreren Unternehmen dünn, liefert aber bei Thyssengas, Carl Zeiss und Thyssenkrupp
  eine zweite Perspektive. Die Dichte je Unternehmen ist in `docs/datenbasis.md` belegt.
- **Status:** endgültig (Autor, 2026-10-02).

## E3 – Erkennungsreihe für die Gesamtbewertung

- **Kontext:** Das Backend kennt zwei Aggregationen: `get_company_timeline`
  (`backend/routes/analytics.py`) mittelt die Spalte `durchschnittsbewertung` je Bewertung
  und Monat; `_compute_avg_overall` (`backend/routes/companies.py`) mittelt die 13
  Kategorienmittelwerte über alle Bewertungen.
- **Entscheidung:** Die Erkennung arbeitet je Unternehmen, Quelle und Kalendermonat auf dem
  arithmetischen Mittel der Spalte `durchschnittsbewertung` aller Bewertungen dieses Monats
  (die Spalte stammt aus dem Kununu-Export und entspricht der dort je Bewertung angezeigten
  Gesamtnote). Einzeldimensionen werden analog aus den jeweiligen `sternebewertung_*`-Spalten
  gemittelt. Bewertungen ohne `datum` werden ignoriert.
- **Begründung:** Diese Reihe ist identisch mit der Zeitleiste im Dashboard, also mit dem,
  was die Nutzer sehen; das Kategorienmittel weicht davon ab, weil Bewertungen mit
  unvollständigen Kategorien anders gewichtet werden, und ist für Kandidaten nicht
  definiert.
- **Status:** endgültig für Inkrement 1; die Serien-CSVs unter `backend/data/series/`
  verwenden genau diese Definition.

## E4 – Mindestdichte je Monat

- **Kontext:** Viele Monate enthalten nur einzelne Bewertungen; ein Monatsmittel aus einer
  oder zwei Bewertungen ist Rauschen.
- **Entscheidung:** Monate mit weniger als 5 Bewertungen werden in der Erkennungsreihe
  nicht bewertet (sie bleiben als Lücke sichtbar). Unternehmen mit weniger als 12 solchen
  Monaten in der Mitarbeiterquelle werden nicht in die automatische Erkennung aufgenommen,
  sondern nur als Fallstudie ohne Zeitreihenanalyse geführt; die Liste steht in
  `docs/datenbasis.md`, Abschnitt „Konsequenzen“. Stand 2026-10-02 erfüllen in der
  Mitarbeiterquelle 15 von 26 Unternehmen das Kriterium, in der Kandidatenquelle 5 von 26.
- **Begründung:** Der Schwellwert 5 entspricht dem Kriterium der Prüfliste für Inkrement 0
  („Monate mit weniger als 5 Bewertungen“). 12 Monate sind das Minimum, damit ein
  Referenzfenster vor und nach einer Veränderung existiert.
- **Status:** vorläufig; nach Vorliegen der Annotationen gegen DZ1 zu prüfen.

## E5 – Referenzzeiträume (Annotationen)

- **Kontext:** DZ1 verlangt den Abgleich der automatisch erkannten Veränderungen mit
  manuell annotierten auffälligen Zeiträumen.
- **Entscheidung:** Die Annotationen stehen in `backend/data/annotations.json` (Schema:
  `company`, `source`, `dimension`, `period_from`, `period_to`, `direction`, `note`). Sie werden
  vom Autor anhand der Serien-CSVs unter `backend/data/series/` eingetragen, bevor
  Erkennungscode entsteht, und mit `backend/scripts/validate_annotations.py` geprüft. Die
  Datei wird in einem eigenen Commit vor dem ersten Erkennungscode versioniert.
- **Begründung:** Eine aus der Erkennung abgeleitete oder nachträglich erzeugte Referenz
  wäre zirkulär und würde den F1-Wert entwerten; die Git-Historie belegt die Reihenfolge.
- **Status:** Vorlage und Validierung vorhanden; Einträge offen (Handarbeit des Autors).

## E6 – Unternehmens-Metadaten

- **Kontext:** Für die Kontextsammlung (Kurse, Ad-hoc-Meldungen) braucht die Erklärung
  Ticker und ISIN; 8 der 26 Unternehmen sind nicht börsennotiert.
- **Entscheidung:** Migration `006_add_company_metadata.sql` ergänzt `companies` um
  `ticker` (Yahoo-Finance-Notation), `isin`, `sector` (Branche) und `peer_group` mit den
  Werten „Börsennotiert DE“, „Börsennotiert Ausland“, „Nicht börsennotiert“, „Demo“. Die
  Werte stehen versioniert in `backend/data/company_metadata.json` und werden mit
  `backend/scripts/seed_company_metadata.py --apply` eingespielt. Nicht börsennotierte
  Unternehmen erhalten keine Finanzmarktquellen; für sie gilt die namensbasierte
  Nachrichtensuche aus E7.
- **Sonderfälle (vorläufig, vom Autor zu bestätigen):** Compugroup Medical wurde 2025 von
  der Börse genommen; yfinance liefert für keinen COP-Ticker Kurse, daher vorerst
  „Nicht börsennotiert“ ohne Ticker, obwohl das Unternehmen im Untersuchungszeitraum
  notiert war. NTT DATA SE ist eine Tochter von NTT DATA Group (9613.T, 2025 von NTT
  übernommen, keine Kursdaten mehr); hinterlegt ist der notierte Mutterkonzern NTT, Inc.
  (9432.T) als „Börsennotiert Ausland“. ISINs konnten über yfinance nicht verifiziert
  werden und bleiben leer, bis sie aus einer belegbaren Quelle nachgetragen sind.
- **Status:** Migration und Daten vorhanden; Einspielen nach Ausführung der Migration.

## E7 – Nachrichtenquelle für historische Meldungen

- **Kontext:** `yfinance.Ticker.get_news` hat keinen Datumsparameter und liefert nur die
  jüngsten Meldungen; Anomalien liegen überwiegend Jahre zurück.
- **Entscheidung (vorläufig, Spike vom 2026-10-02, `docs/quellen-spike.md`):**
  Google-News-RSS ist die primäre Quelle für alle Unternehmen (Monatsfenster, bei 0 Treffern
  ±1 Monat); EQS-News-REST ist sekundäre Quelle für börsennotierte Unternehmen (Ad-hoc,
  Stimmrechte, Finanzberichte; undokumentierte Schnittstelle, companyUUID je Unternehmen
  einmalig ermittelt); GDELT bleibt optional hinter einem Flag (Rate-Limit 429, Cap
  75 Treffer); yfinance wird für Nachrichten nicht genutzt.
- **Begründung:** Im Spike lieferte Google-News-RSS für Thyssenkrupp 04/2023 28 datierte
  deutsche Treffer inklusive des Vorstandswechsels, für Bechtle 10/2020 6, für das nicht
  notierte KIT 8; EQS lieferte 5 bzw. 1 Meldung nur für die notierten Fälle; yfinance 0 im
  Fenster. Für Open Grid Europe fand keine Quelle Treffer im Einzelmonat, erst im
  3-Monats-Fenster.
- **Offen:** Nutzungsbedingungen von Google News RSS und EQS für die Arbeit, Umgang mit
  englischsprachigen Treffern, Fenstergröße 1 oder 3 Monate.
- **Status:** vorläufig.

## E8 – Reproduzierbarkeit des Docker-Stacks

- **Kontext:** `backend/Dockerfile` kopierte mit `COPY . .` auch `backend/.env` ins Image.
  Weil `database/supabase_client.py` den Service-Key der Datei vor dem Anon-Key aus
  `docker-compose.yml` bevorzugt, sprach der Container gegen das lokale PostgREST mit dem
  Schlüssel des gehosteten Projekts (Fehler PGRST301), und der Schlüssel lag im Image.
- **Entscheidung:** `backend/.dockerignore` schließt `.env`, `.venv`, Caches und trainierte
  Modelle aus. Die Abhängigkeiten `ruptures` und `yfinance` stehen in `pyproject.toml`,
  `uv.lock`, `requirements.txt` und beiden Dockerfiles.
- **Status:** endgültig; Image nach der Änderung neu bauen.
