import { useCallback, useEffect, useMemo, useRef, useState } from "react"
import { API_URL } from "../config"
import { NO_CATEGORY } from "../lib/evidenceText"

export const EVIDENCE_PAGE_SIZE = 25
/* Seitengröße beim Laden aller Belege (Sortierung nach Relevanz, Filter nach Ereignisart; Inkrement 5);
 * entspricht MAX_LIMIT der Route. */
export const EVIDENCE_ALL_PAGE_SIZE = 200
/* Dauert die erste Seite länger als so viele Millisekunden, werden Monate zum ersten Mal von
 * den Quellen geladen (ein Abruf je Quelle und Monat mit 2 s Abstand); aus dem Speicher
 * antwortet die Route in Bruchteilen einer Sekunde. Dann zeigt der Abschnitt den Hinweis. */
export const FIRST_FETCH_HINT_MS = 2000

/* Lädt die externen Belege im Ereignisfenster seitenweise (Inkrement 4):
 * GET /analytics/company/{id}/anomalies/{anomalyId}/context für eine Veränderung
 * oder einen Einzelmonat, GET /analytics/company/{id}/context?from=&to= für eine
 * freie Auswahl. Die erste Seite kommt beim Wechsel der Auswahl, weitere mit
 * loadMore; loadAll holt alle restlichen Seiten (für Sortierung und Filter der
 * Belegliste, Inkrement 5). Ergebnis je Anfrage-Schlüssel, wie in useReviewPages.
 * `slow` ist wahr, solange die erste Seite länger als FIRST_FETCH_HINT_MS braucht.
 * dimensionOnly (2026-10-23, Dimension als globaler Filter): mit einer Einzeldimension
 * nur Belege, die zur Dimension gehören (dimension_only=true, auch für die freie
 * Auswahl mit source und dimension); jeder Beleg trägt dann `dimension_match`, die
 * Antwort `scope`. */
export function useEvidence(companyId, { anomalyId = null, selection = null, source = "employee", dimension = null, status = null, dimensionOnly = false } = {}) {
  const anchorKey = anomalyId ? `a:${anomalyId}` : selection?.from && selection?.to ? `s:${selection.from}:${selection.to}` : null
  const scoped = Boolean(dimension) && dimensionOnly
  const requestKey = companyId && anchorKey ? `${companyId}:${anchorKey}:${source}:${dimension ?? ""}:${status ?? ""}:${scoped}` : null
  const [result, setResult] = useState({ key: null, data: null, items: [], total: 0, error: "", loadingMore: false, loadingAll: false })
  const [slowKey, setSlowKey] = useState(null)
  const controllerRef = useRef(null)

  const fetchPage = useCallback(
    (offset, signal, limit = EVIDENCE_PAGE_SIZE) => {
      const params = new URLSearchParams({ offset: String(offset), limit: String(limit) })
      let url
      if (anomalyId) {
        params.set("source", source)
        if (dimension) params.set("dimension", dimension)
        if (status) params.set("status", status)
        if (scoped) params.set("dimension_only", "true")
        url = `${API_URL}/analytics/company/${companyId}/anomalies/${encodeURIComponent(anomalyId)}/context?${params}`
      } else {
        params.set("from", selection.from)
        params.set("to", selection.to)
        if (scoped) {
          params.set("source", source)
          params.set("dimension", dimension)
          params.set("dimension_only", "true")
        }
        url = `${API_URL}/analytics/company/${companyId}/context?${params}`
      }
      return fetch(url, { signal }).then(async (res) => {
        const json = await res.json().catch(() => ({}))
        if (!res.ok) throw new Error(typeof json.detail === "string" ? json.detail : `HTTP ${res.status}`)
        return json
      })
    },
    [companyId, anomalyId, selection, source, dimension, status, scoped],
  )

  useEffect(() => {
    if (!requestKey) return undefined
    const controller = new AbortController()
    controllerRef.current = controller
    fetchPage(0, controller.signal)
      .then((json) => setResult({ key: requestKey, data: json, items: json.items ?? [], total: json.total ?? 0, error: "", loadingMore: false, loadingAll: false }))
      .catch((e) => {
        if (e.name !== "AbortError") setResult({ key: requestKey, data: null, items: [], total: 0, error: e.message, loadingMore: false, loadingAll: false })
      })
    return () => controller.abort()
  }, [requestKey, fetchPage])

  useEffect(() => {
    if (!requestKey) return undefined
    const timer = setTimeout(() => setSlowKey(requestKey), FIRST_FETCH_HINT_MS)
    return () => clearTimeout(timer)
  }, [requestKey])

  const current = result.key === requestKey ? result : null
  const loading = Boolean(requestKey) && !current

  const loadMore = useCallback(() => {
    if (!current || current.loadingMore || current.items.length >= current.total) return
    const signal = controllerRef.current?.signal
    setResult((r) => ({ ...r, loadingMore: true }))
    fetchPage(current.items.length, signal)
      .then((json) => setResult((r) => (r.key === requestKey
        ? { ...r, items: [...r.items, ...(json.items ?? [])], total: json.total ?? r.total, loadingMore: false }
        : r)))
      .catch((e) => {
        if (e.name !== "AbortError") setResult((r) => (r.key === requestKey ? { ...r, loadingMore: false, error: e.message } : r))
      })
  }, [current, fetchPage, requestKey])

  /* Alle restlichen Belege in Seiten von EVIDENCE_ALL_PAGE_SIZE nachladen. */
  const loadAll = useCallback(async () => {
    if (!current || current.loadingMore || current.items.length >= current.total) return
    const signal = controllerRef.current?.signal
    setResult((r) => ({ ...r, loadingMore: true, loadingAll: true }))
    try {
      let items = current.items
      let total = current.total
      while (items.length < total) {
        const json = await fetchPage(items.length, signal, EVIDENCE_ALL_PAGE_SIZE)
        const page = json.items ?? []
        if (!page.length) break
        items = [...items, ...page]
        total = json.total ?? total
      }
      const done = items
      const doneTotal = total
      setResult((r) => (r.key === requestKey ? { ...r, items: done, total: doneTotal, loadingMore: false, loadingAll: false } : r))
    } catch (e) {
      if (e.name !== "AbortError") setResult((r) => (r.key === requestKey ? { ...r, loadingMore: false, loadingAll: false, error: e.message } : r))
    }
  }, [current, fetchPage, requestKey])

  return {
    loading,
    slow: loading && slowKey === requestKey,
    error: current?.error ?? "",
    data: current?.data ?? null,
    items: current?.items ?? [],
    total: current?.total ?? 0,
    hasMore: Boolean(current) && current.items.length < current.total,
    loadingMore: current?.loadingMore ?? false,
    loadingAll: current?.loadingAll ?? false,
    loadMore,
    loadAll,
  }
}

/* Allgemeine Ereignisse (GET /analytics/global-events, Inkrement 4, Schritt 7; seit E29 automatisch aus Wirtschaftsdaten)
 * für das Overlay im Diagramm; enabled=false lädt nichts. Ergebnis: {loading, error, events}. */
export function useGlobalEvents(enabled) {
  const [result, setResult] = useState({ loaded: false, events: [], error: "" })

  useEffect(() => {
    if (!enabled) return undefined
    const controller = new AbortController()
    fetch(`${API_URL}/analytics/global-events`, { signal: controller.signal })
      .then(async (res) => {
        const json = await res.json().catch(() => ({}))
        if (!res.ok) throw new Error(typeof json.detail === "string" ? json.detail : `HTTP ${res.status}`)
        setResult({ loaded: true, events: json.events ?? [], error: "" })
      })
      .catch((e) => {
        if (e.name !== "AbortError") setResult({ loaded: true, events: [], error: e.message })
      })
    return () => controller.abort()
  }, [enabled])

  return { loading: enabled && !result.loaded, error: result.error, events: enabled ? result.events : [] }
}

/* Sortierung und Filter der Belegliste (Inkrement 5). evidence = Rückgabe von
   useEvidence, scores = item_scores aus explanation_summary des Vergleichs (null,
   solange er lädt). Für Sortierung nach Relevanz und Filter müssen alle Belege
   des Fensters geladen sein; das übernimmt der Effekt. Ergebnis: sichtbare
   Belege, Ereignisarten der Auswahl, Hinweis für den Untertitel, needAll. */
export function useEvidenceList(evidence, scores, { sort, category }) {
  const needAll = sort === "relevance" || category !== ""
  useEffect(() => {
    if (needAll && evidence.hasMore && !evidence.loadingMore) evidence.loadAll()
  }, [needAll, evidence])
  const categories = useMemo(() => {
    const found = new Map()
    Object.values(scores ?? {}).forEach((s) => {
      if (s.category && !found.has(s.category)) found.set(s.category, s.category_label ?? s.category)
    })
    return [...found.entries()].map(([id, label]) => ({ id, label })).sort((a, b) => a.label.localeCompare(b.label, "de"))
  }, [scores])
  const items = useMemo(() => {
    let list = evidence.items
    if (category) {
      list = list.filter((item) => {
        const cat = scores?.[item.id]?.category ?? null
        return category === NO_CATEGORY ? cat == null : cat === category
      })
    }
    if (sort === "relevance" && scores) {
      list = [...list].sort((a, b) => (scores[a.id]?.rank ?? Infinity) - (scores[b.id]?.rank ?? Infinity) || String(b.date ?? "").localeCompare(String(a.date ?? "")))
    }
    return list
  }, [evidence.items, category, sort, scores])
  const listNote = [
    sort === "relevance" ? "sortiert nach Relevanz" : null,
    category ? `Ereignisart: ${category === NO_CATEGORY ? "ohne" : categories.find((c) => c.id === category)?.label ?? category} (${items.length} von ${evidence.items.length})` : null,
  ].filter(Boolean).join(" · ")
  return { items, categories, listNote, needAll }
}
