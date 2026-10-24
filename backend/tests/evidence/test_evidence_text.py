"""
Tests für services/evidence_text.py (Texte der Belege, E35, 2026-10-23): Auflösung der
Google-Weiterleitung (konstruierte Seite und Antwort), Text aus HTML, Textspeicher,
Abruf je Beleg mit nachgebildeten Antworten, Anhängen an Belege ohne Änderung der
Eingabe, Drosselung je Host, Speicher außerhalb der Versionierung. Ohne Netz; alle Texte
sind konstruiert.

Ausführung:
    cd backend
    uv run python -m pytest tests/evidence/test_evidence_text.py -q -p no:cacheprovider
"""

import json
import os
import sys
from datetime import datetime, timezone

import pytest

BACKEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
sys.path.insert(0, BACKEND_DIR)

import services.evidence_sources as src  # noqa: E402
import services.evidence_text as et  # noqa: E402

NOW = datetime(2026, 10, 23, 12, 0, tzinfo=timezone.utc)
GID = "CBMiAbc_DEF-123"
GOOGLE_URL = f"https://news.google.com/rss/articles/{GID}?oc=5"
TARGET = "https://www.verlag.example/wirtschaft/artikel-eins/"
ARTICLE_PAGE = ('<html><body><c-wiz data-n-a-id="x" data-n-a-sg="SIG.abc" data-n-a-ts="1700000000">'
                '<a href="#">Öffnen</a></c-wiz></body></html>')
BATCH_BODY = (")]}'\n\n123\n"
              '[["wrb.fr","Fbv4je","[\\"garturlres\\",\\"' + TARGET + '\\",1]",null,null,null,"generic"],["di",47]]\n')
LONG_P = "Das Unternehmen kündigt einen Stellenabbau an und will Standorte zusammenlegen, sagte die Sprecherin am Montag."
LONG_P2 = ("Der Betriebsrat kündigte Widerstand an und verwies auf die Zusagen aus dem Vorjahr, nach denen betriebsbedingte "
           "Kündigungen bis Ende des Jahrzehnts ausgeschlossen sein sollten.")
PAGE = ("<html><head><title>T</title><style>p{}</style><script>var a=1;</script></head><body>"
        "<nav><p>Startseite Wirtschaft Politik Sport Kultur Abo Newsletter Anmelden</p></nav>"
        "<article><h1>Stellenabbau beim Beispielkonzern angekündigt</h1>"
        f"<p>{LONG_P}</p><p>{LONG_P}</p><p>{LONG_P2}</p><p>kurz</p><ul><li>Betroffen sind nach Angaben des Betriebsrats rund 400 Beschäftigte am Standort Nord.</li></ul>"
        "<figure><figcaption>Ein Bild mit einer langen Bildunterschrift, die nicht zum Text gehört.</figcaption></figure></article>"
        "<aside><p>Mehr zum Thema: Weitere Artikel aus der Rubrik Wirtschaft finden Sie hier in der Übersicht.</p></aside>"
        "<footer><p>Impressum Datenschutz Kontakt AGB Mediadaten Jobs bei uns Hilfe und Kontakt</p></footer></body></html>")


def item(kind="news", url=None, title="Stellenabbau beim Beispielkonzern angekündigt"):
    """Beleg; ohne ``url`` der Google-Link, bei abweichendem Titel ein eigener Link (die Kennung folgt dem Link)."""
    if url is None:
        url = GOOGLE_URL if title == "Stellenabbau beim Beispielkonzern angekündigt" else f"https://news.google.com/rss/articles/{abs(hash(title))}"
    return src.make_item(title=title, url=url, published_at="2024-07-10", publisher="Verlag", source="gnews" if kind == "news" else "eqs",
                         source_type=kind)


class FakeHttp:
    """GET/POST nachgebildet: Antworten je Adresse; zählt Aufrufe; Adressen in ``fail`` werfen."""

    def __init__(self, pages=None, fail=()):
        self.pages = pages or {}
        self.fail = set(fail)
        self.calls = []

    def get(self, url):
        self.calls.append(("GET", url))
        if url in self.fail:
            raise OSError("Netz weg")
        if url not in self.pages:
            raise KeyError(url)
        page = self.pages[url]
        return page.encode("utf-8") if isinstance(page, str) else page

    def post(self, url, data):
        self.calls.append(("POST", url, data))
        if url in self.fail:
            raise OSError("Netz weg")
        return self.pages[url].encode("utf-8")


@pytest.fixture(autouse=True)
def quiet_throttle(monkeypatch):
    monkeypatch.setattr(src, "_last_request", {})
    monkeypatch.setattr(src, "_source_locks", {})


# ── Google-Weiterleitung ────────────────────────────────────────────────────

class TestGoogleDecode:
    def test_article_id_from_both_link_forms(self):
        assert et.google_article_id(GOOGLE_URL) == GID
        assert et.google_article_id(f"https://news.google.com/articles/{GID}") == GID
        assert et.google_article_id("https://www.verlag.example/a") is None
        assert et.google_article_id(None) is None

    def test_params_from_article_page(self):
        assert et.google_decode_params(ARTICLE_PAGE) == ("SIG.abc", 1700000000)
        assert et.google_decode_params(ARTICLE_PAGE.encode()) == ("SIG.abc", 1700000000)
        assert et.google_decode_params("<html>ohne Attribute</html>") is None
        assert et.google_decode_params('<c-wiz data-n-a-sg="s" data-n-a-ts="x">') is None

    def test_payload_names_id_timestamp_and_signature(self):
        payload = et.google_decode_payload(GID, 1700000000, "SIG.abc").decode()
        assert payload.startswith("f.req=")
        import urllib.parse
        outer = json.loads(urllib.parse.unquote(payload[len("f.req="):]))
        inner = json.loads(outer[0][0][1])
        assert outer[0][0][0] == "Fbv4je" and inner[0] == "garturlreq"
        assert inner[-3:] == [GID, 1700000000, "SIG.abc"]

    def test_parse_response_json_lines_and_escaped_fallback(self):
        assert et.parse_google_decode(BATCH_BODY) == TARGET
        assert et.parse_google_decode(BATCH_BODY.encode()) == TARGET
        one_line = '[\\"garturlres\\",\\"https://a.example/x?y=1\\",1]'
        assert et.parse_google_decode(one_line) == "https://a.example/x?y=1"
        assert et.parse_google_decode(")]}'\n[[\"wrb.fr\",\"Fbv4je\",\"[\\\"garturlres\\\",\\\"javascript:1\\\"]\"]]") is None
        assert et.parse_google_decode("") is None
        assert et.parse_google_decode("nichts") is None

    def test_resolve_makes_two_throttled_requests(self):
        http = FakeHttp({et.GOOGLE_ARTICLE_URL.format(article_id=GID): ARTICLE_PAGE, et.GOOGLE_BATCH_URL: BATCH_BODY})
        waits = []
        clock = iter([0.0, 0.5, 2.5]).__next__   # erste Anfrage bei 0, zweite bei 0,5 wartet 1,5 s, danach 2,5
        target = et.resolve_google_url(GOOGLE_URL, fetcher=http.get, poster=http.post, sleep=waits.append, clock=clock)
        assert target == TARGET
        assert [c[0] for c in http.calls] == ["GET", "POST"]
        assert waits == [pytest.approx(1.5)]   # zweite Anfrage an Google News wartet den Abstand (2 s) ab

    def test_resolve_passes_non_google_links_through_and_raises_on_missing_parts(self):
        assert et.resolve_google_url(TARGET, fetcher=lambda u: b"", poster=lambda u, d: b"", sleep=lambda s: None) == TARGET
        http = FakeHttp({et.GOOGLE_ARTICLE_URL.format(article_id=GID): "<html></html>"})
        with pytest.raises(ValueError, match="Signatur"):
            et.resolve_google_url(GOOGLE_URL, fetcher=http.get, poster=http.post, sleep=lambda s: None)
        http = FakeHttp({et.GOOGLE_ARTICLE_URL.format(article_id=GID): ARTICLE_PAGE, et.GOOGLE_BATCH_URL: ")]}'\n[]"})
        with pytest.raises(ValueError, match="Zieladresse"):
            et.resolve_google_url(GOOGLE_URL, fetcher=http.get, poster=http.post, sleep=lambda s: None)


# ── Text aus HTML ────────────────────────────────────────────────────────────

class TestExtractMainText:
    def test_article_paragraphs_without_navigation_and_short_lines(self):
        text = et.extract_main_text(PAGE)
        lines = text.split("\n")
        assert lines[0] == "Stellenabbau beim Beispielkonzern angekündigt"
        assert LONG_P in lines and lines.count(LONG_P) == 1 and LONG_P2 in lines   # gleiche Absätze einmal
        assert any(l.startswith("Betroffen sind") for l in lines)
        assert "kurz" not in lines and "Startseite" not in text and "Impressum" not in text
        assert "Bildunterschrift" not in text and "Mehr zum Thema" not in text and "var a" not in text

    def test_main_then_body_when_no_long_article(self):
        html = f"<html><body><main><p>{LONG_P}</p></main><p>{LONG_P} zweite</p></body></html>"
        assert et.extract_main_text(html) == LONG_P
        html = f"<html><body><div><p>{LONG_P}</p></div></body></html>"
        assert et.extract_main_text(html) == LONG_P
        assert et.extract_main_text("") == ""
        assert et.extract_main_text(b"") == ""

    def test_longest_article_wins_and_text_is_capped(self):
        short = "<article><p>Teaser eines anderen Artikels, der nur angerissen wird und kurz bleibt.</p></article>"
        long_ = "<article>" + "".join(f"<p>{LONG_P} {i}</p>" for i in range(12)) + "</article>"
        text = et.extract_main_text(f"<html><body>{short}{long_}</body></html>")
        assert "Teaser" not in text and text.count(LONG_P) == 12
        huge = "<html><body><article>" + "".join(f"<p>{LONG_P} {i}</p>" for i in range(2000)) + "</article></body></html>"
        assert len(et.extract_main_text(huge)) == et.MAX_TEXT_CHARS


# ── Textspeicher ─────────────────────────────────────────────────────────────

class TestStore:
    def test_path_load_save_roundtrip(self, tmp_path):
        record = et._record(7, item(), status=et.STATUS_OK, text="x" * 400, target_url=TARGET, now=NOW)
        path = et.save_text(record, tmp_path)
        assert path == tmp_path / "7" / f"{item()['id']}.json" and path.exists()
        assert et.load_text(7, item()["id"], tmp_path) == record
        assert et.load_text(8, item()["id"], tmp_path) is None
        assert et.load_text(7, "andere", tmp_path) is None
        assert record["fetched_at"] == "2026-10-23T12:00:00+00:00" and record["n_chars"] == 400

    def test_unreadable_file_is_none(self, tmp_path):
        path = et.text_path(7, "abc", tmp_path)
        path.parent.mkdir(parents=True)
        path.write_text("{kaputt", encoding="utf-8")
        assert et.load_text(7, "abc", tmp_path) is None

    def test_store_is_ignored_by_git(self):
        with open(os.path.join(BACKEND_DIR, "..", ".gitignore"), encoding="utf-8") as fh:
            assert "backend/data/context_text/" in fh.read()
        assert et.TEXT_DIR.name == "context_text"


# ── Abruf je Beleg ───────────────────────────────────────────────────────────

class TestFetchItemText:
    def test_news_resolves_google_and_reads_publisher(self):
        http = FakeHttp({et.GOOGLE_ARTICLE_URL.format(article_id=GID): ARTICLE_PAGE, et.GOOGLE_BATCH_URL: BATCH_BODY, TARGET: PAGE})
        record = et.fetch_item_text(7, item(), fetcher=http.get, poster=http.post, sleep=lambda s: None, now=NOW)
        assert record["status"] == et.STATUS_OK and record["target_url"] == TARGET and record["error"] is None
        assert record["text"].startswith("Stellenabbau beim Beispielkonzern") and record["n_chars"] == len(record["text"])
        assert record["id"] == item()["id"] and record["company_id"] == 7 and record["source_type"] == "news"
        assert [c[0] for c in http.calls] == ["GET", "POST", "GET"] and http.calls[-1][1] == TARGET

    def test_adhoc_reads_the_notice_page_directly(self):
        url = "https://www.eqs-news.com/news/adhoc/beispiel/abc"
        http = FakeHttp({url: f"<html><body><main><p>{LONG_P}</p></main></body></html>"})
        record = et.fetch_item_text(7, item("adhoc", url=url), fetcher=http.get, poster=http.post, sleep=lambda s: None, now=NOW)
        assert record["status"] == et.STATUS_SHORT and record["text"] == LONG_P and record["target_url"] == url
        assert [c[0] for c in http.calls] == ["GET"]

    def test_failures_become_status_without_raising(self):
        http = FakeHttp({et.GOOGLE_ARTICLE_URL.format(article_id=GID): ARTICLE_PAGE, et.GOOGLE_BATCH_URL: BATCH_BODY}, fail=[TARGET])
        record = et.fetch_item_text(7, item(), fetcher=http.get, poster=http.post, sleep=lambda s: None, now=NOW)
        assert record["status"] == et.STATUS_FAILED and record["target_url"] is None and "OSError" in record["error"]
        http = FakeHttp({et.GOOGLE_ARTICLE_URL.format(article_id=GID): ARTICLE_PAGE, et.GOOGLE_BATCH_URL: BATCH_BODY,
                         TARGET: "<html><body><p>kurz</p></body></html>"})
        record = et.fetch_item_text(7, item(), fetcher=http.get, poster=http.post, sleep=lambda s: None, now=NOW)
        assert record["status"] == et.STATUS_FAILED and record["target_url"] == TARGET and "kein Text" in record["error"]
        record = et.fetch_item_text(7, {**item(), "source_type": "global", "url": ""}, fetcher=http.get, now=NOW)
        assert record["status"] == et.STATUS_FAILED and "kein abrufbarer Link" in record["error"]

    def test_text_record_uses_store_and_retries_failures_only_on_request(self, tmp_path):
        http = FakeHttp({et.GOOGLE_ARTICLE_URL.format(article_id=GID): ARTICLE_PAGE, et.GOOGLE_BATCH_URL: BATCH_BODY}, fail=[TARGET])
        first = et.text_record(7, item(), text_dir=tmp_path, fetcher=http.get, poster=http.post, sleep=lambda s: None, now=NOW)
        assert first["fetched_now"] and first["record"]["status"] == et.STATUS_FAILED
        again = et.text_record(7, item(), text_dir=tmp_path, fetcher=http.get, poster=http.post, sleep=lambda s: None, now=NOW)
        assert not again["fetched_now"] and again["record"]["status"] == et.STATUS_FAILED
        http.fail.clear()
        http.pages[TARGET] = PAGE
        retry = et.text_record(7, item(), text_dir=tmp_path, retry_failed=True, fetcher=http.get, poster=http.post,
                               sleep=lambda s: None, now=NOW)
        assert retry["fetched_now"] and retry["record"]["status"] == et.STATUS_OK
        stored = et.text_record(7, item(), text_dir=tmp_path, fetch=False)
        assert not stored["fetched_now"] and stored["record"]["status"] == et.STATUS_OK
        assert et.text_record(7, item(title="neu"), text_dir=tmp_path, fetch=False)["record"] is None


# ── Anhängen an Belege ───────────────────────────────────────────────────────

class TestAttachTexts:
    def test_copies_with_text_and_counts(self, tmp_path):
        ok, short, failed, none = item(), item(title="zwei"), item(title="drei"), item(title="vier")
        et.save_text(et._record(7, ok, status=et.STATUS_OK, text="a" * 400, now=NOW), tmp_path)
        et.save_text(et._record(7, short, status=et.STATUS_SHORT, text="b" * 50, now=NOW), tmp_path)
        et.save_text(et._record(7, failed, status=et.STATUS_FAILED, error="x", now=NOW), tmp_path)
        glob_ = {**item(title="Ereignis"), "source_type": "global"}
        items = [ok, short, failed, none, glob_]
        out, counts = et.attach_texts(7, items, tmp_path)
        assert counts == {"items": 5, "with_text": 2, "ok": 1, "kurz": 1, "fehlgeschlagen": 1}
        assert out[0]["text"] == "a" * 400 and out[0]["text_status"] == "ok"
        assert out[1]["text"] == "b" * 50 and out[1]["text_status"] == "kurz"
        assert all("text" not in o for o in out[2:])
        assert all("text" not in i for i in items), "die Eingabe bleibt ohne Text"
        assert [o["id"] for o in out] == [i["id"] for i in items]

    def test_empty(self, tmp_path):
        assert et.attach_texts(7, [], tmp_path) == ([], {"items": 0, "with_text": 0, "ok": 0, "kurz": 0, "fehlgeschlagen": 0})
