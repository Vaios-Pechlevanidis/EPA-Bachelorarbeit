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
