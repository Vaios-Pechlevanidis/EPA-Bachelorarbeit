/* Sterne-Kategorien der Mitarbeiterbewertungen (Kununu): Schlüssel wie in der
 * Datenbank ohne Präfix "sternebewertung_", identisch mit
 * DIMENSIONS_BY_SOURCE["employee"] im Backend (ohne die Gesamtbewertung).
 * Einzige Zuordnung Schlüssel → Anzeigename (beide Quellen, siehe unten);
 * genutzt von ReviewDetailModal und den Anomalie-Ansichten. */
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

/* Sterne-Kategorien der Bewerberbewertungen, Schlüssel wie
 * DIMENSIONS_BY_SOURCE["candidates"] im Backend (ohne die Gesamtbewertung),
 * in dessen Reihenfolge. */
export const CANDIDATE_RATING_CATEGORIES = [
  { key: "erklaerung_der_weiteren_schritte",  label: "Erklärung der weiteren Schritte" },
  { key: "zufriedenstellende_reaktion",       label: "Zufriedenstellende Reaktion" },
  { key: "vollstaendigkeit_der_infos",        label: "Vollständigkeit der Infos" },
  { key: "zufriedenstellende_antworten",      label: "Zufriedenstellende Antworten" },
  { key: "angenehme_atmosphaere",             label: "Angenehme Atmosphäre" },
  { key: "professionalitaet_des_gespraechs",  label: "Professionalität des Gesprächs" },
  { key: "wertschaetzende_behandlung",        label: "Wertschätzende Behandlung" },
  { key: "erwartbarkeit_des_prozesses",       label: "Erwartbarkeit des Prozesses" },
  { key: "zeitgerechte_zu_oder_absage",       label: "Zeitgerechte Zu- oder Absage" },
  { key: "schnelle_antwort",                  label: "Schnelle Antwort" },
]

/* Gesamtbewertung (Spalte durchschnittsbewertung, E3) als erste Dimension. */
export const OVERALL_DIMENSION = { key: "durchschnittsbewertung", label: "Gesamtbewertung" }

/* Auswählbare Dimensionen je Quelle in der Reihenfolge des Backends. */
export const EMPLOYEE_DIMENSIONS = [OVERALL_DIMENSION, ...RATING_CATEGORIES]
export const CANDIDATE_DIMENSIONS = [OVERALL_DIMENSION, ...CANDIDATE_RATING_CATEGORIES]
export const DIMENSIONS_BY_SOURCE = { employee: EMPLOYEE_DIMENSIONS, candidates: CANDIDATE_DIMENSIONS }

/* Quellen (Bewertendengruppe, erste Ebene); Farben wie in TimelineCard. */
export const SOURCES = [
  { value: "employee",   label: "Mitarbeiter", color: "#3b82f6" },
  { value: "candidates", label: "Bewerber",    color: "#10b981" },
]
export const DEFAULT_SOURCE = "employee"

export function isSource(key) {
  return SOURCES.some((s) => s.value === key)
}

export function sourceLabel(key) {
  return SOURCES.find((s) => s.value === key)?.label ?? key
}

export function dimensionsFor(source = DEFAULT_SOURCE) {
  return DIMENSIONS_BY_SOURCE[source] ?? EMPLOYEE_DIMENSIONS
}

export function isDimensionOf(source, key) {
  return dimensionsFor(source).some((d) => d.key === key)
}

/* Anzeigename einer Dimension; die Schlüssel beider Quellen überschneiden sich
 * nur in der Gesamtbewertung. */
export function dimensionLabel(key) {
  return [...EMPLOYEE_DIMENSIONS, ...CANDIDATE_RATING_CATEGORIES].find((d) => d.key === key)?.label ?? key
}
