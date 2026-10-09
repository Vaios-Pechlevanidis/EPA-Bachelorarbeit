import * as React from "react"
import { useState, useEffect, useCallback, useRef } from "react"
import { useLocation, useNavigate } from "react-router-dom"
import { Loader2, Upload, Clock } from "lucide-react"

import { WorkPulseLogo }     from "@/components/WorkPulseLogo"
import { TimelineCard }      from "@/components/dashboard/TimelineCard"
import { TopicRatingCard }   from "@/components/dashboard/TopicRatingCard"
import { TopicOverviewCard } from "@/components/dashboard/TopicOverviewCard"
import { AnomalyCard }       from "@/components/dashboard/AnomalyCard"
import KPIGrid               from "@/components/dashboard/KPIGrid"
import { DataStatusBar }     from "@/components/dashboard/DataStatusBar"
import { invalidateDataStatus, loadDataStatus } from "@/hooks/useDataStatus"
import { CompanySearchSelect } from "@/components/CompanySearchSelect"
import SorceModal        from "../components/dashboard/modals/SorceModal"
import TrendModal        from "../components/dashboard/modals/TrendModal"
import RollingModal      from "../components/dashboard/modals/RollingModal"
import MostCriticalModal from "../components/dashboard/modals/MostCriticalModal"
import NegativTopicModal from "../components/dashboard/modals/NegativTopicModal"
import ImportModal from "../components/dashboard/modals/ImportModal"
import { getImportHistory } from "@/lib/importHistory"

import {
  Dashboard as DashboardIcon, Compare, Download, Building, Home, Search, Loader, Sun, Moon, Anomaly as AnomalyIcon, TrendUp,
} from "../icons"
import { loadCompanies } from "@/lib/companies"
import { fetchJsonShared } from "@/lib/sharedFetch"
import { useTheme } from "../hooks/useTheme"
import { API_URL, SHOW_FINANCE_EXTRAS } from "../config"
import { exportKPIsAsPDF } from "../utils/pdfExport"
import { waitForMultipleCharts, waitForChartReady, validateChart, waitForImagesInElement } from "../utils/chartValidator"

export default function Dashboard() {
  const location = useLocation()
  const navigate = useNavigate()
  const companyFromWelcome    = location.state?.companyId
  const companyNameFromWelcome = location.state?.companyName

  /* ---- Modal state ---- */
  const [open, setOpen]               = useState(false)
  const [openTrend, setOpenTrend]     = useState(false)
  const [openRolling, setOpenRolling] = useState(false)
  const [openNegative, setOpenNegative] = useState(false)
  const [openMostCritical, setOpenMostCritical] = useState(false)
  const [openImport, setOpenImport]   = useState(false)

  /* ---- Company state ---- */
  const [companyQuery, setCompanyQuery] = useState(companyNameFromWelcome || "")
  const [selectedCompany, setSelectedCompany]     = useState(companyFromWelcome || "")
  const [selectedCompanyId, setSelectedCompanyId] = useState(companyFromWelcome || null)
  const [selectedCompanyName, setSelectedCompanyName] = useState(companyNameFromWelcome || "")
  const [companies, setCompanies]   = useState([])
  const [error, setError]           = useState("")

  /* ---- KPI data ---- */
  const [data, setData]                       = useState(null)
  const [trendData, setTrendData]             = useState(null)
  const [rollingData, setRollingData]         = useState(null)   // 12- vs. 24-Monats-Schnitt (Inkrement 6, FA-08)
  const [mostCriticalData, setMostCriticalData] = useState(null)
  const [negativeTopicItem, setNegativeTopicItem] = useState(null)

  /* ---- Global time range filter ---- */
  const [globalTimeRange, setGlobalTimeRange] = useState("all")

  /* ---- Timeline / TopicRating filter state ---- */
  const [timelineFilters, setTimelineFilters] = useState({
    metric: "Ø Score", source: "employee", granularity: "overall", selectedYear: null,
  })
  const [topicRatingFilters, setTopicRatingFilters] = useState({
    source: "employee", granularity: "overall", selectedYear: null, visibleTopics: [], stats: {},
  })
  const [topicOverviewData, setTopicOverviewData] = useState({ topics: [], sourceFilter: null, stats: {} })
  // Zustand der Anomalien-Karte (Auswahl, Zähler, Eignung) für den PDF-Export
  const [anomalyExportData, setAnomalyExportData] = useState(null)

  /* ---- Loading ---- */
  const [dashboardLoadingStates, setDashboardLoadingStates] = useState({
    timelineChart: true, topicRatingChart: true, topicOverview: true, anomalyChart: true,
  })
  const [exportingPDF, setExportingPDF] = useState(false)

  const topicOverviewRef = useRef(null)

  const effectiveCompanyId = selectedCompany || selectedCompanyId || companyFromWelcome || null

  // Kacheln: geladen, sobald der Schlüssel (Firma, Zeitraum) der letzten Ladung passt
  // (abgeleitet statt setState im Effekt, Lint-Regel react-hooks/set-state-in-effect).
  const kpiKey = effectiveCompanyId ? `${effectiveCompanyId}:${globalTimeRange}` : null
  const [kpiDoneKey, setKpiDoneKey] = useState(null)
  const kpiLoading = Boolean(kpiKey) && kpiDoneKey !== kpiKey
  const loadingStatesRef = useRef({ ...dashboardLoadingStates, kpiCards: kpiLoading })
  useEffect(() => {
    loadingStatesRef.current = { ...dashboardLoadingStates, kpiCards: kpiLoading }
  }, [dashboardLoadingStates, kpiLoading])
  // Import-Verlauf (localStorage) je Firma, beim Rendern gelesen (bis zu 10 Einträge).
  const importHistory = effectiveCompanyId ? getImportHistory(effectiveCompanyId) : []

  /* ---- Company helpers ---- */
  // Ohne Firma: Kennzahlen leeren (in den Ereignisbehandlern, nicht im Effekt).
  const clearKpis = useCallback(() => {
    setData(null); setTrendData(null); setRollingData(null); setMostCriticalData(null); setNegativeTopicItem(null)
  }, [])

  const handleCompanySelectFromDropdown = useCallback((company) => {
    if (company) {
      setSelectedCompanyId(company.id)
      setSelectedCompanyName(company.name)
      setSelectedCompany(company.id)
      setCompanyQuery(company.name)
      setError("")
    } else {
      setSelectedCompanyId(null)
      setSelectedCompanyName("")
      setSelectedCompany("")
      clearKpis()
    }
  }, [clearKpis])

  const handleCreateNewCompany = (companyName) => {
    const name = companyName?.trim()
    navigate("/welcome", name ? { state: { prefillCompanyName: name } } : undefined)
  }

  /* ---- KPI fetching ---- */
  function getStartDate(timeRange) {
    if (timeRange === "1y") {
      const d = new Date(); d.setFullYear(d.getFullYear() - 1); return d.toISOString().slice(0, 10)
    }
    if (timeRange === "3y") {
      const d = new Date(); d.setFullYear(d.getFullYear() - 3); return d.toISOString().slice(0, 10)
    }
    return null
  }

  const getAvg = useCallback(async (timeRange = globalTimeRange) => {
    const companyId = effectiveCompanyId
    if (!companyId) return
    try {
      const startDate = getStartDate(timeRange)
      const url = startDate
        ? `${API_URL}/companies/${companyId}/ratings?start_date=${startDate}`
        : `${API_URL}/companies/${companyId}/ratings`
      const res = await fetch(url)
      if (!res.ok) throw new Error()
      setData(await res.json())
    } catch { setData(null) }
  }, [effectiveCompanyId, globalTimeRange])

  // Trend der Gesamtnote (D1, 2026-10-09): letzte 12 (bei „3 Jahre“ 36) volle
  // Kalendermonate bis zum letzten vollen Monat mit Bewertungen gegen dieselbe Zahl
  // Monate davor, n je Fenster (Modus score_months). Kein Rückfall auf die
  // Kategorien-Modi, damit die Kachel immer dieselbe Basis wie der Ø Score hat.
  const getTrend = useCallback(async (timeRange = globalTimeRange) => {
    const companyId = effectiveCompanyId
    if (!companyId) return
    const months = timeRange === "3y" ? 36 : 12
    try {
      const res = await fetch(`${API_URL}/companies/${companyId}/ratings/trend?mode=score_months&months=${months}`)
      if (!res.ok) throw new Error()
      const json = await res.json()
      const delta = Number(json.difference)
      if (json.difference == null || !Number.isFinite(delta)) {
        setTrendData(json.anchor ? { avgDelta: null, sign: null, windowMonths: json.months ?? months, nReviews: json.n_reviews ?? null, raw: json } : null)
        return
      }
      setTrendData({ avgDelta: delta.toFixed(2), sign: json.sign ?? "flat", windowMonths: json.months ?? months, nReviews: json.n_reviews ?? null, raw: json })
    } catch { setTrendData(null) }
  }, [effectiveCompanyId, globalTimeRange])

  // Rollierende Schnitte (FA-08): unabhängig vom Zeitfilter, Anker ist der letzte volle Monat mit Daten.
  const getRolling = useCallback(async () => {
    const companyId = effectiveCompanyId
    if (!companyId) return
    try {
      const res = await fetch(`${API_URL}/companies/${companyId}/ratings/trend?mode=rolling`)
      if (!res.ok) throw new Error()
      setRollingData(await res.json())
    } catch { setRollingData(null) }
  }, [effectiveCompanyId])

  const getMostCritical = useCallback(async (timeRange = globalTimeRange) => {
    const companyId = effectiveCompanyId
    if (!companyId) return
    try {
      const startDate = getStartDate(timeRange)
      const url = startDate
        ? `${API_URL}/companies/${companyId}/ratings/avg?start_date=${startDate}`
        : `${API_URL}/companies/${companyId}/ratings/avg`
      const res = await fetch(url)
      if (!res.ok) throw new Error()
      const json = await res.json()
      const labelMap = {
        avg_arbeitsatmosphaere:      "Arbeitsatmosphäre",
        avg_image:                   "Image",
        avg_work_life_balance:       "Work-Life-Balance",
        avg_karriere_weiterbildung:  "Karriere/Weiterbildung",
        avg_gehalt_sozialleistungen: "Gehalt/Sozialleistungen",
        avg_kollegenzusammenhalt:    "Kollegenzusammenhalt",
        avg_umwelt_sozialbewusstsein:"Umwelt-/Sozialbewusstsein",
        avg_vorgesetztenverhalten:   "Vorgesetztenverhalten",
        avg_kommunikation:           "Kommunikation",
        avg_interessante_aufgaben:   "Interessante Aufgaben",
        avg_umgang_aelteren_kollegen:"Umgang mit älteren Kollegen",
        avg_arbeitsbedingungen:      "Arbeitsbedingungen",
        avg_gleichberechtigung:      "Gleichberechtigung",
      }
      const entries = Object.entries(json)
        .map(([k, v]) => ({ key: k, title: labelMap[k] ?? k, score: Number(v) }))
        .filter((x) => Number.isFinite(x.score))
      if (!entries.length) { setMostCriticalData(null); return }
      const min = entries.reduce((b, c) => (c.score < b.score ? c : b), entries[0])
      // n der Kategorie (FA-26): Zähler je Kategorie über alle Mitarbeitenden-Bewertungen;
      // mit Zeitfilter nicht je Zeitraum verfügbar, dann ohne n.
      let n = null
      if (!startDate) {
        try {
          const countsRes = await fetch(`${API_URL}/companies/${companyId}/ratings/category-counts`)
          if (countsRes.ok) {
            const counts = await countsRes.json()
            n = Number.isFinite(Number(counts?.[min.key])) ? Number(counts[min.key]) : null
          }
        } catch { /* n bleibt leer */ }
      }
      setMostCriticalData({ topicName: min.title, score: min.score.toFixed(2), n })
    } catch { setMostCriticalData(null) }
  }, [effectiveCompanyId, globalTimeRange])

  const getNegativeTopic = useCallback(async (timeRange = globalTimeRange) => {
    const companyId = effectiveCompanyId
    if (!companyId) return
    const startDate = getStartDate(timeRange)

    const normSent  = (s) => String(s || "").toLowerCase()
    const isNeg = (t) => normSent(t?.sentiment).includes("neg")
    const isNeu = (t) => normSent(t?.sentiment).includes("neu")
    const isPos = (t) => normSent(t?.sentiment).includes("pos")
    const hasNone = (t) => !normSent(t?.sentiment)
    const ratingOf = (t) => { const r = Number(t?.avgRating); return Number.isFinite(r) ? r : NaN }
    const freqOf   = (t) => { const f = Number(t?.frequency); return Number.isFinite(f) ? f : 0 }
    const impactOf = (t) => { const f = Math.max(0, freqOf(t)); const r = ratingOf(t); return Number.isFinite(r) ? f * Math.max(0, 5 - r) : 0 }

    const pickFromTopics = (topics) => {
      if (!topics.length) return null
      const neg = topics.filter(isNeg), neu = topics.filter(isNeu), none = topics.filter(hasNone)
      const pool = neg.length ? neg : (neu.length ? neu : (none.length ? none : topics.filter((t) => !isPos(t))))
      const rPool = pool.filter((t) => Number.isFinite(ratingOf(t)))
      const base = rPool.length ? rPool : pool
      const chosen = base.reduce((best, cur) => {
        const bi = impactOf(best), ci = impactOf(cur)
        if (ci > bi) return cur; if (ci < bi) return best
        const br = ratingOf(best), cr = ratingOf(cur)
        if (Number.isFinite(br) && Number.isFinite(cr)) { if (cr < br) return cur; if (cr > br) return best }
        return freqOf(cur) > freqOf(best) ? cur : best
      }, base[0])
      return { ...chosen, title: "Negative Topic", topic_label: chosen?.topic, categories: chosen?.topic ? [chosen.topic] : chosen?.categories }
    }

    try {
      // ML-based endpoint has no date filter — only use it for "all"
      if (!startDate) {
        const res = await fetch(`${API_URL}/topics/company/${companyId}/negative-topics`)
        if (res.ok) {
          const json = await res.json()
          const list = json?.negative_topics || []
          if (Array.isArray(list) && list.length) {
            const mentionsOf = (t) => { const n = Number(t?.mention_count); return Number.isFinite(n) ? n : 0 }
            const rOf        = (t) => { const r = Number(t?.avg_rating);    return Number.isFinite(r) ? r : NaN }
            const iOf        = (t) => { const n = Math.max(0, mentionsOf(t)); const r = rOf(t); return Number.isFinite(r) ? n * Math.max(0, 5 - r) : 0 }
            const chosen = list.reduce((best, cur) => {
              const bi = iOf(best), ci = iOf(cur)
              if (ci > bi) return cur; if (ci < bi) return best
              const br = rOf(best), cr = rOf(cur)
              if (Number.isFinite(br) && Number.isFinite(cr)) { if (cr < br) return cur; if (cr > br) return best }
              return mentionsOf(cur) > mentionsOf(best) ? cur : best
            }, list[0])
            setNegativeTopicItem({
              ...chosen,
              title: "Negative Topic",
              topic_label: chosen?.topic_label || chosen?.topic || chosen?.topic_text,
              categories: Array.isArray(chosen?.categories) ? chosen.categories : (chosen?.topic_label ? [chosen.topic_label] : []),
            })
            return
          }
        }
      }

      const fallbackUrl = startDate
        ? `${API_URL}/analytics/company/${companyId}/topic-overview?start_date=${startDate}`
        : `${API_URL}/analytics/company/${companyId}/topic-overview`
      // Gemeinsamer Abruf mit der Themenkarte (dieselbe Adresse, lib/sharedFetch.js).
      const fallbackJson = await fetchJsonShared(fallbackUrl)
      const topics = Array.isArray(fallbackJson?.topics) ? fallbackJson.topics : []
      setNegativeTopicItem(pickFromTopics(topics))
    } catch { setNegativeTopicItem(null) }
  }, [effectiveCompanyId, globalTimeRange])

  const getNegativeTopicName = (t) => {
    if (!t) return "-"
    if (t.topic_label) return String(t.topic_label)
    if (t.topic_text)  return String(t.topic_text)
    if (t.topic)       return String(t.topic)
    if (Array.isArray(t.topic_words) && t.topic_words.length) return String(t.topic_words[0])
    if (Array.isArray(t.top_words) && t.top_words.length) {
      const w = t.top_words[0]
      if (typeof w === "string") return w
      if (w?.word) return String(w.word)
    }
    if (Array.isArray(t.categories) && t.categories.length) return String(t.categories[0])
    return "-"
  }

  /* ---- PDF export ---- */
  // Übernimmt alle Elemente des Dashboards: Datenstand, fünf Kennzahlen mit n und
  // Datenbasis, Timeline, Topics im Detail, Anomalien im Verlauf, Topic-Übersicht.
  const handleExportPDF = async () => {
    if (!selectedCompanyName) { setError("Bitte wählen Sie zuerst eine Firma aus."); return }
    try {
      setExportingPDF(true); setError(null)
      const checkIfReady = () => {
        const s = loadingStatesRef.current
        return !s.timelineChart && !s.topicRatingChart && !s.topicOverview && !s.kpiCards && !s.anomalyChart
      }
      if (!checkIfReady()) {
        const maxWait = 45000, interval = 300, start = Date.now()
        await new Promise((resolve, reject) => {
          const t = setInterval(() => {
            if (Date.now() - start > maxWait) { clearInterval(t); reject(new Error("Timeout")); return }
            if (checkIfReady()) { clearInterval(t); resolve() }
          }, interval)
        })
      }
      const chartIds = ["timeline-chart-export", "topic-rating-chart-export"]
      const chartResults = await waitForMultipleCharts(chartIds, 15000)
      if (!chartResults.allReady) await new Promise((r) => setTimeout(r, 3000))
      const timelineEl    = document.getElementById("timeline-chart-export")
      const topicRatingEl = document.getElementById("topic-rating-chart-export")
      // Fehlt ein Diagramm (z. B. keine Daten im gewählten Zeitraum), zeigt die Karte im
      // Dashboard einen Text; das PDF übernimmt diesen Zustand statt abzubrechen.
      const tv = validateChart(timelineEl, "Timeline")
      const rv = validateChart(topicRatingEl, "Topic-Rating")
      if (!tv.isValid) console.warn("PDF-Export ohne Timeline-Diagramm:", tv.message)
      if (!rv.isValid) console.warn("PDF-Export ohne Topic-Rating-Diagramm:", rv.message)
      await waitForImagesInElement(timelineEl, 3000)
      await waitForImagesInElement(topicRatingEl, 3000)
      // Anomalien-Diagramm: nur prüfen, wenn die Reihe Monate hat (sonst zeigt die
      // Karte einen Text statt eines Diagramms); ein fehlendes Diagramm bricht den
      // Export nicht ab, die Seite nennt dann den Grund.
      let anomalyEl = null
      if (anomalyExportData?.monthsInSpan > 0) {
        const anomalyReady = await waitForChartReady("anomaly-chart-export", 8000)
        anomalyEl = anomalyReady.success ? anomalyReady.element : null
      }
      // Datenstand (dieselbe Antwort wie die Leiste, aus dem Zwischenspeicher)
      const dataStatus = await loadDataStatus(effectiveCompanyId).catch(() => null)
      const company = companies.find((c) => String(c.id) === String(effectiveCompanyId))
      await new Promise((r) => setTimeout(r, 1500))
      await exportKPIsAsPDF({
        companyName: selectedCompanyName,
        reviewCount: company?.review_count ?? null,
        timeRange: globalTimeRange,
        lastImportLocal: importHistory[0]?.timestamp ?? null,
        dataStatus,
        avgScore: data?.score ?? "-",
        avgCount: data?.score_n ?? null,
        categoryMean: data?.avg_overall ?? null,
        trend: trendData,
        rolling: rollingData,
        mostCritical: mostCriticalData,
        negativeTopic: getNegativeTopicName(negativeTopicItem),
        negativeTopicItem,
        timelineChartElement: tv.isValid ? timelineEl : null,
        timelineFilters,
        topicRatingChartElement: rv.isValid ? topicRatingEl : null,
        topicRatingFilters,
        anomalyChartElement: anomalyEl,
        anomalyData: anomalyExportData,
        topicOverviewData,
      })
    } catch (err) {
      setError(`Export fehlgeschlagen: ${err.message}`)
    } finally {
      setExportingPDF(false)
    }
  }

  /* ---- Effects ---- */
  // Gemeinsame Firmenliste (lib/companies.js), dieselbe wie im Suchfeld.
  useEffect(() => {
    loadCompanies().then(setCompanies).catch(() => { /* Firmenliste bleibt leer; die Suche zeigt dann keine Vorschläge */ })
  }, [])

  useEffect(() => {
    if (!kpiKey) return undefined
    let active = true
    const load = async () => {
      await Promise.allSettled([getAvg(globalTimeRange), getTrend(globalTimeRange), getRolling(), getMostCritical(globalTimeRange), getNegativeTopic(globalTimeRange)])
      if (active) setKpiDoneKey(kpiKey)
    }
    load()
    return () => { active = false }
  }, [kpiKey, globalTimeRange, getAvg, getTrend, getRolling, getMostCritical, getNegativeTopic])

  const handleImportSuccess = useCallback(() => {
    invalidateDataStatus(effectiveCompanyId)
    Promise.allSettled([getAvg(), getTrend(), getRolling(), getMostCritical(), getNegativeTopic()])
      .then(() => setKpiDoneKey(kpiKey))
  }, [effectiveCompanyId, kpiKey, getAvg, getTrend, getRolling, getMostCritical, getNegativeTopic])

  const handleTimelineFiltersChange     = useCallback((f) => setTimelineFilters(f), [])
  const handleTimelineLoadingChange     = useCallback((v) => setDashboardLoadingStates((p) => ({ ...p, timelineChart: v })), [])
  const handleTopicRatingFiltersChange  = useCallback((f) => setTopicRatingFilters(f), [])
  const handleTopicRatingLoadingChange  = useCallback((v) => setDashboardLoadingStates((p) => ({ ...p, topicRatingChart: v })), [])
  const handleTopicOverviewDataChange   = useCallback((d) => setTopicOverviewData(d), [])
  const handleTopicOverviewLoadingChange = useCallback((v) => setDashboardLoadingStates((p) => ({ ...p, topicOverview: v })), [])
  const handleAnomalyDataChange         = useCallback((d) => setAnomalyExportData(d), [])
  const handleAnomalyLoadingChange      = useCallback((v) => setDashboardLoadingStates((p) => ({ ...p, anomalyChart: v })), [])

  /* ---- Anomalien-Detailseite (analog zum Vergleich) ---- */
  // selection: {source, dimension, status} von der AnomalyCard; beim Klick auf den Topbar-Knopf ein Event.
  const openAnomalies = useCallback((selection) => {
    if (!effectiveCompanyId) return
    const params = new URLSearchParams({ company: String(effectiveCompanyId) })
    const { source, dimension, status } = selection && typeof selection === "object" && "dimension" in selection ? selection : {}
    if (source && source !== "employee") params.set("source", source)
    if (typeof dimension === "string" && dimension !== "durchschnittsbewertung") params.set("dimension", dimension)
    if (status) params.set("status", status)
    navigate(`/anomalies?${params}`, {
      state: { company: { id: effectiveCompanyId, name: selectedCompanyName } },
    })
  }, [effectiveCompanyId, selectedCompanyName, navigate])

  /* ---- Aktien-Dashboard (Inkrement 3, E16) ---- */
  const openStock = useCallback(() => {
    if (!effectiveCompanyId) return
    navigate(`/aktie?company=${effectiveCompanyId}`, {
      state: { company: { id: effectiveCompanyId, name: selectedCompanyName } },
    })
  }, [effectiveCompanyId, selectedCompanyName, navigate])

  /* ---- Theme ---- */
  const { isDark, toggle: toggleTheme } = useTheme()

  /* ================================================================
     RENDER
     ================================================================ */
  return (
    <>
      <div className="ds-app">

        {/* ---- RAIL ---- */}
        <aside className="ds-rail">
          {/* Brand */}
          <div className="ds-brand">
            <WorkPulseLogo variant="badge" />
          </div>

          {/* Analyse group */}
          <div className="ds-nav-group">
            <span className="ds-nav-group-label">Analyse</span>
            <button className="ds-nav-link active">
              <DashboardIcon />
              Dashboard
            </button>
            <button
              className="ds-nav-link"
              onClick={() => navigate("/compare", {
                state: { companies: selectedCompanyId && selectedCompanyName ? [{ id: selectedCompanyId, name: selectedCompanyName }] : [] }
              })}
            >
              <Compare />
              Vergleich
            </button>
            <button
              className="ds-nav-link"
              onClick={openAnomalies}
              disabled={!effectiveCompanyId}
              title={effectiveCompanyId ? "Anomalien im Verlauf" : "Erst eine Firma auswählen"}
            >
              <AnomalyIcon />
              Anomalien
            </button>
            <button
              className="ds-nav-link"
              onClick={openStock}
              disabled={!effectiveCompanyId}
              title={effectiveCompanyId
                ? (SHOW_FINANCE_EXTRAS ? "Aktienkurs, Empfehlungen, Umsatz und Nachrichten" : "Aktienkurs und Kennzahlen")
                : "Erst eine Firma auswählen"}
            >
              <TrendUp />
              Aktie
            </button>
          </div>

          {/* Daten group */}
          <div className="ds-nav-group">
            <span className="ds-nav-group-label">Daten</span>
            <button className="ds-nav-link" onClick={() => navigate("/welcome")}>
              <Building />
              Firmen
              {companies.length > 0 && (
                <span className="ds-nav-count">{companies.length}</span>
              )}
            </button>
            <button
              className="ds-nav-link"
              onClick={() => setOpenImport(true)}
              disabled={!effectiveCompanyId}
              title={effectiveCompanyId ? "Daten importieren" : "Erst eine Firma auswählen"}
            >
              <Upload style={{ width: 16, height: 16 }} />
              Importieren
            </button>
          </div>

          {/* Bottom actions */}
          <div className="ds-nav-group" style={{ marginTop: "auto" }}>
            <span className="ds-nav-group-label">Aktionen</span>
            <button className="ds-nav-link" onClick={() => navigate("/welcome")}>
              <Home />
              Startseite
            </button>
            <button
              className="ds-nav-link"
              onClick={handleExportPDF}
              disabled={exportingPDF || !effectiveCompanyId}
            >
              {exportingPDF ? <Loader /> : <Download />}
              {exportingPDF ? "Exportiere…" : "PDF Export"}
            </button>
            <button
              className="ds-nav-link"
              onClick={toggleTheme}
              title={isDark ? "Zu Hell wechseln" : "Zu Dunkel wechseln"}
            >
              {isDark ? <Sun /> : <Moon />}
              {isDark ? "Hell" : "Dunkel"}
            </button>
          </div>
        </aside>

        {/* ---- MAIN ---- */}
        <div style={{ display: "flex", flexDirection: "column", overflow: "hidden", background: "var(--slate-0)" }}>

          {/* TOPBAR */}
          <div className="ds-topbar">
            {/* Breadcrumbs */}
            <div className="ds-crumbs">
              <span>Firmen</span>
              {selectedCompanyName && (
                <>
                  <span className="sep">/</span>
                  <span className="cur">{selectedCompanyName}</span>
                </>
              )}
            </div>

            {/* Company search */}
            <div className="ds-topbar-search">
              <Search className="ds-topbar-search-icon" width="13" height="13" />
              <CompanySearchSelect
                value={companyQuery}
                compact
                placeholder={selectedCompanyName ? "Firma wechseln…" : "Firma suchen…"}
                onValueChange={(val) => {
                  setCompanyQuery(val)
                  if (!val) {
                    setSelectedCompanyId(null)
                    setSelectedCompanyName("")
                    setSelectedCompany("")
                    clearKpis()
                  }
                }}
                onCompanySelect={handleCompanySelectFromDropdown}
                onCreateNew={handleCreateNewCompany}
              />
            </div>

            {/* Global time range filter */}
            <div className="ds-topbar-actions">
              {error && (
                <span style={{ fontSize: 12, color: "var(--rose-700)", maxWidth: 240 }} className="truncate">
                  {error}
                </span>
              )}
              <div className="ds-time-filter">
                {[
                  { value: "all", label: "Standard" },
                  { value: "1y",  label: "1 Jahr" },
                  { value: "3y",  label: "3 Jahre" },
                ].map(({ value, label }) => (
                  <button
                    key={value}
                    className={`ds-time-btn${globalTimeRange === value ? " active" : ""}`}
                    onClick={() => setGlobalTimeRange(value)}
                  >
                    {label}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* CONTENT */}
          <div className="ds-content">

            {/* Page heading */}
            {selectedCompanyName && (
              <div style={{ marginBottom: 24 }}>
                <div style={{ display: "flex", alignItems: "baseline", gap: 10, flexWrap: "wrap" }}>
                  <h1 style={{ margin: 0, font: "600 24px/30px var(--font-sans)", letterSpacing: "-0.015em", color: "var(--color-fg)" }}>
                    {selectedCompanyName}
                  </h1>
                  {(() => {
                    const cid = effectiveCompanyId
                    const co = companies.find(c => String(c.id) === String(cid))
                    return co?.review_count != null ? (
                      <span style={{ font: "400 13px/1 var(--font-sans)", color: "var(--color-fg-muted)" }}>
                        {co.review_count} Bewertungen
                      </span>
                    ) : null
                  })()}
                </div>
                <div style={{ display: "flex", alignItems: "center", gap: 16, marginTop: 4, flexWrap: "wrap" }}>
                  <p style={{ margin: 0, font: "400 13px/1.5 var(--font-sans)", color: "var(--color-fg-muted)" }}>
                    Übersicht aller Bewertungen, Topics und Trends.
                  </p>
                  {importHistory.length > 0 && (
                    <span
                      style={{
                        display: "inline-flex", alignItems: "center", gap: 4,
                        font: "400 11px/1 var(--font-sans)", color: "var(--color-fg-subtle)",
                        padding: "3px 8px", borderRadius: "var(--radius-full)",
                        border: "1px solid var(--color-border)", background: "var(--slate-50)",
                      }}
                      title={`Import-Verlauf: ${importHistory.length} Einträge`}
                    >
                      <Clock style={{ width: 10, height: 10 }} />
                      Letzter Import:{" "}
                      {new Date(importHistory[0].timestamp).toLocaleString("de-DE", {
                        day: "2-digit", month: "2-digit", year: "numeric",
                        hour: "2-digit", minute: "2-digit",
                      })}
                    </span>
                  )}
                </div>
              </div>
            )}

            {/* Datenstand (Inkrement 6, FA-37) */}
            {effectiveCompanyId && <DataStatusBar companyId={effectiveCompanyId} className="mb-4" />}

            {/* Error banner */}
            {error && <div className="ds-error">{error}</div>}

            {/* KPI section heading */}
            <div style={{ display: "flex", alignItems: "baseline", justifyContent: "space-between", marginBottom: 12 }}>
              <h2 style={{ margin: 0, font: "600 14px/20px var(--font-sans)", color: "var(--color-fg)" }}>Kennzahlen</h2>
              <span style={{ font: "400 12px/1 var(--font-sans)", color: "var(--color-fg-subtle)" }}>
                Karte anklicken öffnet Detailansicht
              </span>
            </div>

            {/* KPI Grid (expandable cards) */}
            <div style={{ marginBottom: 20 }}>
              <KPIGrid
                companyId={effectiveCompanyId}
                avgScore={data?.score ?? null}
                avgCount={data?.score_n ?? null}
                trendData={trendData}
                rollingData={rollingData}
                mostCriticalData={mostCriticalData}
                negativeTopicItem={negativeTopicItem}
                getNegativeTopicName={getNegativeTopicName}
                onOpenScore={() => setOpen(true)}
                onOpenTrend={() => setOpenTrend(true)}
                onOpenRolling={() => setOpenRolling(true)}
                onOpenCritical={() => setOpenMostCritical(true)}
                onOpenNegative={() => setOpenNegative(true)}
                topicOverviewRef={topicOverviewRef}
              />
            </div>

            {/* Charts row */}
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, marginBottom: 16 }}>
              <TimelineCard
                companyId={selectedCompany || selectedCompanyId}
                onFiltersChange={handleTimelineFiltersChange}
                onLoadingChange={handleTimelineLoadingChange}
                globalTimeRange={globalTimeRange}
              />
              <TopicRatingCard
                companyId={selectedCompany || selectedCompanyId}
                onFiltersChange={handleTopicRatingFiltersChange}
                onLoadingChange={handleTopicRatingLoadingChange}
                globalTimeRange={globalTimeRange}
              />
            </div>

            {/* Anomalies (Inkrement 1) */}
            <div style={{ marginBottom: 16 }}>
              <AnomalyCard
                companyId={selectedCompany || selectedCompanyId}
                onOpen={openAnomalies}
                onDataChange={handleAnomalyDataChange}
                onLoadingChange={handleAnomalyLoadingChange}
              />
            </div>

            {/* Topic overview */}
            <TopicOverviewCard
              ref={topicOverviewRef}
              companyId={selectedCompany || selectedCompanyId}
              onDataChange={handleTopicOverviewDataChange}
              onLoadingChange={handleTopicOverviewLoadingChange}
              globalTimeRange={globalTimeRange}
            />

          </div>
        </div>
      </div>

      {/* ---- Modals ---- */}
      <SorceModal
        open={open}
        onOpenChange={setOpen}
        companyId={effectiveCompanyId}
        scoreData={data}
        startDate={getStartDate(globalTimeRange)}
      />

      <TrendModal
        open={openTrend}
        onOpenChange={setOpenTrend}
        companyId={effectiveCompanyId}
        scoreTrend={trendData?.raw ?? null}
      />

      <RollingModal
        open={openRolling}
        onOpenChange={setOpenRolling}
        data={rollingData}
        companyName={selectedCompanyName}
      />

      <MostCriticalModal
        open={openMostCritical}
        onOpenChange={setOpenMostCritical}
        companyId={effectiveCompanyId}
      />

      <NegativTopicModal
        open={openNegative}
        onOpenChange={setOpenNegative}
        companyId={effectiveCompanyId}
        topic={negativeTopicItem}
      />

      <ImportModal
        open={openImport}
        onOpenChange={setOpenImport}
        companyId={effectiveCompanyId}
        companyName={selectedCompanyName}
        onImportSuccess={handleImportSuccess}
      />
    </>
  )
}
