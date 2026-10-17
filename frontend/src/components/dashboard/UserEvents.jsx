import { useState } from "react"
import { Flag, Pencil, Plus, Trash2 } from "lucide-react"
import { Dialog, DialogContent, DialogTitle } from "@/components/ui/dialog"
import { MonthPicker } from "./DrilldownPicker"
import { periodIndex } from "@/lib/anomalySeries"
import { NOTE_MAX, TITLE_MAX, USER_EVENT_NOTE, eventSpanLabel, validateUserEventInput } from "@/lib/userEvents"

/* ============================================================================
   UserEvents — eigene Ereignisse im Monatsverlauf (2026-10-17, E32).
   Nutzerinnen und Nutzer tragen zu einem Unternehmen Zeiträume mit Titel und
   Vermerk ein (z. B. Führungswechsel, Umstrukturierung). Hier stehen der Knopf
   „Ereignis eintragen“ (Kopf des Monatsverlaufs), das Formular im Dialog und
   die Liste in der Karte „Markierungen“ der Detailseite; die Marken im
   Diagramm zeichnet AnomalyChart (AnomalyCard.jsx). Nummer in Liste und
   Diagramm sind dieselbe (Reihenfolge nach Beginn). Wortwahl: Einordnung
   durch die Nutzenden, keine Aussage über Ursachen.
   ============================================================================ */

export const USER_EVENT_COLOR = "var(--user-event)"

const buttonClass =
    "h-7 px-2.5 inline-flex items-center gap-1.5 rounded-md border border-slate-300 bg-white text-[12px] font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed [&_svg]:w-3.5 [&_svg]:h-3.5"
const fieldClass =
    "w-full rounded-md border border-slate-300 bg-white px-2.5 py-1.5 text-[13px] text-slate-800 placeholder:text-slate-400 focus:outline-none focus-visible:ring-1 focus-visible:ring-slate-400"
const labelClass = "block text-[11px] font-medium text-slate-600 mb-1"

/* Nummernmarke wie im Diagramm (Legende, Liste, Tooltip). */
export function UserEventGlyph({ number = null, size = 16, className = "" }) {
    return (
        <span
            aria-hidden="true"
            className={`inline-grid place-items-center rounded-full flex-none font-semibold tnum leading-none ${className}`}
            style={{ width: size, height: size, background: USER_EVENT_COLOR, color: "var(--color-bg-card)", fontSize: Math.round(size * 0.58) }}
        >
            {number ?? ""}
        </span>
    )
}

/* Knopf im Kopf des Monatsverlaufs. */
export function AddUserEventButton({ onClick, disabled = false, title = "Eigenes Ereignis zu diesem Unternehmen eintragen" }) {
    return (
        <button type="button" className={buttonClass} onClick={(e) => { e.stopPropagation(); onClick() }} disabled={disabled} title={title}>
            <Plus />
            Ereignis eintragen
        </button>
    )
}

function initialDraft(event, initial, months) {
    const last = months[months.length - 1] ?? null
    const from = event?.date_from ?? initial?.from ?? last
    const to = event?.date_to ?? initial?.to ?? from
    return { title: event?.title ?? "", from, to, note: event?.note ?? "" }
}

/* Formular im Dialog: Titel, von, bis (Monatsraster wie im Drill-down), Vermerk.
   event = bestehender Eintrag (Ändern, mit Löschen) oder null (Neu); initial =
   {from, to} als Vorbelegung (aktuelle Auswahl). months: Monate der Reihe,
   counts: Bewertungen je Monat. onSave(payload) gibt ein Promise zurück; die
   Meldung eines Fehlers erscheint im Dialog. Das Formular selbst (UserEventForm)
   wird mit dem Dialoginhalt eingehängt, sein Zustand beginnt also bei jedem
   Öffnen frisch. */
export function UserEventDialog({ open, onOpenChange, event = null, initial = null, months = [], counts = null, saving = false, onSave, onDelete = null }) {
    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="overflow-hidden p-0 gap-0 sm:max-w-[520px]" aria-describedby={undefined}>
                <span aria-hidden="true" className="block h-[3px] w-full" style={{ background: USER_EVENT_COLOR }} />
                <div className="px-5 py-4 pr-14 border-b border-slate-200 flex items-start gap-2.5">
                    <span className="w-9 h-9 rounded-md grid place-items-center bg-slate-100 text-slate-600 flex-none [&_svg]:w-[18px] [&_svg]:h-[18px]">
                        <Flag />
                    </span>
                    <div className="min-w-0">
                        <p className="m-0 mb-0.5 font-mono text-[10px] tracking-[0.06em] uppercase text-slate-500 leading-none">
                            {event ? "EIGENES EREIGNIS · ÄNDERN" : "EIGENES EREIGNIS · NEU"}
                        </p>
                        <DialogTitle className="m-0 text-[18px] leading-6 font-semibold tracking-tight text-slate-900">
                            {event ? "Ereignis ändern" : "Ereignis eintragen"}
                        </DialogTitle>
                        <p className="m-0 mt-0.5 text-[11px] text-slate-500">
                            Zeitraum in Monaten, wie der Verlauf; die Marke erscheint im Diagramm und in der Liste „Eigene Ereignisse“.
                        </p>
                    </div>
                </div>
                {!months.length ? (
                    <p className="m-0 px-5 py-4 text-[13px] text-slate-500">Keine datierten Bewertungen; ohne Monatsverlauf kann kein Ereignis eingetragen werden.</p>
                ) : (
                    <UserEventForm
                        key={`${event?.id ?? "neu"}:${initial?.from ?? ""}:${initial?.to ?? ""}`}
                        event={event} initial={initial} months={months} counts={counts} saving={saving}
                        onSave={onSave} onDelete={onDelete} onClose={() => onOpenChange(false)}
                    />
                )}
            </DialogContent>
        </Dialog>
    )
}

function UserEventForm({ event, initial, months, counts, saving, onSave, onDelete, onClose }) {
    const [draft, setDraft] = useState(() => initialDraft(event, initial, months))
    const [error, setError] = useState("")
    const [confirmDelete, setConfirmDelete] = useState(false)

    const monthSet = new Set(months)
    const first = months[0]
    const last = months[months.length - 1]
    const pickerProps = { months: monthSet, first, last, counts, range: draft.from && draft.to ? { from: draft.from, to: draft.to } : null }

    // Beim Setzen folgt der jeweils andere Monat mit, damit nie "bis" vor "von" liegt.
    const setFrom = (m) => setDraft((d) => ({ ...d, from: m, to: d.to && periodIndex(d.to) < periodIndex(m) ? m : d.to }))
    const setTo = (m) => setDraft((d) => ({ ...d, to: m, from: d.from && periodIndex(d.from) > periodIndex(m) ? m : d.from }))

    const submit = async (e) => {
        e.preventDefault()
        let payload
        try {
            payload = validateUserEventInput(draft)
        } catch (err) {
            setError(err.message)
            return
        }
        try {
            await onSave(payload)
            onClose()
        } catch (err) {
            setError(err.message || "Speichern fehlgeschlagen.")
        }
    }

    const remove = async () => {
        try {
            await onDelete()
            onClose()
        } catch (err) {
            setError(err.message || "Löschen fehlgeschlagen.")
        }
    }

    const months_ = draft.from && draft.to ? periodIndex(draft.to) - periodIndex(draft.from) + 1 : 0

    return (
                    <form onSubmit={submit} className="px-5 py-4 space-y-3.5">
                        <div>
                            <label htmlFor="user-event-title" className={labelClass}>Titel</label>
                            <input
                                id="user-event-title"
                                type="text"
                                className={fieldClass}
                                value={draft.title}
                                maxLength={TITLE_MAX}
                                placeholder="z. B. Führungswechsel, Umstrukturierung, Standortschließung"
                                autoFocus
                                onChange={(e) => setDraft((d) => ({ ...d, title: e.target.value }))}
                            />
                        </div>
                        <div className="flex flex-wrap items-end gap-3 text-[12px] text-slate-600">
                            <div>
                                <span className={labelClass}>von</span>
                                <MonthPicker label="von" value={draft.from} {...pickerProps} onChange={setFrom} />
                            </div>
                            <div>
                                <span className={labelClass}>bis</span>
                                <MonthPicker label="bis" value={draft.to} {...pickerProps} onChange={setTo} />
                            </div>
                            <span className="pb-1.5 text-[11px] text-slate-500 tnum">
                                {months_ === 1 ? "1 Monat" : `${months_} Monate`} · {eventSpanLabel({ date_from: draft.from, date_to: draft.to })}
                            </span>
                        </div>
                        <div>
                            <label htmlFor="user-event-note" className={labelClass}>Vermerk <span className="font-normal text-slate-400">(optional)</span></label>
                            <textarea
                                id="user-event-note"
                                className={`${fieldClass} min-h-[72px] resize-y`}
                                value={draft.note}
                                maxLength={NOTE_MAX}
                                placeholder="Was ist in diesem Zeitraum geschehen? Quelle oder Stichworte"
                                onChange={(e) => setDraft((d) => ({ ...d, note: e.target.value }))}
                            />
                            <p className="m-0 mt-1 text-right text-[10px] text-slate-400 tnum">{draft.note.length} / {NOTE_MAX}</p>
                        </div>
                        {error && <p className="m-0 text-[12px] text-rose-700" role="alert">{error}</p>}
                        <p className="m-0 text-[11px] text-slate-500 leading-snug">{USER_EVENT_NOTE}</p>
                        <div className="flex flex-wrap items-center gap-2 pt-1">
                            <button type="submit" disabled={saving}
                                className="h-8 px-3 rounded-md text-[12px] font-medium text-white disabled:opacity-50"
                                style={{ background: USER_EVENT_COLOR }}>
                                {saving ? "Speichern…" : event ? "Änderungen speichern" : "Eintragen"}
                            </button>
                            <button type="button" className={buttonClass} onClick={onClose} disabled={saving}>
                                Abbrechen
                            </button>
                            {event && onDelete && (
                                <span className="ml-auto inline-flex items-center gap-2">
                                    {confirmDelete ? (
                                        <>
                                            <span className="text-[12px] text-slate-600">Wirklich löschen?</span>
                                            <button type="button" className={`${buttonClass} text-rose-700 border-rose-200 hover:bg-rose-50`} onClick={remove} disabled={saving}>
                                                Ja, löschen
                                            </button>
                                            <button type="button" className={buttonClass} onClick={() => setConfirmDelete(false)} disabled={saving}>
                                                Nein
                                            </button>
                                        </>
                                    ) : (
                                        <button type="button" className={`${buttonClass} text-rose-700`} onClick={() => setConfirmDelete(true)} disabled={saving} title="Dieses Ereignis löschen">
                                            <Trash2 />
                                            Löschen
                                        </button>
                                    )}
                                </span>
                            )}
                        </div>
                    </form>
    )
}

const iconButtonClass =
    "h-6 w-6 flex-none rounded-md grid place-items-center text-slate-400 hover:bg-slate-200 hover:text-slate-800 disabled:opacity-50 [&_svg]:w-3.5 [&_svg]:h-3.5"

/* Liste in der Karte "Markierungen" (Detailseite). events tragen number (Reihenfolge
   nach Beginn über alle Ereignisse des Unternehmens, wie im Diagramm). Klick auf
   die Zeile wählt den Zeitraum des Ereignisses als Auswahl (onSelect), der Stift
   öffnet das Formular (onEdit), der Papierkorb fragt in der Zeile nach und löscht
   (onDelete, Promise; Fehler erscheinen in der Zeile). selection = aktuelle
   Auswahl {from, to}. */
export function UserEventList({ events, selection = null, onSelect = null, onEdit = null, onDelete = null, emptyText = "Noch keine eigenen Ereignisse." }) {
    // Zeile, die gerade die Rückfrage zeigt, und Zeile, die gerade gelöscht wird (je Kennung)
    const [confirmId, setConfirmId] = useState(null)
    const [pending, setPending] = useState({ id: null, error: "" })
    if (!events.length) return <p className="text-[12px] text-slate-500 m-0">{emptyText}</p>

    const remove = async (e) => {
        setPending({ id: e.id, error: "" })
        try {
            await onDelete(e)
            setConfirmId(null)
            setPending({ id: null, error: "" })
        } catch (err) {
            setPending({ id: e.id, error: err.message || "Löschen fehlgeschlagen." })
        }
    }

    return (
        <ul className="m-0 p-0 list-none">
            {events.map((e) => {
                const selected = Boolean(selection && selection.from === e.date_from && selection.to === e.date_to)
                const select = () => onSelect?.(e)
                const asking = confirmId === e.id
                const deleting = pending.id === e.id && !pending.error
                const error = pending.id === e.id ? pending.error : ""
                return (
                    <li
                        key={e.id}
                        className={[
                            "flex items-start gap-3 py-2 text-[12px] border-t border-slate-100 first:border-t-0",
                            onSelect ? "cursor-pointer px-2 -mx-2 rounded-md hover:bg-slate-50" : "",
                            selected ? "bg-slate-100 hover:bg-slate-100" : "",
                        ].join(" ")}
                        onClick={onSelect ? select : undefined}
                        onKeyDown={onSelect ? (ev) => { if (ev.target === ev.currentTarget && (ev.key === "Enter" || ev.key === " ")) { ev.preventDefault(); select() } } : undefined}
                        role={onSelect ? "button" : undefined}
                        tabIndex={onSelect ? 0 : undefined}
                        aria-pressed={onSelect ? selected : undefined}
                        title={onSelect ? "Auswählen: Bewertungen und Vergleich dieses Zeitraums zeigen" : undefined}
                    >
                        <UserEventGlyph number={e.number} className="mt-0.5" />
                        <span className="flex-1 min-w-0">
                            <span className="flex items-center gap-2 min-w-0">
                                <span className="font-medium text-slate-800 truncate">{e.title}</span>
                                <span className="ml-auto flex-none text-[11px] text-slate-500 tnum">{eventSpanLabel(e)}</span>
                            </span>
                            {e.note && !asking && (
                                <span className="block text-[11px] text-slate-500 leading-snug line-clamp-2 whitespace-pre-line">{e.note}</span>
                            )}
                            {asking && (
                                // Rückfrage in der Zeile; Klicks hier wählen nicht die Zeile aus.
                                <span className="mt-1 flex flex-wrap items-center gap-2 text-[11px]" onClick={(ev) => ev.stopPropagation()}>
                                    <span className="text-slate-700">{deleting ? "Wird gelöscht…" : "Wirklich löschen?"}</span>
                                    <button type="button" className={`${buttonClass} h-6 px-2 text-[11px] text-rose-700 border-rose-200 hover:bg-rose-50`}
                                        onClick={() => remove(e)} disabled={deleting} autoFocus>
                                        Ja, löschen
                                    </button>
                                    <button type="button" className={`${buttonClass} h-6 px-2 text-[11px]`}
                                        onClick={() => { setConfirmId(null); setPending({ id: null, error: "" }) }} disabled={deleting}>
                                        Nein
                                    </button>
                                    {error && <span className="basis-full text-rose-700" role="alert">{error}</span>}
                                </span>
                            )}
                        </span>
                        {onEdit && !asking && (
                            <button
                                type="button"
                                className={iconButtonClass}
                                title="Ereignis ändern"
                                aria-label={`Ereignis „${e.title}“ ändern`}
                                onClick={(ev) => { ev.stopPropagation(); onEdit(e) }}
                            >
                                <Pencil />
                            </button>
                        )}
                        {onDelete && !asking && (
                            <button
                                type="button"
                                className={`${iconButtonClass} hover:text-rose-700`}
                                title="Ereignis löschen (mit Rückfrage)"
                                aria-label={`Ereignis „${e.title}“ löschen`}
                                onClick={(ev) => { ev.stopPropagation(); setPending({ id: null, error: "" }); setConfirmId(e.id) }}
                            >
                                <Trash2 />
                            </button>
                        )}
                    </li>
                )
            })}
        </ul>
    )
}
