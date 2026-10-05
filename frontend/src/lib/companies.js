import { API_URL } from "../config"

/* Gemeinsame Firmenliste (GET /companies) für alle Seiten: Suchfeld,
 * Dashboard, Welcome, Anomalien- und Aktienseite. Die Liste wird einmal
 * geladen und für COMPANIES_TTL im Modul gehalten, auch über Seitenwechsel
 * hinweg; gleichzeitige Anfragen teilen sich denselben Abruf. Nach Upload,
 * Anlegen oder Löschen ruft der Aufrufer invalidateCompanies() auf, damit die
 * Bewertungszahlen neu geladen werden. */

export const COMPANIES_TTL = 5 * 60 * 1000

let cache = null    // { at: Zeitpunkt, data: Liste }
let pending = null  // laufender Abruf

export function cachedCompanies() {
  return cache && Date.now() - cache.at < COMPANIES_TTL ? cache.data : null
}

export function loadCompanies({ force = false } = {}) {
  const cached = force ? null : cachedCompanies()
  if (cached) return Promise.resolve(cached)
  if (pending && !force) return pending
  const request = fetch(`${API_URL}/companies`)
    .then((res) => {
      if (!res.ok) throw new Error(`Firmen konnten nicht geladen werden (HTTP ${res.status})`)
      return res.json()
    })
    .then((data) => {
      const list = Array.isArray(data) ? data : []
      if (pending === request) cache = { at: Date.now(), data: list }
      return list
    })
    .finally(() => {
      if (pending === request) pending = null
    })
  pending = request
  return request
}

export function invalidateCompanies() {
  cache = null
  pending = null
}

/* Eintrag einer Firma aus der Liste (mit ticker, peer_group …) oder null. */
export async function loadCompany(companyId) {
  const list = await loadCompanies()
  return list.find((c) => String(c.id) === String(companyId)) ?? null
}

/* Name einer Firma aus der Liste ("" wenn unbekannt). */
export async function loadCompanyName(companyId) {
  const company = await loadCompany(companyId)
  return company?.name?.trim() ?? ""
}
