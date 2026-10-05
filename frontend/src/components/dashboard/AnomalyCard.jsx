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
    ReferenceDot,
    ReferenceArea,
} from "recharts"
import { ArrowDownRight, ArrowUpRight, Layers, Maximize2, Users } from "lucide-react"
import { Anomaly as AnomalyIcon } from "../../icons"
import { useAnomalies } from "@/hooks/useAnomalies"
import { ChartCardHeader, DropdownPicker, SourceToggle } from "./ChartHeader"
import { DEFAULT_SOURCE, OVERALL_DIMENSION, SOURCES, dimensionLabel, dimensionsFor, isDimensionOf } from "@/lib/ratingCategories"
import { groupLabel, statusOptions } from "@/lib/reviewerStatus"
import { INTERP_KEYS, TIME_RANGES, comparisonWindows, fmtPeriod, inWindow, interpolateGaps, levelsFromAnomalies, outlierCountText, periodIndex, trimToEvaluated } from "@/lib/anomalySeries"
import { PARENT_SCOPE, fmtPrice, fmtPriceTick } from "@/lib/market"

/* ============================================================================
   AnomalyCard — Monatsverlauf mit auffälligen Veränderungen (Inkrement 1).
   Daten: GET /analytics/company/{id}/anomalies (live berechnet, nur lesend).
   Die Karte zeigt Verlauf und Zähler; die Liste der Veränderungen steht nur auf
   der Detailseite /anomalies, die ein Klick auf die Karte öffnet (onOpen).
   Wortwahl: "auffällige Veränderung", keine Aussage über Ursachen.
   Inkrement 2: Quelle (Mitarbeiter, Bewerber) und Status wählen die
   Bewertendengruppe; die Erkennung läuft je Gruppe neu (E13).
   Inkrement 3: Im Aktien-Dashboard läuft der Aktienkurs als Einordnung auf einer
   zweiten Y-Achse mit (prop "market"); die Dashboard-Karte übergibt keinen Kurs.
   ============================================================================ */

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

/* Ring-Symbol der Karte (Legende): wie die ReferenceDot-Markierung im Diagramm. */
function RingGlyph({ direction, size = 10 }) {
    const color = DIRECTION[direction].color
    return (
        <svg width={size} height={size} viewBox="0 0 10 10" aria-hidden="true" className="flex-none">
            <circle cx="5" cy="5" r="3.75" fill={color} fillOpacity={0.35} stroke={color} strokeWidth={1.5} />
        </svg>
    )
}

/* Raute für auffällige Einzelmonate (E14): Monat, der stark von seinen
   Nachbarmonaten abweicht, ohne ein neues Niveau zu bilden. Hohl, damit sie
   sich von den Ringen der Karte und den Stufen der Detailseite unterscheidet. */
export function DiamondGlyph({ direction, size = 10 }) {
    const color = DIRECTION[direction].color
    return (
        <svg width={size} height={size} viewBox="0 0 10 10" aria-hidden="true" className="flex-none">
            <path d="M5 0.75 L9.25 5 L5 9.25 L0.75 5 Z" fill="var(--color-bg-card)" stroke={color} strokeWidth={1.5} strokeLinejoin="round" />
        </svg>
    )
}

function diamondShape(outlier, { selected = false, onSelect = null, size = 5 } = {}) {
    function OutlierMarker({ cx, cy }) {
        if (![cx, cy].every(Number.isFinite)) return <g />
        const r = selected ? size + 1.5 : size
        return (
            <path
                d={`M${cx} ${cy - r} L${cx + r} ${cy} L${cx} ${cy + r} L${cx - r} ${cy} Z`}
                fill="var(--color-bg-card)"
                stroke={DIRECTION[outlier.direction].color}
                strokeWidth={selected ? 2.25 : 1.5}
                strokeLinejoin="round"
                onClick={onSelect ? () => onSelect(outlier.date) : undefined}
                style={onSelect ? { cursor: "pointer" } : undefined}
            />
        )
    }
    return OutlierMarker
}

/* Markierung im Diagramm: Stufe am markierten Monat von Ø davor (links) zu
   Ø danach (rechts). Höhe = Ausmaß im Maßstab der Y-Achse, Form = Richtung,
   Strichstärke = Schweregrad. Der Monatswert selbst bleibt auf der Linie. */
function stepShape(anomaly, halfWidth, { selected = false, onSelect = null } = {}) {
    function StepMarker({ x1, y1, y2 }) {
        if (![x1, y1, y2].every(Number.isFinite)) return <g />
        const d = `M${x1 - halfWidth} ${y1} H${x1} V${y2} H${x1 + halfWidth}`
        return (
            <g
                onClick={onSelect ? () => onSelect(anomaly.id) : undefined}
                style={onSelect ? { cursor: "pointer" } : undefined}
            >
                {/* Breitere, unsichtbare Trefferfläche, damit die Stufe gut anklickbar ist. */}
                {onSelect && <path d={d} fill="none" stroke="transparent" strokeWidth={12} pointerEvents="stroke" />}
                <path
                    d={d}
                    fill="none"
                    stroke={DIRECTION[anomaly.direction].color}
                    strokeWidth={(STEP_WIDTH[anomaly.severity] ?? 1.5) + (selected ? 1.25 : 0)}
                    strokeLinecap="round"
                    strokeLinejoin="round"
                />
            </g>
        )
    }
    return StepMarker
}

const SEVERITY_LABEL = { high: "deutlich", medium: "mäßig" }

const fmt = (v, digits = 2) =>
    v == null ? "–" : Number(v).toLocaleString("de-DE", { minimumFractionDigits: digits, maximumFractionDigits: digits })

const fmtDelta = (v) => (v > 0 ? "+" : v < 0 ? "−" : "") + fmt(Math.abs(v))

const fmtSpan = (from, to) => (from && to && from !== to ? `${fmtPeriod(from)} – ${fmtPeriod(to)}` : fmtPeriod(from ?? to))

function AnomalyTooltip({ active, payload, anomaliesByPeriod, outliersByPeriod = {}, priceCurrency = null }) {
    if (!active || !payload?.length) return null
    const point = payload[0].payload
    const anomaly = anomaliesByPeriod[point.period]
    const outlier = outliersByPeriod[point.period]
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
            {priceCurrency && point.price != null && (
                <p className="flex items-center justify-between gap-3">
                    <span className="text-slate-400">Aktienkurs (Monatsschluss)</span>
                    <span className="tnum text-slate-300">{fmtPrice(point.price)} {priceCurrency}</span>
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
            {outlier && (
                <div className="mt-1.5 pt-1.5 border-t border-slate-700 max-w-[280px]">
                    <p className="mb-1 inline-flex items-center gap-1.5 text-white font-medium">
                        <DiamondGlyph direction={outlier.direction} />
                        Auffälliger Einzelmonat ({outlier.direction === "fall" ? "unter" : "über"} den Nachbarmonaten)
                    </p>
                    <p className="flex items-center justify-between gap-3">
                        <span className="text-slate-400">Abweichung</span>
                        <span className="font-semibold tnum text-white">{fmtDelta(outlier.deviation)} Sterne</span>
                    </p>
                    <p className="flex items-center justify-between gap-3">
                        <span className="text-slate-400">Niveau der Nachbarmonate</span>
                        <span className="tnum text-slate-300">{fmt(outlier.level)} ({fmtSpan(outlier.neighbours_from, outlier.neighbours_to)})</span>
                    </p>
                    <p className="m-0 mt-1 text-[11px] text-slate-400">
                        Einzelner Monat, kein neues Niveau; beruht auf {outlier.n_values} Bewertungen mit Wert.
                    </p>
                </div>
            )}
        </div>
    )
}

/* Zähler für Untertitel (FA-26); bei nicht geeigneter Reihe kein "0". */
function countLabel(anomalies, eligibility, outliers = []) {
    if (eligibility && !eligibility.eligible) return "keine automatische Erkennung"
    const n = anomalies.length
    return `${n} ${n === 1 ? "auffällige Veränderung" : "auffällige Veränderungen"}${outlierCountText(outliers.length)}`
}

/* Liste der auffälligen Einzelmonate (Detailseite); Klick wählt den Monat aus. */
export function OutlierList({ outliers, selectedPeriod = null, onSelect = null, emptyText = "Keine auffälligen Einzelmonate." }) {
    if (!outliers.length) return <p className="text-[12px] text-slate-500 m-0">{emptyText}</p>
    return (
        <ul className="m-0 p-0 list-none">
            {outliers.map((o) => {
                const selected = o.date === selectedPeriod
                const select = () => onSelect?.(o.date)
                return (
                    <li
                        key={o.id}
                        className={[
                            "flex items-center gap-3 py-2 text-[12px] border-t border-slate-100 first:border-t-0",
                            onSelect ? "cursor-pointer px-2 -mx-2 rounded-md hover:bg-slate-50" : "",
                            selected ? "bg-slate-100 hover:bg-slate-100" : "",
                        ].join(" ")}
                        onClick={onSelect ? select : undefined}
                        onKeyDown={onSelect ? (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); select() } } : undefined}
                        role={onSelect ? "button" : undefined}
                        tabIndex={onSelect ? 0 : undefined}
                        aria-pressed={onSelect ? selected : undefined}
                        title={onSelect ? "Auswählen: Bewertungen dieses Monats zeigen" : undefined}
                    >
                        <DiamondGlyph direction={o.direction} size={12} />
                        <span className="w-[84px] flex-none text-slate-700 tnum">{fmtPeriod(o.date)}</span>
                        <span className="w-[92px] flex-none font-semibold tnum" style={{ color: DIRECTION[o.direction].color }}>{fmtDelta(o.deviation)} Sterne</span>
                        <span className="flex-1 min-w-0 truncate text-slate-500 tnum">
                            Ø {fmt(o.month_mean)} gegen Niveau {fmt(o.level)} der Nachbarmonate ({fmtSpan(o.neighbours_from, o.neighbours_to)}) · {o.n_values} Bewertungen mit Wert
                        </span>
                    </li>
                )
            })}
        </ul>
    )
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

export function AnomalyList({ anomalies, eligibility, emptyText = "Keine auffälligen Veränderungen erkannt.", selectedId = null, onSelect = null }) {
    if (eligibility && !eligibility.eligible) return <IneligibleNotice eligibility={eligibility} />
    if (!anomalies.length) {
        return <p className="text-[12px] text-slate-500 m-0">{emptyText}</p>
    }
    return (
        <ul className="m-0 p-0 list-none">
            {anomalies.map((a) => {
                const dir = DIRECTION[a.direction]
                const selected = a.id === selectedId
                const rowClass = [
                    "flex items-center gap-3 py-2 text-[12px] border-t border-slate-100 first:border-t-0",
                    onSelect ? "cursor-pointer px-2 -mx-2 rounded-md hover:bg-slate-50" : "",
                    selected ? "bg-slate-100 hover:bg-slate-100" : "",
                ].join(" ")
                const select = () => onSelect?.(a.id)
                return (
                    <li
                        key={a.id}
                        className={rowClass}
                        onClick={onSelect ? select : undefined}
                        onKeyDown={onSelect ? (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); select() } } : undefined}
                        role={onSelect ? "button" : undefined}
                        tabIndex={onSelect ? 0 : undefined}
                        aria-pressed={onSelect ? selected : undefined}
                        title={onSelect ? "Auswählen: Bewertungen und Vergleich des Zeitraums zeigen" : undefined}
                    >
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
/* compact (Dashboard-Karte): Darstellung wie in der ersten Version der Karte –
   kräftige Monatslinie, je Veränderung ein dezenter Ring auf dem Monatswert des
   markierten Monats, unter dem Diagramm nur Interpolation und Datenbasis.
   Stufen, Niveaulinie, ausführliche Legende und ausgeblendete Ränder stehen auf
   der Detailseite.
   Ausführliche Legende und ausgeblendete Ränder stehen auf der Detailseite. */
/* market (Aktien-Dashboard, Inkrement 3, E15/E16): {prices: [{period, close}], currency,
   ticker} oder null. Der Kurs läuft als dünne Linie auf einer rechten Y-Achse mit,
   nur für die angezeigten Monate. Er ist eine Einordnung des Marktumfelds; es wird
   kein Zusammenhang mit den Bewertungen berechnet.
   showLegend=false blendet die Zeilen unter dem Diagramm aus (kleine Karte im
   Aktien-Dashboard; die vergrößerte Ansicht zeigt sie). */
export function AnomalyChart({ data, anomalies, loading, error, height = 220, range = null, showLevels = false, compact = false, selectedId = null, onSelect = null, selectedOutlier = null, onSelectOutlier = null, market = null, showLegend = true }) {
    const minReviews = data?.params?.min_reviews_per_month
    const series = useMemo(() => data?.series ?? [], [data])
    const trimmed = useMemo(() => trimToEvaluated(series), [series])
    // Niveau je Monat (Mittel des Abschnitts zwischen zwei erkannten Wechseln), nur mit showLevels.
    const levels = useMemo(() => (showLevels ? levelsFromAnomalies(anomalies) : {}), [anomalies, showLevels])
    // Monatsschlusskurs je Monat; Monate ohne Kurs bleiben leer.
    const priceByPeriod = useMemo(
        () => (market?.prices?.length ? Object.fromEntries(market.prices.map((p) => [p.period, p.close])) : null),
        [market],
    )
    const fullData = useMemo(() => {
        const interp = interpolateGaps(series)
        return series.map((m, i) => ({
            ...m,
            ...interp[i],
            minReviews,
            value: m.evaluated ? m.mean : null,
            level: levels[m.period] ?? null,
            price: priceByPeriod?.[m.period] ?? null,
        }))
    }, [series, minReviews, levels, priceByPeriod])
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
    // Auffällige Einzelmonate (E14) im sichtbaren Ausschnitt.
    const visibleOutliers = useMemo(
        () => (data?.outlier_months ?? []).filter((o) => inWindow(o.date, range)),
        [data, range],
    )
    const outliersByPeriod = useMemo(
        () => Object.fromEntries(visibleOutliers.map((o) => [o.date, o])),
        [visibleOutliers],
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
    // Vergleichsfenster der ausgewählten Veränderung als Flächen, auf den sichtbaren Ausschnitt begrenzt.
    const windowAreas = useMemo(() => {
        const selected = anomalies.find((a) => a.id === selectedId)
        const windows = selected && !compact ? comparisonWindows(selected) : null
        if (!windows || !chartData.length) return []
        const first = periodIndex(chartData[0].period)
        const last = periodIndex(chartData[chartData.length - 1].period)
        return [
            { key: "before", win: windows.before, color: "var(--color-fg-subtle)" },
            { key: "after", win: windows.after, color: DIRECTION[selected.direction].color },
        ].flatMap(({ key, win, color }) => {
            const from = Math.max(periodIndex(win.from), first)
            const to = Math.min(periodIndex(win.to), last)
            if (from > to) return []
            const period = (i) => chartData.find((m) => periodIndex(m.period) === i)?.period
            return [{ key, x1: period(from), x2: period(to), color }]
        }).filter((a) => a.x1 && a.x2)
    }, [anomalies, selectedId, chartData, compact])
    // Klick auf den Monat einer Veränderung wählt sie aus (zusätzlich zur Stufe selbst).
    // Ohne Veränderung in diesem Monat wählt der Klick einen auffälligen Einzelmonat aus.
    const handleChartClick = (state) => {
        const idx = Number(state?.activeTooltipIndex)
        const period = state?.activeLabel ?? (Number.isInteger(idx) ? chartData[idx]?.period : null)
        if (!period) return
        if (onSelect && anomaliesByPeriod[period]) onSelect(anomaliesByPeriod[period].id)
        else if (onSelectOutlier && outliersByPeriod[period]) onSelectOutlier(period)
    }
    const hasInterpolation = chartData.some((m) => m.interpolated)
    const hasVisibleValues = chartData.some((m) => m.value != null)
    const hasLevels = chartData.some((m) => m.level != null)
    const showPrice = Boolean(priceByPeriod) && chartData.some((m) => m.price != null)
    const stepHalfWidth = compact ? 4 : height >= 300 ? 6 : 5
    const style = { valueOpacity: 1, valueWidth: 1.5, interpOpacity: 1, levelColor: "var(--color-fg-subtle)", levelWidth: 1, levelOpacity: 0.8 }

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
                    <LineChart data={chartData} margin={{ left: 0, right: showPrice ? 4 : 16, top: 8, bottom: 5 }} onClick={onSelect || onSelectOutlier ? handleChartClick : undefined}>
                        <CartesianGrid strokeDasharray="2 4" stroke="var(--color-grid)" vertical={false} />
                        {windowAreas.map((a) => (
                            <ReferenceArea key={a.key} x1={a.x1} x2={a.x2} fill={a.color} fillOpacity={0.08} stroke="none" ifOverflow="hidden" />
                        ))}
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
                        {showPrice && (
                            <YAxis
                                yAxisId="price"
                                orientation="right"
                                domain={["auto", "auto"]}
                                tick={{ fontSize: 10, fill: "var(--color-axis)" }}
                                tickLine={false}
                                axisLine={false}
                                width={58}
                                tickFormatter={fmtPriceTick}
                                label={{ value: `Kurs in ${market.currency ?? "?"}`, angle: 90, position: "insideRight", offset: 0, fontSize: 10, fill: "var(--color-axis)" }}
                            />
                        )}
                        <Tooltip
                            content={<AnomalyTooltip anomaliesByPeriod={anomaliesByPeriod} outliersByPeriod={outliersByPeriod} priceCurrency={showPrice ? market.currency ?? "" : null} />}
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
                        {showPrice && (
                            // Aktienkurs: dünn und zurückhaltend unter der Bewertungslinie.
                            <Line
                                yAxisId="price"
                                type="linear"
                                dataKey="price"
                                stroke="var(--market-price)"
                                strokeWidth={1}
                                strokeOpacity={0.7}
                                dot={false}
                                activeDot={{ r: 2.5, fill: "var(--market-price)", stroke: "var(--color-bg-card)", strokeWidth: 1 }}
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
                        {visibleAnomalies.map((a) => (compact ? (
                            // Karte: Ring auf dem Monatswert des markierten Monats (erste Version).
                            <ReferenceDot
                                key={a.id}
                                x={a.date}
                                y={a.month_mean}
                                r={a.severity === "high" ? 5 : 4}
                                fill={DIRECTION[a.direction].color}
                                fillOpacity={0.35}
                                stroke={DIRECTION[a.direction].color}
                                strokeWidth={1.5}
                                ifOverflow="visible"
                            />
                        ) : (
                            <ReferenceLine
                                key={a.id}
                                segment={[{ x: a.date, y: a.before_mean }, { x: a.date, y: a.after_mean }]}
                                shape={stepShape(a, stepHalfWidth, { selected: a.id === selectedId, onSelect })}
                                ifOverflow="visible"
                            />
                        )))}
                        {visibleOutliers.map((o) => (
                            <ReferenceDot
                                key={o.id}
                                x={o.date}
                                y={o.month_mean}
                                ifOverflow="visible"
                                shape={diamondShape(o, { selected: o.date === selectedOutlier, onSelect: onSelectOutlier, size: compact ? 4 : 5 })}
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
        {showLegend && !error && minReviews != null && (
            <p className="m-0 mt-2 flex flex-wrap items-center justify-center gap-x-3 gap-y-1 text-[11px] text-slate-500">
                {hasInterpolation && (
                    <span className="inline-flex items-center gap-1.5">
                        <span className="inline-block w-4 h-0 border-t border-dashed border-slate-400" />
                        interpoliert (Monat mit weniger als {minReviews} Bewertungen mit Wert, nicht in der Erkennung)
                    </span>
                )}
                <span>Sternebewertung, Monatsmittel, Monate mit mindestens {minReviews} Bewertungen mit Wert</span>
                {showPrice && (
                    <span className="inline-flex items-center gap-1.5">
                        <span className="inline-block w-4 h-0 border-t" style={{ borderColor: "var(--market-price)" }} />
                        Aktienkurs{market.ticker ? ` ${market.ticker}` : ""}{market.ticker_scope === PARENT_SCOPE ? " (Konzernmutter)" : ""}, Monatsschluss in {market.currency ?? "?"}, bereinigt (rechte Achse)
                    </span>
                )}
            </p>
        )}
        {showLegend && !error && compact && visibleAnomalies.length > 0 && (
            <p className="m-0 mt-1 flex flex-wrap items-center justify-center gap-x-3 gap-y-1 text-[11px] text-slate-500">
                <span>Ring = auffällige Veränderung ab diesem Monat:</span>
                <span className="inline-flex items-center gap-1"><RingGlyph direction="fall" /> Abfall</span>
                <span className="inline-flex items-center gap-1"><RingGlyph direction="rise" /> Anstieg</span>
            </p>
        )}
        {showLegend && !error && visibleOutliers.length > 0 && (
            <p className="m-0 mt-1 flex flex-wrap items-center justify-center gap-x-3 gap-y-1 text-[11px] text-slate-500">
                <span className="inline-flex items-center gap-1">
                    <DiamondGlyph direction="fall" /><DiamondGlyph direction="rise" />
                    auffälliger Einzelmonat (unter bzw. über den Nachbarmonaten, mindestens 3 σ und 0,5 Sterne; kein neues Niveau)
                </span>
            </p>
        )}
        {showLegend && !error && visibleAnomalies.length > 0 && !compact && (
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
                {windowAreas.length > 0 && (
                    <span className="inline-flex items-center gap-1.5">
                        <span className="inline-block w-3 h-2.5 rounded-[2px] bg-slate-200" />
                        Vergleichsfenster der ausgewählten Veränderung
                    </span>
                )}
                {onSelect && windowAreas.length === 0 && <span>Stufe anklicken, um die Bewertungen des Zeitraums zu sehen.</span>}
            </p>
        )}
        {showLegend && !error && minReviews != null && hiddenEdges.length > 0 && hasVisibleValues && !compact && (
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
export function TimeRangeFilter({ value, onChange, small = false }) {
    return (
        <div className={`ds-time-filter${small ? " ds-time-filter-sm" : ""}`} role="group" aria-label="Zeitraum">
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

/* Auswahl der Dimension der Quelle, Standard Gesamtbewertung. */
export function DimensionPicker({ value, onChange, source = DEFAULT_SOURCE, compact = false }) {
    return (
        <DropdownPicker
            label="Dimension"
            icon={<Layers />}
            value={dimensionLabel(value)}
            options={dimensionsFor(source).map((d) => ({ value: d.key, label: d.label }))}
            onChange={onChange}
            align="start"
            compact={compact}
        />
    )
}

/* Quelle der Bewertungen (Mitarbeiter, Bewerber). */
export function AnomalySourceToggle({ value, onChange, compact = false }) {
    return <SourceToggle value={value} onChange={onChange} options={SOURCES} compact={compact} />
}

/* Auswahl des Status innerhalb der Quelle; null = alle (E13). */
export function StatusPicker({ source, value, onChange, compact = false }) {
    const options = statusOptions(source)
    return (
        <DropdownPicker
            label="Status"
            icon={<Users />}
            value={options.find((o) => o.key === value)?.label ?? "Alle"}
            options={options.map((o) => ({ value: o.key ?? "", label: o.label }))}
            onChange={(key) => onChange(key || null)}
            align="start"
            compact={compact}
        />
    )
}

export const AnomalyCard = memo(function AnomalyCard({ companyId, onOpen }) {
    const [selection, setSelection] = useState({ source: DEFAULT_SOURCE, dimension: OVERALL_DIMENSION.key, status: null })
    const { source, dimension, status } = selection
    const { data, anomalies, loading, error } = useAnomalies(companyId, { source, dimension, status })

    if (!companyId) return null

    const subtitle = `${groupLabel(source, status)} · ${dimensionLabel(dimension)} · ${countLabel(anomalies, data?.eligibility, data?.outlier_months ?? [])}`
    const open = () => onOpen?.(selection)
    // Quellenwechsel: Status zurücksetzen, Dimension nur behalten, wenn es sie in der neuen Quelle gibt.
    const changeSource = (next) => setSelection((s) => ({
        source: next,
        status: null,
        dimension: isDimensionOf(next, s.dimension) ? s.dimension : OVERALL_DIMENSION.key,
    }))

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
                actions={
                    <>
                        <AnomalySourceToggle value={source} onChange={changeSource} compact />
                        <DimensionPicker source={source} value={dimension} onChange={(key) => setSelection((s) => ({ ...s, dimension: key }))} compact />
                        <StatusPicker source={source} value={status} onChange={(key) => setSelection((s) => ({ ...s, status: key }))} compact />
                    </>
                }
            />
            <div className="px-4 pt-4 pb-4">
                <AnomalyChart data={data} anomalies={anomalies} loading={loading} error={error} height={220} compact />

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
