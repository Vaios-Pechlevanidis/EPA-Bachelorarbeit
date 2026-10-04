"""
Fixtures der Drill-down-Tests (Inkrement 2). ``in_memory_db`` kommt aus
``tests/conftest.py``; die Stimmung läuft im Lexikon-Modus (ohne Modell und
ohne Netzwerk).
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from _helpers import analytics_client  # noqa: E402


@pytest.fixture(scope="module")
def api(in_memory_db):
    """TestClient mit Analytics-Router gegen den In-Memory-Store."""
    with pytest.MonkeyPatch.context() as mp:
        yield analytics_client(mp, in_memory_db)


@pytest.fixture(scope="module")
def lexicon_analyzer():
    """Analyzer des Vergleichs im Lexikon-Modus; danach wieder ungesetzt."""
    from models.sentiment_analyzer import SentimentAnalyzer
    from services import explanation_service

    analyzer = SentimentAnalyzer(mode="lexicon")
    explanation_service.set_sentiment_analyzer(analyzer)
    yield analyzer
    explanation_service.set_sentiment_analyzer(None)
