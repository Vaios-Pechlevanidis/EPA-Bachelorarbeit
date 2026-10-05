import { useMemo } from "react"
import { Area, AreaChart, Bar, BarChart, CartesianGrid, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts"
import { ExternalLink } from "lucide-react"
import { FillBox } from "./ExpandableCard"
import {
    RATING_LEVELS, fiscalYearLabel, fmtAmount, fmtDay, fmtMonth, fmtPrice, fmtPriceTick, quarterLabel,
} from "@/lib/market"

/* ============================================================================
   FinanceCards — Bausteine des Aktien-Dashboards (/aktie, Inkrement 3, E16):
   Kursverlauf, Analystenempfehlungen, Umsatz und Nettoergebnis, Nachrichten.
   Alle Angaben stammen aus Yahoo Finance (yfinance) bzw. Google-News-RSS und
   sind eine Einordnung des Marktumfelds, keine Erklärung der Bewertungen.
   height ist jeweils die Gesamthöhe des Bausteins (Diagramm samt Legende);
   das Diagramm nimmt, was die Legende übrig lässt. compact (kleine Karte)
   lässt Zusatzzeilen weg, die in der vergrößerten Ansicht stehen.
   ============================================================================ */

const AXIS_TICK = { fontSize: 10, fill: "var(--color-axis)" }

function TooltipBox({ title, children }) {
    return (
        <div className="bg-slate-900 border border-slate-700 rounded-md shadow-lg px-3 py-2 text-[12px] min-w-[170px]">
            <p className="font-mono text-[10px] tracking-[0.05em] uppercase text-slate-400 mb-1.5 m-0">{title}</p>
            {children}
        </div>
    )
}

function TooltipRow({ label, value, color }) {
    return (
        <p className="m-0 flex items-center justify-between gap-3">
            <span className="inline-flex items-center gap-1.5 text-slate-400">
                {color && <span className="inline-block w-2.5 h-2.5 rounded-[2px]" style={{ background: color }} />}
                {label}
            </span>
            <span className="tnum text-white font-medium">{value}</span>
        </p>
    )
}

function Swatch({ color, label }) {
    return (
        <span className="inline-flex items-center gap-1.5">
            <span className="inline-block w-2.5 h-2.5 rounded-[2px]" style={{ background: color }} />
            {label}
        </span>
    )
}

export function EmptyNote({ children, height = 160 }) {
    return (
        <div className="flex items-center justify-center px-6 text-center" style={{ height }}>
            <p className="m-0 text-[12px] text-slate-500">{children}</p>
        </div>
    )
}

/* ---------------------------------------------------------------------------
   Kursverlauf: Monatsschlusskurse des gewählten Fensters als Fläche.
   --------------------------------------------------------------------------- */
export function StockPriceChart({ prices, currency, height = 300 }) {
    if (!prices?.length) return <EmptyNote height={height}>Keine Monatskurse im gewählten Zeitraum.</EmptyNote>
    return (
        <ResponsiveContainer width="100%" height={height}>
            <AreaChart data={prices} margin={{ left: 0, right: 8, top: 8, bottom: 5 }}>
                <defs>
                    <linearGradient id="price-fill" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor="var(--market-price)" stopOpacity={0.22} />
                        <stop offset="100%" stopColor="var(--market-price)" stopOpacity={0} />
                    </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="2 4" stroke="var(--color-grid)" vertical={false} />
                <XAxis dataKey="period" tickFormatter={fmtMonth} tick={AXIS_TICK} tickLine={false}
                    axisLine={{ stroke: "var(--color-border)" }} interval="preserveStartEnd" minTickGap={28} tickMargin={8} />
                <YAxis domain={["auto", "auto"]} tick={AXIS_TICK} tickLine={false} axisLine={false} width={52}
                    tickFormatter={fmtPriceTick}
                    label={{ value: currency ?? "", angle: -90, position: "insideLeft", offset: 10, fontSize: 10, fill: "var(--color-axis)" }} />
                <Tooltip
                    cursor={{ stroke: "var(--color-border-strong)", strokeWidth: 1, strokeDasharray: "3 3" }}
                    content={({ active, payload }) => active && payload?.length ? (
                        <TooltipBox title={fmtMonth(payload[0].payload.period)}>
                            <TooltipRow label="Monatsschluss" value={`${fmtPrice(payload[0].payload.close)} ${currency ?? ""}`} />
                        </TooltipBox>
                    ) : null}
                />
                <Area type="linear" dataKey="close" stroke="var(--market-price)" strokeWidth={1.5} fill="url(#price-fill)"
                    dot={false} activeDot={{ r: 3, fill: "var(--market-price)", stroke: "var(--color-bg-card)", strokeWidth: 1 }}
                    isAnimationActive={false} />
            </AreaChart>
        </ResponsiveContainer>
    )
}

/* ---------------------------------------------------------------------------
   Analystenempfehlungen: Zahl der Empfehlungen je Stufe und Monat, gestapelt.
   --------------------------------------------------------------------------- */
export function AnalystChart({ analysts, height = 240, compact = false }) {
    const months = analysts?.months ?? []
    if (!months.length) return <EmptyNote height={height}>Yahoo Finance liefert für dieses Wertpapier keine Analystenempfehlungen.</EmptyNote>
    const latest = months[months.length - 1]
    return (
        <div className="flex flex-col" style={{ height }}>
            <FillBox>{(chartHeight) => (
                <ResponsiveContainer width="100%" height={chartHeight}>
                    <BarChart data={months} margin={{ left: 0, right: 8, top: 8, bottom: 5 }} barCategoryGap="28%">
                        <CartesianGrid strokeDasharray="2 4" stroke="var(--color-grid)" vertical={false} />
                        <XAxis dataKey="month" tickFormatter={fmtMonth} tick={AXIS_TICK} tickLine={false} axisLine={{ stroke: "var(--color-border)" }} tickMargin={8} />
                        <YAxis allowDecimals={false} tick={AXIS_TICK} tickLine={false} axisLine={false} width={28} />
                        <Tooltip
                            cursor={{ fill: "var(--color-grid)", fillOpacity: 0.5 }}
                            content={({ active, payload }) => active && payload?.length ? (
                                <TooltipBox title={fmtMonth(payload[0].payload.month)}>
                                    {RATING_LEVELS.map((l) => (
                                        <TooltipRow key={l.key} label={l.label} value={payload[0].payload[l.key]} color={l.color} />
                                    ))}
                                    <p className="m-0 mt-1 pt-1 border-t border-slate-700 flex justify-between gap-3">
                                        <span className="text-slate-400">Analysten insgesamt</span>
                                        <span className="tnum text-white font-medium">{payload[0].payload.total}</span>
                                    </p>
                                </TooltipBox>
                            ) : null}
                        />
                        {RATING_LEVELS.map((l, i) => (
                            <Bar key={l.key} dataKey={l.key} stackId="rating" fill={l.color} isAnimationActive={false}
                                radius={i === RATING_LEVELS.length - 1 ? [3, 3, 0, 0] : 0} />
                        ))}
                    </BarChart>
                </ResponsiveContainer>
            )}</FillBox>
            <p className={`m-0 flex flex-wrap items-center justify-center text-[11px] text-slate-500 flex-none ${compact ? "mt-1.5 gap-x-2.5 gap-y-0.5" : "mt-2 gap-x-3 gap-y-1"}`}>
                {RATING_LEVELS.map((l) => <Swatch key={l.key} color={l.color} label={l.label} />)}
            </p>
            {!compact && <p className="m-0 mt-2 text-[11px] text-slate-500 text-center flex-none">
                {fmtMonth(latest.month)}: {latest.total} Empfehlungen, davon {latest.strong_buy + latest.buy} kaufen,{" "}
                {latest.hold} halten, {latest.sell + latest.strong_sell} verkaufen · Stand {fmtDay(analysts.as_of)}
            </p>}
        </div>
    )
}

/* ---------------------------------------------------------------------------
   Umsatz und Nettoergebnis je Geschäftsjahr oder Quartal, nebeneinander.
   --------------------------------------------------------------------------- */
export function EarningsChart({ earnings, period = "annual", height = 240, compact = false }) {
    const rows = useMemo(() => (earnings?.[period] ?? []).map((r) => ({
        ...r,
        label: period === "annual" ? fiscalYearLabel(r.period_end) : quarterLabel(r.period_end),
    })), [earnings, period])
    const currency = earnings?.currency ?? ""
    if (!rows.length) {
        return <EmptyNote height={height}>Yahoo Finance liefert {period === "annual" ? "keine Jahreszahlen" : "keine Quartalszahlen"} zu Umsatz und Gewinn.</EmptyNote>
    }
    const hasLoss = rows.some((r) => (r.net_income ?? 0) < 0)
    return (
        <div className="flex flex-col" style={{ height }}>
            <FillBox>{(chartHeight) => (
                <ResponsiveContainer width="100%" height={chartHeight}>
                    <BarChart data={rows} margin={{ left: 0, right: 8, top: 8, bottom: 5 }} barCategoryGap="24%" barGap={2}>
                        <CartesianGrid strokeDasharray="2 4" stroke="var(--color-grid)" vertical={false} />
                        <XAxis dataKey="label" tick={AXIS_TICK} tickLine={false} axisLine={{ stroke: "var(--color-border)" }} tickMargin={8} />
                        <YAxis tick={AXIS_TICK} tickLine={false} axisLine={false} width={72} tickFormatter={(v) => fmtAmount(v)} />
                        {hasLoss && <ReferenceLine y={0} stroke="var(--color-border-strong)" />}
                        <Tooltip
                            cursor={{ fill: "var(--color-grid)", fillOpacity: 0.5 }}
                            content={({ active, payload }) => active && payload?.length ? (
                                <TooltipBox title={payload[0].payload.label}>
                                    <TooltipRow label="Umsatz" value={fmtAmount(payload[0].payload.revenue, currency)} color="var(--finance-revenue)" />
                                    <TooltipRow label="Nettoergebnis" value={fmtAmount(payload[0].payload.net_income, currency)} color="var(--finance-earnings)" />
                                    <p className="m-0 mt-1 text-[10px] text-slate-400">Stichtag {fmtDay(payload[0].payload.period_end)}</p>
                                </TooltipBox>
                            ) : null}
                        />
                        <Bar dataKey="revenue" fill="var(--finance-revenue)" radius={[3, 3, 0, 0]} isAnimationActive={false} />
                        <Bar dataKey="net_income" fill="var(--finance-earnings)" radius={[3, 3, 0, 0]} isAnimationActive={false} />
                    </BarChart>
                </ResponsiveContainer>
            )}</FillBox>
            <p className={`m-0 flex flex-wrap items-center justify-center text-[11px] text-slate-500 flex-none ${compact ? "mt-1.5 gap-x-2.5 gap-y-0.5" : "mt-2 gap-x-3 gap-y-1"}`}>
                <Swatch color="var(--finance-revenue)" label={`Umsatz (${currency})`} />
                <Swatch color="var(--finance-earnings)" label={`Nettoergebnis (${currency})`} />
                {!compact && <span>Berichtswährung, wie von Yahoo Finance geliefert; fehlende Werte bleiben leer</span>}
            </p>
        </div>
    )
}

/* ---------------------------------------------------------------------------
   Nachrichten: aktuelle Meldungen, neueste zuerst, Link zur Quelle.
   --------------------------------------------------------------------------- */
export function NewsList({ news, listClassName = "", showFootnote = true, dense = false }) {
    const items = news?.items ?? []
    return (
        <div>
            {items.length === 0 ? (
                <EmptyNote height={100}>{news?.reason ?? "Keine Meldungen."}</EmptyNote>
            ) : (
                <ul className={`m-0 p-0 pr-2 list-none ${listClassName}`} aria-label="Meldungen">
                    {items.map((item) => (
                        <li key={item.url} className={`border-t border-slate-100 first:border-t-0 ${dense ? "py-2" : "py-2.5"}`}>
                            <a href={item.url} target="_blank" rel="noreferrer noopener" onClick={(e) => e.stopPropagation()}
                                className={`group inline-flex items-start gap-1.5 font-medium text-slate-900 hover:text-blue-700 ${dense ? "text-[12.5px] leading-[18px]" : "text-[13px] leading-5"}`}>
                                <span>{item.title}</span>
                                <ExternalLink className={`w-3 h-3 flex-none text-slate-400 group-hover:text-blue-700 ${dense ? "mt-0.5" : "mt-1"}`} />
                            </a>
                            <p className={`m-0 text-slate-500 ${dense ? "mt-0.5 text-[11px]" : "text-[11px]"}`}>
                                {item.source ?? "Quelle unbekannt"} · {item.published_at ? fmtDay(item.published_at.slice(0, 10)) : "ohne Datum"}
                            </p>
                        </li>
                    ))}
                </ul>
            )}
            {news && showFootnote && (
                <p className="m-0 mt-3 text-[11px] text-slate-400 leading-4">
                    Quelle: {news.source}; Suchbegriff {news.query}, letzte {news.window_days} Tage.
                    {news.fetched_at && ` Abgerufen am ${fmtDay(news.fetched_at.slice(0, 10))}.`}
                    {news.stale && " Älterer Stand, der neue Abruf war nicht möglich."}
                    {" "}Die Suche geht nach dem Namen; mehrdeutige Namen liefern auch fremde Treffer. Die Meldungen
                    werden keiner Veränderung der Bewertungen zugeordnet.
                </p>
            )}
        </div>
    )
}
