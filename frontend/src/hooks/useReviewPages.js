import { useCallback, useEffect, useRef, useState } from "react"
import { API_URL } from "../config"

export const REVIEW_PAGE_SIZE = 25

/* Lädt die Bewertungen eines Zeitraums seitenweise
 * (GET /analytics/company/{id}/reviews mit start, end, status, offset und
 * format=full; mit dimension zusätzlich die Fundstellen des zugehörigen
 * Schlüsselwort-Themas). Die erste Seite kommt beim Wechsel des Zeitraums, weitere mit
 * loadMore; so wird nie die ganze Liste auf einmal geladen und gerendert.
 * Ergebnis je Anfrage-Schlüssel, wie in useAnomalies. */
export function useReviewPages(companyId, { source = "employee", status = null, start, end, dimension = null, topicOnly = false } = {}) {
  const requestKey = companyId && start && end ? `${companyId}:${source}:${status ?? ""}:${start}:${end}:${dimension ?? ""}:${topicOnly}` : null
  const [result, setResult] = useState({ key: null, items: [], total: 0, highlight: null, error: "", loadingMore: false })
  const controllerRef = useRef(null)

  const fetchPage = useCallback(
    (offset, signal) => {
      const params = new URLSearchParams({ source, start, end, offset: String(offset), limit: String(REVIEW_PAGE_SIZE), format: "full" })
      if (status) params.set("status", status)
      if (dimension) params.set("dimension", dimension)
      if (dimension && topicOnly) params.set("topic_only", "true")
      return fetch(`${API_URL}/analytics/company/${companyId}/reviews?${params}`, { signal }).then(async (res) => {
        const json = await res.json().catch(() => ({}))
        if (!res.ok) throw new Error(typeof json.detail === "string" ? json.detail : `HTTP ${res.status}`)
        return json
      })
    },
    [companyId, source, status, start, end, dimension, topicOnly],
  )

  useEffect(() => {
    if (!requestKey) return undefined
    const controller = new AbortController()
    controllerRef.current = controller
    fetchPage(0, controller.signal)
      .then((json) => setResult({ key: requestKey, items: json.reviews ?? [], total: json.total ?? 0, highlight: json.highlight ?? null, error: "", loadingMore: false }))
      .catch((e) => {
        if (e.name !== "AbortError") setResult({ key: requestKey, items: [], total: 0, highlight: null, error: e.message, loadingMore: false })
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
        ? { ...r, items: [...r.items, ...(json.reviews ?? [])], total: json.total ?? r.total, loadingMore: false }
        : r)))
      .catch((e) => {
        if (e.name !== "AbortError") setResult((r) => (r.key === requestKey ? { ...r, loadingMore: false, error: e.message } : r))
      })
  }, [current, fetchPage, requestKey])

  return {
    loading: Boolean(requestKey) && !current,
    loadingMore: current?.loadingMore ?? false,
    error: current?.error ?? "",
    items: current?.items ?? [],
    total: current?.total ?? 0,
    // {dimension, topic, mentions}: Thema der Dimension und wie viele Bewertungen des Zeitraums es nennen
    highlight: current?.highlight ?? null,
    hasMore: Boolean(current) && current.items.length < current.total,
    loadMore,
  }
}
