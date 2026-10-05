import { useEffect, useMemo, useState } from "react"
import { useLocation, useNavigate, useSearchParams } from "react-router-dom"
import { ArrowLeft, Building2, Diamond, GitCompareArrows, ListOrdered, MessageSquareText, MousePointerClick } from "lucide-react"
import { Anomaly as AnomalyIcon } from "../icons"
import { CompanySearchSelect } from "@/components/CompanySearchSelect"
import { AnomalyChart, AnomalyList, AnomalySourceToggle, DimensionPicker, OutlierList, StatusPicker, TimeRangeFilter } from "@/components/dashboard/AnomalyCard"
import { AnomalyComparison } from "@/components/dashboard/AnomalyComparison"
import { DrilldownPicker } from "@/components/dashboard/DrilldownPicker"
import { PageSection } from "@/components/dashboard/PageSection"
import { PeriodReviewList, TopicOnlyToggle, WindowSideToggle } from "@/components/dashboard/PeriodReviews"
import { DEFAULT_TIME_RANGE, comparisonWindows, fmtPeriod, inWindow, isPeriod, isTimeRangeKey, outlierCountText, periodIndex, periodWindows, selectionLabel, timeWindow, trimToEvaluated } from "@/lib/anomalySeries"
import { DEFAULT_SOURCE, OVERALL_DIMENSION, dimensionLabel, isDimensionOf, isSource } from "@/lib/ratingCategories"
import { groupLabel, validStatus } from "@/lib/reviewerStatus"
import { useAnomalies } from "@/hooks/useAnomalies"
import { useAnomalyComparison, usePeriodComparison } from "@/hooks/useAnomalyComparison"
import { useReviewPages } from "@/hooks/useReviewPages"
import { useTheme } from "@/hooks/useTheme"
import { loadCompanyName } from "@/lib/companies"

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
   Der Aktienkurs (Inkrement 3, E15) steht nicht hier, sondern im
   Aktien-Dashboard (/aktie, E16); unter dem Diagramm führt ein Link dorthin.
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
            <div className="h-12 min-h-[48px] border-b border-slate-200 bg-white flex items-center px-5 gap-3 sticky top-0 z-30 flex-shrink-0">
                <button
                    onClick={backToDashboard}
                    title="Zurück zum Dashboard"
                    className="h-7 w-7 rounded-md grid place-items-center text-slate-500 hover:bg-slate-100 hover:text-slate-900 [&_svg]:w-3.5 [&_svg]:h-3.5"
                >
                    <ArrowLeft />
                </button>
                <div className="h-5 w-px bg-slate-200" />
                <div className="flex items-center gap-2.5 min-w-0 flex-1">
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
                <div className="w-[260px] flex-none">
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

            <div className="flex-1 px-5 py-5 max-w-[1400px] w-full mx-auto space-y-4">
                {!companyId ? (
                    <PageSection icon={<Building2 />} eyebrow="AUSWAHL" title="Firma wählen">
                        <p className="m-0 text-[13px] text-slate-500">Oben rechts eine Firma suchen, um ihren Verlauf zu sehen.</p>
                    </PageSection>
                ) : (
                    <>
                        <PageSection
                            icon={<AnomalyIcon />}
                            eyebrow="VERLAUF · AUFFÄLLIGE VERÄNDERUNGEN"
                            title={`Monatsverlauf · ${dimensionLabel(dimension)}`}
                            subtitle={chartSubtitle}
                            actions={
                                <TimeRangeFilter
                                    value={rangeKey}
                                    onChange={(key) => updateParams({ range: key === DEFAULT_TIME_RANGE ? null : key })}
                                />
                            }
                        >
                            <AnomalyChart
                                data={data}
                                anomalies={anomalies}
                                loading={loading}
                                error={error}
                                height={380}
                                range={range}
                                showLevels
                                selectedId={selectedId}
                                onSelect={selectAnomaly}
                                selectedOutlier={selectedOutlier?.date ?? null}
                                onSelectOutlier={selectOutlier}
                                selection={selection}
                                onSelectPeriod={selectPeriod}
                            />
                            <p className="m-0 mt-3 pt-3 border-t border-slate-100 text-[11px] text-slate-500">
                                Aktienkurs, Kennzahlen und Nachrichten stehen im{" "}
                                <button
                                    type="button"
                                    className="underline underline-offset-2 text-slate-700 hover:text-slate-900"
                                    onClick={() => navigate(`/aktie?company=${companyId}`, { state: { company: { id: companyId, name: companyName } } })}
                                >
                                    Aktien-Dashboard
                                </button>
                                , dort auch zusammen mit diesem Bewertungsverlauf.
                            </p>
                        </PageSection>

                        {!error && data && (
                            <PageSection
                                icon={<MousePointerClick />}
                                eyebrow="DRILL-DOWN"
                                title="Bewertungen eines Zeitraums ansehen"
                                subtitle={selection
                                    ? `Auswahl ${selectionLabel(selection)}; Vergleich und Bewertungen stehen weiter unten`
                                    : selectedAnomaly
                                        ? `Ausgewählt ist die Veränderung ab ${fmtPeriod(selectedAnomaly.date)}; eine eigene Auswahl ersetzt sie`
                                        : "Monat im Diagramm anklicken, einen Zeitraum ziehen oder hier wählen; geht auch ohne erkannte Veränderung"}
                            >
                                <DrilldownPicker
                                    key={selectionKey ?? "none"}
                                    months={seriesMonths}
                                    selection={selection}
                                    onSelect={selectPeriod}
                                    onClear={selection || selectedAnomaly ? clearSelection : null}
                                />
                            </PageSection>
                        )}

                        <PageSection
                            icon={<ListOrdered />}
                            eyebrow="LISTE"
                            title="Auffällige Veränderungen"
                            subtitle={range
                                ? `Im gewählten Zeitraum (${fmtPeriod(range.from)} – ${fmtPeriod(range.to)}); Abfälle zuerst, innerhalb nach Größe`
                                : "Abfälle zuerst, innerhalb nach Größe der Veränderung"}
                        >
                            {!loading && !error && <AnomalyList
                                    anomalies={visibleAnomalies}
                                    eligibility={eligibility}
                                    emptyText={range ? "Im gewählten Zeitraum keine auffälligen Veränderungen." : undefined}
                                    selectedId={selectedId}
                                    onSelect={selectAnomaly}
                                />}
                            {!loading && !error && range && hiddenCount > 0 && (
                                <p className="m-0 mt-2 text-[11px] text-slate-500">
                                    {hiddenCount}{visibleAnomalies.length ? " weitere" : ""} {hiddenCount === 1 ? "auffällige Veränderung liegt" : "auffällige Veränderungen liegen"} außerhalb des gewählten Zeitraums.{" "}
                                    <button
                                        type="button"
                                        className="underline underline-offset-2 text-slate-700 hover:text-slate-900"
                                        onClick={() => updateParams({ range: null })}
                                    >
                                        Gesamten Zeitraum zeigen
                                    </button>
                                </p>
                            )}
                            {!loading && !error && selectedId && !selectedAnomaly && (
                                <p className="m-0 mt-2 text-[11px] text-slate-500">
                                    Die ausgewählte Veränderung gibt es mit den aktuellen Einstellungen nicht.{" "}
                                    <button
                                        type="button"
                                        className="underline underline-offset-2 text-slate-700 hover:text-slate-900"
                                        onClick={() => updateParams({ anomaly: null, month: null, from: null, to: null })}
                                    >
                                        Auswahl aufheben
                                    </button>
                                </p>
                            )}
                        </PageSection>

                        {!loading && !error && eligibility?.eligible && (
                            <PageSection
                                icon={<Diamond />}
                                eyebrow="LISTE · E14"
                                title="Auffällige Einzelmonate"
                                subtitle="Monate, die stark von ihren Nachbarmonaten abweichen, ohne ein neues Niveau zu bilden (mindestens 3 σ und 0,5 Sterne); größte Abweichung zuerst"
                            >
                                <OutlierList
                                    outliers={visibleOutliers}
                                    selectedPeriod={selectedOutlier?.date ?? null}
                                    onSelect={selectOutlier}
                                    emptyText={range ? "Im gewählten Zeitraum keine auffälligen Einzelmonate." : undefined}
                                />
                            </PageSection>
                        )}

                        {selection && selectionWindows && (
                            <PageSection
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
                        )}

                        {selection && selectionWindows && reviewSpan && (
                            <PageSection
                                icon={<MessageSquareText />}
                                eyebrow={`EINZELBEWERTUNGEN · AUSWAHL ${selectionLabel(selection).toUpperCase()}`}
                                title="Bewertungen der Auswahl"
                                subtitle={`${group} · ${periodSide === "before" ? "Zeitraum davor" : "Auswahl"} · ${selectionLabel(reviewSpan)}${
                                    reviewPages.loading || reviewPages.error ? "" : ` · ${reviewPages.total} ${reviewPages.total === 1 ? "Bewertung" : "Bewertungen"}${mentionText}`}`}
                                actions={
                                    <>
                                        {topicToggle}
                                        <WindowSideToggle
                                            value={periodSide}
                                            onChange={(key) => setPeriodSideState({ key: selectionKey, side: key })}
                                            labels={{ before: "Zeitraum davor", after: "Auswahl" }}
                                        />
                                    </>
                                }
                            >
                                <PeriodReviewList
                                    key={`${selectionKey}:${periodSide}:${topicOnly}`}
                                    pages={reviewPages}
                                    emptyText={topicOnly ? "Keine Bewertung dieses Zeitraums nennt das Thema." : "Keine Bewertungen in diesem Zeitraum."}
                                />
                                <p className="m-0 mt-3 text-[11px] text-slate-400">
                                    Alle Bewertungen der gewählten Kalendermonate, auch aus Monaten mit wenigen Bewertungen. Vergleichszeitraum: die gleich
                                    vielen Monate direkt davor, mindestens 6 (E17, vorläufig).
                                </p>
                            </PageSection>
                        )}

                        {selectedAnomaly && windows && (
                            <PageSection
                                icon={<GitCompareArrows />}
                                eyebrow={`VERGLEICH · VERÄNDERUNG AB ${fmtPeriod(selectedAnomaly.date).toUpperCase()}`}
                                title="Vorher-Nachher-Vergleich"
                                subtitle={comparison.data
                                    ? `${group} · davor ${fmtPeriod(comparison.data.windows.before.from)} – ${fmtPeriod(comparison.data.windows.before.to)}: ${comparison.data.windows.before.n_reviews} · ab dem markierten Monat ${fmtPeriod(comparison.data.windows.after.from)} – ${fmtPeriod(comparison.data.windows.after.to)}: ${comparison.data.windows.after.n_reviews} Bewertungen`
                                    : `${group} · Verschiebungen in den Bewertungen zwischen den Vergleichsfenstern`}
                            >
                                <AnomalyComparison data={comparison.data} loading={comparison.loading} error={comparison.error} />
                            </PageSection>
                        )}

                        {selectedAnomaly && windows && (
                            <PageSection
                                icon={<MessageSquareText />}
                                eyebrow={`EINZELBEWERTUNGEN · VERÄNDERUNG AB ${fmtPeriod(selectedAnomaly.date).toUpperCase()}`}
                                title="Bewertungen des Zeitraums"
                                subtitle={`${group} · ${side === "before" ? "davor" : "ab dem markierten Monat"} · ${fmtPeriod(sideWindow.from)}${sideWindow.from !== sideWindow.to ? ` – ${fmtPeriod(sideWindow.to)}` : ""}${
                                    reviewPages.loading || reviewPages.error ? "" : ` · ${reviewPages.total} ${reviewPages.total === 1 ? "Bewertung" : "Bewertungen"}${mentionText}`}`}
                                actions={
                                    <>
                                        {topicToggle}
                                        <WindowSideToggle value={side} onChange={(key) => setSideState({ id: selectedId, side: key })} />
                                    </>
                                }
                            >
                                <PeriodReviewList key={`${selectedId}:${side}:${topicOnly}`} pages={reviewPages} emptyText={topicOnly ? "Keine Bewertung dieses Zeitraums nennt das Thema." : undefined} />
                                <p className="m-0 mt-3 text-[11px] text-slate-400">
                                    Vergleichsfenster: bis zu {windows.windowMonths} Kalendermonate vor dem markierten Monat und ab ihm, begrenzt
                                    durch die benachbarten Veränderungen; alle Bewertungen dieser Monate, auch aus Monaten mit wenigen Bewertungen.
                                </p>
                            </PageSection>
                        )}
                    </>
                )}
            </div>
        </div>
    )
}
