import { useEffect, useMemo, useState } from "react"
import { useLocation, useNavigate, useSearchParams } from "react-router-dom"
import { Activity, ArrowLeft, Building2, ListOrdered } from "lucide-react"
import { CompanySearchSelect } from "@/components/CompanySearchSelect"
import { AnomalyChart, AnomalyList, DimensionPicker, TimeRangeFilter } from "@/components/dashboard/AnomalyCard"
import { DEFAULT_TIME_RANGE, fmtPeriod, inWindow, isTimeRangeKey, timeWindow } from "@/lib/anomalySeries"
import { EMPLOYEE_DIMENSIONS, OVERALL_DIMENSION, dimensionLabel } from "@/lib/ratingCategories"
import { useAnomalies } from "@/hooks/useAnomalies"
import { useTheme } from "@/hooks/useTheme"
import { API_URL } from "../config"

/* ============================================================================
   Anomalies — Detailseite "Anomalien im Verlauf" (Inkrement 1).
   Geöffnet per Klick auf die AnomalyCard im Dashboard, analog zum Vergleich.
   Die Firma steht in der URL (?company=ID), damit Neuladen und Teilen
   funktionieren; der Name kommt aus dem Navigationszustand oder /companies.
   Dimension und Zeitraum stehen ebenfalls in der URL (?dimension=key&range=1y).
   Der Zeitraum wählt nur den Ausschnitt; erkannt wird auf der ganzen Reihe.
   ============================================================================ */

// Quelle fest auf Mitarbeitende; die Quellenauswahl folgt in Inkrement 2.
const SOURCE = "employee"

function Section({ icon, eyebrow, title, subtitle, actions, children }) {
    return (
        <section className="bg-white border border-slate-200 rounded-lg overflow-hidden shadow-xs">
            <div className="px-4 pt-3 pb-3 border-b border-slate-200 flex items-start gap-2.5">
                <span className="w-7 h-7 rounded-md grid place-items-center flex-none bg-slate-100 text-slate-600 mt-0.5 [&_svg]:w-[14px] [&_svg]:h-[14px]">
                    {icon}
                </span>
                <div className="min-w-0 flex-1">
                    <p className="m-0 mb-0.5 font-mono text-[10px] tracking-[0.06em] uppercase text-slate-500 leading-none">{eyebrow}</p>
                    <h2 className="m-0 text-[14px] leading-5 font-semibold tracking-tight text-slate-900">{title}</h2>
                    {subtitle && <p className="m-0 mt-0.5 text-[11px] text-slate-500 leading-4">{subtitle}</p>}
                </div>
                {actions && <div className="flex-none flex items-center gap-2">{actions}</div>}
            </div>
            <div className="px-4 py-4">{children}</div>
        </section>
    )
}

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
    const dimensionParam = searchParams.get("dimension")
    const dimension = EMPLOYEE_DIMENSIONS.some((d) => d.key === dimensionParam) ? dimensionParam : OVERALL_DIMENSION.key
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

    const { data, anomalies, loading, error } = useAnomalies(companyId, { source: SOURCE, dimension })
    const eligibility = data?.eligibility
    const count = anomalies.length
    // Sichtbares Fenster relativ zum letzten Monat der Reihe (null = ganze Reihe).
    const range = useMemo(() => timeWindow(data?.series ?? [], rangeKey), [data, rangeKey])
    const visibleAnomalies = useMemo(() => anomalies.filter((a) => inWindow(a.date, range)), [anomalies, range])
    const hiddenCount = count - visibleAnomalies.length
    const countText = `${count} ${count === 1 ? "auffällige Veränderung" : "auffällige Veränderungen"}`
    const chartSubtitle = eligibility && !eligibility.eligible
        ? "Mitarbeiter · keine automatische Erkennung"
        : range
            ? `Mitarbeiter · ${fmtPeriod(range.from)} – ${fmtPeriod(range.to)} · ${count
                ? `${visibleAnomalies.length} von ${count} ${count === 1 ? "auffälligen Veränderung" : "auffälligen Veränderungen"} im Zeitraum`
                : "keine auffälligen Veränderungen"}`
            : `Mitarbeiter · ${countText}`

    // Zurück mit der gewählten Firma, damit das Dashboard sie wieder anzeigt.
    const backToDashboard = () =>
        navigate("/dashboard", companyId ? { state: { companyId, companyName } } : undefined)

    const selectCompany = (company) => {
        if (!company) return
        const id = String(company.id)
        setNames((n) => ({ ...n, [id]: company.name }))
        setQuery(company.name)
        updateParams({ company: id })
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
                        <Activity />
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
                    <DimensionPicker
                        value={dimension}
                        onChange={(key) => updateParams({ dimension: key === OVERALL_DIMENSION.key ? null : key })}
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
                    <Section icon={<Building2 />} eyebrow="AUSWAHL" title="Firma wählen">
                        <p className="m-0 text-[13px] text-slate-500">Oben rechts eine Firma suchen, um ihren Verlauf zu sehen.</p>
                    </Section>
                ) : (
                    <>
                        <Section
                            icon={<Activity />}
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
                            <AnomalyChart data={data} anomalies={anomalies} loading={loading} error={error} height={380} range={range} />
                        </Section>

                        <Section
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
                        </Section>
                    </>
                )}
            </div>
        </div>
    )
}
