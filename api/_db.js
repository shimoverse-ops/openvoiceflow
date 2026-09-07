import { neon } from "@neondatabase/serverless";

export class DatabaseUnavailableError extends Error {
  constructor(message) {
    super(message);
    this.name = "DatabaseUnavailableError";
  }
}

let sqlClient = null;
let schemaReady = null;

export function databaseUrl(env = process.env) {
  const value = env.DATABASE_URL || env.POSTGRES_URL || env.POSTGRES_URL_NON_POOLING;
  if (typeof value !== "string" || value.length === 0) {
    throw new DatabaseUnavailableError("No supported PostgreSQL connection variable is configured");
  }
  return value;
}

/// Keep runtime logs useful without echoing driver messages that may contain
/// connection URLs or credentials.
export function databaseErrorDetails(error) {
  const name = typeof error?.name === "string" ? error.name : "Error";
  const code = typeof error?.code === "string" && /^[A-Z0-9_]+$/.test(error.code)
    ? error.code
    : undefined;
  return code ? { name, code } : { name };
}

function sql() {
  if (!sqlClient) sqlClient = neon(databaseUrl());
  return sqlClient;
}

// Schema creation remains idempotent and retries after a failed cold start.
export async function ensureSchema() {
  if (!schemaReady) {
    schemaReady = (async () => {
      const query = sql();
      await query`
        CREATE TABLE IF NOT EXISTS devices (
          device_id       UUID PRIMARY KEY,
          display_name    TEXT NOT NULL,
          words_total     INTEGER NOT NULL DEFAULT 0,
          minutes_saved   INTEGER NOT NULL DEFAULT 0,
          streak_days     INTEGER NOT NULL DEFAULT 0,
          feature_usage   JSONB NOT NULL DEFAULT '{}'::jsonb,
          country         TEXT,
          app_version     TEXT,
          first_use_date  TIMESTAMPTZ,
          first_seen      TIMESTAMPTZ NOT NULL DEFAULT now(),
          last_seen       TIMESTAMPTZ NOT NULL DEFAULT now()
        )
      `;
      await query`
        CREATE INDEX IF NOT EXISTS devices_minutes_saved_idx ON devices (minutes_saved DESC)
      `;
      // Added after the table shipped, so existing deployments need the
      // ALTER rather than only the CREATE above.
      await query`
        ALTER TABLE devices ADD COLUMN IF NOT EXISTS events JSONB NOT NULL DEFAULT '{}'::jsonb
      `;
      // Active-install windows scan by recency, not by rank.
      await query`
        CREATE INDEX IF NOT EXISTS devices_last_seen_idx ON devices (last_seen DESC)
      `;
      await query`
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
        )
      `;
      await query`
        CREATE INDEX IF NOT EXISTS website_events_created_idx
        ON website_events (created_at DESC)
      `;
      await query`
        CREATE INDEX IF NOT EXISTS website_events_session_created_idx
        ON website_events (session_id, created_at DESC)
      `;
      await query`
        CREATE INDEX IF NOT EXISTS website_events_name_created_idx
        ON website_events (event_name, created_at DESC)
      `;
      await query`
        ALTER TABLE website_events
        ADD COLUMN IF NOT EXISTS campaign_id TEXT,
        ADD COLUMN IF NOT EXISTS recipient_token TEXT
      `;
      // Earlier campaign-attribution builds briefly allowed one-sided rows.
      // Clear those unusable values before enforcing the pair invariant.
      await query`
        UPDATE website_events
        SET campaign_id = NULL, recipient_token = NULL
        WHERE (campaign_id IS NULL) <> (recipient_token IS NULL)
      `;
      await query`
        DO $$
        BEGIN
          ALTER TABLE website_events
          ADD CONSTRAINT website_events_campaign_pair_check CHECK (
            (campaign_id IS NULL AND recipient_token IS NULL)
            OR (campaign_id IS NOT NULL AND recipient_token IS NOT NULL)
          );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$
      `;
      await query`
        CREATE INDEX IF NOT EXISTS website_events_campaign_created_idx
        ON website_events (campaign_id, created_at DESC)
        WHERE campaign_id IS NOT NULL
      `;
    })();
  }
  try {
    await schemaReady;
  } catch (error) {
    schemaReady = null;
    throw error;
  }
}

export async function deleteDevice(deviceId) {
  await sql()`DELETE FROM devices WHERE device_id = ${deviceId}`;
}

export async function upsertDevice(device) {
  const query = sql();
  await query`
    INSERT INTO devices (
      device_id, display_name, words_total, minutes_saved, streak_days,
      feature_usage, events, country, app_version, first_use_date, first_seen, last_seen
    ) VALUES (
      ${device.deviceId}, ${device.displayName}, ${device.wordsTotal}, ${device.minutesSaved},
      ${device.streakDays}, ${JSON.stringify(device.featureUsage)},
      ${JSON.stringify(device.events || {})}, ${device.country},
      ${device.appVersion}, ${device.firstUseDate}, now(), now()
    )
    ON CONFLICT (device_id) DO UPDATE SET
      display_name = EXCLUDED.display_name,
      words_total = EXCLUDED.words_total,
      minutes_saved = EXCLUDED.minutes_saved,
      streak_days = EXCLUDED.streak_days,
      feature_usage = EXCLUDED.feature_usage,
      -- Merge per key, taking the larger value. Counters are lifetime totals,
      -- so the larger number is always the newer one — but "newer" is not the
      -- same as "arrives second": syncIfDue, the leaderboard open and a
      -- nickname commit can all be in flight at once, and if an older request
      -- lands last, wholesale replacement would roll every counter backwards
      -- and drop any key the newer snapshot had added. A per-key MAX is
      -- order-independent, so it does not matter which request wins the race.
      -- Non-numeric values (an older or buggy client) collapse to 0 rather
      -- than failing the upsert; CASE is required because AND does not
      -- short-circuit in SQL.
      events = (
        SELECT COALESCE(jsonb_object_agg(key, to_jsonb(value)), '{}'::jsonb)
        FROM (
          SELECT key, MAX(value) AS value
          FROM (
            SELECT key, CASE WHEN jsonb_typeof(value) = 'number'
                             THEN (value)::numeric ELSE 0 END AS value
            FROM jsonb_each(devices.events)
            UNION ALL
            SELECT key, CASE WHEN jsonb_typeof(value) = 'number'
                             THEN (value)::numeric ELSE 0 END
            FROM jsonb_each(EXCLUDED.events)
          ) pairs
          GROUP BY key
        ) largest
      ),
      country = COALESCE(EXCLUDED.country, devices.country),
      app_version = EXCLUDED.app_version,
      first_use_date = COALESCE(devices.first_use_date, EXCLUDED.first_use_date),
      last_seen = now()
  `;
}

function rowShape(row) {
  return {
    deviceId: row.device_id,
    displayName: row.display_name,
    minutesSaved: Number(row.minutes_saved),
    rank: Number(row.rank),
  };
}

export async function readLeaderboard(deviceId, limit) {
  const query = sql();
  const topRows = await query`
    SELECT device_id, display_name, minutes_saved,
           RANK() OVER (ORDER BY minutes_saved DESC) AS rank
    FROM devices
    ORDER BY minutes_saved DESC, device_id ASC
    LIMIT ${limit}
  `;

  let you = null;
  if (deviceId) {
    const rows = await query`
      WITH ranked AS (
        SELECT device_id, display_name, minutes_saved,
               RANK() OVER (ORDER BY minutes_saved DESC) AS rank
        FROM devices
      )
      SELECT device_id, display_name, minutes_saved, rank FROM ranked
      WHERE device_id = ${deviceId}
    `;
    if (rows.length > 0) you = rowShape(rows[0]);
  }

  return { top: topRows.map(rowShape), you };
}

/// Aggregate install + usage telemetry for the private analytics dashboard.
///
/// Every figure here is a COUNT or SUM across devices — no row is ever
/// returned, so nothing here can identify a device, and display names (the
/// one user-supplied string in the table) are not read at all. The public
/// leaderboard deliberately hides the population size; this lives behind
/// ANALYTICS_STATS_TOKEN precisely so that stays true.
export async function readInstallStats({ activeDays = 30, recentDays = 7, limit = 25 } = {}) {
  const query = sql();

  const [totals] = await query`
    SELECT
      COUNT(*)::int AS installs,
      COUNT(*) FILTER (WHERE last_seen >= now() - make_interval(days => ${recentDays}))::int AS active_recent,
      COUNT(*) FILTER (WHERE last_seen >= now() - make_interval(days => ${activeDays}))::int AS active_window,
      COUNT(*) FILTER (WHERE first_seen >= now() - make_interval(days => ${activeDays}))::int AS new_window,
      COUNT(DISTINCT country) FILTER (WHERE country IS NOT NULL)::int AS countries,
      COALESCE(SUM(words_total), 0)::bigint AS words_total,
      COALESCE(SUM(minutes_saved), 0)::bigint AS minutes_saved
    FROM devices
  `;

  const versions = await query`
    SELECT COALESCE(app_version, 'unknown') AS key, COUNT(*)::int AS total
    FROM devices GROUP BY 1 ORDER BY total DESC, key ASC LIMIT ${limit}
  `;

  const countries = await query`
    SELECT country AS key, COUNT(*)::int AS total
    FROM devices WHERE country IS NOT NULL
    GROUP BY 1 ORDER BY total DESC, key ASC LIMIT ${limit}
  `;

  // CASE, not `jsonb_typeof(...) = 'number' AND (...)::numeric > 0`: SQL's AND
  // does not short-circuit, so the planner is free to attempt the cast on a
  // row the type check would have excluded and fail the whole query with
  // "cannot cast jsonb string to type numeric". CASE is defined to skip the
  // branches it does not select. Rows written by an older or buggy client are
  // exactly where a non-number shows up, so this has to hold for real data.
  const [features] = await query`
    SELECT
      COUNT(*) FILTER (WHERE feature_usage->>'cleanupEnabled' = 'true')::int AS cleanup_enabled,
      COUNT(*) FILTER (WHERE CASE WHEN jsonb_typeof(feature_usage->'snippetsCount') = 'number'
                                  THEN (feature_usage->'snippetsCount')::numeric > 0
                                  ELSE false END)::int AS uses_snippets,
      COUNT(*) FILTER (WHERE CASE WHEN jsonb_typeof(feature_usage->'dictionaryCount') = 'number'
                                  THEN (feature_usage->'dictionaryCount')::numeric > 0
                                  ELSE false END)::int AS uses_dictionary,
      COUNT(*) FILTER (WHERE feature_usage->>'hasKnowMeProfile' = 'true')::int AS has_profile
    FROM devices
  `;

  // One row per event name, summed across devices. `devices` is how many
  // installs touched it at all — the more honest adoption number, since a
  // single heavy user can dominate a raw total.
  const events = await query`
    SELECT key, SUM(value)::bigint AS total, COUNT(*)::int AS devices
    FROM (
      SELECT entry.key AS key,
             CASE WHEN jsonb_typeof(entry.value) = 'number'
                  THEN (entry.value)::numeric ELSE 0 END AS value
      FROM devices, LATERAL jsonb_each(devices.events) AS entry
    ) counted
    WHERE value > 0
    GROUP BY key ORDER BY total DESC, key ASC LIMIT ${limit}
  `;

  const rank = (rows) => rows.map((row) => ({ key: String(row.key), total: Number(row.total) }));

  return {
    window: { activeDays, recentDays },
    totals: {
      installs: Number(totals.installs),
      activeRecent: Number(totals.active_recent),
      activeWindow: Number(totals.active_window),
      newWindow: Number(totals.new_window),
      countries: Number(totals.countries),
      wordsTotal: Number(totals.words_total),
      minutesSaved: Number(totals.minutes_saved),
    },
    versions: rank(versions),
    countries: rank(countries),
    features: {
      cleanupEnabled: Number(features.cleanup_enabled),
      usesSnippets: Number(features.uses_snippets),
      usesDictionary: Number(features.uses_dictionary),
      hasKnowMeProfile: Number(features.has_profile),
    },
    events: events.map((row) => ({
      key: String(row.key),
      total: Number(row.total),
      devices: Number(row.devices),
    })),
  };
}

export async function insertWebsiteEvent(event) {
  const query = sql();
  await query`
    INSERT INTO website_events (
      event_id, session_id, event_name, path, target, acquisition_source,
      country, region, city, campaign_id, recipient_token, created_at
    ) VALUES (
      ${event.eventId}, ${event.sessionId}, ${event.eventName}, ${event.path},
      ${event.target}, ${event.acquisitionSource}, ${event.location.country},
      ${event.location.region}, ${event.location.city}, ${event.campaignId ?? null},
      ${event.recipientToken ?? null}, now()
    )
    ON CONFLICT (event_id) DO NOTHING
  `;
}

export async function deleteExpiredWebsiteEvents(retainedDays = 90) {
  const query = sql();
  const result = await query`
    DELETE FROM website_events
    WHERE created_at < NOW() - (${retainedDays} * INTERVAL '1 day')
    RETURNING event_id
  `;
  return result.length;
}

function normalizeReportRows(rows) {
  const numericFields = new Set([
    "sessions", "pageviews", "clicks", "downloads", "events", "pages_per_session",
    "bounce_rate", "reporting_installations", "total_items", "visitors", "downloaders",
  ]);
  return rows.map((row) => Object.fromEntries(Object.entries(row).map(([key, value]) => {
    if (typeof value === "bigint") return [key, Number(value)];
    if (numericFields.has(key) && typeof value === "string" && value !== "") return [key, Number(value)];
    return [key, value];
  })));
}

export async function readAnalyticsReport(days = 30) {
  const query = sql();
  const [
    websiteSummary,
    websitePaths,
    websiteClicks,
    websiteEvents,
    websiteLocations,
    websiteSources,
    websiteDaily,
    emailCampaigns,
    appLastSync,
    installStats,
  ] = await Promise.all([
    query`
      WITH per_session AS (
        SELECT session_id,
               COUNT(*) FILTER (WHERE event_name = 'page_view')::int AS pageviews,
               COUNT(*) FILTER (WHERE event_name <> 'page_view')::int AS clicks
        FROM website_events
        WHERE created_at >= NOW() - (${days} * INTERVAL '1 day')
        GROUP BY session_id
      )
      SELECT COUNT(*)::int AS sessions,
             COALESCE(SUM(pageviews), 0)::int AS pageviews,
             COALESCE(SUM(clicks), 0)::int AS clicks,
             COALESCE(ROUND(AVG(pageviews), 2), 0) AS pages_per_session,
             COALESCE(ROUND(100.0 * COUNT(*) FILTER (WHERE pageviews = 1) / NULLIF(COUNT(*), 0), 1), 0) AS bounce_rate,
             (SELECT COUNT(*)::int FROM website_events
              WHERE event_name = 'download_click'
                AND created_at >= NOW() - (${days} * INTERVAL '1 day')) AS downloads,
             (SELECT MAX(created_at)::text FROM website_events
              WHERE created_at >= NOW() - (${days} * INTERVAL '1 day')) AS last_event_at
      FROM per_session
    `,
    query`
      SELECT path, COUNT(*)::int AS pageviews,
             COUNT(DISTINCT session_id)::int AS sessions
      FROM website_events
      WHERE event_name = 'page_view'
        AND created_at >= NOW() - (${days} * INTERVAL '1 day')
      GROUP BY path ORDER BY pageviews DESC, sessions DESC LIMIT 100
    `,
    query`
      SELECT event_name, path, target, COUNT(*)::int AS clicks,
             COUNT(DISTINCT session_id)::int AS sessions
      FROM website_events
      WHERE event_name <> 'page_view'
        AND created_at >= NOW() - (${days} * INTERVAL '1 day')
      GROUP BY event_name, path, target
      ORDER BY clicks DESC, sessions DESC LIMIT 100
    `,
    query`
      SELECT event_name, COUNT(*)::int AS events,
             COUNT(DISTINCT session_id)::int AS sessions
      FROM website_events
      WHERE created_at >= NOW() - (${days} * INTERVAL '1 day')
      GROUP BY event_name ORDER BY events DESC
    `,
    query`
      SELECT COALESCE(country, 'Unknown') AS country,
             COALESCE(region, 'Unknown') AS region,
             COALESCE(city, 'Unknown') AS city,
             COUNT(DISTINCT session_id)::int AS sessions,
             COUNT(*)::int AS events
      FROM website_events
      WHERE created_at >= NOW() - (${days} * INTERVAL '1 day')
      GROUP BY country, region, city
      ORDER BY sessions DESC, events DESC LIMIT 100
    `,
    query`
      SELECT acquisition_source, COUNT(DISTINCT session_id)::int AS sessions,
             COUNT(*) FILTER (WHERE event_name = 'page_view')::int AS pageviews,
             COUNT(*) FILTER (WHERE event_name <> 'page_view')::int AS clicks
      FROM website_events
      WHERE created_at >= NOW() - (${days} * INTERVAL '1 day')
      GROUP BY acquisition_source ORDER BY sessions DESC, pageviews DESC
    `,
    query`
      SELECT created_at::date::text AS day,
             COUNT(DISTINCT session_id)::int AS sessions,
             COUNT(*) FILTER (WHERE event_name = 'page_view')::int AS pageviews,
             COUNT(*) FILTER (WHERE event_name <> 'page_view')::int AS clicks
      FROM website_events
      WHERE created_at >= NOW() - (${days} * INTERVAL '1 day')
      GROUP BY created_at::date ORDER BY day
    `,
    query`
      SELECT campaign_id,
             COUNT(DISTINCT recipient_token) FILTER (WHERE event_name = 'page_view')::int AS visitors,
             COUNT(DISTINCT recipient_token) FILTER (WHERE event_name = 'download_click')::int AS downloaders,
             COUNT(*)::int AS events,
             MAX(created_at)::text AS last_event_at
      FROM website_events
      WHERE campaign_id IS NOT NULL
        AND recipient_token IS NOT NULL
        AND created_at >= NOW() - (${days} * INTERVAL '1 day')
      GROUP BY campaign_id ORDER BY visitors DESC, events DESC
    `,
    query`SELECT MAX(last_seen)::text AS last_synced_at FROM devices`,
    readInstallStats({ activeDays: days, recentDays: 7, limit: 100 }),
  ]);

  return {
    website: {
      summary: normalizeReportRows(websiteSummary)[0] || {},
      paths: normalizeReportRows(websitePaths),
      clicks: normalizeReportRows(websiteClicks),
      events: normalizeReportRows(websiteEvents),
      locations: normalizeReportRows(websiteLocations),
      sources: normalizeReportRows(websiteSources),
      daily: normalizeReportRows(websiteDaily),
      email_campaigns: normalizeReportRows(emailCampaigns),
    },
    app: {
      summary: {
        reporting_installations: installStats.totals.installs,
        active_7d: installStats.totals.activeRecent,
        active_30d: installStats.totals.activeWindow,
        active_period: installStats.totals.activeWindow,
        words_total: installStats.totals.wordsTotal,
        minutes_saved: installStats.totals.minutesSaved,
        last_synced_at: appLastSync[0]?.last_synced_at || null,
      },
      features: [
        { feature: "AI cleanup", reporting_installations: installStats.features.cleanupEnabled, total_items: null },
        { feature: "Snippets", reporting_installations: installStats.features.usesSnippets, total_items: null },
        { feature: "Dictionary", reporting_installations: installStats.features.usesDictionary, total_items: null },
        { feature: "Know Me profile", reporting_installations: installStats.features.hasKnowMeProfile, total_items: null },
      ],
      versions: installStats.versions.map((row) => ({
        app_version: row.key,
        reporting_installations: row.total,
      })),
      countries: installStats.countries.map((row) => ({
        country: row.key,
        reporting_installations: row.total,
      })),
      events: installStats.events,
    },
  };
}
