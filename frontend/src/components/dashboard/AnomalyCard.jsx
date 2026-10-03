import * as React from "react"
import { useMemo, memo } from "react"
import {
    LineChart,
    Line,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    ReferenceDot,
} from "recharts"
import { Activity, ArrowDownRight, ArrowUpRight, Maximize2 } from "lucide-react"
import { useAnomalies } from "@/hooks/useAnomalies"
import { ChartCardHeader } from "./ChartHeader"

/* ============================================================================
   AnomalyCard — Monatsverlauf mit auffälligen Veränderungen (Inkrement 1).
   Daten: GET /analytics/company/{id}/anomalies (live berechnet, nur lesend).
   Die Karte öffnet per Klick die Detailseite /anomalies (onOpen); Diagramm und
   Liste werden dort wiederverwendet.
   Wortwahl: "auffällige Veränderung", keine Aussage über Ursachen.
   ============================================================================ */

const SOURCE = "employee"
const DIMENSION = "durchschnittsbewertung"

const SOURCE_LABEL = { employee: "Mitarbeiter", candidates: "Bewerber" }

const DIRECTION = {
    fall: { label: "Abfall", color: "var(--rose-500)", Icon: ArrowDownRight, text: "text-rose-600" },
    rise: { label: "Anstieg", color: "var(--emerald-500)", Icon: ArrowUpRight, text: "text-emerald-600" },
}

const SEVERITY_LABEL = { high: "deutlich", medium: "mäßig" }

const fmt = (v, digits = 2) =>
    v == null ? "–" : Number(v).toLocaleString("de-DE", { minimumFractionDigits: digits, maximumFractionDigits: digits })

const fmtDelta = (v) => (v > 0 ? "+" : v < 0 ? "−" : "") + fmt(Math.abs(v))

function fmtPeriod(period) {
    const [y, m] = period.split("-").map(Number)
    return new Date(y, m - 1, 1).toLocaleDateString("de-DE", { month: "short", year: "numeric" })
}

function AnomalyTooltip({ active, payload, anomaliesByPeriod }) {
    if (!active || !payload?.length) return null
    const point = payload[0].payload
    const anomaly = anomaliesByPeriod[point.period]
    return (
        <div className="bg-slate-900 border border-slate-700 rounded-md shadow-lg px-3 py-2 text-[12px] min-w-[170px]">
            <p className="font-mono text-[10px] tracking-[0.05em] uppercase text-slate-400 mb-1.5">{fmtPeriod(point.period)}</p>
            <p className="flex items-center justify-between gap-3">
                <span className="text-slate-400">Monatsmittel</span>
                <span className="font-semibold tnum text-white">{fmt(point.mean)}</span>
            </p>
            <p className="flex items-center justify-between gap-3">
                <span className="text-slate-400">Bewertungen</span>
                <span className="tnum text-slate-300">{point.count}</span>
            </p>
            {anomaly && (
                <div className="mt-1.5 pt-1.5 border-t border-slate-700">
                    <p className="mb-1 inline-flex items-center gap-1.5" style={{ color: DIRECTION[anomaly.direction].color }}>
                        <span className="w-1.5 h-1.5 rounded-full" style={{ background: DIRECTION[anomaly.direction].color }} />
                        Auffällige Veränderung
                    </p>
                    <p className="flex items-center justify-between gap-3">
                        <span className="text-slate-400">Delta</span>
                        <span className="font-semibold tnum text-white">{fmtDelta(anomaly.delta)} Sterne</span>
                    </p>
                    <p className="flex items-center justify-between gap-3">
                        <span className="text-slate-400">Ø davor → danach</span>
                        <span className="tnum text-slate-300">{fmt(anomaly.before_mean)} → {fmt(anomaly.after_mean)}</span>
                    </p>
                    <p className="flex items-center justify-between gap-3">
                        <span className="text-slate-400">Anzahl</span>
                        <span className="tnum text-slate-300">{anomaly.n_reviews} Bewertungen</span>
                    </p>
                </div>
            )}
        </div>
    )
}

export function AnomalyList({ anomalies }) {
    if (!anomalies.length) {
        return <p className="text-[12px] text-slate-500 m-0">Keine auffälligen Veränderungen erkannt.</p>
    }
    return (
        <ul className="m-0 p-0 list-none">
            {anomalies.map((a) => {
                const dir = DIRECTION[a.direction]
                return (
                    <li key={a.id} className="flex items-center gap-3 py-2 text-[12px] border-t border-slate-100 first:border-t-0">
                        <dir.Icon className={`w-4 h-4 flex-none ${dir.text}`} aria-label={dir.label} />
                        <span className="w-[72px] flex-none text-slate-700 tnum">{fmtPeriod(a.date)}</span>
                        <span className={`w-[92px] flex-none font-semibold tnum ${dir.text}`}>{fmtDelta(a.delta)} Sterne</span>
                        <span className="flex-1 min-w-0 truncate text-slate-500 tnum">
                            Ø {fmt(a.before_mean)} → {fmt(a.after_mean)} · {a.n_reviews} Bewertungen
                        </span>
                        <span className="flex-none text-[11px] text-slate-500">{SEVERITY_LABEL[a.severity] ?? a.severity}</span>
                    </li>
                )
            })}
        </ul>
    )
}

/* Diagramm mit Lade-, Fehler- und Leerzustand; Höhe frei wählbar (Karte 220, Seite größer). */
export function AnomalyChart({ data, anomalies, loading, error, height = 220 }) {
    const anomaliesByPeriod = useMemo(
        () => Object.fromEntries(anomalies.map((a) => [a.date, a])),
        [anomalies],
    )
    const chartData = useMemo(
        () => (data?.series ?? []).filter((m) => m.evaluated && m.mean != null),
        [data],
    )
    const yDomain = useMemo(() => {
        if (!chartData.length) return [1, 5]
        const vals = chartData.map((m) => m.mean)
        return [Math.max(1, Math.floor((Math.min(...vals) - 0.2) * 2) / 2), Math.min(5, Math.ceil((Math.max(...vals) + 0.2) * 2) / 2)]
    }, [chartData])

    return (
        <div className="relative w-full" style={{ height }}>
            {error ? (
                <div className="h-full flex items-center justify-center">
                    <p className="text-[13px] text-slate-500">Anomalien konnten nicht geladen werden: {error}</p>
                </div>
            ) : chartData.length === 0 && !loading ? (
                <div className="h-full flex items-center justify-center">
                    <p className="text-[13px] text-slate-500">Keine bewerteten Monate vorhanden.</p>
                </div>
            ) : (
                <ResponsiveContainer width="100%" height={height}>
                    <LineChart data={chartData} margin={{ left: 0, right: 16, top: 8, bottom: 5 }}>
                        <CartesianGrid strokeDasharray="2 4" stroke="var(--color-grid)" vertical={false} />
                        <XAxis
                            dataKey="period"
                            tickFormatter={fmtPeriod}
                            tick={{ fontSize: 10, fill: "var(--color-axis)" }}
                            tickLine={false}
                            axisLine={{ stroke: "var(--color-border)" }}
                            interval="preserveStartEnd"
                            minTickGap={24}
                            tickMargin={8}
                        />
                        <YAxis
                            domain={yDomain}
                            tick={{ fontSize: 10, fill: "var(--color-axis)" }}
                            tickLine={false}
                            axisLine={false}
                            width={32}
                            tickFormatter={(v) => v.toFixed(1)}
                        />
                        <Tooltip
                            content={<AnomalyTooltip anomaliesByPeriod={anomaliesByPeriod} />}
                            cursor={{ stroke: "var(--color-border-strong)", strokeWidth: 1, strokeDasharray: "3 3" }}
                        />
                        <Line
                            type="monotone"
                            dataKey="mean"
                            stroke="#3b82f6"
                            strokeWidth={1.5}
                            dot={false}
                            activeDot={{ r: 3 }}
                            isAnimationActive={false}
                        />
                        {anomalies.map((a) => {
                            const point = chartData.find((m) => m.period === a.date)
                            if (!point) return null
                            return (
                                <ReferenceDot
                                    key={a.id}
                                    x={a.date}
                                    y={point.mean}
                                    r={a.severity === "high" ? 5 : 4}
                                    fill={DIRECTION[a.direction].color}
                                    fillOpacity={0.35}
                                    stroke={DIRECTION[a.direction].color}
                                    strokeWidth={1.5}
                                />
                            )
                        })}
                    </LineChart>
                </ResponsiveContainer>
            )}
            {loading && (
                <div className="absolute inset-0 bg-white/70 flex items-center justify-center rounded-md pointer-events-none">
                    <div className="flex items-center gap-2">
                        <div className="animate-spin rounded-full h-5 w-5 border-2 border-slate-200 border-t-slate-600"></div>
                        <p className="text-slate-600 text-[12px]">Lade Verlauf…</p>
                    </div>
                </div>
            )}
        </div>
    )
}

export const AnomalyCard = memo(function AnomalyCard({ companyId, onOpen }) {
    const { data, anomalies, loading, error } = useAnomalies(companyId, { source: SOURCE, dimension: DIMENSION })

    if (!companyId) return null

    const count = anomalies.length
    const subtitle = `${SOURCE_LABEL[SOURCE]} · Gesamtbewertung · ${count} ${count === 1 ? "auffällige Veränderung" : "auffällige Veränderungen"}`
    const open = () => onOpen?.()

    return (
        <div
            role="link"
            tabIndex={0}
            title="Detailansicht öffnen"
            onClick={open}
            onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); open() } }}
            className="group bg-white border border-slate-200 rounded-lg overflow-hidden shadow-xs hover:shadow-sm transition-shadow cursor-pointer flex flex-col"
        >
            <ChartCardHeader
                icon={<Activity />}
                eyebrow="VERLAUF · AUFFÄLLIGE VERÄNDERUNGEN"
                title="Anomalien im Verlauf"
                subtitle={subtitle}
                expandable
            />
            <div className="px-4 pt-4 pb-4">
                <AnomalyChart data={data} anomalies={anomalies} loading={loading} error={error} height={220} />

                <div className="mt-3 pt-3 border-t border-slate-100">
                    {!loading && !error && <AnomalyList anomalies={anomalies} />}
                </div>

                <p className="text-[11px] text-slate-400 text-center mt-3 m-0 inline-flex w-full items-center justify-center gap-1">
                    <Maximize2 className="w-3 h-3" />
                    Karte anklicken öffnet die Detailseite
                </p>
            </div>
        </div>
    )
})

export default AnomalyCard
