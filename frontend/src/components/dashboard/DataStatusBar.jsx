import { useState } from "react"
import { ChevronDown, ChevronRight, Database } from "lucide-react"
import { useDataStatus } from "@/hooks/useDataStatus"
import { evidenceText, lastImportText, marketText, platformText, sourceLine, summaryText, timestampCell } from "@/lib/dataStatusText"

/* ============================================================================
   DataStatusBar — Datenstand und Abdeckung (Inkrement 6, FA-37).
   Eine Leiste auf Dashboard, Anomalien und Aktie: je Quelle Anzahl der
   Bewertungen im Datensatz, Zeitraum (erste bis jüngste Bewertung), bewertete
   Monate und Eignung (E4), dazu der letzte Import in die Datenbank (das
   Abrufdatum bei Kununu ist nicht gespeichert), der Stand des
   Kurs-Zwischenspeichers (E15) und des Belegspeichers (E18) und der Vergleich
   mit der Plattform aus der Metadatei (nur vom Autor gefüllt, sonst „nicht
   hinterlegt“). Standardmäßig zugeklappt: eine Kurzzeile (Bewertungen je
   Quelle, jüngste Bewertung); „Datengrundlage“ klappt alle Angaben
   auf, darin aufklappbar die Zeitstempel je Feld mit ihrer Bedeutung.
   Daten: GET /companies/{id}/data-status (useDataStatus). Nur Beschreibung.
   Die Texte stehen in lib/dataStatusText.js; der PDF-Export nutzt dieselben.
   ============================================================================ */

function Item({ label, children, title }) {
  return (
    <span className="inline-flex items-baseline gap-1 min-w-0" title={title}>
      <span className="font-medium text-slate-700 flex-none">{label}:</span>
      <span className="text-slate-600 min-w-0">{children}</span>
    </span>
  )
}

function TimestampTable({ data }) {
  const fields = Object.entries(data.timestamp_fields ?? {})
  const sources = Object.entries(data.sources ?? {})
  return (
    <div className="overflow-x-auto">
      <table className="text-[11px] border-collapse min-w-[520px]">
        <thead>
          <tr className="text-left text-[10px] uppercase tracking-wider text-slate-500">
            <th className="font-medium py-1 pr-3">Feld</th>
            <th className="font-medium py-1 pr-3">Bedeutung</th>
            {sources.map(([key, s]) => (
              <th key={key} className="font-medium py-1 pr-3">{s.label}: ältester – jüngster</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {fields.map(([field, meaning]) => (
            <tr key={field} className="border-t border-slate-100 text-slate-700 align-top">
              <td className="py-1 pr-3 font-mono">{field}</td>
              <td className="py-1 pr-3 max-w-[320px]">{meaning}</td>
              {sources.map(([key, s]) => {
                const t = s.timestamps?.[field]
                return (
                  <td key={key} className="py-1 pr-3 tnum whitespace-nowrap">
                    {timestampCell(t)}
                  </td>
                )
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

/* companyId: Firma. Zugeklappt eine Kurzzeile (summaryText); aufgeklappt alle
   Angaben je Quelle und darunter die aufklappbare Zeitstempel-Tabelle. */
export function DataStatusBar({ companyId, className = "" }) {
  const { loading, error, data } = useDataStatus(companyId)
  const [expanded, setExpanded] = useState(false)
  const [open, setOpen] = useState(false)
  if (!companyId) return null
  const emp = data?.sources?.employee
  const cand = data?.sources?.candidates
  const market = data?.market_cache
  const evidence = data?.evidence_store
  const platform = data?.platform
  const thresholds = data?.thresholds ?? { min_reviews_per_month: 5, min_evaluated_months: 12 }
  return (
    <section
      className={`bg-white border border-slate-200 rounded-lg shadow-xs px-4 py-1.5 text-[11px] leading-4 ${className}`}
      aria-label="Datenstand"
    >
      <button
        type="button"
        className="w-full flex items-center gap-3 text-left group"
        onClick={() => setExpanded((v) => !v)}
        aria-expanded={expanded}
        disabled={!data}
      >
        <span className="inline-flex items-center gap-1.5 font-mono text-[10px] tracking-[0.06em] uppercase text-slate-500 flex-none">
          <Database className="w-3 h-3" aria-hidden="true" />
          Datenstand
        </span>
        <span className="text-slate-600 min-w-0 truncate">
          {loading
            ? "Lade Datenstand…"
            : error
              ? `Datenstand konnte nicht geladen werden: ${error}`
              : data ? summaryText(data) : null}
        </span>
        {data && (
          <span className="inline-flex items-center gap-1 text-slate-500 group-hover:text-slate-800 ml-auto flex-none">
            {expanded ? <ChevronDown className="w-3 h-3" aria-hidden="true" /> : <ChevronRight className="w-3 h-3" aria-hidden="true" />}
            {expanded ? "Ausblenden" : "Datengrundlage"}
          </span>
        )}
      </button>
      {expanded && data && (
        <div className="mt-1.5 pt-1.5 pb-0.5 border-t border-slate-100 space-y-1">
          <div className="flex flex-col gap-y-1">
            <Item label="Mitarbeitende" title={`Sternebewertung und Freitexte der Mitarbeitenden; bewertet = Monat mit mindestens ${thresholds.min_reviews_per_month} Bewertungen (E4), geeignet = mindestens ${thresholds.min_evaluated_months} bewertete Monate`}>
              {sourceLine(emp)}
            </Item>
            <Item label="Bewerbende" title="Sternebewertung und Freitexte der Bewerbenden">
              {sourceLine(cand)}
            </Item>
            <Item label="Letzter Import" title={data.last_import?.meaning ?? ""}>
              {lastImportText(data)}
            </Item>
            <Item label="Plattform" title="Anzahl der Bewertungen auf Kununu zum Stichtag, vom Autor in backend/data/company_metadata.json hinterlegt; kein Abruf">
              {platformText(platform)}
            </Item>
            {market !== undefined && (
              <Item label="Kurs" title="Zwischenspeicher der Monatsschlusskurse (E15); Abruf = fetched_at der Datei">
                {marketText(market)}
              </Item>
            )}
            {evidence !== undefined && (
              <Item label="Belege" title="Belegspeicher der externen Meldungen je Monat (E18); Abruf = jüngstes fetched_at">
                {evidenceText(evidence)}
              </Item>
            )}
          </div>
          <button
            type="button"
            className="inline-flex items-center gap-1 text-slate-500 hover:text-slate-800 underline-offset-2 hover:underline"
            onClick={() => setOpen((v) => !v)}
            aria-expanded={open}
          >
            {open ? <ChevronDown className="w-3 h-3" aria-hidden="true" /> : <ChevronRight className="w-3 h-3" aria-hidden="true" />}
            Zeitstempel
          </button>
          {open && (
            <div className="pt-1 space-y-1.5">
              <TimestampTable data={data} />
              <p className="m-0 text-slate-500">{data.note}</p>
            </div>
          )}
        </div>
      )}
    </section>
  )
}
