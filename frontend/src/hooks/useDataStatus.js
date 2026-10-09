import { useEffect, useState } from "react"
import { API_URL } from "../config"

/* Datenstand eines Unternehmens (GET /companies/{id}/data-status, Inkrement 6,
 * FA-37). Die Antwort ändert sich nur durch einen Import und wird deshalb im
 * Modul je Unternehmen für DATA_STATUS_TTL gehalten, auch über Seitenwechsel
 * hinweg (Dashboard, Anomalien, Aktie zeigen dieselbe Leiste). Nach einem
 * Import ruft der Aufrufer invalidateDataStatus() auf. Ergebnis wie in
 * useCompanyResource: {loading, error, data}. */

export const DATA_STATUS_TTL = 5 * 60 * 1000

const cache = new Map()    // companyId → { at, data }
const pending = new Map()  // companyId → Promise

export function invalidateDataStatus(companyId = null) {
  if (companyId == null) { cache.clear(); pending.clear(); return }
  cache.delete(String(companyId))
  pending.delete(String(companyId))
}

export function loadDataStatus(companyId) {
  const key = String(companyId)
  const cached = cache.get(key)
  if (cached && Date.now() - cached.at < DATA_STATUS_TTL) return Promise.resolve(cached.data)
  if (pending.has(key)) return pending.get(key)
  const request = fetch(`${API_URL}/companies/${key}/data-status`)
    .then(async (res) => {
      const json = await res.json().catch(() => ({}))
      if (!res.ok) throw new Error(typeof json.detail === "string" ? json.detail : `HTTP ${res.status}`)
      cache.set(key, { at: Date.now(), data: json })
      return json
    })
    .finally(() => { if (pending.get(key) === request) pending.delete(key) })
  pending.set(key, request)
  return request
}

export function useDataStatus(companyId) {
  const key = companyId ? String(companyId) : null
  const [result, setResult] = useState({ key: null, data: null, error: "" })

  useEffect(() => {
    if (!key) return undefined
    let active = true
    loadDataStatus(key)
      .then((data) => { if (active) setResult({ key, data, error: "" }) })
      .catch((e) => { if (active) setResult({ key, data: null, error: e.message }) })
    return () => { active = false }
  }, [key])

  const current = result.key === key ? result : null
  return {
    loading: Boolean(key) && !current,
    error: current?.error ?? "",
    data: current?.data ?? null,
  }
}
