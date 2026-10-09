"""
Schlüsselwort-Themen der Kununu-Bewertungen (Zyklus 2, Inkrement 2, E10).

Die Themen-Definitionen je Quelle und ``analyze_topic`` standen bis Inkrement 1
in ``routes/analytics.py`` (Themenübersicht ``topic-overview``). Sie sind hierher
umgezogen, damit der Vorher-Nachher-Vergleich (``explanation_service``) dieselben
Themen nutzt, ohne ein Route-Modul zu importieren. Die Ausgabe von
``topic-overview`` ist unverändert.

Ein Thema gilt in einer Bewertung als genannt, wenn eines seiner Schlüsselwörter
(regulärer Ausdruck, Groß-/Kleinschreibung egal) in einem der Textfelder
``TOPIC_TEXT_FIELDS`` vorkommt. Die Schlüsselwörter sind deutsch; englische Texte
werden kaum erfasst (siehe E10).

- ``topic_definitions_for(source)``: Definitionen der Quelle; ohne Quelle beide
  zusammen (Bewerber-Themen überschreiben gleichnamige, wie bisher).
- ``topics_in_review(row, source)``: Namen der genannten Themen, reine Funktion.
- ``analyze_topic(...)``: Kennzahlen eines Themas für die Themenübersicht.
"""

from __future__ import annotations

import re
from collections import defaultdict
from datetime import datetime
from functools import lru_cache
from typing import Any, Dict, List, Optional

from services.review_service import build_full_review, clean_html_text

# Textfelder, in denen nach Schlüsselwörtern gesucht wird (beide Quellen).
TOPIC_TEXT_FIELDS: List[str] = [
    'stellenbeschreibung', 'verbesserungsvorschlaege',  # candidates
    'jobbeschreibung', 'gut_am_arbeitgeber_finde_ich',  # employee
    'schlecht_am_arbeitgeber_finde_ich', 'titel'
]

# NFA-07 (Inkrement 6, 2026-10-09): Aus diesen Feldern stammt nie ein
# Beispielzitat (``example``, ``typicalStatements``, ``reviewDetails[].preview``
# für Topic-Tabelle, Topic-Details und PDF). Sie beschreiben Tätigkeit oder
# Stelle und können Rückschlüsse auf einzelne Personen erlauben. Für die
# Erkennung eines Themas (Häufigkeit, Bewertung, Stimmung) zählen sie weiter
# mit; die Topic-Berechnung aus Zyklus 1 bleibt unverändert.
QUOTE_EXCLUDED_FIELDS: tuple = ('jobbeschreibung', 'stellenbeschreibung')


EMPLOYEE_TOPIC_DEFINITIONS: Dict[str, Dict[str, List[str]]] = {
    "Work-Life Balance": {
        "keywords": [
            r'\bwork[\s-]*life[\s-]*balance\b',
            r'\büberstunden\b',
            r'\barbeitszeit\b',
            r'\burlaub\b',
            r'\bfreizeit\b',
            r'\bprivatleben\b',
            r'\bflexibilität\b',
            r'\bhomeoffice\b',
            r'\berreichbarkeit\b'
        ],
        "rating_fields": ["sternebewertung_work_life_balance"]
    },
    "Vorgesetztenverhalten": {
        "keywords": [
            r'\bführung\b',
            r'\bmanagement\b',
            r'\bvorgesetzte\b',
            r'\bchef\b',
            r'\bleitung\b',
            r'\bführungskräfte\b',
            r'\bvorgesetztenverhalten\b',
            r'\bkompetenz\b',
            r'\bentscheidung\b'
        ],
        "rating_fields": ["sternebewertung_vorgesetztenverhalten"]
    },
    "Gehalt & Sozialleistungen": {
        "keywords": [
            r'\bgehalt\b',
            r'\bbezahlung\b',
            r'\blohn\b',
            r'\bvergütung\b',
            r'\bbenefits\b',
            r'\bsozialleistungen\b',
            r'\baltersvorsorge\b',
            r'\bprämie\b',
            r'\bbonus\b'
        ],
        "rating_fields": ["sternebewertung_gehalt_sozialleistungen"]
    },
    "Kollegenzusammenhalt": {
        "keywords": [
            r'\bteam\b',
            r'\bkollegen\b',
            r'\bzusammenhalt\b',
            r'\bkollegenzusammenhalt\b',
            r'\bzusammenarbeit\b',
            r'\bgemeinschaft\b'
        ],
        "rating_fields": ["sternebewertung_kollegenzusammenhalt"]
    },
    "Karriere & Weiterbildung": {
        "keywords": [
            r'\bkarriere\b',
            r'\bweiterbildung\b',
            r'\bentwicklung\b',
            r'\baufstieg\b',
            r'\bförderung\b',
            r'\bschulungen\b',
            r'\bbeförderung\b',
            r'\bperspektive\b'
        ],
        "rating_fields": ["sternebewertung_karriere_weiterbildung"]
    },
    "Kommunikation": {
        "keywords": [
            r'\bkommunikation\b',
            r'\binformation\b',
            r'\btransparenz\b',
            r'\bfeedback\b',
            r'\bgespräch\b',
            r'\baustausch\b',
            r'\brückmeldung\b'
        ],
        "rating_fields": ["sternebewertung_kommunikation"]
    },
    "Arbeitsbedingungen": {
        "keywords": [
            r'\barbeitsbedingungen\b',
            r'\bausstattung\b',
            r'\bbüro\b',
            r'\barbeitsplatz\b',
            r'\btechnik\b',
            r'\bumgebung\b',
            r'\binfrastruktur\b'
        ],
        "rating_fields": ["sternebewertung_arbeitsbedingungen"]
    },
    "Arbeitsatmosphäre": {
        "keywords": [
            r'\batmosphäre\b',
            r'\barbeitsatmosphäre\b',
            r'\barbeitsklima\b',
            r'\bstimmung\b',
            r'\bklima\b'
        ],
        "rating_fields": ["sternebewertung_arbeitsatmosphaere"]
    },
    "Image": {
        "keywords": [
            r'\bimage\b',
            r'\bruf\b',
            r'\breputation\b',
            r'\bansehen\b',
            r'\bbekanntheitsgrad\b'
        ],
        "rating_fields": ["sternebewertung_image"]
    },
    "Interessante Aufgaben": {
        "keywords": [
            r'\baufgaben\b',
            r'\btätigkeit\b',
            r'\binteressant\b',
            r'\bherausforderung\b',
            r'\babwechslung\b',
            r'\bvielfalt\b'
        ],
        "rating_fields": ["sternebewertung_interessante_aufgaben"]
    },
    "Umwelt- & Sozialbewusstsein": {
        "keywords": [
            r'\bumwelt\b',
            r'\bnachhaltigkeit\b',
            r'\bsozialbewusstsein\b',
            r'\bverantwortung\b',
            r'\böko\b',
            r'\bklima\b'
        ],
        "rating_fields": ["sternebewertung_umwelt_sozialbewusstsein"]
    },
    "Umgang mit älteren Kollegen": {
        "keywords": [
            r'\bältere kollegen\b',
            r'\balter\b',
            r'\bsenior\b',
            r'\berfahrung\b',
            r'\bumgang\b'
        ],
        "rating_fields": ["sternebewertung_umgang_mit_aelteren_kollegen"]
    },
    "Gleichberechtigung": {
        "keywords": [
            r'\bgleichberechtigung\b',
            r'\bdiversität\b',
            r'\bvielfalt\b',
            r'\bdiskriminierung\b',
            r'\bchancengleichheit\b',
            r'\binklusion\b'
        ],
        "rating_fields": ["sternebewertung_gleichberechtigung"]
    }
}


CANDIDATE_TOPIC_DEFINITIONS: Dict[str, Dict[str, List[str]]] = {
    "Erklärung der weiteren Schritte": {
        "keywords": [
            r'\bschritte\b',
            r'\bweitere schritte\b',
            r'\bprozess\b',
            r'\berklärung\b',
            r'\binformation\b',
            r'\bablauf\b'
        ],
        "rating_fields": ["sternebewertung_erklaerung_der_weiteren_schritte"]
    },
    "Zufriedenstellende Reaktion": {
        "keywords": [
            r'\breaktion\b',
            r'\brückmeldung\b',
            r'\bantwort\b',
            r'\bresponse\b',
            r'\bzufriedenstellend\b'
        ],
        "rating_fields": ["sternebewertung_zufriedenstellende_reaktion"]
    },
    "Vollständigkeit der Infos": {
        "keywords": [
            r'\binformation\b',
            r'\binfos\b',
            r'\bvollständig\b',
            r'\bdetail\b',
            r'\bausführlich\b'
        ],
        "rating_fields": ["sternebewertung_vollstaendigkeit_der_infos"]
    },
    "Zufriedenstellende Antworten": {
        "keywords": [
            r'\bantwort\b',
            r'\bfrage\b',
            r'\bzufriedenstellend\b',
            r'\bauskunft\b'
        ],
        "rating_fields": ["sternebewertung_zufriedenstellende_antworten"]
    },
    "Angenehme Atmosphäre": {
        "keywords": [
            r'\batmosphäre\b',
            r'\bangenehm\b',
            r'\bstimmung\b',
            r'\bklima\b',
            r'\bwohlbefinden\b'
        ],
        "rating_fields": ["sternebewertung_angenehme_atmosphaere"]
    },
    "Professionalität des Gesprächs": {
        "keywords": [
            r'\bprofessionalität\b',
            r'\bgespräch\b',
            r'\binterview\b',
            r'\bprofessionell\b',
            r'\bkompetent\b'
        ],
        "rating_fields": ["sternebewertung_professionalitaet_des_gespraechs"]
    },
    "Wertschätzende Behandlung": {
        "keywords": [
            r'\bwertschätzung\b',
            r'\bbehandlung\b',
            r'\brespekt\b',
            r'\bwertschätzend\b',
            r'\bhöflich\b'
        ],
        "rating_fields": ["sternebewertung_wertschaetzende_behandlung"]
    },
    "Erwartbarkeit des Prozesses": {
        "keywords": [
            r'\berwartbarkeit\b',
            r'\bprozess\b',
            r'\bvorhersehbar\b',
            r'\bstruktur\b',
            r'\borganisation\b'
        ],
        "rating_fields": ["sternebewertung_erwartbarkeit_des_prozesses"]
    },
    "Zeitgerechte Zu- oder Absage": {
        "keywords": [
            r'\bzusage\b',
            r'\babsage\b',
            r'\bzeitgerecht\b',
            r'\bpünktlich\b',
            r'\bfrist\b',
            r'\btermin\b'
        ],
        "rating_fields": ["sternebewertung_zeitgerechte_zu_oder_absage"]
    },
    "Schnelle Antwort": {
        "keywords": [
            r'\bschnell\b',
            r'\bantwort\b',
            r'\breaktionszeit\b',
            r'\bzügig\b',
            r'\bprompt\b'
        ],
        "rating_fields": ["sternebewertung_schnelle_antwort"]
    }
}


@lru_cache(maxsize=256)
def _compiled_keywords(keywords: tuple) -> tuple:
    """Muster eines Themas, einmal kompiliert: einzeln in Listenreihenfolge
    (sie bestimmt, welcher Satz zitiert wird) und als eine Alternation, die als
    Vorfilter ein Textfeld mit einem einzigen Suchlauf prüft. Die Muster sind
    einfache Wortmuster ohne Gruppen, die Alternation trifft daher genau dann,
    wenn eines der einzelnen Muster trifft."""
    single = tuple(re.compile(p, re.IGNORECASE) for p in keywords)
    combined = re.compile("|".join(f"(?:{p})" for p in keywords), re.IGNORECASE)
    return single, combined


def analyze_topic(
    topic_name: str,
    keywords: List[str],
    rating_fields: List[str],
    all_reviews: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Analyze a specific topic across all reviews.
    
    Returns a dictionary matching the format expected by TopicOverviewCard.jsx
    """
    # Text fields to search
    text_fields = TOPIC_TEXT_FIELDS
    keyword_res, any_keyword = _compiled_keywords(tuple(keywords))
    
    # Find mentions and collect data
    mentions = []
    ratings = []
    monthly_ratings = defaultdict(list)
    example_texts = []
    typical_statements = []
    review_details = []
    
    for review in all_reviews:
        # Check if topic is mentioned in text fields
        mentioned = False
        mention_texts = []
        full_review_text = []
        
        for field in text_fields:
            text = review.get(field, "")
            if text and isinstance(text, str):
                text_lower = text.lower()
                # Vorfilter: ein Suchlauf für alle Muster; ohne Treffer ist das Feld erledigt.
                if not any_keyword.search(text_lower):
                    continue
                for keyword_re in keyword_res:
                    if keyword_re.search(text_lower):
                        mentioned = True
                        # Extract sentence containing keyword (nie aus den Feldern in QUOTE_EXCLUDED_FIELDS, NFA-07)
                        sentences = re.split(r'[.!?]+', text) if field not in QUOTE_EXCLUDED_FIELDS else []
                        for sentence in sentences:
                            if keyword_re.search(sentence) and len(sentence.strip()) > 20:
                                mention_texts.append(sentence.strip())
                                break
                        
                        # Collect full text from all relevant fields
                        full_review_text.append(f"{field}: {text}")
                        break
        
        if mentioned:
            mentions.append(review)
            
            # Collect example texts with full review details
            if mention_texts:
                for text in mention_texts[:3]:
                    example_texts.append(clean_html_text(text))
                    review_details.append({
                        "id": review.get("id"),
                        "preview": clean_html_text(text),
                        "fullReview": build_full_review(review),
                    })
            
            # Collect ratings — topic-specific fields take priority.
            # Using both durchschnittsbewertung AND the specific field would
            # double-count and bias the topic average toward the overall mean.
            topic_specific = []
            for field in rating_fields:
                field_rating = review.get(field)
                if field_rating is not None:
                    try:
                        topic_specific.append(float(field_rating))
                    except (TypeError, ValueError):
                        pass

            if topic_specific:
                ratings.extend(topic_specific)
            else:
                # No topic-specific rating available — use overall avg as fallback
                avg_rating_val = review.get("durchschnittsbewertung")
                if avg_rating_val is not None:
                    try:
                        ratings.append(float(avg_rating_val))
                    except (TypeError, ValueError):
                        pass
            
            # Group by month for timeline
            date_str = review.get("datum")
            if date_str:
                try:
                    date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                    month_key = date.strftime("%b")
                    if avg_rating:
                        monthly_ratings[month_key].append(float(avg_rating))
                except:
                    pass
    
    # Calculate average rating
    avg_rating = round(sum(ratings) / len(ratings), 1) if ratings else 0.0
    
    # Determine sentiment based on rating
    if avg_rating >= 3.5:
        sentiment = "Positiv"
        color = "green"
    elif avg_rating >= 2.5:
        sentiment = "Neutral"
        color = "orange"
    else:
        sentiment = "Negativ"
        color = "red"
    
    # Create timeline data (all available months, sorted chronologically)
    timeline_data = []
    months_order = ["Jan", "Feb", "Mär", "Apr", "Mai", "Jun", "Jul", "Aug", "Sep", "Okt", "Nov", "Dez"]
    
    # Collect all dates from reviews to determine the full time range
    all_dates = []
    for review in mentions:
        date_str = review.get("datum")
        if date_str:
            try:
                date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                all_dates.append(date)
            except:
                pass
    
    if all_dates:
        # Find the earliest and latest dates
        min_date = min(all_dates)
        max_date = max(all_dates)
        
        # Generate all months between min and max date
        current_date = min_date.replace(day=1)
        end_date = max_date.replace(day=1)
        
        # Create a dictionary to store month-year combinations with their ratings
        monthly_data = defaultdict(list)
        for review in mentions:
            date_str = review.get("datum")
            avg_rating_review = review.get("durchschnittsbewertung")
            if date_str and avg_rating_review:
                try:
                    date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                    month_year_key = f"{months_order[date.month - 1]} {date.year}"
                    monthly_data[month_year_key].append(float(avg_rating_review))
                except:
                    pass
        
        # Generate timeline for all months in range
        while current_date <= end_date:
            month_name = months_order[current_date.month - 1]
            month_year_key = f"{month_name} {current_date.year}"
            
            if month_year_key in monthly_data and monthly_data[month_year_key]:
                month_avg = sum(monthly_data[month_year_key]) / len(monthly_data[month_year_key])
                timeline_data.append({
                    "month": month_year_key,
                    "rating": round(month_avg, 1),
                    "year": current_date.year,
                    "monthNum": current_date.month
                })
            
            # Move to next month
            if current_date.month == 12:
                current_date = current_date.replace(year=current_date.year + 1, month=1)
            else:
                current_date = current_date.replace(month=current_date.month + 1)
    
    # Select typical statements (up to 13 most relevant - 3 for "Typische Aussagen" + 10 for "Beispiel-Review")
    # Score each statement by relevance instead of random selection
    def _richness_score(detail):
        """Score a review by how complete its text content is across all fields."""
        fr = detail.get("fullReview") or {}
        fields = [
            fr.get("gut_am_arbeitgeber", "") or "",
            fr.get("schlecht_am_arbeitgeber", "") or "",
            fr.get("verbesserungsvorschlaege", "") or "",
            fr.get("stellenbeschreibung", "") or "",
            fr.get("jobbeschreibung", "") or "",
        ]
        filled = sum(1 for f in fields if len(f.strip()) > 20)
        total_chars = sum(len(f) for f in fields)
        gut = fr.get("gut_am_arbeitgeber", "") or ""
        schlecht = fr.get("schlecht_am_arbeitgeber", "") or ""
        both_bonus = 15 if (len(gut.strip()) > 20 and len(schlecht.strip()) > 20) else 0
        return filled * 10 + both_bonus + min(total_chars / 100, 20)

    if review_details:
        # Score each review_detail by how "typical"/representative it is
        def score_statement(detail):
            text = detail.get("preview", "")
            text_lower = text.lower()
            score = 0.0

            # 1. Keyword density: more keyword matches = more relevant
            keyword_hits = 0
            for kw in keywords:
                keyword_hits += len(re.findall(kw, text_lower, re.IGNORECASE))
            score += keyword_hits * 10

            # 2. Ideal sentence length (40-200 chars is most readable/informative)
            length = len(text)
            if 40 <= length <= 200:
                score += 8
            elif 25 <= length <= 300:
                score += 4
            elif length > 300:
                score += 1  # too long, less "typical"
            # very short (<25) gets 0 bonus

            # 3. Penalize generic/uninformative text
            generic_patterns = [
                r'^(ja|nein|ok|gut|schlecht|nichts|keine ahnung|kein kommentar)',
                r'^(s\.?\s*o\.?|siehe oben|wie gesagt)',
                r'^[-–—•\s]*$',
            ]
            for pattern in generic_patterns:
                if re.search(pattern, text_lower.strip()):
                    score -= 15

            # 4. Bonus for substantive content (contains verbs/descriptive words)
            substantive_indicators = [
                r'\b(ist|sind|war|wurde|haben|kann|sollte|muss|finde|denke|fühle)\b',
                r'\b(sehr|besonders|leider|leicht|schwer|gut|toll|super|schlecht|mangelhaft)\b',
            ]
            for pattern in substantive_indicators:
                if re.search(pattern, text_lower):
                    score += 2

            # 5. Review richness: prioritize reviews with more filled text fields
            score += _richness_score(detail) * 0.4  # weighted: relevant but secondary to keyword match

            return score
        
        # Score and sort by relevance
        scored = [(score_statement(d), i, d) for i, d in enumerate(review_details)]
        scored.sort(key=lambda x: -x[0])  # highest score first
        
        # Deduplicate: skip statements that are too similar to already-selected ones
        selected_reviews = []
        selected_texts = []
        
        def is_too_similar(new_text, existing_texts, threshold=0.6):
            """Check if new_text is too similar to any existing text using word overlap."""
            new_words = set(new_text.lower().split())
            if len(new_words) < 3:
                return any(new_text.lower().strip() == e.lower().strip() for e in existing_texts)
            for existing in existing_texts:
                existing_words = set(existing.lower().split())
                if not existing_words or not new_words:
                    continue
                overlap = len(new_words & existing_words)
                max_len = max(len(new_words), len(existing_words))
                if max_len > 0 and overlap / max_len > threshold:
                    return True
            return False
        
        for _score, _idx, detail in scored:
            if len(selected_reviews) >= 13:
                break
            preview = detail.get("preview", "")
            # Nur Statements aufnehmen, die mindestens ein Keyword enthalten (Topic-Relevanz)
            preview_lower = preview.lower()
            has_keyword = any(re.search(kw, preview_lower, re.IGNORECASE) for kw in keywords)
            if has_keyword and not is_too_similar(preview, selected_texts):
                selected_reviews.append(detail)
                selected_texts.append(preview)
        
        # Falls nach Keyword-Filter + Dedup weniger als 13: restliche auffüllen (mit Keyword-Check)
        if len(selected_reviews) < 13:
            for _score, _idx, detail in scored:
                if len(selected_reviews) >= 13:
                    break
                if detail not in selected_reviews:
                    preview = detail.get("preview", "")
                    preview_lower = preview.lower()
                    has_keyword = any(re.search(kw, preview_lower, re.IGNORECASE) for kw in keywords)
                    if has_keyword:
                        selected_reviews.append(detail)
        
        # First 3 = relevanz-sortierte "Typische Aussagen" (bleiben stabil)
        # Ab Index 3 = "Beispiel-Review" → nach Kommentar-Reichhaltigkeit sortiert
        top_statements = selected_reviews[:3]
        example_pool = selected_reviews[3:]
        example_pool.sort(key=_richness_score, reverse=True)
        selected_reviews = top_statements + example_pool
        
        typical_statements = [detail["preview"] for detail in selected_reviews]
    else:
        typical_statements = [f"Keine spezifischen Aussagen zu {topic_name} gefunden"]
        selected_reviews = [{
            "id": None,
            "preview": typical_statements[0],
            "fullReview": None
        }]
    
    # Select one example
    example = typical_statements[0] if typical_statements else f"Thema: {topic_name}"
    if len(example) > 80:
        example = example[:77] + "..."
    
    return {
        "topic": topic_name,
        "frequency": len(mentions),
        "avgRating": avg_rating,
        "sentiment": sentiment,
        "example": example,
        "color": color,
        "timelineData": timeline_data,
        "typicalStatements": typical_statements,
        "reviewDetails": selected_reviews  # Relevanz-sortierte Reviews
    }


TOPIC_DEFINITIONS_BY_SOURCE: Dict[str, Dict[str, Dict[str, List[str]]]] = {
    "employee": EMPLOYEE_TOPIC_DEFINITIONS,
    "candidates": CANDIDATE_TOPIC_DEFINITIONS,
}


def topic_definitions_for(source: Optional[str]) -> Dict[str, Dict[str, List[str]]]:
    """Themen-Definitionen der Quelle; ``None`` (oder unbekannt) = beide zusammen."""
    if source in TOPIC_DEFINITIONS_BY_SOURCE:
        return TOPIC_DEFINITIONS_BY_SOURCE[source]
    return {**EMPLOYEE_TOPIC_DEFINITIONS, **CANDIDATE_TOPIC_DEFINITIONS}


_COMPILED: Dict[Optional[str], List[tuple]] = {}


def _compiled_topics(source: Optional[str]) -> List[tuple]:
    """(Thema, [kompilierte Muster]) je Quelle, einmal je Prozess."""
    if source not in _COMPILED:
        _COMPILED[source] = [
            (name, [re.compile(p, re.IGNORECASE) for p in config["keywords"]])
            for name, config in topic_definitions_for(source).items()
        ]
    return _COMPILED[source]


def topics_in_review(row: Dict[str, Any], source: Optional[str]) -> List[str]:
    """Namen der Themen, die eine Bewertung nennt, in der Reihenfolge der Definitionen.

    Gleiche Regel wie ``analyze_topic``: ein Schlüsselwort in einem der
    ``TOPIC_TEXT_FIELDS`` (Text klein geschrieben, Muster ohne Beachtung der
    Groß-/Kleinschreibung).
    """
    texts = [
        row.get(field).lower()
        for field in TOPIC_TEXT_FIELDS
        if row.get(field) and isinstance(row.get(field), str)
    ]
    if not texts:
        return []
    return [
        name for name, patterns in _compiled_topics(source)
        if any(p.search(text) for text in texts for p in patterns)
    ]


def topic_for_dimension(source: str, dimension: str) -> Optional[str]:
    """Schlüsselwort-Thema zu einer Dimension der Erkennung (über die Sternespalte
    in ``rating_fields``), z. B. ``image`` → ``"Image"``; für die Gesamtbewertung
    oder ohne passendes Thema None. ValueError bei ungültiger Quelle oder Dimension."""
    from services.rating_series_service import OVERALL_DIMENSION, value_column  # vermeidet Importzyklus

    column = value_column(source, dimension)
    if dimension == OVERALL_DIMENSION:
        return None
    return next(
        (name for name, config in topic_definitions_for(source).items() if column in config["rating_fields"]),
        None,
    )


def topic_spans(text: Any, topic: str, source: Optional[str]) -> List[List[int]]:
    """Fundstellen der Schlüsselwörter eines Themas in ``text`` als
    ``[[start, ende], ...]`` (Zeichenpositionen, Ende exklusiv), sortiert und
    zusammengeführt; gleiche Muster wie ``topics_in_review``."""
    if not text or not isinstance(text, str):
        return []
    patterns = next((p for name, p in _compiled_topics(source) if name == topic), [])
    found = sorted((m.start(), m.end()) for p in patterns for m in p.finditer(text) if m.end() > m.start())
    merged: List[List[int]] = []
    for start, end in found:
        if merged and start <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])
    return merged


__all__ = [
    "topic_for_dimension", "topic_spans",
    "TOPIC_TEXT_FIELDS", "EMPLOYEE_TOPIC_DEFINITIONS", "CANDIDATE_TOPIC_DEFINITIONS",
    "QUOTE_EXCLUDED_FIELDS", "TOPIC_DEFINITIONS_BY_SOURCE", "topic_definitions_for", "topics_in_review", "analyze_topic",
]
