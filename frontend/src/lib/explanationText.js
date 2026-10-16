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
    if (summary.state === "offen") {
        return short
            ? `offen · ${summary.n_items} ${summary.n_items === 1 ? "Beleg" : "Belege"} im Ereignisfenster`
            : `offen · ${summary.n_items} ${summary.n_items === 1 ? "Beleg" : "Belege"} im Ereignisfenster, keiner erreicht die Stufe niedrig`
    }
    const head = `${entries.length} ${entries.length === 1 ? "Ansatz" : "Ansätze"} aus ${summary.n_items} Belegen`
    if (short) return head
    return `${head} (${summary.n_bundles} Bündel${summary.n_groups != null ? `, ${summary.n_groups} ${summary.n_groups === 1 ? "Gruppe" : "Gruppen"} nach Ereignisart` : ""})${signalCounts(summary.n_by_signal_label)
        ? ` · Bündel nach Signalen: ${signalCounts(summary.n_by_signal_label)}`
        : stageCounts(summary.n_by_stage, rules) ? ` · Bündel je Stufe: ${stageCounts(summary.n_by_stage, rules)}` : ""}`
}
