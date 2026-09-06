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
      -- The app sends lifetime totals, so a late or duplicated sync can only
      -- repeat a number, never inflate one. Taking the larger of the two also
      -- keeps counters intact if a device's local store is reset.
      events = CASE WHEN EXCLUDED.events = '{}'::jsonb THEN devices.events ELSE EXCLUDED.events END,
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
