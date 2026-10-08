import { useCallback, useEffect, useRef, useState } from "react"
import { API_URL } from "../config"

export const EVIDENCE_PAGE_SIZE = 25

/* Lädt die externen Belege im Ereignisfenster seitenweise (Inkrement 4):
 * GET /analytics/company/{id}/anomalies/{anomalyId}/context für eine Veränderung
 * oder einen Einzelmonat, GET /analytics/company/{id}/context?from=&to= für eine
 * freie Auswahl. Die erste Seite kommt beim Wechsel der Auswahl, weitere mit
 * loadMore. Ergebnis je Anfrage-Schlüssel, wie in useReviewPages. */
export function useEvidence(companyId, { anomalyId = null, selection = null, source = "employee", dimension = null, status = null } = {}) {
  const anchorKey = anomalyId ? `a:${anomalyId}` : selection?.from && selection?.to ? `s:${selection.from}:${selection.to}` : null
  const requestKey = companyId && anchorKey ? `${companyId}:${anchorKey}:${source}:${dimension ?? ""}:${status ?? ""}` : null
  const [result, setResult] = useState({ key: null, data: null, items: [], total: 0, error: "", loadingMore: false })
  const controllerRef = useRef(null)

  const fetchPage = useCallback(
    (offset, signal) => {
      const params = new URLSearchParams({ offset: String(offset), limit: String(EVIDENCE_PAGE_SIZE) })
      let url
      if (anomalyId) {
        params.set("source", source)
        if (dimension) params.set("dimension", dimension)
        if (status) params.set("status", status)
        url = `${API_URL}/analytics/company/${companyId}/anomalies/${encodeURIComponent(anomalyId)}/context?${params}`
      } else {
        params.set("from", selection.from)
        params.set("to", selection.to)
        url = `${API_URL}/analytics/company/${companyId}/context?${params}`
      }
      return fetch(url, { signal }).then(async (res) => {
        const json = await res.json().catch(() => ({}))
        if (!res.ok) throw new Error(typeof json.detail === "string" ? json.detail : `HTTP ${res.status}`)
        return json
      })
    },
    [companyId, anomalyId, selection, source, dimension, status],
  )

  useEffect(() => {
    if (!requestKey) return undefined
    const controller = new AbortController()
    controllerRef.current = controller
    fetchPage(0, controller.signal)
      .then((json) => setResult({ key: requestKey, data: json, items: json.items ?? [], total: json.total ?? 0, error: "", loadingMore: false }))
      .catch((e) => {
        if (e.name !== "AbortError") setResult({ key: requestKey, data: null, items: [], total: 0, error: e.message, loadingMore: false })
      })
    return () => controller.abort()
  }, [requestKey, fetchPage])

  const current = result.key === requestKey ? result : null

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

  return {
    loading: Boolean(requestKey) && !current,
    error: current?.error ?? "",
    data: current?.data ?? null,
    items: current?.items ?? [],
    total: current?.total ?? 0,
    hasMore: Boolean(current) && current.items.length < current.total,
    loadingMore: current?.loadingMore ?? false,
    loadMore,
  }
}

/* Bestätigte allgemeine Ereignisse (GET /analytics/global-events, Inkrement 4, Schritt 7)
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
