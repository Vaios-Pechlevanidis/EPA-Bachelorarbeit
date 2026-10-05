/* Gemeinsamer Abruf für teure, gleiche GET-Anfragen (Leistung, 2026-10-05).
 *
 * Mehrere Dashboard-Karten fragen dieselbe Adresse gleichzeitig an, z. B.
 * topic-overview (Themenkarte und Kachel "Negativstes Thema") oder
 * topic-ratings-timeseries (Jahre und Daten der Themenkarte). Das Backend
 * rechnet sonst zweimal, und beide Antworten kommen später. Hier teilen sich
 * gleiche Adressen einen Abruf; die Antwort bleibt SHARED_TTL gültig.
 * Jeder Aufrufer bekommt eine eigene Kopie, damit Sortieren o. Ä. die anderen
 * nicht verändert. Nach Upload oder Löschen invalidateSharedFetches() aufrufen. */

export const SHARED_TTL = 30 * 1000

const entries = new Map() // url -> { at, done, promise }

export function fetchJsonShared(url) {
  const hit = entries.get(url)
  if (!hit || (hit.done && Date.now() - hit.at >= SHARED_TTL)) {
    const entry = { at: Date.now(), done: false, promise: null }
    entry.promise = fetch(url)
      .then((res) => {
        if (!res.ok) throw new Error(`API Error: ${res.status}`)
        return res.json()
      })
      .then(
        (json) => {
          entry.done = true
          entry.at = Date.now()
          return json
        },
        (error) => {
          if (entries.get(url) === entry) entries.delete(url) // Fehler nicht zwischenspeichern
          throw error
        },
      )
    entries.set(url, entry)
  }
  return entries.get(url).promise.then((json) => structuredClone(json))
}

export function invalidateSharedFetches() {
  entries.clear()
}
