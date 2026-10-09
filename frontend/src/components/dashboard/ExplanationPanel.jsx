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
   Iteration 2 (Befund 1 der Bewertung vom 2026-10-08): Die Stufe beschreibt,
   was gefunden wurde ("Wortbezug und Ereignisart", "Wortbezug oder
   Themenbezug", "nur Ereignisart"), und bewertet nicht; alle Badges in
   derselben neutralen Farbe, keine Ampel. Die Schlüssel der Schnittstelle
   (hoch, mittel, niedrig) bleiben; die Bezeichnung kommt als stage_label bzw.
   rules.stage_labels aus der Antwort. Befund 3: In der obersten Liste steht
   höchstens ein Eintrag je Ereignisart (ohne Ereignisart je Begriff); die
   übrigen Bündel der Gruppe (entry.group.others) sind aufklappbar, mit Anzahl
   und Herausgebern. Beides ändert keine Stufe und keine Zahl der Auswertung.
   ============================================================================ */

export const EXPLANATION_NOTE = "Die Einstufung beruht auf Titeln und Wortbezügen. Sie zeigt mögliche Zusammenhänge, keine Ursachen."

/* Bezeichnung je Stufe (Rückfall, wenn die Antwort keine rules.stage_labels trägt). */
const STAGE_LABELS = {
    hoch: "Wortbezug und Ereignisart",
    mittel: "Wortbezug oder Themenbezug",
    niedrig: "nur Ereignisart",
    keine: "kein Bezug",
}
const STAGE_ORDER = ["hoch", "mittel", "niedrig"]
/* Eine neutrale Farbe für alle Stufen: die Bezeichnung trägt die Aussage, nicht die Farbe. */
const STAGE_CLASS = "bg-slate-100 text-slate-700 border border-slate-300"

const stageLabel = (stage, rules = null) => rules?.stage_labels?.[stage] ?? STAGE_LABELS[stage] ?? stage

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

/* Stufe als Badge mit ihrer Bezeichnung; rules = explanation_summary.rules (Bezeichnungen
   und Regeln für den Tooltip). Der Schlüssel der Stufe steht nur im Tooltip. */
export function StageBadge({ stage, rules = null, small = false }) {
    const label = stageLabel(stage, rules)
    const rule = rules?.stages?.[stage]
    return (
        <span
            className={`flex-none inline-flex items-center rounded-full font-medium tracking-wide ${small ? "px-1.5 py-0.5 text-[9.5px]" : "px-2 py-0.5 text-[10px]"} ${STAGE_CLASS}`}
            title={`${label} (Schlüssel: ${stage})${rule ? `; Regel: ${rule}` : ""}`}
        >
            {label}
        </span>
    )
}

function Chip({ children, title, strong = false }) {
    return (
        <span
            className={`inline-flex items-center gap-1 rounded-full border border-slate-200 bg-slate-50 px-1.5 py-0.5 text-[10.5px] max-w-full break-words ${strong ? "text-slate-800 font-medium" : "text-slate-600"}`}
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
                <li key={item.id} className="flex flex-col sm:flex-row sm:items-start gap-x-2 gap-y-0.5 text-[11.5px] min-w-0">
                    <span className="sm:w-[70px] flex-none text-slate-500 tnum">{fmtDay(item.date)}</span>
                    <span className="min-w-0 flex-1">
                        <a href={item.url} target="_blank" rel="noopener noreferrer" className="text-slate-800 hover:underline underline-offset-2 inline-flex items-center gap-1 min-w-0 max-w-full">
                            <span className="truncate">{item.title}</span>
                            <ExternalLink className="w-3 h-3 flex-none text-slate-400" aria-hidden="true" />
                        </a>
                        <span className="block text-[10.5px] text-slate-500 break-words">
                            {item.publisher || "Herausgeber unbekannt"} · {TYPE_LABELS[item.source_type] ?? item.source_type}
                            {item.issuer ? ` · Mitteilung von ${item.issuer}` : ""} · Zeit {num(item.time_match, 2)}, Thema {num(item.topic_match, 2)}
                        </span>
                    </span>
                    <span className="flex-none self-start"><StageBadge stage={item.stage} rules={rules} small /></span>
                </li>
            ))}
        </ul>
    )
}

/* Weitere Bündel derselben Gruppe (Ereignisart oder Begriff), aufklappbar unter dem Stellvertreter. */
function GroupMembers({ others, rules }) {
    return (
        <ul className="m-0 mt-2 p-0 list-none border-l-2 border-slate-200 pl-3 space-y-1.5">
            {others.map((o) => (
                <li key={o.id} className="flex flex-col sm:flex-row sm:items-start gap-x-2 gap-y-0.5 text-[11.5px] min-w-0">
                    <span className="sm:w-[70px] flex-none text-slate-500 tnum">{fmtDay(o.date)}</span>
                    <span className="min-w-0 flex-1">
                        <a href={o.url} target="_blank" rel="noopener noreferrer" className="text-slate-800 hover:underline underline-offset-2 inline-flex items-center gap-1 min-w-0 max-w-full">
                            <span className="truncate">{o.event}</span>
                            <ExternalLink className="w-3 h-3 flex-none text-slate-400" aria-hidden="true" />
                        </a>
                        <span className="block text-[10.5px] text-slate-500 break-words">
                            {o.source || "Herausgeber unbekannt"} · {TYPE_LABELS[o.source_type] ?? o.source_type}
                            {o.issuer ? ` · Mitteilung von ${o.issuer}` : ""}
                            {o.n_items > 1 ? ` · ${o.n_items} Meldungen (${(o.publishers ?? []).join(", ")})` : ""}
                            {" "}· {o.time_phrase} · Zeit {num(o.time_match, 2)}, Thema {num(o.topic_match, 2)}
                            {o.terms?.length ? ` · Begriff: ${o.terms.map((t) => `‚${t}‘`).join(", ")}` : ""}
                        </span>
                    </span>
                    <span className="flex-none self-start"><StageBadge stage={o.confidence} rules={rules} small /></span>
                </li>
            ))}
        </ul>
    )
}

function ExplanationEntry({ entry, rules }) {
    const [open, setOpen] = useState(false)
    const [groupOpen, setGroupOpen] = useState(false)
    const bundled = entry.n_items > 1
    const group = entry.group ?? null
    const others = group?.others ?? []
    const groupLabel = group ? (group.kind === "ereignisart" ? `Ereignisart ${group.label}` : group.label) : ""
    return (
        <li className="border-t border-slate-100 first:border-t-0 py-3 flex flex-col sm:flex-row sm:items-start gap-x-3 gap-y-1.5 min-w-0">
            <div className="flex-none pt-0.5 sm:w-[118px]">
                <StageBadge stage={entry.confidence} rules={rules} />
            </div>
            <div className="min-w-0 flex-1">
                <p className="m-0 text-[12.5px] text-slate-800 leading-5 break-words">{entry.text}</p>
                <p className="m-0 mt-1 text-[11.5px] text-slate-600 flex items-center gap-1.5 flex-wrap min-w-0">
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
                {others.length > 0 && (
                    <div className="mt-1.5">
                        <p className="m-0 text-[11px] text-slate-600 flex flex-wrap items-center gap-x-1.5 gap-y-0.5 min-w-0">
                            <button
                                type="button"
                                className="inline-flex items-start gap-1 text-left text-slate-600 hover:text-slate-900 underline-offset-2 hover:underline min-w-0"
                                onClick={() => setGroupOpen((v) => !v)}
                                aria-expanded={groupOpen}
                                title={`In der obersten Liste steht je ${group.kind === "ereignisart" ? "Ereignisart" : "Begriff"} ein Eintrag; die übrigen Bündel der Gruppe stehen hier.`}
                            >
                                {groupOpen ? <ChevronDown className="w-3 h-3" aria-hidden="true" /> : <ChevronRight className="w-3 h-3" aria-hidden="true" />}
                                {groupOpen ? `Weitere Einträge zu ${groupLabel} ausblenden` : `${others.length} ${others.length === 1 ? "weiterer Eintrag" : "weitere Einträge"} zu ${groupLabel} anzeigen`}
                            </button>
                            <span className="text-slate-400 break-words min-w-0">
                                · Gruppe: {group.n_bundles} Bündel, {group.n_items} {group.n_items === 1 ? "Meldung" : "Meldungen"} ({(group.publishers ?? []).join(", ")})
                            </span>
                        </p>
                        {groupOpen && <GroupMembers others={others} rules={rules} />}
                    </div>
                )}
            </div>
        </li>
    )
}

function stageCounts(n, rules) {
    if (!n) return ""
    return STAGE_ORDER.filter((s) => n[s]).map((s) => `${stageLabel(s, rules)} ${n[s]}`).join(", ")
}

/* Abschnitt über der Belegliste. data = Antwort des Vergleichs (explanations, explanation_summary). */
export function ExplanationPanel({ data, loading, error, eyebrow = "ERKLÄRUNGSANSÄTZE", className = "" }) {
    const [showRules, setShowRules] = useState(false)
    const summary = data?.explanation_summary ?? null
    const entries = data?.explanations ?? []
    const rules = summary?.rules ?? null
    const open = summary?.state === "offen"
    const subtitle = loading
        ? "Erklärungsansätze werden berechnet…"
        : error
            ? "Erklärungsansätze konnten nicht geladen werden"
            : summary
                ? open
                    ? `offen · ${summary.n_items} ${summary.n_items === 1 ? "Beleg" : "Belege"} im Ereignisfenster, keiner erreicht die Stufe niedrig`
                    : `${entries.length} ${entries.length === 1 ? "Ansatz" : "Ansätze"} aus ${summary.n_items} Belegen (${summary.n_bundles} Bündel${summary.n_groups != null ? `, ${summary.n_groups} ${summary.n_groups === 1 ? "Gruppe" : "Gruppen"} nach Ereignisart` : ""})${stageCounts(summary.n_by_stage, rules) ? ` · Bündel je Stufe: ${stageCounts(summary.n_by_stage, rules)}` : ""}`
                : ""
    return (
        <PageSection className={className} icon={<Lightbulb />} eyebrow={eyebrow} title="Mögliche Zusammenhänge" subtitle={subtitle} basis={["external", "text"]}>
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
                                abnehmend zum Rand des Fensters, danach {num(rules.time_after_factor, 1)}). Thema = Maximum aus Begriff und Ereignisart
                                (ordnet nur innerhalb einer Stufe).
                            </p>
                            <p className="m-0">
                                Stufen nach festen Regeln{rules.version ? ` (Fassung ${rules.version}${rules.version_date ? `, ${rules.version_date}` : ""})` : ""}: <span className="font-medium">{stageLabel("hoch", rules)}</span> (Schlüssel hoch) = {rules.stages?.hoch};
                                {" "}<span className="font-medium">{stageLabel("mittel", rules)}</span> (Schlüssel mittel) = {rules.stages?.mittel};
                                {" "}<span className="font-medium">{stageLabel("niedrig", rules)}</span> (Schlüssel niedrig) = {rules.stages?.niedrig};
                                sonst kein Bezug. Meldungen ohne Arbeitgeberbezug (Börsenbericht, Kursziel, Sport, Produkt) eine Stufe tiefer. Die Quellenart ordnet
                                nur innerhalb einer Stufe. Meldungen zum selben Ereignis (gleiche Ereignisart, höchstens {rules.bundle_max_days} Tage Abstand,
                                ähnlicher Titel) sind gebündelt. In der obersten Liste steht höchstens ein Eintrag je Ereignisart (ohne Ereignisart je Begriff),
                                die übrigen Bündel der Gruppe sind darunter aufklappbar. Höchstens {rules.max_explanations} Einträge. Alle Schwellen sind vorläufige Setzungen.
                            </p>
                            <p className="m-0">
                                {rules.finding_note ?? "In der Auswertung vom 08.10.2026 traten Einträge dieser Art in Zeiträumen ohne Markierung ähnlich häufig auf wie bei Markierungen. Sie sind Kandidaten für die eigene Einordnung."}
                            </p>
                        </div>
                    )}
                </div>
            )}
            <p className="m-0 mt-3 text-[11px] text-slate-400">{summary?.note ?? EXPLANATION_NOTE}</p>
        </PageSection>
    )
}
