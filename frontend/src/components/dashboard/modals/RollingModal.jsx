import ModalShell, { ModalEmpty } from "./ModalShell";
import { TrendUp as TrendUpIcon } from "../../../icons";
import { fmtPeriod } from "@/lib/anomalySeries";
import { rollingSentence } from "@/lib/rollingAverage";

/* ============================================================================
   RollingModal — Detailfenster der Kachel „12- vs. 24-Monats-Schnitt“
   (Inkrement 6, FA-08). Daten: GET /companies/{id}/ratings/trend?mode=rolling
   (bereits im Dashboard geladen, kein eigener Abruf). Zeigt beide Fenster mit
   Zeitraum, Monaten mit Bewertungen, n und Mittel, die Differenz und die
   Regeln (Anker, Datenbasis, kleine Basis). Beschreibt nur die Lage der beiden
   Mittel zueinander; keine Prognose.
   ============================================================================ */

const num = (v, digits = 2) =>
  v == null ? "–" : Number(v).toLocaleString("de-DE", { minimumFractionDigits: digits, maximumFractionDigits: digits })
const signed = (v, digits = 2) => (v == null ? "–" : (v > 0 ? "+" : v < 0 ? "−" : "±") + num(Math.abs(v), digits))
const span = (w) => (w ? `${fmtPeriod(w.from)} – ${fmtPeriod(w.to)}` : "–")

function WindowCard({ label, win, minReviews }) {
  if (!win) return null
  return (
    <div className="flex-1 min-w-[200px] rounded-md border border-slate-200 px-3 py-2.5">
      <p className="m-0 font-mono text-[10px] tracking-[0.06em] uppercase text-slate-500">{label}</p>
      <p className="m-0 mt-0.5 text-[13px] font-semibold text-slate-900">{span(win)}</p>
      <p className="m-0 mt-1 text-[22px] font-semibold tnum text-slate-900 leading-7">{num(win.mean)}</p>
      <p className="m-0 mt-1 text-[12px] text-slate-600 tnum">
        n = {Number(win.n).toLocaleString("de-DE")} Bewertungen · {win.months_with_reviews} von {win.months} Monaten mit Bewertungen
      </p>
      {win.low_basis && (
        <p className="m-0 mt-1 text-[11px] text-slate-600">Kleine Basis: unter {minReviews} Bewertungen im Fenster.</p>
      )}
      {win.covered === false && (
        <p className="m-0 mt-1 text-[11px] text-slate-600">
          Der Datensatz beginnt erst {fmtPeriod(win.covered_from)}; das Fenster ist nicht vollständig abgedeckt.
        </p>
      )}
    </div>
  )
}

export default function RollingModal({ open, onOpenChange, data, companyName = "" }) {
  const minReviews = data?.low_basis_rule?.min_reviews_per_window ?? 10
  return (
    <ModalShell
      open={open}
      onOpenChange={onOpenChange}
      tone="neutral"
      icon={<TrendUpIcon />}
      eyebrow="KENNZAHL · ROLLIERENDE SCHNITTE"
      title="12-Monats-Schnitt vs. 24-Monats-Schnitt"
      subtitle={data?.anchor ? `${companyName ? `${companyName} · ` : ""}bis ${fmtPeriod(data.anchor)} (letzter voller Monat mit Bewertungen)` : "Sternebewertung, Mitarbeitende"}
      size="lg"
    >
      {!data || !data.anchor ? (
        <ModalEmpty>Keine datierten Bewertungen mit Gesamtnote vorhanden.</ModalEmpty>
      ) : (
        <div className="space-y-4">
          <div className="flex flex-wrap gap-3">
            <WindowCard label="12-Monats-Schnitt" win={data.short} minReviews={minReviews} />
            <WindowCard label="24-Monats-Schnitt" win={data.long} minReviews={minReviews} />
            <div className="flex-1 min-w-[160px] rounded-md border border-slate-200 px-3 py-2.5">
              <p className="m-0 font-mono text-[10px] tracking-[0.06em] uppercase text-slate-500">Differenz 12 − 24</p>
              <p className="m-0 mt-1 text-[22px] font-semibold tnum text-slate-900 leading-7">{signed(data.difference)}</p>
              <p className="m-0 mt-1 text-[12px] text-slate-600">{rollingSentence(data)}</p>
            </div>
          </div>

          {data.insufficient_history && (
            <p className="m-0 text-[12px] text-slate-600 rounded-md border border-slate-300 bg-slate-50 px-3 py-2">
              <span className="font-medium text-slate-800">Weniger als 24 Monate Daten.</span> Der Datensatz reicht bis zum Anker{" "}
              {data.history_months} {data.history_months === 1 ? "Monat" : "Monate"} zurück (ab {fmtPeriod(data.first_month)}); die
              Mittel beruhen auf den vorhandenen Monaten.
            </p>
          )}

          <div className="text-[12px] text-slate-600 leading-5 space-y-1.5">
            <p className="m-0">
              <span className="font-medium text-slate-800">Datenbasis:</span> Sternebewertung, Gesamtnote je Bewertung
              (Spalte „durchschnittsbewertung“) der Mitarbeitenden, wie im Monatsverlauf der Anomalien (E3). Das Fenster mittelt
              alle Bewertungen seiner Kalendermonate; ein Monat mit vielen Bewertungen wiegt mehr als ein Monat mit wenigen.
            </p>
            <p className="m-0">
              <span className="font-medium text-slate-800">Anker:</span> {data.anchor_rule}. Hier {fmtPeriod(data.anchor)}; das
              24-Monats-Fenster enthält die 12 Monate des kürzeren Fensters.
            </p>
            <p className="m-0">
              <span className="font-medium text-slate-800">Kleine Basis:</span> ein Fenster mit weniger als {minReviews} Bewertungen
              (vorläufig dieselbe Schwelle wie bei den Vergleichsfenstern, E12).
            </p>
            <p className="m-0 text-slate-500">
              Die Differenz beschreibt die Lage der beiden Mittel zueinander im Datensatz; sie ist keine Prognose und keine Aussage
              über Ursachen.
            </p>
          </div>
        </div>
      )}
    </ModalShell>
  )
}
