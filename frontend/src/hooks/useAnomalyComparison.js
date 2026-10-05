import { useEffect, useState } from "react"
import { API_URL } from "../config"

/* Lädt einen Vorher-Nachher-Vergleich von url; Ergebnis je Anfrage-Schlüssel,
 * wie in useAnomalies. url = null lädt nichts. */
function useComparisonRequest(url) {
  const [result, setResult] = useState({ key: null, data: null, error: "" })

  useEffect(() => {
    if (!url) return undefined
    const controller = new AbortController()
    fetch(url, { signal: controller.signal })
      .then(async (res) => {
        const json = await res.json().catch(() => ({}))
        if (!res.ok) throw new Error(typeof json.detail === "string" ? json.detail : `HTTP ${res.status}`)
        setResult({ key: url, data: json, error: "" })
      })
      .catch((e) => {
        if (e.name !== "AbortError") setResult({ key: url, data: null, error: e.message })
      })
    return () => controller.abort()
  }, [url])

  const current = result.key === url ? result : null
  return {
    loading: Boolean(url) && !current,
    error: current?.error ?? "",
    data: current?.data ?? null,
  }
}

function groupParams({ source = "employee", dimension, status = null }) {
  const params = new URLSearchParams({ source })
  if (dimension) params.set("dimension", dimension)
  if (status) params.set("status", status)
  return params
}

/* Vergleich einer auffälligen Veränderung
 * (GET /analytics/company/{id}/anomalies/{anomalyId}/explanations). */
export function useAnomalyComparison(companyId, anomalyId, options = {}) {
  const url = companyId && anomalyId
    ? `${API_URL}/analytics/company/${companyId}/anomalies/${encodeURIComponent(anomalyId)}/explanations?${groupParams(options)}`
    : null
  return useComparisonRequest(url)
}

/* Vergleich einer frei gewählten Auswahl {from, to} mit dem Zeitraum davor (E17,
 * GET /analytics/company/{id}/compare), auch ohne erkannte Veränderung. */
export function usePeriodComparison(companyId, period, options = {}) {
  let url = null
  if (companyId && period?.from && period?.to) {
    const params = groupParams(options)
    params.set("from", period.from)
    params.set("to", period.to)
    url = `${API_URL}/analytics/company/${companyId}/compare?${params}`
  }
  return useComparisonRequest(url)
}
