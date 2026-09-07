-- OpenVoiceFlow app analytics, leaderboard, and privacy-safe website behavior schema.
--
-- App rows are anonymous installation snapshots. Website events use a visit ID
-- that rotates after 30 minutes of inactivity and is not a persistent person
-- identifier. Coarse edge-derived location may be stored, but IP addresses,
-- query strings, typed text, form values, and raw click coordinates are not.
-- Dictation content, snippets, dictionary entries, and profile data stay local.

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

CREATE TABLE IF NOT EXISTS website_events (
    event_id           UUID PRIMARY KEY,
    session_id         UUID NOT NULL,
    event_name         TEXT NOT NULL,
    path               TEXT NOT NULL,
    target             TEXT,
    acquisition_source TEXT NOT NULL,
    country            TEXT,
    region             TEXT,
    city               TEXT,
    campaign_id        TEXT,
    recipient_token    TEXT,
    CONSTRAINT website_events_campaign_pair_check CHECK (
        (campaign_id IS NULL AND recipient_token IS NULL)
        OR (campaign_id IS NOT NULL AND recipient_token IS NOT NULL)
    ),
    created_at         TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS website_events_created_idx
    ON website_events (created_at DESC);
CREATE INDEX IF NOT EXISTS website_events_session_created_idx
    ON website_events (session_id, created_at DESC);
CREATE INDEX IF NOT EXISTS website_events_name_created_idx
    ON website_events (event_name, created_at DESC);
CREATE INDEX IF NOT EXISTS website_events_campaign_created_idx
    ON website_events (campaign_id, created_at DESC)
    WHERE campaign_id IS NOT NULL;
