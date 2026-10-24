/* Tests für lib/reportSummary.js (Kurzbericht des PDF-Exports; Prüfung 2026-10-17,
 * docs/feature-doku/16-report-qualitaet.md). Konstruierte Daten, ohne Netzwerk.
 *
 * Ausführen:  cd frontend && npm test */
import { describe, expect, it } from "vitest"
import {
  buildReportSummary, datenstandLines, nextSteps, situationCells, summarizeChanges, summarizeColumns, warningLines,
} from "../reportSummary"

const anomalyData = {
  group: "Mitarbeitende", dimensionName: "Gesamtnote", evaluatedMonths: 48,
  evaluatedRange: { from: "2015-01", to: "2018-05" }, eligibility: { eligible: true },
  anomalies: [
    { date: "2016-10", direction: "fall", delta: -0.74, before_mean: 3.84, after_mean: 3.1, before_from: "2015-01", previous_period: "2016-09", after_to: "2017-08", n_reviews_before: 56, n_reviews_after: 31, severity: "high", gap_months: 0, stability: { variants: 48, matches: 20, share: 0.42, tolerance_months: 3, grid: {} } },
    { date: "2017-09", direction: "rise", delta: 0.41, before_mean: 3.1, after_mean: 3.51, before_from: "2016-10", previous_period: "2017-06", after_to: "2018-05", n_reviews_before: 31, n_reviews_after: 22, severity: "medium", gap_months: 2, stability: { variants: 48, matches: 40, share: 0.83, tolerance_months: 3, grid: {} } },
  ],
  outliers: [],
}
const topics = [
  { topic: "Kollegenzusammenhalt", avgRating: 4.21, frequency: 312, sentiment: "Positiv", n_rated: 300, statistical_meta: { risk_level: "solid", sample_size: 312 } },
  { topic: "Gehalt", avgRating: 2.31, frequency: 120, sentiment: "Negativ", n_rated: 118, statistical_meta: { risk_level: "limited", sample_size: 120 } },
  { topic: "Kommunikation", avgRating: 2.9, frequency: 80, sentiment: "Negativ", statistical_meta: { risk_level: "acceptable" } },
  { topic: "Kantine", avgRating: 4.8, frequency: 2, sentiment: "Positiv" },
]
const trend = { avgDelta: "-0.21", sign: "down", windowMonths: 12, nReviews: { current: 120, previous: 98 }, raw: { difference_ci95: 0.3 } }
const rolling = { anchor: "2025-07", short: { mean: 3.21, from: "2024-08", to: "2025-07", n: 120 }, long: { mean: 3.4, from: "2023-08", n: 230 }, difference: -0.19, sign: "down" }

describe("summarizeChanges", () => {
  it("nennt die jüngste Veränderung zuerst, mit Folge, Stabilität und Netto", () => {
    const ch = summarizeChanges(anomalyData)
    expect(ch.state).toBe("ok")
    expect(ch.items[0].date).toBe("2017-09")
    expect(ch.items[0].consequence).toContain("bis zum letzten bewerteten Monat")
    expect(ch.items[0].stabilityText).toBe("40/48")
    expect(ch.items[1].consequence).toContain("hängt deutlich von den Schwellen ab")
    expect(ch.net.text).toContain("netto -0,33 Sterne")
  })
  it("nennt eigene Ereignisse im Ereignisfenster des Wechsels als möglichen Zusammenhang", () => {
    // Wechsel ab 2016-10 ohne Lücke: Fenster 2016-07 bis 2016-11
    const own = [
      { id: 1, title: "Führungswechsel", date_from: "2016-08", date_to: "2016-08" },
      { id: 2, title: "Weit weg", date_from: "2018-01", date_to: "2018-01" },
    ]
    const ch = summarizeChanges(anomalyData, undefined, own)
    const older = ch.items.find((it) => it.date === "2016-10")
    expect(older.ownEvents.map((e) => e.id)).toEqual([1])
    expect(older.ownEventsText).toBe("Eigenes Ereignis im Ereignisfenster: Führungswechsel (Aug. 2016) – möglicher Zusammenhang, keine Ursache.")
    expect(older.consequence).toContain("möglicher Zusammenhang, keine Ursache")
    expect(ch.items.find((it) => it.date === "2017-09").ownEventsText).toBeNull()
    expect(summarizeChanges(anomalyData).items[0].ownEvents).toEqual([])
  })
  it("liefert Zustände für fehlende, ungeeignete und leere Reihen", () => {
    expect(summarizeChanges(null).state).toBe("missing")
    expect(summarizeChanges({ ...anomalyData, eligibility: { eligible: false, reason: "nur 4 Monate" } }).note).toBe("Keine automatische Erkennung: nur 4 Monate")
    expect(summarizeChanges({ ...anomalyData, anomalies: [] }).state).toBe("none")
  })
})

describe("situationCells", () => {
  it("zeigt zwei Nachkommastellen und Intervalle", () => {
    const cells = situationCells({ avgScore: "3.4", avgCount: 1234, scoreCi95: 0.06, trend, rolling })
    expect(cells[0].value).toBe("3,40")
    expect(cells[0].sub).toContain("±0,06 (95 %)")
    expect(cells[1].sub).toContain("±0,30 (95 %)")
    expect(cells[2].tone).toBe("bad")
  })
})

describe("summarizeColumns", () => {
  const changes = summarizeChanges(anomalyData)
  const cols = summarizeColumns({ topics, mostCritical: { topicName: "Gehalt/Sozialleistungen", score: "2.80", n: 410 }, negativeTopicItem: { mention_count: 45 }, negativeTopic: "Führung", trend, rolling, changes })
  it("ordnet nach festen Regeln und nutzt die Einstufung nach Ø Sternen", () => {
    expect(cols.strengths[0].title).toBe("Jüngste auffällige Veränderung: Anstieg")
    expect(cols.issues.map((i) => i.title)).toEqual([
      "Gesamtnote sinkt", "12-Monats-Schnitt unter dem 24-Monats-Schnitt", "Kritischste Kategorie: Gehalt/Sozialleistungen", "Gehalt", "Kommunikation", "Führung",
    ])
    expect(cols.strengths.find((s) => s.title === "Kollegenzusammenhalt").detail).toBe("Ø 4,21 · 312 Erwähnungen (300 mit Wert) · Einstufung positiv")
    expect(cols.issues.find((i) => i.title === "Gehalt").warning).toBe("begrenzte Datenbasis (n = 118)")
  })
  it("warnt, wenn die Trend-Differenz im Intervall liegt", () => {
    expect(cols.issues[0].warning).toContain("statistisch nicht von 0 unterscheidbar")
  })
  it("lässt Topics unter der Mindestzahl Erwähnungen aus", () => {
    expect(cols.strengths.some((s) => s.title === "Kantine")).toBe(false)
  })
  it("nennt zur Einordnung das niedrigste Topic, wenn keine Regel trifft", () => {
    const only = summarizeColumns({ topics: [topics[0]], mostCritical: null, negativeTopic: "-", trend: null, rolling: null, changes: { items: [] } })
    expect(only.issues[0].title).toBe("Zur Einordnung: niedrigstes Topic")
  })
})

describe("Datenstand, Warnungen, nächste Schritte", () => {
  const dataStatus = {
    sources: { employee: { n_reviews: 1291, last_review: "2025-07-21", n_duplicates: 3, n_undated: 0, n_without_value: 0 }, candidates: { n_reviews: 195, last_review: "2025-06-27" } },
    last_import: { value: "2026-10-02T18:45:00" },
  }
  it("nennt letzten Bewertungsmonat, Abstand zu heute und Import", () => {
    const lines = datenstandLines({ dataStatus, now: new Date(2026, 9, 17) })
    expect(lines[0]).toContain("Mitarbeitende bis 21.07.2025 (1.291 Bewertungen)")
    expect(lines[1]).toContain("15 Monate vor dem Berichtsdatum")
    expect(lines[2]).toContain("02.10.2026")
  })
  it("sammelt Warnungen zu Duplikaten, kleiner Basis, Prognose, Trend und Stabilität", () => {
    const timelineFilters = { hasForecast: true, forecastInfo: { n_months: 106, months_below_min_reviews: 33, min_reviews_per_month: 5, last_month: "2025-07", backtest: { best_method: "ma6", methods: { holt: { mae: 0.64 }, ma6: { mae: 0.48, label: "Mittel der letzten 6 Monate" } } } } }
    const w = warningLines({ dataStatus, topics, timelineFilters, anomalyData, trend })
    expect(w.some((t) => t.includes("3 exakte Duplikate"))).toBe(true)
    expect(w.some((t) => t.includes("1 von 4 Topics"))).toBe(true)
    expect(w.some((t) => t.includes("33 von 106 Monaten"))).toBe(true)
    expect(w.some((t) => t.includes("ungenauer als die einfache Fortschreibung"))).toBe(true)
    expect(w.some((t) => t.includes("statistisch nicht von 0 unterscheidbar"))).toBe(true)
    expect(w.some((t) => t.includes("Okt. 2016: in 20 von 48 Parametervarianten"))).toBe(true)
    expect(w.some((t) => t.includes("nicht gegen Referenzzeiträume geprüft"))).toBe(false)   // Hinweis am 2026-10-24 entfernt (E25)
  })
  it("leitet höchstens drei Untersuchungsfragen aus den Handlungsfeldern ab", () => {
    const steps = nextSteps([{ kind: "change", ref: { date: "2016-10" } }, { kind: "trend" }, { kind: "topic", ref: { topic: "Gehalt" } }, { kind: "topic", ref: { topic: "X" } }])
    expect(steps).toHaveLength(3)
    expect(steps[0]).toContain("Veränderung ab Okt. 2016")
    expect(steps[2]).toContain("Topic Gehalt")
  })
  it("buildReportSummary liefert alle Blöcke ohne verbotene Zeichen", () => {
    const r = buildReportSummary({ avgScore: "3.37", avgCount: 1291, scoreCi95: 0.06, trend, rolling, mostCritical: null, negativeTopic: "-", topics, anomalyData, dataStatus, timelineFilters: null, now: new Date(2026, 9, 17) })
    for (const key of ["cells", "series", "datenstand", "changes", "strengths", "issues", "warnings", "limits", "nextSteps", "rules"]) expect(r).toHaveProperty(key)
    expect(/[→−←]/.test(JSON.stringify(r))).toBe(false)
  })
})
