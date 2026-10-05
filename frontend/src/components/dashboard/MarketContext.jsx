/* ============================================================================
   MarketContext — Kennzahlen, Herkunft und Hinweis im Aktien-Dashboard
   (Inkrement 3, E15, E16). Daten: GET /analytics/company/{id}/finance. Der
   Kurs zeigt das Marktumfeld; ein Zusammenhang mit den Bewertungen wird nicht
   behauptet und nicht berechnet.
   ============================================================================ */
import {
    MARKET_DISCLAIMER_LEAD, MARKET_DISCLAIMER_TEXT, PARENT_SCOPE,
    fiscalYearLabel, fmtAmount, fmtDay, fmtMonth, fmtPercent, fmtPrice,
} from "@/lib/market"
import { KpiTile as Tile } from "./KpiTile"

/* Umschalter "Aktienkurs" (Kurs im Bewertungsverlauf ein/aus). */
export function PriceToggle({ checked, onChange }) {
    return (
        <label className="inline-flex items-center gap-1.5 text-[12px] text-slate-700 cursor-pointer select-none"
            onClick={(e) => e.stopPropagation()}>
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


/* Kennzahlenleiste oben im Aktien-Dashboard. Aktuelle Werte tragen
   "aktuell, Stand …", Jahreswerte ihr Geschäftsjahr; fehlende Werte zeigen "–". */
export function FinanceKpis({ market, last, first, change }) {
    const metrics = market?.metrics ?? {}
    const annual = market?.earnings?.annual ?? []
    const lastYear = annual[annual.length - 1]
    const latestRevenue = metrics.revenue?.[metrics.revenue.length - 1]
    const analysts = market?.analysts?.months ?? []
    const latestAnalysts = analysts[analysts.length - 1]
    const currency = market?.earnings?.currency ?? latestRevenue?.unit ?? ""
    return (
        <div className="grid gap-3 grid-cols-2 md:grid-cols-3 xl:grid-cols-6">
            <Tile
                label={last ? `Kurs · ${fmtMonth(last.period)}` : "Kurs"}
                value={last ? `${fmtPrice(last.close)} ${market.currency ?? ""}` : "–"}
                note={last ? `${fmtPercent(change)} seit ${fmtMonth(first.period)}` : "–"}
            />
            <Tile
                label="Marktkapitalisierung"
                value={metrics.market_cap ? fmtAmount(metrics.market_cap.value, metrics.market_cap.unit) : "–"}
                note={metrics.market_cap ? `aktuell, Stand ${fmtDay(metrics.market_cap.as_of)}` : "keine Angabe"}
            />
            <Tile
                label="Mitarbeitende"
                value={metrics.employees ? metrics.employees.value.toLocaleString("de-DE") : "–"}
                note={metrics.employees ? `aktuell, Abruf ${fmtDay(metrics.employees.as_of)}` : "keine Angabe"}
            />
            <Tile
                label="Umsatz"
                value={lastYear?.revenue != null ? fmtAmount(lastYear.revenue, currency) : latestRevenue ? fmtAmount(latestRevenue.value, latestRevenue.unit) : "–"}
                note={lastYear ? fiscalYearLabel(lastYear.period_end) : latestRevenue ? fiscalYearLabel(latestRevenue.fiscal_year_end) : "keine Angabe"}
            />
            <Tile
                label="Nettoergebnis"
                value={lastYear?.net_income != null ? fmtAmount(lastYear.net_income, currency) : "–"}
                note={lastYear ? fiscalYearLabel(lastYear.period_end) : "keine Angabe"}
            />
            <Tile
                label={latestAnalysts ? `Analysten · ${fmtMonth(latestAnalysts.month)}` : "Analysten"}
                value={latestAnalysts ? `${latestAnalysts.strong_buy + latestAnalysts.buy} / ${latestAnalysts.hold} / ${latestAnalysts.sell + latestAnalysts.strong_sell}` : "–"}
                note={latestAnalysts ? "kaufen / halten / verkaufen" : "keine Angabe"}
            />
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

/* Eine Zeile mit Wertpapier, Quelle, Abrufdatum und festem Hinweis (E15). */
export function MarketSourceNote({ market, companyName }) {
    if (!market?.available) return null
    return (
        <p className="m-0 text-[11px] text-slate-500 leading-4">
            <span className="font-medium text-slate-700">{MARKET_DISCLAIMER_LEAD}</span> {MARKET_DISCLAIMER_TEXT}{" "}
            {securityText(market, companyName)} Quelle: {market.source}, Monatsschlusskurse um Splits und Dividenden
            bereinigt; abgerufen am {fmtDay(market.fetched_at?.slice(0, 10))}.
        </p>
    )
}
