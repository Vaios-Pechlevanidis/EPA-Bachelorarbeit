/* Sterne-Kategorien der Mitarbeiterbewertungen (Kununu): Schlüssel wie in der
 * Datenbank ohne Präfix "sternebewertung_", identisch mit
 * DIMENSIONS_BY_SOURCE["employee"] im Backend (ohne die Gesamtbewertung).
 * Einzige Zuordnung Schlüssel → Anzeigename; genutzt von ReviewDetailModal
 * und den Anomalie-Ansichten. */
export const RATING_CATEGORIES = [
  { key: "arbeitsatmosphaere",         label: "Arbeitsatmosphäre" },
  { key: "image",                       label: "Image" },
  { key: "work_life_balance",           label: "Work-Life Balance" },
  { key: "karriere_weiterbildung",      label: "Karriere/Weiterbildung" },
  { key: "gehalt_sozialleistungen",     label: "Gehalt/Sozialleistungen" },
  { key: "kollegenzusammenhalt",        label: "Kollegenzusammenhalt" },
  { key: "umwelt_sozialbewusstsein",    label: "Umwelt-/Sozialbewusstsein" },
  { key: "vorgesetztenverhalten",       label: "Vorgesetztenverhalten" },
  { key: "kommunikation",               label: "Kommunikation" },
  { key: "interessante_aufgaben",       label: "Interessante Aufgaben" },
  { key: "umgang_mit_aelteren_kollegen", label: "Umgang mit älteren Kollegen" },
  { key: "arbeitsbedingungen",          label: "Arbeitsbedingungen" },
  { key: "gleichberechtigung",          label: "Gleichberechtigung" },
]

/* Gesamtbewertung (Spalte durchschnittsbewertung, E3) als erste Dimension. */
export const OVERALL_DIMENSION = { key: "durchschnittsbewertung", label: "Gesamtbewertung" }

/* Auswählbare Dimensionen der Mitarbeiterquelle in der Reihenfolge des Backends. */
export const EMPLOYEE_DIMENSIONS = [OVERALL_DIMENSION, ...RATING_CATEGORIES]

export function dimensionLabel(key) {
  return EMPLOYEE_DIMENSIONS.find((d) => d.key === key)?.label ?? key
}
