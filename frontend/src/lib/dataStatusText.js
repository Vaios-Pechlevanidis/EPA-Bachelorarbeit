import { fmtPeriod } from "./anomalySeries"

/* Texte des Datenstands (Inkrement 6, FA-37), gemeinsam für die Leiste im
 * Dashboard (DataStatusBar) und den PDF-Export (utils/pdfExport.js), damit beide
 * dieselben Formulierungen zeigen. Daten: GET /companies/{id}/data-status.
 * Nur Beschreibung, keine Bewertung. */

export const fmtN = (n) => (n == null ? "–" : Number(n).toLocaleString("de-DE"))

/* "2026-10-02T18:50:16" → "02.10.2026"; "2025-07-21" → "21.07.2025" */
export const fmtDay = (value) => {
  if (!value) return "–"
  const [y, m, d] = String(value).slice(0, 10).split("-")
  return d && m && y ? `${d}.${m}.${y}` : "–"
}

/* Zeitstempel mit Uhrzeit, wenn vorhanden: "02.10.2026 18:50" */
export const fmtStamp = (value) => {
  if (!value) return "–"
  const s = String(value)
  return s.length >= 16 ? `${fmtDay(s)} ${s.slice(11, 16)}` : fmtDay(s)
}

/* Eine Quelle (Mitarbeitende, Bewerbende): Anzahl, Zeitraum, bewertete Monate, Eignung (E4). */
export function sourceLine(s) {
  if (!s || !s.n_reviews) return "keine Bewertungen"
  const span = s.first_review && s.last_review ? `${fmtDay(s.first_review)} – ${fmtDay(s.last_review)}` : "ohne Datum"
  const eligible = s.eligible
    ? `${s.evaluated_months} bewertete Monate, geeignet für die Erkennung`
    : `${s.evaluated_months} bewertete ${s.evaluated_months === 1 ? "Monat" : "Monate"}, keine automatische Erkennung`
  return `${fmtN(s.n_reviews)} ${s.n_reviews === 1 ? "Bewertung" : "Bewertungen"} · ${span} · ${eligible}${
    s.n_undated ? ` · ${s.n_undated} ohne Datum` : ""}`
}

/* Letzter Import in die Datenbank (created_at); das Abrufdatum bei Kununu ist nicht gespeichert. */
export function lastImportText(data) {
  return data?.last_import?.value
    ? `${fmtStamp(data.last_import.value)} (Datenbank; Abrufdatum bei Kununu nicht gespeichert)`
    : "unbekannt"
}

/* Vergleich mit der Plattform aus der Metadatei (nur vom Autor gefüllt). */
export function platformText(platform) {
  return platform?.available
    ? `${fmtN(platform.review_count)} Bewertungen am ${fmtDay(platform.count_date)} · im Datensatz ${fmtN(platform.dataset_count)} (${Math.round((platform.coverage_share ?? 0) * 100)} %)`
    : platform?.note ?? "–"
}

/* Stand des Kurs-Zwischenspeichers (E15); null = kein Ticker hinterlegt. */
export function marketText(market) {
  if (market === null) return "kein Ticker"
  if (!market) return "–"
  return market.available
    ? `${market.ticker}${market.ticker_scope && market.ticker_scope !== "eigene Aktie" ? ` (${market.ticker_scope})` : ""} · ${fmtPeriod(market.first_month)} – ${fmtPeriod(market.last_month)} · abgerufen ${fmtDay(market.fetched_at)}`
    : `${market.ticker}: kein Zwischenspeicher`
}

/* Stand des Belegspeichers (E18); null oder ohne Monate = nichts gespeichert. */
export function evidenceText(evidence) {
  if (evidence === null || !evidence?.months) return "kein gespeicherter Monat"
  return `${Object.values(evidence.sources ?? {}).map((s) => `${s.label} ${s.months} ${s.months === 1 ? "Monat" : "Monate"}`).join(", ")} · ${fmtPeriod(evidence.first_month)} – ${fmtPeriod(evidence.last_month)} · abgerufen ${fmtDay(evidence.fetched_at)}`
}

/* Schwellen der Eignung (E4), wie im Tooltip der Leiste. */
export function thresholdsNote(thresholds) {
  const t = thresholds ?? { min_reviews_per_month: 5, min_evaluated_months: 12 }
  return `bewertet = Monat mit mindestens ${t.min_reviews_per_month} Bewertungen (E4), geeignet = mindestens ${t.min_evaluated_months} bewertete Monate`
}

/* Zelle der Zeitstempel-Tabelle: ältester – jüngster Wert (n) oder "leer". */
export function timestampCell(t) {
  return t?.n ? `${fmtStamp(t.min)} – ${fmtStamp(t.max)} (${fmtN(t.n)})` : "leer"
}
