export const API_URL = (import.meta.env.VITE_API_URL || "http://localhost:8000") + "/api";

/* Zusatzkarten des Aktien-Dashboards (E16): Analystenempfehlungen, Umsatz und
   Nettoergebnis, Aktuelle Meldungen samt ihren Kacheln. Sie gehören nicht zum
   evaluierten Artefakt (FA-15 verlangt nur Kurs und Kennzahlen). Standard an;
   VITE_SHOW_FINANCE_EXTRAS=false (oder 0) blendet sie beim Bauen aus, z. B. für
   die Evaluationsinstanz. */
export const SHOW_FINANCE_EXTRAS = !["false", "0"].includes(
  String(import.meta.env.VITE_SHOW_FINANCE_EXTRAS ?? "").trim().toLowerCase(),
);
