# 11 – Prognose im Zeitverlauf erklären

| | |
|---|---|
| Inkrement | Nachtrag nach Inkrement 6 |
| Anforderungen | keine eigene Anforderung; Nähe zu FA-38 (Berechnung erklären) |
| Entscheidungen | E28 (Prognose als Schalter beim Bauen) in `docs/entscheidungen.md`; keine neue Entscheidung |
| Status | umgesetzt (2026-10-13), nicht committet; Begründung durch den Autor offen |
| Stand | 2026-10-13 |

## 1. Vorstellung

Im Detailfenster des Zeitverlaufs (Karte anklicken, Metrik „Ø Score“) steht neben dem
Legendeneintrag **„Prognose“** ein **„?“**. Es öffnet eine Erklärung, wie die Prognose entsteht,
mit den Werten der gewählten Firma und Quelle. Zusätzlich zeigt das Fenster zwei
Durchschnittswerte, an denen man ablesen kann, warum die Prognose dort liegt, wo sie liegt:

- **Geglättetes Niveau** (violette Linie und Kachel): der gewichtete Durchschnitt, von dem die
  Prognose ausgeht.
- **Ø Historisch** (gestrichelte waagerechte Linie): das ungewichtete Mittel aller Monate.

Die Legendeneinträge „Historisch (Monatswerte)“ und „Geglättetes Niveau“ schalten zwischen zwei
Ansichten um; jeder Klick auf einen der beiden wechselt die Ansicht (an ↔ aus). Es ist immer
genau eine sichtbar, der andere Eintrag ist blass und durchgestrichen.
Beim Öffnen des Fensters zeigt es die Monatswerte. In der geglätteten Ansicht setzt die
Prognoselinie am geglätteten Niveau des letzten Monats an, so wie das Verfahren rechnet.

Die Kachel **„Trend der Prognose“** zeigt die Steigung je Monat, mit der die Prognose
fortgeschrieben wird. Die kleine Karte im Dashboard bleibt unverändert.

## 2. Erklärung

**Daten.** `GET /api/analytics/company/{id}/timeline` bildet je Monat das Mittel der Gesamtnote
(`durchschnittsbewertung`) der gewählten Quelle, höchstens über die letzten 10 Jahre
(`days=3650`). Monate ohne Bewertungen fehlen in der Reihe und werden von der Prognose
übersprungen.

**Verfahren.** Holts exponentielle Glättung mit Trend (Charles C. Holt, 1957; Nachdruck im
*International Journal of Forecasting* 2004), berechnet mit `statsmodels.tsa.holtwinters.Holt`.
Das Verfahren führt zwei Größen Monat für Monat fort:

- **Niveau** ℓ: ℓₜ = α · yₜ + (1 − α) · (ℓₜ₋₁ + bₜ₋₁), ein gewichteter Durchschnitt, in dem
  jüngere Monate stärker zählen;
- **Steigung** b: bₜ = β · (ℓₜ − ℓₜ₋₁) + (1 − β) · bₜ₋₁.

α und β schätzt `statsmodels` aus den Daten (Minimierung der quadrierten
Ein-Schritt-Fehler). Die Prognose für Monat h nach dem letzten Monat ist ℓ + h · b, begrenzt
auf 0 bis 5. Scheitert die Schätzung, ist die Prognose der Mittelwert aller Monate.

**Kenngrößen.** `forecast_with_details` in `backend/routes/analytics.py` liefert neben der
Prognose `forecast_info`: `method` (`holt` oder `mean`), `n_months`, `first_month`,
`last_month`, `historical_mean`, `alpha`, `beta`, `level` und `trend` am Ende der Reihe,
`smoothed` (Niveau je Monat) und `clamped`. `calculate_forecast` gibt unverändert nur die
Prognose zurück.

**Anzeige.** `frontend/src/components/dashboard/ForecastExplanation.jsx` (Text des „?“),
`frontend/src/lib/forecastText.js` (Formatierung), `TimelineCard.jsx` (Linien, Legende,
Kacheln; nur im Detailfenster). Beispiel 1&1 AG, Mitarbeitende: 106 Monate, α = 0,41,
β = 0,22, Niveau 3,59, Steigung +0,009 je Monat, Prognose 3,60 bis 3,65; Ø Historisch 3,16;
der letzte Monat (Juli 2025) liegt bei 4,17 mit 4 Bewertungen.

**Trend-Kachel.** Bis 2026-10-13 verglich die Kachel „Trend“ den letzten Prognosemonat mit dem
letzten Monat der Daten. Bei einem Ausreißer im letzten Monat zeigte sie deshalb „Fallend“, obwohl
die Prognose stieg (1&1 AG: 4,17 gegen 3,65). Sie heißt jetzt „Trend der Prognose“ und zeigt
das Vorzeichen und den Wert der Steigung b; ohne Kenngrößen gilt der alte Vergleich.

## 3. Begründung

Gewünscht vom Autor (2026-10-13): Nutzende sollen sehen, wie die Prognose entsteht und warum
sie vom historischen Durchschnitt abweicht. Die Erklärung nennt nur Werte, die das Verfahren
tatsächlich verwendet. Die weitere Begründung trägt der Autor nach.

## 4. Grenzen

- Die Prognose schreibt die Entwicklung fort; sie kennt keine Ursachen und gibt keinen
  Unsicherheitsbereich an.
- Monate ohne Bewertungen werden übersprungen, nicht als Lücke behandelt; Monate mit wenigen
  Bewertungen gehen mit demselben Gewicht ein wie volle Monate.
- In der Ansicht der Monatswerte (und in der kleinen Karte) beginnt die Prognoselinie wie bisher
  am letzten Monatswert; der Sprung zum geglätteten Niveau ist dort sichtbar.
- In der Evaluationsinstanz (`VITE_SHOW_FORECAST=false`, E28) gibt es weder Prognose noch
  Erklärung. Der PDF-Export enthält die Erklärung nicht.

## 5. Prüfung und Belege

- Tests: `backend/tests/forecast/test_forecast_details.py` (Kenngrößen, Prognose = Niveau +
  h · Steigung, Ersatzverfahren); alle Tests unter `backend/tests/forecast/` grün (77).
- Im Browser (1&1 AG, dunkles Theme): Linien, Legende, „?“-Fenster, Kacheln, keine
  Konsolenfehler.

## 6. Offene Punkte

- Begründung des Autors.
- Ob die Erklärung auch im PDF-Export erscheinen soll.
