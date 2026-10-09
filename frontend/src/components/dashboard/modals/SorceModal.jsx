import { useEffect, useMemo, useState } from "react";
import { Input } from "@/components/ui/input";
import { ArrowDown, ArrowUp, Filter, Search, Star as StarIcon, X } from "lucide-react";
import ModalShell, { ModalLoader, ModalError } from "./ModalShell";
import { Star } from "../../../icons";
import { CATEGORY_MEAN_NOTE, CATEGORY_MEAN_TITLE, SCORE_HINT, scoreCountText } from "@/lib/scoreText";

const API_URL = (import.meta.env.VITE_API_URL || "http://localhost:8000") + "/api";

const LABELS = {
  avg_arbeitsatmosphaere: "Arbeitsatmosphäre",
  avg_image: "Image",
  avg_work_life_balance: "Work-Life-Balance",
  avg_karriere_weiterbildung: "Karriere/Weiterbildung",
  avg_gehalt_sozialleistungen: "Gehalt/Sozialleistungen",
  avg_kollegenzusammenhalt: "Kollegenzusammenhalt",
  avg_umwelt_sozialbewusstsein: "Umwelt-/Sozialbewusstsein",
  avg_vorgesetztenverhalten: "Vorgesetztenverhalten",
  avg_interessante_aufgaben: "Interessante Aufgaben",
  avg_umgang_aelteren_kollegen: "Umgang mit älteren Kollegen",
  avg_arbeitsbedingungen: "Arbeitsbedingungen",
  avg_gleichberechtigung: "Gleichberechtigung",
  avg_kommunikation: "Kommunikation",
};

/* Tone for a single score */
const scoreTone = (s) => {
  const n = Number(s);
  if (!Number.isFinite(n)) return { bg: "bg-slate-100", text: "text-slate-600", bar: "bg-slate-300" };
  if (n >= 3.5) return { bg: "bg-emerald-50", text: "text-emerald-700", bar: "bg-emerald-500" };
  if (n >= 2.5) return { bg: "bg-amber-50",   text: "text-amber-700",   bar: "bg-amber-500" };
  return            { bg: "bg-rose-50",    text: "text-rose-700",    bar: "bg-rose-500" };
};

function ScoreStars({ score }) {
  const filled = Math.max(0, Math.min(5, Math.round(score)));
  return (
    <div className="flex items-center gap-0.5">
      {Array.from({ length: 5 }, (_, i) => (
        <StarIcon
          key={i}
          className={["h-3.5 w-3.5", i < filled ? "fill-amber-400 text-amber-400" : "text-slate-300"].join(" ")}
        />
      ))}
    </div>
  );
}

/* Detailfenster der Kachel „Ø Score“ (D1, 2026-10-09): oben die Gesamtnote mit n
   (scoreData = Antwort von GET /companies/{id}/ratings, wie die Kachel), darunter
   die Kategorien unter „Kategorienmittel“ für denselben Zeitraum (startDate). */
export default function SorceModal({ open, onOpenChange, companyId, scoreData = null, startDate = null }) {
  // Ergebnis je Firma und Zeitraum; "loading" gilt, solange der Schlüssel nicht passt
  // (kein setState im Effekt, Lint-Regel react-hooks/set-state-in-effect).
  const requestKey = companyId ? `${companyId}:${startDate ?? "all"}` : null;
  const [result, setResult] = useState({ key: null, data: null, error: "" });
  const loading = open && Boolean(requestKey) && result.key !== requestKey;
  const data = result.key === requestKey ? result.data : null;
  const error = result.key === requestKey ? result.error : "";

  const [searchTerm, setSearchTerm]   = useState("");
  const [filtersOpen, setFiltersOpen] = useState(false);
  const [minScore, setMinScore]       = useState("");
  const [maxScore, setMaxScore]       = useState("");
  const [sortKey, setSortKey]         = useState("score");
  const [sortDir, setSortDir]         = useState("asc");

  useEffect(() => {
    if (!open || !requestKey) return undefined;
    let active = true;
    const url = startDate
      ? `${API_URL}/companies/${companyId}/ratings/avg?start_date=${startDate}`
      : `${API_URL}/companies/${companyId}/ratings/avg`;
    fetch(url)
      .then((r) => { if (!r.ok) throw new Error("API error"); return r.json(); })
      .then((json) => { if (active) setResult({ key: requestKey, data: json, error: "" }); })
      .catch((e) => { if (active) setResult({ key: requestKey, data: null, error: e.message || "Error" }); });
    return () => { active = false; };
  }, [open, companyId, startDate, requestKey]);

  const rows = useMemo(() => {
    if (!data) return [];
    return Object.entries(data)
      .map(([key, value]) => ({ key, title: LABELS[key] ?? key, score: Number(value) }))
      .filter((x) => Number.isFinite(x.score));
  }, [data]);

  const filteredRows = useMemo(() => {
    const q = searchTerm.trim().toLowerCase();
    const min = minScore === "" ? null : Number(minScore);
    const max = maxScore === "" ? null : Number(maxScore);
    let list = rows;
    if (q) list = list.filter((r) => r.title.toLowerCase().includes(q));
    if (min !== null && Number.isFinite(min)) list = list.filter((r) => r.score >= min);
    if (max !== null && Number.isFinite(max)) list = list.filter((r) => r.score <= max);
    const dir = sortDir === "desc" ? -1 : 1;
    return [...list].sort((a, b) =>
      sortKey === "title" ? a.title.localeCompare(b.title) * dir : (a.score - b.score) * dir
    );
  }, [rows, searchTerm, minScore, maxScore, sortKey, sortDir]);

  const toggleSort = (key) => {
    if (sortKey === key) setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    else { setSortKey(key); setSortDir("asc"); }
  };

  const resetFilters = () => {
    setSearchTerm(""); setMinScore(""); setMaxScore(""); setSortKey("score"); setSortDir("asc");
  };

  // Gesamtnote (Ø Score) aus derselben Antwort wie die Kachel; Mittel der Kategorienmittel aus der Liste
  const score = Number.isFinite(Number(scoreData?.score)) && scoreData?.score != null ? Number(scoreData.score) : null;
  const categoryMean = rows.length ? rows.reduce((s, r) => s + r.score, 0) / rows.length : null;
  const fmt2 = (n) => n.toFixed(2).replace(".", ",");

  return (
    <ModalShell
      open={open}
      onOpenChange={onOpenChange}
      tone={score != null ? (score >= 3.5 ? "good" : score >= 2.5 ? "warn" : "bad") : "neutral"}
      icon={<Star />}
      eyebrow="KENNZAHL · BEWERTUNGS­ÜBERSICHT"
      title="Ø Score"
      subtitle={score != null ? `Gesamtnote ${fmt2(score)} / 5 · ${scoreCountText(scoreData?.score_n)}` : "Gesamtnote, Mitarbeitende"}
      size="lg"
      toolbar={
        <div className="flex flex-col gap-2">
          <div className="flex items-center gap-2">
            <div className="relative flex-1">
              <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-slate-400" />
              <Input
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Kategorie filtern…"
                className="h-8 pl-8 text-[13px]"
              />
            </div>
            <button
              onClick={() => setFiltersOpen((v) => !v)}
              className={[
                "h-8 px-2.5 inline-flex items-center gap-1.5 rounded-md text-[12px] font-medium border transition-colors",
                filtersOpen
                  ? "bg-slate-900 text-white border-slate-900"
                  : "bg-white text-slate-700 border-slate-300 hover:bg-slate-50",
              ].join(" ")}
            >
              <Filter className="h-3.5 w-3.5" /> Filter
            </button>
            <button
              onClick={resetFilters}
              className="h-8 px-2.5 inline-flex items-center gap-1.5 rounded-md text-[12px] font-medium bg-white text-slate-700 border border-slate-300 hover:bg-slate-50"
            >
              <X className="h-3.5 w-3.5" /> Reset
            </button>
          </div>

          {filtersOpen && (
            <div className="flex flex-wrap items-end gap-3 p-2.5 rounded-md border border-slate-200 bg-white">
              <div>
                <label className="block text-[10px] font-mono uppercase tracking-wider text-slate-500 mb-1">Min</label>
                <Input type="number" step="0.1" min="0" max="5"
                  value={minScore} onChange={(e) => setMinScore(e.target.value)}
                  className="h-8 w-20 text-[13px]" />
              </div>
              <div>
                <label className="block text-[10px] font-mono uppercase tracking-wider text-slate-500 mb-1">Max</label>
                <Input type="number" step="0.1" min="0" max="5"
                  value={maxScore} onChange={(e) => setMaxScore(e.target.value)}
                  className="h-8 w-20 text-[13px]" />
              </div>
              <div>
                <label className="block text-[10px] font-mono uppercase tracking-wider text-slate-500 mb-1">Sortieren</label>
                <div className="flex gap-1.5">
                  <button onClick={() => toggleSort("score")} className={[
                    "h-8 px-2.5 inline-flex items-center gap-1 rounded-md text-[12px] font-medium border",
                    sortKey === "score" ? "bg-slate-900 text-white border-slate-900" : "bg-white text-slate-700 border-slate-300"
                  ].join(" ")}>
                    Score {sortKey === "score" && (sortDir === "asc" ? <ArrowUp className="h-3 w-3" /> : <ArrowDown className="h-3 w-3" />)}
                  </button>
                  <button onClick={() => toggleSort("title")} className={[
                    "h-8 px-2.5 inline-flex items-center gap-1 rounded-md text-[12px] font-medium border",
                    sortKey === "title" ? "bg-slate-900 text-white border-slate-900" : "bg-white text-slate-700 border-slate-300"
                  ].join(" ")}>
                    Kategorie {sortKey === "title" && (sortDir === "asc" ? <ArrowUp className="h-3 w-3" /> : <ArrowDown className="h-3 w-3" />)}
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      }
    >
      {/* Gesamtnote mit n und Berechnungshinweis (FA-38, wortgleich mit Kachel und PDF) */}
      <div className="mb-4 rounded-md border border-slate-200 bg-slate-50 px-3 py-2.5" data-testid="score-overall">
        <div className="flex items-baseline justify-between gap-3">
          <span className="text-[13px] font-semibold text-slate-900">Gesamtnote</span>
          <span className={["font-semibold tnum text-[18px]", scoreTone(score).text].join(" ")}>
            {score != null ? `${fmt2(score)} / 5` : "—"}
          </span>
        </div>
        <span className="block text-[12px] text-slate-600 tnum">{scoreCountText(scoreData?.score_n)}</span>
        <p className="mt-1.5 text-[11.5px] leading-4 text-slate-500">{SCORE_HINT}</p>
      </div>

      <div className="mb-1">
        <div className="flex items-baseline justify-between gap-3">
          <h3 className="text-[13px] font-semibold text-slate-900">{CATEGORY_MEAN_TITLE}</h3>
          {categoryMean != null && (
            <span className="text-[12px] text-slate-500 tnum">Mittel der Kategorien: {fmt2(categoryMean)} / 5</span>
          )}
        </div>
        <p className="text-[11.5px] leading-4 text-slate-500">{CATEGORY_MEAN_NOTE}</p>
      </div>

      {loading && <ModalLoader />}
      {error && <ModalError>{error}</ModalError>}

      {!loading && !error && (
        <div className="flex flex-col">
          {filteredRows.map((row, idx) => {
            const t = scoreTone(row.score);
            return (
              <div
                key={row.key}
                className={[
                  "grid items-center gap-3 py-2.5",
                  idx < filteredRows.length - 1 ? "border-b border-slate-100" : "",
                ].join(" ")}
                style={{ gridTemplateColumns: "1.4fr 90px 1fr 56px" }}
              >
                <span className="font-medium text-[13px] text-slate-900 truncate" title={row.title}>
                  {row.title}
                </span>
                <ScoreStars score={row.score} />
                <span className="h-1.5 rounded-full bg-slate-100 overflow-hidden">
                  <span
                    className={["h-full rounded-full block", t.bar].join(" ")}
                    style={{ width: `${(row.score / 5) * 100}%`, transition: "width 400ms ease" }}
                  />
                </span>
                <span className={["text-right font-semibold tnum text-[13px]", t.text].join(" ")}>
                  {row.score.toFixed(2).replace(".", ",")}
                </span>
              </div>
            );
          })}

          {filteredRows.length === 0 && (
            <div className="py-8 text-center text-[13px] text-slate-500">
              Keine Treffer für diese Filter.
            </div>
          )}
        </div>
      )}
    </ModalShell>
  );
}
