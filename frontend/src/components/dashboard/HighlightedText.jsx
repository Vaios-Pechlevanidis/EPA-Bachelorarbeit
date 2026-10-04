/* Text mit markierten Fundstellen. spans: [[start, ende], ...] als
 * Zeichenpositionen im Text (Ende exklusiv), vom Backend berechnet
 * (topic_spans in backend/services/keyword_topic_service.py), damit die
 * Markierung genau der Themenregel folgt. Ohne spans bleibt der Text unverändert. */
export function HighlightedText({ text, spans, title }) {
    if (!text) return null
    if (!spans?.length) return text
    const parts = []
    let pos = 0
    spans.forEach(([start, end], i) => {
        if (start > pos) parts.push(text.slice(pos, start))
        parts.push(
            <mark key={i} title={title} className="bg-amber-100 text-inherit rounded-[2px] px-0.5 -mx-0.5 font-medium">
                {text.slice(start, end)}
            </mark>,
        )
        pos = Math.max(pos, end)
    })
    if (pos < text.length) parts.push(text.slice(pos))
    return parts
}
