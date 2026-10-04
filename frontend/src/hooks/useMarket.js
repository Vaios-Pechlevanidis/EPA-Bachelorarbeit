import { useEffect, useState } from "react"
import { API_URL } from "../config"

/* Lädt Aktienkurs und Kennzahlen eines Unternehmens als Einordnung
 * (GET /analytics/company/{id}/market, Inkrement 3, E15). Ohne Ticker oder
 * ohne Kursdaten liefert der Endpunkt available: false mit reason; das ist
 * kein Fehler. "loading" gilt, solange das Ergebnis nicht zur Firma passt. */
export function useMarket(companyId) {
  const requestKey = companyId ? String(companyId) : null
  const [result, setResult] = useState({ key: null, data: null, error: "" })

  useEffect(() => {
    if (!requestKey) return undefined
    const controller = new AbortController()
    fetch(`${API_URL}/analytics/company/${requestKey}/market`, { signal: controller.signal })
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
