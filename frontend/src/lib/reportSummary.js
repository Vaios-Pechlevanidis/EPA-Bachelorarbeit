/* Kurzbericht des PDF-Exports (Nachtrag 2026-10-17, docs/feature-doku/14-kurzbericht-pdf.md;
 * erweitert durch die Prüfung 2026-10-17, docs/feature-doku/16-report-qualitaet.md).
 *
 * Leitet aus den Daten, die die Dashboard-Seite ohnehin für den Export sammelt,
 * nach festen Regeln kurze Aussagen ab:
 *   - Lage der Bewertung (Ø Score mit Intervall, Trend, 12- vs. 24-Monats-Schnitt),
 *   - Datenstand (letzter Bewertungsmonat, Import, Abstand zu heute),
 *   - die jüngsten auffälligen Veränderungen mit Folge für das Niveau und Stabilität,
 *   - „Was gut läuft“ und „Was verbessert werden sollte“ laut Bewertungen,
 *   - Warnungen zur Datenqualität, Grenzen und nächste Analyseschritte (Vorschläge).
 *
 * Nur Darstellung: Jede Aussage folgt einer Regel aus REPORT_RULES und nennt ihre
 * Zahlen (Ø, n, Zeitraum). Die Schwellen sind Setzungen des Autors (vorläufig) und
 * entsprechen den Farbschwellen der Kacheln (3,5 / 2,5). Keine Aussage über Ursachen.
 * Keine Pfeile und kein U+2212 in den Texten (Standardschriften des PDF). */

import { fmtPeriod, periodIndex } from "./anomalySeries"
import { MIN_REVIEWS_PER_WINDOW } from "./dataBasis"
import { dataQualityNotes, fmtDay, fmtN } from "./dataStatusText"
import { CRITICAL_LABEL, NEGATIVE_TOPIC_LABEL } from "./labels"
import { fmtRollingMonth, rollingReady, rollingWarnings } from "./rollingAverage"

export const REPORT_RULES = {
  maxChanges: 3,      // jüngste auffällige Veränderungen im Bericht
  maxTopics: 3,       // Topics je Spalte (Stärken, Handlungsfelder)
  goodRating: 3.5,    // Ø, ab dem ein Topic oder eine Kategorie als Stärke zählt
  weakRating: 2.5,    // Ø, unter dem ein Topic als Handlungsfeld zählt
  minMentions: 5,     // Erwähnungen, ab denen ein Topic in den Bericht kommt
  lowStability: 0.5,  // Anteil der Parametervarianten, unter dem eine Veränderung als instabil gilt
}

export const DIRECTION_WORD = { fall: "Abfall", rise: "Anstieg" }
export const CLASS_WORD = "Einstufung"   // nach Ø Sternen, keine Textanalyse (B1)

const num = (v, digits = 2) =>
  v == null || !Number.isFinite(Number(v)) ? "–" : Number(v).toFixed(digits).replace(".", ",")

const signed = (v, digits = 2) =>
  v == null || !Number.isFinite(Number(v)) ? "–" : `${v > 0 ? "+" : v < 0 ? "-" : "±"}${num(Math.abs(v), digits)}`

const span = (from, to) => (from && to && from !== to ? `${fmtPeriod(from)} – ${fmtPeriod(to)}` : fmtPeriod(from ?? to))

const norm = (s) => String(s ?? "").trim().toLowerCase()
const classOf = (t) => {
  const s = norm(t?.sentiment)
  return s.includes("neg") ? "negativ" : s.includes("pos") ? "positiv" : "neutral"
}
const ratingOf = (t) => { const r = Number(t?.avgRating); return Number.isFinite(r) ? r : NaN }
const freqOf = (t) => { const f = Number(t?.frequency); return Number.isFinite(f) ? f : 0 }
const isLimited = (t) => t?.statistical_meta?.risk_level === "limited"
// n eines Topics: Bewertungen mit Wert (n_rated, seit 2026-10-17), sonst sample_size
const sampleOf = (t) => t?.n_rated ?? t?.statistical_meta?.sample_size ?? t?.statistical_meta?.review_count ?? null

/* "in 20 von 48 Parametervarianten" oder null */
export function stabilityText(stability) {
  if (!stability || stability.variants == null) return null
  return `in ${stability.matches} von ${stability.variants} Parametervarianten`
}

/* Jüngste auffällige Veränderungen (nach Monat absteigend) mit der Folge für das
 * Niveau und der Stabilität. Rückgabe: {state, items, shown, total, net, note}; state ist
 * "ok", "none" (keine Veränderung), "ineligible" (keine Erkennung), "error" oder
 * "missing" (Karte nicht geladen). */
export function summarizeChanges(anomalyData, rules = REPORT_RULES) {
  const an = anomalyData
  if (!an) return { state: "missing", items: [], shown: 0, total: 0, net: null, note: "Die Anomalien-Karte war beim Export nicht geladen." }
  if (an.error) return { state: "error", items: [], shown: 0, total: 0, net: null, note: `Anomalien konnten nicht geladen werden: ${an.error}` }
  const elig = an.eligibility
  if (elig && !elig.eligible) {
    return { state: "ineligible", items: [], shown: 0, total: 0, net: null, note: elig.reason ? `Keine automatische Erkennung: ${elig.reason}` : "Keine automatische Erkennung." }
  }
  const all = [...(an.anomalies ?? [])].sort((a, b) => periodIndex(b.date) - periodIndex(a.date))
  if (!all.length) {
    const months = an.evaluatedMonths != null ? `, ${an.evaluatedMonths} bewertete Monate` : ""
    return {
      state: "none", items: [], shown: 0, total: 0, net: null,
      note: `Keine auffällige Veränderung in der Reihe ${an.group} · ${an.dimensionName}${months}${an.evaluatedRange ? ` (${span(an.evaluatedRange.from, an.evaluatedRange.to)})` : ""}.`,
    }
  }
  const lastEvaluated = an.evaluatedRange?.to ?? null
  const items = all.slice(0, rules.maxChanges).map((a, i) => {
    const next = i > 0 ? all[i - 1] : null // der zeitlich folgende Wechsel
    const word = DIRECTION_WORD[a.direction] || a.direction
    const rel = a.direction === "fall" ? "unter" : "über"
    const parts = []
    if (!next) {
      const holds = lastEvaluated && a.after_to === lastEvaluated
      parts.push(
        `Folge: Seit ${fmtPeriod(a.date)} liegt das Monatsmittel bei Ø ${num(a.after_mean)} und damit ${num(Math.abs(a.delta))} Sterne ${rel} dem Abschnitt davor (Ø ${num(a.before_mean)}, ${span(a.before_from, a.previous_period)})` +
        (holds ? `; das gilt bis zum letzten bewerteten Monat (${fmtPeriod(a.after_to)}).` : `; der Abschnitt danach reicht bis ${fmtPeriod(a.after_to)}.`),
      )
    } else {
      parts.push(
        `Folge: Ø ${num(a.after_mean)} für ${span(a.date, a.after_to)} statt Ø ${num(a.before_mean)} davor; ab ${fmtPeriod(next.date)} folgte ein weiterer Wechsel (${DIRECTION_WORD[next.direction] || next.direction}).`,
      )
    }
    if (a.gap_months > 0) {
      parts.push(`Davor ${a.gap_months} ${a.gap_months === 1 ? "Monat" : "Monate"} nicht bewertet (seit ${fmtPeriod(a.previous_period)}); der Übergang kann in dieser Lücke liegen.`)
    }
    const stab = stabilityText(a.stability)
    if (stab) {
      const low = a.stability.share != null && a.stability.share < rules.lowStability
      parts.push(`Stabilität: ${stab} erkannt${low ? "; die Markierung hängt deutlich von den Schwellen ab" : ""}.`)
    }
    return {
      date: a.date,
      direction: a.direction,
      directionWord: word,
      delta: a.delta,
      deltaText: `${word} um ${num(Math.abs(a.delta))} Sterne`,
      levelText: `von Ø ${num(a.before_mean)} auf Ø ${num(a.after_mean)}`,
      countText: `${fmtN(a.n_reviews_before)} / ${fmtN(a.n_reviews_after)}`,
      severity: a.severity,
      stability: a.stability ?? null,
      stabilityText: a.stability?.variants != null ? `${a.stability.matches}/${a.stability.variants}` : "–",
      current: !next,
      consequence: parts.join(" "),
    }
  })
  // Netto über alle Wechsel: erster Abschnitt gegen letzten Abschnitt
  const first = all[all.length - 1]
  const last = all[0]
  const net = all.length >= 2 && first.before_mean != null && last.after_mean != null
    ? {
        from: first.before_mean,
        to: last.after_mean,
        delta: last.after_mean - first.before_mean,
        text: `Über alle ${all.length} Wechsel: von Ø ${num(first.before_mean)} (Abschnitt ab ${fmtPeriod(first.before_from)}) auf Ø ${num(last.after_mean)} (bis ${fmtPeriod(last.after_to)}), netto ${signed(last.after_mean - first.before_mean)} Sterne.`,
      }
    : null
  return { state: "ok", items, shown: items.length, total: all.length, net, note: null }
}

/* Einzelmonate: ein Satz oder null; die Erklärung zu „ungeprüft“ steht auf der Seite „Technische Hinweise“. */
export function outlierSentence(outliers) {
  const list = outliers ?? []
  if (!list.length) return null
  const latest = [...list].sort((a, b) => periodIndex(b.date) - periodIndex(a.date))[0]
  return `Zusätzlich ${list.length} ${list.length === 1 ? "auffälliger Einzelmonat" : "auffällige Einzelmonate"} (ungeprüft), zuletzt ${fmtPeriod(latest.date)}; sie markieren kein neues Niveau.`
}

/* Lage der Bewertung als drei Zellen (Ø Score, Trend, 12- vs. 24-Monats-Schnitt)
 * für den Kennzahlen-Streifen. tone wie die Kacheln: good / warn / bad / neutral.
 * Mit scoreCi95 (halbe Breite des 95-%-Intervalls) und difference_ci95 des Trends. */
export function situationCells({ avgScore, avgCount, scoreCi95 = null, trend, rolling }, rules = REPORT_RULES) {
  const score = avgScore !== "-" && avgScore != null ? Number(avgScore) : NaN
  const scoreTone = !Number.isFinite(score) ? "neutral" : score >= rules.goodRating ? "good" : score >= rules.weakRating ? "warn" : "bad"
  const cells = [{
    label: "Ø Score",
    value: Number.isFinite(score) ? num(score, 2) : "–",
    sub: avgCount != null
      ? `von 5 · n = ${fmtN(avgCount)}${scoreCi95 != null ? ` · ±${num(scoreCi95)} (95 %)` : ""}`
      : "von 5 · Gesamtnote, Mitarbeitende",
    tone: scoreTone,
  }]
  const tv = trend?.avgDelta != null ? parseFloat(trend.avgDelta) : NaN
  const months = trend?.windowMonths
  const trendWord = trend?.sign === "up" ? "steigend" : trend?.sign === "down" ? "sinkend" : trend?.sign ? "stabil" : null
  const diffCi = trend?.raw?.difference_ci95
  cells.push({
    label: months ? `Trend ${months} M` : "Trend",
    value: Number.isFinite(tv) ? signed(tv) : "–",
    sub: trendWord
      ? `${trendWord} · ${months} M gegen ${months} M davor${diffCi != null ? ` · ±${num(diffCi)} (95 %)` : ""}`
      : "keine datierten Bewertungen mit Gesamtnote",
    tone: trend?.sign === "up" ? "good" : trend?.sign === "down" ? "bad" : "neutral",
  })
  const ok = rollingReady(rolling)
  const d = ok ? Math.abs(rolling.difference) : null
  cells.push({
    label: "12 vs. 24 Monate",
    value: ok ? `${num(rolling.short.mean)} / ${num(rolling.long.mean)}` : "–",
    sub: !ok ? "kein Vergleich möglich"
      : rolling.sign === "down" ? `12 Monate ${num(d)} unter dem 24-Monats-Schnitt`
      : rolling.sign === "up" ? `12 Monate ${num(d)} über dem 24-Monats-Schnitt`
      : "beide Schnitte gleichauf",
    tone: !ok ? "neutral" : rolling.sign === "down" ? "bad" : rolling.sign === "up" ? "good" : "neutral",
  })
  return cells
}

/* Ein Satz zur Reihe der Erkennung: Gruppe, Dimension, bewertete Monate, Zeitraum. */
export function seriesSentence(anomalyData) {
  const an = anomalyData
  if (!an || an.error) return null
  const months = an.evaluatedMonths != null ? `${an.evaluatedMonths} bewertete Monate` : null
  const range = an.evaluatedRange ? span(an.evaluatedRange.from, an.evaluatedRange.to) : null
  return `Reihe der Erkennung: ${an.group} · ${an.dimensionName}${months ? ` · ${months}` : ""}${range ? ` (${range})` : ""}.`
}

/* Datenstand als kurze Zeilen: letzter Bewertungsmonat je Quelle, Import, Abstand zu heute. */
export function datenstandLines({ dataStatus, timelineFilters = null, now = new Date() } = {}) {
  const out = []
  const emp = dataStatus?.sources?.employee
  const cand = dataStatus?.sources?.candidates
  if (emp?.last_review || cand?.last_review) {
    const parts = []
    if (emp?.last_review) parts.push(`Mitarbeitende bis ${fmtDay(emp.last_review)} (${fmtN(emp.n_reviews)} Bewertungen)`)
    if (cand?.last_review) parts.push(`Bewerbende bis ${fmtDay(cand.last_review)} (${fmtN(cand.n_reviews)} Bewertungen)`)
    out.push(`Datenstand: ${parts.join(", ")}.`)
  }
  const last = [emp?.last_review, cand?.last_review].filter(Boolean).sort().pop()
  if (last) {
    const d = new Date(String(last).slice(0, 10))
    const months = (now.getFullYear() - d.getFullYear()) * 12 + (now.getMonth() - d.getMonth())
    if (months >= 2) out.push(`Die jüngste Bewertung liegt ${months} Monate vor dem Berichtsdatum; neuere Bewertungen sind nicht im Datensatz.`)
  }
  if (dataStatus?.last_import?.value) out.push(`Letzter Import in die Datenbank: ${fmtDay(dataStatus.last_import.value)}.`)
  const fi = timelineFilters?.forecastInfo
  if (timelineFilters?.hasForecast && fi?.last_month) {
    out.push(`Die Prognose im Zeitverlauf beginnt am letzten Datenmonat (${fmtPeriod(fi.last_month)}) und ist eine Fortschreibung, keine Beobachtung.`)
  }
  return out
}

/* Warnungen zur Datenqualität und Aussagekraft, als Liste (leer, wenn nichts auffällt). */
export function warningLines({ dataStatus, topics = [], timelineFilters = null, anomalyData = null, trend = null, unvalidatedScope = false }, rules = REPORT_RULES) {
  const out = [...dataQualityNotes(dataStatus)]
  const limited = (topics ?? []).filter(isLimited).length
  if (limited) out.push(`${limited} von ${topics.length} Topics haben eine begrenzte Datenbasis (unter 30 Bewertungen); ihre Mittel und Einstufungen sind unsicher.`)
  const fi = timelineFilters?.forecastInfo
  if (fi?.months_below_min_reviews > 0) {
    out.push(`Zeitverlauf: ${fi.months_below_min_reviews} von ${fi.n_months} Monaten haben weniger als ${fi.min_reviews_per_month ?? 5} Bewertungen und zählen im Monatsmittel und in der Prognose trotzdem voll.`)
  }
  if (timelineFilters?.hasForecast && fi?.backtest?.best_method && fi.backtest.best_method !== "holt") {
    const holt = fi.backtest.methods?.holt?.mae
    const best = fi.backtest.methods?.[fi.backtest.best_method]
    out.push(`Prognose: Im Backtest war die Prognose (mittlerer Fehler ${num(holt)} Sterne) ungenauer als die einfache Fortschreibung „${best?.label ?? fi.backtest.best_method}“ (${num(best?.mae)}); sie ist als grobe Fortschreibung zu lesen.`)
  }
  const trendCi = trend?.raw?.difference_ci95
  const tv = trend?.avgDelta != null ? parseFloat(trend.avgDelta) : NaN
  if (trend?.sign && trend.sign !== "flat" && trendCi != null && Number.isFinite(tv) && Math.abs(tv) <= trendCi) {
    out.push(`Trend: Die Differenz ${signed(tv)} liegt innerhalb ihres 95-%-Intervalls (±${num(trendCi)}); sie ist statistisch nicht von 0 unterscheidbar.`)
  }
  const unstable = (anomalyData?.anomalies ?? []).filter((a) => a.stability?.share != null && a.stability.share < rules.lowStability)
  if (unstable.length) {
    out.push(`${unstable.length} von ${anomalyData.anomalies.length} auffälligen Veränderungen ${unstable.length === 1 ? "bleibt" : "bleiben"} in weniger als der Hälfte der Parametervarianten bestehen (${unstable.map((a) => `${fmtPeriod(a.date)}: ${stabilityText(a.stability)}`).join("; ")}).`)
  }
  if (unvalidatedScope) out.push("Die Erkennung ist für diese Auswahl (Quelle, Dimension oder Status) nicht gegen Referenzzeiträume geprüft.")
  return out
}

/* Grenzen der Aussagen, feste Sätze. */
export function limitLines() {
  return [
    "Kununu-Bewertungen sind freiwillig und selektiv; der Datensatz ist keine Stichprobe aller Beschäftigten oder Bewerbenden und erlaubt keine Aussage über Repräsentativität.",
    "Der Bericht beschreibt Befunde in den Bewertungen; er belegt keine Ursachen. Zeitliche Nähe zu Ereignissen ist ein Hinweis, kein Nachweis.",
    "Intervalle setzen unabhängige Bewertungen voraus; Mehrfachbewertungen derselben Person sind nicht erkennbar.",
    "Topics beruhen auf deutschen Schlüsselwörtern in den Freitexten; die Einstufung positiv / neutral / negativ folgt dem Ø der Sterne der nennenden Bewertungen, nicht dem Text.",
  ]
}

/* Einträge für die beiden Spalten. Jeder Eintrag: {title, detail, warning, basis, kind, ref}.
 * basis: "stars" (Sterne) oder "text" (Freitexte), wie das Kennzeichen der Datenbasis;
 * kind/ref dienen den nächsten Schritten. */
export function summarizeColumns({ topics, mostCritical, negativeTopicItem, negativeTopic, trend, rolling, changes }, rules = REPORT_RULES) {
  const strengths = []
  const issues = []
  const seen = { strengths: new Set(), issues: new Set() }
  const push = (list, key, item) => {
    const k = norm(item.title)
    if (seen[key].has(k)) return
    seen[key].add(k)
    list.push(item)
  }

  // 1. Jüngste auffällige Veränderung
  const latest = changes?.items?.[0] ?? null
  if (latest) {
    const stab = stabilityText(latest.stability)
    const item = {
      title: `Jüngste auffällige Veränderung: ${latest.directionWord}`,
      detail: `${signed(latest.delta)} Sterne ab ${fmtPeriod(latest.date)}, ${latest.levelText}${latest.current ? "; dieses Niveau gilt bis zum letzten bewerteten Monat" : ""}${stab ? `; ${stab} erkannt` : ""}`,
      warning: latest.stability?.share != null && latest.stability.share < rules.lowStability ? "Markierung hängt deutlich von den Schwellen ab" : null,
      basis: "stars",
      kind: "change",
      ref: latest,
    }
    push(latest.direction === "rise" ? strengths : issues, latest.direction === "rise" ? "strengths" : "issues", item)
  }

  // 2. Trend der Gesamtnote
  const tv = trend?.avgDelta != null ? parseFloat(trend.avgDelta) : NaN
  if (trend?.sign === "up" || trend?.sign === "down") {
    const months = trend.windowMonths
    const nCur = trend.nReviews?.current, nPrev = trend.nReviews?.previous
    const nMin = Math.min(nCur ?? Infinity, nPrev ?? Infinity)
    const ci = trend.raw?.difference_ci95
    const warnings = []
    if (Number.isFinite(nMin) && nMin < MIN_REVIEWS_PER_WINDOW) warnings.push(`kleine Basis (${fmtN(nMin)} Bewertungen in einem Fenster, unter ${MIN_REVIEWS_PER_WINDOW})`)
    if (ci != null && Number.isFinite(tv) && Math.abs(tv) <= ci) warnings.push("statistisch nicht von 0 unterscheidbar (95 %)")
    const item = {
      title: `Gesamtnote ${trend.sign === "up" ? "steigt" : "sinkt"}`,
      detail: `${signed(tv)} Sterne${ci != null ? ` (±${num(ci)}, 95 %)` : ""}, ${months} volle Monate gegenüber den ${months} Monaten davor`,
      warning: warnings.length ? warnings.join(" · ") : null,
      basis: "stars",
      kind: "trend",
      ref: trend,
    }
    push(trend.sign === "up" ? strengths : issues, trend.sign === "up" ? "strengths" : "issues", item)
  }

  // 3. 12- vs. 24-Monats-Schnitt
  if (rollingReady(rolling) && (rolling.sign === "up" || rolling.sign === "down")) {
    const warn = rollingWarnings(rolling)
    const item = {
      title: `12-Monats-Schnitt ${rolling.sign === "up" ? "über" : "unter"} dem 24-Monats-Schnitt`,
      detail: `${num(rolling.short.mean)} gegenüber ${num(rolling.long.mean)}; 12 Monate ${fmtRollingMonth(rolling.short.from)} – ${fmtRollingMonth(rolling.short.to)}, n = ${fmtN(rolling.short.n)}`,
      warning: warn.length ? warn.join(" · ") : null,
      basis: "stars",
      kind: "rolling",
      ref: rolling,
    }
    push(rolling.sign === "up" ? strengths : issues, rolling.sign === "up" ? "strengths" : "issues", item)
  }

  // 4. Niedrigste Kategorie (Kategorienmittel)
  const mcScore = mostCritical?.topicName && mostCritical.topicName !== "-" ? Number(mostCritical.score) : NaN
  if (Number.isFinite(mcScore)) {
    const nText = mostCritical.n != null ? `, n = ${fmtN(mostCritical.n)}` : ""
    if (mcScore < rules.goodRating) {
      push(issues, "issues", {
        title: `${CRITICAL_LABEL}: ${mostCritical.topicName}`,
        detail: `Ø ${num(mcScore)} von 5, niedrigstes Kategorienmittel über alle Bewertungen mit diesem Stern, Mitarbeitende${nText}`,
        warning: mostCritical.n != null && mostCritical.n < MIN_REVIEWS_PER_WINDOW ? `kleine Basis (${fmtN(mostCritical.n)} Bewertungen, unter ${MIN_REVIEWS_PER_WINDOW})` : null,
        basis: "stars",
        kind: "category",
        ref: mostCritical,
      })
    } else {
      push(strengths, "strengths", {
        title: `Alle Kategorien ab Ø ${num(mcScore)}`,
        detail: `niedrigste Kategorie ist ${mostCritical.topicName} (Ø ${num(mcScore)} von 5${nText})`,
        warning: null,
        basis: "stars",
        kind: "category",
        ref: mostCritical,
      })
    }
  }

  // 5. Topics aus der Topic-Übersicht (Freitexte): Einstufung und Ø Sterne
  const list = (topics ?? []).filter((t) => t?.topic && freqOf(t) >= rules.minMentions)
  const byFreq = (a, b) => freqOf(b) - freqOf(a)
  const topicItem = (t) => ({
    title: String(t.topic),
    detail: `Ø ${num(ratingOf(t))} · ${fmtN(freqOf(t))} Erwähnungen${sampleOf(t) != null && sampleOf(t) !== freqOf(t) ? ` (${fmtN(sampleOf(t))} mit Wert)` : ""} · ${CLASS_WORD} ${classOf(t)}`,
    warning: isLimited(t) ? `begrenzte Datenbasis${sampleOf(t) != null ? ` (n = ${fmtN(sampleOf(t))})` : ""}` : null,
    basis: "text",
    kind: "topic",
    ref: t,
  })
  const good = list.filter((t) => ratingOf(t) >= rules.goodRating && classOf(t) !== "negativ")
    .sort((a, b) => (classOf(a) === "positiv") === (classOf(b) === "positiv") ? byFreq(a, b) : classOf(a) === "positiv" ? -1 : 1)
  const weak = list.filter((t) => classOf(t) === "negativ" || ratingOf(t) < rules.weakRating).sort(byFreq)
  good.slice(0, rules.maxTopics).forEach((t) => push(strengths, "strengths", topicItem(t)))
  weak.slice(0, rules.maxTopics).forEach((t) => push(issues, "issues", topicItem(t)))

  // 6. Negativstes Topic (höchste Negativrate), falls noch nicht genannt
  const negName = negativeTopic && negativeTopic !== "-" ? String(negativeTopic) : null
  if (negName && !seen.issues.has(norm(negName))) {
    const mentions = negativeTopicItem?.mention_count
    push(issues, "issues", {
      title: negName,
      detail: `${NEGATIVE_TOPIC_LABEL}: höchste Negativrate in den Freitexten${mentions != null ? `, n = ${fmtN(mentions)} Nennungen` : ""}`,
      warning: null,
      basis: "text",
      kind: "topic",
      ref: negativeTopicItem,
    })
  }

  // 7. Rückfall: Trifft keine Regel, nennt die Spalte zur Einordnung das höchste
  //    bzw. niedrigste Topic (mit Ø und mindestens minMentions Erwähnungen).
  const rated = list.filter((t) => Number.isFinite(ratingOf(t)))
  const fallback = (t, kind) => ({
    ...topicItem(t),
    title: `Zur Einordnung: ${kind === "best" ? "höchstes" : "niedrigstes"} Topic`,
    detail: `${t.topic}: ${topicItem(t).detail} (${kind === "best" ? "keine Stärke" : "kein Handlungsfeld"} nach den Regeln)`,
    kind: "fallback",
  })
  if (!strengths.length && rated.length) {
    push(strengths, "strengths", fallback([...rated].sort((a, b) => ratingOf(b) - ratingOf(a) || byFreq(a, b))[0], "best"))
  }
  if (!issues.length && rated.length) {
    push(issues, "issues", fallback([...rated].sort((a, b) => ratingOf(a) - ratingOf(b) || byFreq(a, b))[0], "worst"))
  }

  return { strengths, issues }
}

/* Nächste Analyseschritte als Vorschläge, je Handlungsfeld eine Untersuchungsfrage
 * (Vorlagen nach Art des Eintrags; keine Maßnahme, kein Nachweis). Höchstens maxSteps. */
export function nextSteps(issues, { maxSteps = 3 } = {}) {
  const out = []
  for (const item of issues ?? []) {
    if (out.length >= maxSteps) break
    if (item.kind === "change") {
      out.push(`Veränderung ab ${fmtPeriod(item.ref.date)}: Bewertungen vor und nach dem Wechsel vergleichen (Themen, Status, Freitexte) und externe Berichte im Ereignisfenster sichten; Detailseite „Anomalien“.`)
    } else if (item.kind === "trend" || item.kind === "rolling") {
      out.push("Rückgang der Gesamtnote: prüfen, ob er von einzelnen Monaten mit kleiner Basis oder von einer Statusgruppe getragen wird (Monatsverlauf, Statusfilter).")
    } else if (item.kind === "category") {
      out.push(`Kategorie ${item.ref.topicName}: Verteilung der Sterne und Entwicklung über die Jahre prüfen; vergleichen, ob das Topic gleichen Namens in den Freitexten dasselbe Bild zeigt (anderer Nenner).`)
    } else if (item.kind === "topic" && item.ref?.topic) {
      out.push(`Topic ${item.ref.topic}: die negativen Freitexte lesen (Drill-down), wiederkehrende Aspekte zählen und die Entwicklung im Zeitverlauf des Topics prüfen.`)
    }
  }
  return out
}

/* Text der Regeln unter dem Bericht (vorläufige Setzungen des Autors). */
export function rulesText(rules = REPORT_RULES) {
  return (
    `Regeln dieses Berichts (Setzungen, vorläufig): Es werden die ${rules.maxChanges} jüngsten auffälligen Veränderungen genannt, mit ihrer Stabilität über ein Raster aus Strafterm, Mindestlänge und Mindestdichte. ` +
    `Als Stärke zählt ein Topic mit Ø ab ${num(rules.goodRating, 1)} ohne negative Einstufung, als Handlungsfeld ein Topic mit negativer Einstufung ` +
    `oder Ø unter ${num(rules.weakRating, 1)}; die Einstufung folgt dem Ø der Sterne der nennenden Bewertungen (ab 3,5 positiv, unter 2,5 negativ), nicht dem Text. ` +
    `Je Spalte höchstens ${rules.maxTopics} Topics mit mindestens ${rules.minMentions} Erwähnungen, nach Erwähnungen sortiert. ` +
    `Reihenfolge der Einträge: jüngste Veränderung, Trend, 12- vs. 24-Monats-Schnitt, niedrigste Kategorie, Topics nach Erwähnungen, Negativstes Topic; es gibt keinen Punktescore. ` +
    `Trifft keine Regel, nennt die Spalte zur Einordnung das höchste bzw. niedrigste Topic. ` +
    `Die nächsten Schritte sind Vorschläge für Untersuchungsfragen, keine Maßnahmen. ` +
    `Der Bericht nennt, wo die Bewertungen auffallen, nicht warum: keine Aussage über Ursachen.`
  )
}

/* Alles für die Seite „Kurzbericht“ des PDF-Exports. */
export function buildReportSummary(input, rules = REPORT_RULES) {
  const changes = summarizeChanges(input.anomalyData, rules)
  const columns = summarizeColumns({ ...input, changes }, rules)
  return {
    cells: situationCells(input, rules),
    series: seriesSentence(input.anomalyData),
    datenstand: datenstandLines(input),
    changes,
    outliers: outlierSentence(input.anomalyData?.outliers),
    ...columns,
    warnings: warningLines(input, rules),
    limits: limitLines(),
    nextSteps: nextSteps(columns.issues),
    rules: rulesText(rules),
  }
}
