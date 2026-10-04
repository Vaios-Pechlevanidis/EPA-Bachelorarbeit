import { sourceLabel } from "./ratingCategories"

/* Status der Bewertenden (Kununu). Die Rohwerte in der Datenbank sind
 * uneinheitlich: Mitarbeitende "1.0", "0.0", "True", "False", "Angestellt",
 * "Ex-Angestellt" oder leer; Bewerbende "hired", "offerDeclined", "rejected",
 * "deferred", "Bewerber" (nur Demo) oder leer. Die Zuordnung entspricht
 * normalize_status in backend/services/review_service.py. */

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
  deferred: "Zurückgestellt",
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
    { key: "zurueckgestellt", label: "Zurückgestellt" },
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
