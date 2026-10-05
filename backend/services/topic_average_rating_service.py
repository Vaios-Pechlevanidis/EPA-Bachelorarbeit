from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Optional, Dict, Any, List, Literal, Callable
from collections import defaultdict

from database.supabase_client import get_supabase_client


Source = Literal["employee", "candidates"]
Granularity = Literal["month", "year"]

EMPLOYEE_TOPIC_COLUMNS: Dict[str, str] = {
    "arbeitsatmosphaere": "sternebewertung_arbeitsatmosphaere",
    "image": "sternebewertung_image",
    "work_life_balance": "sternebewertung_work_life_balance",
    "karriere_weiterbildung": "sternebewertung_karriere_weiterbildung",
    "gehalt_sozialleistungen": "sternebewertung_gehalt_sozialleistungen",
    "kollegenzusammenhalt": "sternebewertung_kollegenzusammenhalt",
    "umwelt_sozialbewusstsein": "sternebewertung_umwelt_sozialbewusstsein",
    "vorgesetztenverhalten": "sternebewertung_vorgesetztenverhalten",
    "kommunikation": "sternebewertung_kommunikation",
    "interessante_aufgaben": "sternebewertung_interessante_aufgaben",
    "umgang_mit_aelteren_kollegen": "sternebewertung_umgang_mit_aelteren_kollegen",
    "arbeitsbedingungen": "sternebewertung_arbeitsbedingungen",
    "gleichberechtigung": "sternebewertung_gleichberechtigung",
}

CANDIDATES_TOPIC_COLUMNS: Dict[str, str] = {
    "erklaerung_der_weiteren_schritte": "sternebewertung_erklaerung_der_weiteren_schritte",
    "zufriedenstellende_reaktion": "sternebewertung_zufriedenstellende_reaktion",
    "vollstaendigkeit_der_infos": "sternebewertung_vollstaendigkeit_der_infos",
    "zufriedenstellende_antworten": "sternebewertung_zufriedenstellende_antworten",
    "angenehme_atmosphaere": "sternebewertung_angenehme_atmosphaere",
    "professionalitaet_des_gespraechs": "sternebewertung_professionalitaet_des_gespraechs",
    "wertschaetzende_behandlung": "sternebewertung_wertschaetzende_behandlung",
    "erwartbarkeit_des_prozesses": "sternebewertung_erwartbarkeit_des_prozesses",
    "zeitgerechte_zu_oder_absage": "sternebewertung_zeitgerechte_zu_oder_absage",
    "schnelle_antwort": "sternebewertung_schnelle_antwort",
}

TOPIC_COLUMNS_BY_SOURCE: Dict[Source, Dict[str, str]] = {
    "employee": EMPLOYEE_TOPIC_COLUMNS,
    "candidates": CANDIDATES_TOPIC_COLUMNS,
}

def _period_key(dt: datetime, granularity: Granularity) -> str:
    if granularity == "year":
        return f"{dt.year:04d}"
    if granularity == "month":
        return f"{dt.year:04d}-{dt.month:02d}"
    raise ValueError("granularity must be 'month' or 'year'")

def _fetch_all_rows(query, page_size: int = 1000) -> List[Dict[str, Any]]:
    """
    Supabase/PostgREST kann Ergebnisse paginieren (z.B. nur 1000 Zeilen).
    Diese Funktion holt alle Seiten via range().
    """
    all_rows: List[Dict[str, Any]] = []
    start = 0

    while True:
        res = query.range(start, start + page_size - 1).execute()
        batch = res.data or []
        all_rows.extend(batch)

        if len(batch) < page_size:
            break

        start += page_size

    return all_rows


# Seiten nach der ersten parallel laden (fetch_all_rows_parallel). Jeder Thread
# baut seine Abfrage selbst und nutzt damit seinen eigenen Supabase-Client
# (database/supabase_client.py); ein Query-Builder wird beim range() verändert
# und darf deshalb nicht zwischen Threads geteilt werden.
_PAGE_WORKERS = 6
_page_pool = ThreadPoolExecutor(max_workers=_PAGE_WORKERS, thread_name_prefix="review-pages")


def fetch_all_rows_parallel(
    make_query: Callable[[Optional[str]], Any],
    page_size: int = 1000,
) -> List[Dict[str, Any]]:
    """
    Wie ``_fetch_all_rows``, aber schneller bei vielen Seiten: Die erste Seite
    liefert mit ``count="exact"`` die Gesamtzahl, die übrigen Seiten werden
    parallel geholt und in Seitenreihenfolge zusammengesetzt.

    ``make_query(count)`` baut die Abfrage jedes Mal neu (``count`` ist None
    oder ``"exact"``); sie muss stabil sortiert sein (z. B. nach ``id``).
    Liefert die Datenbank keine Gesamtzahl oder ist die letzte Seite voll
    (Zeilen kamen zwischen den Abfragen dazu), wird wie bisher seitenweise
    weitergelesen.
    """
    first = make_query("exact").range(0, page_size - 1).execute()
    rows: List[Dict[str, Any]] = list(first.data or [])
    if len(rows) < page_size:
        return rows
    total = first.count
    starts = list(range(page_size, total, page_size)) if isinstance(total, int) else []

    def load_page(start: int) -> List[Dict[str, Any]]:
        return make_query(None).range(start, start + page_size - 1).execute().data or []

    pages = list(_page_pool.map(load_page, starts))
    for page in pages:
        rows.extend(page)
    # Ohne Gesamtzahl oder bei voller letzter Seite: seitenweise weiter.
    last_full = len(pages[-1]) == page_size if pages else True
    start = page_size * (len(pages) + 1)
    while last_full:
        page = load_page(start)
        rows.extend(page)
        last_full = len(page) == page_size
        start += page_size
    return rows


def get_topic_rating_timeseries(
    *,
    source: Source,
    company_id: int,
    granularity: Granularity = "month",
    start: Optional[str] = None,  # ISO, z.B. 2023-01-01
    end: Optional[str] = None,    # ISO, z.B. 2024-12-31
) -> Dict[str, Any]:
    supabase = get_supabase_client()
    topic_cols = TOPIC_COLUMNS_BY_SOURCE[source]

    select_cols = ["datum", "company_id"] + list(topic_cols.values())

    q = (
        supabase.table(source)
        .select(",".join(select_cols))
        .eq("company_id", company_id)
        .not_.is_("datum", "null")
    )

    if start:
        q = q.gte("datum", start)
    if end:
        q = q.lte("datum", end)

    q = q.order("datum", desc=False)
    rows = _fetch_all_rows(q, page_size=1000)

    sums = defaultdict(float)   # (period, topic) -> sum
    counts = defaultdict(int)   # (period, topic) -> count

    for r in rows:
        dt_raw = r.get("datum")
        if not dt_raw:
            continue

        try:
            dt = datetime.fromisoformat(str(dt_raw).replace("Z", "+00:00"))
        except Exception:
            continue

        period = _period_key(dt, granularity)

        for topic, col in topic_cols.items():
            val = r.get(col)
            if val is None:
                continue
            try:
                v = float(val)
            except Exception:
                continue
            sums[(period, topic)] += v
            counts[(period, topic)] += 1

    periods = sorted({p for (p, _t) in counts.keys()} | {p for (p, _t) in sums.keys()})

    data: List[Dict[str, Any]] = []
    for p in periods:
        item: Dict[str, Any] = {"period": p}
        for topic in topic_cols.keys():
            c = counts.get((p, topic), 0)
            item[topic] = None if c == 0 else round(sums[(p, topic)] / c, 2)
        data.append(item)

    return {
        "source": source,
        "granularity": granularity,
        "company_id": company_id,
        "topics": list(topic_cols.keys()),  # wichtig fürs Frontend: dynamisch Lines bauen
        "data": data,
    }
