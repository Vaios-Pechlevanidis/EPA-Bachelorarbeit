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

/* Auffällige Einzelmonate (E14) in den Anomalie-Ansichten. Standard an;
   VITE_SHOW_OUTLIER_MONTHS=false (oder 0) blendet sie beim Bauen aus: keine
   Rauten im Monatsverlauf, keine Einzelmonat-Zeile im Tooltip, keine Liste
   „Einzelmonate“, kein Einzelmonat im Zähler und in der Legende, im PDF weder
   Kachel noch Liste. Ein Klick auf einen Monat (auch ?from=&to= aus einem
   älteren Link) ist dann eine freie Auswahl (E17). Anlass: Einzelmonate treten
   in der Simulation etwa so häufig auf wie bei reinem Zufall (E30, Befund
   2026-10-13). Ob die Evaluationsinstanz mit false baut, entscheidet der Autor
   (docs/evaluationsinstanz.md). Das Backend liefert outlier_months weiter. */
export const SHOW_OUTLIER_MONTHS = !["false", "0"].includes(
  String(import.meta.env.VITE_SHOW_OUTLIER_MONTHS ?? "").trim().toLowerCase(),
);

/* Prüfumfang der Erkennung (DZ1, E30): Geprüft sind nur die Niveauwechsel der
   Gesamtbewertung der Mitarbeitenden ohne Statusfilter (DZ1: 8 annotierte der
   15 geeigneten Reihen; E30: alle 15 Reihen); für Einzeldimensionen, die
   Bewerberquelle und Statusgruppen läuft dieselbe Erkennung ungeprüft. Der
   Hinweis „Erkennung für diese Auswahl nicht geprüft“ unter dem Diagramm wurde
   am 2026-10-24 auf Entscheidung des Autors entfernt (E25, Nachtrag); der
   Prüfumfang steht in der Arbeit, nicht mehr im Dashboard. Der Zusatz zu den
   Einzelmonaten bleibt. */

/* Zusatz, wo auffällige Einzelmonate erklärt werden (Legende, Tooltip, Liste, PDF):
   ohne Veränderung entstehen in der Simulation 8,9 bzw. 5,4 Einzelmonate je 15
   Reihen, auf den echten Reihen sind es 9 (E30, Befund 2026-10-13). */
export const OUTLIER_UNVALIDATED_NOTE = "Ungeprüft: in der Simulation etwa so häufig wie bei reinem Zufall";
