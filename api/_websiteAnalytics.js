import crypto from "node:crypto";

const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
const SAFE_PATH_RE = /^\/(?:[A-Za-z0-9._~-]+\/?)*$/;
const OWNER_EXCLUSION_MESSAGE = "openvoiceflow-owner-exclusion:v1";
export const OWNER_EXCLUSION_COOKIE = "ovf_owner_analytics_excluded";
export const OWNER_EXCLUSION_MAX_AGE_MS = 5 * 60 * 1000;

export const ALLOWED_WEBSITE_EVENTS = Object.freeze([
  "page_view",
  "download_click",
  "install_guide_click",
  "navigation_click",
  "hero_cta_click",
  "github_click",
  "demo_play",
  "docs_nav_click",
  "footer_click",
  "copy_click",
  "disclosure_open",
]);

export const ALLOWED_ACQUISITION_SOURCES = Object.freeze([
  "direct", "google_organic", "google_paid", "bing_organic", "github",
  "reddit", "linkedin", "x", "youtube", "newsletter", "chatgpt",
  "perplexity", "claude", "gemini", "copilot", "other_ai", "other",
]);

const EVENT_FIELDS = new Set([
  "eventId", "sessionId", "eventName", "path", "target", "acquisitionSource",
  "campaignId", "recipientToken",
]);

const CAMPAIGN_ID_RE = /^[a-z0-9][a-z0-9_-]{2,63}$/;
const RECIPIENT_TOKEN_RE = /^v1\.[A-Za-z0-9_-]{22}\.[A-Za-z0-9_-]{22}$/;

function campaignTokenMac(campaignId, nonce, secret) {
  if (typeof secret !== "string" || secret.length < 32) return "";
  return crypto
    .createHmac("sha256", secret)
    .update(`openvoiceflow-campaign-attribution:v1:${campaignId}:${nonce}`)
    .digest()
    .subarray(0, 16)
    .toString("base64url");
}

export function createCampaignRecipientToken(campaignId, secret, nonceBytes = crypto.randomBytes(16)) {
  if (!CAMPAIGN_ID_RE.test(String(campaignId || ""))) throw new TypeError("campaignId is invalid");
  if (!Buffer.isBuffer(nonceBytes) || nonceBytes.length !== 16) throw new TypeError("nonce must be 16 random bytes");
  const nonce = nonceBytes.toString("base64url");
  const mac = campaignTokenMac(campaignId, nonce, secret);
  if (!mac) throw new TypeError("campaign attribution secret is invalid");
  return `v1.${nonce}.${mac}`;
}

function isValidCampaignRecipientToken(campaignId, token, secret) {
  if (!RECIPIENT_TOKEN_RE.test(token || "")) return false;
  const [, nonce, suppliedMac] = token.split(".");
  const expectedMac = campaignTokenMac(campaignId, nonce, secret);
  if (!expectedMac) return false;
  const supplied = Buffer.from(suppliedMac, "base64url");
  const expected = Buffer.from(expectedMac, "base64url");
  return supplied.length === expected.length && crypto.timingSafeEqual(supplied, expected);
}

function cleanString(value, maxLength) {
  if (value === null || value === undefined || value === "") return null;
  if (typeof value !== "string") throw new TypeError("event fields must be strings");
  const cleaned = value.trim().replace(/[\u0000-\u001f\u007f]/g, "").slice(0, maxLength);
  return cleaned || null;
}

function cleanWebsitePath(value) {
  const raw = cleanString(value, 240);
  if (!raw) throw new TypeError("path is invalid");
  let path;
  try {
    path = new URL(raw, "https://openvoiceflow.com").pathname;
  } catch {
    throw new TypeError("path is invalid");
  }
  if (!path || path.length > 180 || !SAFE_PATH_RE.test(path)) {
    throw new TypeError("path is invalid");
  }
  return path;
}

function cleanTarget(value, eventName) {
  const target = cleanString(value, 200);

  if (eventName === "download_click") {
    if (!target) throw new TypeError("target is invalid");
    const filename = target.split("/").pop();
    if (!filename || !/^OpenVoiceFlow-[0-9]+\.[0-9]+\.[0-9]+(?:-[A-Za-z0-9._-]+)?\.(?:dmg|zip)$/.test(filename)) {
      throw new TypeError("target is invalid");
    }
    return filename;
  }

  if (["navigation_click", "hero_cta_click", "docs_nav_click", "footer_click"].includes(eventName)) {
    if (!target) throw new TypeError("target is invalid");
    let parsed;
    try {
      parsed = new URL(target, "https://openvoiceflow.com");
    } catch {
      throw new TypeError("target is invalid");
    }
    if (parsed.hostname === "github.com" && parsed.pathname.startsWith("/shimoverse/openvoiceflow")) {
      return "github";
    }
    if (!["openvoiceflow.com", "www.openvoiceflow.com"].includes(parsed.hostname)) {
      throw new TypeError("target is invalid");
    }
    return cleanWebsitePath(parsed.pathname || "/");
  }

  if (eventName === "disclosure_open") {
    if (!target || !/^(?:#[A-Za-z0-9._~-]{1,80}|disclosure-[1-9][0-9]{0,3})$/.test(target)) {
      throw new TypeError("target is invalid");
    }
    return target;
  }

  if (target) throw new TypeError("target is invalid");
  return null;
}

export function normalizeWebsiteEvent(input, options = {}) {
  if (!input || typeof input !== "object" || Array.isArray(input)) {
    throw new TypeError("body must be an object");
  }
  for (const field of Object.keys(input)) {
    if (!EVENT_FIELDS.has(field)) throw new TypeError(`field ${field} is invalid`);
  }

  const eventId = cleanString(input.eventId, 36);
  const sessionId = cleanString(input.sessionId, 36);
  const eventName = cleanString(input.eventName, 48);
  const acquisitionSource = cleanString(input.acquisitionSource, 32) || "direct";
  const campaignId = cleanString(input.campaignId, 64);
  const recipientToken = cleanString(input.recipientToken, 64);

  if (!eventId || !UUID_RE.test(eventId)) throw new TypeError("eventId must be a UUID");
  if (!sessionId || !UUID_RE.test(sessionId)) throw new TypeError("sessionId must be a UUID");
  if (!eventName || !ALLOWED_WEBSITE_EVENTS.includes(eventName)) throw new TypeError("eventName is invalid");
  if (!ALLOWED_ACQUISITION_SOURCES.includes(acquisitionSource)) {
    throw new TypeError("acquisitionSource is invalid");
  }
  if (Boolean(campaignId) !== Boolean(recipientToken)) {
    throw new TypeError("campaign attribution must include both fields");
  }
  if (campaignId && !CAMPAIGN_ID_RE.test(campaignId)) throw new TypeError("campaignId is invalid");
  if (recipientToken && !isValidCampaignRecipientToken(
    campaignId,
    recipientToken,
    options.campaignAttributionSecret
  )) throw new TypeError("recipientToken is invalid");

  const event = {
    eventId,
    sessionId,
    eventName,
    path: cleanWebsitePath(input.path),
    target: cleanTarget(input.target, eventName),
    acquisitionSource,
  };
  if (campaignId) event.campaignId = campaignId;
  if (recipientToken) event.recipientToken = recipientToken;
  return event;
}

function readHeader(headers, name) {
  const value = headers?.[name] ?? headers?.[name.toLowerCase()];
  return Array.isArray(value) ? value[0] : value;
}

export function hasOwnerExclusionCookie(headers) {
  const cookieHeader = String(readHeader(headers, "cookie") || "");
  return cookieHeader.split(";").some((part) => {
    const [name, ...valueParts] = part.trim().split("=");
    return name === OWNER_EXCLUSION_COOKIE && valueParts.join("=") === "1";
  });
}

export function createOwnerExclusionSignature(timestamp, secret) {
  if (!secret || typeof secret !== "string") return "";
  return crypto
    .createHmac("sha256", secret)
    .update(`${OWNER_EXCLUSION_MESSAGE}:${timestamp}`)
    .digest("hex");
}

export function isAuthorizedOwnerExclusion(body, secret, now = Date.now()) {
  if (!body || typeof body !== "object" || Array.isArray(body)) return false;
  const timestamp = String(body.timestamp || "");
  const signature = String(body.signature || "");
  if (!/^\d{13}$/.test(timestamp) || !/^[0-9a-f]{64}$/.test(signature)) return false;

  const issuedAt = Number(timestamp);
  if (!Number.isSafeInteger(issuedAt) || issuedAt > now + 30_000 || now - issuedAt > OWNER_EXCLUSION_MAX_AGE_MS) {
    return false;
  }

  const expected = createOwnerExclusionSignature(timestamp, secret);
  const actualBuffer = Buffer.from(signature, "hex");
  const expectedBuffer = Buffer.from(expected, "hex");
  return actualBuffer.length === expectedBuffer.length
    && crypto.timingSafeEqual(actualBuffer, expectedBuffer);
}

function decodeLocation(value, maxLength) {
  const raw = cleanString(value, maxLength);
  if (!raw) return null;
  try {
    return decodeURIComponent(raw).slice(0, maxLength);
  } catch {
    return raw;
  }
}

export function readEdgeLocation(headers) {
  return {
    country: decodeLocation(readHeader(headers, "x-vercel-ip-country"), 2)?.toUpperCase() ?? null,
    region: decodeLocation(readHeader(headers, "x-vercel-ip-country-region"), 100),
    city: decodeLocation(readHeader(headers, "x-vercel-ip-city"), 100),
  };
}

export function isAuthorizedReportRequest(headers, secret) {
  if (!secret || typeof secret !== "string") return false;
  const supplied = readHeader(headers, "authorization");
  if (typeof supplied !== "string" || !supplied.startsWith("Bearer ")) return false;
  const actual = Buffer.from(supplied.slice(7));
  const expected = Buffer.from(secret);
  return actual.length === expected.length && crypto.timingSafeEqual(actual, expected);
}

export function isSameSiteRequest(headers) {
  const fetchSite = String(readHeader(headers, "sec-fetch-site") || "").toLowerCase();
  if (fetchSite && !["same-origin", "same-site"].includes(fetchSite)) return false;

  const source = readHeader(headers, "origin") || readHeader(headers, "referer");
  if (!source) return fetchSite === "same-origin" || fetchSite === "same-site";
  try {
    return ["openvoiceflow.com", "www.openvoiceflow.com"].includes(new URL(source).hostname);
  } catch {
    return false;
  }
}

export function isAutomatedRequest(headers) {
  const userAgent = String(readHeader(headers, "user-agent") || "");
  const purpose = String(readHeader(headers, "purpose") || readHeader(headers, "sec-purpose") || "");
  return /bot|crawl|spider|slurp|headless|lighthouse|preview/i.test(userAgent)
    || /prefetch|preview/i.test(purpose);
}

export function setPrivateResponseHeaders(res) {
  res.setHeader("Cache-Control", "no-store");
  res.setHeader("X-Content-Type-Options", "nosniff");
  res.setHeader("X-Robots-Tag", "noindex, nofollow, noarchive");
}
