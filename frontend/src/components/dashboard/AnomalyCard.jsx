import * as React from "react"
import { useMemo, useState, memo } from "react"
import {
    LineChart,
    Line,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    ReferenceLine,
} from "recharts"
import { ArrowDownRight, ArrowUpRight, Layers, Maximize2 } from "lucide-react"
import { Anomaly as AnomalyIcon } from "../../icons"
import { useAnomalies } from "@/hooks/useAnomalies"
import { ChartCardHeader, DropdownPicker } from "./ChartHeader"
import { EMPLOYEE_DIMENSIONS, OVERALL_DIMENSION, dimensionLabel } from "@/lib/ratingCategories"
import { INTERP_KEYS, TIME_RANGES, fmtPeriod, inWindow, interpolateGaps, levelsFromAnomalies, trimToEvaluated } from "@/lib/anomalySeries"

/* ============================================================================
   AnomalyCard — Monatsverlauf mit auffälligen Veränderungen (Inkrement 1).
   Daten: GET /analytics/company/{id}/anomalies (live berechnet, nur lesend).
   Die Karte zeigt Verlauf und Zähler; die Liste der Veränderungen steht nur auf
   der Detailseite /anomalies, die ein Klick auf die Karte öffnet (onOpen).
   Wortwahl: "auffällige Veränderung", keine Aussage über Ursachen.
   ============================================================================ */

// Quelle fest auf Mitarbeitende; die Quellenauswahl folgt in Inkrement 2.
const SOURCE = "employee"

const SOURCE_LABEL = { employee: "Mitarbeiter", candidates: "Bewerber" }

// Farbe je Richtung als Theme-Token (index.css: hell 700er-, dunkel 400er-Töne).
// "glyph" ist der mittlere 500er-Ton für den Tooltip, dessen Hintergrund mit dem
// Theme wechselt (hell dunkel, dunkel hell).
const DIRECTION = {
    fall: { label: "Abfall", color: "var(--anomaly-fall)", glyph: "var(--rose-500)", Icon: ArrowDownRight },
    rise: { label: "Anstieg", color: "var(--anomaly-rise)", glyph: "var(--emerald-500)", Icon: ArrowUpRight },
}

// Strichstärke der Stufe: kräftig = deutlich (ab 0,5 Sternen), dünn = mäßig.
const STEP_WIDTH = { high: 2.25, medium: 1.25 }

/* Kleines Stufen-Symbol (Legende, Tooltip): waagerecht altes Niveau, senkrecht
   der Sprung, waagerecht das neue Niveau. */
export function StepGlyph({ direction, severity = "high", color, size = 12 }) {
    const y1 = direction === "fall" ? 3 : 9
    const y2 = direction === "fall" ? 9 : 3
    return (
        <svg width={size} height={size} viewBox="0 0 12 12" aria-hidden="true" className="flex-none">
            <path
                d={`M1 ${y1} H6 V${y2} H11`}
                fill="none"
                stroke={color ?? DIRECTION[direction].color}
                strokeWidth={STEP_WIDTH[severity] ?? 1.5}
                strokeLinecap="round"
                strokeLinejoin="round"
            />
        </svg>
    )
}

/* Markierung im Diagramm: Stufe am markierten Monat von Ø davor (links) zu
   Ø danach (rechts). Höhe = Ausmaß im Maßstab der Y-Achse, Form = Richtung,
   Strichstärke = Schweregrad. Der Monatswert selbst bleibt auf der Linie. */
function stepShape(anomaly, halfWidth) {
    function StepMarker({ x1, y1, y2 }) {
        if (![x1, y1, y2].every(Number.isFinite)) return <g />
        return (
            <path
                d={`M${x1 - halfWidth} ${y1} H${x1} V${y2} H${x1 + halfWidth}`}
                fill="none"
                stroke={DIRECTION[anomaly.direction].color}
                strokeWidth={STEP_WIDTH[anomaly.severity] ?? 1.5}
                strokeLinecap="round"
                strokeLinejoin="round"
            />
        )
    }
    return StepMarker
}

const SEVERITY_LABEL = { high: "deutlich", medium: "mäßig" }

const fmt = (v, digits = 2) =>
    v == null ? "–" : Number(v).toLocaleString("de-DE", { minimumFractionDigits: digits, maximumFractionDigits: digits })

const fmtDelta = (v) => (v > 0 ? "+" : v < 0 ? "−" : "") + fmt(Math.abs(v))

const fmtSpan = (from, to) => (from && to && from !== to ? `${fmtPeriod(from)} – ${fmtPeriod(to)}` : fmtPeriod(from ?? to))

function AnomalyTooltip({ active, payload, anomaliesByPeriod }) {
    if (!active || !payload?.length) return null
    const point = payload[0].payload
    const anomaly = anomaliesByPeriod[point.period]
    return (
        <div className="bg-slate-900 border border-slate-700 rounded-md shadow-lg px-3 py-2 text-[12px] min-w-[170px]">
            <p className="font-mono text-[10px] tracking-[0.05em] uppercase text-slate-400 mb-1.5">{fmtPeriod(point.period)}</p>
            {point.evaluated ? (
                <p className="flex items-center justify-between gap-3">
                    <span className="text-slate-400">Monatsmittel</span>
                    <span className="font-semibold tnum text-white">{fmt(point.mean)}</span>
                </p>
            ) : (
                <p className="text-slate-400 italic m-0">
                    nicht bewertet (unter {point.minReviews} Bewertungen mit Wert)
                    {point.interpolated && <><br />Linie interpoliert, nur Darstellung</>}
                </p>
            )}
            <p className="flex items-center justify-between gap-3">
                <span className="text-slate-400">Bewertungen</span>
                <span className="tnum text-slate-300">{point.count}</span>
            </p>
            {point.n_values != null && point.n_values !== point.count && (
                <p className="flex items-center justify-between gap-3">
                    <span className="text-slate-400">davon mit Wert</span>
                    <span className="tnum text-slate-300">{point.n_values}</span>
                </p>
            )}
            {anomaly && (
                <div className="mt-1.5 pt-1.5 border-t border-slate-700 max-w-[280px]">
                    <p className="mb-1 inline-flex items-center gap-1.5 text-white font-medium">
                        <StepGlyph direction={anomaly.direction} severity={anomaly.severity} color={DIRECTION[anomaly.direction].glyph} />
                        Auffällige Veränderung ab diesem Monat ({DIRECTION[anomaly.direction].label}, {SEVERITY_LABEL[anomaly.severity] ?? anomaly.severity})
                    </p>
                    <p className="flex items-center justify-between gap-3">
                        <span className="text-slate-400">Delta</span>
                        <span className="font-semibold tnum text-white">{fmtDelta(anomaly.delta)} Sterne</span>
                    </p>
                    <p className="flex items-center justify-between gap-3">
                        <span className="text-slate-400">Ø davor</span>
                        <span className="tnum text-slate-300">{fmt(anomaly.before_mean)} ({fmtSpan(anomaly.before_from, anomaly.previous_period)})</span>
                    </p>
                    <p className="flex items-center justify-between gap-3">
                        <span className="text-slate-400">Ø ab hier</span>
                        <span className="tnum text-slate-300">{fmt(anomaly.after_mean)} ({fmtSpan(anomaly.date, anomaly.after_to)})</span>
                    </p>
                    <p className="flex items-center justify-between gap-3">
                        <span className="text-slate-400">Bewertungen mit Wert davor / ab hier</span>
                        <span className="tnum text-slate-300">{anomaly.n_reviews_before} / {anomaly.n_reviews_after}</span>
                    </p>
                    {anomaly.gap_months > 0 && (
                        <p className="m-0 mt-1 text-[11px] text-slate-400">
                            Davor {anomaly.gap_months} {anomaly.gap_months === 1 ? "Monat" : "Monate"} nicht bewertet (seit {fmtPeriod(anomaly.previous_period)}); der Übergang kann in dieser Lücke liegen.
                        </p>
                    )}
                    {anomaly.month_near_previous_level && (
                        <p className="m-0 mt-1 text-[11px] text-slate-400">
                            Das Monatsmittel liegt noch nahe am alten Niveau. Ein Abschnitt umfasst mindestens 3 Monate, der sichtbare Übergang folgt daher später.
                        </p>
                    )}
                </div>
            )}
        </div>
    )
}

/* Zähler für Untertitel (FA-26); bei nicht geeigneter Reihe kein "0". */
function countLabel(anomalies, eligibility) {
    if (eligibility && !eligibility.eligible) return "keine automatische Erkennung"
    const n = anomalies.length
    return `${n} ${n === 1 ? "auffällige Veränderung" : "auffällige Veränderungen"}`
}

/* Hinweis, wenn die Reihe für die automatische Erkennung zu dünn ist (E4). */
export function IneligibleNotice({ eligibility }) {
    return (
        <p className="text-[12px] text-slate-500 m-0">
            <span className="font-medium text-slate-700">Keine automatische Erkennung.</span>{" "}
            {eligibility?.reason}
        </p>
    )
}

export function AnomalyList({ anomalies, eligibility, emptyText = "Keine auffälligen Veränderungen erkannt." }) {
    if (eligibility && !eligibility.eligible) return <IneligibleNotice eligibility={eligibility} />
    if (!anomalies.length) {
        return <p className="text-[12px] text-slate-500 m-0">{emptyText}</p>
    }
    return (
        <ul className="m-0 p-0 list-none">
            {anomalies.map((a) => {
                const dir = DIRECTION[a.direction]
                return (
                    <li key={a.id} className="flex items-center gap-3 py-2 text-[12px] border-t border-slate-100 first:border-t-0">
                        <dir.Icon className="w-4 h-4 flex-none" style={{ color: dir.color }} aria-label={dir.label} />
                        <span className="w-[84px] flex-none text-slate-700 tnum">ab {fmtPeriod(a.date)}</span>
                        <span className="w-[92px] flex-none font-semibold tnum" style={{ color: dir.color }}>{fmtDelta(a.delta)} Sterne</span>
                        <span className="flex-1 min-w-0 truncate text-slate-500 tnum">
                            Ø {fmt(a.before_mean)} → {fmt(a.after_mean)} · Bewertungen davor / danach {a.n_reviews_before} / {a.n_reviews_after}
                            {a.gap_months > 0 && ` · nach ${a.gap_months} nicht ${a.gap_months === 1 ? "bewertetem Monat" : "bewerteten Monaten"}`}
                        </span>
                        <span className="flex-none text-[11px] text-slate-500">{SEVERITY_LABEL[a.severity] ?? a.severity}</span>
                    </li>
                )
            })}
        </ul>
    )
}

/* Punkt nur für bewertete Monate ohne bewerteten Nachbarn; sonst wären sie
   zwischen zwei Lücken unsichtbar, weil eine Linie zwei Punkte braucht. */
function isolatedDot(chartData, opacity = 1) {
    function IsolatedDot({ cx, cy, index }) {
        const isolated = chartData[index]?.value != null
            && chartData[index - 1]?.value == null
            && chartData[index + 1]?.value == null
        if (!isolated || cx == null || cy == null) return <g key={`iso-${index}`} />
        return <circle key={`iso-${index}`} cx={cx} cy={cy} r={2} fill="#3b82f6" fillOpacity={opacity} />
    }
    return IsolatedDot
}

/* Diagramm mit Lade-, Fehler- und Leerzustand; Höhe frei wählbar (Karte 220, Seite größer).
   Bewertete Monate bilden die durchgezogene Linie. Nicht bewertete Monate
   zwischen zwei bewerteten werden gestrichelt und linear überbrückt (nur
   Darstellung, siehe lib/anomalySeries.js). Angezeigt wird der Bereich vom
   ersten bis zum letzten bewerteten Monat; leere Ränder davor und danach
   werden ausgeblendet und unter dem Diagramm genannt. "range" ({from, to}
   oder null) wählt einen Ausschnitt; Interpolation und Erkennung beruhen
   trotzdem auf der ganzen Reihe, damit Linien am Fensterrand richtig
   weiterlaufen. */
/* compact (Dashboard-Karte): Die Niveaulinie ist die Hauptlinie, die Monatswerte
   laufen blass im Hintergrund, die Legende ist eine kurze Zeile ohne Erklärtexte.
   Ausführliche Legende und ausgeblendete Ränder stehen auf der Detailseite. */
export function AnomalyChart({ data, anomalies, loading, error, height = 220, range = null, showLevels = false, compact = false }) {
    const minReviews = data?.params?.min_reviews_per_month
    const series = useMemo(() => data?.series ?? [], [data])
    const trimmed = useMemo(() => trimToEvaluated(series), [series])
    // Niveau je Monat (Mittel des Abschnitts zwischen zwei erkannten Wechseln), nur mit showLevels.
    const levels = useMemo(() => (showLevels ? levelsFromAnomalies(anomalies) : {}), [anomalies, showLevels])
    const fullData = useMemo(() => {
        const interp = interpolateGaps(series)
        return series.map((m, i) => ({
            ...m,
            ...interp[i],
            minReviews,
            value: m.evaluated ? m.mean : null,
            level: levels[m.period] ?? null,
        }))
    }, [series, minReviews, levels])
    const chartData = useMemo(() => {
        const shown = trimmed.series.length
            ? fullData.filter((m) => inWindow(m.period, { from: trimmed.series[0].period, to: trimmed.series[trimmed.series.length - 1].period }))
            : fullData
        return range ? shown.filter((m) => inWindow(m.period, range)) : shown
    }, [fullData, trimmed, range])
    // Ausgeblendete Ränder nennen. Im Ausschnitt nur den hinteren: Das Fenster endet am
    // letzten bewerteten Monat, jüngere Monate mit wenigen Bewertungen fehlen sonst unbemerkt.
    const hiddenEdges = [range ? null : trimmed.hiddenBefore, trimmed.hiddenAfter].filter(Boolean)
    const visibleAnomalies = useMemo(
        () => anomalies.filter((a) => inWindow(a.date, range)),
        [anomalies, range],
    )
    const anomaliesByPeriod = useMemo(
        () => Object.fromEntries(visibleAnomalies.map((a) => [a.date, a])),
        [visibleAnomalies],
    )
    // Achse aus den sichtbaren Werten (bewertet, interpoliert, Niveaus und Stufen);
    // dünne Monatsmittel gehen nicht ein, weil sie die Achse verzerren würden.
    const yDomain = useMemo(() => {
        const vals = [
            ...chartData.flatMap((m) => [m.value, m.level, ...INTERP_KEYS.map((k) => m[k])]),
            ...visibleAnomalies.flatMap((a) => [a.before_mean, a.after_mean]),
        ].filter((v) => v != null)
        if (!vals.length) return [1, 5]
        return [Math.max(1, Math.floor((Math.min(...vals) - 0.2) * 2) / 2), Math.min(5, Math.ceil((Math.max(...vals) + 0.2) * 2) / 2)]
    }, [chartData, visibleAnomalies])
    // Achsenstriche auf dem 0,5er-Raster der Domain, bei schmalem Ausschnitt 0,25;
    // sonst setzt Recharts Viertelwerte, die toFixed(1) falsch beschriften würde.
    const yTicks = useMemo(() => {
        const step = yDomain[1] - yDomain[0] <= 1 ? 0.25 : 0.5
        const ticks = []
        for (let v = yDomain[0]; v <= yDomain[1] + 1e-9; v += step) ticks.push(+v.toFixed(2))
        return ticks
    }, [yDomain])
    const hasInterpolation = chartData.some((m) => m.interpolated)
    const hasVisibleValues = chartData.some((m) => m.value != null)
    const hasLevels = chartData.some((m) => m.level != null)
    const stepHalfWidth = compact ? 4 : height >= 300 ? 6 : 5
    const style = compact
        ? { valueOpacity: 0.35, valueWidth: 1, interpOpacity: 0.45, levelColor: "var(--color-fg-muted)", levelWidth: 1.5, levelOpacity: 1 }
        : { valueOpacity: 1, valueWidth: 1.5, interpOpacity: 1, levelColor: "var(--color-fg-subtle)", levelWidth: 1, levelOpacity: 0.8 }

    return (
        <div className="w-full">
        <div className="relative w-full" style={{ height }}>
            {error ? (
                <div className="h-full flex items-center justify-center">
                    <p className="text-[13px] text-slate-500">Anomalien konnten nicht geladen werden: {error}</p>
                </div>
            ) : series.length === 0 && !loading ? (
                <div className="h-full flex items-center justify-center">
                    <p className="text-[13px] text-slate-500">Keine datierten Bewertungen vorhanden.</p>
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
                            ticks={yTicks}
                            tick={{ fontSize: 10, fill: "var(--color-axis)" }}
                            tickLine={false}
                            axisLine={false}
                            width={34}
                            tickFormatter={(v) => (Number.isInteger(v * 2) ? v.toFixed(1) : v.toFixed(2))}
                        />
                        <Tooltip
                            content={<AnomalyTooltip anomaliesByPeriod={anomaliesByPeriod} />}
                            cursor={{ stroke: "var(--color-border-strong)", strokeWidth: 1, strokeDasharray: "3 3" }}
                            filterNull={false}
                        />
                        {INTERP_KEYS.map((key) => (
                            <Line
                                key={key}
                                type="linear"
                                dataKey={key}
                                stroke="var(--color-fg-subtle)"
                                strokeWidth={1.25}
                                strokeOpacity={style.interpOpacity}
                                strokeDasharray="4 4"
                                dot={false}
                                activeDot={false}
                                connectNulls={false}
                                legendType="none"
                                isAnimationActive={false}
                            />
                        ))}
                        {hasLevels && (
                            <Line
                                type="stepAfter"
                                dataKey="level"
                                stroke={style.levelColor}
                                strokeWidth={style.levelWidth}
                                strokeOpacity={style.levelOpacity}
                                dot={false}
                                activeDot={false}
                                connectNulls={false}
                                legendType="none"
                                isAnimationActive={false}
                            />
                        )}
                        <Line
                            type="monotone"
                            dataKey="value"
                            stroke="#3b82f6"
                            strokeWidth={style.valueWidth}
                            strokeOpacity={style.valueOpacity}
                            dot={isolatedDot(chartData, style.valueOpacity)}
                            activeDot={{ r: 3, stroke: "var(--color-bg-card)", strokeWidth: 1 }}
                            connectNulls={false}
                            isAnimationActive={false}
                        />
                        {visibleAnomalies.map((a) => (
                            <ReferenceLine
                                key={a.id}
                                segment={[{ x: a.date, y: a.before_mean }, { x: a.date, y: a.after_mean }]}
                                shape={stepShape(a, stepHalfWidth)}
                                ifOverflow="visible"
                            />
                        ))}
                    </LineChart>
                </ResponsiveContainer>
            )}
            {!error && !loading && series.length > 0 && !hasVisibleValues && (
                <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                    <p className="text-[13px] text-slate-500 bg-white/70 px-2 rounded">
                        {range ? "Im gewählten Zeitraum gibt es" : "Die Reihe hat"} keinen Monat mit mindestens {minReviews} Bewertungen.
                    </p>
                </div>
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
        {!error && minReviews != null && compact && (
            <p className="m-0 mt-2 flex flex-wrap items-center justify-center gap-x-3 gap-y-1 text-[11px] text-slate-500">
                <span className="inline-flex items-center gap-1.5">
                    <span className="inline-block w-4 h-0 border-t border-blue-500 opacity-50" />
                    Monatsmittel (ab {minReviews} Bewertungen)
                </span>
                {hasInterpolation && (
                    <span className="inline-flex items-center gap-1.5">
                        <span className="inline-block w-4 h-0 border-t border-dashed border-slate-400" />
                        interpoliert
                    </span>
                )}
                {hasLevels && (
                    <span className="inline-flex items-center gap-1.5">
                        <span className="inline-block w-4 h-0 border-t-[1.5px] border-slate-500" />
                        Niveau
                    </span>
                )}
                {visibleAnomalies.length > 0 && (
                    <>
                        <span className="inline-flex items-center gap-1"><StepGlyph direction="fall" /> Abfall</span>
                        <span className="inline-flex items-center gap-1"><StepGlyph direction="rise" /> Anstieg</span>
                    </>
                )}
            </p>
        )}
        {!error && minReviews != null && !compact && (
            <p className="m-0 mt-2 flex flex-wrap items-center justify-center gap-x-3 gap-y-1 text-[11px] text-slate-500">
                {hasInterpolation && (
                    <span className="inline-flex items-center gap-1.5">
                        <span className="inline-block w-4 h-0 border-t border-dashed border-slate-400" />
                        interpoliert (Monat mit weniger als {minReviews} Bewertungen mit Wert, nicht in der Erkennung)
                    </span>
                )}
                <span>Sternebewertung, Monatsmittel, Monate mit mindestens {minReviews} Bewertungen mit Wert</span>
            </p>
        )}
        {!error && visibleAnomalies.length > 0 && !compact && (
            <p className="m-0 mt-1 flex flex-wrap items-center justify-center gap-x-3 gap-y-1 text-[11px] text-slate-500">
                <span>Auffällige Veränderung des Niveaus ab dem markierten Monat, Stufe von Ø davor zu Ø danach:</span>
                <span className="inline-flex items-center gap-1"><StepGlyph direction="fall" /> Abfall</span>
                <span className="inline-flex items-center gap-1"><StepGlyph direction="rise" /> Anstieg</span>
                <span className="inline-flex items-center gap-1">
                    <StepGlyph direction="fall" color="var(--color-fg-muted)" /> kräftig = deutlich (ab 0,5 Sternen),
                    <StepGlyph direction="fall" severity="medium" color="var(--color-fg-muted)" /> dünn = mäßig
                </span>
                {hasLevels && (
                    <span className="inline-flex items-center gap-1.5">
                        <span className="inline-block w-4 h-0 border-t border-slate-400" />
                        Niveau (Mittel je Abschnitt)
                    </span>
                )}
            </p>
        )}
        {!error && minReviews != null && hiddenEdges.length > 0 && hasVisibleValues && !compact && (
            <p className="m-0 mt-1 text-center text-[11px] text-slate-400">
                Ausgeblendet (kein Monat mit mindestens {minReviews} Bewertungen mit Wert):{" "}
                {hiddenEdges
                    .map((e) => `${fmtPeriod(e.from)}${e.months > 1 ? ` – ${fmtPeriod(e.to)}` : ""} (${e.months} ${e.months === 1 ? "Monat" : "Monate"})`)
                    .join(", ")}
            </p>
        )}
        </div>
    )
}

/* Zeitfilter (Segmentschalter im Stil des Dashboard-Filters). Bezugspunkt ist
   der letzte bewertete Monat; der Filter wählt nur den Ausschnitt. */
export function TimeRangeFilter({ value, onChange }) {
    return (
        <div className="ds-time-filter" role="group" aria-label="Zeitraum">
            {TIME_RANGES.map(({ key, label }) => (
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

/* Auswahl der Dimension (Mitarbeiterquelle), Standard Gesamtbewertung. */
export function DimensionPicker({ value, onChange, compact = false }) {
    return (
        <DropdownPicker
            label="Dimension"
            icon={<Layers />}
            value={dimensionLabel(value)}
            options={EMPLOYEE_DIMENSIONS.map((d) => ({ value: d.key, label: d.label }))}
            onChange={onChange}
            align="start"
            compact={compact}
        />
    )
}

export const AnomalyCard = memo(function AnomalyCard({ companyId, onOpen }) {
    const [dimension, setDimension] = useState(OVERALL_DIMENSION.key)
    const { data, anomalies, loading, error } = useAnomalies(companyId, { source: SOURCE, dimension })

    if (!companyId) return null

    const subtitle = `${SOURCE_LABEL[SOURCE]} · ${dimensionLabel(dimension)} · ${countLabel(anomalies, data?.eligibility)}`
    const open = () => onOpen?.(dimension)

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
                icon={<AnomalyIcon />}
                eyebrow="VERLAUF · AUFFÄLLIGE VERÄNDERUNGEN"
                title="Anomalien im Verlauf"
                subtitle={subtitle}
                expandable
                actions={<DimensionPicker value={dimension} onChange={setDimension} compact />}
            />
            <div className="px-4 pt-4 pb-4">
                <AnomalyChart data={data} anomalies={anomalies} loading={loading} error={error} height={220} showLevels compact />

                {/* Die Liste der Veränderungen steht nur auf der Detailseite; die Karte
                    zeigt Verlauf und Zähler und erklärt nur, wenn nichts erkannt werden kann. */}
                {!loading && !error && data?.eligibility && !data.eligibility.eligible && (
                    <div className="mt-3 pt-3 border-t border-slate-100">
                        <IneligibleNotice eligibility={data.eligibility} />
                    </div>
                )}

                <p className="text-[11px] text-slate-400 text-center mt-3 m-0 inline-flex w-full items-center justify-center gap-1">
                    <Maximize2 className="w-3 h-3" />
                    Karte anklicken öffnet die Detailseite mit der Liste
                </p>
            </div>
        </div>
    )
})

export default AnomalyCard
