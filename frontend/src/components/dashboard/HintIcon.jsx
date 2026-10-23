import { CircleHelp } from "lucide-react"

/* Kleines Fragezeichen mit kurzer Erklärung, die beim Darüberfahren oder per
 * Tastatur (Fokus) erscheint (2026-10-23). text: ein bis zwei Sätze; label:
 * Beschriftung des Knopfs für Hilfstechnik. Der Klick wird nicht weitergereicht,
 * damit das Symbol auch in anklickbaren Flächen steht. */
export function HintIcon({ text, label = "Erklärung", className = "" }) {
    return (
        <span className={`relative inline-flex group align-middle ${className}`}>
            <button
                type="button"
                aria-label={label}
                className="inline-flex items-center justify-center w-4 h-4 rounded-full text-slate-400 hover:text-slate-700 focus:outline-none focus-visible:ring-1 focus-visible:ring-slate-400"
                onClick={(e) => e.stopPropagation()}
            >
                <CircleHelp className="w-3.5 h-3.5" aria-hidden="true" />
            </button>
            <span
                role="tooltip"
                className="pointer-events-none absolute left-0 top-full z-20 mt-1 hidden w-[280px] max-w-[80vw] rounded-md border border-slate-200 bg-white px-2.5 py-2 text-left text-[11px] font-normal normal-case tracking-normal leading-4 text-slate-700 shadow-md group-hover:block group-focus-within:block"
            >
                {text}
            </span>
        </span>
    )
}
