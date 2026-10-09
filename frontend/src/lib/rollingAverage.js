/* Hilfsfunktionen für die rollierenden Schnitte über 12 und 24 Monate
 * (Inkrement 6, FA-08; Daten: GET /companies/{id}/ratings/trend?mode=rolling).
 * Nur Darstellung: Die Texte beschreiben die Lage der beiden Mittel zueinander
 * im Datensatz, keine Prognose und keine Aussage über Ursachen. */

export const ROLLING_FLAT_EPS = 0.05

const num = (v, digits = 2) =>
  v == null ? "–" : Number(v).toLocaleString("de-DE", { minimumFractionDigits: digits, maximumFractionDigits: digits })

/* Monat "YYYY-MM" als "Juli 2025". */
export function fmtRollingMonth(period) {
  if (!period) return "–"
  const [y, m] = String(period).split("-").map(Number)
  return new Date(y, m - 1, 1).toLocaleDateString("de-DE", { month: "short", year: "numeric" })
}

/* Beide Schnitte und die Differenz vorhanden? */
export function rollingReady(data) {
  return Boolean(data?.anchor && data.short?.mean != null && data.long?.mean != null && data.difference != null)
}

/* Satzteil für die Kachel: "liegt 0,19 unter dem 24-Monats-Schnitt". */
export function rollingPhrase(data) {
  if (!rollingReady(data)) return "kein Vergleich möglich"
  const d = num(Math.abs(data.difference))
  if (data.sign === "down") return `liegt ${d} unter dem 24-Monats-Schnitt`
  if (data.sign === "up") return `liegt ${d} über dem 24-Monats-Schnitt`
  return `liegt gleichauf mit dem 24-Monats-Schnitt (Unterschied bis ${num(ROLLING_FLAT_EPS)})`
}

/* Ganzer Satz für das Detailfenster. */
export function rollingSentence(data) {
  if (!rollingReady(data)) return "Kein Vergleich möglich."
  return `Der 12-Monats-Schnitt ${rollingPhrase(data)}.`
}

/* Warnungen bei kleiner Basis und bei weniger als 24 Monaten Daten (feste Schwellen aus der Antwort). */
export function rollingWarnings(data) {
  if (!data?.anchor) return []
  const minReviews = data.low_basis_rule?.min_reviews_per_window ?? 10
  const out = []
  if (data.low_basis) out.push(`kleine Basis: unter ${minReviews} Bewertungen in einem Fenster`)
  if (data.insufficient_history) {
    out.push(`nur ${data.history_months} ${data.history_months === 1 ? "Monat" : "Monate"} Daten, 24-Monats-Fenster unvollständig`)
  }
  return out
}
