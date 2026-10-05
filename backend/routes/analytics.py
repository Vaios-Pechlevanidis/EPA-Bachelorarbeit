"""
API routes for analytics and company data.
"""

from fastapi import APIRouter, HTTPException, Query
from database.supabase_client import get_supabase_client
from typing import Optional, List, Dict, Any, Literal
from services.topic_average_rating_service import fetch_all_rows_parallel, get_topic_rating_timeseries
import services.review_service as review_service
from services.keyword_topic_service import analyze_topic, topic_definitions_for, topic_for_dimension, topic_spans, topics_in_review
from services.review_service import (
    clean_html_text,
    fetch_review_rows_in_range,
    filter_by_status,
    full_review_item,
    parse_day,
    sort_newest_first,
    validate_status,
)
from services.statistical_validator import StatisticalValidator
from services.statistical_enrichment import (
    enrich_with_statistical_metadata,
    enrich_topic_analysis_with_metadata,
    enrich_comparison_with_metadata
)
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import re
import random

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])


@router.get("/company/{company_id}/overview")
def get_company_overview(company_id: int):
    """Get overall statistics for a company."""
    supabase = get_supabase_client()
    try:
        # Get candidates data
        candidates_response = supabase.table("candidates")\
            .select("durchschnittsbewertung, datum")\
            .eq("company_id", company_id)\
            .execute()
        
        # Get employee data
        employee_response = supabase.table("employee")\
            .select("durchschnittsbewertung, datum")\
            .eq("company_id", company_id)\
            .execute()
        
        candidates_data = candidates_response.data or []
        employee_data = employee_response.data or []
        
        # Calculate average score
        all_ratings = [
            float(r["durchschnittsbewertung"]) 
            for r in candidates_data + employee_data 
            if r.get("durchschnittsbewertung")
        ]
        
        avg_score = round(sum(all_ratings) / len(all_ratings), 2) if all_ratings else 0
        
        # Calculate trend (comparing last 30 days vs previous 30 days)
        now = datetime.now()
        thirty_days_ago = now - timedelta(days=30)
        sixty_days_ago = now - timedelta(days=60)

        def _parse_datum(d: str) -> datetime:
            dt = datetime.fromisoformat(d.replace("Z", "+00:00"))
            return dt.replace(tzinfo=None) if dt.tzinfo else dt

        recent_ratings = [
            float(r["durchschnittsbewertung"])
            for r in candidates_data + employee_data
            if r.get("durchschnittsbewertung") and r.get("datum")
            and _parse_datum(r["datum"]) >= thirty_days_ago
        ]

        previous_ratings = [
            float(r["durchschnittsbewertung"])
            for r in candidates_data + employee_data
            if r.get("durchschnittsbewertung") and r.get("datum")
            and sixty_days_ago <= _parse_datum(r["datum"]) < thirty_days_ago
        ]
        
        recent_avg = sum(recent_ratings) / len(recent_ratings) if recent_ratings else 0
        previous_avg = sum(previous_ratings) / len(previous_ratings) if previous_ratings else 0
        trend = round(recent_avg - previous_avg, 2)
        
        # Find most critical category
        critical_category = get_most_critical_category(company_id)
        
        return {
            "average_score": avg_score,
            "trend": trend,
            "total_reviews": len(candidates_data) + len(employee_data),
            "candidate_reviews": len(candidates_data),
            "employee_reviews": len(employee_data),
            "most_critical": critical_category
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching company overview: {str(e)}")


@router.get("/company/{company_id}/timeline")
def get_company_timeline(
    company_id: int,
    days: int = Query(default=365, description="Number of days to include"),
    forecast_months: int = Query(default=12, description="Number of months to forecast"),
    source: str = Query(default="all", description="Data source: 'employee', 'candidates', or 'all'")
):
    """Get timeline data for ratings over time with forecast."""
    supabase = get_supabase_client()
    try:
        cutoff_date = datetime.now() - timedelta(days=days)
        
        timeline_data = []
        
        # Get candidates data (if source is 'candidates' or 'all')
        if source in ["candidates", "all"]:
            candidates_response = supabase.table("candidates")\
                .select("durchschnittsbewertung, datum")\
                .eq("company_id", company_id)\
                .gte("datum", cutoff_date.isoformat())\
                .order("datum")\
                .execute()
            
            candidates_data = candidates_response.data or []
            for item in candidates_data:
                if item.get("datum") and item.get("durchschnittsbewertung"):
                    timeline_data.append({
                        "date": item["datum"],
                        "score": float(item["durchschnittsbewertung"]),
                        "type": "candidate"
                    })
        
        # Get employee data (if source is 'employee' or 'all')
        if source in ["employee", "all"]:
            employee_response = supabase.table("employee")\
                .select("durchschnittsbewertung, datum")\
                .eq("company_id", company_id)\
                .gte("datum", cutoff_date.isoformat())\
                .order("datum")\
                .execute()
            
            employee_data = employee_response.data or []
            for item in employee_data:
                if item.get("datum") and item.get("durchschnittsbewertung"):
                    timeline_data.append({
                        "date": item["datum"],
                        "score": float(item["durchschnittsbewertung"]),
                        "type": "employee"
                    })
        
        # Sort by date
        timeline_data.sort(key=lambda x: x["date"])
        
        # Group by month for aggregation
        monthly_data = defaultdict(list)
        for item in timeline_data:
            try:
                date = datetime.fromisoformat(item["date"].replace("Z", "+00:00"))
                month_key = date.strftime("%Y-%m")
                monthly_data[month_key].append(item["score"])
            except:
                pass
        
        # Create aggregated monthly timeline
        aggregated_timeline = []
        for month_key in sorted(monthly_data.keys()):
            scores = monthly_data[month_key]
            date_obj = datetime.strptime(month_key, "%Y-%m")
            aggregated_timeline.append({
                "date": month_key,
                "date_display": date_obj.strftime("%b %Y"),
                "score": round(sum(scores) / len(scores), 2),
                "count": len(scores),
                "is_forecast": False
            })
        
        # Calculate forecast using Holt's method
        forecast_data = calculate_forecast(aggregated_timeline, forecast_months)
        
        return {
            "timeline": aggregated_timeline,
            "forecast": forecast_data,
            "total_points": len(timeline_data),
            "current_date": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching timeline: {str(e)}")


def _fallback_forecast_average(
    historical_data: List[Dict[str, Any]], months: int, y_values: List[float]
) -> List[Dict[str, Any]]:
    """Fallback forecast using average of historical scores (used when Holt fails)."""
    avg_score = sum(y_values) / len(y_values)
    forecast = []
    last_date = datetime.strptime(historical_data[-1]["date"], "%Y-%m")
    for i in range(1, months + 1):
        month_offset = last_date.month + i
        year_offset = (month_offset - 1) // 12
        month = ((month_offset - 1) % 12) + 1
        next_month = last_date.replace(year=last_date.year + year_offset, month=month)
        forecast.append({
            "date": next_month.strftime("%Y-%m"),
            "date_display": next_month.strftime("%b %Y"),
            "score": round(avg_score, 2),
            "is_forecast": True
        })
    return forecast


def calculate_forecast(historical_data: List[Dict[str, Any]], months: int) -> List[Dict[str, Any]]:
    """
    Calculate forecast from historical monthly data using Holt's method
    (exponential smoothing with trend). Forecasts are clamped to the rating bounds [0, 5].
    Falls back to average of historical scores if Holt fails (e.g. too little data).
    """
    if months <= 0:
        return []
    if len(historical_data) < 2:
        return []

    y_values = [point["score"] for point in historical_data]
    last_date = datetime.strptime(historical_data[-1]["date"], "%Y-%m")

    try:
        from statsmodels.tsa.holtwinters import Holt  # type: ignore[import-untyped]
        import numpy as np

        series = np.asarray(y_values, dtype=float)
        model = Holt(series)
        fit = model.fit()
        preds = fit.forecast(steps=months)
    except Exception:
        return _fallback_forecast_average(historical_data, months, y_values)

    forecast = []
    for i in range(months):
        month_offset = last_date.month + (i + 1)
        year_offset = (month_offset - 1) // 12
        month = ((month_offset - 1) % 12) + 1
        next_month = last_date.replace(year=last_date.year + year_offset, month=month)
        score = float(preds[i])
        score = max(0.0, min(5.0, score))
        forecast.append({
            "date": next_month.strftime("%Y-%m"),
            "date_display": next_month.strftime("%b %Y"),
            "score": round(score, 2),
            "is_forecast": True
        })
    return forecast


@router.get("/company/{company_id}/category-ratings")
def get_category_ratings(company_id: int):
    """Get average ratings for each category."""
    supabase = get_supabase_client()
    try:
        # Get all rating columns for candidates
        candidates_response = supabase.table("candidates")\
            .select("*")\
            .eq("company_id", company_id)\
            .execute()
        
        # Get all rating columns for employees
        employee_response = supabase.table("employee")\
            .select("*")\
            .eq("company_id", company_id)\
            .execute()
        
        candidates_data = candidates_response.data or []
        employee_data = employee_response.data or []
        
        # Calculate averages for candidate categories
        candidate_categories = {}
        candidate_rating_fields = [
            col for col in (candidates_data[0].keys() if candidates_data else [])
            if col.startswith("sternebewertung_")
        ]
        
        for field in candidate_rating_fields:
            ratings = [
                float(r[field]) for r in candidates_data 
                if r.get(field) is not None
            ]
            if ratings:
                category_name = field.replace("sternebewertung_", "").replace("_", " ").title()
                candidate_categories[category_name] = round(sum(ratings) / len(ratings), 2)
        
        # Calculate averages for employee categories
        employee_categories = {}
        employee_rating_fields = [
            col for col in (employee_data[0].keys() if employee_data else [])
            if col.startswith("sternebewertung_")
        ]
        
        for field in employee_rating_fields:
            ratings = [
                float(r[field]) for r in employee_data 
                if r.get(field) is not None
            ]
            if ratings:
                category_name = field.replace("sternebewertung_", "").replace("_", " ").title()
                employee_categories[category_name] = round(sum(ratings) / len(ratings), 2)
        
        return {
            "candidate_categories": candidate_categories,
            "employee_categories": employee_categories
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching category ratings: {str(e)}")


def get_most_critical_category(company_id: int) -> Dict[str, Any]:
    """Helper function to find the most critical (lowest rated) category."""
    try:
        category_data = get_category_ratings(company_id)
        
        all_categories = {
            **category_data["candidate_categories"],
            **category_data["employee_categories"]
        }
        
        if not all_categories:
            return {"category": "N/A", "score": 0}
        
        lowest = min(all_categories.items(), key=lambda x: x[1])
        return {
            "category": lowest[0],
            "score": lowest[1]
        }
        
    except Exception:
        return {"category": "N/A", "score": 0}


def _review_list_item(item: Dict[str, Any], source: str) -> Dict[str, Any]:
    """Listeneintrag im bisherigen Format der Route ``/reviews``."""
    if source == "candidates":
        return {
            "id": item["id"],
            "type": "candidate",
            "date": item.get("datum"),
            "score": float(item.get("durchschnittsbewertung", 0)),
            "title": item.get("titel", ""),
            "description": item.get("stellenbeschreibung", ""),
            "improvements": item.get("verbesserungsvorschlaege", "")
        }
    return {
        "id": item["id"],
        "type": "employee",
        "date": item.get("datum"),
        "score": float(item.get("durchschnittsbewertung", 0)),
        "title": item.get("titel", ""),
        "job_description": item.get("jobbeschreibung", ""),
        "positive": item.get("gut_am_arbeitgeber_finde_ich", ""),
        "negative": item.get("schlecht_am_arbeitgeber_finde_ich", ""),
        "improvements": item.get("verbesserungsvorschlaege", "")
    }


def _reviews_in_range(
    company_id: int,
    source: Optional[str],
    start: Optional[str],
    end: Optional[str],
    status: Optional[str],
    offset: int,
    limit: int,
    full: bool,
    dimension: Optional[str] = None,
    topic_only: bool = False,
) -> Dict[str, Any]:
    """Bewertungen eines Zeitraums (Drill-down, Inkrement 2), vollständig
    paginiert gelesen, nach Status gefiltert, nach Datum absteigend sortiert;
    davon ``limit`` ab ``offset``. Mit ``dimension`` (braucht ``source``) werden
    die Fundstellen des zugehörigen Schlüsselwort-Themas markiert.
    ValueError bei ungültigen Parametern."""
    if source is not None and source not in ("employee", "candidates"):
        raise ValueError(f"source '{source}' ungültig; erlaubt: employee, candidates.")
    if status is not None and source is None:
        raise ValueError("status braucht source (employee oder candidates).")
    start_day, end_day = parse_day(start, "start"), parse_day(end, "end")
    if start_day and end_day and start_day > end_day:
        raise ValueError("start liegt nach end.")
    validate_status(source, status) if source else None
    if dimension is not None and source is None:
        raise ValueError("dimension braucht source (employee oder candidates).")
    topic = topic_for_dimension(source, dimension) if dimension is not None else None

    sources = [source] if source else ["candidates", "employee"]
    tagged = []
    for src in sources:
        rows = fetch_review_rows_in_range(src, company_id, start_day, end_day)
        tagged.extend({**row, "_source": src} for row in filter_by_status(rows, src, status))
    ordered = sort_newest_first(tagged)
    mentioning = [r for r in ordered if topic in topics_in_review(r, r["_source"])] if topic else []
    if topic_only:
        if dimension is None:
            raise ValueError("topic_only braucht dimension.")
        ordered = mentioning
    page = ordered[offset: offset + max(limit, 0)]

    def item(row: Dict[str, Any]) -> Dict[str, Any]:
        src = row.pop("_source")
        out = full_review_item(row, src) if full else _review_list_item(row, src)
        if topic is not None:
            out["mentions_topic"] = topic in topics_in_review(row, src)
            if full:
                texts = {"preview": out["preview"], **{k: out["fullReview"].get(k) for k in HIGHLIGHT_FIELDS}}
                spans = {k: topic_spans(v, topic, src) for k, v in texts.items()}
                out["highlights"] = {k: v for k, v in spans.items() if v}
        return out

    result = {
        "reviews": [item(dict(row)) for row in page],
        "total": len(ordered),
        "offset": offset,
        "limit": limit,
    }
    if dimension is not None:
        result["highlight"] = {
            "dimension": dimension,
            "topic": topic,
            "mentions": len(mentioning) if topic else None,
            "topic_only": topic_only,
        }
    return result


# Textfelder von fullReview, in denen Fundstellen markiert werden.
HIGHLIGHT_FIELDS = (
    "titel", "gut_am_arbeitgeber", "schlecht_am_arbeitgeber", "verbesserungsvorschlaege",
    "stellenbeschreibung", "jobbeschreibung",
)


@router.get("/company/{company_id}/reviews")
def get_company_reviews(
    company_id: int,
    limit: int = Query(default=50, description="Maximum number of reviews to return"),
    source: Optional[str] = Query(default=None, description="Filter by source: 'candidates' or 'employee'"),
    start: Optional[str] = Query(default=None, description="Erster Tag (YYYY-MM-DD, einschließlich)"),
    end: Optional[str] = Query(default=None, description="Letzter Tag (YYYY-MM-DD, einschließlich)"),
    status: Optional[str] = Query(default=None, description="Statusschlüssel der Bewertendengruppe, braucht source"),
    offset: Optional[int] = Query(default=None, ge=0, description="Anzahl übersprungener Bewertungen"),
    format_: Optional[Literal["full"]] = Query(default=None, alias="format", description="'full': je Bewertung id, preview, fullReview"),
    dimension: Optional[str] = Query(default=None, description="Dimension; markiert Fundstellen des zugehörigen Schlüsselwort-Themas, braucht source"),
    topic_only: bool = Query(default=False, description="Nur Bewertungen, die das Thema der Dimension nennen; braucht dimension"),
):
    """Get detailed reviews for a company.

    Ohne ``start``, ``end``, ``status``, ``offset`` und ``format`` unverändert:
    die neuesten ``limit`` Bewertungen (ohne ``source`` je Quelle ``limit // 2``).

    Mit mindestens einem dieser Parameter (Inkrement 2): alle Bewertungen mit
    ``start <= datum <= end`` (Tage einschließlich) und dem Status ``status``,
    vollständig paginiert gelesen, nach Datum absteigend; davon ``limit`` ab
    ``offset``. ``total`` ist die Zahl aller Treffer. Mit ``format=full`` hat
    jede Bewertung ``id``, ``preview`` (Textauszug) und ``fullReview`` (Format der
    Themenübersicht für ``ReviewDetailModal``). Ungültige Angaben: 400.

    Mit ``dimension`` (z. B. ``image``, braucht ``source``): ``highlight`` nennt das
    zugehörige Schlüsselwort-Thema (E10) und wie viele Bewertungen des Zeitraums es
    nennen (``mentions``); jede Bewertung hat ``mentions_topic`` und mit
    ``format=full`` ``highlights``: je Textfeld (``preview``, ``titel``,
    ``gut_am_arbeitgeber``, …) die Fundstellen ``[[start, ende], ...]``
    (Zeichenpositionen im gelieferten Text, Ende exklusiv). Für die
    Gesamtbewertung ist ``topic`` None. ``topic_only=true`` liefert nur die
    Bewertungen, die das Thema nennen; ``total`` zählt dann nur diese.
    """
    if any(p is not None for p in (start, end, status, offset, format_, dimension)):
        try:
            return _reviews_in_range(
                company_id, source, start, end, status, offset or 0, limit, full=format_ == "full",
                dimension=dimension, topic_only=topic_only,
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error fetching reviews: {str(e)}")

    supabase = get_supabase_client()
    try:
        reviews = []
        
        if source is None or source == "candidates":
            candidates_response = supabase.table("candidates")\
                .select("*")\
                .eq("company_id", company_id)\
                .order("datum", desc=True)\
                .limit(limit if source == "candidates" else limit // 2)\
                .execute()
            
            for item in candidates_response.data or []:
                reviews.append(_review_list_item(item, "candidates"))
        
        if source is None or source == "employee":
            employee_response = supabase.table("employee")\
                .select("*")\
                .eq("company_id", company_id)\
                .order("datum", desc=True)\
                .limit(limit if source == "employee" else limit // 2)\
                .execute()
            
            for item in employee_response.data or []:
                reviews.append(_review_list_item(item, "employee"))
        
        # Sort by date
        reviews.sort(key=lambda x: x.get("date") or "", reverse=True)
        
        return {
            "reviews": reviews[:limit],
            "total": len(reviews)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching reviews: {str(e)}")


@router.get("/company/{company_id}/negative-topics")
def get_negative_topics(company_id: int):
    """Get the most mentioned negative topics."""
    supabase = get_supabase_client()
    try:
        # Get employee negative feedback
        employee_response = supabase.table("employee")\
            .select("schlecht_am_arbeitgeber_finde_ich, durchschnittsbewertung")\
            .eq("company_id", company_id)\
            .execute()
        
        # Get candidate improvement suggestions
        candidates_response = supabase.table("candidates")\
            .select("verbesserungsvorschlaege, durchschnittsbewertung")\
            .eq("company_id", company_id)\
            .execute()
        
        employee_data = employee_response.data or []
        candidates_data = candidates_response.data or []
        
        # Collect negative texts
        negative_texts = []
        for item in employee_data:
            if item.get("schlecht_am_arbeitgeber_finde_ich"):
                negative_texts.append(item["schlecht_am_arbeitgeber_finde_ich"])
        
        for item in candidates_data:
            if item.get("verbesserungsvorschlaege"):
                negative_texts.append(item["verbesserungsvorschlaege"])
        
        # Simple keyword analysis (can be enhanced with NLP)
        keywords = {}
        negative_keywords = [
            "gehalt", "kommunikation", "management", "work-life-balance", 
            "stress", "überstunden", "kollegen", "chef", "führung",
            "bezahlung", "karriere", "entwicklung", "atmosphäre"
        ]
        
        for text in negative_texts:
            text_lower = text.lower()
            for keyword in negative_keywords:
                if keyword in text_lower:
                    keywords[keyword] = keywords.get(keyword, 0) + 1
        
        # Sort by frequency
        sorted_topics = sorted(keywords.items(), key=lambda x: x[1], reverse=True)
        
        return {
            "negative_topics": [
                {"topic": topic, "count": count} 
                for topic, count in sorted_topics[:10]
            ],
            "total_negative_mentions": sum(keywords.values())
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching negative topics: {str(e)}")


@router.get("/company/{company_id}/topic-overview")
def get_topic_overview(
    company_id: int,
    source: Optional[str] = Query(default=None, description="Filter by source: 'candidates' or 'employee'"),
    start_date: Optional[str] = Query(default=None, description="Filter reviews from this date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(default=None, description="Letzter Tag (YYYY-MM-DD, einschließlich)"),
):
    """
    Get topic overview data formatted for the frontend TopicOverviewCard.

    This endpoint analyzes reviews and extracts topics with their frequency,
    average rating, sentiment, and timeline data - matching the format of
    the dummy data in TopicOverviewCard.jsx.

    Args:
        company_id: Company ID to analyze
        source: Optional filter - 'candidates' for Bewerber or 'employee' for Mitarbeiter
        start_date: Optional date string (YYYY-MM-DD) to filter reviews from that date onward
        end_date: Optional date string (YYYY-MM-DD), letzter Tag einschließlich
            (Inkrement 2); ohne den Parameter ist die Antwort unverändert.

    Themen-Definitionen und ``analyze_topic`` stehen in
    ``services/keyword_topic_service.py``.

    Alle Bewertungen werden seitenweise gelesen (nach ``id`` sortiert); bis
    2026-10-04 las die Route je Quelle nur eine Abfrage und damit höchstens
    1000 Zeilen (PostgREST-Grenze). Seit 2026-10-05 werden die Seiten nach der
    ersten parallel geholt (``fetch_all_rows_parallel``).
    """
    try:
        end_day = parse_day(end_date, "end_date")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    # Bis einschließlich end_date: datum ist ein Zeitstempel, daher "< Folgetag".
    end_exclusive = (end_day + timedelta(days=1)).isoformat() if end_day else None
    try:
        # Get reviews based on source filter
        candidates_data = []
        employee_data = []

        def review_query(table: str):
            # Baut die Abfrage je Aufruf neu, auch in den Threads des parallelen
            # Seitenabrufs (jeder mit eigenem Supabase-Client).
            def build(count=None):
                query = get_supabase_client().table(table).select("*", count=count).eq("company_id", company_id)
                if start_date:
                    query = query.gte("datum", start_date)
                if end_exclusive:
                    query = query.lt("datum", end_exclusive)
                return query.order("id")
            return build

        if source is None or source == "candidates":
            candidates_data = fetch_all_rows_parallel(review_query("candidates"), page_size=review_service.PAGE_SIZE)

        if source is None or source == "employee":
            employee_data = fetch_all_rows_parallel(review_query("employee"), page_size=review_service.PAGE_SIZE)
        
        all_reviews = candidates_data + employee_data
        
        if not all_reviews:
            return {
                "topics": [],
                "total_reviews": 0,
                "message": "No reviews found for this company"
            }
        
        # Wähle die richtigen Topic-Definitionen basierend auf der Quelle
        topic_definitions = topic_definitions_for(source)
        if source == "employee":
            reviews_to_analyze = employee_data
        elif source == "candidates":
            reviews_to_analyze = candidates_data
        else:
            # Wenn keine Quelle angegeben oder "alle", kombiniere beide
            reviews_to_analyze = all_reviews
        
        # Analyze each topic
        topics_data = []
        
        for topic_name, topic_config in topic_definitions.items():
            topic_analysis = analyze_topic(
                topic_name=topic_name,
                keywords=topic_config["keywords"],
                rating_fields=topic_config["rating_fields"],
                all_reviews=reviews_to_analyze
            )
            
            if topic_analysis["frequency"] > 0:  # Only include topics that were found
                topics_data.append(topic_analysis)
        
        # Sort by frequency
        topics_data.sort(key=lambda x: x["frequency"], reverse=True)
        
        # Add IDs
        for idx, topic in enumerate(topics_data, start=1):
            topic["id"] = idx
        
        # STATISTICAL ENRICHMENT: Add statistical metadata to each topic
        total_reviews = len(reviews_to_analyze)
        enriched_topics = enrich_topic_analysis_with_metadata(topics_data, total_reviews)
        
        # Add overall statistical assessment
        result = {
            "topics": enriched_topics,
            "total_reviews": total_reviews,
            "total_topics": len(enriched_topics)
        }
        
        # Add overall statistical metadata
        result = enrich_with_statistical_metadata(
            result,
            sample_size=total_reviews,
            analysis_type="anova"
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating topic overview: {str(e)}")

#sara: topicRatingCard
@router.get("/company/{company_id}/topic-ratings-timeseries")
def topic_ratings_timeseries(
    company_id: int,
    source: Literal["employee", "candidates"] = Query(..., description="employee or candidates"),
    granularity: Literal["month", "year"] = Query("month", description="month or year"),
    start: Optional[str] = Query(None, description="ISO date/time, e.g. 2023-01-01"),
    end: Optional[str] = Query(None, description="ISO date/time, e.g. 2024-12-31"),
):
    """
    Returns average star-ratings per topic grouped by month/year for a company.
    Output format fits a line chart: [{period: 'YYYY-MM', topicA: 3.2, ...}, ...]
    """
    try:
        return get_topic_rating_timeseries(
            source=source,
            company_id=company_id,
            granularity=granularity,
            start=start,
            end=end,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error building topic ratings timeseries: {str(e)}")


def extract_short_kritikpunkt(text: str, max_words: int = 4) -> str:
    """
    Extrahiert einen kurzen, sinnvollen Kritikpunkt aus einem negativen Text (2-4 Wörter).
    Fokussiert auf negative Phrasen wie "schlechte Kommunikation", "keine Wertschätzung".
    """
    if not text or not isinstance(text, str):
        return ""
    
    # Clean text
    text = clean_html_text(text)
    text = re.sub(r'\s+', ' ', text).strip().lower()
    
    # 1. PRIORITÄT: Suche nach typischen negativen Mustern
    negative_patterns = [
        # "keine/kein X" Muster
        r'keine?\s+(\w+)',
        # "schlechte/r/s X" Muster  
        r'schlechte[rns]?\s+(\w+)',
        # "fehlende X" Muster
        r'fehlende[rns]?\s+(\w+)',
        # "mangelnde X" Muster
        r'mangelnde[rns]?\s+(\w+)',
        # "wenig X" Muster
        r'wenig\s+(\w+)',
        # "zu wenig X" Muster
        r'zu\s+wenig\s+(\w+)',
        # "kaum X" Muster
        r'kaum\s+(\w+)',
    ]
    
    # Negative Adjektive die wir behalten wollen
    negative_adjectives = {
        'schlechte', 'schlechter', 'schlechtes', 'schlecht',
        'fehlende', 'fehlender', 'fehlendes', 'fehlend',
        'mangelnde', 'mangelnder', 'mangelndes', 'mangelnd',
        'keine', 'kein', 'keiner', 'keines',
        'wenig', 'kaum', 'niedrige', 'niedriger', 'niedriges',
        'unklare', 'unklarer', 'unklares',
        'langsame', 'langsamer', 'langsames',
        'starre', 'starrer', 'starres',
        'veraltete', 'veralteter', 'veraltetes',
        'toxische', 'toxischer', 'toxisches',
    }
    
    # Wichtige Substantive für Kritik
    important_nouns = {
        'kommunikation', 'führung', 'management', 'vorgesetzte', 'chef',
        'gehalt', 'bezahlung', 'vergütung', 'wertschätzung', 'respekt',
        'transparenz', 'feedback', 'entwicklung', 'karriere', 'weiterbildung',
        'arbeitsatmosphäre', 'atmosphäre', 'klima', 'kultur', 'umgang',
        'prozesse', 'strukturen', 'entscheidungen', 'hierarchie',
        'work-life-balance', 'überstunden', 'arbeitszeit', 'druck',
        'zusammenhalt', 'teamarbeit', 'kollegen', 'mitarbeiter',
    }
    
    # Suche nach Mustern
    for pattern in negative_patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            if match in important_nouns or len(match) > 5:
                # Finde das vollständige Match mit Adjektiv
                full_match = re.search(rf'(\w+\s+{match})', text)
                if full_match:
                    result = full_match.group(1).strip()
                    # Kapitalisiere
                    return result[0].upper() + result[1:]
    
    # 2. FALLBACK: Suche nach negativem Adjektiv + Substantiv
    words = text.split()
    for i, word in enumerate(words):
        clean_word = re.sub(r'[^\wäöüß]', '', word)
        if clean_word in negative_adjectives and i + 1 < len(words):
            next_word = re.sub(r'[^\wäöüß]', '', words[i + 1])
            if len(next_word) >= 4:
                result = f"{clean_word} {next_word}"
                return result[0].upper() + result[1:]
    
    # 3. LETZTER FALLBACK: Nimm wichtiges Substantiv allein
    for word in words:
        clean_word = re.sub(r'[^\wäöüß]', '', word)
        if clean_word in important_nouns:
            return clean_word[0].upper() + clean_word[1:]
    
    return ""
    
    return ""


@router.get("/company/{company_id}/negative-kritikpunkte")
def get_negative_kritikpunkte(company_id: int):
    """
    Findet das negativste Topic und extrahiert 2 kurze Kritikpunkte 
    aus den schlechtesten Bewertungen.
    
    Returns:
        {
            "topic": "Führungsqualität",
            "kritikpunkte": ["schlechte Kommunikation", "keine Wertschätzung"],
            "avg_rating": 1.8,
            "negative_share_percent": 70
        }
    """
    supabase = get_supabase_client()
    try:
        # Hole Employee-Daten (haben meist mehr kritische Bewertungen)
        employee_response = supabase.table("employee")\
            .select("*")\
            .eq("company_id", company_id)\
            .execute()
        
        employee_data = employee_response.data or []
        
        if not employee_data:
            return {
                "topic": None,
                "kritikpunkte": [],
                "avg_rating": None,
                "negative_share_percent": None,
                "message": "Keine Bewertungen gefunden"
            }
        
        # Finde die schlechtesten Bewertungen (Rating <= 2.5)
        negative_reviews = [
            r for r in employee_data 
            if r.get("durchschnittsbewertung") and float(r["durchschnittsbewertung"]) <= 2.5
        ]
        
        # Wenn nicht genug negative, nimm die schlechtesten allgemein
        if len(negative_reviews) < 2:
            sorted_reviews = sorted(
                [r for r in employee_data if r.get("durchschnittsbewertung")],
                key=lambda x: float(x["durchschnittsbewertung"])
            )
            negative_reviews = sorted_reviews[:5]
        
        # Sortiere nach Rating (niedrigste zuerst)
        negative_reviews.sort(key=lambda x: float(x.get("durchschnittsbewertung", 5)))
        
        # Extrahiere Kritikpunkte NUR aus "schlecht_am_arbeitgeber_finde_ich"
        kritikpunkte = []
        seen_texts = set()
        
        for review in negative_reviews:
            # NUR aus schlecht_am_arbeitgeber - das ist garantiert negativ!
            text = review.get("schlecht_am_arbeitgeber_finde_ich", "")
            
            if not text or not isinstance(text, str) or len(text.strip()) < 10:
                continue
            
            # Extrahiere mehrere Sätze aus dem Text
            sentences = re.split(r'[.!?\n]+', text)
            for sentence in sentences:
                sentence = sentence.strip()
                if len(sentence) < 15:
                    continue
                    
                kritikpunkt = extract_short_kritikpunkt(sentence, max_words=4)
                
                # Vermeide Duplikate und zu kurze Ergebnisse
                if kritikpunkt and len(kritikpunkt) >= 8 and kritikpunkt.lower() not in seen_texts:
                    kritikpunkte.append(kritikpunkt)
                    seen_texts.add(kritikpunkt.lower())
                
                if len(kritikpunkte) >= 2:
                    break
            
            if len(kritikpunkte) >= 2:
                break
        
        # Bestimme das Haupt-Topic basierend auf Keywords
        topic_keywords = {
            "Führungsqualität": ["führung", "vorgesetzte", "chef", "management", "leitung"],
            "Kommunikation": ["kommunikation", "information", "transparenz", "feedback"],
            "Gehalt & Benefits": ["gehalt", "bezahlung", "lohn", "vergütung", "benefits"],
            "Work-Life Balance": ["work-life", "überstunden", "arbeitszeit", "balance"],
            "Teamzusammenhalt": ["team", "kollegen", "zusammenhalt", "atmosphäre"],
            "Karriereentwicklung": ["karriere", "weiterbildung", "entwicklung", "aufstieg"]
        }
        
        # Zähle Keyword-Treffer in negativen Reviews
        topic_scores = defaultdict(int)
        for review in negative_reviews:
            text_fields = [
                review.get("schlecht_am_arbeitgeber_finde_ich", ""),
                review.get("verbesserungsvorschlaege", ""),
                review.get("titel", "")
            ]
            combined_text = " ".join(str(t) for t in text_fields if t).lower()
            
            for topic, keywords in topic_keywords.items():
                for keyword in keywords:
                    if keyword in combined_text:
                        topic_scores[topic] += 1
        
        # Wähle das Topic mit den meisten Treffern
        main_topic = max(topic_scores.items(), key=lambda x: x[1])[0] if topic_scores else "Allgemein"
        
        # Berechne Statistiken
        total_reviews = len(employee_data)
        negative_count = len([r for r in employee_data if r.get("durchschnittsbewertung") and float(r["durchschnittsbewertung"]) <= 2.5])
        negative_share = round((negative_count / total_reviews) * 100) if total_reviews > 0 else 0
        
        avg_rating = sum(float(r["durchschnittsbewertung"]) for r in negative_reviews if r.get("durchschnittsbewertung")) / len(negative_reviews) if negative_reviews else None
        
        return {
            "topic": main_topic,
            "kritikpunkte": kritikpunkte[:2],
            "avg_rating": round(avg_rating, 1) if avg_rating else None,
            "negative_share_percent": negative_share,
            "categories": [main_topic]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# STATISTICAL VALIDATION ENDPOINTS
# ============================================================================

@router.get("/statistical/validate-sample-size")
def validate_sample_size(
    n: int = Query(..., description="Sample size to validate", ge=1)
) -> Dict[str, Any]:
    """
    Validate sample size adequacy for statistical analysis.
    
    Returns comprehensive assessment including:
    - Risk level (limited/constrained/acceptable/solid)
    - CLT approximation quality
    - Power considerations
    - Confidence interval width estimate
    - Methodological recommendations
    
    Based on established literature:
    - Rice (2006): CLT heuristic n≈30
    - Cohen (1988): Power analysis n≈64 for d=0.5
    - Maxwell et al. (2008): AIPE approach n≈100 for MoE≤±0.20
    """
    try:
        validator = StatisticalValidator()
        assessment = validator.assess_sample_size(n)
        return assessment.to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/statistical/validate-comparison")
def validate_comparison(
    n1: int = Query(..., description="Size of group 1 (or total n for ANOVA)", ge=1),
    n2: int = Query(..., description="Size of group 2 (or k groups for ANOVA)", ge=1),
    comparison_type: Literal["two_group", "anova"] = Query(
        "two_group", 
        description="Type of comparison: two_group (t-test) or anova"
    )
) -> Dict[str, Any]:
    """
    Validate sample sizes for group comparisons.
    
    For two_group (t-test):
    - n1, n2 = sizes of the two groups
    - Returns assessment for both groups
    
    For anova:
    - n1 = total sample size
    - n2 = number of groups (k)
    - Returns assessment based on average group size
    """
    try:
        validator = StatisticalValidator()
        assessment = validator.assess_comparison(n1, n2, comparison_type)
        return assessment
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/statistical/validate-correlation")
def validate_correlation(
    n: int = Query(..., description="Sample size for correlation analysis", ge=1)
) -> Dict[str, Any]:
    """
    Validate sample size for correlation analysis.
    
    Based on Schönbrodt & Perugini (2013): 
    Correlations stabilize around n≈250
    """
    try:
        validator = StatisticalValidator()
        assessment = validator.validate_correlation_stability(n)
        return assessment
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/company/{company_id}/statistical-assessment")
def get_company_statistical_assessment(company_id: int) -> Dict[str, Any]:
    """
    Get comprehensive statistical assessment for company's review data.
    
    Includes:
    - Sample size validation for employee and candidate reviews
    - Topic-wise sample size assessment (ANOVA context)
    - Recommendations for statistical analysis
    """
    supabase = get_supabase_client()
    try:
        validator = StatisticalValidator()
        
        # Get employee reviews count
        employee_response = supabase.table("employee")\
            .select("id", count="exact")\
            .eq("company_id", company_id)\
            .execute()
        
        # Get candidate reviews count
        candidate_response = supabase.table("candidates")\
            .select("id", count="exact")\
            .eq("company_id", company_id)\
            .execute()
        
        employee_count = employee_response.count or 0
        candidate_count = candidate_response.count or 0
        total_count = employee_count + candidate_count
        
        # Overall assessment
        overall_assessment = validator.assess_sample_size(total_count)
        
        # Employee-specific assessment
        employee_assessment = validator.assess_sample_size(employee_count)
        
        # Candidate-specific assessment
        candidate_assessment = validator.assess_sample_size(candidate_count)
        
        # Comparison assessment (employee vs candidate)
        comparison_assessment = validator.assess_comparison(
            employee_count, 
            candidate_count, 
            "two_group"
        ) if employee_count > 0 and candidate_count > 0 else None
        
        # Topic analysis considerations (for ANOVA)
        # Assuming 13 topics as per methodology document
        k_topics = 13
        topic_assessment = validator.assess_comparison(
            total_count,
            k_topics,
            "anova"
        ) if total_count > 0 else None
        
        return {
            "company_id": company_id,
            "sample_sizes": {
                "total": total_count,
                "employee": employee_count,
                "candidate": candidate_count
            },
            "overall_assessment": overall_assessment.to_dict(),
            "employee_assessment": employee_assessment.to_dict(),
            "candidate_assessment": candidate_assessment.to_dict(),
            "comparison_assessment": comparison_assessment,
            "topic_anova_assessment": topic_assessment,
            "summary": {
                "data_quality": overall_assessment.risk_level.value,
                "can_compare_employee_candidate": employee_count >= 30 and candidate_count >= 30,
                "can_perform_topic_analysis": total_count >= (k_topics * 30),
                "primary_limitation": (
                    "Sample size below CLT heuristic - prefer non-parametric tests"
                    if total_count < validator.HEURISTIC_CLT
                    else "Power may be insufficient for small effects"
                    if total_count < validator.HEURISTIC_POWER
                    else "Confidence intervals may be wide"
                    if total_count < validator.HEURISTIC_PRECISION
                    else "Sample size adequate for robust analysis"
                )
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

        raise HTTPException(status_code=500, detail=f"Error fetching negative kritikpunkte: {str(e)}")