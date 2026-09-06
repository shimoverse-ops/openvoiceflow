import { timingSafeEqual } from "node:crypto";

import * as productionDatabase from "../_db.js";

/// Private aggregate telemetry for the local analytics dashboard.
///
/// Deliberately NOT public. api/leaderboard.js goes out of its way to hide the
/// population size — a fixed row cap and a minimum-usage bar so nobody can
/// count the userbase off the standings — and an open install counter would
/// hand over exactly what that protects. So this endpoint stays dark unless
/// ANALYTICS_STATS_TOKEN is configured, and answers 404 when it isn't: an
/// unconfigured deployment shouldn't even advertise that the route exists.
///
/// The response is aggregate-only (COUNTs and SUMs over every device). No
/// device_id, display name, or per-row data is read or returned, so this can
/// tell you how many people run 0.5.21 and which panes they open, and cannot
/// tell you anything about any one of them.

const MIN_TOKEN_LENGTH = 16;

function configuredToken(env) {
  const token = env.ANALYTICS_STATS_TOKEN;
  return typeof token === "string" && token.length >= MIN_TOKEN_LENGTH ? token : null;
}

function presentedToken(req) {
  const header = req.headers?.authorization;
  if (typeof header === "string" && header.startsWith("Bearer ")) return header.slice(7);
  const alternate = req.headers?.["x-analytics-token"];
  return typeof alternate === "string" ? alternate : "";
}

/// Constant-time compare so a wrong token can't be discovered byte by byte.
/// Lengths are compared first because timingSafeEqual throws on a mismatch;
/// token length is not the secret.
function tokenMatches(expected, presented) {
  const a = Buffer.from(expected, "utf8");
  const b = Buffer.from(presented, "utf8");
  if (a.length !== b.length) return false;
  return timingSafeEqual(a, b);
}

function clampDays(raw, fallback, max) {
  const value = Number.parseInt(raw, 10);
  if (!Number.isFinite(value) || value < 1) return fallback;
  return Math.min(value, max);
}

export function createStatsHandler(database = productionDatabase, env = process.env) {
  return async function handler(req, res) {
    const expected = configuredToken(env);
    if (!expected) {
      return res.status(404).json({ error: "not found" });
    }

    if (req.method !== "GET") {
      res.setHeader("Allow", "GET");
      return res.status(405).json({ error: "method not allowed" });
    }

    if (!tokenMatches(expected, presentedToken(req))) {
      res.setHeader("WWW-Authenticate", "Bearer");
      return res.status(401).json({ error: "unauthorized" });
    }

    // Aggregate numbers about people who did not ask to be counted publicly:
    // never cache them at the edge, and keep them out of search engines.
    res.setHeader("Cache-Control", "no-store, private");
    res.setHeader("X-Robots-Tag", "noindex");

    const activeDays = clampDays(req.query?.activeDays, 30, 365);
    const recentDays = Math.min(clampDays(req.query?.recentDays, 7, 365), activeDays);

    try {
      await database.ensureSchema();
      const stats = await database.readInstallStats({ activeDays, recentDays });
      return res.status(200).json({ version: 1, generatedAt: new Date().toISOString(), ...stats });
    } catch (error) {
      console.error("analytics stats failed", productionDatabase.databaseErrorDetails(error));
      return res.status(503).json({ error: "service unavailable" });
    }
  };
}

export default createStatsHandler();
