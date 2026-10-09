import { sourceLabel } from "./ratingCategories"

/* Status der Bewertenden (Kununu). Die Rohwerte in der Datenbank sind
 * uneinheitlich: Mitarbeitende "1.0", "0.0", "True", "False", "Angestellt",
 * "Ex-Angestellt" oder leer; Bewerbende "hired", "offerDeclined", "rejected",
 * "deferred", "Bewerber" (nur Demo) oder leer. Die Zuordnung entspricht
 * normalize_status in backend/services/review_service.py. Bestätigt am
 * 2026-10-08 (E13): "True"/"False" wie "1.0"/"0.0"; "deferred" enthält bei den
 * Unternehmen aus Zyklus 1 auch Absagen, daher "Zurückgestellt oder Absage". */

const RAW_LABELS = {
  "1": "Angestellt",
  "1.0": "Angestellt",
  "true": "Angestellt",
  "0": "Ex-Angestellt",
  "0.0": "Ex-Angestellt",
  "false": "Ex-Angestellt",
  hired: "Eingestellt",
  offerdeclined: "Angebot abgelehnt",
  rejected: "Abgelehnt",
  deferred: "Zurückgestellt oder Absage",
}

/* Anzeigename eines Rohwerts; unbekannte Werte bleiben, wie sie sind, leere → null. */
export function statusLabel(status) {
  if (status == null) return null
  const s = String(status).trim()
  if (!s) return null
  const lower = s.toLowerCase()
  if (RAW_LABELS[lower]) return RAW_LABELS[lower]
  if (/^ex-?angestell/.test(lower.replace(/\s+/g, "-"))) return "Ex-Angestellt"
  return s
}

/* Auswählbare Statusgruppen je Quelle: Schlüssel wie STATUS_LABELS in
 * backend/services/review_service.py; key null = alle. */
export const STATUS_OPTIONS_BY_SOURCE = {
  employee: [
    { key: null, label: "Alle" },
    { key: "angestellt", label: "Angestellt" },
    { key: "ex-angestellt", label: "Ex-Angestellt" },
    { key: "unbekannt", label: "ohne Angabe" },
  ],
  candidates: [
    { key: null, label: "Alle" },
    { key: "eingestellt", label: "Eingestellt" },
    { key: "angebot-abgelehnt", label: "Angebot abgelehnt" },
    { key: "abgelehnt", label: "Abgelehnt" },
    { key: "zurueckgestellt", label: "Zurückgestellt oder Absage" },
    { key: "unbekannt", label: "ohne Angabe" },
  ],
}

export function statusOptions(source) {
  return STATUS_OPTIONS_BY_SOURCE[source] ?? STATUS_OPTIONS_BY_SOURCE.employee
}

/* Gültiger Statusschlüssel der Quelle oder null (alle). */
export function validStatus(source, key) {
  return key && statusOptions(source).some((o) => o.key === key) ? key : null
}

/* Bezeichnung der Bewertendengruppe für Untertitel, z. B. "Mitarbeiter · Angestellt". */
export function groupLabel(source, status) {
  const option = status ? statusOptions(source).find((o) => o.key === status) : null
  return option ? `${sourceLabel(source)} · ${option.label}` : sourceLabel(source)
}

/* Hinweis am Statusfilter (Inkrement 6, A4; E13): Für die Unternehmen aus
 * Zyklus 1 enthält der Export keinen Wert für ehemalige Mitarbeitende.
 * sourceStatus = sources.employee aus GET /companies/{id}/data-status
 * (status_counts, status_distinction). Liefert den Text oder null. */
export const STATUS_NO_DISTINCTION_HINT =
  "Für dieses Unternehmen liegt keine Unterscheidung zwischen aktuellen und ehemaligen Mitarbeitenden vor (Export ohne diesen Wert, E13). „Angestellt“ heißt hier „Bewertung mit Typangabe“ und entspricht bis auf die Bewertungen ohne Angabe der Gruppe „Alle“."

export function statusDistinctionHint(source, sourceStatus) {
  if (source !== "employee" || !sourceStatus || sourceStatus.n_reviews === 0) return null
  return sourceStatus.status_distinction === false ? STATUS_NO_DISTINCTION_HINT : null
}
