#!/usr/bin/env python3
"""Generate docs/releases.html (and docs/release-notes/*.html) from CHANGELOG.md.

Why a generator: CHANGELOG.md is already the maintainers' authoritative,
human-written release notes — re-typing them into a second hand-maintained
HTML page is exactly how a website goes stale the next time someone ships a
release and forgets the second copy. This script re-renders the page from
the changelog every time, so "add a CHANGELOG entry" is the only step that
keeps the public Releases page current.

Two outputs, one source:
  docs/releases.html            the public Releases page, one anchored card
                                per version (#v0.5.20), newest first.
  docs/release-notes/<v>.html   a bare, self-contained page per version, sized
                                for the small WebView Sparkle embeds in its
                                update sheet. The appcast's releaseNotesLink
                                points here and its fullReleaseNotesLink points
                                at releases.html, which is what fills Sparkle's
                                "Version History" button.

Run:  python3 scripts/build_releases.py
Then: python3 -m pytest tests/test_docs_seo.py tests/test_docs_distribution.py -q
"""
from __future__ import annotations

import html
import re
from datetime import date, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHANGELOG = ROOT / "CHANGELOG.md"
OUT = ROOT / "docs" / "releases.html"
NOTES_DIR = ROOT / "docs" / "release-notes"
CANONICAL = "https://openvoiceflow.com"
REPO = "https://github.com/shimoverse/openvoiceflow"

MONTHS = ["January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December"]

# Versions dated within this many days of the newest entry render expanded;
# older ones render collapsed (still readable, one click away) so the page
# opens on recent activity instead of thirty-five expanded release cards.
OPEN_WINDOW_DAYS = 21


def format_date(iso: str) -> str:
    y, m, d = (int(x) for x in iso.split("-"))
    return f"{MONTHS[m - 1]} {d}, {y}"


def inline_md(text: str) -> str:
    text = html.escape(text, quote=False)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', text)
    return text


def parse_changelog() -> list[dict]:
    text = CHANGELOG.read_text(encoding="utf-8")
    body = text.split("\n## Compare links", 1)[0]

    headers = list(re.finditer(r"^## \[(.+?)\](?: — (\d{4}-\d{2}-\d{2}))?\s*$", body, re.M))
    releases = []
    for i, m in enumerate(headers):
        version, iso_date = m.group(1), m.group(2)
        if version == "Unreleased":
            continue
        start = m.end()
        end = headers[i + 1].start() if i + 1 < len(headers) else len(body)
        block = body[start:end]

        sections = []
        for sm in re.finditer(r"^### (.+)$", block, re.M):
            sstart = sm.end()
            send_idx = block.find("\n### ", sstart)
            send_idx = len(block) if send_idx == -1 else send_idx
            section_body = block[sstart:send_idx]
            bullets = []
            for bm in re.finditer(r"^- (.+(?:\n {2}.+)*)", section_body, re.M):
                raw = " ".join(line.strip() for line in bm.group(1).split("\n"))
                bullets.append(inline_md(raw))
            if bullets:
                sections.append((sm.group(1).strip(), bullets))

        if not sections:
            continue
        releases.append({"version": version, "date": iso_date, "sections": sections})
    return releases


def render_release(rel: dict, open_by_default: bool) -> str:
    date_html = f' <span class="release-date">· {format_date(rel["date"])}</span>' if rel["date"] else ""
    parts = [
        f'      <details class="content-card" id="v{rel["version"]}"{" open" if open_by_default else ""}>'
        f'<summary><h2>v{rel["version"]}{date_html}</h2></summary>'
    ]
    for title, bullets in rel["sections"]:
        parts.append(f"        <h3>{html.escape(title)}</h3>")
        parts.append('        <ul class="check-list">')
        for b in bullets:
            parts.append(f"          <li>{b}</li>")
        parts.append("        </ul>")
    parts.append("      </details>")
    return "\n".join(parts)


def render(releases: list[dict]) -> str:
    newest = next((r["date"] for r in releases if r["date"]), None)
    cutoff = (datetime.strptime(newest, "%Y-%m-%d").date() - timedelta(days=OPEN_WINDOW_DAYS)) if newest else date.min

    cards = []
    for rel in releases:
        rel_date = datetime.strptime(rel["date"], "%Y-%m-%d").date() if rel["date"] else date.min
        cards.append(render_release(rel, open_by_default=rel_date >= cutoff))
    cards_html = "\n".join(cards)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Releases — OpenVoiceFlow Version History</title>
  <meta name="description" content="Every OpenVoiceFlow release with its notes, newest first: what shipped, what changed, and what was fixed, straight from the project's changelog." />
  <meta property="og:title" content="OpenVoiceFlow release history" />
  <meta property="og:description" content="Every OpenVoiceFlow release with its notes, newest first — see exactly what shipped and when." />
  <meta property="og:url" content="{CANONICAL}/releases.html" />
  <meta property="og:type" content="website" />
  <meta property="og:image" content="https://openvoiceflow.com/assets/og-card.png" />
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:image" content="https://openvoiceflow.com/assets/og-card.png" />
  <link rel="canonical" href="{CANONICAL}/releases.html" />
  <link rel="icon" href="/assets/openvoiceflow-logo-512.png" sizes="512x512" type="image/png" />
  <link rel="apple-touch-icon" href="/apple-touch-icon.png" />
  <style>.nav-hamburger,.docs-sidebar-toggle{{display:none}}</style>
  <link rel="stylesheet" href="style.css" />
  <script type="application/ld+json">
  {{
    "@context": "https://schema.org",
    "@type": "AboutPage",
    "name": "OpenVoiceFlow release history",
    "url": "{CANONICAL}/releases.html",
    "description": "Every OpenVoiceFlow release with its notes, newest first: what shipped, what changed, and what was fixed.",
    "isPartOf": {{"@type": "WebSite", "name": "OpenVoiceFlow", "url": "{CANONICAL}/"}}
  }}
  </script>
  <script>
    window.va = window.va || function () {{ (window.vaq = window.vaq || []).push(arguments); }};
  </script>
  <script defer src="https://va.vercel-scripts.com/v1/script.js" data-view-endpoint="https://vitals.vercel-analytics.com/v1/view?dsn=hbQ2mG8dCYsBmC0cvPE6eVdkD" data-event-endpoint="https://vitals.vercel-analytics.com/v1/event?dsn=hbQ2mG8dCYsBmC0cvPE6eVdkD"></script>
  <script defer src="/_vercel/speed-insights/script.js"></script>
</head>
<body>
  <nav class="nav" id="nav" aria-label="Main">
    <div class="nav-inner container">
      <a href="index.html" class="nav-logo"><canvas class="nav-glyph" data-wf="glyph" aria-hidden="true"></canvas><span class="nav-logo-text">OpenVoiceFlow</span></a>
      <ul class="nav-links">
        <li><a href="mission.html">Mission</a></li>
        <li><a href="how-it-works.html">How it works</a></li>
        <li><a href="install.html">Install</a></li>
        <li><a href="docs/index.html">Docs</a></li>
        <li><a href="blog/index.html">Blog</a></li>
        <li><a href="{REPO}" class="nav-github" target="_blank" rel="noopener"><svg class="nav-github-icon" viewBox="0 0 16 16" width="16" height="16" aria-hidden="true" fill="currentColor"><path d="M8 0C3.58 0 0 3.64 0 8.13c0 3.59 2.29 6.63 5.47 7.71.4.08.55-.18.55-.4 0-.19-.01-.82-.01-1.49-2.01.38-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.83.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82a7.6 7.6 0 0 1 4 0c1.53-1.03 2.2-.82 2.2-.82.44 1.1 .16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .22.15.46.55.4A8.13 8.13 0 0 0 16 8.13C16 3.64 12.42 0 8 0z"/></svg><span>GitHub</span></a></li>
        <li><a href="download.html" class="btn btn-primary">Download</a></li>
      </ul>
      <button class="nav-hamburger" id="navHamburger" type="button" aria-label="Open menu" aria-expanded="false" aria-controls="navDrawer"><span></span><span></span><span></span></button>
    </div>
    <div class="nav-drawer" id="navDrawer">
      <a href="index.html">Home</a>
      <a href="mission.html">Mission</a>
      <a href="download.html">Download</a>
      <a href="install.html">Install</a>
      <a href="how-it-works.html">How it works</a>
      <a href="docs/index.html">Docs</a>
      <a href="blog/index.html">Blog</a>
      <a href="{REPO}" class="nav-github" target="_blank" rel="noopener"><svg class="nav-github-icon" viewBox="0 0 16 16" width="16" height="16" aria-hidden="true" fill="currentColor"><path d="M8 0C3.58 0 0 3.64 0 8.13c0 3.59 2.29 6.63 5.47 7.71.4.08.55-.18.55-.4 0-.19-.01-.82-.01-1.49-2.01.38-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.83.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82a7.6 7.6 0 0 1 4 0c1.53-1.03 2.2-.82 2.2-.82.44 1.1 .16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .22.15.46.55.4A8.13 8.13 0 0 0 16 8.13C16 3.64 12.42 0 8 0z"/></svg><span>GitHub</span></a>
      <a href="download.html" class="btn btn-primary">Download for Mac</a>
    </div>
  </nav>

  <main>
    <section class="page-hero"><div class="container hero-inner">
      <h1 class="hero-title">Releases</h1>
      <p class="hero-sub answer-block">OpenVoiceFlow ships often — every release below is real, shipped, and notarized, newest first. Notes come straight from the project's changelog, so this list is exactly as current as the code. Want the raw commit history or to file an issue? <a href="{REPO}/releases">See every release on GitHub</a>.</p>

{cards_html}

      <div class="hero-cta-row" style="margin-top:26px">
        <a class="btn btn-primary btn-lg" href="download.html">Download for Mac — free</a>
        <a class="btn btn-outline btn-lg" href="{REPO}" target="_blank" rel="noopener">View source on GitHub</a>
      </div>
    </div></section>
  </main>

  <footer class="footer">
    <div class="container footer-inner">
      <canvas class="footer-glyph" data-wf="glyph" aria-hidden="true"></canvas>
      <p class="footer-copy">© 2026 OpenVoiceFlow contributors. MIT License.</p>
      <nav class="footer-links" aria-label="Footer">
        <a href="index.html">Home</a>
        <a href="mission.html">Mission</a>
        <a href="download.html">Download</a>
        <a href="install.html">Install</a>
        <a href="how-it-works.html">How it works</a>
        <a href="docs/index.html">Docs</a>
        <a href="blog/index.html">Blog</a>
        <a href="privacy.html">Privacy</a>
        <a href="llms.txt">llms.txt</a>
      </nav>
    </div>
  </footer>

  <script src="site.js"></script>
  <script>
    // Deep links carry a version anchor (releases.html#v0.5.20) — the app's
    // update sheet and the changelog both link that way. A collapsed <details>
    // is invisible to the browser's own fragment scroll, so open the targeted
    // release first, then jump to it.
    (function () {{
      function revealTarget() {{
        var id = location.hash.slice(1);
        if (!id) return;
        var card = document.getElementById(id);
        if (!card || card.tagName !== "DETAILS") return;
        card.open = true;
        card.scrollIntoView({{ block: "start" }});
      }}
      window.addEventListener("hashchange", revealTarget);
      revealTarget();
    }})();
  </script>
</body>
</html>
"""


def render_notes(rel: dict) -> str:
    """One version's notes as a standalone page for Sparkle's update sheet.

    Sparkle loads `sparkle:releaseNotesLink` into a small WebView inside the
    update dialog, so this is deliberately not the marketing site: no nav, no
    footer, no external stylesheet (the sheet appears before anything is
    downloaded, and a page that half-loads there looks broken). It is marked
    noindex and canonicalised to the anchored card on the Releases page so the
    two copies never compete in search.
    """
    version = rel["version"]
    body = []
    for title, bullets in rel["sections"]:
        body.append(f"    <h2>{html.escape(title)}</h2>")
        body.append("    <ul>")
        for b in bullets:
            body.append(f"      <li>{b}</li>")
        body.append("    </ul>")
    body_html = "\n".join(body)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <meta name="robots" content="noindex, follow" />
  <title>OpenVoiceFlow {version} release notes</title>
  <link rel="canonical" href="{CANONICAL}/releases.html#v{version}" />
  <style>
    :root {{ color-scheme: light dark; --ink: #16130f; --ink2: #5d564d; --rule: #e4ded4; --ember: #b4531d; --bg: #fffdfa; }}
    @media (prefers-color-scheme: dark) {{
      :root {{ --ink: #f4efe7; --ink2: #a49a8c; --rule: #322d27; --ember: #e2854a; --bg: #17140f; }}
    }}
    html, body {{ background: var(--bg); }}
    body {{
      margin: 0; padding: 16px 20px 22px;
      font: 13px/1.55 -apple-system, BlinkMacSystemFont, "SF Pro Text", "Helvetica Neue", Arial, sans-serif;
      color: var(--ink);
    }}
    h1 {{ margin: 0 0 2px; font-size: 17px; letter-spacing: -0.2px; }}
    .date {{ margin: 0 0 14px; color: var(--ink2); font-size: 12px; }}
    h2 {{ margin: 16px 0 6px; font-size: 12px; text-transform: uppercase; letter-spacing: 0.7px; color: var(--ink2); }}
    ul {{ margin: 0; padding-left: 18px; }}
    li {{ margin: 0 0 5px; }}
    code {{ font-family: "SF Mono", ui-monospace, Menlo, monospace; font-size: 12px; background: color-mix(in srgb, var(--ink) 8%, transparent); padding: 1px 4px; border-radius: 4px; }}
    a {{ color: var(--ember); }}
    footer {{ margin-top: 20px; padding-top: 12px; border-top: 1px solid var(--rule); font-size: 12px; color: var(--ink2); }}
  </style>
</head>
<body>
  <main>
    <h1>OpenVoiceFlow {version}</h1>
    <p class="date">{format_date(rel["date"]) if rel["date"] else "Unreleased"}</p>
{body_html}
  </main>
  <footer>
    <a href="{CANONICAL}/releases.html">See the full version history</a>
  </footer>
</body>
</html>
"""


def write_notes(releases: list[dict]) -> int:
    """Refresh docs/release-notes/, dropping pages for versions the changelog
    no longer carries so a renamed version can't leave a stale page behind."""
    NOTES_DIR.mkdir(parents=True, exist_ok=True)
    keep = set()
    for rel in releases:
        path = NOTES_DIR / f"{rel['version']}.html"
        path.write_text(render_notes(rel), encoding="utf-8")
        keep.add(path.name)
    for stale in NOTES_DIR.glob("*.html"):
        if stale.name not in keep:
            stale.unlink()
    return len(keep)


def main() -> None:
    releases = parse_changelog()
    assert releases, "no releases parsed from CHANGELOG.md"
    OUT.write_text(render(releases), encoding="utf-8")
    count = write_notes(releases)
    print(f"wrote {OUT} ({len(releases)} releases)")
    print(f"wrote {NOTES_DIR} ({count} per-version notes pages)")


if __name__ == "__main__":
    main()
