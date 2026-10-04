import { useEffect, useMemo, useState } from "react"
import { useLocation, useNavigate, useSearchParams } from "react-router-dom"
import { ArrowLeft, BarChart3, Building2, LineChart, Newspaper, Users } from "lucide-react"
import { Anomaly as AnomalyIcon, TrendUp } from "../icons"
import { CompanySearchSelect } from "@/components/CompanySearchSelect"
import { PageSection } from "@/components/dashboard/PageSection"
import { MarketContext, PriceToggle } from "@/components/dashboard/MarketContext"
import { AnomalyChart, TimeRangeFilter } from "@/components/dashboard/AnomalyCard"
import { AnalystChart, EarningsChart, EmptyNote, NewsList, StockPriceChart } from "@/components/dashboard/FinanceCards"
import { useAnomalies } from "@/hooks/useAnomalies"
import { useCompanyResource } from "@/hooks/useCompanyResource"
import { useTheme } from "@/hooks/useTheme"
import { DEFAULT_TIME_RANGE, fmtPeriod, isTimeRangeKey, timeWindow, trimToEvaluated } from "@/lib/anomalySeries"
import {
    DEFAULT_PRICE_RANGE, MARKET_DISCLAIMER_LEAD, MARKET_DISCLAIMER_TEXT, PARENT_SCOPE, PRICE_OFF, PRICE_PARAM, PRICE_RANGES, fmtMonth, fmtPercent, fmtPrice, isPriceRangeKey, noPriceText, pricesInRange,
} from "@/lib/market"
import { API_URL } from "../config"

/* ============================================================================
   Stock — Aktien-Dashboard (/aktie, Inkrement 3, E16).
   Kursverlauf, Analystenempfehlungen, Umsatz und Nettoergebnis sowie aktuelle
   Nachrichten eines Unternehmens auf einer eigenen Seite. Firma, Zeitfenster
   und Jahres- oder Quartalsansicht stehen in der URL
   (?company=19&range=3y&periode=quartal). Der Bereich "Kurs und
   Bewertungsverlauf" legt den Kurs auf einer zweiten Achse über den
   Monatsverlauf der Sternebewertung (Mitarbeitende, Gesamtbewertung) mit den
   auffälligen Veränderungen; Zeitraum ?verlauf=5y|3y|1y, Kurs aus mit ?kurs=aus.
   Ein Klick auf eine Markierung öffnet sie auf der Anomalien-Seite. Alles ist Einordnung des
   Marktumfelds; ein Zusammenhang mit den Bewertungen wird nicht behauptet.
   ============================================================================ */

const EARNINGS_PERIODS = [
    { key: "annual", label: "Jährlich" },
    { key: "quarterly", label: "Quartalsweise" },
]

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

    // Namen nachladen, wenn die Seite direkt über die URL geöffnet wurde.
    useEffect(() => {
        if (!companyId || names[companyId]) return undefined
        const controller = new AbortController()
        fetch(`${API_URL}/companies`, { signal: controller.signal })
            .then((res) => (res.ok ? res.json() : []))
            .then((list) => {
                const co = Array.isArray(list) ? list.find((c) => String(c.id) === companyId) : null
                if (co) {
                    setNames((n) => ({ ...n, [companyId]: co.name?.trim() ?? "" }))
                    setQuery(co.name?.trim() ?? "")
                }
            })
            .catch(() => {})
        return () => controller.abort()
    }, [companyId, names])

    const finance = useCompanyResource(companyId, "finance")
    const news = useCompanyResource(companyId, "news")
    const data = finance.data
    const available = Boolean(data?.available)
    const visiblePrices = useMemo(() => pricesInRange(data?.prices, rangeKey), [data, rangeKey])
    const first = visiblePrices[0]
    const last = visiblePrices[visiblePrices.length - 1]
    const change = first && last && first.close ? ((last.close - first.close) / first.close) * 100 : null
    const security = data?.ticker ? `${data.ticker_name ?? data.ticker} · ${data.ticker}` : ""
    const isParent = data?.ticker_scope === PARENT_SCOPE

    // Kurs und Bewertungsverlauf: Gesamtbewertung der Mitarbeitenden wie auf der Anomalien-Seite.
    const ratings = useAnomalies(available ? companyId : null)
    const historyParam = searchParams.get("verlauf")
    const historyKey = isTimeRangeKey(historyParam) ? historyParam : DEFAULT_TIME_RANGE
    const historyRange = useMemo(() => timeWindow(trimToEvaluated(ratings.data?.series).series, historyKey), [ratings.data, historyKey])
    const showPrice = searchParams.get(PRICE_PARAM) !== PRICE_OFF
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
                            ANALYSE · AKTIE
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

            <div className="flex-1 px-5 py-5 max-w-[1400px] w-full mx-auto space-y-4">
                {!companyId ? (
                    <PageSection icon={<Building2 />} eyebrow="AUSWAHL" title="Firma wählen">
                        <p className="m-0 text-[13px] text-slate-500">Oben rechts eine Firma suchen, um Kurs, Empfehlungen und Nachrichten zu sehen.</p>
                    </PageSection>
                ) : (
                    <>
                        <PageSection
                            icon={<LineChart />}
                            eyebrow="KURSVERLAUF · MONATSSCHLUSS"
                            title={available ? `Aktienkurs · ${security}` : "Aktienkurs"}
                            subtitle={available && last
                                ? `${fmtPrice(last.close)} ${data.currency ?? ""} Ende ${fmtMonth(last.period)} · ${fmtPercent(change)} seit ${fmtMonth(first.period)}${isParent ? " · Kurs der Konzernmutter" : ""}`
                                : undefined}
                            actions={available && (
                                <Segmented options={PRICE_RANGES} value={rangeKey} label="Zeitraum"
                                    onChange={(key) => updateParams({ range: key === DEFAULT_PRICE_RANGE ? null : key })} />
                            )}
                        >
                            {finance.loading ? <Loading height={300} />
                                : finance.error ? <EmptyNote height={120}>Kursdaten konnten nicht geladen werden: {finance.error}</EmptyNote>
                                : !available ? <EmptyNote height={80}>{noPriceText(data?.reason)}</EmptyNote>
                                : <StockPriceChart prices={visiblePrices} currency={data.currency} />}
                            {available && (
                                <div className="mt-4 pt-3 border-t border-slate-100">
                                    <MarketContext market={data} companyName={companyName} />
                                </div>
                            )}
                        </PageSection>

                        {available && (
                            <PageSection
                                icon={<AnomalyIcon />}
                                eyebrow="KURS UND BEWERTUNGSVERLAUF"
                                title="Aktienkurs und Sternebewertung"
                                subtitle={`Mitarbeitende · Gesamtbewertung, Monatsmittel${showPrice ? ` · Kurs ${data.ticker} rechts in ${data.currency ?? "?"}` : ""}${
                                    historyRange ? ` · ${fmtPeriod(historyRange.from)} – ${fmtPeriod(historyRange.to)}` : ""}`}
                                actions={
                                    <>
                                        <PriceToggle checked={showPrice} onChange={(on) => updateParams({ [PRICE_PARAM]: on ? null : PRICE_OFF })} />
                                        <TimeRangeFilter value={historyKey}
                                            onChange={(key) => updateParams({ verlauf: key === DEFAULT_TIME_RANGE ? null : key })} />
                                    </>
                                }
                            >
                                <AnomalyChart
                                    data={ratings.data}
                                    anomalies={ratings.anomalies}
                                    loading={ratings.loading}
                                    error={ratings.error}
                                    height={340}
                                    range={historyRange}
                                    onSelect={(id) => openAnomalies({ anomaly: id })}
                                    onSelectOutlier={(period) => openAnomalies({ month: period })}
                                    market={showPrice ? data : null}
                                />
                                <p className="m-0 mt-3 pt-3 border-t border-slate-100 text-[11px] text-slate-500 leading-4">
                                    <span className="font-medium text-slate-700">{MARKET_DISCLAIMER_LEAD}</span> {MARKET_DISCLAIMER_TEXT}{" "}
                                    Beide Linien stehen nur nebeneinander; es wird nichts verrechnet. Eine Markierung anklicken öffnet die
                                    Veränderung mit Vergleich und Bewertungen auf der Anomalien-Seite.
                                </p>
                            </PageSection>
                        )}

                        {available && (
                            <div className="grid gap-4 lg:grid-cols-2">
                                <PageSection
                                    icon={<Users />}
                                    eyebrow="ANALYSTEN · YAHOO FINANCE"
                                    title="Analystenempfehlungen"
                                    subtitle="Zahl der Empfehlungen je Stufe, letzte vier Monate"
                                >
                                    <AnalystChart analysts={data.analysts} />
                                </PageSection>
                                <PageSection
                                    icon={<BarChart3 />}
                                    eyebrow="ERFOLGSRECHNUNG · YAHOO FINANCE"
                                    title="Umsatz und Nettoergebnis"
                                    subtitle={earningsPeriod === "annual" ? "Je Geschäftsjahr" : "Je Quartal"}
                                    actions={
                                        <Segmented options={EARNINGS_PERIODS} value={earningsPeriod} label="Periode"
                                            onChange={(key) => updateParams({ periode: key === "quarterly" ? "quartal" : null })} />
                                    }
                                >
                                    <EarningsChart earnings={data.earnings} period={earningsPeriod} />
                                </PageSection>
                            </div>
                        )}

                        <PageSection
                            icon={<Newspaper />}
                            eyebrow="NACHRICHTEN · GOOGLE NEWS"
                            title="Aktuelle Meldungen"
                            subtitle={news.data?.items?.length
                                ? `${news.data.items.length} Meldungen der letzten ${news.data.window_days} Tage, neueste zuerst`
                                : undefined}
                        >
                            {news.loading ? <Loading height={100} />
                                : news.error ? <EmptyNote height={100}>Nachrichten konnten nicht geladen werden: {news.error}</EmptyNote>
                                : <NewsList news={news.data} />}
                        </PageSection>
                    </>
                )}
            </div>
        </div>
    )
}
