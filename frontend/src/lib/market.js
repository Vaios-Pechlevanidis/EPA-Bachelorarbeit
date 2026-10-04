/* Hilfsfunktionen für Aktienkurs und Kennzahlen (Inkrement 3, E15). Nur
 * Darstellung: Kurs und Kennzahlen sind eine Einordnung, keine Erklärung. */

/* Kurs mit deutschem Zahlformat; ab 1000 ohne Nachkommastellen. */
export function fmtPrice(v) {
  if (v == null) return "–"
  const digits = Math.abs(v) >= 1000 ? 0 : 2
  return Number(v).toLocaleString("de-DE", { minimumFractionDigits: digits, maximumFractionDigits: digits })
}

/* Achsenbeschriftung: ohne überflüssige Nullen (280, 12,5). */
export function fmtPriceTick(v) {
  return v == null ? "" : Number(v).toLocaleString("de-DE", { maximumFractionDigits: 2 })
}

/* Umschalter in der URL: ?kurs=aus blendet den Kurs aus, Standard an. */
export const PRICE_PARAM = "kurs"
export const PRICE_OFF = "aus"

/* Großer Betrag kompakt: "212,3 Mrd. EUR", "4,6 Mio. EUR". */
export function fmtAmount(v, unit) {
  if (v == null) return "–"
  const abs = Math.abs(v)
  const [div, suffix] = abs >= 1e12 ? [1e12, " Bio."] : abs >= 1e9 ? [1e9, " Mrd."] : abs >= 1e6 ? [1e6, " Mio."] : [1, ""]
  const num = (v / div).toLocaleString("de-DE", { maximumFractionDigits: div === 1 ? 0 : 1 })
  return `${num}${suffix}${unit ? ` ${unit}` : ""}`
}

/* Tag "YYYY-MM-DD" als "02.10.2026". */
export function fmtDay(day) {
  if (!day) return "–"
  const [y, m, d] = String(day).split("-")
  return `${d}.${m}.${y}`
}

/* Geschäftsjahr nach seinem Ende: Kalenderjahr "GJ 2025", sonst "GJ bis 03/2026". */
export function fiscalYearLabel(end) {
  const [y, m] = String(end).split("-")
  return m === "12" ? `GJ ${y}` : `GJ bis ${m}/${y}`
}
