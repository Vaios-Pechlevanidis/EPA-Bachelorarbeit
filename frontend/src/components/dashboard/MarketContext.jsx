/* ============================================================================
   MarketContext — Aktienkurs als Einordnung auf der Detailseite (Inkrement 3, E15).
   Daten: GET /analytics/company/{id}/market (useMarket). Der Kurs zeigt das
   Marktumfeld; ein Zusammenhang mit den Bewertungen wird nicht behauptet und
   nicht berechnet.
   ============================================================================ */
import { MARKET_DISCLAIMER_LEAD, MARKET_DISCLAIMER_TEXT, PARENT_SCOPE, fiscalYearLabel, fmtAmount, fmtDay, noPriceText } from "@/lib/market"

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

function Metric({ label, value, note }) {
    return (
        <div className="min-w-0">
            <p className="m-0 font-mono text-[10px] tracking-[0.06em] uppercase text-slate-500 leading-none">{label}</p>
            <p className="m-0 mt-1 text-[13px] font-semibold text-slate-900 tnum">{value}</p>
            <p className="m-0 text-[11px] text-slate-500 leading-4">{note}</p>
        </div>
    )
}

/* Kennzahlenzeile unter dem Diagramm. Aktuelle Werte tragen "aktuell, Stand …",
   damit niemand sie auf einen früheren Zeitraum bezieht; der Umsatz steht je
   Geschäftsjahr. Fehlende Werte erscheinen nicht und werden nicht geschätzt. */
export function MarketMetrics({ metrics }) {
    const marketCap = metrics?.market_cap
    const employees = metrics?.employees
    const revenue = metrics?.revenue ?? []
    if (!marketCap && !employees && !revenue.length) return null
    return (
        <div className="grid gap-x-6 gap-y-3 grid-cols-[repeat(auto-fit,minmax(160px,1fr))]">
            {marketCap && (
                <Metric
                    label="Marktkapitalisierung"
                    value={fmtAmount(marketCap.value, marketCap.unit)}
                    note={`aktuell, Stand ${fmtDay(marketCap.as_of)}`}
                />
            )}
            {employees && (
                <Metric
                    label="Mitarbeitende"
                    value={employees.value.toLocaleString("de-DE")}
                    note={`aktuell, Stand ${fmtDay(employees.as_of)} (Abruf)`}
                />
            )}
            {revenue.length > 0 && (
                <div className="min-w-0 col-span-full sm:col-span-2">
                    <p className="m-0 font-mono text-[10px] tracking-[0.06em] uppercase text-slate-500 leading-none">Umsatz je Geschäftsjahr</p>
                    <p className="m-0 mt-1 flex flex-wrap gap-x-4 gap-y-0.5 text-[12px] text-slate-700 tnum">
                        {revenue.map((r) => (
                            <span key={r.fiscal_year_end}>
                                <span className="text-slate-500">{fiscalYearLabel(r.fiscal_year_end)}</span>{" "}
                                <span className="font-semibold text-slate-900">{fmtAmount(r.value, r.unit)}</span>
                            </span>
                        ))}
                    </p>
                </div>
            )}
        </div>
    )
}

/* Wessen Kurs gezeigt wird: Wertpapier und Ticker; bei der Konzernmutter ausdrücklich. */
function securityText(market, companyName) {
    const security = market.ticker_name ? `${market.ticker_name} (${market.ticker})` : market.ticker
    if (market.ticker_scope === PARENT_SCOPE) {
        return `Kurs und Kennzahlen der Konzernmutter ${security}, nicht${companyName ? ` von ${companyName}` : " des Unternehmens"} selbst.`
    }
    return `Kurs und Kennzahlen: ${security}.`
}

/* Block unter dem Diagramm: Kennzahlen mit Herkunft und festem Hinweis oder,
   ohne Kurs, nur der Grund. Während des Ladens und bei einem Ladefehler
   bleibt die Ansicht wie ohne Kurs. */
export function MarketContext({ market, loading, error, companyName }) {
    if (loading || error || !market) return null
    if (!market.available) {
        return <p className="m-0 text-[11px] text-slate-500">{noPriceText(market.reason)}</p>
    }
    return (
        <div className="space-y-3">
            <MarketMetrics metrics={market.metrics} />
            <p className="m-0 text-[11px] text-slate-500 leading-4">
                {securityText(market, companyName)} Quelle: {market.source}, Kurse als Monatsschluss, um Splits und Dividenden
                bereinigt; abgerufen am {fmtDay(market.fetched_at?.slice(0, 10))}.
            </p>
            <p className="m-0 text-[11px] text-slate-500 leading-4">
                <span className="font-medium text-slate-700">{MARKET_DISCLAIMER_LEAD}</span> {MARKET_DISCLAIMER_TEXT}
            </p>
        </div>
    )
}
