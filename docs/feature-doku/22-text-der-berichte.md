# 22 – Text der Berichte im Wortbezug

| | |
|---|---|
| Inkrement | Erweiterung der Erklärungsansätze (2026-10-23) |
| Anforderungen | keine eigene Anforderung; Frage des Autors (2026-10-23): „Ist es nicht sinnvoll, auch den Text zu vergleichen und nicht nur den Titel?“; baut auf TF4 (Erklärungsansätze) und der dokumentierten Grenze aus [08](08-erklaerungsansaetze.md) § 4 |
| Entscheidungen | E35 (Textspeicher, Kandidaten, Verwendung nur im Wortbezug) und Nachtrag zu E7 in `docs/entscheidungen.md`; baut auf E18, E21–E23, E33, E34 |
| Status | umgesetzt (2026-10-23), nicht committet; Abruf der Texte am 2026-10-23 gestartet; Werte sind Setzungen; die Zulässigkeit des Abrufs hat der Autor am 2026-10-23 entschieden |
| Stand | 2026-10-23 |

## 1. Vorstellung

Bis zum 2026-10-23 verglich das Dashboard bei den **Erklärungsansätzen** („Mögliche
Zusammenhänge“ auf `/anomalies`, [08](08-erklaerungsansaetze.md)) nur den **Titel** einer
Meldung mit den Bewertungen. Seit dem 2026-10-23 wird, wo er vorliegt, auch der **Text der
Meldung** durchsucht: bei EQS-Mitteilungen der vollständige Mitteilungstext, bei
Presseartikeln der Haupttext der Verlagsseite. Was Nutzerinnen und Nutzer sehen:

- Im Dialog der möglichen Zusammenhänge trägt ein Begriff, der nur im Text steht, das
  Kennzeichen **„Begriff ‚stellenabbau‘ 12 ggü. 1 · im Text“**; die Begründung sagt
  „‚stellenabbau‘ steht im Text der Meldung und wird in den Bewertungen danach häufiger
  genannt (12 gegenüber 1 Bewertungen)“.
- Belege, zu denen ein Text vorliegt, tragen das Kennzeichen **„Text geprüft“** (im Dialog je
  Eintrag, bei gebündelten Meldungen und weiteren Einträgen der Gruppe, in der Belegliste
  „Externe Berichte im Ereignisfenster“). Ohne dieses Kennzeichen wurde die Meldung wie bisher
  nur über den Titel bewertet.
- In der Belegliste steht bei Begriffen aus dem Text „Begriff: ‚stellenabbau‘ (im Text)“; bei
  gewählter Dimension ([20](20-dimension-als-globaler-filter.md)) heißt es „Schlüsselwort im
  Text ‚tarifvertrag‘“, wenn das Schlüsselwort des Themas nur im Text steht.
- Der aufklappbare Absatz **„Wie wird eingestuft?“** erklärt: „Liegt zu einer Meldung der Text
  vor …, sucht der Wortbezug die Begriffe der Bewertungen auch im Text; … Ereignisart,
  Arbeitgeberbezug und die Nennung des Unternehmens kommen weiter aus dem Titel.“

Nutzen: Eine Meldung, deren Titel das Ereignis nur andeutet („Konzern legt Zahlen vor“), kann
jetzt als Erklärungsansatz erscheinen, wenn ihr Text nennt, was die Bewertenden danach
schreiben. Zugleich bleibt sichtbar, ob ein Bezug im Titel oder nur im Text steht. Kein
Eintrag behauptet eine Ursache.

## 2. Erklärung

1. **Textspeicher** (`backend/services/evidence_text.py`). Je Beleg eine Datei
   `backend/data/context_text/<unternehmen>/<beleg-id>.json` (nicht im Repository, wie der
   Belegspeicher) mit Zieladresse, Stand, Status, Zeichenzahl und dem Text als Absätze
   (höchstens 40.000 Zeichen). Status: `ok` ab 300 Zeichen, `kurz` darunter (Teaser,
   Bezahlschranke; wird trotzdem verwendet), `fehlgeschlagen` (Fehlertext; erneuter Versuch
   nur mit `--retry-failed`). Die Monatsdateien des Belegspeichers bleiben ohne Text, und die
   Antworten der Belegliste tragen keine Texte: `attach_texts` hängt die Texte nur für die
   Rangfolge an Kopien der Belege.
2. **Abruf** (`scripts/fetch_evidence_text.py`, nie zur Laufzeit des Dashboards).
   - **EQS-Mitteilungen** (`--eqs`): alle gespeicherten Mitteilungen aller Unternehmen; der
     Text steht auf der öffentlichen Meldungsseite (`item["url"]`) im Element `main`.
   - **Presseartikel** (`--news`, mit `--comparison` auch die Vergleichsfenster): Google News
     nennt nur einen verschlüsselten Weiterleitungslink. `resolve_google_url` löst ihn in zwei
     Schritten auf: die Artikelseite bei Google News liefert Signatur und Zeitstempel
     (`data-n-a-sg`, `data-n-a-ts`), eine Anfrage an `batchexecute` die Zieladresse (Verfahren
     wie in offen verfügbaren Decodern). Danach wird die Verlagsseite geladen.
   - **Kandidaten** statt aller Meldungen: Nur Meldungen der Markierungs- und Vergleichsfenster,
     die die titel- und datumsabhängigen Regeln 1 und 4 der strengen Auswahl erfüllen
     (Unternehmen im Titel genannt oder nicht prüfbar, zeitliche Nähe mindestens 0,5), bekommen
     einen Text. Bei allen anderen kann der Text die Auswahl nicht ändern.
   - `extract_main_text` nimmt die Absätze (`p`, `li`, Überschriften, Zitate ab 30 Zeichen) aus
     dem längsten `article`, sonst `main`, sonst `body`; Skripte, Navigation, Kopf, Fuß,
     Seitenleisten und Formulare entfallen; gleiche Absätze zählen einmal.
   - Drosselung: Google News und EQS 2 s je Anfrage (dieselbe Sperre wie die Monatsabfragen),
     Verlage 1 s je Host. Nach drei Fehlern in Folge vor der Verlagsseite (etwa Status 429 bei
     Google News) bricht der Weg ab und nennt das Unternehmen zum Fortsetzen; eine
     Verlagsseite, die nicht antwortet, zählt nicht. Gespeicherte Texte werden übersprungen,
     `--dry-run` zählt nur, `--max-fetches` begrenzt, `CONTEXT_LIVE_FETCH=0` unterbindet jeden
     Abruf. Dauer: etwa 2 s je EQS-Mitteilung, etwa 5 s je Artikel.
3. **Verwendung in der Rangfolge** (`explanation_ranking.score_item`, `TEXT_VERSION` 1).
   Liegt ein Text vor, läuft `review_terms.match_terms` zusätzlich über den Text, mit derselben
   Richtungsregel wie im Titel (strenge Auswahl: das Wort ist der Begriff oder beginnt mit ihm).
   Je Begriff steht `in` (`title` oder `text`); Titeltreffer zuerst, ein Begriff zählt einmal.
   `term_match` rechnet wie bisher (0,5 je Begriff, 1 bei einem starken Begriff, höchstens 1).
   Zwei Schutzregeln gegen allgemeine Wörter (Abschnitt 3): (a) die Stoppwortliste der Begriffe
   ist um Funktionswörter, Adverbien und Modalverben ergänzt (`review_terms.STOPWORDS`, gilt auch
   für Titel; Korrektur in `CORRECTIONS`); (b) ein Begriff, der in mindestens 3 und in mehr als
   20 % der Texte des Fensters steht, zählt im Text nicht (`frequent_text_terms`,
   `TEXT_TERM_MAX_SHARE` 0,2, `TEXT_TERM_MIN_HITS` 3); Titeltreffer bleiben, die Antwort nennt
   diese Begriffe mit Anteil (`explanation_summary.texts.excluded_terms`), „Wie wird eingestuft?“
   zeigt sie. **Ereignisart, Arbeitgeberbezug und „Unternehmen im Titel genannt“ kommen weiter
   allein aus dem Titel.** Je Beleg, Bündel und Eintrag steht `has_text`; `item_scores` nennt
   `terms_in_text`. Schwellen, Stufenregeln (Fassung 2) und die vier Auswahlregeln bleiben;
   Regel 3 lautet jetzt „im Titel oder, wenn er vorliegt, im Text der Meldung“.
4. **Dimensionsfilter** (`dimension_scope.evidence_dimension_match`, E34). Die Schlüsselwörter
   des Themas werden auch im Text gesucht und als `terms_in_text` getrennt ausgewiesen; die
   Ereignisart kommt aus dem Titel.
5. **Schnittstelle.** `explanation_summary.texts` zählt je Fenster die Belege mit Text
   (`with_text`, `ok`, `kurz`, `fehlgeschlagen`); `rules.text` nennt Fassung, Verwendung und den
   Hinweis. Die Belegliste (`/context`) ist bis auf `dimension_match.terms_in_text` und
   `has_text` unverändert.
6. **Auswertung.** `scripts/report_explanation_validity.py` hängt die Texte je Fenster an und
   weist `n_with_text` und `n_selected_by_text` aus (Belege, die nur durch einen Begriff im
   Text ausgewählt sind, also ohne Titeltreffer und ohne Themenverschiebung). Sie läuft mit den
   Texten genau einmal (Abschnitt 5).

## 3. Begründung

- **Text nur im Wortbezug, nicht in der Ereignisart.** Die kennzeichnenden Begriffe sind je
  Fenster aus den Bewertungen gewonnen (mindestens 3 Bewertungen, 3 %, Verdopplung); sie sind
  selten, und ihr Treffer im Text ist ein Bezug zu dem, was die Bewertenden schreiben. Die
  Schlüsselwörter der Ereignisarten (Verlust, Klage, Übernahme, Aktie, Kurs) stehen dagegen in
  fast jedem Finanzbericht und jeder EQS-Mitteilung; aus dem Text ermittelt würden sie nahezu
  jeden Beleg einer Ereignisart oder der Gruppe ohne Arbeitgeberbezug zuordnen. Die Prüfung
  vom 2026-10-18 (E33) hat gezeigt, dass schon die Titel zu viele schwache Treffer liefern.
- **Schutz vor allgemeinen Wörtern.** Die erste Prüfung mit echten Texten (E.ON, Anstieg ab
  November 2023, 107 Texte) ergab, dass die kennzeichnenden Begriffe der Bewertungen Wörter wie
  „andere“ (in 36 Texten), „deutlich“ (20) und „bisher“ (14) enthielten, während fachliche
  Begriffe („überstunden“, „weiterbildung“, „vorgesetzte“) in keinem Text standen. In Titeln
  waren diese Wörter harmlos, weil sie dort nie vorkommen. Ohne Schutz wären 47 statt 30 Belege
  ausgewählt worden, fast alle über solche Wörter. Die Stoppwortliste fängt die bekannten
  Wörter, die Häufigkeitsgrenze je Fenster das, was die Liste nicht kennt: Ein Begriff, der in
  jedem dritten Text steht, unterscheidet die Belege des Fensters nicht. Beide Werte sind
  Setzungen; die Grenze kann einen fachlichen Begriff treffen, der in einem ereignisreichen
  Fenster in vielen Texten steht, dann bleibt sein Titeltreffer.
- **Kandidaten statt aller Meldungen.** Regel 1 (Unternehmen im Titel) und Regel 4
  (zeitliche Nähe) hängen nicht vom Text ab. Ein Text kann daher nur bei Belegen etwas ändern,
  die beide erfüllen; so sind rund 3.600 statt 18.000 Artikel abzurufen (Stand 2026-10-23:
  1.134 in den Markierungsfenstern, 3.599 mit den Vergleichsfenstern), und die Auswertung bleibt
  vollständig.
- **Fundort je Begriff.** Ein Treffer im Titel ist in der Liste sichtbar, ein Treffer im Text
  nicht; das Kennzeichen „im Text“ und „Text geprüft“ halten die Begründung prüfbar und machen
  sichtbar, welche Belege überhaupt einen Text hatten.
- **Eigener Textspeicher statt Volltexte im Belegspeicher.** Der Belegspeicher bleibt wie
  nach E7 (Titel, Herausgeber, Link, Datum) und seine Verträge
  (`tests/evidence/test_evidence_contracts.py`) gelten weiter; die Texte sind getrennt und
  löschbar, ohne die Belege zu verlieren.
- **Kein Abruf zur Laufzeit.** Ein Fenster großer Unternehmen hat hunderte Belege; drei
  Anfragen je Artikel würden Minuten dauern. Der Speicher wird vorab gefüllt, das Dashboard
  liest nur.

## 4. Grenzen

- **Google News liefert keine Texte.** Die Auflösung der Weiterleitung nutzt ein
  undokumentiertes Verfahren; ändert Google es, bleiben die gespeicherten Texte, neue kommen
  nicht hinzu (der Lauf bricht nach drei Fehlern ab).
- **Bezahlschranken, Cookie-Wände, Blockaden.** Viele Verlage liefern nur einen Teaser (Status
  `kurz`) oder nichts (`fehlgeschlagen`); die Kennung nennt Forschung und nicht-kommerzielle
  Nutzung, einige Seiten antworten darauf nicht. Die Extraktion ist eine einfache Absatzregel;
  Menüs oder Teaser anderer Artikel können Reste hinterlassen, die im Wortbezug mitzählen.
- **Nur Kandidaten.** Freie Auswahlen und Einzeldimensionen außerhalb der Markierungs- und
  Vergleichsfenster, Meldungen ohne Unternehmen im Titel und am Rand des Fensters haben keinen
  Text; „Text geprüft“ zeigt den Unterschied. Für Unternehmen ohne Markierung gibt es nur die
  Texte der EQS-Mitteilungen.
- **Mehr Treffer sind nicht mehr Erklärungskraft.** Ob der Text Markierungsfenster von
  Vergleichsfenstern besser unterscheidet, zeigt allein die Auswertung (Abschnitt 5); E23 fand
  bisher keine Kennzahl, die das tut.
- **Sprache.** Die Begriffe sind deutsch; englische EQS-Mitteilungen treffen sie selten. Texte
  werden nicht übersetzt.
- **Nutzungsbedingungen.** Die Entscheidung, dass der Abruf im Rahmen der wissenschaftlichen
  Arbeit zulässig ist, hat der Autor am 2026-10-23 getroffen (E7, Nachtrag); die Fundstellen
  in `docs/nutzungsbedingungen.md` beziehen sich auf den Stand davor.

## 5. Prüfung und Belege

| Was | Beleg |
|---|---|
| Textspeicher, Auflösung, Extraktion, Abruf | `backend/tests/evidence/test_evidence_text.py` (27 Tests): Kennung aus beiden Linkformen, Signatur und Zeitstempel, Formulardaten, Antwort mit JSON-Zeilen und maskierter Form, zwei gedrosselte Anfragen, Fehler ohne Signatur oder Zieladresse; Absätze ohne Navigation, längstes `article`, `main`, `body`, Obergrenze; Speicher, unlesbare Datei, `.gitignore`; Abruf je Typ, Fehler als Status, Fortsetzen und `retry_failed`; Anhängen ohne Änderung der Eingabe |
| Wortbezug im Text | `backend/tests/explanations/test_text_match.py` (15 Tests): Treffer im Text mit Fundort, Titel zuerst ohne Doppelung, ohne Text wie bisher, Richtung des Wortanfangs im Text (E21 gegen E33), Ereignisart und Arbeitgeberbezug bleiben beim Titel, leerer Text, strenge Auswahl durch Texttreffer, Bündel und Textbausteine, Regeln mit Fassung; Häufigkeitsgrenze (Zählung, Mindestzahl, 20 % genau nicht über der Grenze, Rangfolge lässt den Begriff im Text aus und im Titel zu), ergänzte Stoppwörter (keine Begriffe mehr, fachliche Wörter bleiben) |
| Skript | `backend/tests/evidence/test_fetch_evidence_text_script.py` (8 Tests): Kandidatenregel, `--dry-run`, Abruf und Fortsetzen, Abrufgrenze und `CONTEXT_LIVE_FETCH=0`, `--retry-failed`, Abbruch nach Fehlern bei Google News (nicht bei Verlagen), `--json` |
| Dimensionsfilter | `backend/tests/drilldown/test_dimension_scope.py`, `tests/evidence/test_context_dimension.py` (angepasst: `terms_in_text`, `has_text`); `frontend/src/lib/__tests__/dimensionScope.test.js` |
| Gesamtlauf | `uv run python -m pytest tests -q`: siehe Abschluss unten; eslint und ruff (Pyflakes-Regeln) ohne Befund |
| Live-Stichprobe (2026-10-23) | eine EQS-Mitteilung von SAP (3.073 Zeichen in 0,6 s), zwei Presseartikel der Uni Duisburg-Essen (2.372 und 2.460 Zeichen, 2,4 und 4,5 s) aus dem Speicher; E.ON Markierungsfenster: 105 Kandidaten, 93 ok, 5 kurz, 7 fehlgeschlagen |
| Zählung der Texttreffer (2026-10-23) | Skript im Sitzungsordner (nicht im Repository) über alle Markierungsfenster mit Texten (E.ON 2023-11: 107, RWE 2023-02: 127): „andere“ 36/107, „deutlich“ 20/107, „bisher“ 14/107, „verantwortung“ 11/107, „aktuellen“ 10/127, „stark“ 8/107; „image“, „überstunden“, „vorgesetzte“, „weiterbildung“, „bezahlung“ 0 |
| Wirkung bei E.ON 2023-11 (laufender Backend, 373 Belege, 107 mit Text) | vor den Schutzregeln 47 ausgewählte Belege, 62 mit Begriff im Text; danach 30 ausgewählte, 29 mit Begriff im Text, 14 nur durch den Text ausgewählt; keine Begriffe über der Häufigkeitsgrenze |

### Abruf und Auswertung (Stand 2026-10-23)

Der Abruf wurde am 2026-10-23 gestartet (`scripts/fetch_evidence_text.py --eqs` und
`--news`, danach `--news --comparison`; Zusammenfassungen in
`backend/data/calibration/evidence_text_*_2026-10-23.json`). Die Auswertung nach E23 mit den
Texten folgt, sobald die Texte der Markierungs- und Vergleichsfenster vorliegen; ihre Zahlen
werden hier nachgetragen.

## 6. Offene Punkte

- Auswertung mit Texten (E23) nach Abschluss des Abrufs; Vergleich mit dem Lauf vom
  2026-10-18 (`explanation_validity_strict_2026-10-18`).
- Ob eine Ereignisart aus dem **ersten Absatz** (Vorspann) sinnvoll wäre, ohne die Beiläufigkeit
  langer Texte, bleibt zu prüfen; derzeit nicht umgesetzt (E35).
- Bezahlschranken: Anteil `kurz` und `fehlgeschlagen` je Herausgeber aus den Zusammenfassungen
  ablesen; ob einzelne Verlage ausgenommen werden sollen, entscheidet der Autor.
- Texte für freie Auswahlen und Einzeldimensionen außerhalb der Fenster nur auf Wunsch
  (`--company`, eigener Lauf); kein Abruf zur Laufzeit.
