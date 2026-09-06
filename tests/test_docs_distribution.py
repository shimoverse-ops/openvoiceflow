import json
from hashlib import sha256
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
CANONICAL = "https://openvoiceflow.com"
RELEASE_VERSION = "0.5.24"
RELEASE_BUILD = 29
PREVIOUS_NATIVE_BUILD = 28
PRUNED_RELEASE_VERSIONS = (
    "0.5.5",
    "0.5.6",
    "0.5.8",
    "0.5.12",
    "0.5.13",
    "0.5.14",
    "0.5.15",
    "0.5.16",
    "0.5.17",
    "0.5.18",
    "0.5.19",
    "0.5.20",
    "0.5.21",
    "0.5.22",
    "0.5.23",
)
UNIVERSAL_SHA256 = "109f9c5356e09bc433cafc4b8ab7842ab3125287b67fcfdaaa1aff2bb55a3367"
FALLBACK = "OpenVoiceFlow-0.3.6-arm64.dmg"


def test_native_distribution_assets_exist_and_match_hashes():
    universal = DOCS / "downloads" / f"OpenVoiceFlow-{RELEASE_VERSION}.dmg"
    fallback = DOCS / "downloads" / FALLBACK
    assert universal.exists()
    assert fallback.exists(), "macOS 12–13 fallback must remain reachable"
    assert sha256(universal.read_bytes()).hexdigest() == UNIVERSAL_SHA256
    for version in PRUNED_RELEASE_VERSIONS:
        assert not (DOCS / "downloads" / f"OpenVoiceFlow-{version}.dmg").exists()


def test_download_page_has_one_native_universal_primary_and_a_clear_fallback():
    html = (DOCS / "download.html").read_text(encoding="utf-8")
    assert f'"softwareVersion": "{RELEASE_VERSION}"' in html
    assert '"operatingSystem": "macOS 14+"' in html
    assert f"downloads/OpenVoiceFlow-{RELEASE_VERSION}.dmg" in html
    assert UNIVERSAL_SHA256 in html
    assert "One universal" in html
    assert FALLBACK in html
    assert "macOS 12–13" in html
    assert "OpenVoiceFlow-0.3.6-x86_64.dmg" not in html


def test_client_chooser_always_targets_the_universal_native_dmg():
    js = (DOCS / "site.js").read_text(encoding="utf-8")
    assert js.count(f"downloads/OpenVoiceFlow-{RELEASE_VERSION}.dmg") >= 2
    assert "Universal macOS DMG" in js


def test_appcast_is_present_and_signed_for_the_final_native_release():
    appcast = (DOCS / "appcast.xml").read_text(encoding="utf-8")
    # Derived, not hardcoded: this line was left at 0.4.3 through a version bump
    # that updated everything around it.
    assert f"sparkle:shortVersionString>{RELEASE_VERSION}" in appcast
    assert "sparkle:edSignature=" in appcast
    assert f"OpenVoiceFlow-{RELEASE_VERSION}.dmg" in appcast
    # Sparkle orders updates by CFBundleVersion, so this must match the new
    # release and strictly exceed the previously published native build.
    build = int(appcast.split("sparkle:version>")[1].split("<")[0])
    assert build == RELEASE_BUILD
    assert build > PREVIOUS_NATIVE_BUILD, (
        f"appcast build {build} must exceed previous build {PREVIOUS_NATIVE_BUILD}"
    )


def test_appcast_release_notes_links_point_at_pages_that_exist():
    """Sparkle's "Version History" button opens `fullReleaseNotesLink`, and its
    update sheet loads `releaseNotesLink` — the two links a user reaches from
    Settings ▸ "Check for updates now". Both once pointed at how-it-works.html,
    a marketing page with no version history on it at all, which is invisible
    until someone clicks the button. Both must be real, generated pages.
    """
    appcast = (DOCS / "appcast.xml").read_text(encoding="utf-8")

    def link(tag: str) -> str:
        return appcast.split(f"<sparkle:{tag}>")[1].split(f"</sparkle:{tag}>")[0]

    assert link("fullReleaseNotesLink") == f"{CANONICAL}/releases.html"
    assert (DOCS / "releases.html").exists()

    notes = link("releaseNotesLink")
    assert notes == f"{CANONICAL}/release-notes/{RELEASE_VERSION}.html"
    # The publish PR ships the appcast; the notes page it points at is
    # generated from CHANGELOG.md, so the changelog entry has to land in the
    # same PR or the update sheet 404s for everyone (RELEASE.md).
    notes_page = DOCS / "release-notes" / f"{RELEASE_VERSION}.html"
    assert notes_page.exists(), (
        f"missing {notes_page.relative_to(ROOT)} — add the CHANGELOG entry for "
        f"{RELEASE_VERSION} and run python3 scripts/build_releases.py"
    )
    assert RELEASE_VERSION in notes_page.read_text(encoding="utf-8")

    # Whatever the next release generates must keep both links.
    script = (ROOT / "native" / "scripts" / "appcast.sh").read_text(encoding="utf-8")
    assert "<sparkle:fullReleaseNotesLink>$SITE_BASE/releases.html<" in script
    assert "<sparkle:releaseNotesLink>$SITE_BASE/release-notes/$OVF_VERSION.html<" in script


def test_legacy_split_downloads_redirect_to_the_universal_native_dmg():
    redirects = {item["source"]: item for item in json.loads((ROOT / "vercel.json").read_text())["redirects"]}
    for previous in ["0.2.0", "0.3.2", "0.3.3", "0.3.4", "0.3.5"]:
        for arch in ["arm64", "x86_64"]:
            item = redirects[f"/downloads/OpenVoiceFlow-{previous}-{arch}.dmg"]
            assert item["destination"] == f"/downloads/OpenVoiceFlow-{RELEASE_VERSION}.dmg"
            assert item["permanent"] is True

    for version in PRUNED_RELEASE_VERSIONS:
        pruned = redirects[f"/downloads/OpenVoiceFlow-{version}.dmg"]
        assert pruned["destination"] == f"/downloads/OpenVoiceFlow-{RELEASE_VERSION}.dmg"
        assert pruned["permanent"] is True


def test_public_downloads_remain_website_hosted():
    pages = ["download.html", "install.html", "how-it-works.html"]
    combined = "\n".join((DOCS / name).read_text(encoding="utf-8") for name in pages)
    assert "github.com/shimoverse/openvoiceflow/releases/download" not in combined
    assert CANONICAL in (DOCS / "download.html").read_text(encoding="utf-8")


def test_privacy_friendly_web_observability_is_present_without_native_telemetry():
    public_pages = ["index.html", "download.html", "install.html", "how-it-works.html", "privacy.html", "mission.html"]
    for page in public_pages:
        html = (DOCS / page).read_text(encoding="utf-8")
        assert "va.vercel-scripts.com/v1/script.js" in html
        assert "/_vercel/speed-insights/script.js" in html

    site_js = (DOCS / "site.js").read_text(encoding="utf-8")
    for event in [
        "download_click", "install_guide_click", "navigation_click", "hero_cta_click",
        "github_click", "demo_play", "docs_nav_click",
        # Page-level intent beyond navigation: which footer links, who verifies
        # the checksum, and which release notes / FAQ answers get opened.
        "footer_click", "copy_click", "disclosure_open",
    ]:
        assert event in site_js

    privacy = (ROOT / "PRIVACY.md").read_text(encoding="utf-8")
    # Since v0.5.7 there IS in-app usage sharing (opt-out, on by default) —
    # the policy discloses it plainly rather than claiming it doesn't exist.
    assert "Share anonymous usage & leaderboard rank" in privacy
    assert "on by default" in privacy
    assert "Vercel Speed Insights" in privacy


def test_download_page_pre_warns_about_the_gatekeeper_prompt():
    """The first real user dragged the app to Applications and nothing happened,
    then hit "downloaded from the Internet" and read it as a failure. macOS
    cannot launch an app off a disk image and the prompt is unavoidable outside
    the App Store, so the only fix is to say both up front. If these three
    cards ever go missing, that support question comes straight back."""
    html = (DOCS / "download.html").read_text(encoding="utf-8")
    assert 'class="next-steps"' in html
    assert "Drag it to Applications" in html
    assert "Open it from Applications" in html
    assert "macOS will warn you once" in html
    # The reassurance matters as much as the instruction.
    assert "Nothing is broken" in html
    assert "next-step-warn" in html, "step 3 must be the highlighted card"

    css = (DOCS / "style.css").read_text(encoding="utf-8")
    # Highlighted in both appearances — the site follows the OS theme.
    assert "--warn-bg: #FBF3E7" in css
    assert css.count("--warn-bg") >= 2, "dark mode needs its own value"
