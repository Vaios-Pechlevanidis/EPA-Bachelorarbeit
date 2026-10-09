"""
Bezeichnung der Erklärungsansätze nach Signalen (Nachtrag zu E21, Inkrement 6,
2026-10-09): ``signal_label`` je Beleg, Bündel und Eintrag nennt genau die
vorhandenen Signale (Wortbezug, Ereignisart, Themenverschiebung, ohne
Arbeitgeberbezug). Stufenregeln, ``test_frozen_rules.py`` und die Zahlen aus E23
bleiben unverändert: ``ranking_numbers`` liefert für konstruierte Belege dieselben
Stufen, Bündel und Ränge wie der Code vor dem Nachtrag (Referenz erzeugt auf
Commit 9870875). Alle Titel sind konstruiert.

Ausführung:
    cd backend
    uv run python -m pytest tests/explanations/test_signal_labels.py -q -p no:cacheprovider
"""

import itertools
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))

import services.explanation_ranking as er  # noqa: E402

import services.evidence_service as ev  # noqa: E402
import services.evidence_sources as src  # noqa: E402
from services.event_categories import load_event_categories  # noqa: E402
from services.review_terms import distinctive_terms  # noqa: E402

CATS = load_event_categories(use_cache=False)
WINDOW = ev.window_for_change("2023-04", "2023-02", 1, 3, 1)


def item(n, title, day, source_type="news", publisher="Blatt", category=None):
    return src.make_item(title=title, url=f"https://beispiel.invalid/{n}", published_at=day, publisher=publisher,
                         source="eqs" if source_type == "adhoc" else "gnews", source_type=source_type, category=category)


def reviews(n, text, start):
    return [{"id": start + i, "datum": "2023-04-10", "schlecht_am_arbeitgeber_finde_ich": text} for i in range(n)]


def ranking_numbers(er):
    before = reviews(20, "Alles ruhig im Büro", 1)
    after = reviews(12, "Der Stellenabbau drückt die Stimmung", 100) + reviews(8, "Alles ruhig im Büro", 200)
    terms = distinctive_terms(before, after, exclude={"beispielwerk"})
    topics = er.topic_shift_table(before, after, "employee")
    items = [
        item(1, "Beispielwerk kündigt Stellenabbau in der Verwaltung an", "2023-02-10", publisher="A"),
        item(2, "Beispielwerk kündigt Stellenabbau an", "2023-02-11", publisher="B"),
        item(3, "Beispielwerk: Stellenabbau in der Verwaltung angekündigt", "2023-02-12", source_type="adhoc", publisher="EQS News", category="Ad-hoc"),
        item(4, "Aktie von Beispielwerk erreicht Kursziel", "2023-02-15", publisher="C"),
        item(5, "Beispielwerk gewinnt Pokalspiel", "2023-04-02", publisher="D"),
        item(6, "Neuer Chef bei Beispielwerk", "2022-12-05", publisher="E"),
        item(7, "Beispielwerk eröffnet Kantine", "2023-05-20", publisher="F"),
        item(8, "Beispielwerk streicht Stellen im Vertrieb", "2023-01-20", publisher="G"),
        item(9, "Vorstand von Beispielwerk tritt zurück", "2023-02-20", publisher="H"),
        item(10, "Stellenabbau-Gerüchte bei Beispielwerk", "2023-02-25", publisher="I"),
        item(11, "Stellenabbau beim Pokalsieger Beispielwerk", "2023-03-10", publisher="J"),
    ]
    out = {}
    for name, topics_ in (("mit_themen", topics), ("ohne_themen", [])):
        for grouped in (True, False):
            r = er.rank_evidence(items, WINDOW, terms=terms, topics=topics_, exclude={"beispielwerk"}, categories=CATS,
                                 analyzer=None, group_by_category=grouped)
            out[f"{name}/{grouped}"] = {
                "state": r["state"], "n_items": r["n_items"], "n_bundles": r["n_bundles"], "n_groups": r["n_groups"],
                "n_by_stage": r["n_by_stage"],
                "confidence": [e["confidence"] for e in r["explanations"]],
                "item_stages": {k: [v["stage"], v["item_stage"], v["rank"]] for k, v in sorted(r["item_scores"].items())},
            }
    return out


# Stand vor dem Nachtrag (Commit 9870875), erzeugt mit ranking_numbers(er) auf diesem Commit.
REFERENCE = {
    "mit_themen/False": {
        "confidence": [
            "hoch",
            "hoch",
            "hoch",
            "mittel",
            "niedrig"
        ],
        "item_stages": {
            "0bd276c175ad8cd3": [
                "mittel",
                "mittel",
                6
            ],
            "34e843656879dd05": [
                "hoch",
                "hoch",
                5
            ],
            "5c0d8a90cbc348b9": [
                "hoch",
                "hoch",
                2
            ],
            "7785564e45902af1": [
                "keine",
                "keine",
                11
            ],
            "8f855e544b9d5ca0": [
                "keine",
                "keine",
                9
            ],
            "93e72cc60d3315b2": [
                "niedrig",
                "niedrig",
                8
            ],
            "9518bc0c7aeb6812": [
                "niedrig",
                "niedrig",
                7
            ],
            "a64d1fc430acc3da": [
                "hoch",
                "hoch",
                3
            ],
            "d52c4cf1afb9b688": [
                "hoch",
                "hoch",
                1
            ],
            "f6a5e86b1a160e84": [
                "keine",
                "keine",
                10
            ],
            "fb7fb7bdf467968e": [
                "hoch",
                "hoch",
                4
            ]
        },
        "n_bundles": 9,
        "n_by_stage": {
            "hoch": 3,
            "keine": 3,
            "mittel": 1,
            "niedrig": 2
        },
        "n_groups": 2,
        "n_items": 11,
        "state": "ansaetze"
    },
    "mit_themen/True": {
        "confidence": [
            "hoch",
            "niedrig"
        ],
        "item_stages": {
            "0bd276c175ad8cd3": [
                "mittel",
                "mittel",
                6
            ],
            "34e843656879dd05": [
                "hoch",
                "hoch",
                5
            ],
            "5c0d8a90cbc348b9": [
                "hoch",
                "hoch",
                2
            ],
            "7785564e45902af1": [
                "keine",
                "keine",
                11
            ],
            "8f855e544b9d5ca0": [
                "keine",
                "keine",
                9
            ],
            "93e72cc60d3315b2": [
                "niedrig",
                "niedrig",
                8
            ],
            "9518bc0c7aeb6812": [
                "niedrig",
                "niedrig",
                7
            ],
            "a64d1fc430acc3da": [
                "hoch",
                "hoch",
                3
            ],
            "d52c4cf1afb9b688": [
                "hoch",
                "hoch",
                1
            ],
            "f6a5e86b1a160e84": [
                "keine",
                "keine",
                10
            ],
            "fb7fb7bdf467968e": [
                "hoch",
                "hoch",
                4
            ]
        },
        "n_bundles": 9,
        "n_by_stage": {
            "hoch": 3,
            "keine": 3,
            "mittel": 1,
            "niedrig": 2
        },
        "n_groups": 2,
        "n_items": 11,
        "state": "ansaetze"
    },
    "ohne_themen/False": {
        "confidence": [
            "hoch",
            "hoch",
            "hoch",
            "mittel",
            "niedrig"
        ],
        "item_stages": {
            "0bd276c175ad8cd3": [
                "mittel",
                "mittel",
                6
            ],
            "34e843656879dd05": [
                "hoch",
                "hoch",
                5
            ],
            "5c0d8a90cbc348b9": [
                "hoch",
                "hoch",
                2
            ],
            "7785564e45902af1": [
                "keine",
                "keine",
                11
            ],
            "8f855e544b9d5ca0": [
                "keine",
                "keine",
                9
            ],
            "93e72cc60d3315b2": [
                "niedrig",
                "niedrig",
                8
            ],
            "9518bc0c7aeb6812": [
                "niedrig",
                "niedrig",
                7
            ],
            "a64d1fc430acc3da": [
                "hoch",
                "hoch",
                3
            ],
            "d52c4cf1afb9b688": [
                "hoch",
                "hoch",
                1
            ],
            "f6a5e86b1a160e84": [
                "keine",
                "keine",
                10
            ],
            "fb7fb7bdf467968e": [
                "hoch",
                "hoch",
                4
            ]
        },
        "n_bundles": 9,
        "n_by_stage": {
            "hoch": 3,
            "keine": 3,
            "mittel": 1,
            "niedrig": 2
        },
        "n_groups": 2,
        "n_items": 11,
        "state": "ansaetze"
    },
    "ohne_themen/True": {
        "confidence": [
            "hoch",
            "niedrig"
        ],
        "item_stages": {
            "0bd276c175ad8cd3": [
                "mittel",
                "mittel",
                6
            ],
            "34e843656879dd05": [
                "hoch",
                "hoch",
                5
            ],
            "5c0d8a90cbc348b9": [
                "hoch",
                "hoch",
                2
            ],
            "7785564e45902af1": [
                "keine",
                "keine",
                11
            ],
            "8f855e544b9d5ca0": [
                "keine",
                "keine",
                9
            ],
            "93e72cc60d3315b2": [
                "niedrig",
                "niedrig",
                8
            ],
            "9518bc0c7aeb6812": [
                "niedrig",
                "niedrig",
                7
            ],
            "a64d1fc430acc3da": [
                "hoch",
                "hoch",
                3
            ],
            "d52c4cf1afb9b688": [
                "hoch",
                "hoch",
                1
            ],
            "f6a5e86b1a160e84": [
                "keine",
                "keine",
                10
            ],
            "fb7fb7bdf467968e": [
                "hoch",
                "hoch",
                4
            ]
        },
        "n_bundles": 9,
        "n_by_stage": {
            "hoch": 3,
            "keine": 3,
            "mittel": 1,
            "niedrig": 2
        },
        "n_groups": 2,
        "n_items": 11,
        "state": "ansaetze"
    }
}

TERMS = (0.0, 0.5, 1.0)
CATEGORIES = (0.0, 0.5, 1.0)
EMPLOYER = (None, True, False)


def expected_signals(term, category, employer):
    return {
        "Wortbezug": term >= 0.5,
        "Ereignisart": category >= 0.5,
        "Themenverschiebung": category >= 1.0,
        "ohne Arbeitgeberbezug": employer is False,
    }


@pytest.mark.parametrize("term,category,employer", list(itertools.product(TERMS, CATEGORIES, EMPLOYER)))
def test_label_names_exactly_the_present_signals(term, category, employer):
    label = er.signal_label(term, category, employer)
    parts = label.split(er.SIGNAL_SEPARATOR) if label != er.SIGNAL_NONE_LABEL else []
    for name, present in expected_signals(term, category, employer).items():
        assert (name in parts) is present, (name, label)
    assert all(p in er.SIGNAL_NAMES for p in parts)
    assert parts == [n for n in er.SIGNAL_NAMES if n in parts], "feste Reihenfolge"
    if not parts:
        assert label == "kein Signal"


def test_reachable_item_combinations_have_distinct_labels():
    """Auf Belegebene erreichbar: ohne Ereignisart (employer None, category 0), mit
    Arbeitgeberbezug (category 0,5 oder 1), ohne Arbeitgeberbezug (category 0); je mit und
    ohne Wortbezug. Acht Kombinationen, acht verschiedene Bezeichnungen."""
    reachable = [(t, c, e) for t in (0.0, 0.5) for c, e in ((0.0, None), (0.5, True), (1.0, True), (0.0, False))]
    labels = {er.signal_label(*r) for r in reachable}
    assert len(labels) == 8
    assert er.signal_label(0.5, 1.0, True) == "Wortbezug · Ereignisart · Themenverschiebung"
    assert er.signal_label(0.0, 0.5, True) == "Ereignisart"
    assert er.signal_label(0.5, 0.0, False) == "Wortbezug · ohne Arbeitgeberbezug"
    assert er.signal_label(0.0, 0.0, None) == "kein Signal"


def test_label_does_not_depend_on_time_and_stage_rules_unchanged():
    for t, c, e in itertools.product(TERMS, CATEGORIES, EMPLOYER):
        for z in (0.0, 0.3, 0.5, 1.0):
            assert er.stage_for(t, c, z, e) in er.STAGES
    assert er.RULES_VERSION == 2 and "signal_labels" not in er.rules()


def test_fields_on_items_bundles_entries_and_item_scores():
    result = er.rank_evidence(
        [item(1, "Beispielwerk kündigt Stellenabbau an", "2023-02-10"),
         item(2, "Beispielwerk gewinnt Pokalspiel", "2023-04-02")],
        WINDOW, terms=[], topics=[], exclude={"beispielwerk"}, categories=CATS, analyzer=None)
    for e in result["explanations"]:
        assert e["signal_label"] and all(i["signal_label"] for i in e["items"])
        for o in (e.get("group") or {}).get("others", []):
            assert o["signal_label"]
    for score in result["item_scores"].values():
        assert score["signal_label"] and score["item_signal_label"]
    top = result["explanations"][0]
    assert top["signal_label"] == "Ereignisart" and top["confidence"] == "niedrig"
    assert sum(result["n_by_signal_label"].values()) == sum(v for k, v in result["n_by_stage"].items() if k != "keine")


def test_ranking_numbers_unchanged_against_reference():
    assert ranking_numbers(er) == REFERENCE
