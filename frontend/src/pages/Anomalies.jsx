import { useEffect, useMemo, useState } from "react"
import { useLocation, useNavigate, useSearchParams } from "react-router-dom"
import { ArrowLeft, Building2, Diamond, GitCompareArrows, ListOrdered, MessageSquareText, MousePointerClick } from "lucide-react"
import { Anomaly as AnomalyIcon } from "../icons"
import { CompanySearchSelect } from "@/components/CompanySearchSelect"
import { AnomalyChart, AnomalyList, AnomalySourceToggle, DimensionPicker, OutlierList, StatusPicker, TimeRangeFilter } from "@/components/dashboard/AnomalyCard"
import { AnomalyComparison } from "@/components/dashboard/AnomalyComparison"
import { DrilldownPicker } from "@/components/dashboard/DrilldownPicker"
import { MarketSourceNote, PriceToggle } from "@/components/dashboard/MarketContext"
import { PageSection } from "@/components/dashboard/PageSection"
import { PeriodReviewList, TopicOnlyToggle, WindowSideToggle } from "@/components/dashboard/PeriodReviews"
import { DEFAULT_TIME_RANGE, comparisonWindows, fmtPeriod, inWindow, isPeriod, isTimeRangeKey, outlierCountText, periodIndex, periodWindows, selectionLabel, timeWindow, trimToEvaluated } from "@/lib/anomalySeries"
import { DEFAULT_SOURCE, OVERALL_DIMENSION, dimensionLabel, isDimensionOf, isSource } from "@/lib/ratingCategories"
import { PRICE_ON, PRICE_PARAM, noPriceText } from "@/lib/market"
import { groupLabel, validStatus } from "@/lib/reviewerStatus"
import { useAnomalies } from "@/hooks/useAnomalies"
import { useAnomalyComparison, usePeriodComparison } from "@/hooks/useAnomalyComparison"
import { useCompanyResource } from "@/hooks/useCompanyResource"
import { useReviewPages } from "@/hooks/useReviewPages"
import { useTheme } from "@/hooks/useTheme"
import { SHOW_FINANCE_EXTRAS } from "@/config"
import { loadCompany, loadCompanyName } from "@/lib/companies"

/* ============================================================================
   Anomalies — Detailseite "Anomalien im Verlauf" (Inkrement 1).
   Geöffnet per Klick auf die AnomalyCard im Dashboard, analog zum Vergleich.
   Die Firma steht in der URL (?company=ID), damit Neuladen und Teilen
   funktionieren; der Name kommt aus dem Navigationszustand oder /companies.
   Dimension und Zeitraum stehen ebenfalls in der URL (?dimension=key&range=1y),
   seit Inkrement 2 auch Quelle und Status (?source=candidates&status=eingestellt).
   Der Zeitraum wählt nur den Ausschnitt; erkannt wird auf der ganzen Reihe.
   Inkrement 2: Ein Klick auf eine Stufe oder Listenzeile wählt die Veränderung
   aus (?anomaly=id); darunter stehen der Vorher-Nachher-Vergleich und die
   Bewertungen der Vergleichsfenster. Auffällige Einzelmonate (E14) stehen in
   einer eigenen Liste. Freier Drill-down (E17): Klick auf einen beliebigen
   Monat, Ziehen über einen Zeitraum oder das Auswahlfeld setzt ?from=&to=
   (YYYY-MM; das ältere ?month= gilt als from = to); darunter stehen der
   Vergleich mit dem Zeitraum davor und die Bewertungen der Auswahl, auch wenn
   die Reihe keine erkannte Veränderung hat.
   Aktienkurs (Inkrement 3, E15, Nachtrag 2026-10-05): Hat die Firma einen
   Ticker, blendet das Kästchen "Aktienkurs" im Kopf des Monatsverlaufs den
   Kurs auf einer zweiten Achse ein (?kurs=an, Standard aus). Erst dann wird
   /market geladen; unter dem Diagramm stehen dann der feste Hinweis und bei
   der Konzernmutter der Vermerk. Der Link zum Aktien-Dashboard (/aktie, E16)
   bleibt in jedem Fall.
   ============================================================================ */

export default function AnomaliesPage() {
    const location = useLocation()
    const navigate = useNavigate()
    const [searchParams, setSearchParams] = useSearchParams()
    useTheme() // gespeichertes Theme auch beim direkten Öffnen der Seite anwenden

    const companyId = searchParams.get("company") || (location.state?.company?.id != null ? String(location.state.company.id) : null)
    const [names, setNames] = useState(() =>
        location.state?.company?.id != null ? { [String(location.state.company.id)]: location.state.company.name ?? "" } : {},
    )
    const [query, setQuery] = useState(location.state?.company?.name ?? "")
    const companyName = companyId ? names[companyId] ?? "" : ""
    const sourceParam = searchParams.get("source")
    const source = isSource(sourceParam) ? sourceParam : DEFAULT_SOURCE
    const status = validStatus(source, searchParams.get("status"))
    const group = groupLabel(source, status)
    const dimensionParam = searchParams.get("dimension")
    const dimension = isDimensionOf(source, dimensionParam) ? dimensionParam : OVERALL_DIMENSION.key
    const rangeParam = searchParams.get("range")
    const rangeKey = isTimeRangeKey(rangeParam) ? rangeParam : DEFAULT_TIME_RANGE

    // Suchparameter ändern, ohne die übrigen (Firma, Dimension) zu verlieren.
    const updateParams = (patch) => {
        const next = new URLSearchParams(searchParams)
        Object.entries(patch).forEach(([k, v]) => (v == null ? next.delete(k) : next.set(k, v)))
        setSearchParams(next)
    }

    // Firma aus dem Navigationszustand in die URL übernehmen (Neuladen, Teilen).
    useEffect(() => {
        if (companyId && !searchParams.get("company")) {
            const next = new URLSearchParams(searchParams)
            next.set("company", companyId)
            setSearchParams(next, { replace: true })
        }
    }, [companyId, searchParams, setSearchParams])

    // Namen nachladen, wenn die Seite direkt über die URL geöffnet wurde
    // (gemeinsame Firmenliste, lib/companies.js).
    useEffect(() => {
        if (!companyId || names[companyId]) return undefined
        let active = true
        loadCompanyName(companyId)
            .then((name) => {
                if (active && name) {
                    setNames((n) => ({ ...n, [companyId]: name }))
                    setQuery(name)
                }
            })
            .catch(() => {})
        return () => { active = false }
    }, [companyId, names])

    // Ticker aus der gemeinsamen Firmenliste: Nur mit Ticker gibt es das Kästchen
    // "Aktienkurs". null = kein Ticker oder Firma unbekannt.
    const [tickers, setTickers] = useState({})
    useEffect(() => {
        if (!companyId || companyId in tickers) return undefined
        let active = true
        loadCompany(companyId)
            .then((company) => {
                if (active) setTickers((t) => ({ ...t, [companyId]: company?.ticker || null }))
            })
            .catch(() => {})
        return () => { active = false }
    }, [companyId, tickers])
    const hasTicker = Boolean(companyId && tickers[companyId])
    // Kurs als Einordnung (E15): Standard aus; /market wird erst geladen, wenn er an ist.
    const showPrice = hasTicker && searchParams.get(PRICE_PARAM) === PRICE_ON
    const market = useCompanyResource(showPrice ? companyId : null, "market")
    const marketData = market.data?.available ? market.data : null

    const { data, anomalies, loading, error } = useAnomalies(companyId, { source, dimension, status })
    const selectedId = searchParams.get("anomaly")
    const selectedAnomaly = useMemo(() => anomalies.find((a) => a.id === selectedId) ?? null, [anomalies, selectedId])
    const windows = useMemo(() => comparisonWindows(selectedAnomaly), [selectedAnomaly])
    // Fenster der Bewertungsliste; beim Wechsel der Veränderung wieder "davor".
    const [sideState, setSideState] = useState({ id: null, side: "before" })
    const side = sideState.id === selectedId ? sideState.side : "before"
    const sideWindow = windows?.[side] ?? null
    const outliers = useMemo(() => data?.outlier_months ?? [], [data])
    // Freie Auswahl (E17): ?from=&to=, ?month= als ein Monat; nur ohne ausgewählte Veränderung.
    const fromParam = searchParams.get("from") ?? searchParams.get("month")
    const toParam = searchParams.get("to") ?? searchParams.get("month")
    const selection = useMemo(() => {
        if (selectedAnomaly || !isPeriod(fromParam) || !isPeriod(toParam)) return null
        const [a, b] = [fromParam, toParam].sort((x, y) => periodIndex(x) - periodIndex(y))
        return { from: a, to: b }
    }, [selectedAnomaly, fromParam, toParam])
    const selectionKey = selection ? `${selection.from}_${selection.to}` : null
    const selectionWindows = useMemo(() => (selection ? periodWindows(selection.from, selection.to) : null), [selection])
    const selectedOutlier = selection && selection.from === selection.to ? outliers.find((o) => o.date === selection.from) ?? null : null
    // Fenster der Bewertungsliste der Auswahl; Standard ist die Auswahl selbst.
    const [periodSideState, setPeriodSideState] = useState({ key: null, side: "after" })
    const periodSide = periodSideState.key === selectionKey ? periodSideState.side : "after"
    const reviewSpan = selectedAnomaly ? sideWindow : selectionWindows?.[periodSide] ?? null
    // Nur Bewertungen mit dem Thema der Dimension (?thema=nur); nur bei Einzeldimension.
    const topicOnly = dimension !== OVERALL_DIMENSION.key && searchParams.get("thema") === "nur"
    const reviewPages = useReviewPages(companyId, {
        source, status, start: reviewSpan?.start, end: reviewSpan?.end,
        dimension: dimension === OVERALL_DIMENSION.key ? null : dimension,
        topicOnly,
    })
    const topicToggle = reviewPages.highlight?.topic && (
        <TopicOnlyToggle
            topic={reviewPages.highlight.topic}
            checked={topicOnly}
            onChange={(on) => updateParams({ thema: on ? "nur" : null })}
        />
    )
    // " · davon 12 nennen Image" für die Untertitel der Bewertungslisten.
    const mentionText = reviewPages.highlight?.topic && reviewPages.highlight.mentions != null && !topicOnly
        ? ` · davon ${reviewPages.highlight.mentions} ${reviewPages.highlight.mentions === 1 ? "nennt" : "nennen"} ${reviewPages.highlight.topic}`
        : topicOnly && reviewPages.highlight?.topic ? `, die ${reviewPages.highlight.topic} nennen` : ""
    const comparison = useAnomalyComparison(companyId, selectedAnomaly?.id, { source, dimension, status })
    const periodComparison = usePeriodComparison(companyId, selection, { source, dimension, status })
    // Karte "Markierungen": Veränderungen oder Einzelmonate (?liste=einzelmonate).
    const markerTab = searchParams.get("liste") === "einzelmonate" ? "outliers" : "changes"
    const setMarkerTab = (key) => updateParams({ liste: key === "outliers" ? "einzelmonate" : null })
    const selectAnomaly = (id) => updateParams({ anomaly: id, month: null, from: null, to: null })
    const selectPeriod = (from, to) => updateParams({ from, to, month: null, anomaly: null })
    const selectOutlier = (period) => selectPeriod(period, period)
    const clearSelection = () => updateParams({ anomaly: null, month: null, from: null, to: null })
    // Monate der Reihe für das Auswahlfeld (erster bis letzter Monat mit datierter Bewertung).
    const seriesMonths = useMemo(() => (data?.series ?? []).map((m) => m.period), [data])
    const eligibility = data?.eligibility
    const count = anomalies.length
    // Sichtbares Fenster relativ zum letzten angezeigten (bewerteten) Monat; null = alles.
    const range = useMemo(() => timeWindow(trimToEvaluated(data?.series).series, rangeKey), [data, rangeKey])
    const visibleAnomalies = useMemo(() => anomalies.filter((a) => inWindow(a.date, range)), [anomalies, range])
    const hiddenCount = count - visibleAnomalies.length
    const visibleOutliers = useMemo(() => outliers.filter((o) => inWindow(o.date, range)), [outliers, range])
    const countText = `${count} ${count === 1 ? "auffällige Veränderung" : "auffällige Veränderungen"}`
    // Im Fehlerfall und beim Laden kein Zähler: "0" wäre dort eine falsche Aussage.
    const chartSubtitle = error || loading
        ? group
        : eligibility && !eligibility.eligible
        ? `${group} · keine automatische Erkennung`
        : range
            ? `${group} · ${fmtPeriod(range.from)} – ${fmtPeriod(range.to)} · ${count
                ? `${visibleAnomalies.length} von ${count} ${count === 1 ? "auffälligen Veränderung" : "auffälligen Veränderungen"} im Zeitraum`
                : "keine auffälligen Veränderungen"}${outlierCountText(visibleOutliers.length)}`
            : `${group} · ${countText}${outlierCountText(outliers.length)}`

    // Zurück mit der gewählten Firma, damit das Dashboard sie wieder anzeigt.
    const backToDashboard = () =>
        navigate("/dashboard", companyId ? { state: { companyId, companyName } } : undefined)

    const selectCompany = (company) => {
        if (!company) return
        const id = String(company.id)
        setNames((n) => ({ ...n, [id]: company.name }))
        setQuery(company.name)
        updateParams({ company: id, anomaly: null, month: null, from: null, to: null })
    }

    return (
        <div className="min-h-screen bg-slate-50 flex flex-col">
            {/* Topbar — wie im Vergleich */}
            <div className="min-h-[48px] py-1.5 border-b border-slate-200 bg-white flex flex-wrap items-center px-5 gap-x-3 gap-y-1.5 sticky top-0 z-30 flex-shrink-0">
                <button
                    onClick={backToDashboard}
                    title="Zurück zum Dashboard"
                    className="h-7 w-7 rounded-md grid place-items-center text-slate-500 hover:bg-slate-100 hover:text-slate-900 [&_svg]:w-3.5 [&_svg]:h-3.5"
                >
                    <ArrowLeft />
                </button>
                <div className="h-5 w-px bg-slate-200" />
                <div className="flex items-center gap-2.5 min-w-[180px] flex-1">
                    <span className="w-7 h-7 rounded-md grid place-items-center flex-none bg-slate-100 text-slate-600 [&_svg]:w-[14px] [&_svg]:h-[14px]">
                        <AnomalyIcon />
                    </span>
                    <div className="min-w-0">
                        <p className="m-0 mb-0.5 font-mono text-[10px] tracking-[0.06em] uppercase text-slate-500 leading-none">
                            ANALYSE · ANOMALIEN IM VERLAUF
                        </p>
                        <p className="m-0 text-[14px] leading-5 font-semibold tracking-tight text-slate-900 truncate">
                            {companyName ? `Anomalien · ${companyName}` : "Anomalien"}
                        </p>
                    </div>
                </div>
                {companyId && (
                    <AnomalySourceToggle
                        value={source}
                        onChange={(key) => updateParams({
                            source: key === DEFAULT_SOURCE ? null : key,
                            status: null,
                            dimension: isDimensionOf(key, dimension) && dimension !== OVERALL_DIMENSION.key ? dimension : null,
                            anomaly: null, month: null,
                        })}
                    />
                )}
                {companyId && (
                    <StatusPicker
                        source={source}
                        value={status}
                        onChange={(key) => updateParams({ status: key, anomaly: null })}
                    />
                )}
                {companyId && (
                    <DimensionPicker
                        source={source}
                        value={dimension}
                        onChange={(key) => updateParams({ dimension: key === OVERALL_DIMENSION.key ? null : key, anomaly: null })}
                    />
                )}
                <div className="w-[260px] max-w-full flex-none">
                    <CompanySearchSelect
                        value={query}
                        onValueChange={setQuery}
                        onCompanySelect={selectCompany}
                        onCreateNew={null}
                        variant="light"
                        compact
                        placeholder="Firma wechseln…"
                    />
                </div>
            </div>

            <div className="flex-1 px-5 py-3 max-w-[1600px] w-full mx-auto space-y-3">
                {!companyId ? (
                    <PageSection icon={<Building2 />} eyebrow="AUSWAHL" title="Firma wählen">
                        <p className="m-0 text-[13px] text-slate-500">Oben rechts eine Firma suchen, um ihren Verlauf zu sehen.</p>
                    </PageSection>
                ) : (
                    <>
                        {/* Verlauf (zwei Drittel) und Markierungen (ein Drittel) */}
                        <div className="grid gap-3 xl:grid-cols-3">
                            <PageSection
                                className="xl:col-span-2"
                                icon={<AnomalyIcon />}
                                eyebrow="VERLAUF · AUFFÄLLIGE VERÄNDERUNGEN"
                                title={`Monatsverlauf · ${dimensionLabel(dimension)}`}
                                subtitle={chartSubtitle}
                                actions={
                                    <>
                                        {hasTicker && (
                                            <PriceToggle
                                                checked={showPrice}
                                                onChange={(on) => updateParams({ [PRICE_PARAM]: on ? PRICE_ON : null })}
                                            />
                                        )}
                                        <TimeRangeFilter
                                            value={rangeKey}
                                            onChange={(key) => updateParams({ range: key === DEFAULT_TIME_RANGE ? null : key })}
                                        />
                                    </>
                                }
                                bodyClassName="px-4 pt-3 pb-3"
                            >
                                <AnomalyChart
                                    data={data}
                                    anomalies={anomalies}
                                    loading={loading}
                                    error={error}
                                    height={340}
                                    range={range}
                                    showLevels
                                    selectedId={selectedId}
                                    onSelect={selectAnomaly}
                                    selectedOutlier={selectedOutlier?.date ?? null}
                                    onSelectOutlier={selectOutlier}
                                    selection={selection}
                                    onSelectPeriod={selectPeriod}
                                    market={showPrice ? marketData : null}
                                />
                                <div className="mt-2 pt-2 border-t border-slate-100 space-y-1">
                                    {/* Eingeblendeter Kurs: fester Hinweis, Wertpapier (Konzernmutter ausdrücklich), Quelle */}
                                    {showPrice && (market.loading ? (
                                        <p className="m-0 text-[11px] text-slate-500">Lade Aktienkurs…</p>
                                    ) : market.error ? (
                                        <p className="m-0 text-[11px] text-slate-500">Aktienkurs konnte nicht geladen werden: {market.error}</p>
                                    ) : marketData ? (
                                        <MarketSourceNote market={marketData} companyName={companyName} subject="Kurs" />
                                    ) : (
                                        <p className="m-0 text-[11px] text-slate-500">{noPriceText(market.data?.reason)}</p>
                                    ))}
                                    <p className="m-0 text-[11px] text-slate-500">
                                        {SHOW_FINANCE_EXTRAS ? "Aktienkurs, Kennzahlen und Nachrichten" : "Aktienkurs und Kennzahlen"} stehen im{" "}
                                        <button
                                            type="button"
                                            className="underline underline-offset-2 text-slate-700 hover:text-slate-900"
                                            onClick={() => navigate(`/aktie?company=${companyId}`, { state: { company: { id: companyId, name: companyName } } })}
                                        >
                                            Aktien-Dashboard
                                        </button>
                                        , dort auch zusammen mit diesem Bewertungsverlauf.
                                    </p>
                                </div>
                            </PageSection>

                            <PageSection
                                className="flex flex-col"
                                icon={markerTab === "outliers" ? <Diamond /> : <ListOrdered />}
                                eyebrow={range ? `MARKIERUNGEN · ${fmtPeriod(range.from).toUpperCase()} – ${fmtPeriod(range.to).toUpperCase()}` : "MARKIERUNGEN"}
                                title={markerTab === "outliers" ? "Auffällige Einzelmonate" : "Auffällige Veränderungen"}
                                subtitle={markerTab === "outliers"
                                    ? "Starke Abweichung von den Nachbarmonaten, kein neues Niveau (E14); größte zuerst"
                                    : "Niveauwechsel (E9); Abfälle zuerst, innerhalb nach Größe"}
                                bodyClassName="px-4 pt-2 pb-3 flex-1 min-h-0 flex flex-col"
                            >
                                {eligibility?.eligible && (
                                    <div className="ds-time-filter self-start mb-2" role="group" aria-label="Markierungen">
                                        {[
                                            { key: "changes", label: `Veränderungen (${visibleAnomalies.length})` },
                                            { key: "outliers", label: `Einzelmonate (${visibleOutliers.length})` },
                                        ].map((t) => (
                                            <button key={t.key} type="button" aria-pressed={markerTab === t.key}
                                                className={`ds-time-btn${markerTab === t.key ? " active" : ""}`} onClick={() => setMarkerTab(t.key)}>
                                                {t.label}
                                            </button>
                                        ))}
                                    </div>
                                )}
                                {/* Eigener Scrollbereich: ab xl so hoch wie der Verlauf daneben */}
                                <div className="relative flex-1 min-h-0">
                                    <div className="max-h-[360px] xl:max-h-none xl:absolute xl:inset-0 overflow-y-auto overscroll-contain pr-1">
                                        {loading ? (
                                            <p className="m-0 text-[12px] text-slate-500">Lade Markierungen…</p>
                                        ) : error ? (
                                            <p className="m-0 text-[12px] text-slate-500">Keine Markierungen: {error}</p>
                                        ) : markerTab === "outliers" && eligibility?.eligible ? (
                                            <OutlierList
                                                compact
                                                outliers={visibleOutliers}
                                                selectedPeriod={selectedOutlier?.date ?? null}
                                                onSelect={selectOutlier}
                                                emptyText={range ? "Im gewählten Zeitraum keine auffälligen Einzelmonate." : undefined}
                                            />
                                        ) : (
                                            <AnomalyList
                                                compact
                                                anomalies={visibleAnomalies}
                                                eligibility={eligibility}
                                                emptyText={range ? "Im gewählten Zeitraum keine auffälligen Veränderungen." : "Keine auffälligen Veränderungen erkannt. Für einen Zeitraum ohne Markierung: Monat anklicken, ziehen oder unten wählen."}
                                                selectedId={selectedId}
                                                onSelect={selectAnomaly}
                                            />
                                        )}
                                    </div>
                                </div>
                                {!loading && !error && range && markerTab !== "outliers" && hiddenCount > 0 && (
                                    <p className="m-0 mt-2 text-[11px] text-slate-500">
                                        {hiddenCount} weitere außerhalb des Zeitraums.{" "}
                                        <button type="button" className="underline underline-offset-2 text-slate-700 hover:text-slate-900"
                                            onClick={() => updateParams({ range: null })}>
                                            Gesamten Zeitraum zeigen
                                        </button>
                                    </p>
                                )}
                                {!loading && !error && selectedId && !selectedAnomaly && (
                                    <p className="m-0 mt-2 text-[11px] text-slate-500">
                                        Die ausgewählte Veränderung gibt es mit den aktuellen Einstellungen nicht.{" "}
                                        <button type="button" className="underline underline-offset-2 text-slate-700 hover:text-slate-900"
                                            onClick={clearSelection}>
                                            Auswahl aufheben
                                        </button>
                                    </p>
                                )}
                            </PageSection>
                        </div>

                        {/* Drill-down-Leiste: freie Auswahl eines Zeitraums (E17) */}
                        {!error && data && (
                            <div className="bg-white border border-slate-200 rounded-lg shadow-xs px-4 py-2.5 flex flex-wrap items-center gap-x-4 gap-y-2">
                                <div className="flex items-center gap-2.5 min-w-0">
                                    <span className="w-7 h-7 rounded-md grid place-items-center flex-none bg-slate-100 text-slate-600 [&_svg]:w-[14px] [&_svg]:h-[14px]">
                                        <MousePointerClick />
                                    </span>
                                    <div className="min-w-0">
                                        <p className="m-0 mb-0.5 font-mono text-[10px] tracking-[0.06em] uppercase text-slate-500 leading-none">DRILL-DOWN</p>
                                        <p className="m-0 text-[13px] font-semibold text-slate-900 leading-5 truncate">
                                            {selectedAnomaly
                                                ? `Veränderung ab ${fmtPeriod(selectedAnomaly.date)}`
                                                : selection
                                                    ? `Auswahl ${selectionLabel(selection)}`
                                                    : "Zeitraum wählen"}
                                        </p>
                                    </div>
                                </div>
                                <DrilldownPicker
                                    key={selectionKey ?? "none"}
                                    months={seriesMonths}
                                    selection={selection}
                                    onSelect={selectPeriod}
                                    onClear={selection || selectedAnomaly ? clearSelection : null}
                                />
                                {!selection && !selectedAnomaly && (
                                    <p className="m-0 text-[11px] text-slate-500 basis-full xl:basis-auto xl:ml-auto">
                                        oder im Verlauf: Stufe, Raute oder Monat anklicken, Zeitraum ziehen
                                    </p>
                                )}
                            </div>
                        )}

                        {/* Ausgewählte Veränderung: Vergleich (links) und Bewertungen (rechts); ab xl
                            sind beide gleich hoch, die Bewertungsliste scrollt in dieser Höhe. */}
                        {selectedAnomaly && windows && (
                            <div className="grid gap-3 xl:grid-cols-5">
                                <PageSection
                                    className="xl:col-span-3"
                                    icon={<GitCompareArrows />}
                                    eyebrow={`VERGLEICH · VERÄNDERUNG AB ${fmtPeriod(selectedAnomaly.date).toUpperCase()}`}
                                    title="Vorher-Nachher-Vergleich"
                                    subtitle={comparison.data
                                        ? `${group} · davor ${fmtPeriod(comparison.data.windows.before.from)} – ${fmtPeriod(comparison.data.windows.before.to)}: ${comparison.data.windows.before.n_reviews} · ab dem markierten Monat ${fmtPeriod(comparison.data.windows.after.from)} – ${fmtPeriod(comparison.data.windows.after.to)}: ${comparison.data.windows.after.n_reviews} Bewertungen`
                                        : `${group} · Verschiebungen in den Bewertungen zwischen den Vergleichsfenstern`}
                                >
                                    <AnomalyComparison data={comparison.data} loading={comparison.loading} error={comparison.error} />
                                </PageSection>
                                <PageSection
                                    className="xl:col-span-2 flex flex-col"
                                    bodyClassName="px-4 py-4 flex-1 min-h-0 flex flex-col"
                                    icon={<MessageSquareText />}
                                    eyebrow={`EINZELBEWERTUNGEN · VERÄNDERUNG AB ${fmtPeriod(selectedAnomaly.date).toUpperCase()}`}
                                    title="Bewertungen des Zeitraums"
                                    subtitle={`${group} · ${side === "before" ? "davor" : "ab dem markierten Monat"} · ${fmtPeriod(sideWindow.from)}${sideWindow.from !== sideWindow.to ? ` – ${fmtPeriod(sideWindow.to)}` : ""}${
                                        reviewPages.loading || reviewPages.error ? "" : ` · ${reviewPages.total} ${reviewPages.total === 1 ? "Bewertung" : "Bewertungen"}${mentionText}`}`}
                                    actions={<WindowSideToggle value={side} onChange={(key) => setSideState({ id: selectedId, side: key })} />}
                                >
                                    {topicToggle && <div className="mb-2">{topicToggle}</div>}
                                    <div className="relative flex-1 min-h-[320px]"><div className="max-h-[720px] xl:max-h-none xl:absolute xl:inset-0 overflow-y-auto overscroll-contain pr-1">
                                        <PeriodReviewList key={`${selectedId}:${side}:${topicOnly}`} pages={reviewPages} emptyText={topicOnly ? "Keine Bewertung dieses Zeitraums nennt das Thema." : undefined} />
                                    </div></div>
                                    <p className="m-0 mt-3 text-[11px] text-slate-400">
                                        Vergleichsfenster: bis zu {windows.windowMonths} Kalendermonate vor dem markierten Monat und ab ihm, begrenzt
                                        durch die benachbarten Veränderungen; alle Bewertungen dieser Monate.
                                    </p>
                                </PageSection>
                            </div>
                        )}

                        {/* Freie Auswahl (E17): Vergleich mit dem Zeitraum davor und Bewertungen */}
                        {selection && selectionWindows && (
                            <div className="grid gap-3 xl:grid-cols-5">
                                <PageSection
                                    className="xl:col-span-3"
                                    icon={<GitCompareArrows />}
                                    eyebrow={`DRILL-DOWN · AUSWAHL ${selectionLabel(selection).toUpperCase()}`}
                                    title="Vergleich mit dem Zeitraum davor"
                                    subtitle={periodComparison.data
                                        ? `${group} · Zeitraum davor ${selectionLabel(periodComparison.data.windows.before)}: ${periodComparison.data.windows.before.n_reviews} · Auswahl ${selectionLabel(periodComparison.data.windows.after)}: ${periodComparison.data.windows.after.n_reviews} Bewertungen`
                                        : `${group} · Auswahl gegen den gleich langen Zeitraum davor (mindestens ${selectionWindows.windowMonths} Monate)`}
                                >
                                    {selectedOutlier && (
                                        <p className="m-0 mb-3 text-[12px] text-slate-600">
                                            Auffälliger Einzelmonat: {fmtPeriod(selectedOutlier.date)} weicht um {String(selectedOutlier.deviation).replace(".", ",")} Sterne
                                            vom Niveau seiner Nachbarmonate ab. Das ist ein Hinweis auf einen auffälligen Monat, keine Aussage über Ursachen.
                                        </p>
                                    )}
                                    <AnomalyComparison
                                        data={periodComparison.data}
                                        loading={periodComparison.loading}
                                        error={periodComparison.error}
                                        labels={{ before: "Zeitraum davor", after: "Auswahl" }}
                                    />
                                </PageSection>
                                {reviewSpan && (
                                    <PageSection
                                        className="xl:col-span-2 flex flex-col"
                                        bodyClassName="px-4 py-4 flex-1 min-h-0 flex flex-col"
                                        icon={<MessageSquareText />}
                                        eyebrow={`EINZELBEWERTUNGEN · AUSWAHL ${selectionLabel(selection).toUpperCase()}`}
                                        title="Bewertungen der Auswahl"
                                        subtitle={`${group} · ${periodSide === "before" ? "Zeitraum davor" : "Auswahl"} · ${selectionLabel(reviewSpan)}${
                                            reviewPages.loading || reviewPages.error ? "" : ` · ${reviewPages.total} ${reviewPages.total === 1 ? "Bewertung" : "Bewertungen"}${mentionText}`}`}
                                        actions={
                                            <WindowSideToggle
                                                value={periodSide}
                                                onChange={(key) => setPeriodSideState({ key: selectionKey, side: key })}
                                                labels={{ before: "Zeitraum davor", after: "Auswahl" }}
                                            />
                                        }
                                    >
                                        {topicToggle && <div className="mb-2">{topicToggle}</div>}
                                        <div className="relative flex-1 min-h-[320px]"><div className="max-h-[720px] xl:max-h-none xl:absolute xl:inset-0 overflow-y-auto overscroll-contain pr-1">
                                            <PeriodReviewList
                                                key={`${selectionKey}:${periodSide}:${topicOnly}`}
                                                pages={reviewPages}
                                                emptyText={topicOnly ? "Keine Bewertung dieses Zeitraums nennt das Thema." : "Keine Bewertungen in diesem Zeitraum."}
                                            />
                                        </div></div>
                                        <p className="m-0 mt-3 text-[11px] text-slate-400">
                                            Alle Bewertungen der gewählten Kalendermonate. Vergleichszeitraum: die gleich vielen Monate direkt davor,
                                            mindestens 6 (E17, vorläufig).
                                        </p>
                                    </PageSection>
                                )}
                            </div>
                        )}
                    </>
                )}
            </div>
        </div>
    )
}
