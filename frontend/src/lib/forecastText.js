/* Formatierung der Prognose-Kenngrößen (forecast_info, 2026-10-13), gemeinsam für
 * ForecastExplanation und die Kacheln im Detailfenster des Zeitverlaufs. */

const MONTHS = ["Jan", "Feb", "Mär", "Apr", "Mai", "Jun", "Jul", "Aug", "Sep", "Okt", "Nov", "Dez"]

export const fmtDe = (v, d = 2) => (v == null || !Number.isFinite(Number(v)) ? "–" : Number(v).toFixed(d).replace(".", ","))
export const fmtSigned = (v, d = 3) => (v == null ? "–" : `${Number(v) >= 0 ? "+" : "−"}${fmtDe(Math.abs(Number(v)), d)}`)

/* "2025-07" → "Jul 2025" */
export const fmtMonthKey = (key) => {
  const [y, m] = String(key ?? "").split("-").map(Number)
  return y && m ? `${MONTHS[m - 1]} ${y}` : "–"
}
