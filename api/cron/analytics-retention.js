import * as productionDatabase from "../../_db.js";
import { isAuthorizedReportRequest, setPrivateResponseHeaders } from "../../_websiteAnalytics.js";

export function createAnalyticsRetentionHandler(database = productionDatabase, options = { cronSecret: process.env.CRON_SECRET }) {
  return async function handler(req, res) {
    setPrivateResponseHeaders(res);
    if (req.method !== "GET") {
      res.setHeader("Allow", "GET");
      return res.status(405).json({ error: "method not allowed" });
    }
    if (!isAuthorizedReportRequest(req.headers, options.cronSecret)) {
      return res.status(401).json({ error: "unauthorized" });
    }

    try {
      await database.ensureSchema();
      const deleted = await database.deleteExpiredWebsiteEvents(90);
      return res.status(200).json({ ok: true, deleted, retained_days: 90 });
    } catch (error) {
      console.error("website analytics retention failed", productionDatabase.databaseErrorDetails(error));
      return res.status(503).json({ error: "service unavailable" });
    }
  };
}

export default createAnalyticsRetentionHandler();
