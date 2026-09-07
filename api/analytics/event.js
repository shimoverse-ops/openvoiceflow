import * as productionDatabase from "../_db.js";
import {
  hasOwnerExclusionCookie,
  isAutomatedRequest,
  isSameSiteRequest,
  normalizeWebsiteEvent,
  readEdgeLocation,
  setPrivateResponseHeaders,
} from "../_websiteAnalytics.js";

function serviceUnavailable(res, error) {
  console.error("website analytics ingest failed", productionDatabase.databaseErrorDetails(error));
  return res.status(503).json({ error: "service unavailable" });
}

export function createWebsiteEventHandler(
  database = productionDatabase,
  options = { campaignAttributionSecret: process.env.ANALYTICS_CAMPAIGN_SECRET }
) {
  return async function handler(req, res) {
    setPrivateResponseHeaders(res);
    if (req.method !== "POST") {
      res.setHeader("Allow", "POST");
      return res.status(405).json({ error: "method not allowed" });
    }
    if (!isSameSiteRequest(req.headers)) {
      return res.status(403).json({ error: "forbidden" });
    }
    if (hasOwnerExclusionCookie(req.headers)) {
      return res.status(202).json({ ok: true, ignored: true });
    }
    if (isAutomatedRequest(req.headers)) {
      return res.status(202).json({ ok: true, ignored: true });
    }

    let event;
    try {
      event = normalizeWebsiteEvent(req.body || {}, options);
    } catch (error) {
      return res.status(400).json({ error: error?.message || "invalid event" });
    }

    try {
      await database.ensureSchema();
      await database.insertWebsiteEvent({
        ...event,
        location: readEdgeLocation(req.headers),
      });
      return res.status(202).json({ ok: true });
    } catch (error) {
      return serviceUnavailable(res, error);
    }
  };
}

export default createWebsiteEventHandler();
