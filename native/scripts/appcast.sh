#!/usr/bin/env bash
#
# Generate the Sparkle appcast entry for a freshly built DMG.
#
# Sparkle refuses unsigned updates, so each DMG is signed with the EdDSA
# private key (the public half lives in Info.plist as SUPublicEDKey). This
# emits native/dist/appcast.xml pointing at the website-hosted DMG.
#
# Env:
#   OVF_VERSION            marketing version (e.g. 0.4.0)          [required]
#   OVF_BUILD              CFBundleVersion / sparkle:version       [default: read from Info.plist]
#   SPARKLE_ED_PRIVATE_KEY the exported EdDSA private key string   [REQUIRED — fails if unset]
#   OVF_DOWNLOAD_BASE      URL prefix the DMG will be served from
#                          [default https://openvoiceflow.com/downloads]
#   OVF_SITE_BASE          website root the release-notes links point at
#                          [default https://openvoiceflow.com]
#   SPARKLE_VERSION        Sparkle release to pull sign_update from [default 2.9.4]
#
# REQUIRED for a release: fails loudly if SPARKLE_ED_PRIVATE_KEY is unset, since
# shipping a DMG without a signed appcast silently breaks in-app updates.
#
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"   # native/
cd "$HERE"

if [[ -z "${SPARKLE_ED_PRIVATE_KEY:-}" ]]; then
  echo "::error::SPARKLE_ED_PRIVATE_KEY is required — a release without a signed appcast silently breaks in-app updates for every user."
  exit 1
fi

: "${OVF_VERSION:?set OVF_VERSION}"
# Sparkle orders updates by CFBundleVersion (sparkle:version) — read the real
# build number from Info.plist so it increments every release, or Sparkle won't
# see a new build as newer.
BUILD="${OVF_BUILD:-$(/usr/libexec/PlistBuddy -c 'Print :CFBundleVersion' Info.plist 2>/dev/null || echo 1)}"
DOWNLOAD_BASE="${OVF_DOWNLOAD_BASE:-https://openvoiceflow.com/downloads}"
# The feed's own URL — must match Info.plist SUFeedURL (served at the site root).
FEED_URL="${OVF_APPCAST_URL:-https://openvoiceflow.com/appcast.xml}"
# Where the website is served from. Sparkle reads two release-notes links off
# the item: releaseNotesLink fills the WebView in the update sheet, and
# fullReleaseNotesLink is what the "Version History" button opens — including
# on the "You're up to date!" alert, which is the only place a current user
# ever sees it. Both must be real pages; build_releases.py in the private site
# repo generates them from this repo's CHANGELOG.md, so the changelog entry has
# to land before this appcast goes live (RELEASE.md).
SITE_BASE="${OVF_SITE_BASE:-https://openvoiceflow.com}"
SPARKLE_VERSION="${SPARKLE_VERSION:-2.9.4}"

DMG="dist/OpenVoiceFlow-$OVF_VERSION.dmg"
[[ -f "$DMG" ]] || { echo "::error::missing $DMG (run build-app.sh first)"; exit 1; }

# ── fetch Sparkle's sign_update tool ────────────────────────────────────────
TOOLS="build/sparkle-tools"
if [[ ! -x "$TOOLS/bin/sign_update" ]]; then
  mkdir -p "$TOOLS"
  URL="https://github.com/sparkle-project/Sparkle/releases/download/$SPARKLE_VERSION/Sparkle-$SPARKLE_VERSION.tar.xz"
  echo "▸ Fetching Sparkle tools $SPARKLE_VERSION"
  curl -fsSL "$URL" | tar -xJ -C "$TOOLS"
fi
SIGN_UPDATE="$TOOLS/bin/sign_update"
[[ -x "$SIGN_UPDATE" ]] || { echo "::error::sign_update not found in Sparkle tarball"; exit 1; }

# ── sign the DMG ────────────────────────────────────────────────────────────
KEY_FILE="build/sparkle_ed_private_key"
printf '%s' "$SPARKLE_ED_PRIVATE_KEY" > "$KEY_FILE"
chmod 600 "$KEY_FILE"
# sign_update prints: sparkle:edSignature="…" length="…"
SIG_ATTRS="$("$SIGN_UPDATE" "$DMG" -f "$KEY_FILE")"
rm -f "$KEY_FILE"

PUBDATE="$(date -u '+%a, %d %b %Y %H:%M:%S +0000')"
DMG_NAME="OpenVoiceFlow-$OVF_VERSION.dmg"

# ── write a single-entry appcast (first native release) ─────────────────────
cat > dist/appcast.xml <<XML
<?xml version="1.0" encoding="utf-8"?>
<rss version="2.0" xmlns:sparkle="http://www.andymatuschak.org/xml-namespaces/sparkle" xmlns:dc="http://purl.org/dc/elements/1.1/">
  <channel>
    <title>OpenVoiceFlow</title>
    <link>$FEED_URL</link>
    <description>OpenVoiceFlow native app updates.</description>
    <language>en</language>
    <item>
      <title>Version $OVF_VERSION</title>
      <sparkle:releaseNotesLink>$SITE_BASE/release-notes/$OVF_VERSION.html</sparkle:releaseNotesLink>
      <sparkle:fullReleaseNotesLink>$SITE_BASE/releases.html</sparkle:fullReleaseNotesLink>
      <pubDate>$PUBDATE</pubDate>
      <sparkle:version>$BUILD</sparkle:version>
      <sparkle:shortVersionString>$OVF_VERSION</sparkle:shortVersionString>
      <sparkle:minimumSystemVersion>14.0</sparkle:minimumSystemVersion>
      <enclosure url="$DOWNLOAD_BASE/$DMG_NAME" $SIG_ATTRS type="application/octet-stream" />
    </item>
  </channel>
</rss>
XML

echo "▸ Wrote dist/appcast.xml"
cat dist/appcast.xml
