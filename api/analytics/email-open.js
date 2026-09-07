import * as productionDatabase from "../_db.js";
import {
  createEmailCampaignEvent,
  isAutomatedRequest,
  isPrivacyOptOutRequest,
  setPrivateResponseHeaders,
} from "../_websiteAnalytics.js";

const TRANSPARENT_GIF = Buffer.from(
  "R0lGODlhAQABAIAAAAAAAP///ywAAAAAAQABAAACAUwAOw==",
  "base64"
);

async function recordOpen(req, database, options) {
  if (isPrivacyOptOutRequest(req.headers) || isAutomatedRequest(req.headers)) return;
  let event;
  try {
    event = createEmailCampaignEvent({
      campaignId: String(req.query?.c || ""),
      recipientToken: String(req.query?.r || ""),
      eventName: "email_open_detected",
      target: null,
    }, options.campaignAttributionSecret);
  } catch {
    return;
  }
  try {
    await database.ensureSchema();
    await database.insertWebsiteEvent(event);
  } catch (error) {
    console.error("email open analytics failed", productionDatabase.databaseErrorDetails(error));
  }
}

export function createEmailOpenHandler(
  database = productionDatabase,
  options = { campaignAttributionSecret: process.env.ANALYTICS_CAMPAIGN_SECRET }
) {
  return async function handler(req, res) {
    setPrivateResponseHeaders(res);
    res.setHeader("Content-Type", "image/gif");
    res.setHeader("Content-Length", String(TRANSPARENT_GIF.length));
    res.setHeader("Referrer-Policy", "no-referrer");
    if (req.method !== "GET") {
      res.setHeader("Allow", "GET");
      return res.status(405).end();
    }
    await recordOpen(req, database, options);
    return res.status(200).end(TRANSPARENT_GIF);
  };
}

export default createEmailOpenHandler();
