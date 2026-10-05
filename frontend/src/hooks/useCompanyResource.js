import { useEffect, useState } from "react"
import { API_URL } from "../config"

/* Lädt GET /analytics/company/{id}/{path} (market, finance, news).
 * "loading" gilt, solange das Ergebnis nicht zu Firma und Pfad passt;
 * Fehler kommen als Text aus {"detail": ...} oder als HTTP-Status. */
export function useCompanyResource(companyId, path) {
  const requestKey = companyId ? `${companyId}/${path}` : null
  const [result, setResult] = useState({ key: null, data: null, error: "" })

  useEffect(() => {
    if (!requestKey) return undefined
    const controller = new AbortController()
    fetch(`${API_URL}/analytics/company/${requestKey}`, { signal: controller.signal })
      .then(async (res) => {
        const json = await res.json().catch(() => ({}))
        if (!res.ok) throw new Error(typeof json.detail === "string" ? json.detail : `HTTP ${res.status}`)
        setResult({ key: requestKey, data: json, error: "" })
      })
      .catch((e) => {
        if (e.name !== "AbortError") setResult({ key: requestKey, data: null, error: e.message })
      })
    return () => controller.abort()
  }, [requestKey])

  const current = result.key === requestKey ? result : null
  return {
    loading: Boolean(requestKey) && !current,
    error: current?.error ?? "",
    data: current?.data ?? null,
  }
}
