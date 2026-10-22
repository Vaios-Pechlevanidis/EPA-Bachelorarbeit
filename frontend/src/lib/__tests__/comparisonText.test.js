/* Tests für lib/comparisonText.js: Zahl der Bewertungen ohne
 * Freitext je Fenster (MR2, 2026-10-22). Konstruierte Daten, ohne Netzwerk.
 *
 * Ausführen:  cd frontend && npm test */
import { describe, expect, it } from "vitest"
import { withoutTextText } from "../comparisonText"

describe("withoutTextText", () => {
  it("nennt die Zahl ohne Freitext", () => {
    expect(withoutTextText({ n_reviews: 12, n_without_text: 3 })).toBe("3 ohne Freitext")
  })
  it("unterscheidet alle und keine mit Freitext", () => {
    expect(withoutTextText({ n_reviews: 12, n_without_text: 0 })).toBe("alle mit Freitext")
    expect(withoutTextText({ n_reviews: 4, n_without_text: 4 })).toBe("keine mit Freitext")
  })
  it("schweigt bei leerem Fenster oder alter Antwort ohne das Feld", () => {
    expect(withoutTextText({ n_reviews: 0, n_without_text: 0 })).toBeNull()
    expect(withoutTextText({ n_reviews: 5 })).toBeNull()
    expect(withoutTextText(null)).toBeNull()
  })
})
