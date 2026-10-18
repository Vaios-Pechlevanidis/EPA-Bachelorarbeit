/* Texte der Karte "Mögliche Zusammenhänge" (ExplanationPanel, AnomalyDetailCards):
 * Bezeichnung der Stufen und Untertitel. Hier statt in der Komponentendatei,
 * damit Fast Refresh nur Komponenten exportiert sieht. */

/* Bezeichnung je Stufe (Rückfall, wenn die Antwort keine rules.stage_labels trägt). */
const STAGE_LABELS = {
    hoch: "Wortbezug und Ereignisart",
    mittel: "Wortbezug oder Themenbezug",
    niedrig: "nur Ereignisart",
    keine: "kein Bezug",
}
const STAGE_ORDER = ["hoch", "mittel", "niedrig"]

export const stageLabel = (stage, rules = null) => rules?.stage_labels?.[stage] ?? STAGE_LABELS[stage] ?? stage

export function stageCounts(n, rules) {
    if (!n) return ""
    return STAGE_ORDER.filter((s) => n[s]).map((s) => `${stageLabel(s, rules)} ${n[s]}`).join(", ")
}

/* Strenge Auswahl (E33, 2026-10-18): gilt, wenn die Antwort selection.strict trägt. */
export const isStrict = (summary) => Boolean(summary?.selection?.strict ?? summary?.rules?.selection?.strict)

/* Ausgeschlossene Belege je Grund ("Unternehmen im Titel nicht genannt 12, ohne Arbeitgeberbezug 5"). */
export function exclusionCounts(n) {
    if (!n) return ""
    return Object.entries(n).filter(([, count]) => count > 0).map(([reason, count]) => `${reason} ${count}`).join(", ")
}

/* Satz zur strengen Auswahl für den Dialog; "" ohne strenge Auswahl oder ohne Belege. */
export function selectionText(summary) {
    if (!isStrict(summary) || !summary?.n_items) return ""
    const counts = exclusionCounts(summary.n_excluded_by_reason)
    return `Strenge Auswahl: ${summary.n_selected} von ${summary.n_items} ${summary.n_items === 1 ? "Beleg" : "Belegen"} erfüllen alle vier Regeln, ${summary.n_excluded} ausgeschlossen${counts ? ` (${counts})` : ""}. Die Belegliste nennt je Meldung die nicht erfüllte Regel.`
}

/* Kopfzeile: Bündel (Stufe mindestens niedrig) je Bezeichnung nach Signalen. */
export function signalCounts(n) {
    if (!n) return ""
    return Object.entries(n).sort((a, b) => b[1] - a[1]).map(([label, count]) => `${label} ${count}`).join(", ")
}

/* Untertitel der Karte "Mögliche Zusammenhänge". data = Antwort des Vergleichs
   (explanations, explanation_summary); short = Kurzform für die Vorschau-Karte. */
export function explanationSubtitle({ data, loading, error }, { short = false } = {}) {
    const summary = data?.explanation_summary ?? null
    const entries = data?.explanations ?? []
    const rules = summary?.rules ?? null
    if (loading) return "Erklärungsansätze werden berechnet…"
    if (error) return "Erklärungsansätze konnten nicht geladen werden"
    if (!summary) return ""
    // Allgemeine Ereignisse im Fenster (Hypothese, außerhalb der Rangfolge; Nachtrag zu E29, 2026-10-17)
    const nGlobal = summary.global_events?.length ?? 0
    const globalText = nGlobal ? ` · ${nGlobal} ${nGlobal === 1 ? "allgemeines Ereignis" : "allgemeine Ereignisse"} (Hypothese)` : ""
    const strict = isStrict(summary)
    if (summary.state === "offen") {
        const why = strict ? "keiner erfüllt die strengen Auswahlregeln" : "keiner erreicht die Stufe niedrig"
        return short
            ? `offen · ${summary.n_items} ${summary.n_items === 1 ? "Beleg" : "Belege"} im Ereignisfenster`
            : `offen · ${summary.n_items} ${summary.n_items === 1 ? "Beleg" : "Belege"} im Ereignisfenster, ${why}${globalText}`
    }
    const head = `${entries.length} ${entries.length === 1 ? "Ansatz" : "Ansätze"} aus ${summary.n_items} Belegen`
    if (short) return head
    const selected = strict && summary.n_selected != null ? `${summary.n_selected} geeignet nach strenger Auswahl, ${summary.n_excluded} ausgeschlossen; ` : ""
    return `${head} (${selected}${summary.n_bundles} Bündel${summary.n_groups != null ? `, ${summary.n_groups} ${summary.n_groups === 1 ? "Gruppe" : "Gruppen"} nach Ereignisart` : ""})${signalCounts(summary.n_by_signal_label)
        ? ` · Bündel nach Signalen: ${signalCounts(summary.n_by_signal_label)}`
        : stageCounts(summary.n_by_stage, rules) ? ` · Bündel je Stufe: ${stageCounts(summary.n_by_stage, rules)}` : ""}${globalText}`
}
