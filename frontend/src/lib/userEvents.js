import { fmtPeriod, isPeriod, periodIndex } from "./anomalySeries"

/* Eigene Ereignisse (2026-10-17, E32): reine Hilfsfunktionen für Liste,
 * Formular und Diagramm. Grenzen wie im Backend (services/user_events_service.py). */

export const TITLE_MAX = 120
export const NOTE_MAX = 1000

/* Fester Hinweis unter Liste und Formular; derselbe Wortlaut wie im Backend. */
export const USER_EVENT_NOTE =
  "Eigene Ereignisse sind von Nutzerinnen und Nutzern eingetragene Zeiträume zur Einordnung. Sie sind keine Aussage über Ursachen und gehen nicht in Erkennung, Erklärungsansätze oder Belege ein."

/* Nach Beginn, dann Ende, dann Kennung; so stimmt die Nummer im Diagramm mit der Liste überein. */
export function sortUserEvents(events) {
  return [...events].sort((a, b) =>
    periodIndex(a.date_from) - periodIndex(b.date_from)
    || periodIndex(a.date_to) - periodIndex(b.date_to)
    || (a.id ?? 0) - (b.id ?? 0))
}

/* "März 2024" oder "Jan. 2024 – Juni 2024". */
export function eventSpanLabel(event) {
  if (!event) return ""
  return event.date_from === event.date_to ? fmtPeriod(event.date_from) : `${fmtPeriod(event.date_from)} – ${fmtPeriod(event.date_to)}`
}

/* Zahl der Monate von date_from bis date_to einschließlich. */
export function eventMonths(event) {
  return periodIndex(event.date_to) - periodIndex(event.date_from) + 1
}

/* Wahr, wenn der Monat im Zeitraum des Ereignisses liegt. */
export function eventCoversPeriod(event, period) {
  const i = periodIndex(period)
  return periodIndex(event.date_from) <= i && i <= periodIndex(event.date_to)
}

/* Prüfung der Eingabe vor dem Senden; dieselben Regeln wie im Backend.
 * Rückgabe: {title, date_from, date_to, note} oder wirft Error mit Meldung. */
export function validateUserEventInput({ title, from, to, note }) {
  const t = String(title ?? "").trim()
  if (!t) throw new Error("Bitte einen Titel angeben.")
  if (t.length > TITLE_MAX) throw new Error(`Der Titel darf höchstens ${TITLE_MAX} Zeichen haben.`)
  if (!isPeriod(from)) throw new Error("Bitte einen Startmonat wählen.")
  const end = to || from
  if (!isPeriod(end)) throw new Error("Bitte einen Endmonat wählen.")
  if (periodIndex(end) < periodIndex(from)) throw new Error("Der Endmonat darf nicht vor dem Startmonat liegen.")
  const n = String(note ?? "").trim()
  if (n.length > NOTE_MAX) throw new Error(`Der Vermerk darf höchstens ${NOTE_MAX} Zeichen haben.`)
  return { title: t, date_from: from, date_to: end, note: n || null }
}
