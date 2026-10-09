import { AlertTriangle } from "lucide-react"
import { BASIS } from "@/lib/dataBasis"

/* ============================================================================
   DataBasis — Kennzeichnung der Datenbasis je Element (Inkrement 6, FA-25)
   und Warnung bei kleiner Basis (FA-26). Festes Vokabular aus vier Begriffen,
   damit Diagramme aus Sternen nicht mit Diagrammen aus Texten oder externen
   Quellen verwechselt werden:
   - Sternebewertung: Sterne der Kununu-Bewertungen (Gesamtnote, Kategorien)
   - Freitextanalyse: Freitexte der Bewertungen (Schlüsselwort-Themen, Stimmung,
     kennzeichnende Begriffe)
   - Externe Meldungen: Meldungen externer Quellen (Google News RSS, EQS News,
     allgemeine Ereignisse)
   - Marktdaten: Kurse und Kennzahlen (Yahoo Finance)
   Schwellen der Warnung sind die bestehenden: 5 Bewertungen je Monat (E4),
   10 Bewertungen je Fenster (E12); keine neue Schwelle. Vokabular und
   Schwellen stehen in lib/dataBasis.js.
   ============================================================================ */

/* Ein Kennzeichen; small für Kopfzeilen mit wenig Platz. */
export function DataBasisTag({ basis, small = false, className = "" }) {
  const b = BASIS[basis]
  if (!b) return null
  return (
    <span
      className={`inline-flex items-center rounded-full border border-slate-300 bg-slate-50 text-slate-600 font-sans normal-case tracking-normal ${small ? "px-1.5 py-px text-[9.5px]" : "px-1.5 py-0.5 text-[10px]"} ${className}`}
      title={b.title}
    >
      {b.label}
    </span>
  )
}

/* Mehrere Kennzeichen nebeneinander (basis: Schlüssel oder Liste). */
export function DataBasisTags({ basis, small = false, className = "" }) {
  const keys = Array.isArray(basis) ? basis : basis ? [basis] : []
  if (!keys.length) return null
  return (
    <span className={`inline-flex flex-wrap items-center gap-1 ${className}`} aria-label="Datenbasis">
      {keys.map((k) => <DataBasisTag key={k} basis={k} small={small} />)}
    </span>
  )
}

/* Warnung bei kleiner Basis: n unter der Schwelle min (Einheit im Text). */
export function SmallBasisWarning({ n, min, unit = "Bewertungen", context = "", className = "" }) {
  if (n == null || min == null || n >= min) return null
  return (
    <span className={`inline-flex items-center gap-1 text-amber-700 ${className}`} title={`Kleine Basis: ${n} ${unit}${context ? ` ${context}` : ""}, Schwelle ${min}`}>
      <AlertTriangle className="w-3 h-3 flex-none" aria-hidden="true" />
      kleine Basis ({n} {unit}{context ? ` ${context}` : ""}, unter {min})
    </span>
  )
}
