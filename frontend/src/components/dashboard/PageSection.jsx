/* Abschnitt einer Detailseite (Anomalien, Aktie): Kopf mit Symbol, Kennung,
   Titel, Untertitel und Aktionen, darunter der Inhalt. */
export function PageSection({ icon, eyebrow, title, subtitle, actions, children }) {
    return (
        <section className="bg-white border border-slate-200 rounded-lg overflow-hidden shadow-xs">
            <div className="px-4 pt-3 pb-3 border-b border-slate-200 flex items-start gap-2.5">
                <span className="w-7 h-7 rounded-md grid place-items-center flex-none bg-slate-100 text-slate-600 mt-0.5 [&_svg]:w-[14px] [&_svg]:h-[14px]">
                    {icon}
                </span>
                <div className="min-w-0 flex-1">
                    <p className="m-0 mb-0.5 font-mono text-[10px] tracking-[0.06em] uppercase text-slate-500 leading-none">{eyebrow}</p>
                    <h2 className="m-0 text-[14px] leading-5 font-semibold tracking-tight text-slate-900">{title}</h2>
                    {subtitle && <p className="m-0 mt-0.5 text-[11px] text-slate-500 leading-4">{subtitle}</p>}
                </div>
                {actions && <div className="flex-none flex items-center gap-2">{actions}</div>}
            </div>
            <div className="px-4 py-4">{children}</div>
        </section>
    )
}
