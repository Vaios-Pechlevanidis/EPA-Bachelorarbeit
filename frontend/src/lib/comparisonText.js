/* Texte des Vorher-Nachher-Vergleichs (AnomalyComparison, AnomalyDetailCards). */

/* Bewertungen ohne Freitext je Fenster: die Zahl allein ist nicht deutbar, deshalb
   steht sichtbar, wo Text fehlt (MR2, 2026-10-22). Ältere Antworten ohne
   n_without_text oder ein leeres Fenster: null. */
export function withoutTextText(stats) {
  const n = stats?.n_without_text
  if (n == null || !stats?.n_reviews) return null
  if (n === 0) return "alle mit Freitext"
  return n === stats.n_reviews ? "keine mit Freitext" : `${n} ohne Freitext`
}
