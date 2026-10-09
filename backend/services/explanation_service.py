"""
Vorher-Nachher-Vergleich einer auffälligen Veränderung (Zyklus 2, Inkrement 2).

Der Vergleich beschreibt, was sich in den Bewertungen zwischen zwei Zeitfenstern
verändert hat. Er ist keine Aussage über Ursachen.

Vergleichsfenster (E12, vorläufig) einer Veränderung mit Monat ``date``:

- davor: die ``window_months`` Kalendermonate vor ``date``, nicht früher als
  ``before_from``
- danach: ``date`` und die folgenden Monate, zusammen ``window_months``, nicht
  später als ``after_to``

In die Fenster gehen alle Bewertungen dieser Monate ein, auch aus Monaten mit
weniger als 5 Bewertungen (anders als in der Erkennungsreihe, E4).

Je Fenster (``compare_windows``):

- Anzahl Bewertungen und mittlere Gesamtnote (``durchschnittsbewertung``), bei
  einer Einzeldimension zusätzlich deren Mittel
- je Schlüsselwort-Thema (E10, ``keyword_topic_service``) der Anteil der
  Bewertungen, die es nennen
- Stimmung (E11) gesamt und je Thema: Anteile positiv, neutral, negativ und
  mittlere Polarität (-1 bis 1)

Daraus je Thema die Verschiebung des Anteils in Prozentpunkten und der
mittleren Polarität; sortiert nach dem Betrag der Anteilsverschiebung, größte
zuerst. ``low_basis`` kennzeichnet eine kleine Basis: ein Fenster mit weniger
als 10 Bewertungen, oder je Thema weniger als 5 Nennungen in beiden Fenstern
zusammen.

Stimmung: ein ``SentimentAnalyzer`` je Prozess im Modus ``transformer`` mit der
Sternebewertung als Hinweis; lädt das Modell nicht, gilt der Lexikon-Modus
(eingebauter Rückfall). Höchstens ``SENTIMENT_SAMPLE_LIMIT`` = 300 Bewertungen
mit Freitext je Fenster gehen in die Stimmungsanalyse, bei mehr die jüngsten.
Ergebnisse werden je Quelle, Bewertungs-ID und Modus im Prozess
zwischengespeichert. Die Antwort nennt ``sentiment_mode`` und
``sentiment_sample``.

Erklärungsansätze (Inkrement 5, A4): ``explanations_for`` holt die Belege des
Ereignisfensters (E18, ``evidence_service``), rechnet die kennzeichnenden
Begriffe der beiden Vergleichsfenster (``review_terms``) und die Rangfolge
(``explanation_ranking``) und füllt ``explanations`` (höchstens fünf Einträge)
sowie ``explanation_summary`` (Zustand ``ansaetze`` oder ``offen``, Fenster,
Stand je Quelle, Begriffe, Signale je Beleg für die Belegliste, Regeln). Die
Stimmungsanalyse der Bewertungen wird dafür nicht erneut berechnet; die
Themenverschiebung kommt aus ``comparison``. Ein Fehler in diesem Teil ergibt
den Zustand ``offen`` mit Fehlertext, nie einen Fehler der Route.
"""

from __future__ import annotations

import calendar
import threading
from typing import Any, Dict, Iterable, List, Optional

from services.keyword_topic_service import topic_definitions_for, topic_for_dimension, topics_in_review
from services.rating_series_service import month_key
from services.review_service import review_text, sort_newest_first

DEFAULT_WINDOW_MONTHS = 6       # E12, vorläufig
SENTIMENT_SAMPLE_LIMIT = 300    # E11
LOW_BASIS_MIN_REVIEWS = 10      # je Fenster
LOW_BASIS_MIN_MENTIONS = 5      # je Thema, beide Fenster zusammen
_CACHE_MAX_ENTRIES = 50_000

SENTIMENT_LABELS = ("positive", "neutral", "negative")


# ── Vergleichsfenster ───────────────────────────────────────────────────────


def _month_index(period: str) -> int:
    y, m = (int(x) for x in period.split("-"))
    return y * 12 + (m - 1)


def _period(index: int) -> str:
    return f"{index // 12:04d}-{index % 12 + 1:02d}"


def _last_day(period: str) -> str:
    y, m = (int(x) for x in period.split("-"))
    return f"{period}-{calendar.monthrange(y, m)[1]:02d}"


def _span(first: int, last: int) -> Dict[str, Any]:
    start, end = _period(first), _period(last)
    return {"from": start, "to": end, "start": f"{start}-01", "end": _last_day(end), "months": last - first + 1}


def comparison_windows(anomaly: Dict[str, Any], window_months: int = DEFAULT_WINDOW_MONTHS) -> Dict[str, Any]:
    """Fenster davor und danach einer Veränderung (E12).

    Rückgabe ``{"window_months", "before", "after"}``, je Fenster ``from``/``to``
    (``YYYY-MM``), ``start``/``end`` (``YYYY-MM-DD``, einschließlich) und
    ``months``. Ohne ``before_from``/``after_to`` gilt nur ``window_months``.
    """
    if window_months < 1:
        raise ValueError("window_months muss mindestens 1 sein.")
    date = _month_index(anomaly["date"])
    before_from = _month_index(anomaly["before_from"]) if anomaly.get("before_from") else date - window_months
    after_to = _month_index(anomaly["after_to"]) if anomaly.get("after_to") else date + window_months - 1
    return {
        "window_months": window_months,
        "before": _span(max(date - window_months, before_from), date - 1),
        "after": _span(date, min(date + window_months - 1, after_to)),
    }


def split_rows_by_window(rows: Iterable[Dict[str, Any]], windows: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
    """Zeilen nach Kalendermonat auf die Fenster ``before`` und ``after`` verteilen;
    Zeilen außerhalb oder ohne Datum entfallen."""
    out: Dict[str, List[Dict[str, Any]]] = {"before": [], "after": []}
    for row in rows:
        period = month_key(row.get("datum"))
        if period is None:
            continue
        for side in ("before", "after"):
            if windows[side]["from"] <= period <= windows[side]["to"]:
                out[side].append(row)
    return out


# ── Stimmung ────────────────────────────────────────────────────────────────

_analyzer = None
_analyzer_lock = threading.Lock()   # Aufbau und Analyse; die Pipeline ist nicht als threadsicher dokumentiert
_cache: Dict[tuple, Dict[str, Any]] = {}


def get_sentiment_analyzer():
    """Der ``SentimentAnalyzer`` des Prozesses (Modus transformer, Rückfall lexicon)."""
    global _analyzer
    with _analyzer_lock:
        if _analyzer is None:
            from models.sentiment_analyzer import SentimentAnalyzer  # lazy: lädt ggf. das Modell
            _analyzer = SentimentAnalyzer(mode="transformer")
    return _analyzer


def set_sentiment_analyzer(analyzer) -> None:
    """Analyzer des Prozesses setzen (Tests: Lexikon-Modus ohne Netzwerk) und
    den Zwischenspeicher leeren."""
    global _analyzer
    with _analyzer_lock:
        _analyzer = analyzer
        _cache.clear()


def sentiment_mode(analyzer) -> str:
    """Tatsächlich verwendeter Modus: ``transformer`` nur, wenn das Modell geladen ist."""
    if getattr(analyzer, "mode", None) == "transformer" and getattr(analyzer, "_transformer_available", False):
        return "transformer"
    return "lexicon"


def _rating(row: Dict[str, Any], column: str = "durchschnittsbewertung") -> Optional[float]:
    value = row.get(column)
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _sentiments(rows: List[Dict[str, Any]], source: str, analyzer, mode: str) -> List[Dict[str, Any]]:
    """Stimmung je Zeile in derselben Reihenfolge, zwischengespeichert je
    (Quelle, ``id``, Modus)."""
    results: List[Dict[str, Any]] = []
    with _analyzer_lock:
        for row in rows:
            rid = row.get("id")
            key = (source, rid, mode)
            cached = _cache.get(key) if rid is not None else None
            if cached is None:
                raw = analyzer.analyze_sentiment(review_text(row, source), _rating(row))
                cached = {"sentiment": raw.get("sentiment", "neutral"), "polarity": float(raw.get("polarity", 0.0))}
                if rid is not None:
                    if len(_cache) >= _CACHE_MAX_ENTRIES:
                        _cache.pop(next(iter(_cache)))
                    _cache[key] = cached
            results.append(cached)
    return results


def _sentiment_summary(items: List[Dict[str, Any]]) -> Dict[str, Any]:
    n = len(items)
    if not n:
        return {"n": 0, "positive": None, "neutral": None, "negative": None, "mean_polarity": None}
    summary: Dict[str, Any] = {"n": n}
    for label in SENTIMENT_LABELS:
        summary[label] = round(sum(1 for s in items if s["sentiment"] == label) / n, 4)
    summary["mean_polarity"] = round(sum(s["polarity"] for s in items) / n, 4)
    return summary


# ── Vergleich ───────────────────────────────────────────────────────────────


def _window_stats(
    rows: List[Dict[str, Any]],
    source: str,
    topics: List[str],
    analyzer,
    mode: str,
    sample_limit: int,
    value_column: Optional[str],
) -> Dict[str, Any]:
    """Kennzahlen eines Fensters samt Themen und Stimmung je Bewertung."""
    ratings = [r for r in (_rating(row) for row in rows) if r is not None]
    with_text = [row for row in sort_newest_first(rows) if review_text(row, source)]
    sample = with_text[:sample_limit]
    # Zuordnung über die Objektidentität: sample enthält dieselben Zeilenobjekte wie rows.
    sentiment_of = dict(zip((id(row) for row in sample), _sentiments(sample, source, analyzer, mode)))

    mentions = {topic: 0 for topic in topics}
    topic_sentiments: Dict[str, List[Dict[str, Any]]] = {topic: [] for topic in topics}
    for row in rows:
        for topic in topics_in_review(row, source):
            if topic not in mentions:
                continue
            mentions[topic] += 1
            if id(row) in sentiment_of:
                topic_sentiments[topic].append(sentiment_of[id(row)])

    n = len(rows)
    stats: Dict[str, Any] = {
        "n_reviews": n,
        "mean_rating": round(sum(ratings) / len(ratings), 3) if ratings else None,
        "n_rated": len(ratings),
        "sentiment": _sentiment_summary(list(sentiment_of.values())),
        "sentiment_sample": {
            "with_text": len(with_text),
            "analyzed": len(sample),
            "limited": len(with_text) > len(sample),
        },
        "_mentions": mentions,
        "_topic_sentiments": {t: _sentiment_summary(v) for t, v in topic_sentiments.items()},
    }
    if value_column and value_column != "durchschnittsbewertung":
        values = [v for v in (_rating(row, value_column) for row in rows) if v is not None]
        stats["mean_value"] = round(sum(values) / len(values), 3) if values else None
        stats["n_values"] = len(values)
    return stats


def _diff(after: Optional[float], before: Optional[float], digits: int = 4) -> Optional[float]:
    return None if after is None or before is None else round(after - before, digits)


def compare_windows(
    before_rows: List[Dict[str, Any]],
    after_rows: List[Dict[str, Any]],
    source: str,
    *,
    analyzer=None,
    sample_limit: int = SENTIMENT_SAMPLE_LIMIT,
    value_column: Optional[str] = None,
) -> Dict[str, Any]:
    """Vorher-Nachher-Vergleich zweier Fenster einer Quelle.

    ``before_rows``/``after_rows``: Bewertungszeilen (mit ``id``, ``datum``,
    ``durchschnittsbewertung``, Freitextfeldern). ``analyzer``: Objekt mit
    ``analyze_sentiment(text, star_rating)``; Standard ist der Analyzer des
    Prozesses. ``value_column``: Spalte der Dimension, deren Mittel zusätzlich
    berichtet wird.

    Rückgabe::

        {"before": {...}, "after": {...},      # n_reviews, mean_rating, sentiment, ...
         "rating_shift", "polarity_shift",
         "topics": [{"topic", "before": {"mentions", "share", "sentiment"},
                     "after": {...}, "share_shift_pp", "polarity_shift",
                     "low_basis"}, ...],      # nach |share_shift_pp| absteigend
         "low_basis", "low_basis_rule", "sentiment_mode", "sentiment_sample"}
    """
    analyzer = analyzer if analyzer is not None else get_sentiment_analyzer()
    mode = sentiment_mode(analyzer)
    topics = list(topic_definitions_for(source).keys())
    windows = {
        side: _window_stats(rows, source, topics, analyzer, mode, sample_limit, value_column)
        for side, rows in (("before", before_rows), ("after", after_rows))
    }
    small_window = any(w["n_reviews"] < LOW_BASIS_MIN_REVIEWS for w in windows.values())

    topic_rows: List[Dict[str, Any]] = []
    for topic in topics:
        entry: Dict[str, Any] = {"topic": topic}
        for side, w in windows.items():
            mentions = w["_mentions"][topic]
            entry[side] = {
                "mentions": mentions,
                "share": round(mentions / w["n_reviews"], 4) if w["n_reviews"] else None,
                "sentiment": w["_topic_sentiments"][topic],
            }
        before_share, after_share = entry["before"]["share"], entry["after"]["share"]
        entry["share_shift_pp"] = _diff(
            None if after_share is None else after_share * 100,
            None if before_share is None else before_share * 100,
            digits=2,
        )
        entry["polarity_shift"] = _diff(
            entry["after"]["sentiment"]["mean_polarity"], entry["before"]["sentiment"]["mean_polarity"],
        )
        entry["low_basis"] = small_window or (
            entry["before"]["mentions"] + entry["after"]["mentions"] < LOW_BASIS_MIN_MENTIONS
        )
        topic_rows.append(entry)

    topic_rows.sort(key=lambda e: (
        -abs(e["share_shift_pp"] or 0.0),
        -abs(e["polarity_shift"] or 0.0),
        e["topic"],
    ))

    for w in windows.values():
        w.pop("_mentions")
        w.pop("_topic_sentiments")

    result: Dict[str, Any] = {
        "before": windows["before"],
        "after": windows["after"],
        "rating_shift": _diff(windows["after"]["mean_rating"], windows["before"]["mean_rating"], digits=3),
        "polarity_shift": _diff(
            windows["after"]["sentiment"]["mean_polarity"], windows["before"]["sentiment"]["mean_polarity"],
        ),
        "topics": topic_rows,
        "low_basis": small_window,
        "low_basis_rule": {
            "min_reviews_per_window": LOW_BASIS_MIN_REVIEWS,
            "min_mentions_per_topic": LOW_BASIS_MIN_MENTIONS,
        },
        "sentiment_mode": mode,
        "sentiment_sample": {
            "limit": sample_limit,
            "before": windows["before"].pop("sentiment_sample"),
            "after": windows["after"].pop("sentiment_sample"),
        },
    }
    if "mean_value" in windows["before"]:
        result["value_shift"] = _diff(windows["after"]["mean_value"], windows["before"]["mean_value"], digits=3)
    return result


# ── Erklärungsansätze (Inkrement 5) ─────────────────────────────────────────

import logging  # noqa: E402

logger = logging.getLogger(__name__)


def _direction_from_shift(shift: Optional[float]) -> Optional[str]:
    if shift is None or shift == 0:
        return None
    return "fall" if shift < 0 else "rise"


def explanations_for(
    company_id: int,
    window: Dict[str, Any],
    before_rows: List[Dict[str, Any]],
    after_rows: List[Dict[str, Any]],
    comparison: Dict[str, Any],
    *,
    direction: Optional[str] = None,
    analyzer=None,
    info: Optional[Dict[str, Any]] = None,
    evidence: Optional[Dict[str, Any]] = None,
    source: Optional[str] = None,
) -> Dict[str, Any]:
    """Erklärungsansätze zu einem Ereignisfenster (E18) aus den Belegen des Speichers
    (bzw. Abruf, wenn erlaubt), den Bewertungen der Vergleichsfenster und der
    Themenliste des Vergleichs. Rückgabe ``{"explanations": [...], "summary": {...}}``;
    ``summary["state"]`` ist ``ansaetze`` oder ``offen``. ``info`` und ``evidence``
    ersetzen Unternehmensdaten und Belege (Tests, Auswertung). Wirft nicht."""
    from services import evidence_service as ev
    from services.explanation_ranking import OPEN_NOTE, STATE_OPEN, rank_evidence, rules
    from services.review_terms import company_terms, distinctive_terms

    base: Dict[str, Any] = {
        "state": STATE_OPEN, "kind": window.get("kind"), "window": {k: window.get(k) for k in (
            "kind", "from", "to", "months", "transition_from", "anchor_from", "anchor_to", "window_before", "window_after")},
        "n_items": 0, "n_bundles": 0, "n_groups": 0, "n_by_stage": None, "n_by_signal_label": None, "terms": [], "item_scores": {}, "sources": {},
        "coverage": False, "reason": None, "error": None, "note": None, "open_note": OPEN_NOTE, "rules": rules(),
    }
    try:
        info = info if info is not None else ev.company_context_info(company_id)
        if info is None:
            return {"explanations": [], "summary": {**base, "reason": f"Unternehmen {company_id} nicht gefunden."}}
        evidence = evidence if evidence is not None else ev.evidence_for_window(info, window)
        exclude = company_terms(info.get("name"), info.get("search_term"))
        terms = distinctive_terms(before_rows, after_rows, source=source, exclude=exclude)
        ranked = rank_evidence(
            evidence["items"], window, terms=terms, topics=comparison.get("topics"), direction=direction,
            exclude=exclude, analyzer=analyzer, kind=window.get("kind"),
        )
    except Exception as exc:  # noqa: BLE001 – Belege oder Rangfolge: der Vergleich bleibt nutzbar
        logger.warning("Erklärungsansätze für Unternehmen %s nicht berechenbar: %s", company_id, exc)
        return {"explanations": [], "summary": {**base, "error": f"{type(exc).__name__}: {exc}"}}
    summary = {
        **base,
        "state": ranked["state"], "n_items": ranked["n_items"], "n_bundles": ranked["n_bundles"], "n_groups": ranked["n_groups"],
        "n_by_stage": ranked["n_by_stage"], "n_by_signal_label": ranked["n_by_signal_label"], "terms": ranked["terms"], "item_scores": ranked["item_scores"],
        "sources": evidence.get("sources", {}), "coverage": evidence.get("coverage", False), "reason": evidence.get("reason"),
        "note": ranked["note"], "open_note": ranked["open_note"], "search_term": info.get("search_term"),
        "direction": direction,
    }
    return {"explanations": ranked["explanations"], "summary": summary}


# ── Veränderung aus der Datenbank ───────────────────────────────────────────


def parse_anomaly_id(anomaly_id: str) -> Optional[Dict[str, str]]:
    """``"{source}:{dimension}:{YYYY-MM}"`` zerlegen; None bei anderem Aufbau."""
    parts = anomaly_id.split(":")
    if len(parts) != 3 or not all(parts):
        return None
    return {"source": parts[0], "dimension": parts[1], "date": parts[2]}


def explain_anomaly(
    company_id: int,
    anomaly_id: str,
    source: Optional[str] = None,
    dimension: Optional[str] = None,
    window_months: int = DEFAULT_WINDOW_MONTHS,
    *,
    status: Optional[str] = None,
    analyzer=None,
) -> Optional[Dict[str, Any]]:
    """Vergleich für eine Veränderung eines Unternehmens, nur lesend.

    Die Veränderungen werden mit den Standardparametern der Erkennung neu
    berechnet (``company_anomalies``). Fehlen ``source`` oder ``dimension``,
    gelten die Angaben aus ``anomaly_id``. ``status`` wählt die
    Bewertendengruppe (E13): Erkennung und Fenster nur mit ihren Bewertungen.
    Rückgabe None, wenn ``anomaly_id`` nicht unter den erkannten Veränderungen
    ist. ValueError bei ungültiger Quelle, Dimension, ungültigem Status oder
    ``window_months``.
    """
    from services.anomaly_service import company_anomalies
    from services.rating_series_service import value_column
    from services.review_service import fetch_review_rows_in_range, filter_by_status, parse_day

    parsed = parse_anomaly_id(anomaly_id)
    if parsed is None:
        return None
    source = source or parsed["source"]
    dimension = dimension or parsed["dimension"]
    column = value_column(source, dimension)  # ValueError bei ungültiger Angabe
    if window_months < 1:
        raise ValueError("window_months muss mindestens 1 sein.")

    detected = company_anomalies(company_id, source=source, dimension=dimension, status=status)
    anomaly = next((a for a in detected["anomalies"] if a["id"] == anomaly_id), None)
    if anomaly is None:
        return None

    windows = comparison_windows(anomaly, window_months)
    rows = fetch_review_rows_in_range(
        source, company_id, parse_day(windows["before"]["start"], "start"), parse_day(windows["after"]["end"], "end"),
    )
    by_window = split_rows_by_window(filter_by_status(rows, source, status), windows)
    for side in ("before", "after"):
        windows[side]["n_reviews"] = len(by_window[side])
    comparison = compare_windows(
        by_window["before"], by_window["after"], source, analyzer=analyzer, value_column=column,
    )
    from services.evidence_service import window_for_anomaly  # Ereignisfenster (E18)

    explained = explanations_for(
        company_id, window_for_anomaly(anomaly), by_window["before"], by_window["after"], comparison,
        direction=anomaly.get("direction"), analyzer=analyzer if analyzer is not None else get_sentiment_analyzer(),
        source=source,
    )
    return {
        "company_id": company_id,
        "source": source,
        "dimension": dimension,
        "status": status,
        "dimension_topic": topic_for_dimension(source, dimension),  # Thema der Dimension, für die Hervorhebung
        "anomaly": anomaly,
        "windows": windows,
        "comparison": comparison,
        "explanations": explained["explanations"],          # Erklärungsansätze (Inkrement 5), höchstens fünf
        "explanation_summary": explained["summary"],
    }


# ── Freie Auswahl (E17) ─────────────────────────────────────────────────────

MIN_BASELINE_MONTHS = 6   # E17, vorläufig: Vergleichszeitraum mindestens 6 Monate


def _parse_month(value: str, name: str) -> int:
    try:
        y, m = (int(x) for x in str(value).split("-"))
        if not 1 <= m <= 12 or len(str(value)) != 7:
            raise ValueError
    except ValueError:
        raise ValueError(f"{name} '{value}' ist kein Monat im Format YYYY-MM.") from None
    return y * 12 + (m - 1)


def period_windows(from_month: str, to_month: str, min_baseline: int = MIN_BASELINE_MONTHS) -> Dict[str, Any]:
    """Fenster für eine frei gewählte Auswahl ``from_month`` bis ``to_month``
    (einschließlich): ``after`` ist die Auswahl, ``before`` der gleich lange
    Zeitraum direkt davor, mindestens ``min_baseline`` Monate (E17).
    ValueError bei falschem Format oder ``from_month`` nach ``to_month``."""
    first, last = _parse_month(from_month, "from"), _parse_month(to_month, "to")
    if first > last:
        raise ValueError("from liegt nach to.")
    length = last - first + 1
    baseline = max(length, min_baseline)
    return {
        "window_months": baseline,
        "before": _span(first - baseline, first - 1),
        "after": _span(first, last),
    }


def compare_period(
    company_id: int,
    from_month: str,
    to_month: str,
    source: str = "employee",
    dimension: Optional[str] = None,
    *,
    status: Optional[str] = None,
    analyzer=None,
) -> Dict[str, Any]:
    """Vergleich einer frei gewählten Auswahl mit dem Zeitraum davor (E17), auch
    ohne erkannte Veränderung; sonst wie ``explain_anomaly``. Nur lesend.
    ValueError bei ungültiger Quelle, Dimension, Status oder Monatsangabe."""
    from services.rating_series_service import OVERALL_DIMENSION, value_column
    from services.review_service import fetch_review_rows_in_range, filter_by_status, parse_day, validate_status

    dimension = dimension or OVERALL_DIMENSION
    column = value_column(source, dimension)
    validate_status(source, status)
    windows = period_windows(from_month, to_month)
    rows = fetch_review_rows_in_range(
        source, company_id, parse_day(windows["before"]["start"], "start"), parse_day(windows["after"]["end"], "end"),
    )
    by_window = split_rows_by_window(filter_by_status(rows, source, status), windows)
    for side in ("before", "after"):
        windows[side]["n_reviews"] = len(by_window[side])
    comparison = compare_windows(
        by_window["before"], by_window["after"], source, analyzer=analyzer, value_column=column,
    )
    from services.evidence_service import window_for_selection  # Ereignisfenster um die Auswahl (E18)

    explained = explanations_for(
        company_id, window_for_selection(from_month, to_month), by_window["before"], by_window["after"], comparison,
        direction=_direction_from_shift(comparison.get("rating_shift")),
        analyzer=analyzer if analyzer is not None else get_sentiment_analyzer(), source=source,
    )
    return {
        "company_id": company_id,
        "source": source,
        "dimension": dimension,
        "status": status,
        "dimension_topic": topic_for_dimension(source, dimension),
        "selection": {"from": from_month, "to": to_month},
        "windows": windows,
        "comparison": comparison,
        "explanations": explained["explanations"],
        "explanation_summary": explained["summary"],
    }


__all__ = [
    "MIN_BASELINE_MONTHS", "period_windows", "compare_period", "explanations_for",
    "parse_anomaly_id", "explain_anomaly",
    "DEFAULT_WINDOW_MONTHS", "SENTIMENT_SAMPLE_LIMIT", "LOW_BASIS_MIN_REVIEWS", "LOW_BASIS_MIN_MENTIONS",
    "comparison_windows", "split_rows_by_window", "get_sentiment_analyzer", "set_sentiment_analyzer",
    "sentiment_mode", "compare_windows",
]
