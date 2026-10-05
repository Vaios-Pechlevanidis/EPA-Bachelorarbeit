import { useCallback, useEffect, useState } from "react"
import { Maximize2 } from "lucide-react"
import { Dialog, DialogContent, DialogTitle } from "@/components/ui/dialog"

/* ============================================================================
   ExpandableCard — Karte, die sich per Klick vergrößert, wie die Karten im
   Haupt-Dashboard (TimelineCard): Kopf mit Symbol, Kennung, Titel und
   Aktionen, Inhalt, Fußzeile "Karte anklicken zum Vergrößern"; Klick auf die
   Karte öffnet einen Dialog mit 90 % der Breite und 85 % der Höhe des Fensters.
   Schalter stehen rechts neben dem Titel (bei Platzmangel darunter).

   children und actions sind Funktionen ({ modal, height }) => Knoten, damit
   die Karte im Dialog größer gezeichnet wird. height ist die Höhe, die der
   Inhalt einnehmen darf (Diagramm samt Legende):
   - fill=true: gemessene Höhe des Inhaltsbereichs; die Karte füllt dann die
     Fläche, die ihr das Raster gibt (Aktien-Dashboard ab 1280 px Breite),
   - sonst cardHeight,
   - im Dialog die verfügbare Höhe unter dem Kopf.
   ============================================================================ */

const MODAL_RESERVE = 120 // Kopf und Innenabstand des Dialogs in Pixeln

/* Füllt die Resthöhe eines Spaltencontainers und gibt die gemessene Höhe an
   children(h) weiter; Recharts braucht eine Höhe in Pixeln. Gemessen wird
   beim Einhängen sofort (auch in einem noch nicht sichtbaren Tab, in dem der
   ResizeObserver erst später meldet) und danach bei jeder Größenänderung. */
export function FillBox({ children, className = "" }) {
    const [node, setNode] = useState(null)
    const [height, setHeight] = useState(0)
    const ref = useCallback((el) => {
        setNode(el)
        if (el) setHeight(Math.floor(el.getBoundingClientRect().height))
    }, [])
    useEffect(() => {
        if (!node || typeof ResizeObserver === "undefined") return undefined
        const observer = new ResizeObserver(([entry]) => setHeight(Math.floor(entry.contentRect.height)))
        observer.observe(node)
        return () => observer.disconnect()
    }, [node])
    return <div ref={ref} className={`flex-1 min-h-0 ${className}`}>{height > 0 ? children(height) : null}</div>
}

function measureModalHeight() {
    return typeof window === "undefined" ? 520 : Math.max(320, Math.round(window.innerHeight * 0.85) - MODAL_RESERVE)
}

function useModalHeight(open) {
    const [height, setHeight] = useState(measureModalHeight)
    useEffect(() => {
        if (!open) return undefined
        const update = () => setHeight(measureModalHeight())
        update()
        window.addEventListener("resize", update)
        return () => window.removeEventListener("resize", update)
    }, [open])
    return height
}

export function ExpandableCard({
    icon, eyebrow, title, subtitle, actions = null, children,
    cardHeight = 220, fill = false, accent = "bg-violet-500", className = "",
}) {
    const [open, setOpen] = useState(false)
    const modalHeight = useModalHeight(open)
    const render = (fn, ctx) => (typeof fn === "function" ? fn(ctx) : fn)

    return (
        <>
            <div
                role="button"
                tabIndex={0}
                title="Karte anklicken zum Vergrößern"
                onClick={() => setOpen(true)}
                onKeyDown={(e) => { if (e.target === e.currentTarget && (e.key === "Enter" || e.key === " ")) { e.preventDefault(); setOpen(true) } }}
                className={`group bg-white border border-slate-200 rounded-lg overflow-hidden shadow-xs hover:shadow-sm transition-shadow cursor-pointer flex flex-col min-w-0 min-h-0 ${className}`}
            >
                <div className="px-4 py-2.5 border-b border-slate-200 flex flex-wrap items-center gap-x-3 gap-y-2 flex-none">
                    <div className="flex items-start gap-2.5 min-w-[180px] flex-1">
                        <span className="w-7 h-7 rounded-md grid place-items-center flex-none bg-slate-100 text-slate-600 mt-0.5 [&_svg]:w-[14px] [&_svg]:h-[14px]">
                            {icon}
                        </span>
                        <div className="min-w-0 flex-1">
                            <p className="m-0 mb-0.5 font-mono text-[10px] tracking-[0.06em] uppercase text-slate-500 leading-none truncate">{eyebrow}</p>
                            <h3 className="m-0 text-[14px] leading-5 font-semibold tracking-tight text-slate-900 flex items-center gap-1.5 min-w-0">
                                <span className="truncate">{title}</span>
                                <Maximize2 aria-hidden="true" className="h-3 w-3 flex-none text-slate-400 opacity-0 group-hover:opacity-100 transition-opacity" />
                            </h3>
                            {subtitle && <p className="m-0 mt-0.5 text-[11px] leading-4 text-slate-500 truncate" title={subtitle}>{subtitle}</p>}
                        </div>
                    </div>
                    {actions && (
                        <div onClick={(e) => e.stopPropagation()} className="flex items-center gap-1.5 flex-wrap justify-end ml-auto">
                            {render(actions, { modal: false })}
                        </div>
                    )}
                </div>
                <div className="px-4 pt-3 flex flex-col flex-1 min-h-0">
                    {fill
                        ? <FillBox>{(height) => render(children, { modal: false, height })}</FillBox>
                        : render(children, { modal: false, height: cardHeight })}
                </div>
                <p className="m-0 px-4 pt-1.5 pb-2 text-[11px] text-slate-400 text-center inline-flex w-full items-center justify-center gap-1 flex-none">
                    <Maximize2 aria-hidden="true" className="w-3 h-3" />
                    Karte anklicken zum Vergrößern
                </p>
            </div>

            <Dialog open={open} onOpenChange={setOpen}>
                <DialogContent
                    className="overflow-hidden flex flex-col p-0 gap-0"
                    style={{ width: "90vw", maxWidth: "90vw", height: "85vh", maxHeight: "85vh" }}
                    aria-describedby={undefined}
                >
                    <span aria-hidden="true" className={`block h-[3px] w-full ${accent}`} />
                    <div className="px-5 py-4 pr-14 border-b border-slate-200 flex items-start justify-between gap-3 flex-shrink-0">
                        <div className="flex items-start gap-2.5 min-w-0">
                            <span className="w-9 h-9 rounded-md grid place-items-center bg-slate-100 text-slate-600 flex-none [&_svg]:w-[18px] [&_svg]:h-[18px]">
                                {icon}
                            </span>
                            <div className="min-w-0">
                                <p className="m-0 mb-0.5 font-mono text-[10px] tracking-[0.06em] uppercase text-slate-500 leading-none">{eyebrow}</p>
                                <DialogTitle className="m-0 text-[18px] leading-6 font-semibold tracking-tight text-slate-900">{title}</DialogTitle>
                                {subtitle && <p className="m-0 mt-0.5 text-[11px] text-slate-500">{subtitle}</p>}
                            </div>
                        </div>
                        {actions && (
                            <div className="flex items-center gap-2 flex-wrap justify-end">{render(actions, { modal: true })}</div>
                        )}
                    </div>
                    <div className="flex-1 min-h-0 overflow-y-auto px-5 py-4">
                        {open && render(children, { modal: true, height: modalHeight })}
                    </div>
                </DialogContent>
            </Dialog>
        </>
    )
}
