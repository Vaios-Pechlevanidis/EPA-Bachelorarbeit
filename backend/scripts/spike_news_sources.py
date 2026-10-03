"""
Spike (Prüfpunkt 9, Inkrement 0 „Fundament“): Welche Quelle liefert HISTORISCHE
Nachrichten für ein Unternehmen und einen Kalendermonat?

Geprüft werden vier Quellen, jeweils isoliert (eigener try/except, 20 s Timeout
für alle urllib-Aufrufe, möglichst eine Anfrage je Quelle und Lauf):

  a) GDELT DOC 2.0 API   Volltext-Index weltweiter Online-Nachrichten; die
                         Historie beginnt 2017. Bei HTTP 429 (Rate-Limit: eine
                         Anfrage je 5 s) wird genau einmal nach 6 s erneut
                         angefragt.
  b) Google News RSS     Suche mit den Operatoren after:/before:, de/DE.
  c) EQS News REST       Undokumentierter WordPress-Endpunkt
                         (/wp-json/eqsnews/v1/news) für Pflicht- und
                         Unternehmensmitteilungen börsennotierter Emittenten.
                         Der Parameter company_name wird vom Backend als
                         companyUUID interpretiert; ein Klarname liefert
                         „API Unavailable“ (500). Mit --eqs-uuid bzw.
                         --eqs-find-uuid (Suche der UUID über die datumsgefilterte
                         Gesamtliste, mehrere Seiten à 100 Einträge, 1 s Pause)
                         funktioniert die Abfrage mit Datumsfenster.
  d) yfinance            Ticker.get_news() hat KEINEN Datumsfilter; es werden
                         die zurückgegebenen Einträge gezählt, die ins Fenster
                         fallen (erwartet: 0 für alte Monate). Zusätzlich wird
                         yfinance.Search(<Name>).news als Vergleich erfasst.

Pro Quelle werden erfasst: Trefferzahl, frühestes/spätestes
Veröffentlichungsdatum, Sprachschätzung, drei Beispieltitel, Fehler.
Das Ergebnis wird als JSON in backend/data/spike_news_sources.json gespeichert
(Merge, Schlüssel = normalisierter Firmenname + Monat).

Monatswahl aus der DB (--pick-month, strikt lesend): der Monat >= 2019 mit
>= 5 Employee-Bewertungen und der größten absoluten Änderung des Monatsmittels
von durchschnittsbewertung gegenüber dem Vormonat (der Vormonat selbst ist
nicht beschränkt; seine Fallzahl wird mit ausgegeben).

Verwendung (aus backend/):
  uv run python scripts/spike_news_sources.py --company "Thyssenkrupp" --pick-month \
      --ticker TKA.DE --isin DE0007500001 --eqs-find-uuid 60
  uv run python scripts/spike_news_sources.py --company "Bechtle" --month 2020-10 \
      --ticker BC8.DE --isin DE0005158703 --eqs-find-uuid 60
  uv run python scripts/spike_news_sources.py --company "Open Grid Europe" --pick-month

Weitere Optionen:
  --window-months N      Fenster = Startmonat plus N-1 Folgemonate (Standard 1)
  --query "..."          Suchbegriff für GDELT/Google News/yfinance.Search statt Firmenname
  --sourcelang german    GDELT-Filter sourcelang:<x> (optional)
  --eqs-uuid <uuid>      bekannte EQS-companyUUID direkt verwenden
  --eqs-find-uuid N      UUID über maximal N Seiten der EQS-Monatsliste suchen
  --sources a,b,c        Teilmenge aus gdelt,gnews,eqs,yfinance
  --out <pfad>           Ziel-JSON (Standard backend/data/spike_news_sources.json)
  --no-save              Ergebnis nur ausgeben, nicht speichern
"""

import argparse
import calendar
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from typing import Any, Dict, List, Optional, Tuple

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND_DIR)

DEFAULT_OUT = os.path.join(BACKEND_DIR, "data", "spike_news_sources.json")
TIMEOUT_S = 20
USER_AGENT = "Mozilla/5.0 (compatible; EPA-Bachelorarbeit-Spike/0.1; research, non-commercial)"

GDELT_URL = "https://api.gdeltproject.org/api/v2/doc/doc"
GNEWS_URL = "https://news.google.com/rss/search"
EQS_URL = "https://www.eqs-news.com/wp-json/eqsnews/v1/news"
ALL_SOURCES = ("gdelt", "gnews", "eqs", "yfinance")

SAMPLE_TITLES = 3

# Einfache Stoppwort-Heuristik für die Sprachschätzung der Titel.
DE_WORDS = {
    "und", "der", "die", "das", "für", "mit", "von", "im", "am", "bei", "nach",
    "über", "zum", "zur", "ist", "wird", "sich", "nicht", "auf", "den", "dem",
    "des", "ein", "eine", "einen", "neue", "neuer", "neues", "gegen", "bis",
}
EN_WORDS = {
    "the", "and", "of", "for", "with", "to", "in", "on", "at", "is", "are",
    "by", "from", "as", "that", "this", "its", "new", "will", "has", "after",
}


# ── Hilfsfunktionen ──────────────────────────────────────────────────────────

def normalize_name(s: Optional[str]) -> str:
    """Whitespace zusammenfassen, trimmen, casefold (DB-Namen haben Defekte)."""
    return re.sub(r"\s+", " ", (s or "")).strip().casefold()


def month_window(month: str, window_months: int) -> Tuple[date, date]:
    """Liefert (erster Tag des Startmonats, letzter Tag des Endmonats)."""
    y, m = int(month[:4]), int(month[5:7])
    start = date(y, m, 1)
    total = y * 12 + (m - 1) + max(window_months, 1) - 1
    ey, em = divmod(total, 12)
    em += 1
    end = date(ey, em, calendar.monthrange(ey, em)[1])
    return start, end


def http_get(url: str, timeout: int = TIMEOUT_S) -> Tuple[int, bytes, Dict[str, str]]:
    """GET mit User-Agent und Timeout; HTTP-Fehler werden als Status zurückgegeben,
    Netzwerkfehler/Timeouts propagieren als Exception."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "*/*"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read(), dict(resp.headers)
    except urllib.error.HTTPError as e:
        body = b""
        try:
            body = e.read()
        except Exception:
            pass
        return e.code, body, dict(e.headers or {})


def guess_language(titles: List[str]) -> str:
    """Grobe Sprachschätzung über Stoppwörter in den Titeln."""
    de = en = 0
    for t in titles:
        for tok in re.findall(r"[a-zäöüß]+", (t or "").lower()):
            if tok in DE_WORDS:
                de += 1
            elif tok in EN_WORDS:
                en += 1
    if de == 0 and en == 0:
        return "unbekannt"
    if de > en:
        return "de"
    if en > de:
        return "en"
    return "gemischt"


def iso(dt: Optional[datetime]) -> Optional[str]:
    return dt.isoformat() if dt else None


def in_window(dt: Optional[datetime], start: date, end: date) -> bool:
    if dt is None:
        return False
    d = dt.astimezone(timezone.utc).date() if dt.tzinfo else dt.date()
    return start <= d <= end


def summarize(entries: List[Tuple[str, Optional[datetime]]]) -> Dict[str, Any]:
    """entries = [(titel, datum)] -> count, earliest, latest, Sprachschätzung, Beispiele."""
    dates = [d for _, d in entries if d is not None]
    titles = [t for t, _ in entries if t]
    return {
        "count": len(entries),
        "earliest": iso(min(dates)) if dates else None,
        "latest": iso(max(dates)) if dates else None,
        "language_guess": guess_language(titles),
        "sample_titles": titles[:SAMPLE_TITLES],
    }


def base_result(url: str) -> Dict[str, Any]:
    return {"request_url": url, "http_status": None, "count": None, "earliest": None,
            "latest": None, "language_guess": None, "sample_titles": [], "error": None,
            "notes": []}


# ── a) GDELT DOC 2.0 ─────────────────────────────────────────────────────────

def probe_gdelt(query: str, start: date, end: date, sourcelang: Optional[str]) -> Dict[str, Any]:
    q = f'"{query}"' if (" " in query and not query.startswith('"')) else query
    if sourcelang:
        q += f" sourcelang:{sourcelang}"
    params = {
        "query": q,
        "mode": "artlist",
        "format": "json",
        "startdatetime": start.strftime("%Y%m%d") + "000000",
        "enddatetime": end.strftime("%Y%m%d") + "235959",
        "maxrecords": 75,
        "sort": "datedesc",
    }
    url = GDELT_URL + "?" + urllib.parse.urlencode(params)
    result = base_result(url)
    if start.year < 2017:
        result["notes"].append("GDELT DOC deckt erst ab 2017 ab; Fenster liegt (teilweise) davor")

    status, body, _ = http_get(url)
    if status == 429:
        result["notes"].append("HTTP 429 (Rate-Limit: eine Anfrage je 5 s) – ein Retry nach 6 s")
        time.sleep(6)
        status, body, _ = http_get(url)
    result["http_status"] = status
    text = body.decode("utf-8", "replace")
    if status != 200:
        result["error"] = f"HTTP {status}: {text[:200].strip()}"
        return result
    if not text.strip():
        result["notes"].append("leerer Body (GDELT liefert bei 0 Treffern keinen JSON-Inhalt)")
        result["count"] = 0
        return result
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        result["error"] = f"keine JSON-Antwort: {text[:200].strip()}"
        return result

    articles = data.get("articles", []) or []
    entries: List[Tuple[str, Optional[datetime]]] = []
    for a in articles:
        dt = None
        raw = a.get("seendate")
        if raw:
            try:
                dt = datetime.strptime(raw, "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc)
            except ValueError:
                pass
        entries.append((a.get("title") or "", dt))
    result.update(summarize(entries))
    result["languages_reported"] = dict(Counter(a.get("language") for a in articles))
    result["source_countries"] = dict(Counter(a.get("sourcecountry") for a in articles).most_common(5))
    result["domains"] = dict(Counter(a.get("domain") for a in articles).most_common(5))
    result["in_window"] = sum(1 for _, d in entries if in_window(d, start, end))
    return result


# ── b) Google News RSS ───────────────────────────────────────────────────────

def probe_gnews(query: str, start: date, end: date) -> Dict[str, Any]:
    q_name = f'"{query}"' if (" " in query and not query.startswith('"')) else query
    # before: ist exklusiv -> Folgetag des Fensterendes
    q = f"{q_name} after:{start:%Y-%m-%d} before:{(end + timedelta(days=1)):%Y-%m-%d}"
    params = {"q": q, "hl": "de", "gl": "DE", "ceid": "DE:de"}
    url = GNEWS_URL + "?" + urllib.parse.urlencode(params)
    result = base_result(url)

    status, body, _ = http_get(url)
    result["http_status"] = status
    if status != 200:
        result["error"] = f"HTTP {status}: {body[:200].decode('utf-8', 'replace').strip()}"
        return result
    root = ET.fromstring(body)
    result["channel_language"] = root.findtext("./channel/language")
    items = root.findall("./channel/item")
    entries: List[Tuple[str, Optional[datetime]]] = []
    sources: Counter = Counter()
    for it in items:
        dt = None
        raw = it.findtext("pubDate")
        if raw:
            try:
                dt = parsedate_to_datetime(raw)
            except Exception:
                pass
        src = it.find("source")
        if src is not None and src.text:
            sources[src.text] += 1
        entries.append((it.findtext("title") or "", dt))
    result.update(summarize(entries))
    result["in_window"] = sum(1 for _, d in entries if in_window(d, start, end))
    result["top_sources"] = dict(sources.most_common(5))
    result["notes"].append("RSS liefert maximal ca. 100 Einträge; keine Paginierung")
    return result


# ── c) EQS News REST (undokumentiert) ────────────────────────────────────────

def _eqs_call(params: Dict[str, Any], attempts: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    url = EQS_URL + "?" + urllib.parse.urlencode(params)
    status, body, _ = http_get(url)
    data: Optional[Dict[str, Any]] = None
    try:
        parsed = json.loads(body)
        data = parsed if isinstance(parsed, dict) else None
    except json.JSONDecodeError:
        pass
    records = (data or {}).get("records") or []
    attempts.append({
        "params": params,
        "http_status": status,
        "backend_status": (data or {}).get("status"),
        "backend_error": (data or {}).get("error") or None,
        "records": len(records),
        "total_items": records[0].get("totalItem") if records else None,
    })
    return data


def _eqs_matches(rec: Dict[str, Any], company: str, isin: Optional[str]) -> bool:
    """ISIN exakt, sonst Name als ganzes Wort/Wortfolge im companyName (nicht als
    Teilstring: 'rwe' steckt z. B. auch in 'schwerwelt')."""
    if isin and (rec.get("isin") or "").upper() == isin.upper():
        return True
    target = normalize_name(company)
    if not target:
        return False
    return re.search(rf"(?<!\w){re.escape(target)}(?!\w)", normalize_name(rec.get("companyName"))) is not None


def probe_eqs(company: str, isin: Optional[str], start: date, end: date,
              uuid: Optional[str], find_uuid_pages: int) -> Dict[str, Any]:
    result = base_result(EQS_URL)
    attempts: List[Dict[str, Any]] = []
    result["attempts"] = attempts
    s, e = start.isoformat(), end.isoformat()
    records: List[Dict[str, Any]] = []
    uuid_source = "argument" if uuid else None

    if not uuid:
        # Versuch 1: Klarname (dokumentiert: Backend erwartet companyUUID -> 500 "API Unavailable")
        data = _eqs_call({"company_name": company, "start_date": s, "end_date": e, "per_page": 100}, attempts)
        recs = (data or {}).get("records") or []
        if recs:
            records = recs
            uuid_source = "name"
        else:
            result["notes"].append("company_name=<Klarname> liefert keine Datensätze "
                                   "(Backend interpretiert den Wert als companyUUID)")
        if not records and find_uuid_pages > 0:
            # Versuch 2: UUID über die datumsgefilterte Gesamtliste suchen (ISIN oder Name)
            pages_used = 0
            for page in range(1, find_uuid_pages + 1):
                data = _eqs_call({"start_date": s, "end_date": e, "per_page": 100, "page": page}, attempts)
                pages_used = page
                recs = (data or {}).get("records") or []
                if not recs:
                    break
                hit = next((r for r in recs if _eqs_matches(r, company, isin)), None)
                if hit:
                    uuid = hit.get("companyUUID")
                    uuid_source = f"discovery (Seite {page}, {hit.get('companyName')!r}, ISIN {hit.get('isin')})"
                    break
                total = recs[0].get("totalItem") or 0
                if page * 100 >= total:
                    break
                time.sleep(1.0)
            # Die Seitenaufrufe zu einer Zeile zusammenfassen, um das JSON klein zu halten
            paged = [a for a in attempts if "page" in a["params"]]
            for a in paged[1:]:
                attempts.remove(a)
            if paged:
                paged[0]["params"] = {k: v for k, v in paged[0]["params"].items() if k != "page"}
                paged[0]["pages_requested"] = pages_used
            if not uuid:
                result["notes"].append(f"UUID-Suche über {pages_used} Seite(n) ohne Treffer")

    if uuid and not records:
        data = _eqs_call({"company_name": uuid, "start_date": s, "end_date": e, "per_page": 100}, attempts)
        records = (data or {}).get("records") or []

    result["company_uuid"] = uuid
    result["uuid_source"] = uuid_source
    result["http_status"] = attempts[-1]["http_status"] if attempts else None

    if not uuid and not records:
        result["count"] = 0
        result["error"] = ("keine companyUUID bekannt; Klarname/ISIN werden vom Endpunkt nicht aufgelöst "
                           "(--eqs-uuid oder --eqs-find-uuid verwenden)")
        return result

    entries: List[Tuple[str, Optional[datetime]]] = []
    for r in records:
        dt = None
        raw = r.get("dateUtc") or r.get("date")
        if raw:
            try:
                dt = datetime.strptime(raw, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
            except ValueError:
                pass
        entries.append((r.get("headline") or "", dt))
    result.update(summarize(entries))
    result["in_window"] = sum(1 for _, d in entries if in_window(d, start, end))
    result["languages_reported"] = dict(Counter(r.get("language") for r in records))
    result["categories"] = dict(Counter(r.get("category") for r in records))
    result["company_names_reported"] = sorted({r.get("companyName") for r in records if r.get("companyName")})
    result["notes"].append("Endpunkt undokumentiert; per_page ist serverseitig auf 100 begrenzt")
    return result


# ── d) yfinance ──────────────────────────────────────────────────────────────

def _yf_item(it: Dict[str, Any]) -> Tuple[str, Optional[datetime]]:
    """Normalisiert alte und neue yfinance-Formate zu (titel, datum)."""
    c = it.get("content") if isinstance(it.get("content"), dict) else it
    title = c.get("title") or ""
    dt = None
    if c.get("pubDate"):
        try:
            dt = datetime.fromisoformat(str(c["pubDate"]).replace("Z", "+00:00"))
        except ValueError:
            pass
    elif c.get("providerPublishTime"):
        try:
            dt = datetime.fromtimestamp(int(c["providerPublishTime"]), tz=timezone.utc)
        except (TypeError, ValueError, OSError):
            pass
    return title, dt


def probe_yfinance(ticker: Optional[str], query: str, start: date, end: date) -> Dict[str, Any]:
    result: Dict[str, Any] = {"ticker": ticker, "error": None,
                              "notes": ["yfinance.Ticker.get_news() hat keinen Datumsfilter; "
                                        "yfinance nutzt eine eigene HTTP-Schicht (get_news ohne Timeout-Parameter, "
                                        f"Search mit timeout={TIMEOUT_S} s)"]}
    import yfinance as yf  # erst hier, damit die anderen Quellen auch ohne yfinance laufen

    # get_news(): nur mit Ticker sinnvoll
    gn: Dict[str, Any] = {"count": None, "in_window": None, "earliest": None, "latest": None,
                          "language_guess": None, "sample_titles": [], "error": None}
    if ticker:
        try:
            items = yf.Ticker(ticker).get_news(count=20) or []
            entries = [_yf_item(it) for it in items]
            gn.update(summarize(entries))
            gn["in_window"] = sum(1 for _, d in entries if in_window(d, start, end))
        except Exception as ex:  # noqa: BLE001 – Spike: jede Quelle isoliert
            gn["error"] = f"{type(ex).__name__}: {str(ex)[:200]}"
    else:
        gn["error"] = "kein Ticker angegeben (nicht börsennotiert)"
    result["get_news"] = gn

    # Search(...).news: Vergleich, ebenfalls ohne Datumsfilter
    sn: Dict[str, Any] = {"query": query, "count": None, "in_window": None, "earliest": None,
                          "latest": None, "language_guess": None, "sample_titles": [], "error": None}
    try:
        news = yf.Search(query, news_count=20, timeout=TIMEOUT_S).news or []
        entries = [_yf_item(it) for it in news]
        sn.update(summarize(entries))
        sn["in_window"] = sum(1 for _, d in entries if in_window(d, start, end))
    except Exception as ex:  # noqa: BLE001
        sn["error"] = f"{type(ex).__name__}: {str(ex)[:200]}"
    result["search_news"] = sn

    # Für die Übersicht: Kennzahlen von get_news() auf die oberste Ebene spiegeln
    result["count"] = gn["count"]
    result["in_window"] = gn["in_window"]
    result["earliest"] = gn["earliest"]
    result["latest"] = gn["latest"]
    result["language_guess"] = gn["language_guess"]
    result["sample_titles"] = gn["sample_titles"]
    result["http_status"] = None
    return result


# ── Monatswahl aus der DB (lesend) ───────────────────────────────────────────

def pick_month_from_db(company: str, min_reviews: int = 5, min_month: str = "2019-01") -> Dict[str, Any]:
    from database.supabase_client import get_supabase_client
    from services.topic_average_rating_service import _fetch_all_rows

    sb = get_supabase_client()
    companies = sb.table("companies").select("id,name").execute().data or []
    target = normalize_name(company)
    matches = [c for c in companies if normalize_name(c.get("name")) == target]
    if not matches:
        known = ", ".join(sorted(normalize_name(c.get("name")) for c in companies))
        raise SystemExit(f"Unternehmen '{company}' nicht in der DB gefunden. Bekannt: {known}")
    if re.fullmatch(r"demo \d+", target):
        raise SystemExit(f"'{company}' ist eine synthetische Demo-Firma und von allen Analysen ausgeschlossen")
    cid = matches[0]["id"]

    q = (sb.table("employee")
         .select("datum,durchschnittsbewertung")
         .eq("company_id", cid)
         .not_.is_("datum", "null"))
    rows = _fetch_all_rows(q)

    sums: Dict[str, float] = defaultdict(float)
    cnt: Dict[str, int] = defaultdict(int)
    for r in rows:
        v = r.get("durchschnittsbewertung")
        if v is None:
            continue
        try:
            dt = datetime.fromisoformat(str(r["datum"]).replace("Z", "+00:00"))
            fv = float(v)
        except (ValueError, TypeError):
            continue
        k = f"{dt.year:04d}-{dt.month:02d}"
        sums[k] += fv
        cnt[k] += 1

    months = sorted(cnt)
    best: Optional[Dict[str, Any]] = None
    for i, m in enumerate(months):
        if i == 0 or m < min_month or cnt[m] < min_reviews:
            continue
        prev = months[i - 1]
        mean, pmean = sums[m] / cnt[m], sums[prev] / cnt[prev]
        delta = mean - pmean
        if best is None or abs(delta) > abs(best["delta"]):
            best = {"month": m, "delta": round(delta, 3), "mean": round(mean, 3), "n": cnt[m],
                    "prev_month": prev, "prev_mean": round(pmean, 3), "n_prev": cnt[prev]}
    if best is None:
        raise SystemExit(f"Kein Monat >= {min_month} mit >= {min_reviews} Bewertungen für '{company}'")
    best.update({"company_id": cid, "db_name": matches[0].get("name"), "employee_rows": len(rows),
                 "rule": f"Monat >= {min_month}, n >= {min_reviews}, max |Δ Monatsmittel durchschnittsbewertung| "
                         f"ggü. Vormonat (Vormonat = letzter Monat mit Daten, unbeschränkt)"})
    return best


# ── Persistenz & Ausgabe ─────────────────────────────────────────────────────

def run_key(company: str, month: str, window_months: int) -> str:
    """Schlüssel im JSON: normalisierter Name|YYYY-MM, bei Fenstern > 1 Monat mit Suffix '+Nm'."""
    suffix = f"+{window_months}m" if window_months > 1 else ""
    return f"{normalize_name(company)}|{month}{suffix}"


def save_run(path: str, key: str, run: Dict[str, Any]) -> None:
    """Merge in die JSON-Datei: Läufe sind nach Schlüssel abgelegt; ein Teil-Lauf
    (--sources ...) ersetzt nur die neu geprüften Quellen, die übrigen bleiben erhalten."""
    store: Dict[str, Any] = {"schema": 1,
                             "description": "Ergebnisse des Quellen-Spikes (scripts/spike_news_sources.py); "
                                            "Schlüssel = normalisierter Firmenname|YYYY-MM[+Nm]",
                             "runs": {}}
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as fh:
                loaded = json.load(fh)
            if isinstance(loaded, dict) and isinstance(loaded.get("runs"), dict):
                store = loaded
        except (OSError, json.JSONDecodeError):
            pass
    previous = store["runs"].get(key)
    if isinstance(previous, dict) and isinstance(previous.get("sources"), dict):
        merged = dict(previous["sources"])
        merged.update(run["sources"])
        run["sources"] = merged
        if run.get("month_selection") is None and previous.get("month_selection"):
            run["month_selection"] = previous["month_selection"]
    store["runs"][key] = run
    store["updated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(store, fh, ensure_ascii=False, indent=2)
        fh.write("\n")


def print_summary(run: Dict[str, Any]) -> None:
    w = run["window"]
    print(f"\n=== {run['company']} | Monat {run['month']} | Fenster {w['start']}..{w['end']} "
          f"| Ticker {run.get('ticker') or '-'} | ISIN {run.get('isin') or '-'}")
    ms = run.get("month_selection")
    if ms:
        print(f"    Monatswahl (DB, employee): {ms['month']} Δ={ms['delta']:+.3f} "
              f"(Mittel {ms['mean']}, n={ms['n']}; Vormonat {ms['prev_month']} Mittel {ms['prev_mean']}, n={ms['n_prev']})")
    for name, res in run["sources"].items():
        err = res.get("error")
        print(f"  [{name:8}] count={res.get('count')} in_window={res.get('in_window')} "
              f"earliest={res.get('earliest')} latest={res.get('latest')} lang={res.get('language_guess')} "
              f"http={res.get('http_status')}")
        if name == "yfinance" and res.get("search_news"):
            sn = res["search_news"]
            print(f"             Search.news: count={sn.get('count')} in_window={sn.get('in_window')} "
                  f"earliest={sn.get('earliest')} latest={sn.get('latest')} err={sn.get('error')}")
        if name == "eqs":
            print(f"             uuid={res.get('company_uuid')} ({res.get('uuid_source')}); "
                  f"Versuche={len(res.get('attempts') or [])}")
        for t in res.get("sample_titles") or []:
            print(f"             - {t[:110]}")
        for n in res.get("notes") or []:
            print(f"             ! {n}")
        if err:
            print(f"             ERROR: {err}")


# ── main ─────────────────────────────────────────────────────────────────────

def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(
        description="Spike: historische Nachrichten je Unternehmen und Monat aus GDELT, Google News RSS, "
                    "EQS News REST und yfinance (lesend, eine Anfrage je Quelle).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__.split("Verwendung (aus backend/):", 1)[1] if "Verwendung" in __doc__ else None,
    )
    ap.add_argument("--company", required=True, help="Firmenname (wird normalisiert gegen die DB gematcht)")
    grp = ap.add_mutually_exclusive_group(required=True)
    grp.add_argument("--month", help="Kalendermonat YYYY-MM")
    grp.add_argument("--pick-month", action="store_true",
                     help="Monat aus der DB wählen (>= 2019, >= 5 Bewertungen, max |Δ Monatsmittel|)")
    ap.add_argument("--ticker", help="Yahoo-Ticker, z. B. TKA.DE (nur börsennotiert)")
    ap.add_argument("--isin", help="ISIN, z. B. DE0007500001 (für EQS-UUID-Suche)")
    ap.add_argument("--window-months", type=int, default=1, help="Fensterlänge in Monaten (Standard 1)")
    ap.add_argument("--query", help="Suchbegriff statt Firmenname (GDELT, Google News, yfinance.Search)")
    ap.add_argument("--sourcelang", help="GDELT sourcelang-Filter, z. B. german")
    ap.add_argument("--eqs-uuid", help="bekannte EQS-companyUUID")
    ap.add_argument("--eqs-find-uuid", type=int, default=0, metavar="MAX_PAGES",
                    help="EQS-UUID über bis zu MAX_PAGES Seiten der Monatsliste suchen (je 100 Einträge, 1 s Pause)")
    ap.add_argument("--sources", default=",".join(ALL_SOURCES), help="Teilmenge: gdelt,gnews,eqs,yfinance")
    ap.add_argument("--out", default=DEFAULT_OUT, help="Ziel-JSON (Merge)")
    ap.add_argument("--no-save", action="store_true", help="nicht speichern")
    args = ap.parse_args(argv)

    sources = [s.strip() for s in args.sources.split(",") if s.strip()]
    unknown = [s for s in sources if s not in ALL_SOURCES]
    if unknown:
        ap.error(f"unbekannte Quelle(n): {', '.join(unknown)}; erlaubt: {', '.join(ALL_SOURCES)}")
    if not sources:
        ap.error(f"--sources darf nicht leer sein; erlaubt: {', '.join(ALL_SOURCES)}")
    if args.window_months < 1:
        ap.error("--window-months muss >= 1 sein")

    month_selection = None
    if args.pick_month:
        month_selection = pick_month_from_db(args.company)
        month = month_selection["month"]
    else:
        month = args.month
        if not re.fullmatch(r"\d{4}-(0[1-9]|1[0-2])", month or ""):
            ap.error("--month muss das Format YYYY-MM haben (Monat 01..12)")

    start, end = month_window(month, args.window_months)
    # Suchbegriff: Whitespace-Defekte der DB-Namen (z. B. doppelte Leerzeichen) nicht in die Anfragen tragen
    query = args.query or re.sub(r"\s+", " ", args.company).strip()

    run: Dict[str, Any] = {
        "company": args.company,
        "company_normalized": normalize_name(args.company),
        "month": month,
        "window": {"start": start.isoformat(), "end": end.isoformat(), "months": args.window_months},
        "ticker": args.ticker,
        "isin": args.isin,
        "query": query,
        "month_selection": month_selection,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "sources": {},
    }

    probes = {
        "gdelt": lambda: probe_gdelt(query, start, end, args.sourcelang),
        "gnews": lambda: probe_gnews(query, start, end),
        "eqs": lambda: probe_eqs(args.company, args.isin, start, end, args.eqs_uuid, args.eqs_find_uuid),
        "yfinance": lambda: probe_yfinance(args.ticker, query, start, end),
    }
    for name in sources:
        t0 = time.monotonic()
        try:
            res = probes[name]()
        except Exception as ex:  # noqa: BLE001 – Spike: jede Quelle isoliert
            res = base_result("")
            res["error"] = f"{type(ex).__name__}: {str(ex)[:300]}"
        res["elapsed_s"] = round(time.monotonic() - t0, 2)
        res["probed_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
        run["sources"][name] = res

    print_summary(run)

    if not args.no_save:
        key = run_key(args.company, month, args.window_months)
        save_run(args.out, key, run)
        print(f"\nGespeichert: {args.out} (Schlüssel '{key}')")
    return 0


if __name__ == "__main__":
    sys.exit(main())
