import { useState } from "react"
import { fmtPeriod } from "@/lib/anomalySeries"

/* ============================================================================
   AnomalyComparison — Vorher-Nachher-Vergleich einer auffälligen Veränderung
   (Inkrement 2). Daten: GET …/anomalies/{id}/explanations (useAnomalyComparison).
   Zeigt, was sich in den Bewertungen zwischen den Fenstern verändert hat:
   Anzahl, Gesamtnote, Stimmung und je Schlüsselwort-Thema Anteil und Stimmung.
   Wortwahl: "Verschiebung", keine Aussage über Ursachen.
   ============================================================================ */

const TOP_TOPICS = 6

const SENTIMENT_MODE_LABEL = {
    transformer: "Transformer-Modell (German Sentiment BERT) mit der Sternebewertung als Hinweis",
    lexicon: "Lexikon (Wortlisten); das Transformer-Modell war nicht verfügbar",
}

const num = (v, digits = 2) =>
    v == null ? "–" : Number(v).toLocaleString("de-DE", { minimumFractionDigits: digits, maximumFractionDigits: digits })

const signed = (v, digits = 2) => (v == null ? "–" : (v > 0 ? "+" : v < 0 ? "−" : "±") + num(Math.abs(v), digits))

const pct = (share) => (share == null ? "–" : `${num(share * 100, 0)} %`)

const span = (w) => (w.from === w.to ? fmtPeriod(w.from) : `${fmtPeriod(w.from)} – ${fmtPeriod(w.to)}`)

const count = (n) => `${n} ${n === 1 ? "Bewertung" : "Bewertungen"}`

/* Kleiner Balken positiv / neutral / negativ mit mittlerer Polarität daneben. */
function SentimentBar({ sentiment, emptyText = "keine Texte" }) {
    if (!sentiment?.n) return <span className="text-[11px] text-slate-400">{emptyText}</span>
    const parts = [
        { key: "positive", label: "positiv", className: "bg-emerald-500" },
        { key: "neutral", label: "neutral", className: "bg-slate-300" },
        { key: "negative", label: "negativ", className: "bg-rose-500" },
    ]
    const title = `${parts.map((p) => `${p.label} ${pct(sentiment[p.key])}`).join(", ")}; mittlere Polarität ${signed(sentiment.mean_polarity)} (n = ${sentiment.n})`
    return (
        <span className="inline-flex items-center gap-2" title={title}>
            <span className="inline-flex h-2 w-14 rounded-full overflow-hidden bg-slate-100" aria-hidden="true">
                {parts.map((p) => (
                    <span key={p.key} className={p.className} style={{ width: `${(sentiment[p.key] ?? 0) * 100}%` }} />
                ))}
            </span>
            <span className="tnum text-[11px] text-slate-600 w-[38px]">{signed(sentiment.mean_polarity)}</span>
        </span>
    )
}

function LowBasisBadge({ title }) {
    return (
        <span
            className="inline-flex items-center px-1.5 py-0.5 rounded-full border border-slate-300 text-slate-500 text-[10px] uppercase tracking-wider"
            title={title}
        >
            kleine Basis
        </span>
    )
}

function WindowHeader({ label, win, stats }) {
    return (
        <div className="flex-1 min-w-[220px] rounded-md border border-slate-200 px-3 py-2.5">
            <p className="m-0 font-mono text-[10px] tracking-[0.06em] uppercase text-slate-500">{label}</p>
            <p className="m-0 mt-0.5 text-[13px] font-semibold text-slate-900">{span(win)}</p>
            <p className="m-0 mt-1 text-[12px] text-slate-600 tnum">
                {count(stats.n_reviews)} · Ø Gesamtnote {num(stats.mean_rating)}
                {stats.mean_value !== undefined && ` · Ø Dimension ${num(stats.mean_value)}`}
            </p>
            <div className="mt-1.5 flex items-center gap-2 text-[11px] text-slate-500">
                Stimmung <SentimentBar sentiment={stats.sentiment} />
            </div>
        </div>
    )
}

/* labels: Bezeichnungen der beiden Fenster, Standard für eine auffällige
   Veränderung; bei freier Auswahl (E17) "Zeitraum davor" und "Auswahl". */
export function AnomalyComparison({ data, loading, error, labels = { before: "davor", after: "ab dem markierten Monat" } }) {
    // Kurzformen für die Tabellenköpfe ("Anteil davor" / "Anteil Auswahl").
    const short = { before: "davor", after: labels.after === "ab dem markierten Monat" ? "danach" : labels.after }
    const [showAll, setShowAll] = useState(false)

    if (loading) {
        return (
            <div className="flex items-center gap-2 py-3">
                <div className="animate-spin rounded-full h-4 w-4 border-2 border-slate-200 border-t-slate-600"></div>
                <p className="m-0 text-slate-600 text-[12px]">Vergleich wird berechnet; die Stimmungsanalyse kann beim ersten Aufruf dauern…</p>
            </div>
        )
    }
    if (error) return <p className="m-0 text-[12px] text-slate-500">Vergleich konnte nicht geladen werden: {error}</p>
    if (!data) return null

    const { windows, comparison } = data
    const dimensionTopic = data.dimension_topic ?? null
    const topics = comparison.topics ?? []
    // Das Thema der gewählten Dimension bleibt sichtbar, auch wenn es nicht unter den größten Verschiebungen ist.
    const top = topics.slice(0, TOP_TOPICS)
    const pinned = data.dimension_topic && !top.some((t) => t.topic === data.dimension_topic)
        ? topics.filter((t) => t.topic === data.dimension_topic)
        : []
    const shown = showAll ? topics : [...top, ...pinned]
    const rule = comparison.low_basis_rule ?? {}
    const sample = comparison.sentiment_sample ?? {}
    const sampleText = ["before", "after"]
        .map((side) => {
            const s = sample[side]
            if (!s) return null
            const label = side === "before" ? labels.before : labels.after
            return s.limited ? `${label} die jüngsten ${s.analyzed} von ${s.with_text}` : `${label} alle ${s.analyzed}`
        })
        .filter(Boolean)
        .join(", ")

    return (
        <div className="space-y-4">
            <div className="flex flex-wrap gap-3">
                <WindowHeader label={labels.before} win={windows.before} stats={comparison.before} />
                <WindowHeader label={labels.after} win={windows.after} stats={comparison.after} />
                <div className="flex-1 min-w-[180px] rounded-md border border-slate-200 px-3 py-2.5">
                    <p className="m-0 font-mono text-[10px] tracking-[0.06em] uppercase text-slate-500">Verschiebung</p>
                    <p className="m-0 mt-0.5 text-[13px] font-semibold text-slate-900 tnum">{signed(comparison.rating_shift)} Sterne</p>
                    <p className="m-0 mt-1 text-[12px] text-slate-600 tnum">Polarität {signed(comparison.polarity_shift)}</p>
                    {comparison.value_shift !== undefined && (
                        <p className="m-0 mt-0.5 text-[12px] text-slate-600 tnum">Dimension {signed(comparison.value_shift)} Sterne</p>
                    )}
                </div>
            </div>

            {comparison.low_basis && (
                <p className="m-0 text-[12px] text-slate-600 rounded-md border border-slate-300 bg-slate-50 px-3 py-2">
                    <span className="font-medium text-slate-800">Kleine Basis.</span> Mindestens ein Fenster hat weniger als{" "}
                    {rule.min_reviews_per_window} Bewertungen; Anteile und Stimmung schwanken dann stark.
                </p>
            )}

            <div>
                <p className="m-0 mb-1.5 text-[12px] font-medium text-slate-800">Größte Verschiebungen je Thema</p>
                <div className="overflow-x-auto">
                    <table className="w-full text-[12px] border-collapse">
                        <thead>
                            <tr className="text-left text-[10px] uppercase tracking-wider text-slate-500">
                                <th className="font-medium py-1.5 pr-3">Thema</th>
                                <th className="font-medium py-1.5 pr-3 text-right">Anteil {short.before}</th>
                                <th className="font-medium py-1.5 pr-3 text-right">Anteil {short.after}</th>
                                <th className="font-medium py-1.5 pr-3 text-right">Differenz</th>
                                <th className="font-medium py-1.5 pr-3">Stimmung {short.before}</th>
                                <th className="font-medium py-1.5">Stimmung {short.after}</th>
                            </tr>
                        </thead>
                        <tbody>
                            {shown.map((t) => (
                                <tr
                                    key={t.topic}
                                    className={`border-t border-slate-100 ${t.low_basis ? "text-slate-500" : "text-slate-800"} ${t.topic === dimensionTopic ? "bg-amber-100" : ""}`}
                                >
                                    <td className="py-1.5 pr-3">
                                        <span className="inline-flex items-center gap-2">
                                            <span className={t.topic === dimensionTopic ? "font-semibold" : undefined}>{t.topic}</span>
                                            {t.topic === dimensionTopic && (
                                                <span className="text-[10px] uppercase tracking-wider text-slate-600">gewählte Dimension</span>
                                            )}
                                            {t.low_basis && (
                                                <LowBasisBadge
                                                    title={`Weniger als ${rule.min_mentions_per_topic} Nennungen in beiden Fenstern zusammen oder ein Fenster mit weniger als ${rule.min_reviews_per_window} Bewertungen`}
                                                />
                                            )}
                                        </span>
                                    </td>
                                    <td className="py-1.5 pr-3 text-right tnum" title={`${t.before.mentions} Nennungen`}>{pct(t.before.share)}</td>
                                    <td className="py-1.5 pr-3 text-right tnum" title={`${t.after.mentions} Nennungen`}>{pct(t.after.share)}</td>
                                    <td className="py-1.5 pr-3 text-right tnum font-semibold">{signed(t.share_shift_pp, 1)} Pp.</td>
                                    <td className="py-1.5 pr-3"><SentimentBar sentiment={t.before.sentiment} emptyText={t.before.mentions ? "keine Texte" : "keine Nennung"} /></td>
                                    <td className="py-1.5"><SentimentBar sentiment={t.after.sentiment} emptyText={t.after.mentions ? "keine Texte" : "keine Nennung"} /></td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
                {topics.length > TOP_TOPICS && (
                    <button
                        type="button"
                        onClick={() => setShowAll((v) => !v)}
                        className="mt-2 text-[11px] underline underline-offset-2 text-slate-600 hover:text-slate-900"
                    >
                        {showAll ? `Nur die ${TOP_TOPICS} größten zeigen` : `Alle ${topics.length} Themen zeigen`}
                    </button>
                )}
            </div>

            <p className="m-0 text-[11px] text-slate-500 leading-4">
                Der Vergleich zeigt, was sich in den Bewertungen verändert hat; er ist keine Aussage über Ursachen.
                Anteil = Bewertungen, die das Thema nennen (deutsche Schlüsselwörter), an allen Bewertungen des Fensters;
                Differenz in Prozentpunkten (Pp.). Stimmung: {SENTIMENT_MODE_LABEL[comparison.sentiment_mode] ?? comparison.sentiment_mode};
                Balken positiv / neutral / negativ, Zahl = mittlere Polarität von −1 bis +1.
                {sampleText && ` Ausgewertet je Fenster höchstens ${sample.limit} Bewertungen mit Freitext (${sampleText}).`}
            </p>
        </div>
    )
}
