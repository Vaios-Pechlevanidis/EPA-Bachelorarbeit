import { CircleHelp } from "lucide-react"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import { fmtDe, fmtMonthKey, fmtSigned } from "@/lib/forecastText"

/* ============================================================================
   ForecastExplanation — „?“ an der Prognose im Detailfenster des Zeitverlaufs
   (2026-10-13). Erklärt mit den Kenngrößen aus GET …/timeline (forecast_info,
   backend/routes/analytics.py → forecast_with_details), wie die Prognose
   entsteht: Holts exponentielle Glättung mit Trend (Holt 1957), geschätzte
   Gewichte α und β, geglättetes Niveau und Steigung am Ende der Reihe.
   Seit 2026-10-17 (Prüfung, docs/feature-doku/16-report-qualitaet.md) zusätzlich:
   Datenstand (Monate seit dem letzten Datenmonat), Backtest mit rollierendem
   Ursprung gegen einfache Vergleichsverfahren (MAE), Bandbreite (80 %) aus den
   Backtest-Fehlern und Monate mit weniger als 5 Bewertungen.
   ============================================================================ */

const METHOD_LABELS = {
  holt: "Holt (diese Prognose)",
  naive: "letzter Wert",
  mean: "Mittel aller Monate",
  ma6: "Mittel der letzten 6 Monate",
  snaive12: "Wert 12 Monate zuvor",
}

/* Backtest-Zeilen: MAE je Verfahren, bestes zuerst; null ohne Backtest. */
function backtestRows(backtest) {
  if (!backtest?.methods) return null
  return Object.entries(backtest.methods)
    .filter(([, m]) => m?.mae != null)
    .sort((a, b) => a[1].mae - b[1].mae)
    .map(([key, m]) => ({ key, label: METHOD_LABELS[key] ?? key, mae: m.mae }))
}

function Row({ title, children }) {
  return (
    <div>
      <p className="m-0 font-semibold text-slate-800">{title}</p>
      <div className="m-0 text-slate-600">{children}</div>
    </div>
  )
}

/* info: forecast_info; sourceLabel: „Mitarbeiter“ oder „Bewerber“; lastCount: Bewertungen im letzten Monat */
export function ForecastExplanation({ info, sourceLabel, lastCount = null }) {
  if (!info) return null
  const holt = info.method === "holt"
  return (
    <Popover>
      <PopoverTrigger asChild>
        <button
          type="button"
          className="inline-flex items-center justify-center w-4 h-4 rounded-full text-slate-400 hover:text-slate-700 focus-visible:outline focus-visible:outline-2 focus-visible:outline-blue-500"
          aria-label="Wie entsteht die Prognose?"
          title="Wie entsteht die Prognose?"
          onClick={(e) => e.stopPropagation()}
        >
          <CircleHelp className="w-4 h-4" aria-hidden="true" />
        </button>
      </PopoverTrigger>
      <PopoverContent
        side="top"
        align="center"
        collisionPadding={12}
        className="w-[380px] max-w-[calc(100vw-32px)] max-h-[var(--radix-popover-content-available-height)] overflow-y-auto bg-white text-slate-700 border-slate-200 p-4 text-[12px] leading-[17px] space-y-2.5"
        onClick={(e) => e.stopPropagation()}
      >
        <p className="m-0 text-[13px] font-semibold text-slate-900">So entsteht die Prognose</p>

        <Row title="Grundlage">
          Monatsmittel der Gesamtnote ({sourceLabel}), {info.n_months} Monate mit Bewertungen von{" "}
          {fmtMonthKey(info.first_month)} bis {fmtMonthKey(info.last_month)} (höchstens die letzten
          10 Jahre). Monate ohne Bewertungen werden übersprungen.
        </Row>

        {holt ? (
          <>
            <Row title="Verfahren">
              Holts exponentielle Glättung mit Trend (Charles C. Holt, 1957; berechnet mit statsmodels).
              Sie führt zwei Werte Monat für Monat fort: ein <b>geglättetes Niveau</b>, also einen
              gewichteten Durchschnitt, in dem jüngere Monate stärker zählen (violette Linie), und eine{" "}
              <b>geglättete Steigung</b> je Monat.
            </Row>
            <Row title="Gewichte (aus den Daten geschätzt)">
              α = {fmtDe(info.alpha)} für das Niveau, β = {fmtDe(info.beta)} für die Steigung. Je näher α
              an 1, desto stärker folgt das Niveau dem jeweils letzten Monat; nahe 0 entspricht es dem
              langen Durchschnitt.
            </Row>
            <Row title="Rechnung">
              Prognose für Monat h = Niveau am Ende ({fmtDe(info.level)}) + h × Steigung (
              {fmtSigned(info.trend)} je Monat){info.clamped ? ", begrenzt auf 0 bis 5" : ""}.
            </Row>
            <Row title={`Warum nicht Ø Historisch (${fmtDe(info.historical_mean)})?`}>
              Der historische Durchschnitt zählt alle Monate gleich. Die Prognose startet beim geglätteten
              Niveau der jüngsten Monate; einzelne Ausreißer
              {lastCount != null ? ` wie der letzte Monat (${lastCount} ${lastCount === 1 ? "Bewertung" : "Bewertungen"})` : ""}{" "}
              gehen nur abgeschwächt ein.
            </Row>
          </>
        ) : (
          <Row title="Verfahren">
            Die Glättung ließ sich für diese Reihe nicht schätzen. Die Prognose ist deshalb der Mittelwert
            aller Monate ({fmtDe(info.historical_mean)}).
          </Row>
        )}

        <Row title="Datenstand">
          Letzter Datenmonat {fmtMonthKey(info.last_month)}; die Prognose beginnt dort, nicht beim heutigen Datum
          {info.months_since_last_data != null && info.months_since_last_data > 0
            ? ` (${info.months_since_last_data} ${info.months_since_last_data === 1 ? "Monat" : "Monate"} vor heute, keine neueren Bewertungen im Datensatz)`
            : ""}.
          {info.months_below_min_reviews > 0 && (
            <> {info.months_below_min_reviews} der {info.n_months} Monate haben weniger als {info.min_reviews_per_month ?? 5} Bewertungen; sie zählen hier voll mit, anders als in der Erkennung auffälliger Veränderungen.</>
          )}
        </Row>

        {backtestRows(info.backtest) ? (
          <Row title={`Prüfung: Backtest mit rollierendem Ursprung (${info.backtest.origins} Ursprünge, ${info.backtest.horizon} Monate voraus)`}>
            Mittlerer absoluter Fehler (MAE) in Sternen, nur mit Daten vor dem jeweiligen Ursprung:
            <ul className="m-0 mt-1 pl-4 list-disc">
              {backtestRows(info.backtest).map((r) => (
                <li key={r.key} className={r.key === "holt" ? "font-semibold" : ""}>
                  {r.label}: {fmtDe(r.mae)}
                </li>
              ))}
            </ul>
            {info.backtest.best_method && info.backtest.best_method !== "holt" && (
              <span className="block mt-1 text-amber-700">
                Auf dieser Reihe war ein einfacheres Verfahren ({METHOD_LABELS[info.backtest.best_method] ?? info.backtest.best_method}) genauer als diese Prognose.
              </span>
            )}
          </Row>
        ) : (
          <Row title="Prüfung">Für einen Backtest ist die Reihe zu kurz (mindestens 25 Monate).</Row>
        )}

        <Row title="Bandbreite">
          {info.interval?.available
            ? "Die helle Fläche um die Prognose ist die Bandbreite (80 %): In 80 % der Backtest-Fälle lag der tatsächliche Monatswert so nah an der Prognose. Sie folgt aus den Fehlern dieser Reihe, nicht aus einer Verteilungsannahme."
            : "Für eine Bandbreite liegen zu wenige Backtest-Fehler vor."}
        </Row>

        <Row title="Grenzen">
          Die Prognose schreibt die bisherige Entwicklung fort; sie kennt keine Ursachen. Holt setzt gleich
          lange Abstände voraus, übersprungene Monate verletzen das. Die Werte sind auf eine Nachkommastelle zu
          lesen; der Backtest zeigt, wie genau sie in der Vergangenheit waren.
        </Row>
      </PopoverContent>
    </Popover>
  )
}
