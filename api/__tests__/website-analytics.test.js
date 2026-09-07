import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";

import {
  createCampaignRecipientToken,
  createOwnerExclusionSignature,
  normalizeWebsiteEvent,
  readEdgeLocation,
  isAuthorizedReportRequest,
} from "../_websiteAnalytics.js";
import { createWebsiteEventHandler } from "../analytics/event.js";
import { createEmailOpenHandler } from "../analytics/email-open.js";
import { createEmailLinkHandler } from "../analytics/email-link.js";
import { createOwnerOptOutHandler } from "../analytics/owner-opt-out.js";
import { createAnalyticsReportHandler } from "../analytics/report.js";
import { createAnalyticsRetentionHandler } from "../cron/analytics-retention.js";

const EVENT_ID = "00000000-0000-4000-8000-000000000001";
const SESSION_ID = "00000000-0000-4000-8000-000000000002";
const CAMPAIGN_SECRET = "test-only-campaign-secret-at-least-32-bytes";

function responseRecorder() {
  return {
    statusCode: 200,
    headers: {},
    body: undefined,
    setHeader(name, value) { this.headers[name.toLowerCase()] = value; },
    status(code) { this.statusCode = code; return this; },
    json(body) { this.body = body; return this; },
    end(body = "") { this.body = body; return this; },
  };
}

async function call(handler, { method = "GET", body = {}, query = {}, headers = {} } = {}) {
  const response = responseRecorder();
  await handler({ method, body, query, headers }, response);
  return response;
}

function pageView(overrides = {}) {
  return {
    eventId: EVENT_ID,
    sessionId: SESSION_ID,
    eventName: "page_view",
    path: "/docs/quickstart.html?private=discarded",
    target: null,
    acquisitionSource: "google_organic",
    ...overrides,
  };
}

test("website events keep only allow-listed metadata and strip query strings", () => {
  assert.deepEqual(normalizeWebsiteEvent(pageView()), {
    eventId: EVENT_ID,
    sessionId: SESSION_ID,
    eventName: "page_view",
    path: "/docs/quickstart.html",
    target: null,
    acquisitionSource: "google_organic",
  });

  assert.throws(
    () => normalizeWebsiteEvent(pageView({ eventName: "raw_click", coordinates: "1,2" })),
    /field coordinates is invalid/
  );
  assert.throws(() => normalizeWebsiteEvent(pageView({ eventName: "raw_click" })), /eventName is invalid/);
  assert.throws(() => normalizeWebsiteEvent(pageView({ sessionId: "person@example.com" })), /sessionId must be a UUID/);
});

test("website events accept only server-verifiable anonymous campaign attribution pairs", () => {
  const recipientToken = createCampaignRecipientToken(
    "creator_outreach_2026_09",
    CAMPAIGN_SECRET,
    Buffer.alloc(16, 7)
  );
  const attributed = normalizeWebsiteEvent(pageView({
    campaignId: "creator_outreach_2026_09",
    recipientToken,
  }), { campaignAttributionSecret: CAMPAIGN_SECRET });
  assert.equal(attributed.campaignId, "creator_outreach_2026_09");
  assert.equal(attributed.recipientToken, recipientToken);

  assert.throws(
    () => normalizeWebsiteEvent(pageView({ recipientToken })),
    /campaign attribution must include both fields/
  );
  assert.throws(
    () => normalizeWebsiteEvent(pageView({ campaignId: "creator_outreach_2026_09" })),
    /campaign attribution must include both fields/
  );
  assert.throws(
    () => normalizeWebsiteEvent(pageView({
      campaignId: "Creator Outreach / September",
      recipientToken,
    }), { campaignAttributionSecret: CAMPAIGN_SECRET }),
    /campaignId is invalid/
  );
  assert.throws(
    () => normalizeWebsiteEvent(pageView({
      campaignId: "creator_outreach_2026_09",
      recipientToken: "YWxpY2VAZXhhbXBsZS5jb20",
    }), { campaignAttributionSecret: CAMPAIGN_SECRET }),
    /recipientToken is invalid/
  );
  assert.throws(
    () => normalizeWebsiteEvent(pageView({
      campaignId: "creator_outreach_2026_09",
      recipientToken: createCampaignRecipientToken("different_campaign", CAMPAIGN_SECRET, Buffer.alloc(16, 7)),
    }), { campaignAttributionSecret: CAMPAIGN_SECRET }),
    /recipientToken is invalid/
  );
});

test("event endpoint rejects unissued campaign attribution before database access", async () => {
  let databaseCalls = 0;
  const handler = createWebsiteEventHandler({
    async ensureSchema() { databaseCalls += 1; },
    async insertWebsiteEvent() { databaseCalls += 1; },
  }, { campaignAttributionSecret: CAMPAIGN_SECRET });
  const response = await call(handler, {
    method: "POST",
    body: pageView({
      campaignId: "creator_outreach_2026_09",
      recipientToken: "YWxpY2VAZXhhbXBsZS5jb20",
    }),
    headers: {
      origin: "https://openvoiceflow.com",
      "sec-fetch-site": "same-origin",
      "user-agent": "Mozilla/5.0 Safari/605.1.15",
    },
  });
  assert.equal(response.statusCode, 400);
  assert.equal(databaseCalls, 0);
});

test("event endpoint fails closed for attributed events when the campaign secret is absent", async () => {
  let databaseCalls = 0;
  const recipientToken = createCampaignRecipientToken(
    "creator_outreach_2026_09",
    CAMPAIGN_SECRET,
    Buffer.alloc(16, 7)
  );
  const handler = createWebsiteEventHandler({
    async ensureSchema() { databaseCalls += 1; },
    async insertWebsiteEvent() { databaseCalls += 1; },
  }, { campaignAttributionSecret: undefined });
  const response = await call(handler, {
    method: "POST",
    body: pageView({
      campaignId: "creator_outreach_2026_09",
      recipientToken,
    }),
    headers: {
      origin: "https://openvoiceflow.com",
      "sec-fetch-site": "same-origin",
      "user-agent": "Mozilla/5.0 Safari/605.1.15",
    },
  });
  assert.equal(response.statusCode, 400);
  assert.equal(databaseCalls, 0);
});

test("privacy disclosure explains anonymous outreach attribution", () => {
  const privacy = readFileSync(new URL("../../docs/privacy.html", import.meta.url), "utf8");
  assert.match(privacy, /opaque campaign and recipient tokens/i);
  assert.match(privacy, /never contain.*name.*email address/i);
  assert.match(privacy, /open detected/i);
  assert.match(privacy, /image prox(?:y|ies)|preload/i);
  assert.match(privacy, /first-party redirect/i);
});

test("email open endpoint records only a privacy-safe open detection and returns a transparent pixel", async () => {
  const recipientToken = createCampaignRecipientToken(
    "creator_outreach_2026_09",
    CAMPAIGN_SECRET,
    Buffer.alloc(16, 8)
  );
  const inserted = [];
  const handler = createEmailOpenHandler({
    async ensureSchema() {},
    async insertWebsiteEvent(event) { inserted.push(event); },
  }, { campaignAttributionSecret: CAMPAIGN_SECRET });

  const response = await call(handler, {
    query: { c: "creator_outreach_2026_09", r: recipientToken },
    headers: { "user-agent": "Mozilla/5.0" },
  });

  assert.equal(response.statusCode, 200);
  assert.equal(response.headers["content-type"], "image/gif");
  assert.equal(response.headers["referrer-policy"], "no-referrer");
  assert.ok(Buffer.isBuffer(response.body));
  assert.equal(inserted.length, 1);
  assert.equal(inserted[0].eventName, "email_open_detected");
  assert.equal(inserted[0].path, "/email");
  assert.equal(inserted[0].campaignId, "creator_outreach_2026_09");
  assert.equal(inserted[0].recipientToken, recipientToken);
  assert.deepEqual(inserted[0].location, { country: null, region: null, city: null });
});

test("email open endpoint honors privacy signals and ignores automation without breaking the pixel", async () => {
  const recipientToken = createCampaignRecipientToken(
    "creator_outreach_2026_09",
    CAMPAIGN_SECRET,
    Buffer.alloc(16, 9)
  );
  let databaseCalls = 0;
  const handler = createEmailOpenHandler({
    async ensureSchema() { databaseCalls += 1; },
    async insertWebsiteEvent() { databaseCalls += 1; },
  }, { campaignAttributionSecret: CAMPAIGN_SECRET });

  for (const headers of [
    { "sec-gpc": "1", "user-agent": "Mozilla/5.0" },
    { dnt: "1", "user-agent": "Mozilla/5.0" },
    { "user-agent": "Googlebot" },
    { purpose: "prefetch", "user-agent": "Mozilla/5.0" },
  ]) {
    const response = await call(handler, {
      query: { c: "creator_outreach_2026_09", r: recipientToken },
      headers,
    });
    assert.equal(response.statusCode, 200);
    assert.equal(response.headers["content-type"], "image/gif");
  }
  assert.equal(databaseCalls, 0);
});

test("email link endpoint records allow-listed clicks and redirects without leaking a referrer", async () => {
  const recipientToken = createCampaignRecipientToken(
    "creator_outreach_2026_09",
    CAMPAIGN_SECRET,
    Buffer.alloc(16, 10)
  );
  const inserted = [];
  const handler = createEmailLinkHandler({
    async ensureSchema() {},
    async insertWebsiteEvent(event) { inserted.push(event); },
  }, { campaignAttributionSecret: CAMPAIGN_SECRET });

  const demo = await call(handler, {
    query: { c: "creator_outreach_2026_09", r: recipientToken, to: "demo" },
    headers: { "user-agent": "Mozilla/5.0" },
  });
  assert.equal(demo.statusCode, 302);
  assert.equal(demo.headers.location, "https://www.youtube.com/watch?v=tWDLtZolv0A");
  assert.equal(demo.headers["referrer-policy"], "no-referrer");
  assert.equal(inserted[0].eventName, "email_demo_click");
  assert.equal(inserted[0].target, "youtube_demo");

  const site = await call(handler, {
    query: { c: "creator_outreach_2026_09", r: recipientToken, to: "site" },
    headers: { "user-agent": "Mozilla/5.0" },
  });
  assert.equal(site.statusCode, 302);
  assert.equal(site.headers.location, `https://openvoiceflow.com/?utm_source=creator_outreach&utm_medium=email&utm_campaign=creator_outreach_2026_09&ovf_r=${encodeURIComponent(recipientToken)}`);
  assert.equal(inserted[1].eventName, "email_site_click");
  assert.equal(inserted[1].target, "website");
});

test("email links still reach allow-listed destinations when tracking is opted out", async () => {
  const recipientToken = createCampaignRecipientToken(
    "creator_outreach_2026_09",
    CAMPAIGN_SECRET,
    Buffer.alloc(16, 11)
  );
  let databaseCalls = 0;
  const handler = createEmailLinkHandler({
    async ensureSchema() { databaseCalls += 1; },
    async insertWebsiteEvent() { databaseCalls += 1; },
  }, { campaignAttributionSecret: CAMPAIGN_SECRET });

  const response = await call(handler, {
    query: { c: "creator_outreach_2026_09", r: recipientToken, to: "demo" },
    headers: { dnt: "1", "user-agent": "Mozilla/5.0" },
  });
  assert.equal(response.statusCode, 302);
  assert.equal(response.headers.location, "https://www.youtube.com/watch?v=tWDLtZolv0A");
  assert.equal(databaseCalls, 0);

  for (const headers of [
    { dnt: "1", "user-agent": "Mozilla/5.0" },
    { "sec-gpc": "1", "user-agent": "Mozilla/5.0" },
    { "user-agent": "Googlebot" },
  ]) {
    const site = await call(handler, {
      query: { c: "creator_outreach_2026_09", r: recipientToken, to: "site" },
      headers,
    });
    assert.equal(site.statusCode, 302);
    assert.equal(site.headers.location, "https://openvoiceflow.com/");
  }
  assert.equal(databaseCalls, 0);
});

test("email site redirect never propagates malformed or unverifiable attribution", async () => {
  let databaseCalls = 0;
  const database = {
    async ensureSchema() { databaseCalls += 1; },
    async insertWebsiteEvent() { databaseCalls += 1; },
  };
  const handler = createEmailLinkHandler(database, { campaignAttributionSecret: CAMPAIGN_SECRET });
  for (const query of [
    { to: "site" },
    { to: "site", c: "creator_outreach_2026_09", r: "person@example.com" },
    { to: "site", c: "person@example.com", r: "not-a-token" },
  ]) {
    const response = await call(handler, { query, headers: { "user-agent": "Mozilla/5.0" } });
    assert.equal(response.statusCode, 302);
    assert.equal(response.headers.location, "https://openvoiceflow.com/");
  }

  const recipientToken = createCampaignRecipientToken(
    "creator_outreach_2026_09",
    CAMPAIGN_SECRET,
    Buffer.alloc(16, 12)
  );
  const missingSecretHandler = createEmailLinkHandler(database, { campaignAttributionSecret: "" });
  const missingSecret = await call(missingSecretHandler, {
    query: { to: "site", c: "creator_outreach_2026_09", r: recipientToken },
    headers: { "user-agent": "Mozilla/5.0" },
  });
  assert.equal(missingSecret.statusCode, 302);
  assert.equal(missingSecret.headers.location, "https://openvoiceflow.com/");
  assert.equal(databaseCalls, 0);
});

test("canonical database schema preserves campaign attribution as an all-or-nothing pair", () => {
  const schema = readFileSync(new URL("../../db/schema.sql", import.meta.url), "utf8");
  const databaseSource = readFileSync(new URL("../_db.js", import.meta.url), "utf8");
  assert.match(schema, /campaign_id\s+TEXT/);
  assert.match(schema, /recipient_token\s+TEXT/);
  assert.match(
    schema,
    /CHECK\s*\(\s*\(campaign_id IS NULL AND recipient_token IS NULL\)\s*OR\s*\(campaign_id IS NOT NULL AND recipient_token IS NOT NULL\)\s*\)/i
  );
  assert.match(
    databaseSource,
    /SELECT MAX\(created_at\)::text FROM website_events\s+WHERE event_name NOT LIKE 'email_%'/,
    "ordinary website last-event reporting must exclude email signals"
  );
});

test("click events require safe targets and never retain arbitrary link text", () => {
  const click = normalizeWebsiteEvent(pageView({
    eventName: "navigation_click",
    path: "/",
    target: "https://openvoiceflow.com/docs/quickstart.html?email=discarded",
  }));
  assert.equal(click.target, "/docs/quickstart.html");

  assert.throws(
    () => normalizeWebsiteEvent(pageView({ eventName: "navigation_click", target: "https://example.com/private" })),
    /target is invalid/
  );
  assert.throws(
    () => normalizeWebsiteEvent(pageView({ eventName: "download_click", target: "../../secret.txt" })),
    /target is invalid/
  );

  const footer = normalizeWebsiteEvent(pageView({
    eventName: "footer_click",
    target: "https://openvoiceflow.com/privacy.html?source=discarded",
  }));
  assert.equal(footer.target, "/privacy.html");
  assert.equal(normalizeWebsiteEvent(pageView({ eventName: "copy_click", target: null })).target, null);
  assert.equal(
    normalizeWebsiteEvent(pageView({ eventName: "disclosure_open", target: "#v0.5.22" })).target,
    "#v0.5.22"
  );
  assert.equal(
    normalizeWebsiteEvent(pageView({ eventName: "disclosure_open", target: "disclosure-12" })).target,
    "disclosure-12"
  );
  assert.throws(
    () => normalizeWebsiteEvent(pageView({ eventName: "disclosure_open", target: "the user said something private" })),
    /target is invalid/
  );
});

test("edge location uses coarse Vercel headers and no IP address", () => {
  const location = readEdgeLocation({
    "x-vercel-ip-country": "us",
    "x-vercel-ip-country-region": "CA",
    "x-vercel-ip-city": "San%20Francisco",
    "x-forwarded-for": "203.0.113.10",
  });
  assert.deepEqual(location, { country: "US", region: "CA", city: "San Francisco" });
  assert.equal(Object.hasOwn(location, "ip"), false);
});

test("event endpoint records same-site human events with server-derived location", async () => {
  const inserted = [];
  const database = {
    async ensureSchema() {},
    async insertWebsiteEvent(event) { inserted.push(event); },
  };
  const handler = createWebsiteEventHandler(database);
  const response = await call(handler, {
    method: "POST",
    body: pageView(),
    headers: {
      origin: "https://openvoiceflow.com",
      "sec-fetch-site": "same-origin",
      "user-agent": "Mozilla/5.0 Safari/605.1.15",
      "x-vercel-ip-country": "US",
      "x-vercel-ip-country-region": "CA",
      "x-vercel-ip-city": "Tracy",
    },
  });

  assert.equal(response.statusCode, 202);
  assert.deepEqual(response.body, { ok: true });
  assert.equal(inserted.length, 1);
  assert.equal(inserted[0].sessionId, SESSION_ID);
  assert.deepEqual(inserted[0].location, { country: "US", region: "CA", city: "Tracy" });
  assert.match(response.headers["cache-control"], /no-store/);
});

test("event endpoint ignores an owner browser without storing or comparing IP addresses", async () => {
  let databaseCalls = 0;
  const handler = createWebsiteEventHandler({
    async ensureSchema() { databaseCalls += 1; },
    async insertWebsiteEvent() { databaseCalls += 1; },
  });
  const response = await call(handler, {
    method: "POST",
    body: pageView(),
    headers: {
      origin: "https://openvoiceflow.com",
      "sec-fetch-site": "same-origin",
      cookie: "theme=dark; ovf_owner_analytics_excluded=1",
      "x-forwarded-for": "203.0.113.10",
    },
  });

  assert.equal(response.statusCode, 202);
  assert.deepEqual(response.body, { ok: true, ignored: true });
  assert.equal(databaseCalls, 0);
});

test("owner opt-out requires a fresh dashboard-signed POST and sets a first-party HttpOnly cookie", async () => {
  const secret = "report-secret";
  const now = 1_800_000_000_000;
  const timestamp = String(now);
  const signature = createOwnerExclusionSignature(timestamp, secret);
  const handler = createOwnerOptOutHandler({ secret, now: () => now });

  let response = await call(handler, {
    method: "GET",
    body: { timestamp, signature },
    headers: { origin: "https://openvoiceflow-analytics.vercel.app" },
  });
  assert.equal(response.statusCode, 405);

  response = await call(handler, {
    method: "POST",
    body: { timestamp, signature },
    headers: { origin: "https://example.com" },
  });
  assert.equal(response.statusCode, 403);

  response = await call(handler, {
    method: "POST",
    body: { timestamp, signature: `${signature}0` },
    headers: { origin: "https://openvoiceflow-analytics.vercel.app" },
  });
  assert.equal(response.statusCode, 403);

  response = await call(handler, {
    method: "POST",
    body: { timestamp, signature },
    headers: { origin: "https://openvoiceflow-analytics.vercel.app" },
  });
  assert.equal(response.statusCode, 303);
  assert.equal(response.headers.location, "https://openvoiceflow-analytics.vercel.app/?owner_excluded=1");
  assert.match(response.headers["set-cookie"], /^ovf_owner_analytics_excluded=1;/);
  assert.match(response.headers["set-cookie"], /Max-Age=31536000/);
  assert.match(response.headers["set-cookie"], /HttpOnly/);
  assert.match(response.headers["set-cookie"], /Secure/);
  assert.match(response.headers["set-cookie"], /SameSite=Lax/);
  assert.doesNotMatch(response.headers["set-cookie"], /Domain=/);
});

test("event endpoint rejects cross-site, bot, and malformed events", async () => {
  const database = {
    async ensureSchema() {},
    async insertWebsiteEvent() { throw new Error("must not insert"); },
  };
  const handler = createWebsiteEventHandler(database);

  const crossSite = await call(handler, {
    method: "POST",
    body: pageView(),
    headers: { origin: "https://example.com", "user-agent": "Mozilla/5.0" },
  });
  assert.equal(crossSite.statusCode, 403);

  const bot = await call(handler, {
    method: "POST",
    body: pageView(),
    headers: { origin: "https://openvoiceflow.com", "user-agent": "Googlebot" },
  });
  assert.equal(bot.statusCode, 202);
  assert.deepEqual(bot.body, { ok: true, ignored: true });

  const malformed = await call(handler, {
    method: "POST",
    body: pageView({ path: "/docs/<script>" }),
    headers: { origin: "https://openvoiceflow.com", "user-agent": "Mozilla/5.0" },
  });
  assert.equal(malformed.statusCode, 400);
});

test("report endpoint is bearer-protected and returns aggregate-only semantics", async () => {
  const report = {
    website: {
      summary: { sessions: 3, pageviews: 7, clicks: 2, pages_per_session: 2.33, bounce_rate: 33.3 },
      paths: [{ path: "/", pageviews: 4, sessions: 2 }],
      clicks: [{ event_name: "download_click", path: "/download.html", target: "OpenVoiceFlow-0.5.21.dmg", clicks: 2, sessions: 2 }],
      locations: [{ country: "US", region: "CA", city: "Tracy", sessions: 2, events: 5 }],
    },
    app: {
      summary: { reporting_installations: 5, active_30d: 5 },
      features: [{ feature: "AI cleanup", reporting_installations: 3 }],
    },
  };
  const database = {
    async ensureSchema() {},
    async readAnalyticsReport(days) { assert.equal(days, 30); return report; },
  };
  const handler = createAnalyticsReportHandler(database, { reportToken: "report-secret" });

  let response = await call(handler, { headers: {} });
  assert.equal(response.statusCode, 401);

  response = await call(handler, {
    headers: { authorization: "Bearer report-secret" },
    query: { days: "30" },
  });
  assert.equal(response.statusCode, 200);
  assert.equal(response.body.period_days, 30);
  assert.equal(response.body.website.summary.sessions, 3);
  assert.equal(response.body.app.features[0].feature, "AI cleanup");
  assert.match(response.body.semantics.location, /IP addresses are not stored/);
  assert.match(response.headers["x-robots-tag"], /noindex/);
});

test("report authorization uses exact bearer token matching", () => {
  assert.equal(isAuthorizedReportRequest({ authorization: "Bearer secret" }, "secret"), true);
  assert.equal(isAuthorizedReportRequest({ authorization: "Bearer secretx" }, "secret"), false);
  assert.equal(isAuthorizedReportRequest({}, "secret"), false);
  assert.equal(isAuthorizedReportRequest({ authorization: "Bearer secret" }, ""), false);
});

test("retention endpoint enforces method and exact cron bearer token", async () => {
  let deleted = false;
  const database = {
    async ensureSchema() {},
    async deleteExpiredWebsiteEvents(days) { deleted = true; assert.equal(days, 90); return 4; },
  };
  const handler = createAnalyticsRetentionHandler(database, { cronSecret: "cron-secret" });

  let response = await call(handler, { method: "POST", headers: { authorization: "Bearer cron-secret" } });
  assert.equal(response.statusCode, 405);
  assert.equal(deleted, false);

  response = await call(handler, { headers: { authorization: "Bearer wrong" } });
  assert.equal(response.statusCode, 401);
  assert.equal(deleted, false);

  response = await call(handler, { headers: { authorization: "Bearer cron-secret" } });
  assert.equal(response.statusCode, 200);
  assert.deepEqual(response.body, { ok: true, deleted: 4, retained_days: 90 });
  assert.equal(deleted, true);
});

test("retention endpoint fails closed when deletion fails", async () => {
  const database = {
    async ensureSchema() {},
    async deleteExpiredWebsiteEvents() { throw new Error("database unavailable"); },
  };
  const handler = createAnalyticsRetentionHandler(database, { cronSecret: "cron-secret" });
  const originalError = console.error;
  console.error = () => {};
  try {
    const response = await call(handler, { headers: { authorization: "Bearer cron-secret" } });
    assert.equal(response.statusCode, 503);
    assert.deepEqual(response.body, { error: "service unavailable" });
  } finally {
    console.error = originalError;
  }
});
