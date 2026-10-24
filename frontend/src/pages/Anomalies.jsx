import { useEffect, useMemo, useState } from "react"
import { useLocation, useNavigate, useSearchParams } from "react-router-dom"
import { ArrowLeft, Building2, Diamond, Flag, ListOrdered, MousePointerClick } from "lucide-react"
import { Anomaly as AnomalyIcon } from "../icons"
import { CompanySearchSelect } from "@/components/CompanySearchSelect"
import { AnomalyChart, AnomalyList, AnomalySourceToggle, DimensionPicker, OutlierList, StatusHint, StatusPicker, TimeRangeFilter } from "@/components/dashboard/AnomalyCard"
import { ComparisonCard, EvidenceCard, ExplanationCard, ReviewsCard } from "@/components/dashboard/AnomalyDetailCards"
import { DataStatusBar } from "@/components/dashboard/DataStatusBar"
import { DrilldownPicker } from "@/components/dashboard/DrilldownPicker"
import { EventsToggle } from "@/components/dashboard/EvidenceSection"
import { MarketSourceNote, PriceToggle } from "@/components/dashboard/MarketContext"
import { AddUserEventButton, UserEventDialog, UserEventList } from "@/components/dashboard/UserEvents"
import { PageSection } from "@/components/dashboard/PageSection"
import { DEFAULT_TIME_RANGE, comparisonWindows, fmtPeriod, inWindow, isPeriod, isTimeRangeKey, outlierCountText, periodIndex, periodWindows, selectionLabel, timeWindow, trimToEvaluated } from "@/lib/anomalySeries"
import { DEFAULT_SOURCE, OVERALL_DIMENSION, dimensionLabel, isDimensionOf, isSource } from "@/lib/ratingCategories"
import { dimensionScopeNote, isSingleDimension, reviewScopeEmptyText, reviewScopeText } from "@/lib/dimensionScope"
import { PRICE_ON, PRICE_PARAM, noPriceText } from "@/lib/market"
import { groupLabel, statusDistinctionHint, validStatus } from "@/lib/reviewerStatus"
import { useAnomalies } from "@/hooks/useAnomalies"
import { useAnomalyComparison, usePeriodComparison } from "@/hooks/useAnomalyComparison"
import { useCompanyResource } from "@/hooks/useCompanyResource"
import { useDataStatus } from "@/hooks/useDataStatus"
import { useGlobalEvents } from "@/hooks/useEvidence"
import { useReviewPages } from "@/hooks/useReviewPages"
import { useTheme } from "@/hooks/useTheme"
import { useUserEvents } from "@/hooks/useUserEvents"
import { OUTLIER_UNVALIDATED_NOTE, SHOW_FINANCE_EXTRAS, SHOW_OUTLIER_MONTHS } from "@/config"
import { loadCompany, loadCompanyName } from "@/lib/companies"
import { USER_EVENT_NOTE } from "@/lib/userEvents"

/* ============================================================================
   Anomalies — Detailseite "Anomalien im Verlauf" (Inkrement 1).
   Geöffnet per Klick auf die AnomalyCard im Dashboard, analog zum Vergleich.
   Die Firma steht in der URL (?company=ID), damit Neuladen und Teilen
   funktionieren; der Name kommt aus dem Navigationszustand oder /companies.
   Dimension und Zeitraum stehen ebenfalls in der URL (?dimension=key&range=1y),
   seit Inkrement 2 auch Quelle und Status (?source=candidates&status=eingestellt).
   Der Zeitraum wählt nur den Ausschnitt; erkannt wird auf der ganzen Reihe.
   Inkrement 2: Ein Klick auf eine Stufe oder Listenzeile wählt die Veränderung
   aus (?anomaly=id); darunter stehen der Vorher-Nachher-Vergleich und die
   Bewertungen der Vergleichsfenster. Auffällige Einzelmonate (E14) stehen in
   einer eigenen Liste. Freier Drill-down (E17): Klick auf einen beliebigen
   Monat, Ziehen über einen Zeitraum oder das Auswahlfeld setzt ?from=&to=
   (YYYY-MM; das ältere ?month= gilt als from = to); darunter stehen der
   Vergleich mit dem Zeitraum davor und die Bewertungen der Auswahl, auch wenn
   die Reihe keine erkannte Veränderung hat.
   Aktienkurs (Inkrement 3, E15, Nachtrag 2026-10-05): Hat die Firma einen
   Ticker, blendet das Kästchen "Aktienkurs" im Kopf des Monatsverlaufs den
   Kurs auf einer zweiten Achse ein (?kurs=an, Standard aus). Erst dann wird
   /market geladen; unter dem Diagramm stehen dann der feste Hinweis und bei
   der Konzernmutter der Vermerk. Der Link zum Aktien-Dashboard (/aktie, E16)
   bleibt in jedem Fall.
   Externe Berichte (Inkrement 4, E18): Unter dem Vergleich steht für die
   ausgewählte Veränderung, den Einzelmonat oder die freie Auswahl der Abschnitt
   "Externe Berichte im Ereignisfenster" (EvidenceSection): zeitlich nahe
   Meldungen aus externen Quellen, keine Aussage über Ursachen. Das Kästchen
   "Allgemeine Ereignisse" (?ereignisse=an, Standard aus) blendet die automatisch
   aus Wirtschaftsdaten ermittelten allgemeinen Ereignisse (E29) als Flächen in den Monatsverlauf ein, beschriftet als
   "Allgemeines Ereignis, Hypothese".
   Erklärungsansätze (Inkrement 5): Über der Belegliste steht der Abschnitt
   "Mögliche Zusammenhänge" (ExplanationPanel) mit den Erklärungsansätzen aus
   der Antwort des Vergleichs (explanations, explanation_summary); die
   Belegliste erhält daraus Stufe und Ereignisart je Beleg, eine Umschaltung
   der Sortierung (Datum, Relevanz) und einen Filter nach Ereignisart.
   Kennzeichnung (2026-10-13, E30): Einzelmonate tragen den Zusatz "ungeprüft";
   der Hinweis zum Prüfumfang unter dem Verlauf wurde am 2026-10-24 entfernt (E25). Mit VITE_SHOW_OUTLIER_MONTHS=false (config.js) gibt es keine
   Einzelmonate: keine Liste, kein Umschalter, ?liste=einzelmonate zeigt die
   Veränderungen, ein Monat aus ?from=&to= ist eine freie Auswahl.
   Vorschau-Karten (2026-10-16): Vergleich, Bewertungen, Erklärungsansätze und
   externe Berichte stehen in einer Reihe aus vier Karten wie im
   Haupt-Dashboard (AnomalyDetailCards): auf der Karte die wichtigsten
   Erkenntnisse als Stichpunkte, ein Klick öffnet die volle Ansicht im Dialog.
   Dieselben Karten gelten für die Veränderung, die freie Auswahl und den
   Einzelmonat; nur Bezeichnungen, Fenster und Datenquelle unterscheiden sich.
   Eigene Ereignisse (2026-10-17, E32): "Ereignis eintragen" im Kopf des
   Monatsverlaufs öffnet ein Formular (Titel, von, bis, Vermerk); die Einträge
   liegen je Unternehmen in der Datenbank (useUserEvents) und erscheinen als
   nummerierte Marken im Verlauf und als dritte Liste der Karte "Markierungen"
   (?liste=ereignisse). Klick auf Marke oder Zeile wählt den Zeitraum als
   freie Auswahl (?from=&to=); der Stift in der Zeile ändert oder löscht.
   Keine Aussage über Ursachen, kein Eingang in Erkennung oder Erklärungen.
   Dimension als globaler Filter (2026-10-23): Die im Kopf gewählte Dimension
   (?dimension=) gilt für alle Karten der Seite. Bei einer Einzeldimension zeigt
   "Bewertungen des Zeitraums" nur Bewertungen, die zur Dimension gehören
   (Kommentar zur Kategorie oder Schlüsselwort ihres Themas; je Zeile die Sterne
   der Dimension und der Kommentar), und "Externe Berichte" nur Meldungen mit
   Schlüsselwort im Titel oder zugeordneter Ereignisart (dimension_only in
   useReviewPages und useEvidence, Regeln in backend/services/dimension_scope.py).
   Ein Hinweis unter dem Verlauf nennt das; "Gesamtbewertung" zeigt wieder alles.
   Zurück zum Dashboard nimmt Quelle, Dimension und Status mit (AnomalyCard).
   Drill-down aus dem Vergleich (2026-10-23): Im Dialog des Vorher-Nachher-
   Vergleichs ist jede Themenzeile anklickbar; der Klick schließt den Dialog,
   wechselt die Seite zur Dimension des Themas (global, siehe oben) und behält
   den Zeitraum des Fensters (ab dem markierten Monat, über den Anteil davor das
   Fenster davor) als freie Auswahl ?from=&to=; dann öffnet sich die
   Bewertungsliste (openCard, ExpandableCard mit open/onOpenChange). Themen ohne
   Dimension setzen stattdessen den Themenfilter ?thema=<Thema>.
   ============================================================================ */

export default function AnomaliesPage() {
    const location = useLocation()
    const navigate = useNavigate()
    const [searchParams, setSearchParams] = useSearchParams()
    useTheme() // gespeichertes Theme auch beim direkten Öffnen der Seite anwenden

    const companyId = searchParams.get("company") || (location.state?.company?.id != null ? String(location.state.company.id) : null)
    const [names, setNames] = useState(() =>
        location.state?.company?.id != null ? { [String(location.state.company.id)]: location.state.company.name ?? "" } : {},
    )
    const [query, setQuery] = useState(location.state?.company?.name ?? "")
    const companyName = companyId ? names[companyId] ?? "" : ""
    const sourceParam = searchParams.get("source")
    const source = isSource(sourceParam) ? sourceParam : DEFAULT_SOURCE
    const status = validStatus(source, searchParams.get("status"))
    const group = groupLabel(source, status)
    const dimensionParam = searchParams.get("dimension")
    const dimension = isDimensionOf(source, dimensionParam) ? dimensionParam : OVERALL_DIMENSION.key
    // Einzeldimension: Bewertungsliste und Belegliste nur zur Dimension (2026-10-23).
    const singleDimension = isSingleDimension(dimension)
    const rangeParam = searchParams.get("range")
    const rangeKey = isTimeRangeKey(rangeParam) ? rangeParam : DEFAULT_TIME_RANGE

    // Suchparameter ändern, ohne die übrigen (Firma, Dimension) zu verlieren.
    const updateParams = (patch) => {
        const next = new URLSearchParams(searchParams)
        Object.entries(patch).forEach(([k, v]) => (v == null ? next.delete(k) : next.set(k, v)))
        setSearchParams(next)
    }

    // Firma aus dem Navigationszustand in die URL übernehmen (Neuladen, Teilen).
    useEffect(() => {
        if (companyId && !searchParams.get("company")) {
            const next = new URLSearchParams(searchParams)
            next.set("company", companyId)
            setSearchParams(next, { replace: true })
        }
    }, [companyId, searchParams, setSearchParams])

    // Namen nachladen, wenn die Seite direkt über die URL geöffnet wurde
    // (gemeinsame Firmenliste, lib/companies.js).
    useEffect(() => {
        if (!companyId || names[companyId]) return undefined
        let active = true
        loadCompanyName(companyId)
            .then((name) => {
                if (active && name) {
                    setNames((n) => ({ ...n, [companyId]: name }))
                    setQuery(name)
                }
            })
            .catch(() => {})
        return () => { active = false }
    }, [companyId, names])

    // Ticker aus der gemeinsamen Firmenliste: Nur mit Ticker gibt es das Kästchen
    // "Aktienkurs". null = kein Ticker oder Firma unbekannt.
    const [tickers, setTickers] = useState({})
    useEffect(() => {
        if (!companyId || companyId in tickers) return undefined
        let active = true
        loadCompany(companyId)
            .then((company) => {
                if (active) setTickers((t) => ({ ...t, [companyId]: company?.ticker || null }))
            })
            .catch(() => {})
        return () => { active = false }
    }, [companyId, tickers])
    const hasTicker = Boolean(companyId && tickers[companyId])
    // Kurs als Einordnung (E15): Standard aus; /market wird erst geladen, wenn er an ist.
    const showPrice = hasTicker && searchParams.get(PRICE_PARAM) === PRICE_ON
    const market = useCompanyResource(showPrice ? companyId : null, "market")
    const marketData = market.data?.available ? market.data : null
    // Allgemeine Ereignisse als Overlay (Inkrement 4, E20): Standard aus, Zustand in der URL.
    const showEvents = searchParams.get("ereignisse") === "an"
    const globalEvents = useGlobalEvents(showEvents)
    // Eigene Ereignisse des Unternehmens (E32), mit Nummer nach Beginn wie im Diagramm.
    const userEvents = useUserEvents(companyId)
    const numberedUserEvents = useMemo(() => userEvents.events.map((e, i) => ({ ...e, number: i + 1 })), [userEvents.events])
    // Formular: null = zu, sonst {event: bestehender Eintrag | null, initial: {from, to} | null}
    const [eventDialog, setEventDialog] = useState(null)

    const { data, anomalies, loading, error } = useAnomalies(companyId, { source, dimension, status })
    // Datenstand: n je Statusgruppe und Hinweis, wenn aktuell/ehemalig nicht unterschieden wird (A4, E13)
    const dataStatus = useDataStatus(companyId)
    const sourceStatus = dataStatus.data?.sources?.[source] ?? null
    const statusHint = statusDistinctionHint(source, sourceStatus)
    const selectedId = searchParams.get("anomaly")
    const selectedAnomaly = useMemo(() => anomalies.find((a) => a.id === selectedId) ?? null, [anomalies, selectedId])
    const windows = useMemo(() => comparisonWindows(selectedAnomaly), [selectedAnomaly])
    // Fenster der Bewertungsliste; beim Wechsel der Veränderung wieder "ab dem
    // markierten Monat", passend zu "von / bis" der Drill-down-Leiste und zur
    // freien Auswahl. "davor" zeigt die älteren Bewertungen nur auf Wunsch.
    const [sideState, setSideState] = useState({ id: null, side: "after" })
    const side = sideState.id === selectedId ? sideState.side : "after"
    const sideWindow = windows?.[side] ?? null
    // Auffällige Einzelmonate (E14); ohne SHOW_OUTLIER_MONTHS keine, ein Monat ist dann freie Auswahl.
    const outliers = useMemo(() => (SHOW_OUTLIER_MONTHS ? data?.outlier_months ?? [] : []), [data])
    // Freie Auswahl (E17): ?from=&to=, ?month= als ein Monat; nur ohne ausgewählte Veränderung.
    const fromParam = searchParams.get("from") ?? searchParams.get("month")
    const toParam = searchParams.get("to") ?? searchParams.get("month")
    const selection = useMemo(() => {
        if (selectedAnomaly || !isPeriod(fromParam) || !isPeriod(toParam)) return null
        const [a, b] = [fromParam, toParam].sort((x, y) => periodIndex(x) - periodIndex(y))
        return { from: a, to: b }
    }, [selectedAnomaly, fromParam, toParam])
    const selectionKey = selection ? `${selection.from}_${selection.to}` : null
    const selectionWindows = useMemo(() => (selection ? periodWindows(selection.from, selection.to) : null), [selection])
    const selectedOutlier = selection && selection.from === selection.to ? outliers.find((o) => o.date === selection.from) ?? null : null
    // Fenster der Bewertungsliste der Auswahl; Standard ist die Auswahl selbst.
    const [periodSideState, setPeriodSideState] = useState({ key: null, side: "after" })
    const periodSide = periodSideState.key === selectionKey ? periodSideState.side : "after"
    const reviewSpan = selectedAnomaly ? sideWindow : selectionWindows?.[periodSide] ?? null
    // Themenfilter der Bewertungsliste (?thema=<Thema>, Auswahl im Dialog der Karte,
    // Nachtrag 2026-10-18). Das ältere ?thema=nur heißt weiter "nur das Thema der
    // gewählten Dimension" (nur bei Einzeldimension).
    const themaParam = searchParams.get("thema")
    const topicOnly = dimension !== OVERALL_DIMENSION.key && themaParam === "nur"
    const topicParam = themaParam && themaParam !== "nur" ? themaParam : null
    // Sortierung nach dem Tag, an dem die Bewertung geschrieben wurde (?sortierung=aelteste).
    const reviewOrder = searchParams.get("sortierung") === "aelteste" ? "asc" : "desc"
    const reviewPages = useReviewPages(companyId, {
        source, status, start: reviewSpan?.start, end: reviewSpan?.end,
        dimension: dimension === OVERALL_DIMENSION.key ? null : dimension,
        dimensionOnly: singleDimension, topicOnly, topic: topicParam, order: reviewOrder,
    })
    const filterTopic = topicParam ?? (topicOnly ? reviewPages.highlight?.topic ?? null : null)
    const topicFilter = { value: filterTopic, onChange: (name) => updateParams({ thema: name }) }
    const setReviewOrder = (key) => updateParams({ sortierung: key === "asc" ? "aelteste" : null })
    // " · davon 12 nennen Image" bzw. ", die Gehalt & Sozialleistungen nennen" für die Untertitel.
    const mentionText = filterTopic
        ? `, die ${filterTopic} nennen`
        : reviewPages.highlight?.topic && reviewPages.highlight.mentions != null
            ? ` · davon ${reviewPages.highlight.mentions} ${reviewPages.highlight.mentions === 1 ? "nennt" : "nennen"} ${reviewPages.highlight.topic}`
            : ""
    const topicEmptyText = filterTopic
        ? `Keine Bewertung dieses Zeitraums nennt das Thema ${filterTopic}.`
        : singleDimension ? reviewScopeEmptyText(dimension) : null
    // Zählung mit Dimension als Filter: "12 von 40 Bewertungen zur Dimension Image" statt "12 Bewertungen".
    const scopeText = reviewScopeText(reviewPages.highlight, dimension)
    const reviewCountText = scopeText && !filterTopic
        ? scopeText
        : `${reviewPages.total} ${reviewPages.total === 1 ? "Bewertung" : "Bewertungen"}${mentionText}`
    const comparison = useAnomalyComparison(companyId, selectedAnomaly?.id, { source, dimension, status })
    const periodComparison = usePeriodComparison(companyId, selection, { source, dimension, status })
    // Untertitel der Bewertungskarte: kurz auf der Karte, mit Zeitraum und Anzahl im Dialog.
    const reviewsSubtitle = (sideLabel, span) => ({
        short: `${group} · ${sideLabel}`,
        full: `${group} · ${sideLabel} · ${span}${reviewPages.loading || reviewPages.error ? "" : ` · ${reviewCountText}`}`,
    })
    // Die vier Karten zur Auswahl (2026-10-16): dieselben Bausteine für eine
    // ausgewählte Veränderung und für die freie Auswahl bzw. den Einzelmonat.
    const detail = selectedAnomaly && windows
        ? {
            tag: `VERÄNDERUNG AB ${fmtPeriod(selectedAnomaly.date).toUpperCase()}`,
            labels: { before: "davor", after: "ab dem markierten Monat" },
            comparison,
            comparisonTitle: "Vorher-Nachher-Vergleich",
            comparisonSubtitle: {
                short: group,
                full: comparison.data
                    ? `${group} · davor ${selectionLabel(comparison.data.windows.before)}: ${comparison.data.windows.before.n_reviews} · ab dem markierten Monat ${selectionLabel(comparison.data.windows.after)}: ${comparison.data.windows.after.n_reviews} Bewertungen`
                    : `${group} · Verschiebungen in den Bewertungen zwischen den Vergleichsfenstern`,
            },
            intro: null,
            introText: null,
            reviewsTitle: "Bewertungen des Zeitraums",
            reviewsEyebrow: "EINZELBEWERTUNGEN",
            reviewsSubtitle: reviewsSubtitle(side === "before" ? "davor" : "ab dem markierten Monat", selectionLabel(sideWindow)),
            side,
            onSide: (key) => setSideState({ id: selectedId, side: key }),
            window: sideWindow,
            listKey: `${selectedId}:${side}:${themaParam ?? ""}:${reviewOrder}`,
            emptyText: topicEmptyText ?? undefined,
            footnote: `Vergleichsfenster: bis zu ${windows.windowMonths} Kalendermonate vor dem markierten Monat und ab ihm, begrenzt durch die benachbarten Veränderungen; alle Bewertungen dieser Monate.`,
            evidence: { anomalyId: selectedAnomaly.id, selection: null },
        }
        : selection && selectionWindows
            ? {
                tag: `${selectedOutlier ? "EINZELMONAT" : "AUSWAHL"} ${selectionLabel(selection).toUpperCase()}`,
                labels: { before: "Zeitraum davor", after: "Auswahl" },
                comparison: periodComparison,
                comparisonTitle: "Vergleich mit dem Zeitraum davor",
                comparisonSubtitle: {
                    short: group,
                    full: periodComparison.data
                        ? `${group} · Zeitraum davor ${selectionLabel(periodComparison.data.windows.before)}: ${periodComparison.data.windows.before.n_reviews} · Auswahl ${selectionLabel(periodComparison.data.windows.after)}: ${periodComparison.data.windows.after.n_reviews} Bewertungen`
                        : `${group} · Auswahl gegen den gleich langen Zeitraum davor (mindestens ${selectionWindows.windowMonths} Monate)`,
                },
                intro: selectedOutlier
                    ? `Einzelmonat: ${String(selectedOutlier.deviation).replace(".", ",")} Sterne Abweichung von den Nachbarmonaten · ungeprüft`
                    : null,
                introText: selectedOutlier
                    ? `Auffälliger Einzelmonat: ${fmtPeriod(selectedOutlier.date)} weicht um ${String(selectedOutlier.deviation).replace(".", ",")} Sterne vom Niveau seiner Nachbarmonate ab. Das ist ein Hinweis auf einen auffälligen Monat, keine Aussage über Ursachen. ${OUTLIER_UNVALIDATED_NOTE}.`
                    : null,
                reviewsTitle: "Bewertungen der Auswahl",
                reviewsEyebrow: "EINZELBEWERTUNGEN",
                reviewsSubtitle: reviewsSubtitle(periodSide === "before" ? "Zeitraum davor" : "Auswahl", selectionLabel(reviewSpan)),
                side: periodSide,
                onSide: (key) => setPeriodSideState({ key: selectionKey, side: key }),
                window: reviewSpan,
                listKey: `${selectionKey}:${periodSide}:${themaParam ?? ""}:${reviewOrder}`,
                emptyText: topicEmptyText ?? "Keine Bewertungen in diesem Zeitraum.",
                footnote: "Alle Bewertungen der gewählten Kalendermonate. Vergleichszeitraum: die gleich vielen Monate direkt davor, mindestens 6 (vorläufig).",
                evidence: { anomalyId: selectedOutlier?.id ?? null, selection: selectedOutlier ? null : selection },
            }
            : null
    // Dialoge der Karten Vergleich und Bewertungen von der Seite aus (2026-10-23): Ein Klick
    // auf eine Themenzeile im Vergleich schließt dessen Dialog und öffnet die Bewertungen,
    // die das Thema nennen, im gewählten Fenster.
    const [openCard, setOpenCard] = useState(null) // "comparison" | "reviews" | null
    const drillToTopic = (topicName, sideKey, dimensionKey = null) => {
        const spans = selectedAnomaly ? windows : selectionWindows
        const win = spans?.[sideKey] ?? null
        // Thema mit eigener Dimension (jede Kununu-Kategorie): Die Seite wechselt zu dieser
        // Dimension, der Zeitraum des angeklickten Fensters bleibt als Auswahl; Bewertungen und
        // Belege gelten dann für die Dimension (Doku 20), ein Themenfilter ist nicht mehr nötig.
        if (dimensionKey && isDimensionOf(source, dimensionKey) && win) {
            if (dimensionKey !== dimension) {
                updateParams({ dimension: dimensionKey, anomaly: null, month: null, from: win.from, to: win.to, thema: null })
                setPeriodSideState({ key: `${win.from}_${win.to}`, side: "after" })
            } else {
                detail?.onSide(sideKey)
                updateParams({ thema: null })
            }
            setOpenCard("reviews")
            return
        }
        detail?.onSide(sideKey)
        updateParams({ thema: topicName })
        setOpenCard("reviews")
    }
    // Filtermarke im Dialogkopf: Dimension abwählen (Gesamtbewertung); eine markierte
    // Veränderung gehört zur Reihe der Dimension, ihr aktuelles Fenster bleibt als Auswahl.
    const clearDimension = () => {
        const win = selectedAnomaly ? windows?.[side] ?? null : null
        if (win) {
            updateParams({ dimension: null, anomaly: null, month: null, from: win.from, to: win.to, thema: null })
            setPeriodSideState({ key: `${win.from}_${win.to}`, side: "after" })
        } else {
            updateParams({ dimension: null, anomaly: null, thema: null })
        }
    }
    // Karte "Markierungen": Veränderungen, Einzelmonate (?liste=einzelmonate, nur mit
    // SHOW_OUTLIER_MONTHS) oder eigene Ereignisse (?liste=ereignisse, E32).
    const listParam = searchParams.get("liste")
    const markerTab = listParam === "ereignisse" ? "events" : SHOW_OUTLIER_MONTHS && listParam === "einzelmonate" ? "outliers" : "changes"
    const setMarkerTab = (key) => updateParams({ liste: key === "outliers" ? "einzelmonate" : key === "events" ? "ereignisse" : null })
    // Der Themenfilter der Bewertungsliste (?thema=) gehört zur aktuellen Auswahl: Er wird
    // zurückgesetzt, sobald Auswahl, Dimension, Status oder Firma wechseln (2026-10-23, Rückmeldung
    // des Autors: alter Filter blieb nach dem Wechsel der Dimension stehen). Beim Wechsel
    // davor / danach und der Sortierung bleibt er.
    const selectAnomaly = (id) => updateParams({ anomaly: id, month: null, from: null, to: null, thema: null })
    const selectPeriod = (from, to) => updateParams({ from, to, month: null, anomaly: null, thema: null })
    const selectOutlier = (period) => selectPeriod(period, period)
    const clearSelection = () => updateParams({ anomaly: null, month: null, from: null, to: null, thema: null })
    // Eigenes Ereignis (E32): Zeitraum als freie Auswahl, Liste "Eigene Ereignisse" aufklappen.
    const selectUserEvent = (e) => updateParams({ from: e.date_from, to: e.date_to, month: null, anomaly: null, liste: "ereignisse", thema: null })
    // Formular öffnen: neu mit der aktuellen Auswahl bzw. dem Monat der Veränderung als Vorbelegung.
    const openNewUserEvent = () => setEventDialog({
        event: null,
        initial: selection ?? (selectedAnomaly ? { from: selectedAnomaly.date, to: selectedAnomaly.date } : null),
    })
    const openEditUserEvent = (e) => setEventDialog({ event: e, initial: null })
    // Löschen aus der Zeile (Papierkorb mit Rückfrage); war der Zeitraum ausgewählt, Auswahl aufheben.
    const deleteUserEvent = async (e) => {
        await userEvents.remove(e.id)
        if (selection && selection.from === e.date_from && selection.to === e.date_to) clearSelection()
    }
    const saveUserEvent = async (payload) => {
        if (eventDialog?.event) {
            await userEvents.update(eventDialog.event.id, payload)
        } else {
            const created = await userEvents.add(payload)
            selectUserEvent(created)
        }
    }
    // Monate der Reihe für das Auswahlfeld (erster bis letzter Monat mit datierter Bewertung).
    const seriesMonths = useMemo(() => (data?.series ?? []).map((m) => m.period), [data])
    // Bewertungen je Monat für das Monatsraster des Auswahlfelds.
    const monthCounts = useMemo(() => Object.fromEntries((data?.series ?? []).map((m) => [m.period, m.count ?? 0])), [data])
    const eligibility = data?.eligibility
    const count = anomalies.length
    // Sichtbares Fenster relativ zum letzten angezeigten (bewerteten) Monat; null = alles.
    const range = useMemo(() => timeWindow(trimToEvaluated(data?.series).series, rangeKey), [data, rangeKey])
    const visibleAnomalies = useMemo(() => anomalies.filter((a) => inWindow(a.date, range)), [anomalies, range])
    const hiddenCount = count - visibleAnomalies.length
    const visibleOutliers = useMemo(() => outliers.filter((o) => inWindow(o.date, range)), [outliers, range])
    // Eigene Ereignisse, die den sichtbaren Ausschnitt berühren (Nummern bleiben die der ganzen Liste).
    const visibleUserEvents = useMemo(
        () => (range ? numberedUserEvents.filter((e) => periodIndex(e.date_to) >= periodIndex(range.from) && periodIndex(e.date_from) <= periodIndex(range.to)) : numberedUserEvents),
        [numberedUserEvents, range],
    )
    const hiddenUserEvents = numberedUserEvents.length - visibleUserEvents.length
    const countText = `${count} ${count === 1 ? "auffällige Veränderung" : "auffällige Veränderungen"}`
    // Im Fehlerfall und beim Laden kein Zähler: "0" wäre dort eine falsche Aussage.
    const chartSubtitle = error || loading
        ? group
        : eligibility && !eligibility.eligible
        ? `${group} · keine automatische Erkennung`
        : range
            ? `${group} · ${fmtPeriod(range.from)} – ${fmtPeriod(range.to)} · ${count
                ? `${visibleAnomalies.length} von ${count} ${count === 1 ? "auffälligen Veränderung" : "auffälligen Veränderungen"} im Zeitraum`
                : "keine auffälligen Veränderungen"}${outlierCountText(visibleOutliers.length)}`
            : `${group} · ${countText}${outlierCountText(outliers.length)}`

    // Zurück mit der gewählten Firma, damit das Dashboard sie wieder anzeigt; Quelle,
    // Dimension und Status gehen mit, damit die Anomalien-Karte dort dieselbe Reihe zeigt.
    const backToDashboard = () =>
        navigate("/dashboard", companyId ? { state: { companyId, companyName, anomalySelection: { source, dimension, status } } } : undefined)

    const selectCompany = (company) => {
        if (!company) return
        const id = String(company.id)
        setNames((n) => ({ ...n, [id]: company.name }))
        setQuery(company.name)
        updateParams({ company: id, anomaly: null, month: null, from: null, to: null, thema: null })
    }

    return (
        <div className="min-h-screen bg-slate-50 flex flex-col">
            {/* Topbar — wie im Vergleich */}
            <div className="min-h-[48px] py-1.5 border-b border-slate-200 bg-white flex flex-wrap items-center px-5 gap-x-3 gap-y-1.5 sticky top-0 z-30 flex-shrink-0">
                <button
                    onClick={backToDashboard}
                    title="Zurück zum Dashboard"
                    className="h-7 w-7 rounded-md grid place-items-center text-slate-500 hover:bg-slate-100 hover:text-slate-900 [&_svg]:w-3.5 [&_svg]:h-3.5"
                >
                    <ArrowLeft />
                </button>
                <div className="h-5 w-px bg-slate-200" />
                <div className="flex items-center gap-2.5 min-w-[180px] flex-1">
                    <span className="w-7 h-7 rounded-md grid place-items-center flex-none bg-slate-100 text-slate-600 [&_svg]:w-[14px] [&_svg]:h-[14px]">
                        <AnomalyIcon />
                    </span>
                    <div className="min-w-0">
                        <p className="m-0 mb-0.5 font-mono text-[10px] tracking-[0.06em] uppercase text-slate-500 leading-none">
                            ANALYSE · ANOMALIEN IM VERLAUF
                        </p>
                        <p className="m-0 text-[14px] leading-5 font-semibold tracking-tight text-slate-900 truncate">
                            {companyName ? `Anomalien · ${companyName}` : "Anomalien"}
                        </p>
                    </div>
                </div>
                {companyId && (
                    <AnomalySourceToggle
                        value={source}
                        onChange={(key) => updateParams({
                            source: key === DEFAULT_SOURCE ? null : key,
                            status: null,
                            dimension: isDimensionOf(key, dimension) && dimension !== OVERALL_DIMENSION.key ? dimension : null,
                            // Themen gehören zur Quelle (Bewerbende haben andere)
                            anomaly: null, month: null, thema: null,
                        })}
                    />
                )}
                {companyId && (
                    <StatusPicker
                        source={source}
                        value={status}
                        onChange={(key) => updateParams({ status: key, anomaly: null, thema: null })}
                        counts={sourceStatus?.status_counts ?? null}
                        hint={statusHint}
                    />
                )}
                {companyId && (
                    <DimensionPicker
                        source={source}
                        value={dimension}
                        onChange={(key) => updateParams({ dimension: key === OVERALL_DIMENSION.key ? null : key, anomaly: null, thema: null })}
                    />
                )}
                <div className="w-[260px] max-w-full flex-none">
                    <CompanySearchSelect
                        value={query}
                        onValueChange={setQuery}
                        onCompanySelect={selectCompany}
                        onCreateNew={null}
                        variant="light"
                        compact
                        placeholder="Firma wechseln…"
                    />
                </div>
            </div>

            <div className="flex-1 px-5 py-3 max-w-[1600px] w-full mx-auto space-y-3">
                {!companyId ? (
                    <PageSection icon={<Building2 />} eyebrow="AUSWAHL" title="Firma wählen">
                        <p className="m-0 text-[13px] text-slate-500">Oben rechts eine Firma suchen, um ihren Verlauf zu sehen.</p>
                    </PageSection>
                ) : (
                    <>
                        {/* Datenstand (Inkrement 6, FA-37) */}
                        <DataStatusBar companyId={companyId} />

                        {/* Verlauf (zwei Drittel) und Markierungen (ein Drittel) */}
                        <div className="grid gap-3 xl:grid-cols-3">
                            <PageSection
                                className="xl:col-span-2"
                                icon={<AnomalyIcon />}
                                eyebrow="VERLAUF · AUFFÄLLIGE VERÄNDERUNGEN"
                                title={`Monatsverlauf · ${dimensionLabel(dimension)}`}
                                subtitle={chartSubtitle}
                                basis={[
                                    "stars",
                                    ...(showPrice && marketData ? ["market"] : []),
                                    ...(showEvents && globalEvents.events.length ? ["external"] : []),
                                ]}
                                actions={
                                    <>
                                        <AddUserEventButton onClick={openNewUserEvent} disabled={Boolean(error) || !seriesMonths.length} />
                                        <EventsToggle
                                            checked={showEvents}
                                            onChange={(on) => updateParams({ ereignisse: on ? "an" : null })}
                                        />
                                        {hasTicker && (
                                            <PriceToggle
                                                checked={showPrice}
                                                onChange={(on) => updateParams({ [PRICE_PARAM]: on ? PRICE_ON : null })}
                                            />
                                        )}
                                        <TimeRangeFilter
                                            value={rangeKey}
                                            onChange={(key) => updateParams({ range: key === DEFAULT_TIME_RANGE ? null : key })}
                                        />
                                    </>
                                }
                                bodyClassName="px-4 pt-3 pb-3"
                            >
                                <AnomalyChart
                                    data={data}
                                    anomalies={anomalies}
                                    loading={loading}
                                    error={error}
                                    height={340}
                                    range={range}
                                    showLevels
                                    selectedId={selectedId}
                                    onSelect={selectAnomaly}
                                    selectedOutlier={selectedOutlier?.date ?? null}
                                    onSelectOutlier={selectOutlier}
                                    selection={selection}
                                    onSelectPeriod={selectPeriod}
                                    market={showPrice ? marketData : null}
                                    events={showEvents ? globalEvents.events : null}
                                    userEvents={numberedUserEvents}
                                    onSelectUserEvent={selectUserEvent}
                                />
                                <div className="mt-2 pt-2 border-t border-slate-100 space-y-1">
                                    <StatusHint hint={statusHint} />
                                    {singleDimension && (
                                        <p className="m-0 text-[11px] text-slate-500">{dimensionScopeNote(dimension)}</p>
                                    )}
                                    {showEvents && !globalEvents.loading && !globalEvents.error && globalEvents.events.length === 0 && (
                                        <p className="m-0 text-[11px] text-slate-500">
                                            Keine allgemeinen Ereignisse: Die Wirtschaftsdaten (Eurostat) liegen nicht vor oder zeigen keinen Konjunktureinbruch und keinen Inflationsschub.
                                        </p>
                                    )}
                                    {showEvents && globalEvents.error && (
                                        <p className="m-0 text-[11px] text-slate-500">Allgemeine Ereignisse konnten nicht geladen werden: {globalEvents.error}</p>
                                    )}
                                    {/* Eingeblendeter Kurs: fester Hinweis, Wertpapier (Konzernmutter oder Konzerngesellschaft ausdrücklich), Quelle */}
                                    {showPrice && (market.loading ? (
                                        <p className="m-0 text-[11px] text-slate-500">Lade Aktienkurs…</p>
                                    ) : market.error ? (
                                        <p className="m-0 text-[11px] text-slate-500">Aktienkurs konnte nicht geladen werden: {market.error}</p>
                                    ) : marketData ? (
                                        <MarketSourceNote market={marketData} companyName={companyName} subject="Kurs" />
                                    ) : (
                                        <p className="m-0 text-[11px] text-slate-500">{noPriceText(market.data?.reason)}</p>
                                    ))}
                                    <p className="m-0 text-[11px] text-slate-500">
                                        {SHOW_FINANCE_EXTRAS ? "Aktienkurs, Kennzahlen und Nachrichten" : "Aktienkurs und Kennzahlen"} stehen im{" "}
                                        <button
                                            type="button"
                                            className="underline underline-offset-2 text-slate-700 hover:text-slate-900"
                                            onClick={() => navigate(`/aktie?company=${companyId}`, { state: { company: { id: companyId, name: companyName } } })}
                                        >
                                            Aktien-Dashboard
                                        </button>
                                        , dort auch zusammen mit diesem Bewertungsverlauf.
                                    </p>
                                </div>
                            </PageSection>

                            <PageSection
                                className="flex flex-col"
                                icon={markerTab === "outliers" ? <Diamond /> : markerTab === "events" ? <Flag /> : <ListOrdered />}
                                eyebrow={range ? `MARKIERUNGEN · ${fmtPeriod(range.from).toUpperCase()} – ${fmtPeriod(range.to).toUpperCase()}` : "MARKIERUNGEN"}
                                basis={markerTab === "events" ? null : "stars"}
                                title={markerTab === "outliers" ? "Auffällige Einzelmonate" : markerTab === "events" ? "Eigene Ereignisse" : "Auffällige Veränderungen"}
                                subtitle={markerTab === "outliers"
                                    ? "Starke Abweichung von den Nachbarmonaten, kein neues Niveau; größte zuerst"
                                    : markerTab === "events"
                                        ? "Von Nutzerinnen und Nutzern eingetragene Zeiträume zur Einordnung; nach Beginn sortiert"
                                        : "Niveauwechsel; Abfälle zuerst, innerhalb nach Größe"}
                                bodyClassName="px-4 pt-2 pb-3 flex-1 min-h-0 flex flex-col"
                            >
                                {!loading && !error && data && (
                                    <div className="ds-time-filter self-start mb-2" role="group" aria-label="Markierungen">
                                        {[
                                            { key: "changes", label: `Veränderungen (${eligibility?.eligible ? visibleAnomalies.length : "–"})` },
                                            ...(eligibility?.eligible && SHOW_OUTLIER_MONTHS ? [{ key: "outliers", label: `Einzelmonate (${visibleOutliers.length})` }] : []),
                                            { key: "events", label: `Eigene Ereignisse (${userEvents.error ? "–" : visibleUserEvents.length})` },
                                        ].map((t) => (
                                            <button key={t.key} type="button" aria-pressed={markerTab === t.key}
                                                className={`ds-time-btn${markerTab === t.key ? " active" : ""}`} onClick={() => setMarkerTab(t.key)}>
                                                {t.label}
                                            </button>
                                        ))}
                                    </div>
                                )}
                                {/* Eigener Scrollbereich: ab xl so hoch wie der Verlauf daneben */}
                                <div className="relative flex-1 min-h-0">
                                    <div className="max-h-[360px] xl:max-h-none xl:absolute xl:inset-0 overflow-y-auto overscroll-contain pr-1">
                                        {loading ? (
                                            <p className="m-0 text-[12px] text-slate-500">Lade Markierungen…</p>
                                        ) : error ? (
                                            <p className="m-0 text-[12px] text-slate-500">Keine Markierungen: {error}</p>
                                        ) : markerTab === "events" ? (
                                            userEvents.loading ? (
                                                <p className="m-0 text-[12px] text-slate-500">Lade eigene Ereignisse…</p>
                                            ) : userEvents.error ? (
                                                <p className="m-0 text-[12px] text-slate-500">Eigene Ereignisse konnten nicht geladen werden: {userEvents.error}</p>
                                            ) : (
                                                <UserEventList
                                                    events={visibleUserEvents}
                                                    selection={selection}
                                                    onSelect={selectUserEvent}
                                                    onEdit={openEditUserEvent}
                                                    onDelete={deleteUserEvent}
                                                    emptyText={range && numberedUserEvents.length
                                                        ? "Im gewählten Zeitraum keine eigenen Ereignisse."
                                                        : "Noch keine eigenen Ereignisse. „Ereignis eintragen“ legt einen Zeitraum mit Titel an, z. B. einen Führungswechsel; die Marke erscheint im Verlauf."}
                                                />
                                            )
                                        ) : markerTab === "outliers" && eligibility?.eligible ? (
                                            <OutlierList
                                                compact
                                                outliers={visibleOutliers}
                                                selectedPeriod={selectedOutlier?.date ?? null}
                                                onSelect={selectOutlier}
                                                emptyText={range ? "Im gewählten Zeitraum keine auffälligen Einzelmonate." : undefined}
                                            />
                                        ) : (
                                            <AnomalyList
                                                compact
                                                anomalies={visibleAnomalies}
                                                eligibility={eligibility}
                                                emptyText={range ? "Im gewählten Zeitraum keine auffälligen Veränderungen." : "Keine auffälligen Veränderungen erkannt. Für einen Zeitraum ohne Markierung: Monat anklicken, ziehen oder unten wählen."}
                                                selectedId={selectedId}
                                                onSelect={selectAnomaly}
                                            />
                                        )}
                                    </div>
                                </div>
                                {!loading && !error && markerTab === "outliers" && eligibility?.eligible && visibleOutliers.length > 0 && (
                                    <p className="m-0 mt-2 text-[11px] text-slate-500">{OUTLIER_UNVALIDATED_NOTE}.</p>
                                )}
                                {!loading && !error && markerTab === "events" && (
                                    <div className="mt-2 pt-2 border-t border-slate-100 space-y-1.5">
                                        {range && hiddenUserEvents > 0 && (
                                            <p className="m-0 text-[11px] text-slate-500">
                                                {hiddenUserEvents} weitere außerhalb des Zeitraums.{" "}
                                                <button type="button" className="underline underline-offset-2 text-slate-700 hover:text-slate-900"
                                                    onClick={() => updateParams({ range: null })}>
                                                    Gesamten Zeitraum zeigen
                                                </button>
                                            </p>
                                        )}
                                        <AddUserEventButton onClick={openNewUserEvent} disabled={!seriesMonths.length} />
                                        <p className="m-0 text-[11px] text-slate-500">{USER_EVENT_NOTE}</p>
                                    </div>
                                )}
                                {!loading && !error && range && markerTab !== "outliers" && hiddenCount > 0 && (
                                    <p className="m-0 mt-2 text-[11px] text-slate-500">
                                        {hiddenCount} weitere außerhalb des Zeitraums.{" "}
                                        <button type="button" className="underline underline-offset-2 text-slate-700 hover:text-slate-900"
                                            onClick={() => updateParams({ range: null })}>
                                            Gesamten Zeitraum zeigen
                                        </button>
                                    </p>
                                )}
                                {!loading && !error && selectedId && !selectedAnomaly && (
                                    <p className="m-0 mt-2 text-[11px] text-slate-500">
                                        Die ausgewählte Veränderung gibt es mit den aktuellen Einstellungen nicht.{" "}
                                        <button type="button" className="underline underline-offset-2 text-slate-700 hover:text-slate-900"
                                            onClick={clearSelection}>
                                            Auswahl aufheben
                                        </button>
                                    </p>
                                )}
                            </PageSection>
                        </div>

                        {/* Drill-down-Leiste: freie Auswahl eines Zeitraums (E17) */}
                        {!error && data && (
                            <div className="bg-white border border-slate-200 rounded-lg shadow-xs px-4 py-2.5 flex flex-wrap items-center gap-x-4 gap-y-2">
                                <div className="flex items-center gap-2.5 min-w-0">
                                    <span className="w-7 h-7 rounded-md grid place-items-center flex-none bg-slate-100 text-slate-600 [&_svg]:w-[14px] [&_svg]:h-[14px]">
                                        <MousePointerClick />
                                    </span>
                                    <div className="min-w-0">
                                        <p className="m-0 mb-0.5 font-mono text-[10px] tracking-[0.06em] uppercase text-slate-500 leading-none">DRILL-DOWN</p>
                                        <p className="m-0 text-[13px] font-semibold text-slate-900 leading-5 truncate">
                                            {selectedAnomaly
                                                ? `Veränderung ab ${fmtPeriod(selectedAnomaly.date)}`
                                                : selection
                                                    ? `Auswahl ${selectionLabel(selection)}`
                                                    : "Zeitraum wählen"}
                                        </p>
                                    </div>
                                </div>
                                {/* Bei ausgewählter Veränderung zeigen "von / bis" ihr Fenster ab dem markierten Monat (E12). */}
                                <DrilldownPicker
                                    key={selectedAnomaly ? `anomaly:${selectedAnomaly.id}` : selectionKey ?? "none"}
                                    months={seriesMonths}
                                    counts={monthCounts}
                                    selection={selectedAnomaly ? windows?.after ?? null : selection}
                                    onSelect={selectPeriod}
                                    onClear={selection || selectedAnomaly ? clearSelection : null}
                                />
                                {!selection && !selectedAnomaly && (
                                    <p className="m-0 text-[11px] text-slate-500 basis-full xl:basis-auto xl:ml-auto">
                                        oder im Verlauf: {SHOW_OUTLIER_MONTHS ? "Stufe, Raute oder Monat" : "Stufe oder Monat"} anklicken, Zeitraum ziehen
                                    </p>
                                )}
                            </div>
                        )}

                        {/* Vier Karten zur Auswahl (2026-10-16): Vorschau mit Stichpunkten, Klick öffnet die
                            Detailansicht im Dialog. Für eine ausgewählte Veränderung (Inkrement 2, 4, 5) ebenso
                            wie für die freie Auswahl und den Einzelmonat (E14, E17). */}
                        {/* Formular für eigene Ereignisse (E32): neu oder ändern/löschen */}
                        <UserEventDialog
                            open={Boolean(eventDialog)}
                            onOpenChange={(open) => { if (!open) setEventDialog(null) }}
                            event={eventDialog?.event ?? null}
                            initial={eventDialog?.initial ?? null}
                            months={seriesMonths}
                            counts={monthCounts}
                            saving={userEvents.saving}
                            onSave={saveUserEvent}
                            onDelete={eventDialog?.event ? () => userEvents.remove(eventDialog.event.id) : null}
                        />

                        {detail && (
                            <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
                                <ComparisonCard
                                    eyebrow={`VERGLEICH · ${detail.tag}`}
                                    title={detail.comparisonTitle}
                                    subtitle={detail.comparisonSubtitle}
                                    comparison={detail.comparison}
                                    labels={detail.labels}
                                    intro={detail.intro}
                                    introText={detail.introText}
                                    onDrill={drillToTopic}
                                    open={openCard === "comparison"}
                                    onOpenChange={(o) => setOpenCard(o ? "comparison" : null)}
                                />
                                <ReviewsCard
                                    eyebrow={`${detail.reviewsEyebrow} · ${detail.tag}`}
                                    title={detail.reviewsTitle}
                                    subtitle={detail.reviewsSubtitle}
                                    pages={reviewPages}
                                    side={detail.side}
                                    onSide={detail.onSide}
                                    labels={detail.labels}
                                    window={detail.window}
                                    comparison={detail.comparison}
                                    topic={topicFilter}
                                    dimension={singleDimension ? dimension : null}
                                    onClearDimension={singleDimension ? clearDimension : null}
                                    order={reviewOrder}
                                    onOrder={setReviewOrder}
                                    listKey={detail.listKey}
                                    emptyText={detail.emptyText}
                                    footnote={detail.footnote}
                                    open={openCard === "reviews"}
                                    onOpenChange={(o) => setOpenCard(o ? "reviews" : null)}
                                />
                                <ExplanationCard
                                    eyebrow={`ERKLÄRUNGSANSÄTZE · ${detail.tag}`}
                                    subtitle={group}
                                    comparison={detail.comparison}
                                    onSelectPeriod={selectPeriod}
                                    userEvents={numberedUserEvents}
                                />
                                <EvidenceCard
                                    eyebrow={`EXTERNE BERICHTE · ${detail.tag}`}
                                    subtitle={group}
                                    companyId={companyId}
                                    anomalyId={detail.evidence.anomalyId}
                                    selection={detail.evidence.selection}
                                    group={{ source, dimension, status }}
                                    dimensionOnly={singleDimension}
                                    onClearDimension={clearDimension}
                                    scores={detail.comparison.data?.explanation_summary?.item_scores ?? null}
                                    rules={detail.comparison.data?.explanation_summary?.rules ?? null}
                                />
                            </div>
                        )}
                    </>
                )}
            </div>
        </div>
    )
}
