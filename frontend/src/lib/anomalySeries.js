/* Reine Hilfsfunktionen für die Darstellung der Monatsreihe in den
 * Anomalie-Ansichten (AnomalyChart, Detailseite). Sie ändern nur die
 * Anzeige; die Erkennung im Backend läuft immer auf der vollständigen Reihe
 * und nur auf bewerteten Monaten (E4, E9). */

/* Zeitfilter der Detailseite. Bezugspunkt ist der letzte angezeigte Monat
 * (letzter bewerteter Monat, siehe trimToEvaluated), nicht das heutige Datum:
 * viele Reihen enden 2025, ein Fenster ab heute wäre dort leer. */
export const TIME_RANGES = [
  { key: "all", label: "Gesamt", months: null },
  { key: "5y", label: "5 Jahre", months: 60 },
  { key: "3y", label: "3 Jahre", months: 36 },
  { key: "1y", label: "12 Monate", months: 12 },
]

export const DEFAULT_TIME_RANGE = "all"

export function isTimeRangeKey(key) {
  return TIME_RANGES.some((r) => r.key === key)
}

/* Monat "YYYY-MM" als "Jan. 2023" (de-DE). */
export function fmtPeriod(period) {
  const [y, m] = String(period).split("-").map(Number)
  return new Date(y, m - 1, 1).toLocaleDateString("de-DE", { month: "short", year: "numeric" })
}

/* Monat "YYYY-MM" als fortlaufende Zahl (Jahr · 12 + Monat − 1). */
export function periodIndex(period) {
  const [y, m] = String(period).split("-").map(Number)
  return y * 12 + (m - 1)
}

export function periodFromIndex(index) {
  const y = Math.floor(index / 12)
  const m = (index % 12) + 1
  return `${y}-${String(m).padStart(2, "0")}`
}

/* Anzeigebereich: vom ersten bis zum letzten bewerteten Monat. Davor und
 * danach gibt es keinen Monat mit genug Bewertungen und nichts zu überbrücken;
 * diese Ränder würden nur leere Fläche erzeugen. Rückgabe: {series, hiddenBefore,
 * hiddenAfter}, die Ränder als {from, to, months} oder null. Ohne bewerteten
 * Monat bleibt die Reihe unverändert (series ist dann die ganze Reihe). */
export function trimToEvaluated(series) {
  const list = series ?? []
  const isValue = (m) => m.evaluated && m.mean != null
  const first = list.findIndex(isValue)
  if (first < 0) return { series: list, hiddenBefore: null, hiddenAfter: null }
  let last = list.length - 1
  while (!isValue(list[last])) last--
  const edge = (a, b) => (b >= a ? { from: list[a].period, to: list[b].period, months: b - a + 1 } : null)
  return {
    series: list.slice(first, last + 1),
    hiddenBefore: edge(0, first - 1),
    hiddenAfter: edge(last + 1, list.length - 1),
  }
}

/* Sichtbares Fenster {from, to} (inklusive) für einen Zeitfilter oder null
 * für die ganze Reihe. Das Fenster beginnt nie vor dem ersten Monat. */
export function timeWindow(series, rangeKey) {
  const range = TIME_RANGES.find((r) => r.key === rangeKey)
  if (!range?.months || !series?.length) return null
  const first = periodIndex(series[0].period)
  const last = periodIndex(series[series.length - 1].period)
  const from = Math.max(first, last - range.months + 1)
  if (from <= first) return null // Fenster umfasst die ganze Reihe
  return { from: periodFromIndex(from), to: periodFromIndex(last) }
}

export function inWindow(period, win) {
  if (!win) return true
  const i = periodIndex(period)
  return i >= periodIndex(win.from) && i <= periodIndex(win.to)
}

/* Lineare Interpolation über nicht bewertete Monate, nur zur Darstellung.
 *
 * Für jede Lücke zwischen zwei bewerteten Monaten werden die Werte auf einer
 * der beiden Schlüssel "interpA"/"interpB" abgelegt, einschließlich der beiden
 * bewerteten Randmonate, damit die gestrichelte Linie an die durchgezogene
 * anschließt. Aufeinanderfolgende Lücken wechseln den Schlüssel: so wird
 * zwischen zwei direkt benachbarten bewerteten Monaten, die Ränder zweier
 * Lücken sind, keine gestrichelte Linie über die durchgezogene gezeichnet.
 * Lücken am Anfang oder Ende der Reihe bleiben leer (kein Nachbar).
 *
 * Eingabe: Monate mit {period, mean, evaluated}; Ausgabe: gleiche Länge,
 * je Monat {interpA, interpB, interpolated} (interpolated: Monat liegt in
 * einer überbrückten Lücke). */
export const INTERP_KEYS = ["interpA", "interpB"]

export function interpolateGaps(series) {
  const out = series.map(() => ({ interpA: null, interpB: null, interpolated: false }))
  const isValue = (m) => m.evaluated && m.mean != null
  let gapNo = 0
  let i = 0
  while (i < series.length) {
    if (isValue(series[i])) { i++; continue }
    const start = i
    while (i < series.length && !isValue(series[i])) i++
    const before = start - 1
    const after = i
    if (before >= 0 && after < series.length) {
      const key = INTERP_KEYS[gapNo % 2]
      const a = series[before].mean
      const b = series[after].mean
      const span = after - before
      out[before][key] = a
      out[after][key] = b
      for (let j = start; j < after; j++) {
        out[j][key] = +(a + ((j - before) / span) * (b - a)).toFixed(3)
        out[j].interpolated = true
      }
      gapNo++
    }
  }
  return out
}

/* Niveau je Kalendermonat aus den erkannten Veränderungen: Mittel des
 * Abschnitts zwischen zwei Wechseln (before_mean / after_mean der API).
 * Ein Abschnitt reicht von before_from bis zum Monat vor date (alt) bzw. von
 * date bis after_to (neu); nicht bewertete Monate dazwischen behalten das
 * alte Niveau, die Stufe liegt am markierten Monat. Monate außerhalb der
 * Abschnitte (ohne Veränderungen oder hinter einem nicht angezeigten
 * Wechsel) bleiben leer. Rückgabe: {period: level}. */
export function levelsFromAnomalies(anomalies) {
  const levels = {}
  const fill = (from, to, value) => {
    for (let i = periodIndex(from); i <= periodIndex(to); i++) levels[periodFromIndex(i)] = value
  }
  const sorted = [...(anomalies ?? [])]
    .filter((a) => a.before_from && a.after_to)
    .sort((a, b) => periodIndex(a.date) - periodIndex(b.date))
  for (const a of sorted) {
    fill(a.before_from, periodFromIndex(periodIndex(a.date) - 1), a.before_mean)
    fill(a.date, a.after_to, a.after_mean)
  }
  return levels
}
