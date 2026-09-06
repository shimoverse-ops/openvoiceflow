#!/usr/bin/env python3
"""Generate the OpenVoiceFlow documentation site into docs/docs/.

Why a generator: the manual is ~18 pages that must share a sidebar, nav,
breadcrumbs, JSON-LD, and prev/next pager. Hand-maintaining that chrome
across 18 files is how sidebars drift and canonicals go stale. Content
lives in `PAGES` below; everything around it is derived.

Run:  python3 scripts/build_docs.py
Then: python3 -m pytest tests/test_docs_seo.py -q
"""
from __future__ import annotations

import html
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "docs"
CANONICAL = "https://openvoiceflow.com"
VERSION = "0.5.23"
UPDATED = "2026-09-02"

# ── sidebar / page order ────────────────────────────────────────────────
# (group title, [(slug, sidebar label)]). Order here is reading order and
# drives the prev/next pager.
NAV: list[tuple[str, list[tuple[str, str]]]] = [
    ("Getting started", [
        ("index", "Documentation home"),
        ("quickstart", "Quickstart"),
        ("installation", "Installation"),
        ("permissions", "Permissions"),
    ]),
    ("Using OpenVoiceFlow", [
        ("dictation-basics", "Dictation basics"),
        ("hotkeys", "Hotkeys"),
        ("text-insertion", "How text is inserted"),
        ("dashboard", "Dashboard & history"),
    ]),
    ("Transcription", [
        ("how-transcription-works", "How transcription works"),
        ("models", "Whisper models"),
        ("languages", "Languages"),
        ("accuracy", "Improving accuracy"),
    ]),
    ("Personalization", [
        ("dictionary", "Personal dictionary"),
        ("snippets", "Snippets"),
        ("styles", "Per-app styles"),
        ("profile", "Know-Me profile"),
    ]),
    ("AI cleanup", [
        ("ai-cleanup", "AI cleanup overview"),
        ("backends", "Choosing a backend"),
        ("api-keys", "API keys & costs"),
    ]),
    ("Reference", [
        ("settings", "Settings reference"),
        ("privacy-architecture", "Privacy architecture"),
        ("updates", "Updates & versions"),
        ("uninstall", "Uninstalling"),
    ]),
    ("Help", [
        ("troubleshooting", "Troubleshooting"),
        ("faq", "FAQ"),
    ]),
]

ORDER = [slug for _, items in NAV for slug, _ in items]

# Real, standalone files rather than a data: URI — Google's favicon-in-
# search pipeline fetches the icon as its own crawlable resource and falls
# back to a generic globe when it can't (data: URIs aren't a stable,
# separately-fetchable URL, which is exactly the failure mode this fixes).
FAVICON = (
    '  <link rel="icon" href="../favicon.svg" type="image/svg+xml" />\n'
    '  <link rel="icon" href="../favicon-48.png" sizes="48x48" type="image/png" />\n'
    '  <link rel="icon" href="../favicon.ico" sizes="any" />\n'
    '  <link rel="apple-touch-icon" href="../apple-touch-icon.png" />'
)

# Mobile-only controls are hidden by style.css, which is a separate request.
# When the browser paints before that stylesheet applies — it occasionally
# does on same-site navigation with a revalidating cache — the unstyled
# buttons flash as bordered rectangles in the top-left. Hiding them from an
# inline block that ships with the HTML closes that window. The media
# queries in style.css load after this and still reveal them on phones.
CRITICAL_CSS = "  <style>.nav-hamburger,.docs-sidebar-toggle{display:none}</style>"

ANALYTICS = """  <script>
    window.va = window.va || function () { (window.vaq = window.vaq || []).push(arguments); };
  </script>
  <script defer src="https://va.vercel-scripts.com/v1/script.js" data-view-endpoint="https://vitals.vercel-analytics.com/v1/view?dsn=hbQ2mG8dCYsBmC0cvPE6eVdkD" data-event-endpoint="https://vitals.vercel-analytics.com/v1/event?dsn=hbQ2mG8dCYsBmC0cvPE6eVdkD"></script>
  <script defer src="/_vercel/speed-insights/script.js"></script>"""

GITHUB_ICON = ('<svg class="nav-github-icon" viewBox="0 0 16 16" width="16" height="16" '
               'aria-hidden="true" fill="currentColor"><path d="M8 0C3.58 0 0 3.64 0 8.13c0 3.59 '
               '2.29 6.63 5.47 7.71.4.08.55-.18.55-.4 0-.19-.01-.82-.01-1.49-2.01.38-2.53-.49-2.69-.94-'
               '.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.83.72 1.21 1.87.87 '
               '2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-'
               '.36-1.02.08-2.12 0 0 .67-.21 2.2.82a7.6 7.6 0 0 1 4 0c1.53-1.03 2.2-.82 2.2-.82.44 1.1 '
               '.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 '
               '1.07-.01 1.93-.01 2.2 0 .22.15.46.55.4A8.13 8.13 0 0 0 16 8.13C16 3.64 12.42 0 8 0z"/></svg>')
GITHUB_REPO = "https://github.com/shimoverse/openvoiceflow"
GITHUB_LINK_NAV = (f'        <li><a href="{GITHUB_REPO}" class="nav-github" target="_blank" '
                    f'rel="noopener">{GITHUB_ICON}<span>GitHub</span></a></li>')
GITHUB_LINK_DRAWER = (f'      <a href="{GITHUB_REPO}" class="nav-github" target="_blank" '
                      f'rel="noopener">{GITHUB_ICON}<span>GitHub</span></a>')

NAVBAR = f"""  <nav class="nav" id="nav" aria-label="Main">
    <div class="nav-inner container">
      <a href="../index.html" class="nav-logo"><canvas class="nav-glyph" data-wf="glyph" aria-hidden="true"></canvas><span class="nav-logo-text">OpenVoiceFlow</span></a>
      <ul class="nav-links">
        <li><a href="../mission.html">Mission</a></li>
        <li><a href="index.html">Docs</a></li>
        <li><a href="../blog/index.html">Blog</a></li>
{GITHUB_LINK_NAV}
        <li><a href="../download.html" class="btn btn-primary">Download</a></li>
      </ul>
      <button class="nav-hamburger" id="navHamburger" type="button" aria-label="Open menu" aria-expanded="false" aria-controls="navDrawer"><span></span><span></span><span></span></button>
    </div>
    <div class="nav-drawer" id="navDrawer">
      <a href="../index.html">Home</a>
      <a href="../mission.html">Mission</a>
      <a href="../download.html">Download</a>
      <a href="index.html">Docs</a>
      <a href="../how-it-works.html">How it works</a>
      <a href="../blog/index.html">Blog</a>
{GITHUB_LINK_DRAWER}
      <a href="../download.html" class="btn btn-primary">Download for Mac</a>
    </div>
  </nav>"""

FOOTER = """  <footer class="footer">
    <div class="container footer-inner">
      <canvas class="footer-glyph" data-wf="glyph" aria-hidden="true"></canvas>
      <p class="footer-copy">© 2026 OpenVoiceFlow contributors. MIT License.</p>
      <nav class="footer-links" aria-label="Footer">
        <a href="../index.html">Home</a>
        <a href="../download.html">Download</a>
        <a href="index.html">Docs</a>
        <a href="../how-it-works.html">How it works</a>
        <a href="../blog/index.html">Blog</a>
        <a href="../releases.html">Releases</a>
        <a href="../privacy.html">Privacy</a>
        <a href="../llms.txt">llms.txt</a>
      </nav>
    </div>
  </footer>"""


def sidebar(current: str) -> str:
    out = ['      <aside class="docs-sidebar" id="docsSidebar" data-collapsed="true">',
           '        <button class="docs-sidebar-toggle" id="docsSidebarToggle" type="button" aria-expanded="false" aria-controls="docsSidebar">Documentation menu ▾</button>']
    for group, items in NAV:
        out.append('        <div class="docs-nav-group">')
        out.append(f'          <div class="docs-nav-title">{group}</div>')
        out.append("          <ul>")
        for slug, label in items:
            cur = ' aria-current="page"' if slug == current else ""
            out.append(f'            <li><a href="{slug}.html"{cur}>{label}</a></li>')
        out.append("          </ul>")
        out.append("        </div>")
    out.append("      </aside>")
    return "\n".join(out)


def pager(slug: str) -> str:
    i = ORDER.index(slug)
    labels = {slug_: label for _, items in NAV for slug_, label in items}
    parts = ['      <nav class="docs-pager" aria-label="Pagination">']
    if i > 0:
        p = ORDER[i - 1]
        parts.append(f'        <a class="prev" href="{p}.html"><span class="dir">← Previous</span>'
                     f'<span class="label">{labels[p]}</span></a>')
    if i < len(ORDER) - 1:
        n = ORDER[i + 1]
        parts.append(f'        <a class="next" href="{n}.html"><span class="dir">Next →</span>'
                     f'<span class="label">{labels[n]}</span></a>')
    parts.append("      </nav>")
    return "\n".join(parts)


def faq_schema(pairs: list[tuple[str, str]]) -> str:
    items = []
    for q, a in pairs:
        text = re.sub(r"<[^>]+>", "", a).replace("&nbsp;", " ")
        text = html.unescape(re.sub(r"\s+", " ", text)).strip()
        items.append(
            '      {"@type": "Question", "name": %s,\n       "acceptedAnswer": {"@type": "Answer", "text": %s}}'
            % (json_str(q), json_str(text))
        )
    return ('  <script type="application/ld+json">\n  {\n'
            '    "@context": "https://schema.org",\n    "@type": "FAQPage",\n'
            '    "mainEntity": [\n' + ",\n".join(items) + "\n    ]\n  }\n  </script>")


def json_str(s: str) -> str:
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def howto_schema(name: str, description: str, total_time: str, steps: list[tuple[str, str]]) -> str:
    items = ",\n".join(
        '      {"@type": "HowToStep", "name": %s, "text": %s}' % (json_str(n), json_str(t))
        for n, t in steps
    )
    return ('  <script type="application/ld+json">\n  {\n'
            '    "@context": "https://schema.org",\n    "@type": "HowTo",\n'
            f'    "name": {json_str(name)},\n    "description": {json_str(description)},\n'
            f'    "totalTime": "{total_time}",\n    "step": [\n' + items + "\n    ]\n  }\n  </script>")


def render(slug: str, page: dict) -> str:
    url = f"{CANONICAL}/docs/" if slug == "index" else f"{CANONICAL}/docs/{slug}.html"
    title = page["title"]
    label = {slug_: text for _, items in NAV for slug_, text in items}[slug]
    crumb = ('      <div class="docs-breadcrumb"><a href="../index.html">Home</a>'
             '<span class="sep">/</span><a href="index.html">Docs</a>')
    if slug != "index":
        crumb += f'<span class="sep">/</span><span>{label}</span>'
    crumb += "</div>"

    schemas = [
        '  <script type="application/ld+json">\n  {\n'
        '    "@context": "https://schema.org",\n    "@type": "TechArticle",\n'
        f'    "headline": {json_str(title)},\n    "description": {json_str(page["description"])},\n'
        f'    "url": "{url}",\n    "datePublished": "{UPDATED}",\n    "dateModified": "{UPDATED}",\n'
        '    "author": {"@type": "Organization", "name": "OpenVoiceFlow maintainers", "url": "https://openvoiceflow.com/"},\n'
        '    "publisher": {"@type": "Organization", "name": "OpenVoiceFlow", "url": "https://openvoiceflow.com/", "logo": {"@type": "ImageObject", "url": "https://openvoiceflow.com/assets/openvoiceflow-logo-512.png"}},\n'
        f'    "proficiencyLevel": "Beginner",\n    "about": {json_str("OpenVoiceFlow " + VERSION + " for macOS")},\n'
        f'    "mainEntityOfPage": "{url}"\n  }}\n  </script>',
        '  <script type="application/ld+json">\n  {\n'
        '    "@context": "https://schema.org",\n    "@type": "BreadcrumbList",\n'
        '    "itemListElement": [\n'
        '      {"@type": "ListItem", "position": 1, "name": "Home", "item": "https://openvoiceflow.com/"},\n'
        '      {"@type": "ListItem", "position": 2, "name": "Documentation", "item": "https://openvoiceflow.com/docs/"}'
        + ("" if slug == "index" else
           f',\n      {{"@type": "ListItem", "position": 3, "name": {json_str(label)}, "item": "{url}"}}')
        + "\n    ]\n  }\n  </script>",
    ]
    if page.get("faq"):
        schemas.append(faq_schema(page["faq"]))
    if page.get("howto"):
        schemas.append(howto_schema(*page["howto"]))

    body = page["body"]
    if page.get("faq"):
        body += "\n        <h2 id=\"faq\">Frequently asked</h2>\n"
        for q, a in page["faq"]:
            body += f"        <h3>{q}</h3>\n        {a}\n"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{page['head_title']}</title>
  <meta name="description" content="{html.escape(page['description'], quote=True)}" />
  <meta property="og:title" content="{html.escape(title, quote=True)}" />
  <meta property="og:description" content="{html.escape(page['description'], quote=True)}" />
  <meta property="og:url" content="{url}" />
  <meta property="og:type" content="article" />
  <meta property="og:image" content="https://openvoiceflow.com/assets/og-card.png" />
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:image" content="https://openvoiceflow.com/assets/og-card.png" />
  <link rel="canonical" href="{url}" />
{FAVICON}
{CRITICAL_CSS}
  <link rel="stylesheet" href="../style.css" />
{chr(10).join(schemas)}
{ANALYTICS}
</head>
<body>
{NAVBAR}

  <main>
    <div class="container docs-layout">
{sidebar(slug)}

      <article class="docs-main">
{crumb}
        <h1 class="docs-title">{title}</h1>
        <p class="docs-lede">{page['lede']}</p>

        <div class="docs-body">
{body}
        </div>

{pager(slug)}
        <p class="docs-feedback">Documentation for OpenVoiceFlow {VERSION} · last updated {UPDATED}. Something wrong or missing here? That is a bug — tell us at <a href="mailto:shimoverse@gmail.com">shimoverse@gmail.com</a>.</p>
      </article>
    </div>
  </main>

{FOOTER}

  <script src="../site.js"></script>
</body>
</html>
"""


def main() -> None:
    from docs_content import PAGES  # noqa: E402  (content lives next door)

    missing = [s for s in ORDER if s not in PAGES]
    extra = [s for s in PAGES if s not in ORDER]
    assert not missing, f"NAV lists pages with no content: {missing}"
    assert not extra, f"content for pages not in NAV: {extra}"

    OUT.mkdir(parents=True, exist_ok=True)
    for slug in ORDER:
        (OUT / f"{slug}.html").write_text(render(slug, PAGES[slug]), encoding="utf-8")
        print(f"wrote docs/{slug}.html")
    print(f"{len(ORDER)} pages generated into {OUT}")


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    main()
