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
