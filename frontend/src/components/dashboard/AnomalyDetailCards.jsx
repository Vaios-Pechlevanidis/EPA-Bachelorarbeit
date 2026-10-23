import { useState } from "react"
import { ArrowDownRight, ArrowUpRight, GitCompareArrows, Lightbulb, MessageSquareText, Newspaper } from "lucide-react"
import { ExpandableCard } from "./ExpandableCard"
import { AnomalyComparison } from "./AnomalyComparison"
import { ExplanationContent, ExplanationPreview } from "./ExplanationPanel"
import { EvidenceContent, EvidencePreview, ListControls } from "./EvidenceSection"
import { Headline, PreviewLabel, PreviewStatus, SentimentRows, ShiftBars, Warn } from "./CardPreview"
import { PeriodReviewList, ReviewListControls, WindowSideToggle } from "./PeriodReviews"
import { Delta } from "../ui/primitives"
import { selectionLabel } from "@/lib/anomalySeries"
import { useEvidence, useEvidenceList } from "@/hooks/useEvidence"
import { evidenceSubtitle } from "@/lib/evidenceText"
import { explanationSubtitle } from "@/lib/explanationText"
import { dimensionLabel } from "@/lib/ratingCategories"

/* ============================================================================
   AnomalyDetailCards — die vier Karten unter der Drill-down-Leiste der Seite
   "Anomalien im Verlauf" (2026-10-16): Vorher-Nachher-Vergleich, Bewertungen
   des Zeitraums, Mögliche Zusammenhänge, Externe Berichte. Wie die Kacheln und
   Karten des Haupt-Dashboards zeigt jede Karte in der Vorschau eine große
   Kennzahl und höchstens ein kleines Diagramm (CardPreview), damit man auf einen
   Blick sieht, wo die stärksten Unterschiede liegen; ein Klick öffnet die volle
   Ansicht im Dialog (ExpandableCard, 90 % der Breite, 85 % der Höhe). Schalter
   (davor / danach, Thema, Sortierung, Ereignisart) stehen nur im Dialog.
   Inhalte und Wortwahl sind unverändert: keine Aussage über Ursachen.
   Dimension als globaler Filter (2026-10-23): Mit einer Einzeldimension zeigen
   Bewertungskarte und Belegkarte nur, was zur Dimension gehört (dimension in
   ReviewsCard, dimensionOnly in EvidenceCard); die Vorschau nennt die Zählung
   vor und nach dem Filter und das Mittel der Sterne der Dimension.
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
    // Bewertungen ohne Freitext je Fenster (MR2); nur wenn in einem Fenster Text fehlt.
    const noText = (before.n_without_text ?? 0) > 0 || (after.n_without_text ?? 0) > 0
        ? ` · ohne Freitext ${before.n_without_text ?? 0} → ${after.n_without_text ?? 0}`
        : ""
    return (
        <div>
            {intro && <Warn className="mb-2">{intro}</Warn>}
            <Headline
                value={signed(rating_shift)}
                unit="Sterne"
                tone={tone}
                chip={chip}
                sub={`Ø ${num(before.mean_rating)} → ${num(after.mean_rating)} · ${before.n_reviews} → ${after.n_reviews} Bewertungen${noText}${value_shift !== undefined ? ` · Dimension ${signed(value_shift)}` : ""}`}
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
   Fenster als gestapelter Balken, damit der Unterschied davor / danach sichtbar ist.
   filterTopic: gefiltertes Thema oder null. dimension: Einzeldimension als Filter
   (2026-10-23): Zählung nur zur Dimension, Ø der Sterne der Dimension statt der Gesamtnote. */
function ReviewsPreview({ pages, comparison, side, labels, span, filterTopic, dimension = null }) {
    if (pages.loading) return <PreviewStatus spinner>Lade Bewertungen…</PreviewStatus>
    if (pages.error && !pages.items.length) return <PreviewStatus>Bewertungen konnten nicht geladen werden: {pages.error}</PreviewStatus>
    const topic = pages.highlight?.topic ?? null
    const mentions = pages.highlight?.mentions
    const scope = dimension && pages.highlight?.dimension_only ? pages.highlight : null
    const stats = comparison.data?.comparison ?? null
    const meanRating = filterTopic ? null : scope ? scope.dimension_mean ?? null : stats?.[side]?.mean_rating ?? null
    const short = shortLabels(labels)
    const sub = `${labels[side]} · ${span}${filterTopic
        ? ` · nur Bewertungen, die ${filterTopic} nennen`
        : scope
            ? ` · zur Dimension ${dimensionLabel(dimension)}, von ${scope.n_all} insgesamt`
            : topic && mentions != null ? ` · ${mentions} ${mentions === 1 ? "nennt" : "nennen"} ${topic}` : ""}`
    return (
        <div>
            <Headline
                value={pages.total}
                unit={pages.total === 1 ? "Bewertung" : "Bewertungen"}
                chip={meanRating != null ? <Delta tone={ratingTone(meanRating)}>{scope ? "Ø Dimension" : "Ø"} {num(meanRating)}</Delta> : null}
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
   des Fensters; topic = {value, onChange} für den Themenfilter (gefiltertes Thema
   oder null); order/onOrder = "desc" | "asc" (Sortierung nach Datum); dimension =
   Schlüssel der Einzeldimension, wenn sie als Filter gilt (2026-10-23), sonst null. */
export function ReviewsCard({ eyebrow, title, subtitle, pages, comparison, side, onSide, labels, window, topic, order, onOrder, listKey, emptyText, footnote, dimension = null }) {
    const span = window ? selectionLabel(window) : ""
    const withoutTopic = pages.topicCounts?.withoutTopic
    return (
        <ExpandableCard
            icon={<MessageSquareText />}
            eyebrow={eyebrow}
            title={title}
            subtitle={({ modal }) => (modal ? subtitle.full : subtitle.short)}
            basis={["stars", "text"]}
            accent="bg-slate-500"
            hint={HINT}
            actions={({ modal }) => (modal ? (
                <>
                    <WindowSideToggle value={side} onChange={onSide} labels={labels} />
                    <ReviewListControls order={order} onOrder={onOrder} topics={pages.topicCounts} value={topic.value} onTopic={topic.onChange} />
                </>
            ) : null)}
        >
            {({ modal }) => (modal ? (
                <>
                    <PeriodReviewList key={listKey} pages={pages} emptyText={emptyText} dimension={dimension} />
                    <p className="m-0 mt-3 text-[11px] text-slate-400">{footnote}</p>
                    {dimension && pages.highlight?.note && (
                        <p className="m-0 mt-1 text-[11px] text-slate-400">
                            Dimension {dimensionLabel(dimension)} als Filter: {pages.highlight.note} Je Zeile stehen die Sterne der Dimension und, wenn vorhanden, der Kommentar zur Kategorie.
                        </p>
                    )}
                    <p className="m-0 mt-1 text-[11px] text-slate-400">
                        Themen: die Schlüsselwort-Themen der Themenübersicht, erkannt an Schlüsselwörtern in Titel, Freitexten und
                        Kategorie-Kommentaren; eine Bewertung kann mehrere oder keines nennen
                        {withoutTopic != null ? ` (in diesem Zeitraum ${withoutTopic} ohne erkanntes Thema)` : ""}. Keine Textanalyse durch ein Modell.
                    </p>
                </>
            ) : (
                <ReviewsPreview pages={pages} comparison={comparison} side={side} labels={labels} span={span} filterTopic={topic.value} dimension={dimension} />
            ))}
        </ExpandableCard>
    )
}

/* ---- Mögliche Zusammenhänge ---------------------------------------------- */

/* comparison = Antwort des Vergleichs mit explanations und explanation_summary;
   subtitle = Kurzform für die Karte (im Dialog steht die vollständige Zählung). */
/* onSelectPeriod(from, to): "Zeitraum wählen" bei den allgemeinen Ereignissen im Dialog
   (Drill-down in das Ereignis, Nachtrag zu E29, 2026-10-17). */
/* userEvents: eigene Ereignisse des Unternehmens (nummeriert); die im Ereignisfenster
   stehen als Gruppe "Eigenes Ereignis" (Nachtrag zu E32, 2026-10-22). */
export function ExplanationCard({ eyebrow, subtitle, comparison, onSelectPeriod = null, userEvents = null }) {
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
                ? <ExplanationContent data={comparison.data} loading={comparison.loading} error={comparison.error} onSelectPeriod={onSelectPeriod} userEvents={userEvents} />
                : <ExplanationPreview data={comparison.data} loading={comparison.loading} error={comparison.error} userEvents={userEvents} />)}
        </ExpandableCard>
    )
}

/* ---- Externe Berichte ---------------------------------------------------- */

/* anomalyId für Veränderung oder Einzelmonat, sonst selection {from, to};
   group = {source, dimension, status} wie die Erkennung; scores und rules aus
   explanation_summary des Vergleichs (null, solange er lädt). Sortierung und
   Filter bleiben beim Wechsel der Auswahl erhalten (wie bisher). dimensionOnly:
   nur Belege zur Einzeldimension der Gruppe (2026-10-23). */
export function EvidenceCard({ eyebrow, subtitle, companyId, anomalyId = null, selection = null, group = {}, scores = null, rules = null, dimensionOnly = false }) {
    const evidence = useEvidence(companyId, { anomalyId, selection, ...group, dimensionOnly })
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
