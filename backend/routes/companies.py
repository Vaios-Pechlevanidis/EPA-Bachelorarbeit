import logging
from concurrent.futures import ThreadPoolExecutor
from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel, field_validator
from database.supabase_client import get_supabase_client
from services.rolling_average_service import company_rolling_averages
from services.topic_average_rating_service import _fetch_all_rows
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

router = APIRouter(prefix="/api", tags=["Companies"])
logger = logging.getLogger(__name__)

# Erlaubte Werte für companies.peer_group (Vergleichsgruppe für Zyklus 2,
# siehe backend/migrations/006_add_company_metadata.sql).
PEER_GROUPS: tuple[str, ...] = (
    "Börsennotiert DE",
    "Börsennotiert Ausland",
    "Nicht börsennotiert",
    "Demo",
)

# Metadaten-Spalten aus Migration 006; können in einer DB ohne diese
# Migration fehlen (PostgREST meldet dann SQLSTATE 42703).
COMPANY_META_COLUMNS: tuple[str, ...] = ("ticker", "isin", "sector", "peer_group")
COMPANY_SELECT_FULL = "id,name," + ",".join(COMPANY_META_COLUMNS)
COMPANY_SELECT_BASIC = "id,name"

_meta_columns_warning_logged = False

# Zählabfragen für GET /companies laufen parallel: je Firma und Tabelle eine
# Anfrage mit count="exact", weil Supabase gruppierte Zählungen nicht erlaubt
# (PostgREST PGRST123). Nacheinander dauerten 29 Firmen × 2 Tabellen rund
# 2,3 s. Jeder Thread nutzt seinen eigenen Client (database/supabase_client.py).
REVIEW_TABLES: tuple[str, ...] = ("employee", "candidates")
_COUNT_WORKERS = 16
_count_pool = ThreadPoolExecutor(max_workers=_COUNT_WORKERS, thread_name_prefix="review-count")


def _is_missing_column_error(exc: Exception) -> bool:
    """True, wenn PostgREST eine fehlende Spalte meldet (SQLSTATE 42703)."""
    if getattr(exc, "code", None) == "42703":
        return True
    return "42703" in str(exc)


def _warn_meta_columns_missing_once() -> None:
    """Loggt einmalig eine Warnung, dass Migration 006 noch nicht eingespielt ist."""
    global _meta_columns_warning_logged
    if _meta_columns_warning_logged:
        return
    _meta_columns_warning_logged = True
    logger.warning(
        "Die Spalten %s fehlen in der Tabelle companies (PostgREST 42703). "
        "Bitte Migration backend/migrations/006_add_company_metadata.sql ausführen; "
        "bis dahin werden nur id und name geladen bzw. gespeichert.",
        ", ".join(COMPANY_META_COLUMNS),
    )


class CompanyCreate(BaseModel):
    """Eingabemodell zum Anlegen eines Unternehmens inkl. optionaler Metadaten.

    - ticker: Yahoo-Finance-Notation (z. B. TKA.DE); wird getrimmt und in
      Großbuchstaben umgewandelt.
    - isin: ISIN der Aktie; wird getrimmt und in Großbuchstaben umgewandelt.
    - sector: Branche als Freitext.
    - peer_group: Vergleichsgruppe, muss einen Wert aus PEER_GROUPS haben.
    Leere Strings werden zu None.
    """

    name: str
    ticker: Optional[str] = None
    isin: Optional[str] = None
    sector: Optional[str] = None
    peer_group: Optional[str] = None

    @field_validator("ticker", "isin", mode="before")
    @classmethod
    def _upper_or_none(cls, value: Any) -> Any:
        if value is None:
            return None
        if isinstance(value, str):
            cleaned = value.strip().upper()
            return cleaned or None
        return value

    @field_validator("sector", "peer_group", mode="before")
    @classmethod
    def _strip_or_none(cls, value: Any) -> Any:
        if value is None:
            return None
        if isinstance(value, str):
            cleaned = " ".join(value.split())
            return cleaned or None
        return value

    @field_validator("peer_group")
    @classmethod
    def _check_peer_group(cls, value: Optional[str]) -> Optional[str]:
        if value is not None and value not in PEER_GROUPS:
            raise ValueError(
                f"peer_group muss einer der Werte {list(PEER_GROUPS)} sein, nicht {value!r}"
            )
        return value


def normalize_company_name(raw_name: str) -> str:
    """Normalisiert einen Unternehmensnamen für Speicherung und Abgleich.

    Trimmt den Namen, entfernt Zeilenumbrüche und reduziert mehrfachen Whitespace
    auf ein einzelnes Leerzeichen ('E.ON\\n' -> 'E.ON', 'NTT  DATA SE' ->
    'NTT DATA SE'). Beginnt der Name mit einem Kleinbuchstaben, wird dieser
    großgeschrieben; die restliche Schreibweise bleibt unverändert.
    """
    if raw_name is None:
        return ""
    trimmed = " ".join(str(raw_name).split())
    if not trimmed:
        return trimmed
    first = trimmed[0]
    if first.isalpha() and first.islower():
        return f"{first.upper()}{trimmed[1:]}"
    return trimmed


def _select_companies_with_fallback() -> list[dict]:
    """Lädt alle Unternehmen inkl. Metadaten; ohne Migration 006 nur id und name.

    Fehlen die Metadaten-Spalten (42703), wird einmalig gewarnt und auf
    "id,name" zurückgefallen; die Metadaten-Schlüssel werden dann mit None
    ergänzt, damit die Antwortstruktur stabil bleibt.
    """
    supabase = get_supabase_client()
    try:
        res = (
            supabase.table("companies")
            .select(COMPANY_SELECT_FULL)
            .order("name", desc=False)
            .execute()
        )
        return res.data or []
    except Exception as exc:  # noqa: BLE001
        if not _is_missing_column_error(exc):
            raise
        _warn_meta_columns_missing_once()
    res = (
        supabase.table("companies")
        .select(COMPANY_SELECT_BASIC)
        .order("name", desc=False)
        .execute()
    )
    data = res.data or []
    for row in data:
        for col in COMPANY_META_COLUMNS:
            row.setdefault(col, None)
    return data

def _count_reviews(table: str, company_id: Any) -> int:
    """Anzahl der Bewertungen eines Unternehmens in einer Tabelle (nur lesend)."""
    supabase = get_supabase_client()
    res = supabase.table(table).select("id", count="exact").eq("company_id", company_id).limit(1).execute()
    return res.count or 0


def _review_counts(company_ids: list[Any]) -> dict[Any, int]:
    """Bewertungen (employee + candidates) je Unternehmen, parallel gezählt."""
    jobs = [
        (cid, _count_pool.submit(_count_reviews, table, cid))
        for cid in company_ids for table in REVIEW_TABLES
    ]
    counts: dict[Any, int] = {cid: 0 for cid in company_ids}
    for cid, job in jobs:
        counts[cid] += job.result()
    return counts


@router.get("/companies/search")
def search_companies(q: str = Query(..., min_length=1)):
    # Vorschläge aus DB, case-insensitive, enthält-suche
    supabase = get_supabase_client()
    res = (
        supabase.table("companies")
        .select("id,name")
        .ilike("name", f"%{q}%")
        .order("name", desc=False)
        .limit(10)
        .execute()
    )
    return res.data or []
@router.get("/companies")
def get_companies():
    """Liefert alle Unternehmen mit Metadaten (ticker, isin, sector, peer_group)
    und der Gesamtzahl der Bewertungen (employee + candidates); die Zählungen
    laufen parallel (siehe _review_counts)."""
    data = _select_companies_with_fallback()
    counts = _review_counts([row["id"] for row in data if row.get("id") is not None])

    for row in data:
        if "id" in row and row["id"] is not None:
            cid = row["id"]
            row["review_count"] = counts[cid]
            row["id"] = str(cid)
    return data


@router.get("/companies/{company_id}/ratings/avg")
def get_company_ratings_avg(
    company_id: int,
    start_date: Optional[str] = Query(default=None, description="Filter reviews from this date (YYYY-MM-DD)"),
):
    supabase = get_supabase_client()
    if start_date:
        columns = list(CATEGORY_COLUMN_MAP.values())
        # Seitenweise (PostgREST liefert höchstens 1000 Zeilen je Abfrage; bis
        # 2026-10-09 fehlten bei Unternehmen mit mehr Bewertungen ab dem
        # Startdatum die übrigen Zeilen, Inkrement 6).
        q = supabase.table("employee").select(",".join(columns)).eq("company_id", company_id).gte("datum", start_date).order("id")
        rows = _fetch_all_rows(q, page_size=1000)
        result = {}
        for avg_key, col in CATEGORY_COLUMN_MAP.items():
            vals = [float(r[col]) for r in rows if r.get(col) is not None]
            result[avg_key] = round(sum(vals) / len(vals), 4) if vals else None
        return result

    res = supabase.rpc("get_employee_ratings_avg", {"p_company_id": company_id}).execute()
    if res.data is None:
        raise HTTPException(status_code=500, detail="No data returned from RPC")
    return res.data[0] if len(res.data) > 0 else {}


# Wortlaut der Score-Definition der Kachel „Ø Score“ (Inkrement 6, FA-38); die
# Erkennungsreihe und der Zeitverlauf mitteln dagegen die Spalte
# durchschnittsbewertung je Bewertung (E3).
AVG_OVERALL_DEFINITION = "Mittel der 13 Kategorienmittel (ungewichtet), nur Mitarbeitende"

# Mapping used for category counts (same keys as frontend CATEGORY_LABELS)
CATEGORY_COLUMN_MAP = {
    "avg_arbeitsatmosphaere": "sternebewertung_arbeitsatmosphaere",
    "avg_image": "sternebewertung_image",
    "avg_work_life_balance": "sternebewertung_work_life_balance",
    "avg_karriere_weiterbildung": "sternebewertung_karriere_weiterbildung",
    "avg_gehalt_sozialleistungen": "sternebewertung_gehalt_sozialleistungen",
    "avg_kollegenzusammenhalt": "sternebewertung_kollegenzusammenhalt",
    "avg_umwelt_sozialbewusstsein": "sternebewertung_umwelt_sozialbewusstsein",
    "avg_vorgesetztenverhalten": "sternebewertung_vorgesetztenverhalten",
    "avg_kommunikation": "sternebewertung_kommunikation",
    "avg_interessante_aufgaben": "sternebewertung_interessante_aufgaben",
    "avg_umgang_aelteren_kollegen": "sternebewertung_umgang_mit_aelteren_kollegen",
    "avg_arbeitsbedingungen": "sternebewertung_arbeitsbedingungen",
    "avg_gleichberechtigung": "sternebewertung_gleichberechtigung",
}


@router.get("/companies/{company_id}/ratings/category-counts")
def get_company_category_counts(company_id: int):
    """Return number of non-null ratings per category (employee table). Keys match avg_* used elsewhere."""
    supabase = get_supabase_client()
    try:
        columns = list(CATEGORY_COLUMN_MAP.values())
        # Seitenweise, sonst höchstens 1000 Zeilen (Korrektur 2026-10-09, Inkrement 6).
        query = supabase.table("employee").select(",".join(columns)).eq("company_id", company_id).order("id")
        rows = _fetch_all_rows(query, page_size=1000)
        counts = {}
        for avg_key, col in CATEGORY_COLUMN_MAP.items():
            n = sum(1 for r in rows if r.get(col) is not None)
            counts[avg_key] = n
        return counts
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def avg_overall_from_rows(rows: list[dict]) -> dict[str, Any]:
    """Mittel der Kategorienmittel (``avg_overall``) aus Zeilen der Tabelle
    ``employee``; reine Funktion. Jede Kategorie wird über ihre nicht-leeren
    Werte gemittelt, das Ergebnis ist das arithmetische Mittel dieser bis zu
    13 Kategorienmittel (ungewichtet). ``n_reviews`` zählt die Zeilen,
    ``n_rated`` die Zeilen mit mindestens einem Kategorienwert."""
    columns = list(CATEGORY_COLUMN_MAP.values())
    totals: dict[str, list[float]] = {col: [] for col in columns}
    n_rated = 0
    for row in rows:
        rated = False
        for col in columns:
            v = row.get(col)
            if v is None:
                continue
            try:
                totals[col].append(float(v))
                rated = True
            except (TypeError, ValueError):
                pass
        n_rated += 1 if rated else 0
    cat_avgs = [sum(vals) / len(vals) for vals in totals.values() if vals]
    return {
        "avg_overall": round(sum(cat_avgs) / len(cat_avgs), 2) if cat_avgs else None,
        "n_reviews": len(rows),
        "n_rated": n_rated,
        "n_categories": len(cat_avgs),
    }


def _compute_avg_overall(company_id: int, start_date: Optional[str] = None) -> dict[str, Any]:
    """Liest die Tabelle ``employee`` seitenweise (optional ab ``start_date``)
    und liefert ``avg_overall_from_rows``. Bis 2026-10-09 las die Funktion nur
    eine Abfrage und damit höchstens 1000 Zeilen (PostgREST-Grenze); bei
    Unternehmen mit mehr Bewertungen war der Wert unvollständig (Inkrement 6)."""
    supabase = get_supabase_client()
    columns = list(CATEGORY_COLUMN_MAP.values())
    q = supabase.table("employee").select(",".join(columns)).eq("company_id", company_id)
    if start_date:
        q = q.gte("datum", start_date)
    rows = _fetch_all_rows(q.order("id"), page_size=1000)
    return avg_overall_from_rows(rows)


@router.get("/companies/{company_id}/ratings")
def get_company_ratings_overall(
    company_id: int,
    start_date: Optional[str] = Query(default=None, description="Filter reviews from this date (YYYY-MM-DD)"),
):
    """Kachel „Ø Score“: Mittel der Kategorienmittel der Mitarbeitenden.

    Antwort (seit 2026-10-09 mit zusätzlichen Feldern, ``avg_overall`` unverändert)::

        {"avg_overall": 3.9, "n_reviews": 6899, "n_rated": 6880, "n_categories": 13,
         "source": "employee", "basis": "sternebewertung",
         "definition": "Mittel der 13 Kategorienmittel (ungewichtet), nur Mitarbeitende"}

    Ohne ``start_date`` kommt der Wert aus der SQL-Funktion
    ``get_employee_ratings_avg`` (alle Zeilen), ``n_reviews`` aus einer
    Zählabfrage; mit ``start_date`` werden die Zeilen seitenweise gelesen.
    """
    supabase = get_supabase_client()
    meta = {
        "source": "employee",
        "basis": "sternebewertung",
        "definition": AVG_OVERALL_DEFINITION,
    }
    if start_date:
        return {**_compute_avg_overall(company_id, start_date), **meta}

    res = supabase.rpc("get_employee_ratings_avg", {"p_company_id": company_id}).execute()
    if res.data is None:
        raise HTTPException(status_code=500, detail="No data returned from RPC")
    row = res.data[0] if len(res.data) > 0 else {}
    values = []
    for v in row.values():
        if v is None:
            continue
        try:
            values.append(float(v))
        except (TypeError, ValueError):
            continue
    avg_overall = round(sum(values) / len(values), 2) if values else None
    return {
        "avg_overall": avg_overall,
        "n_reviews": _count_reviews("employee", company_id),
        "n_rated": None,
        "n_categories": len(values),
        **meta,
    }
    
@router.get("/companies/{company_id}/ratings/trend")
def get_company_ratings_trend(
    company_id: int,
    days: int = Query(30, ge=1, le=3650),
    mode: str = Query(
        "rate",
        description="Trend mode. 'rate' compares last N days vs previous N days and normalizes to 30 days. 'stable_months' compares last N full months vs the N months before. 'stable_all' auto-picks a comparable window (up to N months) based on available history. 'rolling' (Inkrement 6, FA-08): rollierende Schnitte der Gesamtbewertung über die letzten 12 und 24 vollen Kalendermonate mit Daten, Anker ist der letzte volle Monat mit Bewertungen.",
    ),
    months: int = Query(12, ge=1, le=120),
):
    """
    Calculate trend by comparing ratings from two time periods based on review date (datum).
    
    - Current period: last {days} days
    - Previous period: {days} days before that
    - Delta = current_avg - previous_avg
    
    Uses the 'datum' field (review date) not 'created_at' for time-based filtering.

    **Modus ``rolling`` (Inkrement 6, FA-08):** rollierende Durchschnitte der
    Gesamtbewertung (Spalte ``durchschnittsbewertung`` der Mitarbeitenden, wie
    E3) über die letzten 12 und 24 vollen Kalendermonate bis zum Anker, dem
    letzten vollen Monat mit Bewertungen des Unternehmens (nicht das heutige
    Datum). Antwort: ``anchor``, ``short`` und ``long`` (je ``from``, ``to``,
    ``mean``, ``n``, ``months_with_reviews``, ``low_basis``, ``covered``),
    ``difference`` = 12-Monats-Schnitt minus 24-Monats-Schnitt, ``sign``,
    ``low_basis`` (ein Fenster unter 10 Bewertungen, vorläufig wie E12),
    ``history_months`` und ``insufficient_history`` (weniger als 24 Monate
    Daten bis zum Anker). ``days`` und ``months`` werden in diesem Modus nicht
    verwendet; die übrigen Modi sind unverändert. Logik in
    ``services/rolling_average_service.py``.
    """
    if mode == "rolling":
        try:
            return company_rolling_averages(company_id)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    supabase = get_supabase_client()
    def to_float(x):
        try:
            return float(x) if x is not None else None
        except (TypeError, ValueError):
            return None

    eps = 0.05

    def sign_from_delta(delta_points: Optional[float]) -> str:
        if delta_points is None:
            return "flat"
        if delta_points > eps:
            return "up"
        if delta_points < -eps:
            return "down"
        return "flat"

    if mode in {"stable_months", "stable_all"}:
        # "Stabil": volle Kalendermonate verwenden (aktueller, angefangener Monat wird NICHT gezählt)
        now = datetime.now(timezone.utc).replace(microsecond=0)
        end_exclusive = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        def add_months(dt: datetime, delta_months: int) -> datetime:
            total = dt.year * 12 + (dt.month - 1) + delta_months
            new_year, new_month0 = divmod(total, 12)
            return dt.replace(year=new_year, month=new_month0 + 1, day=1)

        requested_months = months

        if mode == "stable_all":
            # Auto-select a window size that fits the available history.
            bounds = (
                supabase.table("employee")
                .select("datum")
                .eq("company_id", company_id)
                .not_.is_("datum", None)
                .order("datum", desc=False)
                .execute()
            )
            if not bounds.data:
                return {
                    "mode": mode,
                    "months": None,
                    "requestedMonths": requested_months,
                    "current_range": {"from": None, "to": end_exclusive.isoformat()},
                    "previous_range": {"from": None, "to": None},
                    "overall": {"deltaPoints": None, "deltaPercent": None},
                    "metrics": {},
                }

            try:
                def _to_utc(s: str) -> datetime:
                    dt = datetime.fromisoformat(str(s).replace("Z", "+00:00"))
                    if dt.tzinfo is None:
                        from datetime import timezone as _tz
                        dt = dt.replace(tzinfo=_tz.utc)
                    return dt
                first_dt = _to_utc(bounds.data[0]["datum"])
                last_dt  = _to_utc(bounds.data[-1]["datum"])
            except Exception:
                return {
                    "mode": mode,
                    "months": None,
                    "requestedMonths": requested_months,
                    "current_range": {"from": None, "to": end_exclusive.isoformat()},
                    "previous_range": {"from": None, "to": None},
                    "overall": {"deltaPoints": None, "deltaPercent": None},
                    "metrics": {},
                }

            # Use the month after the last review as anchor so historical data aligns correctly.
            last_month_end = add_months(last_dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0), 1)
            if last_month_end < end_exclusive:
                end_exclusive = last_month_end

            first_month_start = first_dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            total_months = (end_exclusive.year - first_month_start.year) * 12 + (end_exclusive.month - first_month_start.month)
            if total_months < 2:
                return {
                    "mode": mode,
                    "months": None,
                    "requestedMonths": requested_months,
                    "current_range": {"from": None, "to": end_exclusive.isoformat()},
                    "previous_range": {"from": None, "to": None},
                    "overall": {"deltaPoints": None, "deltaPercent": None},
                    "metrics": {},
                }

            months = min(requested_months, max(1, total_months // 2))

        # 2*months volle Monate: previous window + current window
        start_all = add_months(end_exclusive, -2 * months)

        # Compute stable monthly averages from raw rows in ONE (paginated) query.
        # This avoids making 2*months RPC calls, which can hit rate limits / return empty data.
        metric_to_column = {
            "avg_arbeitsatmosphaere": "sternebewertung_arbeitsatmosphaere",
            "avg_image": "sternebewertung_image",
            "avg_work_life_balance": "sternebewertung_work_life_balance",
            "avg_karriere_weiterbildung": "sternebewertung_karriere_weiterbildung",
            "avg_gehalt_sozialleistungen": "sternebewertung_gehalt_sozialleistungen",
            "avg_kollegenzusammenhalt": "sternebewertung_kollegenzusammenhalt",
            "avg_umwelt_sozialbewusstsein": "sternebewertung_umwelt_sozialbewusstsein",
            "avg_vorgesetztenverhalten": "sternebewertung_vorgesetztenverhalten",
            "avg_kommunikation": "sternebewertung_kommunikation",
            "avg_interessante_aufgaben": "sternebewertung_interessante_aufgaben",
            "avg_umgang_aelteren_kollegen": "sternebewertung_umgang_mit_aelteren_kollegen",
            "avg_arbeitsbedingungen": "sternebewertung_arbeitsbedingungen",
            "avg_gleichberechtigung": "sternebewertung_gleichberechtigung",
        }

        select_fields = ["datum"] + list(metric_to_column.values())
        select_clause = ",".join(select_fields)

        batch_size = 1000
        offset = 0

        rows = []
        while True:
            query = (
                supabase.table("employee")
                .select(select_clause)
                .eq("company_id", company_id)
                .gte("datum", start_all.isoformat())
                .lt("datum", end_exclusive.isoformat())
                .range(offset, offset + batch_size - 1)
            )
            resp = query.execute()
            batch = resp.data or []
            rows.extend(batch)
            if len(batch) < batch_size:
                break
            offset += batch_size

        # month_key -> metric_key -> list[float]
        monthly_values: dict[tuple[int, int], dict[str, list[float]]] = {}
        # Bewertungen je Kalendermonat (n je Fenster, Inkrement 6, FA-26)
        monthly_reviews: dict[tuple[int, int], int] = {}
        for r in rows:
            d = r.get("datum")
            if not d:
                continue
            try:
                dt = datetime.fromisoformat(str(d).replace("Z", "+00:00"))
            except Exception:
                continue

            month_key = (dt.year, dt.month)
            monthly_reviews[month_key] = monthly_reviews.get(month_key, 0) + 1
            if month_key not in monthly_values:
                monthly_values[month_key] = {k: [] for k in metric_to_column.keys()}

            for metric_key, col in metric_to_column.items():
                v = to_float(r.get(col))
                if v is None:
                    continue
                monthly_values[month_key][metric_key].append(v)

        # Reduce to month-level averages: month_key -> metric_key -> float
        monthly_avgs: dict[tuple[int, int], dict[str, float]] = {}
        for month_key, per_metric_lists in monthly_values.items():
            month_avg_row = {}
            for metric_key, vals in per_metric_lists.items():
                if vals:
                    month_avg_row[metric_key] = sum(vals) / len(vals)
            if month_avg_row:
                monthly_avgs[month_key] = month_avg_row

        # Build the two windows of full months
        def months_in_window(start: datetime, count: int) -> list[tuple[int, int]]:
            out = []
            cur = start
            for _ in range(count):
                out.append((cur.year, cur.month))
                cur = add_months(cur, 1)
            return out

        prev_start = add_months(end_exclusive, -2 * months)
        cur_start = add_months(end_exclusive, -months)
        prev_month_keys = months_in_window(prev_start, months)
        cur_month_keys = months_in_window(cur_start, months)

        keys = set(metric_to_column.keys())

        result = {}
        deltas_for_overall = []
        percent_for_overall = []

        for k in keys:
            prev_vals = [monthly_avgs.get(mk, {}).get(k) for mk in prev_month_keys]
            cur_vals = [monthly_avgs.get(mk, {}).get(k) for mk in cur_month_keys]
            prev_vals = [v for v in prev_vals if v is not None]
            cur_vals = [v for v in cur_vals if v is not None]

            prev_avg = (sum(prev_vals) / len(prev_vals)) if prev_vals else None
            cur_avg = (sum(cur_vals) / len(cur_vals)) if cur_vals else None

            if cur_avg is None:
                result[k] = {
                    "score": None,
                    "prev": prev_avg,
                    "delta": None,
                    "deltaPercent": None,
                    "sign": "flat",
                    "has_prev": prev_avg is not None,
                    "monthsUsed": {"current": len(cur_vals), "previous": len(prev_vals)},
                }
                continue

            if prev_avg is None:
                result[k] = {
                    "score": round(cur_avg, 2),
                    "prev": None,
                    "delta": None,
                    "deltaPercent": None,
                    "sign": "new",
                    "has_prev": False,
                    "monthsUsed": {"current": len(cur_vals), "previous": 0},
                }
                continue

            delta_points = cur_avg - prev_avg
            delta_percent = None
            if abs(prev_avg) > 1e-12:
                delta_percent = (delta_points / prev_avg) * 100

            deltas_for_overall.append(delta_points)
            if delta_percent is not None:
                percent_for_overall.append(delta_percent)

            result[k] = {
                "score": round(cur_avg, 2),
                "prev": round(prev_avg, 2),
                "delta": round(delta_points, 2),
                "deltaPercent": round(delta_percent, 1) if delta_percent is not None else None,
                "sign": sign_from_delta(delta_points),
                "has_prev": True,
                "monthsUsed": {"current": len(cur_vals), "previous": len(prev_vals)},
            }

        overall_points = round(sum(deltas_for_overall) / len(deltas_for_overall), 2) if deltas_for_overall else None
        overall_percent = round(sum(percent_for_overall) / len(percent_for_overall), 1) if percent_for_overall else None

        return {
            "mode": mode,
            "months": months,
            "requestedMonths": requested_months,
            "current_range": {"from": add_months(end_exclusive, -months).isoformat(), "to": end_exclusive.isoformat()},
            "previous_range": {"from": add_months(end_exclusive, -2 * months).isoformat(), "to": add_months(end_exclusive, -months).isoformat()},
            "overall": {"deltaPoints": overall_points, "deltaPercent": overall_percent},
            "metrics": result,
            # Bewertungen je Fenster (alle Zeilen der Monate, Inkrement 6, FA-26)
            "n_reviews": {
                "current": sum(monthly_reviews.get(mk, 0) for mk in cur_month_keys),
                "previous": sum(monthly_reviews.get(mk, 0) for mk in prev_month_keys),
            },
            "source": "employee",
            "basis": "sternebewertung",
        }

    # Default: legacy "rate" mode (days-based, normalized to 30 days)
    now = datetime.now(timezone.utc).replace(microsecond=0)
    cur_from = now - timedelta(days=days)
    prev_from = now - timedelta(days=2 * days)
    prev_to = cur_from

    cur = supabase.rpc("get_employee_ratings_avg_range", {
        "p_company_id": company_id,
        "p_from": cur_from.isoformat(),
        "p_to": now.isoformat(),
    }).execute()

    prev = supabase.rpc("get_employee_ratings_avg_range", {
        "p_company_id": company_id,
        "p_from": prev_from.isoformat(),
        "p_to": prev_to.isoformat(),
    }).execute()

    cur_row = cur.data[0] if cur.data else {}
    prev_row = prev.data[0] if prev.data else {}

    # optional: Meta-Felder rausfiltern, falls je vorhanden
    EXCLUDE_KEYS = {"company_id", "count", "n", "from", "to"}
    keys = (set(cur_row.keys()) | set(prev_row.keys())) - EXCLUDE_KEYS

    result = {}
    deltas_for_overall = []

    for k in keys:
        c_val = to_float(cur_row.get(k))
        p_val = to_float(prev_row.get(k))

        # wenn current fehlt → keine Aussage
        if c_val is None:
            result[k] = {"score": None, "prev": p_val, "delta": None, "sign": "flat", "has_prev": p_val is not None}
            continue

        # wenn previous fehlt → NEW
        if p_val is None:
            result[k] = {"score": c_val, "prev": None, "delta": None, "sign": "new", "has_prev": False}
            continue

        # Trendrate berechnen: Trend(t1, t2) = (Y_t2 - Y_t1) / (t2 - t1)
        # Normalisiert auf 30 Tage (1 Monat) für Vergleichbarkeit
        raw_diff = c_val - p_val
        delta_per_month = (raw_diff / days) * 30  # Änderungsrate pro 30 Tage
        
        sign = "flat"
        if delta_per_month > eps:
            sign = "up"
        elif delta_per_month < -eps:
            sign = "down"

        delta = round(delta_per_month, 1)
        deltas_for_overall.append(delta_per_month)

        result[k] = {"score": c_val, "prev": p_val, "delta": delta, "sign": sign, "has_prev": True}

    overall = None
    if deltas_for_overall:
        overall = round(sum(deltas_for_overall) / len(deltas_for_overall), 1)

    return {
        "mode": mode,
        "days": days,
        "current_range": {"from": cur_from.isoformat(), "to": now.isoformat()},
        "previous_range": {"from": prev_from.isoformat(), "to": prev_to.isoformat()},
        "overall": {"avgDelta": overall},
        "metrics": result,
    }    

@router.post("/companies/")
def create_company(company: CompanyCreate):
    """
    Legt ein neues Unternehmen an und gibt es mit seiner ID zurück.

    Der Name wird normalisiert (siehe normalize_company_name). Existiert bereits
    ein Unternehmen mit diesem Namen (case-insensitive), wird dieses zurückgegeben.
    Von den Metadaten (ticker, isin, sector, peer_group) werden nur die gesetzten
    (nicht-None) Felder gespeichert. Fehlen die Metadaten-Spalten in der DB
    (Migration 006 nicht eingespielt), wird gewarnt und nur der Name gespeichert.
    """
    supabase = get_supabase_client()
    normalized_name = normalize_company_name(company.name)
    if not normalized_name:
        raise HTTPException(status_code=400, detail="Unternehmensname darf nicht leer sein")

    # Check if company already exists
    existing = (
        supabase.table("companies")
        .select("id,name")
        .ilike("name", normalized_name)
        .execute()
    )

    if existing.data:
        # Unternehmen existiert bereits: unverändert zurückgeben. Mitgeschickte
        # Metadaten werden bewusst NICHT übernommen (Pflege über
        # scripts/seed_company_metadata.py), das wird aber protokolliert.
        ignored = {col: getattr(company, col) for col in COMPANY_META_COLUMNS
                   if getattr(company, col) is not None}
        if ignored:
            logger.warning(
                "Unternehmen %r existiert bereits (id=%s); mitgeschickte Metadaten "
                "werden ignoriert: %s", normalized_name, existing.data[0].get("id"), ignored,
            )
        rows = [r for r in _select_companies_with_fallback()
                if str(r.get("id")) == str(existing.data[0].get("id"))]
        return rows[0] if rows else existing.data[0]

    # Create new company (nur gesetzte Metadaten mitschicken)
    payload: dict[str, Any] = {"name": normalized_name}
    for col in COMPANY_META_COLUMNS:
        value = getattr(company, col)
        if value is not None:
            payload[col] = value

    try:
        result = supabase.table("companies").insert(payload).execute()
    except Exception as exc:  # noqa: BLE001
        if len(payload) == 1 or not _is_missing_column_error(exc):
            raise
        _warn_meta_columns_missing_once()
        logger.warning(
            "Metadaten für Unternehmen %r wurden verworfen, da die Spalten fehlen: %s",
            normalized_name, {k: v for k, v in payload.items() if k != "name"},
        )
        result = supabase.table("companies").insert({"name": normalized_name}).execute()

    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to create company")

    return result.data[0]


@router.delete("/companies/{company_id}")
def delete_company(company_id: int):
    """
    Deletes a company from the database.
    This is used for rollback when file upload fails.
    """
    supabase = get_supabase_client()
    try:
        # First, check if company has any data (employees or candidates)
        employees = supabase.table("employee").select("id").eq("company_id", company_id).limit(1).execute()
        candidates = supabase.table("candidates").select("id").eq("company_id", company_id).limit(1).execute()
        
        # Only allow deletion if no data exists
        if employees.data or candidates.data:
            raise HTTPException(
                status_code=400, 
                detail="Cannot delete company with existing data"
            )
        
        # Delete the company
        result = supabase.table("companies").delete().eq("id", company_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Company not found")
        
        return {"message": "Company deleted successfully", "id": company_id}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete company: {str(e)}")

@router.delete("/companies/{company_id}/data")
def delete_company_data(company_id: int):
    """
    Deletes all data (employees and candidates) for a company.
    The company itself remains in the database.
    Used when user wants to replace existing data with new uploads.
    """
    supabase = get_supabase_client()
    try:
        # Delete all employees for this company
        employees_result = supabase.table("employee").delete().eq("company_id", company_id).execute()
        
        # Delete all candidates for this company
        candidates_result = supabase.table("candidates").delete().eq("company_id", company_id).execute()
        
        employees_count = len(employees_result.data) if employees_result.data else 0
        candidates_count = len(candidates_result.data) if candidates_result.data else 0
        
        return {
            "message": "Company data deleted successfully",
            "company_id": company_id,
            "deleted": {
                "employees": employees_count,
                "candidates": candidates_count
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete company data: {str(e)}")