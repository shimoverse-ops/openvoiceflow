-- OpenVoiceFlow analytics + leaderboard schema (Vercel Postgres / any Postgres 14+).
--
-- One row per anonymous device. No account, no email, no IP address stored —
-- country is derived from Vercel's edge geo header at request time and only
-- the two-letter code is kept. device_id is a client-generated random UUID;
-- it identifies a Mac, not a person, and is never linked to dictation
-- content, snippets, dictionary, or profile data (those never leave the Mac).

CREATE TABLE IF NOT EXISTS devices (
    device_id       UUID PRIMARY KEY,
    display_name    TEXT NOT NULL,
    words_total     INTEGER NOT NULL DEFAULT 0,
    minutes_saved   INTEGER NOT NULL DEFAULT 0,
    streak_days     INTEGER NOT NULL DEFAULT 0,
    feature_usage   JSONB NOT NULL DEFAULT '{}'::jsonb,
    -- Aggregate "which panes and features get used" counters: a fixed set of
    -- names (UsageCounters.Event in the app, EVENT_KEYS in api/analytics/
    -- ingest.js) mapped to lifetime totals. No timestamps and no free text —
    -- the server drops any name it does not already know, which is what keeps
    -- dictated content out of this column.
    events          JSONB NOT NULL DEFAULT '{}'::jsonb,
    country         TEXT,
    app_version     TEXT,
    first_use_date  TIMESTAMPTZ,
    first_seen      TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_seen       TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Leaderboard ordering.
CREATE INDEX IF NOT EXISTS devices_minutes_saved_idx ON devices (minutes_saved DESC);
-- Active-install windows in api/analytics/stats.js scan by recency.
CREATE INDEX IF NOT EXISTS devices_last_seen_idx ON devices (last_seen DESC);
