import { fmtPeriod } from "./anomalySeries"
import { evidenceScopeText } from "./dimensionScope"

/* Texte der Karte "Externe Berichte im Ereignisfenster" (EvidenceSection,
 * AnomalyDetailCards): Zählung, Fenster und Untertitel. Hier statt in der
 * Komponentendatei, damit Fast Refresh nur Komponenten exportiert sieht. */

/* Filterwert "ohne Ereignisart" der Belegliste (Inkrement 5). */
export const NO_CATEGORY = "__none__"

/* "12 Belege: 10 Meldungen, 2 EQS" */
export function countsText(total, counts) {
    if (!total) return "kein Beleg"
    const parts = [
        counts?.news ? `${counts.news} ${counts.news === 1 ? "Meldung" : "Meldungen"}` : null,
        counts?.adhoc ? `${counts.adhoc} EQS` : null,
        counts?.global ? `${counts.global} ${counts.global === 1 ? "allgemeines Ereignis" : "allgemeine Ereignisse"}` : null,
    ].filter(Boolean)
    return `${total} ${total === 1 ? "Beleg" : "Belege"}${parts.length ? `: ${parts.join(", ")}` : ""}`
}

/* "Okt. 2022 – Feb. 2023 (5 Monate: 3 vor dem Übergang, 1 danach)" */
export function windowText(window) {
    if (!window) return ""
    const span = window.from === window.to ? fmtPeriod(window.from) : `${fmtPeriod(window.from)} – ${fmtPeriod(window.to)}`
    const ref = window.kind === "auswahl" ? "um die Auswahl" : window.kind === "einzelmonat" ? "um den Monat" : "um den Übergang"
    return `${span} (${window.months} ${window.months === 1 ? "Monat" : "Monate"}: ${window.window_before} davor, ${window.window_after} danach, ${ref})`
}

/* Untertitel der Karte; short = Kurzform für die Vorschau-Karte (nur die Zählung). */
export function evidenceSubtitle(evidence, listNote = "", { short = false } = {}) {
    const data = evidence.data
    if (evidence.loading) return "Lade Belege…"
    if (evidence.error) return "Belege konnten nicht geladen werden"
    if (!data) return ""
    if (short) return countsText(data.total, data.counts)
    // Mit der Dimension als Filter (2026-10-23): "… · nur zur Dimension Image: 3 von 12 Belegen"
    const scope = evidenceScopeText(data.scope)
    return `Ereignisfenster ${windowText(data.window)} · ${countsText(data.total, data.counts)}${scope ? ` · ${scope}` : ""}${listNote ? ` · ${listNote}` : ""}`
}
