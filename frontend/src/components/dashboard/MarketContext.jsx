/* ============================================================================
   MarketContext — Aktienkurs als Einordnung auf der Detailseite (Inkrement 3, E15).
   Daten: GET /analytics/company/{id}/market (useMarket). Der Kurs zeigt das
   Marktumfeld; ein Zusammenhang mit den Bewertungen wird nicht behauptet und
   nicht berechnet.
   ============================================================================ */

/* Umschalter "Aktienkurs" im Kopf des Diagrammabschnitts. */
export function PriceToggle({ checked, onChange }) {
    return (
        <label className="inline-flex items-center gap-1.5 text-[12px] text-slate-700 cursor-pointer select-none">
            <input
                type="checkbox"
                className="accent-violet-600"
                checked={checked}
                onChange={(e) => onChange(e.target.checked)}
            />
            Aktienkurs
        </label>
    )
}
