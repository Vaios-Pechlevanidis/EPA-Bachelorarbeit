import { useState } from "react"
import { fmtPeriod, periodFromIndex, periodIndex } from "@/lib/anomalySeries"

/* ============================================================================
   DrilldownPicker — freie Auswahl eines Zeitraums für den Drill-down (E17).
   Für Reihen ohne erkannte Veränderung und für Monate, die im Diagramm nicht
   anklickbar sind (z. B. dünne Reihen ohne bewerteten Monat). Die Monate kommen
   aus der Monatsreihe (erster bis letzter Monat mit datierter Bewertung).
   ============================================================================ */

const selectClass =
    "h-7 rounded-md border border-slate-300 bg-white px-2 text-[12px] text-slate-800 tnum focus:outline-none focus:ring-1 focus:ring-slate-400"
const buttonClass =
    "h-7 px-2.5 rounded-md border border-slate-300 bg-white text-[12px] font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-50"

/* months: Monate "YYYY-MM" der Reihe, aufsteigend. selection: angezeigter Zeitraum
   {from, to} oder null – die freie Auswahl oder bei einer ausgewählten Veränderung
   ihr Fenster ab dem markierten Monat; ohne Auswahl steht der letzte Monat da. */
export function DrilldownPicker({ months, selection, onSelect, onClear }) {
    const [draft, setDraft] = useState(null) // eigene Eingabe, bis "Anzeigen" geklickt wird
    if (!months.length) {
        return <p className="m-0 text-[12px] text-slate-500">Keine datierten Bewertungen in dieser Auswahl.</p>
    }
    const last = months[months.length - 1]
    const from = draft?.from ?? selection?.from ?? last
    const to = draft?.to ?? selection?.to ?? last
    const descending = [...months].reverse()
    const lastN = (n) => periodFromIndex(Math.max(periodIndex(months[0]), periodIndex(last) - n + 1))
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

    return (
        <div className="flex flex-wrap items-center gap-2 text-[12px] text-slate-600">
            <label className="inline-flex items-center gap-1.5">
                von
                <select className={selectClass} value={from} onChange={(e) => setDraft({ from: e.target.value, to })}>
                    {descending.map((m) => <option key={m} value={m}>{fmtPeriod(m)}</option>)}
                </select>
            </label>
            <label className="inline-flex items-center gap-1.5">
                bis
                <select className={selectClass} value={to} onChange={(e) => setDraft({ from, to: e.target.value })}>
                    {descending.map((m) => <option key={m} value={m}>{fmtPeriod(m)}</option>)}
                </select>
            </label>
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
