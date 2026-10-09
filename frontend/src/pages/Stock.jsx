import { useEffect, useMemo, useState, useSyncExternalStore } from "react"
import { useLocation, useNavigate, useSearchParams } from "react-router-dom"
import { ArrowLeft, BarChart3, Building2, LineChart, Newspaper, Users } from "lucide-react"
import { TrendUp } from "../icons"
import { CompanySearchSelect } from "@/components/CompanySearchSelect"
import { DataStatusBar } from "@/components/dashboard/DataStatusBar"
import { PageSection } from "@/components/dashboard/PageSection"
import { ExpandableCard } from "@/components/dashboard/ExpandableCard"
import { FinanceKpis, MarketSourceNote, PriceToggle } from "@/components/dashboard/MarketContext"
import { AnomalyChart, TimeRangeFilter } from "@/components/dashboard/AnomalyCard"
import { AnalystChart, EarningsChart, EmptyNote, NewsList, StockPriceChart } from "@/components/dashboard/FinanceCards"
import { useAnomalies } from "@/hooks/useAnomalies"
import { useCompanyResource } from "@/hooks/useCompanyResource"
import { useTheme } from "@/hooks/useTheme"
import { SHOW_FINANCE_EXTRAS } from "@/config"
import { loadCompanyName } from "@/lib/companies"
import { DEFAULT_TIME_RANGE, fmtPeriod, isTimeRangeKey, timeWindow, trimToEvaluated } from "@/lib/anomalySeries"
import {
    DEFAULT_PRICE_RANGE, PARENT_SCOPE, GROUP_COMPANY_SCOPE, PRICE_OFF, PRICE_PARAM, PRICE_RANGES, isPriceRangeKey, noPriceText, pricesInRange,
} from "@/lib/market"

/* ============================================================================
   Stock — Aktien-Dashboard (/aktie, Inkrement 3, E16).
   Übersicht auf einer Bildschirmseite: oben eine Kennzahlenleiste, darunter
   Karten für Kursverlauf, Analystenempfehlungen, Umsatz und Nettoergebnis
   sowie Nachrichten. Jede Karte vergrößert sich per Klick (ExpandableCard,
   wie im Haupt-Dashboard). Ab 1280 px Breite füllt das Raster die Höhe des
   Fensters (mindestens 620 px), die Diagramme wachsen mit; darunter stehen
   die Karten mit festen Höhen untereinander.

   Die Kurskarte hat zwei Ansichten (?ansicht=bewertung): nur der Kurs
   (Zeitraum ?range=1y|3y|5y|10y|max) oder der Kurs auf einer zweiten Achse
   über dem Monatsverlauf der Sternebewertung (Mitarbeitende,
   Gesamtbewertung) mit den auffälligen Veränderungen (Zeitraum
   ?verlauf=5y|3y|1y, Kurs aus mit ?kurs=aus). In der vergrößerten Ansicht
   öffnet ein Klick auf eine Markierung sie auf der Anomalien-Seite.
   Jahres- oder Quartalszahlen: ?periode=quartal. Alles ist Einordnung des
   Marktumfelds; ein Zusammenhang mit den Bewertungen wird nicht behauptet.

   Rolle in der Arbeit (E16): Kurs und Kennzahlen decken FA-15. Die Karten
   Analystenempfehlungen, Umsatz und Nettoergebnis sowie Aktuelle Meldungen
   und ihre Kacheln (Nettoergebnis, Analysten) sind ein Zusatz außerhalb des
   evaluierten Artefakts. VITE_SHOW_FINANCE_EXTRAS=false blendet sie aus
   (config.js); die Seite lädt dann /market statt /finance und keine
   Nachrichten, die Kurskarte nimmt die ganze Breite ein.
   ============================================================================ */

const PRICE_VIEWS = [
    { key: "kurs", label: "Kurs" },
    { key: "bewertung", label: "Mit Bewertung" },
]

const EARNINGS_PERIODS = [
    { key: "annual", label: "Jahr" },
    { key: "quarterly", label: "Quartal" },
]

/* Breites Layout (Raster füllt die Fensterhöhe) ab der Tailwind-Stufe xl. */
const WIDE_QUERY = "(min-width: 1280px)"
const subscribeWide = (onChange) => {
    const mql = window.matchMedia(WIDE_QUERY)
    mql.addEventListener("change", onChange)
    return () => mql.removeEventListener("change", onChange)
}
const isWide = () => window.matchMedia(WIDE_QUERY).matches

function Segmented({ options, value, onChange, label }) {
    return (
        <div className="ds-time-filter" role="group" aria-label={label}>
            {options.map((o) => (
                <button key={o.key} type="button" aria-pressed={value === o.key}
                    className={`ds-time-btn${value === o.key ? " active" : ""}`} onClick={() => onChange(o.key)}>
                    {o.label}
                </button>
            ))}
        </div>
    )
}

function Loading({ height = 160 }) {
    return (
        <div className="flex items-center justify-center gap-2" style={{ height }}>
            <div className="animate-spin rounded-full h-5 w-5 border-2 border-slate-200 border-t-slate-600"></div>
            <p className="m-0 text-slate-600 text-[12px]">Lade Daten…</p>
        </div>
    )
}

export default function StockPage() {
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
    const rangeParam = searchParams.get("range")
    const rangeKey = isPriceRangeKey(rangeParam) ? rangeParam : DEFAULT_PRICE_RANGE
    const earningsPeriod = searchParams.get("periode") === "quartal" ? "quarterly" : "annual"

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

    // Ohne Zusatzkarten weder /finance (Empfehlungen, Umsatz und Gewinn) noch /news:
    // Kurs und Kennzahlen kommen dann aus /market.
    const finance = useCompanyResource(companyId, SHOW_FINANCE_EXTRAS ? "finance" : "market")
    const news = useCompanyResource(SHOW_FINANCE_EXTRAS ? companyId : null, "news")
    const data = finance.data
    const available = Boolean(data?.available)
    const visiblePrices = useMemo(() => pricesInRange(data?.prices, rangeKey), [data, rangeKey])
    const first = visiblePrices[0]
    const last = visiblePrices[visiblePrices.length - 1]
    const change = first && last && first.close ? ((last.close - first.close) / first.close) * 100 : null
    const security = data?.ticker ? `${data.ticker_name ?? data.ticker} · ${data.ticker}` : ""
    const isParent = data?.ticker_scope === PARENT_SCOPE
    const isGroupCompany = data?.ticker_scope === GROUP_COMPANY_SCOPE
    const scopeSuffix = isParent ? " · Kurs der Konzernmutter" : isGroupCompany ? " · Kurs der Konzerngesellschaft" : ""
    const priceView = searchParams.get("ansicht") === "bewertung" ? "bewertung" : "kurs"

    // Kurs und Bewertungsverlauf: Gesamtbewertung der Mitarbeitenden wie auf der Anomalien-Seite.
    const ratings = useAnomalies(available && priceView === "bewertung" ? companyId : null)
    const historyParam = searchParams.get("verlauf")
    const historyKey = isTimeRangeKey(historyParam) ? historyParam : DEFAULT_TIME_RANGE
    const historyRange = useMemo(() => timeWindow(trimToEvaluated(ratings.data?.series).series, historyKey), [ratings.data, historyKey])
    const showPrice = searchParams.get(PRICE_PARAM) !== PRICE_OFF
    const wide = useSyncExternalStore(subscribeWide, isWide, () => false)
    const fill = wide && available
    const openAnomalies = (patch) => {
        const params = new URLSearchParams({ company: companyId, ...patch })
        navigate(`/anomalies?${params}`, { state: { company: { id: companyId, name: companyName } } })
    }

    const selectCompany = (company) => {
        if (!company) return
        const id = String(company.id)
        setNames((n) => ({ ...n, [id]: company.name }))
        setQuery(company.name)
        updateParams({ company: id })
    }
    const backToDashboard = () =>
        navigate("/dashboard", companyId ? { state: { companyId, companyName } } : undefined)

    // Kopfaktionen der Kurskarte: Ansicht, dann Zeitraum (und Kurs an/aus) der Ansicht.
    const priceActions = () => (
        <>
            <Segmented options={PRICE_VIEWS} value={priceView} label="Ansicht"
                onChange={(key) => updateParams({ ansicht: key === "bewertung" ? "bewertung" : null })} />
            {priceView === "kurs" ? (
                <Segmented options={PRICE_RANGES} value={rangeKey} label="Zeitraum"
                    onChange={(key) => updateParams({ range: key === DEFAULT_PRICE_RANGE ? null : key })} />
            ) : (
                <>
                    <TimeRangeFilter value={historyKey}
                        onChange={(key) => updateParams({ verlauf: key === DEFAULT_TIME_RANGE ? null : key })} />
                    <PriceToggle checked={showPrice} onChange={(on) => updateParams({ [PRICE_PARAM]: on ? null : PRICE_OFF })} />
                </>
            )}
        </>
    )
    const priceSubtitle = priceView === "kurs"
        ? `${security} · Monatsschluss in ${data?.currency ?? "?"}${scopeSuffix}`
        : `Mitarbeitende · Gesamtbewertung, Monatsmittel${showPrice ? ` · Kurs ${data?.ticker} rechts in ${data?.currency ?? "?"}` : ""}${
            historyRange ? ` · ${fmtPeriod(historyRange.from)} – ${fmtPeriod(historyRange.to)}` : ""}${scopeSuffix}`
    const priceBody = ({ modal, height }) => (priceView === "kurs" ? (
        <StockPriceChart prices={visiblePrices} currency={data.currency} height={height} />
    ) : (
        <AnomalyChart
            data={ratings.data}
            anomalies={ratings.anomalies}
            loading={ratings.loading}
            error={ratings.error}
            height={modal ? height - 110 : height}
            range={historyRange}
            compact={!modal}
            onSelect={modal ? (id) => openAnomalies({ anomaly: id }) : null}
            onSelectOutlier={modal ? (period) => openAnomalies({ month: period }) : null}
            market={showPrice ? data : null}
            showLegend={modal}
        />
    ))

    const newsCard = (
        <ExpandableCard
            icon={<Newspaper />}
            eyebrow="NACHRICHTEN · GOOGLE NEWS"
            basis="external"
            title="Aktuelle Meldungen"
            subtitle={news.data?.items?.length ? `${news.data.items.length} Meldungen der letzten ${news.data.window_days} Tage` : undefined}
            accent="bg-sky-500"
            className={available ? "xl:row-span-2" : "lg:col-span-2 xl:col-span-2"}
            cardHeight={available ? 380 : 300}
            fill={fill}
        >
            {({ modal, height }) => (news.loading ? <Loading height={160} />
                : news.error ? <EmptyNote height={160}>Nachrichten konnten nicht geladen werden: {news.error}</EmptyNote>
                : modal ? <NewsList news={news.data} />
                : (
                    // Eigener Scrollbereich in Kartenhöhe.
                    <div className="relative" style={{ height }}>
                        <div className="absolute inset-0 overflow-y-auto overscroll-contain">
                            <NewsList news={news.data} showFootnote={false} dense />
                        </div>
                    </div>
                ))}
        </ExpandableCard>
    )

    return (
        <div className="min-h-screen bg-slate-50 flex flex-col">
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
                        <TrendUp />
                    </span>
                    <div className="min-w-0">
                        <p className="m-0 mb-0.5 font-mono text-[10px] tracking-[0.06em] uppercase text-slate-500 leading-none">
                            ANALYSE · AKTIE{security ? ` · ${security}` : ""}
                        </p>
                        <p className="m-0 text-[14px] leading-5 font-semibold tracking-tight text-slate-900 truncate">
                            {companyName ? `Aktie · ${companyName}` : "Aktie"}
                        </p>
                    </div>
                </div>
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

            <div className={`px-5 py-3 max-w-[1600px] w-full mx-auto ${fill ? "flex-none h-[calc(100vh-48px)] min-h-[620px] flex flex-col" : "flex-1"}`}>
                {!companyId ? (
                    <PageSection icon={<Building2 />} eyebrow="AUSWAHL" title="Firma wählen">
                        <p className="m-0 text-[13px] text-slate-500">
                            Oben rechts eine Firma suchen, um {SHOW_FINANCE_EXTRAS ? "Kurs, Empfehlungen und Nachrichten" : "Kurs und Kennzahlen"} zu sehen.
                        </p>
                    </PageSection>
                ) : finance.loading ? (
                    <Loading height={300} />
                ) : finance.error ? (
                    <PageSection icon={<LineChart />} eyebrow="AKTIE" title="Aktienkurs">
                        <EmptyNote height={80}>Kursdaten konnten nicht geladen werden: {finance.error}</EmptyNote>
                    </PageSection>
                ) : (
                    <div className={fill ? "flex-1 min-h-0 flex flex-col gap-3" : "space-y-3"}>
                        {/* Datenstand (Inkrement 6, FA-37) */}
                        <DataStatusBar companyId={companyId} className="flex-none" />
                        {available && <FinanceKpis market={data} first={first} last={last} change={change} extras={SHOW_FINANCE_EXTRAS} />}

                        {/* Mit Zusatzkarten: Kurs (zwei Spalten), Meldungen (zwei Reihen), darunter
                            Empfehlungen und Umsatz/Nettoergebnis; ohne: die Kurskarte über die ganze Fläche. */}
                        <div className={`grid gap-3 lg:grid-cols-2 xl:grid-cols-3 ${!fill ? "" : SHOW_FINANCE_EXTRAS
                            ? "flex-1 min-h-0 grid-rows-[minmax(0,1.25fr)_minmax(0,1fr)]" : "flex-1 min-h-0 grid-rows-[minmax(0,1fr)]"}`}>
                            {available ? (
                                <>
                                    <ExpandableCard
                                        icon={<LineChart />}
                                        eyebrow={priceView === "kurs" ? "KURSVERLAUF · MONATSSCHLUSS" : "KURS UND BEWERTUNGSVERLAUF"}
                                        basis={priceView === "kurs" ? "market" : showPrice ? ["stars", "market"] : "stars"}
                                        title={priceView === "kurs" ? "Aktienkurs" : "Aktienkurs und Sternebewertung"}
                                        subtitle={priceSubtitle}
                                        actions={priceActions}
                                        cardHeight={SHOW_FINANCE_EXTRAS ? 240 : 320}
                                        fill={fill}
                                        className={SHOW_FINANCE_EXTRAS ? "lg:col-span-2" : "lg:col-span-2 xl:col-span-3"}
                                    >
                                        {priceBody}
                                    </ExpandableCard>
                                    {SHOW_FINANCE_EXTRAS && (
                                        <>
                                            {newsCard}
                                            <ExpandableCard
                                                icon={<Users />}
                                                eyebrow="ANALYSTEN · YAHOO FINANCE"
                                                basis="market"
                                                title="Analystenempfehlungen"
                                                subtitle="Empfehlungen je Stufe, letzte vier Monate"
                                                accent="bg-emerald-500"
                                                cardHeight={210}
                                                fill={fill}
                                            >
                                                {({ modal, height }) => <AnalystChart analysts={data.analysts} height={height} compact={!modal} />}
                                            </ExpandableCard>
                                            <ExpandableCard
                                                icon={<BarChart3 />}
                                                eyebrow="ERFOLGSRECHNUNG · YAHOO FINANCE"
                                                basis="market"
                                                title="Umsatz und Nettoergebnis"
                                                subtitle={earningsPeriod === "annual" ? "Je Geschäftsjahr" : "Je Quartal"}
                                                accent="bg-indigo-500"
                                                cardHeight={210}
                                                fill={fill}
                                                actions={() => (
                                                    <Segmented options={EARNINGS_PERIODS} value={earningsPeriod} label="Periode"
                                                        onChange={(key) => updateParams({ periode: key === "quarterly" ? "quartal" : null })} />
                                                )}
                                            >
                                                {({ modal, height }) => <EarningsChart earnings={data.earnings} period={earningsPeriod} height={height} compact={!modal} />}
                                            </ExpandableCard>
                                        </>
                                    )}
                                </>
                            ) : (
                                <>
                                    {/* Ohne Kurs: Hinweis über die ganze Zeile, ab xl neben den Meldungen. */}
                                    <PageSection icon={<LineChart />} eyebrow="AKTIE" basis="market" title="Aktienkurs"
                                        className={SHOW_FINANCE_EXTRAS ? "lg:col-span-2 xl:col-span-1" : "lg:col-span-2 xl:col-span-3"}>
                                        <EmptyNote height={80}>{noPriceText(data?.reason)}</EmptyNote>
                                    </PageSection>
                                    {SHOW_FINANCE_EXTRAS && newsCard}
                                </>
                            )}
                        </div>

                        <MarketSourceNote market={data} companyName={companyName} />
                    </div>
                )}
            </div>
        </div>
    )
}
