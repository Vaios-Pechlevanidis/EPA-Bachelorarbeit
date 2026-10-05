/* Kachel einer Kennzahlenleiste (Aktien-Dashboard, Anomalien-Seite):
   Kennung, Wert, Anmerkung; tone färbt den Wert (z. B. Abfall/Anstieg). */
export function KpiTile({ label, value, note, tone }) {
    return (
        <div className="bg-white border border-slate-200 rounded-lg px-3.5 py-2 min-w-0 shadow-xs">
            <p className="m-0 font-mono text-[10px] tracking-[0.06em] uppercase text-slate-500 leading-none truncate">{label}</p>
            <p className="m-0 mt-1 text-[16px] leading-6 font-semibold text-slate-900 tnum truncate" style={tone ? { color: tone } : undefined}>{value}</p>
            <p className="m-0 text-[11px] text-slate-500 leading-4 truncate" title={note}>{note}</p>
        </div>
    )
}
