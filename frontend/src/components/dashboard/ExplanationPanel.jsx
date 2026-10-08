import { useState } from "react"
import { ChevronDown, ChevronRight, ExternalLink, Lightbulb } from "lucide-react"
import { PageSection } from "./PageSection"

/* ============================================================================
   ExplanationPanel — "Mögliche Zusammenhänge" (Inkrement 5, Erklärungsansätze).
   Daten: explanations und explanation_summary aus GET …/explanations bzw.
   GET …/compare (useAnomalyComparison, usePeriodComparison). Ein
   Erklärungsansatz ist ein möglicher Zusammenhang zwischen der Veränderung
   und einem extern belegten Ereignis, begründet durch zeitliche und
   thematische Korrespondenz; nie eine Ursache. Je Eintrag: Stufe als Badge,
   Begründung in Klartext, die Signale als kleine Kennzeichen (Begriff,
   Ereignisart und Thema, zeitliche Nähe, Quellenart; Stimmung des Titels ohne
   Einfluss auf die Stufe), Link, aufklappbar die gebündelten Meldungen.
   Zustand "offen", wenn kein Beleg die Stufe niedrig erreicht.
   ============================================================================ */

export const EXPLANATION_NOTE = "Die Einstufung beruht auf Titeln und Wortbezügen. Sie zeigt mögliche Zusammenhänge, keine Ursachen."

const STAGES = {
    hoch: { label: "hoch", className: "bg-emerald-100 text-slate-800" },
    mittel: { label: "mittel", className: "bg-amber-100 text-slate-800" },
    niedrig: { label: "niedrig", className: "bg-slate-100 text-slate-700 border border-slate-300" },
    keine: { label: "keine", className: "bg-slate-50 text-slate-500 border border-slate-200" },
}

const TYPE_LABELS = { news: "Meldung", adhoc: "Ad-hoc", global: "Allgemeines Ereignis" }
const SENTIMENT_LABELS = { positive: "positiv", neutral: "neutral", negative: "negativ" }

const num = (v, digits = 2) =>
    v == null ? "–" : Number(v).toLocaleString("de-DE", { minimumFractionDigits: digits, maximumFractionDigits: digits })
const signed = (v, digits = 1) => (v == null ? "–" : (v > 0 ? "+" : v < 0 ? "−" : "±") + num(Math.abs(v), digits))

const fmtDay = (value) => {
    if (!value) return "ohne Datum"
    const d = new Date(value.length === 10 ? `${value}T12:00:00` : value)
    return Number.isNaN(d.getTime()) ? "ohne Datum" : d.toLocaleDateString("de-DE", { day: "2-digit", month: "2-digit", year: "numeric" })
}

/* Stufe als Badge; rule = Regel der Stufe als Tooltip (aus explanation_summary.rules). */
export function StageBadge({ stage, rule = null, small = false }) {
    const s = STAGES[stage] ?? STAGES.keine
    return (
        <span
            className={`flex-none inline-flex items-center rounded-full font-medium uppercase tracking-wider ${small ? "px-1.5 py-0.5 text-[9.5px]" : "px-2 py-0.5 text-[10px]"} ${s.className}`}
            title={rule ? `Stufe ${s.label}: ${rule}` : `Stufe ${s.label}`}
        >
            {s.label}
        </span>
    )
}

function Chip({ children, title, strong = false }) {
    return (
        <span
            className={`inline-flex items-center gap-1 rounded-full border border-slate-200 bg-slate-50 px-1.5 py-0.5 text-[10.5px] ${strong ? "text-slate-800 font-medium" : "text-slate-600"}`}
            title={title}
        >
            {children}
        </span>
    )
}

/* Kennzeichen der Signale eines Eintrags. */
function SignalChips({ entry }) {
    const cat = entry.category
    const terms = entry.terms ?? []
    const shifted = cat?.shifted_topics ?? []
    const sentiment = entry.sentiment
    return (
        <div className="mt-1.5 flex flex-wrap gap-1">
            {terms.map((t) => (
                <Chip
                    key={t.term}
                    strong={t.strong}
                    title={`Kennzeichnender Begriff der Bewertungen im Titel („${t.word}“): ${t.after} von ${t.n_after} Bewertungen danach gegenüber ${t.before} von ${t.n_before} davor${t.strong ? "; starker Begriff" : ""}`}
                >
                    Begriff ‚{t.term}‘ {t.after} ggü. {t.before}
                </Chip>
            ))}
            {cat && cat.employer_related && (
                <Chip
                    strong={shifted.length > 0}
                    title={`Ereignisart aus dem Titel (Schlüsselwort: ${(cat.keywords ?? []).join(", ")}); zugeordnete Themen: ${(cat.topics ?? []).join(", ")}`}
                >
                    Ereignisart {cat.label}
                    {shifted.length
                        ? ` · ${shifted.map((s) => `${s.topic} ${signed(s.share_shift_pp)} Pp.`).join(", ")}`
                        : " · nur erkannt"}
                </Chip>
            )}
            {cat && !cat.employer_related && (
                <Chip title={`Schlüsselwort: ${(cat.keywords ?? []).join(", ")}; eine Stufe zurückgestuft`}>
                    ohne Arbeitgeberbezug · zurückgestuft
                </Chip>
            )}
            <Chip title={`Zeitliche Nähe ${num(entry.time_match)}: am höchsten im Monat vor dem Übergang und im Übergang, abnehmend zum Rand des Fensters, niedriger danach`}>
                {entry.time_phrase} · {num(entry.time_match, 2)}
            </Chip>
            <Chip title={`Quellenart ordnet nur innerhalb einer Stufe; Verlässlichkeit ${entry.reliability ?? "–"}`}>
                {TYPE_LABELS[entry.source_type] ?? entry.source_type}
                {entry.language === "en" ? " · EN" : ""}
            </Chip>
            {entry.company_in_title === false && (
                <Chip title="Der Titel nennt den Unternehmensnamen nicht; die Meldung kann ein fremder Treffer des Suchbegriffs sein. Nur Hinweis, ohne Einfluss auf die Stufe">
                    Unternehmen im Titel nicht genannt
                </Chip>
            )}
            {sentiment && (
                <Chip title="Stimmung des Titels über den Sentiment-Analyzer (an Bewertungen geprüft, nicht an Schlagzeilen); ohne Einfluss auf die Stufe">
                    Stimmung des Titels {SENTIMENT_LABELS[sentiment.label] ?? sentiment.label} ({signed(sentiment.polarity, 2)})
                    {sentiment.fits_direction === true ? ", passt zur Richtung" : sentiment.fits_direction === false ? ", passt nicht zur Richtung" : ""}
                </Chip>
            )}
        </div>
    )
}

function BundledItems({ items, rules }) {
    return (
        <ul className="m-0 mt-2 p-0 list-none border-l-2 border-slate-200 pl-3 space-y-1">
            {items.map((item) => (
                <li key={item.id} className="flex items-start gap-2 text-[11.5px]">
                    <span className="w-[70px] flex-none text-slate-500 tnum">{fmtDay(item.date)}</span>
                    <span className="min-w-0 flex-1">
                        <a href={item.url} target="_blank" rel="noopener noreferrer" className="text-slate-800 hover:underline underline-offset-2 inline-flex items-center gap-1 min-w-0">
                            <span className="truncate">{item.title}</span>
                            <ExternalLink className="w-3 h-3 flex-none text-slate-400" aria-hidden="true" />
                        </a>
                        <span className="block text-[10.5px] text-slate-500">
                            {item.publisher || "Herausgeber unbekannt"} · {TYPE_LABELS[item.source_type] ?? item.source_type}
                            {item.issuer ? ` · Mitteilung von ${item.issuer}` : ""} · Zeit {num(item.time_match, 2)}, Thema {num(item.topic_match, 2)}
                        </span>
                    </span>
                    <StageBadge stage={item.stage} rule={rules?.stages?.[item.stage]} small />
                </li>
            ))}
        </ul>
    )
}

function ExplanationEntry({ entry, rules }) {
    const [open, setOpen] = useState(false)
    const bundled = entry.n_items > 1
    return (
        <li className="border-t border-slate-100 first:border-t-0 py-3 flex items-start gap-3">
            <div className="flex-none pt-0.5 w-[62px]">
                <StageBadge stage={entry.confidence} rule={rules?.stages?.[entry.confidence]} />
            </div>
            <div className="min-w-0 flex-1">
                <p className="m-0 text-[12.5px] text-slate-800 leading-5">{entry.text}</p>
                <p className="m-0 mt-1 text-[11.5px] text-slate-600 flex items-center gap-1.5 flex-wrap">
                    <a
                        href={entry.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="font-medium text-slate-900 hover:underline underline-offset-2 inline-flex items-center gap-1 min-w-0 max-w-full"
                        title="Meldung beim Herausgeber öffnen (neuer Tab)"
                    >
                        <span className="truncate">{entry.event}</span>
                        <ExternalLink className="w-3 h-3 flex-none text-slate-400" aria-hidden="true" />
                    </a>
                    <span className="text-slate-500 tnum">
                        · {fmtDay(entry.date)} · {entry.source || "Herausgeber unbekannt"}
                        {entry.issuer ? ` · Mitteilung von ${entry.issuer}` : ""}
                        {bundled ? ` · ${entry.n_items} Meldungen (${(entry.publishers ?? []).join(", ")})` : ""}
                    </span>
                </p>
                <SignalChips entry={entry} />
                {bundled && (
                    <button
                        type="button"
                        className="mt-1.5 inline-flex items-center gap-1 text-[11px] text-slate-600 hover:text-slate-900 underline-offset-2 hover:underline"
                        onClick={() => setOpen((v) => !v)}
                        aria-expanded={open}
                    >
                        {open ? <ChevronDown className="w-3 h-3" aria-hidden="true" /> : <ChevronRight className="w-3 h-3" aria-hidden="true" />}
                        {open ? "Gebündelte Meldungen ausblenden" : `${entry.n_items} gebündelte Meldungen anzeigen`}
                    </button>
                )}
                {bundled && open && <BundledItems items={entry.items ?? []} rules={rules} />}
            </div>
        </li>
    )
}

function stageCounts(n) {
    if (!n) return ""
    return ["hoch", "mittel", "niedrig"].filter((s) => n[s]).map((s) => `${s} ${n[s]}`).join(", ")
}

/* Abschnitt über der Belegliste. data = Antwort des Vergleichs (explanations, explanation_summary). */
export function ExplanationPanel({ data, loading, error, eyebrow = "ERKLÄRUNGSANSÄTZE", className = "" }) {
    const [showRules, setShowRules] = useState(false)
    const summary = data?.explanation_summary ?? null
    const entries = data?.explanations ?? []
    const open = summary?.state === "offen"
    const subtitle = loading
        ? "Erklärungsansätze werden berechnet…"
        : error
            ? "Erklärungsansätze konnten nicht geladen werden"
            : summary
                ? open
                    ? `offen · ${summary.n_items} ${summary.n_items === 1 ? "Beleg" : "Belege"} im Ereignisfenster, keiner erreicht die Stufe niedrig`
                    : `${entries.length} ${entries.length === 1 ? "Ansatz" : "Ansätze"} aus ${summary.n_items} Belegen (${summary.n_bundles} Bündel)${stageCounts(summary.n_by_stage) ? ` · Bündel je Stufe: ${stageCounts(summary.n_by_stage)}` : ""}`
                : ""
    const rules = summary?.rules ?? null
    return (
        <PageSection className={className} icon={<Lightbulb />} eyebrow={eyebrow} title="Mögliche Zusammenhänge" subtitle={subtitle}>
            {loading ? (
                <div className="flex items-center gap-2 py-1">
                    <div className="animate-spin rounded-full h-4 w-4 border-2 border-slate-200 border-t-slate-600"></div>
                    <p className="m-0 text-slate-600 text-[12px]">Erklärungsansätze werden berechnet; beim ersten Aufruf dauert die Stimmungsanalyse des Vergleichs…</p>
                </div>
            ) : error ? (
                <p className="m-0 text-[12px] text-slate-500">Erklärungsansätze konnten nicht geladen werden: {error}</p>
            ) : !summary ? null : summary.error ? (
                <p className="m-0 text-[12px] text-slate-500">Erklärungsansätze konnten nicht berechnet werden: {summary.error}</p>
            ) : open ? (
                <div className="space-y-1">
                    <p className="m-0 text-[12.5px] font-medium text-slate-700">Offen.</p>
                    <p className="m-0 text-[12px] text-slate-600">{summary.open_note}</p>
                    {summary.reason && !summary.coverage && <p className="m-0 text-[12px] text-slate-500">{summary.reason}</p>}
                </div>
            ) : (
                <ul className="m-0 p-0 list-none">
                    {entries.map((entry) => <ExplanationEntry key={entry.id ?? entry.rank} entry={entry} rules={rules} />)}
                </ul>
            )}
            {rules && !loading && !error && (
                <div className="mt-3">
                    <button
                        type="button"
                        className="inline-flex items-center gap-1 text-[11px] text-slate-500 hover:text-slate-800 underline-offset-2 hover:underline"
                        onClick={() => setShowRules((v) => !v)}
                        aria-expanded={showRules}
                    >
                        {showRules ? <ChevronDown className="w-3 h-3" aria-hidden="true" /> : <ChevronRight className="w-3 h-3" aria-hidden="true" />}
                        Wie wird eingestuft?
                    </button>
                    {showRules && (
                        <div className="mt-1.5 text-[11px] text-slate-600 leading-4 space-y-1">
                            <p className="m-0">
                                Drei Signale je Beleg, alle aus dem Titel und den Bewertungen: <span className="font-medium">Begriff</span> (kennzeichnende
                                Begriffe, die in den Bewertungen danach deutlich häufiger vorkommen als davor und im Titel stehen; je Begriff
                                {" "}{num(rules.term_match_per_term, 1)}, ein starker Begriff {num(rules.term_match_strong, 1)}),
                                {" "}<span className="font-medium">Ereignisart</span> (aus Schlüsselwörtern im Titel; {num(rules.category_match_with_shift, 1)}, wenn sich ein
                                zugeordnetes Thema im Vergleich um mindestens {num(rules.topic_shift_min_pp, 0)} Prozentpunkte verschoben hat, sonst
                                {" "}{num(rules.category_match_only, 1)}) und <span className="font-medium">zeitliche Nähe</span> (1 im Monat vor dem Übergang und im Übergang,
                                abnehmend zum Rand des Fensters, danach {num(rules.time_after_factor, 1)}). Thema = Maximum aus Begriff und Ereignisart.
                            </p>
                            <p className="m-0">
                                Stufen nach festen Regeln: hoch = {rules.stages?.hoch}; mittel = {rules.stages?.mittel}; niedrig = {rules.stages?.niedrig};
                                sonst keine. Meldungen ohne Arbeitgeberbezug (Börsenbericht, Kursziel, Sport, Produkt) eine Stufe tiefer. Die Quellenart ordnet
                                nur innerhalb einer Stufe. Meldungen zum selben Ereignis (gleiche Ereignisart, höchstens {rules.bundle_max_days} Tage Abstand,
                                ähnlicher Titel) sind gebündelt. Höchstens {rules.max_explanations} Einträge. Alle Schwellen sind vorläufige Setzungen.
                            </p>
                        </div>
                    )}
                </div>
            )}
            <p className="m-0 mt-3 text-[11px] text-slate-400">{summary?.note ?? EXPLANATION_NOTE}</p>
        </PageSection>
    )
}
