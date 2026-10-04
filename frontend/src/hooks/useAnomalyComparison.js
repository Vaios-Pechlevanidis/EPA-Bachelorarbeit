import { useEffect, useState } from "react"
import { API_URL } from "../config"

/* Lädt den Vorher-Nachher-Vergleich einer auffälligen Veränderung
 * (GET /analytics/company/{id}/anomalies/{anomalyId}/explanations).
 * Ergebnis je Anfrage-Schlüssel, wie in useAnomalies. */
export function useAnomalyComparison(companyId, anomalyId, { source = "employee", dimension, status = null } = {}) {
  const requestKey = companyId && anomalyId ? `${companyId}:${anomalyId}:${source}:${dimension ?? ""}:${status ?? ""}` : null
  const [result, setResult] = useState({ key: null, data: null, error: "" })

  useEffect(() => {
    if (!requestKey) return undefined
    const controller = new AbortController()
    const params = new URLSearchParams({ source })
    if (dimension) params.set("dimension", dimension)
    if (status) params.set("status", status)
    fetch(`${API_URL}/analytics/company/${companyId}/anomalies/${encodeURIComponent(anomalyId)}/explanations?${params}`, { signal: controller.signal })
      .then(async (res) => {
        const json = await res.json().catch(() => ({}))
        if (!res.ok) throw new Error(typeof json.detail === "string" ? json.detail : `HTTP ${res.status}`)
        setResult({ key: requestKey, data: json, error: "" })
      })
      .catch((e) => {
        if (e.name !== "AbortError") setResult({ key: requestKey, data: null, error: e.message })
      })
    return () => controller.abort()
  }, [companyId, anomalyId, source, dimension, status, requestKey])

  const current = result.key === requestKey ? result : null
  return {
    loading: Boolean(requestKey) && !current,
    error: current?.error ?? "",
    data: current?.data ?? null,
  }
}
