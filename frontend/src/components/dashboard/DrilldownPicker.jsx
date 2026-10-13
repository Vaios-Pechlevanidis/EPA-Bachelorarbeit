import { useState } from "react"
import { CalendarDays, ChevronDown, ChevronLeft, ChevronRight } from "lucide-react"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import { fmtPeriod, periodFromIndex, periodIndex } from "@/lib/anomalySeries"

/* ============================================================================
   DrilldownPicker — freie Auswahl eines Zeitraums für den Drill-down (E17).
   Für Reihen ohne erkannte Veränderung und für Monate, die im Diagramm nicht
   anklickbar sind (z. B. dünne Reihen ohne bewerteten Monat). Die Monate kommen
   aus der Monatsreihe (erster bis letzter Monat mit datierter Bewertung).
   "von" und "bis" öffnen je ein Monatsraster (Jahr wählen, dann Monat) mit der
   Zahl der Bewertungen je Monat; bis 2026-10-13 waren es Auswahllisten mit allen
   Monaten der Reihe, bei langen Reihen über hundert Einträge.
   ============================================================================ */

const buttonClass =
    "h-7 px-2.5 rounded-md border border-slate-300 bg-white text-[12px] font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-50"
const navClass =
    "h-7 w-7 rounded-md grid place-items-center text-slate-500 hover:bg-slate-100 hover:text-slate-900 disabled:opacity-30 disabled:hover:bg-transparent [&_svg]:w-3.5 [&_svg]:h-3.5"

// Monatsnamen wie in fmtPeriod ("Jan.", "März", "Sept.").
const MONTH_LABELS = Array.from({ length: 12 }, (_, i) =>
    new Date(2000, i, 1).toLocaleDateString("de-DE", { month: "short" }))

const yearOf = (period) => Number(String(period).slice(0, 4))
const periodOf = (year, monthIndex) => `${year}-${String(monthIndex + 1).padStart(2, "0")}`
const fmtCount = (n) => (n === 1 ? "1 Bewertung" : `${n.toLocaleString("de-DE")} Bewertungen`)

/* Ein Monat der Reihe: Knopf mit dem Monat; das Fenster zeigt ein Jahr als Raster
   mit 12 Monaten. months: Set der wählbaren Monate; counts: {YYYY-MM: Anzahl} oder
   null; range: {from, to} der aktuellen Auswahl, wird hinterlegt. */
function MonthPicker({ label, value, months, first, last, counts, range, onChange }) {
    const [open, setOpen] = useState(false)
    const [viewYear, setViewYear] = useState(yearOf(value))
    const minYear = yearOf(first)
    const maxYear = yearOf(last)
    const years = Array.from({ length: maxYear - minYear + 1 }, (_, i) => maxYear - i)
    const [lo, hi] = range ? [range.from, range.to].sort((a, b) => periodIndex(a) - periodIndex(b)) : [null, null]
    const inRange = (p) => lo && periodIndex(p) >= periodIndex(lo) && periodIndex(p) <= periodIndex(hi)

    return (
        <Popover open={open} onOpenChange={(next) => { if (next) setViewYear(yearOf(value)); setOpen(next) }}>
            <PopoverTrigger asChild>
                <button
                    type="button"
                    aria-label={`${label}: ${fmtPeriod(value)}`}
                    className="h-7 min-w-[118px] inline-flex items-center gap-1.5 rounded-md border border-slate-300 bg-white px-2 text-[12px] text-slate-800 tnum hover:bg-slate-50 focus:outline-none focus-visible:ring-1 focus-visible:ring-slate-400 [&_svg]:w-3.5 [&_svg]:h-3.5 [&_svg]:flex-none"
                >
                    <CalendarDays className="text-slate-500" />
                    <span className="flex-1 text-left">{fmtPeriod(value)}</span>
                    <ChevronDown className="text-slate-400" />
                </button>
            </PopoverTrigger>
            <PopoverContent
                align="start"
                collisionPadding={12}
                className="w-[272px] p-3 bg-white text-slate-700 border-slate-200"
                // Fokus auf den gewählten Monat statt auf den ersten Pfeil (Tastatur: Tab/Enter)
                onOpenAutoFocus={(e) => {
                    const current = e.currentTarget?.querySelector?.("[aria-pressed='true']")
                    if (current) { e.preventDefault(); current.focus() }
                }}
            >
                {/* Jahr: Pfeile für das Nachbarjahr, Liste für Sprünge */}
                <div className="flex items-center justify-between mb-2">
                    <button type="button" className={navClass} aria-label="Jahr zurück"
                        disabled={viewYear <= minYear} onClick={() => setViewYear((y) => y - 1)}>
                        <ChevronLeft />
                    </button>
                    <select
                        aria-label="Jahr"
                        value={viewYear}
                        onChange={(e) => setViewYear(Number(e.target.value))}
                        className="h-7 rounded-md bg-transparent px-1.5 text-[13px] font-semibold text-slate-900 tnum hover:bg-slate-100 focus:outline-none focus-visible:ring-1 focus-visible:ring-slate-400 cursor-pointer"
                    >
                        {years.map((y) => <option key={y} value={y}>{y}</option>)}
                    </select>
                    <button type="button" className={navClass} aria-label="Jahr vor"
                        disabled={viewYear >= maxYear} onClick={() => setViewYear((y) => y + 1)}>
                        <ChevronRight />
                    </button>
                </div>

                {/* Monate des Jahres; unter dem Namen die Zahl der Bewertungen */}
                <div className="grid grid-cols-4 gap-1" role="group" aria-label={`Monate ${viewYear}`}>
                    {MONTH_LABELS.map((name, i) => {
                        const period = periodOf(viewYear, i)
                        const selectable = months.has(period)
                        const count = counts?.[period] ?? null
                        const selected = period === value
                        const tone = !selectable
                            ? "text-slate-300 cursor-not-allowed"
                            : selected
                                ? "bg-blue-600 text-white font-semibold"
                                : inRange(period)
                                    ? "bg-blue-50 text-blue-700 hover:bg-slate-100"
                                    : count === 0
                                        ? "text-slate-400 hover:bg-slate-100"
                                        : "text-slate-800 hover:bg-slate-100"
                        return (
                            <button
                                key={period}
                                type="button"
                                disabled={!selectable}
                                aria-pressed={selected}
                                title={selectable ? `${fmtPeriod(period)}${count != null ? `: ${fmtCount(count)}` : ""}` : `${fmtPeriod(period)}: außerhalb der Reihe`}
                                onClick={() => { onChange(period); setOpen(false) }}
                                className={`h-11 rounded-md flex flex-col items-center justify-center leading-tight transition-colors ${tone}`}
                            >
                                <span className="text-[12px]">{name}</span>
                                {selectable && count != null && (
                                    <span className={`text-[10px] tnum ${selected ? "text-white/80" : "opacity-70"}`}>
                                        {count === 0 ? "–" : count.toLocaleString("de-DE")}
                                    </span>
                                )}
                            </button>
                        )
                    })}
                </div>

                <p className="m-0 mt-2.5 text-[11px] text-slate-500 leading-snug">
                    Zahl = Bewertungen im Monat, „–“ = keine; hinterlegt = gewählter Zeitraum.
                </p>
            </PopoverContent>
        </Popover>
    )
}

/* months: Monate "YYYY-MM" der Reihe, aufsteigend. counts: {YYYY-MM: Zahl der
   Bewertungen} oder null. selection: angezeigter Zeitraum {from, to} oder null – die
   freie Auswahl oder bei einer ausgewählten Veränderung ihr Fenster ab dem markierten
   Monat; ohne Auswahl steht der letzte Monat da. */
export function DrilldownPicker({ months, counts = null, selection, onSelect, onClear }) {
    const [draft, setDraft] = useState(null) // eigene Eingabe, bis "Anzeigen" geklickt wird
    if (!months.length) {
        return <p className="m-0 text-[12px] text-slate-500">Keine datierten Bewertungen in dieser Auswahl.</p>
    }
    const first = months[0]
    const last = months[months.length - 1]
    const from = draft?.from ?? selection?.from ?? last
    const to = draft?.to ?? selection?.to ?? last
    const monthSet = new Set(months)
    const lastN = (n) => periodFromIndex(Math.max(periodIndex(first), periodIndex(last) - n + 1))
    const apply = (f, t) => {
        setDraft(null)
        const [a, b] = periodIndex(f) <= periodIndex(t) ? [f, t] : [t, f]
        onSelect(a, b)
    }
    const quick = [
        { label: "Letzter Monat", from: last, to: last },
        { label: "Letzte 6 Monate", from: lastN(6), to: last },
        { label: "Letzte 12 Monate", from: lastN(12), to: last },
    ]
    const pickerProps = { months: monthSet, first, last, counts, range: { from, to } }

    return (
        <div className="flex flex-wrap items-center gap-2 text-[12px] text-slate-600">
            <span className="inline-flex items-center gap-1.5">
                von
                <MonthPicker label="von" value={from} {...pickerProps} onChange={(m) => setDraft({ from: m, to })} />
            </span>
            <span className="inline-flex items-center gap-1.5">
                bis
                <MonthPicker label="bis" value={to} {...pickerProps} onChange={(m) => setDraft({ from, to: m })} />
            </span>
            <button type="button" className={buttonClass} onClick={() => apply(from, to)}>
                Anzeigen
            </button>
            <span className="w-px h-5 bg-slate-200 mx-1" aria-hidden="true" />
            {quick.map((q) => (
                <button key={q.label} type="button" className={buttonClass} onClick={() => apply(q.from, q.to)}>
                    {q.label}
                </button>
            ))}
            {selection && onClear && (
                <button type="button" className="underline underline-offset-2 text-slate-600 hover:text-slate-900 ml-1" onClick={() => { setDraft(null); onClear() }}>
                    Auswahl aufheben
                </button>
            )}
        </div>
    )
}
