import { useState } from "react"
import { Star } from "lucide-react"
import ReviewDetailModal from "./modals/ReviewDetailModal"
import { statusLabel } from "@/lib/reviewerStatus"
import { HighlightedText } from "./HighlightedText"
import { REVIEW_PAGE_SIZE } from "@/hooks/useReviewPages"
import { dimensionLabel } from "@/lib/ratingCategories"

/* ============================================================================
   PeriodReviews — Bewertungen eines Vergleichsfensters (Inkrement 2).
   Liste der Einzelbewertungen vor bzw. ab dem markierten Monat einer
   auffälligen Veränderung; Daten aus useReviewPages (seitenweise geladen).
   Ein Klick öffnet die Bewertung im vorhandenen ReviewDetailModal. Ist eine
   Dimension gewählt, sind die Fundstellen ihres Schlüsselwort-Themas markiert
   (Textauszug und Detailfenster).
   Nachtrag 2026-10-18: Jede Zeile nennt die Schlüsselwort-Themen der Bewertung;
   der Themenfilter lässt nur Bewertungen eines Themas übrig (dessen Fundstellen
   sind dann markiert), die Sortierung ordnet nach dem Tag, an dem die Bewertung
   geschrieben wurde (neueste oder älteste zuerst).
   Dimension als globaler Filter (2026-10-23): Mit einer Einzeldimension (dimension)
   enthält die Liste nur Bewertungen, die zur Dimension gehören; die Sternespalte
   zeigt dann die Sterne der Dimension (die Gesamtnote klein darunter) und der
   Textauszug, wenn vorhanden, den Kommentar zur Kategorie statt des allgemeinen
   Textauszugs (Fundstellen markiert).
   ============================================================================ */

const WINDOW_SIDES = [
    { key: "before", label: "davor" },
    { key: "after", label: "ab dem markierten Monat" },
]

/* Umschalter "davor" / "ab dem markierten Monat" im Stil des Zeitfilters. */
export function WindowSideToggle({ value, onChange, labels = null }) {
    return (
        <div className="ds-time-filter" role="group" aria-label="Vergleichsfenster">
            {WINDOW_SIDES.map(({ key, label: defaultLabel }) => ({ key, label: labels?.[key] ?? defaultLabel })).map(({ key, label }) => (
                <button
                    key={key}
                    type="button"
                    aria-pressed={value === key}
                    className={`ds-time-btn${value === key ? " active" : ""}`}
                    onClick={() => onChange(key)}
                >
                    {label}
                </button>
            ))}
        </div>
    )
}

const fmtDay = (value) => {
    if (!value) return "ohne Datum"
    const d = new Date(value)
    return Number.isNaN(d.getTime()) ? "ohne Datum" : d.toLocaleDateString("de-DE", { day: "2-digit", month: "2-digit", year: "numeric" })
}

const fmtStars = (v) => (v == null || !Number.isFinite(Number(v)) ? "–" : Number(v).toLocaleString("de-DE", { minimumFractionDigits: 1, maximumFractionDigits: 1 }))

/* Themen der Bewertung als kleine Marken; das markierte Thema (Filter bzw.
   Dimension) in Bernstein wie seine Fundstellen im Text. */
function TopicTags({ topics, marked }) {
    if (!topics) return null
    if (!topics.length) return <span className="block mt-1 text-[10.5px] text-slate-400">kein Thema erkannt</span>
    return (
        <span className="flex flex-wrap gap-1 mt-1" aria-label="Themen der Bewertung">
            {topics.map((t) => (
                <span
                    key={t}
                    className={`inline-flex items-center px-1.5 py-px rounded-full text-[10.5px] ${t === marked ? "bg-amber-100 text-slate-800 font-medium" : "bg-slate-100 text-slate-600"}`}
                >
                    {t}
                </span>
            ))}
        </span>
    )
}

function ReviewRow({ item, onOpen, topic, dimension = null }) {
    const review = item.fullReview ?? {}
    const status = statusLabel(review.status)
    // Bezug zur gewählten Dimension (Sterne, Kommentar zur Kategorie), nur mit Filter.
    const dim = dimension ? item.dimension ?? null : null
    const dimLabel = dimension ? dimensionLabel(dimension) : ""
    return (
        <li className="border-t border-slate-100 first:border-t-0">
            <button
                type="button"
                onClick={onOpen}
                className="w-full text-left flex items-start gap-3 py-2.5 px-2 -mx-2 rounded-md hover:bg-slate-50 transition-colors"
            >
                <span className="w-[76px] flex-none text-[11px] text-slate-500 tnum pt-0.5">{fmtDay(review.datum)}</span>
                {/* Sternespalte: mit gewählter Dimension deren Sterne, die Gesamtnote klein darunter;
                    sonst die Gesamtnote wie bisher. */}
                {dim && dim.rating != null ? (
                    <span className="w-[64px] flex-none flex flex-col pt-px">
                        <span
                            className="inline-flex items-center gap-1 text-[12px] font-semibold text-slate-800 tnum"
                            title={`Sterne der Dimension ${dimLabel} in dieser Bewertung`}
                        >
                            <Star className="w-3 h-3 fill-amber-400 text-amber-400" strokeWidth={1.5} aria-hidden="true" />
                            {fmtStars(dim.rating)}
                        </span>
                        <span className="text-[10.5px] text-slate-500 tnum leading-tight" title="Gesamtbewertung dieser Bewertung">
                            Gesamt {fmtStars(review.durchschnittsbewertung)}
                        </span>
                    </span>
                ) : (
                    <span
                        className={`${dim ? "w-[64px]" : "w-[46px]"} flex-none inline-flex items-center gap-1 text-[12px] font-semibold text-slate-800 tnum pt-px`}
                        title={dim ? `Gesamtbewertung; keine Sterne für ${dimLabel} in dieser Bewertung` : undefined}
                    >
                        <Star className="w-3 h-3 fill-amber-400 text-amber-400" strokeWidth={1.5} aria-hidden="true" />
                        {fmtStars(review.durchschnittsbewertung)}
                    </span>
                )}
                <span className="min-w-0 flex-1">
                    <span className="flex items-center gap-2 min-w-0">
                        <span className="text-[12.5px] font-medium text-slate-900 truncate">{review.titel || "Ohne Titel"}</span>
                        {status && (
                            <span className="flex-none inline-flex items-center px-1.5 py-0.5 rounded-full bg-slate-100 text-slate-600 text-[10px] uppercase tracking-wider">
                                {status}
                            </span>
                        )}
                    </span>
                    <span className="block mt-0.5 text-[12px] text-slate-500 leading-snug line-clamp-2">
                        {dim?.comment ? (
                            <>
                                <span className="text-slate-400">Kommentar zu {dimLabel} · </span>
                                <HighlightedText text={dim.comment} spans={item.highlights?.comment} title={topic ? `Thema ${topic}` : undefined} />
                            </>
                        ) : item.preview
                            ? <HighlightedText text={item.preview} spans={item.highlights?.preview} title={topic ? `Thema ${topic}` : undefined} />
                            : "Kein Freitext."}
                    </span>
                    <TopicTags topics={item.topics} marked={topic} />
                </span>
            </button>
        </li>
    )
}

const ORDERS = [
    { key: "desc", label: "neueste zuerst" },
    { key: "asc", label: "älteste zuerst" },
]
const selectClass =
    "h-7 rounded-md border border-slate-300 bg-white px-2 text-[12px] text-slate-800 focus:outline-none focus:ring-1 focus:ring-slate-400 disabled:opacity-50 max-w-[260px]"

/* Sortierung nach Datum und Themenfilter im Kopf des Dialogs. topics =
   {counts: [{topic, n}], withoutTopic} des Zeitraums (null, solange er lädt);
   value = gefiltertes Thema oder null. dimension (2026-10-23): gilt die Dimension
   als Filter, heißt die Grundauswahl des Feldes wie die Dimension statt "Alle Themen"
   (alle Bewertungen zur Dimension; ein Thema darunter schränkt weiter ein). */
export function ReviewListControls({ order, onOrder, topics, value, onTopic, dimension = null }) {
    const counts = topics?.counts ?? []
    const allLabel = dimension ? dimensionLabel(dimension) : "Alle Themen"
    const selectTitle = dimension
        ? `Bewertungen zur Dimension ${dimensionLabel(dimension)}; ein Thema darunter zeigt nur die, die es nennen (Zahl = Bewertungen des Zeitraums mit dem Thema)`
        : "Nur Bewertungen, die dieses Thema nennen (Schlüsselwort in Titel, Freitext oder Kategorie-Kommentar); Zahl = Bewertungen des Zeitraums mit dem Thema"
    // Gewähltes Thema ohne Treffer im Zeitraum (z. B. nach dem Wechsel davor / danach) bleibt wählbar.
    const options = value && !counts.some((c) => c.topic === value) ? [...counts, { topic: value, n: 0 }] : counts
    return (
        <>
            <div className="ds-time-filter" role="group" aria-label="Sortierung nach Datum" title="Sortiert nach dem Tag, an dem die Bewertung geschrieben wurde">
                {ORDERS.map((o) => (
                    <button
                        key={o.key}
                        type="button"
                        aria-pressed={order === o.key}
                        className={`ds-time-btn${order === o.key ? " active" : ""}`}
                        onClick={() => onOrder(o.key)}
                    >
                        {o.label}
                    </button>
                ))}
            </div>
            <select
                className={selectClass}
                value={value ?? ""}
                onChange={(e) => onTopic(e.target.value || null)}
                disabled={!topics && !value}
                aria-label="Filter nach Thema"
                title={selectTitle}
            >
                <option value="">{allLabel}</option>
                {options.map((c) => <option key={c.topic} value={c.topic}>{c.topic} ({c.n})</option>)}
            </select>
        </>
    )
}

/* Liste mit Nachladen. pages: Rückgabe von useReviewPages; dimension: Schlüssel der
   Einzeldimension, wenn sie als Filter gilt (2026-10-23), sonst null. */
export function PeriodReviewList({ pages, emptyText = "Keine Bewertungen in diesem Zeitraum.", dimension = null }) {
    const { items, total, loading, loadingMore, error, hasMore, loadMore } = pages
    const topic = pages.markedTopic ?? null
    const [openIndex, setOpenIndex] = useState(null)

    if (loading) {
        return (
            <div className="flex items-center gap-2 py-3">
                <div className="animate-spin rounded-full h-4 w-4 border-2 border-slate-200 border-t-slate-600"></div>
                <p className="m-0 text-slate-600 text-[12px]">Lade Bewertungen…</p>
            </div>
        )
    }
    if (error && !items.length) {
        return <p className="m-0 text-[12px] text-slate-500">Bewertungen konnten nicht geladen werden: {error}</p>
    }
    if (!items.length) return <p className="m-0 text-[12px] text-slate-500">{emptyText}</p>

    const navigate = (i) => {
        setOpenIndex(i)
        if (hasMore && i >= items.length - 2) loadMore()
    }

    return (
        <>
            <ul className="m-0 p-0 list-none">
                {items.map((item, i) => (
                    <ReviewRow key={`${item.id}-${i}`} item={item} onOpen={() => setOpenIndex(i)} topic={topic} dimension={dimension} />
                ))}
            </ul>
            <div className="mt-3 flex flex-wrap items-center gap-3 text-[11px] text-slate-500">
                <span className="tnum">{items.length} von {total} angezeigt</span>
                {hasMore && (
                    <button
                        type="button"
                        onClick={loadMore}
                        disabled={loadingMore}
                        className="h-7 px-2.5 rounded-md border border-slate-300 bg-white text-[12px] font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-50"
                    >
                        {loadingMore ? "Lade…" : `Weitere ${Math.min(REVIEW_PAGE_SIZE, total - items.length)} laden`}
                    </button>
                )}
                {error && <span>Nachladen fehlgeschlagen: {error}</span>}
            </div>
            <ReviewDetailModal
                open={openIndex != null && Boolean(items[openIndex])}
                onOpenChange={(open) => !open && setOpenIndex(null)}
                reviewDetail={openIndex != null ? items[openIndex] : null}
                allReviewDetails={items}
                currentIndex={openIndex ?? 0}
                onNavigate={navigate}
                highlightTopic={topic}
                dimension={dimension}
            />
        </>
    )
}
