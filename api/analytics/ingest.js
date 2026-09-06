import * as productionDatabase from "../_db.js";

const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
const MAX_COUNTER = 100_000_000;
const FEATURE_KEYS = ["cleanupEnabled", "snippetsCount", "dictionaryCount", "hasKnowMeProfile"];

/// Which pane/feature counters the app is allowed to report, mirroring
/// UsageCounters.Event in the native app (tests/test_usage_counters_contract.py
/// fails if the two drift). An allowlist rather than a pattern: it is the one
/// thing standing between an aggregate counter store and an arbitrary
/// client-supplied string, and a string is where user content could leak in.
/// Unknown names are dropped silently so an older server never rejects a newer
/// app's sync outright.
const EVENT_KEYS = [
  "pane.home",
  "pane.history",
  "pane.personalize",
  "pane.settings",
  "pane.leaderboard",
  "tab.dictionary",
  "tab.snippets",
  "tab.styles",
  "tab.profile",
  "action.dictation_completed",
  "action.history_copied",
  "action.history_cleared",
  "action.dictionary_entry_added",
  "action.snippet_added",
  "action.style_applied",
  "action.know_me_interview_started",
  "action.know_me_interview_finished",
  "action.cleanup_backend_changed",
  "action.update_checked",
  "action.version_history_opened",
  "action.feedback_opened",
  "action.feedback_sent",
  "action.leaderboard_name_changed",
  "action.onboarding_completed",
];
const CONTROL_CHARS_RE = /[\x00-\x1F\x7F]/g;

function isNonNegInt(value) {
  return typeof value === "number"
    && Number.isFinite(value)
    && Number.isInteger(value)
    && value >= 0
    && value <= MAX_COUNTER;
}

function sanitizeName(raw) {
  if (typeof raw !== "string") return null;
  const cleaned = raw.replace(CONTROL_CHARS_RE, "").replace(/\s+/g, " ").trim().slice(0, 40);
  return cleaned.length > 0 ? cleaned : null;
}

function sanitizeFeatureUsage(raw) {
  if (typeof raw !== "object" || raw === null || Array.isArray(raw)) return {};
  const out = {};
  for (const key of FEATURE_KEYS) {
    const value = raw[key];
    if (typeof value === "boolean") out[key] = value;
    else if (isNonNegInt(value)) out[key] = value;
  }
  return out;
}

function sanitizeEvents(raw) {
  if (typeof raw !== "object" || raw === null || Array.isArray(raw)) return {};
  const out = {};
  for (const key of EVENT_KEYS) {
    const value = raw[key];
    if (isNonNegInt(value) && value > 0) out[key] = value;
  }
  return out;
}

function serviceUnavailable(res, label, error) {
  console.error(label, productionDatabase.databaseErrorDetails(error));
  return res.status(503).json({ error: "service unavailable" });
}

export function createIngestHandler(database = productionDatabase) {
  return async function handler(req, res) {
    if (req.method === "DELETE") {
      const deviceId = typeof req.query.deviceId === "string" ? req.query.deviceId.toLowerCase() : "";
      if (!UUID_RE.test(deviceId)) {
        return res.status(400).json({ error: "deviceId must be a UUID" });
      }
      try {
        await database.ensureSchema();
        await database.deleteDevice(deviceId);
        return res.status(200).json({ ok: true });
      } catch (error) {
        return serviceUnavailable(res, "analytics delete failed", error);
      }
    }

    if (req.method !== "POST") {
      res.setHeader("Allow", "POST, DELETE");
      return res.status(405).json({ error: "method not allowed" });
    }

    const body = req.body || {};
    const deviceId = typeof body.deviceId === "string" ? body.deviceId.toLowerCase() : "";
    if (!UUID_RE.test(deviceId)) {
      return res.status(400).json({ error: "deviceId must be a UUID" });
    }
    const displayName = sanitizeName(body.displayName);
    if (!displayName) {
      return res.status(400).json({ error: "displayName is required" });
    }

    const firstUseDate = typeof body.firstUseDate === "string" && !Number.isNaN(Date.parse(body.firstUseDate))
      ? new Date(body.firstUseDate)
      : null;
    const country = typeof req.headers["x-vercel-ip-country"] === "string"
      ? req.headers["x-vercel-ip-country"].slice(0, 2)
      : null;
    const device = {
      deviceId,
      displayName,
      wordsTotal: isNonNegInt(body.wordsTotal) ? body.wordsTotal : 0,
      minutesSaved: isNonNegInt(body.minutesSaved) ? body.minutesSaved : 0,
      streakDays: isNonNegInt(body.streakDays) ? body.streakDays : 0,
      featureUsage: sanitizeFeatureUsage(body.featureUsage),
      events: sanitizeEvents(body.events),
      country,
      appVersion: typeof body.appVersion === "string" ? body.appVersion.slice(0, 20) : null,
      firstUseDate,
    };

    try {
      await database.ensureSchema();
      await database.upsertDevice(device);
      return res.status(200).json({ ok: true });
    } catch (error) {
      return serviceUnavailable(res, "analytics ingest failed", error);
    }
  };
}

export default createIngestHandler();
