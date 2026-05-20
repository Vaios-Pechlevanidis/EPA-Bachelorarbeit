# Installationsanleitung — Gruppe P1-3

Hinweis zur KI-Unterstützung

Teile dieser Datei wurden mit Hilfe von KI-gestützten Entwicklungswerkzeugen erstellt:
- GitHub Copilot
- Claude Sonnet 4.6

Die generierten Inhalte wurden anschließend vom Autor geprüft,
überarbeitet und in das Projekt integriert.

Quelle der KI-Ausgabe:
Anthropic (2026)

Autor: Vaios Pechlevanidis
Datum: 01.03.2026

Anthropic (2026): Claude Sonnet 4.6 – Large Language Model.
https://www.anthropic.com. Abgerufen am 01.03.2026.

GitHub (2026): GitHub Copilot – AI Pair Programmer.
https://github.com/features/copilot. Abgerufen am 01.03.2026.

Diese Anleitung beschreibt Schritt für Schritt, wie du das Projekt lokal einrichtest und startest.

---

## Inhaltsverzeichnis

0. [Von 0 auf 100 — Schnellstart](#0-von-0-auf-100--schnellstart)
1. [Voraussetzungen](#1-voraussetzungen)
2. [Repository klonen](#2-repository-klonen)
3. [Backend einrichten](#3-backend-einrichten)
4. [Frontend einrichten](#4-frontend-einrichten)
5. [Umgebungsvariablen konfigurieren](#5-umgebungsvariablen-konfigurieren)
6. [Projekt starten](#6-projekt-starten)
7. [Installation verifizieren](#7-installation-verifizieren)
8. [LDA-Modelle trainieren & verwalten](#8-lda-modelle-trainieren--verwalten)
9. [Häufige Probleme & Lösungen](#9-häufige-probleme--lösungen)

---

## 0. Von 0 auf 100 — Schnellstart

Alle Befehle der Reihe nach ausführen. Am Ende läuft das Projekt vollständig lokal.

> **Voraussetzung:** Git und Node.js (20+) müssen bereits installiert sein.
> Python wird über `uv` verwaltet, muss also **nicht** separat installiert werden.

### Schritt 1 — uv installieren

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.zshrc   # oder ~/.bashrc

# Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Schritt 2 — Repository klonen

```bash
git clone https://github.com/IIS-Bachelorprojekt/gruppe-P1-3.git gruppe-P1-3
cd gruppe-P1-3
```

### Schritt 3 — Backend-Dependencies installieren

```bash
cd backend
uv sync
cd ..
```

### Schritt 4 — Umgebungsvariablen setzen

```bash
# macOS / Linux
touch backend/.env
echo "SUPABASE_URL=https://dein-projekt.supabase.co" >> backend/.env
echo "SUPABASE_KEY=dein-supabase-anon-key" >> backend/.env

# Windows (PowerShell)
New-Item backend/.env
Add-Content backend/.env "SUPABASE_URL=https://dein-projekt.supabase.co"
Add-Content backend/.env "SUPABASE_KEY=dein-supabase-anon-key"
```

> Ersetze die Platzhalter durch die echten Supabase-Zugangsdaten deines Teams (siehe [Schritt 5](#5-umgebungsvariablen-konfigurieren)).

### Schritt 5 — Frontend-Dependencies installieren

```bash
cd frontend
npm install
cd ..
```

### Schritt 6 — Backend starten (Terminal 1 offen lassen)

```bash
cd backend
uv run uvicorn main:app --reload
```

Backend läuft unter: **<http://localhost:8000>**

### Schritt 7 — Frontend starten (neues Terminal)

```bash
cd frontend
npm run dev
```

Frontend läuft unter: **<http://localhost:5173>**

### Schritt 8 — Erstes LDA-Modell trainieren (neues Terminal)

```bash
curl -X POST http://localhost:8000/api/topics/train \
  -H "Content-Type: application/json" \
  -d '{"source": "both", "num_topics": 5}'
```

> Ohne trainiertes Modell sind Topic-Analysen nicht verfügbar. Dieser Schritt dauert je nach Datenmenge 30–120 Sekunden.

### Fertig

| Dienst   | URL                          |
| -------- | ---------------------------- |
| Frontend | <http://localhost:5173>      |
| Backend  | <http://localhost:8000>      |
| Swagger  | <http://localhost:8000/docs> |

---

## 1. Voraussetzungen

Stelle sicher, dass folgende Software auf deinem System installiert ist:

| Software   | Mindestversion | Prüfbefehl          | Download                                                  |
| ---------- | -------------- | -------------------- | --------------------------------------------------------- |
| **Python** | 3.13+          | `python --version`   | https://www.python.org/downloads/                         |
| **Node.js**| 20+            | `node --version`     | https://nodejs.org/                                       |
| **npm**    | (mit Node.js)  | `npm --version`      | (kommt mit Node.js)                                       |
| **uv**     | (empfohlen)    | `uv --version`       | https://docs.astral.sh/uv/getting-started/installation/   |
| **Git**    | —              | `git --version`      | https://git-scm.com/                                      |

### uv installieren (empfohlen)

`uv` ist ein schneller Python-Paketmanager und wird für das Projekt empfohlen:

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

> **Hinweis:** Das Projekt funktioniert auch mit klassischem `pip`, `uv` ist aber deutlich schneller.

---

## 2. Repository klonen

```bash
git clone https://github.com/IIS-Bachelorprojekt/gruppe-P1-3.git gruppe-P1-3
cd gruppe-P1-3
```

---

## 3. Backend einrichten

### Option A: Mit `uv` (empfohlen)

```bash
cd backend
uv sync
```

Das erstellt automatisch eine `.venv` und installiert alle Dependencies aus `pyproject.toml`.

### Option B: Mit `pip`

```bash
cd backend
python -m venv .venv

# Virtuelle Umgebung aktivieren
source .venv/bin/activate        # macOS / Linux
# .venv\Scripts\activate         # Windows

pip install -r ../requirements.txt
```

### Python-Interpreter in VS Code setzen

1. Öffne die Command Palette: `Cmd+Shift+P` (Mac) / `Ctrl+Shift+P` (Windows/Linux)
2. Suche: **Python: Select Interpreter**
3. Wähle den Interpreter aus `backend/.venv/bin/python`

### Installierte Backend-Pakete

| Paket            | Zweck                                      |
| ---------------- | ------------------------------------------ |
| `fastapi`        | Web-Framework (REST API)                   |
| `uvicorn`        | ASGI-Server                                |
| `supabase`       | Datenbank-Client (PostgreSQL)              |
| `gensim`         | LDA Topic Modeling                         |
| `transformers`   | ML-basierte Sentiment-Analyse (German BERT)|
| `torch`          | PyTorch Backend für Transformers           |
| `pandas`         | Datenverarbeitung                          |
| `openpyxl`       | Excel-Import/-Export                       |
| `statsmodels`    | Statistische Auswertung                    |
| `python-dotenv`  | Umgebungsvariablen aus `.env`              |
| `python-multipart` | Datei-Upload-Support                     |

---

## 4. Frontend einrichten

```bash
cd frontend
npm install
```

Das installiert alle Dependencies aus `package.json`.

### Installierte Frontend-Pakete

| Paket                        | Zweck                        |
| ---------------------------- | ---------------------------- |
| `react` / `react-dom`       | UI-Framework                 |
| `react-router-dom`          | Client-Side Routing          |
| `recharts`                  | Chart-Bibliothek             |
| `tailwindcss`               | CSS-Framework                |
| `lucide-react`              | Icon-Bibliothek              |
| `@radix-ui/react-*`         | UI-Komponenten (shadcn/ui)   |
| `jspdf` / `html2canvas`     | PDF-Export                   |
| `vite`                      | Build Tool & Dev Server      |

---

## 5. Umgebungsvariablen konfigurieren

Erstelle eine `.env`-Datei im `backend/`-Ordner:

```bash
cp backend/.env.example backend/.env   # Falls .env.example vorhanden
# Oder manuell erstellen:
touch backend/.env
```

Füge folgende Variablen ein:

```env
# Supabase Configuration (PFLICHT)
SUPABASE_URL=https://dein-projekt.supabase.co
SUPABASE_KEY=dein-supabase-anon-key

# Optional: API Configuration
API_HOST=0.0.0.0
API_PORT=8000
```

> ⚠️ **Wichtig:**
> - Die `.env`-Datei ist in `.gitignore` und wird **nicht** ins Repository committed.
> - Frage dein Team nach den korrekten Supabase-Zugangsdaten.
> - Ohne gültige Supabase-Credentials startet das Backend mit einer Warnung.

### Supabase-Zugangsdaten finden

1. Gehe zu [supabase.com](https://supabase.com) und logge dich ein
2. Wähle dein Projekt aus
3. Gehe zu **Settings → API**
4. Kopiere die **Project URL** → `SUPABASE_URL`
5. Kopiere den **anon/public Key** → `SUPABASE_KEY`

---

## 6. Projekt starten

Du brauchst **zwei Terminal-Fenster**, eins für das Backend und eins für das Frontend.

### Terminal 1 — Backend starten

```bash
cd backend

# Mit uv (empfohlen)
uv run uvicorn main:app --reload

# Oder mit aktivierter venv
source .venv/bin/activate
python -m uvicorn main:app --reload
```

Das Backend läuft unter: **http://localhost:8000**
API-Dokumentation (Swagger): **http://localhost:8000/docs**

### Terminal 2 — Frontend starten

```bash
cd frontend
npm run dev
```

Das Frontend läuft unter: **http://localhost:5173**

---

## 7. Installation verifizieren

### Backend prüfen

```bash
# API erreichbar?
curl http://localhost:8000/api/hello
# Erwartete Antwort: {"message":"Hallo von FastAPI"}

# Datenbankverbindung testen
curl http://localhost:8000/api/test-connection
# Erwartete Antwort: {"status":"success", ...}

# Swagger UI öffnen
open http://localhost:8000/docs   # macOS
# xdg-open http://localhost:8000/docs   # Linux
```

### Frontend prüfen

Öffne **http://localhost:5173** im Browser. Die Welcome-Seite sollte angezeigt werden.

### Erstes LDA-Modell trainieren

```bash
curl -X POST http://localhost:8000/api/topics/train \
  -H "Content-Type: application/json" \
  -d '{"source": "both", "num_topics": 5}'
```

### Tests ausführen

```bash
cd backend

# Alle Tests
uv run pytest tests/

# Nur Topic Modeling Tests
uv run pytest tests/topic_modeling/

# Nur Sentiment-Analyse Tests
uv run pytest tests/sentiment_analysis/

# Nur Statistische Tests
uv run pytest tests/statistical/
```

---

## 8. LDA-Modelle trainieren & verwalten

Das Projekt nutzt **LDA (Latent Dirichlet Allocation)** zur automatischen Themenextraktion aus Feedback-Texten. Ohne ein trainiertes Modell können keine Topic-Analysen durchgeführt werden.

> **Voraussetzung:** Das Backend muss laufen und die Supabase-Datenbank muss Daten enthalten.

### 8.1 Modell über die API trainieren (empfohlen)

Das Backend muss gestartet sein (`http://localhost:8000`).

#### Erstes Modell trainieren

```bash
# Kombiniertes Modell (Bewerber + Mitarbeiter), 5 Topics
curl -X POST http://localhost:8000/api/topics/train \
  -H "Content-Type: application/json" \
  -d '{"source": "both", "num_topics": 5}'
```

#### Trainings-Parameter

| Parameter              | Werte                                   | Standard | Beschreibung                                   |
| ---------------------- | --------------------------------------- | -------- | ---------------------------------------------- |
| `source`               | `"candidates"`, `"employee"`, `"both"`  | `"both"` | Datenquelle für das Training                   |
| `num_topics`           | 2–20                                    | `5`      | Anzahl der zu extrahierenden Topics            |
| `limit`                | Zahl oder `null`                        | `null`   | Max. Anzahl Datensätze pro Quelle              |
| `use_employee_weighting` | `true` / `false`                      | `true`   | Gewichtung nach Mitarbeitertyp anwenden        |

#### Beispiele

```bash
# Nur Mitarbeiter-Feedback, 10 Topics
curl -X POST http://localhost:8000/api/topics/train \
  -H "Content-Type: application/json" \
  -d '{"source": "employee", "num_topics": 10}'

# Nur Bewerber-Feedback, 8 Topics, max. 100 Datensätze
curl -X POST http://localhost:8000/api/topics/train \
  -H "Content-Type: application/json" \
  -d '{"source": "candidates", "num_topics": 8, "limit": 100}'

# 15 Topics ohne Mitarbeiter-Gewichtung
curl -X POST http://localhost:8000/api/topics/train \
  -H "Content-Type: application/json" \
  -d '{"source": "both", "num_topics": 15, "use_employee_weighting": false}'
```

Nach dem Training wird das Modell automatisch unter `backend/models/saved_models/` gespeichert.

### 8.2 Modell über das Trainings-Skript trainieren

Alternativ kann das Trainings-Skript direkt ausgeführt werden (trainiert ein kombiniertes Modell mit 15 Topics):

```bash
cd backend

# Mit uv
uv run python scripts/train_models.py

# Mit aktivierter venv
python scripts/train_models.py
```

Das Skript gibt Informationen über die geladenen Daten, Perplexity und Coherence Score aus.

### 8.3 Gespeicherte Modelle auflisten

```bash
curl http://localhost:8000/api/topics/models/list
```

Antwort:
```json
{
  "status": "success",
  "count": 4,
  "models": [
    "lda_model_20260214_233448",
    "lda_model_20260201_152130",
    "..."
  ]
}
```

### 8.4 Gespeichertes Modell laden

Beim Neustart des Backends muss ein zuvor trainiertes Modell geladen werden:

```bash
curl -X POST "http://localhost:8000/api/topics/models/load?model_name=lda_model_20260214_233448"
```

### 8.5 Modell-Status prüfen

```bash
curl http://localhost:8000/api/topics/status
```

Zeigt an, ob ein Modell geladen ist und wie viele Topics es enthält.

### 8.6 Modell testen

Nach dem Training kannst du das Modell direkt testen:

```bash
# Text analysieren (Topics + Sentiment)
curl -X POST http://localhost:8000/api/topics/predict-with-sentiment \
  -H "Content-Type: application/json" \
  -d '{"text": "Die Work-Life-Balance ist ausgezeichnet und das Gehalt fair!", "threshold": 0.1}'

# Topic-Rating-Korrelation abrufen
curl http://localhost:8000/api/topics/analyze/topic-rating-correlation

# Alle entdeckten Topics anzeigen
curl http://localhost:8000/api/topics/topics
```

### 8.7 Alte Modelle aufräumen

Jedes Training erzeugt mehrere Dateien (~6 Dateien pro Modell). Um Speicherplatz freizugeben:

```bash
cd backend/models/saved_models

# Alle Modelle auflisten
ls -la *.model

# ALLE alten Modelle löschen (Vorsicht!)
rm -f lda_model_*.*

# Nur ein bestimmtes Modell löschen
rm -f lda_model_20260201_143902.*
```

### 8.8 Swagger UI verwenden

Alle oben genannten API-Calls können auch bequem über die **Swagger UI** ausgeführt werden:

1. Öffne **http://localhost:8000/docs** im Browser
2. Navigiere zum Abschnitt **topics**
3. Klicke auf den gewünschten Endpunkt (z.B. `/api/topics/train`)
4. Klicke **Try it out**, passe die Parameter an und klicke **Execute**

---

## 9. Häufige Probleme & Lösungen

### ❌ `uv: command not found`

```bash
# uv installieren
curl -LsSf https://astral.sh/uv/install.sh | sh
# Danach Terminal neu starten oder:
source ~/.bashrc   # oder ~/.zshrc
```

### ❌ Port 8000 ist belegt

```bash
# Prozess auf Port 8000 beenden
lsof -ti:8000 | xargs kill -9
# Backend neu starten
uv run uvicorn main:app --reload
```

### ❌ `SUPABASE_URL environment variable is required`

Die `.env`-Datei fehlt oder ist nicht korrekt konfiguriert. Siehe [Schritt 5](#5-umgebungsvariablen-konfigurieren).

### ❌ `ModuleNotFoundError: No module named '...'`

```bash
cd backend

# Mit uv
uv sync

# Mit pip
source .venv/bin/activate
pip install -r ../requirements.txt
```

### ❌ Frontend: `Module not found` oder fehlende Pakete

```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

### ❌ `Model not trained` Fehler

Trainiere zuerst ein LDA-Modell:

```bash
curl -X POST http://localhost:8000/api/topics/train \
  -H "Content-Type: application/json" \
  -d '{"source": "employee", "num_topics": 5}'
```

### ❌ Python Cache Probleme

```bash
# Alle __pycache__ Verzeichnisse löschen
find . -type d -name "__pycache__" -exec rm -rf {} +
```

### ❌ Alte/korrupte Modelle

```bash
cd backend/models/saved_models
rm -f lda_model_*.* 2>/dev/null
```

### ❌ Dashboard lädt langsam

1. **Hard-Reload:** `Cmd+Shift+R` (Mac) / `Ctrl+Shift+F5` (Windows)
2. **Browser Cache löschen:** DevTools → Application → Clear Storage
3. **Network Tab prüfen:** API-Calls sollten parallel laufen

---

## Kurzreferenz

```bash
# === Backend ===
cd backend
uv sync                              # Dependencies installieren
uv run uvicorn main:app --reload     # Server starten
uv run pytest tests/                 # Tests ausführen

# === Frontend ===
cd frontend
npm install                          # Dependencies installieren
npm run dev                          # Dev Server starten
npm run build                        # Production Build

# === Aufräumen ===
find . -type d -name "__pycache__" -exec rm -rf {} +   # Python Cache
cd backend/models/saved_models && rm -f lda_model_*.*   # Alte Modelle
```
