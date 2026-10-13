# 03 – Auffällige Einzelmonate

| | |
|---|---|
| Inkrement | 2 (Nachtrag, Zyklus 2) |
| Anforderungen | Wunsch des Autors vom 2026-10-04: einzelne stark abweichende Monate sichtbar machen (Anlass Telekom Dezember 2022) |
| Entscheidungen | E14 in `docs/entscheidungen.md`; E3, E4, E9 unverändert; Zufallsbefund aus E30 (Befund 2026-10-13) |
| Status | umgesetzt; Schwellen **vorläufig**; Treffsicherheit **ungeprüft**, als „ungeprüft“ gekennzeichnet; per Schalter `VITE_SHOW_OUTLIER_MONTHS` ausblendbar (2026-10-13) |
| Stand | 2026-10-13 |

## 1. Vorstellung

Im Monatsverlauf (Dashboard-Karte und Detailseite „Anomalien im Verlauf“) markiert eine
hohle **Raute** auf dem Monatswert einen **auffälligen Einzelmonat**: einen Monat, der stark
von den Monaten davor und danach abweicht, nach dem das Niveau aber gleich bleibt. Rot heißt
unter, grün über den Nachbarmonaten. Der Tooltip nennt die Abweichung, das Niveau der
Nachbarmonate und die Zahl der Bewertungen. Der Untertitel zählt die Einzelmonate getrennt
von den Niveauwechseln („4 auffällige Veränderungen · 3 auffällige Einzelmonate“).

Auf der Detailseite steht unter der Liste der Veränderungen eine Liste **„Auffällige
Einzelmonate“**, größte Abweichung zuerst. Ein Klick auf eine Zeile oder eine Raute wählt den
Monat aus (`?month=2022-12`); darunter erscheinen die **Bewertungen dieses Monats** im
gleichen Format wie beim Vergleich, mit Detailfenster.

Nutzen: Kurze Einbrüche oder Spitzen, die die Niveauerkennung bewusst übergeht, werden
sichtbar, und man kommt direkt zu den Bewertungen des Monats.

**Nachtrag 2026-10-13 – Kennzeichnung und Schalter:**

- **Kennzeichnung:** Überall, wo Einzelmonate erklärt werden, steht der Zusatz „Ungeprüft: in
  der Simulation etwa so häufig wie bei reinem Zufall (E30)“:
  - in der Legende unter dem Monatsverlauf (Karte, Detailseite, vergrößerte Kurskarte im
    Aktien-Dashboard),
  - im Tooltip einer Raute,
  - unter der Liste „Einzelmonate“ der Karte „Markierungen“,
  - im Text über dem Vergleich, wenn ein Einzelmonat ausgewählt ist,
  - im PDF-Export: Legende, Kachel „Einzelmonate“ („auffällig, ungeprüft (E30)“) und Kopf der
    Liste.

  Der Wortlaut steht einmal in `frontend/src/config.js` (`OUTLIER_UNVALIDATED_NOTE`), damit alle
  Ansichten dasselbe zeigen.
- **Schalter `VITE_SHOW_OUTLIER_MONTHS`** (beim Bauen, Muster wie `VITE_SHOW_FORECAST`, E28):
  Standard an; `false` oder `0` blendet die Einzelmonate im Frontend ganz aus.
  - Monatsverlauf: keine Rauten, keine Einzelmonat-Zeile im Tooltip, kein Legendeneintrag.
  - Detailseite: kein Umschalter „Veränderungen“ / „Einzelmonate“ und keine Liste;
    `?liste=einzelmonate` zeigt die Veränderungen.
  - Zähler: kein Einzelmonat in den Untertiteln von Karte und Detailseite.
  - PDF-Export: weder Kachel noch Liste „Auffällige Einzelmonate“; das Inhaltsverzeichnis nennt
    sie nicht.
  - Ein Monat aus einem älteren Link (`?from=2022-12&to=2022-12` oder `?month=2022-12`) ist dann
    eine freie Auswahl dieses Monats (Doku 06, E17), ohne den Text „Auffälliger Einzelmonat“.
  - Das Backend liefert `outlier_months` unverändert; der Schalter wirkt nur auf die Anzeige.

## 2. Erklärung

Für jeden bewerteten Monat (mindestens 5 Bewertungen mit Wert, E4):

1. **Nachbarn:** die bis zu 3 bewerteten Monate davor und die bis zu 3 danach (nicht
   bewertete Monate werden übersprungen). Je Seite sind mindestens 2 nötig.
2. **Schwelle** `T = max(3 · σ, 0,5 Sterne)`. σ ist die robuste Streuung der Monatsmittel
   der Reihe (`noise_sigma`, dieselbe wie im Strafterm, E9). Bei ruhigen Reihen gilt
   0,5 Sterne, bei stark schwankenden 3 σ (Telekom: σ 0,28, T 0,85).
3. **Prüfung:** Der Monat weicht vom Median der Monate davor und vom Median der Monate
   danach jeweils um mindestens `T` ab, in dieselbe Richtung, und seine direkten Nachbarn
   weichen selbst nicht so stark ab.
4. **Kennzahlen:** Niveau = Median aller Nachbarmonate, Abweichung = Monatsmittel minus
   Niveau.

Beispiel Telekom Dezember 2022: Monatsmittel 2,60 (11 Bewertungen), Niveau der Monate
September 2022 bis März 2023 4,01, Abweichung −1,41 Sterne.

Die Werte stehen in der API unter `outlier_months`, die Parameter unter `params`
(`outlier_sigma_factor`, `outlier_min_delta`, `outlier_neighbours`). Quelle, Dimension und
Statusgruppe wirken wie bei den Niveauwechseln. Nicht geeignete Reihen (E4) haben keine
Einzelmonate.

## 3. Begründung

- **Getrennt von den Niveauwechseln:** Ein Einzelmonat ist kein neues Niveau. Ihn als
  Niveauwechsel zu markieren, hieße den Strafterm senken oder `min_size` verkleinern; das
  erzeugt bei verrauschten Reihen viele Fehlmarkierungen (E9). Eine eigene Markierung mit
  eigener Form hält beide Aussagen auseinander.
- **Vergleich mit beiden Seiten:** Am Niveauwechsel liegt eine Seite auf dem Niveau des
  Monats; dort wird nichts gemeldet. Ein erster Entwurf mit dem Niveau des PELT-Abschnitts
  wurde verworfen (Nachbarmonate wurden mitgemeldet, siehe E14).
- **Schwelle relativ zur Streuung:** 3 σ passt sich jeder Reihe an; 0,5 Sterne verhindern,
  dass in sehr ruhigen Reihen kleine Schwankungen gemeldet werden.
- **Raute:** Die Karte nutzt Ringe, die Detailseite Stufen für Niveauwechsel; eine hohle
  Raute ist davon unterscheidbar und auch ohne Farbe lesbar.

## 4. Grenzen

- **Zufallsbefund (E30, Befund 2026-10-13):** In der semi-synthetischen Prüfung entstehen in den
  15 geeigneten Reihen (Mitarbeitende, Gesamtbewertung) **ohne** eingesetzte Veränderung im
  Mittel 8,9 Einzelmonate je Wiederholung, wenn die Noten über die Bewertungen permutiert
  werden, und 5,4, wenn die bewerteten Monate ihre Plätze tauschen. Auf den echten Reihen sind
  es 9: etwa so viele wie bei permutierten Noten und rund 1,7-mal so viele wie bei getauschten
  Monaten. Einzelmonate treten damit etwa so häufig auf wie bei reinem Zufall; aus der Zahl
  allein lässt sich nicht ablesen, dass ein gemeldeter Monat mehr ist als Rauschen. Die Werte
  stehen nebeneinander und werden nicht verrechnet; es gibt keine Signifikanzaussage (E30). Die
  Regel und ihre Parameter bleiben unverändert (E14).
- Ob die gemeldeten Einzelmonate zutreffen, ist nicht geprüft: Die Referenzzeiträume schließen
  einzelne Ausreißermonate aus (Regel 4, E5), der Hauptwert des Abgleichs nach Regel 6 wertet
  nur Niveauwechsel (E14, Aktualisierung 2026-10-10). Deshalb der Zusatz „ungeprüft“ in der Anzeige.
- Viele Einzelmonate beruhen auf 5 bis 11 Bewertungen; ein solcher Monat kann Zufall sein.
- Keine Aussage über Ursachen.
- Ränder der Reihe und zwei aufeinanderfolgende auffällige Monate werden nicht gemeldet.
- Mehrere Einzelmonate in einer Reihe sind möglich (Telekom 3, Cancom 2); bei
  Einzeldimensionen sind es mehr (121 in 208 geeigneten Reihen), weil diese stärker
  schwanken.

## 5. Prüfung und Belege

| Was | Beleg |
|---|---|
| Regel | `backend/tests/anomaly/test_outlier_months.py`: einzelner Einbruch und einzelne Spitze, kein Einzelmonat am Niveauwechsel, Mindestabweichung 0,5, Schwelle 3 σ bei Streuung, nicht bewertete Monate, Sortierung, Route mit `outlier_months` und `dimension=all` |
| Echte Daten | 2026-10-04, Mitarbeitende, Gesamtbewertung: Faktor 2,5 / 3 / 3,5 → 18 / 9 / 3 Einzelmonate in 15 Reihen; Liste in E14 |
| Browser | Telekom: Rauten 2015-05, 2017-05, 2022-12; Auswahl Dezember 2022 → 11 Bewertungen; Dashboard-Karte mit Rauten, Legende und Zähler |
| Simulation (E30) | `backend/data/calibration/semisynthetisch_2026-10-13.json`: `results.total`, Zeilen mit `delta` 0, `outliers_mean` 0,5913 (Permutation der Noten) bzw. 0,3583 (getauschte Monate) je Reihe und Wiederholung, mal 15 Reihen = 8,9 bzw. 5,4; `series[].observed_outliers` summiert 9 |
| Kennzeichnung und Schalter (2026-10-13) | `npx eslint` ohne Befund für `config.js`, `AnomalyCard.jsx`, `Anomalies.jsx`, `pdfExport.js`; `vite build` im Standard und mit `VITE_SHOW_OUTLIER_MONTHS=false` (im Bündel ist der Wert eingesetzt). Browser, Telekom, Standardbau: Legende und Liste „Einzelmonate“ (Gesamtbewertung) sowie Tooltip der Raute Dez. 2022 (Dimension Kommunikation) mit dem Zusatz. Bau mit `false`: keine Rauten, kein Umschalter, `?liste=einzelmonate` zeigt die 4 Veränderungen, Untertitel ohne Einzelmonate (Detailseite und Dashboard-Karte), Hinweis „Stufe oder Monat anklicken“, keine Konsolenfehler aus der App. PDF-Export nicht im Browser erzeugt (nur Code und Bau geprüft) |

## 6. Offene Punkte

- **Entscheidung des Autors offen:** Baut die Evaluationsinstanz (DZ3) mit
  `VITE_SHOW_OUTLIER_MONTHS=false`? Vorschlag und Folgen in `docs/evaluationsinstanz.md`.
- Eine Prüfung der Einzelmonate bräuchte eine eigene Annotation einzelner Monate oder eine
  vorab festgelegte Prüfung mit anderen Daten (E30: keine Nachkalibrierung mit denselben 15
  Reihen).
- Faktor 3, Mindestabweichung 0,5 Sterne und 3 Nachbarmonate sind vorläufig.
- Sollen Einzelmonate mit sehr wenigen Bewertungen (5–6) anders dargestellt werden?
- Vorher-Nachher-Vergleich für einen Einzelmonat (Monat gegen Nachbarmonate) ist nicht
  umgesetzt; bisher nur die Bewertungsliste des Monats.
