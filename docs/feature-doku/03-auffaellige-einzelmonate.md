# 03 – Auffällige Einzelmonate

| | |
|---|---|
| Inkrement | 2 (Nachtrag, Zyklus 2) |
| Anforderungen | Wunsch des Autors vom 2026-10-04: einzelne stark abweichende Monate sichtbar machen (Anlass Telekom Dezember 2022) |
| Entscheidungen | E14 in `docs/entscheidungen.md`; E3, E4, E9 unverändert |
| Status | umgesetzt; Schwellen **vorläufig** |
| Stand | 2026-10-04 |

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

## 6. Offene Punkte

- Faktor 3, Mindestabweichung 0,5 Sterne und 3 Nachbarmonate sind vorläufig.
- Sollen Einzelmonate mit sehr wenigen Bewertungen (5–6) anders dargestellt werden?
- Vorher-Nachher-Vergleich für einen Einzelmonat (Monat gegen Nachbarmonate) ist nicht
  umgesetzt; bisher nur die Bewertungsliste des Monats.
