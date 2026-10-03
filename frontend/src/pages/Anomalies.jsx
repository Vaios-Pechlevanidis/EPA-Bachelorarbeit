import { useEffect, useState } from "react"
import { useLocation, useNavigate, useSearchParams } from "react-router-dom"
import { Activity, ArrowLeft, Building2, ListOrdered } from "lucide-react"
import { CompanySearchSelect } from "@/components/CompanySearchSelect"
import { AnomalyChart, AnomalyList } from "@/components/dashboard/AnomalyCard"
import { useAnomalies } from "@/hooks/useAnomalies"
import { useTheme } from "@/hooks/useTheme"
import { API_URL } from "../config"

/* ============================================================================
   Anomalies — Detailseite "Anomalien im Verlauf" (Inkrement 1).
   Geöffnet per Klick auf die AnomalyCard im Dashboard, analog zum Vergleich.
   Die Firma steht in der URL (?company=ID), damit Neuladen und Teilen
   funktionieren; der Name kommt aus dem Navigationszustand oder /companies.
   ============================================================================ */

const SOURCE = "employee"
const DIMENSION = "durchschnittsbewertung"

function Section({ icon, eyebrow, title, subtitle, children }) {
    return (
        <section className="bg-white border border-slate-200 rounded-lg overflow-hidden shadow-xs">
            <div className="px-4 pt-3 pb-3 border-b border-slate-200 flex items-start gap-2.5">
                <span className="w-7 h-7 rounded-md grid place-items-center flex-none bg-slate-100 text-slate-600 mt-0.5 [&_svg]:w-[14px] [&_svg]:h-[14px]">
                    {icon}
                </span>
                <div className="min-w-0">
                    <p className="m-0 mb-0.5 font-mono text-[10px] tracking-[0.06em] uppercase text-slate-500 leading-none">{eyebrow}</p>
                    <h2 className="m-0 text-[14px] leading-5 font-semibold tracking-tight text-slate-900">{title}</h2>
                    {subtitle && <p className="m-0 mt-0.5 text-[11px] text-slate-500 leading-4">{subtitle}</p>}
                </div>
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

    // Firma aus dem Navigationszustand in die URL übernehmen (Neuladen, Teilen).
    useEffect(() => {
        if (companyId && !searchParams.get("company")) setSearchParams({ company: companyId }, { replace: true })
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

    const { data, anomalies, loading, error } = useAnomalies(companyId, { source: SOURCE, dimension: DIMENSION })
    const eligibility = data?.eligibility
    const count = anomalies.length

    // Zurück mit der gewählten Firma, damit das Dashboard sie wieder anzeigt.
    const backToDashboard = () =>
        navigate("/dashboard", companyId ? { state: { companyId, companyName } } : undefined)

    const selectCompany = (company) => {
        if (!company) return
        const id = String(company.id)
        setNames((n) => ({ ...n, [id]: company.name }))
        setQuery(company.name)
        setSearchParams({ company: id })
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
                            title="Monatsverlauf der Gesamtbewertung"
                            subtitle={`Mitarbeiter · ${count} ${count === 1 ? "auffällige Veränderung" : "auffällige Veränderungen"}`}
                        >
                            <AnomalyChart data={data} anomalies={anomalies} loading={loading} error={error} height={380} />
                            {eligibility && !eligibility.eligible && (
                                <p className="m-0 mt-3 text-[12px] text-slate-500">
                                    Keine automatische Erkennung: {eligibility.reason}
                                </p>
                            )}
                        </Section>

                        <Section
                            icon={<ListOrdered />}
                            eyebrow="LISTE"
                            title="Auffällige Veränderungen"
                            subtitle="Abfälle zuerst, innerhalb nach Größe der Veränderung"
                        >
                            {!loading && !error && <AnomalyList anomalies={anomalies} />}
                        </Section>
                    </>
                )}
            </div>
        </div>
    )
}
