# Passung und Unterschied der Erklärungsansätze (DZ2, Ergänzung zu E23)

| | |
|---|---|
| Gegenstand | Erklärungsansätze „Mögliche Zusammenhänge“ (Inkrement 5, E21–E23; Feature-Doku 08) |
| Zweck | Zwei offene Fragen der Auswertung E23 beantworten: Wie gut passt der einzelne Erklärungsansatz zu seiner Veränderung, und unterscheiden die Ansätze Markierungsfenster von Vergleichsfenstern mit Test und Konfidenzintervall? |
| Werkzeug | `backend/scripts/rate_explanations.py` (Unterbefehle `bogen`, `pruefen`, `auswerten`); Agent `erklaerungs-bewertung` (`.claude/agents/`) |
| Tests | `backend/tests/explanations/test_rate_explanations.py` |
| Status | Instrument angelegt am 2026-10-17; Teil A (Tests auf den Stufen des Berichts vom 2026-10-13) einmal gerechnet; blinde Bewertung (Teil B) noch nicht gelaufen; Einordnung in E23 Entscheidung des Autors |
| Stand | 2026-10-17 |

## 1. Ausgangslage

Die Auswertung E23 rechnet für jedes Markierungsfenster (Niveauwechsel und auffällige
Einzelmonate) und jedes verschobene Vergleichsfenster desselben Unternehmens (E18: um ±12 und
±24 Monate) dieselbe Rangfolge wie das Dashboard und zählt, wie viele Fenster einen
Erklärungsansatz je Stufe haben. Befund (Lauf vom 2026-10-13): 23 von 28 Markierungen und 57 von
72 Vergleichsfenstern haben mindestens einen Ansatz; die Anteile „liegen in derselben
Größenordnung“. E23 verzichtet ausdrücklich auf eine Signifikanzaussage und sagt nichts darüber,
ob ein einzelner Ansatz inhaltlich zu seiner Veränderung passt.

Das hier beschriebene Instrument ergänzt E23 um beides, ohne eine Schwelle, eine Stufenregel oder
eine Datei des Berichts zu ändern.

## 2. Frage 1: Passung (blinde Beurteilung)

**Passung** heißt hier: Beschreibt die Meldung ein Ereignis, das zu der beschriebenen Veränderung
der Bewertungen passt (richtiges Unternehmen, Arbeitgeberbezug, zeitliche Lage, Stoßrichtung,
Wortbezug)? Sie ist ein Urteil über den Inhalt des Titels im Verhältnis zur Veränderung, keine
Aussage über Ursachen.

**Bogen (blind).** `bogen` erzeugt für jedes Markierungs- und jedes Vergleichsfenster denselben
Datensatz: Unternehmen, Fensterart, Monate, Richtung der Veränderung in den Bewertungen (aus dem
Mittel der Gesamtnote der beiden Vergleichsfenster nach E12/E17, für beide Gruppen gleich
gerechnet), Zahl der Bewertungen, kennzeichnende Begriffe, merklich verschobene Themen, Zahl der
Belege und Bündel, und die obersten drei Erklärungsansätze mit Titel, Datum, Herausgeber,
Quellenart, Sprache, „Unternehmen im Titel“, Lage im Fenster, Signalen, Stufe und der Begründung
des Systems. Die Fenster werden gemischt und mit Kennungen `F-001` … versehen. **Nicht** im Bogen
stehen: ob das Fenster eine Markierung trägt, der Versatz, der Referenztreffer (E5) und die Größe
der Verschiebung. Das steht im getrennten **Schlüssel**, den die bewertende Instanz erst nach
Abschluss der Urteile öffnet. Die Zeitangaben im Begründungstext folgen bei Vergleichsfenstern
der Art der zugehörigen Markierung („im auffälligen Monat“ statt „im Übergang“), damit die
Wortwahl die Gruppe nicht verrät.

**Skala** (Setzung, im Bogen und im Skript als `PASSUNG_RULES`):

| Passung | Bedeutung |
|---|---|
| 3 – passend | Meldung betrifft erkennbar dieses Unternehmen als Arbeitgeber, liegt vor oder im Übergang (bei Einzelmonaten vor oder im auffälligen Monat), passt in der Stoßrichtung zur Richtung der Veränderung, oder ein kennzeichnender Begriff der Bewertungen benennt dasselbe Ereignis |
| 2 – teilweise passend | Arbeitgeberbezug und richtiges Unternehmen, aber Richtung neutral oder unklar, Meldung erst nach dem markierten Monat, oder nur allgemeiner Bezug |
| 1 – kaum passend | kein Arbeitgeberbezug (Produkt, Kurs, Sport, Kapitalmarkt), mehrdeutiges Schlüsselwort oder mehrdeutiger Begriff, Unternehmen nur am Rand erwähnt |
| 0 – nicht passend | anderes Unternehmen (fremder Treffer), kein Bezug zur Belegschaft und kein Begriff, oder zeitlich ohne sinnvolle Lage |

Dazu je Ansatz die **Richtung** (passt, neutral, widerspricht, unklar) und eine Begründung in
eigenen Worten ohne Titelzitat. Schwelle „passend“ in der Auswertung: Passung mindestens 2.

**Bewertende Instanz.** Vorgesehen ist der Agent `erklaerungs-bewertung` (ein Sprachmodell);
dieselbe Vorlage kann eine Person ausfüllen. Die Urteile eines Sprachmodells sind keine
Expertenurteile; das wird in `bewertungen.json` (`rater`), im Bericht und im Commit offengelegt.
Eine zweite bewertende Instanz und ein Maß der Übereinstimmung sind nicht Teil des Instruments
(offener Punkt).

## 3. Frage 2: Unterschied (Tests)

Markierungsfenster und ihre Vergleichsfenster sind nicht unabhängig: Jedes Vergleichsfenster
gehört zu genau einer Markierung desselben Unternehmens (Cluster aus Markierung und bis zu drei
Vergleichsfenstern). Deshalb rechnet `auswerten` je Merkmal:

- **Anteile und Differenz** in Prozentpunkten, Markierungen gegen Vergleichsfenster.
- **Konfidenzintervall nach Newcombe** (Methode 10, 95 %) für die Differenz zweier Anteile:
  Bereich der Differenzen, der mit den Daten verträglich ist. Enthält es 0, ist „kein
  Unterschied“ mit den Daten verträglich; seine Breite zeigt, wie wenig die Daten festlegen.
- **Exakter Test nach Fisher** (zweiseitig) auf der Vierfeldertafel; er behandelt die Fenster
  als unabhängig und ist hier nur Vergleichswert.
- **Permutationstest in Clustern** (20 000 Permutationen, fester Startwert): Unter der
  Nullhypothese ist innerhalb jedes Clusters jedes Fenster gleich wahrscheinlich das
  Markierungsfenster. Der Test vergibt die Rolle „Markierung“ je Cluster zufällig neu und zählt,
  wie oft die Differenz der Mittelwerte mindestens so groß ausfällt wie beobachtet. Er
  berücksichtigt die Abhängigkeit und ist der maßgebliche Test. Dazu die gepaarte Sicht:
  Markierung minus Mittel ihrer Vergleichsfenster je Cluster.
- **Nachweisbare Differenz** (Teststärke 80 %, Niveau 5 %, Normalnäherung): der Anteil bei
  Markierungen, ab dem ein Unterschied zum beobachteten Vergleichsanteil mit diesen Fallzahlen
  überhaupt gefunden würde. Mit 28 gegen 72 Fenstern und einem Vergleichsanteil von 79 % wären
  nur Anteile über 96 % oder unter 49 % nachweisbar. Ein p-Wert über 0,05 heißt deshalb nicht
  „kein Unterschied“, sondern „ein Unterschied dieser Größe ist hier nicht nachweisbar“.
- **Rangmerkmal** oberste Stufe (offen 0, niedrig 1, mittel 2, hoch 3): Mittelwerte und
  Permutationstest.
- **Rangkorrelation nach Spearman** (mit Permutationstest) zwischen Stufe und Passung sowie
  zwischen Zahl der Belege und Stufe (Nullmodell des Gutachtens vom 2026-10-13: folgt die
  Abdeckung der Belegdichte?); zusätzlich die Anteile „mit Ansatz“ je Drittel der Belegzahl.

Teil A rechnet diese Tests auf den Stufen des vorhandenen Berichts
(`explanation_validity_korrektur_2026-10-13.json`, ohne Datenbank). Teil B rechnet sie auf den
entblindeten Passungsurteilen (oberster Ansatz passend, bester Ansatz passend, mittlere Passung;
einmal nur für Fenster mit Ansatz, einmal für alle Fenster mit „offen“ als Passung 0), je Art der
Markierung, Stufe gegen Passung (Kreuztabelle), Signale und Ereignisarten gegen Passung,
Richtungsurteile je Gruppe, Rangfolge (steht der passendste Ansatz oben?) und Referenztreffer
(E5). Alle Tests sind zweiseitig; es gibt keine Korrektur für Mehrfachtests (Grenze).

## 4. Ablauf

```
cd backend
uv run python scripts/rate_explanations.py bogen --out-dir data/bewertungsbogen/<Datum>
#   -> bogen.json, bogen.md, schluessel.json, bewertungen_vorlage.json (Datenbank + Belegspeicher, kein Abruf)
#   Urteile in data/calibration/erklaerungs_bewertung_<Datum>/bewertungen.json eintragen (blind)
uv run python scripts/rate_explanations.py pruefen --bogen <bogen.json> --ratings <bewertungen.json>
uv run python scripts/rate_explanations.py auswerten --validity data/calibration/explanation_validity_korrektur_2026-10-13.json \
  --bogen <bogen.json> --key <schluessel.json> --ratings <bewertungen.json> --json <auswertung.json> --md <auswertung.md>
```

Der Bogenordner `backend/data/bewertungsbogen/` steht in `.gitignore` (Titel und Links aus dem
Belegspeicher, der selbst nicht eingecheckt ist). Eingecheckt werden können `bewertungen.json`
(Urteile mit Begründungen in eigenen Worten), `auswertung.json` und `auswertung.md` (nur Zahlen,
keine Titel). Ein Bogenordner wird nicht überschrieben; eine Korrektur ist ein neuer Lauf.

## 5. Teil A: Ergebnis auf dem Bericht vom 2026-10-13 (gerechnet am 2026-10-17)

`uv run python scripts/rate_explanations.py auswerten` (Standardpfad, 20 000 Permutationen):

| Merkmal | Markierungen | Vergleichsfenster | Differenz | 95 %-Intervall | p Fisher | p Permutation (Cluster) | nachweisbar wäre |
|---|---|---|---|---|---|---|---|
| mindestens ein Ansatz | 23/28 (82 %) | 57/72 (79 %) | +3 pp | [−16; +18] pp | 1,000 | 0,76 | ≥ 96 % oder ≤ 49 % |
| oberste Stufe mindestens mittel | 15/28 (54 %) | 32/72 (44 %) | +9 pp | [−12; +29] pp | 0,505 | 0,44 | ≥ 73 % oder ≤ 18 % |
| mindestens ein Bündel hoch | 3/28 (11 %) | 5/72 (7 %) | +4 pp | [−7; +21] pp | 0,683 | 0,64 | ≥ 33 % |
| Fenster mit kennzeichnenden Begriffen | 21/28 (75 %) | 54/72 (75 %) | 0 pp | [−20; +17] pp | 1,000 | 1,000 | ≥ 94 % oder ≤ 45 % |
| oberste Stufe (0–3), Mittel | 1,46 | 1,31 | +0,16 | – | – | 0,39 | – |

Gepaart je Cluster (27 Paare): Markierung höher 13, gleich 6, niedriger 8. Niveauwechsel allein:
oberste Stufe mindestens mittel 13/19 (68 %) gegen 23/48 (48 %), +20 pp, Intervall [−6; +42] pp,
p Permutation 0,17. Nullmodell: Spearman ρ zwischen Zahl der Belege und oberster Stufe 0,40
(p < 0,001), mit „mit Ansatz“ 0,55 (p < 0,001); im unteren Drittel der Belegzahl haben 5 von 9
Markierungen und 11 von 23 Vergleichsfenstern einen Ansatz, im oberen Drittel alle.

**Lesart:** Kein Merkmal unterscheidet Markierungs- von Vergleichsfenstern nachweisbar; alle
Intervalle enthalten 0 und sind breit. Die Zahlen bestätigen die Lesart von E23 und ergänzen sie
um die Grenze der Teststärke: Mit 28 Markierungen wären nur sehr große Unterschiede nachweisbar.
Die Stufe folgt deutlich der Zahl der Belege (Nullmodell des Gutachtens). Die genauen Zahlen mit
Permutations-p stehen in der jeweiligen `auswertung.json` eines Laufs; die p-Werte der Permutation
schwanken je Startwert in der zweiten Nachkommastelle.

## 6. Grenzen

- Die Passungsurteile stammen von einem Sprachmodell; es gibt keine zweite bewertende Instanz
  und kein Maß der Übereinstimmung. Eine Stichprobe der Urteile sollte der Autor nachprüfen.
- Die Verblindung ist unvollständig: Unternehmen, Monate und Richtung sind sichtbar und könnten
  eine Vermutung über die Gruppe erlauben; die Größe der Verschiebung ist verdeckt.
- Nur Titel, nur Mitarbeitende und Gesamtbewertung, 28 Markierungen in 11 Unternehmen;
  mehrere Tests ohne Korrektur; die nachweisbare Differenz zeigt, dass kleine und mittlere
  Unterschiede hier grundsätzlich unentdeckt bleiben.
- Teil B gilt nur für die bewerteten obersten drei Ansätze je Fenster, nicht für alle Bündel.
- Ein Unterschied oder dessen Fehlen sagt nichts über Ursachen; ein Erklärungsansatz bleibt ein
  möglicher Zusammenhang.

## 7. Offene Punkte

- Lauf der blinden Bewertung (Agent, Modus `komplett`) und Prüfung einer Stichprobe der Urteile
  durch den Autor.
- Zweite bewertende Instanz (Person) mit derselben Vorlage; Übereinstimmung (zum Beispiel
  gewichtetes Kappa) als eigener Schritt.
- Entscheidung des Autors, ob und wie die Zahlen in E23 (Nachtrag) und in DZ2 eingehen.
