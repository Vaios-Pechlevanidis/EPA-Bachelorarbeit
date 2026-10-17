-- Migration: Create User Events
-- Description: Eigene Ereignisse (2026-10-17, E32). Nutzerinnen und Nutzer des
--   Dashboards tragen zu einem Unternehmen Zeiträume mit Titel und Vermerk ein
--   (z. B. Führungswechsel, Umstrukturierung, Standortschließung). Die Einträge
--   erscheinen als Markierungen im Monatsverlauf der Seite „Anomalien im
--   Verlauf“ und in der Liste „Eigene Ereignisse“. Sie gehen nicht in die
--   Erkennung, nicht in die Erklärungsansätze und nicht in die Belege ein; sie
--   sind keine Aussage über Ursachen.
--   Monatsgenau wie der Verlauf: date_from und date_to als „JJJJ-MM“, date_to
--   größer oder gleich date_from (Textvergleich reicht bei diesem Format).
--   Die Migration ist idempotent (IF NOT EXISTS, DO-Block für die Policies).
--   Ohne diese Tabelle antwortet GET/POST/PUT/DELETE /api/companies/{id}/events
--   mit 503 und nennt diese Datei.

CREATE TABLE IF NOT EXISTS user_events (
    id SERIAL PRIMARY KEY,
    company_id INTEGER NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    date_from TEXT NOT NULL CHECK (date_from ~ '^[0-9]{4}-(0[1-9]|1[0-2])$'),
    date_to   TEXT NOT NULL CHECK (date_to   ~ '^[0-9]{4}-(0[1-9]|1[0-2])$'),
    title TEXT NOT NULL CHECK (char_length(title) BETWEEN 1 AND 120),
    note TEXT CHECK (note IS NULL OR char_length(note) <= 1000),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_user_events_span CHECK (date_to >= date_from)
);

-- Abfrage je Unternehmen, sortiert nach Beginn
CREATE INDEX IF NOT EXISTS idx_user_events_company_from ON user_events(company_id, date_from);

COMMENT ON TABLE user_events IS
    'Eigene Ereignisse der Dashboard-Nutzer je Unternehmen (E32): Zeitraum in Monaten, Titel, Vermerk. Markierung im Monatsverlauf; keine Aussage über Ursachen, kein Eingang in Erkennung oder Erklärungsansätze.';
COMMENT ON COLUMN user_events.date_from IS 'Erster Monat des Ereignisses als JJJJ-MM.';
COMMENT ON COLUMN user_events.date_to IS 'Letzter Monat des Ereignisses als JJJJ-MM, größer oder gleich date_from; bei einem Monat gleich date_from.';
COMMENT ON COLUMN user_events.title IS 'Kurzer Titel (1 bis 120 Zeichen), erscheint in Liste und Tooltip.';
COMMENT ON COLUMN user_events.note IS 'Optionaler Vermerk (bis 1000 Zeichen), erscheint in Liste und Tooltip.';

-- Zugriff wie bei den übrigen Tabellen (Migration 005): anon liest, service_role schreibt.
ALTER TABLE user_events ENABLE ROW LEVEL SECURITY;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'user_events' AND policyname = 'public_read_user_events') THEN
        CREATE POLICY "public_read_user_events"
            ON user_events FOR SELECT
            TO anon, authenticated
            USING (true);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'user_events' AND policyname = 'service_role_all_user_events') THEN
        CREATE POLICY "service_role_all_user_events"
            ON user_events FOR ALL
            TO service_role
            USING (true)
            WITH CHECK (true);
    END IF;
END $$;
