/* Festes Vokabular der Datenbasis (Inkrement 6, FA-25) und die bestehenden
 * Schwellen für die Warnung bei kleiner Basis (FA-26): 5 Bewertungen je Monat
 * (E4), 10 Bewertungen je Fenster (E12). Keine neue Schwelle; die Begriffe
 * sind eine Setzung des Autors, damit Diagramme aus Sternen nicht mit
 * Diagrammen aus Texten oder externen Quellen verwechselt werden. */

export const BASIS = {
  stars: { label: "Sternebewertung", title: "Datenbasis: Sterne der Kununu-Bewertungen (Gesamtnote je Bewertung oder Kategorien)" },
  text: { label: "Freitextanalyse", title: "Datenbasis: Freitexte der Kununu-Bewertungen (Schlüsselwort-Themen, Stimmung, kennzeichnende Begriffe)" },
  external: { label: "Externe Meldungen", title: "Datenbasis: Meldungen externer Quellen (Google News RSS, EQS News, allgemeine Ereignisse); keine Aussage über Ursachen" },
  market: { label: "Marktdaten", title: "Datenbasis: Kurse und Kennzahlen von Yahoo Finance; Einordnung, kein Zusammenhang mit den Bewertungen behauptet" },
}

export const MIN_REVIEWS_PER_MONTH = 5    // E4
export const MIN_REVIEWS_PER_WINDOW = 10  // E12

export function basisLabel(key) {
  return BASIS[key]?.label ?? key
}
