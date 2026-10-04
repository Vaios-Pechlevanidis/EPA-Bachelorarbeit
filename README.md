---
title: EPA Bachelorprojekt
emoji: 📊
colorFrom: blue
colorTo: green
sdk: docker
pinned: false
---

# EPA Analytics

> Employer Review Analytics Platform — NLP-powered analysis of employer reviews using LDA Topic Modeling and Sentiment Analysis.

Parts of this project were developed with the assistance of AI tools (GitHub Copilot, Claude Sonnet 4.6). The generated content was reviewed and integrated by the author.


## 📋 Table of Contents

- [Knowledge Repository](#-knowledge-repository)
- [Requirements / Dependencies](#-requirements--dependencies)
- [Quick Start](#-quick-start)
- [Installation Guide](#-installation-guide)
- [Setup](#-setup)
- [Project Structure](#-project-structure)
- [LDA Topic Modeling](#-lda-topic-modeling)
- [Technology Stack](#️-technology-stack)

## 📚 Knowledge Repository

Here you can find all central resources and tools of the project:

| Resource | Description | Link |
|----------|-------------|------|
| **Figma** | UI/UX Prototype & Design Documentation | [Figma → Prototype](https://www.figma.com/design/J6DpLLKbuyFah1hdt6lgm3/Prototype?node-id=0-1&t=AheLdS2Z58LItjWB-0) |
| **Entscheidungen Zyklus 2** | Design decisions for cycle 2 (detection series, thresholds, metadata, sources) | [docs/entscheidungen.md](docs/entscheidungen.md) |
| **Datenbasis** | Review density per company and source (generated) | [docs/datenbasis.md](docs/datenbasis.md) |
| **Referenzzeiträume** | Literature note and annotation protocol for the manual reference periods (DZ1) | [docs/referenzzeitraeume-literatur.md](docs/referenzzeitraeume-literatur.md) |
| **Feature-Doku** | Each new dashboard feature presented, explained and justified (German) | [docs/feature-doku/](docs/feature-doku/README.md) |
| **Quellen-Spike** | Which news source delivers historical items (GDELT, Google News RSS, EQS, yfinance) | [docs/quellen-spike.md](docs/quellen-spike.md) |

---

## 🧱 Cycle 2 – Increment 0 "Fundament"

Groundwork for anomaly detection and explanation (Design Science Research, cycle 2):

| Step | Where | How to run |
|---|---|---|
| Company metadata (ticker, ISIN, sector, peer group) | `backend/migrations/006_add_company_metadata.sql`, `backend/data/company_metadata.json` | Run the migration in the Supabase SQL editor, then `cd backend && uv run python scripts/seed_company_metadata.py` (dry-run) / `--apply` |
| Detection series (E3) | `backend/services/rating_series_service.py` | Input for anomaly detection in increment 1: `monthly_series(company_id, source, dimension)`, eligibility via `is_eligible` |
| Data density report | `backend/scripts/report_data_density.py` → `docs/datenbasis.md`, `backend/data/data_density.json` | `cd backend && uv run python scripts/report_data_density.py` |
| Annotation basis (monthly series per company) | `backend/scripts/make_annotation_basis.py` → `backend/data/series/*.csv`, `backend/data/annotations.json` | `cd backend && uv run python scripts/make_annotation_basis.py` |
| Annotation check | `backend/scripts/validate_annotations.py` | `cd backend && uv run python scripts/validate_annotations.py` |
| News-source spike | `backend/scripts/spike_news_sources.py` → `docs/quellen-spike.md` | `cd backend && uv run python scripts/spike_news_sources.py --company "Thyssenkrupp" --month 2023-04 --ticker TKA.DE` |

Reference periods in `backend/data/annotations.json` are entered manually by the author from the series CSVs (see `docs/entscheidungen.md`, E5). Status 2026-10-03: the entries were deferred and the detection code of increment 1 now exists, so the order originally planned in E5 no longer applies. Replacement rule (E5): annotate before the evaluation, from the series CSVs and without looking at any detection results; this is recorded as a limitation for DZ1.

---

## 🔎 Cycle 2 – Increment 1 "Anomalien im Verlauf"

Detects lasting level shifts in the monthly rating series and shows them in the dashboard. The feature is presented, explained and justified in [docs/feature-doku/01-anomalien-im-verlauf.md](docs/feature-doku/01-anomalien-im-verlauf.md); method and parameters are recorded as preliminary in `docs/entscheidungen.md`, E9.

| Part | Where | Notes |
|---|---|---|
| Change point detector | `backend/models/changepoint_detector.py` | PELT from `ruptures` (`model="l2"`, `min_size=3`, scaled penalty `2 · σ² · ln(n)` per series with robust `noise_sigma`; fixed `penalty` still selectable), moving-mean fallback for short series, `ChangePointDetector` protocol for further methods |
| Anomaly service | `backend/services/anomaly_service.py` | Uses `monthly_series` and `is_eligible` (E3/E4), detects on evaluated months only, filters `min_delta` (0.3 stars), sorts falls before rises; reviews before/after per change |
| API | `backend/routes/anomalies.py` | `GET /api/analytics/company/{company_id}/anomalies?source=employee&dimension=durchschnittsbewertung&penalty_factor=&penalty=&min_delta=` — `penalty_factor` (default 2) scales the penalty, `penalty` switches to a fixed value; returns series (period, mean, count, n_values, evaluated), anomalies (incl. segment bounds, gap before the marked month), parameters, eligibility; `dimension=all` returns eligibility and anomalies per dimension plus one combined list. Computed live, read-only, no migration |
| Dashboard card | `frontend/src/components/dashboard/AnomalyCard.jsx` | Below the chart row; chart as in the first version (monthly line, rings on the marked months), dashed interpolation over gaps, dimension picker, counter, eligibility notice; click opens the detail page, which shows the list, step markers (mean before → mean after), level line and full legend |
| Detail page | `frontend/src/pages/Anomalies.jsx`, route `/anomalies?company=ID&dimension=KEY&range=5y\|3y\|1y` | Larger chart and list, dimension and company switcher, chart range from the first to the last evaluated month (hidden empty edges are named below the chart), time filter (view window counted back from the last evaluated month; detection always uses the full series), also reachable via "Anomalien" in the sidebar |
| Parameter overview | `backend/scripts/explore_anomaly_params.py` → `backend/data/calibration/` | `cd backend && uv run python scripts/explore_anomaly_params.py` (read-only; evidence for checkpoint 1, not a calibration against reference periods) |
| Tests | `backend/tests/anomaly/` (detector, service, route; in-memory store, no network) | `cd backend && uv run python -m pytest tests/anomaly tests/forecast tests/test_rating_series_service.py -q` |

---

## 🔍 Cycle 2 – Increment 2 "Drill-down und Vorher-Nachher-Vergleich"

Select a change on the detail page to see the reviews of the periods before and after it and a comparison of what shifted in those reviews (topic shares, sentiment). The comparison describes changes in the reviews; it makes no statement about causes. Feature doc: [docs/feature-doku/02-drilldown-und-vergleich.md](docs/feature-doku/02-drilldown-und-vergleich.md); decisions E10–E13 in `docs/entscheidungen.md` (comparison windows and thresholds preliminary).

| Part | Where | Notes |
|---|---|---|
| Reviews of a period | `backend/services/review_service.py`, `GET /api/analytics/company/{id}/reviews?source=&start=&end=&status=&offset=&limit=&format=full` | Dates inclusive, paginated read (more than 1000 rows), newest first, `total` = all matches; `format=full` returns `id`, `preview`, `fullReview` (format of the topic overview). Without the new parameters the response is unchanged |
| Keyword topics | `backend/services/keyword_topic_service.py` | Topic definitions per source and `analyze_topic` (moved from `routes/analytics.py`, output unchanged), `topics_in_review(row, source)`; `topic-overview` gains `end_date` |
| Comparison | `backend/services/explanation_service.py`, `GET /api/analytics/company/{id}/anomalies/{anomaly_id}/explanations?source=&dimension=&status=&window_months=6` | Windows (E12), count and mean rating, share per topic and sentiment (overall and per topic), shift in percentage points, `low_basis`; one `SentimentAnalyzer` per process (transformer with star rating as hint, lexicon fallback), at most 300 newest reviews with text per window, cached per review id; `explanations` is empty until increment 5; unknown id → 404 |
| Reviewer group | `rating_series_service`, `anomaly_service`, `/anomalies?status=` | Status keys per source (`angestellt`, `ex-angestellt`, `eingestellt`, `abgelehnt`, …, `unbekannt`); detection, eligibility and penalty run per source, dimension and status (E13) |
| Frontend | `frontend/src/pages/Anomalies.jsx` (`?anomaly=&source=&status=`), `components/dashboard/AnomalyComparison.jsx`, `PeriodReviews.jsx`, `hooks/useReviewPages.js`, `useAnomalyComparison.js`, `lib/reviewerStatus.js` | Click a step or list row to select; sections "Vorher-Nachher-Vergleich" and "Bewertungen des Zeitraums" (25 per page, opens `ReviewDetailModal`); source toggle and status picker on card and detail page |
| Topic highlight | `/reviews?…&dimension=image&format=full[&topic_only=true]`, `components/dashboard/HighlightedText.jsx` | With a single dimension selected, keyword hits of its topic are marked in the review lists and the review modal, reviews mentioning it are tagged, a toggle shows only those (`?thema=nur`), and the comparison row of the topic is highlighted |
| Outlier months (E14) | `detect_outlier_months` in `backend/services/anomaly_service.py`, field `outlier_months` in `/anomalies` | Single months that differ from the medians of up to 3 evaluated months before and after by at least `max(3·σ, 0.5)` stars without forming a new level; shown as diamonds on card and detail page, list and reviews of the month (`?month=YYYY-MM`). Feature doc: [docs/feature-doku/03-auffaellige-einzelmonate.md](docs/feature-doku/03-auffaellige-einzelmonate.md) |
| Tests | `backend/tests/drilldown/`, `backend/tests/anomaly/test_status_filter.py` (in-memory store, lexicon mode, no network) | `cd backend && uv run python -m pytest tests/anomaly tests/drilldown tests/forecast tests/test_rating_series_service.py -q` |

---

## 📈 Cycle 2 – Increment 3 "Aktienkurs und Kennzahlen"

On the detail page the share price runs along the rating chart on a second y-axis, with a few company figures below it. Price and figures place the ratings in their market context; they are not an explanation. The dashboard neither claims nor computes any relation between price and ratings. Feature doc: [docs/feature-doku/04-kurs-und-kennzahlen.md](docs/feature-doku/04-kurs-und-kennzahlen.md); decision E15 in `docs/entscheidungen.md` (preliminary).

| Part | Where | Notes |
|---|---|---|
| Service | `backend/services/context_service.py` | Ticker from `companies.ticker`, fallback to `backend/data/company_metadata.json` when the column or value is missing (only if the name matches); monthly closes via yfinance (`period="max"`, `interval="1mo"`, adjusted for splits and dividends, running month dropped); market cap, employees, revenue per fiscal year; the network call sits behind `fetch_raw` and can be swapped |
| Cache | `backend/data/market/<ticker>.json` (in `.gitignore`, not committed) | Fields `ticker`, `ticker_name`, `currency`, `fetched_at`, `source`, `adjustment`, `prices`, `metrics`. Not refreshed automatically; rerun the script to update |
| Fill the cache | `backend/scripts/fetch_market_data.py` | `cd backend && uv run python scripts/fetch_market_data.py` (all tickers), `--ticker SAP.DE` or `--company 19` (one). Reads the database, writes only files |
| Runtime | `MARKET_LIVE_FETCH` (environment) | Cache first. Without a cache file the backend fetches once live and stores the result, unless `MARKET_LIVE_FETCH=0`. A failed fetch returns `available: false` with a reason (no 500) and is not retried for 15 minutes |
| API | `backend/routes/market.py` | `GET /api/analytics/company/{company_id}/market?start=YYYY-MM&end=YYYY-MM` → `company_id`, `ticker`, `ticker_scope` (`eigene Aktie` / `Konzernmutter`), `ticker_name`, `currency`, `available`, `reason`, `prices`, `metrics`, `fetched_at`, `source`. Without a ticker: `available: false` with the reason from `peer_group`; unknown company 404; invalid period 400 |
| Frontend | `frontend/src/pages/Anomalies.jsx` (`?kurs=aus`), `components/dashboard/MarketContext.jsx`, `AnomalyChart` (prop `market`), `hooks/useMarket.js`, `lib/market.js` | Thin violet line on the right axis (currency in the axis label, legend, tooltip), only for the displayed months; toggle "Aktienkurs" (on by default when a price exists); figures row with "aktuell, Stand …"; fixed note "Einordnung, keine Erklärung …"; parent company named explicitly (NTT DATA SE → NTT, Inc.). The dashboard card and the PDF export are unchanged |
| Stock dashboard (E16) | `frontend/src/pages/Stock.jsx`, route `/aktie?company=ID&range=1y\|3y\|5y\|10y\|max&periode=quartal`, `components/dashboard/FinanceCards.jsx` | Separate page ("Aktie" in the dashboard sidebar, link on the anomaly page): price chart, analyst recommendations (last four months), revenue vs. net income (annual or quarterly), recent news. Feature doc: [docs/feature-doku/05-aktien-dashboard.md](docs/feature-doku/05-aktien-dashboard.md) |
| Finance API | `GET /api/analytics/company/{id}/finance`, `GET /api/analytics/company/{id}/news` | `/finance` = `/market` plus `analysts` and `earnings` (from the same cache; run the script again for caches from before E16). `/news` reads Google News RSS by company name (`backend/services/news_service.py`), cached 12 h under `backend/data/market/news/`; `fetch_market_data.py --news` fills it |
| Tests | `backend/tests/market/` (mocked fetcher, temporary cache directory, no network) | `cd backend && uv run python -m pytest tests/market -q` |

---

## ⚡ Quick Start

```bash
# Start backend
cd backend
uv sync
uv run uvicorn main:app --reload

# Start frontend (new terminal)
cd frontend
npm install
npm run dev
```

**Backend:** `http://localhost:8000` | **API Docs:** `http://localhost:8000/docs`  
**Frontend:** `http://localhost:5173`

## 📋 Requirements / Dependencies

To run the project locally, you need:

* **Python** >= 3.13
* **Node.js** v20+
* **npm** (comes with Node.js)
* **uv** → https://docs.astral.sh/uv/ (recommended for Python)
* **Supabase Account** (for database)
* IDE of your choice, preferably **VSCode**

### Python Packages (Backend):
* `fastapi` - Web Framework
* `gensim` - Topic Modeling (LDA)
* `transformers` >= 5.1 - ML-based Sentiment Analysis (German BERT)
* `torch` >= 2.10 - PyTorch Backend for Transformers
* `pandas` - Data Processing
* `supabase` - Database Client
* `statsmodels` - Statistical Analysis

### npm Packages (Frontend):
* `@radix-ui/react-checkbox` - Checkbox Component
* `@radix-ui/react-label` - Label Component
* `@radix-ui/react-dialog` - Dialog/Modal Component
* `@radix-ui/react-select` - Select/Dropdown Component
* `@radix-ui/react-dropdown-menu` - Dropdown Menu Component
* `@radix-ui/react-popover` - Popover Component
* `@radix-ui/react-separator` - Separator Component
* `cmdk` - Command Menu Component
* `recharts` - Chart Library
* `lucide-react` - Icon Library
* `tailwindcss` - CSS Framework
* `html2canvas` + `jspdf` - PDF Export

## 📦 Installation Guide

A detailed step-by-step guide for setting up the project can be found in **[INSTALLATION.md](./INSTALLATION.md)**.

It covers:
- Prerequisites & Software Installation
- Backend & Frontend Setup (with `uv` and `pip`)
- Configuring Environment Variables
- Verifying the Installation
- Common Problems & Solutions

## 🚀 Setup

### Backend (FastAPI)

If `uv` is installed, open the terminal and run:

```bash
cd backend
uv sync
```

Then select the `.venv` folder as the Python Interpreter for the project.

**Alternative without uv:** If you prefer classic `pip`:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # On macOS/Linux
# .venv\Scripts\activate  # On Windows
pip install -r requirements.txt
```

The backend server can be started as follows:

```bash
uv run uvicorn main:app --reload
```

or with classic Python:

```bash
python -m uvicorn main:app --reload
```

**Backend runs at:** `http://localhost:8000`  
**API Documentation:** `http://localhost:8000/docs` (Swagger UI)

### Frontend (React + Vite)

If `node` is installed, open the terminal and run:

```bash
cd frontend
npm install
```

Then start the frontend dev server:

```bash
npm run dev
```

**Frontend runs at:** `http://localhost:5173`

## 🔧 Environment Variables

Create a `.env` file in the `backend/` folder:

```env
# Supabase Configuration
SUPABASE_URL=your-supabase-url
SUPABASE_KEY=your-supabase-key

# Optional: API Configuration
API_HOST=0.0.0.0
API_PORT=8000
```

**Important:** The `.env` file is listed in `.gitignore` and will not be committed to the repository!

## 💡 Tips

* It's best to have **2 terminal sessions** open to run backend and frontend simultaneously!
* Make sure the `.env` file in the backend folder is correctly configured
* For a production build of the frontend: `npm run build`
* Clear cache: `find . -type d -name "__pycache__" -exec rm -rf {} +`
* Delete old models: `cd backend/models && rm -f lda_model_*.* 2>/dev/null`

### Performance Tips (Version 2.1):
* **Dashboard loading slowly?** → Hard-Reload (Cmd+Shift+R / Ctrl+Shift+F5)
* **Check API calls**: Browser DevTools → Network Tab → Filter "Fetch/XHR"
* **Analyze re-renders**: React DevTools → Profiler Tab
* **Caching enabled**: CompanySearchSelect automatically caches after first load

### Topic Detail Modal Features:
* **Collapsible view controls:** Click "Customize View" to show/hide elements
* **Smart layout:** Charts automatically expand when others are hidden
* **5 customizable sections:**
  - ✅ Statistics (Frequency, Rating, Sentiment)
  - ✅ Timeline Chart (Rating over time)
  - ✅ Sentiment Chart (Gauge with percentage display)
  - ✅ Typical Statements (Top 3 Statements)
  - ✅ Sample Review (with navigation)
* **Time Filter:** Choose between All Time, 1 Year, 6 Months, 3 Months, or 1 Month
* **Review Navigation:** Click on statements to see the full review

## 📁 Project Structure

```
epa-analytics/
├── backend/                      # FastAPI Backend
│   ├── main.py                  # Main entry point
│   ├── config.py                # Configuration
│   ├── pyproject.toml           # Python Dependencies (uv)
│   ├── examples_statistical_usage.py # Statistics examples
│   │
│   ├── database/                # Database connections (Supabase)
│   │   └── supabase_client.py
│   │
│   ├── migrations/              # SQL migrations
│   │   ├── 001_create_candidates_table.sql
│   │   ├── 002_create_employee_table.sql
│   │   ├── 003_create_companies_table.sql
│   │   └── 004_add_company_references.sql
│   │
│   ├── models/                  # Machine Learning Models
│   │   ├── changepoint_detector.py # Level-shift detection (PELT, increment 1)
│   │   ├── lda_topic_model.py  # LDA Topic Modeling
│   │   ├── sentiment_analyzer.py # Sentiment Analysis
│   │   └── saved_models/       # Trained models
│   │
│   ├── services/                # Business Logic Services
│   │   ├── rating_series_service.py       # Monthly rating series (E3/E4)
│   │   ├── anomaly_service.py             # Anomalies in the monthly series (increment 1)
│   │   ├── review_service.py              # Reviews of a period, fullReview, status groups (increment 2)
│   │   ├── keyword_topic_service.py       # Keyword topics, topics_in_review (increment 2)
│   │   ├── explanation_service.py         # Before/after comparison of a change (increment 2)
│   │   ├── excel_service.py               # Excel Import/Export
│   │   ├── topic_model_service.py         # Topic Modeling DB Service
│   │   ├── topic_rating_service.py        # Topic-Rating Analysis
│   │   ├── topic_average_rating_service.py # Topic Average Ratings
│   │   ├── statistical_enrichment.py      # Statistical Enrichment
│   │   └── statistical_validator.py       # Statistical Validation
│   │
│   ├── routes/                  # API Endpoints
│   │   ├── analytics.py        # Analytics API (12 Endpoints)
│   │   ├── anomalies.py        # Anomalies and comparison API (increments 1 and 2)
│   │   ├── companies.py        # Company Management (9 Endpoints)
│   │   ├── topics.py           # Topic Modeling API (13 Endpoints)
│   │   └── upload.py           # File Upload
│   │
│   ├── scripts/                 # Utility Scripts
│   │   ├── explore_anomaly_params.py # Anomaly parameter overview (read-only)
│   │   ├── train_models.py     # Model Training
│   │   ├── fix_html_entities.py # Text Cleanup
│   │   ├── sweep_num_topics_db.py    # Topic Count Optimization
│   │   └── test_num_topics_compare.py # Topic Comparison Tests
│   │
│   ├── tests/                   # Organized Tests
│   │   ├── anomaly/            # Change point detection tests
│   │   ├── drilldown/          # Reviews, keyword topics, comparison (increment 2)
│   │   ├── topic_modeling/     # Topic Modeling Tests
│   │   ├── sentiment_analysis/ # Sentiment Tests
│   │   └── statistical/        # Statistical Tests
│   │
│   └── examples/                # Examples & Demos
│       ├── topic_modeling_examples.py
│       └── topic_rating_examples.py
│
├── frontend/                    # React/Vite Frontend
│   ├── src/                    # Source Code
│   │   ├── components/         # React Components
│   │   │   ├── CompanySearchSelect.jsx  # Optimized with caching
│   │   │   ├── dashboard/     # Dashboard Components
│   │   │   │   ├── AnomalyCard.jsx          # Anomalies in the rating history
│   │   │   │   ├── AnomalyComparison.jsx    # Before/after comparison (increment 2)
│   │   │   │   ├── PeriodReviews.jsx        # Reviews of a comparison window (increment 2)
│   │   │   │   ├── DominantTopicsCard.jsx   # Dominant Topics
│   │   │   │   ├── IndividualReviewsCard.jsx # Individual Reviews
│   │   │   │   ├── TimelineCard.jsx         # React.memo optimized
│   │   │   │   ├── TopicRatingCard.jsx      # React.memo optimized
│   │   │   │   ├── TopicOverviewCard.jsx    # React.memo optimized
│   │   │   │   └── modals/
│   │   │   │       ├── MostCriticalModal.jsx
│   │   │   │       ├── NegativTopicModal.jsx
│   │   │   │       ├── SorceModal.jsx
│   │   │   │       ├── TrendModal.jsx
│   │   │   │       ├── TopicTableModal.jsx    # Topic Table
│   │   │   │       ├── TopicDetailModal.jsx   # Topic Details with Customize View
│   │   │   │       └── ReviewDetailModal.jsx  # Full Review View
│   │   │   └── ui/            # UI Components (shadcn)
│   │   │       ├── badge.tsx
│   │   │       ├── button.tsx
│   │   │       ├── card.tsx
│   │   │       ├── checkbox.jsx
│   │   │       ├── command.tsx
│   │   │       ├── dialog.tsx
│   │   │       ├── dropdown-menu.tsx
│   │   │       ├── input.tsx
│   │   │       ├── label.jsx
│   │   │       ├── popover.tsx
│   │   │       ├── select.tsx
│   │   │       ├── separator.tsx
│   │   │       └── table.tsx
│   │   ├── pages/             # Pages
│   │   │   ├── Dashboard.jsx
│   │   │   ├── Compare.jsx
│   │   │   ├── Anomalies.jsx  # Detail page for anomalies
│   │   │   └── Welcome.jsx
│   │   ├── hooks/             # React Hooks
│   │   │   ├── useAnomalies.js # Fetches series and anomalies
│   │   │   ├── useAnomalyComparison.js # Fetches the before/after comparison
│   │   │   ├── useReviewPages.js # Loads reviews of a period page by page
│   │   │   └── useTheme.js    # Light/dark theme
│   │   ├── utils/             # Utility Functions
│   │   │   ├── pdfExport.js   # PDF Export
│   │   │   ├── chartValidator.js # Chart Validation
│   │   │   └── pdf/           # PDF Utilities
│   │   └── lib/               # Utilities
│   │       ├── anomalySeries.js # Time window and display-only interpolation for anomaly charts
│   │       ├── ratingCategories.js # Rating dimensions per source: key → label
│   │       ├── reviewerStatus.js # Reviewer status labels and options
│   │       └── utils.ts
│   ├── public/                # Static Assets
│   └── package.json           # Node.js Dependencies
├── requirements.txt            # Python Dependencies (Project Root)
└── INSTALLATION.md             # Detailed Installation Guide
```

## 🛠️ Technology Stack

### Backend
* **Framework:** FastAPI (modern Python Web API)
* **Server:** Uvicorn (ASGI Server)
* **Database:** Supabase (PostgreSQL)
* **ML/AI:** 
  - Gensim 4.3+ (LDA Topic Modeling)
  - Transformers 5.1+ (ML-based Sentiment Analysis with German BERT)
  - PyTorch 2.10+ (Backend for Transformer models)
  - Lexicon-based Sentiment Analysis (rule-based, fast)
* **Statistics:** Statsmodels 0.14+
* **Data Processing:** Pandas, OpenPyXL
* **Tools:** Python-dotenv, Python-multipart

### Frontend
* **Framework:** React 19
* **Build Tool:** Vite 6
* **Routing:** React Router DOM 7
* **UI Library:** shadcn/ui (Radix UI + Tailwind CSS)
  - Dialog, Select, Dropdown Menu, Popover, Separator
  - Checkbox, Label (for view customization)
  - Badge, Button, Card, Input, Command, Table
* **Charts:** Recharts (Line Charts, Gauge Charts)
* **Icons:** Lucide React (Eye, ChevronDown, ChevronUp, Calendar, etc.)
* **PDF Export:** html2canvas + jsPDF
* **Styling:** Tailwind CSS v4 with Custom Animations
* **Linting:** ESLint

### Dashboard Features
* **Performance Optimizations (Version 2.1):**
  - ⚡ **Parallel Loading**: All KPI data loads simultaneously (~50% faster)
  - 💾 **Caching**: Company list is cached (~80% faster from 2nd load onward)
  - ⏱️ **Debouncing**: Smart search with 300ms delay
  - 🎯 **React.memo**: Optimized re-renders for large components
  - 🔄 **Better Error Handling**: Explicit logging for easier debugging

* **Topic Overview:**
  - Interactive topic table with search functionality
  - Detail view with line chart (rating over time)
  - Gauge chart for sentiment visualization
  - Typical statements and sample reviews
  - Two-level modal interaction (Table → Details)
  - **Customize View:** Toggleable elements with intelligent layout adjustment
  - **Responsive Charts:** Charts automatically expand when others are hidden

### Database Schema
* **Tables:** `candidates`, `employee`, `companies`
* **Features:** Star ratings, text feedback, relational data

## 🤖 LDA Topic Modeling

This project includes a complete **LDA Topic Modeling** integration with **Gensim** for automatic topic extraction from candidate and employee feedback.

### Features

✅ **Automatic Topic Detection** in text data  
✅ **Sentiment Analysis** - Dual-Mode (Lexicon + ML-Transformer)
  - **Lexicon Mode:** Fast, rule-based, no dependencies
  - **Transformer Mode:** ML-based with German BERT, 100% accuracy
✅ **Star Ratings** - Combines text topics with rating data  
✅ **Database Integration** - Direct access to candidate and employee data  
✅ **RESTful API** - 13 endpoints for training, analysis, and prediction  
✅ **Model Persistence** - Save and load trained models  
✅ **German Text Processing** - Optimized stopword list  
✅ **Flexible Analysis** - Individual texts or entire datasets  
✅ **Topic-Rating Correlation** - Understand how different topics are rated  

### Quick Start

1. **Start Backend:**
   ```bash
   cd backend
   uv run uvicorn main:app --reload
   ```

2. **Open API Documentation:**
   ```
   http://localhost:8000/docs
   ```

3. **Train first model:**
   ```bash
   curl -X POST http://localhost:8000/api/topics/train \
     -H "Content-Type: application/json" \
     -d '{"source": "both", "num_topics": 5}'
   ```

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/topics/status` | GET | Get model status |
| `/api/topics/database/stats` | GET | Database statistics |
| `/api/topics/train` | POST | Train a new model |
| `/api/topics/topics` | GET | Show discovered topics |
| `/api/topics/predict` | POST | Predict topics for text |
| `/api/topics/analyze-record` | POST | Analyze a specific record |
| `/api/topics/analyze/employee-reviews-with-ratings` | GET | Employee reviews with topics, sentiment & ratings |
| `/api/topics/analyze/candidate-reviews-with-ratings` | GET | Candidate reviews with topics, sentiment & ratings |
| `/api/topics/analyze/topic-rating-correlation` | GET | Correlation between topics and ratings |
| `/api/topics/models/list` | GET | List saved models |
| `/api/topics/models/load` | POST | Load a saved model |
| `/api/topics/company/{company_id}/negative-topics` | GET | Negative topics for a company |
| `/api/topics/company/{company_id}/most-critical` | GET | Most critical topics for a company |

### Test Installation

```bash
# Run tests
cd backend
pytest tests/
```

### Run Examples

**Basic Topic Modeling:**
```bash
cd backend
uv run python examples/topic_modeling_examples.py
```

**Topic-Rating Analysis (NEW):**
```bash
cd backend
uv run python examples/topic_rating_examples.py
```

### Examples

- 💡 [`backend/examples/`](backend/examples/) - Examples & Demos
  - `topic_modeling_examples.py` - Basic LDA
  - `topic_rating_examples.py` - Topics + Sentiment + Ratings

### Workflow

```mermaid
graph LR
    A[Database] --> B[Extract Text]
    B --> C[Preprocessing]
    C --> D[LDA Training]
    D --> E[Topics Discovered]
    E --> F[Save Model]
    F --> G[Make Predictions]
```

### Data Sources

**Candidates Table:**
- `stellenbeschreibung`
- `verbesserungsvorschlaege`

**Employee Table:**
- `jobbeschreibung`
- `gut_am_arbeitgeber_finde_ich`
- `schlecht_am_arbeitgeber_finde_ich`
- `verbesserungsvorschlaege`

### Example Usage

#### Python (Topic-Rating Analysis):
```python
import requests

# Train model
response = requests.post(
    "http://localhost:8000/api/topics/train",
    json={"source": "employee", "num_topics": 5}
)
print(response.json())

# Analyze employee reviews with sentiment & ratings
response = requests.get(
    "http://localhost:8000/api/topics/analyze/employee-reviews-with-ratings",
    params={"limit": 50}
)
analysis = response.json()['analysis']

# Get topic-rating correlation
response = requests.get(
    "http://localhost:8000/api/topics/analyze/topic-rating-correlation"
)
correlation = response.json()['correlation']

for topic in correlation['topics']:
    print(f"Topic {topic['topic_id']}: "
          f"{topic['avg_rating']:.1f}⭐ "
          f"({topic['mention_count']} mentions)")
```

#### cURL:
```bash
# Analyze topics with ratings
curl "http://localhost:8000/api/topics/analyze/topic-rating-correlation"

# Analyze text
curl -X POST http://localhost:8000/api/topics/predict \
  -H "Content-Type: application/json" \
  -d '{"text": "The work-life balance is excellent!", "threshold": 0.1}'
```

### Technical Details

- **LDA Algorithm**: Latent Dirichlet Allocation with Gensim
- **Sentiment Analysis**: Lexicon-based with 100+ German sentiment words
  - Recognizes intensifiers (sehr, extrem, total)
  - Considers negations (nicht, kein, nie)
  - Calculates polarity (-1 to +1) and subjectivity (0 to 1)
- **Preprocessing**: Lowercase, stopword removal, token filtering
- **Language**: Optimized for German texts
- **Parameters**: Configurable topics (2–20), passes, iterations
- **Storage**: Automatic saving of trained models
- **Integration**: Combines topics, sentiment, and star ratings

## 🚨 Common Problems & Solutions

### Backend won't start
```bash
# Port 8000 is in use
lsof -ti:8000 | xargs kill -9
uv run uvicorn main:app --reload
```

### Frontend won't start
```bash
# Missing dependencies
cd frontend
npm install
npm run dev

# Reinstall specific packages (if necessary)
npm install @radix-ui/react-checkbox @radix-ui/react-label
```

### Dashboard loading slowly (Version 2.1 should fix this!)
```bash
# 1. Hard-Reload in browser
# Chrome/Edge: Cmd+Shift+R (Mac) or Ctrl+Shift+F5 (Windows)
# Firefox: Cmd+Shift+R (Mac) or Ctrl+F5 (Windows)

# 2. Clear browser cache
# DevTools → Application → Clear Storage

# 3. Check Network Tab
# DevTools → Network → Check if KPI calls run in parallel
# Should now be ~50% faster!
```

### "Model not trained" Error
```bash
# Train a model first
curl -X POST http://localhost:8000/api/topics/train \
  -H "Content-Type: application/json" \
  -d '{"source": "employee", "num_topics": 5}'
```

### Python Cache Issues
```bash
# Delete all __pycache__ directories
find . -type d -name "__pycache__" -exec rm -rf {} +
```

### Delete old models
```bash
# Free up disk space
cd backend/models
rm -f lda_model_*.* 2>/dev/null
```

### Finding tests after reorganization
```bash
# Tests are now organized in backend/tests/
pytest backend/tests/                    # All tests
pytest backend/tests/topic_modeling/     # Topic modeling only
pytest backend/tests/sentiment_analysis/ # Sentiment only
pytest backend/tests/statistical/        # Statistical only
```

## 📚 Further Resources

### Project Documentation
- **Installation Guide**: [INSTALLATION.md](./INSTALLATION.md)
- **Test Documentation**: [backend/tests/](./backend/tests/)
- **Examples**: [backend/examples/](./backend/examples/)

### API & Tools
- **API Documentation**: http://localhost:8000/docs (Swagger UI)
- **Supabase**: https://supabase.com/docs
- **FastAPI**: https://fastapi.tiangolo.com
- **React**: https://react.dev
- **Gensim**: https://radimrehurek.com/gensim/
- **Recharts**: https://recharts.org/

## 👥 Team

Vaios Pechlevanidis

## 📄 License

This project is **not Open Source**.

**Usage & Licensing**

Any use, reuse, reproduction, or licensing of this project — in whole or in part — requires the explicit written permission of the author.

This applies in particular to:
- commercial use
- distribution to third parties
- publication or inclusion in other projects
- modification and further development

Contact for inquiries: **Vaios Pechlevanidis** – pechlevanidis.vaios@gmail.com
