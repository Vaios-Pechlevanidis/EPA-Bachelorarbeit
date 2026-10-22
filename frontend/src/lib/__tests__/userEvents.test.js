/* Tests für lib/userEvents.js: Ereignisfenster eines Wechsels, Lage zum Fenster und
 * eigene Ereignisse im Fenster (Nachtrag zu E32, 2026-10-22). Konstruierte Daten.
 *
 * Ausführen:  cd frontend && npm test */
import { describe, expect, it } from "vitest"
import { changeEventWindow, eventWindowPhrase, userEventsInWindow } from "../userEvents"

const events = [
  { id: 1, title: "Führungswechsel", date_from: "2023-06", date_to: "2023-06" },
  { id: 2, title: "Umstrukturierung", date_from: "2022-11", date_to: "2023-03" },
  { id: 3, title: "Standortschließung", date_from: "2024-01", date_to: "2024-02" },
  { id: 4, title: "Tarifrunde", date_from: "2022-01", date_to: "2025-01" },
]

describe("changeEventWindow", () => {
  it("reicht von 3 Monaten vor dem Übergang bis 1 Monat nach dem markierten Monat", () => {
    expect(changeEventWindow({ date: "2023-07", previous_period: "2023-06" })).toEqual({ from: "2023-04", to: "2023-08" })
  })
  it("beginnt den Übergang nach einer Lücke im Monat nach previous_period", () => {
    expect(changeEventWindow({ date: "2023-07", previous_period: "2023-03" })).toEqual({ from: "2023-01", to: "2023-08" })
  })
  it("nimmt am Reihenrand den markierten Monat als Übergang; ohne Datum null", () => {
    expect(changeEventWindow({ date: "2023-01" })).toEqual({ from: "2022-10", to: "2023-02" })
    expect(changeEventWindow(null)).toBeNull()
  })
})

describe("eventWindowPhrase", () => {
  const win = { from: "2023-04", to: "2023-08" }
  it("beschreibt die Lage zum Fenster", () => {
    expect(eventWindowPhrase(events[0], win)).toBe("im Ereignisfenster")
    expect(eventWindowPhrase(events[1], win)).toBe("beginnt vor dem Ereignisfenster")
    expect(eventWindowPhrase({ date_from: "2023-08", date_to: "2023-10" }, win)).toBe("reicht über das Ereignisfenster hinaus")
    expect(eventWindowPhrase(events[3], win)).toBe("umfasst das Ereignisfenster")
  })
})

describe("userEventsInWindow", () => {
  it("findet Ereignisse, deren Zeitraum das Fenster berührt, sortiert nach Beginn", () => {
    const hits = userEventsInWindow(events, { from: "2023-03", to: "2023-08" })
    expect(hits.map((e) => e.id)).toEqual([4, 2, 1])
    expect(hits.map((e) => e.time_phrase)).toEqual(["umfasst das Ereignisfenster", "beginnt vor dem Ereignisfenster", "im Ereignisfenster"])
  })
  it("ist leer ohne Fenster, ohne Liste oder ohne Treffer", () => {
    expect(userEventsInWindow(events, null)).toEqual([])
    expect(userEventsInWindow(null, { from: "2023-03", to: "2023-08" })).toEqual([])
    expect(userEventsInWindow(events.slice(0, 3), { from: "2025-06", to: "2025-08" })).toEqual([])
  })
})
