/* Tests für lib/dimensionScope.js: Texte der Dimension als globalem Filter
 * (2026-10-23). Konstruierte Daten, ohne Netzwerk.
 *
 * Ausführen:  cd frontend && npm test */
import { describe, expect, it } from "vitest"
import {
  dimensionScopeNote, evidenceMatchText, evidenceScopeEmptyText, evidenceScopeText,
  isSingleDimension, reviewScopeEmptyText, reviewScopeText,
} from "../dimensionScope"

describe("isSingleDimension", () => {
  it("filtert nur bei einer Einzeldimension", () => {
    expect(isSingleDimension("gehalt_sozialleistungen")).toBe(true)
    expect(isSingleDimension("durchschnittsbewertung")).toBe(false)
    expect(isSingleDimension(null)).toBe(false)
  })
})

describe("reviewScopeText", () => {
  it("nennt die Zählung vor und nach dem Filter mit dem Anzeigenamen", () => {
    expect(reviewScopeText({ dimension_only: true, n_dimension: 12, n_all: 40 }, "gehalt_sozialleistungen"))
      .toBe("12 von 40 Bewertungen zur Dimension Gehalt/Sozialleistungen")
    expect(reviewScopeText({ dimension_only: true, n_dimension: 1, n_all: 1 }, "image")).toBe("1 von 1 Bewertung zur Dimension Image")
  })
  it("schweigt ohne Filter", () => {
    expect(reviewScopeText({ dimension: "image", topic: "Image", mentions: 3, topic_only: false }, "image")).toBeNull()
    expect(reviewScopeText(null, "image")).toBeNull()
  })
})

describe("evidenceScopeText", () => {
  it("nennt die Belege zur Dimension", () => {
    expect(evidenceScopeText({ dimension: "kommunikation", n_dimension: 3, n_all: 12 })).toBe("nur zur Dimension Kommunikation: 3 von 12 Belegen")
    expect(evidenceScopeText({ dimension: "kommunikation", n_dimension: 0, n_all: 1 })).toBe("nur zur Dimension Kommunikation: 0 von 1 Beleg")
    expect(evidenceScopeText(null)).toBeNull()
  })
})

describe("leere Listen und Hinweise", () => {
  it("erklärt die leere Bewertungsliste", () => {
    expect(reviewScopeEmptyText("image")).toMatch(/^Keine Bewertung dieses Zeitraums gehört zur Dimension Image/)
  })
  it("erklärt die leere Belegliste mit und ohne Belege im Fenster", () => {
    expect(evidenceScopeEmptyText({ dimension: "image", n_all: 0 })).toBe("Kein Beleg im Fenster, also auch keiner zur Dimension Image.")
    expect(evidenceScopeEmptyText({ dimension: "image", n_all: 4 })).toMatch(/^Kein Beleg zur Dimension Image im Fenster\. 4 Belege im Fenster gehören nicht dazu/)
  })
  it("nennt im Hinweis die Dimension und den Weg zurück", () => {
    const note = dimensionScopeNote("work_life_balance")
    expect(note).toMatch(/^Dimension Work-Life Balance gewählt/)
    expect(note).toContain("„Gesamtbewertung“")
  })
})

describe("evidenceMatchText", () => {
  it("nennt Schlüsselwörter und Ereignisart", () => {
    expect(evidenceMatchText({ terms: ["gehaltserhöhung"], category: "Vergütung und Sozialleistungen" }))
      .toBe("Bezug zur Dimension: Schlüsselwort ‚gehaltserhöhung‘ · Ereignisart Vergütung und Sozialleistungen")
    expect(evidenceMatchText({ terms: [], category: "Tarifverhandlung und Streik" })).toBe("Bezug zur Dimension: Ereignisart Tarifverhandlung und Streik")
  })
  it("schweigt ohne Bezug", () => {
    expect(evidenceMatchText(null)).toBeNull()
    expect(evidenceMatchText({ terms: [], category: null })).toBeNull()
  })
})
