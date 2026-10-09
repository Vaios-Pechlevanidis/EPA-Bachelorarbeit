/* Texte zum Ø Score (Entscheidung D1 des Autors, 2026-10-09; FA-38), gemeinsam für
 * die Kachel (KPIGrid), das Detailfenster (SorceModal), die Trend-Kachel und den
 * PDF-Export (utils/pdfExport.js), damit alle Stellen denselben Wortlaut zeigen.
 * Daten: GET /companies/{id}/ratings (Felder score, score_n, avg_overall). */

/* Berechnungshinweis (FA-38), wortgleich an Kachel, Detailfenster und PDF. */
export const SCORE_HINT =
  "Ø Score: Mittel der Gesamtnote aller Bewertungen von Mitarbeitenden im gewählten Zeitraum, ungewichtet. " +
  "Kununu berechnet seinen Score anders (laut Experteninterviews ohne Bewerbende und mit geringerem Gewicht " +
  "für ältere Bewertungen); der Wert kann deshalb von der Anzeige auf Kununu abweichen."

/* Überschrift und Satz über den Kategorien im Detailfenster und im PDF. */
export const CATEGORY_MEAN_TITLE = "Kategorienmittel"
export const CATEGORY_MEAN_NOTE =
  "Mittel der einzelnen Kategorien (Sternebewertung je Kategorie, Mitarbeitende). Ihr Mittel kann von der " +
  "Gesamtnote abweichen: Die Gesamtnote ist eine eigene Angabe je Bewertung, und nicht jede Bewertung enthält " +
  "jede Kategorie."

/* Beschriftung der Kachel mit der niedrigsten Kategorie (kategorienbasiert). */
export const CRITICAL_LABEL = "Kritischste Kategorie"
export const CRITICAL_NOTE = "niedrigstes Kategorienmittel, Mitarbeitende"

const fmtN = (n) => (n == null ? "–" : Number(n).toLocaleString("de-DE"))

/* "n = 1.234 Bewertungen mit Gesamtnote" */
export function scoreCountText(n) {
  return n == null ? "Mitarbeitende" : `n = ${fmtN(n)} ${n === 1 ? "Bewertung" : "Bewertungen"} mit Gesamtnote, Mitarbeitende`
}

/* "2024-08" → "08/2024" */
const fmtMonth = (p) => {
  if (!p) return "–"
  const [y, m] = String(p).split("-")
  return m && y ? `${m}/${y}` : "–"
}

/* Trend der Gesamtnote (Modus score_months): Fenster und n, z. B.
 * "08/2024 – 07/2025 (n = 120) vs. 08/2023 – 07/2024 (n = 98)" */
export function scoreTrendWindowsText(trend) {
  if (!trend?.current || !trend?.previous) return "keine datierten Bewertungen mit Gesamtnote"
  return `${fmtMonth(trend.current.from)} – ${fmtMonth(trend.current.to)} (n = ${fmtN(trend.current.n)}) vs. ` +
    `${fmtMonth(trend.previous.from)} – ${fmtMonth(trend.previous.to)} (n = ${fmtN(trend.previous.n)})`
}
