import { useEffect, useState } from "react"
import { Maximize2 } from "lucide-react"
import { Dialog, DialogContent, DialogTitle } from "@/components/ui/dialog"

/* ============================================================================
   ExpandableCard — Karte, die sich per Klick vergrößert, wie die Karten im
   Haupt-Dashboard (TimelineCard): Kopf mit Symbol, Kennung, Titel und
   Aktionen, Inhalt; Klick auf die Karte öffnet einen Dialog mit 90 % der
   Breite und 85 % der Höhe des Fensters. Der Kopf der Karte ist kompakt:
   Schalter stehen rechts neben dem Titel (bei Platzmangel darunter), ein
   Symbol oben rechts zeigt an, dass sich die Karte vergrößern lässt.

   children und actions sind Funktionen ({ modal, height }) => Knoten, damit
   die Karte im Dialog größer gezeichnet wird. height ist im Dialog die für
   das Diagramm verfügbare Höhe in Pixeln, sonst cardHeight.
   ============================================================================ */

function measureHeight(reserve) {
    return typeof window === "undefined" ? 520 : Math.max(320, Math.round(window.innerHeight * 0.85) - reserve)
}

function useModalChartHeight(open, reserve) {
    const [height, setHeight] = useState(() => measureHeight(reserve))
    useEffect(() => {
        if (!open) return undefined
        const update = () => setHeight(measureHeight(reserve))
        update()
        window.addEventListener("resize", update)
        return () => window.removeEventListener("resize", update)
    }, [open, reserve])
    return height
}

export function ExpandableCard({
    icon, eyebrow, title, subtitle, actions = null, children,
    cardHeight = 220, modalReserve = 200, accent = "bg-violet-500", className = "", bodyClassName = "",
}) {
    const [open, setOpen] = useState(false)
    const modalHeight = useModalChartHeight(open, modalReserve)
    const render = (fn, ctx) => (typeof fn === "function" ? fn(ctx) : fn)

    return (
        <>
            <div
                role="button"
                tabIndex={0}
                title="Karte anklicken zum Vergrößern"
                onClick={() => setOpen(true)}
                onKeyDown={(e) => { if (e.target === e.currentTarget && (e.key === "Enter" || e.key === " ")) { e.preventDefault(); setOpen(true) } }}
                className={`group bg-white border border-slate-200 rounded-lg overflow-hidden shadow-xs hover:shadow-sm transition-shadow cursor-pointer flex flex-col min-w-0 ${className}`}
            >
                <div className="px-3 py-2 border-b border-slate-200 flex flex-wrap items-center gap-x-2 gap-y-1.5">
                    <div className="flex items-center gap-2 min-w-[150px] flex-1">
                        <span className="w-6 h-6 rounded-md grid place-items-center flex-none bg-slate-100 text-slate-600 [&_svg]:w-[13px] [&_svg]:h-[13px]">
                            {icon}
                        </span>
                        <div className="min-w-0 flex-1">
                            <p className="m-0 font-mono text-[9px] tracking-[0.06em] uppercase text-slate-500 leading-none truncate">{eyebrow}</p>
                            <h3 className="m-0 mt-0.5 text-[13px] leading-4 font-semibold tracking-tight text-slate-900 truncate">{title}</h3>
                            {subtitle && <p className="m-0 mt-0.5 text-[10.5px] leading-[13px] text-slate-500 truncate" title={subtitle}>{subtitle}</p>}
                        </div>
                    </div>
                    <div className="flex items-center gap-1.5 flex-wrap justify-end ml-auto">
                        {actions && (
                            <div onClick={(e) => e.stopPropagation()} className="flex items-center gap-1.5 flex-wrap justify-end">
                                {render(actions, { modal: false })}
                            </div>
                        )}
                        <Maximize2 aria-hidden="true" className="w-3.5 h-3.5 flex-none text-slate-400 group-hover:text-slate-700 transition-colors" />
                    </div>
                </div>
                <div className={`px-3 pt-2 pb-2 flex flex-col flex-1 min-h-0 ${bodyClassName}`}>
                    {render(children, { modal: false, height: cardHeight })}
                </div>
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
