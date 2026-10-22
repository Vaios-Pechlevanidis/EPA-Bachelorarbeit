import { fmtPeriod, isPeriod, periodFromIndex, periodIndex } from "./anomalySeries"

/* Eigene Ereignisse (2026-10-17, E32): reine Hilfsfunktionen für Liste,
 * Formular und Diagramm. Grenzen wie im Backend (services/user_events_service.py). */

export const TITLE_MAX = 120
export const NOTE_MAX = 1000

/* Fester Hinweis unter Liste und Formular; derselbe Wortlaut wie im Backend. */
export const USER_EVENT_NOTE =
  "Eigene Ereignisse sind von Nutzerinnen und Nutzern eingetragene Zeiträume zur Einordnung. Sie sind keine Aussage über Ursachen und gehen nicht in Erkennung, Rangfolge oder Belege ein; bei den Erklärungsansätzen stehen sie nur nach zeitlicher Nähe als möglicher Zusammenhang."

/* Hinweis unter der Gruppe "Eigenes Ereignis" bei den Erklärungsansätzen (Nachtrag zu E32, 2026-10-22). */
export const USER_EVENT_EXPLANATION_NOTE =
  "Eigene Ereignisse haben keine Quelle und keine Stufe; sie stehen hier, weil ihr Zeitraum das Ereignisfenster berührt. Möglicher Zusammenhang, keine Ursache."

/* Ereignisfenster eines Niveauwechsels wie im Backend (evidence_service.window_for_change,
 * E18): von DEFAULT_WINDOW_BEFORE Monaten vor dem Beginn des Übergangs (Monat nach
 * previous_period, ohne Lücke der markierte Monat) bis DEFAULT_WINDOW_AFTER Monate nach dem
 * markierten Monat. Nur für den PDF-Export, der die Erklärungsansätze nicht abruft; die
 * Detailseite nimmt das Fenster aus der Antwort (explanation_summary.window). Werte vorläufig (E18). */
export const EVENT_WINDOW_BEFORE = 3
export const EVENT_WINDOW_AFTER = 1

export function changeEventWindow(anomaly, before = EVENT_WINDOW_BEFORE, after = EVENT_WINDOW_AFTER) {
  if (!anomaly || !isPeriod(anomaly.date)) return null
  const transitionFrom = isPeriod(anomaly.previous_period) ? periodIndex(anomaly.previous_period) + 1 : periodIndex(anomaly.date)
  return { from: periodFromIndex(transitionFrom - before), to: periodFromIndex(periodIndex(anomaly.date) + after) }
}

/* Lage eines Ereignisses zum Fenster {from, to}: "im Ereignisfenster", "beginnt vor dem
 * Ereignisfenster", "reicht über das Ereignisfenster hinaus" oder "umfasst das Ereignisfenster". */
export function eventWindowPhrase(event, window) {
  const f = periodIndex(event.date_from), t = periodIndex(event.date_to)
  const wf = periodIndex(window.from), wt = periodIndex(window.to)
  if (f < wf && t > wt) return "umfasst das Ereignisfenster"
  if (f < wf) return "beginnt vor dem Ereignisfenster"
  if (t > wt) return "reicht über das Ereignisfenster hinaus"
  return "im Ereignisfenster"
}

/* Eigene Ereignisse, deren Zeitraum das Fenster {from, to} berührt (Monate einschließlich),
 * sortiert wie die Liste, je Ereignis mit time_phrase. Ohne Fenster oder Ereignisse: leer. */
export function userEventsInWindow(events, window) {
  if (!Array.isArray(events) || !window || !isPeriod(window.from) || !isPeriod(window.to)) return []
  const wf = periodIndex(window.from), wt = periodIndex(window.to)
  return sortUserEvents(events.filter((e) => isPeriod(e.date_from) && isPeriod(e.date_to) && periodIndex(e.date_to) >= wf && periodIndex(e.date_from) <= wt))
    .map((e) => ({ ...e, time_phrase: eventWindowPhrase(e, window) }))
}

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
