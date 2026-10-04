import { useCompanyResource } from "./useCompanyResource"

/* Aktienkurs und Kennzahlen eines Unternehmens als Einordnung
 * (GET /analytics/company/{id}/market, Inkrement 3, E15). Ohne Ticker oder
 * ohne Kursdaten liefert der Endpunkt available: false mit reason; das ist
 * kein Fehler. */
export function useMarket(companyId) {
  return useCompanyResource(companyId, "market")
}
