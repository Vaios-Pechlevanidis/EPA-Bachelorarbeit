/* Import-Verlauf je Unternehmen im localStorage (bis zu 10 Einträge).
 * Aus ImportModal.jsx ausgelagert, damit die Komponentendatei nur Komponenten
 * exportiert (Lint-Regel react-refresh/only-export-components); Verhalten
 * unverändert. */

export function saveImportHistory(companyId, entry) {
  if (!companyId) return
  const key = `import_history_${companyId}`
  const existing = JSON.parse(localStorage.getItem(key) || "[]")
  const updated = [entry, ...existing].slice(0, 10)
  localStorage.setItem(key, JSON.stringify(updated))
}

export function getImportHistory(companyId) {
  if (!companyId) return []
  return JSON.parse(localStorage.getItem(`import_history_${companyId}`) || "[]")
}
