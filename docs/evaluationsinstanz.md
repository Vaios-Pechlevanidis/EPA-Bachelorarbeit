# Evaluationsinstanz für die Interviews (DZ3) – Varianten, Einstellungen, Prüfliste

Stand: 2026-10-09. Die Evaluationsinstanz ist die Ausgabe des Dashboards, die in den
Experteninterviews (DZ3) gezeigt wird: Backend und Frontend aus diesem Repository auf dem
Rechner des Autors gegen die gehostete Datenbank (nur lesend). Dieses Dokument legt die beiden
Varianten mit ihren Folgen vor, nennt die nötigen Einstellungen und enthält eine Prüfliste für
den Tag vor einem Interview. Beispielwerte stehen in `docs/evaluationsinstanz.env.example`
(ohne Zugangsdaten).

> **Entscheidung des Autors (2026-10-08, D3): Variante B.** Die Evaluationsinstanz wird mit
> `VITE_SHOW_FINANCE_EXTRAS=false` gebaut; die Zusatzkarten des Aktien-Dashboards sind in den
> Interviews nicht sichtbar (E16). Variante A bleibt als Standardbau außerhalb der Evaluation
> beschrieben.
>
> **Entscheidung des Autors (2026-10-09, D2): ohne Prognose.** Die Evaluationsinstanz wird
> zusätzlich mit `VITE_SHOW_FORECAST=false` gebaut. Der Zeitverlauf ruft dann
> `forecast_months=0` ab und zeigt weder Prognoselinie noch Trennlinie, Legendeneintrag oder
> „Ø Prognose“; die x-Achse endet am letzten Monat mit Daten; der PDF-Export folgt demselben
> Schalter (E28). Ohne Angabe bleibt die Prognose aus Zyklus 1 sichtbar.

## 1. Die beiden Varianten (Entscheidung D3)

| | Variante A: mit Zusatzkarten (Standard) | Variante B: ohne Zusatzkarten |
|---|---|---|
| Einstellung | Frontend ohne Angabe oder `VITE_SHOW_FINANCE_EXTRAS=true` gebaut | Frontend mit `VITE_SHOW_FINANCE_EXTRAS=false` gebaut (`frontend/src/config.js`, E16) |
| Seite `/aktie` | sechs Kacheln (Kurs, Marktkapitalisierung, Mitarbeitende, Umsatz, Nettoergebnis, Analysten) und vier Karten: Kurs (mit und ohne Bewertungsverlauf), Aktuelle Meldungen, Analystenempfehlungen, Umsatz und Nettoergebnis | vier Kacheln (Kurs, Marktkapitalisierung, Mitarbeitende, Umsatz) und die Kurskarte über die ganze Fläche |
| Abrufe des Frontends | `GET …/finance` und `GET …/news` | nur `GET …/market`; `/finance` und `/news` werden nicht aufgerufen |
| Externe Quellen, die während des Interviews sichtbar sind | Yahoo Finance (Kurs, Kennzahlen, Empfehlungen, Erfolgszahlen) und Google News RSS (Schlagzeilen der letzten 90 Tage) | Yahoo Finance (Kurs, Kennzahlen) |
| Bezug zu den Anforderungen | zeigt neben FA-15 auch Elemente ohne Anforderung aus den Interviews (Wunsch des Autors, E16 „Rolle in der Arbeit“) | zeigt genau den Teil, der FA-15 deckt |
| Folgen für die Interviews | Die Befragten sehen mehr Marktinformationen und können sie kommentieren; Rückfragen zu Empfehlungen („Anlageempfehlung?“) und zu fremden Nachrichtentreffern (z. B. Sportverein bei „Carl Zeiss“) sind wahrscheinlich; die Meldungskarte braucht Netz oder einen frischen Zwischenspeicher (12 Stunden); mehr mögliche Fehlerquellen im Gespräch | Die Seite ist auf Kurs und Kennzahlen reduziert; weniger Erklärungsbedarf; keine Abrufe bei Google News während des Interviews; das Gespräch bleibt bei den Anforderungen |
| Folgen für die Arbeit | Das gezeigte Artefakt enthält Zusätze, die E16 ausdrücklich nicht zum evaluierten Artefakt zählt; der Interviewleitfaden müsste sie ausklammern oder die Auswertung sie trennen | deckungsgleich mit E16: evaluiert wird das Artefakt aus den Anforderungen; die Zusatzkarten bleiben außerhalb der Evaluation nutzbar |
| Nutzungsbedingungen | Google News RSS und Yahoo Finance werden vor Dritten gezeigt (`docs/nutzungsbedingungen.md`, Fragen 3 bis 5) | nur Yahoo Finance (Fragen 1 bis 3) |
| Tooltip „Aktie“ in der Seitenleiste | „Aktienkurs, Empfehlungen, Umsatz und Nachrichten“ | „Aktienkurs und Kennzahlen“ (seit 2026-10-08 nach dem Schalter, `frontend/src/pages/Dashboard.jsx`) |

In beiden Varianten gilt: Der Kurs auf der Anomalien-Seite ist Standard aus und nur per
Kästchen einblendbar (E15, Nachtrag 2026-10-05); Dashboard-Karte und PDF-Export bleiben ohne
Kurs; es gibt keine Korrelation und keine Aussage über einen Zusammenhang.

## 2. Einstellungen

### 2.1 Backend (Umgebung oder `backend/.env`)

| Variable | Bedeutung | Empfehlung für die Interviews |
|---|---|---|
| `SUPABASE_URL` | Adresse der gehosteten Datenbank | wie in der Entwicklung; der Wert bleibt in `backend/.env` (nicht im Repository) |
| `SUPABASE_SERVICE_KEY` oder `SUPABASE_KEY` | Zugangsschlüssel; der Service-Key hat Vorrang (`backend/database/supabase_client.py`) | für die Instanz genügt ein lesender Schlüssel; die Instanz schreibt nicht |
| `MARKET_LIVE_FETCH` | `0` unterbindet jeden Live-Abruf bei Yahoo Finance; dann gilt nur der Zwischenspeicher `backend/data/market/` (`backend/services/context_service.py`, E15) | `0` am Interviewtag: keine Abrufe bei Yahoo während des Gesprächs, keine Wartezeit, kein Fehlschlag wegen Netz; Voraussetzung ist ein vorher gefüllter Zwischenspeicher (Prüfliste) |
| `CONTEXT_LIVE_FETCH` | `0` unterbindet jeden Abruf externer Belege (Google News RSS, EQS); dann gilt nur der Belegspeicher `backend/data/context/` (`backend/services/evidence_service.py`, Inkrement 4, E18) | `0` am Interviewtag: keine Abrufe bei Google News oder EQS während des Gesprächs (ein nicht gespeichertes Fenster braucht sonst beim ersten Abruf rund 10 s, die Ansicht zeigt dann einen Hinweis); Voraussetzung ist der Vorabruf mit `scripts/fetch_context.py --comparison` und `--from-month` (Prüfliste, Punkt 4a) |
| `CONTEXT_GDELT` | `1` schaltet GDELT als dritte Belegquelle ein (Standard aus) | aus lassen |
| Port | `uvicorn main:app --port 8000` (`.claude/launch.json`, README) | 8000; die Browser-Freigabe (CORS in `backend/main.py`) erlaubt nur `localhost:3000` und `localhost:5173` als Frontend-Adresse |

Fehlt der Zwischenspeicher bei `MARKET_LIVE_FETCH=0`, antwortet `/market` mit
`available: false` und einer Begründung (kein Serverfehler); die Ansicht zeigt dann „Kein
Aktienkurs“ mit dem Grund.

### 2.2 Frontend (beim Bauen oder Start des Entwicklungsservers gelesen)

| Variable | Bedeutung | Empfehlung |
|---|---|---|
| `VITE_API_URL` | Adresse des Backends, `/api` wird angehängt (`frontend/src/config.js`) | `http://localhost:8000` |
| `VITE_SHOW_FINANCE_EXTRAS` | `false` oder `0` blendet die Zusatzkarten aus (Variante B); jeder andere Wert oder keine Angabe: Variante A | `false` (Variante B, Entscheidung D3 vom 2026-10-08) |
| `VITE_SHOW_FORECAST` | `false` oder `0` blendet die Prognose im Zeitverlauf und im PDF aus (`frontend/src/config.js`, E28); jeder andere Wert oder keine Angabe: mit Prognose | `false` (Entscheidung D2 vom 2026-10-09) |

Bauen und starten (Beispiele):

```bash
# Evaluationsinstanz als Produktionsbau, danach mit npm run preview oder einem statischen Server auf Port 3000 ausliefern
# (VITE_API_URL ausdrücklich setzen: frontend/.env.production zeigt auf einen entfernten Server)
cd frontend && VITE_API_URL=http://localhost:8000 VITE_SHOW_FINANCE_EXTRAS=false VITE_SHOW_FORECAST=false npm run build

# dasselbe mit dem Entwicklungsserver (Port 5173 ist in der CORS-Liste)
cd frontend && VITE_SHOW_FINANCE_EXTRAS=false VITE_SHOW_FORECAST=false npm run dev -- --port 5173

# Docker (beide Dienste)
docker compose build --build-arg VITE_SHOW_FINANCE_EXTRAS=false --build-arg VITE_SHOW_FORECAST=false frontend

# Abnahme der Umgebung und der Speicher (nur lesend, Exit-Code ungleich 0 bei Lücken)
cd backend && uv run python scripts/check_evaluation_instance.py
```

### 2.3 Stimmungsmodus (Vorher-Nachher-Vergleich, E11)

Es gibt **keinen Schalter**. Der Vergleich erzeugt beim ersten Aufruf je Prozess einen
`SentimentAnalyzer` im Modus `transformer` (`backend/services/explanation_service.py`); dieser
lädt das Modell „oliverguhr/german-sentiment-bert“ (Rückfall: ein mehrsprachiges
Cardiff-NLP-Modell) über die Bibliothek `transformers`. Schlägt das Laden fehl (kein Netz beim
ersten Laden, kein Modell im Cache), arbeitet der Vergleich **stillschweigend im Lexikon-Modus**;
die Antwort nennt den tatsächlich verwendeten Modus im Feld `sentiment_mode` (`transformer`
oder `lexicon`), die Ansicht zeigt ihn im Hinweistext unter dem Vergleich. Folgen:

- Das Modell liegt im Hugging-Face-Cache des Rechners (im Docker-Image unter
  `TRANSFORMERS_CACHE=/tmp/hf_cache`, lokal im Standardordner der Bibliothek). Einmal geladen,
  braucht ein späterer Start kein Netz mehr; ob das klappt, zeigt nur ein Probelauf.
- Die erste Anfrage je Prozess dauert mehrere Sekunden (Laden 3,6–4,0 s, Vergleich 1,6–8,4 s je
  nach Textmenge; Feature-Doku 02, Abschnitt 5). Danach greift der Zwischenspeicher je
  Bewertung (0,2–0,5 s). Vor dem Interview daher einmal aufwärmen (Prüfliste).
- Soll das Backend am Interviewtag garantiert keine Verbindung zu Hugging Face aufbauen, kann
  die Umgebungsvariable `HF_HUB_OFFLINE=1` der Bibliothek gesetzt werden (keine Variable dieses
  Projekts); das Modell muss dann vorher im Cache liegen, sonst gilt der Lexikon-Modus.
- Im Interviewprotokoll den Modus festhalten; die Arbeit nennt ihn als Bedingung der Evaluation.

### 2.4 Weitere Festlegungen vor dem Interview (keine Variablen)

- **Demo-Unternehmen:** Demo 1–3 stehen in der Firmenliste der gehosteten Datenbank. Sie
  gehen in keine Auswertung ein (E2); für die Interviews ist festzulegen, dass sie nicht
  ausgewählt werden (eine Ausblendung ist nicht vorgesehen).
- **Bildschirm:** Der Aufbau wurde bei 1440 × 900 Pixeln geprüft (Feature-Doku 05); ab 1280 px
  Breite füllt das Aktien-Dashboard die Fensterhöhe. Zoom 100 %, helles oder dunkles Schema
  vorab wählen.
- **Zeitraum der Daten:** Die Bewertungen reichen je nach Unternehmen bis 2025-07 (TecDAX) bzw.
  2026-07 (Zyklus 1); der Zwischenspeicher der Kurse trägt sein Abrufdatum (`fetched_at`), das
  die Ansicht nennt.

## 3. Prüfliste für den Tag vor einem Interview

Jeden Punkt abhaken und die Ergebnisse (Commit, Werte, Zeiten) im Interviewprotokoll notieren.

1. **Stand einfrieren:** `git status` ohne offene Änderungen; Commit-Hash des gezeigten Stands
   notieren (`git rev-parse --short HEAD`). Kein Branch-Wechsel mehr bis nach dem Interview.
2. **Backend-Tests:** `cd backend && uv run python -m pytest -q` grün.
3. **Umgebung Backend:** `backend/.env` vorhanden (Variablen aus 2.1); `MARKET_LIVE_FETCH=0`
   für den Prozess gesetzt, der im Interview läuft.
4. **Kurs-Zwischenspeicher füllen und prüfen** (einziger Zeitpunkt mit Abruf bei Yahoo; Fragen
   in `docs/nutzungsbedingungen.md` beachten):
   `cd backend && uv run python scripts/fetch_market_data.py` und danach
   `uv run python scripts/fetch_market_data.py --summary` mit Exit-Code 0 (alle 17 Ticker mit
   Kursreihe); `fetched_at` notieren.
4a. **Belegspeicher füllen** (Inkrement 4): `cd backend && uv run python scripts/fetch_context.py --comparison`
   holt die Meldungen für alle Fenster der Niveauwechsel und Einzelmonate der geeigneten
   Unternehmen und für die Vergleichsfenster (gedrosselt, fortsetzbar; `--dry-run` zählt nur).
   Für die Unternehmen, die im Interview frei durchsucht werden sollen, zusätzlich alle Monate
   laden, damit jede Dimension und jede freie Auswahl sofort antwortet:
   `uv run python scripts/fetch_context.py --from-month 2019-01 --company <id> …` (Stand
   2026-10-08 für die acht Unternehmen mit Markierungen ab 2019 geladen; rund 2 s je Abruf,
   die Quellen `--source gnews` und `--source eqs` lassen sich in zwei Prozessen nebeneinander
   laufen). Bricht eine Quelle nach wiederholten Fehlern ab (Status 429 oder 503), nennt die
   Zusammenfassung Unternehmen und Monat; nach einer Pause denselben Aufruf wiederholen, geladene
   Monate werden übersprungen. Danach `CONTEXT_LIVE_FETCH=0` für den Interviewprozess setzen,
   damit im Gespräch keine Abrufe laufen; für Zeiträume, die nicht im Speicher liegen, gibt es
   dann keine Belege, die Ansicht nennt den Grund.
4b. **Erklärungsansätze** (Inkrement 5): Sie entstehen aus demselben Belegspeicher und den
   Bewertungen; ein eigener Vorabruf ist nicht nötig. Mit `CONTEXT_LIVE_FETCH=0` zeigt der
   Abschnitt „Mögliche Zusammenhänge“ für Zeiträume ohne gespeicherte Monate den Zustand „offen“
   mit dem Grund. Der erste Aufruf eines Vergleichs braucht wegen der Stimmungsanalyse der
   Bewertungen einige Sekunden (SAP SE: rund 12 s, danach unter 1 s); die Markierungen, die im
   Interview gezeigt werden sollen, am Tag vorher einmal anklicken, damit der Zwischenspeicher
   des Prozesses gefüllt ist (gilt je Prozess, also nach jedem Neustart erneut).
5. **Entfällt bei Variante B** (nur Variante A: Meldungen füllen mit
   `uv run python scripts/fetch_market_data.py --news`).
6. **Frontend bauen** mit `VITE_SHOW_FINANCE_EXTRAS=false` (Variante B, Abschnitt 2.2) und
   `VITE_SHOW_FORECAST=false` (D2) und starten; im Browser prüfen: der Zeitverlauf zeigt keine
   Prognose; `/aktie` zeigt vier Kacheln und die Kurskarte über die ganze
   Fläche, der Link unter dem Diagramm der Anomalien-Seite lautet „Aktienkurs und Kennzahlen“,
   der Tooltip „Aktie“ in der Seitenleiste ebenso.
7. **Backend starten** und Antworten prüfen: `GET /api/analytics/company/19/market` liefert
   `available: true` aus dem Zwischenspeicher; ein Unternehmen ohne Ticker (z. B. id 4) liefert
   `available: false` mit Grund; keine Live-Abrufe im Backend-Log.
8. **Stimmung aufwärmen:** Auf der Anomalien-Seite eine Veränderung mit Vergleich öffnen (z. B.
   Freenet, Abfall ab 2021-09); in der Antwort von `/explanations` bzw. `/compare` steht
   `sentiment_mode: "transformer"`. Steht dort `lexicon`, hat das Modell nicht geladen: Netz
   prüfen, Backend neu starten, erneut aufwärmen; bleibt es beim Lexikon, den Modus im
   Protokoll vermerken.
9. **Durchlauf der Interviewfälle:** Für jedes vorgesehene Unternehmen Dashboard, Anomalien-Seite
   (Quelle, Status, Dimension, Drill-down, Vergleich, Bewertungen) und Aktien-Dashboard öffnen;
   Ladezeiten und Browser-Konsole ohne Fehler; Demo-Unternehmen nicht verwenden.
10. **Browser vorbereiten:** Fenstergröße 1440 × 900 oder größer, Zoom 100 %, Farbschema,
    Lesezeichen für die Startseiten, andere Tabs schließen; `/docs` des Backends und `.env`
    nicht auf dem Bildschirm.
11. **Netz:** Mit gefülltem Zwischenspeicher und `MARKET_LIVE_FETCH=0` braucht das Backend für
    Kurs und Kennzahlen kein Netz; die Datenbank (Supabase) und, in Variante A, Google News
    brauchen es. Verbindung am Interviewort vorab prüfen oder Variante B wählen.
12. **Protokoll:** Commit-Hash, `VITE_SHOW_FINANCE_EXTRAS`, `VITE_SHOW_FORECAST`, `MARKET_LIVE_FETCH`, `CONTEXT_LIVE_FETCH`,
    `fetched_at` der Zwischenspeicher (Kurs und Belege, Zusammenfassung von `fetch_context.py`),
    `sentiment_mode` und das Datum des Durchlaufs festhalten.

## 4. Beispieldatei

`docs/evaluationsinstanz.env.example` enthält die Variablen aus Abschnitt 2 mit Platzhaltern.
Sie wird nicht direkt eingelesen: Die Backend-Zeilen gehören nach `backend/.env` (Vorlage
`backend/.env.example`), die Frontend-Zeilen werden beim Bauen in der Shell gesetzt oder nach
`frontend/.env.local` übernommen. Zugangsdaten stehen nie im Repository (`.gitignore`).
