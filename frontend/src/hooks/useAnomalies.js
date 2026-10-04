import { useEffect, useMemo, useState } from "react"
import { API_URL } from "../config"

/* Lädt Monatsreihe und auffällige Veränderungen eines Unternehmens
 * (GET /analytics/company/{id}/anomalies). Ergebnis je Anfrage-Schlüssel;
 * "loading" gilt, solange der Schlüssel des Ergebnisses nicht passt. */
export function useAnomalies(companyId, { source = "employee", dimension = "durchschnittsbewertung", status = null } = {}) {
  const requestKey = companyId ? `${companyId}:${source}:${dimension}:${status ?? ""}` : null
  const [result, setResult] = useState({ key: null, data: null, error: "" })

  useEffect(() => {
    if (!requestKey) return undefined
    const controller = new AbortController()
    const params = new URLSearchParams({ source, dimension })
    if (status) params.set("status", status)
    fetch(`${API_URL}/analytics/company/${companyId}/anomalies?${params}`, { signal: controller.signal })
      .then(async (res) => {
        const json = await res.json().catch(() => ({}))
        if (!res.ok) throw new Error(typeof json.detail === "string" ? json.detail : `HTTP ${res.status}`)
        setResult({ key: requestKey, data: json, error: "" })
      })
      .catch((e) => {
        if (e.name !== "AbortError") setResult({ key: requestKey, data: null, error: e.message })
      })
    return () => controller.abort()
  }, [companyId, source, dimension, status, requestKey])

  const current = result.key === requestKey ? result : null
  const data = current?.data ?? null
  const anomalies = useMemo(() => data?.anomalies ?? [], [data])

  return {
    loading: Boolean(requestKey) && !current,
    error: current?.error ?? "",
    data,
    anomalies,
  }
}
