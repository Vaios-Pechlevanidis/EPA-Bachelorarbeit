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

/* Umschalter in der URL: Im Aktien-Dashboard ist der Kurs Standard an
   (?kurs=aus blendet ihn aus), auf der Anomalien-Seite Standard aus
   (?kurs=an blendet ihn ein). */
export const PRICE_PARAM = "kurs"
export const PRICE_OFF = "aus"
export const PRICE_ON = "an"

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

/* Fester Hinweis bei Kurs und Kennzahlen (E15), in zwei Teilen für die Hervorhebung. */
export const MARKET_DISCLAIMER_LEAD = "Einordnung, keine Erklärung."
export const MARKET_DISCLAIMER_TEXT = "Der Kurs zeigt das Marktumfeld; ein Zusammenhang mit den Bewertungen wird nicht behauptet."

export const PARENT_SCOPE = "Konzernmutter"

/* Grund ohne Kurs, immer mit "Kein Aktienkurs" am Anfang. */
export function noPriceText(reason) {
  if (!reason) return "Kein Aktienkurs."
  return reason.startsWith("Kein Aktienkurs") ? reason : `Kein Aktienkurs: ${reason}`
}

/* Zeitfenster der Kursansicht im Aktien-Dashboard (Monate, null = alles). */
export const PRICE_RANGES = [
  { key: "1y", label: "1 J.", months: 12 },
  { key: "3y", label: "3 J.", months: 36 },
  { key: "5y", label: "5 J.", months: 60 },
  { key: "10y", label: "10 J.", months: 120 },
  { key: "max", label: "Max.", months: null },
]
export const DEFAULT_PRICE_RANGE = "5y"

export function isPriceRangeKey(key) {
  return PRICE_RANGES.some((r) => r.key === key)
}

/* Die letzten n Monatskurse (n = Monate des Fensters) oder alle. */
export function pricesInRange(prices, rangeKey) {
  const range = PRICE_RANGES.find((r) => r.key === rangeKey)
  const list = prices ?? []
  return range?.months ? list.slice(-range.months) : list
}

/* Empfehlungsstufen in der Reihenfolge von yfinance, mit Farbe (index.css). */
export const RATING_LEVELS = [
  { key: "strong_buy", label: "Stark kaufen", color: "var(--rating-strong-buy)" },
  { key: "buy", label: "Kaufen", color: "var(--rating-buy)" },
  { key: "hold", label: "Halten", color: "var(--rating-hold)" },
  { key: "sell", label: "Verkaufen", color: "var(--rating-sell)" },
  { key: "strong_sell", label: "Stark verkaufen", color: "var(--rating-strong-sell)" },
]

/* Monat "YYYY-MM" als "Okt. 2026". */
export function fmtMonth(period) {
  const [y, m] = String(period).split("-").map(Number)
  return new Date(y, m - 1, 1).toLocaleDateString("de-DE", { month: "short", year: "numeric" })
}

/* Quartal nach seinem Ende: "Q2 2026" (Kalenderquartal des Stichtags). */
export function quarterLabel(end) {
  const [y, m] = String(end).split("-").map(Number)
  return `Q${Math.ceil(m / 3)} ${y}`
}

/* Prozent mit Vorzeichen: "+12,3 %". */
export function fmtPercent(v) {
  if (v == null || !Number.isFinite(v)) return "–"
  const sign = v > 0 ? "+" : v < 0 ? "−" : ""
  return `${sign}${Math.abs(v).toLocaleString("de-DE", { minimumFractionDigits: 1, maximumFractionDigits: 1 })} %`
}
