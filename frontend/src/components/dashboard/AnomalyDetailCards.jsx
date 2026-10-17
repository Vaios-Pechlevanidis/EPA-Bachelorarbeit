import { useState } from "react"
import { ArrowDownRight, ArrowUpRight, GitCompareArrows, Lightbulb, MessageSquareText, Newspaper } from "lucide-react"
import { ExpandableCard } from "./ExpandableCard"
import { AnomalyComparison } from "./AnomalyComparison"
import { ExplanationContent, ExplanationPreview } from "./ExplanationPanel"
import { EvidenceContent, EvidencePreview, ListControls } from "./EvidenceSection"
import { Headline, PreviewLabel, PreviewStatus, SentimentRows, ShiftBars, Warn } from "./CardPreview"
import { PeriodReviewList, TopicOnlyToggle, WindowSideToggle } from "./PeriodReviews"
import { Delta } from "../ui/primitives"
import { selectionLabel } from "@/lib/anomalySeries"
import { useEvidence, useEvidenceList } from "@/hooks/useEvidence"
import { evidenceSubtitle } from "@/lib/evidenceText"
import { explanationSubtitle } from "@/lib/explanationText"

/* ============================================================================
   AnomalyDetailCards — die vier Karten unter der Drill-down-Leiste der Seite
   "Anomalien im Verlauf" (2026-10-16): Vorher-Nachher-Vergleich, Bewertungen
   des Zeitraums, Mögliche Zusammenhänge, Externe Berichte. Wie die Kacheln und
   Karten des Haupt-Dashboards zeigt jede Karte in der Vorschau eine große
   Kennzahl und höchstens ein kleines Diagramm (CardPreview), damit man auf einen
   Blick sieht, wo die stärksten Unterschiede liegen; ein Klick öffnet die volle
   Ansicht im Dialog (ExpandableCard, 90 % der Breite, 85 % der Höhe). Schalter
   (davor / danach, nur Thema, Sortierung, Ereignisart) stehen nur im Dialog.
   Inhalte und Wortwahl sind unverändert: keine Aussage über Ursachen.
   Die Karten gelten für eine ausgewählte Veränderung (Inkrement 2) ebenso wie
   für die freie Auswahl und den Einzelmonat (E14, E17); labels nennt die
   beiden Fenster ("davor" / "ab dem markierten Monat" bzw. "Zeitraum davor" /
   "Auswahl").
   ============================================================================ */

const HINT = "Karte anklicken öffnet Detailansicht"
const TOP_SHIFTS = 3

const num = (v, digits = 2) =>
    v == null ? "–" : Number(v).toLocaleString("de-DE", { minimumFractionDigits: digits, maximumFractionDigits: digits })
const signed = (v, digits = 2) => (v == null ? "–" : (v > 0 ? "+" : v < 0 ? "−" : "±") + num(Math.abs(v), digits))

/* Farbe der Note wie bei der Kachel "Ø Score" (KPIGrid): ab 3,5 gut, ab 2,5 mittel, sonst kritisch. */
const ratingTone = (v) => {
    const n = Number(v)
    if (!Number.isFinite(n)) return "neu"
    return n >= 3.5 ? "pos" : n >= 2.5 ? "warn" : "neg"
}

/* Kurzbezeichnung der Fenster in den Zeilen: "davor" / "danach" bzw. "davor" / "Auswahl". */
const shortLabels = (labels) => ({ before: "davor", after: labels.after === "Auswahl" ? "Auswahl" : "danach" })

/* ---- Vorher-Nachher-Vergleich ------------------------------------------- */

/* Kennzahl: Verschiebung der Gesamtnote mit Richtung; darunter die größten
   Verschiebungen je Thema als Balken um die Mittelachse; kleine Basis als Warnung. */
function ComparisonPreview({ comparison, intro = null }) {
    if (comparison.loading) return <PreviewStatus spinner>Vergleich wird berechnet; die Stimmungsanalyse kann beim ersten Aufruf dauern…</PreviewStatus>
    if (comparison.error) return <PreviewStatus>Vergleich konnte nicht geladen werden: {comparison.error}</PreviewStatus>
    const data = comparison.data
    if (!data) return null
    const { before, after, rating_shift, value_shift, low_basis, low_basis_rule, topics = [] } = data.comparison
    const dir = rating_shift > 0 ? "rise" : rating_shift < 0 ? "fall" : "flat"
    const tone = dir === "fall" ? "bad" : dir === "rise" ? "good" : "neutral"
    const chip = (
        <Delta
            tone={dir === "fall" ? "neg" : dir === "rise" ? "pos" : "neu"}
            icon={dir === "fall" ? <ArrowDownRight className="w-3 h-3" /> : dir === "rise" ? <ArrowUpRight className="w-3 h-3" /> : null}
        >
            {dir === "fall" ? "Abfall" : dir === "rise" ? "Anstieg" : "stabil"}
        </Delta>
    )
    const top = topics.slice(0, TOP_SHIFTS)
    return (
        <div>
            {intro && <Warn className="mb-2">{intro}</Warn>}
            <Headline
                value={signed(rating_shift)}
                unit="Sterne"
                tone={tone}
                chip={chip}
                sub={`Ø ${num(before.mean_rating)} → ${num(after.mean_rating)} · ${before.n_reviews} → ${after.n_reviews} Bewertungen${value_shift !== undefined ? ` · Dimension ${signed(value_shift)}` : ""}`}
            />
            {top.length > 0 && (
                <>
                    <PreviewLabel>Stärkste Verschiebungen je Thema</PreviewLabel>
                    <ShiftBars rows={top.map((t) => ({ label: t.topic, value: t.share_shift_pp, text: `${signed(t.share_shift_pp, 1)} Pp.` }))} />
                </>
            )}
            {low_basis && (
                <Warn className="mt-2" title={`Mindestens ein Fenster hat weniger als ${low_basis_rule?.min_reviews_per_window} Bewertungen; Anteile und Stimmung schwanken dann stark`}>
                    Kleine Basis: ein Fenster hat weniger als {low_basis_rule?.min_reviews_per_window} Bewertungen.
                </Warn>
            )}
        </div>
    )
}

/* comparison = useAnomalyComparison / usePeriodComparison; subtitle = {short, full};
   intro: Hinweis zum Einzelmonat (Warnzeile auf der Karte, Absatz im Dialog). */
export function ComparisonCard({ eyebrow, title, subtitle, comparison, labels, intro = null, introText = null }) {
    return (
        <ExpandableCard
            icon={<GitCompareArrows />}
            eyebrow={eyebrow}
            title={title}
            subtitle={({ modal }) => (modal ? subtitle.full : subtitle.short)}
            basis={["stars", "text"]}
            accent="bg-slate-500"
            hint={HINT}
        >
            {({ modal }) => (modal ? (
                <>
                    {introText && <p className="m-0 mb-3 text-[12px] text-slate-600">{introText}</p>}
                    <AnomalyComparison data={comparison.data} loading={comparison.loading} error={comparison.error} labels={labels} />
                </>
            ) : (
                <ComparisonPreview comparison={comparison} intro={intro} />
            ))}
        </ExpandableCard>
    )
}

/* ---- Bewertungen des Zeitraums ------------------------------------------- */

/* Kennzahl: Anzahl der Bewertungen im gewählten Fenster mit mittlerer Note (aus
   dem Vergleich, nur ohne Themenfilter); darunter die Stimmung der Freitexte je
   Fenster als gestapelter Balken, damit der Unterschied davor / danach sichtbar ist. */
function ReviewsPreview({ pages, comparison, side, labels, span, topicOnly }) {
    if (pages.loading) return <PreviewStatus spinner>Lade Bewertungen…</PreviewStatus>
    if (pages.error && !pages.items.length) return <PreviewStatus>Bewertungen konnten nicht geladen werden: {pages.error}</PreviewStatus>
    const topic = pages.highlight?.topic ?? null
    const mentions = pages.highlight?.mentions
    const stats = comparison.data?.comparison ?? null
    const meanRating = !topicOnly ? stats?.[side]?.mean_rating ?? null : null
    const short = shortLabels(labels)
    const sub = `${labels[side]} · ${span}${topicOnly && topic ? ` · nur Bewertungen, die ${topic} nennen` : topic && mentions != null ? ` · ${mentions} ${mentions === 1 ? "nennt" : "nennen"} ${topic}` : ""}`
    return (
        <div>
            <Headline
                value={pages.total}
                unit={pages.total === 1 ? "Bewertung" : "Bewertungen"}
                chip={meanRating != null ? <Delta tone={ratingTone(meanRating)}>Ø {num(meanRating)}</Delta> : null}
                sub={sub}
            />
            <PreviewLabel>Stimmung der Freitexte</PreviewLabel>
            {comparison.loading ? (
                <PreviewStatus spinner>wird berechnet…</PreviewStatus>
            ) : stats ? (
                <SentimentRows rows={[{ label: short.before, sentiment: stats.before.sentiment }, { label: short.after, sentiment: stats.after.sentiment }]} />
            ) : (
                <PreviewStatus>nicht verfügbar</PreviewStatus>
            )}
        </div>
    )
}

/* pages = useReviewPages des gewählten Fensters; comparison = Antwort des Vergleichs
   (Note und Stimmung je Fenster); side/onSide = "before" | "after"; window = {from, to}
   des Fensters; topic = {topic, checked, onChange} für den Themenfilter. */
export function ReviewsCard({ eyebrow, title, subtitle, pages, comparison, side, onSide, labels, window, topic = null, listKey, emptyText, footnote }) {
    const span = window ? selectionLabel(window) : ""
    return (
        <ExpandableCard
            icon={<MessageSquareText />}
            eyebrow={eyebrow}
            title={title}
            subtitle={({ modal }) => (modal ? subtitle.full : subtitle.short)}
            basis={["stars", "text"]}
            accent="bg-slate-500"
            hint={HINT}
            actions={({ modal }) => (modal ? <WindowSideToggle value={side} onChange={onSide} labels={labels} /> : null)}
        >
            {({ modal }) => (modal ? (
                <>
                    {topic && (
                        <div className="mb-2">
                            <TopicOnlyToggle topic={topic.topic} checked={topic.checked} onChange={topic.onChange} />
                        </div>
                    )}
                    <PeriodReviewList key={listKey} pages={pages} emptyText={emptyText} />
                    <p className="m-0 mt-3 text-[11px] text-slate-400">{footnote}</p>
                </>
            ) : (
                <ReviewsPreview pages={pages} comparison={comparison} side={side} labels={labels} span={span} topicOnly={Boolean(topic?.checked)} />
            ))}
        </ExpandableCard>
    )
}

/* ---- Mögliche Zusammenhänge ---------------------------------------------- */

/* comparison = Antwort des Vergleichs mit explanations und explanation_summary;
   subtitle = Kurzform für die Karte (im Dialog steht die vollständige Zählung). */
/* onSelectPeriod(from, to): "Zeitraum wählen" bei den allgemeinen Ereignissen im Dialog
   (Drill-down in das Ereignis, Nachtrag zu E29, 2026-10-17). */
export function ExplanationCard({ eyebrow, subtitle, comparison, onSelectPeriod = null }) {
    return (
        <ExpandableCard
            icon={<Lightbulb />}
            eyebrow={eyebrow}
            title="Mögliche Zusammenhänge"
            subtitle={({ modal }) => (modal ? explanationSubtitle(comparison) : subtitle)}
            basis={["external", "text"]}
            accent="bg-slate-500"
            hint={HINT}
        >
            {({ modal }) => (modal
                ? <ExplanationContent data={comparison.data} loading={comparison.loading} error={comparison.error} onSelectPeriod={onSelectPeriod} />
                : <ExplanationPreview data={comparison.data} loading={comparison.loading} error={comparison.error} />)}
        </ExpandableCard>
    )
}

/* ---- Externe Berichte ---------------------------------------------------- */

/* anomalyId für Veränderung oder Einzelmonat, sonst selection {from, to};
   group = {source, dimension, status} wie die Erkennung; scores und rules aus
   explanation_summary des Vergleichs (null, solange er lädt). Sortierung und
   Filter bleiben beim Wechsel der Auswahl erhalten (wie bisher). */
export function EvidenceCard({ eyebrow, subtitle, companyId, anomalyId = null, selection = null, group = {}, scores = null, rules = null }) {
    const evidence = useEvidence(companyId, { anomalyId, selection, ...group })
    const [sort, setSort] = useState("date")
    const [category, setCategory] = useState("")
    const list = useEvidenceList(evidence, scores, { sort, category })
    const showControls = !evidence.loading && !evidence.error && evidence.total > 0
    return (
        <ExpandableCard
            icon={<Newspaper />}
            eyebrow={eyebrow}
            title="Externe Berichte im Ereignisfenster"
            subtitle={({ modal }) => (modal ? evidenceSubtitle(evidence, list.listNote) : subtitle)}
            basis="external"
            accent="bg-slate-500"
            hint={HINT}
            actions={({ modal }) => (modal && showControls ? (
                <ListControls sort={sort} onSort={setSort} category={category} onCategory={setCategory} categories={list.categories} enabled={Boolean(scores)} />
            ) : null)}
        >
            {({ modal }) => (modal
                ? <EvidenceContent evidence={evidence} items={list.items} needAll={list.needAll} sort={sort} category={category} scores={scores} rules={rules} />
                : <EvidencePreview evidence={evidence} />)}
        </ExpandableCard>
    )
}
