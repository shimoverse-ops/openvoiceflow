import * as productionDatabase from "../_db.js";
import { isAuthorizedReportRequest, setPrivateResponseHeaders } from "../_websiteAnalytics.js";

function requestedDays(value) {
  const days = Number.parseInt(String(value || "30"), 10);
  return [7, 30, 90].includes(days) ? days : 30;
}

export function createAnalyticsReportHandler(
  database = productionDatabase,
  options = { reportToken: process.env.ANALYTICS_REPORT_TOKEN }
) {
  return async function handler(req, res) {
    setPrivateResponseHeaders(res);
    if (req.method !== "GET") {
      res.setHeader("Allow", "GET");
      return res.status(405).json({ error: "method not allowed" });
    }
    if (!isAuthorizedReportRequest(req.headers, options.reportToken)) {
      return res.status(401).json({ error: "unauthorized" });
    }

    const days = requestedDays(req.query?.days);
    try {
      await database.ensureSchema();
      const report = await database.readAnalyticsReport(days);
      return res.status(200).json({
        schema_version: 1,
        generated_at: new Date().toISOString(),
        period_days: days,
        semantics: {
          website_sessions: "Distinct privacy-safe browser visit IDs. A visit rotates after 30 minutes of inactivity and is not a persistent person identifier.",
          website_visitors: "Vercel Web Analytics supplies privacy-preserving visitor totals separately; first-party event tracking does not persist a cross-visit browser ID.",
          app_reporting_installations: "Anonymous installations that opted into leaderboard analytics and successfully synced; not App Store install counts.",
          app_features: "Current aggregate feature state from the latest opt-in installation snapshot, not raw feature-event history.",
          location: "Coarse city, region, and country are derived from Vercel edge headers when available; IP addresses are not stored.",
          clicks: "Allow-listed navigation and product actions only. No raw coordinates, typed text, form values, query strings, or arbitrary DOM text are retained.",
        },
        ...report,
      });
    } catch (error) {
      console.error("analytics report failed", productionDatabase.databaseErrorDetails(error));
      return res.status(503).json({ error: "service unavailable" });
    }
  };
}

export default createAnalyticsReportHandler();
