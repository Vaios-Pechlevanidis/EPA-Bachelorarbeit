import { useEffect, useMemo, useState } from "react"
import { ExternalLink, Newspaper } from "lucide-react"
import { PageSection } from "./PageSection"
import { StageBadge } from "./ExplanationPanel"
import { fmtPeriod } from "@/lib/anomalySeries"
import { useEvidence } from "@/hooks/useEvidence"

/* ============================================================================
   EvidenceSection — "Externe Belege im Ereignisfenster" (Inkrement 4, E18).
   Zeigt zu einer ausgewählten Veränderung, einem Einzelmonat oder einer freien
   Auswahl die Meldungen externer Quellen, deren Datum im Ereignisfenster liegt:
   Datum, Titel als Link (neuer Tab), Herausgeber, Typ als Badge, Sprache als
   Badge bei englischen Meldungen; neueste zuerst, lange Listen werden
   nachgeladen. Dauert die erste Seite länger als zwei Sekunden, nennt ein
   Hinweis den Grund: Die Monate werden zum ersten Mal von den Quellen geladen.
   Wortwahl: "Beleg" = zeitlich nahe Meldung; keine Aussage über Ursachen.
   Inkrement 5: Mit `scores` (item_scores aus explanation_summary des
   Vergleichs) lässt sich die Liste nach Relevanz (Rang der Erklärungsansätze)
   statt nach Datum sortieren und nach Ereignisart filtern; dafür werden alle
   Belege des Fensters geladen. Je Beleg stehen dann Stufe und Ereignisart.
   ============================================================================ */

const SORTS = [
    { key: "date", label: "Datum" },
    { key: "relevance", label: "Relevanz" },
]
const NO_CATEGORY = "__none__"
const selectClass =
    "h-7 rounded-md border border-slate-300 bg-white px-2 text-[12px] text-slate-800 focus:outline-none focus:ring-1 focus:ring-slate-400 disabled:opacity-50 max-w-[260px]"

const TYPE_LABELS = {
    news: { label: "Meldung", className: "bg-slate-100 text-slate-600", title: "Nachrichtenmeldung (Google News RSS), Verlässlichkeit mittel" },
    adhoc: { label: "Ad-hoc", className: "bg-blue-100 text-slate-700", title: "Pflicht- oder Unternehmensmitteilung (EQS News), Verlässlichkeit hoch" },
    global: { label: "Allgemeines Ereignis, Hypothese", className: "bg-amber-100 text-slate-700", title: "Allgemeines Ereignis aus global_events.json (vom Autor bestätigt), Verlässlichkeit: Hypothese" },
}

/* Kästchen "Allgemeine Ereignisse" im Kopf des Monatsverlaufs (Overlay, Standard aus). */
export function EventsToggle({ checked, onChange }) {
    return (
        <label className="inline-flex items-center gap-1.5 text-[12px] text-slate-700 cursor-pointer select-none"
            onClick={(e) => e.stopPropagation()}>
            <input
                type="checkbox"
                className="accent-amber-600"
                checked={checked}
                onChange={(e) => onChange(e.target.checked)}
            />
            Allgemeine Ereignisse
        </label>
    )
}

const fmtDay = (value) => {
    if (!value) return "ohne Datum"
    const d = new Date(value.length === 10 ? `${value}T12:00:00` : value)
    return Number.isNaN(d.getTime()) ? "ohne Datum" : d.toLocaleDateString("de-DE", { day: "2-digit", month: "2-digit", year: "numeric" })
}

const fmtStamp = (value) => {
    if (!value) return null
    const d = new Date(value)
    return Number.isNaN(d.getTime()) ? null : d.toLocaleDateString("de-DE", { day: "2-digit", month: "2-digit", year: "numeric" })
}

/* "12 Belege: 10 Meldungen, 2 Ad-hoc" */
function countsText(total, counts) {
    if (!total) return "kein Beleg"
    const parts = [
        counts?.news ? `${counts.news} ${counts.news === 1 ? "Meldung" : "Meldungen"}` : null,
        counts?.adhoc ? `${counts.adhoc} Ad-hoc` : null,
        counts?.global ? `${counts.global} ${counts.global === 1 ? "allgemeines Ereignis" : "allgemeine Ereignisse"}` : null,
    ].filter(Boolean)
    return `${total} ${total === 1 ? "Beleg" : "Belege"}${parts.length ? `: ${parts.join(", ")}` : ""}`
}

/* "Okt. 2022 – Feb. 2023 (5 Monate: 3 vor dem Übergang, 1 danach)" */
function windowText(window) {
    if (!window) return ""
    const span = window.from === window.to ? fmtPeriod(window.from) : `${fmtPeriod(window.from)} – ${fmtPeriod(window.to)}`
    const ref = window.kind === "auswahl" ? "um die Auswahl" : window.kind === "einzelmonat" ? "um den Monat" : "um den Übergang"
    return `${span} (${window.months} ${window.months === 1 ? "Monat" : "Monate"}: ${window.window_before} davor, ${window.window_after} danach, ${ref})`
}

function TypeBadge({ type }) {
    const t = TYPE_LABELS[type] ?? { label: type, className: "bg-slate-100 text-slate-600", title: "" }
    return (
        <span className={`flex-none inline-flex items-center px-1.5 py-0.5 rounded-full text-[10px] uppercase tracking-wider ${t.className}`} title={t.title}>
            {t.label}
        </span>
    )
}

/* score = item_scores[item.id] aus den Erklärungsansätzen (Stufe, Rang, Ereignisart), optional. */
function EvidenceRow({ item, score = null, rules = null }) {
    return (
        <li className="border-t border-slate-100 first:border-t-0 py-2 flex items-start gap-3">
            <span className="w-[76px] flex-none text-[11px] text-slate-500 tnum pt-0.5">{fmtDay(item.date)}</span>
            <span className="min-w-0 flex-1">
                <span className="flex items-center gap-2 min-w-0 flex-wrap">
                    <a
                        href={item.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-[12.5px] font-medium text-slate-900 hover:underline underline-offset-2 inline-flex items-center gap-1 min-w-0"
                        title="Meldung beim Herausgeber öffnen (neuer Tab)"
                    >
                        <span className="truncate">{item.title}</span>
                        <ExternalLink className="w-3 h-3 flex-none text-slate-400" aria-hidden="true" />
                    </a>
                    <TypeBadge type={item.source_type} />
                    {item.language === "en" && (
                        <span className="flex-none inline-flex items-center px-1.5 py-0.5 rounded-full border border-slate-300 text-slate-500 text-[10px] uppercase tracking-wider" title="englischsprachige Meldung">
                            EN
                        </span>
                    )}
                    {score && score.stage !== "keine" && <StageBadge stage={score.stage} rule={rules?.stages?.[score.stage]} small />}
                </span>
                <span className="block mt-0.5 text-[11px] text-slate-500">
                    {item.event
                        ? `${fmtPeriod(item.event.from)} – ${fmtPeriod(item.event.to)}${item.event.scope ? ` · ${item.event.scope}` : ""}${item.event.note ? ` · ${item.event.note}` : ""}`
                        : `${item.publisher || (item.source === "eqs" ? "EQS News" : "Herausgeber unbekannt")}${item.issuer ? ` · Mitteilung von ${item.issuer}` : ""}${item.category ? ` · ${item.category}` : ""}`}
                    {score?.category_label ? ` · Ereignisart: ${score.category_label}` : ""}
                    {score?.terms?.length ? ` · Begriff: ${score.terms.map((t) => `‚${t}‘`).join(", ")}` : ""}
                    {score?.company_in_title === false ? " · Unternehmen im Titel nicht genannt" : ""}
                </span>
            </span>
        </li>
    )
}

/* Umschaltung der Sortierung und Filter nach Ereignisart (Kopf des Abschnitts). */
function ListControls({ sort, onSort, category, onCategory, categories, enabled }) {
    const hint = enabled ? "" : "Relevanz und Ereignisart folgen aus den Erklärungsansätzen oben; sie werden geladen…"
    return (
        <>
            <div className="ds-time-filter" role="group" aria-label="Sortierung der Belege" title={hint || "Sortierung: Datum (neueste zuerst) oder Relevanz (Rang der Erklärungsansätze)"}>
                {SORTS.map((s) => (
                    <button
                        key={s.key}
                        type="button"
                        aria-pressed={sort === s.key}
                        className={`ds-time-btn${sort === s.key ? " active" : ""}`}
                        disabled={!enabled && s.key === "relevance"}
                        onClick={() => onSort(s.key)}
                    >
                        {s.label}
                    </button>
                ))}
            </div>
            <select
                className={selectClass}
                value={category}
                onChange={(e) => onCategory(e.target.value)}
                disabled={!enabled}
                aria-label="Filter nach Ereignisart"
                title={hint || "Nur Belege dieser Ereignisart (aus Schlüsselwörtern im Titel)"}
            >
                <option value="">Alle Ereignisarten</option>
                {categories.map((c) => <option key={c.id} value={c.id}>{c.label}</option>)}
                <option value={NO_CATEGORY}>ohne Ereignisart</option>
            </select>
        </>
    )
}

/* Stand je Quelle: "Google News RSS: 5 von 5 Monaten vorhanden, 5 gerade abgerufen, Stand 08.10.2026; 1 Monat nicht abrufbar". */
function SourcesLine({ sources }) {
    if (!sources) return null
    const parts = Object.values(sources).map((s) => {
        const stored = s.from_store + s.fetched_now
        const bits = [`${stored} von ${s.months} ${s.months === 1 ? "Monat" : "Monaten"} vorhanden`]
        if (s.fetched_now) bits.push(`${s.fetched_now} gerade abgerufen`)
        if (s.fetched_at) bits.push(`Stand ${fmtStamp(s.fetched_at)}`)
        if (s.errors?.length) bits.push(`${s.errors.length} ${s.errors.length === 1 ? "Monat" : "Monate"} nicht abrufbar`)
        return `${s.label}: ${bits.join(", ")}`
    })
    return <p className="m-0 mt-2 text-[11px] text-slate-400">{parts.join(" · ")}</p>
}

/* Abschnitt auf der Detailseite. anomalyId für Veränderung oder Einzelmonat,
   sonst selection {from, to}; group = {source, dimension, status} wie die Erkennung.
   scores = item_scores aus explanation_summary des Vergleichs (null, solange er lädt),
   rules = explanation_summary.rules (Tooltips der Stufen). */
export function EvidenceSection({ companyId, anomalyId = null, selection = null, group = {}, eyebrow = "EXTERNE BELEGE", className = "", scores = null, rules = null }) {
    const evidence = useEvidence(companyId, { anomalyId, selection, ...group })
    const data = evidence.data
    const [sort, setSort] = useState("date")
    const [category, setCategory] = useState("")
    const hasScores = Boolean(scores)
    const needAll = sort === "relevance" || category !== ""
    // Für Sortierung und Filter müssen alle Belege des Fensters geladen sein.
    useEffect(() => {
        if (needAll && evidence.hasMore && !evidence.loadingMore) evidence.loadAll()
    }, [needAll, evidence])
    const categories = useMemo(() => {
        const found = new Map()
        Object.values(scores ?? {}).forEach((s) => {
            if (s.category && !found.has(s.category)) found.set(s.category, s.category_label ?? s.category)
        })
        return [...found.entries()].map(([id, label]) => ({ id, label })).sort((a, b) => a.label.localeCompare(b.label, "de"))
    }, [scores])
    const items = useMemo(() => {
        let list = evidence.items
        if (category) {
            list = list.filter((item) => {
                const cat = scores?.[item.id]?.category ?? null
                return category === NO_CATEGORY ? cat == null : cat === category
            })
        }
        if (sort === "relevance" && scores) {
            list = [...list].sort((a, b) => (scores[a.id]?.rank ?? Infinity) - (scores[b.id]?.rank ?? Infinity) || String(b.date ?? "").localeCompare(String(a.date ?? "")))
        }
        return list
    }, [evidence.items, category, sort, scores])
    const listNote = [
        sort === "relevance" ? "sortiert nach Relevanz" : null,
        category ? `Ereignisart: ${category === NO_CATEGORY ? "ohne" : categories.find((c) => c.id === category)?.label ?? category} (${items.length} von ${evidence.items.length})` : null,
    ].filter(Boolean).join(" · ")
    const subtitle = evidence.loading
        ? "Lade Belege…"
        : evidence.error
            ? "Belege konnten nicht geladen werden"
            : data
                ? `Ereignisfenster ${windowText(data.window)} · ${countsText(data.total, data.counts)}${listNote ? ` · ${listNote}` : ""}`
                : ""
    return (
        <PageSection
            className={className}
            icon={<Newspaper />}
            eyebrow={eyebrow}
            title="Externe Belege im Ereignisfenster"
            subtitle={subtitle}
            actions={!evidence.loading && !evidence.error && evidence.total > 0 && (
                <ListControls sort={sort} onSort={setSort} category={category} onCategory={setCategory} categories={categories} enabled={hasScores} />
            )}
        >
            {evidence.loading ? (
                <div className="space-y-1">
                    <p className="m-0 text-[12px] text-slate-500">Lade Belege…</p>
                    {evidence.slow && (
                        <p className="m-0 text-[12px] text-slate-500" role="status">
                            Belege für diesen Zeitraum werden zum ersten Mal von den Quellen geladen; das dauert einige
                            Sekunden (je Quelle ein Abruf je Monat mit zwei Sekunden Abstand). Beim nächsten Aufruf kommen sie
                            aus dem Speicher.
                        </p>
                    )}
                </div>
            ) : evidence.error ? (
                <p className="m-0 text-[12px] text-slate-500">Belege konnten nicht geladen werden: {evidence.error}</p>
            ) : evidence.items.length === 0 ? (
                <div className="space-y-1">
                    <p className="m-0 text-[12.5px] font-medium text-slate-700">Kein Beleg im Fenster gefunden.</p>
                    {data?.reason && data.reason !== "Kein Beleg im Fenster gefunden." && (
                        <p className="m-0 text-[12px] text-slate-500">{data.reason}</p>
                    )}
                    <p className="m-0 text-[12px] text-slate-500">
                        Bekannte Grenzen: Für ältere Zeiträume liefern die Quellen deutlich weniger Meldungen, für kleine
                        Unternehmen oft keine; mehrdeutige Namen bringen fremde Treffer. Ein fehlender Beleg heißt nicht,
                        dass nichts geschehen ist.
                    </p>
                </div>
            ) : (
                <>
                    {needAll && evidence.loadingAll && (
                        <p className="m-0 mb-2 text-[12px] text-slate-500" role="status">Lade alle {evidence.total} Belege für Sortierung und Filter…</p>
                    )}
                    {items.length === 0 && category ? (
                        <p className="m-0 text-[12px] text-slate-500">Kein Beleg dieser Ereignisart im Fenster.</p>
                    ) : (
                        <ul className="m-0 p-0 list-none">
                            {items.map((item) => <EvidenceRow key={item.id} item={item} score={scores?.[item.id] ?? null} rules={rules} />)}
                        </ul>
                    )}
                    {evidence.hasMore && !needAll && (
                        <button
                            type="button"
                            className="mt-2 text-[12px] underline underline-offset-2 text-slate-700 hover:text-slate-900 disabled:opacity-50"
                            onClick={evidence.loadMore}
                            disabled={evidence.loadingMore}
                        >
                            {evidence.loadingMore ? "Lade weitere…" : `Weitere Belege laden (${evidence.items.length} von ${evidence.total})`}
                        </button>
                    )}
                </>
            )}
            {!evidence.loading && !evidence.error && <SourcesLine sources={data?.sources} />}
            <p className="m-0 mt-3 text-[11px] text-slate-400">
                {data?.note ?? "Belege sind zeitlich nahe Meldungen aus externen Quellen. Sie sind keine Aussage über Ursachen; interne Auslöser sind von außen nicht sichtbar."}
            </p>
        </PageSection>
    )
}
