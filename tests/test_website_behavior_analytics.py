"""Privacy and wiring contracts for first-party website behavior analytics."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_site_tracks_visits_pages_and_allowlisted_actions_without_persistent_browser_id() -> None:
    site = read("docs/site.js")

    assert "'/api/analytics/event'" in site
    assert "sessionTimeoutMs = 30 * 60 * 1000" in site
    assert "window.sessionStorage" in site
    assert "window.localStorage" not in site
    assert "track('page_view')" in site
    for event in (
        "download_click",
        "install_guide_click",
        "navigation_click",
        "hero_cta_click",
        "github_click",
        "demo_play",
        "docs_nav_click",
    ):
        assert event in site
    assert "navigator.globalPrivacyControl" in site
    assert "navigator.doNotTrack" in site


def test_public_privacy_copy_matches_collected_fields_and_retention() -> None:
    markdown = read("PRIVACY.md")
    public = read("docs/privacy.html")

    for content in (markdown, public):
        assert "30 minutes" in content
        assert "90 days" in content
        assert "IP address" in content or "IP addresses" in content
        assert "raw click coordinates" in content
        assert "persistent cross-visit browser" in content
        assert "Global Privacy Control" in content


def test_schema_has_coarse_location_but_no_ip_or_raw_click_fields() -> None:
    schema = read("db/schema.sql").lower()
    website_schema = schema.split("create table if not exists website_events", 1)[1]

    for field in ("session_id", "event_name", "path", "target", "country", "region", "city"):
        assert field in website_schema
    for forbidden in ("ip_address", "ip_hash", "click_x", "click_y", "query_string", "form_value"):
        assert forbidden not in website_schema


def test_retention_cron_is_declared() -> None:
    vercel = read("vercel.json")
    assert '"path": "/api/cron/analytics-retention"' in vercel
    assert '"schedule": "17 3 * * *"' in vercel
