import { useCallback, useEffect, useMemo, useState } from "react"
import { API_URL } from "../config"
import { sortUserEvents } from "../lib/userEvents"

/* Eigene Ereignisse eines Unternehmens (2026-10-17, E32):
 * GET/POST /companies/{id}/events, PUT/DELETE /companies/{id}/events/{eventId}.
 * Ergebnis je Unternehmen; nach jeder Änderung wird die Liste lokal
 * fortgeschrieben (sortiert nach Beginn), ohne neu zu laden. add/update/remove
 * geben ein Promise zurück und werfen bei Fehlern mit der Meldung des Backends
 * (deutsch), damit der Dialog sie anzeigen kann. */

async function request(url, options) {
  const res = await fetch(url, { headers: { "Content-Type": "application/json" }, ...options })
  const json = await res.json().catch(() => ({}))
  if (!res.ok) throw new Error(typeof json.detail === "string" ? json.detail : `HTTP ${res.status}`)
  return json
}

export function useUserEvents(companyId) {
  const [result, setResult] = useState({ key: null, events: [], note: "", error: "" })
  const [saving, setSaving] = useState(false)
  const base = companyId ? `${API_URL}/companies/${companyId}/events` : null

  const load = useCallback((signal) => {
    if (!base) return Promise.resolve()
    return request(base, { signal })
      .then((json) => setResult({ key: companyId, events: sortUserEvents(json.events ?? []), note: json.note ?? "", error: "" }))
      .catch((e) => {
        if (e.name !== "AbortError") setResult({ key: companyId, events: [], note: "", error: e.message })
      })
  }, [base, companyId])

  useEffect(() => {
    if (!base) return undefined
    const controller = new AbortController()
    load(controller.signal)
    return () => controller.abort()
  }, [base, load])

  const current = result.key === companyId ? result : null

  const mutate = useCallback(async (fn) => {
    setSaving(true)
    try {
      return await fn()
    } finally {
      setSaving(false)
    }
  }, [])

  const add = useCallback((payload) => mutate(async () => {
    const created = await request(base, { method: "POST", body: JSON.stringify(payload) })
    setResult((r) => (r.key === companyId ? { ...r, events: sortUserEvents([...r.events, created]), error: "" } : r))
    return created
  }), [base, companyId, mutate])

  const update = useCallback((id, payload) => mutate(async () => {
    const updated = await request(`${base}/${id}`, { method: "PUT", body: JSON.stringify(payload) })
    setResult((r) => (r.key === companyId ? { ...r, events: sortUserEvents(r.events.map((e) => (e.id === id ? updated : e))), error: "" } : r))
    return updated
  }), [base, companyId, mutate])

  const remove = useCallback((id) => mutate(async () => {
    await request(`${base}/${id}`, { method: "DELETE" })
    setResult((r) => (r.key === companyId ? { ...r, events: r.events.filter((e) => e.id !== id) } : r))
  }), [base, companyId, mutate])

  const events = useMemo(() => current?.events ?? [], [current])

  return {
    loading: Boolean(base) && !current,
    error: current?.error ?? "",
    note: current?.note ?? "",
    events,
    saving,
    add,
    update,
    remove,
    reload: () => load(),
  }
}
