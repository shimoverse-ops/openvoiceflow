import {
  isAuthorizedOwnerExclusion,
  OWNER_EXCLUSION_COOKIE,
  setPrivateResponseHeaders,
} from "../_websiteAnalytics.js";

const DASHBOARD_ORIGIN = "https://openvoiceflow-analytics.vercel.app";
const RETURN_URL = `${DASHBOARD_ORIGIN}/?owner_excluded=1`;

function parseBody(body) {
  if (body && typeof body === "object" && !Array.isArray(body)) return body;
  if (typeof body !== "string") return {};
  return Object.fromEntries(new URLSearchParams(body));
}

export function createOwnerOptOutHandler({
  secret = process.env.ANALYTICS_REPORT_TOKEN,
  now = Date.now,
} = {}) {
  return async function handler(req, res) {
    setPrivateResponseHeaders(res);
    if (req.method !== "POST") {
      res.setHeader("Allow", "POST");
      return res.status(405).json({ error: "method not allowed" });
    }
    if (req.headers?.origin !== DASHBOARD_ORIGIN) {
      return res.status(403).json({ error: "forbidden" });
    }
    if (!isAuthorizedOwnerExclusion(parseBody(req.body), secret, now())) {
      return res.status(403).json({ error: "forbidden" });
    }

    res.setHeader(
      "Set-Cookie",
      `${OWNER_EXCLUSION_COOKIE}=1; Max-Age=31536000; Path=/; HttpOnly; Secure; SameSite=Lax`
    );
    res.setHeader("Location", RETURN_URL);
    return res.status(303).end();
  };
}

export default createOwnerOptOutHandler();
