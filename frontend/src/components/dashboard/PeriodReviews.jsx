import { useState } from "react"
import { Star } from "lucide-react"
import ReviewDetailModal from "./modals/ReviewDetailModal"
import { statusLabel } from "@/lib/reviewerStatus"
import { REVIEW_PAGE_SIZE } from "@/hooks/useReviewPages"

/* ============================================================================
   PeriodReviews — Bewertungen eines Vergleichsfensters (Inkrement 2).
   Liste der Einzelbewertungen vor bzw. ab dem markierten Monat einer
   auffälligen Veränderung; Daten aus useReviewPages (seitenweise geladen).
   Ein Klick öffnet die Bewertung im vorhandenen ReviewDetailModal.
   ============================================================================ */

const WINDOW_SIDES = [
    { key: "before", label: "davor" },
    { key: "after", label: "ab dem markierten Monat" },
]

/* Umschalter "davor" / "ab dem markierten Monat" im Stil des Zeitfilters. */
export function WindowSideToggle({ value, onChange }) {
    return (
        <div className="ds-time-filter" role="group" aria-label="Vergleichsfenster">
            {WINDOW_SIDES.map(({ key, label }) => (
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

function ReviewRow({ item, onOpen }) {
    const review = item.fullReview ?? {}
    const status = statusLabel(review.status)
    return (
        <li className="border-t border-slate-100 first:border-t-0">
            <button
                type="button"
                onClick={onOpen}
                className="w-full text-left flex items-start gap-3 py-2.5 px-2 -mx-2 rounded-md hover:bg-slate-50 transition-colors"
            >
                <span className="w-[76px] flex-none text-[11px] text-slate-500 tnum pt-0.5">{fmtDay(review.datum)}</span>
                <span className="w-[46px] flex-none inline-flex items-center gap-1 text-[12px] font-semibold text-slate-800 tnum pt-px">
                    <Star className="w-3 h-3 fill-amber-400 text-amber-400" strokeWidth={1.5} aria-hidden="true" />
                    {fmtStars(review.durchschnittsbewertung)}
                </span>
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
                        {item.preview || "Kein Freitext."}
                    </span>
                </span>
            </button>
        </li>
    )
}

/* Liste mit Nachladen. pages: Rückgabe von useReviewPages. */
export function PeriodReviewList({ pages, emptyText = "Keine Bewertungen in diesem Zeitraum." }) {
    const { items, total, loading, loadingMore, error, hasMore, loadMore } = pages
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
                    <ReviewRow key={`${item.id}-${i}`} item={item} onOpen={() => setOpenIndex(i)} />
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
            />
        </>
    )
}
