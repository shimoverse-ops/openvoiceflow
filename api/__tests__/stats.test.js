import assert from "node:assert/strict";
import { test } from "node:test";

import { createIngestHandler } from "../analytics/ingest.js";
import { createStatsHandler } from "../analytics/stats.js";
import { MemoryDatabase } from "./memory-database.js";

const ID_A = "00000000-0000-4000-8000-000000000001";
const ID_B = "00000000-0000-4000-8000-000000000002";
const TOKEN = "test-token-that-is-long-enough";

function responseRecorder() {
  return {
    statusCode: 200,
    headers: {},
    body: undefined,
    setHeader(name, value) {
      this.headers[name] = value;
    },
    status(code) {
      this.statusCode = code;
      return this;
    },
    json(body) {
      this.body = body;
      return this;
    },
  };
}

function getRequest(token, query = {}) {
  return { method: "GET", query, headers: token ? { authorization: `Bearer ${token}` } : {} };
}

async function seed(database, devices) {
  const ingest = createIngestHandler(database);
  for (const device of devices) {
    const res = responseRecorder();
    await ingest({ method: "POST", query: {}, headers: {}, body: device }, res);
    assert.equal(res.statusCode, 200, JSON.stringify(res.body));
  }
}

test("stats stays dark when no token is configured", async () => {
  const handler = createStatsHandler(new MemoryDatabase(), {});
  const res = responseRecorder();
  await handler(getRequest(TOKEN), res);
  // 404, not 401: an unconfigured deployment should not advertise the route.
  assert.equal(res.statusCode, 404);
});

test("stats rejects a missing or wrong token", async () => {
  const handler = createStatsHandler(new MemoryDatabase(), { ANALYTICS_STATS_TOKEN: TOKEN });

  const missing = responseRecorder();
  await handler(getRequest(null), missing);
  assert.equal(missing.statusCode, 401);

  const wrong = responseRecorder();
  await handler(getRequest("not-the-token-but-long"), wrong);
  assert.equal(wrong.statusCode, 401);

  // A token that is a prefix of the real one must not pass either.
  const prefix = responseRecorder();
  await handler(getRequest(TOKEN.slice(0, -1)), prefix);
  assert.equal(prefix.statusCode, 401);
});

test("stats refuses a short token as unconfigured", async () => {
  const handler = createStatsHandler(new MemoryDatabase(), { ANALYTICS_STATS_TOKEN: "short" });
  const res = responseRecorder();
  await handler(getRequest("short"), res);
  assert.equal(res.statusCode, 404);
});

test("stats counts installs and aggregates in-app counters", async () => {
  const database = new MemoryDatabase();
  await seed(database, [
    {
      deviceId: ID_A,
      displayName: "Otter 42",
      appVersion: "0.5.21",
      featureUsage: { cleanupEnabled: true, snippetsCount: 3, dictionaryCount: 0, hasKnowMeProfile: true },
      events: { "pane.home": 10, "pane.settings": 4, "action.dictation_completed": 120 },
    },
    {
      deviceId: ID_B,
      displayName: "Heron 11",
      appVersion: "0.5.20",
      featureUsage: { cleanupEnabled: false, snippetsCount: 0, dictionaryCount: 7, hasKnowMeProfile: false },
      events: { "pane.home": 5, "action.dictation_completed": 30 },
    },
  ]);

  const handler = createStatsHandler(database, { ANALYTICS_STATS_TOKEN: TOKEN });
  const res = responseRecorder();
  await handler(getRequest(TOKEN), res);

  assert.equal(res.statusCode, 200);
  assert.equal(res.body.version, 1);
  assert.equal(res.body.totals.installs, 2);
  assert.equal(res.headers["Cache-Control"], "no-store, private");

  const events = Object.fromEntries(res.body.events.map((row) => [row.key, row]));
  assert.equal(events["action.dictation_completed"].total, 150);
  assert.equal(events["action.dictation_completed"].devices, 2);
  assert.equal(events["pane.settings"].devices, 1);

  assert.deepEqual(res.body.features, {
    cleanupEnabled: 1,
    usesSnippets: 1,
    usesDictionary: 1,
    hasKnowMeProfile: 1,
  });
  assert.deepEqual(res.body.versions.map((row) => row.key).sort(), ["0.5.20", "0.5.21"]);

  // Aggregate only: nothing that identifies a device may appear anywhere.
  const serialized = JSON.stringify(res.body);
  assert.ok(!serialized.includes(ID_A));
  assert.ok(!serialized.includes("Otter 42"));
});

test("ingest drops unknown or malformed counter names", async () => {
  const database = new MemoryDatabase();
  await seed(database, [
    {
      deviceId: ID_A,
      displayName: "Otter 42",
      events: {
        "pane.home": 3,
        // An attacker-supplied key is the one way dictated text could reach
        // this table. The allowlist is what stops it.
        "the user said something private": 9,
        "pane.home; DROP TABLE devices": 1,
        "action.dictation_completed": "many",
        "pane.settings": -4,
      },
    },
  ]);

  const handler = createStatsHandler(database, { ANALYTICS_STATS_TOKEN: TOKEN });
  const res = responseRecorder();
  await handler(getRequest(TOKEN), res);

  assert.deepEqual(res.body.events.map((row) => row.key), ["pane.home"]);
});

test("stats rejects non-GET methods", async () => {
  const handler = createStatsHandler(new MemoryDatabase(), { ANALYTICS_STATS_TOKEN: TOKEN });
  const res = responseRecorder();
  await handler({ method: "POST", query: {}, headers: { authorization: `Bearer ${TOKEN}` } }, res);
  assert.equal(res.statusCode, 405);
  assert.equal(res.headers.Allow, "GET");
});
