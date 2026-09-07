import * as productionDatabase from "../_db.js";
import {
  createEmailCampaignEvent,
  isAutomatedRequest,
  isPrivacyOptOutRequest,
  isValidCampaignRecipientToken,
  setPrivateResponseHeaders,
} from "../_websiteAnalytics.js";

const DEMO_URL = "https://www.youtube.com/watch?v=tWDLtZolv0A";

function attributionIsAllowed(req, secret) {
  if (isPrivacyOptOutRequest(req.headers) || isAutomatedRequest(req.headers)) return false;
  return isValidCampaignRecipientToken(
    String(req.query?.c || ""),
    String(req.query?.r || ""),
    secret
  );
}

function destination(query, includeAttribution) {
  if (query?.to === "demo") {
    return { url: DEMO_URL, eventName: "email_demo_click", target: "youtube_demo" };
  }
  if (query?.to === "site") {
    if (!includeAttribution) {
      return { url: "https://openvoiceflow.com/", eventName: "email_site_click", target: "website" };
    }
    const campaignId = String(query?.c || "");
    const recipientToken = String(query?.r || "");
    const params = new URLSearchParams({
      utm_source: "creator_outreach",
      utm_medium: "email",
      utm_campaign: campaignId,
      ovf_r: recipientToken,
    });
    return {
      url: `https://openvoiceflow.com/?${params.toString()}`,
      eventName: "email_site_click",
      target: "website",
    };
  }
  return null;
}

async function recordClick(req, route, database, options) {
  let event;
  try {
    event = createEmailCampaignEvent({
      campaignId: String(req.query?.c || ""),
      recipientToken: String(req.query?.r || ""),
      eventName: route.eventName,
      target: route.target,
    }, options.campaignAttributionSecret);
  } catch {
    return;
  }
  try {
    await database.ensureSchema();
    await database.insertWebsiteEvent(event);
  } catch (error) {
    console.error("email link analytics failed", productionDatabase.databaseErrorDetails(error));
  }
}

export function createEmailLinkHandler(
  database = productionDatabase,
  options = { campaignAttributionSecret: process.env.ANALYTICS_CAMPAIGN_SECRET }
) {
  return async function handler(req, res) {
    setPrivateResponseHeaders(res);
    res.setHeader("Referrer-Policy", "no-referrer");
    if (req.method !== "GET") {
      res.setHeader("Allow", "GET");
      return res.status(405).end();
    }
    const mayRecord = attributionIsAllowed(req, options.campaignAttributionSecret);
    const route = destination(req.query, mayRecord);
    if (!route) return res.status(404).end();
    if (mayRecord) await recordClick(req, route, database, options);
    res.setHeader("Location", route.url);
    return res.status(302).end();
  };
}

export default createEmailLinkHandler();
