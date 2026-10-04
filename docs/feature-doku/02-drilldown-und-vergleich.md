# 02 – Drill-down und Vorher-Nachher-Vergleich

| | |
|---|---|
| Inkrement | 2 (Zyklus 2) |
| Anforderungen | Drill-down und Vorher-Nachher-Vergleich zu den auffälligen Veränderungen aus [01](01-anomalien-im-verlauf.md); Anforderungstexte liegen nicht im Repository |
| Entscheidungen | E10 (Themenweg), E11 (Stimmung), E12 (Vergleichsfenster), E13 (Statusfilter) in `docs/entscheidungen.md`; E3, E4, E9 unverändert |
| Status | Inkrement 2 umgesetzt (Branch `feature/inkrement-2-drilldown`); Fensterlänge, Stichprobe und Schwellen der kleinen Basis **vorläufig** |
| Stand | 2026-10-04 |

## 1. Vorstellung

Auf der Detailseite **„Anomalien im Verlauf“** (`/anomalies`) lässt sich eine auffällige
Veränderung auswählen: per Klick auf ihre **Stufe** im Diagramm oder auf ihre **Zeile** in
der Liste. Die Auswahl steht in der Adresse (`?anomaly=…`), lässt sich also neu laden und
teilen. Die ausgewählte Stufe wird kräftiger gezeichnet; zwei leicht getönte Flächen zeigen
die beiden Vergleichsfenster.

Darunter erscheinen zwei Abschnitte:

- **„Vorher-Nachher-Vergleich“**: Kopfzeile mit Zeitraum und Zahl der Bewertungen je
  Fenster („davor“ und „ab dem markierten Monat“), mittlere Gesamtnote und Stimmung je
  Fenster, die Verschiebung der Note und der Stimmung, darunter eine Tabelle der größten
  **Verschiebungen je Thema**: Anteil davor, Anteil danach, Differenz in Prozentpunkten,
  Stimmung davor und danach. Standard sind die sechs größten, „Alle Themen zeigen“ klappt
  den Rest auf. Themen oder Fenster mit **kleiner Basis** tragen das Kennzeichen „kleine
  Basis“ und sind grau. Ein Hinweistext sagt: Der Vergleich zeigt, was sich in den
  Bewertungen verändert hat, er ist keine Aussage über Ursachen; dazu der verwendete
  Stimmungsmodus und die Stichprobe.
- **„Bewertungen des Zeitraums“**: die Einzelbewertungen eines Fensters, umschaltbar
  zwischen „davor“ und „ab dem markierten Monat“. Der Untertitel nennt Gruppe, Zeitraum und
  Anzahl. Je Bewertung stehen Datum, Sterne, Titel, Status und ein Textauszug; ein Klick
  öffnet die Bewertung im vorhandenen Detailfenster (`ReviewDetailModal`), dort lässt sich
  mit den Pfeilen blättern. Es werden 25 Bewertungen geladen, weitere auf Knopfdruck.

Neu sind außerdem die **Bewertendengruppe** und ihre Auswahl auf Karte und Detailseite:
ein Umschalter **Mitarbeiter / Bewerber** (Quelle) und eine Auswahl **Status** (z. B.
„Angestellt“, „Ex-Angestellt“, „Eingestellt“, „Abgelehnt“, „Alle“). Die Erkennung läuft für
die gewählte Gruppe neu; Vergleich und Bewertungsliste beziehen sich auf dieselbe Gruppe.
Auf der Detailseite stehen Quelle und Status in der Adresse (`?source=candidates&status=eingestellt`),
die Karte übergibt ihre Auswahl beim Öffnen der Detailseite.

Kleinere Ergänzungen aus Inkrement 1: Die Dashboard-Karte erklärt die Ringe in einer
kurzen Legende (Abfall, Anstieg); auf der Detailseite steht beim Laden und im Fehlerfall
kein Zähler im Untertitel.

Nutzen: Von der auffälligen Veränderung kommt man in zwei Klicks zu den Bewertungen, auf
denen sie beruht, und sieht, welche Themen in den Texten häufiger oder seltener genannt
werden.

## 2. Erklärung

### 2.1 Vergleichsfenster (E12)

Für eine Veränderung mit Monat `date` (erster bewerteter Monat auf dem neuen Niveau):

- **davor**: die 6 Kalendermonate vor `date`, aber nicht früher als `before_from`, der
  Beginn des Abschnitts vor dem Wechsel,
- **danach**: `date` und die folgenden 5 Monate, aber nicht später als `after_to`, das Ende
  des Abschnitts nach dem Wechsel.

Beispiel Freenet, Abfall ab 2021-09 (Abschnitt danach endet 2022-01): davor 2021-03 bis
2021-08, danach 2021-09 bis 2022-01 (5 Monate). In die Fenster gehen **alle** Bewertungen
dieser Monate ein, auch aus Monaten mit weniger als 5 Bewertungen; die Mindestdichte E4
gilt nur für die Erkennungsreihe.

### 2.2 Bewertungen eines Zeitraums

`GET /api/analytics/company/{id}/reviews` kennt neu `start` und `end` (Tage, einschließlich),
`status`, `offset` und `format=full`. Alle Bewertungen des Zeitraums werden seitenweise
gelesen (PostgREST liefert höchstens 1000 Zeilen je Abfrage), nach Status gefiltert, nach
Datum absteigend sortiert und davon `limit` ab `offset` geliefert; `total` ist die Zahl
aller Treffer. Mit `format=full` hat jede Bewertung `id`, `preview` (Textauszug, höchstens
240 Zeichen) und `fullReview`, also genau das Format, das die Themenübersicht für das
Detailfenster liefert (`build_full_review` in `backend/services/review_service.py`). Ohne
die neuen Parameter ist die Antwort unverändert.

### 2.3 Themen und Anteile (E10)

Die Themen sind die **Schlüsselwort-Themen** der Themenübersicht (Mitarbeitende 13,
Bewerbende 10, benannt wie die Kununu-Kategorien). Ein Thema gilt in einer Bewertung als
genannt, wenn eines seiner Schlüsselwörter in einem Textfeld vorkommt
(`topics_in_review` in `backend/services/keyword_topic_service.py`). Der **Anteil** eines
Themas in einem Fenster ist die Zahl der Bewertungen, die es nennen, geteilt durch alle
Bewertungen des Fensters. Die **Verschiebung** ist Anteil danach minus Anteil davor in
**Prozentpunkten** (Pp.), also die Differenz zweier Prozentwerte (z. B. 18 % → 31 % =
+12 Pp.). Die Tabelle ist nach dem Betrag der Verschiebung sortiert, größte zuerst.

### 2.4 Stimmung (E11)

Je Bewertung schätzt der vorhandene `SentimentAnalyzer` die Stimmung der Freitexte:
**positiv, neutral oder negativ** und eine **Polarität** zwischen −1 (negativ) und +1
(positiv). Hauptmodus ist ein Transformer-Modell (German Sentiment BERT), die
Sternebewertung dient als Hinweis; lädt das Modell nicht, gilt das Lexikon (Wortlisten). Je
Fenster gehen höchstens 300 Bewertungen mit Freitext ein, bei mehr die jüngsten 300. Die
Stimmung „je Thema“ ist die Stimmung der Bewertungen, die das Thema nennen. Angezeigt
werden die Anteile als dreifarbiger Balken (grün positiv, grau neutral, rot negativ) und die
mittlere Polarität als Zahl.

### 2.5 Kleine Basis

`low_basis` kennzeichnet Werte, die auf wenigen Bewertungen beruhen: ein Fenster mit
weniger als **10 Bewertungen** (dann gilt das für den ganzen Vergleich) oder ein Thema mit
weniger als **5 Nennungen** in beiden Fenstern zusammen. Beide Schwellen sind Setzungen
(E12, vorläufig).

### 2.6 Bewertendengruppe (E13)

Die Statuswerte der Datenbank sind uneinheitlich (`1.0`, `0.0`, `True`, `hired`,
`offerDeclined`, …). `normalize_status` führt sie auf feste Schlüssel zurück: Mitarbeitende
`angestellt`, `ex-angestellt`, `unbekannt`; Bewerbende `eingestellt`, `angebot-abgelehnt`,
`abgelehnt`, `zurueckgestellt`, `unbekannt`. Mit einem Status laufen Monatsreihe, Eignung,
Strafterm und Erkennung nur auf dieser Gruppe; jede Kombination aus Quelle, Dimension und
Status ist eine eigene Reihe mit eigenem Strafterm.

### 2.7 Endpunkt des Vergleichs

`GET /api/analytics/company/{id}/anomalies/{anomaly_id}/explanations?source=&dimension=&status=&window_months=`
berechnet die Veränderungen mit den Standardparametern neu, sucht `anomaly_id` und liefert
`anomaly`, `windows` (mit Anzahl je Fenster), `comparison` und `explanations` (leer, folgt in
Inkrement 5). Eine unbekannte `anomaly_id` ergibt 404. Die Datenbank wird nur gelesen.

### 2.8 Beispiel aus den echten Daten (2026-10-04)

Freenet, Mitarbeitende, Gesamtbewertung, Abfall ab 2021-09 (−1,06 Sterne, Ø der
Monatsmittel 4,20 → 3,14):

| | davor (2021-03 – 2021-08) | danach (2021-09 – 2022-01) |
|---|---|---|
| Bewertungen | 45 | 45 |
| Ø Gesamtnote je Bewertung | 4,08 | 3,17 |
| Stimmung (24 bzw. 15 mit Freitext) | 17 % positiv, 25 % negativ, Ø −0,07 | 27 % positiv, 40 % negativ, Ø −0,12 |

Größte Verschiebungen je Thema: Kollegenzusammenhalt 18 % → 7 % (−11,1 Pp.),
Work-Life Balance 9 % → 2 % (−6,7 Pp.), Kommunikation 11 % → 4 % (−6,7 Pp.). Die Anteile
beruhen auf 3 bis 8 Nennungen je Fenster; die Stimmung je Thema auf noch weniger Texten.

## 3. Begründung

- **Drill-down zur Bewertung:** Eine erkannte Veränderung ist ein Hinweis, keine Erklärung.
  Die Bewertungen selbst sind die nächste prüfbare Ebene; das Dashboard soll sie ohne
  Umweg zeigen. Die Liste nutzt das vorhandene Detailfenster, damit Einzelbewertungen
  überall gleich aussehen.
- **Vergleich statt Ursache:** Der Vergleich beschreibt nur, was sich in den Bewertungen
  verändert hat (Anteile, Stimmung). Er sagt nicht, warum. Die Wortwahl („Verschiebung“,
  „auffällige Veränderung“) und der Hinweistext halten das fest; Erklärungen mit Kontext
  folgen erst in Inkrement 5.
- **Schlüsselwort-Themen statt LDA (E10):** dieselben, benannten Themen wie im Dashboard,
  nachvollziehbar je Bewertung und schnell genug für eine Live-Berechnung.
- **Transformer mit Rückfall (E11):** Hauptmodus des Projekts; die Stichprobe von 300 hält
  die erste Antwort unter rund 11 s, danach hilft der Zwischenspeicher.
- **Feste Fenster mit Begrenzung (E12):** gleich lange Fenster sind vergleichbar; die
  Begrenzung durch die Nachbarabschnitte verhindert, dass ein Fenster über einen weiteren
  Wechsel reicht.
- **Statusfilter (E13):** aktuelle und ehemalige Mitarbeitende bzw. erfolgreiche und
  abgelehnte Bewerbende bewerten aus unterschiedlichen Lagen; eine Veränderung kann in einer
  Gruppe deutlicher sein als in der Mischung.
- **Nachladen statt alles auf einmal:** Fenster können mehrere hundert Bewertungen haben
  (Telekom 2018-04 bis 2018-09: 729). 25 je Seite halten Liste und Antwort klein.

## 4. Grenzen

- **Keine Ursachen.** Eine Verschiebung zeigt, dass ein Thema häufiger oder seltener
  genannt wird, nicht, dass es die Veränderung ausgelöst hat.
- **Gewichtung:** Die Erkennung vergleicht Monatsmittel (jeder Monat zählt gleich), der
  Vergleich Bewertungen (jede Bewertung zählt gleich). Bei sehr ungleich verteilten
  Bewertungen können beide in verschiedene Richtungen zeigen: SAP SE, Anstieg ab 2024-07
  (Ø der Monatsmittel 3,07 → 3,74), aber Ø je Bewertung 3,79 → 3,65, weil im März 2024
  174 der 246 Bewertungen des Fensters davor liegen (Ø 4,16).
- **Freitext fehlt oft:** Bei älteren Bewertungen gibt es wenig Text (Telekom 2010: 6 von 27
  Bewertungen davor). Die Stimmung beruht dann auf wenigen Texten.
- **Schlüsselwörter:** nur deutsch, mehrdeutige Wörter zählen mit, keine Validierung
  (E10).
- **Stimmung:** Modellschätzung je ganzer Bewertung; der Lexikon-Modus erkennt Wörter mit
  Satzzeichen nicht (E11).
- **Bewerberquelle:** Die meisten Statusgruppen sind für die automatische Erkennung zu dünn
  (E13); die Seite zeigt dann den Eignungshinweis.
- **Themenübersicht:** `topic-overview` liest je Quelle höchstens 1000 Bewertungen (siehe
  Offene Punkte); der Vergleich ist davon nicht betroffen, er liest paginiert.

## 5. Prüfung und Belege

| Was | Beleg |
|---|---|
| Bewertungen eines Zeitraums | `backend/tests/drilldown/test_reviews_route.py`: Grenzen einschließlich, ein Tag, Sortierung, beide Quellen, `status`, `offset`, `format=full`, mehrere Seiten, 400/422; Antwort ohne neue Parameter gleicht Commit 4ad0a80 (Hash für Demo 1–3) |
| Themen | `backend/tests/drilldown/test_keyword_topic_service.py`: `topic-overview` für Demo 1–3 identisch zu Commit 4ad0a80, `end_date`, `topics_in_review` = `frequency`, kein Dienst importiert eine Route |
| Vergleich | `backend/tests/drilldown/test_explanation_service.py`: Fenster, Anteile, Verschiebung, Sortierung, `low_basis`, `sentiment_sample`, Zwischenspeicher, Modus (konstruierte Zeilen, Lexikon bzw. Stub) |
| Endpunkt | `backend/tests/drilldown/test_explanations_route.py`: Form, 404, 400, `window_months`, `status` |
| Erkennung je Status | `backend/tests/anomaly/test_status_filter.py`: Zuordnung der Rohwerte, Reihen je Gruppe, Demo 3 je Status gültige Antwort |
| Ohne Netzwerk | alle neuen Tests gegen den In-Memory-Store; zusätzlich mit unerreichbarer `SUPABASE_URL` grün |
| Browser | Demo 3 (gehostet, id 18): Auswahl per Stufe und Zeile, Umschalter, Nachladen (25 → 50), Detailfenster mit Blättern, Vergleich im Transformer-Modus; Carl Zeiss Bewerber mit Status „Eingestellt“; Karte → Detailseite mit Quelle; helles und dunkles Theme |
| Antwortzeit (2026-10-04, Entwicklungsrechner) | Lexikon 0,4–0,7 s je Anfrage; Transformer: Laden 3,6–4,0 s einmal je Prozess, erste Anfrage 1,6 s (Freenet, 39 Texte) bis 8,4 s (SAP, 285 Texte), Telekom 457 Texte 10,8 s nur Vergleich; mit Zwischenspeicher 0,2–0,5 s |
| PDF-Export | Codepfad (`frontend/src/utils/pdfExport.js`) unverändert |
| Commits | `bbb5d64` (Bewertungen), `7a89a93` (Durchstich Frontend), `48c3105` (Themen als Dienst), `81dc44c` (Vergleich), `d78d258` (Quelle und Status), `75c2053` (Reste Inkrement 1), `0818c42` (Tests) |

## 6. Offene Punkte

- **topic-overview schneidet ab:** Die Route liest je Quelle mit einer einzigen Abfrage
  ohne Paginierung; PostgREST liefert höchstens 1000 Zeilen. Gemessen 2026-10-04: Telekom
  (6 899 Mitarbeiterbewertungen), Bechtle (2 369), Carl Zeiss (1 700) liefern
  `total_reviews` 1000; betroffen sind auch 1&1 (1 291), Cancom (1 474) und Freenet
  (1 027). Nicht geändert (Auftrag); Entscheidung des Autors.
- Gewichtung Monatsmittel gegen Bewertungen (siehe Grenzen): zusätzlich das Mittel der
  Monatsmittel je Fenster zeigen?
- Fensterlänge 6 Monate, Stichprobe 300 und Schwellen der kleinen Basis (10 / 5) sind
  vorläufig.
- Zuordnung der Statuswerte (`True`/`False`, `deferred`, „Bewerber“) vom Autor zu bestätigen.
- Der Vergleich für Einzeldimensionen nutzt dieselben Themen wie die Gesamtbewertung; ob
  je Dimension nur das zugehörige Thema gezeigt werden soll, ist offen.
- Der Fix für den gemeinsamen Supabase-Client (`fix/supabase-client-thread-safety`) ist
  nicht in `main`; mit mehreren gleichzeitigen Anfragen der Detailseite treten die
  bekannten 500-Fehler ohne CORS-Kopf häufiger auf (beobachtet bei `/companies`).
