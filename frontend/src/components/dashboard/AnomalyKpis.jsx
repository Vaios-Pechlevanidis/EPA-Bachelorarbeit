import { KpiTile } from "./KpiTile"
import { fmtPeriod, seriesKpis } from "@/lib/anomalySeries"

/* ============================================================================
   AnomalyKpis — Kennzahlenleiste der Detailseite "Anomalien im Verlauf",
   im Stil des Aktien-Dashboards. Alle Werte gelten für die gewählte
   Bewertendengruppe und Dimension; Grundlage ist die Monatsreihe (E3, E4)
   und die Erkennung (E9, E14) der ganzen Reihe, unabhängig vom Zeitfilter.
   ============================================================================ */

const FALL = "var(--anomaly-fall)"
const RISE = "var(--anomaly-rise)"

const num = (v, digits = 2) =>
    v == null ? "–" : Number(v).toLocaleString("de-DE", { minimumFractionDigits: digits, maximumFractionDigits: digits })
const signed = (v) => (v == null ? "–" : `${v > 0 ? "+" : v < 0 ? "−" : "±"}${num(Math.abs(v))}`)
// Farbe erst ab 0,1 Sternen; kleinere Unterschiede sind Rauschen und bleiben neutral.
const toneOf = (v) => (v == null || Math.abs(v) < 0.1 ? undefined : v < 0 ? FALL : RISE)

export function AnomalyKpis({ data, anomalies, outliers, loading }) {
    const kpis = seriesKpis(data?.series)
    const eligible = data?.eligibility?.eligible
    const falls = anomalies.filter((a) => a.direction === "fall").length
    const latest = [...anomalies].sort((a, b) => (a.date < b.date ? 1 : -1))[0]
    const biggestOutlier = outliers[0]
    const yearShift = kpis?.recent && kpis?.previous ? kpis.recent.mean - kpis.previous.mean : null
    const pending = loading ? "…" : "–"

    return (
        <div className="grid gap-3 grid-cols-2 md:grid-cols-3 xl:grid-cols-6">
            <KpiTile
                label={kpis ? `Letzter bewerteter Monat · ${fmtPeriod(kpis.last.period)}` : "Letzter bewerteter Monat"}
                value={kpis ? `${num(kpis.last.mean)} Sterne` : pending}
                note={kpis ? `Monatsmittel aus ${kpis.last.n_values} Bewertungen` : "kein Monat mit mindestens 5 Bewertungen"}
            />
            <KpiTile
                label="Ø letzte 12 Monate"
                value={kpis?.recent ? `${num(kpis.recent.mean)} Sterne` : pending}
                note={kpis?.recent
                    ? kpis.previous
                        ? `Vorjahr ${num(kpis.previous.mean)} · ${signed(yearShift)} Sterne`
                        : `${kpis.recent.n} Bewertungen, kein Vorjahr`
                    : "keine Angabe"}
                tone={toneOf(yearShift)}
            />
            <KpiTile
                label="Bewertungen"
                value={kpis ? kpis.total.toLocaleString("de-DE") : pending}
                note={kpis ? `${kpis.evaluatedMonths} von ${kpis.months} Monaten bewertet, seit ${fmtPeriod(kpis.first)}` : "keine datierten Bewertungen"}
            />
            <KpiTile
                label="Auffällige Veränderungen"
                value={eligible ? String(anomalies.length) : loading ? "…" : "–"}
                note={eligible
                    ? anomalies.length ? `${falls} ${falls === 1 ? "Abfall" : "Abfälle"} · ${anomalies.length - falls} ${anomalies.length - falls === 1 ? "Anstieg" : "Anstiege"}` : "keine erkannt"
                    : data ? "keine automatische Erkennung" : "–"}
            />
            <KpiTile
                label={latest ? `Letzte Veränderung · ab ${fmtPeriod(latest.date)}` : "Letzte Veränderung"}
                value={latest ? `${signed(latest.delta)} Sterne` : loading ? "…" : "–"}
                note={latest ? `Ø ${num(latest.before_mean)} → ${num(latest.after_mean)}` : "keine erkannt"}
                tone={latest ? toneOf(latest.delta) : undefined}
            />
            <KpiTile
                label="Auffällige Einzelmonate"
                value={eligible ? String(outliers.length) : loading ? "…" : "–"}
                note={biggestOutlier
                    ? `größte: ${fmtPeriod(biggestOutlier.date)} ${signed(biggestOutlier.deviation)}`
                    : eligible ? "keine erkannt" : "keine automatische Erkennung"}
            />
        </div>
    )
}
