import assert from "node:assert/strict";
import { test } from "node:test";

import {
  normalizeWebsiteEvent,
  readEdgeLocation,
  isAuthorizedReportRequest,
} from "../_websiteAnalytics.js";
import { createWebsiteEventHandler } from "../analytics/event.js";
import { createAnalyticsReportHandler } from "../analytics/report.js";

const EVENT_ID = "00000000-0000-4000-8000-000000000001";
const SESSION_ID = "00000000-0000-4000-8000-000000000002";

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
