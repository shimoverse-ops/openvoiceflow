"""SEO/AEO contracts for the public website.

The blog exists to bring search and AI-assistant traffic to the site. Each
test here pins the plumbing that quietly breaks that goal when a page is
added or edited: a missing canonical splits ranking signal across URL
variants, a page absent from the sitemap can go unindexed for weeks, an
article without analytics is invisible in the numbers, and a broken
llms.txt link teaches AI assistants to cite 404s. None of these failures
are visible on the rendered page — which is exactly why they're tests.
"""
import json
import re
import struct
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
CANONICAL = "https://openvoiceflow.com"

MAIN_PAGES = [
    "index.html",
    "mission.html",
    "download.html",
    "install.html",
    "how-it-works.html",
    "privacy.html",
    "releases.html",
]
ARTICLES = sorted(
    p.name for p in (DOCS / "blog").glob("*.html") if p.name != "index.html"
)
MANUAL = sorted(p.name for p in (DOCS / "docs").glob("*.html"))
ALL_PAGES = (
    MAIN_PAGES
    + ["blog/index.html"] + [f"blog/{name}" for name in ARTICLES]
    + [f"docs/{name}" for name in MANUAL]
)


def read(rel: str) -> str:
    return (DOCS / rel).read_text(encoding="utf-8")


def expected_url(rel: str) -> str:
    """index.html pages canonicalize to their directory URL, others to .html."""
    if rel == "index.html":
        return f"{CANONICAL}/"
    if rel in ("blog/index.html", "docs/index.html"):
        return f"{CANONICAL}/{rel.rsplit('/', 1)[0]}/"
    return f"{CANONICAL}/{rel}"


def test_blog_launch_set_is_present():
    # The current article set. If one is renamed, every reference below —
    # sitemap, llms.txt, homepage cards — must move with it; start here.
    assert ARTICLES == sorted([
        "best-dictation-software-mac.html",
        "wispr-flow-alternative.html",
        "how-to-dictate-on-mac.html",
        "whisper-models-for-dictation.html",
        "offline-dictation-mac.html",
        "voice-typing-for-developers.html",
        "personal-dictionary-dictation.html",
        "dictation-for-writers.html",
        "is-on-device-dictation-private.html",
    ])


def test_every_public_page_has_exactly_one_matching_canonical():
    """Vercel serves /blog/ and /blog/index.html as the same content; the
    canonical tag is what stops search engines treating them as duplicates."""
    for rel in ALL_PAGES:
        html = read(rel)
        tags = re.findall(r'<link rel="canonical" href="([^"]+)"', html)
        assert tags == [expected_url(rel)], f"{rel}: canonical is {tags}"


def test_every_public_page_has_a_real_meta_description():
    # Search snippets and AI answer engines read this. Empty or runaway
    # descriptions get rewritten by Google into something we didn't choose.
    for rel in ALL_PAGES:
        html = read(rel)
        m = re.search(r'<meta name="description" content="([^"]*)"', html)
        assert m, f"{rel}: missing meta description"
        assert 40 <= len(m.group(1)) <= 200, f"{rel}: description length {len(m.group(1))}"


def test_every_public_page_has_social_cards_and_analytics():
    """A shared page with no OG image renders as a bare link in Slack and
    social feeds; a page without analytics is a page whose traffic the
    maintainers can't see. Both regressions are silent in the browser."""
    for rel in ALL_PAGES:
        html = read(rel)
        assert 'property="og:image"' in html, f"{rel}: missing og:image"
        assert 'name="viewport"' in html, f"{rel}: missing viewport"
        assert "va.vercel-scripts.com/v1/script.js" in html, f"{rel}: missing analytics"
        assert "/_vercel/speed-insights/script.js" in html, f"{rel}: missing speed insights"


def test_sitemap_lists_exactly_the_public_pages():
    sitemap = read("sitemap.xml")
    listed = set(re.findall(r"<loc>([^<]+)</loc>", sitemap))
    expected = {expected_url(rel) for rel in ALL_PAGES}
    assert listed == expected, (
        f"missing from sitemap: {expected - listed}; stale in sitemap: {listed - expected}"
    )
    for lastmod in re.findall(r"<lastmod>([^<]+)</lastmod>", sitemap):
        date.fromisoformat(lastmod)  # raises on garbage


def test_robots_txt_still_points_at_the_sitemap():
    robots = read("robots.txt")
    assert "Allow: /" in robots
    assert f"Sitemap: {CANONICAL}/sitemap.xml" in robots


def test_every_article_carries_its_structured_data():
    """BlogPosting + FAQPage JSON-LD is how articles become rich results and
    AI-assistant citations rather than plain blue links. Publish dates are
    deliberately omitted (maintainer decision, August 2026): every article
    launched on the same day, and a shared datePublished across the whole
    blog reads as fake freshness rather than real dates worth showing."""
    for name in ARTICLES:
        html = read(f"blog/{name}")
        assert '"@type": "BlogPosting"' in html, f"{name}: missing BlogPosting schema"
        assert '"datePublished"' not in html, f"{name}: should not carry datePublished"
        assert '"@type": "FAQPage"' in html, f"{name}: missing FAQPage schema"
        blobs = re.findall(
            r'<script type="application/ld\+json">\s*(\{.*?\})\s*</script>', html, re.S
        )
        assert blobs, f"{name}: no JSON-LD blocks"
        for blob in blobs:
            json.loads(blob)  # malformed JSON-LD is silently ignored by crawlers


def test_every_article_opens_with_a_direct_answer_and_links_to_download():
    # The answer box is the AEO contract: the first thing an extractive
    # engine sees must answer the query. The download link is the
    # conversion path — traffic without it is a library, not a funnel.
    for name in ARTICLES:
        html = read(f"blog/{name}")
        assert 'class="article-answer"' in html, f"{name}: missing answer box"
        assert '../download.html' in html, f"{name}: no path to the download page"


def test_blog_index_links_every_article_and_home_links_the_blog():
    index = read("blog/index.html")
    for name in ARTICLES:
        assert f'href="{name}"' in index, f"blog index does not link {name}"
    home = read("index.html")
    assert 'href="blog/index.html"' in home, "homepage does not link the blog"


def test_the_manual_is_complete_and_matches_its_generator():
    """docs/docs/ is generated by scripts/build_docs.py. If NAV and the
    generated files ever diverge, the sidebar links somewhere that 404s —
    invisible until a reader clicks it."""
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "build_docs", ROOT / "scripts" / "build_docs.py"
    )
    build_docs = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(build_docs)

    assert sorted(f"{s}.html" for s in build_docs.ORDER) == MANUAL, (
        "generated manual does not match build_docs.ORDER — re-run "
        "python3 scripts/build_docs.py"
    )
    assert len(MANUAL) >= 20, "the manual should stay substantial"


def test_manual_pages_carry_techarticle_schema_and_navigation():
    for name in MANUAL:
        html = read(f"docs/{name}")
        assert '"@type": "TechArticle"' in html, f"docs/{name}: missing TechArticle schema"
        assert 'class="docs-sidebar"' in html, f"docs/{name}: missing sidebar"
        assert 'class="docs-breadcrumb"' in html, f"docs/{name}: missing breadcrumb"
        # every page but the two endpoints has both pager directions
        assert 'class="docs-pager"' in html, f"docs/{name}: missing pager"


def test_the_docs_stylesheet_and_sidebar_script_are_present():
    """The manual is 25 pages of markup that render as an unstyled wall of
    links if style.css loses the docs layer — and every HTML assertion in
    this file still passes while that happens. Pin the CSS and the mobile
    sidebar toggle so the failure is loud instead of visual-only."""
    css = read("style.css")
    for cls in [".docs-layout", ".docs-sidebar", ".docs-body", ".callout",
                ".issue", ".docs-cards", ".docs-pager", "kbd {"]:
        assert cls in css, f"style.css is missing the docs rule {cls}"
    assert 'grid-template-columns: 232px' in css, "docs two-column grid missing"

    site_js = read("site.js")
    assert "docsSidebarToggle" in site_js, "mobile docs sidebar toggle missing"
    assert "docs_nav_click" in site_js, "docs nav analytics missing"


def test_mobile_only_controls_cannot_flash_before_the_stylesheet():
    """The hamburger and the docs sidebar toggle are hidden on desktop by
    style.css — a separate request. A paint that beats that stylesheet (the
    browser occasionally does this on same-site navigation with a
    revalidating cache) flashed them as bordered rectangles in the top-left.
    An inline rule shipped with the HTML closes that window, and it must
    stay BEFORE the stylesheet link so the mobile media queries, which come
    later in style.css, still win and reveal the controls on phones."""
    inline = ".nav-hamburger,.docs-sidebar-toggle{display:none}"
    for rel in ALL_PAGES:
        html = read(rel)
        assert inline in html, f"{rel}: missing the anti-flash inline style"
        assert html.index(inline) < html.index('rel="stylesheet"'), (
            f"{rel}: inline style must precede the stylesheet link, or the "
            f"mobile media queries can no longer override it"
        )


def test_manual_internal_links_all_resolve():
    """A manual that links to its own 404s is worse than no manual."""
    import re as _re

    for name in MANUAL:
        html = read(f"docs/{name}")
        for href in _re.findall(r'href="([^"#:]+\.html)(?:#[^"]*)?"', html):
            target = (DOCS / "docs" / href).resolve()
            assert target.exists(), f"docs/{name} links to missing {href}"


def test_the_manual_never_claims_spoken_punctuation_commands():
    """v0.5.13 has no spoken-punctuation command table — that feature lives
    only in the retired Python app. The marketing site claimed it once;
    this test keeps the claim from coming back anywhere."""
    for rel in ALL_PAGES:
        low = read(rel).lower()
        assert "voice punctuation" not in low, f"{rel}: claims voice punctuation"
        assert "apply voice commands" not in low, f"{rel}: claims voice commands"


def test_every_page_navigation_reaches_the_blog_and_the_manual():
    """Nav links are the crawl path; a section reachable only from the
    sitemap looks orphaned to search engines and to humans alike. Paths are
    relative, so the expected href depends on which directory the page is in."""
    for rel in ALL_PAGES:
        html = read(rel)
        if rel in MAIN_PAGES:
            blog, docs = "blog/index.html", "docs/index.html"
        elif rel.startswith("blog/"):
            blog, docs = "index.html", "../docs/index.html"
        else:
            blog, docs = "../blog/index.html", "index.html"
        assert f'<li><a href="{blog}">Blog</a></li>' in html, f"{rel}: no Blog nav link"
        assert f'<li><a href="{docs}">Docs</a></li>' in html, f"{rel}: no Docs nav link"


def test_llms_txt_covers_the_blog_and_never_links_a_404():
    """llms.txt is what AI assistants read first; a dead link there becomes
    a hallucinated citation in someone's chat answer."""
    llms = read("llms.txt")
    assert f"{CANONICAL}/blog/" in llms
    for name in ARTICLES:
        assert f"{CANONICAL}/blog/{name}" in llms, f"llms.txt missing {name}"
    for url in re.findall(rf"{re.escape(CANONICAL)}(/[^\s)]*)", llms):
        path = url.split("#")[0]
        if path.endswith("/"):
            path += "index.html"
        assert (DOCS / path.lstrip("/")).exists(), f"llms.txt links missing file {path}"


def test_the_product_film_ships_with_its_plumbing():
    """The homepage embeds a 52s product film. A missing poster means a black
    rectangle above the fold; a missing captions track fails accessibility;
    a VideoObject whose contentUrl 404s becomes a broken rich result."""
    film = DOCS / "assets" / "openvoiceflow-demo.mp4"
    poster = DOCS / "assets" / "demo-poster.jpg"
    vtt = DOCS / "assets" / "openvoiceflow-demo.en.vtt"
    assert film.exists() and film.stat().st_size > 500_000, "film missing or truncated"
    assert poster.exists() and poster.stat().st_size > 10_000, "poster missing or truncated"
    assert vtt.exists() and vtt.read_text(encoding="utf-8").startswith("WEBVTT")

    home = read("index.html")
    assert '<video data-film' in home
    assert 'poster="assets/demo-poster.jpg"' in home
    assert 'src="assets/openvoiceflow-demo.mp4"' in home
    assert '<track kind="captions" src="assets/openvoiceflow-demo.en.vtt"' in home
    assert '"@type": "VideoObject"' in home
    assert '"contentUrl": "https://openvoiceflow.com/assets/openvoiceflow-demo.mp4"' in home

    site_js = read("site.js")
    assert "demo_play" in site_js, "film plays must be visible in analytics"


def test_every_page_links_the_public_github_repo():
    """Maintainer decision (September 2026, superseding the July 2026 "no
    GitHub links" call): every page now carries a clearly-labeled GitHub nav
    item — logo plus "GitHub" — linking straight to the public repository,
    alongside the Releases page that surfaces the changelog as version
    history. site.js's github_click handler, previously inert, now fires for
    real."""
    repo = "https://github.com/shimoverse/openvoiceflow"
    for rel in ALL_PAGES:
        html = read(rel)
        assert 'class="nav-github"' in html, f"{rel}: missing the GitHub nav link"
        assert html.count(repo) >= 1, f"{rel}: GitHub nav link does not point at {repo}"
    assert "shimoverse@gmail.com" in read("mission.html")


def test_releases_page_lists_recent_versions_with_notes():
    """The Releases page is generated from CHANGELOG.md by
    scripts/build_releases.py — it must actually list real, dated release
    notes (not just link out to GitHub) so visitors can see the project is
    actively maintained without leaving the site."""
    html = read("releases.html")
    for version in ["0.5.24", "0.5.23", "0.5.8"]:
        assert f"v{version}" in html, f"releases.html missing v{version}"
    assert html.count('<details class="content-card"') >= 20, (
        "releases.html should list a substantial version history"
    )
    assert "https://github.com/shimoverse/openvoiceflow/releases" in html


def test_every_release_card_is_deep_linkable():
    """Each release renders as a collapsed-by-default <details>, and a browser
    will not scroll to — or reveal — a fragment inside a closed one. The app's
    Settings link and the appcast both address versions as releases.html#vX.Y.Z,
    so every card carries that id and the page opens the targeted one."""
    html = read("releases.html")
    versions = re.findall(r'<summary><h2>v([0-9.]+)', html)
    assert len(versions) >= 20
    for version in versions:
        assert f'id="v{version}"' in html, f"releases.html: v{version} has no anchor"
    assert "hashchange" in html, "releases.html must open the release named by the URL fragment"


def test_per_version_release_notes_pages_are_self_contained_and_unindexed():
    """These pages exist for the WebView Sparkle embeds in its update sheet:
    no nav, no external stylesheet (nothing else is loaded yet), and noindex +
    canonical so they don't compete with releases.html in search."""
    for version in ["0.5.24", "0.5.23"]:
        page = DOCS / "release-notes" / f"{version}.html"
        assert page.exists(), f"missing release notes page for {version}"
        html = page.read_text(encoding="utf-8")
        assert 'name="robots" content="noindex' in html
        assert f'<link rel="canonical" href="{CANONICAL}/releases.html#v{version}" />' in html
        assert 'rel="stylesheet"' not in html
        assert f"{CANONICAL}/releases.html" in html, "must link back to the full history"


def test_homepage_structured_data_links_the_project_to_its_repository():
    blocks = [
        json.loads(raw)
        for raw in re.findall(
            r'<script type="application/ld\+json">(.*?)</script>',
            read("index.html"),
            flags=re.DOTALL,
        )
    ]
    software = next(block for block in blocks if block.get("@type") == "SoftwareApplication")
    organization = next(block for block in blocks if block.get("@type") == "Organization")
    repository = "https://github.com/shimoverse/openvoiceflow"

    assert software["license"] == "https://opensource.org/licenses/MIT"
    assert software["codeRepository"] == repository
    assert software["sameAs"] == repository
    assert organization["sameAs"] == [repository, "https://github.com/shimoverse"]


def test_articles_keep_the_competitor_claims_hedged():
    # AGENTS.md: claims on the website must be true of the shipped app, and
    # competitor claims must be dated. Comparison pages carry the hedge line
    # so a reader (or a competitor's lawyer) sees sourcing, not assertion.
    for name in ["wispr-flow-alternative.html", "best-dictation-software-mac.html"]:
        html = read(f"blog/{name}")
        assert "July 2026" in html, f"{name}: competitor claims lost their date hedge"
        assert "affiliation" in html.lower(), f"{name}: missing no-affiliation note"


def test_favicon_is_a_real_file_not_a_data_uri():
    # Google's favicon-in-search pipeline fetches the icon as its own
    # crawlable resource and falls back to a generic globe when it can't —
    # a data: URI isn't a stable, separately-fetchable URL. Every page must
    # link real files, and those files must actually exist and be square.
    for rel in ALL_PAGES:
        html = read(rel)
        assert "data:image/svg+xml" not in html, f"{rel}: favicon reverted to a data: URI"
        assert 'rel="icon" href="' in html, f"{rel}: missing a real <link rel=\"icon\">"

    for asset in ["favicon.svg", "favicon.ico", "favicon-48.png", "favicon-192.png", "apple-touch-icon.png"]:
        path = DOCS / asset
        assert path.is_file(), f"missing {asset} at the site root"
        assert path.stat().st_size > 0, f"{asset} is empty"

    assert png_dimensions("favicon-48.png") == (48, 48), \
        "favicon-48.png must be exactly 48x48 (square, per Google's guidance)"
    assert png_dimensions("apple-touch-icon.png") == (180, 180), \
        "apple-touch-icon.png must be 180x180 per Apple's convention"


def png_dimensions(name: str) -> tuple[int, int]:
    # PNG width/height live as big-endian uint32s right after the 8-byte
    # signature + IHDR chunk header (bytes 16:20 and 20:24). No imaging
    # library needed for a bounds check this simple.
    header = (DOCS / name).read_bytes()[:24]
    width, height = struct.unpack(">II", header[16:24])
    return width, height


def test_organization_logo_is_on_brand_and_square():
    """The Organization/BlogPosting "logo" feeds Google's rich-result and
    Knowledge Panel branding. It must point at the current brand icon (the
    amber waveform ring on the dark app-icon square) rather than the
    retired mic-and-waveform icon the legacy Python app's icon generator
    draws, and rather than the 1200x630 og:image social card — Google
    expects a roughly square logo, and a wide card fails that shape."""
    assert png_dimensions("assets/openvoiceflow-logo-512.png") == (512, 512), \
        "brand logo must be square"
    for rel in ALL_PAGES:
        html = read(rel)
        assert "openvoiceflow-icon-512.png" not in html, (
            f"{rel}: still references the retired mic-icon logo"
        )
        assert '"logo": "https://openvoiceflow.com/assets/og-card.png"' not in html, (
            f"{rel}: Organization logo is the wide social card, not a square logo"
        )
