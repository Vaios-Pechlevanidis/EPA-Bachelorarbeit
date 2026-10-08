"""Hilfen der Belege-Tests (Inkrement 4): nachgebildete RSS-Antworten von Google News.
Eigener Modulname, weil tests/drilldown/_helpers.py im Gesamtlauf denselben Namen belegt."""

from datetime import datetime
from email.utils import format_datetime


def rss(entries):
    """RSS wie Google News: Titel mit angehängter Quelle, Link, pubDate, source.
    ``entries``: (titel, url, tag, herausgeber)."""
    items = []
    for title, url, day, publisher in entries:
        pub = format_datetime(datetime.fromisoformat(day + "T10:00:00+00:00"))
        items.append(f"<item><title>{title} - {publisher}</title><link>{url}</link><pubDate>{pub}</pubDate>"
                     f"<source url=\"https://{publisher.lower()}.example\">{publisher}</source></item>")
    return ("<?xml version=\"1.0\"?><rss version=\"2.0\"><channel><title>t</title><language>de</language>"
            + "".join(items) + "</channel></rss>").encode("utf-8")


class FakeRss:
    """Abruf je Monat: Einträge aus ``by_month``; Monate in ``fail`` werfen; zählt Abfragen."""

    def __init__(self, by_month=None, fail=()):
        self.by_month = by_month or {}
        self.fail = set(fail)
        self.queries = []

    def __call__(self, query):
        self.queries.append(query)
        month = query.split("after:")[1][:7]
        if month in self.fail:
            raise OSError("Netz weg")
        return rss(self.by_month.get(month, []))
