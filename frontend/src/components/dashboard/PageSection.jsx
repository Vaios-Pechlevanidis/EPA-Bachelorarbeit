import { DataBasisTags } from "./DataBasis"

/* Abschnitt einer Detailseite (Anomalien, Aktie): Kopf mit Symbol, Kennung,
   Titel, Untertitel und Aktionen, darunter der Inhalt. className z. B. für
   Rasterspalten, bodyClassName für den Inhaltsbereich (Standard px-4 py-4).
   Bei Platzmangel rücken die Aktionen unter den Titel (wie in ExpandableCard).
   basis: Datenbasis des Abschnitts (Schlüssel aus DataBasis, auch Liste),
   als Kennzeichen neben der Kennung (Inkrement 6, FA-25). */
export function PageSection({ icon, eyebrow, title, subtitle, actions, children, className = "", bodyClassName = "px-4 py-4", basis = null }) {
    return (
        <section className={`bg-white border border-slate-200 rounded-lg overflow-hidden shadow-xs min-w-0 ${className}`}>
            <div className="px-4 pt-3 pb-3 border-b border-slate-200 flex flex-wrap items-start gap-x-2.5 gap-y-2">
                <div className="flex items-start gap-2.5 min-w-[180px] flex-1">
                    <span className="w-7 h-7 rounded-md grid place-items-center flex-none bg-slate-100 text-slate-600 mt-0.5 [&_svg]:w-[14px] [&_svg]:h-[14px]">
                        {icon}
                    </span>
                    <div className="min-w-0 flex-1">
                        <p className="m-0 mb-0.5 font-mono text-[10px] tracking-[0.06em] uppercase text-slate-500 leading-none flex flex-wrap items-center gap-x-2 gap-y-1">
                            <span>{eyebrow}</span>
                            <DataBasisTags basis={basis} small />
                        </p>
                        <h2 className="m-0 text-[14px] leading-5 font-semibold tracking-tight text-slate-900">{title}</h2>
                        {subtitle && <p className="m-0 mt-0.5 text-[11px] text-slate-500 leading-4">{subtitle}</p>}
                    </div>
                </div>
                {actions && <div className="flex flex-wrap items-center justify-end gap-2 ml-auto max-w-full">{actions}</div>}
            </div>
            <div className={bodyClassName}>{children}</div>
        </section>
    )
}
