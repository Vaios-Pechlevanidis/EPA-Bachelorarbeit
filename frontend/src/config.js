export const API_URL = (import.meta.env.VITE_API_URL || "http://localhost:8000") + "/api";

/* Zusatzkarten des Aktien-Dashboards (E16): Analystenempfehlungen, Umsatz und
   Nettoergebnis, Aktuelle Meldungen samt ihren Kacheln. Sie gehören nicht zum
   evaluierten Artefakt (FA-15 verlangt nur Kurs und Kennzahlen). Standard an;
   VITE_SHOW_FINANCE_EXTRAS=false (oder 0) blendet sie beim Bauen aus, z. B. für
   die Evaluationsinstanz. */
export const SHOW_FINANCE_EXTRAS = !["false", "0"].includes(
  String(import.meta.env.VITE_SHOW_FINANCE_EXTRAS ?? "").trim().toLowerCase(),
);

/* Prognose im Zeitverlauf (Holt, aus Zyklus 1; Entscheidung D2 des Autors,
   2026-10-09). Standard an; VITE_SHOW_FORECAST=false (oder 0) blendet sie beim
   Bauen aus: Der Zeitverlauf ruft dann forecast_months=0 ab und zeigt weder
   Prognoselinie noch Trennlinie, Legende oder „Ø Prognose“; der PDF-Export folgt
   demselben Schalter. Die Evaluationsinstanz baut mit false. */
export const SHOW_FORECAST = !["false", "0"].includes(
  String(import.meta.env.VITE_SHOW_FORECAST ?? "").trim().toLowerCase(),
);
